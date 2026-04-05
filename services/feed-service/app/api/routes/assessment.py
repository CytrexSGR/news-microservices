"""
Feed assessment routes for triggering source credibility analysis.
"""
import logging
import time
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import os
from datetime import datetime

from app.db import get_async_db
from app.models import Feed, FeedAssessmentHistory
from app.api.dependencies import get_current_user_id, get_optional_user_id, security
from app.schemas.research_response import ResearchTaskValidationMixin
from app.metrics.assessment_metrics import (
    assessment_requests_total,
    assessment_duration_seconds,
    research_service_response_time_seconds,
    validation_errors_total,
    active_assessments,
    polling_iterations_total,
    polling_wait_time_seconds
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def trigger_feed_assessment(feed_id: UUID, feed_url: str, feed_name: str, auth_header: str = ""):
    """
    Trigger assessment analysis via research service.
    This runs in the background after the endpoint returns.

    Args:
        feed_id: UUID of the feed
        feed_url: URL of the feed
        feed_name: Name of the feed
        auth_header: Authorization header value (e.g., "Bearer <token>")
    """
    logger.info(f"[FEED-SERVICE] trigger_feed_assessment called for feed_id={feed_id}, feed_name={feed_name}")
    logger.info(f"[FEED-SERVICE] ⚠️  REMINDER: If assessment fails, check if research-service needs restart")
    logger.info(f"[FEED-SERVICE] ⚠️  Run: docker compose stop research-service && docker compose up -d research-service")
    from app.db import AsyncSessionLocal

    # Enable httpx wire-level logging to see exact HTTP body
    import logging as log_module
    httpx_logger = log_module.getLogger("httpx")
    httpx_logger.setLevel(log_module.DEBUG)

    research_service_url = os.getenv("RESEARCH_SERVICE_URL", "http://research-service:8000")
    logger.info(f"[FEED-SERVICE] research_service_url = {research_service_url}")

    # Create new DB session for background task
    async with AsyncSessionLocal() as db:
        # Start metrics tracking
        start_time = time.time()
        active_assessments.inc()

        try:
            # Generate unique request ID for tracing
            import uuid
            request_id = str(uuid.uuid4())
            logger.info(f"[FEED-SERVICE] Request ID: {request_id}")

            # Extract domain from feed URL
            from app.utils import parse_domain_from_url
            domain = parse_domain_from_url(feed_url)

            async with httpx.AsyncClient(timeout=120.0) as client:
                # Prepare request payload
                request_payload = {
                    "request_id": request_id,
                    "query": f"Assess the credibility and reliability of {feed_name} news source",
                    "research_function": "feed_source_assessment",
                    "feed_id": str(feed_id),
                    "function_parameters": {
                        "domain": domain,
                        "feed_url": feed_url,
                        "feed_name": feed_name,
                    }
                }

                # CRITICAL VALIDATION: Ensure research_function is present before POST
                assert "research_function" in request_payload and request_payload["research_function"], \
                    f"[{request_id}] CRITICAL: research_function missing before POST"

                logger.info(f"[{request_id}] ✓ research_function validation passed: {request_payload['research_function']}")

                # DEBUG: Log exact payload being sent
                logger.info(f"[{request_id}] Sending POST to {research_service_url}/api/v1/research/")
                logger.info(f"[{request_id}] Payload: {request_payload}")
                logger.info(f"[{request_id}] Payload keys: {list(request_payload.keys())}")

                # Prepare headers with authentication
                headers = {}
                if auth_header:
                    headers["Authorization"] = auth_header
                    logger.info(f"[{request_id}] ✓ Using authentication")

                # Track research service response time
                research_start_time = time.time()

                response = await client.post(
                    f"{research_service_url}/api/v1/research/",
                    json=request_payload,
                    headers=headers
                )

                # Fail-fast: Raise exception on non-201 status
                logger.info(f"[{request_id}] Response status: {response.status_code}")
                response.raise_for_status()

                if response.status_code == 201:  # Research service returns 201 Created
                    task_data = response.json()
                    task_id = task_data.get("id")

                    # Poll for task completion (wait until status is 'completed' or 'failed')
                    import asyncio
                    max_wait_time = 30  # Maximum 30 seconds
                    poll_interval = 1  # Check every 1 second
                    elapsed_time = 0
                    task_status = "pending"

                    logger.info(f"[{request_id}] Polling for task {task_id} completion...")

                    while task_status not in ["completed", "failed"] and elapsed_time < max_wait_time:
                        await asyncio.sleep(poll_interval)
                        elapsed_time += poll_interval

                        # Fetch task status
                        task_response = await client.get(
                            f"{research_service_url}/api/v1/research/{task_id}",
                            headers=headers
                        )

                        if task_response.status_code == 200:
                            task_result_temp = task_response.json()
                            task_status = task_result_temp.get("status", "unknown")
                            logger.info(f"[{request_id}] Task {task_id} status: {task_status} (waited {elapsed_time}s)")
                        else:
                            logger.warning(f"[{request_id}] Failed to fetch task status: {task_response.status_code}")
                            break

                    # Record polling metrics
                    polling_iterations_total.observe(elapsed_time / poll_interval)
                    polling_wait_time_seconds.observe(elapsed_time)

                    # Record research service total response time (POST to completion)
                    research_response_time = time.time() - research_start_time
                    research_service_response_time_seconds.observe(research_response_time)
                    logger.info(f"[METRICS] Research service response time: {research_response_time:.2f}s")

                    # Check final status
                    if task_status != "completed":
                        if elapsed_time >= max_wait_time:
                            logger.error(f"[{request_id}] Task {task_id} timeout after {max_wait_time}s (status: {task_status})")
                            raise ValueError(f"Research task timed out after {max_wait_time}s")
                        elif task_status == "failed":
                            logger.error(f"[{request_id}] Task {task_id} failed")
                            raise ValueError("Research task failed")

                    # Final fetch to get complete result with structured_data
                    task_response = await client.get(
                        f"{research_service_url}/api/v1/research/{task_id}",
                        headers=headers
                    )

                    if task_response.status_code == 200:
                        try:
                            task_result = task_response.json()
                        except Exception as e:
                            logger.error(f"[{request_id}] Failed to parse research response: {e}")
                            raise HTTPException(
                                status_code=502,
                                detail=f"Invalid JSON from research service: {e}"
                            )

                        # VALIDATE task_result using typed validation
                        try:
                            task_result = ResearchTaskValidationMixin.validate_task_result(task_result)
                        except ValueError as e:
                            logger.error(f"[{request_id}] Task result validation failed: {e}")

                            # Track validation error type
                            error_msg = str(e)
                            if "task_result is None" in error_msg:
                                validation_errors_total.labels(error_type='none_task_result').inc()
                            elif "not a dict" in error_msg:
                                validation_errors_total.labels(error_type='invalid_type').inc()
                            elif "missing required fields" in error_msg:
                                validation_errors_total.labels(error_type='missing_fields').inc()
                            elif "invalid status" in error_msg:
                                validation_errors_total.labels(error_type='invalid_status').inc()
                            else:
                                validation_errors_total.labels(error_type='other').inc()

                            raise HTTPException(
                                status_code=502,
                                detail=f"Research service returned invalid data: {e}"
                            )

                        # Try to use structured_data first (from Perplexity structured output)
                        structured_data = ResearchTaskValidationMixin.validate_structured_data(
                            task_result.get("structured_data")
                        )

                        if structured_data:
                            # Use structured data directly (preferred method)
                            credibility_tier = structured_data.get("credibility_tier")
                            reputation_score = structured_data.get("reputation_score")
                            founded_year = structured_data.get("founded_year")
                            organization_type = structured_data.get("organization_type")
                            political_bias = structured_data.get("political_bias")

                            # Editorial standards
                            editorial_standards = structured_data.get("editorial_standards", {})
                            if not isinstance(editorial_standards, dict):
                                editorial_standards = {
                                    "fact_checking_level": "unknown",
                                    "corrections_policy": "standard",
                                    "source_attribution": "consistent"
                                }

                            # Trust ratings
                            trust_ratings = structured_data.get("trust_ratings", {})
                            if not isinstance(trust_ratings, dict):
                                trust_ratings = {
                                    "media_bias_fact_check": "High" if credibility_tier == "tier_1" else "Medium",
                                    "allsides_rating": political_bias or "Unknown",
                                    "newsguard_score": reputation_score or 0
                                }

                            # Recommendation
                            recommendation = structured_data.get("recommendation", {})
                            if not isinstance(recommendation, dict):
                                recommendation = {
                                    "skip_waiting_period": credibility_tier == "tier_1",
                                    "initial_quality_boost": 10 if credibility_tier == "tier_1" else 5,
                                    "bot_detection_threshold": 0.7
                                }

                            # Summary
                            assessment_summary = structured_data.get("summary", "")

                            # Category (from Perplexity)
                            category = structured_data.get("category", "")

                        else:
                            # Fallback to RegEx parsing if structured_data is not available
                            logger.warning(f"[{request_id}] No structured_data available, using fallback regex parsing")
                            category = ""  # Will be determined by keyword matching later

                            # Use typed validation for result content
                            result_content = ResearchTaskValidationMixin.validate_result_content(task_result) or ""
                            if not result_content:
                                logger.warning(f"[{request_id}] No result.content available, cannot parse category from regex")

                            import re

                            # Extract credibility tier
                            tier_match = re.search(r'\*\*Credibility tier:\*\*\s+\*?([a-z_0-9]+)\*?', result_content, re.IGNORECASE)
                            credibility_tier = tier_match.group(1) if tier_match else None

                            # Extract reputation score
                            score_match = re.search(r'\*\*Reputation score.*?:\*\*.*?\*(\d+)(?:-(\d+))?\*', result_content, re.IGNORECASE)
                            reputation_score = int(score_match.group(2) if score_match and score_match.group(2) else score_match.group(1)) if score_match else None

                            # Extract founded year
                            year_match = re.search(r'\*\*Founded year:\*\*\s+\*?(\d{4})\*?', result_content, re.IGNORECASE)
                            founded_year = int(year_match.group(1)) if year_match else None

                            # Extract organization type
                            org_match = re.search(r'\*\*Organization type:\*\*\s+\*?([a-z_]+)\*?', result_content, re.IGNORECASE)
                            organization_type = org_match.group(1).lower() if org_match else None

                            # Extract political bias
                            bias_match = re.search(r'\*\*Political bias:\*\*\s+\*([^*]+)\*', result_content, re.IGNORECASE)
                            if bias_match:
                                bias_text = bias_match.group(1).strip()
                                if ' to ' in bias_text:
                                    bias_text = bias_text.split(' to ')[0].strip()
                                political_bias = bias_text.replace(' ', '_').replace('-', '_')
                            else:
                                political_bias = None

                            # Extract fact checking level
                            fact_match = re.search(r'\*\*Fact checking level:\*\*\s+\*?(\w+)\*?', result_content, re.IGNORECASE)
                            fact_checking_level = fact_match.group(1) if fact_match else None

                            # Build structured data
                            editorial_standards = {
                                "fact_checking_level": fact_checking_level or "unknown",
                                "corrections_policy": "standard",
                                "source_attribution": "consistent"
                            }

                            trust_ratings = {
                                "media_bias_fact_check": "High" if credibility_tier == "tier_1" else "Medium",
                                "allsides_rating": political_bias or "Unknown",
                                "newsguard_score": reputation_score or 0
                            }

                            recommendation = {
                                "skip_waiting_period": credibility_tier == "tier_1",
                                "initial_quality_boost": 10 if credibility_tier == "tier_1" else 5,
                                "bot_detection_threshold": 0.7
                            }

                            # Get summary
                            summary_match = re.search(r'\*\*Assessment summary:\*\*\s+(.+?)(?:\n\n|\Z)', result_content, re.IGNORECASE | re.DOTALL)
                            assessment_summary = summary_match.group(1).strip() if summary_match else result_content[-500:]

                        # Save to history table
                        history_entry = FeedAssessmentHistory(
                            feed_id=feed_id,
                            assessment_status="completed",
                            assessment_date=datetime.utcnow(),
                            credibility_tier=credibility_tier,
                            reputation_score=reputation_score,
                            founded_year=founded_year,
                            organization_type=organization_type,
                            political_bias=political_bias,
                            editorial_standards=editorial_standards,
                            trust_ratings=trust_ratings,
                            recommendation=recommendation,
                            assessment_summary=assessment_summary,
                        )
                        db.add(history_entry)

                        # Also update feed table for backward compatibility
                        result = await db.execute(select(Feed).where(Feed.id == feed_id))
                        feed = result.scalar_one_or_none()
                        if feed:
                            # Use category from Perplexity if available, otherwise fall back to keyword matching
                            if not category:
                                logger.info(f"[POST-ASSESSMENT] Category not provided by Perplexity, using keyword matching")
                                category = _determine_category(
                                    feed_name=feed_name,
                                    feed_url=feed_url,
                                    organization_type=organization_type or "",
                                    assessment_summary=assessment_summary or ""
                                )
                            else:
                                logger.info(f"[POST-ASSESSMENT] Using category from Perplexity: {category}")

                            feed.assessment_status = "completed"
                            feed.assessment_date = datetime.utcnow()
                            feed.credibility_tier = credibility_tier
                            feed.reputation_score = reputation_score
                            feed.founded_year = founded_year
                            feed.organization_type = organization_type
                            feed.political_bias = political_bias
                            feed.editorial_standards = editorial_standards
                            feed.trust_ratings = trust_ratings
                            feed.recommendation = recommendation
                            feed.assessment_summary = assessment_summary

                            # IMPORTANT: Update description and category on re-assessment
                            # Only update if values are not empty (prevent overwriting existing data)
                            if assessment_summary:
                                feed.description = assessment_summary  # Full description, not truncated
                            else:
                                logger.warning(f"[{request_id}] assessment_summary is empty, keeping existing description")

                            if category:
                                feed.category = category
                            else:
                                logger.warning(f"[{request_id}] category is empty, keeping existing category")

                            logger.info(f"✅ Updated feed {feed_id} with category: {category}")

                        await db.commit()

                        # Record success metric
                        assessment_requests_total.labels(status='success').inc()

        except Exception as e:
            # Log error with full traceback
            import traceback
            logger.error(f"Error during feed assessment: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Mark as failed in history
            history_entry = FeedAssessmentHistory(
                feed_id=feed_id,
                assessment_status="failed",
                assessment_date=datetime.utcnow(),
                assessment_summary=f"Assessment failed: {str(e)}"
            )
            db.add(history_entry)

            # Update feed table
            result = await db.execute(select(Feed).where(Feed.id == feed_id))
            feed = result.scalar_one_or_none()
            if feed:
                feed.assessment_status = "failed"
                feed.assessment_date = datetime.utcnow()

            await db.commit()

            # Record failure metric
            assessment_requests_total.labels(status='failed').inc()

        finally:
            # Always decrement active assessments and record duration
            active_assessments.dec()
            duration = time.time() - start_time
            assessment_duration_seconds.observe(duration)
            logger.info(f"[METRICS] Assessment completed in {duration:.2f}s")


@router.post("/{feed_id}/assess")
async def request_feed_assessment(
    feed_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Trigger a feed source assessment analysis.

    This endpoint:
    1. Validates the feed exists
    2. Marks the assessment as pending
    3. Triggers background task to call research service
    4. Returns immediately

    The research service will analyze the feed source using Perplexity
    and return credibility, bias, trust ratings, etc.
    """
    # Get feed
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    # Mark as pending
    feed.assessment_status = "pending"
    feed.assessment_date = datetime.utcnow()
    await db.commit()

    # Extract auth header for forwarding to research service
    auth_header = request.headers.get("Authorization", "")

    # TEMP: Run synchronously for debugging (normally use background_tasks.add_task)
    logger.info(f"[SYNC DEBUG] Calling trigger_feed_assessment synchronously")
    await trigger_feed_assessment(
        feed_id=feed.id,
        feed_url=feed.url,
        feed_name=feed.name,
        auth_header=auth_header
    )
    logger.info(f"[SYNC DEBUG] trigger_feed_assessment completed")

    return {
        "message": "Assessment completed (sync debug mode)",
        "feed_id": str(feed_id),
        "status": "completed"
    }


@router.get("/{feed_id}/assessment-history")
async def get_assessment_history(
    feed_id: UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_db),
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Get assessment history for a feed.

    Returns the most recent assessments in descending order.
    """
    # Verify feed exists
    result = await db.execute(select(Feed).where(Feed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    # Get assessment history
    history_result = await db.execute(
        select(FeedAssessmentHistory)
        .where(FeedAssessmentHistory.feed_id == feed_id)
        .order_by(FeedAssessmentHistory.assessment_date.desc())
        .limit(limit)
    )
    history = history_result.scalars().all()

    return [
        {
            "id": str(h.id),
            "assessment_status": h.assessment_status,
            "assessment_date": h.assessment_date,
            "credibility_tier": h.credibility_tier,
            "reputation_score": h.reputation_score,
            "founded_year": h.founded_year,
            "organization_type": h.organization_type,
            "political_bias": h.political_bias,
            "editorial_standards": h.editorial_standards,
            "trust_ratings": h.trust_ratings,
            "recommendation": h.recommendation,
            "assessment_summary": h.assessment_summary,
        }
        for h in history
    ]


@router.post("/pre-assess")
async def pre_assess_feed_source(
    url: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Run a pre-assessment of a feed source BEFORE creating the feed.

    This endpoint allows users to assess a feed's credibility and get
    recommendations before actually creating the feed entry. The results
    can be used to pre-fill form fields in the feed creation dialog.

    Args:
        url: The feed URL to assess (e.g., https://example.com/rss)

    Returns:
        Assessment data including:
        - credibility_tier (tier_1/tier_2/tier_3)
        - reputation_score (0-100)
        - organization_type
        - political_bias
        - editorial_standards
        - trust_ratings
        - recommendation (suggested initial settings)
        - assessment_summary
    """
    # Validate JWT token
    from jose import JWTError, jwt
    from app.config import settings

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    import httpx
    import re

    # Extract domain from URL for assessment
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or url

        # Clean domain (remove www. prefix)
        clean_domain = domain
        if clean_domain.startswith('www.'):
            clean_domain = clean_domain[4:]

        # Extract feed name from domain
        feed_name = clean_domain.split('.')[0].title()
    except Exception as e:
        logger.error(f"Failed to parse URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid URL format: {str(e)}")

    research_service_url = os.getenv("RESEARCH_SERVICE_URL", "http://research-service:8000")

    try:
        # Generate unique request ID
        import uuid
        request_id = str(uuid.uuid4())
        logger.info(f"[PRE-ASSESSMENT] Request ID: {request_id} for URL: {url}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Prepare request payload
            request_payload = {
                "request_id": request_id,
                "query": f"Assess the credibility and reliability of {feed_name} news source",
                "research_function": "feed_source_assessment",
                "function_parameters": {
                    "feed_url": url,
                    "feed_name": feed_name,
                    "domain": clean_domain,
                }
            }

            logger.info(f"[{request_id}] Sending POST to {research_service_url}/api/v1/research/")
            logger.info(f"[{request_id}] Payload: {request_payload}")

            # Create research task with forwarded auth token
            response = await client.post(
                f"{research_service_url}/api/v1/research/",
                json=request_payload,
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )

            logger.info(f"[{request_id}] Response status: {response.status_code}")
            response.raise_for_status()

            if response.status_code == 201:
                task_data = response.json()
                task_id = task_data.get("id")

                # Poll for task completion (research tasks can take time)
                import asyncio
                max_polls = 15  # 15 attempts
                poll_interval = 2  # 2 seconds between attempts

                task_response = None
                for attempt in range(max_polls):
                    await asyncio.sleep(poll_interval)

                    task_response = await client.get(
                        f"{research_service_url}/api/v1/research/{task_id}",
                        headers={"Authorization": f"Bearer {credentials.credentials}"}
                    )

                    if task_response.status_code == 200:
                        task_result = task_response.json()
                        task_status = task_result.get("status")

                        logger.info(f"[{request_id}] Poll attempt {attempt + 1}/{max_polls}: status={task_status}")

                        if task_status == "completed":
                            break
                        elif task_status in ["failed", "error"]:
                            error_msg = task_result.get("error", "Unknown error")
                            raise HTTPException(status_code=500, detail=f"Assessment failed: {error_msg}")

                if not task_response or task_response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Failed to retrieve assessment results")

                # Task completed successfully
                task_result = task_response.json()

                # Debug: Log the task result structure
                logger.info(f"[{request_id}] Task result keys: {list(task_result.keys())}")

                # Try to use structured_data first (from Perplexity structured output)
                structured_data = task_result.get("structured_data")

                if structured_data:
                    # Use structured data directly (preferred method)
                    credibility_tier = structured_data.get("credibility_tier")
                    reputation_score = structured_data.get("reputation_score")
                    founded_year = structured_data.get("founded_year")
                    organization_type = structured_data.get("organization_type")
                    political_bias = structured_data.get("political_bias")

                    # Editorial standards
                    editorial_standards = structured_data.get("editorial_standards", {})
                    if not isinstance(editorial_standards, dict):
                        editorial_standards = {
                            "fact_checking_level": "unknown",
                            "corrections_policy": "standard",
                            "source_attribution": "consistent"
                        }

                    # Trust ratings
                    trust_ratings = structured_data.get("trust_ratings", {})
                    if not isinstance(trust_ratings, dict):
                        trust_ratings = {
                            "media_bias_fact_check": "High" if credibility_tier == "tier_1" else "Medium",
                            "allsides_rating": political_bias or "Unknown",
                            "newsguard_score": reputation_score or 0
                        }

                    # Recommendation
                    recommendation = structured_data.get("recommendation", {})
                    if not isinstance(recommendation, dict):
                        recommendation = {
                            "skip_waiting_period": credibility_tier == "tier_1",
                            "initial_quality_boost": 10 if credibility_tier == "tier_1" else 5,
                            "bot_detection_threshold": 0.7
                        }

                    # Summary
                    assessment_summary = structured_data.get("summary", "")

                    # Category (from Perplexity)
                    category = structured_data.get("category", "")

                else:
                    # Fallback to RegEx parsing if structured_data is not available
                    category = ""  # Will be determined by keyword matching later
                    result = task_result.get("result") or {}
                    result_content = result.get("content", "") if isinstance(result, dict) else ""

                    # Extract credibility tier
                    tier_match = re.search(r'\*\*Credibility tier:\*\*\s+\*?([a-z_0-9]+)\*?', result_content, re.IGNORECASE)
                    credibility_tier = tier_match.group(1) if tier_match else None

                    # Extract reputation score
                    score_match = re.search(r'\*\*Reputation score.*?:\*\*.*?\*(\d+)(?:-(\d+))?\*', result_content, re.IGNORECASE)
                    reputation_score = int(score_match.group(2) if score_match and score_match.group(2) else score_match.group(1)) if score_match else None

                    # Extract founded year
                    year_match = re.search(r'\*\*Founded year:\*\*\s+\*?(\d{4})\*?', result_content, re.IGNORECASE)
                    founded_year = int(year_match.group(1)) if year_match else None

                    # Extract organization type
                    org_match = re.search(r'\*\*Organization type:\*\*\s+\*?([a-z_]+)\*?', result_content, re.IGNORECASE)
                    organization_type = org_match.group(1).lower() if org_match else None

                    # Extract political bias
                    bias_match = re.search(r'\*\*Political bias:\*\*\s+\*([^*]+)\*', result_content, re.IGNORECASE)
                    if bias_match:
                        bias_text = bias_match.group(1).strip()
                        if ' to ' in bias_text:
                            bias_text = bias_text.split(' to ')[0].strip()
                        political_bias = bias_text.replace(' ', '_').replace('-', '_')
                    else:
                        political_bias = None

                    # Extract fact checking level
                    fact_match = re.search(r'\*\*Fact checking level:\*\*\s+\*?(\w+)\*?', result_content, re.IGNORECASE)
                    fact_checking_level = fact_match.group(1) if fact_match else None

                    # Build structured data
                    editorial_standards = {
                        "fact_checking_level": fact_checking_level or "unknown",
                        "corrections_policy": "standard",
                        "source_attribution": "consistent"
                    }

                    trust_ratings = {
                        "media_bias_fact_check": "High" if credibility_tier == "tier_1" else "Medium",
                        "allsides_rating": political_bias or "Unknown",
                        "newsguard_score": reputation_score or 0
                    }

                    recommendation = {
                        "skip_waiting_period": credibility_tier == "tier_1",
                        "initial_quality_boost": 10 if credibility_tier == "tier_1" else 5,
                        "bot_detection_threshold": 0.7
                    }

                    # Get summary
                    summary_match = re.search(r'\*\*Assessment summary:\*\*\s+(.+?)(?:\n\n|\Z)', result_content, re.IGNORECASE | re.DOTALL)
                    assessment_summary = summary_match.group(1).strip() if summary_match else result_content[-500:]

                # Use category from Perplexity if available, otherwise fall back to keyword matching
                if not category:
                    logger.info(f"[PRE-ASSESSMENT] Category not provided by Perplexity, using keyword matching")
                    category = _determine_category(
                        feed_name=feed_name,
                        feed_url=url,
                        organization_type=organization_type or "",
                        assessment_summary=assessment_summary or ""
                    )
                else:
                    logger.info(f"[PRE-ASSESSMENT] Using category from Perplexity: {category}")

                # Return assessment data (without saving to DB)
                return {
                    "success": True,
                    "assessment": {
                        "credibility_tier": credibility_tier,
                        "reputation_score": reputation_score,
                        "founded_year": founded_year,
                        "organization_type": organization_type,
                        "political_bias": political_bias,
                        "editorial_standards": editorial_standards,
                        "trust_ratings": trust_ratings,
                        "recommendation": recommendation,
                        "assessment_summary": assessment_summary,
                    },
                    "suggested_values": {
                        "name": feed_name,
                        "description": assessment_summary if assessment_summary else None,  # Send full description
                        "category": category,  # Single category from fixed set
                    }
                }

                raise HTTPException(status_code=500, detail="Failed to retrieve assessment results")

    except httpx.HTTPError as e:
        logger.error(f"[PRE-ASSESSMENT] HTTP error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assess feed source: {str(e)}")
    except Exception as e:
        logger.error(f"[PRE-ASSESSMENT] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during assessment: {str(e)}")


def _determine_category(feed_name: str, feed_url: str, organization_type: str, assessment_summary: str) -> str:
    """
    Determine the feed category from the fixed set based on assessment data.

    Categories:
    - General News: Breite allgemeine Nachrichten (BBC, Reuters, CNN, Aljazeera)
    - Finance & Markets: Börsen, Wirtschaft, Rohstoffe, Devisen
    - Tech & Science: Technologie, Forschung, Innovation
    - Geopolitics & Security: Internationale Politik, Militär, Konflikte
    - Energy & Industry: Energie, Rohstoffe, Infrastruktur
    - Regional / Local: Länderspezifisch oder kontinental
    - Think Tanks / Analysis: Institute, Studien, strategische Analysen
    - Special Interest: Themenportale (z. B. Umwelt, KI, Medien)
    """
    # Combine all text for keyword matching
    combined_text = f"{feed_name} {feed_url} {organization_type} {assessment_summary}".lower()

    # Finance & Markets keywords
    if any(keyword in combined_text for keyword in [
        'bloomberg', 'financial times', 'marketwatch', 'stock', 'market', 'trading',
        'forex', 'currency', 'commodity', 'finance', 'wirtschaft', 'börse', 'investor'
    ]):
        return "Finance & Markets"

    # Tech & Science keywords
    if any(keyword in combined_text for keyword in [
        'tech', 'technology', 'science', 'innovation', 'research', 'wired',
        'ars technica', 'techcrunch', 'ai', 'artificial intelligence', 'computing'
    ]):
        return "Tech & Science"

    # Geopolitics & Security keywords
    if any(keyword in combined_text for keyword in [
        'defense', 'military', 'geopolit', 'security', 'conflict', 'war',
        'foreign affairs', 'international relations', 'diplomacy', 'nato'
    ]):
        return "Geopolitics & Security"

    # Energy & Industry keywords
    if any(keyword in combined_text for keyword in [
        'energy', 'oil', 'gas', 'oilprice', 'petroleum', 'renewable',
        'infrastructure', 'industry', 'manufacturing', 'rohstoff'
    ]):
        return "Energy & Industry"

    # Think Tanks / Analysis keywords
    if any(keyword in combined_text for keyword in [
        'brookings', 'rand', 'think tank', 'institute', 'study', 'research center',
        'analysis', 'policy', 'strategic', 'iiss', 'csis'
    ]):
        return "Think Tanks / Analysis"

    # Regional / Local keywords
    if any(keyword in combined_text for keyword in [
        'abc australia', 'allafrica', 'euronews', 'regional', 'continental',
        'africa', 'asia', 'europe', 'latin america', 'middle east'
    ]):
        return "Regional / Local"

    # Special Interest keywords
    if any(keyword in combined_text for keyword in [
        'mit tech review', 'nature', 'environment', 'climate', 'sustainability',
        'media', 'journalism', 'special interest', 'themen'
    ]):
        return "Special Interest"

    # Default to General News if no specific category matches
    return "General News"

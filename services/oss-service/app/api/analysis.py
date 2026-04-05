"""
API routes for OSS analysis operations.

Issue #3: Rate limiting added to prevent abuse.
"""
import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from datetime import datetime
import uuid
import httpx

from app.database import Neo4jConnection, get_neo4j
from app.analyzers.pattern_detector import PatternDetector
from app.analyzers.inconsistency_detector import InconsistencyDetector
from app.models.proposal import AnalysisResult, OntologyChangeProposal
from app.config import settings
from app.core.rate_limiting import limiter, RateLimits
from app.core.deduplication import deduplicator
from app.core.proposal_queue import proposal_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])

# Issue #3: Analysis lock to prevent concurrent runs
_analysis_lock = asyncio.Lock()


async def submit_proposal_to_api(
    proposal: OntologyChangeProposal,
    queue_on_failure: bool = True
) -> bool:
    """
    Submit proposal to Ontology Proposals API.

    Issue #8: Graceful degradation - queues proposal on failure.

    Args:
        proposal: Proposal to submit
        queue_on_failure: Whether to queue for retry on failure

    Returns:
        True if successful, False otherwise
    """
    error_message = None

    try:
        url = f"{settings.PROPOSALS_API_URL}/api/v1/ontology/proposals"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=proposal.model_dump(mode="json"),
                timeout=10.0
            )

            if response.status_code == 201:
                logger.info(f"Submitted proposal {proposal.proposal_id} successfully")
                return True
            else:
                error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(f"Failed to submit proposal: {error_message}")

    except httpx.ConnectError as e:
        error_message = f"Connection error: {str(e)}"
        logger.error(f"Proposals API unavailable: {e}")

    except httpx.TimeoutException as e:
        error_message = f"Timeout: {str(e)}"
        logger.error(f"Proposals API timeout: {e}")

    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(f"Error submitting proposal: {e}", exc_info=True)

    # Issue #8: Queue for retry on failure
    if queue_on_failure and error_message:
        await proposal_queue.enqueue(proposal, error_message)

    return False


async def run_analysis_cycle(neo4j: Neo4jConnection) -> AnalysisResult:
    """
    Run one complete analysis cycle.

    Args:
        neo4j: Neo4j connection

    Returns:
        AnalysisResult with generated proposals
    """
    cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    result = AnalysisResult(cycle_id=cycle_id)

    try:
        logger.info(f"Starting analysis cycle {cycle_id}")

        # Initialize analyzers
        pattern_detector = PatternDetector(neo4j)
        inconsistency_detector = InconsistencyDetector(neo4j)

        # 1. Pattern Detection
        logger.info("Running pattern detection...")
        entity_patterns = await pattern_detector.detect_entity_patterns()
        relationship_patterns = await pattern_detector.detect_relationship_patterns()
        result.patterns_detected = len(entity_patterns) + len(relationship_patterns)

        # 2. Inconsistency Detection
        logger.info("Running inconsistency detection...")
        iso_violations = await inconsistency_detector.detect_iso_code_violations()
        duplicates = await inconsistency_detector.detect_duplicate_entities()
        missing_props = await inconsistency_detector.detect_missing_required_properties()
        unknown_entities = await inconsistency_detector.detect_unknown_entity_types()
        article_entities = await inconsistency_detector.detect_article_entities()
        result.inconsistencies_detected = (
            len(iso_violations) +
            len(duplicates) +
            len(missing_props) +
            len(unknown_entities) +
            len(article_entities)
        )

        # 3. Collect all proposals
        all_proposals = (
            entity_patterns +
            relationship_patterns +
            iso_violations +
            duplicates +
            missing_props +
            unknown_entities +
            article_entities
        )

        # 4. Filter by confidence threshold
        filtered_proposals = [
            p for p in all_proposals
            if p.confidence >= settings.CONFIDENCE_THRESHOLD
        ]

        result.proposals_generated = len(filtered_proposals)

        # 5. Deduplicate proposals (Issue #4)
        unique_proposals = []
        duplicates_skipped = 0

        for proposal in filtered_proposals:
            is_duplicate = await deduplicator.is_duplicate(proposal)
            if not is_duplicate:
                unique_proposals.append(proposal)
            else:
                duplicates_skipped += 1

        if duplicates_skipped > 0:
            logger.info(f"Skipped {duplicates_skipped} duplicate proposals")

        result.duplicates_skipped = duplicates_skipped
        result.proposals = unique_proposals

        # 6. Submit unique proposals to API
        logger.info(f"Submitting {len(unique_proposals)} unique proposals to API...")
        for proposal in unique_proposals:
            success = await submit_proposal_to_api(proposal)
            if success:
                result.proposals_submitted += 1
                # Mark as submitted for future deduplication
                await deduplicator.mark_submitted(proposal)

        result.completed_at = datetime.now()

        logger.info(
            f"Analysis cycle {cycle_id} completed: "
            f"{result.patterns_detected} patterns, "
            f"{result.inconsistencies_detected} inconsistencies, "
            f"{result.proposals_generated} proposals generated, "
            f"{result.proposals_submitted} proposals submitted"
        )

        return result

    except Exception as e:
        logger.error(f"Analysis cycle {cycle_id} failed: {e}", exc_info=True)
        result.errors.append(str(e))
        result.completed_at = datetime.now()
        return result


@router.post("/run", response_model=AnalysisResult)
@limiter.limit(RateLimits.ANALYSIS)
async def trigger_analysis(
    request: Request,
    background_tasks: BackgroundTasks,
    neo4j: Neo4jConnection = Depends(get_neo4j)
):
    """
    Trigger an OSS analysis cycle.

    This endpoint runs a complete analysis cycle:
    1. Pattern detection (new entity/relationship types)
    2. Inconsistency detection (data quality issues)
    3. Proposal generation
    4. Submission to Ontology Proposals API

    **Rate Limit:** 5 requests per minute (analysis is resource-intensive)

    Returns:
        AnalysisResult with generated proposals

    Raises:
        HTTPException 409: If another analysis is already running
        HTTPException 429: If rate limit exceeded
    """
    # Issue #3: Prevent concurrent analysis runs
    if _analysis_lock.locked():
        logger.warning("Analysis trigger rejected: another analysis is already running")
        raise HTTPException(
            status_code=409,
            detail="Analysis already in progress. Please wait for the current cycle to complete."
        )

    logger.info("Analysis cycle triggered via API")

    async with _analysis_lock:
        # Run analysis
        result = await run_analysis_cycle(neo4j)

    return result


@router.get("/status")
@limiter.limit(RateLimits.STATUS)
async def get_status(request: Request, neo4j: Neo4jConnection = Depends(get_neo4j)):
    """
    Get OSS service status.

    **Rate Limit:** 60 requests per minute

    Returns:
        Service status information including analysis lock status
    """
    return {
        "service": "OSS Service",
        "version": settings.APP_VERSION,
        "status": "operational",
        "neo4j_connected": neo4j.check_connection(),
        "analysis_in_progress": _analysis_lock.locked(),
        "proposals_api": settings.PROPOSALS_API_URL,
        "analysis_interval_seconds": settings.ANALYSIS_INTERVAL_SECONDS,
        "min_pattern_occurrences": settings.MIN_PATTERN_OCCURRENCES,
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
        "deduplication": deduplicator.get_stats()  # Issue #4
    }


@router.get("/deduplication/stats")
@limiter.limit(RateLimits.STATUS)
async def get_deduplication_stats(request: Request):
    """
    Get detailed deduplication cache statistics.

    **Rate Limit:** 60 requests per minute

    Returns:
        Deduplication cache status and statistics
    """
    return {
        "deduplication": deduplicator.get_stats(),
        "description": "Proposal deduplication prevents duplicate proposals across analysis cycles"
    }


@router.post("/deduplication/clear")
@limiter.limit(RateLimits.ANALYSIS)
async def clear_deduplication_cache(request: Request):
    """
    Clear the deduplication cache.

    **Rate Limit:** 5 requests per minute

    Use this to reset deduplication state, allowing previously skipped
    proposals to be submitted again.

    Returns:
        Number of cache entries cleared
    """
    count = await deduplicator.clear_cache()
    logger.info(f"Deduplication cache cleared via API ({count} entries)")
    return {
        "message": "Deduplication cache cleared",
        "entries_cleared": count
    }


# Issue #8: Queue status and retry endpoints

@router.get("/queue/status")
@limiter.limit(RateLimits.STATUS)
async def get_queue_status(request: Request):
    """
    Get proposal retry queue status.

    Issue #8: Shows failed proposal queue state for monitoring.

    **Rate Limit:** 60 requests per minute

    Returns:
        Queue statistics and health status
    """
    return {
        "queue": proposal_queue.get_queue_status(),
        "description": "Retry queue for proposals that failed to submit"
    }


@router.post("/queue/retry")
@limiter.limit(RateLimits.ANALYSIS)
async def trigger_queue_retry(request: Request):
    """
    Manually trigger retry of queued proposals.

    Issue #8: Forces immediate retry of pending proposals.

    **Rate Limit:** 5 requests per minute

    Returns:
        Retry results
    """
    ready = await proposal_queue.get_ready_for_retry()

    if not ready:
        return {
            "message": "No proposals ready for retry",
            "retried": 0,
            "succeeded": 0,
            "failed": 0
        }

    succeeded = 0
    failed = 0

    for queued in ready:
        success = await submit_proposal_to_api(
            queued.proposal,
            queue_on_failure=False  # Don't re-queue during manual retry
        )

        if success:
            await proposal_queue.mark_success(queued)
            succeeded += 1
        else:
            # Re-queue with updated retry count
            await proposal_queue.requeue_failed(
                queued,
                "Manual retry failed"
            )
            failed += 1

    logger.info(f"Manual queue retry: {succeeded} succeeded, {failed} failed")

    return {
        "message": "Queue retry completed",
        "retried": len(ready),
        "succeeded": succeeded,
        "failed": failed
    }


@router.get("/queue/failed")
@limiter.limit(RateLimits.STATUS)
async def get_failed_proposals(request: Request):
    """
    Get list of permanently failed proposals.

    Issue #8: Shows proposals that exceeded retry limit.

    **Rate Limit:** 60 requests per minute

    Returns:
        List of failed proposals
    """
    return {
        "failed_proposals": proposal_queue.get_failed_proposals(),
        "description": "Proposals that exceeded maximum retry attempts"
    }


@router.post("/queue/clear")
@limiter.limit(RateLimits.ANALYSIS)
async def clear_queue(request: Request):
    """
    Clear the retry queue.

    **Rate Limit:** 5 requests per minute

    Returns:
        Number of items cleared
    """
    count = await proposal_queue.clear_queue()
    logger.info(f"Retry queue cleared via API ({count} items)")
    return {
        "message": "Retry queue cleared",
        "items_cleared": count
    }

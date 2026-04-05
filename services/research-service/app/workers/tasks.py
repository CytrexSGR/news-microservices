"""
Celery tasks for Research Service.

These tasks run asynchronously in Celery workers for research processing,
scheduled research, batch operations, cache management, and cost tracking.
"""
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from uuid import UUID

from celery import current_task
from sqlalchemy import select, and_, func

from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.perplexity import perplexity_client
from app.models.research import (
    ResearchTask,
    ResearchCache,
    ResearchRun,
    ResearchTemplate,
    CostTracking
)

logger = logging.getLogger(__name__)


@celery_app.task(
    name="research.research_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def research_task(self, task_id: str) -> Dict[str, Any]:
    """
    Celery task to process a single research task asynchronously.

    Args:
        task_id: ID of the research task to process (integer as string)

    Returns:
        Dictionary with task execution results
    """
    try:
        task_id_int = int(task_id)
        logger.info(f"Starting research task {task_id_int}")

        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(_process_research_task(task_id_int))
            logger.info(f"Research task {task_id_int} completed: {result}")
            return result

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in research task {task_id}: {e}")
        # Retry the task
        raise self.retry(exc=e)


async def _process_research_task(task_id: int) -> Dict[str, Any]:
    """Async helper to process a research task."""
    db = SessionLocal()
    try:
        # Get task
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": "Task not found"}

        # Update status
        task.status = "processing"
        db.commit()

        # Check cache first
        cache_hit = _check_cache(task.query, task.model_name, task.depth, db)
        if cache_hit:
            logger.info(f"Cache hit for task {task_id}")

            # Parse structured data from cached result
            structured_data = None
            result = cache_hit["result"]
            if result.get("content"):
                try:
                    import json
                    import re
                    content = result["content"]

                    # Handle double-encoded JSON (Postgres stores as JSON field)
                    if isinstance(content, str):
                        # First parse to unwrap outer quotes if present
                        unwrapped = json.loads(content) if content.strip().startswith('"') else content

                        # If still a string, check for markdown code blocks
                        if isinstance(unwrapped, str):
                            # Extract JSON from markdown code blocks: ```json\n{...}\n```
                            match = re.search(r'```(?:json)?\s*\n(\{.*?\})\s*\n```', unwrapped, re.DOTALL)
                            if match:
                                unwrapped = match.group(1)

                            structured_data = json.loads(unwrapped)
                        else:
                            structured_data = unwrapped
                        logger.info(f"Parsed structured_data from cache for task {task_id}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse structured data from cache for task {task_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error parsing structured data from cache for task {task_id}: {e}")

            task.status = "completed"
            task.result = cache_hit["result"]
            task.structured_data = structured_data
            task.tokens_used = cache_hit["tokens_used"]
            task.cost = cache_hit["cost"]
            task.completed_at = datetime.utcnow()
            db.commit()

            return {
                "status": "success",
                "task_id": str(task_id),
                "cache_hit": True,
                "celery_task_id": current_task.request.id,
            }

        # Perform research via Perplexity API
        # Use structured research if output_schema is present
        if task.output_schema:
            logger.info(f"Task {task_id} has output_schema, using structured JSON mode")
            try:
                import json

                # Build response_format from output_schema
                response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_output",
                        "schema": task.output_schema,
                        "strict": True
                    }
                }

                logger.info(f"Task {task_id}: Calling Perplexity with response_format for structured JSON")
                result = await perplexity_client.research(
                    task.query,
                    task.model_name,
                    task.depth,
                    response_format=response_format
                )

                # With response_format, Perplexity should return valid JSON directly
                structured_data = None
                if result.get("content"):
                    try:
                        import re
                        content = result["content"]

                        # response_format mode: Content should be valid JSON already
                        if isinstance(content, dict):
                            # Already parsed as dict - perfect!
                            structured_data = content
                            logger.info(f"Received structured_data as dict from Perplexity for task {task_id}")
                        elif isinstance(content, str):
                            # Try direct JSON parse first (should work with response_format)
                            try:
                                structured_data = json.loads(content)
                                logger.info(f"Parsed structured_data directly from JSON string for task {task_id}")
                            except json.JSONDecodeError:
                                # Fallback: Extract from markdown or find JSON in text
                                logger.warning(f"response_format didn't return pure JSON for task {task_id}, using fallback parsing")
                                # Method 1: Extract from markdown code blocks
                                match = re.search(r'```(?:json)?\s*\n(\{.*?\})\s*\n```', content, re.DOTALL)
                                if match:
                                    structured_data = json.loads(match.group(1))
                                    logger.info(f"Extracted JSON from markdown code block for task {task_id}")
                                else:
                                    # Method 2: Find first complete JSON object
                                    brace_count = 0
                                    start_idx = content.find('{')
                                    if start_idx != -1:
                                        for i in range(start_idx, len(content)):
                                            if content[i] == '{':
                                                brace_count += 1
                                            elif content[i] == '}':
                                                brace_count -= 1
                                                if brace_count == 0:
                                                    json_str = content[start_idx:i+1]
                                                    structured_data = json.loads(json_str)
                                                    logger.info(f"Extracted JSON object from text for task {task_id}")
                                                    break
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse structured data for task {task_id}: {e}. Content preview: {str(content)[:200]}")
                    except Exception as e:
                        logger.error(f"Unexpected error parsing structured data for task {task_id}: {e}")

            except Exception as e:
                logger.error(f"Structured research failed for task {task_id}: {e}")
                # Fall back to regular research
                result = await perplexity_client.research(
                    task.query,
                    task.model_name,
                    task.depth
                )
                structured_data = None
        else:
            # Regular unstructured research
            result = await perplexity_client.research(
                task.query,
                task.model_name,
                task.depth
            )

            # Try to parse structured data from JSON response
            structured_data = None
            if result.get("content"):
                try:
                    import json
                    import re
                    # Perplexity returns JSON in content field for structured output
                    content = result["content"]

                    # Handle double-encoded JSON (Postgres stores as JSON field)
                    if isinstance(content, str):
                        # First parse to unwrap outer quotes if present
                        unwrapped = json.loads(content) if content.strip().startswith('"') else content

                        # If still a string, check for markdown code blocks
                        if isinstance(unwrapped, str):
                            # Extract JSON from markdown code blocks: ```json\n{...}\n```
                            match = re.search(r'```(?:json)?\s*\n(\{.*?\})\s*\n```', unwrapped, re.DOTALL)
                            if match:
                                unwrapped = match.group(1)

                            structured_data = json.loads(unwrapped)
                        else:
                            structured_data = unwrapped
                        logger.info(f"Parsed structured_data for task {task_id}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse structured data for task {task_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error parsing structured data for task {task_id}: {e}")

        # Update task with results
        task.status = "completed"
        task.result = result
        task.structured_data = structured_data
        task.tokens_used = result.get("tokens_used", 0)
        task.cost = result.get("cost", 0.0)
        task.completed_at = datetime.utcnow()
        db.commit()

        # Cache the result
        _cache_result(task.query, task.model_name, task.depth, result, db)

        # Track cost
        _track_cost(task, db)

        logger.info(f"Task {task_id} completed successfully")
        return {
            "status": "success",
            "task_id": str(task_id),
            "tokens_used": task.tokens_used,
            "cost": task.cost,
            "cache_hit": False,
            "celery_task_id": current_task.request.id,
        }

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()
        raise

    finally:
        db.close()


@celery_app.task(
    name="research.scheduled_research_task",
    bind=True,
    max_retries=1,
)
def scheduled_research_task(self) -> Dict[str, Any]:
    """
    Celery task to process scheduled research runs.

    This task runs periodically (every 15 minutes) to check for and execute
    scheduled research runs.

    Returns:
        Dictionary with execution results
    """
    try:
        logger.info("Starting scheduled research task")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(_process_scheduled_research())
            logger.info(f"Scheduled research task completed: {results}")
            return results
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in scheduled research task: {e}")
        raise


async def _process_scheduled_research() -> Dict[str, Any]:
    """Async helper to process scheduled research runs."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Find scheduled runs that are due
        runs = db.query(ResearchRun).filter(
            and_(
                ResearchRun.status == "pending",
                ResearchRun.scheduled_at <= now
            )
        ).all()

        logger.info(f"Found {len(runs)} scheduled research runs to process")

        results = {
            "total_runs": len(runs),
            "processed": 0,
            "failed": 0,
            "run_results": [],
        }

        for run in runs:
            try:
                # Update run status
                run.status = "running"
                run.started_at = datetime.utcnow()
                db.commit()

                # Get template
                template = db.query(ResearchTemplate).filter(
                    ResearchTemplate.id == run.template_id
                ).first()

                if not template:
                    raise ValueError(f"Template {run.template_id} not found")

                # Apply parameters to template
                query = template.query_template
                for key, value in run.parameters.items():
                    query = query.replace(f"{{{key}}}", str(value))

                # Create research task
                task = ResearchTask(
                    user_id=run.user_id,
                    query=query,
                    model_name=run.model_name,
                    depth=run.depth,
                    run_id=run.id,
                    status="pending"
                )
                db.add(task)
                db.commit()

                # Queue research task
                research_task.delay(str(task.id))

                run.tasks_created += 1
                db.commit()

                results["processed"] += 1
                results["run_results"].append({
                    "run_id": run.id,
                    "success": True,
                    "task_id": task.id,
                })

                # Update template usage
                template.usage_count += 1
                template.last_used_at = datetime.utcnow()
                db.commit()

            except Exception as e:
                logger.error(f"Failed to process run {run.id}: {e}")
                run.status = "failed"
                run.error_message = str(e)
                run.completed_at = datetime.utcnow()
                db.commit()

                results["failed"] += 1
                results["run_results"].append({
                    "run_id": run.id,
                    "success": False,
                    "error": str(e),
                })

        return results

    finally:
        db.close()


@celery_app.task(
    name="research.batch_research_task",
    bind=True,
)
def batch_research_task(self, task_ids: List[str]) -> Dict[str, Any]:
    """
    Celery task to process multiple research tasks in batch.

    Args:
        task_ids: List of research task IDs to process

    Returns:
        Dictionary with batch execution results
    """
    try:
        logger.info(f"Starting batch research for {len(task_ids)} tasks")

        results = []
        for task_id in task_ids:
            result = research_task.delay(task_id)
            results.append({
                "task_id": task_id,
                "celery_task_id": result.id,
            })

        return {
            "status": "success",
            "task_count": len(task_ids),
            "celery_tasks": results,
        }

    except Exception as e:
        logger.error(f"Batch research failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


@celery_app.task(
    name="research.cache_cleanup_task",
    bind=True,
    max_retries=1,
)
def cache_cleanup_task(self) -> Dict[str, Any]:
    """
    Celery task to clean up expired cache entries.

    This task removes cache entries that have exceeded their expiration time
    to prevent the database from growing indefinitely.

    Returns:
        Dictionary with cleanup results
    """
    try:
        logger.info("Starting cache cleanup task")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(_cleanup_expired_cache())
            logger.info(f"Cache cleanup task completed: {results}")
            return results
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in cache cleanup task: {e}")
        raise


async def _cleanup_expired_cache() -> Dict[str, Any]:
    """Async helper to clean up expired cache entries."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Count expired entries
        expired_count = db.query(ResearchCache).filter(
            ResearchCache.expires_at < now
        ).count()

        if expired_count > 0:
            # Delete expired entries
            deleted = db.query(ResearchCache).filter(
                ResearchCache.expires_at < now
            ).delete()

            db.commit()

            logger.info(f"Cleaned up {deleted} expired cache entries")
            return {
                "status": "success",
                "deleted": deleted,
                "timestamp": now.isoformat(),
            }
        else:
            logger.info("No expired cache entries found")
            return {
                "status": "success",
                "deleted": 0,
                "timestamp": now.isoformat(),
            }

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }

    finally:
        db.close()


@celery_app.task(
    name="research.cost_aggregation_task",
    bind=True,
    max_retries=1,
)
def cost_aggregation_task(self) -> Dict[str, Any]:
    """
    Celery task to aggregate daily cost summaries.

    This task runs daily to aggregate cost data by user and model,
    providing daily summaries for reporting and billing.

    Returns:
        Dictionary with aggregation results
    """
    try:
        logger.info("Starting cost aggregation task")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(_aggregate_daily_costs())
            logger.info(f"Cost aggregation task completed: {results}")
            return results
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in cost aggregation task: {e}")
        raise


async def _aggregate_daily_costs() -> Dict[str, Any]:
    """Async helper to aggregate daily costs."""
    db = SessionLocal()
    try:
        # Get yesterday's date range
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)

        # Aggregate costs by user and model for yesterday
        aggregates = db.query(
            ResearchTask.user_id,
            ResearchTask.model_name,
            func.sum(ResearchTask.tokens_used).label('total_tokens'),
            func.sum(ResearchTask.cost).label('total_cost'),
            func.count(ResearchTask.id).label('request_count')
        ).filter(
            and_(
                ResearchTask.created_at >= yesterday,
                ResearchTask.created_at < today,
                ResearchTask.status == "completed"
            )
        ).group_by(
            ResearchTask.user_id,
            ResearchTask.model_name
        ).all()

        logger.info(f"Found {len(aggregates)} cost aggregates for {yesterday.date()}")

        # Store aggregates
        for agg in aggregates:
            cost_tracking = CostTracking(
                user_id=agg.user_id,
                date=yesterday,
                model_name=agg.model_name,
                tokens_used=agg.total_tokens or 0,
                cost=agg.total_cost or 0.0,
                request_count=agg.request_count or 0,
            )
            db.add(cost_tracking)

        db.commit()

        total_cost = sum(agg.total_cost or 0.0 for agg in aggregates)
        total_tokens = sum(agg.total_tokens or 0 for agg in aggregates)

        return {
            "status": "success",
            "date": yesterday.date().isoformat(),
            "aggregates_created": len(aggregates),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
        }

    except Exception as e:
        logger.error(f"Cost aggregation failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }

    finally:
        db.close()


@celery_app.task(name="research.health_check")
def health_check_task() -> Dict[str, Any]:
    """Simple health check task for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "research-service-celery",
    }


# Helper functions
def _check_cache(query: str, model_name: str, depth: str, db) -> Dict[str, Any]:
    """Check if result exists in cache."""
    import hashlib

    # Generate cache key
    cache_key = hashlib.sha256(
        f"{query}:{model_name}:{depth}".encode()
    ).hexdigest()

    # Check cache
    cache_entry = db.query(ResearchCache).filter(
        and_(
            ResearchCache.cache_key == cache_key,
            ResearchCache.expires_at > datetime.utcnow()
        )
    ).first()

    if cache_entry:
        # Update hit count and last accessed
        cache_entry.hit_count += 1
        cache_entry.last_accessed_at = datetime.utcnow()
        db.commit()

        return {
            "result": cache_entry.result,
            "tokens_used": cache_entry.tokens_used,
            "cost": cache_entry.cost,
        }

    return None


def _cache_result(query: str, model_name: str, depth: str, result: Dict[str, Any], db):
    """Cache research result."""
    import hashlib
    from app.core.config import settings

    # Generate cache key
    cache_key = hashlib.sha256(
        f"{query}:{model_name}:{depth}".encode()
    ).hexdigest()

    # Check if already cached
    existing = db.query(ResearchCache).filter(
        ResearchCache.cache_key == cache_key
    ).first()

    if existing:
        # Update existing cache
        existing.result = result
        existing.tokens_used = result.get("tokens_used", 0)
        existing.cost = result.get("cost", 0.0)
        existing.expires_at = datetime.utcnow() + timedelta(
            seconds=settings.CACHE_RESEARCH_RESULTS_TTL
        )
        existing.last_accessed_at = datetime.utcnow()
    else:
        # Create new cache entry
        cache_entry = ResearchCache(
            cache_key=cache_key,
            query=query,
            model_name=model_name,
            depth=depth,
            result=result,
            tokens_used=result.get("tokens_used", 0),
            cost=result.get("cost", 0.0),
            expires_at=datetime.utcnow() + timedelta(
                seconds=settings.CACHE_RESEARCH_RESULTS_TTL
            ),
        )
        db.add(cache_entry)

    db.commit()


def _track_cost(task: ResearchTask, db):
    """Track cost for billing."""
    cost_tracking = CostTracking(
        user_id=task.user_id,
        date=datetime.utcnow(),
        model_name=task.model_name,
        tokens_used=task.tokens_used,
        cost=task.cost,
        task_id=task.id,
        run_id=task.run_id,
    )
    db.add(cost_tracking)
    db.commit()

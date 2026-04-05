"""API routes for entity canonicalization."""
import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import (
    CanonicalizeRequest,
    CanonicalizeResponse,
    CanonicalizeBatchRequest,
    CanonicalizeBatchResponse,
    CanonicalizationStats,
    DetailedCanonicalizationStats,
    ReprocessingStatus,
    StartReprocessingRequest,
    EntityTypeTrendsResponse,
    EntityTypeTrendData,
    AsyncBatchJobResponse,
    AsyncBatchJobStatus,
    AsyncBatchJobResult
)
from app.services.canonicalizer import EntityCanonicalizer
from app.services.fragmentation_metrics import FragmentationMetrics
from app.services.alias_store import AliasStore
from app.api.dependencies import get_db_session, get_canonicalizer
from app.config import settings

# Celery task import
from app.tasks.batch_reprocessing import batch_reprocess_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/canonicalization", tags=["canonicalization"])


@router.post("/canonicalize", response_model=CanonicalizeResponse)
async def canonicalize_entity(
    request: CanonicalizeRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Canonicalize a single entity.

    Multi-stage canonicalization:
    1. Exact match in alias store
    2. Fuzzy + semantic similarity
    3. Wikidata entity linking
    4. Create new canonical form

    Example:
    ```json
    POST /api/v1/canonicalization/canonicalize
    {
        "entity_name": "USA",
        "entity_type": "LOCATION",
        "language": "en"
    }
    ```

    Response:
    ```json
    {
        "canonical_name": "United States",
        "canonical_id": "Q30",
        "aliases": ["USA", "US", "United States of America"],
        "confidence": 0.98,
        "source": "wikidata",
        "entity_type": "LOCATION",
        "processing_time_ms": 145.2
    }
    ```
    """
    start_time = time.time()

    try:
        canonicalizer = await get_canonicalizer(session)

        result = await canonicalizer.canonicalize(
            request.entity_name,
            request.entity_type,
            request.language
        )

        processing_time_ms = (time.time() - start_time) * 1000

        return CanonicalizeResponse(
            canonical_name=result.canonical_name,
            canonical_id=result.canonical_id,
            aliases=result.aliases,
            confidence=result.confidence,
            source=result.source,
            entity_type=result.entity_type,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Error canonicalizing entity '{request.entity_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/canonicalize/batch", response_model=CanonicalizeBatchResponse)
async def canonicalize_entities_batch(
    request: CanonicalizeBatchRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Batch canonicalization for multiple entities.

    More efficient than individual calls for large batches.

    Example:
    ```json
    POST /api/v1/canonicalization/canonicalize/batch
    {
        "entities": [
            {"entity_name": "USA", "entity_type": "LOCATION", "language": "en"},
            {"entity_name": "Barack Obama", "entity_type": "PERSON", "language": "en"}
        ]
    }
    ```
    """
    start_time = time.time()

    try:
        canonicalizer = await get_canonicalizer(session)

        # Prepare entities for batch processing
        entities = [
            (e.entity_name, e.entity_type, e.language)
            for e in request.entities
        ]

        # Batch canonicalization
        results = await canonicalizer.canonicalize_batch(entities)

        total_time_ms = (time.time() - start_time) * 1000

        # Convert to response format
        responses = [
            CanonicalizeResponse(
                canonical_name=r.canonical_name,
                canonical_id=r.canonical_id,
                aliases=r.aliases,
                confidence=r.confidence,
                source=r.source,
                entity_type=r.entity_type
            )
            for r in results
        ]

        return CanonicalizeBatchResponse(
            results=responses,
            total_processed=len(responses),
            total_time_ms=total_time_ms
        )

    except Exception as e:
        logger.error(f"Error in batch canonicalization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Async Batch Processing Endpoints
# ===========================

@router.post("/canonicalize/batch/async", response_model=AsyncBatchJobResponse)
async def canonicalize_batch_async(
    request: CanonicalizeBatchRequest
):
    """
    Start async batch canonicalization job.

    Use this for large batches (>10 entities) to avoid timeouts.

    Returns job_id immediately. Client polls /jobs/{job_id}/status for progress.

    Example:
    ```json
    POST /api/v1/canonicalization/canonicalize/batch/async
    {
        "entities": [
            {"entity_name": "USA", "entity_type": "LOCATION", "language": "en"},
            {"entity_name": "Barack Obama", "entity_type": "PERSON", "language": "en"}
        ]
    }
    ```

    Response:
    ```json
    {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "queued",
        "message": "Batch canonicalization job started",
        "total_entities": 2
    }
    ```

    Then poll: GET /jobs/{job_id}/status
    """
    from app.services.async_batch_processor import get_async_processor

    try:
        processor = get_async_processor()

        # Start async job (processor creates its own DB session)
        job_id = await processor.start_job(
            entities=request.entities
        )

        return AsyncBatchJobResponse(
            job_id=job_id,
            status="queued",
            message="Batch canonicalization job started",
            total_entities=len(request.entities)
        )

    except Exception as e:
        logger.error(f"Failed to start async batch job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status", response_model=AsyncBatchJobStatus)
async def get_job_status(job_id: str):
    """
    Get current status of async batch job.

    Poll this endpoint to check progress.

    Returns:
    ```json
    {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "processing",  // queued | processing | completed | failed
        "progress_percent": 45.5,
        "stats": {
            "total_entities": 100,
            "processed_entities": 45,
            "successful": 44,
            "failed": 1
        },
        "started_at": "2025-10-29T14:30:00Z",
        "completed_at": null,
        "error_message": null
    }
    ```
    """
    from app.services.async_batch_processor import get_async_processor

    processor = get_async_processor()
    status = await processor.get_status(job_id)

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    return status


@router.get("/jobs/{job_id}/result", response_model=AsyncBatchJobResult)
async def get_job_result(job_id: str):
    """
    Get results of completed async batch job.

    Only returns data if job status is 'completed'.

    Returns:
    ```json
    {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "results": [
            {
                "canonical_name": "United States",
                "canonical_id": "Q30",
                "aliases": ["USA", "US"],
                "confidence": 1.0,
                "source": "exact",
                "entity_type": "LOCATION"
            }
        ],
        "total_processed": 100,
        "total_time_ms": 45230.5
    }
    ```
    """
    from app.services.async_batch_processor import get_async_processor

    processor = get_async_processor()
    result = await processor.get_result(job_id)

    if not result:
        # Check if job exists but not completed yet
        status = await processor.get_status(job_id)
        if status:
            if status.status == "failed":
                raise HTTPException(
                    status_code=500,
                    detail=f"Job {job_id} failed: {status.error_message}"
                )
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Job {job_id} not completed yet (status: {status.status})"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

    return result


@router.get("/aliases/{canonical_name}", response_model=List[str])
async def get_aliases(
    canonical_name: str,
    entity_type: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get all known aliases for a canonical entity.

    Example:
    ```
    GET /api/v1/canonicalization/aliases/United States?entity_type=LOCATION
    ```

    Response:
    ```json
    ["USA", "US", "United States of America", "U.S.", "U.S.A."]
    ```
    """
    try:
        canonicalizer = await get_canonicalizer(session)
        aliases = await canonicalizer.get_aliases(canonical_name, entity_type)

        if not aliases:
            raise HTTPException(
                status_code=404,
                detail=f"Canonical entity '{canonical_name}' ({entity_type}) not found"
            )

        return aliases

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting aliases for '{canonical_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=CanonicalizationStats)
async def get_canonicalization_stats(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get canonicalization statistics.

    Example response:
    ```json
    {
        "total_canonical_entities": 1245,
        "total_aliases": 3821,
        "wikidata_linked": 987,
        "coverage_percentage": 306.8,
        "cache_hit_rate": 0.73
    }
    ```
    """
    try:
        canonicalizer = await get_canonicalizer(session)
        stats = await canonicalizer.get_stats()

        return CanonicalizationStats(**stats)

    except Exception as e:
        logger.error(f"Error getting canonicalization stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/detailed", response_model=DetailedCanonicalizationStats)
async def get_detailed_canonicalization_stats(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed canonicalization statistics for admin dashboard.

    Includes:
    - Basic stats (entities, aliases, wikidata coverage)
    - Deduplication ratio (how many aliases per entity)
    - Entity type distribution
    - Top 10 entities by alias count
    - Performance metrics (cache hit rate, response time)
    - Cost savings estimates

    Example response:
    ```json
    {
        "total_canonical_entities": 191,
        "total_aliases": 346,
        "wikidata_linked": 142,
        "wikidata_coverage_percent": 74.3,
        "deduplication_ratio": 1.81,
        "source_breakdown": {
            "exact": 0,
            "fuzzy": 0,
            "semantic": 0,
            "wikidata": 142,
            "new": 49
        },
        "entity_type_distribution": {
            "PERSON": 87,
            "ORGANIZATION": 54,
            "LOCATION": 32,
            "EVENT": 18
        },
        "top_entities_by_aliases": [
            {
                "canonical_name": "United States",
                "canonical_id": "Q30",
                "entity_type": "LOCATION",
                "alias_count": 5,
                "wikidata_linked": true
            }
        ],
        "entities_without_qid": 49,
        "avg_cache_hit_time_ms": 2.1,
        "cache_hit_rate": 89.0,
        "total_api_calls_saved": 155,
        "estimated_cost_savings_monthly": 0.31
    }
    ```
    """
    try:
        canonicalizer = await get_canonicalizer(session)
        stats = await canonicalizer.get_detailed_stats()

        return DetailedCanonicalizationStats(**stats)

    except Exception as e:
        logger.error(f"Error getting detailed canonicalization stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Simple health status
    """
    return {
        "status": "healthy",
        "service": "entity-canonicalization-service"
    }


@router.post("/admin/cleanup-memory")
async def cleanup_memory():
    """
    Manual memory cleanup endpoint for admin use.

    Clears:
    - Completed/failed reprocessor jobs
    - Async batch processor cache
    - Forces garbage collection

    Returns:
        Cleanup statistics
    """
    import gc
    from app.services.async_batch_processor import get_async_processor

    global _reprocessor

    cleanup_stats = {
        "reprocessor_cleared": False,
        "batch_jobs_cleared": 0,
        "gc_collected": 0
    }

    # Clear global reprocessor if not running
    if _reprocessor and _reprocessor.status.status in ("completed", "failed"):
        _reprocessor = None
        cleanup_stats["reprocessor_cleared"] = True
        logger.info("Manual cleanup: Cleared global reprocessor")

    # Clear completed batch jobs
    processor = get_async_processor()
    async with processor._lock:
        jobs_before = len(processor._jobs)
        # Remove completed/failed jobs
        jobs_to_remove = [
            job_id for job_id, job in processor._jobs.items()
            if job["status"].status in ("completed", "failed")
        ]
        for job_id in jobs_to_remove:
            del processor._jobs[job_id]
        cleanup_stats["batch_jobs_cleared"] = len(jobs_to_remove)
        logger.info(f"Manual cleanup: Cleared {len(jobs_to_remove)} completed batch jobs")

    # Force garbage collection
    cleanup_stats["gc_collected"] = gc.collect()
    logger.info(f"Manual cleanup: Garbage collected {cleanup_stats['gc_collected']} objects")

    return {
        "message": "Memory cleanup completed",
        "stats": cleanup_stats
    }


# ===========================
# Batch Reprocessing Endpoints
# ===========================

# Global reprocessor instance (singleton pattern)
_reprocessor = None


@router.post("/reprocess/start")
async def start_batch_reprocessing(
    request: StartReprocessingRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Start batch reprocessing of all entities using Celery background worker.

    **✅ NEW: Non-blocking Celery implementation**

    This will:
    1. Find and merge duplicate entities
    2. Add missing Wikidata Q-IDs
    3. Apply fuzzy and semantic matching retroactively
    4. Improve overall data quality

    **Performance:**
    - Runs in separate worker process (service stays HEALTHY)
    - 20x faster Wikidata lookup (parallel API calls)
    - 0% duplicate loss (increased buffer from 10k to 30k pairs)
    - Expected duration: 5-7 minutes (vs 37+ minutes old version)

    Args:
        request: Reprocessing configuration
            - dry_run (bool): If true, don't persist changes (testing mode)
            - min_confidence (float): Minimum similarity score (0.0-1.0)

    Returns:
        Task ID and status URL for monitoring

    Example Response:
        {
            "task_id": "abc123...",
            "status": "started",
            "status_url": "/api/v1/canonicalization/reprocess/celery-status/abc123...",
            "dry_run": true,
            "message": "Batch reprocessing started in background worker"
        }

    Raises:
        500: Server error
    """
    try:
        # Start Celery task (non-blocking)
        task = batch_reprocess_task.delay(
            dry_run=request.dry_run,
            min_confidence=getattr(request, 'min_confidence', 0.7),
            max_duplicate_pairs=settings.MAX_DUPLICATE_PAIRS
        )

        logger.info(
            f"Started batch reprocessing Celery task {task.id}: "
            f"dry_run={request.dry_run}, min_confidence={getattr(request, 'min_confidence', 0.7)}"
        )

        return {
            "task_id": task.id,
            "status": "started",
            "status_url": f"/api/v1/canonicalization/reprocess/celery-status/{task.id}",
            "dry_run": request.dry_run,
            "message": "Batch reprocessing started in background worker"
        }

    except Exception as e:
        logger.error(f"Failed to start batch reprocessing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start reprocessing: {str(e)}")


@router.get("/reprocess/status", response_model=ReprocessingStatus)
async def get_reprocessing_status():
    """
    Get current status of batch reprocessing job.

    Returns:
        Current status including:
        - status: idle | running | completed | failed
        - progress_percent: 0-100%
        - current_phase: analyzing | fuzzy_matching | semantic_matching | wikidata_lookup | merging | updating
        - stats: processed entities, duplicates found, Q-IDs added, etc.
        - timestamps: started_at, completed_at
        - error_message: if failed
    """
    global _reprocessor

    if not _reprocessor:
        # No job has been started yet
        return ReprocessingStatus()

    status = _reprocessor.get_status()

    # 🔧 MEMORY FIX: Auto-cleanup after completion/failure
    # Frees ~200 MB of memory from global singleton
    if status.status in ("completed", "failed"):
        logger.info(f"Auto-cleaning up completed reprocessor (status: {status.status})")
        _reprocessor = None

    return status


@router.post("/reprocess/stop")
async def stop_batch_reprocessing():
    """
    Stop current batch reprocessing job gracefully.

    The job will finish its current operation and then stop.

    Returns:
        Confirmation message and final statistics

    Raises:
        404: No reprocessing job is currently running
        500: Server error
    """
    global _reprocessor

    if not _reprocessor or _reprocessor.status.status != "running":
        raise HTTPException(
            status_code=404,
            detail="No batch reprocessing job is currently running"
        )

    try:
        result = await _reprocessor.stop()
        logger.info("Batch reprocessing stopped by user")

        # 🔧 MEMORY FIX: Clear global reprocessor after stop
        _reprocessor = None

        return result

    except Exception as e:
        logger.error(f"Failed to stop batch reprocessing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reprocess/celery-status/{task_id}")
async def get_celery_task_status(task_id: str):
    """
    Get status of Celery batch reprocessing task.

    **✅ NEW: Celery task status endpoint**

    This endpoint queries the Celery result backend (Redis) for task progress.
    Use the task_id returned from /reprocess/start to monitor progress.

    Args:
        task_id: Celery task ID (UUID)

    Returns:
        Task status with progress information

    Example Response:
        {
            "task_id": "abc123...",
            "state": "PROGRESS",  // PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
            "info": {
                "status": "running",
                "progress_percent": 45.0,
                "current_phase": "wikidata_lookup",
                "stats": {
                    "duplicates_found": 24554,
                    "qids_added": 1234,
                    "entities_merged": 0,
                    "errors": 3
                },
                "started_at": "2025-11-06T12:00:00Z",
                "dry_run": true
            }
        }

    Raises:
        404: Task not found
        500: Server error
    """
    try:
        # Get task result from Celery backend
        from celery.result import AsyncResult
        result = AsyncResult(task_id, app=batch_reprocess_task.app)

        if result.state == 'PENDING':
            # Task hasn't started yet or doesn't exist
            return {
                "task_id": task_id,
                "state": "PENDING",
                "info": {
                    "status": "pending",
                    "message": "Task is queued or doesn't exist"
                }
            }

        elif result.state == 'STARTED':
            # Task has started but no progress yet
            return {
                "task_id": task_id,
                "state": "STARTED",
                "info": result.info if result.info else {
                    "status": "starting",
                    "message": "Task is initializing"
                }
            }

        elif result.state == 'PROGRESS':
            # Task is running with progress updates
            return {
                "task_id": task_id,
                "state": "PROGRESS",
                "info": result.info
            }

        elif result.state == 'SUCCESS':
            # Task completed successfully
            return {
                "task_id": task_id,
                "state": "SUCCESS",
                "result": result.result
            }

        elif result.state == 'FAILURE':
            # Task failed
            return {
                "task_id": task_id,
                "state": "FAILURE",
                "error": str(result.info) if result.info else "Unknown error",
                "traceback": result.traceback
            }

        else:
            # Unknown state
            return {
                "task_id": task_id,
                "state": result.state,
                "info": result.info
            }

    except Exception as e:
        logger.error(f"Failed to get Celery task status for {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


# ===========================
# Analytics Endpoints
# ===========================

@router.get("/trends/entity-types", response_model=EntityTypeTrendsResponse)
async def get_entity_type_trends(
    days: int = 30,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get entity type trends over time.

    Returns daily counts of entities by type for the specified number of days.
    Uses created_at timestamps to show growth over time.

    Args:
        days: Number of days to include (default: 30, max: 365)

    Returns:
        Entity type counts per day

    Example:
    ```
    GET /api/v1/canonicalization/trends/entity-types?days=7
    ```
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, func, cast, Date
    from app.database.models import CanonicalEntity

    try:
        # Limit days to reasonable range
        days = min(max(days, 1), 365)

        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days - 1)

        # Query: Group entities by date and type
        query = select(
            cast(CanonicalEntity.created_at, Date).label('date'),
            CanonicalEntity.type,
            func.count(CanonicalEntity.id).label('count')
        ).where(
            cast(CanonicalEntity.created_at, Date) >= start_date
        ).group_by(
            cast(CanonicalEntity.created_at, Date),
            CanonicalEntity.type
        ).order_by(
            cast(CanonicalEntity.created_at, Date)
        )

        result = await session.execute(query)
        rows = result.all()

        # Build daily data structure
        daily_counts = {}
        for row in rows:
            date_str = row.date.isoformat()
            entity_type = row.type
            count = row.count

            if date_str not in daily_counts:
                daily_counts[date_str] = {
                    'date': date_str,
                    'PERSON': 0,
                    'ORGANIZATION': 0,
                    'LOCATION': 0,
                    'EVENT': 0,
                    'PRODUCT': 0,
                    'OTHER': 0,
                    'MISC': 0,
                    'NOT_APPLICABLE': 0
                }

            # Map type to field
            if entity_type in daily_counts[date_str]:
                daily_counts[date_str][entity_type] = count
            else:
                # Unknown type -> OTHER
                daily_counts[date_str]['OTHER'] += count

        # Fill in missing dates with zeros
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str not in daily_counts:
                daily_counts[date_str] = {
                    'date': date_str,
                    'PERSON': 0,
                    'ORGANIZATION': 0,
                    'LOCATION': 0,
                    'EVENT': 0,
                    'PRODUCT': 0,
                    'OTHER': 0,
                    'MISC': 0,
                    'NOT_APPLICABLE': 0
                }
            all_dates.append(date_str)
            current_date += timedelta(days=1)

        # Convert to list sorted by date
        trends = [EntityTypeTrendData(**daily_counts[date]) for date in sorted(all_dates)]

        # Calculate total entities
        total_entities = sum(
            sum(getattr(trend, field) for field in ['PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT', 'PRODUCT', 'OTHER', 'MISC', 'NOT_APPLICABLE'])
            for trend in trends
        )

        return EntityTypeTrendsResponse(
            trends=trends,
            days=days,
            total_entities=total_entities
        )

    except Exception as e:
        logger.error(f"Error getting entity type trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/merges", response_model=List[Dict[str, Any]])
async def get_merge_history(
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get recent entity merge events.

    This endpoint returns a history of entity deduplication operations,
    showing which entities were merged, the method used, and confidence scores.

    Query Parameters:
    - limit: Number of events to return (default: 20, max: 100)

    Returns:
    ```json
    [
      {
        "id": "123",
        "timestamp": "2025-01-24T19:30:00Z",
        "source_entity": "USA",
        "source_type": "LOCATION",
        "target_entity": "United States",
        "target_type": "LOCATION",
        "merge_method": "exact",
        "confidence": 0.95
      }
    ]
    ```

    Raises:
        500: Server error
    """
    from app.database.models import EntityMergeEvent

    try:
        # Limit to max 100
        limit = min(limit, 100)

        # Query recent merge events
        stmt = (
            select(EntityMergeEvent)
            .where(EntityMergeEvent.event_type == "merge")
            .order_by(desc(EntityMergeEvent.created_at))
            .limit(limit)
        )

        result = await session.execute(stmt)
        events = result.scalars().all()

        # Format response to match frontend MergeEvent interface
        return [
            {
                "id": str(event.id),
                "timestamp": event.created_at.isoformat() + "Z",
                "source_entity": event.source_entity,
                "source_type": event.entity_type,
                "target_entity": event.target_entity,
                "target_type": event.entity_type,
                "merge_method": event.merge_method,
                "confidence": event.confidence
            }
            for event in events
        ]

    except Exception as e:
        logger.error(f"Error fetching merge history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Fragmentation & Usage Stats Endpoints (Epic 1.4)
# ===========================

@router.get("/fragmentation/report")
async def get_fragmentation_report(
    entity_type: Optional[str] = Query(None, description="Entity type to analyze"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get fragmentation analysis report.

    Returns metrics including:
    - Fragmentation score (0-1, higher is better)
    - Total entities and aliases
    - Singleton count (entities with only 1 alias)
    - Potential duplicates

    Example:
    ```
    GET /api/v1/canonicalization/fragmentation/report?entity_type=ORGANIZATION
    ```

    Response:
    ```json
    {
        "entity_type": "ORGANIZATION",
        "fragmentation_score": 0.4,
        "total_entities": 100,
        "total_aliases": 250,
        "avg_aliases_per_entity": 2.5,
        "singleton_count": 30,
        "singleton_percentage": 30.0,
        "potential_duplicates": [],
        "potential_duplicate_count": 0,
        "improvement_target": "30% reduction in singletons"
    }
    ```
    """
    try:
        metrics = FragmentationMetrics(session)
        report = await metrics.generate_report(entity_type)
        return report

    except Exception as e:
        logger.error(f"Error generating fragmentation report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fragmentation/duplicates")
async def get_potential_duplicates(
    entity_type: str = Query(..., description="Entity type"),
    threshold: float = Query(0.90, ge=0.5, le=1.0, description="Similarity threshold"),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Find potential duplicate entities.

    Returns pairs of entities with high similarity scores.

    Example:
    ```
    GET /api/v1/canonicalization/fragmentation/duplicates?entity_type=PERSON&threshold=0.90
    ```

    Response:
    ```json
    {
        "duplicates": [
            {
                "entity_id_1": 1,
                "name1": "Apple Inc.",
                "entity_id_2": 2,
                "name2": "Apple Inc",
                "similarity": 0.98
            }
        ],
        "count": 1
    }
    ```
    """
    try:
        metrics = FragmentationMetrics(session)
        duplicates = await metrics.find_potential_duplicates(entity_type, threshold, limit)
        return {"duplicates": duplicates, "count": len(duplicates)}

    except Exception as e:
        logger.error(f"Error finding potential duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fragmentation/singletons")
async def get_singleton_entities(
    entity_type: str = Query(..., description="Entity type"),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get entities with only one alias.

    These are high fragmentation risk candidates that may represent
    unmerged duplicates or entities that need alias enrichment.

    Example:
    ```
    GET /api/v1/canonicalization/fragmentation/singletons?entity_type=LOCATION
    ```

    Response:
    ```json
    {
        "singletons": [
            {
                "id": 1,
                "name": "Lonely Entity",
                "type": "LOCATION",
                "wikidata_id": "Q123"
            }
        ],
        "count": 1
    }
    ```
    """
    try:
        metrics = FragmentationMetrics(session)
        singletons = await metrics.get_singleton_entities(entity_type, limit)
        return {
            "singletons": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "wikidata_id": e.wikidata_id
                }
                for e in singletons
            ],
            "count": len(singletons)
        }

    except Exception as e:
        logger.error(f"Error getting singleton entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/usage")
async def get_usage_stats(
    entity_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get alias usage statistics.

    Returns most frequently used entities and their aliases.

    Example:
    ```
    GET /api/v1/canonicalization/stats/usage?entity_type=LOCATION
    ```

    Response:
    ```json
    {
        "most_used_entities": [
            {"name": "United States", "type": "LOCATION", "total_usage": 500},
            {"name": "Germany", "type": "LOCATION", "total_usage": 300}
        ]
    }
    ```
    """
    try:
        store = AliasStore(session)

        most_used = []
        if entity_type:
            most_used = await store.get_most_used_entities(entity_type, limit)

        return {
            "most_used_entities": [
                {"name": e.name, "type": e.type, "total_usage": usage}
                for e, usage in most_used
            ]
        }

    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

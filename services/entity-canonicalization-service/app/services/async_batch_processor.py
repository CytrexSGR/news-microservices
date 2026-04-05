"""
Async batch processor for canonicalization jobs.

Handles background processing of large entity batches without blocking API responses.
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from cachetools import TTLCache

from app.services.canonicalizer import EntityCanonicalizer
from app.models.entities import (
    CanonicalizeRequest,
    CanonicalizeResponse,
    AsyncBatchJobStatus,
    AsyncBatchJobStats,
    AsyncBatchJobResult
)

logger = logging.getLogger(__name__)


class AsyncBatchProcessor:
    """
    Handles async batch canonicalization processing.

    Jobs are stored in-memory with job_id as key.
    Each job runs in a background asyncio task.

    Memory Management:
    - LRU Cache with TTL eviction policy
    - Max size: 1000 jobs (prevents unbounded growth)
    - TTL: 3600 seconds (1 hour - auto-cleanup completed jobs)
    - Thread-safe with asyncio.Lock
    """

    def __init__(self):
        from app.config import settings

        # ✅ BOUNDED CACHE: LRU + TTL eviction
        # Replaces unbounded dict to prevent memory leak (was ~1.77 GiB)
        # 🔧 MEMORY FIX: Configurable size and TTL (saves ~150 MB vs old 1000)
        # Uses config values: BATCH_JOB_CACHE_SIZE and BATCH_JOB_TTL
        self._jobs = TTLCache(
            maxsize=settings.BATCH_JOB_CACHE_SIZE,
            ttl=settings.BATCH_JOB_TTL
        )
        self._lock = asyncio.Lock()

    async def start_job(
        self,
        entities: List[CanonicalizeRequest]
    ) -> str:
        """
        Start a new async canonicalization job.

        Args:
            entities: List of entities to canonicalize

        Returns:
            job_id: Unique identifier for this job
        """
        job_id = str(uuid.uuid4())

        # Initialize job status
        async with self._lock:
            self._jobs[job_id] = {
                "status": AsyncBatchJobStatus(
                    job_id=job_id,
                    status="queued",
                    stats=AsyncBatchJobStats(total_entities=len(entities))
                ),
                "entities": entities,
                "results": None,
                "task": None
            }

        # Start background processing (creates its own DB session)
        task = asyncio.create_task(
            self._process_batch(job_id, entities)
        )

        async with self._lock:
            self._jobs[job_id]["task"] = task

        logger.info(f"Started async batch job {job_id} with {len(entities)} entities")
        return job_id

    async def get_status(self, job_id: str) -> Optional[AsyncBatchJobStatus]:
        """
        Get current status of a job.

        Args:
            job_id: Job identifier

        Returns:
            Job status or None if not found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return job["status"]

    async def get_result(self, job_id: str) -> Optional[AsyncBatchJobResult]:
        """
        Get results of a completed job.

        Args:
            job_id: Job identifier

        Returns:
            Job results or None if not found/not completed
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job or job["status"].status != "completed":
                return None
            return job["results"]

    async def cleanup_job(self, job_id: str) -> bool:
        """
        Remove job from memory (call after client retrieved results).

        Args:
            job_id: Job identifier

        Returns:
            True if job was removed, False if not found
        """
        async with self._lock:
            if job_id in self._jobs:
                # Cancel task if still running
                task = self._jobs[job_id].get("task")
                if task and not task.done():
                    task.cancel()

                del self._jobs[job_id]
                logger.info(f"Cleaned up job {job_id}")
                return True
            return False

    async def _process_batch(
        self,
        job_id: str,
        entities: List[CanonicalizeRequest]
    ):
        """
        Background task that processes entities batch.

        Creates its own database session to avoid connection issues.

        Args:
            job_id: Job identifier
            entities: Entities to process
        """
        from app.api.dependencies import get_db_session, get_canonicalizer

        start_time = time.time()
        results: List[CanonicalizeResponse] = []

        try:
            # Update status to processing
            async with self._lock:
                self._jobs[job_id]["status"].status = "processing"
                self._jobs[job_id]["status"].started_at = datetime.utcnow().isoformat()

            logger.info(f"Processing batch job {job_id} with {len(entities)} entities")

            # Create our own database session for background task
            async for db in get_db_session():
                try:
                    # Use dependency injection to get canonicalizer (singleton pattern)
                    # This prevents creating new SentenceTransformer instances (420 MB each)
                    # and shares the model across all batch jobs, reducing memory from 8.5GB to 500MB
                    canonicalizer = await get_canonicalizer(db)

                    # Process each entity
                    for idx, entity_req in enumerate(entities, 1):
                        try:
                            # Canonicalize single entity
                            result = await canonicalizer.canonicalize(
                                entity_name=entity_req.entity_name,
                                entity_type=entity_req.entity_type,
                                language=entity_req.language
                            )

                            # Convert EntityCanonical to CanonicalizeResponse
                            response = CanonicalizeResponse(
                                canonical_name=result.canonical_name,
                                canonical_id=result.canonical_id,
                                aliases=result.aliases,
                                confidence=result.confidence,
                                source=result.source,
                                entity_type=result.entity_type
                            )
                            results.append(response)

                            # Update progress
                            async with self._lock:
                                job = self._jobs[job_id]
                                job["status"].stats.processed_entities = idx
                                job["status"].stats.successful += 1
                                job["status"].progress_percent = (idx / len(entities)) * 100

                        except Exception as e:
                            logger.error(f"Failed to canonicalize entity {entity_req.entity_name}: {e}")
                            async with self._lock:
                                job = self._jobs[job_id]
                                job["status"].stats.processed_entities = idx
                                job["status"].stats.failed += 1
                                job["status"].progress_percent = (idx / len(entities)) * 100

                    # Mark as completed
                    total_time_ms = (time.time() - start_time) * 1000

                    async with self._lock:
                        job = self._jobs[job_id]
                        job["status"].status = "completed"
                        job["status"].progress_percent = 100.0
                        job["status"].completed_at = datetime.utcnow().isoformat()
                        job["results"] = AsyncBatchJobResult(
                            job_id=job_id,
                            results=results,
                            total_processed=len(results),
                            total_time_ms=total_time_ms
                        )

                        # 🔧 MEMORY FIX: Clear large input data after completion
                        # Keeps only results, frees ~50% of job memory
                        job["entities"] = []

                    logger.info(
                        f"Completed batch job {job_id}: "
                        f"{len(results)} processed in {total_time_ms:.2f}ms"
                    )

                    # 🔧 MEMORY FIX: Expunge session identity map
                    # Releases references to all loaded entities
                    if hasattr(db, 'expunge_all'):
                        db.expunge_all()

                finally:
                    # Session cleanup handled by async context manager
                    pass

        except Exception as e:
            logger.error(f"Batch job {job_id} failed: {e}", exc_info=True)
            async with self._lock:
                job = self._jobs[job_id]
                job["status"].status = "failed"
                job["status"].error_message = str(e)
                job["status"].completed_at = datetime.utcnow().isoformat()

                # 🔧 MEMORY FIX: Clear input data even on failure
                job["entities"] = []


# Global processor instance
_async_processor = AsyncBatchProcessor()


def get_async_processor() -> AsyncBatchProcessor:
    """Get global async batch processor instance."""
    return _async_processor

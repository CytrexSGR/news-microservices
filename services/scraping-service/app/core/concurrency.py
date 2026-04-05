"""
Concurrency Control for Scraping Operations.

Prevents resource exhaustion by:
- Limiting concurrent scraping jobs
- Queueing excess requests
- Tracking active jobs
- Memory-efficient semaphore-based limiting
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class JobStats:
    """Statistics for a scraping job."""
    job_id: str
    url: str
    started_at: datetime
    feed_id: Optional[str] = None
    item_id: Optional[str] = None


class ConcurrencyLimiter:
    """
    Limits concurrent scraping operations using asyncio.Semaphore.

    Features:
    - Semaphore-based concurrency control
    - Job tracking and statistics
    - Graceful queue management
    - Resource monitoring
    """

    def __init__(self, max_concurrent: int = None):
        """
        Initialize concurrency limiter.

        Args:
            max_concurrent: Maximum concurrent jobs (uses settings if None)
        """
        self.max_concurrent = max_concurrent or settings.SCRAPING_MAX_CONCURRENT_JOBS
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.active_jobs: Dict[str, JobStats] = {}
        self.total_jobs = 0
        self.completed_jobs = 0
        self.failed_jobs = 0

        logger.info(f"✅ Concurrency limiter initialized: max_concurrent={self.max_concurrent}")

    async def acquire(
        self,
        job_id: str,
        url: str,
        feed_id: Optional[str] = None,
        item_id: Optional[str] = None
    ):
        """
        Acquire semaphore slot for job.

        Blocks if max concurrent jobs reached.

        Args:
            job_id: Unique job identifier
            url: URL being scraped
            feed_id: Optional feed ID
            item_id: Optional item ID
        """
        # Wait for available slot
        queue_position = self.semaphore._value
        if queue_position == 0:
            logger.info(
                f"⏳ Job {job_id} queued (active: {len(self.active_jobs)}/{self.max_concurrent})"
            )

        await self.semaphore.acquire()

        # Track active job
        self.active_jobs[job_id] = JobStats(
            job_id=job_id,
            url=url,
            started_at=datetime.utcnow(),
            feed_id=feed_id,
            item_id=item_id
        )
        self.total_jobs += 1

        logger.debug(
            f"🔵 Job {job_id} started (active: {len(self.active_jobs)}/{self.max_concurrent})"
        )

    def release(self, job_id: str, success: bool = True):
        """
        Release semaphore slot after job completion.

        Args:
            job_id: Job identifier
            success: Whether job completed successfully
        """
        # Update stats
        if success:
            self.completed_jobs += 1
        else:
            self.failed_jobs += 1

        # Remove from active jobs
        job_stats = self.active_jobs.pop(job_id, None)

        if job_stats:
            duration = (datetime.utcnow() - job_stats.started_at).total_seconds()
            logger.debug(
                f"✅ Job {job_id} completed in {duration:.2f}s "
                f"(active: {len(self.active_jobs)}/{self.max_concurrent})"
            )

        # Release semaphore
        self.semaphore.release()

    async def execute_with_limit(
        self,
        func,
        *args,
        job_id: str,
        url: str,
        feed_id: Optional[str] = None,
        item_id: Optional[str] = None,
        **kwargs
    ):
        """
        Execute async function with concurrency limit.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            job_id: Unique job identifier
            url: URL being processed
            feed_id: Optional feed ID
            item_id: Optional item ID
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            Exception from func if it fails
        """
        # Acquire semaphore slot
        await self.acquire(job_id=job_id, url=url, feed_id=feed_id, item_id=item_id)

        try:
            # Execute function
            result = await func(*args, **kwargs)
            self.release(job_id, success=True)
            return result

        except Exception as e:
            self.release(job_id, success=False)
            raise e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get concurrency statistics.

        Returns:
            dict: Statistics including active jobs, queue depth, success rate
        """
        return {
            "max_concurrent": self.max_concurrent,
            "active_jobs": len(self.active_jobs),
            "available_slots": self.semaphore._value,
            "queued_jobs": max(0, self.total_jobs - self.completed_jobs - self.failed_jobs - len(self.active_jobs)),
            "total_jobs": self.total_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "success_rate": (
                self.completed_jobs / (self.completed_jobs + self.failed_jobs)
                if (self.completed_jobs + self.failed_jobs) > 0
                else 0.0
            ),
            "active_job_details": [
                {
                    "job_id": stats.job_id,
                    "url": stats.url,
                    "started_at": stats.started_at.isoformat(),
                    "duration_seconds": (datetime.utcnow() - stats.started_at).total_seconds()
                }
                for stats in self.active_jobs.values()
            ]
        }

    def reset_stats(self):
        """Reset statistics (keeps active jobs tracking)."""
        completed = self.completed_jobs
        failed = self.failed_jobs
        total = self.total_jobs

        self.total_jobs = len(self.active_jobs)
        self.completed_jobs = 0
        self.failed_jobs = 0

        logger.info(
            f"📊 Stats reset: {completed} completed, {failed} failed "
            f"(out of {total} total jobs)"
        )


# Global concurrency limiter instance
concurrency_limiter = ConcurrencyLimiter()

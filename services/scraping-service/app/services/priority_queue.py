"""
Priority Queue Service

Phase 6: Scale

Manages a priority queue for scraping jobs with:
- Multiple priority levels
- Scheduled/delayed jobs
- Job deduplication
- Statistics tracking
"""
import logging
import uuid
import heapq
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import threading

from app.models.priority_queue import (
    ScrapeJob,
    ScrapeJobCreate,
    PriorityLevel,
    QueueStats
)

logger = logging.getLogger(__name__)


class PriorityQueue:
    """
    Thread-safe priority queue for scraping jobs.

    Features:
    - Priority-based ordering (highest first)
    - Scheduled jobs with delay
    - Job deduplication by URL
    - Completion tracking
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: List[Tuple[int, datetime, ScrapeJob]] = []  # heap: (-priority, created_at, job)
        self._jobs: Dict[str, ScrapeJob] = {}  # id -> job
        self._url_to_job_id: Dict[str, str] = {}  # url -> job_id (for dedup)
        self._processing: Dict[str, ScrapeJob] = {}  # Currently processing jobs
        self._completed: Dict[str, ScrapeJob] = {}  # Recently completed (limited)
        self._lock = threading.Lock()

        # Stats
        self._total_completed = 0
        self._total_failed = 0
        self._wait_times: List[float] = []
        self._processing_times: List[float] = []

    def enqueue(self, job_create: ScrapeJobCreate) -> ScrapeJob:
        """
        Add a job to the queue.

        Returns existing job if URL already queued.
        """
        with self._lock:
            # Check for duplicate URL
            if job_create.url in self._url_to_job_id:
                existing_id = self._url_to_job_id[job_create.url]
                existing = self._jobs.get(existing_id)
                if existing and existing.status == "pending":
                    logger.debug(f"Job already queued for URL: {job_create.url}")
                    return existing

            # Check queue size
            if len(self._queue) >= self.max_size:
                # Remove lowest priority job
                self._remove_lowest_priority()

            # Create new job
            job = ScrapeJob(
                id=str(uuid.uuid4()),
                url=job_create.url,
                priority=job_create.priority,
                method=job_create.method,
                max_retries=job_create.max_retries,
                callback_url=job_create.callback_url,
                metadata=job_create.metadata or {}
            )

            # Handle delayed scheduling
            if job_create.delay_seconds > 0:
                job.scheduled_at = datetime.utcnow() + timedelta(seconds=job_create.delay_seconds)

            # Add to queue
            self._jobs[job.id] = job
            self._url_to_job_id[job.url] = job.id

            # Push to heap (negate priority for max-heap behavior)
            heapq.heappush(
                self._queue,
                (-job.priority.value, job.created_at, job)
            )

            logger.debug(f"Enqueued job {job.id} with priority {job.priority.name}")
            return job

    def dequeue(self) -> Optional[ScrapeJob]:
        """
        Get the next job to process.

        Returns highest priority job that is ready (not scheduled for later).
        """
        with self._lock:
            now = datetime.utcnow()

            # Find first ready job
            while self._queue:
                _, _, job = heapq.heappop(self._queue)

                # Check if job still exists and is pending
                if job.id not in self._jobs or self._jobs[job.id].status != "pending":
                    continue

                # Check if scheduled for later
                if job.scheduled_at and job.scheduled_at > now:
                    # Put back in queue
                    heapq.heappush(
                        self._queue,
                        (-job.priority.value, job.created_at, job)
                    )
                    return None  # No ready jobs

                # Mark as processing
                job.status = "processing"
                job.started_at = now
                self._processing[job.id] = job

                # Track wait time
                wait_time = (now - job.created_at).total_seconds()
                self._wait_times.append(wait_time)
                if len(self._wait_times) > 1000:
                    self._wait_times = self._wait_times[-500:]

                logger.debug(f"Dequeued job {job.id} (waited {wait_time:.1f}s)")
                return job

            return None

    def complete(
        self,
        job_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[ScrapeJob]:
        """
        Mark a job as completed or failed.

        Args:
            job_id: Job ID
            result: Scrape result (for success)
            error: Error message (for failure)

        Returns:
            Updated job or None if not found
        """
        with self._lock:
            job = self._processing.pop(job_id, None)
            if not job:
                job = self._jobs.get(job_id)
                if not job:
                    return None

            now = datetime.utcnow()
            job.completed_at = now

            if error:
                job.status = "failed"
                job.error = error
                self._total_failed += 1

                # Check if can retry
                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = "pending"
                    job.started_at = None
                    job.completed_at = None
                    job.error = None

                    # Re-enqueue with slight delay
                    job.scheduled_at = now + timedelta(seconds=min(60, 10 * job.retry_count))
                    heapq.heappush(
                        self._queue,
                        (-job.priority.value, job.created_at, job)
                    )
                    logger.info(f"Re-queued job {job_id} for retry {job.retry_count}")
                    return job
            else:
                job.status = "completed"
                job.result = result
                self._total_completed += 1

            # Track processing time
            if job.started_at:
                proc_time = (now - job.started_at).total_seconds()
                self._processing_times.append(proc_time)
                if len(self._processing_times) > 1000:
                    self._processing_times = self._processing_times[-500:]

            # Move to completed (limited size)
            self._completed[job_id] = job
            if len(self._completed) > 1000:
                # Remove oldest
                oldest_id = next(iter(self._completed))
                del self._completed[oldest_id]

            # Clean up
            if job_id in self._jobs:
                del self._jobs[job_id]
            if job.url in self._url_to_job_id:
                del self._url_to_job_id[job.url]

            logger.debug(f"Completed job {job_id} with status {job.status}")
            return job

    def get_job(self, job_id: str) -> Optional[ScrapeJob]:
        """Get a job by ID"""
        with self._lock:
            return (
                self._jobs.get(job_id) or
                self._processing.get(job_id) or
                self._completed.get(job_id)
            )

    def cancel(self, job_id: str) -> bool:
        """Cancel a pending job"""
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == "pending":
                job.status = "cancelled"
                del self._jobs[job_id]
                if job.url in self._url_to_job_id:
                    del self._url_to_job_id[job.url]
                return True
            return False

    def get_stats(self) -> QueueStats:
        """Get queue statistics"""
        with self._lock:
            by_priority: Dict[str, int] = defaultdict(int)
            pending = 0
            processing = len(self._processing)

            for job in self._jobs.values():
                if job.status == "pending":
                    pending += 1
                    by_priority[job.priority.name] += 1

            avg_wait = (
                sum(self._wait_times) / len(self._wait_times)
                if self._wait_times else 0.0
            )
            avg_proc = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )

            # Estimate jobs per minute
            recent_completions = len([
                j for j in self._completed.values()
                if j.completed_at and
                j.completed_at > datetime.utcnow() - timedelta(minutes=1)
            ])

            return QueueStats(
                total_jobs=len(self._jobs) + len(self._processing) + len(self._completed),
                pending_jobs=pending,
                processing_jobs=processing,
                completed_jobs=self._total_completed,
                failed_jobs=self._total_failed,
                by_priority=dict(by_priority),
                avg_wait_time_seconds=avg_wait,
                avg_processing_time_seconds=avg_proc,
                jobs_per_minute=float(recent_completions)
            )

    def _remove_lowest_priority(self) -> None:
        """Remove lowest priority job to make room"""
        if not self._queue:
            return

        # Rebuild heap without lowest priority pending job
        temp = []
        removed = None

        while self._queue:
            item = heapq.heappop(self._queue)
            _, _, job = item
            if job.status == "pending" and removed is None:
                removed = job
                continue
            temp.append(item)

        # Rebuild
        for item in temp:
            heapq.heappush(self._queue, item)

        if removed:
            if removed.id in self._jobs:
                del self._jobs[removed.id]
            if removed.url in self._url_to_job_id:
                del self._url_to_job_id[removed.url]
            logger.warning(f"Removed job {removed.id} due to queue overflow")

    def clear(self) -> int:
        """Clear all pending jobs"""
        with self._lock:
            count = len(self._jobs)
            self._queue.clear()
            self._jobs.clear()
            self._url_to_job_id.clear()
            return count


# Singleton instance
_priority_queue: Optional[PriorityQueue] = None


def get_priority_queue() -> PriorityQueue:
    """Get singleton priority queue"""
    global _priority_queue
    if _priority_queue is None:
        _priority_queue = PriorityQueue()
    return _priority_queue

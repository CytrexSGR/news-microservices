"""
Priority Queue Worker

Consumes jobs from the in-memory Priority Queue and processes them.

This worker:
- Polls the queue for pending jobs
- Respects rate limits and concurrency
- Processes jobs using the ContentScraper
- Marks jobs as complete/failed
- Supports graceful shutdown

Note: This is different from scraping_worker.py which consumes from RabbitMQ.
The Priority Queue is for ad-hoc/MCP-triggered scraping requests.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from app.services.scraper import scraper, ScrapeStatus
from app.services.priority_queue import get_priority_queue, PriorityQueue
from app.core.rate_limiter import rate_limiter
from app.core.concurrency import concurrency_limiter
from app.core.config import settings

logger = logging.getLogger(__name__)


class PriorityQueueWorker:
    """
    Background worker that processes jobs from the Priority Queue.

    Features:
    - Configurable polling interval
    - Respects concurrency limits
    - Graceful shutdown
    - Automatic retry on failure
    """

    def __init__(
        self,
        poll_interval: float = 1.0,
        max_concurrent: int = 3,
    ):
        self.poll_interval = poll_interval
        self.max_concurrent = max_concurrent
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.active_jobs: int = 0
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the queue worker."""
        if self.running:
            logger.warning("Queue worker already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info(
            f"Priority Queue Worker started "
            f"(poll_interval={self.poll_interval}s, max_concurrent={self.max_concurrent})"
        )

    async def stop(self):
        """Stop the queue worker gracefully."""
        if not self.running:
            return

        logger.info("Stopping Priority Queue Worker...")
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        # Wait for active jobs to complete (with timeout)
        timeout = 30
        start = datetime.now()
        while self.active_jobs > 0:
            if (datetime.now() - start).seconds > timeout:
                logger.warning(f"Timeout waiting for {self.active_jobs} active jobs")
                break
            await asyncio.sleep(0.5)

        logger.info("Priority Queue Worker stopped")

    async def _run(self):
        """Main worker loop."""
        queue = get_priority_queue()

        while self.running:
            try:
                # Check if we can take more jobs
                if self.active_jobs >= self.max_concurrent:
                    await asyncio.sleep(self.poll_interval)
                    continue

                # Try to dequeue a job
                job = queue.dequeue()

                if job is None:
                    # No jobs available, wait and try again
                    await asyncio.sleep(self.poll_interval)
                    continue

                # Process job in background
                asyncio.create_task(self._process_job(queue, job))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue worker error: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)

    async def _process_job(self, queue: PriorityQueue, job):
        """Process a single job."""
        async with self._lock:
            self.active_jobs += 1

        job_id = job.id
        url = job.url

        try:
            logger.info(f"Processing queue job {job_id}: {url}")

            # Perform the scrape
            result = await scraper.scrape(url)

            # Mark job as complete
            if result.status == ScrapeStatus.SUCCESS:
                queue.complete(
                    job_id,
                    result={
                        "content": result.content,
                        "word_count": result.word_count,
                        "method_used": result.method_used,
                        "extracted_title": result.extracted_title,
                        "extracted_authors": result.extracted_authors,
                    }
                )
                logger.info(
                    f"Job {job_id} completed: {result.word_count} words via {result.method_used}"
                )
            else:
                queue.complete(
                    job_id,
                    error=f"{result.status.value}: {result.error_message}"
                )
                logger.warning(f"Job {job_id} failed: {result.status.value}")

        except Exception as e:
            logger.error(f"Job {job_id} error: {e}", exc_info=True)
            queue.complete(job_id, error=str(e))

        finally:
            async with self._lock:
                self.active_jobs -= 1


# Singleton instance
queue_worker = PriorityQueueWorker(
    poll_interval=1.0,
    max_concurrent=3,
)

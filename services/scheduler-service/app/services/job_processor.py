"""
Job Processor Service

Processes analysis jobs from the queue and executes them via Content Analysis Service.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from database.models import AnalysisJobQueue, JobType, JobStatus

logger = logging.getLogger(__name__)


class JobProcessor:
    """
    Processes analysis jobs from the queue.

    Runs every JOB_PROCESS_INTERVAL seconds (default: 30)
    Processes jobs in priority order (highest first)
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.http_client: Optional[httpx.AsyncClient] = None
        self._is_running = False
        self._max_concurrent_jobs = settings.MAX_CONCURRENT_JOBS

    async def start(self):
        """Start the job processor scheduler"""
        if self._is_running:
            logger.warning("Job processor already running")
            return

        logger.info("Starting job processor")

        # Initialize HTTP client
        # Send scheduler's own key to authenticate to content-analysis service
        headers = {"X-Service-Name": "scheduler-service"}
        if settings.SCHEDULER_SERVICE_API_KEY:
            headers["X-Service-Key"] = settings.SCHEDULER_SERVICE_API_KEY

        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),  # Long timeout for AI analysis
            headers=headers
        )

        # Schedule job processing
        self.scheduler.add_job(
            self._process_jobs,
            trigger=IntervalTrigger(seconds=settings.JOB_PROCESS_INTERVAL),
            id="job_processor",
            name="Job Processor",
            replace_existing=True,
            max_instances=1
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(f"Job processor started (interval: {settings.JOB_PROCESS_INTERVAL}s)")

    async def stop(self):
        """Stop the job processor scheduler"""
        if not self._is_running:
            return

        logger.info("Stopping job processor")
        self.scheduler.shutdown(wait=True)

        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

        self._is_running = False
        logger.info("Job processor stopped")

    async def _process_jobs(self):
        """
        Process pending jobs from the queue.

        Processes up to max_concurrent_jobs at a time.
        """
        db = SessionLocal()
        try:
            logger.debug("Starting job processing cycle")

            # Get pending jobs (ordered by priority DESC, then created_at ASC)
            pending_jobs = db.query(AnalysisJobQueue).filter(
                AnalysisJobQueue.status == JobStatus.PENDING,
                AnalysisJobQueue.retry_count < AnalysisJobQueue.max_retries
            ).order_by(
                AnalysisJobQueue.priority.desc(),
                AnalysisJobQueue.created_at.asc()
            ).limit(self._max_concurrent_jobs).all()

            if not pending_jobs:
                logger.debug("No pending jobs to process")
                return

            logger.info(f"Processing {len(pending_jobs)} jobs")

            # Process each job
            for job in pending_jobs:
                try:
                    await self._process_single_job(db, job)
                except Exception as e:
                    logger.error(f"Error processing job {job.id}: {e}")
                    self._mark_job_failed(db, job, str(e))

            logger.info(f"Job processing cycle complete")

        except Exception as e:
            logger.error(f"Error in job processing cycle: {e}")
        finally:
            db.close()

    async def _process_single_job(self, db: Session, job: AnalysisJobQueue):
        """
        Process a single analysis job.

        Args:
            db: Database session
            job: Job to process
        """
        logger.info(f"Processing job {job.id}: {job.job_type} for article {job.article_id}")

        # Mark job as processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        try:
            # Route to appropriate analysis endpoint
            if job.job_type == JobType.CATEGORIZATION:
                result = await self._run_categorization(job)
            elif job.job_type == JobType.FINANCE_SENTIMENT:
                result = await self._run_finance_sentiment(job)
            elif job.job_type == JobType.GEOPOLITICAL_SENTIMENT:
                result = await self._run_geopolitical_sentiment(job)
            elif job.job_type == JobType.STANDARD_SENTIMENT:
                result = await self._run_standard_sentiment(job)
            elif job.job_type == JobType.OSINT_ANALYSIS:
                result = await self._run_osint_analysis(job)
            elif job.job_type == JobType.SUMMARY:
                result = await self._run_summary(job)
            elif job.job_type == JobType.ENTITIES:
                result = await self._run_entities(job)
            elif job.job_type == JobType.TOPICS:
                result = await self._run_topics(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")

            # Mark job as completed
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            self._mark_job_failed(db, job, str(e))

    async def _run_categorization(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run categorization analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/categorization"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling categorization API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def _run_finance_sentiment(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run finance sentiment analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/finance-sentiment"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling finance sentiment API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def _run_geopolitical_sentiment(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run geopolitical sentiment analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/geopolitical-sentiment"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling geopolitical sentiment API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def _run_standard_sentiment(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run standard sentiment analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/standard-sentiment"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling standard sentiment API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def _run_osint_analysis(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run OSINT event analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/osint"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling OSINT analysis API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def _run_summary(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run summary extraction analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/summary"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling summary extraction API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def _run_entities(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run entity extraction analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/entities"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling entity extraction API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def _run_topics(self, job: AnalysisJobQueue) -> Dict[str, Any]:
        """Run topic classification analysis"""
        url = f"{settings.CONTENT_ANALYSIS_URL}/api/v1/internal/analyze/topics"
        payload = {"article_id": str(job.article_id)}

        logger.debug(f"Calling topic classification API: {url}")
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def _mark_job_failed(self, db: Session, job: AnalysisJobQueue, error_message: str):
        """Mark job as failed and increment retry count"""
        job.retry_count += 1
        job.error_message = error_message

        if job.retry_count >= job.max_retries:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            logger.warning(f"Job {job.id} failed permanently after {job.retry_count} retries")
        else:
            job.status = JobStatus.PENDING
            logger.info(f"Job {job.id} will be retried (attempt {job.retry_count}/{job.max_retries})")

        db.commit()

    def is_running(self) -> bool:
        """Check if job processor is currently running"""
        return self._is_running

    def get_status(self) -> Dict[str, Any]:
        """Get current status of job processor"""
        return {
            "is_running": self._is_running,
            "process_interval_seconds": settings.JOB_PROCESS_INTERVAL,
            "max_concurrent_jobs": self._max_concurrent_jobs
        }


# Global instance
job_processor = JobProcessor()

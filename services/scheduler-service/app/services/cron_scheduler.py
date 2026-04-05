"""
Cron Scheduler Service

Supports cron-like scheduled tasks with flexible triggers.
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job

logger = logging.getLogger(__name__)


class CronScheduler:
    """
    Flexible cron-like task scheduler.

    Supports:
    - Cron expressions (e.g., "0 */6 * * *" for every 6 hours)
    - Interval triggers (e.g., every 30 minutes)
    - Date triggers (one-time at specific datetime)
    - Custom job management (add, remove, pause, resume)
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False
        self._jobs: Dict[str, Job] = {}

    def start(self):
        """Start the scheduler"""
        if self._is_running:
            logger.warning("Cron scheduler already running")
            return

        logger.info("Starting cron scheduler")
        self.scheduler.start()
        self._is_running = True
        logger.info("Cron scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if not self._is_running:
            return

        logger.info("Stopping cron scheduler")
        self.scheduler.shutdown(wait=True)
        self._is_running = False
        self._jobs.clear()
        logger.info("Cron scheduler stopped")

    def add_cron_job(
        self,
        job_id: str,
        func: Callable,
        cron_expression: str,
        name: Optional[str] = None,
        replace_existing: bool = True,
        **kwargs
    ) -> Job:
        """
        Add a job with cron-style scheduling.

        Args:
            job_id: Unique job identifier
            func: Function to execute
            cron_expression: Cron expression (e.g., "0 */6 * * *")
            name: Human-readable job name
            replace_existing: Replace existing job with same ID
            **kwargs: Additional arguments to pass to func

        Returns:
            APScheduler Job object

        Examples:
            # Every 6 hours
            scheduler.add_cron_job("feed_refresh", refresh_feeds, "0 */6 * * *")

            # Daily at midnight
            scheduler.add_cron_job("daily_cleanup", cleanup, "0 0 * * *")

            # Every Monday at 9 AM
            scheduler.add_cron_job("weekly_report", generate_report, "0 9 * * 1")
        """
        logger.info(f"Adding cron job '{job_id}': {cron_expression}")

        # Parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        minute, hour, day, month, day_of_week = parts

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        )

        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            replace_existing=replace_existing,
            kwargs=kwargs
        )

        self._jobs[job_id] = job
        logger.info(f"Cron job '{job_id}' added successfully")
        return job

    def add_interval_job(
        self,
        job_id: str,
        func: Callable,
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        name: Optional[str] = None,
        replace_existing: bool = True,
        **kwargs
    ) -> Job:
        """
        Add a job with interval-based scheduling.

        Args:
            job_id: Unique job identifier
            func: Function to execute
            seconds: Interval in seconds
            minutes: Interval in minutes
            hours: Interval in hours
            days: Interval in days
            name: Human-readable job name
            replace_existing: Replace existing job with same ID
            **kwargs: Additional arguments to pass to func

        Returns:
            APScheduler Job object

        Examples:
            # Every 30 seconds
            scheduler.add_interval_job("health_check", check_health, seconds=30)

            # Every 5 minutes
            scheduler.add_interval_job("feed_check", check_feeds, minutes=5)

            # Every 2 hours
            scheduler.add_interval_job("analysis_batch", analyze_batch, hours=2)
        """
        logger.info(f"Adding interval job '{job_id}'")

        # Build trigger kwargs with only non-None values
        trigger_kwargs = {}
        if seconds is not None:
            trigger_kwargs['seconds'] = seconds
        if minutes is not None:
            trigger_kwargs['minutes'] = minutes
        if hours is not None:
            trigger_kwargs['hours'] = hours
        if days is not None:
            trigger_kwargs['days'] = days

        trigger = IntervalTrigger(**trigger_kwargs)

        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            replace_existing=replace_existing,
            kwargs=kwargs
        )

        self._jobs[job_id] = job
        logger.info(f"Interval job '{job_id}' added successfully")
        return job

    def add_date_job(
        self,
        job_id: str,
        func: Callable,
        run_date: datetime,
        name: Optional[str] = None,
        **kwargs
    ) -> Job:
        """
        Add a one-time job scheduled for specific date/time.

        Args:
            job_id: Unique job identifier
            func: Function to execute
            run_date: Datetime to run the job
            name: Human-readable job name
            **kwargs: Additional arguments to pass to func

        Returns:
            APScheduler Job object

        Examples:
            # Run once at specific time
            scheduler.add_date_job(
                "maintenance",
                run_maintenance,
                datetime(2025, 10, 15, 2, 0, 0)
            )
        """
        logger.info(f"Adding date job '{job_id}' for {run_date}")

        trigger = DateTrigger(run_date=run_date)

        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            kwargs=kwargs
        )

        self._jobs[job_id] = job
        logger.info(f"Date job '{job_id}' added successfully")
        return job

    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        if job_id not in self._jobs:
            logger.warning(f"Job '{job_id}' not found")
            return

        logger.info(f"Removing job '{job_id}'")
        self.scheduler.remove_job(job_id)
        del self._jobs[job_id]
        logger.info(f"Job '{job_id}' removed")

    def pause_job(self, job_id: str):
        """Pause a scheduled job"""
        if job_id not in self._jobs:
            logger.warning(f"Job '{job_id}' not found")
            return

        logger.info(f"Pausing job '{job_id}'")
        self.scheduler.pause_job(job_id)
        logger.info(f"Job '{job_id}' paused")

    def resume_job(self, job_id: str):
        """Resume a paused job"""
        if job_id not in self._jobs:
            logger.warning(f"Job '{job_id}' not found")
            return

        logger.info(f"Resuming job '{job_id}'")
        self.scheduler.resume_job(job_id)
        logger.info(f"Job '{job_id}' resumed")

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> Dict[str, Job]:
        """Get all registered jobs"""
        return self._jobs.copy()

    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed job information"""
        job = self.get_job(job_id)
        if not job:
            return None

        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "pending": job.pending
        }

    def list_jobs(self) -> list[Dict[str, Any]]:
        """List all jobs with their info"""
        return [
            self.get_job_info(job_id)
            for job_id in self._jobs.keys()
        ]

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._is_running

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "is_running": self._is_running,
            "total_jobs": len(self._jobs),
            "running_jobs": len(self.scheduler.get_jobs())
        }


# Global instance
cron_scheduler = CronScheduler()

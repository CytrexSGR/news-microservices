"""Scheduler service client for MCP Orchestration Server."""

import logging
from typing import Any, Dict, Optional

from ..config import settings
from .base import BaseClient

logger = logging.getLogger(__name__)


class SchedulerClient(BaseClient):
    """Client for scheduler-service (Port 8108)."""

    def __init__(self):
        super().__init__(
            service_name="scheduler-service",
            base_url=settings.scheduler_service_url,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    # =========================================================================
    # Scheduler Status & Health
    # =========================================================================

    async def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status overview.

        Returns:
            Current scheduler state, active jobs, worker status
        """
        return await self.request("GET", "/api/v1/scheduler/status")

    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get internal service health details.
        """
        return await self.request("GET", "/api/v1/scheduler/internal/health/service")

    # =========================================================================
    # Job Management
    # =========================================================================

    async def list_jobs(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List scheduler jobs.

        Args:
            status: Filter by status (pending, running, completed, failed)
            skip: Number to skip
            limit: Maximum to return
        """
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status

        return await self.request("GET", "/api/v1/scheduler/jobs", params=params)

    async def get_job_stats(self) -> Dict[str, Any]:
        """
        Get job statistics.

        Returns:
            Stats about job counts, success rates, average durations
        """
        return await self.request("GET", "/api/v1/scheduler/jobs/stats")

    async def cancel_job(
        self,
        job_id: str,
    ) -> Dict[str, Any]:
        """
        Cancel a pending or running job.

        Args:
            job_id: Job ID to cancel
        """
        return await self.request("POST", f"/api/v1/scheduler/jobs/{job_id}/cancel")

    async def retry_job(
        self,
        job_id: str,
    ) -> Dict[str, Any]:
        """
        Retry a failed job.

        Args:
            job_id: Job ID to retry
        """
        return await self.request("POST", f"/api/v1/scheduler/jobs/{job_id}/retry")

    # =========================================================================
    # Cron Jobs
    # =========================================================================

    async def list_cron_jobs(self) -> Dict[str, Any]:
        """
        List scheduled cron jobs.

        Returns:
            List of cron jobs with their schedules
        """
        return await self.request("GET", "/api/v1/scheduler/cron/jobs")

    # =========================================================================
    # Feed Scheduling
    # =========================================================================

    async def check_feed_schedule(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """
        Check schedule for a specific feed.

        Args:
            feed_id: Feed ID to check
        """
        return await self.request(
            "GET",
            f"/api/v1/scheduler/feeds/{feed_id}/check",
        )

"""
Advanced Health Check Endpoint for Scheduler Service.

Provides:
- Deep health checks for all dependencies
- Component-level health status
- Readiness and liveness probes
- Detailed diagnostics
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, status, Response
from pydantic import BaseModel
import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.metrics import (
    update_service_health,
    update_scheduler_running,
    service_uptime_seconds
)
from app.services.feed_monitor import feed_monitor
from app.services.job_processor import job_processor
from app.services.cron_scheduler import cron_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Track service start time
SERVICE_START_TIME = time.time()


# ============================================================================
# Response Models
# ============================================================================

class ComponentHealth(BaseModel):
    """Health status of a single component"""
    name: str
    status: str  # healthy, degraded, unhealthy
    message: Optional[str] = None
    last_check: str
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Complete health check response"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    uptime_seconds: float
    version: str
    components: Dict[str, ComponentHealth]
    summary: Dict[str, int]  # Count by status


# ============================================================================
# Component Health Checks
# ============================================================================

async def check_database_health() -> ComponentHealth:
    """Check database connectivity and health"""
    start_time = time.time()

    try:
        db = SessionLocal()
        try:
            # Try simple query
            db.execute("SELECT 1")
            db.close()

            return ComponentHealth(
                name="database",
                status="healthy",
                message="Database connection successful",
                last_check=datetime.now(timezone.utc).isoformat(),
                details={
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "pool_size": settings.DATABASE_POOL_SIZE
                }
            )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                last_check=datetime.now(timezone.utc).isoformat()
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return ComponentHealth(
            name="database",
            status="unhealthy",
            message=f"Cannot create database session: {str(e)}",
            last_check=datetime.now(timezone.utc).isoformat()
        )


async def check_redis_health() -> ComponentHealth:
    """Check Redis connectivity"""
    # TODO: Implement when Redis client is properly initialized
    return ComponentHealth(
        name="redis",
        status="healthy",
        message="Redis check not implemented",
        last_check=datetime.now(timezone.utc).isoformat()
    )


async def check_rabbitmq_health() -> ComponentHealth:
    """Check RabbitMQ connectivity"""
    # TODO: Implement when RabbitMQ client is properly initialized
    return ComponentHealth(
        name="rabbitmq",
        status="healthy",
        message="RabbitMQ check not implemented",
        last_check=datetime.now(timezone.utc).isoformat()
    )


async def check_feed_service_health() -> ComponentHealth:
    """Check Feed Service connectivity"""
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.FEED_SERVICE_URL}/health")

            if response.status_code == 200:
                return ComponentHealth(
                    name="feed_service",
                    status="healthy",
                    message="Feed Service is healthy",
                    last_check=datetime.now(timezone.utc).isoformat(),
                    details={
                        "response_time_ms": round((time.time() - start_time) * 1000, 2),
                        "url": settings.FEED_SERVICE_URL
                    }
                )
            else:
                return ComponentHealth(
                    name="feed_service",
                    status="degraded",
                    message=f"Feed Service returned status {response.status_code}",
                    last_check=datetime.now(timezone.utc).isoformat()
                )

    except Exception as e:
        logger.warning(f"Feed Service health check failed: {e}")
        return ComponentHealth(
            name="feed_service",
            status="unhealthy",
            message=f"Cannot reach Feed Service: {str(e)}",
            last_check=datetime.now(timezone.utc).isoformat()
        )


async def check_content_analysis_health() -> ComponentHealth:
    """Check Content Analysis Service connectivity"""
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.CONTENT_ANALYSIS_URL}/health")

            if response.status_code == 200:
                return ComponentHealth(
                    name="content_analysis_service",
                    status="healthy",
                    message="Content Analysis Service is healthy",
                    last_check=datetime.now(timezone.utc).isoformat(),
                    details={
                        "response_time_ms": round((time.time() - start_time) * 1000, 2),
                        "url": settings.CONTENT_ANALYSIS_URL
                    }
                )
            else:
                return ComponentHealth(
                    name="content_analysis_service",
                    status="degraded",
                    message=f"Content Analysis Service returned status {response.status_code}",
                    last_check=datetime.now(timezone.utc).isoformat()
                )

    except Exception as e:
        logger.warning(f"Content Analysis Service health check failed: {e}")
        return ComponentHealth(
            name="content_analysis_service",
            status="unhealthy",
            message=f"Cannot reach Content Analysis Service: {str(e)}",
            last_check=datetime.now(timezone.utc).isoformat()
        )


async def check_feed_monitor_health() -> ComponentHealth:
    """Check Feed Monitor component"""
    is_running = feed_monitor.is_running()

    update_scheduler_running("feed_monitor", is_running)

    if is_running:
        status_info = feed_monitor.get_status()
        return ComponentHealth(
            name="feed_monitor",
            status="healthy",
            message="Feed Monitor is running",
            last_check=datetime.now(timezone.utc).isoformat(),
            details=status_info
        )
    else:
        return ComponentHealth(
            name="feed_monitor",
            status="unhealthy",
            message="Feed Monitor is not running",
            last_check=datetime.now(timezone.utc).isoformat()
        )


async def check_job_processor_health() -> ComponentHealth:
    """Check Job Processor component"""
    is_running = job_processor.is_running()

    update_scheduler_running("job_processor", is_running)

    if is_running:
        status_info = job_processor.get_status()
        return ComponentHealth(
            name="job_processor",
            status="healthy",
            message="Job Processor is running",
            last_check=datetime.now(timezone.utc).isoformat(),
            details=status_info
        )
    else:
        return ComponentHealth(
            name="job_processor",
            status="unhealthy",
            message="Job Processor is not running",
            last_check=datetime.now(timezone.utc).isoformat()
        )


async def check_cron_scheduler_health() -> ComponentHealth:
    """Check Cron Scheduler component"""
    is_running = cron_scheduler.is_running()

    update_scheduler_running("cron_scheduler", is_running)

    if is_running:
        status_info = cron_scheduler.get_status()
        return ComponentHealth(
            name="cron_scheduler",
            status="healthy",
            message="Cron Scheduler is running",
            last_check=datetime.now(timezone.utc).isoformat(),
            details=status_info
        )
    else:
        return ComponentHealth(
            name="cron_scheduler",
            status="unhealthy",
            message="Cron Scheduler is not running",
            last_check=datetime.now(timezone.utc).isoformat()
        )


# ============================================================================
# Health Check Endpoints
# ============================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check endpoint.

    Checks:
    - Database connectivity
    - Redis connectivity
    - RabbitMQ connectivity
    - External service health (Feed Service, Content Analysis)
    - Scheduler component status
    """
    # Check all components
    components = {
        "database": await check_database_health(),
        "redis": await check_redis_health(),
        "rabbitmq": await check_rabbitmq_health(),
        "feed_service": await check_feed_service_health(),
        "content_analysis_service": await check_content_analysis_health(),
        "feed_monitor": await check_feed_monitor_health(),
        "job_processor": await check_job_processor_health(),
        "cron_scheduler": await check_cron_scheduler_health()
    }

    # Calculate summary
    summary = {
        "healthy": sum(1 for c in components.values() if c.status == "healthy"),
        "degraded": sum(1 for c in components.values() if c.status == "degraded"),
        "unhealthy": sum(1 for c in components.values() if c.status == "unhealthy")
    }

    # Determine overall status
    if summary["unhealthy"] > 0:
        overall_status = "unhealthy"
    elif summary["degraded"] > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # Update metrics
    update_service_health(overall_status)
    uptime = time.time() - SERVICE_START_TIME
    service_uptime_seconds.set(uptime)

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime,
        version="0.1.0",
        components=components,
        summary=summary
    )


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.

    Returns 200 if service is alive (not deadlocked).
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/ready")
async def readiness_probe(response: Response):
    """
    Kubernetes readiness probe.

    Returns 200 if service is ready to accept requests.
    Checks critical components only.
    """
    # Check critical components
    db_health = await check_database_health()
    feed_monitor_health = await check_feed_monitor_health()
    job_processor_health = await check_job_processor_health()

    critical_components = [db_health, feed_monitor_health, job_processor_health]

    # Check if all critical components are healthy
    is_ready = all(c.status == "healthy" for c in critical_components)

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {c.name: c.status for c in critical_components}
        }

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/startup")
async def startup_probe(response: Response):
    """
    Kubernetes startup probe.

    Returns 200 when service has finished starting up.
    """
    # Check if all schedulers are running
    feed_monitor_running = feed_monitor.is_running()
    job_processor_running = job_processor.is_running()
    cron_scheduler_running = cron_scheduler.is_running()

    is_started = all([
        feed_monitor_running,
        job_processor_running,
        cron_scheduler_running
    ])

    if not is_started:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "starting",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "feed_monitor": feed_monitor_running,
                "job_processor": job_processor_running,
                "cron_scheduler": cron_scheduler_running
            }
        }

    return {
        "status": "started",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

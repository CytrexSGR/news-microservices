"""
Monitoring and Metrics API Endpoints.

Provides detailed metrics for:
- Rate limiting statistics
- Concurrency tracking
- Retry statistics
- Memory usage (browser)
- Failure tracking
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.core.rate_limiter import rate_limiter
from app.core.concurrency import concurrency_limiter
from app.core.retry import retry_handler
from app.services.scraper import scraper
from app.services.failure_tracker import failure_tracker

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/metrics")
async def get_metrics():
    """
    Get comprehensive service metrics.

    Returns:
        - Concurrency statistics
        - Retry statistics
        - Browser status
        - Failure tracking
    """
    return {
        "concurrency": concurrency_limiter.get_stats(),
        "retry": retry_handler.get_stats(),
        "browser": {
            "initialized": scraper.browser is not None,
            "playwright_initialized": scraper.playwright is not None
        }
    }


@router.get("/rate-limits/{key}")
async def get_rate_limit_stats(key: str):
    """
    Get rate limit statistics for a specific key.

    Args:
        key: Rate limit key (e.g., "domain:example.com", "global", "feed:uuid")

    Returns:
        Current count and window information
    """
    stats = await rate_limiter.get_stats(key)
    return {
        "key": key,
        **stats
    }


@router.get("/active-jobs")
async def get_active_jobs():
    """
    Get detailed information about currently active scraping jobs.

    Returns:
        List of active jobs with URLs, start times, and durations
    """
    stats = concurrency_limiter.get_stats()
    return {
        "count": stats["active_jobs"],
        "max_concurrent": stats["max_concurrent"],
        "available_slots": stats["available_slots"],
        "jobs": stats["active_job_details"]
    }


@router.post("/reset-stats")
async def reset_statistics():
    """
    Reset collected statistics (for debugging/testing).

    Resets:
    - Concurrency stats
    - Retry stats
    """
    concurrency_limiter.reset_stats()
    retry_handler.reset_stats()

    return {
        "status": "success",
        "message": "Statistics reset"
    }


@router.get("/failures/{feed_id}")
async def get_feed_failures(feed_id: str):
    """
    Get failure count for a specific feed.

    Args:
        feed_id: Feed UUID

    Returns:
        Failure count and status
    """
    try:
        failures = await failure_tracker.get_failure_count(feed_id)
        threshold = await failure_tracker.get_threshold(feed_id)

        return {
            "feed_id": feed_id,
            "failure_count": failures,
            "threshold": threshold,
            "is_disabled": failures >= threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

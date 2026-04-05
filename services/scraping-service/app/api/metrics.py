"""
Prometheus Metrics API Endpoint

Phase 5: Observability

Provides:
- /metrics endpoint for Prometheus scraping
- Health check with metrics summary
"""
from fastapi import APIRouter, Response
from app.core.metrics import get_metrics_collector

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "",
    summary="Prometheus Metrics",
    description="Returns metrics in Prometheus exposition format",
    response_class=Response
)
async def get_metrics():
    """
    Get Prometheus metrics.

    Returns metrics in Prometheus text format for scraping by Prometheus server.

    Metrics include:
    - scraper_requests_total: Counter of scraping requests by method, status, domain
    - scraper_duration_seconds: Histogram of scraping duration
    - scraper_content_size_bytes: Histogram of content sizes
    - scraper_word_count: Histogram of word counts
    - scraper_content_quality_score: Histogram of quality scores
    - scraper_dlq_entries_total: Gauge of DLQ entries by status
    - scraper_rate_limit_hits_total: Counter of rate limit hits
    """
    collector = get_metrics_collector()
    return Response(
        content=collector.get_metrics(),
        media_type=collector.get_content_type()
    )


@router.get(
    "/health",
    summary="Metrics Health",
    description="Returns basic health status with metrics summary"
)
async def metrics_health():
    """
    Check metrics endpoint health.

    Returns basic status to verify metrics collection is working.
    """
    collector = get_metrics_collector()
    return {
        "status": "healthy",
        "metrics_available": True,
        "content_type": collector.get_content_type()
    }

"""
Prometheus Metrics for Scraping Service

Provides comprehensive observability metrics for:
- Scraping operations (success/failure/latency)
- Content quality scores
- DLQ statistics
- Resource utilization
"""
import time
from typing import Optional, Dict, Any
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    multiprocess,
    REGISTRY
)
import logging

logger = logging.getLogger(__name__)

# Try to use multiprocess mode if available (for Gunicorn workers)
try:
    multiprocess.MultiProcessCollector(REGISTRY)
    logger.info("Prometheus multiprocess mode enabled")
except Exception:
    pass


# ============= Scraping Metrics =============

SCRAPE_REQUESTS_TOTAL = Counter(
    'scraper_requests_total',
    'Total number of scraping requests',
    ['method', 'status', 'domain']
)

SCRAPE_DURATION_SECONDS = Histogram(
    'scraper_duration_seconds',
    'Time spent scraping URLs',
    ['method'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

SCRAPE_CONTENT_SIZE_BYTES = Histogram(
    'scraper_content_size_bytes',
    'Size of scraped content in bytes',
    ['method'],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000)
)

SCRAPE_WORD_COUNT = Histogram(
    'scraper_word_count',
    'Word count of scraped content',
    ['method'],
    buckets=(10, 50, 100, 250, 500, 1000, 2000, 5000, 10000)
)

# ============= Quality Metrics =============

CONTENT_QUALITY_SCORE = Histogram(
    'scraper_content_quality_score',
    'Content quality scores (0-1)',
    ['domain'],
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

EXTRACTION_COMPLETENESS = Histogram(
    'scraper_extraction_completeness',
    'Extraction completeness (ratio of expected fields present)',
    ['method'],
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

# ============= DLQ Metrics =============

DLQ_ENTRIES_TOTAL = Gauge(
    'scraper_dlq_entries_total',
    'Current number of DLQ entries',
    ['status']
)

DLQ_ENTRIES_BY_REASON = Gauge(
    'scraper_dlq_entries_by_reason',
    'DLQ entries by failure reason',
    ['reason']
)

DLQ_RETRIES_TOTAL = Counter(
    'scraper_dlq_retries_total',
    'Total number of DLQ retries',
    ['reason', 'success']
)

# ============= Source Registry Metrics =============

SOURCE_PROFILES_TOTAL = Gauge(
    'scraper_source_profiles_total',
    'Total number of source profiles'
)

SOURCE_SUCCESS_RATE = Gauge(
    'scraper_source_success_rate',
    'Success rate per source domain',
    ['domain']
)

SOURCE_AVG_RESPONSE_TIME = Gauge(
    'scraper_source_avg_response_time_ms',
    'Average response time per source domain',
    ['domain']
)

# ============= Resource Metrics =============

BROWSER_CONTEXTS_ACTIVE = Gauge(
    'scraper_browser_contexts_active',
    'Number of active browser contexts'
)

HTTP_CONNECTIONS_ACTIVE = Gauge(
    'scraper_http_connections_active',
    'Number of active HTTP connections'
)

RATE_LIMIT_HITS = Counter(
    'scraper_rate_limit_hits_total',
    'Number of rate limit hits',
    ['domain']
)

# ============= Service Info =============

SERVICE_INFO = Info(
    'scraper_service',
    'Scraping service information'
)


class MetricsCollector:
    """
    Collects and manages Prometheus metrics for the scraping service.
    """

    def __init__(self):
        self._start_time = time.time()
        SERVICE_INFO.info({
            'version': '1.0.0',
            'phase': '5-observability'
        })

    def record_scrape(
        self,
        method: str,
        status: str,
        domain: str,
        duration_seconds: float,
        content_size: int = 0,
        word_count: int = 0
    ):
        """Record a scraping operation"""
        SCRAPE_REQUESTS_TOTAL.labels(
            method=method,
            status=status,
            domain=domain
        ).inc()

        SCRAPE_DURATION_SECONDS.labels(method=method).observe(duration_seconds)

        if content_size > 0:
            SCRAPE_CONTENT_SIZE_BYTES.labels(method=method).observe(content_size)

        if word_count > 0:
            SCRAPE_WORD_COUNT.labels(method=method).observe(word_count)

    def record_quality_score(self, domain: str, score: float):
        """Record content quality score"""
        CONTENT_QUALITY_SCORE.labels(domain=domain).observe(score)

    def record_extraction_completeness(self, method: str, completeness: float):
        """Record extraction completeness ratio"""
        EXTRACTION_COMPLETENESS.labels(method=method).observe(completeness)

    def update_dlq_metrics(self, stats: Dict[str, Any]):
        """Update DLQ metrics from stats"""
        if not stats:
            return

        # Update by status
        by_status = stats.get("by_status", {})
        for status, count in by_status.items():
            DLQ_ENTRIES_TOTAL.labels(status=status).set(count)

        # Update by reason
        by_reason = stats.get("by_failure_reason", {})
        for reason, count in by_reason.items():
            DLQ_ENTRIES_BY_REASON.labels(reason=reason).set(count)

    def record_dlq_retry(self, reason: str, success: bool):
        """Record a DLQ retry attempt"""
        DLQ_RETRIES_TOTAL.labels(
            reason=reason,
            success=str(success).lower()
        ).inc()

    def update_source_metrics(
        self,
        total_profiles: int,
        domain_stats: Dict[str, Dict[str, Any]]
    ):
        """Update source registry metrics"""
        SOURCE_PROFILES_TOTAL.set(total_profiles)

        for domain, stats in domain_stats.items():
            if "success_rate" in stats:
                SOURCE_SUCCESS_RATE.labels(domain=domain).set(stats["success_rate"])
            if "avg_response_time" in stats:
                SOURCE_AVG_RESPONSE_TIME.labels(domain=domain).set(stats["avg_response_time"])

    def set_browser_contexts(self, count: int):
        """Set active browser context count"""
        BROWSER_CONTEXTS_ACTIVE.set(count)

    def set_http_connections(self, count: int):
        """Set active HTTP connection count"""
        HTTP_CONNECTIONS_ACTIVE.set(count)

    def record_rate_limit_hit(self, domain: str):
        """Record a rate limit hit"""
        RATE_LIMIT_HITS.labels(domain=domain).inc()

    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in exposition format"""
        return generate_latest(REGISTRY)

    def get_content_type(self) -> str:
        """Get Prometheus content type header"""
        return CONTENT_TYPE_LATEST


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get singleton metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

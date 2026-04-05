"""
Prometheus Metrics for Content-Analysis-V3

Provides counters, histograms, and gauges for monitoring the analysis pipeline.
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# Service info
SERVICE_INFO = Info(
    'content_analysis_v3_info',
    'Content-Analysis-V3 service information'
)
SERVICE_INFO.info({
    'version': '1.0.0-alpha',
    'pipeline': 'tier0-tier1-tier2'
})

# Request counters
ANALYSIS_REQUESTS_TOTAL = Counter(
    'content_analysis_v3_requests_total',
    'Total analysis requests received',
    ['status']  # success, failed, discarded
)

TIER_EXECUTIONS_TOTAL = Counter(
    'content_analysis_v3_tier_executions_total',
    'Total tier executions',
    ['tier', 'status']  # tier: tier0/tier1/tier2, status: success/failed
)

SPECIALIST_EXECUTIONS_TOTAL = Counter(
    'content_analysis_v3_specialist_executions_total',
    'Total specialist executions',
    ['specialist', 'status']  # specialist: topic_classifier/entity_extractor/etc
)

# Duration histograms
PIPELINE_DURATION = Histogram(
    'content_analysis_v3_pipeline_duration_seconds',
    'Total pipeline execution duration',
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120]
)

TIER_DURATION = Histogram(
    'content_analysis_v3_tier_duration_seconds',
    'Tier execution duration',
    ['tier'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

SPECIALIST_DURATION = Histogram(
    'content_analysis_v3_specialist_duration_seconds',
    'Specialist execution duration',
    ['specialist'],
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

# Cost tracking
ANALYSIS_COST = Histogram(
    'content_analysis_v3_cost_usd',
    'Analysis cost in USD',
    ['tier'],
    buckets=[0.00001, 0.0001, 0.001, 0.01, 0.1]
)

TOKENS_USED = Counter(
    'content_analysis_v3_tokens_total',
    'Total tokens used',
    ['tier', 'provider']  # tier: tier0/tier1/tier2, provider: gemini/openai
)

# Current state gauges
QUEUE_SIZE = Gauge(
    'content_analysis_v3_queue_size',
    'Current queue size (approximate)'
)

ACTIVE_WORKERS = Gauge(
    'content_analysis_v3_active_workers',
    'Number of active workers processing requests'
)

# Error tracking
ERRORS_TOTAL = Counter(
    'content_analysis_v3_errors_total',
    'Total errors by type',
    ['error_type']  # validation, provider, timeout, unknown
)


# Helper functions for recording metrics
def record_request_completed(discarded: bool = False):
    """Record a successfully completed request."""
    status = 'discarded' if discarded else 'success'
    ANALYSIS_REQUESTS_TOTAL.labels(status=status).inc()


def record_request_failed():
    """Record a failed request."""
    ANALYSIS_REQUESTS_TOTAL.labels(status='failed').inc()


def record_tier_execution(tier: str, success: bool, duration_seconds: float, cost_usd: float, tokens: int, provider: str):
    """Record a tier execution with all metrics."""
    status = 'success' if success else 'failed'
    TIER_EXECUTIONS_TOTAL.labels(tier=tier, status=status).inc()
    TIER_DURATION.labels(tier=tier).observe(duration_seconds)
    ANALYSIS_COST.labels(tier=tier).observe(cost_usd)
    TOKENS_USED.labels(tier=tier, provider=provider).inc(tokens)


def record_specialist_execution(specialist: str, success: bool, duration_seconds: float):
    """Record a specialist execution."""
    status = 'success' if success else 'failed'
    SPECIALIST_EXECUTIONS_TOTAL.labels(specialist=specialist, status=status).inc()
    SPECIALIST_DURATION.labels(specialist=specialist).observe(duration_seconds)


def record_error(error_type: str):
    """Record an error by type."""
    ERRORS_TOTAL.labels(error_type=error_type).inc()

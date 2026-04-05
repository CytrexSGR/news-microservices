"""Prometheus metrics for MCP Intelligence Server."""

from prometheus_client import Counter, Histogram, Gauge, Info

# =============================================================================
# Tool Call Metrics (existing)
# =============================================================================

TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "Total MCP tool calls",
    ["tool_name", "status"]
)

TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "MCP tool execution duration",
    ["tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# =============================================================================
# Circuit Breaker Metrics
# =============================================================================
#
# NOTE: Circuit breaker metrics are managed by the resilience module
# (app/resilience/metrics.py) and are automatically tracked by the
# CircuitBreaker class. No additional integration needed here.
#
# Metrics provided by resilience module:
# - circuit_breaker_state (gauge)
# - circuit_breaker_failures_total (counter)
# - circuit_breaker_successes_total (counter)
# - circuit_breaker_rejections_total (counter)
# - circuit_breaker_state_changes_total (counter)
# - circuit_breaker_recovery_time_seconds (histogram)

# =============================================================================
# Cache Metrics
# =============================================================================

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["key_prefix"]
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["key_prefix"]
)

CACHE_LATENCY = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation latency",
    ["operation"],  # get, set, delete
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

CACHE_ERRORS = Counter(
    "cache_errors_total",
    "Total cache errors",
    ["operation", "error_type"]
)

CACHE_SIZE = Gauge(
    "cache_keys_count",
    "Number of keys in cache",
    ["key_prefix"]
)

# =============================================================================
# HTTP Client Metrics (per backend service)
# =============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests to backend services",
    ["service", "method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration to backend services",
    ["service", "method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

HTTP_REQUEST_ERRORS = Counter(
    "http_request_errors_total",
    "HTTP request errors",
    ["service", "error_type"]
)

HTTP_TIMEOUTS = Counter(
    "http_request_timeouts_total",
    "HTTP request timeouts",
    ["service"]
)

# =============================================================================
# Service Health Metrics
# =============================================================================

SERVICE_HEALTH = Gauge(
    "service_health_status",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"]
)

SERVICE_RESPONSE_TIME_P95 = Gauge(
    "service_response_time_p95_seconds",
    "95th percentile response time",
    ["service"]
)

SERVICE_ERROR_RATE = Gauge(
    "service_error_rate",
    "Error rate per service (errors/requests)",
    ["service"]
)

# =============================================================================
# Redis Connection Metrics
# =============================================================================

REDIS_CONNECTED = Gauge(
    "redis_connected",
    "Redis connection status (1=connected, 0=disconnected)"
)

REDIS_OPERATIONS_TOTAL = Counter(
    "redis_operations_total",
    "Total Redis operations",
    ["operation", "status"]
)

# =============================================================================
# Application Info
# =============================================================================

APP_INFO = Info(
    "mcp_intelligence_server",
    "MCP Intelligence Server application info"
)

# Initialize app info
APP_INFO.info({
    "version": "1.0.0",
    "service": "mcp-intelligence-server"
})

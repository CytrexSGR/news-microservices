"""Prometheus metrics for MCP Integration Server."""

from prometheus_client import Counter, Histogram, Gauge, Info

# =============================================================================
# Tool Call Metrics
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
    ["operation"],
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
# HTTP Client Metrics
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
    "mcp_integration_server",
    "MCP Integration Server application info"
)

# Initialize app info
APP_INFO.info({
    "version": "1.0.0",
    "service": "mcp-integration-server"
})

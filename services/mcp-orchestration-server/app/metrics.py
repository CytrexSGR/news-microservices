"""Prometheus metrics for MCP Orchestration Server."""

from prometheus_client import Counter, Histogram, Gauge, Info

# Server info
SERVER_INFO = Info("mcp_orchestration_server", "MCP Orchestration Server information")

# Tool metrics
TOOL_CALLS_TOTAL = Counter(
    "mcp_orch_tool_calls_total",
    "Total number of tool calls",
    ["tool_name", "status"],
)

TOOL_CALL_DURATION = Histogram(
    "mcp_orch_tool_call_duration_seconds",
    "Tool call duration in seconds",
    ["tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Cache metrics
CACHE_HITS = Counter(
    "mcp_orch_cache_hits_total",
    "Total cache hits",
    ["key_prefix"],
)

CACHE_MISSES = Counter(
    "mcp_orch_cache_misses_total",
    "Total cache misses",
    ["key_prefix"],
)

CACHE_LATENCY = Histogram(
    "mcp_orch_cache_operation_seconds",
    "Cache operation latency",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)

CACHE_ERRORS = Counter(
    "mcp_orch_cache_errors_total",
    "Total cache errors",
    ["operation", "error_type"],
)

# Redis metrics
REDIS_CONNECTED = Gauge(
    "mcp_orch_redis_connected",
    "Redis connection status (1=connected, 0=disconnected)",
)

REDIS_OPERATIONS_TOTAL = Counter(
    "mcp_orch_redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],
)

# HTTP client metrics
HTTP_REQUESTS_TOTAL = Counter(
    "mcp_orch_http_requests_total",
    "Total HTTP requests to backend services",
    ["service", "method", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "mcp_orch_http_request_duration_seconds",
    "HTTP request duration",
    ["service", "method"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Circuit breaker metrics
CIRCUIT_BREAKER_STATE = Gauge(
    "mcp_orch_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["service"],
)

CIRCUIT_BREAKER_FAILURES = Counter(
    "mcp_orch_circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["service"],
)

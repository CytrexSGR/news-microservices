"""
Prometheus Metrics for Scheduler Service.

Tracks:
- Task execution counts (by type, status)
- Task duration (histograms)
- Task failures (by error type)
- Queue sizes
- Circuit breaker states
- Service health
"""

import time
import logging
from typing import Optional, Callable, Any
from functools import wraps
from contextlib import contextmanager

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Enum,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)

logger = logging.getLogger(__name__)

# Create custom registry (avoids conflicts with other services)
registry = CollectorRegistry()


# ============================================================================
# Task Metrics
# ============================================================================

task_runs_total = Counter(
    'scheduler_task_runs_total',
    'Total number of scheduled task executions',
    ['task_name', 'status'],  # status: success, failure, timeout
    registry=registry
)

task_duration_seconds = Histogram(
    'scheduler_task_duration_seconds',
    'Duration of scheduled task executions in seconds',
    ['task_name'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=registry
)

task_failures_total = Counter(
    'scheduler_task_failures_total',
    'Total number of task failures',
    ['task_name', 'error_type'],
    registry=registry
)

task_retries_total = Counter(
    'scheduler_task_retries_total',
    'Total number of task retry attempts',
    ['task_name', 'attempt'],
    registry=registry
)


# ============================================================================
# Job Queue Metrics
# ============================================================================

job_queue_size = Gauge(
    'scheduler_job_queue_size',
    'Number of jobs in queue by status',
    ['status'],  # pending, processing, completed, failed
    registry=registry
)

job_processing_duration_seconds = Histogram(
    'scheduler_job_processing_duration_seconds',
    'Duration of job processing in seconds',
    ['job_type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
    registry=registry
)

job_queue_age_seconds = Histogram(
    'scheduler_job_queue_age_seconds',
    'Age of jobs in queue (time since creation)',
    ['status'],
    buckets=(10, 30, 60, 300, 600, 1800, 3600, 7200),
    registry=registry
)


# ============================================================================
# Feed Monitor Metrics
# ============================================================================

feeds_checked_total = Counter(
    'scheduler_feeds_checked_total',
    'Total number of feeds checked',
    ['status'],  # success, error
    registry=registry
)

articles_discovered_total = Counter(
    'scheduler_articles_discovered_total',
    'Total number of new articles discovered',
    ['feed_category'],
    registry=registry
)

feed_check_duration_seconds = Histogram(
    'scheduler_feed_check_duration_seconds',
    'Duration of feed check cycles in seconds',
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=registry
)


# ============================================================================
# Circuit Breaker Metrics
# ============================================================================

circuit_breaker_state = Enum(
    'scheduler_circuit_breaker_state',
    'Current circuit breaker state',
    ['service'],
    states=['CLOSED', 'OPEN', 'HALF_OPEN'],
    registry=registry
)

circuit_breaker_failures_total = Counter(
    'scheduler_circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['service'],
    registry=registry
)

circuit_breaker_trips_total = Counter(
    'scheduler_circuit_breaker_trips_total',
    'Total circuit breaker trips (state transitions to OPEN)',
    ['service'],
    registry=registry
)


# ============================================================================
# HTTP Client Metrics
# ============================================================================

http_requests_total = Counter(
    'scheduler_http_requests_total',
    'Total HTTP requests to external services',
    ['service', 'method', 'status_code'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'scheduler_http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['service', 'method'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=registry
)


# ============================================================================
# Service Health Metrics
# ============================================================================

service_health = Enum(
    'scheduler_service_health',
    'Overall service health status',
    states=['healthy', 'degraded', 'unhealthy'],
    registry=registry
)

service_uptime_seconds = Gauge(
    'scheduler_service_uptime_seconds',
    'Service uptime in seconds',
    registry=registry
)

scheduler_running = Gauge(
    'scheduler_running',
    'Whether scheduler components are running',
    ['component'],  # feed_monitor, job_processor, cron_scheduler
    registry=registry
)


# ============================================================================
# Service Info
# ============================================================================

service_info = Info(
    'scheduler_service',
    'Scheduler service information',
    registry=registry
)

service_info.info({
    'version': '0.1.0',
    'service': 'scheduler-service',
    'environment': 'development'
})


# ============================================================================
# Metric Recording Functions
# ============================================================================

def record_task_execution(task_name: str, status: str, duration: float):
    """
    Record task execution metrics.

    Args:
        task_name: Name of the task
        status: Execution status (success, failure, timeout)
        duration: Execution duration in seconds
    """
    task_runs_total.labels(task_name=task_name, status=status).inc()
    task_duration_seconds.labels(task_name=task_name).observe(duration)


def record_task_failure(task_name: str, error_type: str):
    """
    Record task failure.

    Args:
        task_name: Name of the task
        error_type: Type of error that occurred
    """
    task_failures_total.labels(task_name=task_name, error_type=error_type).inc()


def record_task_retry(task_name: str, attempt: int):
    """
    Record task retry attempt.

    Args:
        task_name: Name of the task
        attempt: Retry attempt number
    """
    task_retries_total.labels(task_name=task_name, attempt=str(attempt)).inc()


def update_job_queue_size(status: str, size: int):
    """
    Update job queue size gauge.

    Args:
        status: Job status (pending, processing, completed, failed)
        size: Number of jobs with this status
    """
    job_queue_size.labels(status=status).set(size)


def record_job_processing(job_type: str, duration: float):
    """
    Record job processing duration.

    Args:
        job_type: Type of job processed
        duration: Processing duration in seconds
    """
    job_processing_duration_seconds.labels(job_type=job_type).observe(duration)


def record_feed_check(status: str, duration: float):
    """
    Record feed check metrics.

    Args:
        status: Check status (success, error)
        duration: Check duration in seconds
    """
    feeds_checked_total.labels(status=status).inc()
    feed_check_duration_seconds.observe(duration)


def record_article_discovered(feed_category: str, count: int = 1):
    """
    Record discovered articles.

    Args:
        feed_category: Category of the feed
        count: Number of articles discovered
    """
    articles_discovered_total.labels(feed_category=feed_category).inc(count)


def update_circuit_breaker_state(service: str, state: str):
    """
    Update circuit breaker state.

    Args:
        service: Service name
        state: Circuit breaker state (CLOSED, OPEN, HALF_OPEN)
    """
    circuit_breaker_state.labels(service=service).state(state)


def record_circuit_breaker_failure(service: str):
    """
    Record circuit breaker failure.

    Args:
        service: Service name
    """
    circuit_breaker_failures_total.labels(service=service).inc()


def record_circuit_breaker_trip(service: str):
    """
    Record circuit breaker trip (state transition to OPEN).

    Args:
        service: Service name
    """
    circuit_breaker_trips_total.labels(service=service).inc()


def record_http_request(service: str, method: str, status_code: int, duration: float):
    """
    Record HTTP request metrics.

    Args:
        service: Target service name
        method: HTTP method (GET, POST, etc.)
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(
        service=service,
        method=method,
        status_code=str(status_code)
    ).inc()

    http_request_duration_seconds.labels(
        service=service,
        method=method
    ).observe(duration)


def update_service_health(status: str):
    """
    Update service health status.

    Args:
        status: Health status (healthy, degraded, unhealthy)
    """
    service_health.state(status)


def update_scheduler_running(component: str, is_running: bool):
    """
    Update scheduler component running status.

    Args:
        component: Component name (feed_monitor, job_processor, cron_scheduler)
        is_running: Whether component is running
    """
    scheduler_running.labels(component=component).set(1 if is_running else 0)


# ============================================================================
# Decorator for Automatic Metric Recording
# ============================================================================

def track_task_execution(task_name: str):
    """
    Decorator to automatically track task execution metrics.

    Usage:
        @track_task_execution("feed_monitor")
        async def monitor_feeds():
            # Task logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                status = "failure"
                error_type = type(e).__name__
                record_task_failure(task_name, error_type)
                raise

            finally:
                duration = time.time() - start_time
                record_task_execution(task_name, status, duration)

        return wrapper
    return decorator


@contextmanager
def track_duration(metric_name: str, labels: dict = None):
    """
    Context manager to track duration of code blocks.

    Usage:
        with track_duration("job_processing", {"job_type": "categorization"}):
            # Code to measure
            pass
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        # Log duration
        logger.debug(f"{metric_name} duration: {duration:.2f}s", extra=labels or {})


# ============================================================================
# Metrics Endpoint
# ============================================================================

def get_metrics() -> tuple[bytes, str]:
    """
    Get Prometheus metrics in text format.

    Returns:
        Tuple of (metrics_data, content_type)
    """
    return generate_latest(registry), CONTENT_TYPE_LATEST


# ============================================================================
# Utility Functions
# ============================================================================

def reset_metrics():
    """Reset all metrics (for testing)"""
    # This will reset all collectors in the registry
    for collector in list(registry._collector_to_names.keys()):
        try:
            registry.unregister(collector)
        except Exception as e:
            logger.warning(f"Failed to unregister collector: {e}")

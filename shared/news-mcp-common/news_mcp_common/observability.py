"""Observability utilities for tracing and metrics."""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.jaeger import thrift
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

from .config import settings

logger = logging.getLogger(__name__)

# Global providers
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None
_tracer: Optional[trace.Tracer] = None
_meter: Optional[metrics.Meter] = None

# Prometheus metrics
request_count = Counter(
    "news_mcp_requests_total",
    "Total number of requests",
    ["service", "endpoint", "method", "status"]
)

request_duration = Histogram(
    "news_mcp_request_duration_seconds",
    "Request duration in seconds",
    ["service", "endpoint", "method"]
)

active_requests = Gauge(
    "news_mcp_active_requests",
    "Number of active requests",
    ["service"]
)

error_count = Counter(
    "news_mcp_errors_total",
    "Total number of errors",
    ["service", "error_type"]
)

db_query_duration = Histogram(
    "news_mcp_db_query_duration_seconds",
    "Database query duration in seconds",
    ["service", "query_type"]
)

cache_hits = Counter(
    "news_mcp_cache_hits_total",
    "Total number of cache hits",
    ["service", "cache_type"]
)

cache_misses = Counter(
    "news_mcp_cache_misses_total",
    "Total number of cache misses",
    ["service", "cache_type"]
)

event_published = Counter(
    "news_mcp_events_published_total",
    "Total number of events published",
    ["service", "event_type"]
)

event_consumed = Counter(
    "news_mcp_events_consumed_total",
    "Total number of events consumed",
    ["service", "event_type"]
)


def setup_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    jaeger_host: Optional[str] = None,
    jaeger_port: Optional[int] = None,
    enable: Optional[bool] = None,
) -> trace.Tracer:
    """Setup OpenTelemetry tracing with Jaeger exporter.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        jaeger_host: Jaeger agent host
        jaeger_port: Jaeger agent port
        enable: Enable tracing (defaults to settings)

    Returns:
        Configured tracer
    """
    global _tracer_provider, _tracer

    if enable is None:
        enable = settings.tracing_enabled

    if not enable:
        logger.info("Tracing disabled")
        return trace.get_tracer(__name__)

    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": settings.environment,
    })

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Configure Jaeger exporter
    jaeger_exporter = thrift.JaegerExporter(
        agent_host_name=jaeger_host or settings.jaeger_host,
        agent_port=jaeger_port or settings.jaeger_port,
    )

    # Add span processor
    _tracer_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Get tracer
    _tracer = trace.get_tracer(service_name, service_version)

    logger.info(f"Tracing initialized for service: {service_name}")
    return _tracer


def setup_metrics(
    service_name: str,
    prometheus_port: Optional[int] = None,
    enable: Optional[bool] = None,
) -> metrics.Meter:
    """Setup OpenTelemetry metrics with Prometheus exporter.

    Args:
        service_name: Name of the service
        prometheus_port: Prometheus metrics port
        enable: Enable metrics (defaults to settings)

    Returns:
        Configured meter
    """
    global _meter_provider, _meter

    if enable is None:
        enable = settings.metrics_enabled

    if not enable:
        logger.info("Metrics disabled")
        return metrics.get_meter(__name__)

    # Start Prometheus HTTP server
    port = prometheus_port or settings.prometheus_port
    start_http_server(port)
    logger.info(f"Prometheus metrics server started on port {port}")

    # Create meter provider with Prometheus reader
    reader = PrometheusMetricReader()
    _meter_provider = MeterProvider(
        resource=Resource.create({"service.name": service_name}),
        metric_readers=[reader],
    )

    # Set global meter provider
    metrics.set_meter_provider(_meter_provider)

    # Get meter
    _meter = metrics.get_meter(service_name)

    logger.info(f"Metrics initialized for service: {service_name}")
    return _meter


def instrument_fastapi(app: Any) -> None:
    """Instrument FastAPI application for tracing.

    Args:
        app: FastAPI application instance
    """
    if settings.tracing_enabled:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument SQLAlchemy engine for tracing.

    Args:
        engine: SQLAlchemy engine instance
    """
    if settings.tracing_enabled:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy instrumentation enabled")


def instrument_redis(redis_client: Any) -> None:
    """Instrument Redis client for tracing.

    Args:
        redis_client: Redis client instance
    """
    if settings.tracing_enabled:
        RedisInstrumentor().instrument(redis_client=redis_client)
        logger.info("Redis instrumentation enabled")


def get_tracer() -> trace.Tracer:
    """Get the configured tracer."""
    return _tracer or trace.get_tracer(__name__)


def get_meter() -> metrics.Meter:
    """Get the configured meter."""
    return _meter or metrics.get_meter(__name__)


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """Context manager for creating a trace span.

    Args:
        name: Span name
        attributes: Span attributes
        kind: Span kind
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(
        name,
        attributes=attributes,
        kind=kind,
    ) as span:
        yield span


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
):
    """Decorator to trace function execution.

    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with trace_span(span_name, attributes):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with trace_span(span_name, attributes):
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_request(
    service_name: str,
    endpoint: str,
    method: str = "GET",
    status: int = 200,
    duration: Optional[float] = None,
):
    """Track HTTP request metrics.

    Args:
        service_name: Service handling the request
        endpoint: Request endpoint
        method: HTTP method
        status: Response status code
        duration: Request duration in seconds
    """
    request_count.labels(
        service=service_name,
        endpoint=endpoint,
        method=method,
        status=status,
    ).inc()

    if duration is not None:
        request_duration.labels(
            service=service_name,
            endpoint=endpoint,
            method=method,
        ).observe(duration)


def track_error(service_name: str, error_type: str):
    """Track error metrics.

    Args:
        service_name: Service where error occurred
        error_type: Type of error
    """
    error_count.labels(
        service=service_name,
        error_type=error_type,
    ).inc()


def track_db_query(service_name: str, query_type: str, duration: float):
    """Track database query metrics.

    Args:
        service_name: Service executing the query
        query_type: Type of query (select, insert, update, delete)
        duration: Query duration in seconds
    """
    db_query_duration.labels(
        service=service_name,
        query_type=query_type,
    ).observe(duration)


def track_cache(service_name: str, cache_type: str, hit: bool):
    """Track cache metrics.

    Args:
        service_name: Service using cache
        cache_type: Type of cache
        hit: Whether it was a cache hit
    """
    if hit:
        cache_hits.labels(
            service=service_name,
            cache_type=cache_type,
        ).inc()
    else:
        cache_misses.labels(
            service=service_name,
            cache_type=cache_type,
        ).inc()


def track_event_published(service_name: str, event_type: str):
    """Track published event metrics.

    Args:
        service_name: Service publishing the event
        event_type: Type of event
    """
    event_published.labels(
        service=service_name,
        event_type=event_type,
    ).inc()


def track_event_consumed(service_name: str, event_type: str):
    """Track consumed event metrics.

    Args:
        service_name: Service consuming the event
        event_type: Type of event
    """
    event_consumed.labels(
        service=service_name,
        event_type=event_type,
    ).inc()


class RequestTracker:
    """Track request metrics automatically."""

    def __init__(self, service_name: str):
        self.service_name = service_name

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Track active requests
            active_requests.labels(service=self.service_name).inc()
            start_time = time.time()

            try:
                # Execute request handler
                response = await func(request, *args, **kwargs)

                # Track request metrics
                duration = time.time() - start_time
                track_request(
                    self.service_name,
                    request.url.path,
                    request.method,
                    response.status_code,
                    duration,
                )

                return response

            except Exception as e:
                # Track error
                track_error(self.service_name, type(e).__name__)
                raise

            finally:
                # Decrement active requests
                active_requests.labels(service=self.service_name).dec()

        return wrapper


# Export convenience items
__all__ = [
    "setup_tracing",
    "setup_metrics",
    "instrument_fastapi",
    "instrument_sqlalchemy",
    "instrument_redis",
    "get_tracer",
    "get_meter",
    "trace_span",
    "trace_function",
    "track_request",
    "track_error",
    "track_db_query",
    "track_cache",
    "track_event_published",
    "track_event_consumed",
    "RequestTracker",
]
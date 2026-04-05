"""
Prometheus metrics for FMP-KG integration monitoring.

Metrics:
- fmp_sync_requests_total: Counter for sync requests by status and asset type
- fmp_sync_duration_seconds: Histogram for sync operation duration
- fmp_markets_total: Gauge for total markets in Neo4j
- fmp_active_markets: Gauge for active markets
- neo4j_query_errors_total: Counter for Neo4j query errors
- neo4j_query_duration_seconds: Histogram for Neo4j query duration
- circuit_breaker_state: Gauge for circuit breaker state (0=closed, 1=open, 2=half_open)
"""

from prometheus_client import Counter, Histogram, Gauge
from typing import Optional
import time
from contextlib import contextmanager

# Sync request metrics
fmp_sync_requests_total = Counter(
    'fmp_sync_requests_total',
    'Total number of FMP sync requests',
    ['status', 'asset_type']
)

fmp_sync_duration_seconds = Histogram(
    'fmp_sync_duration_seconds',
    'Duration of FMP sync operations in seconds',
    ['asset_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

# Market metrics
fmp_markets_total = Gauge(
    'fmp_markets_total',
    'Total number of markets in Neo4j',
    ['asset_type']
)

fmp_active_markets = Gauge(
    'fmp_active_markets',
    'Number of active markets',
    ['asset_type']
)

# Neo4j metrics
neo4j_query_errors_total = Counter(
    'neo4j_query_errors_total',
    'Total number of Neo4j query errors',
    ['query_type', 'error_type']
)

neo4j_query_duration_seconds = Histogram(
    'neo4j_query_duration_seconds',
    'Duration of Neo4j queries in seconds',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]  # Sub-millisecond to seconds
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service']
)


# Helper functions for recording metrics

def record_sync_request(status: str, asset_type: Optional[str] = None) -> None:
    """
    Record a sync request.

    Args:
        status: Request status (success, partial, failed)
        asset_type: Asset type being synced (STOCK, FOREX, etc.) or 'all'
    """
    fmp_sync_requests_total.labels(
        status=status,
        asset_type=asset_type or 'all'
    ).inc()


@contextmanager
def record_sync_duration(asset_type: Optional[str] = None):
    """
    Context manager to record sync operation duration.

    Usage:
        with record_sync_duration(asset_type='STOCK'):
            # perform sync operation
            pass

    Args:
        asset_type: Asset type being synced or 'all'
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        fmp_sync_duration_seconds.labels(
            asset_type=asset_type or 'all'
        ).observe(duration)


def update_market_counts(total_by_type: dict, active_by_type: dict) -> None:
    """
    Update market count gauges.

    Args:
        total_by_type: Dict of {asset_type: total_count}
        active_by_type: Dict of {asset_type: active_count}
    """
    for asset_type, count in total_by_type.items():
        fmp_markets_total.labels(asset_type=asset_type).set(count)

    for asset_type, count in active_by_type.items():
        fmp_active_markets.labels(asset_type=asset_type).set(count)


@contextmanager
def record_neo4j_query(query_type: str):
    """
    Context manager to record Neo4j query duration and errors.

    Usage:
        with record_neo4j_query('merge_market'):
            # execute query
            pass

    Args:
        query_type: Type of query (merge_market, get_market, etc.)
    """
    start_time = time.time()
    try:
        yield
    except Exception as e:
        # Record error
        error_type = type(e).__name__
        neo4j_query_errors_total.labels(
            query_type=query_type,
            error_type=error_type
        ).inc()
        raise
    finally:
        # Record duration
        duration = time.time() - start_time
        neo4j_query_duration_seconds.labels(
            query_type=query_type
        ).observe(duration)


def update_circuit_breaker_state(service: str, state: str) -> None:
    """
    Update circuit breaker state gauge.

    Args:
        service: Service name (fmp_service, neo4j, etc.)
        state: Circuit breaker state (closed, open, half_open)
    """
    state_map = {
        'closed': 0,
        'open': 1,
        'half_open': 2
    }

    circuit_breaker_state.labels(
        service=service
    ).set(state_map.get(state.lower(), 0))

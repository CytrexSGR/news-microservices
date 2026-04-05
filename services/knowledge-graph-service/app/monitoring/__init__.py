"""
Monitoring and observability components for Knowledge-Graph Service.

This package provides:
- Prometheus metrics for FMP-KG integration
- Structured logging with correlation IDs
- Performance tracking
- Circuit breaker monitoring
"""

from .metrics import (
    fmp_sync_requests_total,
    fmp_sync_duration_seconds,
    fmp_markets_total,
    fmp_active_markets,
    neo4j_query_errors_total,
    neo4j_query_duration_seconds,
    circuit_breaker_state,
    record_sync_request,
    record_sync_duration,
    update_market_counts,
    record_neo4j_query,
    update_circuit_breaker_state,
)

__all__ = [
    "fmp_sync_requests_total",
    "fmp_sync_duration_seconds",
    "fmp_markets_total",
    "fmp_active_markets",
    "neo4j_query_errors_total",
    "neo4j_query_duration_seconds",
    "circuit_breaker_state",
    "record_sync_request",
    "record_sync_duration",
    "update_market_counts",
    "record_neo4j_query",
    "update_circuit_breaker_state",
]

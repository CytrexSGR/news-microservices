"""
Monitoring API endpoints

Provides:
- Circuit breaker metrics
- Query performance statistics
- WebSocket connection stats
- System health metrics
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import structlog

from app.core.auth import get_current_user
from app.core.resilience import get_all_circuit_breaker_metrics
from app.core.query_monitor import get_query_monitor, recommend_indexes
from app.api.websocket import manager

logger = structlog.get_logger()

router = APIRouter()


@router.get("/monitoring/circuit-breakers")
async def get_circuit_breaker_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get status of all circuit breakers

    Returns metrics for each service's circuit breaker including:
    - Current state (closed/open/half-open)
    - Success/failure counts
    - State transition history
    """
    metrics = get_all_circuit_breaker_metrics()

    return {
        "circuit_breakers": metrics,
        "total_services": len(metrics),
        "open_circuits": sum(1 for m in metrics.values() if m["state"] == "open"),
        "half_open_circuits": sum(1 for m in metrics.values() if m["state"] == "half_open")
    }


@router.get("/monitoring/query-performance")
async def get_query_performance(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get database query performance statistics

    Returns:
    - Query execution counts
    - Response times (min/max/avg)
    - Slow query list
    - Index recommendations
    """
    monitor = get_query_monitor()
    stats = monitor.get_statistics()
    slow_queries = monitor.get_slow_queries(limit=20)
    recommendations = recommend_indexes(stats)

    return {
        **stats,
        "slow_queries": slow_queries,
        "index_recommendations": recommendations
    }


@router.post("/monitoring/query-performance/reset")
async def reset_query_statistics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """Reset query performance statistics"""
    monitor = get_query_monitor()
    monitor.reset_statistics()

    return {
        "message": "Query statistics reset successfully"
    }


@router.get("/monitoring/websocket")
async def get_websocket_stats(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get WebSocket connection statistics

    Returns:
    - Total connections
    - Connection details (user, subscriptions, uptime)
    - Connection health
    """
    return manager.get_connection_stats()


@router.get("/monitoring/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get comprehensive system health status

    Returns health metrics for:
    - Circuit breakers
    - Database queries
    - WebSocket connections
    """
    circuit_breakers = get_all_circuit_breaker_metrics()
    query_stats = get_query_monitor().get_statistics()
    ws_stats = manager.get_connection_stats()

    # Determine overall health
    open_circuits = sum(1 for m in circuit_breakers.values() if m["state"] == "open")
    slow_queries = sum(
        1 for q in query_stats.get("top_queries", [])
        if q["avg_time_ms"] > 100
    )

    health_status = "healthy"
    issues = []

    if open_circuits > 0:
        health_status = "degraded"
        issues.append(f"{open_circuits} circuit breaker(s) open")

    if slow_queries > 5:
        health_status = "degraded"
        issues.append(f"{slow_queries} slow query patterns detected")

    if open_circuits > 3:
        health_status = "unhealthy"

    return {
        "status": health_status,
        "issues": issues,
        "metrics": {
            "circuit_breakers": {
                "total": len(circuit_breakers),
                "open": open_circuits,
                "closed": sum(1 for m in circuit_breakers.values() if m["state"] == "closed")
            },
            "database": {
                "total_queries": query_stats.get("total_queries", 0),
                "unique_patterns": query_stats.get("unique_patterns", 0),
                "slow_queries": slow_queries
            },
            "websocket": {
                "total_connections": ws_stats.get("total_connections", 0)
            }
        }
    }

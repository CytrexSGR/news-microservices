"""
Health Check Endpoints

Provides health status for the Knowledge Graph Service.
Includes Kubernetes-style liveness and readiness probes.
Enhanced with Prometheus metrics exposition for FMP-KG integration monitoring.
"""

import time
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
from datetime import datetime

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.services.neo4j_service import neo4j_service
from app.consumers.relationships_consumer import relationships_consumer
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Track service start time
_service_start_time = time.time()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        200 OK if service is running with basic status info
    """
    return {
        "status": "healthy",
        "service": "knowledge-graph-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe.

    Returns:
        200 OK if service is alive (process is running)
        Should restart container if this fails
    """
    return {
        "status": "alive",
        "service": "knowledge-graph-service"
    }


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe.

    Returns:
        200 OK if service is ready to accept traffic
        503 if not ready (e.g., dependencies not connected)
    """
    checks = {}
    ready = True

    # Check Neo4j connection
    try:
        neo4j_healthy = await neo4j_service.health_check()
        checks["neo4j"] = "healthy" if neo4j_healthy else "unhealthy"
        if not neo4j_healthy:
            ready = False
    except Exception as e:
        checks["neo4j"] = f"error: {str(e)}"
        ready = False

    # Check RabbitMQ consumer
    try:
        consumer_connected = relationships_consumer.connection and not relationships_consumer.connection.is_closed
        checks["rabbitmq_consumer"] = "healthy" if consumer_connected else "not_connected"
        if not consumer_connected:
            ready = False
    except Exception as e:
        checks["rabbitmq_consumer"] = f"error: {str(e)}"
        ready = False

    if not ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks,
                "message": "Service dependencies are not healthy"
            }
        )

    return {
        "status": "ready",
        "checks": checks,
        "service": "knowledge-graph-service"
    }


@router.get("/health/neo4j")
async def neo4j_health() -> Dict[str, Any]:
    """
    Detailed Neo4j health check.

    Returns:
        Detailed Neo4j connection status and statistics
    """
    try:
        # Check connection
        is_healthy = await neo4j_service.health_check()

        if not is_healthy:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "message": "Neo4j connection failed"
                }
            )

        # Get database info
        try:
            db_info = await neo4j_service.execute_query("CALL dbms.components() YIELD name, versions, edition")
            version = db_info[0]["versions"][0] if db_info else "unknown"
            edition = db_info[0]["edition"] if db_info else "unknown"
        except Exception:
            version = "unknown"
            edition = "unknown"

        return {
            "status": "healthy",
            "connected": True,
            "version": version,
            "edition": edition,
            "host": settings.NEO4J_URI
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": f"Neo4j health check failed: {str(e)}"
            }
        )


@router.get("/health/rabbitmq")
async def rabbitmq_health() -> Dict[str, Any]:
    """
    Detailed RabbitMQ consumer health check.

    Returns:
        RabbitMQ connection status and consumer details
    """
    try:
        consumer = relationships_consumer

        # Check connection
        is_connected = consumer.connection and not consumer.connection.is_closed
        channel_open = consumer.channel and not consumer.channel.is_closed

        if not is_connected or not channel_open:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "connection": "closed" if not is_connected else "open",
                    "channel": "closed" if not channel_open else "open",
                    "message": "RabbitMQ consumer not connected"
                }
            )

        # Get queue info
        queue_info = {}
        try:
            if consumer.queue:
                queue_decl = await consumer.queue.declare(passive=True)
                queue_info = {
                    "name": consumer.queue.name,
                    "message_count": queue_decl.message_count,
                    "consumer_count": queue_decl.consumer_count
                }
        except Exception:
            queue_info = {"name": settings.RABBITMQ_QUEUE, "status": "info_unavailable"}

        return {
            "status": "healthy",
            "connection": "open",
            "channel": "open",
            "exchange": settings.RABBITMQ_EXCHANGE,
            "queue": queue_info,
            "routing_key": settings.RABBITMQ_ROUTING_KEY
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": f"RabbitMQ health check failed: {str(e)}"
            }
        )


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus Metrics Exposition",
    description="Returns Prometheus metrics in exposition format for FMP-KG integration monitoring"
)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics for:
    - FMP sync operations (requests, duration, market counts)
    - Neo4j query performance
    - Circuit breaker state
    - Error rates

    Returns:
        Metrics in Prometheus exposition format
    """
    try:
        metrics_output = generate_latest()
        return Response(
            content=metrics_output,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {str(e)}")
        return Response(
            content=f"# Error generating metrics: {str(e)}",
            status_code=500,
            media_type=CONTENT_TYPE_LATEST
        )

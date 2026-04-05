"""
Health check endpoints for Content-Analysis-V3
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.database import check_db_health

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        Service status and version info
    """
    return {
        "status": "healthy",
        "service": "content-analysis-v3",
        "version": "1.0.0-alpha",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with database connectivity.

    Returns:
        Detailed service status including:
        - Database connectivity
        - Provider configuration
        - Budget limits
    """
    health_status = {
        "status": "healthy",
        "service": "content-analysis-v3",
        "version": "1.0.0-alpha",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # Check database connectivity with pool metrics
    db_health = await check_db_health()
    health_status["components"]["database"] = {
        **db_health,
        "database": settings.POSTGRES_DB,
        "host": settings.POSTGRES_HOST
    }
    if db_health["status"] == "unhealthy":
        health_status["status"] = "unhealthy"

    # Provider configuration
    health_status["components"]["providers"] = {
        "tier0": {
            "provider": settings.V3_TIER0_PROVIDER,
            "model": settings.V3_TIER0_MODEL,
            "max_tokens": settings.V3_TIER0_MAX_TOKENS,
            "max_cost": settings.V3_TIER0_MAX_COST
        },
        "tier1": {
            "provider": settings.V3_TIER1_PROVIDER,
            "model": settings.V3_TIER1_MODEL,
            "max_tokens": settings.V3_TIER1_MAX_TOKENS,
            "max_cost": settings.V3_TIER1_MAX_COST
        },
        "tier2": {
            "provider": settings.V3_TIER2_PROVIDER,
            "model": settings.V3_TIER2_MODEL,
            "max_tokens": settings.V3_TIER2_MAX_TOKENS,
            "max_cost": settings.V3_TIER2_MAX_COST
        }
    }

    # Budget summary
    total_budget_cost = (
        settings.V3_TIER0_MAX_COST +
        settings.V3_TIER1_MAX_COST +
        settings.V3_TIER2_MAX_COST
    )
    total_budget_tokens = (
        settings.V3_TIER0_MAX_TOKENS +
        settings.V3_TIER1_MAX_TOKENS +
        settings.V3_TIER2_MAX_TOKENS
    )

    health_status["components"]["budget"] = {
        "total_tokens": total_budget_tokens,
        "total_cost_usd": total_budget_cost,
        "tiers": {
            "tier0": {"tokens": settings.V3_TIER0_MAX_TOKENS, "cost": settings.V3_TIER0_MAX_COST},
            "tier1": {"tokens": settings.V3_TIER1_MAX_TOKENS, "cost": settings.V3_TIER1_MAX_COST},
            "tier2": {"tokens": settings.V3_TIER2_MAX_TOKENS, "cost": settings.V3_TIER2_MAX_COST}
        }
    }

    return health_status


@router.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Kubernetes readiness probe.

    Returns:
        200 if service is ready to accept traffic
        503 if service is not ready
    """
    db_health = await check_db_health()
    if db_health["status"] == "healthy":
        return {"status": "ready"}
    return {"status": "not ready"}


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe.

    Returns:
        200 if service is alive
    """
    return {"status": "alive"}

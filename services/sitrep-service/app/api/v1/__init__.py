# services/sitrep-service/app/api/v1/__init__.py
"""API v1 routers.

Exports:
    health_router: Health check endpoints (/health, /ready)
    sitrep_router: SITREP API endpoints (/api/v1/sitreps/*)
"""

from fastapi import APIRouter

from app.config import settings
from app.api.v1.sitreps import router as sitrep_api_router

# Health router - standalone endpoints
health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@health_router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Check database and RabbitMQ connections
    return {"status": "ready"}


# SITREP router - includes all SITREP API endpoints
sitrep_router = sitrep_api_router


# Re-export routers
__all__ = ["health_router", "sitrep_router"]

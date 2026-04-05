"""API routes for Research Service."""

from fastapi import APIRouter
from app.api import research, templates, runs
from app.services.perplexity import perplexity_client
from app.core.config import settings

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(research.router)
api_router.include_router(templates.router)
api_router.include_router(runs.router)


@api_router.get("/health")
async def health_check_api():
    """Health check endpoint (API versioned path)."""
    # Check Perplexity API
    perplexity_available = await perplexity_client.check_health()

    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "perplexity_api": perplexity_available,
    }


__all__ = ["api_router"]

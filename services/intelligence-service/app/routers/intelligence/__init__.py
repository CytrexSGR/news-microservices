"""
Intelligence Router Module
Combines all intelligence sub-routers into a single router
"""
from fastapi import APIRouter

from .overview import router as overview_router
from .clusters import router as clusters_router
from .events import router as events_router
from .risk import router as risk_router

# Create main router with prefix
router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

# Include all sub-routers
router.include_router(overview_router)
router.include_router(clusters_router)
router.include_router(events_router)
router.include_router(risk_router)

__all__ = ["router"]

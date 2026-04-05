# services/clustering-service/app/api/v1/__init__.py
"""API v1 module."""

from fastapi import APIRouter

from app.api.v1.clusters import router as clusters_router
from app.api.v1.bursts import router as bursts_router
from app.api.v1.batch_clusters import router as batch_clusters_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.escalation import router as escalation_router

api_router = APIRouter()
api_router.include_router(clusters_router, prefix="/clusters", tags=["clusters"])
api_router.include_router(bursts_router, prefix="/bursts", tags=["bursts"])
api_router.include_router(batch_clusters_router, prefix="/topics", tags=["topics"])
api_router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
api_router.include_router(escalation_router, tags=["escalation"])

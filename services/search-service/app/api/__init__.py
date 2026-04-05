"""API routers"""
from fastapi import APIRouter

from app.api import search, saved_searches, history, admin

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(saved_searches.router, prefix="/search/saved", tags=["saved-searches"])
api_router.include_router(history.router, prefix="/search/history", tags=["history"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

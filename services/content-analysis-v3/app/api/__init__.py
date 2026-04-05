"""
API routers for Content-Analysis-V3
"""

from app.api.health import router as health_router
from app.api.analysis import router as analysis_router

__all__ = [
    "health_router",
    "analysis_router"
]

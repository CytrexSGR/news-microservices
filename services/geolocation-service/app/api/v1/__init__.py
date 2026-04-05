"""API v1 routers for geolocation-service."""
from app.api.v1.locations import router as locations_router
from app.api.v1.map import router as map_router
from app.api.v1.filters import router as filters_router
from app.api.v1.ws_stats import router as ws_stats_router

__all__ = ["locations_router", "map_router", "filters_router", "ws_stats_router"]

# API module
from app.api.analytics import router as analytics_router
from app.api.dashboards import router as dashboards_router
from app.api.reports import router as reports_router
from app.api.widgets import router as widgets_router
from app.api.cache import router as cache_router  # Task 403
from app.api.routes.health import router as health_router  # Health monitoring
from app.api.websocket import router as websocket_router  # WebSocket support
from app.api.monitoring import router as monitoring_router  # System monitoring
from app.api.intelligence import router as intelligence_router  # Twitter Intelligence

__all__ = [
    "analytics_router",
    "dashboards_router",
    "reports_router",
    "widgets_router",
    "cache_router",  # Task 403
    "health_router",  # Health monitoring
    "websocket_router",  # WebSocket support
    "monitoring_router",  # System monitoring
    "intelligence_router"  # Twitter Intelligence
]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import shared rate limiting
import sys
sys.path.insert(0, '/home/cytrex/news-microservices/services')
from common.rate_limiting import setup_rate_limiting

# Import API routers
from app.api import (
    analytics_router,
    dashboards_router,
    reports_router,
    widgets_router,
    cache_router,  # Task 403
    health_router,  # Health monitoring
    websocket_router,  # WebSocket support
    monitoring_router,  # System monitoring
    intelligence_router  # Twitter Intelligence
)

app = FastAPI(
    title="Analytics Service",
    description="News analytics and reporting service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limiting (Redis-backed)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
setup_rate_limiting(app, redis_url)

# Include API routers
app.include_router(
    analytics_router,
    prefix="/api/v1/analytics",
    tags=["analytics"]
)

app.include_router(
    dashboards_router,
    prefix="/api/v1",
    tags=["dashboards"]
)

app.include_router(
    reports_router,
    prefix="/api/v1",
    tags=["reports"]
)

app.include_router(
    widgets_router,
    prefix="/api/v1",
    tags=["widgets"]
)

# Task 403: Cache monitoring endpoint
app.include_router(
    cache_router,
    tags=["cache"]
)

# Health monitoring endpoint
app.include_router(
    health_router,
    prefix="/api/v1/health",
    tags=["health"]
)

# WebSocket endpoint
app.include_router(
    websocket_router,
    tags=["websocket"]
)

# System monitoring endpoint
app.include_router(
    monitoring_router,
    prefix="/api/v1",
    tags=["monitoring"]
)

# Intelligence endpoints (Twitter Intelligence)
app.include_router(
    intelligence_router,
    prefix="/api/v1/intelligence",
    tags=["intelligence"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "analytics-service",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "analytics-service",
        "message": "Analytics service is running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api": {
                "analytics": "/api/v1/analytics",
                "dashboards": "/api/v1/dashboards",
                "reports": "/api/v1/reports"
            }
        }
    }

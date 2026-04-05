"""Geolocation Service - Main Application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import locations, map, filters, ws_stats, security, watchlist
from app.api import websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.SERVICE_NAME}")
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title="Geolocation Service",
    description="Geographic visualization for news articles",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


# Register API routers
app.include_router(locations.router, prefix="/api/v1")
app.include_router(map.router, prefix="/api/v1")
app.include_router(filters.router, prefix="/api/v1")
app.include_router(ws_stats.router, prefix="/api/v1")
app.include_router(security.router, prefix="/api/v1")
app.include_router(watchlist.router, prefix="/api/v1")

# WebSocket endpoint
app.include_router(websocket.router)

# services/clustering-service/app/main.py
"""Clustering Service - Groups related news articles into clusters."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1 import api_router
from app.config import settings
from app.services.event_publisher import close_event_publisher
from app.workers.analysis_consumer import analysis_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.SERVICE_NAME}...")

    # Start RabbitMQ consumer
    await analysis_consumer.start()

    yield

    # Cleanup
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
    await analysis_consumer.stop()
    await close_event_publisher()


app = FastAPI(
    title="Clustering Service",
    description="Groups related news articles into story clusters",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Check database and RabbitMQ connections
    return {"status": "ready"}

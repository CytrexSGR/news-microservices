"""MediaStack Service - News API Integration."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import news_router
from app.services.usage_tracker import get_usage_tracker
from app.clients.mediastack_client import get_mediastack_client

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.SERVICE_NAME} on port {settings.SERVICE_PORT}")

    # Initialize connections
    tracker = get_usage_tracker()
    await tracker.connect()
    logger.info("Usage tracker connected to Redis")

    yield

    # Cleanup
    await tracker.disconnect()
    client = get_mediastack_client()
    await client.close()
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title="MediaStack Service",
    description="News API integration for mass URL discovery",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.SERVICE_NAME}

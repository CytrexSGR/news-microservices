"""
Narrative Service - Main Application
Provides frame detection, bias analysis, and propaganda detection for news narratives.
"""
import sys
import asyncio
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared.auth import get_current_user, UserInfo
from app.database import init_db, close_db
from app.routers import narrative
from app.config import settings
from app import cache as cache_module
from app.events.consumer import get_consumer, close_consumer

# Create auth dependency
get_user = get_current_user(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management for the application

    Startup:
    - Initialize database connection
    - Initialize cache manager
    - Start RabbitMQ event consumer

    Shutdown:
    - Close RabbitMQ consumer
    - Close cache manager
    - Close database connections
    """
    logger.info("Narrative Service starting up...")

    # Initialize database connection
    await init_db()

    # Initialize cache manager
    if settings.CACHE_ENABLED:
        cache_module.cache_manager = cache_module.NarrativeCacheManager(settings.REDIS_URL)
        await cache_module.cache_manager.connect()
        logger.info("Cache manager initialized")
    else:
        logger.info("Cache disabled via configuration")

    # Start RabbitMQ consumer in background
    consumer = get_consumer()
    consumer_task = asyncio.create_task(consumer.start_consuming())
    logger.info("RabbitMQ event consumer started for narrative.frame.detected events")

    yield

    # Shutdown logic
    # Close RabbitMQ consumer
    await close_consumer()
    logger.info("RabbitMQ consumer closed")

    if cache_module.cache_manager:
        await cache_module.cache_manager.close()

    await close_db()
    logger.info("Narrative Service shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Narrative Service",
    description="News Narrative Analysis - Frame Detection, Bias Analysis & Propaganda Detection",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (Security - Week 1 Fix)
# FIXED: Replaced wildcard with environment-based whitelist
# Protects against CSRF attacks, session hijacking, data exfiltration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(narrative.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "narrative",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Narrative Service",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Scraping Service - Main Application

Autonomous content scraping service with multi-strategy support.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.services.scraper import scraper
from app.services.failure_tracker import failure_tracker
from app.workers.scraping_worker import scraping_worker
from app.workers.queue_worker import queue_worker
from app.api import wikipedia
from app.core.rate_limiter import rate_limiter
from app.core.concurrency import concurrency_limiter
from app.core.retry import retry_handler
from app.db import init_async_db, AsyncSessionLocal
from app.services.source_registry import initialize_source_registry

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
    - Initialize database and create tables
    - Initialize source registry (load profiles from DB)
    - Initialize scraper (httpx + Playwright)
    - Initialize failure tracker (Redis)
    - Start RabbitMQ worker

    Shutdown:
    - Stop worker
    - Close all connections
    """
    logger.info(f"Starting {settings.SERVICE_NAME}")

    # Initialize database (create tables if not exist)
    try:
        await init_async_db()
        logger.info("Database initialized (source_profiles table ready)")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Initialize source registry with database
    try:
        await initialize_source_registry(AsyncSessionLocal)
        logger.info("Source Registry initialized with database persistence")
    except Exception as e:
        logger.error(f"Source Registry initialization failed: {e}")

    # Initialize services
    await scraper.start()
    await failure_tracker.start()
    await scraping_worker.start()
    await queue_worker.start()

    logger.info("Scraping service fully initialized (RabbitMQ + Priority Queue workers active)")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    await queue_worker.stop()
    await scraping_worker.stop()
    await failure_tracker.stop()
    await scraper.stop()
    logger.info("Scraping service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Scraping Service",
    description="Autonomous content scraping with Playwright and httpx",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api import monitoring
from app.api import source_profiles
from app.api import dlq
from app.api import metrics
from app.api import cache
from app.api import proxy
from app.api import queue
from app.api import scrape
app.include_router(wikipedia.router)
app.include_router(monitoring.router)
app.include_router(source_profiles.router)
app.include_router(dlq.router)
app.include_router(metrics.router)
app.include_router(cache.router)
app.include_router(proxy.router)
app.include_router(queue.router)
app.include_router(scrape.router)


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns service health including:
    - Overall status
    - Rate limiter status
    - Concurrency stats
    - Retry stats
    - Browser status
    """
    # Check if browser is initialized
    browser_status = "not_initialized" if not scraper.browser else "initialized"

    # Get concurrency stats
    concurrency_stats = concurrency_limiter.get_stats()

    # Get retry stats
    retry_stats = retry_handler.get_stats()

    # Check Redis connection (rate limiter)
    redis_status = "connected" if rate_limiter.redis else "disconnected"

    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "components": {
            "browser": browser_status,
            "redis": redis_status,
            "rate_limiter": {
                "status": redis_status,
                "fail_open": redis_status == "disconnected"
            },
            "concurrency": {
                "max_concurrent": concurrency_stats["max_concurrent"],
                "active_jobs": concurrency_stats["active_jobs"],
                "available_slots": concurrency_stats["available_slots"],
                "total_processed": concurrency_stats["total_jobs"],
                "success_rate": f"{concurrency_stats['success_rate']:.2%}"
            },
            "retry": {
                "total_retries": retry_stats["total_retries"],
                "successful_retries": retry_stats["successful_retries"],
                "failed_retries": retry_stats["failed_retries"],
                "success_rate": f"{retry_stats['success_rate']:.2%}"
            }
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "description": "Autonomous content scraping service",
        "methods": ["httpx", "playwright", "auto"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)

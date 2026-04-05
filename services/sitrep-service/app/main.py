# services/sitrep-service/app/main.py
"""SITREP Service - Intelligence Briefing Generation."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.config import settings
from app.api.v1 import health_router, sitrep_router
from app.db.session import init_db, close_db
from app.workers.cluster_consumer import start_consumer, stop_consumer
from app.workers.scheduled_generator import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start RabbitMQ consumer for cluster events
    aggregator = None
    try:
        aggregator = await start_consumer()
        logger.info("Cluster event consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start cluster consumer: {e}")
        # Continue starting the service even if consumer fails
        # This allows health checks and manual SITREP generation

    # Start scheduled SITREP generator (requires aggregator)
    if aggregator is not None:
        try:
            await start_scheduler(aggregator)
            logger.info(
                f"Scheduled SITREP generator started "
                f"(generation hour: {settings.SITREP_GENERATION_HOUR}:00 UTC)"
            )
        except Exception as e:
            logger.error(f"Failed to start scheduled generator: {e}")
            # Continue without scheduler - manual generation still available
    else:
        logger.warning(
            "Scheduled SITREP generator not started (no aggregator available)"
        )

    yield

    # Cleanup
    await stop_scheduler()
    await stop_consumer()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="SITREP Service",
    description="Intelligence Briefing Generation from News Clusters",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Register routers
app.include_router(health_router, tags=["Health"])
app.include_router(sitrep_router, prefix="/api/v1", tags=["SITREP"])

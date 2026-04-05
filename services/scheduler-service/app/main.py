"""
Scheduler Service - Main Application

Orchestrates automated feed monitoring and multi-stage analysis.
"""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api import scheduler_api
from app.api import health
from app.core.metrics import get_metrics
from app.services.feed_monitor import feed_monitor
from app.services.job_processor import job_processor
from app.services.cron_scheduler import cron_scheduler
from app.services.entity_kg_processor import process_entities_job
from app.services.entity_deduplicator import run_deduplication
from app.services.proposal_auto_approver import auto_approve_proposals_job

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
    - Initialize database
    - Start feed monitor (creates jobs every 60s)
    - Start job processor (processes jobs every 30s)
    - Start cron scheduler (for flexible custom tasks)

    Shutdown:
    - Stop all schedulers
    - Close database connections
    """
    logger.info(f"Starting {settings.SERVICE_NAME}")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Start feed monitor (creates analysis jobs)
    await feed_monitor.start()
    logger.info("Feed monitor started")

    # Start job processor (processes analysis jobs from queue)
    await job_processor.start()
    logger.info("Job processor started")

    # Start cron scheduler (for custom scheduled tasks)
    cron_scheduler.start()
    logger.info("Cron scheduler started")

    # Register entity processing job (runs every 30 seconds)
    cron_scheduler.add_interval_job(
        job_id="process_entities_for_kg",
        func=process_entities_job,
        seconds=30,
        name="Process Entities for Knowledge Graph"
    )
    logger.info("Entity KG processor job registered (every 30s)")

    # Register entity deduplication job (runs daily at 3:00 AM)
    # Merges duplicate entities with same name (case-insensitive) AND same type
    async def deduplication_job():
        result = await run_deduplication(dry_run=False)
        logger.info(f"Entity deduplication completed: {result}")

    cron_scheduler.add_cron_job(
        job_id="entity_deduplication",
        func=deduplication_job,
        cron_expression="0 3 * * *",  # Daily at 3:00 AM
        name="Entity Deduplication (Neo4j)"
    )
    logger.info("Entity deduplication job registered (daily at 3:00 AM, dry_run=True)")

    # Register proposal auto-approval job (runs every 5 minutes)
    # Automatically approves and implements high-confidence ontology proposals
    cron_scheduler.add_interval_job(
        job_id="proposal_auto_approver",
        func=auto_approve_proposals_job,
        seconds=300,  # 5 minutes
        name="Ontology Proposal Auto-Approver"
    )
    logger.info("Proposal auto-approver job registered (every 5 minutes)")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    await feed_monitor.stop()
    logger.info("Feed monitor stopped")

    await job_processor.stop()
    logger.info("Job processor stopped")

    cron_scheduler.stop()
    logger.info("Cron scheduler stopped")


# Create FastAPI application
app = FastAPI(
    title="Scheduler Service",
    description="Automated feed monitoring and analysis orchestration",
    version="0.1.0",
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
app.include_router(scheduler_api.router, prefix="/api/v1")
app.include_router(health.router)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "0.1.0",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)

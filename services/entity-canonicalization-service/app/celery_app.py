"""
Celery application for background job processing.

This module configures Celery for entity canonicalization batch processing.
Tasks run in separate worker processes to avoid blocking the FastAPI service.

Configuration:
- Broker: Redis (message queue)
- Backend: Redis (result storage)
- Serializer: JSON (secure, portable)
- Task time limit: 1 hour max (3600s)
- Soft time limit: 55 minutes (3300s)
- Prefetch: 1 task at a time (heavy tasks)

Usage:
    # Start worker
    celery -A app.celery_app worker --loglevel=info --concurrency=2

    # Monitor tasks
    celery -A app.celery_app inspect active
"""

import logging
from celery import Celery
from celery.signals import worker_ready, worker_shutdown

from app.config import settings

logger = logging.getLogger(__name__)

# Create Celery application
celery_app = Celery(
    'entity-canonicalization',
    broker=f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
    backend=f'redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
    include=['app.tasks.batch_reprocessing']
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Timezone
    timezone='UTC',
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max (hard limit)
    task_soft_time_limit=3300,  # 55 minutes (soft limit, raises exception)
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies

    # Worker
    worker_prefetch_multiplier=1,  # One task at a time (heavy batch processing)
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks (prevent memory leaks)
    worker_max_memory_per_child=400_000,  # 400 MB in KB - hard limit (uses SentenceTransformer)

    # Result backend
    result_expires=86400,  # Keep results for 24 hours
    result_extended=True,  # Store task args/kwargs in result

    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Signal handler: Worker started successfully."""
    logger.info("Celery worker ready for entity canonicalization tasks")


@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """Signal handler: Worker shutting down."""
    logger.info("Celery worker shutting down")

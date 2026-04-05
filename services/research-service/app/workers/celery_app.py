"""
Celery application configuration for Research Service.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "research_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.RESEARCH_TIMEOUT,
    task_soft_time_limit=settings.RESEARCH_TIMEOUT - 30,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200_000,  # 200 MB in KB - hard limit per child
    result_expires=3600,  # 1 hour
    task_reject_on_worker_lost=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,  # For testing
)

# Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Process scheduled research tasks every 15 minutes
    "process-scheduled-research": {
        "task": "research.scheduled_research_task",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "options": {"expires": 900},
    },
    # Clean up expired cache daily at 3 AM
    "cleanup-expired-cache": {
        "task": "research.cache_cleanup_task",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM
        "options": {"expires": 3600},
    },
    # Aggregate daily costs at 1 AM
    "aggregate-daily-costs": {
        "task": "research.cost_aggregation_task",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1:00 AM
        "options": {"expires": 3600},
    },
    # Health check every 5 minutes
    "health-check": {
        "task": "research.health_check",
        "schedule": 300.0,  # Every 5 minutes
        "options": {"expires": 60},
    },
}

# Set up routing for tasks
celery_app.conf.task_routes = {
    "research.research_task": {"queue": "research"},
    "research.scheduled_research_task": {"queue": "research_scheduled"},
    "research.batch_research_task": {"queue": "research_batch"},
    "research.cache_cleanup_task": {"queue": "maintenance"},
    "research.cost_aggregation_task": {"queue": "maintenance"},
    "research.health_check": {"queue": "health"},
}

# Configure task priorities
celery_app.conf.task_annotations = {
    "research.research_task": {"priority": 5},
    "research.scheduled_research_task": {"priority": 3},
    "research.batch_research_task": {"priority": 4},
    "research.cache_cleanup_task": {"priority": 1},
    "research.cost_aggregation_task": {"priority": 1},
    "research.health_check": {"priority": 0},
}

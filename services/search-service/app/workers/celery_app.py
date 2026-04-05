"""
Celery application for background tasks
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "search_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=300_000,  # 300 MB in KB - hard limit per child
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'sync-articles-every-5-minutes': {
        'task': 'app.workers.tasks.sync_articles_task',
        'schedule': settings.INDEXING_INTERVAL,  # 5 minutes
    },
}

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "analytics_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.workers.tasks']
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200_000,  # 200 MB in KB - hard limit per child
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'collect-metrics-every-minute': {
        'task': 'app.workers.tasks.collect_metrics_task',
        'schedule': float(settings.METRICS_COLLECTION_INTERVAL),
        'options': {'queue': 'analytics'},  # Route to analytics queue
    },
    'cleanup-old-metrics-daily': {
        'task': 'app.workers.tasks.cleanup_old_metrics_task',
        'schedule': 86400.0,  # Daily
        'options': {'queue': 'analytics'},  # Route to analytics queue
    },
}

# Task routing - ensure analytics tasks go to analytics queue
celery_app.conf.task_routes = {
    'app.workers.tasks.collect_metrics_task': {'queue': 'analytics'},
    'app.workers.tasks.cleanup_old_metrics_task': {'queue': 'analytics'},
}

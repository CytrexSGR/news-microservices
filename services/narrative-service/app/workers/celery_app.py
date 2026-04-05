from celery import Celery
from app.config import settings

celery_app = Celery(
    "narrative_worker",
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
    # Add periodic narrative tasks here as needed
}

# Task routing - ensure narrative tasks go to narrative queue
celery_app.conf.task_routes = {
    'app.workers.tasks.*': {'queue': 'narrative'},
}

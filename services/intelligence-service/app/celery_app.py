"""
Celery application for Intelligence Service
"""
import os
from celery import Celery
from celery.schedules import crontab

# RabbitMQ connection (broker)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")

# Redis connection (backend) - with authentication
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis_secret_2024")
REDIS_URL = os.getenv("REDIS_URL", f"redis://:{REDIS_PASSWORD}@redis:6379/0")

# Create Celery app
celery_app = Celery(
    "intelligence",
    broker=RABBITMQ_URL,  # Use RabbitMQ for task queue
    backend=REDIS_URL,     # Use Redis for results storage
    include=["app.tasks.ingestion", "app.tasks.clustering"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # Recycle workers frequently to prevent memory buildup
    worker_max_memory_per_child=200_000,  # 200 MB in KB - hard limit per child
)

# Celery Beat Schedule - Periodic Tasks
celery_app.conf.beat_schedule = {
    # Ingest new articles every 10 minutes
    "ingest-articles-every-10min": {
        "task": "app.tasks.ingestion.ingest_recent_articles",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
        "kwargs": {"hours": 1, "limit": 500},  # Last 1 hour, max 500 articles
    },
    # Backfill events with analysis data every 15 minutes
    "enrich-events-every-15min": {
        "task": "app.tasks.ingestion.enrich_events_with_analysis",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "kwargs": {"hours": 2},  # Last 2 hours
    },
    # Update cluster metrics every 20 minutes
    "update-clusters-every-20min": {
        "task": "app.tasks.clustering.update_cluster_metrics",
        "schedule": crontab(minute="*/20"),  # Every 20 minutes
    },
    # Run full clustering every 30 minutes (optimized parameters for TF-IDF + cosine)
    "run-clustering-every-30min": {
        "task": "app.tasks.clustering.run_clustering_pipeline",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "kwargs": {"hours": 24, "min_samples": 2, "eps": 0.6},  # Optimized for TF-IDF vectors with cosine metric
    },
}

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.ingestion.*": {"queue": "intelligence-ingestion"},
    "app.tasks.clustering.*": {"queue": "intelligence-clustering"},
}

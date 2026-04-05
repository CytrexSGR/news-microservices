"""
Celery application configuration for Feed Service
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery app
celery_app = Celery(
    "feed_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.feed_tasks",
        "app.tasks.outbox_processor",
        "app.tasks.fmp_tasks",
        "app.tasks.relevance_batch",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=500,  # Recycle workers more frequently (was 1000)
    worker_max_memory_per_child=300_000,  # 300 MB in KB - hard limit per child
    result_expires=3600,  # 1 hour
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,  # For testing
)

# Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # ⚡ Outbox processor - CRITICAL for reliable event delivery
    # Runs every 5 seconds to publish pending events from outbox to RabbitMQ
    # Implements Outbox Pattern for transactional event publishing
    "process-outbox": {
        "task": "outbox_processor.process_outbox",
        "schedule": 5.0,  # Every 5 seconds (fast feedback)
        "options": {"expires": 10},  # Expire after 10 seconds if not run
    },
    # Fetch all active feeds every 5 minutes
    # This allows feeds with short intervals (10min, 30min) to be fetched on time
    "fetch-all-feeds": {
        "task": "feed.fetch_all_active",
        "schedule": 300.0,  # Every 5 minutes
        "options": {"expires": 300},  # Expire after 5 minutes if not run
    },
    # Clean up old items daily at 2 AM
    "cleanup-old-items": {
        "task": "feed.cleanup_old_items",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2:00 AM
        "kwargs": {"retention_days": 90},
        "options": {"expires": 3600},
    },
    # Health check every 5 minutes
    "health-check": {
        "task": "feed.health_check",
        "schedule": 300.0,  # Every 5 minutes
        "options": {"expires": 60},
    },
    # Calculate Feed Quality V2 scores daily at 3 AM
    "calculate-quality-scores": {
        "task": "feed.calculate_quality_scores",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM
        "kwargs": {"days": 30},  # Analyze last 30 days
        "options": {"expires": 3600},  # Expire after 1 hour if not run
    },
    # Auto-recover feeds stuck in ERROR state every 30 minutes
    # Prevents permanent ERROR states after network outages
    "auto-recover-failed-feeds": {
        "task": "feed.auto_recover_failed_feeds",
        "schedule": 1800.0,  # Every 30 minutes
        "kwargs": {"cooldown_minutes": 60},  # Recover feeds in ERROR for >60 minutes
        "options": {"expires": 600},  # Expire after 10 minutes if not run
    },
    # FMP News - Fetch all 5 categories with staggered scheduling
    # Rate limit safe: 5 calls over 5 minutes = 1 call/min = 0.33% of 300 calls/min limit
    "fmp-fetch-all-categories": {
        "task": "fmp.fetch_all_categories",
        "schedule": 300.0,  # Every 5 minutes (same interval as RSS fetches)
        "kwargs": {"limit": 20},  # Fetch 20 articles per category
        "options": {"expires": 300},  # Expire after 5 minutes if not run
    },
    # Update relevance scores using time-decay algorithm (Epic 2.2)
    # Recalculates scores for articles from last 7 days to reflect aging
    "update-relevance-scores": {
        "task": "feed.update_relevance_scores",
        "schedule": 1800.0,  # Every 30 minutes
        "kwargs": {"days": 7, "batch_size": 1000},
        "options": {"expires": 900},  # Expire after 15 minutes if not run
    },
    # Fetch web sources every 5 minutes
    "fetch-web-sources": {
        "task": "feed.fetch_web_sources",
        "schedule": 300.0,  # Every 5 minutes
        "options": {"queue": "feed_bulk", "expires": 300},
    },
}

# Set up routing for tasks
celery_app.conf.task_routes = {
    "outbox_processor.process_outbox": {"queue": "feed_outbox"},  # Dedicated queue
    "feed.fetch_single": {"queue": "feed_fetches"},
    "feed.fetch_all_active": {"queue": "feed_bulk"},
    "feed.cleanup_old_items": {"queue": "maintenance"},
    "feed.health_check": {"queue": "health"},
    "feed.calculate_quality_scores": {"queue": "maintenance"},  # Low priority maintenance task
    "feed.auto_recover_failed_feeds": {"queue": "maintenance"},  # Recovery task
    "fmp.fetch_all_categories": {"queue": "fmp_bulk"},  # FMP bulk fetch
    "fmp.fetch_category": {"queue": "fmp_fetches"},  # FMP individual category
    "fmp.test_single_category": {"queue": "fmp_fetches"},  # FMP test
    "feed.update_relevance_scores": {"queue": "maintenance"},  # Relevance batch update
    "feed.fetch_web_sources": {"queue": "feed_bulk"},  # Web source fetching
}

# Configure task priorities
celery_app.conf.task_annotations = {
    "feed.fetch_single": {"priority": 5},
    "feed.fetch_all_active": {"priority": 3},
    "feed.cleanup_old_items": {"priority": 1},
    "feed.health_check": {"priority": 0},
    "feed.calculate_quality_scores": {"priority": 1},  # Low priority, runs nightly
    "feed.auto_recover_failed_feeds": {"priority": 2},  # Medium-low priority recovery
    "fmp.fetch_all_categories": {"priority": 4},  # High priority (time-sensitive financial news)
    "fmp.fetch_category": {"priority": 5},  # Highest priority (real-time news)
    "feed.update_relevance_scores": {"priority": 2},  # Medium-low priority, batch maintenance
    "feed.fetch_web_sources": {"priority": 3},  # Web source fetching
}
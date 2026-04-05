# services/clustering-service/app/workers/__init__.py
"""Workers module for RabbitMQ consumers and Celery tasks."""

from app.workers.analysis_consumer import AnalysisConsumer, analysis_consumer

# Note: batch_clustering_worker is imported separately to avoid
# Celery initialization at import time. Import it directly when needed:
#   from app.workers.batch_clustering_worker import celery_app, recompute_clusters

__all__ = [
    "AnalysisConsumer",
    "analysis_consumer",
]

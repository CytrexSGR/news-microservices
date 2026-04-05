"""
Celery tasks for Intelligence Service
"""
from app.tasks.ingestion import ingest_recent_articles, enrich_events_with_analysis
from app.tasks.clustering import update_cluster_metrics, run_clustering_pipeline

__all__ = [
    "ingest_recent_articles",
    "enrich_events_with_analysis",
    "update_cluster_metrics",
    "run_clustering_pipeline",
]

"""
Celery tasks for clustering and cluster maintenance
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio

from app.celery_app import celery_app
from app.database import get_sync_db
from app.services.clustering import ClusteringService, calculate_time_window
from app.services.risk_scoring import RiskScoringService
from app.models.cluster import IntelligenceCluster
from app.models.event import IntelligenceEvent
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.clustering.update_cluster_metrics", bind=True)
def update_cluster_metrics(self) -> Dict[str, Any]:
    """
    Update metrics for all active clusters (event_count, risk_score, last_updated).
    Processes clusters in batches to limit memory usage.

    Returns:
        Statistics about cluster updates
    """
    logger.info("Starting cluster metrics update")

    BATCH_SIZE = 100

    start_time = datetime.utcnow()
    stats = {
        "task_id": self.request.id,
        "started_at": start_time.isoformat(),
        "clusters_updated": 0,
        "errors": 0,
    }

    try:
        from app.database import SyncSessionLocal
        from app.models.risk_history import IntelligenceRiskHistory

        # Pre-calculate week boundaries (same for all clusters)
        today = datetime.utcnow().date()
        current_week_start = today - timedelta(days=today.weekday())
        current_week_end = current_week_start + timedelta(days=6)
        previous_week_start = current_week_start - timedelta(days=7)

        risk_scorer = RiskScoringService()

        # Get total count first
        with SyncSessionLocal() as db:
            total_clusters = db.query(func.count(IntelligenceCluster.id)).filter(
                IntelligenceCluster.is_active == True
            ).scalar()

        logger.info(f"Processing {total_clusters} active clusters in batches of {BATCH_SIZE}")

        # Process in batches using offset/limit
        offset = 0
        while offset < total_clusters:
            with SyncSessionLocal() as db:
                # Fetch one batch of cluster IDs (lightweight query)
                cluster_ids = db.query(IntelligenceCluster.id).filter(
                    IntelligenceCluster.is_active == True
                ).order_by(IntelligenceCluster.id).offset(offset).limit(BATCH_SIZE).all()

                cluster_ids = [cid[0] for cid in cluster_ids]

                if not cluster_ids:
                    break

                for cluster_id in cluster_ids:
                    try:
                        # Load cluster + compute metrics with aggregated DB query
                        cluster = db.query(IntelligenceCluster).get(cluster_id)
                        if not cluster:
                            continue

                        # Use aggregated query instead of loading all events into memory
                        event_stats = db.query(
                            func.count(IntelligenceEvent.id).label("event_count"),
                            func.avg(IntelligenceEvent.sentiment).label("avg_sentiment"),
                            func.count(func.distinct(IntelligenceEvent.source)).label("unique_sources"),
                            func.max(IntelligenceEvent.published_at).label("newest_published"),
                        ).filter(
                            IntelligenceEvent.cluster_id == cluster_id
                        ).first()

                        if not event_stats or event_stats.event_count == 0:
                            continue

                        # Update event count
                        cluster.event_count = event_stats.event_count

                        current_metrics = {
                            "article_count": event_stats.event_count,
                            "avg_sentiment": float(event_stats.avg_sentiment or 0.0),
                            "unique_sources": event_stats.unique_sources,
                        }

                        # Recalculate risk score
                        risk_result = risk_scorer.calculate_risk_score(current_metrics)
                        new_risk_score = risk_result.get("risk_score", 0.0)

                        # Calculate risk_delta from historical data
                        old_risk_record = db.query(IntelligenceRiskHistory).filter(
                            IntelligenceRiskHistory.cluster_id == cluster_id,
                            IntelligenceRiskHistory.week_start == previous_week_start
                        ).first()

                        cluster.risk_delta = (new_risk_score - old_risk_record.risk_score) if (old_risk_record and old_risk_record.risk_score) else 0.0
                        cluster.risk_score = new_risk_score

                        # Upsert current week's history
                        current_week_history = db.query(IntelligenceRiskHistory).filter(
                            IntelligenceRiskHistory.cluster_id == cluster_id,
                            IntelligenceRiskHistory.week_start == current_week_start
                        ).first()

                        if current_week_history:
                            current_week_history.risk_score = new_risk_score
                            current_week_history.article_count = event_stats.event_count
                            current_week_history.avg_sentiment = current_metrics["avg_sentiment"]
                            current_week_history.unique_sources = current_metrics["unique_sources"]
                            if old_risk_record:
                                current_week_history.risk_delta = cluster.risk_delta
                        else:
                            new_history = IntelligenceRiskHistory(
                                cluster_id=cluster_id,
                                week_start=current_week_start,
                                week_end=current_week_end,
                                risk_score=new_risk_score,
                                article_count=event_stats.event_count,
                                avg_sentiment=current_metrics["avg_sentiment"],
                                unique_sources=current_metrics["unique_sources"],
                                risk_delta=cluster.risk_delta
                            )
                            db.add(new_history)

                        # Calculate time_window based on newest event
                        cluster.time_window = calculate_time_window(event_stats.newest_published)
                        cluster.last_updated = datetime.utcnow()

                        stats["clusters_updated"] += 1

                    except Exception as e:
                        logger.error(f"Error updating cluster {cluster_id}: {e}")
                        stats["errors"] += 1

                # Commit and release this batch
                db.commit()

            offset += BATCH_SIZE
            if offset % 1000 == 0:
                logger.info(f"Cluster metrics progress: {offset}/{total_clusters}")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        stats["completed_at"] = end_time.isoformat()
        stats["duration_seconds"] = duration
        stats["success"] = True

        logger.info(
            f"Cluster metrics update completed: updated={stats['clusters_updated']}, "
            f"errors={stats['errors']}, duration={duration:.2f}s"
        )

        return stats

    except Exception as e:
        logger.error(f"Cluster metrics update failed: {e}", exc_info=True)
        stats["success"] = False
        stats["error"] = str(e)
        stats["completed_at"] = datetime.utcnow().isoformat()
        raise


@celery_app.task(name="app.tasks.clustering.run_clustering_pipeline", bind=True)
def run_clustering_pipeline(
    self,
    hours: int = 24,
    min_samples: int = 3,
    eps: float = 0.55
) -> Dict[str, Any]:
    """
    Run full clustering pipeline on recent unclustered events

    Args:
        hours: Process events from last N hours
        min_samples: Minimum events for cluster formation
        eps: DBSCAN epsilon parameter (default 0.55).
             With cosine metric, requires cosine_similarity >= 0.45 (45%).
             Good balance for news event clustering with TF-IDF vectors.

    Returns:
        Statistics about clustering
    """
    logger.info(f"Starting clustering pipeline: hours={hours}, min_samples={min_samples}")

    start_time = datetime.utcnow()
    stats = {
        "task_id": self.request.id,
        "started_at": start_time.isoformat(),
        "events_processed": 0,
        "clusters_created": 0,
        "events_assigned": 0,
        "errors": 0,
    }

    try:
        # Use synchronous database session for Celery
        from app.database import SyncSessionLocal

        with SyncSessionLocal() as db:
            clustering_service = ClusteringService(eps=eps, min_samples=min_samples)

            # Get recent unclustered events
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            unclustered_events = db.query(IntelligenceEvent).filter(
                and_(
                    IntelligenceEvent.published_at >= cutoff_date,
                    IntelligenceEvent.cluster_id == None
                )
            ).all()

            if not unclustered_events:
                logger.info("No unclustered events found")
                return {
                    "task_id": self.request.id,
                    "events_processed": 0,
                    "clusters_created": 0,
                    "events_assigned": 0,
                    "success": True,
                }

            logger.info(f"Found {len(unclustered_events)} unclustered events")
            stats["events_processed"] = len(unclustered_events)

            # Prepare events for clustering
            event_dicts = [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "keywords": e.keywords or [],
                    "published_at": e.published_at,
                    "sentiment": e.sentiment,
                    "bias_score": e.bias_score,
                    "source": e.source,
                }
                for e in unclustered_events
            ]

            # Run clustering
            clusters_dict = clustering_service.cluster_events(event_dicts)

            # Create clusters and assign events
            clusters_created = 0
            events_assigned = 0

            for cluster_label, cluster_events in clusters_dict.items():
                try:
                    # Create cluster metadata
                    metadata = clustering_service.create_cluster_metadata(cluster_events)

                    # Create cluster in database
                    new_cluster = IntelligenceCluster(
                        name=metadata.get("name", f"Cluster {cluster_label}"),
                        description=metadata.get("description"),
                        event_count=len(cluster_events),
                        risk_score=metadata.get("risk_score", 0.0),
                        keywords=metadata.get("keywords", []),
                        category=metadata.get("category"),
                        is_active=True,
                    )
                    db.add(new_cluster)
                    db.flush()

                    # Assign events to cluster
                    event_ids = [e["id"] for e in cluster_events]
                    for event in unclustered_events:
                        if str(event.id) in event_ids:
                            event.cluster_id = new_cluster.id
                            events_assigned += 1

                    clusters_created += 1

                except Exception as e:
                    logger.error(f"Error creating cluster {cluster_label}: {e}")
                    stats["errors"] += 1

            db.commit()
            stats["clusters_created"] = clusters_created
            stats["events_assigned"] = events_assigned

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        stats["completed_at"] = end_time.isoformat()
        stats["duration_seconds"] = duration
        stats["success"] = True

        logger.info(
            f"Clustering pipeline completed: clusters_created={stats['clusters_created']}, "
            f"events_assigned={stats['events_assigned']}, duration={duration:.2f}s"
        )

        return stats

    except Exception as e:
        logger.error(f"Clustering pipeline failed: {e}", exc_info=True)
        stats["success"] = False
        stats["error"] = str(e)
        stats["completed_at"] = datetime.utcnow().isoformat()

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=300 * (2 ** self.request.retries), max_retries=2)

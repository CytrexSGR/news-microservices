"""
Knowledge Graph History Endpoints

Provides API endpoints for viewing historical events and audit trails.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import time

from app.database.models import KnowledgeGraphEvent
from app.api.dependencies import get_db_session
from app.core.metrics import kg_queries_total, kg_query_duration_seconds

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/v1/graph/history/enrichments")
async def get_enrichment_history(
    limit: int = Query(50, ge=1, le=200, description="Number of events to return"),
    event_type: Optional[str] = Query(
        None,
        description="Filter by event type (enrichment_applied, relationship_created, manual_edit, all)"
    ),
    db: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get enrichment history from event log.

    Retrieves recent events from the knowledge graph event log,
    showing enrichments, relationship creations, and manual edits.

    Args:
        limit: Maximum number of events to return (1-200)
        event_type: Optional filter for event type
        db: Database session (injected)

    Returns:
        List of events with timestamps, entity names, confidence changes, etc.

    Example:
        GET /api/v1/graph/history/enrichments?limit=50
        GET /api/v1/graph/history/enrichments?event_type=enrichment_applied&limit=100
    """
    start_time = time.time()

    try:
        # Build query
        query = select(KnowledgeGraphEvent).order_by(desc(KnowledgeGraphEvent.timestamp))

        # Apply event type filter if specified
        if event_type and event_type != "all":
            query = query.where(KnowledgeGraphEvent.event_type == event_type)

        # Apply limit
        query = query.limit(limit)

        # Execute query
        result = await db.execute(query)
        events = result.scalars().all()

        # Transform to dict
        history = []
        for event in events:
            history.append({
                "id": event.id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "event_type": event.event_type,
                "entity1_name": event.entity1_name,
                "entity2_name": event.entity2_name,
                "relationship_type": event.relationship_type,
                "confidence_change": {
                    "old": event.old_confidence,
                    "new": event.new_confidence,
                    "improvement": (
                        event.new_confidence - event.old_confidence
                        if event.old_confidence and event.new_confidence
                        else None
                    )
                } if event.old_confidence or event.new_confidence else None,
                "enrichment_source": event.enrichment_source,
                "enrichment_summary": event.enrichment_summary,
                "user_id": event.user_id,
                "old_relationship_type": event.old_relationship_type
            })

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='enrichment_history', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='enrichment_history').observe(query_time_seconds)

        logger.info(
            f"Enrichment history query completed: "
            f"event_type={event_type or 'all'}, "
            f"results={len(history)}, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return history

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='enrichment_history', status='error').inc()

        logger.error(f"Enrichment history query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query enrichment history: {str(e)}"
        )


@router.get("/api/v1/graph/history/stats")
async def get_history_stats(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get statistics about enrichment history.

    Returns aggregate statistics about events in the event log.

    Args:
        db: Database session (injected)

    Returns:
        Statistics dictionary with event counts by type, recent activity, etc.

    Example:
        GET /api/v1/graph/history/stats
    """
    start_time = time.time()

    try:
        # Get total event count
        total_query = select(KnowledgeGraphEvent)
        total_result = await db.execute(total_query)
        total_events = len(total_result.scalars().all())

        # Get event count by type
        events_query = select(KnowledgeGraphEvent)
        events_result = await db.execute(events_query)
        all_events = events_result.scalars().all()

        event_counts = {}
        enrichment_sources = {}
        users = set()

        for event in all_events:
            # Count by event type
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

            # Count by enrichment source
            if event.enrichment_source:
                enrichment_sources[event.enrichment_source] = (
                    enrichment_sources.get(event.enrichment_source, 0) + 1
                )

            # Track unique users
            if event.user_id:
                users.add(event.user_id)

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='history_stats', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='history_stats').observe(query_time_seconds)

        logger.info(
            f"History stats query completed: "
            f"total_events={total_events}, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return {
            "total_events": total_events,
            "event_counts_by_type": event_counts,
            "enrichment_sources": enrichment_sources,
            "unique_users": len(users),
            "query_time_ms": int(query_time_seconds * 1000)
        }

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='history_stats', status='error').inc()

        logger.error(f"History stats query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query history statistics: {str(e)}"
        )

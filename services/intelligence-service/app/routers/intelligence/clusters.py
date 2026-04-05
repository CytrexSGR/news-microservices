"""
Intelligence Cluster Endpoints
CRUD operations for intelligence clusters
"""
import logging
import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.cluster import IntelligenceCluster
from app.models.event import IntelligenceEvent
from app.schemas.intelligence import (
    ClustersResponse,
    ClusterDetail,
    TimelinePoint,
)
from .utils import normalize_risk_score

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_cluster_timelines_batch(
    db: AsyncSession,
    cluster_ids: list,
    days: int = 7
) -> dict:
    """
    Get timeline data for multiple clusters in a single query.
    Returns dict mapping cluster_id -> list of TimelinePoint.
    """
    if not cluster_ids:
        return {}

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Single query for all clusters: aggregate by cluster_id + date
    from sqlalchemy import cast, Date
    results = await db.execute(
        select(
            IntelligenceEvent.cluster_id,
            cast(IntelligenceEvent.published_at, Date).label('day'),
            func.count().label('event_count'),
            func.avg(IntelligenceEvent.sentiment).label('avg_sentiment')
        )
        .where(
            and_(
                IntelligenceEvent.cluster_id.in_(cluster_ids),
                IntelligenceEvent.published_at >= cutoff_date
            )
        )
        .group_by(IntelligenceEvent.cluster_id, cast(IntelligenceEvent.published_at, Date))
        .order_by(IntelligenceEvent.cluster_id, cast(IntelligenceEvent.published_at, Date))
    )
    rows = results.all()

    # Group results by cluster_id
    timelines = {cid: [] for cid in cluster_ids}
    for row in rows:
        timelines[row.cluster_id].append(
            TimelinePoint(
                date=datetime.combine(row.day, datetime.min.time()),
                event_count=row.event_count,
                avg_sentiment=round(float(row.avg_sentiment or 0), 2)
            )
        )

    return timelines


async def _get_cluster_timeline(
    db: AsyncSession,
    cluster_id: uuid.UUID,
    days: int = 7
) -> List[TimelinePoint]:
    """Get timeline data for a single cluster"""
    timelines = await _get_cluster_timelines_batch(db, [cluster_id], days)
    return timelines.get(cluster_id, [])


@router.get("/clusters", response_model=ClustersResponse)
async def get_clusters(
    min_events: Optional[int] = Query(None, description="Minimum event count"),
    time_range: Optional[int] = Query(7, description="Time range in days"),
    time_window: Optional[str] = Query(None, description="Filter by time window: 1h, 6h, 12h, 24h, week, month"),
    sort_by: str = Query("risk_score", description="Sort by: risk_score, event_count, last_updated"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of intelligence clusters with filtering and pagination
    """
    try:
        # Build query filters
        filters = [IntelligenceCluster.is_active == True]

        if min_events:
            filters.append(IntelligenceCluster.event_count >= min_events)

        if time_range:
            cutoff_date = datetime.utcnow() - timedelta(days=time_range)
            filters.append(IntelligenceCluster.last_updated >= cutoff_date)

        if time_window:
            valid_windows = ['1h', '6h', '12h', '24h', 'week', 'month']
            if time_window not in valid_windows:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid time_window. Must be one of: {', '.join(valid_windows)}"
                )
            filters.append(IntelligenceCluster.time_window == time_window)

        # Determine sort column
        sort_column = IntelligenceCluster.risk_score
        if sort_by == "event_count":
            sort_column = IntelligenceCluster.event_count
        elif sort_by == "last_updated":
            sort_column = IntelligenceCluster.last_updated

        # Get total count
        count_result = await db.execute(
            select(func.count(IntelligenceCluster.id))
            .where(and_(*filters))
        )
        total = count_result.scalar() or 0

        # Get clusters with pagination
        offset = (page - 1) * per_page
        clusters_result = await db.execute(
            select(IntelligenceCluster)
            .where(and_(*filters))
            .order_by(sort_column.desc())
            .offset(offset)
            .limit(per_page)
            .options(selectinload(IntelligenceCluster.events))
        )
        clusters = clusters_result.scalars().all()

        # Batch-load timelines for all clusters (1 query instead of N)
        cluster_ids = [cluster.id for cluster in clusters]
        timelines = await _get_cluster_timelines_batch(db, cluster_ids, days=7)

        # Build detailed response with timeline
        cluster_details = []
        for cluster in clusters:
            timeline = timelines.get(cluster.id, [])

            # Calculate average sentiment
            avg_sentiment = 0.0
            if cluster.events:
                sentiments = [e.sentiment for e in cluster.events if e.sentiment is not None]
                if sentiments:
                    avg_sentiment = sum(sentiments) / len(sentiments)

            # Count unique sources
            unique_sources = 0
            if cluster.events:
                unique_sources = len(set(e.source for e in cluster.events if e.source))

            cluster_details.append(
                ClusterDetail(
                    id=cluster.id,
                    name=cluster.name or "Unnamed Cluster",
                    risk_score=normalize_risk_score(cluster.risk_score or 0.0),
                    risk_delta=cluster.risk_delta or 0.0,
                    event_count=cluster.event_count or 0,
                    keywords=cluster.keywords or [],
                    category=cluster.category,
                    time_window=cluster.time_window,
                    avg_sentiment=round(avg_sentiment, 2),
                    unique_sources=unique_sources,
                    is_active=cluster.is_active,
                    first_seen=cluster.first_seen,
                    last_updated=cluster.last_updated or cluster.first_seen,
                    timeline=timeline
                )
            )

        return ClustersResponse(
            clusters=cluster_details,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        logger.error(f"Failed to get clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/{cluster_id}", response_model=ClusterDetail)
async def get_cluster_detail(
    cluster_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information for a specific cluster including all events
    """
    try:
        cluster_result = await db.execute(
            select(IntelligenceCluster)
            .where(IntelligenceCluster.id == cluster_id)
            .options(selectinload(IntelligenceCluster.events))
        )
        cluster = cluster_result.scalar_one_or_none()

        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

        timeline = await _get_cluster_timeline(db, cluster.id, days=7)

        avg_sentiment = 0.0
        if cluster.events:
            sentiments = [e.sentiment for e in cluster.events if e.sentiment is not None]
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)

        unique_sources = 0
        if cluster.events:
            unique_sources = len(set(e.source for e in cluster.events if e.source))

        return ClusterDetail(
            id=cluster.id,
            name=cluster.name or "Unnamed Cluster",
            risk_score=normalize_risk_score(cluster.risk_score or 0.0),
            risk_delta=cluster.risk_delta or 0.0,
            event_count=cluster.event_count or 0,
            keywords=cluster.keywords or [],
            category=cluster.category,
            time_window=cluster.time_window,
            avg_sentiment=round(avg_sentiment, 2),
            unique_sources=unique_sources,
            is_active=cluster.is_active,
            first_seen=cluster.first_seen,
            last_updated=cluster.last_updated or cluster.first_seen,
            timeline=timeline
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cluster detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/{cluster_id}/events")
async def get_cluster_events(
    cluster_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all events for a specific cluster with pagination
    """
    try:
        cluster_result = await db.execute(
            select(IntelligenceCluster).where(IntelligenceCluster.id == cluster_id)
        )
        cluster = cluster_result.scalar_one_or_none()

        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

        count_result = await db.execute(
            select(func.count(IntelligenceEvent.id))
            .where(IntelligenceEvent.cluster_id == cluster_id)
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * per_page
        events_result = await db.execute(
            select(IntelligenceEvent)
            .where(IntelligenceEvent.cluster_id == cluster_id)
            .order_by(IntelligenceEvent.published_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        events = events_result.scalars().all()

        return {
            "cluster_id": str(cluster_id),
            "cluster_name": cluster.name,
            "events": [
                {
                    "id": str(event.id),
                    "title": event.title,
                    "description": event.description,
                    "source": event.source,
                    "source_url": event.source_url,
                    "published_at": event.published_at.isoformat() if event.published_at else None,
                    "entities": event.entities or {},
                    "keywords": event.keywords or [],
                    "sentiment": event.sentiment,
                    "bias_score": event.bias_score,
                    "confidence": event.confidence,
                }
                for event in events
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cluster events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subcategories")
async def get_subcategories(
    db: AsyncSession = Depends(get_db)
):
    """
    Get top 2 sub-topics per category based on keywords/locations
    """
    try:
        clusters_result = await db.execute(
            select(IntelligenceCluster)
            .where(IntelligenceCluster.is_active == True)
            .options(selectinload(IntelligenceCluster.events))
        )
        clusters = clusters_result.scalars().all()

        subcategories = {
            "geo": {},
            "finance": {},
            "tech": {}
        }

        for cluster in clusters:
            category = cluster.category
            if category not in subcategories:
                continue

            if cluster.keywords:
                for keyword in cluster.keywords[:3]:
                    keyword_lower = keyword.lower()

                    if len(keyword_lower) < 3 or keyword_lower in ['the', 'and', 'that', 'this']:
                        continue

                    if keyword_lower not in subcategories[category]:
                        subcategories[category][keyword_lower] = {
                            "name": keyword,
                            "risk_score": 0.0,
                            "event_count": 0,
                            "clusters": []
                        }

                    subcategories[category][keyword_lower]["risk_score"] += cluster.risk_score or 0.0
                    subcategories[category][keyword_lower]["event_count"] += cluster.event_count or 0
                    subcategories[category][keyword_lower]["clusters"].append(str(cluster.id))

        result = {}
        for category, topics in subcategories.items():
            sorted_topics = sorted(
                topics.values(),
                key=lambda x: x["risk_score"],
                reverse=True
            )[:2]

            for topic in sorted_topics:
                topic["risk_score"] = normalize_risk_score(topic["risk_score"])

            result[category] = sorted_topics

        return result

    except Exception as e:
        logger.error(f"Failed to get subcategories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-history")
async def get_risk_history(
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical risk scores for trend visualization
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        events_result = await db.execute(
            select(IntelligenceEvent)
            .join(IntelligenceCluster, IntelligenceEvent.cluster_id == IntelligenceCluster.id)
            .where(IntelligenceEvent.published_at >= cutoff_date)
            .options(selectinload(IntelligenceEvent.cluster))
            .order_by(IntelligenceEvent.published_at.asc())
        )
        events = events_result.scalars().all()

        daily_data = {}
        for event in events:
            if not event.cluster:
                continue

            day_key = event.published_at.date().isoformat()
            if day_key not in daily_data:
                daily_data[day_key] = {
                    "date": day_key,
                    "global_risk": [],
                    "geo_risk": [],
                    "finance_risk": []
                }

            risk_score = event.cluster.risk_score or 0.0
            daily_data[day_key]["global_risk"].append(risk_score)

            if event.cluster.category == "geo":
                daily_data[day_key]["geo_risk"].append(risk_score)
            elif event.cluster.category == "finance":
                daily_data[day_key]["finance_risk"].append(risk_score)

        history = []
        for day_key in sorted(daily_data.keys()):
            day_data = daily_data[day_key]

            global_avg = sum(day_data["global_risk"]) / len(day_data["global_risk"]) if day_data["global_risk"] else 0.0
            geo_avg = sum(day_data["geo_risk"]) / len(day_data["geo_risk"]) if day_data["geo_risk"] else 0.0
            finance_avg = sum(day_data["finance_risk"]) / len(day_data["finance_risk"]) if day_data["finance_risk"] else 0.0

            history.append({
                "date": day_data["date"],
                "global_risk": normalize_risk_score(global_avg),
                "geo_risk": normalize_risk_score(geo_avg),
                "finance_risk": normalize_risk_score(finance_avg),
                "event_count": len(day_data["global_risk"])
            })

        return {
            "history": history,
            "days": days,
            "total_points": len(history)
        }

    except Exception as e:
        logger.error(f"Failed to get risk history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

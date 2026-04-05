"""
Intelligence Overview Endpoints
GET /overview - Dashboard statistics and metrics
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.cluster import IntelligenceCluster
from app.models.event import IntelligenceEvent
from sqlalchemy import text as sql_text
from app.schemas.intelligence import (
    OverviewResponse,
    ClusterSummary,
    TopRegion,
    TrendingEntity,
)
from .utils import normalize_risk_score

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db)
):
    """
    Get intelligence overview with top clusters and risk metrics

    Returns:
        - global_risk_index: Average risk score of top 5 clusters
        - top_clusters: Top 5 clusters by risk score
        - geo_risk: Average risk for geopolitical category
        - finance_risk: Average risk for financial category
        - top_regions: Top 5 regions by event activity
        - total_clusters: Total active clusters
        - total_events: Total events in last 7 days
    """
    try:
        # Get top 5 clusters by risk score
        top_clusters_result = await db.execute(
            select(IntelligenceCluster)
            .where(IntelligenceCluster.is_active == True)
            .order_by(IntelligenceCluster.risk_score.desc())
            .limit(5)
        )
        top_clusters = top_clusters_result.scalars().all()

        # Calculate global risk index (average of top clusters) - NORMALIZED
        global_risk_index = 0.0
        if top_clusters:
            risk_scores = [normalize_risk_score(c.risk_score or 0.0) for c in top_clusters]
            global_risk_index = sum(risk_scores) / len(risk_scores)

        # Calculate geo risk (average risk for geo category) - NORMALIZED
        geo_risk_result = await db.execute(
            select(func.avg(IntelligenceCluster.risk_score))
            .where(
                and_(
                    IntelligenceCluster.is_active == True,
                    IntelligenceCluster.category == "geo"
                )
            )
        )
        geo_risk = normalize_risk_score(geo_risk_result.scalar() or 0.0)

        # Calculate finance risk (average risk for finance category) - NORMALIZED
        finance_risk_result = await db.execute(
            select(func.avg(IntelligenceCluster.risk_score))
            .where(
                and_(
                    IntelligenceCluster.is_active == True,
                    IntelligenceCluster.category == "finance"
                )
            )
        )
        finance_risk = normalize_risk_score(finance_risk_result.scalar() or 0.0)

        # Get top regions by extracting from event entities
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        events_result = await db.execute(
            select(IntelligenceEvent)
            .where(IntelligenceEvent.published_at >= cutoff_date)
            .options(selectinload(IntelligenceEvent.cluster))
        )
        events = events_result.scalars().all()

        # Extract locations from entities JSONB
        region_stats = {}
        for event in events:
            if not event.entities:
                continue

            locations = []
            if isinstance(event.entities, list):
                locations = [
                    entity.get("name")
                    for entity in event.entities
                    if isinstance(entity, dict) and entity.get("type") == "LOCATION" and entity.get("name")
                ]
            elif isinstance(event.entities, dict):
                locations = event.entities.get("locations", [])

            for location in locations:
                if location not in region_stats:
                    region_stats[location] = {
                        "event_count": 0,
                        "total_risk": 0.0,
                        "clusters": set()
                    }
                region_stats[location]["event_count"] += 1
                if event.cluster and event.cluster.risk_score:
                    region_stats[location]["total_risk"] += event.cluster.risk_score
                    region_stats[location]["clusters"].add(event.cluster_id)

        # Convert to TopRegion objects
        top_regions = []
        for name, stats in sorted(
            region_stats.items(),
            key=lambda x: x[1]["event_count"],
            reverse=True
        )[:5]:
            cluster_count = len(stats["clusters"])
            avg_risk = stats["total_risk"] / cluster_count if cluster_count > 0 else 0.0
            top_regions.append(
                TopRegion(
                    name=name,
                    event_count=stats["event_count"],
                    risk_score=round(avg_risk, 2)
                )
            )

        # Get total clusters
        total_clusters_result = await db.execute(
            select(func.count(IntelligenceCluster.id))
            .where(IntelligenceCluster.is_active == True)
        )
        total_clusters = total_clusters_result.scalar() or 0

        # Get total events in last 7 days
        total_events_result = await db.execute(
            select(func.count(IntelligenceEvent.id))
            .where(IntelligenceEvent.published_at >= cutoff_date)
        )
        total_events = total_events_result.scalar() or 0

        # Get trending entities (top 10 by mention count in last 24h)
        trending_entities = []
        try:
            trending_cutoff = datetime.utcnow() - timedelta(hours=24)
            trending_result = await db.execute(
                sql_text("""
                    SELECT
                        entity->>'name' as entity_name,
                        entity->>'type' as entity_type,
                        COUNT(*) as mention_count
                    FROM article_analysis,
                         jsonb_array_elements(tier1_results->'entities') as entity
                    WHERE created_at > :cutoff
                      AND tier1_results->'entities' IS NOT NULL
                      AND entity->>'name' IS NOT NULL
                    GROUP BY entity->>'name', entity->>'type'
                    ORDER BY mention_count DESC
                    LIMIT 10
                """),
                {"cutoff": trending_cutoff}
            )
            for row in trending_result.fetchall():
                trending_entities.append(
                    TrendingEntity(
                        name=row.entity_name,
                        type=row.entity_type or "UNKNOWN",
                        mention_count=row.mention_count
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to get trending entities: {e}")

        # Build response with NORMALIZED risk scores
        return OverviewResponse(
            global_risk_index=round(global_risk_index, 2),
            top_clusters=[
                ClusterSummary(
                    id=c.id,
                    name=c.name or "Unnamed Cluster",
                    risk_score=normalize_risk_score(c.risk_score or 0.0),
                    risk_delta=c.risk_delta or 0.0,
                    event_count=c.event_count or 0,
                    keywords=c.keywords or [],
                    category=c.category,
                    last_updated=c.last_updated or c.first_seen
                )
                for c in top_clusters
            ],
            geo_risk=round(geo_risk, 2),
            finance_risk=round(finance_risk, 2),
            top_regions=top_regions,
            trending_entities=trending_entities,
            total_clusters=total_clusters,
            total_events=total_events
        )

    except Exception as e:
        logger.error(f"Failed to get intelligence overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

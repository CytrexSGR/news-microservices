"""
Entity Enrichment Service (Layer 2)

Provides knowledge graph evolution features:
- Entity-enriched clusters (JSONB extraction)
- Cross-cluster entity bridges
- Temporal entity tracking

Uses article_analysis.tier1_results JSONB for entity data.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.search import (
    ClusterEntityRequest,
    ClusterEntityResponse,
    EntityEnrichedCluster,
    ClusterEntity,
    CrossClusterBridgeRequest,
    CrossClusterBridgeResponse,
    CrossClusterBridge,
    TemporalEntityRequest,
    TemporalEntityResponse,
)

logger = logging.getLogger(__name__)


class EntityEnrichmentService:
    """
    Service for entity-based cluster enrichment (Layer 2).

    Extracts entities from article_analysis.tier1_results JSONB
    and aggregates them across clusters.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_entity_enriched_clusters(
        self, request: ClusterEntityRequest
    ) -> ClusterEntityResponse:
        """
        Get clusters enriched with their top entities.

        Extracts entities from tier1_results->'entities' JSONB array
        and aggregates by cluster.
        """
        start_time = time.time()

        # Build filter conditions
        filter_conditions = ["c.status = :status"]
        filter_params: Dict[str, Any] = {
            "status": request.status,
            "limit": request.limit,
            "min_mentions": request.min_entity_mentions,
        }

        if request.cluster_id:
            filter_conditions.append("c.id = :cluster_id")
            filter_params["cluster_id"] = request.cluster_id

        where_clause = " AND ".join(filter_conditions)

        # Query for entity-enriched clusters
        # Uses CROSS JOIN LATERAL to expand JSONB arrays
        query = text(f"""
            WITH cluster_entities AS (
                SELECT
                    c.id AS cluster_id,
                    c.title AS cluster_title,
                    c.status,
                    c.article_count,
                    c.first_seen_at,
                    c.last_updated_at,
                    aa.article_id,
                    e.value->>'name' AS entity_name,
                    e.value->>'type' AS entity_type,
                    COALESCE((e.value->>'confidence')::float, 0.5) AS confidence,
                    COALESCE((e.value->>'mentions')::int, 1) AS mentions
                FROM public.article_clusters c
                JOIN public.cluster_memberships cm ON c.id = cm.cluster_id
                JOIN public.article_analysis aa ON cm.article_id = aa.article_id
                CROSS JOIN LATERAL jsonb_array_elements(
                    aa.tier1_results->'entities'
                ) AS e(value)
                WHERE {where_clause}
                  AND aa.tier1_results IS NOT NULL
                  AND aa.tier1_results->'entities' IS NOT NULL
            ),
            aggregated_entities AS (
                SELECT
                    cluster_id,
                    cluster_title,
                    status,
                    article_count,
                    first_seen_at,
                    last_updated_at,
                    entity_name,
                    entity_type,
                    AVG(confidence) AS avg_confidence,
                    SUM(mentions) AS total_mentions,
                    COUNT(DISTINCT article_id) AS articles_with_entity
                FROM cluster_entities
                GROUP BY
                    cluster_id, cluster_title, status, article_count,
                    first_seen_at, last_updated_at, entity_name, entity_type
                HAVING SUM(mentions) >= :min_mentions
            )
            SELECT
                cluster_id::text,
                cluster_title,
                status,
                article_count,
                first_seen_at,
                last_updated_at,
                json_agg(json_build_object(
                    'name', entity_name,
                    'entity_type', entity_type,
                    'confidence', ROUND(avg_confidence::numeric, 3),
                    'mention_count', total_mentions,
                    'article_count', articles_with_entity
                ) ORDER BY total_mentions DESC) AS entities
            FROM aggregated_entities
            GROUP BY
                cluster_id, cluster_title, status, article_count,
                first_seen_at, last_updated_at
            ORDER BY article_count DESC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(query, filter_params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Entity enrichment query failed: {e}")
            return ClusterEntityResponse(
                total=0,
                clusters=[],
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Convert to response objects
        clusters = []
        for row in rows:
            entities_data = row.entities if row.entities else []

            # Filter by entity type if specified
            if request.entity_types:
                entities_data = [
                    e for e in entities_data
                    if e.get("entity_type") in request.entity_types
                ]

            # Build entity type counts
            entity_types: Dict[str, int] = defaultdict(int)
            top_entities = []
            for e in entities_data[:20]:  # Top 20 entities per cluster
                entity_types[e.get("entity_type", "OTHER")] += 1
                top_entities.append(ClusterEntity(
                    name=e.get("name", "Unknown"),
                    entity_type=e.get("entity_type", "OTHER"),
                    confidence=e.get("confidence", 0.5),
                    mention_count=int(e.get("mention_count", 1)),
                    article_count=int(e.get("article_count", 1)),
                ))

            clusters.append(EntityEnrichedCluster(
                cluster_id=row.cluster_id,
                title=row.cluster_title,
                status=row.status,
                article_count=row.article_count or 0,
                top_entities=top_entities,
                entity_types=dict(entity_types),
                first_seen_at=row.first_seen_at,
                last_updated_at=row.last_updated_at,
            ))

        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Entity enrichment completed: clusters={len(clusters)}, "
            f"time={execution_time_ms:.1f}ms"
        )

        return ClusterEntityResponse(
            total=len(clusters),
            clusters=clusters,
            execution_time_ms=execution_time_ms,
        )

    async def get_cross_cluster_bridges(
        self, request: CrossClusterBridgeRequest
    ) -> CrossClusterBridgeResponse:
        """
        Find entities that appear in multiple clusters (bridge entities).

        These entities connect different topic clusters and may indicate
        cross-cutting themes or key actors.
        """
        start_time = time.time()

        # Build entity type filter
        type_filter = ""
        filter_params: Dict[str, Any] = {
            "min_clusters": request.min_clusters,
            "limit": request.limit,
        }

        if request.entity_types:
            type_filter = "AND e.value->>'type' = ANY(:entity_types)"
            filter_params["entity_types"] = request.entity_types

        query = text(f"""
            WITH cluster_entities AS (
                SELECT
                    c.id AS cluster_id,
                    c.title AS cluster_title,
                    e.value->>'name' AS entity_name,
                    e.value->>'type' AS entity_type,
                    COALESCE((e.value->>'mentions')::int, 1) AS mentions
                FROM public.article_clusters c
                JOIN public.cluster_memberships cm ON c.id = cm.cluster_id
                JOIN public.article_analysis aa ON cm.article_id = aa.article_id
                CROSS JOIN LATERAL jsonb_array_elements(
                    aa.tier1_results->'entities'
                ) AS e(value)
                WHERE c.status = 'active'
                  AND aa.tier1_results IS NOT NULL
                  {type_filter}
            ),
            entity_clusters AS (
                SELECT
                    entity_name,
                    entity_type,
                    cluster_id,
                    cluster_title,
                    SUM(mentions) AS cluster_mentions
                FROM cluster_entities
                GROUP BY entity_name, entity_type, cluster_id, cluster_title
            ),
            bridge_entities AS (
                SELECT
                    entity_name,
                    mode() WITHIN GROUP (ORDER BY entity_type) AS primary_type,
                    COUNT(DISTINCT cluster_id) AS cluster_count,
                    SUM(cluster_mentions) AS total_mentions,
                    json_agg(json_build_object(
                        'cluster_id', cluster_id::text,
                        'title', cluster_title,
                        'mentions', cluster_mentions
                    ) ORDER BY cluster_mentions DESC) AS clusters
                FROM entity_clusters
                GROUP BY entity_name
                HAVING COUNT(DISTINCT cluster_id) >= :min_clusters
            )
            SELECT
                entity_name,
                primary_type,
                cluster_count,
                total_mentions,
                clusters
            FROM bridge_entities
            ORDER BY cluster_count DESC, total_mentions DESC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(query, filter_params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Cross-cluster bridge query failed: {e}")
            return CrossClusterBridgeResponse(
                total=0,
                bridges=[],
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Convert to response objects
        bridges = []
        for row in rows:
            bridges.append(CrossClusterBridge(
                entity_name=row.entity_name,
                entity_type=row.primary_type,
                cluster_count=row.cluster_count,
                total_mentions=int(row.total_mentions),
                connected_clusters=row.clusters if row.clusters else [],
            ))

        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Cross-cluster bridges found: bridges={len(bridges)}, "
            f"time={execution_time_ms:.1f}ms"
        )

        return CrossClusterBridgeResponse(
            total=len(bridges),
            bridges=bridges,
            execution_time_ms=execution_time_ms,
        )

    async def get_temporal_entity_trends(
        self, request: TemporalEntityRequest
    ) -> TemporalEntityResponse:
        """
        Track entity mentions over time.

        Groups entity mentions by time period to identify trending
        and declining entities.
        """
        start_time = time.time()

        # Determine time truncation based on granularity
        trunc_map = {
            "hour": "hour",
            "day": "day",
            "week": "week",
        }
        trunc = trunc_map.get(request.granularity, "day")

        # Build filters
        entity_filter = ""
        type_filter = ""
        filter_params: Dict[str, Any] = {
            "min_mentions": request.min_mentions,
            "limit": request.limit,
        }

        if request.entity_name:
            entity_filter = "AND e.value->>'name' ILIKE :entity_name"
            filter_params["entity_name"] = f"%{request.entity_name}%"

        if request.entity_type:
            type_filter = "AND e.value->>'type' = :entity_type"
            filter_params["entity_type"] = request.entity_type

        # Use f-string for days (safe: integer validated by Pydantic)
        days = request.days
        query = text(f"""
            WITH entity_mentions AS (
                SELECT
                    date_trunc('{trunc}', cm.joined_at) AS period,
                    e.value->>'name' AS entity_name,
                    e.value->>'type' AS entity_type,
                    COALESCE((e.value->>'confidence')::float, 0.5) AS confidence,
                    COALESCE((e.value->>'mentions')::int, 1) AS mentions,
                    cm.cluster_id,
                    aa.article_id
                FROM public.cluster_memberships cm
                JOIN public.article_analysis aa ON cm.article_id = aa.article_id
                CROSS JOIN LATERAL jsonb_array_elements(
                    aa.tier1_results->'entities'
                ) AS e(value)
                WHERE cm.joined_at >= NOW() - INTERVAL '{days} days'
                  AND aa.tier1_results IS NOT NULL
                  {entity_filter}
                  {type_filter}
            ),
            aggregated AS (
                SELECT
                    period,
                    entity_name,
                    mode() WITHIN GROUP (ORDER BY entity_type) AS entity_type,
                    SUM(mentions) AS mention_count,
                    COUNT(DISTINCT article_id) AS article_count,
                    COUNT(DISTINCT cluster_id) AS cluster_count,
                    AVG(confidence) AS avg_confidence
                FROM entity_mentions
                GROUP BY period, entity_name
                HAVING SUM(mentions) >= :min_mentions
            ),
            ranked AS (
                SELECT
                    entity_name,
                    entity_type,
                    SUM(mention_count) AS total_mentions,
                    json_agg(json_build_object(
                        'period', period,
                        'mentions', mention_count,
                        'articles', article_count,
                        'clusters', cluster_count,
                        'confidence', ROUND(avg_confidence::numeric, 3)
                    ) ORDER BY period) AS time_series
                FROM aggregated
                GROUP BY entity_name, entity_type
            )
            SELECT
                entity_name,
                entity_type,
                total_mentions,
                time_series
            FROM ranked
            ORDER BY total_mentions DESC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(query, filter_params)
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Temporal entity query failed: {e}")
            return TemporalEntityResponse(
                total_entities=0,
                time_range={"start": start_time, "end": start_time},
                granularity=request.granularity,
                trends=[],
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Build trends
        trends = []
        for row in rows:
            trends.append({
                "entity_name": row.entity_name,
                "entity_type": row.entity_type,
                "total_mentions": int(row.total_mentions),
                "time_series": row.time_series if row.time_series else [],
            })

        # Calculate time range
        from datetime import datetime, timedelta
        end_time = datetime.now()
        range_start = end_time - timedelta(days=request.days)

        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Temporal entity trends found: entities={len(trends)}, "
            f"time={execution_time_ms:.1f}ms"
        )

        return TemporalEntityResponse(
            total_entities=len(trends),
            time_range={"start": range_start, "end": end_time},
            granularity=request.granularity,
            trends=trends,
            execution_time_ms=execution_time_ms,
        )

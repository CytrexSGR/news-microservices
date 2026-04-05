"""
Narrative Analysis Endpoints

Provides API endpoints for querying narrative frames and media framing patterns.

These endpoints expose the NarrativeFrame nodes and FRAMED_AS relationships
ingested from the content-analysis pipeline.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time

from app.services.neo4j_service import neo4j_service
from app.api.dependencies import get_db_session
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds,
    kg_query_results_size
)

router = APIRouter(prefix="/api/v1/graph/narratives")
logger = logging.getLogger(__name__)


# Response Models
class NarrativeFrame(BaseModel):
    """Single narrative frame with metadata."""
    frame_type: str
    confidence: float
    article_id: str
    tension: Optional[float] = None
    created_at: Optional[str] = None


class EntityFraming(BaseModel):
    """How an entity is framed across narratives."""
    entity_name: str
    entity_type: str
    frames: List[Dict[str, Any]]
    total_mentions: int
    dominant_frame: Optional[str] = None


class FrameDistribution(BaseModel):
    """Distribution of frame types."""
    frame_type: str
    count: int
    percentage: float
    avg_confidence: float
    avg_tension: float


class NarrativeCooccurrence(BaseModel):
    """Entities that appear together in narratives."""
    entity1: str
    entity2: str
    shared_frames: int
    frame_types: List[str]
    avg_tension: float


class HighTensionNarrative(BaseModel):
    """High tension narrative with details."""
    article_id: str
    frame_type: str
    tension: float
    confidence: float
    entities: List[str]
    # Extended fields for actionable alerts
    title: Optional[str] = None
    link: Optional[str] = None
    published_at: Optional[str] = None
    text_excerpt: Optional[str] = None


@router.get("/frames/{entity_name}", response_model=List[NarrativeFrame])
async def get_entity_narrative_frames(
    entity_name: str,
    frame_type: Optional[str] = Query(None, description="Filter by frame type"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
) -> List[NarrativeFrame]:
    """
    Get narrative frames associated with an entity.

    Returns all frames where the entity appears, with optional filtering
    by frame type and confidence threshold.

    Args:
        entity_name: Name of the entity to query
        frame_type: Optional filter (conflict, responsibility, morality, etc.)
        min_confidence: Minimum confidence score (0.0-1.0)
        limit: Maximum number of frames to return

    Returns:
        List of NarrativeFrame objects

    Example:
        GET /api/v1/graph/narratives/frames/Hamas
        GET /api/v1/graph/narratives/frames/Trump?frame_type=conflict&min_confidence=0.7
    """
    start_time = time.time()

    try:
        # Build Cypher query with optional frame type filter
        if frame_type:
            cypher = """
            MATCH (e:Entity {name: $entity_name})-[r:FRAMED_AS]->(n:NarrativeFrame)
            WHERE n.frame_type = $frame_type AND n.confidence >= $min_confidence
            RETURN n.frame_type AS frame_type,
                   n.confidence AS confidence,
                   n.article_id AS article_id,
                   n.narrative_tension AS tension,
                   toString(n.created_at) AS created_at
            ORDER BY n.confidence DESC, n.narrative_tension DESC
            LIMIT $limit
            """
            params = {
                "entity_name": entity_name,
                "frame_type": frame_type,
                "min_confidence": min_confidence,
                "limit": limit
            }
        else:
            cypher = """
            MATCH (e:Entity {name: $entity_name})-[r:FRAMED_AS]->(n:NarrativeFrame)
            WHERE n.confidence >= $min_confidence
            RETURN n.frame_type AS frame_type,
                   n.confidence AS confidence,
                   n.article_id AS article_id,
                   n.narrative_tension AS tension,
                   toString(n.created_at) AS created_at
            ORDER BY n.confidence DESC, n.narrative_tension DESC
            LIMIT $limit
            """
            params = {
                "entity_name": entity_name,
                "min_confidence": min_confidence,
                "limit": limit
            }

        results = await neo4j_service.execute_query(cypher, parameters=params)

        frames = [
            NarrativeFrame(
                frame_type=record["frame_type"],
                confidence=record["confidence"] or 0.0,
                article_id=record["article_id"],
                tension=record.get("tension"),
                created_at=record.get("created_at")
            )
            for record in results
        ]

        # Record metrics
        query_time = time.time() - start_time
        kg_queries_total.labels(endpoint='narrative_frames', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='narrative_frames').observe(query_time)
        kg_query_results_size.labels(endpoint='narrative_frames').observe(len(frames))

        logger.info(f"Narrative frames query: entity={entity_name}, count={len(frames)}, time={query_time*1000:.0f}ms")

        return frames

    except Exception as e:
        kg_queries_total.labels(endpoint='narrative_frames', status='error').inc()
        logger.error(f"Narrative frames query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/distribution", response_model=List[FrameDistribution])
async def get_frame_distribution(
    min_count: int = Query(10, ge=1, description="Minimum frame count to include"),
    limit: int = Query(20, ge=1, le=100, description="Maximum frame types to return")
) -> List[FrameDistribution]:
    """
    Get distribution of narrative frame types across all content.

    Returns statistics on how frequently each frame type is used,
    with average confidence and tension scores.

    Args:
        min_count: Minimum occurrences for a frame type to be included
        limit: Maximum number of frame types to return

    Returns:
        List of FrameDistribution objects sorted by count

    Example:
        GET /api/v1/graph/narratives/distribution
        GET /api/v1/graph/narratives/distribution?min_count=50
    """
    start_time = time.time()

    try:
        # First get total count for percentage calculation
        total_query = """
        MATCH (n:NarrativeFrame)
        RETURN count(*) AS total
        """
        total_result = await neo4j_service.execute_query(total_query, parameters={})
        total_frames = total_result[0]["total"] if total_result else 1

        cypher = """
        MATCH (n:NarrativeFrame)
        WITH n.frame_type AS frame_type,
             count(*) AS count,
             avg(n.confidence) AS avg_confidence,
             avg(COALESCE(n.narrative_tension, 0)) AS avg_tension
        WHERE count >= $min_count
        RETURN frame_type,
               count,
               toFloat(count) / $total * 100 AS percentage,
               avg_confidence,
               avg_tension
        ORDER BY count DESC
        LIMIT $limit
        """

        results = await neo4j_service.execute_query(
            cypher,
            parameters={"min_count": min_count, "limit": limit, "total": total_frames}
        )

        distribution = [
            FrameDistribution(
                frame_type=record["frame_type"],
                count=record["count"],
                percentage=round(record["percentage"], 2),
                avg_confidence=round(record["avg_confidence"] or 0, 3),
                avg_tension=round(record["avg_tension"] or 0, 3)
            )
            for record in results
        ]

        # Record metrics
        query_time = time.time() - start_time
        kg_queries_total.labels(endpoint='frame_distribution', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='frame_distribution').observe(query_time)

        logger.info(f"Frame distribution query: types={len(distribution)}, time={query_time*1000:.0f}ms")

        return distribution

    except Exception as e:
        kg_queries_total.labels(endpoint='frame_distribution', status='error').inc()
        logger.error(f"Frame distribution query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/entity-framing/{entity_name}", response_model=EntityFraming)
async def get_entity_framing_analysis(
    entity_name: str,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(50, ge=1, le=500, description="Maximum frames per entity")
) -> EntityFraming:
    """
    Get comprehensive framing analysis for a specific entity.

    Returns how an entity is portrayed across narratives, including
    frame type breakdown and dominant framing pattern.

    Args:
        entity_name: Name of the entity to analyze
        min_confidence: Minimum confidence threshold
        limit: Maximum number of frames to analyze

    Returns:
        EntityFraming with frame breakdown and statistics

    Example:
        GET /api/v1/graph/narratives/entity-framing/Zelenskyy
        GET /api/v1/graph/narratives/entity-framing/Putin?min_confidence=0.7
    """
    start_time = time.time()

    try:
        # Get entity info and frame breakdown
        cypher = """
        MATCH (e:Entity {name: $entity_name})-[r:FRAMED_AS]->(n:NarrativeFrame)
        WHERE n.confidence >= $min_confidence
        WITH e, n.frame_type AS frame_type,
             count(*) AS frame_count,
             avg(n.confidence) AS avg_confidence,
             avg(COALESCE(n.narrative_tension, 0)) AS avg_tension
        WITH e, collect({
            frame_type: frame_type,
            count: frame_count,
            avg_confidence: avg_confidence,
            avg_tension: avg_tension
        }) AS frames,
        sum(frame_count) AS total_mentions
        RETURN e.name AS entity_name,
               COALESCE(e.type, 'UNKNOWN') AS entity_type,
               frames,
               total_mentions,
               frames[0].frame_type AS dominant_frame
        """

        results = await neo4j_service.execute_query(
            cypher,
            parameters={
                "entity_name": entity_name,
                "min_confidence": min_confidence
            }
        )

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No narrative framing data found for entity: {entity_name}"
            )

        record = results[0]

        # Sort frames by count
        frames = sorted(record["frames"], key=lambda x: x["count"], reverse=True)

        entity_framing = EntityFraming(
            entity_name=record["entity_name"],
            entity_type=record["entity_type"],
            frames=frames[:limit],
            total_mentions=record["total_mentions"],
            dominant_frame=record.get("dominant_frame")
        )

        # Record metrics
        query_time = time.time() - start_time
        kg_queries_total.labels(endpoint='entity_framing', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='entity_framing').observe(query_time)

        logger.info(f"Entity framing query: entity={entity_name}, mentions={entity_framing.total_mentions}, time={query_time*1000:.0f}ms")

        return entity_framing

    except HTTPException:
        raise
    except Exception as e:
        kg_queries_total.labels(endpoint='entity_framing', status='error').inc()
        logger.error(f"Entity framing query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/cooccurrence", response_model=List[NarrativeCooccurrence])
async def get_narrative_cooccurrence(
    entity_name: Optional[str] = Query(None, description="Filter by specific entity"),
    frame_type: Optional[str] = Query(None, description="Filter by frame type"),
    min_shared: int = Query(3, ge=1, description="Minimum shared frames"),
    limit: int = Query(50, ge=1, le=200, description="Maximum pairs to return")
) -> List[NarrativeCooccurrence]:
    """
    Find entities that frequently appear together in narratives.

    Discovers entity pairs that are co-framed in articles, useful for
    finding related actors in news coverage.

    Args:
        entity_name: Optional - only find pairs including this entity
        frame_type: Optional - only consider this frame type
        min_shared: Minimum number of shared frames
        limit: Maximum pairs to return

    Returns:
        List of NarrativeCooccurrence with entity pairs and shared frame details

    Example:
        GET /api/v1/graph/narratives/cooccurrence
        GET /api/v1/graph/narratives/cooccurrence?entity_name=Trump&min_shared=5
    """
    start_time = time.time()

    try:
        if entity_name:
            # Find co-occurring entities for a specific entity
            cypher = """
            MATCH (e1:Entity {name: $entity_name})-[:FRAMED_AS]->(n:NarrativeFrame)<-[:FRAMED_AS]-(e2:Entity)
            WHERE e1 <> e2
            """ + (f"AND n.frame_type = $frame_type" if frame_type else "") + """
            WITH e1.name AS entity1, e2.name AS entity2,
                 count(DISTINCT n) AS shared_frames,
                 collect(DISTINCT n.frame_type) AS frame_types,
                 avg(COALESCE(n.narrative_tension, 0)) AS avg_tension
            WHERE shared_frames >= $min_shared
            RETURN entity1, entity2, shared_frames, frame_types, avg_tension
            ORDER BY shared_frames DESC
            LIMIT $limit
            """
            params = {
                "entity_name": entity_name,
                "min_shared": min_shared,
                "limit": limit
            }
            if frame_type:
                params["frame_type"] = frame_type
        else:
            # Find all co-occurring entity pairs
            cypher = """
            MATCH (e1:Entity)-[:FRAMED_AS]->(n:NarrativeFrame)<-[:FRAMED_AS]-(e2:Entity)
            WHERE id(e1) < id(e2)
            """ + (f"AND n.frame_type = $frame_type" if frame_type else "") + """
            WITH e1.name AS entity1, e2.name AS entity2,
                 count(DISTINCT n) AS shared_frames,
                 collect(DISTINCT n.frame_type) AS frame_types,
                 avg(COALESCE(n.narrative_tension, 0)) AS avg_tension
            WHERE shared_frames >= $min_shared
            RETURN entity1, entity2, shared_frames, frame_types, avg_tension
            ORDER BY shared_frames DESC
            LIMIT $limit
            """
            params = {"min_shared": min_shared, "limit": limit}
            if frame_type:
                params["frame_type"] = frame_type

        results = await neo4j_service.execute_query(cypher, parameters=params)

        cooccurrences = [
            NarrativeCooccurrence(
                entity1=record["entity1"],
                entity2=record["entity2"],
                shared_frames=record["shared_frames"],
                frame_types=record["frame_types"],
                avg_tension=round(record["avg_tension"] or 0, 3)
            )
            for record in results
        ]

        # Record metrics
        query_time = time.time() - start_time
        kg_queries_total.labels(endpoint='narrative_cooccurrence', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='narrative_cooccurrence').observe(query_time)
        kg_query_results_size.labels(endpoint='narrative_cooccurrence').observe(len(cooccurrences))

        logger.info(f"Narrative cooccurrence query: pairs={len(cooccurrences)}, time={query_time*1000:.0f}ms")

        return cooccurrences

    except Exception as e:
        kg_queries_total.labels(endpoint='narrative_cooccurrence', status='error').inc()
        logger.error(f"Narrative cooccurrence query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/high-tension", response_model=List[HighTensionNarrative])
async def get_high_tension_narratives(
    min_tension: float = Query(0.7, ge=0.0, le=1.0, description="Minimum tension score"),
    frame_type: Optional[str] = Query(None, description="Filter by frame type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    include_details: bool = Query(True, description="Include article title, link, excerpt"),
    db: AsyncSession = Depends(get_db_session)
) -> List[HighTensionNarrative]:
    """
    Find narratives with high emotional tension.

    Returns articles with high narrative tension scores, useful for
    identifying emotionally charged or controversial content.

    Args:
        min_tension: Minimum tension score (0.0-1.0)
        frame_type: Optional frame type filter
        limit: Maximum narratives to return
        include_details: Include article title, link, published_at, text_excerpt

    Returns:
        List of HighTensionNarrative with details

    Example:
        GET /api/v1/graph/narratives/high-tension
        GET /api/v1/graph/narratives/high-tension?min_tension=0.8&frame_type=conflict
        GET /api/v1/graph/narratives/high-tension?include_details=true
    """
    start_time = time.time()

    try:
        # Neo4j query now includes text_excerpt
        if frame_type:
            cypher = """
            MATCH (e:Entity)-[:FRAMED_AS]->(n:NarrativeFrame)
            WHERE n.narrative_tension >= $min_tension AND n.frame_type = $frame_type
            WITH n, collect(e.name) AS entities
            RETURN n.article_id AS article_id,
                   n.frame_type AS frame_type,
                   n.narrative_tension AS tension,
                   n.confidence AS confidence,
                   n.text_excerpt AS text_excerpt,
                   entities
            ORDER BY n.narrative_tension DESC
            LIMIT $limit
            """
            params = {
                "min_tension": min_tension,
                "frame_type": frame_type,
                "limit": limit
            }
        else:
            cypher = """
            MATCH (e:Entity)-[:FRAMED_AS]->(n:NarrativeFrame)
            WHERE n.narrative_tension >= $min_tension
            WITH n, collect(e.name) AS entities
            RETURN n.article_id AS article_id,
                   n.frame_type AS frame_type,
                   n.narrative_tension AS tension,
                   n.confidence AS confidence,
                   n.text_excerpt AS text_excerpt,
                   entities
            ORDER BY n.narrative_tension DESC
            LIMIT $limit
            """
            params = {"min_tension": min_tension, "limit": limit}

        results = await neo4j_service.execute_query(cypher, parameters=params)

        # Build initial narratives from Neo4j
        narratives = []
        article_ids = []
        for record in results:
            article_id = record["article_id"]
            article_ids.append(article_id)
            narratives.append(HighTensionNarrative(
                article_id=article_id,
                frame_type=record["frame_type"],
                tension=record["tension"] or 0.0,
                confidence=record["confidence"] or 0.0,
                entities=record["entities"][:10],
                text_excerpt=record.get("text_excerpt")
            ))

        # Fetch article details from PostgreSQL if requested
        if include_details and article_ids:
            try:
                # Query feed_items for article metadata
                # Build parameterized query with individual UUID parameters
                placeholders = ", ".join([f":id_{i}" for i in range(len(article_ids))])
                sql = text(f"""
                    SELECT
                        id::text as article_id,
                        title,
                        link,
                        published_at::text as published_at
                    FROM feed_items
                    WHERE id IN ({placeholders})
                """)
                params = {f"id_{i}": article_ids[i] for i in range(len(article_ids))}
                result = await db.execute(sql, params)
                article_details = {row.article_id: row for row in result.fetchall()}

                # Enrich narratives with article details
                for narrative in narratives:
                    if narrative.article_id in article_details:
                        details = article_details[narrative.article_id]
                        narrative.title = details.title
                        narrative.link = details.link
                        narrative.published_at = details.published_at
            except Exception as pg_err:
                # Log but don't fail - article details are optional enrichment
                logger.warning(f"Failed to fetch article details from PostgreSQL: {pg_err}")

        # Record metrics
        query_time = time.time() - start_time
        kg_queries_total.labels(endpoint='high_tension', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='high_tension').observe(query_time)
        kg_query_results_size.labels(endpoint='high_tension').observe(len(narratives))

        logger.info(f"High tension query: count={len(narratives)}, time={query_time*1000:.0f}ms, details={include_details}")

        return narratives

    except Exception as e:
        kg_queries_total.labels(endpoint='high_tension', status='error').inc()
        logger.error(f"High tension query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/stats")
async def get_narrative_stats() -> Dict[str, Any]:
    """
    Get overall narrative analysis statistics.

    Returns aggregate counts and metrics for the narrative frame data.

    Returns:
        Dictionary with total frames, entity counts, frame type breakdown

    Example:
        GET /api/v1/graph/narratives/stats
    """
    start_time = time.time()

    try:
        # Total narrative frames
        frame_count = await neo4j_service.execute_query("""
            MATCH (n:NarrativeFrame)
            RETURN count(n) AS total
        """)
        total_frames = frame_count[0]["total"] if frame_count else 0

        # Total FRAMED_AS relationships
        rel_count = await neo4j_service.execute_query("""
            MATCH ()-[r:FRAMED_AS]->()
            RETURN count(r) AS total
        """)
        total_relationships = rel_count[0]["total"] if rel_count else 0

        # Entities with narrative data
        entity_count = await neo4j_service.execute_query("""
            MATCH (e:Entity)-[:FRAMED_AS]->()
            RETURN count(DISTINCT e) AS total
        """)
        total_entities = entity_count[0]["total"] if entity_count else 0

        # Frame type breakdown
        frame_types = await neo4j_service.execute_query("""
            MATCH (n:NarrativeFrame)
            RETURN n.frame_type AS frame_type, count(*) AS count
            ORDER BY count DESC
        """)

        frame_breakdown = {
            record["frame_type"]: record["count"]
            for record in frame_types
        }

        # Average tension
        tension_stats = await neo4j_service.execute_query("""
            MATCH (n:NarrativeFrame)
            WHERE n.narrative_tension IS NOT NULL
            RETURN avg(n.narrative_tension) AS avg_tension,
                   max(n.narrative_tension) AS max_tension,
                   min(n.narrative_tension) AS min_tension
        """)

        tension = tension_stats[0] if tension_stats else {}

        query_time = time.time() - start_time
        kg_queries_total.labels(endpoint='narrative_stats', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='narrative_stats').observe(query_time)

        return {
            "total_narrative_frames": total_frames,
            "total_framed_as_relationships": total_relationships,
            "entities_with_narrative_data": total_entities,
            "frame_type_breakdown": frame_breakdown,
            "tension_stats": {
                "average": round(tension.get("avg_tension") or 0, 3),
                "max": round(tension.get("max_tension") or 0, 3),
                "min": round(tension.get("min_tension") or 0, 3)
            },
            "query_time_ms": int(query_time * 1000)
        }

    except Exception as e:
        kg_queries_total.labels(endpoint='narrative_stats', status='error').inc()
        logger.error(f"Narrative stats query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/top-entities")
async def get_top_narrative_entities(
    frame_type: Optional[str] = Query(None, description="Filter by frame type"),
    limit: int = Query(20, ge=1, le=100, description="Number of entities to return")
) -> List[Dict[str, Any]]:
    """
    Get entities with the most narrative frame mentions.

    Returns entities ranked by how often they appear in narrative frames,
    useful for identifying major actors in news coverage.

    Args:
        frame_type: Optional frame type filter
        limit: Maximum entities to return

    Returns:
        List of entities with mention counts and frame breakdown

    Example:
        GET /api/v1/graph/narratives/top-entities
        GET /api/v1/graph/narratives/top-entities?frame_type=conflict&limit=10
    """
    start_time = time.time()

    try:
        if frame_type:
            cypher = """
            MATCH (e:Entity)-[r:FRAMED_AS]->(n:NarrativeFrame)
            WHERE n.frame_type = $frame_type
            WITH e, count(n) AS mention_count,
                 collect(DISTINCT n.frame_type) AS frame_types,
                 avg(COALESCE(n.narrative_tension, 0)) AS avg_tension
            RETURN e.name AS entity_name,
                   COALESCE(e.type, 'UNKNOWN') AS entity_type,
                   mention_count,
                   frame_types,
                   avg_tension
            ORDER BY mention_count DESC
            LIMIT $limit
            """
            params = {"frame_type": frame_type, "limit": limit}
        else:
            cypher = """
            MATCH (e:Entity)-[r:FRAMED_AS]->(n:NarrativeFrame)
            WITH e, count(n) AS mention_count,
                 collect(DISTINCT n.frame_type) AS frame_types,
                 avg(COALESCE(n.narrative_tension, 0)) AS avg_tension
            RETURN e.name AS entity_name,
                   COALESCE(e.type, 'UNKNOWN') AS entity_type,
                   mention_count,
                   frame_types,
                   avg_tension
            ORDER BY mention_count DESC
            LIMIT $limit
            """
            params = {"limit": limit}

        results = await neo4j_service.execute_query(cypher, parameters=params)

        entities = [
            {
                "entity_name": record["entity_name"],
                "entity_type": record["entity_type"],
                "mention_count": record["mention_count"],
                "frame_types": record["frame_types"],
                "avg_tension": round(record["avg_tension"] or 0, 3)
            }
            for record in results
        ]

        query_time = time.time() - start_time
        kg_queries_total.labels(endpoint='top_narrative_entities', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='top_narrative_entities').observe(query_time)

        logger.info(f"Top narrative entities query: count={len(entities)}, time={query_time*1000:.0f}ms")

        return entities

    except Exception as e:
        kg_queries_total.labels(endpoint='top_narrative_entities', status='error').inc()
        logger.error(f"Top narrative entities query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

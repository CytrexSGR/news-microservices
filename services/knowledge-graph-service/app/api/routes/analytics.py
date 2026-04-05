"""
Graph Analytics Endpoints

Provides API endpoints for graph analytics and statistics.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta
import time

from app.services.neo4j_service import neo4j_service
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/v1/graph/analytics/top-entities")
async def get_top_entities(
    limit: int = Query(10, ge=1, le=100, description="Number of top entities to return"),
    entity_type: str = Query(None, description="Filter by entity type")
) -> List[Dict[str, Any]]:
    """
    Get top entities by connection count.

    Returns the most connected entities in the knowledge graph.

    Args:
        limit: Maximum number of entities to return (1-100)
        entity_type: Optional filter for specific entity types (PERSON, ORGANIZATION, etc.)

    Returns:
        List of entities with their connection counts, types, and example connections

    Example:
        GET /api/v1/graph/analytics/top-entities?limit=10
        GET /api/v1/graph/analytics/top-entities?entity_type=ORGANIZATION&limit=20
    """
    start_time = time.time()

    try:
        # Build Cypher query with optional type filter
        type_filter = "WHERE e.type = $entity_type" if entity_type else ""

        cypher = f"""
        MATCH (e:Entity)
        {type_filter}
        OPTIONAL MATCH (e)-[r]-(connected:Entity)
        WITH e, count(DISTINCT r) AS connection_count, collect(DISTINCT {{
            name: connected.name,
            type: connected.type,
            relationship_type: type(r)
        }})[0..5] AS sample_connections
        WHERE connection_count > 0
        ORDER BY connection_count DESC
        LIMIT $limit
        RETURN
            e.name AS name,
            e.type AS type,
            connection_count,
            sample_connections
        """

        parameters = {"limit": limit}
        if entity_type:
            parameters["entity_type"] = entity_type

        results = await neo4j_service.execute_query(cypher, parameters=parameters)

        # Transform results
        top_entities = []
        for record in results:
            top_entities.append({
                "name": record["name"],
                "type": record["type"],
                "connection_count": record["connection_count"],
                "sample_connections": record["sample_connections"] or []
            })

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='top_entities', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='top_entities').observe(query_time_seconds)

        logger.info(
            f"Top entities query completed: type={entity_type}, "
            f"results={len(top_entities)}, time={int(query_time_seconds * 1000)}ms"
        )

        return top_entities

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='top_entities', status='error').inc()

        logger.error(f"Top entities query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query top entities: {str(e)}"
        )


@router.get("/api/v1/graph/analytics/growth-history")
async def get_growth_history(
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
) -> List[Dict[str, Any]]:
    """
    Get graph growth history over time.

    Returns daily counts of nodes and relationships.

    Args:
        days: Number of days of history to return (1-365)

    Returns:
        List of daily statistics with dates, node counts, and relationship counts

    Example:
        GET /api/v1/graph/analytics/growth-history?days=30
    """
    start_time = time.time()

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query for entities created over time
        cypher = """
        MATCH (e:Entity)
        WHERE e.created_at IS NOT NULL
          AND e.created_at >= datetime($start_date)
          AND e.created_at <= datetime($end_date)
        WITH date(e.created_at) AS creation_date
        RETURN
            toString(creation_date) AS date,
            count(*) AS new_nodes
        ORDER BY date ASC
        """

        entity_results = await neo4j_service.execute_query(
            cypher,
            parameters={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

        # Query for relationships created over time
        rel_cypher = """
        MATCH ()-[r]->()
        WHERE r.created_at IS NOT NULL
          AND r.created_at >= datetime($start_date)
          AND r.created_at <= datetime($end_date)
        WITH date(r.created_at) AS creation_date
        RETURN
            toString(creation_date) AS date,
            count(*) AS new_relationships
        ORDER BY date ASC
        """

        rel_results = await neo4j_service.execute_query(
            rel_cypher,
            parameters={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

        # Merge results by date
        growth_by_date = {}

        for record in entity_results:
            date = record["date"]
            growth_by_date[date] = {
                "date": date,
                "new_nodes": record["new_nodes"],
                "new_relationships": 0
            }

        for record in rel_results:
            date = record["date"]
            if date in growth_by_date:
                growth_by_date[date]["new_relationships"] = record["new_relationships"]
            else:
                growth_by_date[date] = {
                    "date": date,
                    "new_nodes": 0,
                    "new_relationships": record["new_relationships"]
                }

        # Convert to sorted list
        growth_history = sorted(growth_by_date.values(), key=lambda x: x["date"])

        # Calculate cumulative totals
        cumulative_nodes = 0
        cumulative_relationships = 0

        for entry in growth_history:
            cumulative_nodes += entry["new_nodes"]
            cumulative_relationships += entry["new_relationships"]
            entry["total_nodes"] = cumulative_nodes
            entry["total_relationships"] = cumulative_relationships

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='growth_history', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='growth_history').observe(query_time_seconds)

        logger.info(
            f"Growth history query completed: days={days}, "
            f"data_points={len(growth_history)}, time={int(query_time_seconds * 1000)}ms"
        )

        return growth_history

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='growth_history', status='error').inc()

        logger.error(f"Growth history query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query growth history: {str(e)}"
        )


@router.get("/api/v1/graph/analytics/relationship-stats")
async def get_relationship_stats() -> Dict[str, Any]:
    """
    Get comprehensive statistics about relationship types in the graph.

    Returns:
        Distribution of relationship types with:
        - Counts, confidence metrics, percentages
        - Top 3 concrete examples per type
        - Entity-type patterns (common source→target type combinations)
        - Quality insights

    Example:
        GET /api/v1/graph/analytics/relationship-stats
    """
    start_time = time.time()

    try:
        # Query 1: Relationship type distribution with examples
        cypher_types = """
        MATCH (source:Entity)-[r]->(target:Entity)
        WITH type(r) AS relationship_type,
             count(*) AS count,
             avg(r.confidence) AS avg_confidence,
             sum(r.mention_count) AS total_mentions,
             collect({
                 source: source.name,
                 source_type: source.type,
                 target: target.name,
                 target_type: target.type,
                 confidence: r.confidence,
                 mentions: r.mention_count
             }) AS all_examples
        RETURN
            relationship_type,
            count,
            avg_confidence,
            total_mentions,
            [example IN all_examples | example][0..3] AS top_examples
        ORDER BY count DESC
        """

        type_results = await neo4j_service.execute_query(cypher_types)

        # Transform results with examples
        relationship_types = []
        total_relationships = 0

        for record in type_results:
            count = record["count"]
            total_relationships += count
            avg_conf = record["avg_confidence"] or 0.0

            # Sort examples by mention count
            examples = sorted(
                record["top_examples"] or [],
                key=lambda x: x.get("mentions", 0),
                reverse=True
            )[:3]

            relationship_types.append({
                "type": record["relationship_type"],
                "count": count,
                "avg_confidence": round(avg_conf, 3),
                "total_mentions": record["total_mentions"] or 0,
                "quality": "high" if avg_conf >= 0.8 else "medium" if avg_conf >= 0.6 else "low",
                "examples": [
                    {
                        "source": ex["source"],
                        "source_type": ex["source_type"],
                        "target": ex["target"],
                        "target_type": ex["target_type"],
                        "confidence": round(ex.get("confidence", 0.0), 2),
                        "mentions": ex.get("mentions", 0)
                    }
                    for ex in examples
                ]
            })

        # Add percentages
        for rel_type in relationship_types:
            rel_type["percentage"] = round(
                (rel_type["count"] / total_relationships) * 100, 2
            ) if total_relationships > 0 else 0

        # Query 2: Entity-type patterns (most common source_type -> target_type combinations)
        cypher_patterns = """
        MATCH (source:Entity)-[r]->(target:Entity)
        WITH source.type AS source_type,
             type(r) AS relationship_type,
             target.type AS target_type,
             count(*) AS count
        RETURN
            source_type,
            relationship_type,
            target_type,
            count
        ORDER BY count DESC
        LIMIT 10
        """

        pattern_results = await neo4j_service.execute_query(cypher_patterns)

        patterns = [
            {
                "source_type": record["source_type"],
                "relationship_type": record["relationship_type"],
                "target_type": record["target_type"],
                "count": record["count"]
            }
            for record in pattern_results
        ]

        # Quality insights
        high_quality = [rt for rt in relationship_types if rt["quality"] == "high"]
        needs_review = [rt for rt in relationship_types if rt["quality"] == "low"]

        quality_insights = {
            "high_quality_count": len(high_quality),
            "needs_review_count": len(needs_review),
            "avg_confidence_overall": round(
                sum(rt["avg_confidence"] * rt["count"] for rt in relationship_types) / total_relationships, 3
            ) if total_relationships > 0 else 0
        }

        # Add warnings
        warnings = []
        not_applicable = next(
            (rt for rt in relationship_types if rt["type"] == "NOT_APPLICABLE"),
            None
        )
        if not_applicable and not_applicable["percentage"] > 20:
            warnings.append({
                "type": "high_not_applicable",
                "message": f"NOT_APPLICABLE relationships are {not_applicable['percentage']}% of total. Consider improving entity extraction.",
                "severity": "warning"
            })

        if quality_insights["avg_confidence_overall"] < 0.7:
            warnings.append({
                "type": "low_confidence",
                "message": f"Overall confidence is {quality_insights['avg_confidence_overall']*100:.1f}%. Review relationship extraction quality.",
                "severity": "warning"
            })

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='relationship_stats', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='relationship_stats').observe(query_time_seconds)

        logger.info(
            f"Relationship stats query completed: types={len(relationship_types)}, "
            f"patterns={len(patterns)}, time={int(query_time_seconds * 1000)}ms"
        )

        return {
            "total_relationships": total_relationships,
            "relationship_types": relationship_types,
            "patterns": patterns,
            "quality_insights": quality_insights,
            "warnings": warnings
        }

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='relationship_stats', status='error').inc()

        logger.error(f"Relationship stats query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query relationship stats: {str(e)}"
        )


@router.get("/api/v1/graph/analytics/cross-article-coverage")
async def get_cross_article_coverage(
    top_limit: int = Query(10, ge=1, le=50, description="Number of top entities to return")
) -> Dict[str, Any]:
    """
    Get cross-article entity coverage statistics.

    Shows which entities appear across multiple articles and overall
    entity distribution across the article corpus.

    Args:
        top_limit: Maximum number of top entities to return (1-50)

    Returns:
        Coverage statistics including:
        - total_articles: Total number of unique articles
        - total_unique_entities: Count of unique entities in graph
        - entities_per_article_avg: Average entities per article
        - articles_per_entity_avg: Average articles per entity
        - top_entities: Top entities by article coverage

    Example:
        GET /api/v1/graph/analytics/cross-article-coverage?top_limit=10
    """
    start_time = time.time()

    try:
        # Query 1: Overall statistics
        stats_cypher = """
        MATCH (e:Entity)-[:EXTRACTED_FROM]->(a:Article)
        WITH COUNT(DISTINCT a) AS total_articles,
             COUNT(DISTINCT e) AS total_unique_entities,
             COUNT(*) AS total_mentions
        RETURN total_articles,
               total_unique_entities,
               ROUND(total_mentions * 1.0 / total_articles, 2) AS entities_per_article_avg,
               ROUND(total_mentions * 1.0 / total_unique_entities, 2) AS articles_per_entity_avg
        """

        stats_result = await neo4j_service.execute_query(stats_cypher, parameters={})

        if not stats_result or not stats_result[0]:
            # No data available
            return {
                "total_articles": 0,
                "total_unique_entities": 0,
                "entities_per_article_avg": 0.0,
                "articles_per_entity_avg": 0.0,
                "top_entities": []
            }

        stats = stats_result[0]

        # Query 2: Top entities by article count
        top_entities_cypher = """
        MATCH (e:Entity)-[:EXTRACTED_FROM]->(a:Article)
        WITH e, COUNT(DISTINCT a) AS article_count
        ORDER BY article_count DESC
        LIMIT $top_limit
        MATCH (e)-[:EXTRACTED_FROM]->(recent:Article)
        WITH e, article_count,
             COLLECT(DISTINCT {
                 title: recent.title,
                 published_at: recent.published_at
             })[0..2] AS recent_articles
        RETURN e.name AS entity_name,
               e.type AS entity_type,
               e.wikidata_id AS wikidata_id,
               article_count,
               recent_articles
        ORDER BY article_count DESC
        """

        top_entities_result = await neo4j_service.execute_query(
            top_entities_cypher,
            parameters={"top_limit": top_limit}
        )

        # Calculate total articles for coverage percentage
        total_articles = stats.get("total_articles", 1)

        # Format top entities
        top_entities = []
        for record in top_entities_result:
            article_count = record.get("article_count", 0)
            coverage_percentage = round((article_count / total_articles) * 100, 1) if total_articles > 0 else 0.0

            top_entities.append({
                "entity_name": record.get("entity_name"),
                "entity_type": record.get("entity_type"),
                "wikidata_id": record.get("wikidata_id"),
                "article_count": article_count,
                "coverage_percentage": coverage_percentage,
                "recent_articles": record.get("recent_articles", [])
            })

        # Record success metric
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='cross_article_coverage', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='cross_article_coverage').observe(query_time_seconds)

        logger.info(
            f"Cross-article coverage query successful: "
            f"articles={stats.get('total_articles')}, "
            f"entities={stats.get('total_unique_entities')}, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return {
            "total_articles": stats.get("total_articles", 0),
            "total_unique_entities": stats.get("total_unique_entities", 0),
            "entities_per_article_avg": stats.get("entities_per_article_avg", 0.0),
            "articles_per_entity_avg": stats.get("articles_per_entity_avg", 0.0),
            "top_entities": top_entities
        }

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='cross_article_coverage', status='error').inc()

        logger.error(f"Cross-article coverage query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query cross-article coverage: {str(e)}"
        )


@router.get("/api/v1/graph/analytics/not-applicable-trends")
async def get_not_applicable_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
) -> List[Dict[str, Any]]:
    """
    Get NOT_APPLICABLE relationship trends over time.

    Tracks the ratio and count of NOT_APPLICABLE relationships per day.
    Useful for monitoring data quality improvements.

    Args:
        days: Number of days of history to return (1-365)

    Returns:
        List of daily statistics with:
        - date: Date string (YYYY-MM-DD)
        - not_applicable_count: Number of NOT_APPLICABLE relationships
        - total_relationships: Total relationships on that day
        - not_applicable_ratio: Ratio (0-1) of NOT_APPLICABLE to total
        - not_applicable_percentage: Percentage (0-100)

    Example:
        GET /api/v1/graph/analytics/not-applicable-trends?days=30
    """
    start_time = time.time()

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query NOT_APPLICABLE relationships created over time
        cypher = """
        MATCH ()-[r]->()
        WHERE r.created_at IS NOT NULL
          AND r.created_at >= datetime($start_date)
          AND r.created_at <= datetime($end_date)
        WITH date(r.created_at) AS creation_date,
             type(r) AS rel_type
        RETURN
            toString(creation_date) AS date,
            sum(CASE WHEN rel_type = 'NOT_APPLICABLE' THEN 1 ELSE 0 END) AS not_applicable_count,
            count(*) AS total_relationships
        ORDER BY date ASC
        """

        results = await neo4j_service.execute_query(
            cypher,
            parameters={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

        # Transform results with calculated ratios
        trends = []
        for record in results:
            na_count = record["not_applicable_count"]
            total = record["total_relationships"]
            ratio = na_count / total if total > 0 else 0.0

            trends.append({
                "date": record["date"],
                "not_applicable_count": na_count,
                "total_relationships": total,
                "not_applicable_ratio": round(ratio, 4),
                "not_applicable_percentage": round(ratio * 100, 2)
            })

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='not_applicable_trends', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='not_applicable_trends').observe(query_time_seconds)

        logger.info(
            f"NOT_APPLICABLE trends query completed: days={days}, "
            f"data_points={len(trends)}, time={int(query_time_seconds * 1000)}ms"
        )

        return trends

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='not_applicable_trends', status='error').inc()

        logger.error(f"NOT_APPLICABLE trends query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query NOT_APPLICABLE trends: {str(e)}"
        )


@router.get("/api/v1/graph/analytics/relationship-quality-trends")
async def get_relationship_quality_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
) -> List[Dict[str, Any]]:
    """
    Get relationship quality distribution trends over time.

    Tracks high/medium/low confidence ratios per day to monitor quality improvements.

    Args:
        days: Number of days of history to return (1-365)

    Returns:
        List of daily statistics with:
        - date: Date string (YYYY-MM-DD)
        - high_confidence_count: Number of high confidence relationships
        - medium_confidence_count: Number of medium confidence relationships
        - low_confidence_count: Number of low confidence relationships
        - total_relationships: Total relationships on that day
        - high_confidence_ratio: Ratio (0-1)
        - medium_confidence_ratio: Ratio (0-1)
        - low_confidence_ratio: Ratio (0-1)
        - high_confidence_percentage: Percentage (0-100)
        - medium_confidence_percentage: Percentage (0-100)
        - low_confidence_percentage: Percentage (0-100)

    Example:
        GET /api/v1/graph/analytics/relationship-quality-trends?days=30
    """
    start_time = time.time()

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query relationship quality distribution over time
        cypher = """
        MATCH ()-[r]->()
        WHERE r.created_at IS NOT NULL
          AND r.created_at >= datetime($start_date)
          AND r.created_at <= datetime($end_date)
        WITH date(r.created_at) AS creation_date,
             r.confidence AS conf
        RETURN
            toString(creation_date) AS date,
            sum(CASE WHEN conf > 0.8 THEN 1 ELSE 0 END) AS high_confidence_count,
            sum(CASE WHEN conf >= 0.5 AND conf <= 0.8 THEN 1 ELSE 0 END) AS medium_confidence_count,
            sum(CASE WHEN conf < 0.5 THEN 1 ELSE 0 END) AS low_confidence_count,
            count(*) AS total_relationships
        ORDER BY date ASC
        """

        results = await neo4j_service.execute_query(
            cypher,
            parameters={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

        # Transform results with calculated ratios
        trends = []
        for record in results:
            high = record["high_confidence_count"]
            medium = record["medium_confidence_count"]
            low = record["low_confidence_count"]
            total = record["total_relationships"]

            trends.append({
                "date": record["date"],
                "high_confidence_count": high,
                "medium_confidence_count": medium,
                "low_confidence_count": low,
                "total_relationships": total,
                "high_confidence_ratio": round(high / total, 4) if total > 0 else 0.0,
                "medium_confidence_ratio": round(medium / total, 4) if total > 0 else 0.0,
                "low_confidence_ratio": round(low / total, 4) if total > 0 else 0.0,
                "high_confidence_percentage": round((high / total) * 100, 2) if total > 0 else 0.0,
                "medium_confidence_percentage": round((medium / total) * 100, 2) if total > 0 else 0.0,
                "low_confidence_percentage": round((low / total) * 100, 2) if total > 0 else 0.0
            })

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='relationship_quality_trends', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='relationship_quality_trends').observe(query_time_seconds)

        logger.info(
            f"Relationship quality trends query completed: days={days}, "
            f"data_points={len(trends)}, time={int(query_time_seconds * 1000)}ms"
        )

        return trends

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='relationship_quality_trends', status='error').inc()

        logger.error(f"Relationship quality trends query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query relationship quality trends: {str(e)}"
        )


@router.get("/api/v1/graph/stats/detailed")
async def get_detailed_stats() -> Dict[str, Any]:
    """
    Get comprehensive detailed statistics about the knowledge graph.

    Returns extensive metrics including:
    - Graph size (nodes, relationships, entity type distribution)
    - Relationship quality distribution (high/medium/low confidence)
    - NOT_APPLICABLE ratio and count
    - Orphaned entities (nodes with 0 relationships)
    - Wikidata coverage (entities with wikidata_id)
    - Composite quality score (0-100)
    - Top entities by connection count

    Returns:
        Comprehensive statistics dictionary with all metrics

    Example:
        GET /api/v1/graph/stats/detailed
    """
    start_time = time.time()

    try:
        # 1. Basic graph size metrics
        size_cypher = """
        MATCH (e:Entity)
        WITH count(e) AS total_nodes
        MATCH ()-[r]->()
        WITH total_nodes, count(r) AS total_relationships
        RETURN total_nodes, total_relationships
        """
        size_result = await neo4j_service.execute_query(size_cypher)
        total_nodes = size_result[0]["total_nodes"] if size_result else 0
        total_relationships = size_result[0]["total_relationships"] if size_result else 0

        # 2. Entity type distribution
        type_dist_cypher = """
        MATCH (e:Entity)
        RETURN e.type AS entity_type, count(e) AS count
        ORDER BY count DESC
        """
        type_dist_results = await neo4j_service.execute_query(type_dist_cypher)
        entity_type_distribution = {
            record["entity_type"]: record["count"]
            for record in type_dist_results
        }

        # 3. Relationship quality distribution
        quality_cypher = """
        MATCH ()-[r]->()
        WITH r.confidence AS conf, type(r) AS rel_type
        RETURN
            sum(CASE WHEN conf > 0.8 THEN 1 ELSE 0 END) AS high_confidence,
            sum(CASE WHEN conf >= 0.5 AND conf <= 0.8 THEN 1 ELSE 0 END) AS medium_confidence,
            sum(CASE WHEN conf < 0.5 THEN 1 ELSE 0 END) AS low_confidence,
            sum(CASE WHEN rel_type = 'NOT_APPLICABLE' THEN 1 ELSE 0 END) AS not_applicable_count
        """
        quality_result = await neo4j_service.execute_query(quality_cypher)

        if quality_result:
            high_conf = quality_result[0]["high_confidence"] or 0
            medium_conf = quality_result[0]["medium_confidence"] or 0
            low_conf = quality_result[0]["low_confidence"] or 0
            not_applicable_count = quality_result[0]["not_applicable_count"] or 0
        else:
            high_conf = medium_conf = low_conf = not_applicable_count = 0

        # Calculate NOT_APPLICABLE ratio
        not_applicable_ratio = (
            not_applicable_count / total_relationships
            if total_relationships > 0 else 0.0
        )

        # 4. Orphaned entities (nodes with 0 relationships)
        orphaned_cypher = """
        MATCH (e:Entity)
        WHERE NOT (e)-[]-()
        RETURN count(e) AS orphaned_count
        """
        orphaned_result = await neo4j_service.execute_query(orphaned_cypher)
        orphaned_count = orphaned_result[0]["orphaned_count"] if orphaned_result else 0

        # 5. Wikidata coverage
        wikidata_cypher = """
        MATCH (e:Entity)
        WITH count(e) AS total,
             count(CASE WHEN e.wikidata_id IS NOT NULL THEN 1 END) AS with_wikidata
        RETURN total, with_wikidata
        """
        wikidata_result = await neo4j_service.execute_query(wikidata_cypher)

        if wikidata_result:
            wikidata_total = wikidata_result[0]["total"] or 0
            wikidata_count = wikidata_result[0]["with_wikidata"] or 0
            wikidata_coverage = wikidata_count / wikidata_total if wikidata_total > 0 else 0.0
        else:
            wikidata_count = 0
            wikidata_coverage = 0.0

        # 6. Calculate composite quality score (0-100)
        # Formula: (high_conf_ratio * 0.5 + (1 - not_applicable_ratio) * 0.3 + wikidata_coverage * 0.2) * 100
        high_conf_ratio = high_conf / total_relationships if total_relationships > 0 else 0.0
        quality_score = (
            (high_conf_ratio * 0.5) +
            ((1 - not_applicable_ratio) * 0.3) +
            (wikidata_coverage * 0.2)
        ) * 100

        # 7. Top 10 entities by connection count
        top_entities_cypher = """
        MATCH (e:Entity)
        OPTIONAL MATCH (e)-[r]-()
        WITH e, count(DISTINCT r) AS connection_count
        WHERE connection_count > 0
        ORDER BY connection_count DESC
        LIMIT 10
        RETURN
            e.name AS name,
            e.type AS type,
            connection_count
        """
        top_entities_results = await neo4j_service.execute_query(top_entities_cypher)
        top_entities = [
            {
                "name": record["name"],
                "type": record["type"],
                "connection_count": record["connection_count"]
            }
            for record in top_entities_results
        ]

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='stats_detailed', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='stats_detailed').observe(query_time_seconds)

        logger.info(
            f"Detailed stats query completed: "
            f"nodes={total_nodes}, relationships={total_relationships}, "
            f"quality_score={quality_score:.1f}, time={int(query_time_seconds * 1000)}ms"
        )

        return {
            "graph_size": {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "entity_type_distribution": entity_type_distribution
            },
            "relationship_quality": {
                "high_confidence_count": high_conf,
                "medium_confidence_count": medium_conf,
                "low_confidence_count": low_conf,
                "high_confidence_ratio": high_conf_ratio,
                "medium_confidence_ratio": medium_conf / total_relationships if total_relationships > 0 else 0.0,
                "low_confidence_ratio": low_conf / total_relationships if total_relationships > 0 else 0.0
            },
            "data_completeness": {
                "not_applicable_count": not_applicable_count,
                "not_applicable_ratio": not_applicable_ratio,
                "orphaned_entities_count": orphaned_count,
                "entities_with_wikidata": wikidata_count,
                "wikidata_coverage_ratio": wikidata_coverage
            },
            "quality_score": round(quality_score, 2),
            "top_entities": top_entities,
            "query_time_ms": int(query_time_seconds * 1000)
        }

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='stats_detailed', status='error').inc()

        logger.error(f"Detailed stats query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query detailed statistics: {str(e)}"
        )

"""
Graph Query Endpoints

Provides API endpoints for querying the knowledge graph.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import time

from app.services.neo4j_service import neo4j_service
from app.models.graph import GraphResponse, GraphNode, GraphEdge
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds,
    kg_query_results_size,
    kg_graph_nodes_total,
    kg_graph_relationships_total,
    kg_graph_entity_types_total
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/v1/graph/entity/{entity_name}/connections")
async def get_entity_connections(
    entity_name: str,
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of connections to return")
) -> GraphResponse:
    """
    Get all connections for a specific entity.

    Returns nodes connected to the entity and their relationships.

    Args:
        entity_name: Name of the entity to query
        relationship_type: Optional filter for specific relationship types
        limit: Maximum number of connections (1-1000)

    Returns:
        GraphResponse with nodes and edges

    Example:
        GET /api/v1/graph/entity/Tesla/connections
        GET /api/v1/graph/entity/Tesla/connections?relationship_type=WORKS_FOR&limit=50
    """
    start_time = time.time()

    try:
        # Build Cypher query
        # Search by name OR aliases (for merged entities after canonicalization)
        if relationship_type:
            cypher = """
            MATCH (source:Entity)
            WHERE source.name = $entity_name OR $entity_name IN COALESCE(source.aliases, [])
            WITH source
            MATCH (source)-[r:{rel_type}]->(target:Entity)
            WHERE r.confidence >= 0.5
            RETURN
                source.name AS source_name,
                COALESCE(source.type, 'UNKNOWN') AS source_type,
                source.wikidata_id AS source_wikidata_id,
                source.aliases AS source_aliases,
                target.name AS target_name,
                COALESCE(target.type, 'UNKNOWN') AS target_type,
                target.wikidata_id AS target_wikidata_id,
                type(r) AS rel_type,
                r.confidence AS confidence,
                COALESCE(r.mention_count, 1) AS mention_count,
                r.evidence AS evidence
            ORDER BY r.confidence DESC, COALESCE(r.mention_count, 1) DESC
            LIMIT $limit
            """
            cypher = cypher.replace("{rel_type}", relationship_type)
        else:
            # Search by name OR aliases (for merged entities after canonicalization)
            cypher = """
            MATCH (source:Entity)
            WHERE source.name = $entity_name OR $entity_name IN COALESCE(source.aliases, [])
            WITH source
            MATCH (source)-[r]->(target:Entity)
            WHERE r.confidence >= 0.5
            RETURN
                source.name AS source_name,
                COALESCE(source.type, 'UNKNOWN') AS source_type,
                source.wikidata_id AS source_wikidata_id,
                source.aliases AS source_aliases,
                target.name AS target_name,
                COALESCE(target.type, 'UNKNOWN') AS target_type,
                target.wikidata_id AS target_wikidata_id,
                type(r) AS rel_type,
                r.confidence AS confidence,
                COALESCE(r.mention_count, 1) AS mention_count,
                r.evidence AS evidence
            ORDER BY r.confidence DESC, COALESCE(r.mention_count, 1) DESC
            LIMIT $limit
            """

        results = await neo4j_service.execute_query(
            cypher,
            parameters={"entity_name": entity_name, "limit": limit}
        )

        # Transform results to GraphResponse
        nodes_dict = {}  # Deduplicate nodes
        edges = []

        for record in results:
            source_name = record["source_name"]
            target_name = record["target_name"]

            # Add source node with wikidata_id and aliases
            if source_name not in nodes_dict:
                source_props = {}
                if record.get("source_wikidata_id"):
                    source_props["wikidata_id"] = record["source_wikidata_id"]
                if record.get("source_aliases"):
                    source_props["aliases"] = record["source_aliases"]

                nodes_dict[source_name] = GraphNode(
                    name=source_name,
                    type=record["source_type"],
                    properties=source_props,
                    connection_count=0
                )

            # Add target node with wikidata_id
            if target_name not in nodes_dict:
                target_props = {}
                if record.get("target_wikidata_id"):
                    target_props["wikidata_id"] = record["target_wikidata_id"]

                nodes_dict[target_name] = GraphNode(
                    name=target_name,
                    type=record["target_type"],
                    properties=target_props,
                    connection_count=0
                )

            # Increment connection counts
            nodes_dict[source_name].connection_count += 1
            nodes_dict[target_name].connection_count += 1

            # Add edge
            edges.append(GraphEdge(
                source=source_name,
                target=target_name,
                relationship_type=record["rel_type"],
                confidence=record["confidence"],
                mention_count=record.get("mention_count", 1),
                evidence=record.get("evidence")
            ))

        nodes = list(nodes_dict.values())
        query_time_ms = int((time.time() - start_time) * 1000)
        query_time_seconds = (time.time() - start_time)

        # Record metrics
        kg_queries_total.labels(endpoint='connections', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='connections').observe(query_time_seconds)
        kg_query_results_size.labels(endpoint='connections').observe(len(edges))

        logger.info(
            f"Query completed: entity={entity_name}, nodes={len(nodes)}, "
            f"edges={len(edges)}, time={query_time_ms}ms"
        )

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
            query_time_ms=query_time_ms
        )

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='connections', status='error').inc()

        logger.error(f"Graph query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query graph: {str(e)}"
        )


@router.get("/api/v1/graph/stats")
async def get_graph_stats():
    """
    Get overall graph statistics.

    Returns:
        Total counts of nodes, relationships, and entity types
    """
    start_time = time.time()

    try:
        # Count nodes
        node_result = await neo4j_service.execute_query("""
            MATCH (e:Entity)
            RETURN count(e) AS total_nodes
        """)
        total_nodes = node_result[0]["total_nodes"] if node_result else 0

        # Count relationships
        rel_result = await neo4j_service.execute_query("""
            MATCH ()-[r]->()
            RETURN count(r) AS total_relationships
        """)
        total_relationships = rel_result[0]["total_relationships"] if rel_result else 0

        # Count entity types
        type_result = await neo4j_service.execute_query("""
            MATCH (e:Entity)
            RETURN e.type AS entity_type, count(*) AS count
            ORDER BY count DESC
        """)

        entity_types = {
            record["entity_type"]: record["count"]
            for record in type_result
        }

        # Update Prometheus gauges with current stats
        kg_graph_nodes_total.set(total_nodes)
        kg_graph_relationships_total.set(total_relationships)

        for entity_type, count in entity_types.items():
            kg_graph_entity_types_total.labels(entity_type=entity_type).set(count)

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='stats', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='stats').observe(query_time_seconds)

        return {
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "entity_types": entity_types
        }

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='stats', status='error').inc()

        logger.error(f"Stats query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph stats: {str(e)}"
        )

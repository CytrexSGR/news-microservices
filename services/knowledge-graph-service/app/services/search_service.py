"""
Search Service

Business logic for entity search operations in the knowledge graph.
"""

import logging
from typing import List, Optional

from app.services.neo4j_service import neo4j_service
from app.models.search import EntitySearchResult

logger = logging.getLogger(__name__)


async def search_entities(
    query: str,
    limit: int = 10,
    entity_type: Optional[str] = None
) -> List[EntitySearchResult]:
    """
    Search for entities in the knowledge graph.

    Uses full-text search on entity names with case-insensitive matching.
    Orders results by relevance (exact match first, then fuzzy match).

    Args:
        query: Search term (entity name or partial name)
        limit: Maximum number of results to return (default: 10, max: 100)
        entity_type: Optional filter by entity type (PERSON, ORGANIZATION, etc.)

    Returns:
        List of EntitySearchResult objects

    Implementation Details:
        - Exact matches ranked first
        - Case-insensitive search using LOWER()
        - Counts relationships per entity (connection_count)
        - Includes wikidata_id if available
        - Filters entities with confidence >= 0.5 in relationships

    Example:
        results = await search_entities("Tesla", limit=10)
        results = await search_entities("Musk", limit=5, entity_type="PERSON")
    """
    logger.debug(f"Searching entities: query='{query}', limit={limit}, entity_type={entity_type}")

    # Build Cypher query with optional type filter
    cypher_query = """
    MATCH (e:Entity)
    WHERE LOWER(e.name) CONTAINS LOWER($query)
    """

    # Add entity type filter if provided
    if entity_type:
        cypher_query += " AND e.type = $entity_type"

    # Count relationships (connections) for each entity
    # Note: Only count relationships with confidence >= 0.5
    # Ranking: Exact match (match_rank=0) first, then by connection_count, then alphabetically
    cypher_query += """
    OPTIONAL MATCH (e)-[r]-()
    WHERE r.confidence >= 0.5
    WITH e, count(r) AS connection_count,
         CASE WHEN LOWER(e.name) = LOWER($query) THEN 0 ELSE 1 END AS match_rank
    RETURN
        e.name AS name,
        COALESCE(e.type, 'UNKNOWN') AS type,
        e.last_seen AS last_seen,
        connection_count,
        e.wikidata_id AS wikidata_id
    ORDER BY match_rank, connection_count DESC, e.name ASC
    LIMIT $limit
    """

    # Prepare query parameters
    parameters = {
        "query": query,
        "limit": limit
    }

    if entity_type:
        parameters["entity_type"] = entity_type

    # Execute query
    results = await neo4j_service.execute_query(cypher_query, parameters)

    # Transform results to EntitySearchResult models
    search_results = []
    for record in results:
        # Convert Neo4j DateTime to Python datetime if present
        last_seen = record.get("last_seen")
        if last_seen is not None and hasattr(last_seen, "to_native"):
            last_seen = last_seen.to_native()

        search_results.append(EntitySearchResult(
            name=record["name"],
            type=record["type"],
            last_seen=last_seen,
            connection_count=record["connection_count"],
            wikidata_id=record.get("wikidata_id")
        ))

    logger.debug(f"Found {len(search_results)} results for query '{query}'")

    return search_results

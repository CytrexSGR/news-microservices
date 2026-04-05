"""
Entity Search Endpoints

Provides API endpoints for searching entities in the knowledge graph.
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.search_service import search_entities
from app.models.search import EntitySearchResponse
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds,
    kg_query_results_size
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/v1/graph/search", response_model=EntitySearchResponse)
async def search_entities_endpoint(
    query: str = Query(..., min_length=1, max_length=200, description="Search term for entity names"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results (1-100)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (PERSON, ORGANIZATION, LOCATION, etc.)")
):
    """
    Search for entities in the knowledge graph.

    Performs full-text search on entity names with case-insensitive matching.
    Results are ordered by relevance (exact match first, then by connection count).

    Args:
        query: Search term (required, 1-200 characters)
        limit: Maximum results to return (default: 10, max: 100)
        entity_type: Optional filter by entity type

    Returns:
        EntitySearchResponse with matching entities and metadata

    Examples:
        - GET /api/v1/graph/search?query=Tesla&limit=10
        - GET /api/v1/graph/search?query=Elon&entity_type=PERSON
        - GET /api/v1/graph/search?query=Microsoft&limit=5

    Response:
        {
            "results": [
                {
                    "name": "Tesla",
                    "type": "ORGANIZATION",
                    "last_seen": "2024-11-02T10:30:00Z",
                    "connection_count": 45,
                    "wikidata_id": "Q478214"
                }
            ],
            "total_results": 1,
            "query_time_ms": 123,
            "query": "Tesla",
            "entity_type_filter": null
        }
    """
    start_time = time.time()

    try:
        logger.info(f"Entity search request: query='{query}', limit={limit}, entity_type={entity_type}")

        # Execute search via service layer
        results = await search_entities(
            query=query,
            limit=limit,
            entity_type=entity_type
        )

        # Calculate query time
        query_time_seconds = time.time() - start_time
        query_time_ms = int(query_time_seconds * 1000)

        # Record Prometheus metrics
        kg_queries_total.labels(endpoint='search', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='search').observe(query_time_seconds)
        kg_query_results_size.labels(endpoint='search').observe(len(results))

        logger.info(
            f"Search completed: query='{query}', results={len(results)}, "
            f"time={query_time_ms}ms"
        )

        return EntitySearchResponse(
            results=results,
            total_results=len(results),
            query_time_ms=query_time_ms,
            query=query,
            entity_type_filter=entity_type
        )

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='search', status='error').inc()

        logger.error(f"Entity search failed: query='{query}', error={e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search entities: {str(e)}"
        )

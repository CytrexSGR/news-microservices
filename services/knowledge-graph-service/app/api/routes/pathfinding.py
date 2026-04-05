"""
Pathfinding Endpoints

Provides API endpoints for finding paths between entities in the knowledge graph.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Path
import time

from app.services.pathfinding_service import pathfinding_service
from app.models.pathfinding import PathfindingResponse
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds,
    kg_query_results_size
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/api/v1/graph/path/{entity1}/{entity2}",
    response_model=PathfindingResponse,
    summary="Find paths between two entities",
    description="""
    Find shortest paths between two entities in the knowledge graph.

    Uses Neo4j's allShortestPaths() algorithm to find multiple paths up to a maximum depth.
    Only includes relationships with confidence >= 0.5.

    **Use Cases:**
    - Discover hidden connections between people/organizations
    - Analyze relationship chains (e.g., "How is Person A connected to Company B?")
    - Network analysis and influence mapping

    **Example:**
    - `/api/v1/graph/path/Elon Musk/Tesla?max_depth=2&limit=3`
    - Returns up to 3 shortest paths between entities with max 2 hops
    """
)
async def find_path(
    entity1: str = Path(
        ...,
        description="Source entity name (case-sensitive)",
        example="Elon Musk"
    ),
    entity2: str = Path(
        ...,
        description="Target entity name (case-sensitive)",
        example="Tesla"
    ),
    max_depth: int = Query(
        3,
        ge=1,
        le=5,
        description="Maximum path length (hops). Higher values = slower query."
    ),
    limit: int = Query(
        3,
        ge=1,
        le=10,
        description="Maximum number of paths to return"
    ),
    min_confidence: float = Query(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum relationship confidence score"
    )
) -> PathfindingResponse:
    """
    Find shortest paths between two entities.

    Args:
        entity1: Source entity name
        entity2: Target entity name
        max_depth: Maximum path length (1-5 hops, default: 3)
        limit: Maximum number of paths (1-10, default: 3)
        min_confidence: Minimum relationship confidence (0.0-1.0, default: 0.5)

    Returns:
        PathfindingResponse with found paths and metadata

    Raises:
        HTTPException: If query fails or entities don't exist

    Example Response:
        {
            "paths": [
                {
                    "length": 1,
                    "nodes": [
                        {"name": "Elon Musk", "type": "PERSON"},
                        {"name": "Tesla", "type": "ORGANIZATION"}
                    ],
                    "relationships": [
                        {
                            "type": "CEO_OF",
                            "confidence": 0.95,
                            "evidence": "Elon Musk is CEO of Tesla"
                        }
                    ]
                }
            ],
            "shortest_path_length": 1,
            "query_time_ms": 42,
            "entity1": "Elon Musk",
            "entity2": "Tesla",
            "max_depth": 3,
            "total_paths_found": 1
        }
    """
    start_time = time.time()

    try:
        logger.info(
            f"Pathfinding request: {entity1} -> {entity2} "
            f"(max_depth={max_depth}, limit={limit})"
        )

        # Find paths using pathfinding service
        paths = await pathfinding_service.find_paths(
            entity1=entity1,
            entity2=entity2,
            max_depth=max_depth,
            limit=limit,
            min_confidence=min_confidence
        )

        # Calculate metrics
        query_time_ms = int((time.time() - start_time) * 1000)
        query_time_seconds = time.time() - start_time

        # Determine shortest path length
        shortest_path_length = min((p.length for p in paths), default=0)

        # Record Prometheus metrics
        kg_queries_total.labels(endpoint='pathfinding', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='pathfinding').observe(query_time_seconds)
        kg_query_results_size.labels(endpoint='pathfinding').observe(len(paths))

        logger.info(
            f"Pathfinding completed: {entity1} -> {entity2}, "
            f"found {len(paths)} paths in {query_time_ms}ms, "
            f"shortest={shortest_path_length} hops"
        )

        # Check if no paths found
        if len(paths) == 0:
            logger.warning(
                f"No paths found between '{entity1}' and '{entity2}' "
                f"(max_depth={max_depth}, min_confidence={min_confidence})"
            )

        return PathfindingResponse(
            paths=paths,
            shortest_path_length=shortest_path_length,
            query_time_ms=query_time_ms,
            entity1=entity1,
            entity2=entity2,
            max_depth=max_depth,
            total_paths_found=len(paths)
        )

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='pathfinding', status='error').inc()

        logger.error(
            f"Pathfinding query failed: {entity1} -> {entity2}, error: {e}",
            exc_info=True
        )

        # Check for common errors
        if "Node(0)" in str(e) or "does not exist" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"One or both entities not found in graph: '{entity1}', '{entity2}'"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to find paths: {str(e)}"
        )

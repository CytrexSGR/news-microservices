"""
Article Endpoints

API routes for querying article-entity relationships in the knowledge graph.
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional

from app.services.article_service import article_service
from app.models.articles import ArticleEntitiesResponse
from app.core.metrics import (
    kg_queries_total,
    kg_query_duration_seconds,
    kg_query_results_size
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/api/v1/graph/articles/{article_id}/entities",
    response_model=ArticleEntitiesResponse
)
async def get_article_entities(
    article_id: str = Path(..., description="Article identifier (UUID or custom ID)"),
    entity_type: Optional[str] = Query(
        None,
        description="Filter by entity type (PERSON, ORGANIZATION, LOCATION, etc.)"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=200,
        description="Maximum number of entities to return (1-200)"
    )
) -> ArticleEntitiesResponse:
    """
    Fetch all entities extracted from a specific article.

    This endpoint retrieves entities that have an `EXTRACTED_FROM` relationship
    to the specified article in the knowledge graph.

    **Query Parameters:**
    - `entity_type` (optional): Filter results by entity type (e.g., "PERSON", "ORGANIZATION")
    - `limit`: Maximum entities to return (default: 50, max: 200)

    **Returns:**
    - List of entities with confidence scores, mention counts, and metadata
    - Article information (title, URL) if available in graph
    - Query execution time

    **Notes:**
    - Entities are ordered by confidence score (descending), then mention count
    - If Article node doesn't exist in Neo4j yet, returns entities with article_title=null
    - Empty result means either:
        1. Article has no entities extracted yet
        2. Article ID doesn't exist
        3. All entities filtered out by entity_type

    **Example:**
    ```
    GET /api/v1/graph/articles/abc123/entities?entity_type=PERSON&limit=20
    ```
    """
    start_time = time.time()

    try:
        # Fetch entities from graph
        entities, article_node = await article_service.get_article_entities(
            article_id=article_id,
            entity_type=entity_type,
            limit=limit
        )

        # Calculate query time
        query_time_ms = int((time.time() - start_time) * 1000)
        query_time_seconds = time.time() - start_time

        # Build response
        response = ArticleEntitiesResponse(
            article_id=article_id,
            article_title=article_node.title if article_node else None,
            article_url=article_node.url if article_node else None,
            total_entities=len(entities),
            entities=entities,
            query_time_ms=query_time_ms
        )

        # Record metrics
        kg_queries_total.labels(endpoint='article_entities', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='article_entities').observe(query_time_seconds)
        kg_query_results_size.labels(endpoint='article_entities').observe(len(entities))

        logger.info(
            f"Article entities query completed: article_id={article_id}, "
            f"entity_type={entity_type}, entities={len(entities)}, time={query_time_ms}ms"
        )

        return response

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='article_entities', status='error').inc()

        logger.error(
            f"Failed to fetch article entities: article_id={article_id}, error={e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch article entities: {str(e)}"
        )


@router.get("/api/v1/graph/articles/{article_id}/info")
async def get_article_info(
    article_id: str = Path(..., description="Article identifier")
):
    """
    Get article information from knowledge graph.

    Returns article node metadata including:
    - Title, URL, published date
    - Total count of extracted entities

    **Example:**
    ```
    GET /api/v1/graph/articles/abc123/info
    ```
    """
    start_time = time.time()

    try:
        article_info = await article_service.get_article_info(article_id)

        if not article_info:
            raise HTTPException(
                status_code=404,
                detail=f"Article not found in graph: {article_id}"
            )

        # Calculate query time
        query_time_ms = int((time.time() - start_time) * 1000)
        query_time_seconds = time.time() - start_time

        # Record metrics
        kg_queries_total.labels(endpoint='article_info', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='article_info').observe(query_time_seconds)

        logger.info(
            f"Article info query completed: article_id={article_id}, time={query_time_ms}ms"
        )

        return {
            "article_id": article_info.article_id,
            "title": article_info.title,
            "url": article_info.url,
            "published_date": article_info.published_date,
            "entity_count": article_info.entity_count,
            "query_time_ms": query_time_ms
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='article_info', status='error').inc()

        logger.error(
            f"Failed to fetch article info: article_id={article_id}, error={e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch article info: {str(e)}"
        )

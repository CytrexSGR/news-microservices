"""
Search API endpoints
"""
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_optional_user
from app.services.search_service import SearchService
from app.services.suggestion_service import SuggestionService
from app.schemas.search import (
    SearchRequest, AdvancedSearchRequest, SearchResponse,
    SuggestionRequest, SuggestionResponse,
    SemanticSearchRequest, SemanticSearchResponse,
    # Layer 2 schemas
    ClusterEntityRequest, ClusterEntityResponse,
    CrossClusterBridgeRequest, CrossClusterBridgeResponse,
    TemporalEntityRequest, TemporalEntityResponse,
    # Layer 2.2 Neo4j schemas
    ArticleEntitiesFromGraphResponse, GraphEntity,
    EntityConnectionsResponse, EntityConnectionNode, EntityConnectionEdge,
    EntityPathsResponse, EntityPath, EntityPathRelationship,
)
from app.services.semantic_search_service import SemanticSearchService
from app.services.entity_enrichment_service import EntityEnrichmentService
from app.services.knowledge_graph_client import get_knowledge_graph_client

router = APIRouter()


@router.get("", response_model=SearchResponse)
async def search_articles(
    query: Optional[str] = Query(None, max_length=500),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Basic search endpoint.

    Searches articles using PostgreSQL full-text search.

    Args:
        query: Search query
        page: Page number
        page_size: Results per page
        source: Filter by source
        sentiment: Filter by sentiment
        date_from: Filter by date from (ISO format)
        date_to: Filter by date to (ISO format)

    Returns:
        SearchResponse: Search results
    """
    from app.schemas.search import SearchFilters
    from datetime import datetime

    # Build filters
    filters = SearchFilters()
    if source:
        filters.source = source.split(',')
    if sentiment:
        filters.sentiment = sentiment.split(',')
    if date_from:
        filters.date_from = datetime.fromisoformat(date_from)
    if date_to:
        filters.date_to = datetime.fromisoformat(date_to)

    # Create request
    request = SearchRequest(
        query=query,
        page=page,
        page_size=page_size,
        filters=filters if any([source, sentiment, date_from, date_to]) else None
    )

    # Execute search
    service = SearchService(db)
    user_id = current_user['user_id'] if current_user else None

    return await service.search(request, user_id)


@router.post("/advanced", response_model=SearchResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Advanced search endpoint.

    Supports complex queries with:
    - Fuzzy matching
    - Highlighting
    - Faceted search
    - AND/OR operators
    - Phrase search
    - Field search
    - Exclusion

    Args:
        request: Advanced search request

    Returns:
        SearchResponse: Search results with facets
    """
    service = SearchService(db)
    user_id = current_user['user_id'] if current_user else None

    return await service.advanced_search(request, user_id)


@router.get("/suggest", response_model=SuggestionResponse)
async def get_suggestions(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Autocomplete suggestions endpoint.

    Provides query suggestions based on:
    - Popular searches
    - Article titles
    - Search history

    Args:
        query: Partial query string
        limit: Maximum suggestions

    Returns:
        SuggestionResponse: List of suggestions
    """
    service = SuggestionService(db)
    suggestions = await service.get_suggestions(query, limit)

    return SuggestionResponse(
        query=query,
        suggestions=suggestions
    )


@router.get("/related")
async def get_related_searches(
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Get related search queries.

    Args:
        query: Current query
        limit: Maximum related queries

    Returns:
        List of related queries
    """
    service = SuggestionService(db)
    related = await service.get_related_searches(query, limit)

    return {
        'query': query,
        'related': related
    }


@router.get("/popular")
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most popular search queries.

    Args:
        limit: Maximum queries

    Returns:
        List of popular queries with hit counts
    """
    service = SuggestionService(db)
    popular = await service.get_popular_queries(limit)

    return {
        'popular_queries': popular,
        'total': len(popular)
    }


@router.get("/facets")
async def get_facets(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available filter options (facets).

    Returns all unique sources and categories from indexed articles.
    This allows the frontend to dynamically populate filter dropdowns.

    Returns:
        Dict with sources and categories arrays
    """
    service = SearchService(db)
    facets = await service.get_facets()

    return facets


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Semantic search using vector similarity (Layer 1).

    Uses OpenAI embeddings to convert the query to a vector,
    then searches article_analysis.embedding using pgvector cosine similarity.

    Features:
    - Natural language queries
    - Semantic similarity matching (not keyword-based)
    - Optional result clustering with HDBSCAN
    - Filters by source, sentiment, date range

    Args:
        request: Semantic search request with query and options

    Returns:
        SemanticSearchResponse with results and optional clusters

    Example:
        POST /api/v1/search/semantic
        {
            "query": "federal reserve interest rate policy impact on markets",
            "limit": 50,
            "min_similarity": 0.5,
            "cluster_results": true
        }
    """
    service = SemanticSearchService(db)
    return await service.search(request)


# Layer 2: Knowledge Graph Evolution Endpoints

@router.get("/clusters/entities", response_model=ClusterEntityResponse)
async def get_cluster_entities(
    cluster_id: Optional[str] = Query(None, description="Specific cluster ID"),
    limit: int = Query(20, ge=1, le=100, description="Max clusters to return"),
    min_entity_mentions: int = Query(2, ge=1, description="Minimum mentions"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types"),
    status: str = Query("active", description="Cluster status filter"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get clusters enriched with their top entities (Layer 2.1).

    Extracts entities from article_analysis.tier1_results JSONB
    and aggregates them by cluster.

    Features:
    - Entity extraction from JSONB tier1_results
    - Aggregation across cluster articles
    - Filter by entity types (PERSON, ORGANIZATION, LOCATION, etc.)

    Returns:
        ClusterEntityResponse with entity-enriched clusters

    Example:
        GET /api/v1/search/clusters/entities?limit=10&min_entity_mentions=5
    """
    request = ClusterEntityRequest(
        cluster_id=cluster_id,
        limit=limit,
        min_entity_mentions=min_entity_mentions,
        entity_types=entity_types.split(",") if entity_types else None,
        status=status,
    )

    service = EntityEnrichmentService(db)
    return await service.get_entity_enriched_clusters(request)


@router.get("/clusters/bridges", response_model=CrossClusterBridgeResponse)
async def get_cross_cluster_bridges(
    min_clusters: int = Query(2, ge=2, le=20, description="Min clusters per entity"),
    limit: int = Query(50, ge=1, le=200, description="Max bridge entities"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find entities that bridge multiple clusters (Layer 2.3).

    Bridge entities appear in multiple clusters and may indicate
    cross-cutting themes, key actors, or connecting topics.

    Features:
    - Cross-cluster entity detection
    - Ranked by cluster count and total mentions
    - Filter by entity types

    Returns:
        CrossClusterBridgeResponse with bridge entities

    Example:
        GET /api/v1/search/clusters/bridges?min_clusters=3&limit=20
    """
    request = CrossClusterBridgeRequest(
        min_clusters=min_clusters,
        limit=limit,
        entity_types=entity_types.split(",") if entity_types else None,
    )

    service = EntityEnrichmentService(db)
    return await service.get_cross_cluster_bridges(request)


@router.get("/entities/temporal", response_model=TemporalEntityResponse)
async def get_temporal_entity_trends(
    entity_name: Optional[str] = Query(None, description="Specific entity to track"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    days: int = Query(30, ge=1, le=365, description="Time window in days"),
    granularity: str = Query("day", description="Time granularity (hour, day, week)"),
    min_mentions: int = Query(5, ge=1, description="Minimum mentions to include"),
    limit: int = Query(50, ge=1, le=200, description="Max entities to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Track entity mentions over time (Layer 2.4).

    Provides temporal analysis of entity mentions to identify
    trending and declining entities.

    Features:
    - Time-series entity mention tracking
    - Configurable time granularity (hour/day/week)
    - Filter by specific entity or type

    Returns:
        TemporalEntityResponse with entity trends

    Example:
        GET /api/v1/search/entities/temporal?days=7&granularity=day
    """
    request = TemporalEntityRequest(
        entity_name=entity_name,
        entity_type=entity_type,
        days=days,
        granularity=granularity,
        min_mentions=min_mentions,
        limit=limit,
    )

    service = EntityEnrichmentService(db)
    return await service.get_temporal_entity_trends(request)


# Layer 2.2: Neo4j Knowledge Graph Integration Endpoints

@router.get(
    "/graph/articles/{article_id}/entities",
    response_model=ArticleEntitiesFromGraphResponse
)
async def get_article_entities_from_graph(
    article_id: str = Path(..., description="Article UUID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=200, description="Max entities to return"),
):
    """
    Get entities for an article from Neo4j knowledge graph (Layer 2.2).

    Queries the knowledge-graph-service to retrieve entities that have
    EXTRACTED_FROM relationships to the specified article.

    Features:
    - Direct Neo4j graph queries via knowledge-graph-service
    - Filter by entity type (PERSON, ORGANIZATION, LOCATION, etc.)
    - Includes relationship type and confidence scores

    Returns:
        ArticleEntitiesFromGraphResponse with entities from Neo4j

    Example:
        GET /api/v1/search/graph/articles/abc123-def456/entities?entity_type=PERSON
    """
    start_time = time.time()
    client = get_knowledge_graph_client()

    # Check if service is available
    is_available = await client.health_check()

    if not is_available:
        return ArticleEntitiesFromGraphResponse(
            article_id=article_id,
            article_title=None,
            article_url=None,
            total_entities=0,
            entities=[],
            graph_available=False,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # Query knowledge graph
    result = await client.get_article_entities(
        article_id=article_id,
        entity_type=entity_type,
        limit=limit,
    )

    if result is None:
        return ArticleEntitiesFromGraphResponse(
            article_id=article_id,
            article_title=None,
            article_url=None,
            total_entities=0,
            entities=[],
            graph_available=True,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # Convert to response objects
    entities = [
        GraphEntity(
            name=e.get("name", "Unknown"),
            type=e.get("type", "UNKNOWN"),
            confidence=e.get("confidence", 0.5),
            relationship_type=e.get("relationship_type"),
        )
        for e in result.get("entities", [])
    ]

    return ArticleEntitiesFromGraphResponse(
        article_id=article_id,
        article_title=result.get("article_title"),
        article_url=result.get("article_url"),
        total_entities=result.get("total_entities", len(entities)),
        entities=entities,
        graph_available=True,
        execution_time_ms=(time.time() - start_time) * 1000,
    )


@router.get(
    "/graph/entity/{entity_name}/connections",
    response_model=EntityConnectionsResponse
)
async def get_entity_connections_from_graph(
    entity_name: str = Path(..., description="Entity name"),
    relationship_type: Optional[str] = Query(
        None,
        description="Filter by relationship type (WORKS_FOR, MENTIONED_WITH, etc.)"
    ),
    limit: int = Query(100, ge=1, le=500, description="Max connections to return"),
):
    """
    Get connections for an entity from Neo4j knowledge graph (Layer 2.2).

    Queries the knowledge-graph-service to retrieve all entities
    connected to the specified entity, along with their relationships.

    Features:
    - Graph-based entity relationship exploration
    - Filter by relationship type
    - Returns nodes and edges for visualization

    Returns:
        EntityConnectionsResponse with nodes and edges from Neo4j

    Example:
        GET /api/v1/search/graph/entity/Tesla/connections?relationship_type=WORKS_FOR
    """
    start_time = time.time()
    client = get_knowledge_graph_client()

    # Check if service is available
    is_available = await client.health_check()

    if not is_available:
        return EntityConnectionsResponse(
            entity_name=entity_name,
            nodes=[],
            edges=[],
            total_nodes=0,
            total_edges=0,
            graph_available=False,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # Query knowledge graph
    result = await client.get_entity_connections(
        entity_name=entity_name,
        relationship_type=relationship_type,
        limit=limit,
    )

    if result is None:
        return EntityConnectionsResponse(
            entity_name=entity_name,
            nodes=[],
            edges=[],
            total_nodes=0,
            total_edges=0,
            graph_available=True,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # Convert to response objects
    nodes = [
        EntityConnectionNode(
            name=n.get("name", "Unknown"),
            type=n.get("type", "UNKNOWN"),
            wikidata_id=n.get("wikidata_id"),
            connection_count=n.get("connection_count", 0),
        )
        for n in result.get("nodes", [])
    ]

    edges = []
    for e in result.get("edges", []):
        # Handle evidence field - can be a list, string, or None
        evidence_raw = e.get("evidence")
        if isinstance(evidence_raw, list):
            evidence = evidence_raw
        elif isinstance(evidence_raw, str):
            evidence = [evidence_raw] if evidence_raw else None
        else:
            evidence = None

        edges.append(EntityConnectionEdge(
            source=e.get("source", ""),
            target=e.get("target", ""),
            relationship_type=e.get("relationship_type", "RELATED_TO"),
            confidence=e.get("confidence", 0.5),
            mention_count=e.get("mention_count", 1),
            evidence=evidence,
        ))

    return EntityConnectionsResponse(
        entity_name=entity_name,
        nodes=nodes,
        edges=edges,
        total_nodes=result.get("total_nodes", len(nodes)),
        total_edges=result.get("total_edges", len(edges)),
        graph_available=True,
        execution_time_ms=(time.time() - start_time) * 1000,
    )


@router.get("/graph/paths/{entity1}/{entity2}", response_model=EntityPathsResponse)
async def get_entity_paths_from_graph(
    entity1: str = Path(..., description="First entity name"),
    entity2: str = Path(..., description="Second entity name"),
):
    """
    Find paths between two entities in the knowledge graph (Layer 2.2).

    Queries the knowledge-graph-service to find all paths connecting
    two entities in the Neo4j graph, useful for discovering relationships.

    Features:
    - Pathfinding between any two entities
    - Returns multiple paths with relationship types
    - Shows shortest path length

    Returns:
        EntityPathsResponse with paths from Neo4j

    Example:
        GET /api/v1/search/graph/paths/Trump/Israel
    """
    start_time = time.time()
    client = get_knowledge_graph_client()

    # Check if service is available
    is_available = await client.health_check()

    if not is_available:
        return EntityPathsResponse(
            entity1=entity1,
            entity2=entity2,
            paths=[],
            total_paths=0,
            shortest_path_length=None,
            graph_available=False,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # Query knowledge graph
    result = await client.find_entity_paths(
        entity1=entity1,
        entity2=entity2,
    )

    if result is None:
        return EntityPathsResponse(
            entity1=entity1,
            entity2=entity2,
            paths=[],
            total_paths=0,
            shortest_path_length=None,
            graph_available=True,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    # Convert to response objects
    paths = []
    for p in result.get("paths", []):
        # Handle nodes - can be strings or dicts
        raw_nodes = p.get("nodes", [])
        node_names = []
        for n in raw_nodes:
            if isinstance(n, dict):
                node_names.append(n.get("name", str(n)))
            else:
                node_names.append(str(n))

        paths.append(EntityPath(
            length=p.get("length", 0),
            nodes=node_names,
            relationships=[
                EntityPathRelationship(
                    type=r.get("type", "RELATED_TO"),
                    confidence=r.get("confidence", 0.5),
                )
                for r in p.get("relationships", [])
            ],
        ))

    return EntityPathsResponse(
        entity1=entity1,
        entity2=entity2,
        paths=paths,
        total_paths=result.get("total_paths", len(paths)),
        shortest_path_length=result.get("shortest_path_length"),
        graph_available=True,
        execution_time_ms=(time.time() - start_time) * 1000,
    )

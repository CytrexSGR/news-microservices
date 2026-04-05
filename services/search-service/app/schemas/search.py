"""
Pydantic schemas for Search Service
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Search Request/Response Schemas

class SearchFilters(BaseModel):
    """Search filters"""
    source: Optional[List[str]] = None
    sentiment: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchRequest(BaseModel):
    """Basic search request"""
    query: Optional[str] = Field(default='', max_length=500)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    filters: Optional[SearchFilters] = None


class AdvancedSearchRequest(SearchRequest):
    """Advanced search request with operators"""
    use_fuzzy: bool = Field(default=True)
    highlight: bool = Field(default=True)
    facets: Optional[List[str]] = Field(default=None)  # source, sentiment, date


class SearchResultItem(BaseModel):
    """Single search result"""
    article_id: str
    title: str
    content: str
    author: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    entities: Optional[List[str]] = None
    relevance_score: float
    highlight: Optional[Dict[str, List[str]]] = None

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Search response"""
    query: Optional[str] = ''
    total: int
    page: int
    page_size: int
    results: List[SearchResultItem]
    facets: Optional[Dict[str, Any]] = None
    execution_time_ms: float


# Suggestion Schemas

class SuggestionRequest(BaseModel):
    """Autocomplete suggestion request"""
    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1, le=20)


class SuggestionResponse(BaseModel):
    """Autocomplete suggestion response"""
    query: str
    suggestions: List[str]


# Search History Schemas

class SearchHistoryItem(BaseModel):
    """Search history item"""
    id: int
    query: str
    filters: Optional[Dict[str, Any]] = None
    results_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SearchHistoryResponse(BaseModel):
    """Search history response"""
    total: int
    page: int
    page_size: int
    items: List[SearchHistoryItem]


# Saved Search Schemas

class SavedSearchCreate(BaseModel):
    """Create saved search"""
    name: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    notifications_enabled: bool = Field(default=False)


class SavedSearchUpdate(BaseModel):
    """Update saved search"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    query: Optional[str] = Field(None, min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    notifications_enabled: Optional[bool] = None


class SavedSearchResponse(BaseModel):
    """Saved search response"""
    id: int
    name: str
    query: str
    filters: Optional[Dict[str, Any]] = None
    notifications_enabled: bool
    last_notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedSearchListResponse(BaseModel):
    """Saved search list response"""
    total: int
    items: List[SavedSearchResponse]


# Analytics Schemas

class PopularQuery(BaseModel):
    """Popular query"""
    query: str
    hits: int
    avg_position: Optional[float] = None


class AnalyticsResponse(BaseModel):
    """Analytics response"""
    popular_queries: List[PopularQuery]
    total_searches: int
    unique_queries: int


# Semantic Search Schemas (Layer 1)

class SemanticSearchRequest(BaseModel):
    """Semantic search request using vector similarity"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language search query")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum results to return")
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum cosine similarity threshold")
    cluster_results: bool = Field(default=True, description="Group results by semantic clusters")
    filters: Optional[SearchFilters] = None


class SemanticSearchResultItem(BaseModel):
    """Single semantic search result"""
    article_id: str
    title: str
    content: str
    author: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    entities: Optional[List[Any]] = Field(default=None, description="Entity objects or strings")
    similarity: float = Field(description="Cosine similarity score (0-1)")
    cluster_id: Optional[int] = Field(default=None, description="Cluster ID if clustering enabled")

    model_config = ConfigDict(from_attributes=True)


class SemanticSearchCluster(BaseModel):
    """A cluster of semantically related results"""
    cluster_id: int
    size: int
    representative_title: str
    avg_similarity: float
    articles: List[SemanticSearchResultItem]


class SemanticSearchResponse(BaseModel):
    """Semantic search response"""
    query: str
    total: int
    results: List[SemanticSearchResultItem]
    clusters: Optional[List[SemanticSearchCluster]] = Field(
        default=None,
        description="Results grouped by semantic clusters (if cluster_results=True)"
    )
    embedding_available: bool = Field(description="Whether embedding service is available")
    execution_time_ms: float


# Layer 2: Knowledge Graph Evolution Schemas

class ClusterEntity(BaseModel):
    """Entity extracted from cluster articles"""
    name: str = Field(description="Entity name")
    entity_type: str = Field(description="Entity type (PERSON, ORGANIZATION, LOCATION, etc.)")
    confidence: float = Field(description="Average confidence across mentions")
    mention_count: int = Field(description="Total mentions across cluster articles")
    article_count: int = Field(default=1, description="Number of articles mentioning this entity")


class EntityEnrichedCluster(BaseModel):
    """Cluster enriched with entity information"""
    cluster_id: str = Field(description="Cluster UUID")
    title: str = Field(description="Cluster title")
    status: str = Field(description="Cluster status (active, archived, merged)")
    article_count: int = Field(description="Number of articles in cluster")
    top_entities: List[ClusterEntity] = Field(description="Top entities by mention count")
    entity_types: Dict[str, int] = Field(description="Entity count by type")
    first_seen_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClusterEntityRequest(BaseModel):
    """Request for cluster entity enrichment"""
    cluster_id: Optional[str] = Field(default=None, description="Specific cluster ID (optional)")
    limit: int = Field(default=20, ge=1, le=100, description="Max clusters to return")
    min_entity_mentions: int = Field(default=2, ge=1, description="Minimum entity mentions to include")
    entity_types: Optional[List[str]] = Field(default=None, description="Filter by entity types")
    status: str = Field(default="active", description="Cluster status filter")


class ClusterEntityResponse(BaseModel):
    """Response with entity-enriched clusters"""
    total: int
    clusters: List[EntityEnrichedCluster]
    execution_time_ms: float


class CrossClusterBridge(BaseModel):
    """Entity that bridges multiple clusters"""
    entity_name: str = Field(description="Entity name")
    entity_type: Optional[str] = Field(default=None, description="Primary entity type")
    cluster_count: int = Field(description="Number of clusters containing this entity")
    total_mentions: int = Field(description="Total mentions across all clusters")
    connected_clusters: List[Dict[str, Any]] = Field(
        description="List of clusters with id, title, and mention count"
    )


class CrossClusterBridgeRequest(BaseModel):
    """Request for cross-cluster entity bridges"""
    min_clusters: int = Field(default=2, ge=2, le=20, description="Minimum clusters an entity must appear in")
    limit: int = Field(default=50, ge=1, le=200, description="Max bridge entities to return")
    entity_types: Optional[List[str]] = Field(default=None, description="Filter by entity types")


class CrossClusterBridgeResponse(BaseModel):
    """Response with cross-cluster bridges"""
    total: int
    bridges: List[CrossClusterBridge]
    execution_time_ms: float


class TemporalEntityMention(BaseModel):
    """Entity mention in a time window"""
    entity_name: str
    entity_type: str
    period_start: datetime
    period_end: datetime
    mention_count: int
    article_count: int
    cluster_count: int
    avg_confidence: float


class TemporalEntityRequest(BaseModel):
    """Request for temporal entity tracking"""
    entity_name: Optional[str] = Field(default=None, description="Specific entity to track")
    entity_type: Optional[str] = Field(default=None, description="Filter by entity type")
    days: int = Field(default=30, ge=1, le=365, description="Number of days to analyze")
    granularity: str = Field(default="day", description="Time granularity (hour, day, week)")
    min_mentions: int = Field(default=5, ge=1, description="Minimum mentions to include")
    limit: int = Field(default=50, ge=1, le=200, description="Max entities to return")


class TemporalEntityResponse(BaseModel):
    """Response with temporal entity data"""
    total_entities: int
    time_range: Dict[str, datetime]
    granularity: str
    trends: List[Dict[str, Any]] = Field(description="Entity trends over time")
    execution_time_ms: float


# Layer 2.2: Neo4j Entity Relationships Schemas

class GraphEntity(BaseModel):
    """Entity from Neo4j knowledge graph"""
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type (PERSON, ORGANIZATION, LOCATION, etc.)")
    confidence: float = Field(default=0.5, description="Confidence score")
    relationship_type: Optional[str] = Field(default=None, description="Relationship to article")


class ArticleEntitiesFromGraphRequest(BaseModel):
    """Request for article entities from knowledge graph"""
    article_id: str = Field(description="Article UUID")
    entity_type: Optional[str] = Field(default=None, description="Filter by entity type")
    limit: int = Field(default=50, ge=1, le=200, description="Max entities to return")


class ArticleEntitiesFromGraphResponse(BaseModel):
    """Response with article entities from Neo4j"""
    article_id: str
    article_title: Optional[str] = None
    article_url: Optional[str] = None
    total_entities: int
    entities: List[GraphEntity]
    graph_available: bool = Field(description="Whether knowledge graph service is available")
    execution_time_ms: float


class EntityConnectionNode(BaseModel):
    """Node in entity connection graph"""
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type")
    wikidata_id: Optional[str] = Field(default=None, description="Wikidata identifier")
    connection_count: int = Field(default=0, description="Total connections")


class EntityConnectionEdge(BaseModel):
    """Edge (relationship) in entity connection graph"""
    source: str = Field(description="Source entity name")
    target: str = Field(description="Target entity name")
    relationship_type: str = Field(description="Type of relationship")
    confidence: float = Field(description="Relationship confidence")
    mention_count: int = Field(default=1, description="Number of mentions")
    evidence: Optional[List[str]] = Field(default=None, description="Article IDs as evidence")


class EntityConnectionsRequest(BaseModel):
    """Request for entity connections from knowledge graph"""
    entity_name: str = Field(description="Entity to find connections for")
    relationship_type: Optional[str] = Field(default=None, description="Filter by relationship type")
    limit: int = Field(default=100, ge=1, le=500, description="Max connections to return")


class EntityConnectionsResponse(BaseModel):
    """Response with entity connections from Neo4j"""
    entity_name: str
    nodes: List[EntityConnectionNode]
    edges: List[EntityConnectionEdge]
    total_nodes: int
    total_edges: int
    graph_available: bool = Field(description="Whether knowledge graph service is available")
    execution_time_ms: float


class EntityPathNode(BaseModel):
    """Node in an entity path"""
    name: str = Field(description="Entity name")
    type: Optional[str] = Field(default=None, description="Entity type")


class EntityPathRelationship(BaseModel):
    """Relationship in an entity path"""
    type: str = Field(description="Relationship type")
    confidence: float = Field(description="Confidence score")


class EntityPath(BaseModel):
    """A path between two entities"""
    length: int = Field(description="Path length (number of hops)")
    nodes: List[str] = Field(description="Node names in path order")
    relationships: List[EntityPathRelationship] = Field(description="Relationships in path")


class EntityPathsRequest(BaseModel):
    """Request for paths between entities"""
    entity1: str = Field(description="First entity name")
    entity2: str = Field(description="Second entity name")


class EntityPathsResponse(BaseModel):
    """Response with paths between entities from Neo4j"""
    entity1: str
    entity2: str
    paths: List[EntityPath]
    total_paths: int
    shortest_path_length: Optional[int] = None
    graph_available: bool = Field(description="Whether knowledge graph service is available")
    execution_time_ms: float

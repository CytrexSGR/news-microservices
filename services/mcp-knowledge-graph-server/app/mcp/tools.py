"""MCP Tool Registry for Knowledge Graph Server.

Phase 1: 17 Tools
- Core Entity Operations: 3 tools
- Analytics: 4 tools
- Article Integration: 2 tools
- Market Data: 4 tools
- Quality Monitoring: 2 tools
- Statistics: 2 tools

Total: 17 Tools
"""

import logging
from typing import Dict, Callable, Any
from functools import wraps

from ..clients import KnowledgeGraphClient
from ..models import MCPToolMetadata, MCPToolParameter, MCPToolResult

logger = logging.getLogger(__name__)

# Global tool registry
TOOL_REGISTRY: Dict[str, MCPToolMetadata] = {}
TOOL_FUNCTIONS: Dict[str, Callable] = {}  # Separate dict for function references


def register_tool(
    name: str,
    description: str,
    parameters: list,
    service: str,
    category: str,
    latency: str = "50-200ms",
):
    """Decorator to register an MCP tool."""

    def decorator(func: Callable) -> Callable:
        metadata = MCPToolMetadata(
            name=name,
            description=description,
            parameters=parameters,
            service=service,
            category=category,
            latency=latency,
        )
        TOOL_REGISTRY[name] = metadata
        TOOL_FUNCTIONS[name] = func  # Store function reference separately

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ==================== Phase 1: Core Entity Operations (3 Tools) ====================


@register_tool(
    name="get_entity_connections",
    description="Get all connections for an entity in the knowledge graph. Returns connected entities with relationship types and weights.",
    parameters=[
        MCPToolParameter(
            name="entity_name",
            type="string",
            description="Name of the entity to query",
            required=True,
        ),
        MCPToolParameter(
            name="relationship_type",
            type="string",
            description="Filter by relationship type (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum number of connections to return (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="entity",
    latency="50-200ms",
)
async def get_entity_connections(
    client: KnowledgeGraphClient,
    entity_name: str,
    relationship_type: str = None,
    limit: int = 20,
) -> MCPToolResult:
    """Get entity connections with pagination info."""
    try:
        result = await client.get_entity_connections(
            entity_name=entity_name,
            relationship_type=relationship_type,
            limit=limit,
        )

        # Handle both list and dict responses
        items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("connections", [])))

        return MCPToolResult(
            success=True,
            data={
                "total_found": len(items),  # Minimum known total
                "showing": len(items),
                "has_more": len(items) >= limit,
                "limit": limit,
                "entity_name": entity_name,
                "relationship_type": relationship_type,
                "items": items,
            },
            metadata={
                "tool": "get_entity_connections",
                "service": "knowledge-graph-service",
                "entity_name": entity_name,
            },
        )
    except Exception as e:
        logger.error(f"Get entity connections failed for {entity_name}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_entity_connections", "entity_name": entity_name},
        )


@register_tool(
    name="find_entity_path",
    description="Find paths between two entities in the knowledge graph. Discovers relationship chains and intermediary nodes.",
    parameters=[
        MCPToolParameter(
            name="entity1",
            type="string",
            description="Starting entity",
            required=True,
        ),
        MCPToolParameter(
            name="entity2",
            type="string",
            description="Target entity",
            required=True,
        ),
        MCPToolParameter(
            name="max_depth",
            type="number",
            description="Maximum path depth (default: 3)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="entity",
    latency="100-500ms",
)
async def find_entity_path(
    client: KnowledgeGraphClient,
    entity1: str,
    entity2: str,
    max_depth: int = 3,
) -> MCPToolResult:
    """Find path between entities."""
    try:
        result = await client.find_entity_path(
            entity1=entity1,
            entity2=entity2,
            max_depth=max_depth,
        )
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "find_entity_path",
                "service": "knowledge-graph-service",
                "entity1": entity1,
                "entity2": entity2,
            },
        )
    except Exception as e:
        logger.error(f"Find path failed from {entity1} to {entity2}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "find_entity_path", "entity1": entity1, "entity2": entity2},
        )


@register_tool(
    name="search_entities",
    description="Search entities by name or properties. Returns matching entities with relevance scores.",
    parameters=[
        MCPToolParameter(
            name="query",
            type="string",
            description="Search query string",
            required=True,
        ),
        MCPToolParameter(
            name="entity_type",
            type="string",
            description="Filter by entity type (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum results (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="entity",
    latency="50-200ms",
)
async def search_entities(
    client: KnowledgeGraphClient,
    query: str,
    entity_type: str = None,
    limit: int = 20,
) -> MCPToolResult:
    """Search entities."""
    try:
        result = await client.search_entities(
            query=query,
            entity_type=entity_type,
            limit=limit,
        )
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "search_entities",
                "service": "knowledge-graph-service",
                "query": query,
            },
        )
    except Exception as e:
        logger.error(f"Search entities failed for query '{query}': {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "search_entities", "query": query},
        )


# ==================== Phase 1: Analytics (4 Tools) ====================


@register_tool(
    name="get_top_entities",
    description="Get top entities ranked by connections, mentions, or importance. Critical for identifying key actors and trends.",
    parameters=[
        MCPToolParameter(
            name="limit",
            type="number",
            description="Number of top entities (default: 10)",
            required=False,
        ),
        MCPToolParameter(
            name="metric",
            type="string",
            description="Ranking metric: connections, mentions, importance (default: connections)",
            required=False,
            enum=["connections", "mentions", "importance"],
        ),
    ],
    service="knowledge-graph-service",
    category="analytics",
    latency="100-300ms",
)
async def get_top_entities(
    client: KnowledgeGraphClient,
    limit: int = 10,
    metric: str = "connections",
) -> MCPToolResult:
    """Get top entities."""
    try:
        result = await client.get_top_entities(limit=limit, metric=metric)
        # Wrap list result in dict for MCPToolResult compatibility
        entities_list = result if isinstance(result, list) else []
        return MCPToolResult(
            success=True,
            data={"entities": entities_list, "count": len(entities_list)},
            metadata={
                "tool": "get_top_entities",
                "service": "knowledge-graph-service",
                "limit": limit,
                "metric": metric,
            },
        )
    except Exception as e:
        logger.error(f"Get top entities failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_top_entities"},
        )


@register_tool(
    name="get_relationship_stats",
    description="Get statistics for relationship types in the graph. Shows distribution of relationship types and their counts.",
    parameters=[],
    service="knowledge-graph-service",
    category="analytics",
    latency="100-300ms",
)
async def get_relationship_stats(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get relationship statistics."""
    try:
        result = await client.get_relationship_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_relationship_stats", "service": "knowledge-graph-service"},
        )
    except Exception as e:
        logger.error(f"Get relationship stats failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_relationship_stats"},
        )


@register_tool(
    name="get_growth_history",
    description="Get graph growth history over time. Shows entity and relationship growth trends.",
    parameters=[
        MCPToolParameter(
            name="period",
            type="string",
            description="Time period: 1d, 7d, 30d, 90d (default: 7d)",
            required=False,
            enum=["1d", "7d", "30d", "90d"],
        ),
    ],
    service="knowledge-graph-service",
    category="analytics",
    latency="200-500ms",
)
async def get_growth_history(
    client: KnowledgeGraphClient,
    period: str = "7d",
) -> MCPToolResult:
    """Get growth history."""
    try:
        result = await client.get_growth_history(period=period)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_growth_history",
                "service": "knowledge-graph-service",
                "period": period,
            },
        )
    except Exception as e:
        logger.error(f"Get growth history failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_growth_history"},
        )


@register_tool(
    name="get_cross_article_coverage",
    description="Get entity coverage across articles. Shows which entities appear in multiple articles and their frequency.",
    parameters=[],
    service="knowledge-graph-service",
    category="analytics",
    latency="200-500ms",
)
async def get_cross_article_coverage(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get cross-article coverage."""
    try:
        result = await client.get_cross_article_coverage()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_cross_article_coverage", "service": "knowledge-graph-service"},
        )
    except Exception as e:
        logger.error(f"Get cross-article coverage failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_cross_article_coverage"},
        )


# ==================== Phase 1: Article Integration (2 Tools) ====================


@register_tool(
    name="get_article_entities",
    description="Get all entities extracted from a specific article. Returns entity names, types, and relationships.",
    parameters=[
        MCPToolParameter(
            name="article_id",
            type="number",
            description="Article identifier",
            required=True,
        ),
    ],
    service="knowledge-graph-service",
    category="article",
    latency="50-200ms",
)
async def get_article_entities(
    client: KnowledgeGraphClient,
    article_id: int,
) -> MCPToolResult:
    """Get article entities."""
    try:
        result = await client.get_article_entities(article_id=article_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_article_entities",
                "service": "knowledge-graph-service",
                "article_id": article_id,
            },
        )
    except Exception as e:
        logger.error(f"Get article entities failed for article {article_id}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_article_entities", "article_id": article_id},
        )


@register_tool(
    name="get_article_info",
    description="Get article node information from the knowledge graph. Returns article properties and connected entities.",
    parameters=[
        MCPToolParameter(
            name="article_id",
            type="number",
            description="Article identifier",
            required=True,
        ),
    ],
    service="knowledge-graph-service",
    category="article",
    latency="50-200ms",
)
async def get_article_info(
    client: KnowledgeGraphClient,
    article_id: int,
) -> MCPToolResult:
    """Get article info."""
    try:
        result = await client.get_article_info(article_id=article_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_article_info",
                "service": "knowledge-graph-service",
                "article_id": article_id,
            },
        )
    except Exception as e:
        logger.error(f"Get article info failed for article {article_id}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_article_info", "article_id": article_id},
        )


# ==================== Phase 1: Market Data (4 Tools) ====================


@register_tool(
    name="query_markets",
    description="Query market nodes with filters. Search and filter cryptocurrency/stock markets in the knowledge graph.",
    parameters=[
        MCPToolParameter(
            name="symbol",
            type="string",
            description="Filter by trading symbol (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="exchange",
            type="string",
            description="Filter by exchange (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum results (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="market",
    latency="100-300ms",
)
async def query_markets(
    client: KnowledgeGraphClient,
    symbol: str = None,
    exchange: str = None,
    limit: int = 20,
) -> MCPToolResult:
    """Query markets with pagination info."""
    try:
        result = await client.query_markets(
            symbol=symbol,
            exchange=exchange,
            limit=limit,
        )

        # Handle both list and dict responses
        items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("markets", [])))

        return MCPToolResult(
            success=True,
            data={
                "total_found": len(items),  # Minimum known total
                "showing": len(items),
                "has_more": len(items) >= limit,
                "limit": limit,
                "filters": {"symbol": symbol, "exchange": exchange},
                "items": items,
            },
            metadata={
                "tool": "query_markets",
                "service": "knowledge-graph-service",
            },
        )
    except Exception as e:
        logger.error(f"Query markets failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "query_markets"},
        )


@register_tool(
    name="get_market_details",
    description="Get market details with entity relationships. Returns full market node with connected entities and news articles.",
    parameters=[
        MCPToolParameter(
            name="symbol",
            type="string",
            description="Trading symbol (e.g., 'BTCUSD', 'ETHUSD')",
            required=True,
        ),
    ],
    service="knowledge-graph-service",
    category="market",
    latency="100-300ms",
)
async def get_market_details(
    client: KnowledgeGraphClient,
    symbol: str,
) -> MCPToolResult:
    """Get market details."""
    try:
        result = await client.get_market_details(symbol=symbol)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_market_details",
                "service": "knowledge-graph-service",
                "symbol": symbol,
            },
        )
    except Exception as e:
        logger.error(f"Get market details failed for {symbol}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_market_details", "symbol": symbol},
        )


@register_tool(
    name="get_market_history",
    description="Get historical market price data from Neo4j. Returns price history stored in the knowledge graph.",
    parameters=[
        MCPToolParameter(
            name="symbol",
            type="string",
            description="Trading symbol",
            required=True,
        ),
        MCPToolParameter(
            name="days",
            type="number",
            description="Number of days of history (default: 7)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="market",
    latency="200-500ms",
)
async def get_market_history(
    client: KnowledgeGraphClient,
    symbol: str,
    days: int = 7,
) -> MCPToolResult:
    """Get market history."""
    try:
        result = await client.get_market_history(symbol=symbol, days=days)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_market_history",
                "service": "knowledge-graph-service",
                "symbol": symbol,
                "days": days,
            },
        )
    except Exception as e:
        logger.error(f"Get market history failed for {symbol}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_market_history", "symbol": symbol},
        )


@register_tool(
    name="get_market_stats",
    description="Get market statistics overview. Returns market node counts, connections, and summary statistics.",
    parameters=[],
    service="knowledge-graph-service",
    category="market",
    latency="100-300ms",
)
async def get_market_stats(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get market stats."""
    try:
        result = await client.get_market_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_market_stats", "service": "knowledge-graph-service"},
        )
    except Exception as e:
        logger.error(f"Get market stats failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_market_stats"},
        )


# ==================== Phase 1: Quality Monitoring (2 Tools) ====================


@register_tool(
    name="get_quality_integrity",
    description="Get graph integrity check results. Identifies orphaned nodes, broken relationships, and data quality issues.",
    parameters=[],
    service="knowledge-graph-service",
    category="quality",
    latency="200-500ms",
)
async def get_quality_integrity(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get integrity check."""
    try:
        result = await client.get_quality_integrity()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_quality_integrity", "service": "knowledge-graph-service"},
        )
    except Exception as e:
        logger.error(f"Get integrity check failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_quality_integrity"},
        )


@register_tool(
    name="get_quality_disambiguation",
    description="Get entity disambiguation quality metrics. Shows ambiguous entities and disambiguation statistics.",
    parameters=[],
    service="knowledge-graph-service",
    category="quality",
    latency="200-500ms",
)
async def get_quality_disambiguation(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get disambiguation quality."""
    try:
        result = await client.get_quality_disambiguation()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_quality_disambiguation", "service": "knowledge-graph-service"},
        )
    except Exception as e:
        logger.error(f"Get disambiguation quality failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_quality_disambiguation"},
        )


# ==================== Phase 1: Statistics (2 Tools) ====================


@register_tool(
    name="get_graph_stats",
    description="Get basic graph statistics. Returns entity count, relationship count, and basic metrics.",
    parameters=[],
    service="knowledge-graph-service",
    category="stats",
    latency="50-200ms",
)
async def get_graph_stats(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get graph stats."""
    try:
        result = await client.get_graph_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_graph_stats", "service": "knowledge-graph-service"},
        )
    except Exception as e:
        logger.error(f"Get graph stats failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_graph_stats"},
        )


@register_tool(
    name="get_detailed_stats",
    description="Get detailed graph statistics. Returns comprehensive statistics including entity types, relationship distributions, and advanced metrics.",
    parameters=[],
    service="knowledge-graph-service",
    category="stats",
    latency="200-500ms",
)
async def get_detailed_stats(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get detailed stats."""
    try:
        result = await client.get_detailed_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_detailed_stats", "service": "knowledge-graph-service"},
        )
    except Exception as e:
        logger.error(f"Get detailed stats failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_detailed_stats"},
        )


# ==================== Narrative Analysis Tools (7 Tools) ====================


@register_tool(
    name="get_narrative_frames",
    description="Get narrative frames associated with an entity. Returns how entities are portrayed in media coverage (conflict, responsibility, morality, etc.).",
    parameters=[
        MCPToolParameter(
            name="entity_name",
            type="string",
            description="Name of the entity to query",
            required=True,
        ),
        MCPToolParameter(
            name="frame_type",
            type="string",
            description="Filter by frame type (conflict, responsibility, economic_consequences, morality, human_interest, security)",
            required=False,
        ),
        MCPToolParameter(
            name="min_confidence",
            type="number",
            description="Minimum confidence score 0.0-1.0 (default: 0.5)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum number of frames to return (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="narrative",
    latency="100-300ms",
)
async def get_narrative_frames(
    client: KnowledgeGraphClient,
    entity_name: str,
    frame_type: str = None,
    min_confidence: float = 0.5,
    limit: int = 20,
) -> MCPToolResult:
    """Get narrative frames for an entity with pagination info."""
    try:
        result = await client.get_narrative_frames(
            entity_name=entity_name,
            frame_type=frame_type,
            min_confidence=min_confidence,
            limit=limit,
        )
        # Wrap list result in dict for MCPToolResult compatibility
        frames_list = result if isinstance(result, list) else []
        return MCPToolResult(
            success=True,
            data={
                "total_found": len(frames_list),  # Minimum known total
                "showing": len(frames_list),
                "has_more": len(frames_list) >= limit,
                "limit": limit,
                "entity_name": entity_name,
                "filters": {"frame_type": frame_type, "min_confidence": min_confidence},
                "items": frames_list,
            },
            metadata={
                "tool": "get_narrative_frames",
                "service": "knowledge-graph-service",
                "entity_name": entity_name,
                "frame_count": len(frames_list),
            },
        )
    except Exception as e:
        logger.error(f"Get narrative frames failed for {entity_name}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_narrative_frames", "entity_name": entity_name},
        )


@register_tool(
    name="get_frame_distribution",
    description="Get distribution of narrative frame types across all content. Shows how frequently each frame type is used in media coverage.",
    parameters=[
        MCPToolParameter(
            name="min_count",
            type="number",
            description="Minimum frame count to include (default: 10)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum frame types to return (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="narrative",
    latency="100-300ms",
)
async def get_frame_distribution(
    client: KnowledgeGraphClient,
    min_count: int = 10,
    limit: int = 20,
) -> MCPToolResult:
    """Get frame distribution."""
    try:
        result = await client.get_frame_distribution(
            min_count=min_count,
            limit=limit,
        )
        # Wrap list result in dict for MCPToolResult compatibility
        distribution_list = result if isinstance(result, list) else []
        return MCPToolResult(
            success=True,
            data={"distribution": distribution_list, "count": len(distribution_list)},
            metadata={
                "tool": "get_frame_distribution",
                "service": "knowledge-graph-service",
                "frame_types_count": len(distribution_list),
            },
        )
    except Exception as e:
        logger.error(f"Get frame distribution failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_frame_distribution"},
        )


@register_tool(
    name="get_entity_framing_analysis",
    description="Get comprehensive framing analysis for an entity. Shows how an entity is portrayed across narratives with frame type breakdown and statistics.",
    parameters=[
        MCPToolParameter(
            name="entity_name",
            type="string",
            description="Name of the entity to analyze",
            required=True,
        ),
        MCPToolParameter(
            name="min_confidence",
            type="number",
            description="Minimum confidence threshold (default: 0.5)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum frames to analyze (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="narrative",
    latency="100-300ms",
)
async def get_entity_framing_analysis(
    client: KnowledgeGraphClient,
    entity_name: str,
    min_confidence: float = 0.5,
    limit: int = 20,
) -> MCPToolResult:
    """Get entity framing analysis with pagination info."""
    try:
        result = await client.get_entity_framing_analysis(
            entity_name=entity_name,
            min_confidence=min_confidence,
            limit=limit,
        )

        # Handle both list and dict responses
        items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("frames", [])))

        return MCPToolResult(
            success=True,
            data={
                "total_found": len(items),  # Minimum known total
                "showing": len(items),
                "has_more": len(items) >= limit,
                "limit": limit,
                "entity_name": entity_name,
                "filters": {"min_confidence": min_confidence},
                "items": items,
            },
            metadata={
                "tool": "get_entity_framing_analysis",
                "service": "knowledge-graph-service",
                "entity_name": entity_name,
            },
        )
    except Exception as e:
        logger.error(f"Get entity framing analysis failed for {entity_name}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_entity_framing_analysis", "entity_name": entity_name},
        )


@register_tool(
    name="get_narrative_cooccurrence",
    description="Find entities that appear together in narratives. Discovers entity pairs that are co-framed in articles, useful for finding related actors in news coverage.",
    parameters=[
        MCPToolParameter(
            name="entity_name",
            type="string",
            description="Only find pairs including this entity (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="frame_type",
            type="string",
            description="Only consider this frame type (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="min_shared",
            type="number",
            description="Minimum number of shared frames (default: 3)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum pairs to return (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="narrative",
    latency="200-500ms",
)
async def get_narrative_cooccurrence(
    client: KnowledgeGraphClient,
    entity_name: str = None,
    frame_type: str = None,
    min_shared: int = 3,
    limit: int = 20,
) -> MCPToolResult:
    """Get narrative cooccurrence with pagination info."""
    try:
        result = await client.get_narrative_cooccurrence(
            entity_name=entity_name,
            frame_type=frame_type,
            min_shared=min_shared,
            limit=limit,
        )
        # Wrap list result in dict for MCPToolResult compatibility
        pairs_list = result if isinstance(result, list) else []
        return MCPToolResult(
            success=True,
            data={
                "total_found": len(pairs_list),  # Minimum known total
                "showing": len(pairs_list),
                "has_more": len(pairs_list) >= limit,
                "limit": limit,
                "filters": {"entity_name": entity_name, "frame_type": frame_type, "min_shared": min_shared},
                "items": pairs_list,
            },
            metadata={
                "tool": "get_narrative_cooccurrence",
                "service": "knowledge-graph-service",
                "pairs_found": len(pairs_list),
            },
        )
    except Exception as e:
        logger.error(f"Get narrative cooccurrence failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_narrative_cooccurrence"},
        )


@register_tool(
    name="get_high_tension_narratives",
    description="Find narratives with high emotional tension. Returns articles with high narrative tension scores, useful for identifying emotionally charged or controversial content.",
    parameters=[
        MCPToolParameter(
            name="min_tension",
            type="number",
            description="Minimum tension score 0.0-1.0 (default: 0.7)",
            required=False,
        ),
        MCPToolParameter(
            name="frame_type",
            type="string",
            description="Filter by frame type (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum narratives to return (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="narrative",
    latency="100-300ms",
)
async def get_high_tension_narratives(
    client: KnowledgeGraphClient,
    min_tension: float = 0.7,
    frame_type: str = None,
    limit: int = 20,
) -> MCPToolResult:
    """Get high tension narratives with pagination info."""
    try:
        result = await client.get_high_tension_narratives(
            min_tension=min_tension,
            frame_type=frame_type,
            limit=limit,
        )
        # Wrap list result in dict for MCPToolResult compatibility
        narratives_list = result if isinstance(result, list) else []
        return MCPToolResult(
            success=True,
            data={
                "total_found": len(narratives_list),  # Minimum known total
                "showing": len(narratives_list),
                "has_more": len(narratives_list) >= limit,
                "limit": limit,
                "filters": {"min_tension": min_tension, "frame_type": frame_type},
                "items": narratives_list,
            },
            metadata={
                "tool": "get_high_tension_narratives",
                "service": "knowledge-graph-service",
                "narratives_found": len(narratives_list),
            },
        )
    except Exception as e:
        logger.error(f"Get high tension narratives failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_high_tension_narratives"},
        )


@register_tool(
    name="get_narrative_stats",
    description="Get overall narrative analysis statistics. Returns total frames, entity counts, frame type breakdown, and tension statistics.",
    parameters=[],
    service="knowledge-graph-service",
    category="narrative",
    latency="100-300ms",
)
async def get_narrative_stats(client: KnowledgeGraphClient) -> MCPToolResult:
    """Get narrative stats."""
    try:
        result = await client.get_narrative_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_narrative_stats",
                "service": "knowledge-graph-service",
            },
        )
    except Exception as e:
        logger.error(f"Get narrative stats failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_narrative_stats"},
        )


@register_tool(
    name="get_top_narrative_entities",
    description="Get entities with the most narrative frame mentions. Returns entities ranked by how often they appear in narrative frames, useful for identifying major actors in news coverage.",
    parameters=[
        MCPToolParameter(
            name="frame_type",
            type="string",
            description="Filter by frame type (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="number",
            description="Maximum entities to return (default: 20)",
            required=False,
        ),
    ],
    service="knowledge-graph-service",
    category="narrative",
    latency="100-300ms",
)
async def get_top_narrative_entities(
    client: KnowledgeGraphClient,
    frame_type: str = None,
    limit: int = 20,
) -> MCPToolResult:
    """Get top narrative entities."""
    try:
        result = await client.get_top_narrative_entities(
            frame_type=frame_type,
            limit=limit,
        )
        # Wrap list result in dict for MCPToolResult compatibility
        entities_list = result if isinstance(result, list) else []
        return MCPToolResult(
            success=True,
            data={"entities": entities_list, "count": len(entities_list)},
            metadata={
                "tool": "get_top_narrative_entities",
                "service": "knowledge-graph-service",
                "entities_found": len(entities_list),
            },
        )
    except Exception as e:
        logger.error(f"Get top narrative entities failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_top_narrative_entities"},
        )


logger.info(f"Registered {len(TOOL_REGISTRY)} MCP tools for Knowledge Graph Server")

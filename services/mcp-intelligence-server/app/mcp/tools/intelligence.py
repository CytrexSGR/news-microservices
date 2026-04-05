"""Intelligence Service MCP Tools."""

from typing import List, Optional

from ...models import MCPToolResult
from ...clients import IntelligenceClient
from .registry import register_tool


@register_tool(
    name="get_event_clusters",
    description="Get event clusters from intelligence analysis. Clusters related articles into events using ML clustering. Returns clusters with articles, entities, and timelines.",
    parameters=[
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum clusters to return (default: 50)",
            "required": False,
        },
        {
            "name": "min_articles",
            "type": "integer",
            "description": "Minimum articles per cluster (default: 3)",
            "required": False,
        },
    ],
    service="intelligence-service",
    category="intelligence",
    cost="$0",
    latency="~200ms",
)
async def get_event_clusters(
    limit: int = 50, min_articles: int = 3, client: IntelligenceClient = None
) -> MCPToolResult:
    """Get event clusters."""
    try:
        result = await client.get_event_clusters(limit, min_articles)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "limit": limit,
                "min_articles": min_articles,
                "service": "intelligence-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_cluster_details",
    description="Get detailed information about specific event cluster. Returns cluster details with articles, entities, timeline, and relationships.",
    parameters=[
        {
            "name": "cluster_id",
            "type": "string",
            "description": "Cluster ID",
            "required": True,
        }
    ],
    service="intelligence-service",
    category="intelligence",
    cost="$0",
    latency="~150ms",
)
async def get_cluster_details(
    cluster_id: str, client: IntelligenceClient = None
) -> MCPToolResult:
    """Get cluster details."""
    try:
        result = await client.get_cluster_details(cluster_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"cluster_id": cluster_id, "service": "intelligence-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_latest_events",
    description="Get latest intelligence events with timestamps and summaries.",
    parameters=[
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum events to return (default: 20)",
            "required": False,
        }
    ],
    service="intelligence-service",
    category="intelligence",
    cost="$0",
    latency="~100ms",
)
async def get_latest_events(
    limit: int = 20, client: IntelligenceClient = None
) -> MCPToolResult:
    """Get latest events."""
    try:
        result = await client.get_latest_events(limit)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"limit": limit, "service": "intelligence-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_intelligence_overview",
    description="Get intelligence overview dashboard with statistics, top clusters, and trending entities.",
    parameters=[],
    service="intelligence-service",
    category="intelligence",
    cost="$0",
    latency="~250ms",
)
async def get_intelligence_overview(client: IntelligenceClient = None) -> MCPToolResult:
    """Get intelligence overview."""
    try:
        result = await client.get_intelligence_overview()
        return MCPToolResult(
            success=True, data=result, metadata={"service": "intelligence-service"}
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_cluster_events",
    description="Get paginated events for specific cluster. Returns events with title, source, entities, keywords, sentiment, bias. Essential for drilling down into cluster details.",
    parameters=[
        {
            "name": "cluster_id",
            "type": "string",
            "description": "Cluster identifier (UUID)",
            "required": True,
        },
        {
            "name": "page",
            "type": "integer",
            "description": "Page number (default: 1)",
            "required": False,
        },
        {
            "name": "per_page",
            "type": "integer",
            "description": "Items per page, max 100 (default: 20)",
            "required": False,
        },
    ],
    service="intelligence-service",
    category="intelligence",
    cost="$0",
    latency="~150ms",
)
async def get_cluster_events(
    cluster_id: str, page: int = 1, per_page: int = 20, client: IntelligenceClient = None
) -> MCPToolResult:
    """Get cluster events."""
    try:
        result = await client.get_cluster_events(cluster_id, page, per_page)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "cluster_id": cluster_id,
                "page": page,
                "per_page": per_page,
                "service": "intelligence-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_subcategories",
    description="Get top 2 sub-topics per category (geo, finance, tech). Dynamic sub-category discovery from current news data. Returns top keywords/topics with risk scores and event counts.",
    parameters=[],
    service="intelligence-service",
    category="intelligence",
    cost="$0",
    latency="~200ms",
)
async def get_subcategories(client: IntelligenceClient = None) -> MCPToolResult:
    """Get subcategories."""
    try:
        result = await client.get_subcategories()
        return MCPToolResult(
            success=True, data=result, metadata={"service": "intelligence-service"}
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_risk_history",
    description="Get historical risk scores for trend visualization. Returns daily risk history (global, geo, finance) with dates, risk scores, and event counts.",
    parameters=[
        {
            "name": "days",
            "type": "integer",
            "description": "Days to look back (1-30, default: 7)",
            "required": False,
        }
    ],
    service="intelligence-service",
    category="intelligence",
    cost="$0",
    latency="~150ms",
)
async def get_risk_history(
    days: int = 7, client: IntelligenceClient = None
) -> MCPToolResult:
    """Get risk history."""
    try:
        result = await client.get_risk_history(days)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"days": days, "service": "intelligence-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="detect_events",
    description="Extract entities (persons, organizations, locations) and keywords from text content using spaCy NLP. Useful for analyzing news articles or any text to identify key actors and topics.",
    parameters=[
        {
            "name": "text",
            "type": "string",
            "description": "Text content to analyze (10-50000 characters)",
            "required": True,
        },
        {
            "name": "include_keywords",
            "type": "boolean",
            "description": "Include keyword extraction (default: True)",
            "required": False,
        },
        {
            "name": "max_keywords",
            "type": "integer",
            "description": "Maximum keywords to extract (1-50, default: 10)",
            "required": False,
        },
    ],
    service="intelligence-service",
    category="intelligence",
    cost="~$0.001 per analysis",
    latency="~50ms",
)
async def detect_events(
    text: str,
    include_keywords: bool = True,
    max_keywords: int = 10,
    client: IntelligenceClient = None,
) -> MCPToolResult:
    """Detect entities and keywords from text."""
    try:
        result = await client.detect_events(
            text=text,
            include_keywords=include_keywords,
            max_keywords=max_keywords,
        )
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "text_length": len(text),
                "include_keywords": include_keywords,
                "service": "intelligence-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="calculate_risk",
    description="Calculate risk score for a cluster, entities, or text content. Returns risk score (0-100), risk level (low/medium/high/critical), delta from previous, and contributing factors.",
    parameters=[
        {
            "name": "cluster_id",
            "type": "string",
            "description": "Cluster UUID to calculate risk for (mode 1)",
            "required": False,
        },
        {
            "name": "entities",
            "type": "array",
            "description": "Entity names to analyze (mode 2). Example: ['Goldman Sachs', 'Federal Reserve']",
            "required": False,
        },
        {
            "name": "text",
            "type": "string",
            "description": "Text content to analyze for risk (mode 3, max 50000 chars)",
            "required": False,
        },
        {
            "name": "include_factors",
            "type": "boolean",
            "description": "Include factor breakdown in response (default: True)",
            "required": False,
        },
    ],
    service="intelligence-service",
    category="intelligence",
    cost="~$0.002 per calculation",
    latency="~100ms",
)
async def calculate_risk(
    cluster_id: str = None,
    entities: list = None,
    text: str = None,
    include_factors: bool = True,
    client: IntelligenceClient = None,
) -> MCPToolResult:
    """Calculate risk score for cluster, entities, or text."""
    try:
        result = await client.calculate_risk(
            cluster_id=cluster_id,
            entities=entities,
            text=text,
            include_factors=include_factors,
        )
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "cluster_id": cluster_id,
                "entities_count": len(entities) if entities else 0,
                "text_length": len(text) if text else 0,
                "service": "intelligence-service",
            },
        )
    except ValueError as e:
        return MCPToolResult(success=False, error=str(e))
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))

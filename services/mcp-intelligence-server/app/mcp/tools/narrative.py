"""Narrative Service MCP Tools."""

from ...models import MCPToolResult
from ...clients import NarrativeClient
from .registry import register_tool


@register_tool(
    name="analyze_text_narrative",
    description="Analyze text for narrative frames and bias using InfiniMind multi-agent pipeline. Detects frames, bias scores, and propaganda signals.",
    parameters=[
        {
            "name": "text",
            "type": "string",
            "description": "Text to analyze",
            "required": True,
        }
    ],
    service="narrative-service",
    category="narrative",
    cost="~$0.002 per analysis",
    latency="~800ms",
)
async def analyze_text_narrative(
    text: str, client: NarrativeClient = None
) -> MCPToolResult:
    """Analyze text narrative."""
    try:
        result = await client.analyze_text(text)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"text_length": len(text), "service": "narrative-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_narrative_frames",
    description="Get narrative frames from article analysis with frequency and examples.",
    parameters=[
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum frames to return (default: 50)",
            "required": False,
        },
        {
            "name": "category",
            "type": "string",
            "description": "Optional category filter",
            "required": False,
        },
    ],
    service="narrative-service",
    category="narrative",
    cost="$0",
    latency="~150ms",
)
async def get_narrative_frames(
    limit: int = 50, category: str = None, client: NarrativeClient = None
) -> MCPToolResult:
    """Get narrative frames."""
    try:
        result = await client.get_narrative_frames(limit, category)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "limit": limit,
                "category": category,
                "service": "narrative-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_bias_analysis",
    description="Get bias analysis across articles with distribution, trends, and examples.",
    parameters=[
        {
            "name": "start_date",
            "type": "string",
            "description": "Start date (ISO format)",
            "required": False,
        },
        {
            "name": "end_date",
            "type": "string",
            "description": "End date (ISO format)",
            "required": False,
        },
    ],
    service="narrative-service",
    category="narrative",
    cost="$0",
    latency="~200ms",
)
async def get_bias_analysis(
    start_date: str = None, end_date: str = None, client: NarrativeClient = None
) -> MCPToolResult:
    """Get bias analysis."""
    try:
        result = await client.get_bias_analysis(start_date, end_date)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "start_date": start_date,
                "end_date": end_date,
                "service": "narrative-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_narrative_overview",
    description="Get narrative analysis overview dashboard with top frames, bias distribution, and trends.",
    parameters=[],
    service="narrative-service",
    category="narrative",
    cost="$0",
    latency="~250ms",
)
async def get_narrative_overview(client: NarrativeClient = None) -> MCPToolResult:
    """Get narrative overview."""
    try:
        result = await client.get_narrative_overview()
        return MCPToolResult(
            success=True, data=result, metadata={"service": "narrative-service"}
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="list_narrative_clusters",
    description="List narrative clusters showing related frames. Clusters group similar narrative frames by type and entity overlap. Returns clusters with frame counts, dominant frame type, and keywords.",
    parameters=[
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum clusters to return (default: 50)",
            "required": False,
        },
        {
            "name": "active_only",
            "type": "boolean",
            "description": "Only return active clusters (default: True)",
            "required": False,
        },
        {
            "name": "min_frame_count",
            "type": "integer",
            "description": "Minimum frame count (default: 0)",
            "required": False,
        },
    ],
    service="narrative-service",
    category="narrative",
    cost="$0",
    latency="~150ms",
)
async def list_narrative_clusters(
    limit: int = 50,
    active_only: bool = True,
    min_frame_count: int = 0,
    client: NarrativeClient = None,
) -> MCPToolResult:
    """List narrative clusters."""
    try:
        result = await client.get_narrative_clusters(limit)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "limit": limit,
                "active_only": active_only,
                "min_frame_count": min_frame_count,
                "service": "narrative-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))

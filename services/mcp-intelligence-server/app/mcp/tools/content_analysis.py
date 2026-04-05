"""Content Analysis MCP Tools."""

from ...models import MCPToolResult
from ...clients import ContentAnalysisClient
from .registry import register_tool


@register_tool(
    name="analyze_article",
    description="Analyze article using content-analysis-v3 AI pipeline. Extracts entities, sentiment, topics, and narrative frames using Gemini 2.0 Flash.",
    parameters=[
        {
            "name": "article_id",
            "type": "string",
            "description": "UUID of article to analyze",
            "required": True,
        }
    ],
    service="content-analysis-v3",
    category="analysis",
    cost="$0.00028 per article",
    latency="~200ms",
)
async def analyze_article(article_id: str, client: ContentAnalysisClient) -> MCPToolResult:
    """Analyze article using content-analysis-v3."""
    try:
        result = await client.analyze_article(article_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"article_id": article_id, "service": "content-analysis-v3"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="extract_entities",
    description="Extract named entities from analyzed article. Returns 14 semantic entity types (PERSON, ORG, GPE, LOC, DATE, TIME, MONEY, PERCENT, PRODUCT, EVENT, FACILITY, LANGUAGE, LAW, NORP).",
    parameters=[
        {
            "name": "article_id",
            "type": "string",
            "description": "UUID of article",
            "required": True,
        }
    ],
    service="content-analysis-v3",
    category="analysis",
    cost="$0",
    latency="~50ms",
)
async def extract_entities(article_id: str, client: ContentAnalysisClient) -> MCPToolResult:
    """Extract entities from analyzed article."""
    try:
        result = await client.extract_entities(article_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"article_id": article_id, "service": "content-analysis-v3"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_analysis_status",
    description="Get analysis status for article (pending, processing, completed, failed).",
    parameters=[
        {
            "name": "article_id",
            "type": "string",
            "description": "UUID of article",
            "required": True,
        }
    ],
    service="content-analysis-v3",
    category="analysis",
    cost="$0",
    latency="~20ms",
)
async def get_analysis_status(article_id: str, client: ContentAnalysisClient) -> MCPToolResult:
    """Get analysis status for article."""
    try:
        result = await client.get_analysis_status(article_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"article_id": article_id, "service": "content-analysis-v3"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))

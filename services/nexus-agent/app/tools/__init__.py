"""NEXUS Agent Tools."""

from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry, get_tool_registry

# Import all tool classes
from app.tools.perplexity import PerplexitySearchTool
from app.tools.database import (
    ArticleSearchTool,
    FeedListTool,
    ArticleAnalysisTool,
    DatabaseStatsTool,
)
from app.tools.services import (
    SearchServiceTool,
    AnalyticsServiceTool,
    KnowledgeGraphTool,
    FMPServiceTool,
    ServiceHealthTool,
)
from app.tools.report import ReportTool


def register_all_tools() -> ToolRegistry:
    """Register all available tools and return the registry."""
    registry = get_tool_registry()

    # Perplexity search
    registry.register(PerplexitySearchTool())

    # Database tools
    registry.register(ArticleSearchTool())
    registry.register(FeedListTool())
    registry.register(ArticleAnalysisTool())
    registry.register(DatabaseStatsTool())

    # Service API tools
    registry.register(SearchServiceTool())
    registry.register(AnalyticsServiceTool())
    registry.register(KnowledgeGraphTool())
    registry.register(FMPServiceTool())
    registry.register(ServiceHealthTool())

    # Report generation
    registry.register(ReportTool())

    return registry


__all__ = [
    # Base classes
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "get_tool_registry",
    "register_all_tools",
    # Perplexity
    "PerplexitySearchTool",
    # Database tools
    "ArticleSearchTool",
    "FeedListTool",
    "ArticleAnalysisTool",
    "DatabaseStatsTool",
    # Service tools
    "SearchServiceTool",
    "AnalyticsServiceTool",
    "KnowledgeGraphTool",
    "FMPServiceTool",
    "ServiceHealthTool",
    # Report generation
    "ReportTool",
]

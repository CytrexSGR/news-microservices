"""MCP Tools Registry and Implementations for Search Server."""

import time
import logging
from typing import Dict, Any, Callable, Awaitable
from functools import wraps

from ..models import MCPTool, MCPToolParameter, MCPToolResult
from ..clients import SearchClient, FeedClient, ResearchClient

logger = logging.getLogger(__name__)

# Global tool registry
tool_registry: Dict[str, Dict[str, Any]] = {}


def register_tool(
    name: str,
    description: str,
    parameters: list,
    service: str,
    category: str,
    cost: str = None,
    latency: str = None,
):
    """
    Decorator to register MCP tool.

    Args:
        name: Tool name
        description: Tool description for LLM
        parameters: List of MCPToolParameter dicts
        service: Backend service providing tool
        category: Tool category
        cost: Estimated cost per call
        latency: Expected latency
    """

    def decorator(func: Callable[..., Awaitable[MCPToolResult]]):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> MCPToolResult:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                logger.info(
                    f"Tool {name} executed successfully",
                    extra={
                        "tool": name,
                        "execution_time_ms": execution_time,
                        "success": result.success,
                    },
                )
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Tool {name} execution failed: {e}",
                    extra={
                        "tool": name,
                        "execution_time_ms": execution_time,
                        "error": str(e),
                    },
                )
                return MCPToolResult(
                    success=False,
                    error=str(e),
                    metadata={"execution_time_ms": execution_time},
                )

        # Register tool metadata
        tool_registry[name] = {
            "definition": MCPTool(
                name=name,
                description=description,
                parameters=[MCPToolParameter(**p) for p in parameters],
                service=service,
                cost=cost,
                latency=latency,
                category=category,
            ),
            "handler": wrapper,
        }

        return wrapper

    return decorator


# ============================================================================
# Search Service Tools (search-service:8106)
# ============================================================================


@register_tool(
    name="search_articles",
    description="Basic article search with PostgreSQL full-text search. Supports filters for source, sentiment, date range. Returns paginated results with article metadata.",
    parameters=[
        {
            "name": "query",
            "type": "string",
            "description": "Search query (optional for browsing)",
            "required": False,
        },
        {
            "name": "page",
            "type": "integer",
            "description": "Page number (default: 1)",
            "required": False,
        },
        {
            "name": "page_size",
            "type": "integer",
            "description": "Results per page (default: 20, max: 100)",
            "required": False,
        },
        {
            "name": "source",
            "type": "string",
            "description": "Filter by source (comma-separated)",
            "required": False,
        },
        {
            "name": "sentiment",
            "type": "string",
            "description": "Filter by sentiment (positive, negative, neutral)",
            "required": False,
        },
        {
            "name": "date_from",
            "type": "string",
            "description": "Filter by date from (ISO format: YYYY-MM-DD)",
            "required": False,
        },
        {
            "name": "date_to",
            "type": "string",
            "description": "Filter by date to (ISO format: YYYY-MM-DD)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="50-200ms",
)
async def search_articles(
    query: str = None,
    page: int = 1,
    page_size: int = 20,
    source: str = None,
    sentiment: str = None,
    date_from: str = None,
    date_to: str = None,
) -> MCPToolResult:
    """Search articles with basic filters."""
    client = SearchClient()
    try:
        result = await client.search_articles(
            query=query,
            page=page,
            page_size=page_size,
            source=source,
            sentiment=sentiment,
            date_from=date_from,
            date_to=date_to,
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="advanced_search",
    description="Advanced article search with fuzzy matching, highlighting, faceted search. Supports AND/OR operators, phrase search, field search, exclusion. Returns results with facets and highlights.",
    parameters=[
        {
            "name": "query",
            "type": "string",
            "description": "Search query (supports operators: AND, OR, NOT, quotes for phrases)",
            "required": True,
        },
        {
            "name": "filters",
            "type": "object",
            "description": "Advanced filters (source, sentiment, date_range, category, etc.)",
            "required": False,
        },
        {
            "name": "fuzzy",
            "type": "boolean",
            "description": "Enable fuzzy matching for typo tolerance (default: false)",
            "required": False,
        },
        {
            "name": "highlight",
            "type": "boolean",
            "description": "Enable result highlighting (default: true)",
            "required": False,
        },
        {
            "name": "facets",
            "type": "array",
            "description": "Facets to return (e.g., ['source', 'sentiment', 'category'])",
            "required": False,
        },
        {
            "name": "page",
            "type": "integer",
            "description": "Page number (default: 1)",
            "required": False,
        },
        {
            "name": "page_size",
            "type": "integer",
            "description": "Results per page (default: 20)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="100-300ms",
)
async def advanced_search(
    query: str,
    filters: dict = None,
    fuzzy: bool = False,
    highlight: bool = True,
    facets: list = None,
    page: int = 1,
    page_size: int = 20,
) -> MCPToolResult:
    """Advanced search with complex query features."""
    client = SearchClient()
    try:
        result = await client.advanced_search(
            query=query,
            filters=filters,
            fuzzy=fuzzy,
            highlight=highlight,
            facets=facets,
            page=page,
            page_size=page_size,
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_search_suggestions",
    description="Get search query suggestions/autocomplete based on partial input. Returns list of suggested queries with metadata. Cached for 5 minutes.",
    parameters=[
        {
            "name": "query",
            "type": "string",
            "description": "Partial query string",
            "required": True,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum suggestions to return (default: 10)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="10-50ms (cached)",
)
async def get_search_suggestions(query: str, limit: int = 10) -> MCPToolResult:
    """Get search query suggestions/autocomplete."""
    client = SearchClient()
    try:
        result = await client.get_search_suggestions(query=query, limit=limit)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_search_facets",
    description="Get available facets for search filtering (sources, sentiments, categories, etc.). Helps discover filter options. Cached for 30 minutes.",
    parameters=[],
    service="search-service",
    category="search",
    latency="10-50ms (cached)",
)
async def get_search_facets() -> MCPToolResult:
    """Get available facets for search filtering."""
    client = SearchClient()
    try:
        result = await client.get_search_facets()
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


# ============================================================================
# Feed Service Tools (feed-service:8101)
# ============================================================================


@register_tool(
    name="list_feeds",
    description="List all RSS/Atom feeds with pagination. Returns feeds with metadata, health scores, last fetch time. Supports filtering by status and category. Cached for 30 minutes.",
    parameters=[
        {
            "name": "page",
            "type": "integer",
            "description": "Page number (default: 1)",
            "required": False,
        },
        {
            "name": "page_size",
            "type": "integer",
            "description": "Results per page (default: 50)",
            "required": False,
        },
        {
            "name": "status",
            "type": "string",
            "description": "Filter by feed status (active, paused, error)",
            "required": False,
        },
        {
            "name": "category",
            "type": "string",
            "description": "Filter by category",
            "required": False,
        },
    ],
    service="feed-service",
    category="feed",
    latency="20-100ms (cached)",
)
async def list_feeds(
    page: int = 1,
    page_size: int = 50,
    status: str = None,
    category: str = None,
) -> MCPToolResult:
    """List all RSS/Atom feeds."""
    client = FeedClient()
    try:
        result = await client.list_feeds(
            page=page, page_size=page_size, status=status, category=category
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_feed",
    description="Get specific feed details including configuration, health metrics, and statistics. Cached for 30 minutes.",
    parameters=[
        {
            "name": "feed_id",
            "type": "integer",
            "description": "Feed ID",
            "required": True,
        },
    ],
    service="feed-service",
    category="feed",
    latency="20-100ms (cached)",
)
async def get_feed(feed_id: int) -> MCPToolResult:
    """Get specific feed details."""
    client = FeedClient()
    try:
        result = await client.get_feed(feed_id=feed_id)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_feed_items",
    description="Get feed items/articles with pagination. Returns list with title, content, published date, metadata. Supports date range filtering. Cached for 5 minutes.",
    parameters=[
        {
            "name": "feed_id",
            "type": "integer",
            "description": "Feed ID",
            "required": True,
        },
        {
            "name": "page",
            "type": "integer",
            "description": "Page number (default: 1)",
            "required": False,
        },
        {
            "name": "page_size",
            "type": "integer",
            "description": "Results per page (default: 20)",
            "required": False,
        },
        {
            "name": "date_from",
            "type": "string",
            "description": "Filter by date from (ISO format: YYYY-MM-DD)",
            "required": False,
        },
        {
            "name": "date_to",
            "type": "string",
            "description": "Filter by date to (ISO format: YYYY-MM-DD)",
            "required": False,
        },
    ],
    service="feed-service",
    category="feed",
    latency="50-200ms (cached)",
)
async def get_feed_items(
    feed_id: int,
    page: int = 1,
    page_size: int = 20,
    date_from: str = None,
    date_to: str = None,
) -> MCPToolResult:
    """Get feed items/articles."""
    client = FeedClient()
    try:
        result = await client.get_feed_items(
            feed_id=feed_id,
            page=page,
            page_size=page_size,
            date_from=date_from,
            date_to=date_to,
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="assess_feed",
    description="Assess feed credibility with Perplexity AI. Evaluates source reliability, bias, fact-checking record. Returns credibility assessment with scores, reasoning, recommendations.",
    parameters=[
        {
            "name": "feed_id",
            "type": "integer",
            "description": "Feed ID to assess",
            "required": True,
        },
    ],
    service="feed-service",
    category="feed",
    cost="$0.005 (Perplexity API)",
    latency="2000-5000ms (AI analysis)",
)
async def assess_feed(feed_id: int) -> MCPToolResult:
    """Assess feed credibility with Perplexity AI."""
    client = FeedClient()
    try:
        result = await client.assess_feed(feed_id=feed_id)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


# ============================================================================
# Research Service Tools (research-service:8103)
# ============================================================================


@register_tool(
    name="create_research_task",
    description="Create Perplexity research task for comprehensive AI-powered research with citations. Supports various research types: general, fact_check, trend_analysis, feed_assessment. Returns task details with task_id.",
    parameters=[
        {
            "name": "query",
            "type": "string",
            "description": "Research query/question",
            "required": True,
        },
        {
            "name": "research_type",
            "type": "string",
            "description": "Type of research (general, fact_check, trend_analysis, feed_assessment). Default: general",
            "required": False,
        },
        {
            "name": "context",
            "type": "object",
            "description": "Additional context for research (e.g., feed_id, article_id)",
            "required": False,
        },
        {
            "name": "options",
            "type": "object",
            "description": "Research options (depth, sources, etc.)",
            "required": False,
        },
    ],
    service="research-service",
    category="research",
    cost="$0.005-0.02 (Perplexity API)",
    latency="2000-10000ms (AI analysis)",
)
async def create_research_task(
    query: str,
    research_type: str = "general",
    context: dict = None,
    options: dict = None,
) -> MCPToolResult:
    """Create Perplexity research task."""
    client = ResearchClient()
    try:
        result = await client.create_research_task(
            query=query,
            research_type=research_type,
            context=context,
            options=options,
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_research_task",
    description="Get research task details and results. Returns task results with answer, citations, confidence, metadata.",
    parameters=[
        {
            "name": "task_id",
            "type": "string",
            "description": "Task ID",
            "required": True,
        },
    ],
    service="research-service",
    category="research",
    latency="20-100ms",
)
async def get_research_task(task_id: str) -> MCPToolResult:
    """Get research task details and results."""
    client = ResearchClient()
    try:
        result = await client.get_research_task(task_id=task_id)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="list_research_tasks",
    description="List research tasks with filtering by status and research type. Returns list with summary information. Cached for 5 minutes.",
    parameters=[
        {
            "name": "status",
            "type": "string",
            "description": "Filter by status (pending, running, completed, failed)",
            "required": False,
        },
        {
            "name": "research_type",
            "type": "string",
            "description": "Filter by research type",
            "required": False,
        },
        {
            "name": "page",
            "type": "integer",
            "description": "Page number (default: 1)",
            "required": False,
        },
        {
            "name": "page_size",
            "type": "integer",
            "description": "Results per page (default: 20)",
            "required": False,
        },
    ],
    service="research-service",
    category="research",
    latency="20-100ms (cached)",
)
async def list_research_tasks(
    status: str = None,
    research_type: str = None,
    page: int = 1,
    page_size: int = 20,
) -> MCPToolResult:
    """List research tasks with filtering."""
    client = ResearchClient()
    try:
        result = await client.list_research_tasks(
            status=status,
            research_type=research_type,
            page=page,
            page_size=page_size,
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


# ============================================================================
# Phase 2 - Search Service Tools (Additional)
# ============================================================================


@register_tool(
    name="get_popular_searches",
    description="Get popular/trending search queries with frequency and trend data. Shows what topics are being searched most. Cached for 30 minutes.",
    parameters=[
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum results to return (default: 10)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="10-50ms (cached)",
)
async def get_popular_searches(limit: int = 10) -> MCPToolResult:
    """Get popular/trending search queries."""
    client = SearchClient()
    try:
        result = await client.get_popular_searches(limit=limit)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_related_searches",
    description="Get related search suggestions for a query. Helps discover related topics and refine searches. Cached for 30 minutes.",
    parameters=[
        {
            "name": "query",
            "type": "string",
            "description": "Original search query",
            "required": True,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum suggestions to return (default: 10)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="10-50ms (cached)",
)
async def get_related_searches(query: str, limit: int = 10) -> MCPToolResult:
    """Get related search suggestions."""
    client = SearchClient()
    try:
        result = await client.get_related_searches(query=query, limit=limit)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="list_saved_searches",
    description="List user's saved searches with filters and metadata. Returns saved search queries with creation date, last used, and execution count.",
    parameters=[
        {
            "name": "user_id",
            "type": "string",
            "description": "User ID to list saved searches for (optional)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="20-100ms",
)
async def list_saved_searches(user_id: str = None) -> MCPToolResult:
    """List user's saved searches."""
    client = SearchClient()
    try:
        result = await client.list_saved_searches(user_id=user_id)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="create_saved_search",
    description="Save a search query for later reuse. Stores query parameters and metadata for quick access.",
    parameters=[
        {
            "name": "name",
            "type": "string",
            "description": "Name for the saved search",
            "required": True,
        },
        {
            "name": "query",
            "type": "string",
            "description": "Search query to save",
            "required": True,
        },
        {
            "name": "filters",
            "type": "object",
            "description": "Search filters to save (optional)",
            "required": False,
        },
        {
            "name": "user_id",
            "type": "string",
            "description": "User ID (optional)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="20-100ms",
)
async def create_saved_search(
    name: str,
    query: str,
    filters: dict = None,
    user_id: str = None,
) -> MCPToolResult:
    """Save a search query."""
    client = SearchClient()
    try:
        result = await client.create_saved_search(
            name=name, query=query, filters=filters, user_id=user_id
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="delete_saved_search",
    description="Delete a saved search by ID. Permanently removes the saved search from user's collection.",
    parameters=[
        {
            "name": "search_id",
            "type": "string",
            "description": "Saved search ID to delete",
            "required": True,
        },
    ],
    service="search-service",
    category="search",
    latency="20-100ms",
)
async def delete_saved_search(search_id: str) -> MCPToolResult:
    """Delete a saved search."""
    client = SearchClient()
    try:
        await client.delete_saved_search(search_id=search_id)
        return MCPToolResult(success=True, data={"deleted": True, "search_id": search_id})
    finally:
        await client.close()


# ============================================================================
# Phase 2 - Feed Service Tools (Additional)
# ============================================================================


@register_tool(
    name="get_feed_health",
    description="Get feed health metrics including uptime, error rate, response time, and reliability score. Cached for 5 minutes.",
    parameters=[
        {
            "name": "feed_id",
            "type": "integer",
            "description": "Feed ID",
            "required": True,
        },
    ],
    service="feed-service",
    category="feed",
    latency="20-100ms (cached)",
)
async def get_feed_health(feed_id: int) -> MCPToolResult:
    """Get feed health metrics."""
    client = FeedClient()
    try:
        result = await client.get_feed_health(feed_id=feed_id)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="pre_assess_feed",
    description="Preview feed quality before adding using Perplexity AI. Checks credibility, content quality, update frequency. Returns assessment without adding feed to database.",
    parameters=[
        {
            "name": "feed_url",
            "type": "string",
            "description": "Feed URL to preview/assess",
            "required": True,
        },
    ],
    service="feed-service",
    category="feed",
    cost="$0.005 (Perplexity API)",
    latency="2000-5000ms (AI analysis)",
)
async def pre_assess_feed(feed_url: str) -> MCPToolResult:
    """Preview feed quality before adding."""
    client = FeedClient()
    try:
        result = await client.pre_assess_feed(feed_url=feed_url)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_assessment_history",
    description="Get historical credibility assessments for a feed with scores and trend analysis. Shows how feed quality has changed over time. Cached for 30 minutes.",
    parameters=[
        {
            "name": "feed_id",
            "type": "integer",
            "description": "Feed ID",
            "required": True,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum assessments to return (default: 10)",
            "required": False,
        },
    ],
    service="feed-service",
    category="feed",
    latency="20-100ms (cached)",
)
async def get_assessment_history(feed_id: int, limit: int = 10) -> MCPToolResult:
    """Get historical feed assessments."""
    client = FeedClient()
    try:
        result = await client.get_assessment_history(feed_id=feed_id, limit=limit)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


# ============================================================================
# Phase 2 - Research Service Tools (Additional)
# ============================================================================


@register_tool(
    name="get_research_history",
    description="Get historical research data with filters by user, feed, and date range. Shows research trends and patterns over time. Cached for 30 minutes.",
    parameters=[
        {
            "name": "user_id",
            "type": "string",
            "description": "Filter by user ID (optional)",
            "required": False,
        },
        {
            "name": "feed_id",
            "type": "integer",
            "description": "Filter by feed ID (optional)",
            "required": False,
        },
        {
            "name": "days",
            "type": "integer",
            "description": "Number of days to look back (default: 7)",
            "required": False,
        },
    ],
    service="research-service",
    category="research",
    latency="20-100ms (cached)",
)
async def get_research_history(
    user_id: str = None,
    feed_id: int = None,
    days: int = 7,
) -> MCPToolResult:
    """Get historical research data."""
    client = ResearchClient()
    try:
        result = await client.get_research_history(
            user_id=user_id, feed_id=feed_id, days=days
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="list_research_templates",
    description="List available research templates with descriptions and parameters. Templates provide pre-configured research patterns for common tasks. Cached for 1 hour.",
    parameters=[
        {
            "name": "category",
            "type": "string",
            "description": "Filter by template category (optional)",
            "required": False,
        },
    ],
    service="research-service",
    category="research",
    latency="10-50ms (cached)",
)
async def list_research_templates(category: str = None) -> MCPToolResult:
    """List available research templates."""
    client = ResearchClient()
    try:
        result = await client.list_research_templates(category=category)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="get_research_template",
    description="Get specific research template details with parameters, description, and examples. Shows how to use template for research tasks. Cached for 1 hour.",
    parameters=[
        {
            "name": "template_id",
            "type": "string",
            "description": "Template ID to retrieve",
            "required": True,
        },
    ],
    service="research-service",
    category="research",
    latency="10-50ms (cached)",
)
async def get_research_template(template_id: str) -> MCPToolResult:
    """Get research template details."""
    client = ResearchClient()
    try:
        result = await client.get_research_template(template_id=template_id)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


# ============================================================================
# Phase 3 - Feed Service Tools (Final)
# ============================================================================


@register_tool(
    name="create_feed",
    description="Add new RSS/Atom feed to the system. Validates feed URL, fetches initial items, and sets up monitoring. Returns created feed with ID and initial health status.",
    parameters=[
        {
            "name": "url",
            "type": "string",
            "description": "Feed URL (RSS/Atom)",
            "required": True,
        },
        {
            "name": "name",
            "type": "string",
            "description": "Feed name/title",
            "required": True,
        },
        {
            "name": "category",
            "type": "string",
            "description": "Feed category (optional)",
            "required": False,
        },
        {
            "name": "fetch_interval",
            "type": "integer",
            "description": "Fetch interval in seconds (default: 300 = 5 minutes)",
            "required": False,
        },
        {
            "name": "tags",
            "type": "array",
            "description": "Tags for categorization (optional)",
            "required": False,
        },
    ],
    service="feed-service",
    category="feed",
    latency="1000-3000ms",
)
async def create_feed(
    url: str,
    name: str,
    category: str = None,
    fetch_interval: int = 300,
    tags: list = None,
) -> MCPToolResult:
    """Add new RSS/Atom feed."""
    client = FeedClient()
    try:
        result = await client.create_feed(
            url=url,
            name=name,
            category=category,
            fetch_interval=fetch_interval,
            tags=tags,
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="fetch_feed",
    description="Manually trigger feed fetch/update. Forces immediate fetch of feed items, bypassing normal schedule. Returns number of new items fetched.",
    parameters=[
        {
            "name": "feed_id",
            "type": "integer",
            "description": "Feed ID to fetch",
            "required": True,
        },
    ],
    service="feed-service",
    category="feed",
    latency="1000-5000ms",
)
async def fetch_feed(feed_id: int) -> MCPToolResult:
    """Manually trigger feed fetch."""
    client = FeedClient()
    try:
        result = await client.fetch_feed(feed_id=feed_id)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


# ============================================================================
# Phase 3 - Research Service Tools (Final)
# ============================================================================


@register_tool(
    name="create_batch_research",
    description="Create multiple Perplexity research tasks in batch. Processes queries in parallel for efficiency. Returns array of task IDs with status.",
    parameters=[
        {
            "name": "queries",
            "type": "array",
            "description": "Array of research queries to process in batch",
            "required": True,
        },
    ],
    service="research-service",
    category="research",
    cost="$0.005-0.02 per query (Perplexity API)",
    latency="2000-10000ms per query (parallel)",
)
async def create_batch_research(queries: list) -> MCPToolResult:
    """Create batch research tasks."""
    client = ResearchClient()
    try:
        result = await client.create_batch_research(queries=queries)
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="apply_research_template",
    description="Execute research using pre-configured template. Quick research with template parameters. Returns task results with answer, citations, confidence.",
    parameters=[
        {
            "name": "template_id",
            "type": "string",
            "description": "Template ID to apply",
            "required": True,
        },
        {
            "name": "parameters",
            "type": "object",
            "description": "Template parameters (varies by template)",
            "required": True,
        },
    ],
    service="research-service",
    category="research",
    cost="$0.005-0.02 (Perplexity API)",
    latency="2000-10000ms (AI analysis)",
)
async def apply_research_template(
    template_id: str,
    parameters: dict,
) -> MCPToolResult:
    """Apply research template."""
    client = ResearchClient()
    try:
        result = await client.apply_research_template(
            template_id=template_id, parameters=parameters
        )
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


@register_tool(
    name="list_research_functions",
    description="List available research functions and capabilities. Shows what types of research operations are supported. Cached for 1 hour.",
    parameters=[],
    service="research-service",
    category="research",
    latency="10-50ms (cached)",
)
async def list_research_functions() -> MCPToolResult:
    """List research functions and capabilities."""
    client = ResearchClient()
    try:
        result = await client.list_research_functions()
        return MCPToolResult(success=True, data=result)
    finally:
        await client.close()


# ============================================================================
# Search History & Saved Search Management Tools
# ============================================================================


@register_tool(
    name="get_search_history",
    description="Get search history for a user. Returns recent searches with queries and timestamps. Useful for showing recent activity or analytics.",
    parameters=[
        {
            "name": "user_id",
            "type": "string",
            "description": "User ID to filter history (optional, returns all if not provided)",
            "required": False,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum results to return (default: 50)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="50-100ms",
)
async def get_search_history(
    user_id: str = None,
    limit: int = 50,
) -> MCPToolResult:
    """Get search history."""
    client = SearchClient()
    try:
        result = await client.get_search_history(user_id=user_id, limit=limit)
        return MCPToolResult(success=True, data=result)
    except Exception as e:
        return MCPToolResult(
            success=False, error=f"Failed to get search history: {str(e)}"
        )
    finally:
        await client.close()


@register_tool(
    name="clear_search_history",
    description="Clear search history. Can clear all history or just for a specific user. Use with caution as this is irreversible.",
    parameters=[
        {
            "name": "user_id",
            "type": "string",
            "description": "User ID to clear history for (optional, clears all if not provided)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="50-100ms",
)
async def clear_search_history(
    user_id: str = None,
) -> MCPToolResult:
    """Clear search history."""
    client = SearchClient()
    try:
        result = await client.clear_search_history(user_id=user_id)
        return MCPToolResult(success=True, data=result)
    except Exception as e:
        return MCPToolResult(
            success=False, error=f"Failed to clear search history: {str(e)}"
        )
    finally:
        await client.close()


@register_tool(
    name="get_saved_search",
    description="Get a specific saved search by ID. Returns the saved search details including name, query, and filters.",
    parameters=[
        {
            "name": "search_id",
            "type": "string",
            "description": "Saved search ID",
            "required": True,
        },
    ],
    service="search-service",
    category="search",
    latency="50-100ms",
)
async def get_saved_search(
    search_id: str,
) -> MCPToolResult:
    """Get saved search by ID."""
    client = SearchClient()
    try:
        result = await client.get_saved_search(search_id=search_id)
        return MCPToolResult(success=True, data=result)
    except Exception as e:
        return MCPToolResult(
            success=False, error=f"Failed to get saved search: {str(e)}"
        )
    finally:
        await client.close()


@register_tool(
    name="update_saved_search",
    description="Update an existing saved search. Can update name, query, and/or filters. Only provided fields will be updated.",
    parameters=[
        {
            "name": "search_id",
            "type": "string",
            "description": "Saved search ID to update",
            "required": True,
        },
        {
            "name": "name",
            "type": "string",
            "description": "New name for the saved search",
            "required": False,
        },
        {
            "name": "query",
            "type": "string",
            "description": "New search query",
            "required": False,
        },
        {
            "name": "filters",
            "type": "object",
            "description": "New filter settings (source, sentiment, date range, etc.)",
            "required": False,
        },
    ],
    service="search-service",
    category="search",
    latency="50-100ms",
)
async def update_saved_search(
    search_id: str,
    name: str = None,
    query: str = None,
    filters: dict = None,
) -> MCPToolResult:
    """Update saved search."""
    client = SearchClient()
    try:
        result = await client.update_saved_search(
            search_id=search_id, name=name, query=query, filters=filters
        )
        return MCPToolResult(success=True, data=result)
    except Exception as e:
        return MCPToolResult(
            success=False, error=f"Failed to update saved search: {str(e)}"
        )
    finally:
        await client.close()


# ============================================================================
# Tool Registry Export
# ============================================================================


def get_all_tools() -> list[MCPTool]:
    """Get list of all registered tools."""
    return [entry["definition"] for entry in tool_registry.values()]


def get_tool_handler(name: str) -> Callable[..., Awaitable[MCPToolResult]]:
    """Get tool handler by name."""
    if name not in tool_registry:
        raise ValueError(f"Tool {name} not found in registry")
    return tool_registry[name]["handler"]

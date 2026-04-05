"""MCP Tools for Feed service."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..models import MCPToolDefinition, MCPToolResult
from ..clients import FeedClient
from ..metrics import TOOL_CALLS_TOTAL, TOOL_CALL_DURATION

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        self.tools: Dict[str, MCPToolDefinition] = {}
        self.handlers: Dict[str, Callable] = {}
        self.feed_client: Optional[FeedClient] = None

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        category: str = "general",
    ) -> Callable:
        """Decorator to register a tool."""

        def decorator(func: Callable) -> Callable:
            self.tools[name] = MCPToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema,
                category=category,
            )
            self.handlers[name] = func
            return func

        return decorator

    def list_tools(self) -> List[MCPToolDefinition]:
        """Get all registered tools."""
        return list(self.tools.values())

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolResult:
        """Call a tool by name with given arguments."""
        if name not in self.handlers:
            available = list(self.handlers.keys())
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' not found. Available tools: {available}",
            )

        start_time = time.perf_counter()
        try:
            handler = self.handlers[name]
            result = await handler(self, **arguments)
            elapsed = time.perf_counter() - start_time

            TOOL_CALLS_TOTAL.labels(tool_name=name, status="success").inc()
            TOOL_CALL_DURATION.labels(tool_name=name).observe(elapsed)

            if isinstance(result, dict):
                if "success" in result:
                    return MCPToolResult(**result)
                return MCPToolResult(success=True, data=result)

            return MCPToolResult(success=True, data=result)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            TOOL_CALLS_TOTAL.labels(tool_name=name, status="error").inc()
            TOOL_CALL_DURATION.labels(tool_name=name).observe(elapsed)

            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"execution_time_ms": elapsed * 1000},
            )

    async def initialize_clients(self):
        """Initialize backend service clients."""
        self.feed_client = FeedClient()

    async def close_clients(self):
        """Close backend service clients."""
        if self.feed_client:
            await self.feed_client.close()


# Global tool registry instance
tool_registry = MCPToolRegistry()


# =============================================================================
# Feed Management Tools
# =============================================================================

@tool_registry.register(
    name="feeds_list",
    description="List all RSS/Atom news feeds with pagination. Returns feed metadata including name, URL, category, health score, last fetch time, article count, and error state. Use is_active filter to see only enabled feeds. Essential for getting an overview of all configured news sources.",
    input_schema={
        "type": "object",
        "properties": {
            "skip": {"type": "integer", "description": "Number of feeds to skip for pagination (default: 0)"},
            "limit": {"type": "integer", "description": "Maximum feeds to return (default: 20, max: 500)"},
            "is_active": {"type": "boolean", "description": "Filter by active status - true for enabled feeds, false for disabled, omit for all"},
        },
    },
    category="feeds",
)
async def feeds_list(
    registry: MCPToolRegistry,
    skip: int = 0,
    limit: int = 20,
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """List feeds with pagination info."""
    result = await registry.feed_client.list_feeds(skip, limit, is_active)

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", []))

    return {
        "total_found": len(items) + skip,  # Minimum known total (at least this many exist)
        "showing": len(items),
        "has_more": len(items) >= limit,  # True if likely more available
        "skip": skip,
        "limit": limit,
        "items": items,
    }


@tool_registry.register(
    name="feeds_get",
    description="Get detailed information about a specific RSS/Atom feed by its ID. Returns complete feed metadata including name, URL, category, active status, health metrics, quality scores, last fetch timestamp, article count, error history, and scheduling configuration. Use this to inspect individual feed configuration or diagnose feed-specific issues.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID - get from feeds_list or feed creation response"},
        },
        "required": ["feed_id"],
    },
    category="feeds",
)
async def feeds_get(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Get feed."""
    return await registry.feed_client.get_feed(feed_id)


@tool_registry.register(
    name="feeds_create",
    description="Add a new RSS/Atom feed to the system. The feed will be validated, scheduled for periodic fetching, and quality-assessed automatically. Returns the created feed object with assigned ID. Use quality_pre_assess first to evaluate feed quality before adding. Feeds are active by default and will start fetching immediately. Categories help organize feeds for filtering and reporting.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Human-readable feed name for display (e.g., 'Reuters World News')"},
            "url": {"type": "string", "description": "Full RSS/Atom feed URL (must be valid and accessible)"},
            "category": {"type": "string", "description": "Category for organization (e.g., 'news', 'finance', 'tech')"},
            "is_active": {"type": "boolean", "description": "Whether to start fetching immediately (default: true)", "default": True},
        },
        "required": ["name", "url"],
    },
    category="feeds",
)
async def feeds_create(
    registry: MCPToolRegistry,
    name: str,
    url: str,
    category: Optional[str] = None,
    is_active: bool = True,
) -> Dict[str, Any]:
    """Create feed."""
    return await registry.feed_client.create_feed(name, url, category, is_active)


@tool_registry.register(
    name="feeds_update",
    description="Modify an existing feed's configuration. Use to rename feeds, update URLs when sources change, or enable/disable feeds. Only specified fields are updated - omit fields to keep current values. Disabling a feed (is_active=false) stops scheduled fetching but preserves all historical data. Returns the updated feed object.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to update - get from feeds_list"},
            "name": {"type": "string", "description": "New display name (optional)"},
            "url": {"type": "string", "description": "New feed URL - use if source URL changed (optional)"},
            "is_active": {"type": "boolean", "description": "Set false to pause fetching, true to resume (optional)"},
        },
        "required": ["feed_id"],
    },
    category="feeds",
)
async def feeds_update(
    registry: MCPToolRegistry,
    feed_id: int,
    name: Optional[str] = None,
    url: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update feed."""
    return await registry.feed_client.update_feed(feed_id, name, url, is_active)


@tool_registry.register(
    name="feeds_delete",
    description="Permanently remove a feed from the system. WARNING: This also deletes all associated feed items/articles. Consider using feeds_update with is_active=false to disable instead if you want to preserve historical data. Returns confirmation of deletion. This action cannot be undone.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to delete - get from feeds_list. Deletion is permanent."},
        },
        "required": ["feed_id"],
    },
    category="feeds",
)
async def feeds_delete(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Delete feed."""
    return await registry.feed_client.delete_feed(feed_id)


@tool_registry.register(
    name="feeds_fetch",
    description="Immediately fetch new articles from a specific feed, bypassing the normal schedule. Use this to test a new feed, get urgent updates, or retry after fixing a feed error. Returns fetch results including new article count, errors encountered, and updated health metrics. Does not affect the regular fetch schedule.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to fetch immediately - get from feeds_list"},
        },
        "required": ["feed_id"],
    },
    category="feeds",
)
async def feeds_fetch(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Fetch feed."""
    return await registry.feed_client.fetch_feed(feed_id)


@tool_registry.register(
    name="feeds_bulk_fetch",
    description="Trigger immediate fetch for ALL active feeds at once. Use sparingly - this creates significant load on the system and external feed sources. Best used after system downtime to catch up, or when you need to ensure all feeds are current. Returns summary of fetch operations queued. Individual fetches run asynchronously.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="feeds",
)
async def feeds_bulk_fetch(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Bulk fetch feeds."""
    return await registry.feed_client.bulk_fetch_feeds()


@tool_registry.register(
    name="feeds_stats",
    description="Get aggregate statistics across all feeds. Returns total feed count, active/inactive breakdown, total articles collected, average health scores, fetch success rates, and error summaries. Essential for monitoring overall feed system health and capacity planning. Use feeds_health for individual feed diagnostics.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="feeds",
)
async def feeds_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get feed stats."""
    return await registry.feed_client.get_feed_stats()


@tool_registry.register(
    name="feeds_health",
    description="Get detailed health diagnostics for a specific feed. Returns health score (0-100), recent fetch history, error counts and types, response times, content freshness metrics, and reliability trends. Use this to diagnose why a feed might be failing or performing poorly. Health below 50 indicates issues requiring attention.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to check health - get from feeds_list"},
        },
        "required": ["feed_id"],
    },
    category="feeds",
)
async def feeds_health(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Get feed health."""
    return await registry.feed_client.get_feed_health(feed_id)


@tool_registry.register(
    name="feeds_reset_error",
    description="Clear error state and retry counter for a feed that has been failing. Use after fixing the underlying issue (e.g., feed URL changed, server was temporarily down). This resets the feed to a clean state and allows normal fetching to resume. Does not trigger an immediate fetch - use feeds_fetch after reset if needed.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to reset - get from feeds_list or feeds_health"},
        },
        "required": ["feed_id"],
    },
    category="feeds",
)
async def feeds_reset_error(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Reset feed error."""
    return await registry.feed_client.reset_feed_error(feed_id)


# =============================================================================
# Feed Items Tools
# =============================================================================

@tool_registry.register(
    name="items_list",
    description="List articles/items collected from RSS feeds with pagination. Returns item metadata including title, URL, publication date, feed source, and processing status. Filter by feed_id to see items from a specific feed, or omit to see all items. Items are ordered by publication date (newest first). Use for browsing collected content or verifying feed is producing articles.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Filter to items from specific feed (optional - omit for all feeds)"},
            "skip": {"type": "integer", "description": "Number of items to skip for pagination (default: 0)", "default": 0},
            "limit": {"type": "integer", "description": "Maximum items to return (default: 20, max: 500)", "default": 20},
        },
    },
    category="items",
)
async def items_list(
    registry: MCPToolRegistry,
    feed_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
) -> Dict[str, Any]:
    """List items with pagination info."""
    result = await registry.feed_client.list_feed_items(feed_id, skip, limit)

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", []))

    return {
        "total_found": len(items) + skip,  # Minimum known total (at least this many exist)
        "showing": len(items),
        "has_more": len(items) >= limit,  # True if likely more available
        "skip": skip,
        "limit": limit,
        "feed_id": feed_id,
        "items": items,
    }


@tool_registry.register(
    name="items_get",
    description="Get full details of a specific feed item/article by ID. Returns complete item data including title, full content/description, URL, publication date, author, categories/tags, feed source, and any extracted metadata. Use to inspect individual articles or retrieve content for analysis.",
    input_schema={
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Item ID - get from items_list or search results"},
            "feed_id": {"type": "integer", "description": "Feed ID for faster lookup (optional but recommended)"},
        },
        "required": ["item_id"],
    },
    category="items",
)
async def items_get(
    registry: MCPToolRegistry,
    item_id: int,
    feed_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Get item."""
    return await registry.feed_client.get_feed_item(item_id, feed_id)


# =============================================================================
# Feed Quality Tools
# =============================================================================

@tool_registry.register(
    name="quality_get",
    description="Get the quality assessment for a feed. Returns overall quality score (0-100), component scores (content quality, reliability, freshness, relevance), and the Admiralty Rating (source reliability + information credibility). Use to understand how trustworthy and valuable a feed's content is. For detailed metrics, use quality_get_v2 instead.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to get quality assessment for"},
        },
        "required": ["feed_id"],
    },
    category="quality",
)
async def quality_get(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Get quality."""
    return await registry.feed_client.get_feed_quality(feed_id)


@tool_registry.register(
    name="quality_get_v2",
    description="Get enhanced feed quality assessment with detailed metrics breakdown. Includes everything from quality_get plus: content analysis (avg article length, media presence, author attribution), publishing patterns (frequency, consistency, peak hours), technical metrics (response times, format compliance, encoding issues), and historical quality trends. Preferred over quality_get for thorough feed evaluation.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to get detailed quality metrics for"},
        },
        "required": ["feed_id"],
    },
    category="quality",
)
async def quality_get_v2(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Get quality v2."""
    return await registry.feed_client.get_feed_quality_v2(feed_id)


@tool_registry.register(
    name="quality_overview",
    description="Get quality overview across all feeds in the system. Returns aggregated statistics: average quality scores, distribution by quality tier (excellent/good/fair/poor), feeds needing attention, top and bottom performers, and quality trends over time. Essential for identifying which feeds to prioritize for review or removal.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="quality",
)
async def quality_overview(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get quality overview."""
    return await registry.feed_client.get_quality_overview()


@tool_registry.register(
    name="quality_assess",
    description="Trigger a new quality assessment for a feed. This analyzes recent articles to recalculate quality scores, Admiralty rating, and reliability metrics. Use after feed configuration changes or when you suspect quality has changed. Assessment runs asynchronously - check quality_get after a few seconds for updated scores. Assessments are also run automatically on schedule.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to reassess quality for"},
        },
        "required": ["feed_id"],
    },
    category="quality",
)
async def quality_assess(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Assess feed."""
    return await registry.feed_client.assess_feed(feed_id)


@tool_registry.register(
    name="quality_pre_assess",
    description="Evaluate a feed's quality BEFORE adding it to the system. Fetches the feed, analyzes sample articles, and returns predicted quality scores without creating any database records. Use this to vet potential feeds before committing to add them. Returns quality prediction, content analysis, potential issues, and recommendation (add/skip). Saves time by filtering out low-quality feeds upfront.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "RSS/Atom feed URL to evaluate (must be publicly accessible)"},
        },
        "required": ["url"],
    },
    category="quality",
)
async def quality_pre_assess(
    registry: MCPToolRegistry,
    url: str,
) -> Dict[str, Any]:
    """Pre-assess feed."""
    return await registry.feed_client.pre_assess_feed(url)


@tool_registry.register(
    name="quality_history",
    description="Get historical quality assessments for a feed over time. Returns list of past assessments with timestamps, scores, and what changed. Use to track quality trends, identify when a feed started degrading, or verify that quality improved after fixing issues. Useful for understanding feed behavior patterns over weeks/months.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to get assessment history for"},
        },
        "required": ["feed_id"],
    },
    category="quality",
)
async def quality_history(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Get assessment history."""
    return await registry.feed_client.get_assessment_history(feed_id)


# =============================================================================
# Admiralty Codes Tools
# =============================================================================

@tool_registry.register(
    name="admiralty_status",
    description="Get the current status of the Admiralty Rating system. The Admiralty Code is a NATO intelligence evaluation standard that rates sources (A-F for reliability) and information (1-6 for credibility). Returns system status, distribution of feeds by rating, recent rating changes, and feeds pending evaluation. Essential for intelligence-grade content assessment.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="admiralty",
)
async def admiralty_status(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get admiralty status."""
    return await registry.feed_client.get_admiralty_status()


@tool_registry.register(
    name="admiralty_weights",
    description="Get the weight configuration used for Admiralty Rating calculations. Shows how different factors (publication history, error rate, content quality, source reputation, corroboration) are weighted to compute reliability and credibility scores. Useful for understanding and fine-tuning how feeds are rated. Weights can be adjusted by admins.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="admiralty",
)
async def admiralty_weights(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get admiralty weights."""
    return await registry.feed_client.get_admiralty_weights()


@tool_registry.register(
    name="admiralty_thresholds",
    description="Get the score thresholds that determine Admiralty Rating grades. Shows what score ranges map to each reliability grade (A-F) and credibility grade (1-6). For example: scores 90-100 = Grade A (Completely Reliable), 70-89 = Grade B (Usually Reliable), etc. Useful for understanding why a feed received a particular rating.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="admiralty",
)
async def admiralty_thresholds(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get admiralty thresholds."""
    return await registry.feed_client.get_admiralty_thresholds()


# =============================================================================
# Scheduling Tools
# =============================================================================

@tool_registry.register(
    name="scheduling_stats",
    description="Get aggregate statistics about feed fetch scheduling. Returns total scheduled feeds, average fetch interval, distribution by fetch frequency tier (high/medium/low priority), next scheduled fetches, overdue feeds, and scheduler health metrics. Use to monitor if the scheduling system is working correctly and feeds are being fetched on time.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scheduling",
)
async def scheduling_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get scheduling stats."""
    return await registry.feed_client.get_scheduling_stats()


@tool_registry.register(
    name="scheduling_timeline",
    description="Get a timeline view of upcoming feed fetches. Returns chronologically ordered list of scheduled fetch operations for the next hour/day with feed names, scheduled times, and priority levels. Use to see what fetches are coming up, identify gaps in coverage, or plan maintenance windows that won't interrupt important feeds.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scheduling",
)
async def scheduling_timeline(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get scheduling timeline."""
    return await registry.feed_client.get_scheduling_timeline()


@tool_registry.register(
    name="scheduling_distribution",
    description="Analyze how feed fetches are distributed across time intervals. Returns fetch load by hour of day, day of week, and identifies peak/quiet periods. Use to ensure fetches are evenly distributed to avoid overwhelming the system or external servers. Helps identify if scheduling_optimize is needed to balance load.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scheduling",
)
async def scheduling_distribution(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get scheduling distribution."""
    return await registry.feed_client.get_scheduling_distribution()


@tool_registry.register(
    name="scheduling_conflicts",
    description="Identify scheduling conflicts and issues. Returns feeds scheduled at overlapping times, time slots with too many concurrent fetches, feeds with impossible schedules, and resource contention warnings. Use before adding new feeds or after noticing performance issues to find scheduling problems that need resolution.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scheduling",
)
async def scheduling_conflicts(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get scheduling conflicts."""
    return await registry.feed_client.get_scheduling_conflicts()


@tool_registry.register(
    name="scheduling_optimize",
    description="Automatically optimize feed fetch schedules for better load distribution. Rebalances fetch times to avoid clustering, respects feed priorities, and considers system capacity. Returns optimization report showing what changed and expected improvement. Run after adding many feeds or when scheduling_conflicts shows issues. Changes take effect immediately.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scheduling",
)
async def scheduling_optimize(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Optimize scheduling."""
    return await registry.feed_client.optimize_scheduling()


@tool_registry.register(
    name="scheduling_get_feed",
    description="Get the detailed fetch schedule for a specific feed. Returns fetch interval, next scheduled fetch time, last fetch time, priority tier, and any schedule overrides. Use to understand when a particular feed will be updated or to diagnose why a feed seems to be fetching too often or not often enough.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to get schedule details for"},
        },
        "required": ["feed_id"],
    },
    category="scheduling",
)
async def scheduling_get_feed(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Get feed schedule."""
    return await registry.feed_client.get_feed_schedule(feed_id)

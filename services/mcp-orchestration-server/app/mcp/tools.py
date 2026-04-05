"""MCP Tools for Scheduler service."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..models import MCPToolDefinition, MCPToolResult
from ..clients import SchedulerClient, MediaStackClient, ScrapingClient, IntelligenceClient
from ..metrics import TOOL_CALLS_TOTAL, TOOL_CALL_DURATION

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        self.tools: Dict[str, MCPToolDefinition] = {}
        self.handlers: Dict[str, Callable] = {}
        self.scheduler_client: Optional[SchedulerClient] = None
        self.mediastack_client: Optional[MediaStackClient] = None
        self.scraping_client: Optional[ScrapingClient] = None
        self.intelligence_client: Optional[IntelligenceClient] = None

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
        self.scheduler_client = SchedulerClient()
        self.mediastack_client = MediaStackClient()
        self.scraping_client = ScrapingClient()
        self.intelligence_client = IntelligenceClient()

        # Register intelligence proxy tools after client is initialized
        register_intelligence_proxy_tools(self)

    async def close_clients(self):
        """Close backend service clients."""
        if self.scheduler_client:
            await self.scheduler_client.close()
        if self.mediastack_client:
            await self.mediastack_client.close()
        if self.scraping_client:
            await self.scraping_client.close()
        if self.intelligence_client:
            await self.intelligence_client.close()


# Global tool registry instance
tool_registry = MCPToolRegistry()


# =============================================================================
# Scheduler Status & Health Tools
# =============================================================================

@tool_registry.register(
    name="scheduler_status",
    description="Get scheduler status overview including active jobs and worker status.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="status",
)
async def scheduler_status(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get scheduler status."""
    return await registry.scheduler_client.get_status()


@tool_registry.register(
    name="scheduler_health",
    description="Get detailed scheduler service health information.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="status",
)
async def scheduler_health(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get scheduler health."""
    return await registry.scheduler_client.get_service_health()


# =============================================================================
# Job Management Tools
# =============================================================================

@tool_registry.register(
    name="jobs_list",
    description="List scheduler jobs with optional status filter.",
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "running", "completed", "failed"],
                "description": "Filter by job status",
            },
            "skip": {"type": "integer", "description": "Number to skip", "default": 0},
            "limit": {"type": "integer", "description": "Max to return", "default": 20},
        },
    },
    category="jobs",
)
async def jobs_list(
    registry: MCPToolRegistry,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Dict[str, Any]:
    """List jobs with pagination info."""
    result = await registry.scheduler_client.list_jobs(status, skip, limit)

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("jobs", [])))

    return {
        "total_found": len(items) + skip,  # Minimum known total
        "showing": len(items),
        "has_more": len(items) >= limit,
        "skip": skip,
        "limit": limit,
        "status_filter": status,
        "items": items,
    }


@tool_registry.register(
    name="jobs_stats",
    description="Get job statistics including counts, success rates, and durations.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="jobs",
)
async def jobs_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get job stats."""
    return await registry.scheduler_client.get_job_stats()


@tool_registry.register(
    name="jobs_cancel",
    description="Cancel a pending or running job.",
    input_schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Job ID to cancel"},
        },
        "required": ["job_id"],
    },
    category="jobs",
)
async def jobs_cancel(
    registry: MCPToolRegistry,
    job_id: str,
) -> Dict[str, Any]:
    """Cancel job."""
    return await registry.scheduler_client.cancel_job(job_id)


@tool_registry.register(
    name="jobs_retry",
    description="Retry a failed job.",
    input_schema={
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "Job ID to retry"},
        },
        "required": ["job_id"],
    },
    category="jobs",
)
async def jobs_retry(
    registry: MCPToolRegistry,
    job_id: str,
) -> Dict[str, Any]:
    """Retry job."""
    return await registry.scheduler_client.retry_job(job_id)


# =============================================================================
# Cron Job Tools
# =============================================================================

@tool_registry.register(
    name="cron_list",
    description="List all scheduled cron jobs with their schedules.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="cron",
)
async def cron_list(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """List cron jobs."""
    return await registry.scheduler_client.list_cron_jobs()


# =============================================================================
# Feed Scheduling Tools
# =============================================================================

@tool_registry.register(
    name="feed_schedule_check",
    description="Check the schedule for a specific feed.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {"type": "integer", "description": "Feed ID to check"},
        },
        "required": ["feed_id"],
    },
    category="feeds",
)
async def feed_schedule_check(
    registry: MCPToolRegistry,
    feed_id: int,
) -> Dict[str, Any]:
    """Check feed schedule."""
    return await registry.scheduler_client.check_feed_schedule(feed_id)


# =============================================================================
# MediaStack News Tools
# =============================================================================

@tool_registry.register(
    name="mediastack_live_news",
    description="""Fetch live news articles from MediaStack API.

BEST PRACTICES:
- Keywords: Use SINGLE words, not phrases. 'epstein' finds more than 'epstein files'.
- Sort: ALWAYS use 'published_desc' for current news. Never use 'popularity' (returns old articles).
- Languages: Use 'en' for English sources, 'de' for German, or omit for all.
- Limit: Default 25, max 100 per request.

Returns articles sorted by publication date with source, title, description, and URL.""",
    input_schema={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "Search keywords. Use SINGLE words for best results (e.g., 'bitcoin' not 'bitcoin price'). Multiple words are OR-matched.",
            },
            "sources": {
                "type": "string",
                "description": "Comma-separated source IDs to filter by",
            },
            "categories": {
                "type": "string",
                "description": "Comma-separated categories (general, business, technology, entertainment, sports, science, health)",
            },
            "countries": {
                "type": "string",
                "description": "Comma-separated country codes (us, de, gb, etc.)",
            },
            "languages": {
                "type": "string",
                "description": "Comma-separated language codes (en, de, etc.)",
            },
            "sort": {
                "type": "string",
                "description": "Sort order. USE 'published_desc' for current news (RECOMMENDED). 'published_asc' for historical research. AVOID 'popularity' (returns old viral articles).",
                "default": "published_desc",
            },
            "limit": {
                "type": "integer",
                "description": "Results per page (1-100)",
                "default": 25,
            },
            "offset": {
                "type": "integer",
                "description": "Pagination offset",
                "default": 0,
            },
        },
    },
    category="mediastack",
)
async def mediastack_live_news(
    registry: MCPToolRegistry,
    keywords: Optional[str] = None,
    sources: Optional[str] = None,
    categories: Optional[str] = None,
    countries: Optional[str] = None,
    languages: Optional[str] = None,
    sort: Optional[str] = "published_desc",
    limit: int = 25,
    offset: int = 0,
) -> Dict[str, Any]:
    """Fetch live news from MediaStack."""
    return await registry.mediastack_client.get_live_news(
        keywords=keywords,
        sources=sources,
        categories=categories,
        countries=countries,
        languages=languages,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@tool_registry.register(
    name="mediastack_historical_news",
    description="""Fetch historical news articles from MediaStack API (PAID PLAN ONLY).

BEST PRACTICES:
- Keywords: Use SINGLE words, not phrases. 'epstein' finds more than 'epstein files'.
- Date Range: Use date_from and date_to for specific periods (YYYY-MM-DD format).
- Sort: Use 'published_desc' for most recent first, 'published_asc' for chronological order.

Returns articles within date range with source, title, description, and URL.""",
    input_schema={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "Search keywords. Use SINGLE words for best results (e.g., 'trump' not 'trump news'). Multiple words are OR-matched.",
            },
            "sources": {
                "type": "string",
                "description": "Comma-separated source IDs",
            },
            "categories": {
                "type": "string",
                "description": "Comma-separated categories",
            },
            "countries": {
                "type": "string",
                "description": "Comma-separated country codes",
            },
            "languages": {
                "type": "string",
                "description": "Comma-separated language codes",
            },
            "date_from": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD)",
            },
            "date_to": {
                "type": "string",
                "description": "End date (YYYY-MM-DD)",
            },
            "sort": {
                "type": "string",
                "description": "Sort order. USE 'published_desc' for current news (RECOMMENDED). 'published_asc' for historical research. AVOID 'popularity' (returns old viral articles).",
                "default": "published_desc",
            },
            "limit": {
                "type": "integer",
                "description": "Results per page (1-100)",
                "default": 25,
            },
            "offset": {
                "type": "integer",
                "description": "Pagination offset",
                "default": 0,
            },
        },
    },
    category="mediastack",
)
async def mediastack_historical_news(
    registry: MCPToolRegistry,
    keywords: Optional[str] = None,
    sources: Optional[str] = None,
    categories: Optional[str] = None,
    countries: Optional[str] = None,
    languages: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort: Optional[str] = "published_desc",
    limit: int = 25,
    offset: int = 0,
) -> Dict[str, Any]:
    """Fetch historical news from MediaStack."""
    return await registry.mediastack_client.get_historical_news(
        keywords=keywords,
        sources=sources,
        categories=categories,
        countries=countries,
        languages=languages,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@tool_registry.register(
    name="mediastack_sources",
    description="Get available news sources from MediaStack. Use to discover which sources are available for filtering.",
    input_schema={
        "type": "object",
        "properties": {
            "countries": {
                "type": "string",
                "description": "Filter sources by country codes",
            },
            "categories": {
                "type": "string",
                "description": "Filter sources by categories",
            },
            "languages": {
                "type": "string",
                "description": "Filter sources by language codes",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum sources to return",
                "default": 20,
            },
        },
    },
    category="mediastack",
)
async def mediastack_sources(
    registry: MCPToolRegistry,
    countries: Optional[str] = None,
    categories: Optional[str] = None,
    languages: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Get available news sources with pagination info."""
    result = await registry.mediastack_client.get_sources(
        countries=countries,
        categories=categories,
        languages=languages,
        limit=limit,
    )

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("sources", [])))

    return {
        "total_found": len(items),  # Minimum known total
        "showing": len(items),
        "has_more": len(items) >= limit,
        "limit": limit,
        "filters": {"countries": countries, "categories": categories, "languages": languages},
        "items": items,
    }


@tool_registry.register(
    name="mediastack_usage",
    description="Get MediaStack API usage statistics including calls made, remaining quota, and usage percentage.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="mediastack",
)
async def mediastack_usage(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get API usage statistics."""
    return await registry.mediastack_client.get_usage()


# =============================================================================
# Scraping Service - Monitoring & Health Tools
# =============================================================================

@tool_registry.register(
    name="scraping_health",
    description="Get scraping service health status including browser, Redis, and component status.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_health(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get scraping service health."""
    return await registry.scraping_client.get_health()


@tool_registry.register(
    name="scraping_metrics",
    description="Get comprehensive scraping service metrics including concurrency, retry stats, and browser status.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_metrics(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get service metrics."""
    return await registry.scraping_client.get_metrics()


@tool_registry.register(
    name="scraping_active_jobs",
    description="Get currently active scraping jobs with URLs, start times, and durations.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_active_jobs(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get active scraping jobs."""
    return await registry.scraping_client.get_active_jobs()


@tool_registry.register(
    name="scraping_rate_limits",
    description="Get rate limit statistics for a specific key (e.g., 'domain:example.com', 'global').",
    input_schema={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Rate limit key (e.g., 'domain:example.com', 'global', 'feed:uuid')",
            },
        },
        "required": ["key"],
    },
    category="scraping",
)
async def scraping_rate_limits(
    registry: MCPToolRegistry,
    key: str,
) -> Dict[str, Any]:
    """Get rate limit stats."""
    return await registry.scraping_client.get_rate_limit_stats(key)


@tool_registry.register(
    name="scraping_feed_failures",
    description="Get failure count and threshold for a specific feed.",
    input_schema={
        "type": "object",
        "properties": {
            "feed_id": {
                "type": "string",
                "description": "Feed UUID",
            },
        },
        "required": ["feed_id"],
    },
    category="scraping",
)
async def scraping_feed_failures(
    registry: MCPToolRegistry,
    feed_id: str,
) -> Dict[str, Any]:
    """Get feed failure stats."""
    return await registry.scraping_client.get_feed_failures(feed_id)


# =============================================================================
# Scraping Service - Source Profile Tools
# =============================================================================

@tool_registry.register(
    name="scraping_sources_list",
    description="List source profiles with optional status filter. Shows domains with scraping configuration and performance metrics.",
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["working", "degraded", "blocked", "unknown"],
                "description": "Filter by source status",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results",
                "default": 20,
            },
            "offset": {
                "type": "integer",
                "description": "Pagination offset",
                "default": 0,
            },
        },
    },
    category="scraping",
)
async def scraping_sources_list(
    registry: MCPToolRegistry,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """List source profiles with pagination info."""
    result = await registry.scraping_client.list_sources(status, limit, offset)

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("sources", [])))

    return {
        "total_found": len(items) + offset,  # Minimum known total
        "showing": len(items),
        "has_more": len(items) >= limit,
        "offset": offset,
        "limit": limit,
        "status_filter": status,
        "items": items,
    }


@tool_registry.register(
    name="scraping_sources_stats",
    description="Get overall source registry statistics including total sources, breakdown by status, and average success rate.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_sources_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get source statistics."""
    return await registry.scraping_client.get_source_statistics()


@tool_registry.register(
    name="scraping_source_lookup",
    description="Lookup source profile for a URL. Returns the source profile for the domain, creating one with defaults if none exists.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to lookup source for",
            },
        },
        "required": ["url"],
    },
    category="scraping",
)
async def scraping_source_lookup(
    registry: MCPToolRegistry,
    url: str,
) -> Dict[str, Any]:
    """Lookup source for URL."""
    return await registry.scraping_client.lookup_source(url)


@tool_registry.register(
    name="scraping_source_config",
    description="Get complete scraping configuration for a URL including method, fallbacks, and settings.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to get config for",
            },
        },
        "required": ["url"],
    },
    category="scraping",
)
async def scraping_source_config(
    registry: MCPToolRegistry,
    url: str,
) -> Dict[str, Any]:
    """Get scrape config for URL."""
    return await registry.scraping_client.get_scrape_config(url)


@tool_registry.register(
    name="scraping_source_get",
    description="Get source profile by domain name.",
    input_schema={
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "description": "Domain name (e.g., 'spiegel.de')",
            },
        },
        "required": ["domain"],
    },
    category="scraping",
)
async def scraping_source_get(
    registry: MCPToolRegistry,
    domain: str,
) -> Dict[str, Any]:
    """Get source profile."""
    return await registry.scraping_client.get_source_profile(domain)


@tool_registry.register(
    name="scraping_sources_seed",
    description="Seed the registry with known German news sources (spiegel.de, faz.net, tagesschau.de, etc.) with optimal scraping settings.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_sources_seed(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Seed known sources."""
    return await registry.scraping_client.seed_known_sources()


# =============================================================================
# Scraping Service - Dead Letter Queue Tools
# =============================================================================

@tool_registry.register(
    name="scraping_dlq_stats",
    description="Get Dead Letter Queue statistics including entry counts by status and failure reason.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_dlq_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get DLQ stats."""
    return await registry.scraping_client.get_dlq_stats()


@tool_registry.register(
    name="scraping_dlq_list",
    description="List Dead Letter Queue entries with optional filters.",
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "resolved", "abandoned", "manual"],
                "description": "Filter by status",
            },
            "domain": {
                "type": "string",
                "description": "Filter by domain",
            },
            "failure_reason": {
                "type": "string",
                "enum": ["timeout", "rate_limited", "blocked", "paywall", "parse_error", "network_error", "unknown"],
                "description": "Filter by failure reason",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum entries",
                "default": 20,
            },
        },
    },
    category="scraping",
)
async def scraping_dlq_list(
    registry: MCPToolRegistry,
    status: Optional[str] = None,
    domain: Optional[str] = None,
    failure_reason: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """List DLQ entries with pagination info."""
    result = await registry.scraping_client.list_dlq_entries(
        status, domain, failure_reason, limit
    )

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("entries", [])))

    return {
        "total_found": len(items),  # Minimum known total
        "showing": len(items),
        "has_more": len(items) >= limit,
        "limit": limit,
        "filters": {"status": status, "domain": domain, "failure_reason": failure_reason},
        "items": items,
    }


@tool_registry.register(
    name="scraping_dlq_pending",
    description="Get DLQ entries ready for retry.",
    input_schema={
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "description": "Filter by domain",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum entries",
                "default": 20,
            },
        },
    },
    category="scraping",
)
async def scraping_dlq_pending(
    registry: MCPToolRegistry,
    domain: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Get pending DLQ entries with pagination info."""
    result = await registry.scraping_client.get_pending_dlq_entries(domain, limit)

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("entries", [])))

    return {
        "total_found": len(items),  # Minimum known total
        "showing": len(items),
        "has_more": len(items) >= limit,
        "limit": limit,
        "domain_filter": domain,
        "items": items,
    }


@tool_registry.register(
    name="scraping_dlq_resolve",
    description="Mark a DLQ entry as resolved.",
    input_schema={
        "type": "object",
        "properties": {
            "entry_id": {
                "type": "integer",
                "description": "DLQ entry ID",
            },
            "notes": {
                "type": "string",
                "description": "Resolution notes",
            },
        },
        "required": ["entry_id"],
    },
    category="scraping",
)
async def scraping_dlq_resolve(
    registry: MCPToolRegistry,
    entry_id: int,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve DLQ entry."""
    return await registry.scraping_client.resolve_dlq_entry(entry_id, notes)


@tool_registry.register(
    name="scraping_dlq_cleanup",
    description="Remove resolved/abandoned DLQ entries older than specified days.",
    input_schema={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Remove entries older than this many days",
                "default": 30,
            },
        },
    },
    category="scraping",
)
async def scraping_dlq_cleanup(
    registry: MCPToolRegistry,
    days: int = 30,
) -> Dict[str, Any]:
    """Cleanup old DLQ entries."""
    return await registry.scraping_client.cleanup_dlq(days)


# =============================================================================
# Scraping Service - Cache Tools
# =============================================================================

@tool_registry.register(
    name="scraping_cache_stats",
    description="Get HTTP cache statistics including entries, size, hit rate, and age metrics.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_cache_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get cache stats."""
    return await registry.scraping_client.get_cache_stats()


@tool_registry.register(
    name="scraping_cache_invalidate",
    description="Invalidate cache entries by URL or domain.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Specific URL to invalidate",
            },
            "domain": {
                "type": "string",
                "description": "Domain to invalidate all URLs for",
            },
        },
    },
    category="scraping",
)
async def scraping_cache_invalidate(
    registry: MCPToolRegistry,
    url: Optional[str] = None,
    domain: Optional[str] = None,
) -> Dict[str, Any]:
    """Invalidate cache."""
    return await registry.scraping_client.invalidate_cache(url, domain)


@tool_registry.register(
    name="scraping_cache_cleanup",
    description="Remove all expired cache entries.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_cache_cleanup(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Cleanup expired cache."""
    return await registry.scraping_client.cleanup_cache()


@tool_registry.register(
    name="scraping_cache_clear",
    description="Clear entire HTTP cache (use with caution).",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_cache_clear(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Clear all cache."""
    return await registry.scraping_client.clear_cache()


# =============================================================================
# Scraping Service - Proxy Tools
# =============================================================================

@tool_registry.register(
    name="scraping_proxy_stats",
    description="Get proxy pool statistics including healthy/unhealthy counts, response times, and success rate.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_proxy_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get proxy stats."""
    return await registry.scraping_client.get_proxy_stats()


@tool_registry.register(
    name="scraping_proxy_list",
    description="List all proxies in the pool with their status.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_proxy_list(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """List proxies."""
    return await registry.scraping_client.list_proxies()


@tool_registry.register(
    name="scraping_proxy_add",
    description="Add a proxy to the pool.",
    input_schema={
        "type": "object",
        "properties": {
            "proxy_id": {
                "type": "string",
                "description": "Unique proxy identifier",
            },
            "host": {
                "type": "string",
                "description": "Proxy host address",
            },
            "port": {
                "type": "integer",
                "description": "Proxy port",
            },
            "username": {
                "type": "string",
                "description": "Auth username (optional)",
            },
            "password": {
                "type": "string",
                "description": "Auth password (optional)",
            },
            "proxy_type": {
                "type": "string",
                "enum": ["http", "https", "socks5"],
                "description": "Proxy type",
                "default": "http",
            },
        },
        "required": ["proxy_id", "host", "port"],
    },
    category="scraping",
)
async def scraping_proxy_add(
    registry: MCPToolRegistry,
    proxy_id: str,
    host: str,
    port: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    proxy_type: str = "http",
) -> Dict[str, Any]:
    """Add proxy."""
    return await registry.scraping_client.add_proxy(
        proxy_id, host, port, username, password, proxy_type
    )


@tool_registry.register(
    name="scraping_proxy_remove",
    description="Remove a proxy from the pool.",
    input_schema={
        "type": "object",
        "properties": {
            "proxy_id": {
                "type": "string",
                "description": "Proxy ID to remove",
            },
        },
        "required": ["proxy_id"],
    },
    category="scraping",
)
async def scraping_proxy_remove(
    registry: MCPToolRegistry,
    proxy_id: str,
) -> Dict[str, Any]:
    """Remove proxy."""
    return await registry.scraping_client.remove_proxy(proxy_id)


@tool_registry.register(
    name="scraping_proxy_health",
    description="Get health information for a specific proxy.",
    input_schema={
        "type": "object",
        "properties": {
            "proxy_id": {
                "type": "string",
                "description": "Proxy ID",
            },
        },
        "required": ["proxy_id"],
    },
    category="scraping",
)
async def scraping_proxy_health(
    registry: MCPToolRegistry,
    proxy_id: str,
) -> Dict[str, Any]:
    """Get proxy health."""
    return await registry.scraping_client.get_proxy_health(proxy_id)


@tool_registry.register(
    name="scraping_proxy_reset",
    description="Reset unhealthy proxies for retry.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_proxy_reset(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Reset unhealthy proxies."""
    return await registry.scraping_client.reset_unhealthy_proxies()


# =============================================================================
# Scraping Service - Queue Tools
# =============================================================================

@tool_registry.register(
    name="scraping_queue_stats",
    description="Get priority queue statistics including job counts, wait times, and throughput.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_queue_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get queue stats."""
    return await registry.scraping_client.get_queue_stats()


@tool_registry.register(
    name="scraping_queue_enqueue",
    description="Add a scraping job to the priority queue.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to scrape",
            },
            "priority": {
                "type": "string",
                "enum": ["LOW", "NORMAL", "HIGH", "CRITICAL"],
                "description": "Job priority",
                "default": "NORMAL",
            },
            "method": {
                "type": "string",
                "description": "Scraping method (auto, httpx, playwright, newspaper4k, trafilatura)",
            },
            "max_retries": {
                "type": "integer",
                "description": "Maximum retry attempts",
                "default": 3,
            },
            "delay_seconds": {
                "type": "integer",
                "description": "Delay before processing",
                "default": 0,
            },
        },
        "required": ["url"],
    },
    category="scraping",
)
async def scraping_queue_enqueue(
    registry: MCPToolRegistry,
    url: str,
    priority: str = "NORMAL",
    method: Optional[str] = None,
    max_retries: int = 3,
    delay_seconds: int = 0,
) -> Dict[str, Any]:
    """Enqueue scraping job."""
    return await registry.scraping_client.enqueue_job(
        url, priority, method, max_retries, delay_seconds
    )


@tool_registry.register(
    name="scraping_queue_status",
    description="Get status of a specific scraping job.",
    input_schema={
        "type": "object",
        "properties": {
            "job_id": {
                "type": "string",
                "description": "Job ID",
            },
        },
        "required": ["job_id"],
    },
    category="scraping",
)
async def scraping_queue_status(
    registry: MCPToolRegistry,
    job_id: str,
) -> Dict[str, Any]:
    """Get job status."""
    return await registry.scraping_client.get_job_status(job_id)


@tool_registry.register(
    name="scraping_queue_cancel",
    description="Cancel a pending scraping job.",
    input_schema={
        "type": "object",
        "properties": {
            "job_id": {
                "type": "string",
                "description": "Job ID to cancel",
            },
        },
        "required": ["job_id"],
    },
    category="scraping",
)
async def scraping_queue_cancel(
    registry: MCPToolRegistry,
    job_id: str,
) -> Dict[str, Any]:
    """Cancel job."""
    return await registry.scraping_client.cancel_queue_job(job_id)


@tool_registry.register(
    name="scraping_queue_pending",
    description="List pending jobs in the queue.",
    input_schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum jobs to return",
                "default": 20,
            },
        },
    },
    category="scraping",
)
async def scraping_queue_pending(
    registry: MCPToolRegistry,
    limit: int = 20,
) -> Dict[str, Any]:
    """List pending jobs with pagination info."""
    result = await registry.scraping_client.list_pending_queue_jobs(limit)

    # Handle both list and dict responses
    items = result if isinstance(result, list) else result.get("items", result.get("data", result.get("jobs", [])))

    return {
        "total_found": len(items),  # Minimum known total
        "showing": len(items),
        "has_more": len(items) >= limit,
        "limit": limit,
        "items": items,
    }


@tool_registry.register(
    name="scraping_queue_clear",
    description="Clear all pending jobs from the queue.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="scraping",
)
async def scraping_queue_clear(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Clear queue."""
    return await registry.scraping_client.clear_queue()


# =============================================================================
# Scraping Service - Wikipedia Tools
# =============================================================================

@tool_registry.register(
    name="scraping_wikipedia_search",
    description="Search Wikipedia articles by query. Returns matching articles with snippets.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (entity name)",
            },
            "language": {
                "type": "string",
                "enum": ["de", "en"],
                "description": "Wikipedia language",
                "default": "de",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results",
                "default": 10,
            },
            "auth_token": {
                "type": "string",
                "description": "Bearer token for authentication",
            },
        },
        "required": ["query", "auth_token"],
    },
    category="scraping",
)
async def scraping_wikipedia_search(
    registry: MCPToolRegistry,
    query: str,
    auth_token: str,
    language: str = "de",
    limit: int = 10,
) -> Dict[str, Any]:
    """Search Wikipedia."""
    return await registry.scraping_client.search_wikipedia(
        query, language, limit, auth_token
    )


@tool_registry.register(
    name="scraping_wikipedia_article",
    description="Get full Wikipedia article data including summary, infobox, categories, and links.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Article title (exact match)",
            },
            "language": {
                "type": "string",
                "enum": ["de", "en"],
                "description": "Wikipedia language",
                "default": "de",
            },
            "include_infobox": {
                "type": "boolean",
                "description": "Extract infobox data",
                "default": True,
            },
            "include_categories": {
                "type": "boolean",
                "description": "Extract categories",
                "default": True,
            },
            "include_links": {
                "type": "boolean",
                "description": "Extract related links",
                "default": True,
            },
            "auth_token": {
                "type": "string",
                "description": "Bearer token for authentication",
            },
        },
        "required": ["title", "auth_token"],
    },
    category="scraping",
)
async def scraping_wikipedia_article(
    registry: MCPToolRegistry,
    title: str,
    auth_token: str,
    language: str = "de",
    include_infobox: bool = True,
    include_categories: bool = True,
    include_links: bool = True,
) -> Dict[str, Any]:
    """Get Wikipedia article."""
    return await registry.scraping_client.get_wikipedia_article(
        title, language, include_infobox, include_categories, include_links, auth_token
    )


@tool_registry.register(
    name="scraping_wikipedia_relationships",
    description="Extract relationship candidates from Wikipedia article. Returns relationships with confidence scores for Knowledge Graph enrichment.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Article title (entity name)",
            },
            "language": {
                "type": "string",
                "enum": ["de", "en"],
                "description": "Wikipedia language",
                "default": "de",
            },
            "entity_type": {
                "type": "string",
                "description": "Entity type hint (PERSON, ORGANIZATION, etc.)",
            },
            "auth_token": {
                "type": "string",
                "description": "Bearer token for authentication",
            },
        },
        "required": ["title", "auth_token"],
    },
    category="scraping",
)
async def scraping_wikipedia_relationships(
    registry: MCPToolRegistry,
    title: str,
    auth_token: str,
    language: str = "de",
    entity_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract Wikipedia relationships."""
    return await registry.scraping_client.extract_wikipedia_relationships(
        title, language, entity_type, auth_token
    )


# =============================================================================
# Direct Scraping (No Queue)
# =============================================================================


@tool_registry.register(
    name="scraping_direct_scrape",
    description="Scrape a URL directly and return content immediately. Bypasses queue, synchronous operation. Best for ad-hoc scraping of single URLs.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to scrape",
            },
            "method": {
                "type": "string",
                "enum": ["auto", "newspaper4k", "playwright", "stealth"],
                "description": "Scraping method. auto: intelligent selection based on source profile",
                "default": "auto",
            },
        },
        "required": ["url"],
    },
    category="scraping",
)
async def scraping_direct_scrape(
    registry: MCPToolRegistry,
    url: str,
    method: Optional[str] = None,
) -> Dict[str, Any]:
    """Scrape URL directly without queue."""
    return await registry.scraping_client.direct_scrape(url, method)


# =============================================================================
# Intelligence Tools (Proxied from mcp-intelligence-server)
# =============================================================================

# Intelligence tools to proxy from mcp-intelligence-server with full parameter schemas
INTELLIGENCE_TOOLS = {
    "get_intelligence_overview": {
        "description": "Get intelligence dashboard overview with cluster stats, risk metrics, and trending entities.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    "get_event_clusters": {
        "description": "Get event clusters from intelligence analysis. Returns clusters with articles, entities, and timelines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum clusters to return (default: 20)"},
                "min_articles": {"type": "integer", "description": "Minimum articles per cluster (default: 3)"},
            },
        },
    },
    "get_cluster_details": {
        "description": "Get detailed information about specific event cluster including articles, entities, and timeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string", "description": "Cluster ID (UUID)"},
            },
            "required": ["cluster_id"],
        },
    },
    "get_cluster_events": {
        "description": "Get paginated events for specific cluster with title, source, entities, keywords, sentiment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string", "description": "Cluster ID (UUID)"},
                "page": {"type": "integer", "description": "Page number (default: 1)"},
                "per_page": {"type": "integer", "description": "Items per page, max 100 (default: 20)"},
            },
            "required": ["cluster_id"],
        },
    },
    "get_latest_events": {
        "description": "Get most recent intelligence events with timestamps and summaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum events to return (default: 20)"},
            },
        },
    },
    "get_subcategories": {
        "description": "Get top sub-topics per category (geo, finance, tech) from current news data.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    "get_risk_history": {
        "description": "Get historical risk scores for trend visualization. Returns daily risk history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Days to look back, 1-30 (default: 7)"},
            },
        },
    },
    "analyze_content": {
        "description": "Analyze text content for entities, keywords, and intelligence extraction using NLP.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text content to analyze (10-50000 characters)"},
                "include_keywords": {"type": "boolean", "description": "Include keyword extraction (default: True)"},
                "max_keywords": {"type": "integer", "description": "Maximum keywords, 1-50 (default: 10)"},
            },
            "required": ["text"],
        },
    },
    "get_entity_clusters": {
        "description": "Get entity clusters for given type. Returns canonical entities and their variants.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {"type": "string", "description": "Entity type: PERSON, ORG, GPE, LOC, etc."},
            },
            "required": ["entity_type"],
        },
    },
    "canonicalize_entity": {
        "description": "Canonicalize entity to resolve duplicates using vector similarity. Finds canonical form.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity name to canonicalize"},
                "entity_type": {"type": "string", "description": "Entity type: PERSON, ORG, GPE, LOC, etc."},
            },
            "required": ["entity_name", "entity_type"],
        },
    },
    "get_narrative_analysis": {
        "description": "Get narrative analysis overview with top frames, bias distribution, and trends.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    "get_narrative_frames": {
        "description": "Get narrative frames from article analysis with frequency and examples.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum frames to return (default: 20)"},
                "category": {"type": "string", "description": "Optional category filter"},
            },
        },
    },
}


def register_intelligence_proxy_tools(registry: "MCPToolRegistry"):
    """Register all intelligence tools as proxies with full parameter schemas.

    These tools are forwarded to mcp-intelligence-server (9001).
    Called during initialize_clients() after intelligence_client is set.
    """
    for tool_name, tool_config in INTELLIGENCE_TOOLS.items():
        # Create a closure to capture the current tool_name
        def create_handler(tn: str):
            async def handler(reg: MCPToolRegistry, **kwargs) -> Dict[str, Any]:
                """Proxy handler for intelligence tool."""
                if not reg.intelligence_client:
                    return {"success": False, "error": "Intelligence client not initialized"}
                return await reg.intelligence_client.call_tool(tn, kwargs)
            return handler

        # Register the tool with explicit parameter schema
        registry.tools[tool_name] = MCPToolDefinition(
            name=tool_name,
            description=tool_config["description"],
            input_schema=tool_config["input_schema"],
            category="intelligence",
        )
        registry.handlers[tool_name] = create_handler(tool_name)
        logger.info(f"Registered intelligence proxy tool: {tool_name}")

"""MCP Tools Registry and Implementations."""

import time
import logging
from typing import Dict, Any, Callable, Awaitable, List, Optional
from functools import wraps

from ..models import MCPTool, MCPToolParameter, MCPToolResult
from ..clients import FMPClient, ResearchClient, NotificationClient

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
    """Decorator to register MCP tool."""

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
# FMP Market Data Tools
# ============================================================================

@register_tool(
    name="get_market_quote",
    description="""Get current market quote for a symbol. Returns price, volume, change, and other quote data.

Supports human-readable commodity aliases:
- GOLD → Gold Futures (GCUSD)
- SILVER → Silver Futures (SIUSD)
- OIL/CRUDE → WTI Crude Oil (CLUSD)
- NATGAS/GAS → Natural Gas (NGUSD)
- COPPER → Copper Futures (HGUSD)
- PALLADIUM → Palladium (PAUSD)
- PLATINUM → Platinum (PLUSD)

Examples:
- get_market_quote("GOLD") → Returns gold futures at ~$4982
- get_market_quote("AAPL") → Returns Apple stock quote
- get_market_quote("BTCUSD") → Returns Bitcoin quote""",
    parameters=[
        {
            "name": "symbol",
            "type": "string",
            "description": "Asset symbol (e.g., BTCUSD, AAPL, GOLD, OIL). Commodity aliases are automatically resolved.",
            "required": True,
        }
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~50ms",
)
async def get_market_quote(symbol: str, client: FMPClient) -> MCPToolResult:
    """Get market quote for symbol."""
    try:
        result = await client.get_quote(symbol)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"symbol": symbol, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_market_quotes_batch",
    description="Get quotes for multiple symbols in a single request. More efficient for multiple symbols.",
    parameters=[
        {
            "name": "symbols",
            "type": "array",
            "description": "List of asset symbols",
            "required": True,
        },
        {
            "name": "asset_type",
            "type": "string",
            "description": "Asset type (crypto, forex, indices, commodities)",
            "required": True,
            "enum": ["crypto", "forex", "indices", "commodities"],
        },
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~100ms",
)
async def get_market_quotes_batch(
    symbols: List[str], asset_type: str, client: FMPClient
) -> MCPToolResult:
    """Get batch quotes."""
    try:
        result = await client.get_quotes_batch(symbols, asset_type)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"symbols": symbols, "asset_type": asset_type, "count": len(symbols), "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_ohlcv_candles",
    description="Get OHLCV (Open, High, Low, Close, Volume) candles for a symbol.",
    parameters=[
        {
            "name": "symbol",
            "type": "string",
            "description": "Asset symbol",
            "required": True,
        },
        {
            "name": "interval",
            "type": "string",
            "description": "Candle interval (1min, 5min, 15min, 30min, 1hour, 4hour)",
            "required": False,
            "enum": ["1min", "5min", "15min", "30min", "1hour", "4hour"],
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum candles to return (default: 50)",
            "required": False,
        },
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~100ms",
)
async def get_ohlcv_candles(
    symbol: str,
    interval: str = "1hour",
    limit: int = 50,
    client: FMPClient = None,
) -> MCPToolResult:
    """Get OHLCV candles."""
    try:
        result = await client.get_candles(symbol, interval, limit)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "service": "fmp-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_ohlcv_timerange",
    description="Get OHLCV candles for a specific time range.",
    parameters=[
        {
            "name": "symbol",
            "type": "string",
            "description": "Asset symbol",
            "required": True,
        },
        {
            "name": "start",
            "type": "string",
            "description": "Start datetime (ISO format, e.g., 2024-01-01T00:00:00Z)",
            "required": True,
        },
        {
            "name": "end",
            "type": "string",
            "description": "End datetime (ISO format)",
            "required": True,
        },
        {
            "name": "interval",
            "type": "string",
            "description": "Candle interval",
            "required": False,
        },
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~150ms",
)
async def get_ohlcv_timerange(
    symbol: str,
    start: str,
    end: str,
    interval: str = "1h",
    client: FMPClient = None,
) -> MCPToolResult:
    """Get OHLCV for time range."""
    try:
        result = await client.get_candles_timerange(symbol, start, end, interval)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "symbol": symbol,
                "start": start,
                "end": end,
                "interval": interval,
                "service": "fmp-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_market_status",
    description="Get current market status (open/closed) for all markets.",
    parameters=[],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~30ms",
)
async def get_market_status(client: FMPClient) -> MCPToolResult:
    """Get market status."""
    try:
        result = await client.get_market_status()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="list_symbols",
    description="List available trading symbols with optional filtering by asset type.",
    parameters=[
        {
            "name": "asset_type",
            "type": "string",
            "description": "Asset type filter (crypto, stock, forex, index, commodity)",
            "required": False,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum symbols to return (default: 20)",
            "required": False,
        },
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~100ms",
)
async def list_symbols(
    asset_type: str = None,
    limit: int = 20,
    client: FMPClient = None,
) -> MCPToolResult:
    """List symbols with pagination info."""
    try:
        result = await client.list_symbols(asset_type, limit)

        # Handle both list and dict responses
        items = result if isinstance(result, list) else result.get("items", result.get("data", []))

        return MCPToolResult(
            success=True,
            data={
                "total_found": len(items),  # Minimum known total
                "showing": len(items),
                "has_more": len(items) >= limit,  # True if likely more available
                "limit": limit,
                "asset_type": asset_type,
                "items": items,
            },
            metadata={"asset_type": asset_type, "limit": limit, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="search_symbols",
    description="Search for symbols by name or ticker.",
    parameters=[
        {
            "name": "query",
            "type": "string",
            "description": "Search query",
            "required": True,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum results (default: 20)",
            "required": False,
        },
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~80ms",
)
async def search_symbols(query: str, limit: int = 20, client: FMPClient = None) -> MCPToolResult:
    """Search symbols with pagination info."""
    try:
        result = await client.search_symbols(query, limit)

        # Handle both list and dict responses
        items = result if isinstance(result, list) else result.get("items", result.get("data", []))

        return MCPToolResult(
            success=True,
            data={
                "total_found": len(items),  # Minimum known total
                "showing": len(items),
                "has_more": len(items) >= limit,  # True if likely more available
                "limit": limit,
                "query": query,
                "items": items,
            },
            metadata={"query": query, "limit": limit, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_asset_metadata",
    description="Get metadata for an asset (name, type, exchange, description).",
    parameters=[
        {
            "name": "symbol",
            "type": "string",
            "description": "Asset symbol",
            "required": True,
        }
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~50ms",
)
async def get_asset_metadata(symbol: str, client: FMPClient) -> MCPToolResult:
    """Get asset metadata."""
    try:
        result = await client.get_asset_metadata(symbol)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"symbol": symbol, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


# ============================================================================
# FMP Financial News Tools
# ============================================================================

@register_tool(
    name="get_financial_news",
    description="Get financial news articles with optional symbol filter.",
    parameters=[
        {
            "name": "symbol",
            "type": "string",
            "description": "Optional symbol to filter news",
            "required": False,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum articles (default: 20)",
            "required": False,
        },
    ],
    service="fmp-service",
    category="news",
    cost="$0",
    latency="~100ms",
)
async def get_financial_news(
    symbol: str = None,
    limit: int = 20,
    client: FMPClient = None,
) -> MCPToolResult:
    """Get financial news."""
    try:
        result = await client.get_news(limit, symbol)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"symbol": symbol, "limit": limit, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_news_by_sentiment",
    description="Get financial news filtered by sentiment.",
    parameters=[
        {
            "name": "sentiment",
            "type": "string",
            "description": "Sentiment filter",
            "required": True,
            "enum": ["positive", "negative", "neutral"],
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum articles (default: 20)",
            "required": False,
        },
    ],
    service="fmp-service",
    category="news",
    cost="$0",
    latency="~100ms",
)
async def get_news_by_sentiment(
    sentiment: str,
    limit: int = 20,
    client: FMPClient = None,
) -> MCPToolResult:
    """Get news by sentiment."""
    try:
        result = await client.get_news_by_sentiment(sentiment, limit)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"sentiment": sentiment, "limit": limit, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


# ============================================================================
# FMP Macro Indicators Tools
# ============================================================================

@register_tool(
    name="get_macro_indicators",
    description="List available macroeconomic indicators.",
    parameters=[],
    service="fmp-service",
    category="macro",
    cost="$0",
    latency="~50ms",
)
async def get_macro_indicators(client: FMPClient) -> MCPToolResult:
    """Get macro indicators list."""
    try:
        result = await client.get_macro_indicators()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_macro_indicator_data",
    description="Get data for a specific macroeconomic indicator.",
    parameters=[
        {
            "name": "indicator_name",
            "type": "string",
            "description": "Indicator name (e.g., GDP, CPI, UNEMPLOYMENT)",
            "required": True,
        }
    ],
    service="fmp-service",
    category="macro",
    cost="$0",
    latency="~100ms",
)
async def get_macro_indicator_data(indicator_name: str, client: FMPClient) -> MCPToolResult:
    """Get macro indicator data."""
    try:
        result = await client.get_macro_indicator(indicator_name)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"indicator": indicator_name, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_latest_macro_data",
    description="Get latest values for all macroeconomic indicators.",
    parameters=[],
    service="fmp-service",
    category="macro",
    cost="$0",
    latency="~100ms",
)
async def get_latest_macro_data(client: FMPClient) -> MCPToolResult:
    """Get latest macro data."""
    try:
        result = await client.get_latest_macro()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


# ============================================================================
# FMP Earnings Tools
# ============================================================================

@register_tool(
    name="get_earnings_calendar",
    description="Get upcoming earnings calendar.",
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
    service="fmp-service",
    category="earnings",
    cost="$0",
    latency="~100ms",
)
async def get_earnings_calendar(
    start_date: str = None,
    end_date: str = None,
    client: FMPClient = None,
) -> MCPToolResult:
    """Get earnings calendar."""
    try:
        result = await client.get_earnings_calendar(start_date, end_date)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "start_date": start_date,
                "end_date": end_date,
                "service": "fmp-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_earnings_history",
    description="Get historical earnings data for a stock.",
    parameters=[
        {
            "name": "symbol",
            "type": "string",
            "description": "Stock symbol",
            "required": True,
        }
    ],
    service="fmp-service",
    category="earnings",
    cost="$0",
    latency="~100ms",
)
async def get_earnings_history(symbol: str, client: FMPClient) -> MCPToolResult:
    """Get earnings history."""
    try:
        result = await client.get_earnings_history(symbol)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"symbol": symbol, "service": "fmp-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


# ============================================================================
# Research Service Tools
# ============================================================================

@register_tool(
    name="research_query",
    description="Execute AI-powered research query using Perplexity. Returns comprehensive answer with sources.",
    parameters=[
        {
            "name": "query",
            "type": "string",
            "description": "Research question or topic",
            "required": True,
        },
        {
            "name": "model",
            "type": "string",
            "description": "Perplexity model (sonar, sonar-pro)",
            "required": False,
            "enum": ["sonar", "sonar-pro"],
        },
        {
            "name": "max_tokens",
            "type": "integer",
            "description": "Max response tokens (default: 1024)",
            "required": False,
        },
    ],
    service="research-service",
    category="research",
    cost="~$0.005 per query",
    latency="~2-5s",
)
async def research_query(
    query: str,
    model: str = "sonar",
    max_tokens: int = 1024,
    client: ResearchClient = None,
) -> MCPToolResult:
    """Execute research query."""
    try:
        result = await client.research(query, model, max_tokens)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "query": query[:100],
                "model": model,
                "service": "research-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="research_batch",
    description="Execute multiple research queries in batch. More efficient for multiple queries.",
    parameters=[
        {
            "name": "queries",
            "type": "array",
            "description": "List of research questions",
            "required": True,
        },
        {
            "name": "model",
            "type": "string",
            "description": "Perplexity model",
            "required": False,
        },
    ],
    service="research-service",
    category="research",
    cost="~$0.005 per query",
    latency="~5-15s",
)
async def research_batch(
    queries: List[str],
    model: str = "sonar",
    client: ResearchClient = None,
) -> MCPToolResult:
    """Execute batch research."""
    try:
        result = await client.research_batch(queries, model)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "query_count": len(queries),
                "model": model,
                "service": "research-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_research_result",
    description="Get research result by task ID. Use for async/batch queries.",
    parameters=[
        {
            "name": "task_id",
            "type": "string",
            "description": "Research task ID",
            "required": True,
        }
    ],
    service="research-service",
    category="research",
    cost="$0",
    latency="~50ms",
)
async def get_research_result(task_id: str, client: ResearchClient) -> MCPToolResult:
    """Get research result."""
    try:
        result = await client.get_research_result(task_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"task_id": task_id, "service": "research-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_research_history",
    description="Get research query history.",
    parameters=[
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum results (default: 50)",
            "required": False,
        },
    ],
    service="research-service",
    category="research",
    cost="$0",
    latency="~100ms",
)
async def get_research_history(limit: int = 50, client: ResearchClient = None) -> MCPToolResult:
    """Get research history."""
    try:
        result = await client.get_research_history(limit)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"limit": limit, "service": "research-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="list_research_templates",
    description="List available research templates.",
    parameters=[],
    service="research-service",
    category="research",
    cost="$0",
    latency="~50ms",
)
async def list_research_templates(client: ResearchClient) -> MCPToolResult:
    """List research templates."""
    try:
        result = await client.list_templates()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"service": "research-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="apply_research_template",
    description="Apply research template with variables.",
    parameters=[
        {
            "name": "template_id",
            "type": "integer",
            "description": "Template ID",
            "required": True,
        },
        {
            "name": "variables",
            "type": "object",
            "description": "Template variable values",
            "required": True,
        },
    ],
    service="research-service",
    category="research",
    cost="~$0.005",
    latency="~2-5s",
)
async def apply_research_template(
    template_id: int,
    variables: Dict[str, Any],
    client: ResearchClient = None,
) -> MCPToolResult:
    """Apply research template."""
    try:
        result = await client.apply_template(template_id, variables)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "template_id": template_id,
                "variables": variables,
                "service": "research-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


# ============================================================================
# Notification Service Tools
# ============================================================================

@register_tool(
    name="send_notification",
    description="Send notification to user using a template.",
    parameters=[
        {
            "name": "user_id",
            "type": "integer",
            "description": "Target user ID",
            "required": True,
        },
        {
            "name": "template_id",
            "type": "string",
            "description": "Notification template ID",
            "required": True,
        },
        {
            "name": "channel",
            "type": "string",
            "description": "Delivery channel",
            "required": False,
            "enum": ["email", "webhook", "push"],
        },
        {
            "name": "data",
            "type": "object",
            "description": "Template data",
            "required": False,
        },
    ],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~200ms",
)
async def send_notification(
    user_id: int,
    template_id: str,
    channel: str = "email",
    data: Dict[str, Any] = None,
    client: NotificationClient = None,
) -> MCPToolResult:
    """Send notification."""
    try:
        result = await client.send_notification(user_id, template_id, channel, data)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "user_id": user_id,
                "template_id": template_id,
                "channel": channel,
                "service": "notification-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="send_adhoc_notification",
    description="Send ad-hoc notification without template.",
    parameters=[
        {
            "name": "user_id",
            "type": "integer",
            "description": "Target user ID",
            "required": True,
        },
        {
            "name": "subject",
            "type": "string",
            "description": "Notification subject",
            "required": True,
        },
        {
            "name": "body",
            "type": "string",
            "description": "Notification body",
            "required": True,
        },
        {
            "name": "channel",
            "type": "string",
            "description": "Delivery channel",
            "required": False,
        },
    ],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~200ms",
)
async def send_adhoc_notification(
    user_id: int,
    subject: str,
    body: str,
    channel: str = "email",
    client: NotificationClient = None,
) -> MCPToolResult:
    """Send ad-hoc notification."""
    try:
        result = await client.send_adhoc_notification(user_id, subject, body, channel)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "user_id": user_id,
                "subject": subject[:50],
                "channel": channel,
                "service": "notification-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_notification_history",
    description="Get notification history for a user.",
    parameters=[
        {
            "name": "user_id",
            "type": "integer",
            "description": "User ID (optional)",
            "required": False,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum results (default: 50)",
            "required": False,
        },
    ],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~100ms",
)
async def get_notification_history(
    user_id: int = None,
    limit: int = 50,
    client: NotificationClient = None,
) -> MCPToolResult:
    """Get notification history."""
    try:
        result = await client.get_notification_history(user_id, limit)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "user_id": user_id,
                "limit": limit,
                "service": "notification-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="list_notification_templates",
    description="List available notification templates.",
    parameters=[],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~50ms",
)
async def list_notification_templates(client: NotificationClient) -> MCPToolResult:
    """List notification templates."""
    try:
        result = await client.list_templates()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"service": "notification-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_notification_preferences",
    description="Get notification preferences for user.",
    parameters=[
        {
            "name": "user_id",
            "type": "integer",
            "description": "User ID (optional)",
            "required": False,
        }
    ],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~50ms",
)
async def get_notification_preferences(
    user_id: int = None,
    client: NotificationClient = None,
) -> MCPToolResult:
    """Get notification preferences."""
    try:
        result = await client.get_preferences(user_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"user_id": user_id, "service": "notification-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_notification_queue_stats",
    description="Get notification queue statistics (admin).",
    parameters=[],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~50ms",
)
async def get_notification_queue_stats(client: NotificationClient) -> MCPToolResult:
    """Get queue stats."""
    try:
        result = await client.get_queue_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"service": "notification-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_notification",
    description="Get notification details by ID.",
    parameters=[
        {
            "name": "notification_id",
            "type": "string",
            "description": "Notification ID",
            "required": True,
        }
    ],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~50ms",
)
async def get_notification(
    notification_id: str,
    client: NotificationClient = None,
) -> MCPToolResult:
    """Get notification details."""
    try:
        result = await client.get_notification(notification_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"notification_id": notification_id, "service": "notification-service"},
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="test_notification",
    description="Send a test notification to verify template and channel.",
    parameters=[
        {
            "name": "template_id",
            "type": "string",
            "description": "Template ID to test",
            "required": True,
        },
        {
            "name": "channel",
            "type": "string",
            "description": "Delivery channel (email, webhook, push)",
            "required": False,
            "enum": ["email", "webhook", "push"],
        },
    ],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~500ms",
)
async def test_notification(
    template_id: str,
    channel: str = "email",
    client: NotificationClient = None,
) -> MCPToolResult:
    """Send test notification."""
    try:
        result = await client.test_notification(template_id, channel)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "template_id": template_id,
                "channel": channel,
                "service": "notification-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="update_notification_preferences",
    description="Update notification preferences for user.",
    parameters=[
        {
            "name": "preferences",
            "type": "object",
            "description": "Preference settings (email_enabled, push_enabled, etc.)",
            "required": True,
        },
        {
            "name": "user_id",
            "type": "integer",
            "description": "User ID (optional, uses current user if not provided)",
            "required": False,
        },
    ],
    service="notification-service",
    category="notification",
    cost="$0",
    latency="~100ms",
)
async def update_notification_preferences(
    preferences: Dict[str, Any],
    user_id: int = None,
    client: NotificationClient = None,
) -> MCPToolResult:
    """Update notification preferences."""
    try:
        result = await client.update_preferences(preferences, user_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "user_id": user_id,
                "preferences_updated": list(preferences.keys()),
                "service": "notification-service",
            },
        )
    except Exception as e:
        return MCPToolResult(success=False, error=str(e))


# ============================================================================
# FMP ETF Reference Data Tools
# ============================================================================

@register_tool(
    name="search_etfs",
    description="""Search ETFs by sector, theme, or keyword.

Use cases:
- Find defense ETFs: search_etfs(sector="Defense")
- Find AI/tech ETFs: search_etfs(theme="AI")
- Find specific ETF: search_etfs(search="NVIDIA")

Available sectors: Defense, Tech, Healthcare, Materials, Energy, Utilities, Broad
Available themes: NATO/Military, AI, Semiconductors, Rare Earth, Lithium/Battery, Clean Energy, Cybersecurity, Gaming, Water, Healthcare, Global, Developed Markets, Emerging Markets
""",
    parameters=[
        {
            "name": "sector",
            "type": "string",
            "description": "Filter by sector (Defense, Tech, Healthcare, Materials, Energy, Utilities, Broad)",
            "required": False,
        },
        {
            "name": "theme",
            "type": "string",
            "description": "Filter by investment theme (AI, Rare Earth, NATO/Military, Semiconductors, etc.)",
            "required": False,
        },
        {
            "name": "search",
            "type": "string",
            "description": "Search in ETF name, ticker, or ISIN",
            "required": False,
        },
        {
            "name": "limit",
            "type": "integer",
            "description": "Maximum results (default: 20)",
            "required": False,
        },
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~50-150ms",
)
async def search_etfs(
    sector: str = None,
    theme: str = None,
    search: str = None,
    limit: int = 20,
    client: FMPClient = None,
) -> MCPToolResult:
    """Search ETFs by sector, theme, or keyword."""
    try:
        result = await client.search_etfs(
            sector=sector,
            theme=theme,
            search=search,
            limit=limit,
        )
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "search_etfs",
                "filters": {"sector": sector, "theme": theme, "search": search},
                "service": "fmp-service",
            },
        )
    except Exception as e:
        logger.error(f"ETF search failed: {e}")
        return MCPToolResult(success=False, error=str(e))


@register_tool(
    name="get_etf_details",
    description="Get detailed ETF information by ISIN including holdings and performance.",
    parameters=[
        {
            "name": "isin",
            "type": "string",
            "description": "ETF ISIN (e.g., IE000YYE6WK5 for VanEck Defense)",
            "required": True,
        },
    ],
    service="fmp-service",
    category="market",
    cost="$0",
    latency="~30-100ms",
)
async def get_etf_details(isin: str, client: FMPClient = None) -> MCPToolResult:
    """Get ETF details by ISIN."""
    try:
        result = await client.get_etf(isin=isin)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_etf_details", "isin": isin, "service": "fmp-service"},
        )
    except Exception as e:
        logger.error(f"Get ETF details failed for {isin}: {e}")
        return MCPToolResult(success=False, error=str(e))

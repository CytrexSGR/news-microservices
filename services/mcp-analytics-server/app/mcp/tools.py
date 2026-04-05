"""MCP Tool Registry for Analytics Server.

Phase 1: 12 Tools
- Analytics Service: 4 tools
- Prediction Service: 5 tools
- Execution Service: 3 tools

Phase 2: 20 Tools
- Analytics Service: 7 additional tools (11 total)
- Prediction Service: 9 additional tools (14 total)
- Execution Service: 4 additional tools (7 total)

Total: 32 Tools
"""

import logging
from typing import Dict, Any, Callable, Optional

from ..models import MCPTool, MCPToolParameter, MCPToolResult
from ..clients import AnalyticsClient, PredictionClient, ExecutionClient

logger = logging.getLogger(__name__)

# ============================================================================
# Tool Registry
# ============================================================================

tool_registry: Dict[str, Dict[str, Any]] = {}


def register_tool(
    name: str,
    description: str,
    parameters: list[MCPToolParameter],
    service: str,
    category: str,
    latency: Optional[str] = None,
    cost: Optional[str] = None,
):
    """
    Decorator to register MCP tools.

    Args:
        name: Tool name
        description: Tool description
        parameters: List of tool parameters
        service: Backend service name
        category: Tool category
        latency: Expected latency (optional)
        cost: API cost if applicable (optional)
    """

    def decorator(func: Callable):
        # Create tool definition
        tool_def = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            service=service,
            category=category,
            latency=latency,
            cost=cost,
        )

        # Register tool
        tool_registry[name] = {"definition": tool_def, "handler": func}

        logger.info(f"Registered MCP tool: {name} ({service})")
        return func

    return decorator


# ============================================================================
# Phase 1 - Analytics Service Tools (4 tools)
# ============================================================================


@register_tool(
    name="get_analytics_overview",
    description="Get system-wide analytics overview including metrics summary, health status, and trends. Provides high-level view of entire system performance.",
    parameters=[],
    service="analytics-service",
    category="analytics",
    latency="50-200ms",
)
async def get_analytics_overview(client: AnalyticsClient) -> MCPToolResult:
    """
    Get analytics overview from analytics-service.

    Returns system-wide metrics, health status, trends, and key performance indicators.
    """
    try:
        result = await client.get_overview()

        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_analytics_overview", "service": "analytics-service"},
        )
    except Exception as e:
        logger.error(f"Analytics overview failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_analytics_overview"},
        )


@register_tool(
    name="get_analytics_trends",
    description="Get analytics trends over time for specific metrics or all metrics. Useful for identifying patterns, anomalies, and performance changes.",
    parameters=[
        MCPToolParameter(
            name="metric",
            type="string",
            description="Specific metric to get trends for (e.g., 'cpu_usage', 'response_time'). If not specified, returns all metrics.",
            required=False,
        ),
        MCPToolParameter(
            name="period",
            type="string",
            description="Time period for trend analysis. Options: '1h', '24h', '7d', '30d'. Default: '7d'",
            required=False,
            enum=["1h", "24h", "7d", "30d"],
        ),
    ],
    service="analytics-service",
    category="analytics",
    latency="100-500ms",
)
async def get_analytics_trends(
    client: AnalyticsClient,
    metric: Optional[str] = None,
    period: str = "7d",
) -> MCPToolResult:
    """
    Get analytics trends with time series data.

    Provides historical trend data for system metrics over specified time period.
    """
    try:
        result = await client.get_trends(metric=metric, period=period)

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_analytics_trends",
                "service": "analytics-service",
                "metric": metric,
                "period": period,
            },
        )
    except Exception as e:
        logger.error(f"Analytics trends failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_analytics_trends"},
        )


@register_tool(
    name="get_circuit_breaker_status",
    description="Get circuit breaker status for all monitored backend services. Shows which services are CLOSED (healthy), OPEN (failing), or HALF_OPEN (recovering).",
    parameters=[],
    service="analytics-service",
    category="monitoring",
    latency="50-150ms",
)
async def get_circuit_breaker_status(client: AnalyticsClient) -> MCPToolResult:
    """
    Get circuit breaker status for all services.

    Returns status, failure counts, and recovery state for each monitored service.
    Critical for identifying service outages and degraded performance.
    """
    try:
        result = await client.get_circuit_breakers()

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_circuit_breaker_status",
                "service": "analytics-service",
            },
        )
    except Exception as e:
        logger.error(f"Circuit breaker status failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_circuit_breaker_status"},
        )


@register_tool(
    name="get_query_performance",
    description="Get database query performance metrics including slow queries, average execution times, and query patterns. Essential for identifying database bottlenecks.",
    parameters=[],
    service="analytics-service",
    category="monitoring",
    latency="100-300ms",
)
async def get_query_performance(client: AnalyticsClient) -> MCPToolResult:
    """
    Get database query performance stats.

    Returns slow query analysis, execution time distributions, and query optimization opportunities.
    """
    try:
        result = await client.get_query_performance()

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_query_performance",
                "service": "analytics-service",
            },
        )
    except Exception as e:
        logger.error(f"Query performance failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_query_performance"},
        )


# ============================================================================
# Phase 1 - Prediction Service Tools (5 tools)
# ============================================================================


@register_tool(
    name="get_predictions",
    description="Get recent predictions from ML models with confidence scores and metadata. Useful for reviewing model outputs and tracking prediction history.",
    parameters=[
        MCPToolParameter(
            name="model_name",
            type="string",
            description="Filter predictions by specific model name (optional). If not specified, returns predictions from all models.",
            required=False,
        ),
        MCPToolParameter(
            name="limit",
            type="integer",
            description="Number of predictions to return (max 100). Default: 10",
            required=False,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="50-200ms",
)
async def get_predictions(
    client: PredictionClient,
    model_name: Optional[str] = None,
    limit: int = 10,
) -> MCPToolResult:
    """
    Get recent predictions from ML models.

    Returns list of predictions with confidence scores, timestamps, and model metadata.
    """
    try:
        result = await client.get_predictions(model_name=model_name, limit=limit)

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_predictions",
                "service": "prediction-service",
                "model_name": model_name,
                "limit": limit,
            },
        )
    except Exception as e:
        logger.error(f"Get predictions failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_predictions"},
        )


@register_tool(
    name="create_prediction",
    description="Create new prediction using specified ML model. Requires model name and input features. Returns prediction result with confidence score.",
    parameters=[
        MCPToolParameter(
            name="model_name",
            type="string",
            description="Name of ML model to use for prediction (e.g., 'btc_price_lstm', 'sentiment_classifier')",
            required=True,
        ),
        MCPToolParameter(
            name="input_data",
            type="object",
            description="Input features for prediction as JSON object. Structure depends on model requirements.",
            required=True,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="200-2000ms",
)
async def create_prediction(
    client: PredictionClient,
    model_name: str,
    input_data: Dict[str, Any],
) -> MCPToolResult:
    """
    Create new prediction using ML model.

    Takes input features and returns prediction with confidence score and metadata.
    """
    try:
        result = await client.create_prediction(
            model_name=model_name,
            input_data=input_data,
        )

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "create_prediction",
                "service": "prediction-service",
                "model_name": model_name,
            },
        )
    except Exception as e:
        logger.error(f"Create prediction failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "create_prediction", "model_name": model_name},
        )


@register_tool(
    name="get_features",
    description="Get feature data for a specific trading symbol including technical indicators, market data, and sentiment scores. Essential for ML predictions.",
    parameters=[
        MCPToolParameter(
            name="symbol",
            type="string",
            description="Trading symbol (e.g., 'BTCUSD', 'ETHUSD', 'SOLUSD')",
            required=True,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-500ms",
)
async def get_features(
    client: PredictionClient,
    symbol: str,
) -> MCPToolResult:
    """
    Get feature data for trading symbol.

    Returns comprehensive feature set including technical indicators, market data, and derived features.
    """
    try:
        result = await client.get_features(symbol=symbol)

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_features",
                "service": "prediction-service",
                "symbol": symbol,
            },
        )
    except Exception as e:
        logger.error(f"Get features failed for {symbol}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_features", "symbol": symbol},
        )


@register_tool(
    name="get_indicators",
    description="Get technical indicators for a specific symbol and timeframe. Includes RSI, MACD, Bollinger Bands, moving averages, and more.",
    parameters=[
        MCPToolParameter(
            name="symbol",
            type="string",
            description="Trading symbol (e.g., 'BTCUSD', 'ETHUSD')",
            required=True,
        ),
        MCPToolParameter(
            name="timeframe",
            type="string",
            description="Timeframe for indicators. Options: '1m', '5m', '15m', '1h', '4h', '1d'. Default: '1h'",
            required=False,
            enum=["1m", "5m", "15m", "1h", "4h", "1d"],
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-400ms",
)
async def get_indicators(
    client: PredictionClient,
    symbol: str,
    timeframe: str = "1h",
) -> MCPToolResult:
    """
    Get technical indicators for symbol.

    Returns calculated technical indicators for specified timeframe.
    """
    try:
        result = await client.get_indicators(symbol=symbol, timeframe=timeframe)

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_indicators",
                "service": "prediction-service",
                "symbol": symbol,
                "timeframe": timeframe,
            },
        )
    except Exception as e:
        logger.error(f"Get indicators failed for {symbol}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_indicators", "symbol": symbol},
        )


@register_tool(
    name="get_signals",
    description="[DEPRECATED] Trading signals endpoint was deprecated 2025-12-20. Use 'get_consensus_alerts' for multi-model agreement signals instead.",
    parameters=[
        MCPToolParameter(
            name="symbol",
            type="string",
            description="Filter by trading symbol (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="strategy",
            type="string",
            description="Filter by strategy name (optional)",
            required=False,
        ),
        MCPToolParameter(
            name="min_confidence",
            type="number",
            description="Minimum confidence threshold (0-1). Default: 0.5",
            required=False,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-500ms",
)
async def get_signals(
    client: PredictionClient,
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    min_confidence: float = 0.5,
) -> MCPToolResult:
    """
    [DEPRECATED] Get trading signals from models.

    This endpoint was deprecated on 2025-12-20.
    Use 'get_consensus_alerts' for multi-model agreement signals instead.
    """
    # Return deprecation notice instead of calling deprecated endpoint
    return MCPToolResult(
        success=False,
        error="This tool is deprecated (since 2025-12-20). Use 'get_consensus_alerts' instead for multi-model consensus signals.",
        data={
            "deprecated": True,
            "deprecated_date": "2025-12-20",
            "alternatives": [
                {
                    "tool": "get_consensus_alerts",
                    "description": "Get alerts when multiple ML models agree on predictions",
                },
                {
                    "tool": "get_predictions",
                    "description": "Get raw predictions from ML models",
                },
            ],
            "migration_guide": "Replace get_signals() with get_consensus_alerts() for high-confidence trading signals based on multi-model agreement.",
        },
        metadata={"tool": "get_signals", "status": "deprecated"},
    )


# ============================================================================
# Phase 1 - Execution Service Tools (3 tools)
# ============================================================================


@register_tool(
    name="get_positions",
    description="Get all trading positions with status, entry/exit prices, PnL, and position details. Essential for portfolio monitoring.",
    parameters=[
        MCPToolParameter(
            name="status",
            type="string",
            description="Filter by position status: 'open', 'closed', or 'all'. Default: 'open'",
            required=False,
            enum=["open", "closed", "all"],
        ),
    ],
    service="execution-service",
    category="execution",
    latency="50-200ms",
)
async def get_positions(
    client: ExecutionClient,
    status: Optional[str] = None,
) -> MCPToolResult:
    """
    Get trading positions.

    Returns list of positions with entry/exit prices, PnL, and status information.
    """
    try:
        result = await client.get_positions(status=status)

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_positions",
                "service": "execution-service",
                "status": status,
            },
        )
    except Exception as e:
        logger.error(f"Get positions failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_positions"},
        )


@register_tool(
    name="get_portfolio",
    description="Get portfolio overview including current holdings, total value, PnL, and asset allocations. High-level portfolio summary.",
    parameters=[],
    service="execution-service",
    category="execution",
    latency="100-300ms",
)
async def get_portfolio(client: ExecutionClient) -> MCPToolResult:
    """
    Get portfolio overview.

    Returns current portfolio value, holdings, PnL, and asset allocation breakdown.
    """
    try:
        result = await client.get_portfolio()

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_portfolio",
                "service": "execution-service",
            },
        )
    except Exception as e:
        logger.error(f"Get portfolio failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_portfolio"},
        )


@register_tool(
    name="get_execution_status",
    description="Get execution service health and control status including kill switch state, active orders, and service readiness. Critical for safety monitoring.",
    parameters=[],
    service="execution-service",
    category="execution",
    latency="50-150ms",
)
async def get_execution_status(client: ExecutionClient) -> MCPToolResult:
    """
    Get execution service status.

    Returns service health, kill switch state, active orders count, and system readiness.
    """
    try:
        result = await client.get_execution_status()

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_execution_status",
                "service": "execution-service",
            },
        )
    except Exception as e:
        logger.error(f"Get execution status failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_execution_status"},
        )


# ============================================================================
# Phase 2 - Analytics Service Tools (7 additional tools)
# ============================================================================


@register_tool(
    name="get_analytics_metrics",
    description="Get detailed system metrics for all monitored components. Provides granular metrics beyond the overview.",
    parameters=[],
    service="analytics-service",
    category="analytics",
    latency="100-300ms",
)
async def get_analytics_metrics(client: AnalyticsClient) -> MCPToolResult:
    """Get detailed system metrics."""
    try:
        result = await client.get_metrics()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_analytics_metrics", "service": "analytics-service"},
        )
    except Exception as e:
        logger.error(f"Get analytics metrics failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_analytics_metrics"},
        )


@register_tool(
    name="get_service_analytics",
    description="Get analytics for a specific service. Useful for deep-diving into individual service performance.",
    parameters=[
        MCPToolParameter(
            name="service_name",
            type="string",
            description="Name of the service to analyze (e.g., 'search-service', 'feed-service')",
            required=True,
        ),
    ],
    service="analytics-service",
    category="analytics",
    latency="100-300ms",
)
async def get_service_analytics(client: AnalyticsClient, service_name: str) -> MCPToolResult:
    """Get service-specific analytics."""
    try:
        result = await client.get_service_analytics(service_name=service_name)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_service_analytics", "service": "analytics-service", "target_service": service_name},
        )
    except Exception as e:
        logger.error(f"Get service analytics failed for {service_name}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_service_analytics", "target_service": service_name},
        )


@register_tool(
    name="get_entity_sentiment_history",
    description="Get sentiment timeseries for an entity over time. Tracks daily sentiment changes based on article bias scores. Useful for investment analysis and entity reputation tracking.",
    parameters=[
        MCPToolParameter(
            name="entity",
            type="string",
            description="Entity name to search for (e.g., 'Trump', 'Rheinmetall', 'Tesla'). Case-insensitive partial match.",
            required=True,
        ),
        MCPToolParameter(
            name="days",
            type="integer",
            description="Number of days to look back (default: 30, max: 365)",
            required=False,
        ),
    ],
    service="analytics-service",
    category="intelligence",
    latency="200-500ms",
)
async def get_entity_sentiment_history(
    client: AnalyticsClient,
    entity: str,
    days: int = 30
) -> MCPToolResult:
    """
    Get sentiment timeseries for an entity.

    Returns daily aggregated sentiment with article counts.
    Sentiment ranges from -1 (very negative) to +1 (very positive).
    """
    try:
        result = await client.get_entity_sentiment_history(entity=entity, days=days)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_entity_sentiment_history",
                "service": "analytics-service",
                "entity": entity,
                "days": days,
            },
        )
    except Exception as e:
        logger.error(f"Get entity sentiment history failed for {entity}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_entity_sentiment_history", "entity": entity},
        )


@register_tool(
    name="ask_intelligence",
    description="""Ask an intelligence question and get a concise answer.

Uses RAG (Retrieval-Augmented Generation) to search relevant articles,
aggregate intelligence context, and generate an answer using LLM.

The backend does the heavy lifting - you receive only the answer, not raw data.

Examples:
- "What are the top risks for Defense ETFs?"
- "How has sentiment changed for Rheinmetall this week?"
- "What's driving the current Iran news cluster?"
- "Compare sentiment between Trump and Biden"

Use depth="brief" for quick 2-3 sentence answers.
Use depth="detailed" for comprehensive analysis with evidence.""",
    parameters=[
        MCPToolParameter(
            name="question",
            type="string",
            description="Natural language question (5-500 chars)",
            required=True,
        ),
        MCPToolParameter(
            name="depth",
            type="string",
            description="Response depth: 'brief' (2-3 sentences) or 'detailed' (full analysis)",
            required=False,
            enum=["brief", "detailed"],
        ),
    ],
    service="analytics-service",
    category="intelligence",
    latency="1-3s (includes LLM call)",
)
async def ask_intelligence(
    client: AnalyticsClient,
    question: str,
    depth: str = "brief",
) -> MCPToolResult:
    """Ask an intelligence question via RAG."""
    try:
        result = await client.ask_intelligence(question=question, depth=depth)

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "ask_intelligence",
                "service": "analytics-service",
                "question": question,
                "depth": depth,
            },
        )
    except Exception as e:
        logger.error(f"ask_intelligence tool failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "ask_intelligence", "question": question},
        )


@register_tool(
    name="get_intelligence_context",
    description="""Get raw intelligence context data for Claude to interpret directly.

Unlike ask_intelligence which uses an LLM to generate answers, this tool
returns structured data that you can analyze and interpret yourself.

**PREFERRED for Claude Desktop:** Eliminates redundant LLM call, faster response.

Returns:
- articles: Relevant articles with titles, snippets, sentiment, similarity
- intelligence_summary: Current bursts, momentum trends, contrarian signals
- has_more: Pagination indicator for drill-down

Use this when you want to:
- Analyze raw data and draw your own conclusions
- Drill down iteratively with filters
- Get more articles than the summary provides

Use ask_intelligence when you want:
- Quick pre-interpreted answer (for non-Claude clients)
- Simple yes/no style questions""",
    parameters=[
        MCPToolParameter(
            name="question",
            type="string",
            description="Natural language question (used for semantic search, 3-500 chars)",
            required=True,
        ),
        MCPToolParameter(
            name="limit",
            type="integer",
            description="Maximum articles to return (1-50, default: 10)",
            required=False,
        ),
        MCPToolParameter(
            name="min_similarity",
            type="number",
            description="Minimum similarity threshold (0.0-1.0, default: 0.5)",
            required=False,
        ),
        MCPToolParameter(
            name="entity",
            type="string",
            description="Filter by specific entity name (e.g., 'Rheinmetall', 'Trump')",
            required=False,
        ),
        MCPToolParameter(
            name="sector",
            type="string",
            description="Filter by sector (e.g., 'Defense', 'Technology')",
            required=False,
        ),
        MCPToolParameter(
            name="days",
            type="integer",
            description="Time window in days (1-90, default: 7)",
            required=False,
        ),
    ],
    service="analytics-service",
    category="intelligence",
    latency="200-800ms (no LLM call)",
)
async def get_intelligence_context(
    client: AnalyticsClient,
    question: str,
    limit: int = 10,
    min_similarity: float = 0.5,
    entity: Optional[str] = None,
    sector: Optional[str] = None,
    days: int = 7,
) -> MCPToolResult:
    """Get intelligence context data for Claude interpretation."""
    try:
        result = await client.get_intelligence_context(
            question=question,
            limit=limit,
            min_similarity=min_similarity,
            entity=entity,
            sector=sector,
            days=days,
        )

        return MCPToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "get_intelligence_context",
                "service": "analytics-service",
                "question": question,
                "limit": limit,
            },
        )
    except Exception as e:
        logger.error(f"get_intelligence_context failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_intelligence_context", "question": question},
        )


@register_tool(
    name="get_cache_stats",
    description="Get cache performance statistics including hit rates, memory usage, and cache efficiency metrics.",
    parameters=[],
    service="analytics-service",
    category="monitoring",
    latency="50-150ms",
)
async def get_cache_stats(client: AnalyticsClient) -> MCPToolResult:
    """Get cache performance statistics."""
    try:
        result = await client.get_cache_stats()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_cache_stats", "service": "analytics-service"},
        )
    except Exception as e:
        logger.error(f"Get cache stats failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_cache_stats"},
        )


@register_tool(
    name="get_health_summary",
    description="Get overall system health summary with component statuses. Quick health check for entire system.",
    parameters=[],
    service="analytics-service",
    category="monitoring",
    latency="50-150ms",
)
async def get_health_summary(client: AnalyticsClient) -> MCPToolResult:
    """Get system health summary."""
    try:
        result = await client.get_health_summary()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_health_summary", "service": "analytics-service"},
        )
    except Exception as e:
        logger.error(f"Get health summary failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_health_summary"},
        )


@register_tool(
    name="get_health_containers",
    description="Get Docker container health status for all running containers. Essential for infrastructure monitoring.",
    parameters=[],
    service="analytics-service",
    category="monitoring",
    latency="100-200ms",
)
async def get_health_containers(client: AnalyticsClient) -> MCPToolResult:
    """Get container health status."""
    try:
        result = await client.get_health_containers()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_health_containers", "service": "analytics-service"},
        )
    except Exception as e:
        logger.error(f"Get container health failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_health_containers"},
        )


@register_tool(
    name="list_dashboards",
    description="List all available analytics dashboards. Returns dashboard definitions and metadata.",
    parameters=[],
    service="analytics-service",
    category="analytics",
    latency="50-150ms",
)
async def list_dashboards(client: AnalyticsClient) -> MCPToolResult:
    """List all dashboards."""
    try:
        result = await client.list_dashboards()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "list_dashboards", "service": "analytics-service"},
        )
    except Exception as e:
        logger.error(f"List dashboards failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "list_dashboards"},
        )


@register_tool(
    name="get_dashboard_data",
    description="Get data for a specific dashboard including all widgets and visualizations.",
    parameters=[
        MCPToolParameter(
            name="dashboard_id",
            type="string",
            description="Dashboard identifier",
            required=True,
        ),
    ],
    service="analytics-service",
    category="analytics",
    latency="100-500ms",
)
async def get_dashboard_data(client: AnalyticsClient, dashboard_id: str) -> MCPToolResult:
    """Get dashboard data."""
    try:
        result = await client.get_dashboard_data(dashboard_id=dashboard_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_dashboard_data", "service": "analytics-service", "dashboard_id": dashboard_id},
        )
    except Exception as e:
        logger.error(f"Get dashboard data failed for {dashboard_id}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_dashboard_data", "dashboard_id": dashboard_id},
        )


# ============================================================================
# Phase 2 - Prediction Service Tools (9 additional tools)
# ============================================================================


@register_tool(
    name="get_model_performance",
    description="Get performance metrics for a specific ML model including accuracy, precision, recall, and F1 score.",
    parameters=[
        MCPToolParameter(
            name="model_name",
            type="string",
            description="Name of the ML model to analyze",
            required=True,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-300ms",
)
async def get_model_performance(client: PredictionClient, model_name: str) -> MCPToolResult:
    """Get model performance metrics."""
    try:
        result = await client.get_model_performance(model_name=model_name)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_model_performance", "service": "prediction-service", "model_name": model_name},
        )
    except Exception as e:
        logger.error(f"Get model performance failed for {model_name}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_model_performance", "model_name": model_name},
        )


@register_tool(
    name="get_model_drift",
    description="Detect model drift and performance degradation over time. Critical for ML model monitoring.",
    parameters=[
        MCPToolParameter(
            name="model_name",
            type="string",
            description="Name of the ML model to check for drift",
            required=True,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-500ms",
)
async def get_model_drift(client: PredictionClient, model_name: str) -> MCPToolResult:
    """Get model drift analysis."""
    try:
        result = await client.get_model_drift(model_name=model_name)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_model_drift", "service": "prediction-service", "model_name": model_name},
        )
    except Exception as e:
        logger.error(f"Get model drift failed for {model_name}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_model_drift", "model_name": model_name},
        )


@register_tool(
    name="get_consensus_alerts",
    description="Get consensus alerts when multiple ML models agree on predictions. High confidence signals.",
    parameters=[],
    service="prediction-service",
    category="prediction",
    latency="100-300ms",
)
async def get_consensus_alerts(client: PredictionClient) -> MCPToolResult:
    """Get consensus alerts from multiple models."""
    try:
        result = await client.get_consensus_alerts()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_consensus_alerts", "service": "prediction-service"},
        )
    except Exception as e:
        logger.error(f"Get consensus alerts failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_consensus_alerts"},
        )


@register_tool(
    name="get_regime_analysis",
    description="Get market regime analysis (trending, ranging, volatile). Essential for adaptive strategies.",
    parameters=[],
    service="prediction-service",
    category="prediction",
    latency="100-400ms",
)
async def get_regime_analysis(client: PredictionClient) -> MCPToolResult:
    """Get market regime analysis."""
    try:
        result = await client.get_regime_analysis()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_regime_analysis", "service": "prediction-service"},
        )
    except Exception as e:
        logger.error(f"Get regime analysis failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_regime_analysis"},
        )


@register_tool(
    name="get_backtest_results",
    description="Get backtest results for trading strategies with performance metrics and statistics.",
    parameters=[
        MCPToolParameter(
            name="backtest_id",
            type="string",
            description="Backtest ID (optional, returns list if not provided)",
            required=False,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-500ms",
)
async def get_backtest_results(client: PredictionClient, backtest_id: Optional[str] = None) -> MCPToolResult:
    """Get backtest results."""
    try:
        result = await client.get_backtest_results(backtest_id=backtest_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_backtest_results", "service": "prediction-service", "backtest_id": backtest_id},
        )
    except Exception as e:
        logger.error(f"Get backtest results failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_backtest_results", "backtest_id": backtest_id},
        )


@register_tool(
    name="get_order_flow_data",
    description="Get order flow analysis data (CVD, Delta, Zones). Advanced market microstructure analysis.",
    parameters=[
        MCPToolParameter(
            name="symbol",
            type="string",
            description="Trading symbol (e.g., 'BTCUSD', 'ETHUSD')",
            required=True,
        ),
        MCPToolParameter(
            name="data_type",
            type="string",
            description="Order flow data type: 'cvd' (cumulative volume delta), 'delta', or 'zones'",
            required=False,
            enum=["cvd", "delta", "zones"],
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-500ms",
)
async def get_order_flow_data(client: PredictionClient, symbol: str, data_type: str = "cvd") -> MCPToolResult:
    """Get order flow analysis data."""
    try:
        result = await client.get_order_flow_data(symbol=symbol, data_type=data_type)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_order_flow_data", "service": "prediction-service", "symbol": symbol, "data_type": data_type},
        )
    except Exception as e:
        logger.error(f"Get order flow data failed for {symbol}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_order_flow_data", "symbol": symbol},
        )


@register_tool(
    name="optimize_portfolio",
    description="Optimize portfolio allocation using modern portfolio theory. Returns optimal weights with expected returns and risk.",
    parameters=[
        MCPToolParameter(
            name="symbols",
            type="array",
            description="List of trading symbols to include in portfolio",
            required=True,
        ),
        MCPToolParameter(
            name="constraints",
            type="object",
            description="Optional constraints (max_weight, min_weight, target_return, etc.)",
            required=False,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="500-2000ms",
)
async def optimize_portfolio(client: PredictionClient, symbols: list, constraints: Optional[Dict[str, Any]] = None) -> MCPToolResult:
    """Optimize portfolio allocation."""
    try:
        result = await client.optimize_portfolio(symbols=symbols, constraints=constraints)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "optimize_portfolio", "service": "prediction-service", "symbols": symbols},
        )
    except Exception as e:
        logger.error(f"Portfolio optimization failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "optimize_portfolio", "symbols": symbols},
        )


@register_tool(
    name="list_strategies",
    description="List all available trading strategies with descriptions and parameters.",
    parameters=[],
    service="prediction-service",
    category="prediction",
    latency="50-200ms",
)
async def list_strategies(client: PredictionClient) -> MCPToolResult:
    """List all trading strategies."""
    try:
        result = await client.list_strategies()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "list_strategies", "service": "prediction-service"},
        )
    except Exception as e:
        logger.error(f"List strategies failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "list_strategies"},
        )


@register_tool(
    name="validate_strategy",
    description="Validate a trading strategy configuration. Checks parameters, logic, and potential issues.",
    parameters=[
        MCPToolParameter(
            name="strategy_id",
            type="string",
            description="Strategy identifier to validate",
            required=True,
        ),
    ],
    service="prediction-service",
    category="prediction",
    latency="100-500ms",
)
async def validate_strategy(client: PredictionClient, strategy_id: str) -> MCPToolResult:
    """Validate trading strategy."""
    try:
        result = await client.validate_strategy(strategy_id=strategy_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "validate_strategy", "service": "prediction-service", "strategy_id": strategy_id},
        )
    except Exception as e:
        logger.error(f"Validate strategy failed for {strategy_id}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "validate_strategy", "strategy_id": strategy_id},
        )


# ============================================================================
# Phase 2 - Execution Service Tools (4 additional tools)
# ============================================================================


@register_tool(
    name="get_portfolio_performance",
    description="Get detailed portfolio performance metrics including returns, volatility, Sharpe ratio, and drawdowns.",
    parameters=[],
    service="execution-service",
    category="execution",
    latency="100-300ms",
)
async def get_portfolio_performance(client: ExecutionClient) -> MCPToolResult:
    """Get portfolio performance metrics."""
    try:
        result = await client.get_portfolio_performance()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_portfolio_performance", "service": "execution-service"},
        )
    except Exception as e:
        logger.error(f"Get portfolio performance failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_portfolio_performance"},
        )


@register_tool(
    name="close_position",
    description="Close a specific trading position. Returns final PnL and execution details. Use with caution.",
    parameters=[
        MCPToolParameter(
            name="position_id",
            type="string",
            description="Position identifier to close",
            required=True,
        ),
    ],
    service="execution-service",
    category="execution",
    latency="200-1000ms",
)
async def close_position(client: ExecutionClient, position_id: str) -> MCPToolResult:
    """Close a trading position."""
    try:
        result = await client.close_position(position_id=position_id)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "close_position", "service": "execution-service", "position_id": position_id},
        )
    except Exception as e:
        logger.error(f"Close position failed for {position_id}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "close_position", "position_id": position_id},
        )


@register_tool(
    name="control_autotrade",
    description="Control auto-trading system (start, stop, status). Critical safety control for automated trading.",
    parameters=[
        MCPToolParameter(
            name="action",
            type="string",
            description="Action to perform: 'start', 'stop', or 'status'",
            required=True,
            enum=["start", "stop", "status"],
        ),
    ],
    service="execution-service",
    category="execution",
    latency="100-500ms",
)
async def control_autotrade(client: ExecutionClient, action: str) -> MCPToolResult:
    """Control auto-trading system."""
    try:
        result = await client.control_autotrade(action=action)
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "control_autotrade", "service": "execution-service", "action": action},
        )
    except Exception as e:
        logger.error(f"Control autotrade failed for action {action}: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "control_autotrade", "action": action},
        )


@register_tool(
    name="get_strategy_analytics",
    description="Get analytics for all active trading strategies including performance, win rate, and risk metrics.",
    parameters=[],
    service="execution-service",
    category="execution",
    latency="100-300ms",
)
async def get_strategy_analytics(client: ExecutionClient) -> MCPToolResult:
    """Get strategy analytics."""
    try:
        result = await client.get_strategy_analytics()
        return MCPToolResult(
            success=True,
            data=result,
            metadata={"tool": "get_strategy_analytics", "service": "execution-service"},
        )
    except Exception as e:
        logger.error(f"Get strategy analytics failed: {e}")
        return MCPToolResult(
            success=False,
            error=str(e),
            metadata={"tool": "get_strategy_analytics"},
        )

"""MCP Tools for Auth and Analytics services."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..models import MCPToolDefinition, MCPToolResult
from ..clients import AuthClient, AnalyticsClient
from ..metrics import TOOL_CALLS_TOTAL, TOOL_CALL_DURATION

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        self.tools: Dict[str, MCPToolDefinition] = {}
        self.handlers: Dict[str, Callable] = {}
        self.auth_client: Optional[AuthClient] = None
        self.analytics_client: Optional[AnalyticsClient] = None

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
        self.auth_client = AuthClient()
        self.analytics_client = AnalyticsClient()

    async def close_clients(self):
        """Close backend service clients."""
        if self.auth_client:
            await self.auth_client.close()
        if self.analytics_client:
            await self.analytics_client.close()


# Global tool registry instance
tool_registry = MCPToolRegistry()


# =============================================================================
# Auth Service Tools
# =============================================================================

@tool_registry.register(
    name="auth_login",
    description="Authenticate user with username and password. Returns JWT access and refresh tokens.",
    input_schema={
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "Username"},
            "password": {"type": "string", "description": "Password"},
        },
        "required": ["username", "password"],
    },
    category="auth",
)
async def auth_login(
    registry: MCPToolRegistry,
    username: str,
    password: str,
) -> Dict[str, Any]:
    """Authenticate user and get tokens."""
    return await registry.auth_client.login(username, password)


@tool_registry.register(
    name="auth_refresh_token",
    description="Refresh access token using refresh token.",
    input_schema={
        "type": "object",
        "properties": {
            "refresh_token": {"type": "string", "description": "Refresh token"},
        },
        "required": ["refresh_token"],
    },
    category="auth",
)
async def auth_refresh_token(
    registry: MCPToolRegistry,
    refresh_token: str,
) -> Dict[str, Any]:
    """Refresh access token."""
    return await registry.auth_client.refresh_token(refresh_token)


@tool_registry.register(
    name="auth_logout",
    description="Logout user and invalidate tokens.",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Access token"},
        },
        "required": ["access_token"],
    },
    category="auth",
)
async def auth_logout(
    registry: MCPToolRegistry,
    access_token: str,
) -> Dict[str, Any]:
    """Logout user."""
    return await registry.auth_client.logout(access_token)


@tool_registry.register(
    name="auth_get_current_user",
    description="Get current authenticated user profile.",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Access token"},
        },
        "required": ["access_token"],
    },
    category="auth",
)
async def auth_get_current_user(
    registry: MCPToolRegistry,
    access_token: str,
) -> Dict[str, Any]:
    """Get current user."""
    return await registry.auth_client.get_current_user(access_token)


@tool_registry.register(
    name="auth_get_stats",
    description="Get authentication statistics (admin only).",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Admin access token"},
        },
        "required": ["access_token"],
    },
    category="auth",
)
async def auth_get_stats(
    registry: MCPToolRegistry,
    access_token: str,
) -> Dict[str, Any]:
    """Get auth stats."""
    return await registry.auth_client.get_auth_stats(access_token)


@tool_registry.register(
    name="auth_list_api_keys",
    description="List user's API keys.",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Access token"},
        },
        "required": ["access_token"],
    },
    category="auth",
)
async def auth_list_api_keys(
    registry: MCPToolRegistry,
    access_token: str,
) -> Dict[str, Any]:
    """List API keys."""
    return await registry.auth_client.list_api_keys(access_token)


@tool_registry.register(
    name="auth_create_api_key",
    description="Create a new API key for programmatic access.",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Access token"},
            "name": {"type": "string", "description": "Key name/description"},
            "expires_in_days": {"type": "integer", "description": "Days until expiration (optional)"},
        },
        "required": ["access_token", "name"],
    },
    category="auth",
)
async def auth_create_api_key(
    registry: MCPToolRegistry,
    access_token: str,
    name: str,
    expires_in_days: Optional[int] = None,
) -> Dict[str, Any]:
    """Create API key."""
    return await registry.auth_client.create_api_key(access_token, name, expires_in_days)


@tool_registry.register(
    name="auth_delete_api_key",
    description="Delete an API key.",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Access token"},
            "key_id": {"type": "string", "description": "API key ID to delete"},
        },
        "required": ["access_token", "key_id"],
    },
    category="auth",
)
async def auth_delete_api_key(
    registry: MCPToolRegistry,
    access_token: str,
    key_id: str,
) -> Dict[str, Any]:
    """Delete API key."""
    return await registry.auth_client.delete_api_key(access_token, key_id)


@tool_registry.register(
    name="auth_list_users",
    description="List all users (admin only).",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Admin access token"},
            "skip": {"type": "integer", "description": "Number to skip", "default": 0},
            "limit": {"type": "integer", "description": "Max to return", "default": 100},
        },
        "required": ["access_token"],
    },
    category="auth",
)
async def auth_list_users(
    registry: MCPToolRegistry,
    access_token: str,
    skip: int = 0,
    limit: int = 100,
) -> Dict[str, Any]:
    """List users."""
    return await registry.auth_client.list_users(access_token, skip, limit)


@tool_registry.register(
    name="auth_get_user",
    description="Get user by ID (admin only).",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Admin access token"},
            "user_id": {"type": "integer", "description": "User ID"},
        },
        "required": ["access_token", "user_id"],
    },
    category="auth",
)
async def auth_get_user(
    registry: MCPToolRegistry,
    access_token: str,
    user_id: int,
) -> Dict[str, Any]:
    """Get user by ID."""
    return await registry.auth_client.get_user(access_token, user_id)


@tool_registry.register(
    name="auth_register",
    description="Register a new user account. Creates user with username, password, and email.",
    input_schema={
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "Username for the new account"},
            "password": {"type": "string", "description": "Password (will be hashed)"},
            "email": {"type": "string", "description": "User's email address"},
            "roles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional roles (defaults to ['user'])",
            },
        },
        "required": ["username", "password", "email"],
    },
    category="auth",
)
async def auth_register(
    registry: MCPToolRegistry,
    username: str,
    password: str,
    email: str,
    roles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Register new user."""
    return await registry.auth_client.register(username, password, email, roles)


@tool_registry.register(
    name="auth_update_user",
    description="Update user profile (admin only). Only provided fields will be updated.",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Admin access token"},
            "user_id": {"type": "integer", "description": "User ID to update"},
            "username": {"type": "string", "description": "New username (optional)"},
            "email": {"type": "string", "description": "New email (optional)"},
            "roles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "New roles (optional)",
            },
            "is_active": {"type": "boolean", "description": "Active status (optional)"},
        },
        "required": ["access_token", "user_id"],
    },
    category="auth",
)
async def auth_update_user(
    registry: MCPToolRegistry,
    access_token: str,
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    roles: Optional[List[str]] = None,
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update user."""
    return await registry.auth_client.update_user(
        access_token, user_id, username, email, roles, is_active
    )


@tool_registry.register(
    name="auth_delete_user",
    description="Delete user account (admin only). This action cannot be undone.",
    input_schema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Admin access token"},
            "user_id": {"type": "integer", "description": "User ID to delete"},
        },
        "required": ["access_token", "user_id"],
    },
    category="auth",
)
async def auth_delete_user(
    registry: MCPToolRegistry,
    access_token: str,
    user_id: int,
) -> Dict[str, Any]:
    """Delete user."""
    return await registry.auth_client.delete_user(access_token, user_id)


# =============================================================================
# Analytics Service Tools
# =============================================================================

@tool_registry.register(
    name="analytics_get_overview",
    description="Get system-wide analytics overview with aggregated metrics.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="analytics",
)
async def analytics_get_overview(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get analytics overview."""
    return await registry.analytics_client.get_overview()


@tool_registry.register(
    name="analytics_get_metrics",
    description="Get specific metrics by name and time range.",
    input_schema={
        "type": "object",
        "properties": {
            "metric_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of metric names",
            },
            "time_range": {
                "type": "string",
                "enum": ["1h", "24h", "7d", "30d"],
                "description": "Time range",
                "default": "1h",
            },
        },
    },
    category="analytics",
)
async def analytics_get_metrics(
    registry: MCPToolRegistry,
    metric_names: Optional[List[str]] = None,
    time_range: str = "1h",
) -> Dict[str, Any]:
    """Get metrics."""
    return await registry.analytics_client.get_metrics(metric_names, time_range)


@tool_registry.register(
    name="analytics_get_service",
    description="Get analytics for a specific service.",
    input_schema={
        "type": "object",
        "properties": {
            "service_name": {"type": "string", "description": "Service name"},
        },
        "required": ["service_name"],
    },
    category="analytics",
)
async def analytics_get_service(
    registry: MCPToolRegistry,
    service_name: str,
) -> Dict[str, Any]:
    """Get service analytics."""
    return await registry.analytics_client.get_service_analytics(service_name)


@tool_registry.register(
    name="analytics_get_trends",
    description="Get trend data for metrics over time.",
    input_schema={
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "enum": ["requests", "errors", "latency"],
                "description": "Metric to analyze",
                "default": "requests",
            },
            "period": {
                "type": "string",
                "enum": ["1h", "24h", "7d", "30d"],
                "description": "Time period",
                "default": "24h",
            },
        },
    },
    category="analytics",
)
async def analytics_get_trends(
    registry: MCPToolRegistry,
    metric: str = "requests",
    period: str = "24h",
) -> Dict[str, Any]:
    """Get trends."""
    return await registry.analytics_client.get_trends(metric, period)


@tool_registry.register(
    name="health_get_summary",
    description="Get system health summary across all services.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="health",
)
async def health_get_summary(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get health summary."""
    return await registry.analytics_client.get_health_summary()


@tool_registry.register(
    name="health_get_containers",
    description="Get Docker container health status.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="health",
)
async def health_get_containers(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get container health."""
    return await registry.analytics_client.get_container_health()


@tool_registry.register(
    name="health_get_alerts",
    description="Get active health alerts.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="health",
)
async def health_get_alerts(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get alerts."""
    return await registry.analytics_client.get_health_alerts()


@tool_registry.register(
    name="monitoring_get_circuit_breakers",
    description="Get circuit breaker status for all services.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="monitoring",
)
async def monitoring_get_circuit_breakers(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get circuit breakers."""
    return await registry.analytics_client.get_circuit_breaker_status()


@tool_registry.register(
    name="monitoring_get_health",
    description="Get monitoring system health.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="monitoring",
)
async def monitoring_get_health(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get monitoring health."""
    return await registry.analytics_client.get_monitoring_health()


@tool_registry.register(
    name="monitoring_get_query_performance",
    description="Get database query performance metrics.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="monitoring",
)
async def monitoring_get_query_performance(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get query performance."""
    return await registry.analytics_client.get_query_performance()


@tool_registry.register(
    name="cache_get_stats",
    description="Get cache statistics.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="cache",
)
async def cache_get_stats(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get cache stats."""
    return await registry.analytics_client.get_cache_stats()


@tool_registry.register(
    name="cache_get_health",
    description="Get cache health status.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="cache",
)
async def cache_get_health(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get cache health."""
    return await registry.analytics_client.get_cache_health()


@tool_registry.register(
    name="cache_clear",
    description="Clear cache (optionally by key pattern).",
    input_schema={
        "type": "object",
        "properties": {
            "cache_key": {"type": "string", "description": "Optional key pattern to clear"},
        },
    },
    category="cache",
)
async def cache_clear(
    registry: MCPToolRegistry,
    cache_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Clear cache."""
    return await registry.analytics_client.clear_cache(cache_key)


@tool_registry.register(
    name="dashboards_list",
    description="List available dashboards.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="dashboards",
)
async def dashboards_list(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """List dashboards."""
    return await registry.analytics_client.list_dashboards()


@tool_registry.register(
    name="dashboards_get",
    description="Get dashboard configuration by ID.",
    input_schema={
        "type": "object",
        "properties": {
            "dashboard_id": {"type": "string", "description": "Dashboard ID"},
        },
        "required": ["dashboard_id"],
    },
    category="dashboards",
)
async def dashboards_get(
    registry: MCPToolRegistry,
    dashboard_id: str,
) -> Dict[str, Any]:
    """Get dashboard."""
    return await registry.analytics_client.get_dashboard(dashboard_id)


@tool_registry.register(
    name="dashboards_get_data",
    description="Get dashboard data by ID.",
    input_schema={
        "type": "object",
        "properties": {
            "dashboard_id": {"type": "string", "description": "Dashboard ID"},
        },
        "required": ["dashboard_id"],
    },
    category="dashboards",
)
async def dashboards_get_data(
    registry: MCPToolRegistry,
    dashboard_id: str,
) -> Dict[str, Any]:
    """Get dashboard data."""
    return await registry.analytics_client.get_dashboard_data(dashboard_id)


@tool_registry.register(
    name="reports_list",
    description="List available reports.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="reports",
)
async def reports_list(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """List reports."""
    return await registry.analytics_client.list_reports()


@tool_registry.register(
    name="reports_get",
    description="Get report details by ID.",
    input_schema={
        "type": "object",
        "properties": {
            "report_id": {"type": "string", "description": "Report ID"},
        },
        "required": ["report_id"],
    },
    category="reports",
)
async def reports_get(
    registry: MCPToolRegistry,
    report_id: str,
) -> Dict[str, Any]:
    """Get report."""
    return await registry.analytics_client.get_report(report_id)


# =============================================================================
# Dashboard & Report Management Tools (CRUD)
# =============================================================================

@tool_registry.register(
    name="dashboards_create",
    description="Create a new analytics dashboard. Dashboards contain widgets for visualizing metrics.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Dashboard name"},
            "description": {"type": "string", "description": "Dashboard description"},
            "widgets": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of widget configurations",
            },
            "layout": {
                "type": "object",
                "description": "Dashboard layout configuration",
            },
        },
        "required": ["name"],
    },
    category="dashboards",
)
async def dashboards_create(
    registry: MCPToolRegistry,
    name: str,
    description: Optional[str] = None,
    widgets: Optional[List[Dict[str, Any]]] = None,
    layout: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create dashboard."""
    return await registry.analytics_client.create_dashboard(
        name=name,
        description=description,
        widgets=widgets,
        layout=layout,
    )


@tool_registry.register(
    name="dashboards_update",
    description="Update an existing dashboard. Only provided fields will be updated.",
    input_schema={
        "type": "object",
        "properties": {
            "dashboard_id": {"type": "string", "description": "Dashboard ID to update"},
            "name": {"type": "string", "description": "New dashboard name"},
            "description": {"type": "string", "description": "New description"},
            "widgets": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Updated widget configurations",
            },
            "layout": {
                "type": "object",
                "description": "Updated layout configuration",
            },
        },
        "required": ["dashboard_id"],
    },
    category="dashboards",
)
async def dashboards_update(
    registry: MCPToolRegistry,
    dashboard_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    widgets: Optional[List[Dict[str, Any]]] = None,
    layout: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update dashboard."""
    return await registry.analytics_client.update_dashboard(
        dashboard_id=dashboard_id,
        name=name,
        description=description,
        widgets=widgets,
        layout=layout,
    )


@tool_registry.register(
    name="dashboards_delete",
    description="Delete a dashboard. This action cannot be undone.",
    input_schema={
        "type": "object",
        "properties": {
            "dashboard_id": {"type": "string", "description": "Dashboard ID to delete"},
        },
        "required": ["dashboard_id"],
    },
    category="dashboards",
)
async def dashboards_delete(
    registry: MCPToolRegistry,
    dashboard_id: str,
) -> Dict[str, Any]:
    """Delete dashboard."""
    return await registry.analytics_client.delete_dashboard(dashboard_id)


@tool_registry.register(
    name="reports_create",
    description="Create/generate a new analytics report. Reports can be one-time or scheduled.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Report name"},
            "report_type": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly", "custom"],
                "description": "Type of report",
            },
            "parameters": {
                "type": "object",
                "description": "Report parameters (filters, metrics, date range, etc.)",
            },
            "schedule": {
                "type": "string",
                "description": "Cron schedule for recurring reports (optional)",
            },
        },
        "required": ["name", "report_type"],
    },
    category="reports",
)
async def reports_create(
    registry: MCPToolRegistry,
    name: str,
    report_type: str,
    parameters: Optional[Dict[str, Any]] = None,
    schedule: Optional[str] = None,
) -> Dict[str, Any]:
    """Create report."""
    return await registry.analytics_client.create_report(
        name=name,
        report_type=report_type,
        parameters=parameters,
        schedule=schedule,
    )


@tool_registry.register(
    name="reports_delete",
    description="Delete a report. This action cannot be undone.",
    input_schema={
        "type": "object",
        "properties": {
            "report_id": {"type": "string", "description": "Report ID to delete"},
        },
        "required": ["report_id"],
    },
    category="reports",
)
async def reports_delete(
    registry: MCPToolRegistry,
    report_id: str,
) -> Dict[str, Any]:
    """Delete report."""
    return await registry.analytics_client.delete_report(report_id)


# =============================================================================
# Discovery & Help Tools (For LLM Orientation)
# =============================================================================

SYSTEM_CONTEXT = {
    "system_name": "News Intelligence Platform",
    "description": "Comprehensive news monitoring, AI analysis, and financial data platform",
    "primary_user": "andreas",
    "servers": {
        "core": {"port": 9006, "purpose": "Auth, Analytics, Dashboards, Reports"},
        "search": {"port": 9002, "purpose": "Article Search, Feeds, Research"},
        "integration": {"port": 9005, "purpose": "Market Data, Notifications"},
        "intelligence": {"port": 9001, "purpose": "OSINT, Entities, Narratives"},
        "analytics": {"port": 9003, "purpose": "Metrics, Predictions, Execution"},
        "content": {"port": 9007, "purpose": "Feed CRUD, Quality Assessment"},
        "orchestration": {"port": 9008, "purpose": "Scheduler, Jobs"},
    },
    "quick_start": {
        "search_news": "search_articles(query='topic')",
        "get_quote": "get_market_quote(symbol='AAPL')",
        "research": "research_query(query='question')",
        "analyze": "analyze_article(article_id=123)",
        "notify": "send_notification(user_id=11, type='email', subject='...', message='...')",
    },
}

USE_CASE_GUIDES = {
    "search": {
        "description": "Find articles and news",
        "tools": ["search_articles", "advanced_search", "get_search_suggestions", "get_popular_searches"],
        "example": "search_articles(query='AI regulation', page=1, page_size=20)",
    },
    "feeds": {
        "description": "Manage news sources",
        "tools": ["feeds_list", "feeds_create", "feeds_fetch", "quality_assess"],
        "example": "feeds_list() then feeds_create(url='...', name='...')",
    },
    "research": {
        "description": "AI-powered research with citations",
        "tools": ["research_query", "create_research_task", "list_research_templates"],
        "example": "research_query(query='Current state of quantum computing')",
    },
    "market_data": {
        "description": "Financial market information",
        "tools": ["get_market_quote", "get_ohlcv_candles", "get_financial_news", "get_earnings_calendar"],
        "example": "get_market_quote(symbol='TSLA')",
    },
    "intelligence": {
        "description": "Deep analysis and patterns",
        "tools": ["analyze_article", "extract_entities", "detect_intelligence_patterns", "get_narrative_overview"],
        "example": "analyze_article(article_id=123)",
    },
    "predictions": {
        "description": "Trading signals and forecasts",
        "tools": ["get_predictions", "get_signals", "get_indicators", "optimize_portfolio"],
        "example": "get_predictions(symbol='BTC')",
    },
    "notifications": {
        "description": "Alert user",
        "tools": ["send_notification", "send_adhoc_notification", "test_notification"],
        "example": "send_notification(user_id=11, type='email', subject='Alert', message='...')",
    },
    "monitoring": {
        "description": "System health and status",
        "tools": ["health_get_summary", "get_circuit_breaker_status", "scheduler_status", "analytics_get_overview"],
        "example": "health_get_summary()",
    },
}


@tool_registry.register(
    name="system_get_context",
    description="Get system context and overview. Call this FIRST when connecting to understand the available capabilities. Returns system description, server architecture, and quick-start examples.",
    input_schema={
        "type": "object",
        "properties": {},
    },
    category="discovery",
)
async def system_get_context(
    registry: MCPToolRegistry,
) -> Dict[str, Any]:
    """Get system context for LLM orientation."""
    return {
        "success": True,
        "data": SYSTEM_CONTEXT,
        "message": "Welcome to the News Intelligence Platform. Use 'discover_tools' to find tools by use case.",
    }


@tool_registry.register(
    name="discover_tools",
    description="Discover tools by use case. Helps find the right tools for specific tasks. Categories: search, feeds, research, market_data, intelligence, predictions, notifications, monitoring.",
    input_schema={
        "type": "object",
        "properties": {
            "use_case": {
                "type": "string",
                "description": "Use case category (search, feeds, research, market_data, intelligence, predictions, notifications, monitoring)",
                "enum": ["search", "feeds", "research", "market_data", "intelligence", "predictions", "notifications", "monitoring"],
            },
        },
    },
    category="discovery",
)
async def discover_tools(
    registry: MCPToolRegistry,
    use_case: Optional[str] = None,
) -> Dict[str, Any]:
    """Discover tools by use case."""
    if use_case:
        if use_case in USE_CASE_GUIDES:
            return {
                "success": True,
                "data": {
                    "use_case": use_case,
                    **USE_CASE_GUIDES[use_case],
                },
            }
        else:
            return {
                "success": False,
                "error": f"Unknown use case: {use_case}",
                "available": list(USE_CASE_GUIDES.keys()),
            }
    else:
        return {
            "success": True,
            "data": {
                "available_use_cases": {
                    name: guide["description"]
                    for name, guide in USE_CASE_GUIDES.items()
                },
                "hint": "Call discover_tools(use_case='category') for detailed guidance",
            },
        }


@tool_registry.register(
    name="get_tool_help",
    description="Get detailed help for a specific tool or category. Shows parameters, examples, and related tools.",
    input_schema={
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name of the tool to get help for (optional)",
            },
            "category": {
                "type": "string",
                "description": "Category to list tools from (optional)",
            },
        },
    },
    category="discovery",
)
async def get_tool_help(
    registry: MCPToolRegistry,
    tool_name: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Get help for tools."""
    if tool_name:
        if tool_name in registry.tools:
            tool = registry.tools[tool_name]
            return {
                "success": True,
                "data": {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "parameters": tool.input_schema.get("properties", {}),
                    "required": tool.input_schema.get("required", []),
                },
            }
        else:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "hint": "Use get_tool_help(category='...') to list tools by category",
            }
    elif category:
        tools_in_category = [
            {"name": t.name, "description": t.description}
            for t in registry.tools.values()
            if t.category == category
        ]
        return {
            "success": True,
            "data": {
                "category": category,
                "tools": tools_in_category,
                "count": len(tools_in_category),
            },
        }
    else:
        # List all categories
        categories = {}
        for tool in registry.tools.values():
            if tool.category not in categories:
                categories[tool.category] = 0
            categories[tool.category] += 1
        return {
            "success": True,
            "data": {
                "categories": categories,
                "total_tools": len(registry.tools),
                "hint": "Use get_tool_help(category='...') or get_tool_help(tool_name='...')",
            },
        }


@tool_registry.register(
    name="suggest_workflow",
    description="Get suggested workflow for a task. Describes step-by-step tool usage for common scenarios.",
    input_schema={
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Task description (e.g., 'research a topic', 'monitor market', 'add new feed')",
                "enum": ["research_topic", "monitor_market", "add_feed", "analyze_content", "system_health"],
            },
        },
        "required": ["task"],
    },
    category="discovery",
)
async def suggest_workflow(
    registry: MCPToolRegistry,
    task: str,
) -> Dict[str, Any]:
    """Suggest workflow for common tasks."""
    workflows = {
        "research_topic": {
            "description": "Research a topic with AI assistance",
            "steps": [
                {"step": 1, "action": "search_articles(query='topic')", "purpose": "Find existing articles"},
                {"step": 2, "action": "research_query(query='detailed question')", "purpose": "AI research with citations"},
                {"step": 3, "action": "extract_entities(text='...')", "purpose": "Extract key entities"},
                {"step": 4, "action": "send_notification(...)", "purpose": "Notify user of results"},
            ],
        },
        "monitor_market": {
            "description": "Monitor a stock or market",
            "steps": [
                {"step": 1, "action": "get_market_quote(symbol='...')", "purpose": "Get current price"},
                {"step": 2, "action": "get_ohlcv_candles(symbol='...', interval='1h')", "purpose": "Get price history"},
                {"step": 3, "action": "get_financial_news(symbols=['...'])", "purpose": "Related news"},
                {"step": 4, "action": "get_predictions(symbol='...')", "purpose": "Price predictions"},
                {"step": 5, "action": "get_signals(symbol='...')", "purpose": "Trading signals"},
            ],
        },
        "add_feed": {
            "description": "Add and assess a new news feed",
            "steps": [
                {"step": 1, "action": "quality_pre_assess(feed_url='...')", "purpose": "Preview quality before adding"},
                {"step": 2, "action": "feeds_create(url='...', name='...')", "purpose": "Add the feed"},
                {"step": 3, "action": "feeds_fetch(feed_id=...)", "purpose": "Initial fetch"},
                {"step": 4, "action": "quality_assess(feed_id=...)", "purpose": "Full AI assessment"},
            ],
        },
        "analyze_content": {
            "description": "Analyze article content",
            "steps": [
                {"step": 1, "action": "analyze_article(article_id=...)", "purpose": "Full AI analysis"},
                {"step": 2, "action": "extract_entities(text='...')", "purpose": "Extract entities"},
                {"step": 3, "action": "canonicalize_entity(name='...')", "purpose": "Resolve entities"},
                {"step": 4, "action": "get_bias_analysis(article_id=...)", "purpose": "Detect bias"},
            ],
        },
        "system_health": {
            "description": "Check system health and status",
            "steps": [
                {"step": 1, "action": "health_get_summary()", "purpose": "Overall health"},
                {"step": 2, "action": "get_circuit_breaker_status()", "purpose": "Service resilience"},
                {"step": 3, "action": "scheduler_status()", "purpose": "Job scheduler"},
                {"step": 4, "action": "cache_get_stats()", "purpose": "Cache performance"},
            ],
        },
    }

    if task in workflows:
        return {
            "success": True,
            "data": workflows[task],
        }
    else:
        return {
            "success": False,
            "error": f"Unknown task: {task}",
            "available_tasks": list(workflows.keys()),
        }

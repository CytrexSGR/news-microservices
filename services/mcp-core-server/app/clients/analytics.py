"""Analytics service client for MCP Core Server."""

import logging
from typing import Any, Dict, List, Optional

from ..config import settings
from .base import BaseClient

logger = logging.getLogger(__name__)


class AnalyticsClient(BaseClient):
    """Client for analytics-service (Port 8107)."""

    def __init__(self):
        super().__init__(
            service_name="analytics-service",
            base_url=settings.analytics_service_url,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    # =========================================================================
    # Analytics Endpoints
    # =========================================================================

    async def get_overview(self) -> Dict[str, Any]:
        """
        Get system-wide analytics overview.

        Returns aggregated metrics across all services.
        """
        return await self.request("GET", "/api/v1/analytics/overview")

    async def get_metrics(
        self,
        metric_names: Optional[List[str]] = None,
        time_range: str = "1h",
    ) -> Dict[str, Any]:
        """
        Get specific metrics.

        Args:
            metric_names: List of metric names to fetch
            time_range: Time range (1h, 24h, 7d, 30d)
        """
        params = {"time_range": time_range}
        if metric_names:
            params["metrics"] = ",".join(metric_names)

        return await self.request("GET", "/api/v1/analytics/metrics", params=params)

    async def get_service_analytics(
        self,
        service_name: str,
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific service.
        """
        return await self.request(
            "GET",
            f"/api/v1/analytics/service/{service_name}",
        )

    async def get_trends(
        self,
        metric: str = "requests",
        period: str = "24h",
    ) -> Dict[str, Any]:
        """
        Get trend data for metrics.

        Args:
            metric: Metric to analyze (requests, errors, latency)
            period: Time period (1h, 24h, 7d, 30d)
        """
        return await self.request(
            "GET",
            "/api/v1/analytics/trends",
            params={"metric": metric, "period": period},
        )

    # =========================================================================
    # Health Monitoring
    # =========================================================================

    async def get_health_summary(self) -> Dict[str, Any]:
        """
        Get system health summary across all services.
        """
        return await self.request("GET", "/api/v1/health/summary")

    async def get_container_health(self) -> Dict[str, Any]:
        """
        Get Docker container health status.
        """
        return await self.request("GET", "/api/v1/health/containers")

    async def get_health_alerts(self) -> Dict[str, Any]:
        """
        Get active health alerts.
        """
        return await self.request("GET", "/api/v1/health/alerts")

    # =========================================================================
    # Monitoring
    # =========================================================================

    async def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """
        Get circuit breaker status for all services.
        """
        return await self.request("GET", "/api/v1/monitoring/circuit-breakers")

    async def get_monitoring_health(self) -> Dict[str, Any]:
        """
        Get monitoring system health.
        """
        return await self.request("GET", "/api/v1/monitoring/health")

    async def get_query_performance(self) -> Dict[str, Any]:
        """
        Get database query performance metrics.
        """
        return await self.request("GET", "/api/v1/monitoring/query-performance")

    # =========================================================================
    # Cache Management
    # =========================================================================

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        """
        return await self.request("GET", "/api/v1/cache/stats")

    async def get_cache_health(self) -> Dict[str, Any]:
        """
        Get cache health status.
        """
        return await self.request("GET", "/api/v1/cache/health")

    async def clear_cache(
        self,
        cache_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clear cache (optionally by key pattern).
        """
        params = {}
        if cache_key:
            params["key"] = cache_key

        return await self.request("POST", "/api/v1/cache/clear", params=params)

    # =========================================================================
    # Dashboards
    # =========================================================================

    async def list_dashboards(self) -> Dict[str, Any]:
        """
        List available dashboards.
        """
        return await self.request("GET", "/api/v1/dashboards")

    async def get_dashboard(
        self,
        dashboard_id: str,
    ) -> Dict[str, Any]:
        """
        Get dashboard configuration.
        """
        return await self.request("GET", f"/api/v1/dashboards/{dashboard_id}")

    async def get_dashboard_data(
        self,
        dashboard_id: str,
    ) -> Dict[str, Any]:
        """
        Get dashboard data.
        """
        return await self.request("GET", f"/api/v1/dashboards/{dashboard_id}/data")

    # =========================================================================
    # Reports
    # =========================================================================

    async def list_reports(self) -> Dict[str, Any]:
        """
        List available reports.
        """
        return await self.request("GET", "/api/v1/reports")

    async def get_report(
        self,
        report_id: str,
    ) -> Dict[str, Any]:
        """
        Get report details.
        """
        return await self.request("GET", f"/api/v1/reports/{report_id}")

    async def create_dashboard(
        self,
        name: str,
        description: Optional[str] = None,
        widgets: Optional[List[Dict[str, Any]]] = None,
        layout: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new dashboard.

        Args:
            name: Dashboard name
            description: Optional description
            widgets: List of widget configurations
            layout: Layout configuration
        """
        payload = {"name": name}
        if description:
            payload["description"] = description
        if widgets:
            payload["widgets"] = widgets
        if layout:
            payload["layout"] = layout

        return await self.request("POST", "/api/v1/dashboards", json=payload)

    async def update_dashboard(
        self,
        dashboard_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        widgets: Optional[List[Dict[str, Any]]] = None,
        layout: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing dashboard.

        Args:
            dashboard_id: Dashboard ID to update
            name: New name (optional)
            description: New description (optional)
            widgets: Updated widgets (optional)
            layout: Updated layout (optional)
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if widgets is not None:
            payload["widgets"] = widgets
        if layout is not None:
            payload["layout"] = layout

        return await self.request(
            "PUT", f"/api/v1/dashboards/{dashboard_id}", json=payload
        )

    async def delete_dashboard(
        self,
        dashboard_id: str,
    ) -> Dict[str, Any]:
        """
        Delete a dashboard.

        Args:
            dashboard_id: Dashboard ID to delete
        """
        return await self.request("DELETE", f"/api/v1/dashboards/{dashboard_id}")

    async def create_report(
        self,
        name: str,
        report_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        schedule: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create/generate a new report.

        Args:
            name: Report name
            report_type: Type of report (daily, weekly, monthly, custom)
            parameters: Report parameters (filters, metrics, etc.)
            schedule: Optional cron schedule for recurring reports
        """
        payload = {"name": name, "type": report_type}
        if parameters:
            payload["parameters"] = parameters
        if schedule:
            payload["schedule"] = schedule

        return await self.request("POST", "/api/v1/reports", json=payload)

    async def delete_report(
        self,
        report_id: str,
    ) -> Dict[str, Any]:
        """
        Delete a report.

        Args:
            report_id: Report ID to delete
        """
        return await self.request("DELETE", f"/api/v1/reports/{report_id}")

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.models.analytics import AnalyticsMetric


class WidgetDataService:
    """Service for fetching widget data based on widget configuration"""

    def __init__(self, db: Session):
        self.db = db

    async def get_widget_data(self, widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get data for a widget based on its configuration.

        Args:
            widget_config: Widget configuration dict with type, metric_name, service, etc.

        Returns:
            Formatted data for the widget type
        """
        widget_type = widget_config.get("type")
        metric_name = widget_config.get("metric_name")
        service = widget_config.get("service")
        config = widget_config.get("config", {})

        # Parse time range
        time_range = config.get("time_range", "24h")
        start_time, end_time = self._parse_time_range(time_range)

        # Route to appropriate handler based on widget type
        if widget_type == "stat_card":
            return await self._get_stat_card_data(metric_name, service, start_time, end_time)
        elif widget_type == "line_chart":
            return await self._get_time_series_data(metric_name, service, start_time, end_time)
        elif widget_type == "bar_chart":
            return await self._get_bar_chart_data(metric_name, service, start_time, end_time)
        elif widget_type == "pie_chart":
            return await self._get_pie_chart_data(metric_name, service, start_time, end_time)
        elif widget_type == "table":
            return await self._get_table_data(metric_name, service, start_time, end_time, config.get("limit", 10))
        else:
            return {"error": f"Unknown widget type: {widget_type}"}

    def _parse_time_range(self, time_range: str) -> tuple[datetime, datetime]:
        """Parse time range string like '24h', '7d', '30d' into start and end times"""
        end_time = datetime.utcnow()

        if time_range.endswith("h"):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        elif time_range.endswith("d"):
            days = int(time_range[:-1])
            start_time = end_time - timedelta(days=days)
        else:
            # Default to 24 hours
            start_time = end_time - timedelta(hours=24)

        return start_time, end_time

    async def _get_stat_card_data(
        self, metric_name: str, service: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Get aggregated value for a stat card widget"""
        query = self.db.query(
            func.sum(AnalyticsMetric.value).label("total"),
            func.avg(AnalyticsMetric.value).label("average"),
            func.count(AnalyticsMetric.id).label("count")
        ).filter(
            AnalyticsMetric.metric_name == metric_name,
            AnalyticsMetric.timestamp >= start_time,
            AnalyticsMetric.timestamp <= end_time
        )

        if service:
            query = query.filter(AnalyticsMetric.service == service)

        result = query.first()

        return {
            "value": float(result.total or 0),
            "average": float(result.average or 0),
            "count": result.count or 0,
            "trend": "up",  # TODO: Calculate actual trend
            "change": 0  # TODO: Calculate change percentage
        }

    async def _get_time_series_data(
        self, metric_name: str, service: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Get time series data for line chart"""
        query = self.db.query(
            AnalyticsMetric.timestamp,
            AnalyticsMetric.value,
            AnalyticsMetric.unit
        ).filter(
            AnalyticsMetric.metric_name == metric_name,
            AnalyticsMetric.timestamp >= start_time,
            AnalyticsMetric.timestamp <= end_time
        )

        if service:
            query = query.filter(AnalyticsMetric.service == service)

        metrics = query.order_by(AnalyticsMetric.timestamp).all()

        series = [
            {
                "timestamp": metric.timestamp.isoformat(),
                "value": float(metric.value),
                "unit": metric.unit
            }
            for metric in metrics
        ]

        return {"series": series}

    async def _get_bar_chart_data(
        self, metric_name: str, service: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Get aggregated data grouped by service for bar chart"""
        query = self.db.query(
            AnalyticsMetric.service,
            func.sum(AnalyticsMetric.value).label("total"),
            AnalyticsMetric.unit
        ).filter(
            AnalyticsMetric.metric_name == metric_name,
            AnalyticsMetric.timestamp >= start_time,
            AnalyticsMetric.timestamp <= end_time
        )

        if service:
            query = query.filter(AnalyticsMetric.service == service)

        results = query.group_by(AnalyticsMetric.service, AnalyticsMetric.unit).all()

        series = [
            {
                "name": result.service,
                "value": float(result.total),
                "unit": result.unit
            }
            for result in results
        ]

        return {"series": series}

    async def _get_pie_chart_data(
        self, metric_name: str, service: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Get distribution data for pie chart"""
        # Same as bar chart but formatted for pie chart
        bar_data = await self._get_bar_chart_data(metric_name, service, start_time, end_time)
        return bar_data

    async def _get_table_data(
        self, metric_name: str, service: str, start_time: datetime, end_time: datetime, limit: int
    ) -> Dict[str, Any]:
        """Get recent metrics for table widget"""
        query = self.db.query(AnalyticsMetric).filter(
            AnalyticsMetric.metric_name == metric_name,
            AnalyticsMetric.timestamp >= start_time,
            AnalyticsMetric.timestamp <= end_time
        )

        if service:
            query = query.filter(AnalyticsMetric.service == service)

        metrics = query.order_by(AnalyticsMetric.timestamp.desc()).limit(limit).all()

        rows = [
            {
                "timestamp": metric.timestamp.isoformat(),
                "service": metric.service,
                "metric_name": metric.metric_name,
                "value": float(metric.value),
                "unit": metric.unit
            }
            for metric in metrics
        ]

        return {"rows": rows}

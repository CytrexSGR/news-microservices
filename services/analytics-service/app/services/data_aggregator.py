"""
Data Aggregation Module for Dashboard Widgets

This module provides functions to aggregate metrics from the analytics_metrics table
and format them for different widget types (stat cards, charts, etc.).
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.models.analytics import AnalyticsMetric


def aggregate_stat_card_data(
    db_session: Session,
    widget_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate data for a stat card widget.

    Returns latest metric value with trend calculation compared to previous period.

    Args:
        db_session: Database session
        widget_config: Widget configuration with options like:
            - metric_name: Name of the metric to display
            - service: Service name (optional, defaults to all services)
            - aggregation: How to aggregate (sum, avg, max, min) default: sum

    Returns:
        {
            "value": float,           # Latest aggregated value
            "change": float,          # Percentage change from previous period
            "trend": str             # "up", "down", or "neutral"
        }
    """
    options = widget_config.get("options", {})
    metric_name = options.get("metric_name", "service_status")
    service = options.get("service")
    aggregation = options.get("aggregation", "sum")

    # Time windows: current hour vs previous hour
    now = datetime.utcnow()
    current_hour_start = now.replace(minute=0, second=0, microsecond=0)
    previous_hour_start = current_hour_start - timedelta(hours=1)

    # Build base query
    current_query = db_session.query(AnalyticsMetric).filter(
        AnalyticsMetric.metric_name == metric_name,
        AnalyticsMetric.timestamp >= current_hour_start
    )

    previous_query = db_session.query(AnalyticsMetric).filter(
        AnalyticsMetric.metric_name == metric_name,
        AnalyticsMetric.timestamp >= previous_hour_start,
        AnalyticsMetric.timestamp < current_hour_start
    )

    # Filter by service if specified
    if service:
        current_query = current_query.filter(AnalyticsMetric.service == service)
        previous_query = previous_query.filter(AnalyticsMetric.service == service)

    # Apply aggregation function
    agg_func = {
        "sum": func.sum,
        "avg": func.avg,
        "max": func.max,
        "min": func.min,
        "count": func.count
    }.get(aggregation, func.sum)

    current_value = current_query.with_entities(
        agg_func(AnalyticsMetric.value)
    ).scalar() or 0.0

    previous_value = previous_query.with_entities(
        agg_func(AnalyticsMetric.value)
    ).scalar() or 0.0

    # Calculate percentage change
    if previous_value > 0:
        change = ((current_value - previous_value) / previous_value) * 100
    else:
        change = 0.0 if current_value == 0 else 100.0

    # Determine trend
    if change > 0.5:
        trend = "up"
    elif change < -0.5:
        trend = "down"
    else:
        trend = "neutral"

    return {
        "value": float(current_value),
        "change": round(change, 1),
        "trend": trend
    }


def aggregate_timeseries_data(
    db_session: Session,
    widget_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate time-series data for line/area charts.

    Returns hourly aggregated data points for the last 24 hours.

    Args:
        db_session: Database session
        widget_config: Widget configuration with options like:
            - metric_name: Name of the metric to display
            - service: Service name (optional)
            - aggregation: How to aggregate (sum, avg, max, min) default: avg
            - hours: Number of hours to include (default: 24)

    Returns:
        {
            "series": [
                {"timestamp": "2025-10-19T14:00:00", "value": 123.45},
                ...
            ]
        }
    """
    options = widget_config.get("options", {})
    metric_name = options.get("metric_name", "service_status")
    service = options.get("service")
    aggregation = options.get("aggregation", "avg")
    hours = options.get("hours", 24)

    # Time window
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # Build query
    query = db_session.query(
        func.date_trunc('hour', AnalyticsMetric.timestamp).label('hour'),
        {
            "sum": func.sum,
            "avg": func.avg,
            "max": func.max,
            "min": func.min,
            "count": func.count
        }.get(aggregation, func.avg)(AnalyticsMetric.value).label('value')
    ).filter(
        AnalyticsMetric.metric_name == metric_name,
        AnalyticsMetric.timestamp >= start_time
    )

    if service:
        query = query.filter(AnalyticsMetric.service == service)

    query = query.group_by('hour').order_by('hour')

    results = query.all()

    # Create a complete hourly series (fill gaps with 0 or last known value)
    data_map = {row.hour: float(row.value) if row.value is not None else 0.0 for row in results}

    series = []
    current_hour = start_time.replace(minute=0, second=0, microsecond=0)

    for i in range(hours + 1):  # +1 to include current hour
        hour_timestamp = current_hour + timedelta(hours=i)
        value = data_map.get(hour_timestamp, 0.0)

        series.append({
            "timestamp": hour_timestamp.isoformat(),
            "value": value
        })

    return {"series": series}


def aggregate_bar_chart_data(
    db_session: Session,
    widget_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate data for bar charts (e.g., top services by metric).

    Returns grouped data for categorical comparison.

    Args:
        db_session: Database session
        widget_config: Widget configuration with options like:
            - metric_name: Name of the metric to display
            - group_by: Field to group by (default: "service")
            - aggregation: How to aggregate (sum, avg, max, min) default: sum
            - limit: Maximum number of bars (default: 10)
            - hours: Time window in hours (default: 24)

    Returns:
        {
            "series": [
                {"name": "auth-service", "value": 1234},
                {"name": "feed-service", "value": 987},
                ...
            ]
        }
    """
    options = widget_config.get("options", {})
    metric_name = options.get("metric_name", "service_status")
    group_by = options.get("group_by", "service")
    aggregation = options.get("aggregation", "sum")
    limit = options.get("limit", 10)
    hours = options.get("hours", 24)

    # Time window
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # Build query based on group_by
    if group_by == "service":
        group_column = AnalyticsMetric.service
    else:
        # Default to service if unknown group_by
        group_column = AnalyticsMetric.service

    query = db_session.query(
        group_column.label('name'),
        {
            "sum": func.sum,
            "avg": func.avg,
            "max": func.max,
            "min": func.min,
            "count": func.count
        }.get(aggregation, func.sum)(AnalyticsMetric.value).label('value')
    ).filter(
        AnalyticsMetric.metric_name == metric_name,
        AnalyticsMetric.timestamp >= start_time
    ).group_by(
        group_column
    ).order_by(
        desc('value')
    ).limit(limit)

    results = query.all()

    # Format as series
    series = []
    for row in results:
        series.append({
            "name": row.name,
            "value": float(row.value) if row.value is not None else 0.0
        })

    return {"series": series}


def aggregate_pie_chart_data(
    db_session: Session,
    widget_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate data for pie charts (distribution/percentage breakdown).

    Returns percentage distribution of a metric across categories.

    Args:
        db_session: Database session
        widget_config: Widget configuration with options like:
            - metric_name: Name of the metric to display
            - group_by: Field to group by (default: "service")
            - hours: Time window in hours (default: 24)
            - colors: Dict mapping categories to colors (optional)

    Returns:
        {
            "series": [
                {"name": "auth-service", "value": 45.5, "color": "#3b82f6"},
                {"name": "feed-service", "value": 35.2, "color": "#10b981"},
                ...
            ]
        }
    """
    options = widget_config.get("options", {})
    metric_name = options.get("metric_name", "service_status")
    group_by = options.get("group_by", "service")
    hours = options.get("hours", 24)
    colors = options.get("colors", {})

    # Default color palette
    default_colors = [
        "#3b82f6",  # blue
        "#10b981",  # green
        "#f59e0b",  # amber
        "#ef4444",  # red
        "#8b5cf6",  # purple
        "#ec4899",  # pink
        "#06b6d4",  # cyan
        "#84cc16",  # lime
    ]

    # Time window
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # Build query
    if group_by == "service":
        group_column = AnalyticsMetric.service
    else:
        group_column = AnalyticsMetric.service

    query = db_session.query(
        group_column.label('name'),
        func.sum(AnalyticsMetric.value).label('value')
    ).filter(
        AnalyticsMetric.metric_name == metric_name,
        AnalyticsMetric.timestamp >= start_time
    ).group_by(
        group_column
    ).order_by(
        desc('value')
    )

    results = query.all()

    # Calculate total for percentages
    total = sum(float(row.value) if row.value else 0.0 for row in results)

    # Format as series with percentages
    series = []
    for idx, row in enumerate(results):
        value = float(row.value) if row.value is not None else 0.0
        percentage = (value / total * 100) if total > 0 else 0.0

        # Get color from config or use default
        color = colors.get(row.name, default_colors[idx % len(default_colors)])

        series.append({
            "name": row.name,
            "value": round(percentage, 1),
            "color": color
        })

    return {"series": series}

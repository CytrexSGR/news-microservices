from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


# Metric Schemas
class MetricBase(BaseModel):
    service: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    labels: Optional[Dict[str, Any]] = {}


class MetricCreate(MetricBase):
    timestamp: Optional[datetime] = None


class MetricResponse(MetricBase):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Report Schemas
class ReportConfig(BaseModel):
    services: List[str]
    metrics: List[str]
    start_date: str  # ISO format string for JSON serialization
    end_date: str    # ISO format string for JSON serialization
    aggregation: Optional[str] = "hourly"
    include_charts: bool = True


class ReportCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: ReportConfig
    format: str = Field(default="csv", pattern="^(csv|json|md)$")


class ReportResponse(BaseModel):
    id: int
    user_id: str
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    status: str
    format: str
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Dashboard Schemas
class DashboardWidget(BaseModel):
    id: str
    type: str  # line_chart, bar_chart, pie_chart, stat_card, table
    title: str
    metric_name: str
    service: Optional[str] = None
    config: Dict[str, Any] = {}
    position: Dict[str, int] = {"x": 0, "y": 0, "w": 6, "h": 4}


class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    widgets: List[DashboardWidget] = []
    is_public: bool = False
    refresh_interval: int = 60


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    widgets: Optional[List[DashboardWidget]] = None
    is_public: Optional[bool] = None
    refresh_interval: Optional[int] = None


class DashboardResponse(BaseModel):
    id: int
    user_id: str
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    is_public: bool
    refresh_interval: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alert Schemas
class AlertCreate(BaseModel):
    name: str
    metric_name: str
    service: Optional[str] = None
    threshold: float
    comparison: str = Field(pattern="^(gt|lt|eq|gte|lte)$")
    severity: str = Field(default="warning", pattern="^(info|warning|critical)$")
    notification_channels: List[str] = []
    cooldown_minutes: int = 30


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    comparison: Optional[str] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    notification_channels: Optional[List[str]] = None
    cooldown_minutes: Optional[int] = None


class AlertResponse(BaseModel):
    id: int
    user_id: str
    name: str
    metric_name: str
    service: Optional[str]
    threshold: float
    comparison: str
    severity: str
    enabled: bool
    notification_channels: List[str]
    cooldown_minutes: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Analytics Overview Schema
class ServiceMetrics(BaseModel):
    total_requests: int
    error_rate: float
    avg_latency_ms: float
    active_users: int


class OverviewResponse(BaseModel):
    timestamp: datetime
    services: Dict[str, ServiceMetrics]
    system_health: str
    active_alerts: int
    total_users: int
    total_articles: int


# Trend Analysis Schema
class TrendDataPoint(BaseModel):
    timestamp: datetime
    value: float


class TrendResponse(BaseModel):
    metric_name: str
    service: str
    data_points: List[TrendDataPoint]
    trend: str  # increasing, decreasing, stable
    change_percent: float
    anomalies: List[datetime] = []

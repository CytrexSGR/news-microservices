from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
from datetime import datetime
from app.core.database import Base


# Helper to use JSONB for PostgreSQL, JSON for SQLite
class JSONType(TypeDecorator):
    """Platform-agnostic JSON type that uses JSONB for PostgreSQL, JSON for others."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class AnalyticsMetric(Base):
    """Time-series metrics storage"""
    __tablename__ = "analytics_metrics"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(100), index=True, nullable=False)
    metric_name = Column(String(200), index=True, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    labels = Column(JSONType, default={})
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalyticsReport(Base):
    """Generated analytics reports"""
    __tablename__ = "analytics_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config = Column(JSONType, nullable=False)
    status = Column(String(50), default="pending", index=True)
    format = Column(String(20), nullable=False)
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)


class AnalyticsDashboard(Base):
    """Custom user dashboards"""
    __tablename__ = "analytics_dashboards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config = Column(JSONType, nullable=False, default={})
    widgets = Column(JSONType, default=[])
    is_public = Column(Boolean, default=False)
    refresh_interval = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalyticsAlert(Base):
    """Alert configurations and thresholds"""
    __tablename__ = "analytics_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    metric_name = Column(String(200), index=True, nullable=False)
    service = Column(String(100), index=True)
    threshold = Column(Float, nullable=False)
    comparison = Column(String(20), nullable=False)  # gt, lt, eq, gte, lte
    severity = Column(String(20), default="warning")  # info, warning, critical
    enabled = Column(Boolean, default=True, index=True)
    notification_channels = Column(JSONType, default=[])
    cooldown_minutes = Column(Integer, default=30)
    last_triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

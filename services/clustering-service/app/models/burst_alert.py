"""SQLAlchemy model for burst alerts."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.cluster import Base


class BurstAlert(Base):
    """
    Records burst detection alerts for auditing and cooldown tracking.

    Table tracks all detected bursts with their severity, velocity,
    and whether an external alert was sent.

    New in v2: Added category, title, growth_rate, tension_score, top_entities
    to enable category-based filtering in the UI.
    """
    __tablename__ = "burst_alerts"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Reference to cluster
    cluster_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # Cluster snapshot at detection time (for UI display)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True  # Index for category filtering
    )
    tension_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    growth_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_entities: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Burst detection details
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    velocity: Mapped[int] = mapped_column(Integer, nullable=False)
    window_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Alert status
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Acknowledgment status
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    acknowledged_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    # Article time range (when was the burst activity)
    first_article_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_article_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

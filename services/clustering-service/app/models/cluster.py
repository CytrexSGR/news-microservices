"""SQLAlchemy models for article clusters."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class ArticleCluster(Base):
    """
    Represents a story cluster (group of related articles).

    Table created by V001 migration in Phase 0.
    """
    __tablename__ = "article_clusters"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Cluster metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cluster state
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False
    )

    # Cluster metrics
    article_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    # Centroid vector for similarity matching
    centroid_vector: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Story importance
    tension_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    burst_detected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Primary entities (top entities in this cluster)
    primary_entities: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # CSAI (Cluster Stability Assessment Index) tracking
    # Added by migration 024_add_pgvector_to_article_clusters.py
    csai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    csai_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        default="pending",
        nullable=True
    )
    csai_checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Escalation tracking columns
    # Added by migration 026_add_escalation_columns_to_clusters.py
    escalation_geopolitical: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    escalation_military: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    escalation_economic: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    escalation_combined: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    escalation_level: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    escalation_signals: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )
    escalation_calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class ClusterMembership(Base):
    """
    Tracks which articles belong to which clusters.

    Used for:
    - Idempotency checking (prevent duplicate processing)
    - Article-to-cluster lookups
    - Cluster member listing

    Composite primary key: (cluster_id, article_id)
    """
    __tablename__ = "cluster_memberships"

    cluster_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True
    )
    article_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True
    )

    # Membership metadata
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    similarity_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )


# Note: BurstAlert model moved to app/models/burst_alert.py

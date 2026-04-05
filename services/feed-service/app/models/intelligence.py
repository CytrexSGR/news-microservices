"""
Intelligence models for News Intelligence features.

These models support:
- Stream clustering (article_clusters)
- NewsML-G2 version tracking (article_versions)
- HITL review workflow (publication_review_queue)
- Intelligence briefings (sitrep_reports)
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Date, Text,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.feed import Base
from app.utils.database_types import JSONBType

if TYPE_CHECKING:
    from app.models.feed import FeedItem


class ArticleCluster(Base):
    """
    Represents a story cluster (group of related articles).

    Used for:
    - Stream clustering (Single-Pass algorithm)
    - Story tracking over time
    - Deduplication at story level
    - SITREP generation (top stories)
    """
    __tablename__ = "article_clusters"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Cluster metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cluster state
    status: Mapped[str] = mapped_column(String(20), default='active', nullable=False)

    # Cluster metrics
    article_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Centroid for similarity matching
    centroid_vector: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)

    # Story importance
    tension_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    burst_detected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Primary entities
    primary_entities: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    articles: Mapped[List["FeedItem"]] = relationship(
        "FeedItem",
        back_populates="cluster",
        foreign_keys="FeedItem.cluster_id"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived', 'merged')",
            name='chk_cluster_status'
        ),
        Index('idx_clusters_active_updated', 'status', 'last_updated_at'),
    )

    def __repr__(self) -> str:
        return f"<ArticleCluster(id={self.id}, title={self.title[:50] if self.title else ''}, articles={self.article_count})>"


class ArticleVersion(Base):
    """
    Tracks article version history for NewsML-G2 compliance.

    Created when:
    - Article content changes (version increments)
    - Article is corrected (is_correction = True)
    - Article is withdrawn (pub_status = 'canceled')
    """
    __tablename__ = "article_versions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Reference to current article
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feed_items.id", ondelete="CASCADE"),
        nullable=False
    )

    # Version info
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    pub_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Snapshot of content at this version
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Change metadata
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    article: Mapped["FeedItem"] = relationship("FeedItem", back_populates="versions")

    __table_args__ = (
        CheckConstraint(
            "change_type IN ('update', 'correction', 'withdrawal')",
            name='chk_version_change_type'
        ),
        Index('idx_versions_article_version', 'article_id', 'version'),
    )

    def __repr__(self) -> str:
        return f"<ArticleVersion(article_id={self.article_id}, version={self.version}, type={self.change_type})>"


class PublicationReviewQueue(Base):
    """
    Human-in-the-Loop review queue for content publication.

    Risk-based routing:
    - Low risk (< 0.3): Auto-approve
    - Medium risk (0.3-0.7): Human review
    - High risk (> 0.7): Block + alert
    """
    __tablename__ = "publication_review_queue"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Content reference
    article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feed_items.id", ondelete="CASCADE"),
        nullable=False
    )

    # Publication target
    target: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Risk assessment
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_factors: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)

    # Review status
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)

    # Review metadata
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    article: Mapped["FeedItem"] = relationship("FeedItem", back_populates="review_items")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'edited', 'auto_approved', 'blocked')",
            name='chk_review_status'
        ),
        Index('idx_review_queue_pending', 'status', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<PublicationReviewQueue(id={self.id}, target={self.target}, status={self.status})>"


class SitrepReport(Base):
    """
    Generated Intelligence Briefings (SITREP).

    Structure follows SmartBook/UN OCHA patterns:
    - Top stories (from burst detection)
    - Geopolitical assessment
    - Financial impact
    - Emerging signals
    """
    __tablename__ = "sitrep_reports"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Report metadata
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), default='daily')

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structured data
    top_stories: Mapped[dict] = mapped_column(JSONBType, nullable=False)
    key_entities: Mapped[dict] = mapped_column(JSONBType, nullable=False)
    sentiment_summary: Mapped[dict] = mapped_column(JSONBType, nullable=False)
    emerging_signals: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)

    # Generation metadata
    generation_model: Mapped[str] = mapped_column(String(100), nullable=False)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    articles_analyzed: Mapped[int] = mapped_column(Integer, nullable=False)

    # Quality
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_sitrep_date_type', 'report_date', 'report_type'),
    )

    def __repr__(self) -> str:
        return f"<SitrepReport(id={self.id}, date={self.report_date}, type={self.report_type})>"

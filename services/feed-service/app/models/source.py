"""
Unified Source Management Models

Master entity for news sources with provider-specific feeds.
Replaces the split between feeds (RSS), source_profiles (scraping), and MediaStack sources.

Architecture:
- Source: One entry per domain with centralized assessment and scraping config
- SourceFeed: Provider-specific feeds (RSS, MediaStack, NewsAPI, etc.)
- SourceAssessmentHistory: Historical record of assessments
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.feed import Base
from app.utils.database_types import JSONBType

if TYPE_CHECKING:
    from app.models.feed import Feed, FeedItem


# =============================================================================
# Enums
# =============================================================================

class SourceStatus(str, Enum):
    """Source status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class ScrapeStatus(str, Enum):
    """Scraping status for a source."""
    WORKING = "working"        # Scraping works reliably
    DEGRADED = "degraded"      # Scraping works but with issues
    BLOCKED = "blocked"        # Source blocks our scraping
    UNSUPPORTED = "unsupported"  # Cannot scrape (e.g., SPA, heavy JS)
    UNKNOWN = "unknown"        # Not yet tested


class PaywallType(str, Enum):
    """Paywall types for sources."""
    NONE = "none"              # Free access
    SOFT = "soft"              # Shows partial content, then paywall
    HARD = "hard"              # No content without subscription
    METERED = "metered"        # X free articles per month
    REGISTRATION = "registration"  # Free but requires account


class ProviderType(str, Enum):
    """Feed provider types."""
    RSS = "rss"                # Traditional RSS/Atom feeds
    MEDIASTACK = "mediastack"  # MediaStack API
    NEWSAPI = "newsapi"        # NewsAPI.org
    GDELT = "gdelt"            # GDELT Project
    MANUAL = "manual"          # Manually added


class CredibilityTier(str, Enum):
    """Source credibility tiers."""
    TIER_1 = "tier_1"          # Highly credible (major outlets, agencies)
    TIER_2 = "tier_2"          # Generally credible
    TIER_3 = "tier_3"          # Lower credibility, use with caution
    UNKNOWN = "unknown"        # Not yet assessed


class AssessmentStatus(str, Enum):
    """Assessment status for sources."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Models
# =============================================================================

class Source(Base):
    """
    Master entity for news sources.

    One entry per domain with:
    - Centralized assessment (credibility, bias, trust ratings)
    - Centralized scraping config (method, paywall, rate limits)
    - Scraping metrics (success rate, response times)

    Example:
        heise.de -> canonical_name="Heise Online", organization_name="Heise Medien"
        ct.de -> canonical_name="c't Magazin", organization_name="Heise Medien"

    A Source can have multiple feeds (RSS, MediaStack, etc.) via SourceFeed relationship.
    """
    __tablename__ = "sources"

    # === IDENTITY ===
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # === STATUS ===
    status: Mapped[str] = mapped_column(String(20), default=SourceStatus.ACTIVE.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # === CATEGORIZATION ===
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    # === ASSESSMENT (from Research Service) ===
    assessment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    assessment_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    credibility_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reputation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    political_bias: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    organization_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    editorial_standards: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)
    trust_ratings: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)
    assessment_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # === SCRAPING CONFIG ===
    scrape_method: Mapped[str] = mapped_column(String(50), default="newspaper4k", nullable=False)
    fallback_methods: Mapped[Optional[list]] = mapped_column(JSONBType, nullable=True)
    scrape_status: Mapped[str] = mapped_column(String(50), default=ScrapeStatus.UNKNOWN.value, nullable=False)
    paywall_type: Mapped[str] = mapped_column(String(50), default=PaywallType.NONE.value, nullable=False)
    paywall_bypass_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    requires_stealth: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_proxy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_headers: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)

    # === SCRAPING METRICS ===
    scrape_success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    scrape_avg_response_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scrape_total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scrape_avg_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scrape_avg_quality: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    scrape_last_success: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scrape_last_failure: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # === META ===
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # === RELATIONSHIPS ===
    feeds: Mapped[List["SourceFeed"]] = relationship(
        "SourceFeed",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    assessment_history: Mapped[List["SourceAssessmentHistory"]] = relationship(
        "SourceAssessmentHistory",
        back_populates="source",
        cascade="all, delete-orphan",
        order_by="desc(SourceAssessmentHistory.assessment_date)",
        lazy="dynamic"
    )
    articles: Mapped[List["FeedItem"]] = relationship(
        "FeedItem",
        back_populates="source",
        lazy="dynamic"  # Use dynamic for large collections
    )

    @property
    def active_feeds_count(self) -> int:
        """Count of active feeds for this source."""
        return sum(1 for f in self.feeds if f.is_active)

    @property
    def rss_feeds_count(self) -> int:
        """Count of RSS feeds for this source."""
        return sum(1 for f in self.feeds if f.provider_type == ProviderType.RSS.value)

    @property
    def latest_assessment(self) -> Optional["SourceAssessmentHistory"]:
        """Get the most recent assessment."""
        return self.assessment_history.first() if self.assessment_history else None

    @property
    def is_assessed(self) -> bool:
        """Check if source has been assessed."""
        return self.assessment_status == AssessmentStatus.COMPLETED.value

    def __repr__(self) -> str:
        return f"<Source(domain={self.domain}, name={self.canonical_name})>"


class SourceFeed(Base):
    """
    Provider-specific feed linked to a Source.

    Each Source can have multiple feeds from different providers:
    - RSS: Traditional RSS/Atom feeds (with feed_url, etag, etc.)
    - MediaStack: MediaStack API source (with provider_id)
    - NewsAPI: NewsAPI.org source
    - etc.

    Examples for heise.de:
    - RSS "Newsticker" -> feed_url=heise.de/rss/heise.rdf
    - RSS "Developer" -> feed_url=heise.de/developer/rss/news.rdf
    - MediaStack -> provider_id="heise"
    """
    __tablename__ = "source_feeds"

    # === IDENTITY ===
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # === PROVIDER ===
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    channel_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # === RSS-SPECIFIC ===
    feed_url: Mapped[Optional[str]] = mapped_column(String(500), unique=True, nullable=True)
    etag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_modified: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fetch_interval: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # === STATUS ===
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    health_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # === ANALYSIS CONFIG ===
    enable_analysis: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # === STATISTICS ===
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_last_24h: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # === META ===
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # === RELATIONSHIPS ===
    source: Mapped["Source"] = relationship("Source", back_populates="feeds")

    # === CONSTRAINTS ===
    __table_args__ = (
        UniqueConstraint("source_id", "provider_type", "provider_id", name="uq_source_provider"),
        Index("idx_source_feeds_provider_type", "provider_type"),
        Index("idx_source_feeds_is_active", "is_active"),
        Index("idx_source_feeds_health_score", "health_score"),
        Index("idx_source_feeds_last_fetched", "last_fetched_at"),
    )

    @property
    def is_rss(self) -> bool:
        """Check if this is an RSS feed."""
        return self.provider_type == ProviderType.RSS.value

    @property
    def is_healthy(self) -> bool:
        """Check if feed is healthy (score >= 50)."""
        return self.health_score >= 50

    def __repr__(self) -> str:
        return f"<SourceFeed(source_id={self.source_id}, provider={self.provider_type}, url={self.feed_url})>"


class SourceAssessmentHistory(Base):
    """
    Historical record of source assessments.

    Stores all assessments from research service for tracking changes over time.
    The latest assessment is synced to Source.assessment_* columns for quick access.
    """
    __tablename__ = "source_assessment_history"

    # === IDENTITY ===
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # === ASSESSMENT DATA ===
    assessment_status: Mapped[str] = mapped_column(String(50), nullable=False)
    assessment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    credibility_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reputation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    political_bias: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    organization_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    editorial_standards: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)
    trust_ratings: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)
    assessment_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # === RAW RESPONSE ===
    raw_response: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)

    # === META ===
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # === RELATIONSHIPS ===
    source: Mapped["Source"] = relationship("Source", back_populates="assessment_history")

    # === INDEXES ===
    __table_args__ = (
        Index("idx_source_assessment_history_date", "source_id", "assessment_date"),
    )

    def __repr__(self) -> str:
        return f"<SourceAssessmentHistory(source_id={self.source_id}, date={self.assessment_date})>"

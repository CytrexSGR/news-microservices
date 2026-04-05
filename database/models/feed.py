"""
RSS feed and article models.

Core content aggregation entities used by feed-service.
"""

from enum import Enum
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FeedStatus(str, Enum):
    """Feed operational status."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    INACTIVE = "INACTIVE"


class Feed(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    RSS/Atom feed configuration and metadata.

    Represents external news sources to aggregate content from.
    Target: https://www.derstandard.at/rss
    """

    __tablename__ = "feeds"

    # Feed configuration
    url = Column(String(500), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    fetch_interval = Column(Integer, default=60)  # minutes
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default=FeedStatus.ACTIVE.value)

    # Feed metadata
    last_fetched_at = Column(String(255), nullable=True)  # UTC datetime
    last_modified = Column(String(100), nullable=True)
    etag = Column(String(100), nullable=True)

    # Health and quality metrics
    health_score = Column(Integer, default=100)
    consecutive_failures = Column(Integer, default=0)
    last_error_message = Column(Text, nullable=True)
    last_error_at = Column(String(255), nullable=True)  # UTC datetime

    # Statistics
    total_items = Column(Integer, default=0)
    items_last_24h = Column(Integer, default=0)

    # Content scraping settings
    scrape_full_content = Column(Boolean, default=False)
    scrape_method = Column(String(50), default="auto")  # auto, httpx, playwright

    # Auto-analysis configuration (extended)
    enable_categorization = Column(Boolean, default=False)  # Article categorization (6 categories)
    enable_finance_sentiment = Column(Boolean, default=False)  # Finance sentiment analysis
    enable_geopolitical_sentiment = Column(Boolean, default=False)  # Geopolitical sentiment analysis
    enable_osint_analysis = Column(Boolean, default=False)  # OSINT Event Analysis
    enable_summary = Column(Boolean, default=False)  # Summary & key facts extraction
    enable_entity_extraction = Column(Boolean, default=False)  # Entity extraction (persons, orgs, locations)
    enable_topic_classification = Column(Boolean, default=False)  # Topic classification & keywords

    # Relationships
    items = relationship("FeedItem", back_populates="feed", cascade="all, delete-orphan")
    fetch_logs = relationship("FetchLog", back_populates="feed", cascade="all, delete-orphan")
    health = relationship("FeedHealth", back_populates="feed", uselist=False, cascade="all, delete-orphan")
    categories = relationship("FeedCategory", back_populates="feed", cascade="all, delete-orphan")
    schedules = relationship("FeedSchedule", back_populates="feed", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Feed(id={self.id}, name={self.name}, url={self.url})>"


class FeedItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Individual articles/entries from RSS feeds.

    Append-only table - items are never updated, only created.
    """

    __tablename__ = "feed_items"

    # Foreign key
    feed_id = Column(UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False, index=True)

    # Item content
    title = Column(String(500), nullable=False)
    link = Column(Text, nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # RSS content or scraped full content
    author = Column(String(200), nullable=True)

    # Item metadata
    guid = Column(String(500), index=True, nullable=True)
    published_at = Column(String(255), nullable=True, index=True)  # UTC datetime
    content_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 hash

    # Scraping metadata
    scraped_at = Column(String(255), nullable=True)  # UTC datetime
    scrape_status = Column(String(50), nullable=True)  # success, paywall, error, timeout
    scrape_word_count = Column(Integer, nullable=True)

    # Relationships
    feed = relationship("Feed", back_populates="items")
    analyses = relationship("AnalysisResult", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FeedItem(id={self.id}, title={self.title[:50]}, feed_id={self.feed_id})>"


class FetchLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Fetch operation history tracking.

    Logs all fetch attempts, successes, and failures.
    """

    __tablename__ = "fetch_log"

    # Foreign key
    feed_id = Column(UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False, index=True)

    # Fetch operation details
    status = Column(String(50), nullable=False)  # running, success, error
    items_found = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    duration = Column(Float, nullable=True)  # seconds
    error = Column(Text, nullable=True)

    # Response metadata
    response_time_ms = Column(Integer, nullable=True)
    response_status_code = Column(Integer, nullable=True)

    # Timestamps
    started_at = Column(String(255), nullable=False)  # UTC datetime
    completed_at = Column(String(255), nullable=True)  # UTC datetime

    # Relationships
    feed = relationship("Feed", back_populates="fetch_logs")

    # Index for performance
    __table_args__ = (
        Index("idx_fetch_log_feed_started", "feed_id", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<FetchLog(id={self.id}, feed_id={self.feed_id}, status={self.status})>"


class FeedHealth(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Feed health and reliability metrics.

    One-to-one relationship with Feed.
    """

    __tablename__ = "feed_health"

    # Foreign key (one-to-one with Feed)
    feed_id = Column(UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Health metrics
    health_score = Column(Integer, default=100)  # 0-100
    consecutive_failures = Column(Integer, default=0)
    is_healthy = Column(Boolean, default=True)

    # Performance metrics
    avg_response_time_ms = Column(Float, nullable=True)
    success_rate = Column(Float, default=1.0)  # 0.0-1.0

    # Uptime tracking
    uptime_24h = Column(Float, default=1.0)  # 0.0-1.0
    uptime_7d = Column(Float, default=1.0)  # 0.0-1.0
    uptime_30d = Column(Float, default=1.0)  # 0.0-1.0

    # Last events
    last_success_at = Column(String(255), nullable=True)  # UTC datetime
    last_failure_at = Column(String(255), nullable=True)  # UTC datetime

    # Relationships
    feed = relationship("Feed", back_populates="health", uselist=False)

    def __repr__(self) -> str:
        return f"<FeedHealth(feed_id={self.feed_id}, score={self.health_score}, is_healthy={self.is_healthy})>"


class FeedCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Feed categorization for organization and filtering."""

    __tablename__ = "feed_categories"

    # Foreign key
    feed_id = Column(UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False, index=True)

    # Category details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # UI customization
    color = Column(String(7), nullable=True)  # Hex color
    icon = Column(String(50), nullable=True)  # Emoji or icon name

    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("feed_categories.id"), nullable=True)

    # Relationships
    feed = relationship("Feed", back_populates="categories")
    parent = relationship("FeedCategory", remote_side="FeedCategory.id")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("feed_id", "name", name="uq_feed_category"),
    )

    def __repr__(self) -> str:
        return f"<FeedCategory(id={self.id}, feed_id={self.feed_id}, name={self.name})>"


class FeedSchedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Custom cron-based fetch schedules.

    Alternative to simple interval-based fetching.
    """

    __tablename__ = "feed_schedules"

    # Foreign key
    feed_id = Column(UUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False, index=True)

    # Schedule configuration
    cron_expression = Column(String(100), nullable=False)  # e.g., "0 */6 * * *"
    is_active = Column(Boolean, default=True)

    # Schedule metadata
    description = Column(String(200), nullable=True)
    timezone = Column(String(50), default="UTC")

    # Execution tracking
    last_run_at = Column(String(255), nullable=True)  # UTC datetime
    next_run_at = Column(String(255), nullable=True)  # UTC datetime

    # Relationships
    feed = relationship("Feed", back_populates="schedules")

    def __repr__(self) -> str:
        return f"<FeedSchedule(id={self.id}, feed_id={self.feed_id}, cron={self.cron_expression})>"

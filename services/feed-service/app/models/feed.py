"""
Feed models for the Feed Service

Based on the monolith models but adapted for microservice architecture.
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint, JSON, BigInteger, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from app.utils.database_types import JSONBType

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.intelligence import ArticleCluster, ArticleVersion, PublicationReviewQueue

Base = declarative_base()


class FeedStatus(str, Enum):
    """Feed status enumeration."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    INACTIVE = "INACTIVE"


class FeedCategoryEnum(str, Enum):
    """Fixed feed categories."""
    GENERAL_NEWS = "General News"
    FINANCE_MARKETS = "Finance & Markets"
    TECH_SCIENCE = "Tech & Science"
    GEOPOLITICS_SECURITY = "Geopolitics & Security"
    ENERGY_INDUSTRY = "Energy & Industry"
    REGIONAL_LOCAL = "Regional / Local"
    THINK_TANKS_ANALYSIS = "Think Tanks / Analysis"
    SPECIAL_INTEREST = "Special Interest"


class Feed(Base):
    """
    Main feed model for RSS/Atom feeds.

    This model stores feed configuration, metadata, and health information.

    .. deprecated:: 2025-12-27
        This model is being replaced by the unified Source Management system.
        New code should use :class:`Source` and :class:`SourceFeed` instead.
        Migration path:
        - Source: Master entity per domain (one-to-one with domain)
        - SourceFeed: Provider-specific feeds (RSS, MediaStack, etc.)
        - FeedItem.source_id: Links articles directly to Sources

        The feeds table will be maintained for backward compatibility but
        new features should be built on the Source Management system.
    """
    __tablename__ = "feeds"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Feed configuration
    url: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Single category from FeedCategoryEnum
    fetch_interval: Mapped[int] = mapped_column(Integer, default=60)  # minutes
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default=FeedStatus.ACTIVE.value)

    # Feed type: rss or web (web crawler)
    feed_type: Mapped[str] = mapped_column(String(10), server_default="rss", nullable=False)

    # Feed metadata
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_modified: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    etag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Intelligent Scheduling (prevents thundering herd)
    next_fetch_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    schedule_offset_minutes: Mapped[int] = mapped_column(Integer, default=0)
    scheduling_priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10, higher = better slots

    # Health and quality metrics
    health_score: Mapped[int] = mapped_column(Integer, default=100)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100, auto-calculated via trigger
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Feed Quality V2 metrics (comprehensive scoring system)
    quality_score_v2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100 comprehensive quality score
    quality_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low, medium, high
    quality_trend: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # improving, stable, declining
    quality_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Last calculation timestamp
    article_quality_stats: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)  # Detailed quality breakdown

    # Statistics
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    items_last_24h: Mapped[int] = mapped_column(Integer, default=0)

    # Content scraping settings
    scrape_full_content: Mapped[bool] = mapped_column(Boolean, default=False)
    scrape_method: Mapped[str] = mapped_column(String(50), default="auto")  # auto, httpx, playwright

    # Scrape failure tracking
    scrape_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    scrape_last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scrape_disabled_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # null, "manual", "auto_threshold"
    scrape_failure_threshold: Mapped[int] = mapped_column(Integer, default=5)  # Configurable per-feed threshold

    # Auto-analysis configuration (V1 - DEPRECATED, kept for backward compatibility)
    enable_categorization: Mapped[bool] = mapped_column(Boolean, default=False)  # Article categorization (6 categories)
    enable_finance_sentiment: Mapped[bool] = mapped_column(Boolean, default=False)  # Finance sentiment analysis
    enable_geopolitical_sentiment: Mapped[bool] = mapped_column(Boolean, default=False)  # Geopolitical sentiment analysis
    enable_osint_analysis: Mapped[bool] = mapped_column(Boolean, default=False)  # OSINT Event Analysis
    enable_summary: Mapped[bool] = mapped_column(Boolean, default=False)  # Summary & key facts extraction
    enable_entity_extraction: Mapped[bool] = mapped_column(Boolean, default=False)  # Entity extraction (persons, orgs, locations)
    enable_topic_classification: Mapped[bool] = mapped_column(Boolean, default=False)  # Topic classification & keywords
    enable_bias: Mapped[bool] = mapped_column(Boolean, default=False)  # Bias detection analysis (BIAS_DETECTOR agent)
    enable_conflict: Mapped[bool] = mapped_column(Boolean, default=False)  # Conflict event analysis (CONFLICT_EVENT_ANALYST agent)

    # Auto-analysis configuration (V2 - content-analysis-v2 service)
    enable_analysis_v2: Mapped[bool] = mapped_column(Boolean, default=False)  # Enable content-analysis-v2 pipeline

    # Feed Source Assessment (from Research Service)
    assessment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # pending, completed, failed
    assessment_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    credibility_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # tier_1, tier_2, tier_3
    reputation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    organization_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # news_agency, newspaper, etc.
    political_bias: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # left, center, right, etc.
    editorial_standards: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)  # fact_checking_level, corrections_policy, source_attribution
    trust_ratings: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)  # media_bias_fact_check, allsides_rating, newsguard_score
    recommendation: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)  # skip_waiting_period, initial_quality_boost, bot_detection_threshold
    assessment_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Human-readable summary

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    items: Mapped[List["FeedItem"]] = relationship(back_populates="feed", cascade="all, delete-orphan")
    fetch_logs: Mapped[List["FetchLog"]] = relationship(back_populates="feed", cascade="all, delete-orphan")
    health: Mapped[Optional["FeedHealth"]] = relationship(back_populates="feed", uselist=False, cascade="all, delete-orphan")
    categories: Mapped[List["FeedCategory"]] = relationship(back_populates="feed", cascade="all, delete-orphan")
    schedules: Mapped[List["FeedSchedule"]] = relationship(back_populates="feed", cascade="all, delete-orphan")

    @property
    def assessment(self) -> Optional[dict]:
        """
        Build assessment data object from latest history entry.
        Falls back to direct columns if no history exists (backward compatibility).
        """
        # Try to get the latest assessment from history
        from sqlalchemy.orm import object_session
        session = object_session(self)

        if session:
            latest_assessment = session.query(FeedAssessmentHistory)\
                .filter(FeedAssessmentHistory.feed_id == self.id)\
                .order_by(FeedAssessmentHistory.assessment_date.desc())\
                .first()

            if latest_assessment:
                return {
                    "assessment_status": latest_assessment.assessment_status,
                    "assessment_date": latest_assessment.assessment_date,
                    "credibility_tier": latest_assessment.credibility_tier,
                    "reputation_score": latest_assessment.reputation_score,
                    "founded_year": latest_assessment.founded_year,
                    "organization_type": latest_assessment.organization_type,
                    "political_bias": latest_assessment.political_bias,
                    "editorial_standards": latest_assessment.editorial_standards,
                    "trust_ratings": latest_assessment.trust_ratings,
                    "recommendation": latest_assessment.recommendation,
                    "assessment_summary": latest_assessment.assessment_summary,
                    "quality_score": self.quality_score,  # Include calculated quality score
                }

        # Fallback to direct columns (backward compatibility)
        if not self.assessment_status:
            return None

        return {
            "assessment_status": self.assessment_status,
            "assessment_date": self.assessment_date,
            "credibility_tier": self.credibility_tier,
            "reputation_score": self.reputation_score,
            "founded_year": self.founded_year,
            "organization_type": self.organization_type,
            "political_bias": self.political_bias,
            "editorial_standards": self.editorial_standards,
            "trust_ratings": self.trust_ratings,
            "recommendation": self.recommendation,
            "assessment_summary": self.assessment_summary,
            "quality_score": self.quality_score,  # Include calculated quality score
        }

    def __repr__(self) -> str:
        return f"<Feed(id={self.id}, name={self.name}, url={self.url})>"


class SourceType(str, Enum):
    """Source type enumeration for feed items."""
    RSS = "rss"
    PERPLEXITY_RESEARCH = "perplexity_research"
    SCRAPING = "scraping"
    MANUAL = "manual"
    API_TWITTER = "api_twitter"
    API_TELEGRAM = "api_telegram"


class FeedItem(Base):
    """
    Feed item model (articles from various sources).

    Supports multiple source types:
    - RSS feeds (original behavior)
    - Perplexity research (AI-generated background research)
    - Web scraping results
    - Manual input
    - API sources (Twitter, Telegram, etc.)

    This is an append-only table - items are never updated, only created.
    """
    __tablename__ = "feed_items"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key to legacy feeds table (nullable for non-RSS sources)
    # DEPRECATED: Use source_id instead. This will be removed in a future version.
    feed_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feeds.id", ondelete="CASCADE"),
        nullable=True  # Changed: nullable for non-RSS sources
    )

    # Foreign key to unified source management (preferred)
    source_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Source type (discriminator for different content sources)
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SourceType.RSS.value,
        index=True
    )

    # Source-specific metadata (model, cost, query for Perplexity, etc.)
    source_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONBType,
        nullable=True,
        default=dict
    )

    # Parent article reference (for research/derived content)
    parent_article_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feed_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )


    # Web crawler fields
    depth: Mapped[Optional[int]] = mapped_column(Integer, server_default="0", nullable=True)
    parent_item_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feed_items.id", ondelete="SET NULL"),
        nullable=True
    )
    crawl_session_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    # Item content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # RSS content or scraped full content
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Item metadata
    guid: Mapped[Optional[str]] = mapped_column(String(500), index=True, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # SHA-256 hash

    # Scraping metadata
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scrape_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # success, paywall, error, timeout
    scrape_word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scraped_metadata: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)  # Additional data from newspaper4k (images, keywords, etc.)

    # Timestamps (no updated_at since items are immutable)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # === NewsML-G2 Essential Fields ===
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    version_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pub_status: Mapped[str] = mapped_column(String(20), default='usable', nullable=False)
    is_correction: Mapped[bool] = mapped_column(Boolean, default=False)
    corrects_article_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feed_items.id", ondelete="SET NULL"),
        nullable=True
    )

    # === Deduplication Support ===
    simhash_fingerprint: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # === Clustering Support ===
    cluster_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("article_clusters.id", ondelete="SET NULL"),
        nullable=True
    )
    cluster_similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cluster_assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # === Time-Decay Ranking ===
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relevance_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    feed: Mapped[Optional["Feed"]] = relationship(back_populates="items")
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="articles")
    parent_article: Mapped[Optional["FeedItem"]] = relationship(
        "FeedItem",
        remote_side=[id],
        foreign_keys=[parent_article_id]
    )
    research_articles: Mapped[List["FeedItem"]] = relationship(
        "FeedItem",
        foreign_keys=[parent_article_id],
        back_populates="parent_article"
    )

    # Intelligence relationships
    cluster: Mapped[Optional["ArticleCluster"]] = relationship(
        "ArticleCluster",
        back_populates="articles",
        foreign_keys=[cluster_id]
    )
    corrected_article: Mapped[Optional["FeedItem"]] = relationship(
        "FeedItem",
        remote_side=[id],
        foreign_keys=[corrects_article_id]
    )
    versions: Mapped[List["ArticleVersion"]] = relationship(
        "ArticleVersion",
        back_populates="article",
        cascade="all, delete-orphan"
    )
    review_items: Mapped[List["PublicationReviewQueue"]] = relationship(
        "PublicationReviewQueue",
        back_populates="article",
        cascade="all, delete-orphan"
    )

    @property
    def is_research(self) -> bool:
        """Check if this item is a research article."""
        return self.source_type == SourceType.PERPLEXITY_RESEARCH.value

    @property
    def has_research(self) -> bool:
        """Check if this item has associated research."""
        return bool(self.research_articles)

    def __repr__(self) -> str:
        return f"<FeedItem(id={self.id}, title={self.title[:50]}, source_type={self.source_type})>"


class FetchLog(Base):
    """
    Log of feed fetch operations.

    Tracks the history of fetch attempts, successes, and failures.
    """
    __tablename__ = "fetch_log"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key
    feed_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False)

    # Fetch operation details
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # running, success, error
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    items_new: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # seconds
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response metadata
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    feed: Mapped["Feed"] = relationship(back_populates="fetch_logs")

    # Index for performance
    __table_args__ = (
        Index("idx_fetch_log_feed_started", "feed_id", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<FetchLog(id={self.id}, feed_id={self.feed_id}, status={self.status})>"


class FeedHealth(Base):
    """
    Feed health metrics.

    Tracks feed reliability and performance over time.
    """
    __tablename__ = "feed_health"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key (one-to-one with Feed)
    feed_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Health metrics
    health_score: Mapped[int] = mapped_column(Integer, default=100)  # 0-100
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)

    # Performance metrics
    avg_response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success_rate: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0-1.0

    # Uptime tracking
    uptime_24h: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0-1.0
    uptime_7d: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0-1.0
    uptime_30d: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0-1.0

    # Last events
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    feed: Mapped["Feed"] = relationship(back_populates="health", uselist=False)

    def __repr__(self) -> str:
        return f"<FeedHealth(feed_id={self.feed_id}, score={self.health_score}, is_healthy={self.is_healthy})>"


class FeedCategory(Base):
    """
    Feed categories for organization.

    Categories can be hierarchical and are used for filtering and grouping feeds.
    """
    __tablename__ = "feed_categories"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key
    feed_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False)

    # Category details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # UI customization
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Emoji or icon name

    # Hierarchy
    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feed_categories.id"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    feed: Mapped["Feed"] = relationship(back_populates="categories")
    parent: Mapped[Optional["FeedCategory"]] = relationship(remote_side=[id])

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("feed_id", "name", name="uq_feed_category"),
    )

    def __repr__(self) -> str:
        return f"<FeedCategory(id={self.id}, feed_id={self.feed_id}, name={self.name})>"


class FeedSchedule(Base):
    """
    Custom feed fetch schedules.

    Allows for cron-based scheduling instead of simple intervals.
    """
    __tablename__ = "feed_schedules"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key
    feed_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False)

    # Schedule configuration
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "0 */6 * * *"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Schedule metadata
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    # Execution tracking
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    feed: Mapped["Feed"] = relationship(back_populates="schedules")

    def __repr__(self) -> str:
        return f"<FeedSchedule(id={self.id}, feed_id={self.feed_id}, cron={self.cron_expression})>"


class FeedAssessmentHistory(Base):
    """
    Feed source assessment history.

    Stores historical assessments from research service (Perplexity analysis).
    Allows tracking how a feed's credibility assessment changes over time.
    """
    __tablename__ = "feed_assessment_history"

    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key
    feed_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False)

    # Assessment metadata
    assessment_status: Mapped[str] = mapped_column(String(50), nullable=False)
    assessment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Source credibility data
    credibility_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reputation_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    organization_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    political_bias: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Detailed assessments (JSON/JSONB)
    editorial_standards: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)
    trust_ratings: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)
    recommendation: Mapped[Optional[dict]] = mapped_column(JSONBType, nullable=True)

    # Summary
    assessment_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<FeedAssessmentHistory(id={self.id}, feed_id={self.feed_id}, date={self.assessment_date})>"


class DuplicateCandidate(Base):
    """Near-duplicate articles flagged for human review.

    Created during article ingestion when SimHash fingerprint comparison
    detects a near-duplicate (Hamming distance 4-7 bits).

    Workflow:
    1. Article ingested with SimHash fingerprint
    2. Comparison against recent articles finds near-duplicate
    3. Record created with status='pending'
    4. Human reviewer decides: keep_both, reject_new, or merge
    5. Status updated to 'reviewed' with decision recorded

    Thresholds:
    - Hamming <= 3: Duplicate (rejected at ingestion, no record created)
    - Hamming 4-7: Near-duplicate (this table)
    - Hamming > 7: Different content (no record created)
    """
    __tablename__ = "duplicate_candidates"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    new_article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feed_items.id", ondelete="CASCADE"),
        nullable=False
    )
    existing_article_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feed_items.id", ondelete="CASCADE"),
        nullable=False
    )

    # Similarity metrics
    hamming_distance: Mapped[int] = mapped_column(Integer, nullable=False)
    simhash_new: Mapped[int] = mapped_column(BigInteger, nullable=False)
    simhash_existing: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Review state
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    reviewed_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    new_article: Mapped["FeedItem"] = relationship(
        "FeedItem",
        foreign_keys=[new_article_id],
        lazy="selectin"
    )
    existing_article: Mapped["FeedItem"] = relationship(
        "FeedItem",
        foreign_keys=[existing_article_id],
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<DuplicateCandidate(id={self.id}, "
            f"new={self.new_article_id}, existing={self.existing_article_id}, "
            f"hamming={self.hamming_distance}, status={self.status})>"
        )
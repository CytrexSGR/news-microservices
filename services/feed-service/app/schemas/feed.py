"""
Pydantic schemas for Feed Service API
"""
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from app.models.feed import FeedStatus
from app.schemas.admiralty_code import AdmiraltyCodeData


class FeedBase(BaseModel):
    """Base feed schema."""
    name: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl
    feed_type: str = Field(default="rss", pattern="^(rss|web)$")
    description: Optional[str] = None
    category: Optional[str] = Field(None, description="Feed category from fixed set")
    fetch_interval: int = Field(default=60, ge=5, le=1440)  # 5 min to 24 hours
    scrape_full_content: bool = False
    scrape_method: str = Field(default="newspaper4k", pattern="^(newspaper4k|playwright|auto)$")
    scrape_failure_threshold: int = Field(default=5, ge=1, le=20, description="Auto-disable scraping after X failures")

    # Auto-analysis configuration (extended)
    # NOTE: All enabled by default to match frontend expectations
    enable_categorization: bool = Field(default=True, description="Enable automatic article categorization")
    enable_finance_sentiment: bool = Field(default=True, description="Enable finance-specific sentiment analysis")
    enable_geopolitical_sentiment: bool = Field(default=True, description="Enable geopolitical sentiment analysis")
    enable_osint_analysis: bool = Field(default=True, description="Enable OSINT Event Analysis")
    enable_summary: bool = Field(default=True, description="Enable summary & key facts extraction")
    enable_entity_extraction: bool = Field(default=True, description="Enable entity extraction")
    enable_topic_classification: bool = Field(default=True, description="Enable topic classification & keywords")
    enable_bias: bool = Field(default=True, description="Enable bias detection analysis (BIAS_DETECTOR agent)")
    enable_conflict: bool = Field(default=True, description="Enable conflict event analysis (CONFLICT_EVENT_ANALYST agent)")


class FeedCreate(FeedBase):
    """Schema for creating a new feed."""
    # NOTE: category is inherited from FeedBase (single category from fixed set)

    # Source Assessment (optional, can be provided during creation)
    credibility_tier: Optional[str] = None  # tier_1, tier_2, tier_3
    reputation_score: Optional[int] = Field(None, ge=0, le=100)
    founded_year: Optional[int] = None
    organization_type: Optional[str] = None
    political_bias: Optional[str] = None  # left, center_left, center, center_right, right, unknown
    editorial_standards: Optional[dict] = None  # fact_checking_level, corrections_policy, source_attribution
    trust_ratings: Optional[dict] = None  # media_bias_fact_check, allsides_rating, newsguard_score
    recommendation: Optional[dict] = None  # skip_waiting_period, initial_quality_boost, bot_detection_threshold
    assessment_summary: Optional[str] = None


class FeedUpdate(BaseModel):
    """Schema for updating a feed."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None  # Single category from fixed set
    feed_type: Optional[str] = Field(None, pattern="^(rss|web)$")
    fetch_interval: Optional[int] = Field(None, ge=5, le=1440)
    is_active: Optional[bool] = None
    scrape_full_content: Optional[bool] = None
    scrape_method: Optional[str] = Field(None, pattern="^(newspaper4k|playwright|auto)$")
    scrape_failure_threshold: Optional[int] = Field(None, ge=1, le=20, description="Auto-disable scraping after X failures")
    scrape_disabled_reason: Optional[str] = None  # Internal use: null, "manual", "auto_threshold"
    # Scraping failure tracking (used by scraping-service)
    scrape_failure_count: Optional[int] = Field(None, ge=0, description="Current failure count for auto-disable")
    scrape_last_failure_at: Optional[datetime] = Field(None, description="Timestamp of last scraping failure")

    # Auto-analysis configuration (V1 - DEPRECATED)
    enable_categorization: Optional[bool] = None
    enable_finance_sentiment: Optional[bool] = None
    enable_geopolitical_sentiment: Optional[bool] = None
    enable_osint_analysis: Optional[bool] = None
    enable_summary: Optional[bool] = None
    enable_entity_extraction: Optional[bool] = None
    enable_topic_classification: Optional[bool] = None
    enable_bias: Optional[bool] = None
    enable_conflict: Optional[bool] = None

    # Auto-analysis configuration (V2 - content-analysis-v2 service)
    enable_analysis_v2: Optional[bool] = None


class FeedAssessmentData(BaseModel):
    """Feed Source Assessment structured data."""
    assessment_status: Optional[str] = None
    assessment_date: Optional[datetime] = None
    credibility_tier: Optional[str] = None  # tier_1, tier_2, tier_3
    reputation_score: Optional[int] = None  # 0-100
    founded_year: Optional[int] = None
    organization_type: Optional[str] = None
    political_bias: Optional[str] = None  # left, center_left, center, center_right, right, unknown
    editorial_standards: Optional[dict] = None  # fact_checking_level, corrections_policy, source_attribution
    trust_ratings: Optional[dict] = None  # media_bias_fact_check, allsides_rating, newsguard_score
    recommendation: Optional[dict] = None  # skip_waiting_period, initial_quality_boost, bot_detection_threshold
    assessment_summary: Optional[str] = None
    quality_score: Optional[int] = None  # 0-100, auto-calculated from assessment data

    model_config = ConfigDict(from_attributes=True)


class FeedResponse(FeedBase):
    """Schema for feed responses."""
    id: UUID
    is_active: bool
    status: FeedStatus
    last_fetched_at: Optional[datetime] = None
    health_score: int
    consecutive_failures: int
    quality_score: Optional[int] = Field(None, description="Quality score (0-100): Premium (85-100), Trusted (70-84), Moderate (50-69), Limited (<50)")
    admiralty_code: Optional[AdmiraltyCodeData] = Field(None, description="Admiralty Code rating (A-F) based on quality score")
    total_items: int
    items_last_24h: int
    # V1 Analysis flags (DEPRECATED)
    enable_categorization: Optional[bool] = None
    enable_finance_sentiment: Optional[bool] = None
    enable_geopolitical_sentiment: Optional[bool] = None
    enable_osint_analysis: Optional[bool] = None
    enable_summary: Optional[bool] = None
    enable_entity_extraction: Optional[bool] = None
    enable_topic_classification: Optional[bool] = None
    enable_bias: Optional[bool] = None
    enable_conflict: Optional[bool] = None

    # V2 Analysis flag
    enable_analysis_v2: Optional[bool] = None

    # Scrape failure tracking
    scrape_failure_count: int = 0
    scrape_failure_threshold: int = 5
    scrape_last_failure_at: Optional[datetime] = None
    scrape_disabled_reason: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    # NOTE: category is inherited from FeedBase (single category)

    # Feed Source Assessment
    assessment: Optional[FeedAssessmentData] = None

    # Backward compatibility - will be populated from metadata if available
    legacy_id: Optional[int] = Field(None, description="Legacy integer ID for backward compatibility")

    model_config = ConfigDict(from_attributes=True)


class FeedItemBase(BaseModel):
    """Base feed item schema."""
    title: str
    link: str
    description: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None


class FeedItemUpdate(BaseModel):
    """Schema for updating a feed item (used by scraping service)."""
    content: Optional[str] = None
    author: Optional[str] = None
    scraped_at: Optional[datetime] = None
    scrape_status: Optional[str] = None
    scrape_word_count: Optional[int] = None
    scraped_metadata: Optional[dict] = None


class ResearchArticleCreate(BaseModel):
    """Schema for creating a research article (Perplexity, etc.)."""
    title: str = Field(..., min_length=1, max_length=500)
    link: str = Field(..., description="URL of the research source")
    content: str = Field(..., min_length=10, description="Research content for analysis")
    description: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    parent_article_id: Optional[UUID] = Field(None, description="Parent article this research is linked to")
    source_metadata: Optional[dict] = Field(
        None,
        description="Source-specific metadata (model, cost, query, citations for Perplexity)"
    )
    trigger_analysis: bool = Field(
        default=True,
        description="Automatically trigger V3 content analysis after creation"
    )


class AnalysisTriggerResponse(BaseModel):
    """Response schema for analysis trigger endpoint."""
    success: bool
    article_id: UUID
    message: str
    event_type: str = "analysis.v3.request"


class CategoryAnalysisResponse(BaseModel):
    """Schema for category analysis - ALL FIELDS."""
    category: str
    confidence: float
    alternative_categories: Optional[list] = None  # List of {category, confidence}
    reasoning: Optional[str] = None
    key_indicators: Optional[list] = None  # List of strings

    model_config = ConfigDict(from_attributes=True)


class SentimentAnalysisResponse(BaseModel):
    """Schema for sentiment analysis - ALL FIELDS."""
    overall_sentiment: str
    confidence: float
    positive_score: Optional[float] = None
    negative_score: Optional[float] = None
    neutral_score: Optional[float] = None
    bias_detected: Optional[bool] = None
    bias_direction: Optional[str] = None
    bias_confidence: Optional[float] = None
    subjectivity_score: Optional[float] = None
    emotion_scores: Optional[dict] = None  # Dict of emotion -> score
    reasoning: Optional[str] = None
    key_phrases: Optional[list] = None  # List of strings

    model_config = ConfigDict(from_attributes=True)


class FinanceSentimentResponse(BaseModel):
    """Schema for finance sentiment analysis - ALL FIELDS."""
    market_sentiment: str
    market_confidence: float
    time_horizon: str
    uncertainty: float
    volatility: float
    economic_impact: float
    reasoning: str
    key_indicators: Optional[list] = None  # List of strings
    affected_sectors: Optional[list] = None  # List of strings
    affected_assets: Optional[list] = None  # List of strings

    model_config = ConfigDict(from_attributes=True)


class GeopoliticalSentimentResponse(BaseModel):
    """Schema for geopolitical sentiment analysis - ALL FIELDS."""
    stability_score: float
    security_relevance: float
    escalation_potential: float
    conflict_type: str
    time_horizon: str
    confidence: float
    regions_affected: Optional[List[str]] = None
    impact_beneficiaries: Optional[List[str]] = None
    impact_affected: Optional[List[str]] = None
    alliance_activation: Optional[List[str]] = None
    diplomatic_impact_global: Optional[float] = None
    diplomatic_impact_western: Optional[float] = None
    diplomatic_impact_regional: Optional[float] = None
    reasoning: str
    key_factors: Optional[list] = None  # List of strings

    model_config = ConfigDict(from_attributes=True)


class EventAnalysisResponse(BaseModel):
    """Schema for event analysis - ALL FIELDS."""
    primary_event: str
    location: Optional[str] = None
    confidence_overall: str
    risk_tags: List[str] = []
    actors: Union[dict, list, None] = None  # Can be dict (v1) or list (v2)
    headline: str
    source: str
    publisher_url: Optional[str] = None
    event_date: Optional[str] = None
    means: Union[List[str], str, None] = None  # Can be list or string
    impact: Union[dict, str, None] = None  # Can be dict (v1) or str (v2)
    claims: Optional[list] = None  # List of claim objects
    status: Union[dict, str, None] = None  # Can be dict (v1) or str (v2)
    publisher_context: Union[dict, str, None] = None  # Can be dict (v1) or str (v2)
    summary: str
    confidence_dimensions: Optional[dict] = None
    evidence: Optional[list] = None  # List of evidence objects

    model_config = ConfigDict(from_attributes=True)


class SummaryResponse(BaseModel):
    """Schema for article summary."""
    summary_type: str
    summary_text: str
    compression_ratio: Optional[float] = None
    original_length: Optional[int] = None
    summary_length: Optional[int] = None
    coherence_score: Optional[float] = None
    coverage_score: Optional[float] = None
    bullet_points: Union[dict, list, None] = None  # Can be dict (v1) or list (v2)
    key_sentences: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class TopicResponse(BaseModel):
    """Schema for topic classification."""
    topic: str
    relevance_score: float
    confidence: float
    parent_topic: Optional[str] = None
    topic_hierarchy: Optional[dict] = None
    keywords: Union[dict, list]  # Can be either dict or list (DB stores as list)
    keyword_scores: Optional[dict] = None
    is_primary: Optional[bool] = None
    reasoning: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FeedItemResponse(FeedItemBase):
    """Schema for feed item responses."""
    id: UUID
    feed_id: Optional[UUID] = None  # Nullable for non-RSS sources
    guid: Optional[str] = None
    content_hash: str
    scraped_at: Optional[datetime] = None
    scrape_status: Optional[str] = None
    scrape_word_count: Optional[int] = None
    scraped_metadata: Optional[dict] = None
    created_at: datetime

    # Source type discriminator (rss, perplexity_research, scraping, etc.)
    source_type: Optional[str] = Field("rss", description="Content source type")
    # Source-specific metadata (model, cost, query for Perplexity, etc.)
    source_metadata: Optional[dict] = Field(None, description="Source-specific metadata")
    # Parent article reference (for research/derived content)
    parent_article_id: Optional[UUID] = Field(None, description="Parent article for research")
    # Research articles linked to this article
    research_articles: Optional[List["FeedItemResponse"]] = Field(
        None,
        description="Research articles linked to this article"
    )

    # V2 Analysis data - from content-analysis-v2 API (LEGACY)
    pipeline_execution: Optional[dict] = None  # Full v2 analysis data

    # V3 Analysis data - from content-analysis-v3 service (ACTIVE)
    v3_analysis: Optional[dict] = None  # Full v3 analysis data (tier0, tier1, tier2)

    # Backward compatibility
    legacy_id: Optional[int] = Field(None, description="Legacy integer ID for backward compatibility")
    legacy_feed_id: Optional[int] = Field(None, description="Legacy feed integer ID for backward compatibility")

    model_config = ConfigDict(from_attributes=True)


class FeedItemWithFeedResponse(FeedItemResponse):
    """
    Extended feed item response that includes feed information.

    Used for cross-feed article listings where feed context is needed.
    """
    feed_name: str = Field(..., description="Name of the feed this item belongs to")


class FetchLogResponse(BaseModel):
    """Schema for fetch log responses."""
    id: UUID
    feed_id: UUID
    status: str
    items_found: int
    items_new: int
    duration: Optional[float] = None
    error: Optional[str] = None
    response_time_ms: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FeedHealthResponse(BaseModel):
    """Schema for feed health responses."""
    feed_id: UUID
    health_score: int
    consecutive_failures: int
    is_healthy: bool
    avg_response_time_ms: Optional[float] = None
    success_rate: float
    uptime_24h: float
    uptime_7d: float
    uptime_30d: float
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FeedQualityResponse(BaseModel):
    """Schema for feed quality score responses (legacy/basic)."""
    feed_id: UUID
    quality_score: float
    freshness_score: float
    consistency_score: float
    content_score: float
    reliability_score: float
    recommendations: List[str] = []
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComponentScoreDetails(BaseModel):
    """Detailed breakdown of a quality component."""
    score: float
    weight: float
    breakdown: Optional[dict] = None
    distribution: Optional[dict] = None
    distribution_bonus: Optional[float] = None
    red_flags: Optional[dict] = None
    articles_analyzed: Optional[int] = None


class QualityTrends(BaseModel):
    """Quality trend data."""
    trend_label: str  # improving, stable, declining, unknown
    trend_value: float
    quality_7d_vs_30d: float
    score_7d: Optional[float] = None
    score_30d: Optional[float] = None


class QualityDataStats(BaseModel):
    """Data completeness statistics."""
    articles_analyzed: int
    total_articles: int
    coverage_percentage: float
    date_range_days: int


class FeedQualityV2Response(BaseModel):
    """
    Comprehensive feed quality score response (V2).

    Combines article-level quality metrics from content-analysis-v2
    with feed-level operational metrics.
    """
    feed_id: str
    feed_name: str
    quality_score: float
    admiralty_code: AdmiraltyCodeData
    confidence: str  # high, medium, low
    confidence_score: float
    trend: str  # improving, stable, declining
    trend_direction: float

    # Component scores with detailed breakdowns
    component_scores: dict  # Keys: article_quality, source_credibility, operational, freshness_consistency

    # Quality distribution (article categories)
    quality_distribution: dict

    # Red flags and warnings
    red_flags: dict

    # Trends over time
    trends: QualityTrends

    # Data completeness
    data_stats: QualityDataStats

    # Actionable recommendations
    recommendations: List[str]

    calculated_at: str

    model_config = ConfigDict(from_attributes=True)


class BulkFetchRequest(BaseModel):
    """Schema for bulk fetch requests."""
    feed_ids: Optional[List[Union[UUID, int]]] = None  # If None, fetch all active feeds. Accepts both UUID and int for backward compatibility
    force: bool = False  # Force fetch even if recently fetched


class BulkFetchResponse(BaseModel):
    """Schema for bulk fetch responses."""
    total_feeds: int
    successful_fetches: int
    failed_fetches: int
    total_new_items: int
    details: List[dict] = []


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class FeedFilters(BaseModel):
    """Feed filtering parameters."""
    is_active: Optional[bool] = None
    status: Optional[FeedStatus] = None
    category: Optional[str] = None
    health_score_min: Optional[int] = Field(None, ge=0, le=100)
    health_score_max: Optional[int] = Field(None, ge=0, le=100)


# ========== Epic 0.4: Article Update Schemas ==========


class ArticleUpdateRequest(BaseModel):
    """
    Request schema for updating an article with version tracking.

    Epic 0.4: NewsML-G2 compliant article updates.
    """
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    description: Optional[str] = None
    change_type: str = Field(
        default="update",
        pattern="^(update|correction|withdrawal)$",
        description="Type of change: update, correction, or withdrawal"
    )
    change_reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="Reason for the change (recommended for corrections/withdrawals)"
    )


class ArticleVersionResponse(BaseModel):
    """
    Response schema for article version history.

    Epic 0.4: NewsML-G2 compliant version tracking.
    """
    id: UUID
    article_id: UUID
    version: int
    pub_status: str
    title: str
    content_hash: str
    change_type: str
    change_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
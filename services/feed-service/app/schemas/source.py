"""
Pydantic schemas for Unified Source Management API

Defines request/response schemas for:
- Sources: Master entity for news outlets (one per domain)
- SourceFeeds: Provider-specific feeds (RSS, MediaStack, etc.)
- SourceAssessments: Assessment history and trigger
"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator, model_validator
import re

from app.models.source import (
    SourceStatus,
    ScrapeStatus,
    PaywallType,
    ProviderType,
    CredibilityTier,
    AssessmentStatus,
)


# =============================================================================
# Helper Functions
# =============================================================================

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    # Remove protocol
    domain = re.sub(r'^https?://', '', url)
    # Remove www.
    domain = re.sub(r'^www\.', '', domain)
    # Remove path
    domain = domain.split('/')[0]
    # Remove port
    domain = domain.split(':')[0]
    return domain.lower()


# =============================================================================
# Source Schemas
# =============================================================================

class SourceBase(BaseModel):
    """Base schema for Source."""
    canonical_name: str = Field(..., min_length=1, max_length=200, description="Display name (e.g., Heise Online)")
    organization_name: Optional[str] = Field(None, max_length=200, description="Parent organization (e.g., Heise Medien)")
    description: Optional[str] = None
    homepage_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)

    # Categorization
    category: Optional[str] = Field(None, max_length=50, description="Primary category (general, business, tech, etc.)")
    country: Optional[str] = Field(None, max_length=5, description="ISO country code (de, us, gb)")
    language: Optional[str] = Field(None, max_length=5, description="ISO language code (de, en)")


class SourceCreate(SourceBase):
    """Schema for creating a new Source."""
    domain: str = Field(..., min_length=1, max_length=255, description="Unique domain identifier (e.g., heise.de)")

    # Optional initial scraping config
    scrape_method: str = Field(default="newspaper4k", description="Primary scrape method")
    paywall_type: PaywallType = Field(default=PaywallType.NONE)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
    requires_stealth: bool = False
    requires_proxy: bool = False

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Normalize domain: lowercase, remove www."""
        domain = v.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        # Basic domain validation
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z]{2,})+$', domain):
            raise ValueError('Invalid domain format')
        return domain


class SourceUpdate(BaseModel):
    """Schema for updating a Source (partial update)."""
    canonical_name: Optional[str] = Field(None, min_length=1, max_length=200)
    organization_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    homepage_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)

    # Status
    status: Optional[SourceStatus] = None
    is_active: Optional[bool] = None

    # Categorization
    category: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=5)
    language: Optional[str] = Field(None, max_length=5)

    # Scraping config
    scrape_method: Optional[str] = Field(None, max_length=50)
    fallback_methods: Optional[List[str]] = None
    scrape_status: Optional[ScrapeStatus] = None
    paywall_type: Optional[PaywallType] = None
    paywall_bypass_method: Optional[str] = Field(None, max_length=100)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=100)
    requires_stealth: Optional[bool] = None
    requires_proxy: Optional[bool] = None
    custom_headers: Optional[dict] = None

    # Notes
    notes: Optional[str] = None


class SourceAssessmentData(BaseModel):
    """Assessment data (shared between Source and history)."""
    assessment_status: Optional[str] = None
    assessment_date: Optional[datetime] = None
    credibility_tier: Optional[str] = Field(None, description="tier_1, tier_2, tier_3")
    reputation_score: Optional[int] = Field(None, ge=0, le=100)
    political_bias: Optional[str] = Field(None, description="left, center-left, center, center-right, right")
    founded_year: Optional[int] = Field(None, ge=1600, le=2100)
    organization_type: Optional[str] = Field(None, max_length=100)
    editorial_standards: Optional[dict] = None
    trust_ratings: Optional[dict] = None
    assessment_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScrapeConfigData(BaseModel):
    """Scraping configuration data."""
    scrape_method: str = "newspaper4k"
    fallback_methods: Optional[List[str]] = None
    scrape_status: str = ScrapeStatus.UNKNOWN.value
    paywall_type: str = PaywallType.NONE.value
    paywall_bypass_method: Optional[str] = None
    rate_limit_per_minute: int = 10
    requires_stealth: bool = False
    requires_proxy: bool = False
    custom_headers: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class ScrapeMetricsData(BaseModel):
    """Scraping metrics data."""
    scrape_success_rate: float = 0.0
    scrape_avg_response_ms: int = 0
    scrape_total_attempts: int = 0
    scrape_avg_word_count: int = 0
    scrape_avg_quality: float = 0.0
    scrape_last_success: Optional[datetime] = None
    scrape_last_failure: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SourceFeedSummary(BaseModel):
    """Summary of a SourceFeed for Source responses."""
    id: UUID
    provider_type: str
    provider_id: Optional[str] = None
    channel_name: Optional[str] = None
    feed_url: Optional[str] = None
    is_active: bool
    health_score: int
    total_items: int
    items_last_24h: int
    last_fetched_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SourceResponse(SourceBase):
    """Schema for Source responses."""
    id: UUID
    domain: str
    status: str
    is_active: bool

    # Assessment
    assessment: Optional[SourceAssessmentData] = None

    # Scraping
    scrape_config: ScrapeConfigData
    scrape_metrics: ScrapeMetricsData

    # Feeds summary
    feeds_count: int = Field(default=0, description="Total number of feeds")
    active_feeds_count: int = Field(default=0, description="Number of active feeds")
    feeds: Optional[List[SourceFeedSummary]] = Field(None, description="List of feeds (if requested)")

    # Meta
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_summary(cls, source, include_feeds: bool = False):
        """Create response from ORM model with computed fields."""
        assessment = SourceAssessmentData(
            assessment_status=source.assessment_status,
            assessment_date=source.assessment_date,
            credibility_tier=source.credibility_tier,
            reputation_score=source.reputation_score,
            political_bias=source.political_bias,
            founded_year=source.founded_year,
            organization_type=source.organization_type,
            editorial_standards=source.editorial_standards,
            trust_ratings=source.trust_ratings,
            assessment_summary=source.assessment_summary,
        ) if source.assessment_status else None

        scrape_config = ScrapeConfigData(
            scrape_method=source.scrape_method,
            fallback_methods=source.fallback_methods,
            scrape_status=source.scrape_status,
            paywall_type=source.paywall_type,
            paywall_bypass_method=source.paywall_bypass_method,
            rate_limit_per_minute=source.rate_limit_per_minute,
            requires_stealth=source.requires_stealth,
            requires_proxy=source.requires_proxy,
            custom_headers=source.custom_headers,
        )

        scrape_metrics = ScrapeMetricsData(
            scrape_success_rate=source.scrape_success_rate,
            scrape_avg_response_ms=source.scrape_avg_response_ms,
            scrape_total_attempts=source.scrape_total_attempts,
            scrape_avg_word_count=source.scrape_avg_word_count,
            scrape_avg_quality=source.scrape_avg_quality,
            scrape_last_success=source.scrape_last_success,
            scrape_last_failure=source.scrape_last_failure,
        )

        feeds_list = None
        if include_feeds and source.feeds:
            feeds_list = [
                SourceFeedSummary(
                    id=f.id,
                    provider_type=f.provider_type,
                    provider_id=f.provider_id,
                    channel_name=f.channel_name,
                    feed_url=f.feed_url,
                    is_active=f.is_active,
                    health_score=f.health_score,
                    total_items=f.total_items,
                    items_last_24h=f.items_last_24h,
                    last_fetched_at=f.last_fetched_at,
                )
                for f in source.feeds
            ]

        return cls(
            id=source.id,
            domain=source.domain,
            canonical_name=source.canonical_name,
            organization_name=source.organization_name,
            description=source.description,
            homepage_url=source.homepage_url,
            logo_url=source.logo_url,
            status=source.status,
            is_active=source.is_active,
            category=source.category,
            country=source.country,
            language=source.language,
            assessment=assessment,
            scrape_config=scrape_config,
            scrape_metrics=scrape_metrics,
            feeds_count=len(source.feeds) if source.feeds else 0,
            active_feeds_count=sum(1 for f in source.feeds if f.is_active) if source.feeds else 0,
            feeds=feeds_list,
            notes=source.notes,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )


class SourceListResponse(BaseModel):
    """Paginated list of sources."""
    items: List[SourceResponse]
    total: int
    skip: int
    limit: int


# =============================================================================
# SourceFeed Schemas
# =============================================================================

class SourceFeedBase(BaseModel):
    """Base schema for SourceFeed."""
    provider_type: ProviderType = Field(..., description="Feed provider type")
    provider_id: Optional[str] = Field(None, max_length=100, description="External provider ID")
    channel_name: Optional[str] = Field(None, max_length=100, description="Sub-channel name (e.g., Developer)")

    # RSS-specific
    feed_url: Optional[str] = Field(None, max_length=500, description="RSS/Atom feed URL")
    fetch_interval: int = Field(default=60, ge=5, le=1440, description="Fetch interval in minutes")

    # Analysis
    enable_analysis: bool = Field(default=True, description="Enable content analysis")


class SourceFeedCreate(SourceFeedBase):
    """Schema for creating a SourceFeed."""
    source_id: Optional[UUID] = Field(None, description="Source ID (optional if domain is provided)")
    domain: Optional[str] = Field(None, description="Source domain (auto-creates Source if not exists)")

    @model_validator(mode='after')
    def validate_rss_requires_url(self) -> 'SourceFeedCreate':
        """Validate feed_url is required for RSS feeds."""
        if self.provider_type == ProviderType.RSS and not self.feed_url:
            raise ValueError('feed_url is required for RSS feeds')
        return self

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v: Optional[str]) -> Optional[str]:
        """Normalize domain if provided."""
        if v:
            domain = v.lower().strip()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        return v


class SourceFeedUpdate(BaseModel):
    """Schema for updating a SourceFeed."""
    channel_name: Optional[str] = Field(None, max_length=100)
    fetch_interval: Optional[int] = Field(None, ge=5, le=1440)
    is_active: Optional[bool] = None
    enable_analysis: Optional[bool] = None


class SourceFeedResponse(SourceFeedBase):
    """Schema for SourceFeed responses."""
    id: UUID
    source_id: UUID

    # Status
    is_active: bool
    health_score: int
    consecutive_failures: int
    last_fetched_at: Optional[datetime] = None
    last_error: Optional[str] = None

    # HTTP caching
    etag: Optional[str] = None
    last_modified: Optional[str] = None

    # Statistics
    total_items: int
    items_last_24h: int

    # Meta
    discovered_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Source info (for convenience)
    source_domain: Optional[str] = None
    source_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SourceFeedWithSourceResponse(SourceFeedResponse):
    """SourceFeed response with full Source details."""
    source: Optional[SourceResponse] = None


class SourceFeedListResponse(BaseModel):
    """Paginated list of source feeds."""
    items: List[SourceFeedResponse]
    total: int
    skip: int
    limit: int


# =============================================================================
# Assessment Schemas
# =============================================================================

class SourceAssessmentTrigger(BaseModel):
    """Request to trigger source assessment."""
    force: bool = Field(default=False, description="Force re-assessment even if recently assessed")


class SourceAssessmentTriggerResponse(BaseModel):
    """Response after triggering assessment."""
    success: bool
    source_id: UUID
    domain: str
    message: str
    assessment_status: str


class SourceAssessmentHistoryResponse(BaseModel):
    """Response for assessment history entry."""
    id: UUID
    source_id: UUID
    assessment_status: str
    assessment_date: datetime
    credibility_tier: Optional[str] = None
    reputation_score: Optional[int] = None
    political_bias: Optional[str] = None
    founded_year: Optional[int] = None
    organization_type: Optional[str] = None
    editorial_standards: Optional[dict] = None
    trust_ratings: Optional[dict] = None
    assessment_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Filter & Pagination Schemas
# =============================================================================

class SourceFilters(BaseModel):
    """Source filtering parameters."""
    is_active: Optional[bool] = None
    status: Optional[SourceStatus] = None
    category: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    credibility_tier: Optional[CredibilityTier] = None
    organization_name: Optional[str] = None
    has_assessment: Optional[bool] = None
    scrape_status: Optional[ScrapeStatus] = None


class SourceFeedFilters(BaseModel):
    """SourceFeed filtering parameters."""
    source_id: Optional[UUID] = None
    provider_type: Optional[ProviderType] = None
    is_active: Optional[bool] = None
    health_score_min: Optional[int] = Field(None, ge=0, le=100)
    health_score_max: Optional[int] = Field(None, ge=0, le=100)


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkSourceCreate(BaseModel):
    """Bulk create sources from a list of domains."""
    domains: List[str] = Field(..., min_length=1, max_length=100)
    auto_discover_feeds: bool = Field(default=False, description="Try to discover RSS feeds for each domain")


class BulkSourceCreateResponse(BaseModel):
    """Response for bulk source creation."""
    created: int
    skipped: int  # Already exist
    failed: int
    details: List[dict]


class MediaStackSourceImport(BaseModel):
    """Import sources from MediaStack API."""
    countries: Optional[str] = Field(None, description="Filter by countries (comma-separated)")
    categories: Optional[str] = Field(None, description="Filter by categories (comma-separated)")
    languages: Optional[str] = Field(None, description="Filter by languages (comma-separated)")
    limit: int = Field(default=100, ge=1, le=1000)


class MediaStackSourceImportResponse(BaseModel):
    """Response for MediaStack import."""
    imported: int
    updated: int
    skipped: int
    details: List[dict]

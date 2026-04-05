"""
Tests for Unified Source Management API

Tests cover:
- Source CRUD operations
- SourceFeed CRUD operations
- Model validation
- Domain extraction and normalization
- Assessment operations
"""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    Source,
    SourceFeed,
    SourceAssessmentHistory,
    SourceStatus,
    ScrapeStatus,
    PaywallType,
    ProviderType,
    CredibilityTier,
    AssessmentStatus,
)
from app.schemas import (
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceFeedCreate,
    SourceFeedUpdate,
    extract_domain,
)


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestExtractDomain:
    """Tests for domain extraction helper."""

    def test_extract_domain_with_protocol(self):
        """Extract domain from URL with protocol."""
        assert extract_domain("https://example.com/path") == "example.com"
        assert extract_domain("http://example.com/path") == "example.com"

    def test_extract_domain_with_www(self):
        """Extract domain from URL with www prefix."""
        assert extract_domain("https://www.example.com") == "example.com"
        assert extract_domain("www.example.com/path") == "example.com"

    def test_extract_domain_with_port(self):
        """Extract domain from URL with port."""
        assert extract_domain("https://example.com:8080/path") == "example.com"

    def test_extract_domain_subdomain(self):
        """Extract domain with subdomain."""
        assert extract_domain("https://news.example.com") == "news.example.com"

    def test_extract_domain_case_insensitive(self):
        """Domain extraction should be case-insensitive."""
        assert extract_domain("https://EXAMPLE.COM") == "example.com"
        assert extract_domain("https://Example.Com") == "example.com"


# =============================================================================
# Source Model Tests
# =============================================================================

class TestSourceModel:
    """Tests for Source SQLAlchemy model."""

    @pytest_asyncio.fixture
    async def source(self, db_session: AsyncSession) -> Source:
        """Create a test source."""
        source = Source(
            domain="example.com",
            canonical_name="Example News",
            organization_name="Example Media Group",
            category="general",
            country="us",
            language="en",
            status=SourceStatus.ACTIVE.value,
            is_active=True,
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)
        return source

    @pytest.mark.asyncio
    async def test_create_source(self, db_session: AsyncSession):
        """Test creating a source."""
        source = Source(
            domain="test.com",
            canonical_name="Test Source",
            status=SourceStatus.ACTIVE.value,
        )
        db_session.add(source)
        await db_session.commit()

        result = await db_session.execute(
            select(Source).where(Source.domain == "test.com")
        )
        saved_source = result.scalar_one()

        assert saved_source.domain == "test.com"
        assert saved_source.canonical_name == "Test Source"
        assert saved_source.status == SourceStatus.ACTIVE.value
        assert saved_source.is_active is True
        assert saved_source.scrape_method == "newspaper4k"

    @pytest.mark.asyncio
    async def test_source_default_values(self, db_session: AsyncSession):
        """Test source default values."""
        source = Source(
            domain="defaults.com",
            canonical_name="Default Source",
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        assert source.status == SourceStatus.ACTIVE.value
        assert source.is_active is True
        assert source.scrape_method == "newspaper4k"
        assert source.scrape_status == ScrapeStatus.UNKNOWN.value
        assert source.paywall_type == PaywallType.NONE.value
        assert source.rate_limit_per_minute == 10
        assert source.requires_stealth is False
        assert source.requires_proxy is False
        assert source.scrape_success_rate == 0.0
        assert source.scrape_total_attempts == 0

    @pytest.mark.asyncio
    async def test_source_with_feeds(self, db_session: AsyncSession, source: Source):
        """Test source with associated feeds."""
        # Add RSS feed
        rss_feed = SourceFeed(
            source_id=source.id,
            provider_type=ProviderType.RSS.value,
            feed_url="https://example.com/rss.xml",
            is_active=True,
        )
        db_session.add(rss_feed)

        # Add MediaStack feed
        mediastack_feed = SourceFeed(
            source_id=source.id,
            provider_type=ProviderType.MEDIASTACK.value,
            provider_id="example-news",
            is_active=True,
        )
        db_session.add(mediastack_feed)

        await db_session.commit()
        await db_session.refresh(source)

        assert len(source.feeds) == 2
        assert source.active_feeds_count == 2
        assert source.rss_feeds_count == 1

    @pytest.mark.asyncio
    async def test_source_is_assessed(self, db_session: AsyncSession, source: Source):
        """Test is_assessed property."""
        assert source.is_assessed is False

        source.assessment_status = AssessmentStatus.COMPLETED.value
        await db_session.commit()
        await db_session.refresh(source)

        assert source.is_assessed is True


# =============================================================================
# SourceFeed Model Tests
# =============================================================================

class TestSourceFeedModel:
    """Tests for SourceFeed SQLAlchemy model."""

    @pytest_asyncio.fixture
    async def source(self, db_session: AsyncSession) -> Source:
        """Create a test source."""
        source = Source(
            domain="feedtest.com",
            canonical_name="Feed Test Source",
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)
        return source

    @pytest.mark.asyncio
    async def test_create_rss_feed(self, db_session: AsyncSession, source: Source):
        """Test creating an RSS feed."""
        feed = SourceFeed(
            source_id=source.id,
            provider_type=ProviderType.RSS.value,
            feed_url="https://feedtest.com/rss.xml",
            channel_name="Main Feed",
            fetch_interval=30,
        )
        db_session.add(feed)
        await db_session.commit()
        await db_session.refresh(feed)

        assert feed.provider_type == ProviderType.RSS.value
        assert feed.feed_url == "https://feedtest.com/rss.xml"
        assert feed.is_rss is True
        assert feed.is_active is True
        assert feed.health_score == 100
        assert feed.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_create_mediastack_feed(self, db_session: AsyncSession, source: Source):
        """Test creating a MediaStack feed."""
        feed = SourceFeed(
            source_id=source.id,
            provider_type=ProviderType.MEDIASTACK.value,
            provider_id="feedtest",
        )
        db_session.add(feed)
        await db_session.commit()
        await db_session.refresh(feed)

        assert feed.provider_type == ProviderType.MEDIASTACK.value
        assert feed.provider_id == "feedtest"
        assert feed.is_rss is False

    @pytest.mark.asyncio
    async def test_feed_is_healthy(self, db_session: AsyncSession, source: Source):
        """Test is_healthy property."""
        feed = SourceFeed(
            source_id=source.id,
            provider_type=ProviderType.RSS.value,
            feed_url="https://feedtest.com/rss.xml",
            health_score=100,
        )
        db_session.add(feed)
        await db_session.commit()

        assert feed.is_healthy is True

        feed.health_score = 40
        await db_session.commit()

        assert feed.is_healthy is False


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestSourceSchemas:
    """Tests for Source Pydantic schemas."""

    def test_source_create_valid(self):
        """Test valid source creation schema."""
        data = SourceCreate(
            domain="valid.com",
            canonical_name="Valid Source",
            category="tech",
            country="de",
            language="de",
        )
        assert data.domain == "valid.com"
        assert data.canonical_name == "Valid Source"

    def test_source_create_normalizes_domain(self):
        """Test that domain is normalized."""
        data = SourceCreate(
            domain="WWW.EXAMPLE.COM",
            canonical_name="Example",
        )
        assert data.domain == "example.com"

    def test_source_create_strips_www(self):
        """Test that www. prefix is stripped."""
        data = SourceCreate(
            domain="www.example.com",
            canonical_name="Example",
        )
        assert data.domain == "example.com"

    def test_source_create_invalid_domain(self):
        """Test invalid domain format."""
        with pytest.raises(ValueError, match="Invalid domain format"):
            SourceCreate(
                domain="not-a-domain",
                canonical_name="Invalid",
            )

    def test_source_update_partial(self):
        """Test partial source update."""
        data = SourceUpdate(
            canonical_name="Updated Name",
        )
        assert data.canonical_name == "Updated Name"
        assert data.description is None
        assert data.is_active is None


class TestSourceFeedSchemas:
    """Tests for SourceFeed Pydantic schemas."""

    def test_source_feed_create_rss(self):
        """Test RSS feed creation schema."""
        data = SourceFeedCreate(
            source_id=uuid4(),
            provider_type=ProviderType.RSS,
            feed_url="https://example.com/rss.xml",
            channel_name="Main",
        )
        assert data.provider_type == ProviderType.RSS
        assert data.feed_url == "https://example.com/rss.xml"

    def test_source_feed_create_rss_requires_url(self):
        """Test that RSS feeds require feed_url."""
        with pytest.raises(ValueError, match="feed_url is required for RSS feeds"):
            SourceFeedCreate(
                source_id=uuid4(),
                provider_type=ProviderType.RSS,
                # Missing feed_url
            )

    def test_source_feed_create_mediastack(self):
        """Test MediaStack feed creation schema."""
        data = SourceFeedCreate(
            source_id=uuid4(),
            provider_type=ProviderType.MEDIASTACK,
            provider_id="example-news",
        )
        assert data.provider_type == ProviderType.MEDIASTACK
        assert data.provider_id == "example-news"

    def test_source_feed_create_with_domain(self):
        """Test feed creation with domain (auto-create source)."""
        data = SourceFeedCreate(
            domain="newdomain.com",
            provider_type=ProviderType.RSS,
            feed_url="https://newdomain.com/rss.xml",
        )
        assert data.domain == "newdomain.com"
        assert data.source_id is None


# =============================================================================
# Assessment History Tests
# =============================================================================

class TestSourceAssessmentHistory:
    """Tests for SourceAssessmentHistory model."""

    @pytest_asyncio.fixture
    async def source(self, db_session: AsyncSession) -> Source:
        """Create a test source."""
        source = Source(
            domain="assessment-test.com",
            canonical_name="Assessment Test Source",
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)
        return source

    @pytest.mark.asyncio
    async def test_create_assessment_history(self, db_session: AsyncSession, source: Source):
        """Test creating assessment history."""
        history = SourceAssessmentHistory(
            source_id=source.id,
            assessment_status=AssessmentStatus.COMPLETED.value,
            credibility_tier=CredibilityTier.TIER_1.value,
            reputation_score=85,
            political_bias="center",
            assessment_summary="A highly credible news source.",
        )
        db_session.add(history)
        await db_session.commit()
        await db_session.refresh(history)

        assert history.source_id == source.id
        assert history.credibility_tier == CredibilityTier.TIER_1.value
        assert history.reputation_score == 85


# =============================================================================
# Enum Tests
# =============================================================================

class TestEnums:
    """Tests for Source-related enums."""

    def test_source_status_values(self):
        """Test SourceStatus enum values."""
        assert SourceStatus.ACTIVE.value == "active"
        assert SourceStatus.INACTIVE.value == "inactive"
        assert SourceStatus.BLOCKED.value == "blocked"

    def test_scrape_status_values(self):
        """Test ScrapeStatus enum values."""
        assert ScrapeStatus.WORKING.value == "working"
        assert ScrapeStatus.DEGRADED.value == "degraded"
        assert ScrapeStatus.BLOCKED.value == "blocked"
        assert ScrapeStatus.UNSUPPORTED.value == "unsupported"
        assert ScrapeStatus.UNKNOWN.value == "unknown"

    def test_paywall_type_values(self):
        """Test PaywallType enum values."""
        assert PaywallType.NONE.value == "none"
        assert PaywallType.SOFT.value == "soft"
        assert PaywallType.HARD.value == "hard"
        assert PaywallType.METERED.value == "metered"
        assert PaywallType.REGISTRATION.value == "registration"

    def test_provider_type_values(self):
        """Test ProviderType enum values."""
        assert ProviderType.RSS.value == "rss"
        assert ProviderType.MEDIASTACK.value == "mediastack"
        assert ProviderType.NEWSAPI.value == "newsapi"
        assert ProviderType.GDELT.value == "gdelt"
        assert ProviderType.MANUAL.value == "manual"

    def test_credibility_tier_values(self):
        """Test CredibilityTier enum values."""
        assert CredibilityTier.TIER_1.value == "tier_1"
        assert CredibilityTier.TIER_2.value == "tier_2"
        assert CredibilityTier.TIER_3.value == "tier_3"
        assert CredibilityTier.UNKNOWN.value == "unknown"

    def test_assessment_status_values(self):
        """Test AssessmentStatus enum values."""
        assert AssessmentStatus.PENDING.value == "pending"
        assert AssessmentStatus.IN_PROGRESS.value == "in_progress"
        assert AssessmentStatus.COMPLETED.value == "completed"
        assert AssessmentStatus.FAILED.value == "failed"


# =============================================================================
# Integration Tests (Model + Schema)
# =============================================================================

class TestSourceIntegration:
    """Integration tests for Source management."""

    @pytest_asyncio.fixture
    async def source_with_data(self, db_session: AsyncSession) -> Source:
        """Create a fully populated source."""
        source = Source(
            domain="integration-test.com",
            canonical_name="Integration Test Source",
            organization_name="Test Media Group",
            description="A test news source for integration testing",
            homepage_url="https://integration-test.com",
            category="tech",
            country="de",
            language="de",
            status=SourceStatus.ACTIVE.value,
            is_active=True,
            assessment_status=AssessmentStatus.COMPLETED.value,
            credibility_tier=CredibilityTier.TIER_1.value,
            reputation_score=90,
            political_bias="center",
            scrape_method="newspaper4k",
            scrape_status=ScrapeStatus.WORKING.value,
            paywall_type=PaywallType.NONE.value,
            rate_limit_per_minute=15,
            scrape_success_rate=95.5,
            scrape_total_attempts=100,
        )
        db_session.add(source)
        # Flush to ensure source.id is populated before creating feed
        await db_session.flush()

        # Add feeds using the relationship (SQLAlchemy will handle source_id)
        rss_feed = SourceFeed(
            source_id=source.id,
            provider_type=ProviderType.RSS.value,
            feed_url="https://integration-test.com/rss.xml",
            channel_name="Main",
            is_active=True,
            health_score=95,
            total_items=500,
            items_last_24h=20,
        )
        db_session.add(rss_feed)

        await db_session.commit()
        await db_session.refresh(source)
        return source

    @pytest.mark.asyncio
    async def test_source_response_from_orm(self, db_session: AsyncSession, source_with_data: Source):
        """Test creating SourceResponse from ORM model."""
        response = SourceResponse.from_orm_with_summary(source_with_data, include_feeds=True)

        assert response.domain == "integration-test.com"
        assert response.canonical_name == "Integration Test Source"
        assert response.feeds_count == 1
        assert response.active_feeds_count == 1
        assert len(response.feeds) == 1
        assert response.assessment is not None
        assert response.assessment.credibility_tier == CredibilityTier.TIER_1.value
        assert response.scrape_config.scrape_method == "newspaper4k"
        assert response.scrape_metrics.scrape_success_rate == 95.5

    @pytest.mark.asyncio
    async def test_source_cascade_delete(self, db_session: AsyncSession, source_with_data: Source):
        """Test that deleting a source cascades to feeds."""
        source_id = source_with_data.id

        # Verify feed exists
        feed_result = await db_session.execute(
            select(SourceFeed).where(SourceFeed.source_id == source_id)
        )
        assert feed_result.scalar_one_or_none() is not None

        # Delete source
        await db_session.delete(source_with_data)
        await db_session.commit()

        # Verify feed is also deleted
        feed_result = await db_session.execute(
            select(SourceFeed).where(SourceFeed.source_id == source_id)
        )
        assert feed_result.scalar_one_or_none() is None

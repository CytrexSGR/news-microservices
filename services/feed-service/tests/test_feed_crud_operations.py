"""
CRUD operations tests for Feed model

Tests database-level operations, transactions, and edge cases.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feed, FeedItem, FetchLog, FeedHealth, FeedStatus, FeedCategory


class TestFeedCreation:
    """Test feed creation operations."""

    @pytest.mark.asyncio
    async def test_create_basic_feed(self, db_session: AsyncSession):
        """Test creating a basic feed with required fields."""
        feed = Feed(
            url="https://example.com/rss.xml",
            name="Test Feed",
        )
        db_session.add(feed)
        await db_session.commit()

        # Verify creation
        assert feed.id is not None
        assert feed.url == "https://example.com/rss.xml"
        assert feed.name == "Test Feed"
        assert feed.is_active is True
        assert feed.status == FeedStatus.ACTIVE.value
        assert feed.health_score == 100
        assert feed.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_create_feed_with_all_fields(self, db_session: AsyncSession):
        """Test creating feed with all optional fields."""
        feed = Feed(
            url="https://news.example.com/feed",
            name="Complete Feed",
            description="A fully configured feed",
            category="Tech & Science",
            fetch_interval=120,
            scrape_full_content=True,
            scrape_method="playwright",
            enable_categorization=True,
            enable_finance_sentiment=True,
        )
        db_session.add(feed)
        await db_session.commit()

        assert feed.description == "A fully configured feed"
        assert feed.fetch_interval == 120
        assert feed.scrape_full_content is True
        assert feed.enable_categorization is True

    @pytest.mark.asyncio
    async def test_create_feed_unique_url_constraint(self, db_session: AsyncSession):
        """Test that duplicate URLs are rejected by database."""
        url = "https://unique-example.com/feed.xml"

        feed1 = Feed(url=url, name="Feed 1")
        db_session.add(feed1)
        await db_session.commit()

        # Try to create duplicate
        feed2 = Feed(url=url, name="Feed 2")
        db_session.add(feed2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_create_feed_with_timestamps(self, db_session: AsyncSession):
        """Test that timestamps are automatically set."""
        feed = Feed(
            url="https://example.com/feed.xml",
            name="Timestamp Feed",
        )
        db_session.add(feed)
        await db_session.commit()

        assert feed.created_at is not None
        assert feed.updated_at is not None
        assert isinstance(feed.created_at, datetime)
        assert feed.created_at.tzinfo is not None  # Has timezone

    @pytest.mark.asyncio
    async def test_feed_default_values(self, db_session: AsyncSession):
        """Test all default values are correctly set."""
        feed = Feed(
            url="https://example.com/feed.xml",
            name="Default Values Feed",
        )
        db_session.add(feed)
        await db_session.commit()

        # Check all defaults
        assert feed.is_active is True
        assert feed.status == FeedStatus.ACTIVE.value
        assert feed.health_score == 100
        assert feed.consecutive_failures == 0
        assert feed.total_items == 0
        assert feed.items_last_24h == 0
        assert feed.scrape_full_content is False
        assert feed.scrape_failure_count == 0
        assert feed.enable_categorization is False
        assert feed.enable_analysis_v2 is False


class TestFeedUpdates:
    """Test feed update operations."""

    @pytest.mark.asyncio
    async def test_update_feed_name(self, db_session: AsyncSession):
        """Test updating feed name."""
        feed = Feed(url="https://example.com/feed.xml", name="Original Name")
        db_session.add(feed)
        await db_session.commit()

        feed.name = "Updated Name"
        await db_session.commit()

        # Verify update
        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated_feed = result.scalar_one()
        assert updated_feed.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_feed_status(self, db_session: AsyncSession):
        """Test updating feed status."""
        feed = Feed(url="https://example.com/feed.xml", name="Status Feed")
        db_session.add(feed)
        await db_session.commit()

        feed.status = FeedStatus.PAUSED.value
        feed.is_active = False
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated_feed = result.scalar_one()
        assert updated_feed.status == FeedStatus.PAUSED.value
        assert updated_feed.is_active is False

    @pytest.mark.asyncio
    async def test_update_feed_health_metrics(self, db_session: AsyncSession):
        """Test updating health-related fields."""
        feed = Feed(url="https://example.com/feed.xml", name="Health Feed")
        db_session.add(feed)
        await db_session.commit()

        feed.health_score = 75
        feed.consecutive_failures = 3
        feed.last_error_message = "Connection timeout"
        feed.last_error_at = datetime.now(timezone.utc)
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated_feed = result.scalar_one()
        assert updated_feed.health_score == 75
        assert updated_feed.consecutive_failures == 3
        assert updated_feed.last_error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_update_feed_fetch_metadata(self, db_session: AsyncSession):
        """Test updating fetch-related metadata."""
        feed = Feed(url="https://example.com/feed.xml", name="Fetch Feed")
        db_session.add(feed)
        await db_session.commit()

        now = datetime.now(timezone.utc)
        feed.last_fetched_at = now
        feed.etag = '"12345abcde"'
        feed.last_modified = "Mon, 01 Jan 2024 12:00:00 GMT"
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated_feed = result.scalar_one()
        assert updated_feed.etag == '"12345abcde"'
        assert updated_feed.last_modified == "Mon, 01 Jan 2024 12:00:00 GMT"

    @pytest.mark.asyncio
    async def test_update_feed_scraping_config(self, db_session: AsyncSession):
        """Test updating scraping configuration."""
        feed = Feed(url="https://example.com/feed.xml", name="Scrape Feed")
        db_session.add(feed)
        await db_session.commit()

        feed.scrape_full_content = True
        feed.scrape_method = "playwright"
        feed.scrape_failure_threshold = 8
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated_feed = result.scalar_one()
        assert updated_feed.scrape_full_content is True
        assert updated_feed.scrape_method == "playwright"
        assert updated_feed.scrape_failure_threshold == 8

    @pytest.mark.asyncio
    async def test_update_updated_at_timestamp(self, db_session: AsyncSession):
        """Test that updated_at is automatically updated."""
        feed = Feed(url="https://example.com/feed.xml", name="Timestamp Feed")
        db_session.add(feed)
        await db_session.commit()

        original_updated_at = feed.updated_at

        # Wait a moment and update
        await db_session.refresh(feed)
        feed.name = "Updated Name"
        await db_session.commit()

        assert feed.updated_at > original_updated_at


class TestFeedDeletion:
    """Test feed deletion and cascading."""

    @pytest.mark.asyncio
    async def test_delete_feed(self, db_session: AsyncSession):
        """Test deleting a feed."""
        feed = Feed(url="https://example.com/feed.xml", name="To Delete")
        db_session.add(feed)
        await db_session.commit()

        feed_id = feed.id

        await db_session.delete(feed)
        await db_session.commit()

        # Verify deletion
        result = await db_session.execute(select(Feed).where(Feed.id == feed_id))
        deleted_feed = result.scalar_one_or_none()
        assert deleted_feed is None

    @pytest.mark.asyncio
    async def test_delete_feed_cascade_items(self, db_session: AsyncSession):
        """Test that deleting feed cascades to items."""
        feed = Feed(url="https://example.com/feed.xml", name="Parent Feed")
        db_session.add(feed)
        await db_session.commit()

        # Add items
        item1 = FeedItem(
            feed_id=feed.id,
            title="Item 1",
            link="https://example.com/item1",
            content_hash="hash1",
        )
        item2 = FeedItem(
            feed_id=feed.id,
            title="Item 2",
            link="https://example.com/item2",
            content_hash="hash2",
        )
        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        feed_id = feed.id

        # Delete feed
        await db_session.delete(feed)
        await db_session.commit()

        # Verify items are deleted
        result = await db_session.execute(select(FeedItem).where(FeedItem.feed_id == feed_id))
        items = result.scalars().all()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_delete_feed_cascade_fetch_logs(self, db_session: AsyncSession):
        """Test that deleting feed cascades to fetch logs."""
        feed = Feed(url="https://example.com/feed.xml", name="Feed with Logs")
        db_session.add(feed)
        await db_session.commit()

        # Add fetch logs
        log1 = FetchLog(feed_id=feed.id, status="success", items_found=5, items_new=2)
        log2 = FetchLog(feed_id=feed.id, status="error", items_found=0, items_new=0)
        db_session.add(log1)
        db_session.add(log2)
        await db_session.commit()

        feed_id = feed.id

        # Delete feed
        await db_session.delete(feed)
        await db_session.commit()

        # Verify logs are deleted
        result = await db_session.execute(select(FetchLog).where(FetchLog.feed_id == feed_id))
        logs = result.scalars().all()
        assert len(logs) == 0


class TestFeedReads:
    """Test feed read operations."""

    @pytest.mark.asyncio
    async def test_read_feed_by_id(self, db_session: AsyncSession):
        """Test reading feed by ID."""
        feed = Feed(url="https://example.com/feed.xml", name="Read Feed")
        db_session.add(feed)
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        fetched = result.scalar_one()
        assert fetched.id == feed.id
        assert fetched.name == "Read Feed"

    @pytest.mark.asyncio
    async def test_read_feed_by_url(self, db_session: AsyncSession):
        """Test reading feed by URL (unique index)."""
        url = "https://example.com/unique-feed.xml"
        feed = Feed(url=url, name="Unique Feed")
        db_session.add(feed)
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.url == url))
        fetched = result.scalar_one_or_none()
        assert fetched is not None
        assert fetched.url == url

    @pytest.mark.asyncio
    async def test_list_all_feeds(self, db_session: AsyncSession):
        """Test listing all feeds."""
        feeds = [
            Feed(url=f"https://example.com/feed{i}.xml", name=f"Feed {i}")
            for i in range(5)
        ]
        for feed in feeds:
            db_session.add(feed)
        await db_session.commit()

        result = await db_session.execute(select(Feed))
        all_feeds = result.scalars().all()
        assert len(all_feeds) == 5

    @pytest.mark.asyncio
    async def test_filter_feeds_by_active_status(self, db_session: AsyncSession):
        """Test filtering feeds by active status."""
        active = Feed(url="https://example.com/active.xml", name="Active", is_active=True)
        inactive = Feed(url="https://example.com/inactive.xml", name="Inactive", is_active=False)
        db_session.add(active)
        db_session.add(inactive)
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.is_active == True))
        active_feeds = result.scalars().all()
        assert len(active_feeds) == 1
        assert active_feeds[0].name == "Active"

    @pytest.mark.asyncio
    async def test_filter_feeds_by_status(self, db_session: AsyncSession):
        """Test filtering feeds by status enum."""
        active_feed = Feed(url="https://example.com/active.xml", name="Active Feed", status=FeedStatus.ACTIVE.value)
        paused_feed = Feed(url="https://example.com/paused.xml", name="Paused Feed", status=FeedStatus.PAUSED.value)
        error_feed = Feed(url="https://example.com/error.xml", name="Error Feed", status=FeedStatus.ERROR.value)

        db_session.add(active_feed)
        db_session.add(paused_feed)
        db_session.add(error_feed)
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.status == FeedStatus.PAUSED.value))
        paused = result.scalars().all()
        assert len(paused) == 1
        assert paused[0].status == FeedStatus.PAUSED.value

    @pytest.mark.asyncio
    async def test_filter_feeds_by_health_score(self, db_session: AsyncSession):
        """Test filtering feeds by health score."""
        healthy = Feed(url="https://example.com/healthy.xml", name="Healthy", health_score=95)
        unhealthy = Feed(url="https://example.com/unhealthy.xml", name="Unhealthy", health_score=30)

        db_session.add(healthy)
        db_session.add(unhealthy)
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.health_score >= 80))
        good_health = result.scalars().all()
        assert len(good_health) == 1
        assert good_health[0].health_score == 95

    @pytest.mark.asyncio
    async def test_order_feeds_by_created_date(self, db_session: AsyncSession):
        """Test ordering feeds by creation date."""
        feed1 = Feed(url="https://example.com/feed1.xml", name="Feed 1")
        feed2 = Feed(url="https://example.com/feed2.xml", name="Feed 2")
        feed3 = Feed(url="https://example.com/feed3.xml", name="Feed 3")

        db_session.add(feed1)
        await db_session.commit()

        db_session.add(feed2)
        await db_session.commit()

        db_session.add(feed3)
        await db_session.commit()

        result = await db_session.execute(
            select(Feed).order_by(Feed.created_at.asc())
        )
        ordered = result.scalars().all()
        assert ordered[0].name == "Feed 1"
        assert ordered[1].name == "Feed 2"
        assert ordered[2].name == "Feed 3"


class TestFeedStatistics:
    """Test feed statistics updates."""

    @pytest.mark.asyncio
    async def test_update_total_items_count(self, db_session: AsyncSession):
        """Test updating total items count."""
        feed = Feed(url="https://example.com/feed.xml", name="Stat Feed")
        db_session.add(feed)
        await db_session.commit()

        feed.total_items = 42
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated = result.scalar_one()
        assert updated.total_items == 42

    @pytest.mark.asyncio
    async def test_update_items_24h_count(self, db_session: AsyncSession):
        """Test updating items in last 24 hours count."""
        feed = Feed(url="https://example.com/feed.xml", name="24h Feed")
        db_session.add(feed)
        await db_session.commit()

        feed.items_last_24h = 15
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated = result.scalar_one()
        assert updated.items_last_24h == 15

    @pytest.mark.asyncio
    async def test_update_quality_score(self, db_session: AsyncSession):
        """Test updating quality score."""
        feed = Feed(url="https://example.com/feed.xml", name="Quality Feed")
        db_session.add(feed)
        await db_session.commit()

        feed.quality_score = 85
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated = result.scalar_one()
        assert updated.quality_score == 85


class TestFeedAssessment:
    """Test feed assessment fields."""

    @pytest.mark.asyncio
    async def test_update_assessment_fields(self, db_session: AsyncSession):
        """Test updating assessment-related fields."""
        feed = Feed(url="https://example.com/feed.xml", name="Assessment Feed")
        db_session.add(feed)
        await db_session.commit()

        feed.assessment_status = "completed"
        feed.assessment_date = datetime.now(timezone.utc)
        feed.credibility_tier = "tier_1"
        feed.reputation_score = 85
        feed.founded_year = 2010
        feed.organization_type = "news_agency"
        feed.political_bias = "center"
        feed.editorial_standards = {
            "fact_checking_level": "high",
            "corrections_policy": "published",
        }
        feed.trust_ratings = {
            "media_bias_fact_check": "left-center",
            "newsguard_score": 87,
        }
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        updated = result.scalar_one()
        assert updated.assessment_status == "completed"
        assert updated.credibility_tier == "tier_1"
        assert updated.reputation_score == 85
        assert updated.editorial_standards["fact_checking_level"] == "high"

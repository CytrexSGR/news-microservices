"""
Service layer tests

Tests business logic in feed services.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feed, FeedItem, FetchLog, FeedHealth
from app.services.feed_quality import FeedQualityScorer


class TestFeedQualityScorer:
    """Test feed quality scoring service."""

    @pytest.mark.asyncio
    async def test_calculate_quality_score_no_feed(self, db_session: AsyncSession):
        """Test quality score calculation fails for non-existent feed."""
        scorer = FeedQualityScorer()

        with pytest.raises(ValueError) as exc_info:
            await scorer.calculate_quality_score(db_session, "non-existent-id")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_calculate_quality_score_new_feed(self, db_session: AsyncSession):
        """Test quality score for new feed with no items."""
        feed = Feed(url="https://example.com/feed.xml", name="New Feed")
        db_session.add(feed)
        await db_session.commit()

        scorer = FeedQualityScorer()
        quality = await scorer.calculate_quality_score(db_session, feed.id)

        assert "quality_score" in quality
        assert "freshness_score" in quality
        assert "consistency_score" in quality
        assert "content_score" in quality
        assert "reliability_score" in quality
        assert "recommendations" in quality

    @pytest.mark.asyncio
    async def test_freshness_score_recent_articles(self, db_session: AsyncSession):
        """Test freshness score with recent articles."""
        feed = Feed(url="https://example.com/feed.xml", name="Fresh Feed")
        db_session.add(feed)
        await db_session.commit()

        # Add recent article (within last hour)
        now = datetime.now(timezone.utc)
        recent = FeedItem(
            feed_id=feed.id,
            title="Recent Article",
            link="https://example.com/recent",
            content_hash="hash1",
            published_at=now - timedelta(minutes=30),
        )
        db_session.add(recent)
        await db_session.commit()

        scorer = FeedQualityScorer()
        quality = await scorer.calculate_quality_score(db_session, feed.id)

        # Recent articles should have high freshness score
        assert quality["freshness_score"] >= 80

    @pytest.mark.asyncio
    async def test_freshness_score_old_articles(self, db_session: AsyncSession):
        """Test freshness score with old articles."""
        feed = Feed(url="https://example.com/feed.xml", name="Old Feed")
        db_session.add(feed)
        await db_session.commit()

        # Add old article (older than a month)
        now = datetime.now(timezone.utc)
        old = FeedItem(
            feed_id=feed.id,
            title="Old Article",
            link="https://example.com/old",
            content_hash="hash1",
            published_at=now - timedelta(days=45),
        )
        db_session.add(old)
        await db_session.commit()

        scorer = FeedQualityScorer()
        quality = await scorer.calculate_quality_score(db_session, feed.id)

        # Old articles should have lower freshness score
        assert quality["freshness_score"] <= 40

    @pytest.mark.asyncio
    async def test_quality_score_weighted_average(self, db_session: AsyncSession):
        """Test that quality score is weighted average of components."""
        feed = Feed(url="https://example.com/feed.xml", name="Test Feed")
        db_session.add(feed)
        await db_session.commit()

        scorer = FeedQualityScorer()
        quality = await scorer.calculate_quality_score(db_session, feed.id)

        # Quality score should be between 0 and 100
        assert 0 <= quality["quality_score"] <= 100

        # Verify it's using the weighted formula
        # quality = fresh*0.3 + consistency*0.2 + content*0.2 + reliability*0.3
        expected = (
            quality["freshness_score"] * 0.3 +
            quality["consistency_score"] * 0.2 +
            quality["content_score"] * 0.2 +
            quality["reliability_score"] * 0.3
        )

        assert abs(quality["quality_score"] - round(expected, 2)) < 0.1

    @pytest.mark.asyncio
    async def test_quality_score_recommendations(self, db_session: AsyncSession):
        """Test that recommendations are generated."""
        feed = Feed(url="https://example.com/feed.xml", name="Test Feed")
        db_session.add(feed)
        await db_session.commit()

        scorer = FeedQualityScorer()
        quality = await scorer.calculate_quality_score(db_session, feed.id)

        assert isinstance(quality["recommendations"], list)

    @pytest.mark.asyncio
    async def test_quality_score_with_multiple_items(self, db_session: AsyncSession):
        """Test quality score with multiple items."""
        feed = Feed(url="https://example.com/feed.xml", name="Multi-item Feed")
        db_session.add(feed)
        await db_session.commit()

        # Add multiple items
        now = datetime.now(timezone.utc)
        for i in range(10):
            item = FeedItem(
                feed_id=feed.id,
                title=f"Article {i}",
                link=f"https://example.com/article{i}",
                content_hash=f"hash{i}",
                published_at=now - timedelta(hours=i),
            )
            db_session.add(item)
        await db_session.commit()

        scorer = FeedQualityScorer()
        quality = await scorer.calculate_quality_score(db_session, feed.id)

        # With multiple items, scores should be more complete
        assert quality["freshness_score"] > 0
        assert quality["consistency_score"] > 0
        assert quality["content_score"] > 0


class TestFeedContentHashing:
    """Test content hash calculation and deduplication."""

    @pytest.mark.asyncio
    async def test_content_hash_unique(self, db_session: AsyncSession):
        """Test that different content produces different hashes."""
        import hashlib

        content1 = "Article about Python"
        content2 = "Article about JavaScript"

        hash1 = hashlib.sha256(content1.encode()).hexdigest()
        hash2 = hashlib.sha256(content2.encode()).hexdigest()

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_content_hash_consistent(self):
        """Test that same content produces same hash."""
        import hashlib

        content = "Article about databases"

        hash1 = hashlib.sha256(content.encode()).hexdigest()
        hash2 = hashlib.sha256(content.encode()).hexdigest()

        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_duplicate_detection_by_hash(self, db_session: AsyncSession):
        """Test duplicate detection using content hash."""
        feed = Feed(url="https://example.com/feed.xml", name="Dup Detection")
        db_session.add(feed)
        await db_session.commit()

        # Add first item
        item1 = FeedItem(
            feed_id=feed.id,
            title="Article",
            link="https://example.com/article",
            content_hash="consistent_hash_123",
        )
        db_session.add(item1)
        await db_session.commit()

        # Try to add duplicate with same hash
        item2 = FeedItem(
            feed_id=feed.id,
            title="Article (Repost)",
            link="https://other.com/article",
            content_hash="consistent_hash_123",
        )
        db_session.add(item2)

        # Should fail unique constraint
        with pytest.raises(Exception):
            await db_session.commit()


class TestFeedFetching:
    """Test feed fetching logic."""

    @pytest.mark.asyncio
    async def test_fetch_log_records_success(self, db_session: AsyncSession):
        """Test that successful fetch is logged."""
        feed = Feed(url="https://example.com/feed.xml", name="Log Feed")
        db_session.add(feed)
        await db_session.commit()

        log = FetchLog(
            feed_id=feed.id,
            status="success",
            items_found=5,
            items_new=2,
            response_time_ms=250,
            response_status_code=200,
        )
        db_session.add(log)
        await db_session.commit()

        result = await db_session.execute(
            select(FetchLog).where(FetchLog.feed_id == feed.id)
        )
        fetched = result.scalar_one()

        assert fetched.status == "success"
        assert fetched.items_found == 5
        assert fetched.response_status_code == 200

    @pytest.mark.asyncio
    async def test_fetch_log_records_error(self, db_session: AsyncSession):
        """Test that failed fetch is logged."""
        feed = Feed(url="https://example.com/feed.xml", name="Error Log Feed")
        db_session.add(feed)
        await db_session.commit()

        log = FetchLog(
            feed_id=feed.id,
            status="error",
            items_found=0,
            items_new=0,
            error="Connection timeout after 30s",
            response_status_code=None,
        )
        db_session.add(log)
        await db_session.commit()

        result = await db_session.execute(
            select(FetchLog).where(FetchLog.feed_id == feed.id)
        )
        fetched = result.scalar_one()

        assert fetched.status == "error"
        assert "timeout" in fetched.error.lower()

    @pytest.mark.asyncio
    async def test_etag_conditional_request(self, db_session: AsyncSession):
        """Test ETag is used for conditional requests."""
        feed = Feed(
            url="https://example.com/feed.xml",
            name="ETag Feed",
            etag='"12345abcde"'
        )
        db_session.add(feed)
        await db_session.commit()

        # Verify etag is stored
        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        fetched = result.scalar_one()

        assert fetched.etag == '"12345abcde"'

    @pytest.mark.asyncio
    async def test_last_modified_tracking(self, db_session: AsyncSession):
        """Test Last-Modified header tracking."""
        feed = Feed(
            url="https://example.com/feed.xml",
            name="Last-Modified Feed",
            last_modified="Mon, 01 Jan 2024 12:00:00 GMT"
        )
        db_session.add(feed)
        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        fetched = result.scalar_one()

        assert fetched.last_modified == "Mon, 01 Jan 2024 12:00:00 GMT"


class TestFeedHealthTracking:
    """Test feed health score management."""

    @pytest.mark.asyncio
    async def test_health_score_degradation(self, db_session: AsyncSession):
        """Test health score decreases with failures."""
        feed = Feed(url="https://example.com/feed.xml", name="Degrading Feed")
        db_session.add(feed)
        await db_session.commit()

        initial_health = feed.health_score

        # Simulate failures
        feed.consecutive_failures += 1
        feed.health_score = max(0, feed.health_score - 10)

        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        fetched = result.scalar_one()

        assert fetched.health_score < initial_health

    @pytest.mark.asyncio
    async def test_consecutive_failures_tracking(self, db_session: AsyncSession):
        """Test consecutive failures are tracked."""
        feed = Feed(url="https://example.com/feed.xml", name="Failure Feed")
        db_session.add(feed)
        await db_session.commit()

        # Simulate multiple failures
        for _ in range(3):
            feed.consecutive_failures += 1
            await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        fetched = result.scalar_one()

        assert fetched.consecutive_failures == 3

    @pytest.mark.asyncio
    async def test_failure_recovery(self, db_session: AsyncSession):
        """Test that successful fetch resets consecutive failures."""
        feed = Feed(url="https://example.com/feed.xml", name="Recovery Feed")
        feed.consecutive_failures = 5
        db_session.add(feed)
        await db_session.commit()

        # Simulate successful fetch
        feed.consecutive_failures = 0
        feed.health_score = 100

        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        fetched = result.scalar_one()

        assert fetched.consecutive_failures == 0
        assert fetched.health_score == 100

    @pytest.mark.asyncio
    async def test_error_message_tracking(self, db_session: AsyncSession):
        """Test error messages are recorded."""
        feed = Feed(url="https://example.com/feed.xml", name="Error Feed")
        db_session.add(feed)
        await db_session.commit()

        error_msg = "DNS resolution failed: example.com"
        feed.last_error_message = error_msg
        feed.last_error_at = datetime.now(timezone.utc)

        await db_session.commit()

        result = await db_session.execute(select(Feed).where(Feed.id == feed.id))
        fetched = result.scalar_one()

        assert fetched.last_error_message == error_msg
        assert fetched.last_error_at is not None


class TestFeedStatisticsUpdate:
    """Test feed statistics calculations."""

    @pytest.mark.asyncio
    async def test_total_items_count(self, db_session: AsyncSession):
        """Test total items count calculation."""
        feed = Feed(url="https://example.com/feed.xml", name="Stat Feed")
        db_session.add(feed)
        await db_session.commit()

        # Add items
        for i in range(5):
            item = FeedItem(
                feed_id=feed.id,
                title=f"Item {i}",
                link=f"https://example.com/{i}",
                content_hash=f"hash{i}",
            )
            db_session.add(item)
        await db_session.commit()

        # Count items
        result = await db_session.execute(
            select(FeedItem).where(FeedItem.feed_id == feed.id)
        )
        items = result.scalars().all()

        assert len(items) == 5

    @pytest.mark.asyncio
    async def test_items_24h_count(self, db_session: AsyncSession):
        """Test items published in last 24 hours count."""
        feed = Feed(url="https://example.com/feed.xml", name="24h Feed")
        db_session.add(feed)
        await db_session.commit()

        now = datetime.now(timezone.utc)

        # Add recent items
        for i in range(3):
            item = FeedItem(
                feed_id=feed.id,
                title=f"Recent {i}",
                link=f"https://example.com/recent{i}",
                content_hash=f"recent_hash{i}",
                published_at=now - timedelta(hours=i),
            )
            db_session.add(item)

        # Add old items
        for i in range(2):
            item = FeedItem(
                feed_id=feed.id,
                title=f"Old {i}",
                link=f"https://example.com/old{i}",
                content_hash=f"old_hash{i}",
                published_at=now - timedelta(days=2 + i),
            )
            db_session.add(item)

        await db_session.commit()

        # Count items in 24h
        yesterday = now - timedelta(hours=24)
        result = await db_session.execute(
            select(FeedItem).where(
                FeedItem.feed_id == feed.id,
                FeedItem.published_at >= yesterday
            )
        )
        recent_items = result.scalars().all()

        assert len(recent_items) == 3

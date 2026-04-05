"""
Unit tests for FeedMonitor service.

Tests cover:
- Feed monitor lifecycle (start/stop)
- Fetching active feeds from Feed Service
- Fetching articles since last check
- Scheduling analysis jobs based on feed category
- Feed schedule state tracking
- Error handling (HTTP errors, invalid responses)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.feed_monitor import FeedMonitor, feed_monitor
from database.models import FeedScheduleState, AnalysisJobQueue, JobType, JobStatus


# ============================================================================
# Feed Monitor Lifecycle Tests
# ============================================================================

class TestFeedMonitorLifecycle:
    """Test feed monitor start/stop lifecycle"""

    @pytest.mark.asyncio
    async def test_start_feed_monitor(self):
        """Test successful feed monitor start"""
        monitor = FeedMonitor()

        assert not monitor.is_running()

        await monitor.start()

        assert monitor.is_running()
        assert monitor.http_client is not None

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_stop_feed_monitor(self):
        """Test successful feed monitor stop"""
        monitor = FeedMonitor()
        await monitor.start()

        assert monitor.is_running()

        await monitor.stop()

        assert not monitor.is_running()
        assert monitor.http_client is None

    @pytest.mark.asyncio
    async def test_start_already_running(self, caplog):
        """Test starting an already running monitor"""
        monitor = FeedMonitor()
        await monitor.start()

        await monitor.start()

        assert "already running" in caplog.text
        await monitor.stop()


# ============================================================================
# Feed Fetching Tests
# ============================================================================

class TestFeedFetching:
    """Test fetching feeds from Feed Service"""

    @pytest.mark.asyncio
    async def test_fetch_active_feeds_success(
        self,
        mock_feed_service_response
    ):
        """Test successfully fetching active feeds"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=mock_feed_service_response)
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-type": "application/json"}

        mock_client.get = AsyncMock(return_value=mock_response)
        monitor.http_client = mock_client

        feeds = await monitor._fetch_active_feeds()

        assert len(feeds) == 2
        assert feeds[0]["id"] == "feed-123"
        assert feeds[1]["id"] == "feed-456"

    @pytest.mark.asyncio
    async def test_fetch_active_feeds_empty(self):
        """Test fetching when no active feeds exist"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-type": "application/json"}

        mock_client.get = AsyncMock(return_value=mock_response)
        monitor.http_client = mock_client

        feeds = await monitor._fetch_active_feeds()

        assert len(feeds) == 0

    @pytest.mark.asyncio
    async def test_fetch_active_feeds_http_error(self, caplog):
        """Test handling HTTP error when fetching feeds"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )
        monitor.http_client = mock_client

        feeds = await monitor._fetch_active_feeds()

        assert len(feeds) == 0
        assert "HTTP error" in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_active_feeds_invalid_response(self, caplog):
        """Test handling invalid response format"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"error": "Invalid format"})
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-type": "application/json"}

        mock_client.get = AsyncMock(return_value=mock_response)
        monitor.http_client = mock_client

        feeds = await monitor._fetch_active_feeds()

        assert len(feeds) == 0
        assert "Unexpected response format" in caplog.text


# ============================================================================
# Article Fetching Tests
# ============================================================================

class TestArticleFetching:
    """Test fetching articles from Feed Service"""

    @pytest.mark.asyncio
    async def test_fetch_feed_articles_success(
        self,
        mock_articles_response
    ):
        """Test successfully fetching articles"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=mock_articles_response)
        mock_response.raise_for_status = MagicMock()

        mock_client.get = AsyncMock(return_value=mock_response)
        monitor.http_client = mock_client

        articles = await monitor._fetch_feed_articles("feed-123", None)

        assert len(articles) == 2
        assert articles[0]["id"] == "article-123"
        assert articles[1]["id"] == "article-456"

    @pytest.mark.asyncio
    async def test_fetch_feed_articles_with_since_param(self):
        """Test fetching articles with since parameter"""
        monitor = FeedMonitor()
        monitor._is_running = True

        since = datetime.now(timezone.utc) - timedelta(hours=1)

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()

        mock_client.get = AsyncMock(return_value=mock_response)
        monitor.http_client = mock_client

        articles = await monitor._fetch_feed_articles("feed-123", since)

        # Verify since parameter was passed
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args[1]
        assert "params" in call_kwargs
        assert "since" in call_kwargs["params"]

    @pytest.mark.asyncio
    async def test_fetch_feed_articles_http_error(self, caplog):
        """Test handling HTTP error when fetching articles"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )
        monitor.http_client = mock_client

        articles = await monitor._fetch_feed_articles("feed-123", None)

        assert len(articles) == 0
        assert "HTTP error" in caplog.text


# ============================================================================
# Analysis Job Scheduling Tests
# ============================================================================

class TestAnalysisScheduling:
    """Test scheduling analysis jobs based on feed category"""

    @pytest.mark.asyncio
    async def test_schedule_analysis_finance_category(self, db_session):
        """Test scheduling jobs for finance category feed"""
        monitor = FeedMonitor()
        monitor._is_running = True

        feed = {
            "id": "feed-finance",
            "category": "finance",
            "url": "https://example.com/finance.xml"
        }

        article = {
            "id": "article-123",
            "title": "Finance News",
            "url": "https://example.com/article"
        }

        result = await monitor._schedule_analysis(
            db_session,
            feed["id"],
            feed,
            article
        )

        assert result is True

        # Should have created finance sentiment + standard sentiment jobs
        jobs = db_session.query(AnalysisJobQueue).all()
        job_types = [job.job_type for job in jobs]

        assert JobType.FINANCE_SENTIMENT in job_types
        assert JobType.STANDARD_SENTIMENT in job_types

    @pytest.mark.asyncio
    async def test_schedule_analysis_geopolitics_category(self, db_session):
        """Test scheduling jobs for geopolitics category feed"""
        monitor = FeedMonitor()
        monitor._is_running = True

        feed = {
            "id": "feed-geopolitics",
            "category": "geopolitics",
            "url": "https://example.com/geopolitics.xml"
        }

        article = {
            "id": "article-456",
            "title": "Geopolitical News",
            "url": "https://example.com/article2"
        }

        result = await monitor._schedule_analysis(
            db_session,
            feed["id"],
            feed,
            article
        )

        assert result is True

        jobs = db_session.query(AnalysisJobQueue).all()
        job_types = [job.job_type for job in jobs]

        assert JobType.GEOPOLITICAL_SENTIMENT in job_types
        assert JobType.STANDARD_SENTIMENT in job_types

    @pytest.mark.asyncio
    async def test_schedule_analysis_general_category(self, db_session):
        """Test scheduling jobs for general/uncategorized feed"""
        monitor = FeedMonitor()
        monitor._is_running = True

        feed = {
            "id": "feed-general",
            "category": "general",
            "url": "https://example.com/general.xml"
        }

        article = {
            "id": "article-789",
            "title": "General News",
            "url": "https://example.com/article3"
        }

        result = await monitor._schedule_analysis(
            db_session,
            feed["id"],
            feed,
            article
        )

        assert result is True

        jobs = db_session.query(AnalysisJobQueue).all()
        job_types = [job.job_type for job in jobs]

        # Should have categorization + standard sentiment
        assert JobType.CATEGORIZATION in job_types
        assert JobType.STANDARD_SENTIMENT in job_types

    @pytest.mark.asyncio
    async def test_schedule_analysis_no_category(self, db_session):
        """Test scheduling jobs when category is missing"""
        monitor = FeedMonitor()
        monitor._is_running = True

        feed = {
            "id": "feed-no-category",
            "url": "https://example.com/feed.xml"
            # No category field
        }

        article = {
            "id": "article-999",
            "title": "News",
            "url": "https://example.com/article4"
        }

        result = await monitor._schedule_analysis(
            db_session,
            feed["id"],
            feed,
            article
        )

        assert result is True

        jobs = db_session.query(AnalysisJobQueue).all()
        job_types = [job.job_type for job in jobs]

        # Should default to categorization + standard sentiment
        assert JobType.CATEGORIZATION in job_types
        assert JobType.STANDARD_SENTIMENT in job_types

    @pytest.mark.asyncio
    async def test_schedule_analysis_correct_priorities(self, db_session):
        """Test that jobs are created with correct priorities"""
        monitor = FeedMonitor()
        monitor._is_running = True

        feed = {
            "id": "feed-finance",
            "category": "finance"
        }

        article = {
            "id": "article-123",
            "title": "Finance News"
        }

        await monitor._schedule_analysis(
            db_session,
            feed["id"],
            feed,
            article
        )

        jobs = db_session.query(AnalysisJobQueue).all()

        # Finance sentiment should have priority 8
        finance_job = next(
            (j for j in jobs if j.job_type == JobType.FINANCE_SENTIMENT),
            None
        )
        assert finance_job is not None
        assert finance_job.priority == 8

        # Standard sentiment should have priority 5
        standard_job = next(
            (j for j in jobs if j.job_type == JobType.STANDARD_SENTIMENT),
            None
        )
        assert standard_job is not None
        assert standard_job.priority == 5


# ============================================================================
# Feed Schedule State Tests
# ============================================================================

class TestFeedScheduleState:
    """Test feed schedule state tracking"""

    @pytest.mark.asyncio
    async def test_create_feed_schedule_state(
        self,
        db_session,
        mock_feed_service_response,
        mock_articles_response
    ):
        """Test creating new feed schedule state"""
        monitor = FeedMonitor()
        monitor._is_running = True

        # Mock HTTP client
        mock_client = AsyncMock()

        # Mock articles response
        mock_articles_resp = MagicMock()
        mock_articles_resp.status_code = 200
        mock_articles_resp.json = MagicMock(return_value=mock_articles_response)
        mock_articles_resp.raise_for_status = MagicMock()

        mock_client.get = AsyncMock(return_value=mock_articles_resp)
        monitor.http_client = mock_client

        feed = mock_feed_service_response[0]

        with patch('app.services.feed_monitor.SessionLocal', return_value=db_session):
            await monitor._process_feed(db_session, feed)

        # Check that schedule state was created
        state = db_session.query(FeedScheduleState).filter(
            FeedScheduleState.feed_id == feed["id"]
        ).first()

        assert state is not None
        assert state.feed_id == feed["id"]
        assert state.last_checked_at is not None

    @pytest.mark.asyncio
    async def test_update_feed_schedule_state(
        self,
        db_session,
        sample_feed_schedule_state,
        mock_articles_response
    ):
        """Test updating existing feed schedule state"""
        monitor = FeedMonitor()
        monitor._is_running = True

        original_checked_at = sample_feed_schedule_state.last_checked_at
        original_count = sample_feed_schedule_state.total_articles_processed

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_articles_resp = MagicMock()
        mock_articles_resp.status_code = 200
        mock_articles_resp.json = MagicMock(return_value=mock_articles_response)
        mock_articles_resp.raise_for_status = MagicMock()

        mock_client.get = AsyncMock(return_value=mock_articles_resp)
        monitor.http_client = mock_client

        feed = {
            "id": sample_feed_schedule_state.feed_id,
            "category": "finance",
            "url": "https://example.com/feed.xml"
        }

        with patch('app.services.feed_monitor.SessionLocal', return_value=db_session):
            await monitor._process_feed(db_session, feed)

        db_session.refresh(sample_feed_schedule_state)

        # Check that state was updated
        assert sample_feed_schedule_state.last_checked_at > original_checked_at
        assert sample_feed_schedule_state.total_articles_processed > original_count

    @pytest.mark.asyncio
    async def test_schedule_state_no_new_articles(
        self,
        db_session,
        sample_feed_schedule_state
    ):
        """Test updating state when no new articles found"""
        monitor = FeedMonitor()
        monitor._is_running = True

        original_checked_at = sample_feed_schedule_state.last_checked_at
        original_count = sample_feed_schedule_state.total_articles_processed

        # Mock empty articles response
        mock_client = AsyncMock()
        mock_articles_resp = MagicMock()
        mock_articles_resp.status_code = 200
        mock_articles_resp.json = MagicMock(return_value=[])
        mock_articles_resp.raise_for_status = MagicMock()

        mock_client.get = AsyncMock(return_value=mock_articles_resp)
        monitor.http_client = mock_client

        feed = {
            "id": sample_feed_schedule_state.feed_id,
            "category": "finance",
            "url": "https://example.com/feed.xml"
        }

        with patch('app.services.feed_monitor.SessionLocal', return_value=db_session):
            new_articles = await monitor._process_feed(db_session, feed)

        db_session.refresh(sample_feed_schedule_state)

        # Check that last_checked_at was updated but count stayed the same
        assert sample_feed_schedule_state.last_checked_at > original_checked_at
        assert sample_feed_schedule_state.total_articles_processed == original_count
        assert new_articles == 0


# ============================================================================
# Full Check Cycle Tests
# ============================================================================

class TestFeedCheckCycle:
    """Test complete feed checking cycle"""

    @pytest.mark.asyncio
    async def test_check_feeds_no_active_feeds(self, db_session, caplog):
        """Test check cycle when no active feeds exist"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-type": "application/json"}

        mock_client.get = AsyncMock(return_value=mock_response)
        monitor.http_client = mock_client

        with patch('app.services.feed_monitor.SessionLocal', return_value=db_session):
            await monitor._check_feeds()

        assert "No active feeds found" in caplog.text

    @pytest.mark.asyncio
    async def test_check_feeds_processing_error(
        self,
        db_session,
        mock_feed_service_response,
        caplog
    ):
        """Test handling error during feed processing"""
        monitor = FeedMonitor()
        monitor._is_running = True

        mock_client = AsyncMock()

        # Mock successful feeds fetch
        mock_feeds_resp = MagicMock()
        mock_feeds_resp.status_code = 200
        mock_feeds_resp.json = MagicMock(return_value=mock_feed_service_response)
        mock_feeds_resp.raise_for_status = MagicMock()
        mock_feeds_resp.headers = {"content-type": "application/json"}

        # Mock articles fetch that raises error
        async def get_side_effect(url, **kwargs):
            if "/items" in url:
                raise httpx.HTTPError("Connection failed")
            return mock_feeds_resp

        mock_client.get = AsyncMock(side_effect=get_side_effect)
        monitor.http_client = mock_client

        with patch('app.services.feed_monitor.SessionLocal', return_value=db_session):
            await monitor._check_feeds()

        # Should log errors but not crash
        assert "Error processing feed" in caplog.text


# ============================================================================
# Status Reporting Tests
# ============================================================================

class TestFeedMonitorStatus:
    """Test status reporting"""

    def test_get_status_not_running(self):
        """Test status when monitor is not running"""
        monitor = FeedMonitor()

        status = monitor.get_status()

        assert status["is_running"] is False
        assert "check_interval_seconds" in status

    @pytest.mark.asyncio
    async def test_get_status_running(self):
        """Test status when monitor is running"""
        monitor = FeedMonitor()
        await monitor.start()

        status = monitor.get_status()

        assert status["is_running"] is True
        assert status["check_interval_seconds"] > 0

        await monitor.stop()

    def test_is_running_flag(self):
        """Test is_running flag"""
        monitor = FeedMonitor()

        assert not monitor.is_running()

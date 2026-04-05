"""
Unit tests for FailureTracker service.

Tests graceful degradation when Redis is unavailable (P1-6).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import redis.asyncio as redis

from app.services.failure_tracker import FailureTracker


@pytest.fixture
def failure_tracker(mock_redis_client, mock_http_client):
    """Create a FailureTracker instance with mocked dependencies."""
    tracker = FailureTracker()
    tracker.redis_client = mock_redis_client
    tracker.http_client = mock_http_client
    return tracker


class TestRecordSuccess:
    """Tests for record_success method."""

    @pytest.mark.asyncio
    async def test_record_success_resets_redis_counter(self, failure_tracker, mock_redis_client):
        """Test that successful scrape resets Redis counter."""
        await failure_tracker.record_success("feed-123")

        mock_redis_client.delete.assert_called_once_with("scrape_failures:feed-123")

    @pytest.mark.asyncio
    async def test_record_success_updates_database(self, failure_tracker, mock_http_client):
        """Test that successful scrape updates database via HTTP."""
        await failure_tracker.record_success("feed-123")

        mock_http_client.patch.assert_called_once()
        call_args = mock_http_client.patch.call_args
        assert "/api/v1/feeds/feed-123" in str(call_args)

    @pytest.mark.asyncio
    async def test_record_success_handles_redis_error_gracefully(self, failure_tracker, mock_redis_client, mock_http_client):
        """Test graceful degradation when Redis fails (P1-6)."""
        # Simulate Redis error
        mock_redis_client.delete.side_effect = redis.RedisError("Connection lost")

        # Should not raise, should continue to HTTP update
        await failure_tracker.record_success("feed-123")

        # HTTP update should still be attempted
        mock_http_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_success_handles_no_redis_client(self, failure_tracker, mock_http_client):
        """Test when Redis client is None."""
        failure_tracker.redis_client = None

        # Should not raise
        await failure_tracker.record_success("feed-123")

        # HTTP update should still be attempted
        mock_http_client.patch.assert_called_once()


class TestRecordFailure:
    """Tests for record_failure method."""

    @pytest.mark.asyncio
    async def test_record_failure_increments_counter(self, failure_tracker, mock_redis_client):
        """Test that failure increments Redis counter."""
        mock_redis_client.incr.return_value = 1

        result = await failure_tracker.record_failure("feed-123")

        mock_redis_client.incr.assert_called_once_with("scrape_failures:feed-123")
        assert result is False  # Below threshold

    @pytest.mark.asyncio
    async def test_record_failure_sets_expiry_on_first_failure(self, failure_tracker, mock_redis_client):
        """Test that expiry is set on first failure."""
        mock_redis_client.incr.return_value = 1

        await failure_tracker.record_failure("feed-123")

        mock_redis_client.expire.assert_called_once_with("scrape_failures:feed-123", 86400)

    @pytest.mark.asyncio
    async def test_record_failure_handles_redis_error_gracefully(self, failure_tracker, mock_redis_client, mock_http_client):
        """Test graceful degradation when Redis fails during record_failure (P1-6)."""
        # Simulate Redis error
        mock_redis_client.incr.side_effect = redis.RedisError("Connection lost")

        # Should not raise, should continue with default value
        result = await failure_tracker.record_failure("feed-123")

        # Should use default value (1) and continue
        assert result is False  # Below threshold
        # HTTP update should still be attempted
        mock_http_client.patch.assert_called_once()


class TestGetFailureCount:
    """Tests for get_failure_count method."""

    @pytest.mark.asyncio
    async def test_get_failure_count_returns_value(self, failure_tracker, mock_redis_client):
        """Test getting failure count from Redis."""
        mock_redis_client.get.return_value = "5"

        count = await failure_tracker.get_failure_count("feed-123")

        assert count == 5

    @pytest.mark.asyncio
    async def test_get_failure_count_returns_zero_when_not_found(self, failure_tracker, mock_redis_client):
        """Test returning 0 when no counter exists."""
        mock_redis_client.get.return_value = None

        count = await failure_tracker.get_failure_count("feed-123")

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_failure_count_handles_redis_error(self, failure_tracker, mock_redis_client):
        """Test graceful degradation when Redis fails (P1-6)."""
        mock_redis_client.get.side_effect = redis.RedisError("Connection lost")

        count = await failure_tracker.get_failure_count("feed-123")

        assert count == 0  # Should return 0 on error


class TestResetFailures:
    """Tests for reset_failures method."""

    @pytest.mark.asyncio
    async def test_reset_failures_deletes_key(self, failure_tracker, mock_redis_client):
        """Test that reset_failures deletes the Redis key."""
        await failure_tracker.reset_failures("feed-123")

        mock_redis_client.delete.assert_called_once_with("scrape_failures:feed-123")

    @pytest.mark.asyncio
    async def test_reset_failures_handles_redis_error(self, failure_tracker, mock_redis_client):
        """Test graceful degradation when Redis fails (P1-6)."""
        mock_redis_client.delete.side_effect = redis.RedisError("Connection lost")

        # Should not raise
        await failure_tracker.reset_failures("feed-123")


class TestGetFeedThreshold:
    """Tests for _get_feed_threshold method."""

    @pytest.mark.asyncio
    async def test_get_feed_threshold_uses_cache(self, failure_tracker, mock_redis_client):
        """Test that cached threshold is returned."""
        mock_redis_client.get.return_value = "10"

        threshold = await failure_tracker._get_feed_threshold("feed-123")

        assert threshold == 10
        mock_redis_client.get.assert_called_once_with("feed_threshold:feed-123")

    @pytest.mark.asyncio
    async def test_get_feed_threshold_fetches_from_api(self, failure_tracker, mock_redis_client, mock_http_client):
        """Test fetching threshold from API when not cached."""
        mock_redis_client.get.return_value = None

        threshold = await failure_tracker._get_feed_threshold("feed-123")

        assert threshold == 5  # From mock HTTP client
        mock_http_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_feed_threshold_caches_result(self, failure_tracker, mock_redis_client, mock_http_client):
        """Test that fetched threshold is cached."""
        mock_redis_client.get.return_value = None

        await failure_tracker._get_feed_threshold("feed-123")

        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args[0]
        assert call_args[0] == "feed_threshold:feed-123"
        assert call_args[1] == 3600  # 1 hour cache

    @pytest.mark.asyncio
    async def test_get_feed_threshold_handles_redis_cache_error(self, failure_tracker, mock_redis_client, mock_http_client):
        """Test graceful degradation when Redis cache read fails (P1-6)."""
        mock_redis_client.get.side_effect = redis.RedisError("Connection lost")

        threshold = await failure_tracker._get_feed_threshold("feed-123")

        # Should fall back to API
        assert threshold == 5
        mock_http_client.get.assert_called_once()

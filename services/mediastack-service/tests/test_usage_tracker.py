"""Tests for Usage Tracker."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestUsageTracker:
    """Tests for usage tracking."""

    @pytest.mark.asyncio
    async def test_can_make_request_within_limit(self):
        """Test request allowed when within limits."""
        with patch('app.services.usage_tracker.redis') as mock_redis_module:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=b"50")
            mock_redis_module.from_url.return_value = mock_client

            from app.services.usage_tracker import UsageTracker
            tracker = UsageTracker()
            tracker._redis = mock_client

            result = await tracker.can_make_request()

            assert result is True

    @pytest.mark.asyncio
    async def test_cannot_make_request_at_limit(self):
        """Test request denied when at monthly limit."""
        with patch('app.services.usage_tracker.redis') as mock_redis_module:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=b"10000")
            mock_redis_module.from_url.return_value = mock_client

            from app.services.usage_tracker import UsageTracker
            tracker = UsageTracker()
            tracker._redis = mock_client

            result = await tracker.can_make_request()

            assert result is False

    @pytest.mark.asyncio
    async def test_record_request_increments_counter(self):
        """Test recording request increments counter."""
        with patch('app.services.usage_tracker.redis') as mock_redis_module:
            mock_client = MagicMock()
            mock_client.incr = AsyncMock(return_value=51)
            mock_client.expireat = AsyncMock()
            mock_redis_module.from_url.return_value = mock_client

            from app.services.usage_tracker import UsageTracker
            tracker = UsageTracker()
            tracker._redis = mock_client

            count = await tracker.record_request()

            assert count == 51
            mock_client.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_stats(self):
        """Test getting usage statistics."""
        with patch('app.services.usage_tracker.redis') as mock_redis_module:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=b"5000")
            mock_redis_module.from_url.return_value = mock_client

            from app.services.usage_tracker import UsageTracker
            tracker = UsageTracker()
            tracker._redis = mock_client

            stats = await tracker.get_usage_stats()

            assert stats["current_calls"] == 5000
            assert stats["monthly_limit"] == 10000
            assert stats["remaining"] == 5000
            assert stats["percentage"] == 50.0

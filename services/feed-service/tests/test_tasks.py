"""
Tests for Celery tasks
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone

from app.tasks.feed_tasks import (
    fetch_feed_task,
    fetch_all_active_feeds_task,
    cleanup_old_items_task,
    health_check_task,
)


class TestCeleryTasks:
    """Test Celery background tasks."""

    @patch("app.tasks.feed_tasks.FeedFetcher")
    def test_fetch_feed_task(self, mock_fetcher_class):
        """Test single feed fetch task."""
        # Setup mock
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_feed = AsyncMock(return_value=(True, 5))

        # Execute task
        result = fetch_feed_task(feed_id=1)

        # Assertions
        assert result["feed_id"] == 1
        assert result["success"] is True
        assert result["items_count"] == 5
        assert "task_id" in result

    @patch("app.tasks.feed_tasks.FeedFetcher")
    def test_fetch_feed_task_failure(self, mock_fetcher_class):
        """Test feed fetch task with failure."""
        # Setup mock
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_feed = AsyncMock(return_value=(False, 0))

        # Execute task
        result = fetch_feed_task(feed_id=1)

        # Assertions
        assert result["feed_id"] == 1
        assert result["success"] is False
        assert result["items_count"] == 0

    @patch("app.tasks.feed_tasks._fetch_all_active_feeds")
    def test_fetch_all_active_feeds_task(self, mock_fetch_all):
        """Test fetch all active feeds task."""
        # Setup mock
        mock_results = {
            "total_feeds": 10,
            "successful": 8,
            "failed": 2,
            "total_new_items": 45,
            "feed_results": [],
        }
        mock_fetch_all.return_value = AsyncMock(return_value=mock_results)()

        # Execute task
        result = fetch_all_active_feeds_task()

        # Assertions
        assert result["total_feeds"] == 10
        assert result["successful"] == 8
        assert result["failed"] == 2
        assert result["total_new_items"] == 45

    @patch("app.tasks.feed_tasks._cleanup_old_items")
    def test_cleanup_old_items_task(self, mock_cleanup):
        """Test cleanup old items task."""
        # Setup mock
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
        mock_results = {
            "items_deleted": 150,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": 90,
        }
        mock_cleanup.return_value = AsyncMock(return_value=mock_results)()

        # Execute task
        result = cleanup_old_items_task(retention_days=90)

        # Assertions
        assert result["items_deleted"] == 150
        assert result["retention_days"] == 90
        assert "cutoff_date" in result

    def test_health_check_task(self):
        """Test health check task."""
        result = health_check_task()

        assert result["status"] == "healthy"
        assert result["service"] == "feed-service-celery"
        assert "timestamp" in result


class TestTaskRetry:
    """Test task retry logic."""

    @patch("app.tasks.feed_tasks.FeedFetcher")
    def test_fetch_feed_task_retry_on_exception(self, mock_fetcher_class):
        """Test that fetch task retries on exception."""
        # Setup mock to raise exception
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_feed = AsyncMock(side_effect=Exception("Connection error"))

        # Create mock task with retry method
        mock_task = Mock()
        mock_task.retry = Mock(side_effect=Exception("Retry called"))

        # Execute task should raise retry exception
        with pytest.raises(Exception) as exc_info:
            with patch("app.tasks.feed_tasks.current_task", mock_task):
                fetch_feed_task(mock_task, feed_id=1)

        assert "Retry called" in str(exc_info.value)
"""
Tests for batch relevance score update task.

Epic 2.2 Task 3: Tests for Celery task that updates relevance scores in batch.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


def create_mock_article(
    id_val,
    published_at,
    category="default",
    quality_score=None
):
    """Helper to create a properly configured mock article."""
    mock = MagicMock()
    mock.id = id_val
    mock.published_at = published_at
    mock.category = category
    mock.quality_score = quality_score  # Return actual value, not MagicMock
    mock.relevance_score = None
    mock.relevance_calculated_at = None
    return mock


def create_mock_result_iterator(articles_batches):
    """
    Create a mock that returns different results on successive calls.

    Args:
        articles_batches: List of article lists for each batch call
    """
    call_count = [0]  # Use list to make mutable in closure

    def side_effect(*args, **kwargs):
        mock_result = MagicMock()
        if call_count[0] < len(articles_batches):
            mock_result.scalars.return_value.all.return_value = articles_batches[call_count[0]]
        else:
            mock_result.scalars.return_value.all.return_value = []
        call_count[0] += 1
        return mock_result

    return side_effect


class TestBatchUpdateRelevanceScores:
    """Tests for batch_update_relevance_scores async function."""

    @pytest.mark.asyncio
    async def test_batch_update_relevance_scores_success(self):
        """Test successful batch update of relevance scores."""
        from app.tasks.relevance_batch import _batch_update_relevance_scores

        # Create mock articles with required attributes
        mock_articles = [
            create_mock_article(
                id_val=uuid4(),
                published_at=datetime.now(timezone.utc) - timedelta(hours=2),
                category="breaking_news",
                quality_score=0.9,
            ),
            create_mock_article(
                id_val=uuid4(),
                published_at=datetime.now(timezone.utc) - timedelta(days=1),
                category="analysis",
                quality_score=0.8,
            ),
        ]

        # Setup mock session that returns articles on first call, empty on second
        mock_session = AsyncMock()
        mock_session.execute.side_effect = create_mock_result_iterator([mock_articles])

        with patch("app.tasks.relevance_batch.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            result = await _batch_update_relevance_scores(days=7, batch_size=1000)

            assert result["processed"] == 2
            assert result["updated"] == 2
            assert result["errors"] == 0
            assert "reference_time" in result

            # Verify articles were updated with scores
            for article in mock_articles:
                assert article.relevance_score is not None
                assert article.relevance_calculated_at is not None

    @pytest.mark.asyncio
    async def test_batch_update_handles_empty_result(self):
        """Test batch update with no articles to process."""
        from app.tasks.relevance_batch import _batch_update_relevance_scores

        # Setup mock session with empty result
        mock_session = AsyncMock()
        mock_session.execute.side_effect = create_mock_result_iterator([])

        with patch("app.tasks.relevance_batch.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            result = await _batch_update_relevance_scores(days=7, batch_size=1000)

            assert result["processed"] == 0
            assert result["updated"] == 0
            assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_batch_update_handles_missing_published_at(self):
        """Test batch update skips articles without published_at."""
        from app.tasks.relevance_batch import _batch_update_relevance_scores

        mock_articles = [
            create_mock_article(
                id_val=uuid4(),
                published_at=datetime.now(timezone.utc) - timedelta(hours=1),
                category="breaking_news",
                quality_score=0.9,
            ),
            create_mock_article(
                id_val=uuid4(),
                published_at=None,  # Missing published_at
                category="analysis",
                quality_score=0.8,
            ),
        ]

        mock_session = AsyncMock()
        mock_session.execute.side_effect = create_mock_result_iterator([mock_articles])

        with patch("app.tasks.relevance_batch.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            result = await _batch_update_relevance_scores(days=7, batch_size=1000)

            # Should process 2 but only update 1 (the one with published_at)
            assert result["processed"] == 2
            assert result["updated"] == 1
            assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_batch_update_uses_correct_time_window(self):
        """Test that batch update fetches articles from correct time window."""
        from app.tasks.relevance_batch import _batch_update_relevance_scores

        mock_session = AsyncMock()
        mock_session.execute.side_effect = create_mock_result_iterator([])

        with patch("app.tasks.relevance_batch.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            # Call with specific days parameter
            await _batch_update_relevance_scores(days=14, batch_size=500)

            # Verify execute was called (query was built)
            mock_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_batch_update_processes_multiple_batches(self):
        """Test that batch update handles multiple batches correctly."""
        from app.tasks.relevance_batch import _batch_update_relevance_scores

        # Create two batches of articles
        batch1 = [
            create_mock_article(
                id_val=uuid4(),
                published_at=datetime.now(timezone.utc) - timedelta(hours=1),
                category="breaking_news",
                quality_score=0.9,
            ),
        ]
        batch2 = [
            create_mock_article(
                id_val=uuid4(),
                published_at=datetime.now(timezone.utc) - timedelta(hours=2),
                category="analysis",
                quality_score=0.8,
            ),
        ]

        mock_session = AsyncMock()
        mock_session.execute.side_effect = create_mock_result_iterator([batch1, batch2])

        with patch("app.tasks.relevance_batch.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            result = await _batch_update_relevance_scores(days=7, batch_size=1)

            # Should process both batches
            assert result["processed"] == 2
            assert result["updated"] == 2
            assert result["errors"] == 0


class TestUpdateRelevanceScoresCeleryTask:
    """Tests for the Celery task wrapper."""

    def test_celery_task_is_registered(self):
        """Test that the Celery task is properly registered."""
        from app.tasks.relevance_batch import update_relevance_scores_task

        assert update_relevance_scores_task.name == "feed.update_relevance_scores"

    def test_celery_task_returns_stats_dict(self):
        """Test that Celery task returns expected stats dictionary."""
        from app.tasks.relevance_batch import update_relevance_scores_task

        with patch("app.tasks.relevance_batch._batch_update_relevance_scores") as mock_batch:
            mock_batch.return_value = {
                "processed": 100,
                "updated": 95,
                "errors": 5,
                "reference_time": datetime.now(timezone.utc).isoformat(),
            }

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete.return_value = mock_batch.return_value

                result = update_relevance_scores_task(days=7, batch_size=1000)

                assert "processed" in result
                assert "updated" in result
                assert "errors" in result


class TestCeleryBeatScheduleConfiguration:
    """Tests for Celery Beat schedule configuration (Task 2.2.4)."""

    def test_relevance_task_in_beat_schedule(self):
        """Test that update_relevance_scores task is in beat_schedule (every 30 min)."""
        from app.celery_app import celery_app

        beat_schedule = celery_app.conf.beat_schedule

        # Task should be scheduled
        assert "update-relevance-scores" in beat_schedule, (
            "update-relevance-scores not found in beat_schedule"
        )

        schedule_entry = beat_schedule["update-relevance-scores"]

        # Verify task name
        assert schedule_entry["task"] == "feed.update_relevance_scores", (
            f"Expected task name 'feed.update_relevance_scores', "
            f"got {schedule_entry['task']}"
        )

        # Verify schedule is 30 minutes (1800 seconds)
        assert schedule_entry["schedule"] == 1800.0, (
            f"Expected 30 min schedule (1800s), got {schedule_entry['schedule']}"
        )

        # Should have expires option
        assert "options" in schedule_entry
        assert "expires" in schedule_entry["options"]

    def test_relevance_task_in_task_routes(self):
        """Test that update_relevance_scores is routed to 'maintenance' queue."""
        from app.celery_app import celery_app

        task_routes = celery_app.conf.task_routes

        assert "feed.update_relevance_scores" in task_routes, (
            "feed.update_relevance_scores not found in task_routes"
        )

        route_config = task_routes["feed.update_relevance_scores"]
        assert route_config["queue"] == "maintenance", (
            f"Expected queue 'maintenance', got {route_config['queue']}"
        )

    def test_relevance_task_in_task_annotations(self):
        """Test that update_relevance_scores has priority 2 annotation."""
        from app.celery_app import celery_app

        task_annotations = celery_app.conf.task_annotations

        assert "feed.update_relevance_scores" in task_annotations, (
            "feed.update_relevance_scores not found in task_annotations"
        )

        annotation = task_annotations["feed.update_relevance_scores"]
        assert annotation["priority"] == 2, (
            f"Expected priority 2, got {annotation['priority']}"
        )

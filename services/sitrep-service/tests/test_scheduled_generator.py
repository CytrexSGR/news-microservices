# services/sitrep-service/tests/test_scheduled_generator.py
"""Tests for scheduled SITREP generation.

Tests the ScheduledGenerator which:
- Uses AsyncIO-based scheduling (not Celery)
- Runs at configurable time (default 6 AM UTC)
- Uses StoryAggregator for top stories retrieval
- Uses SitrepGenerator for LLM generation
- Persists results via SitrepRepository

Test coverage:
- Scheduler lifecycle (start/stop)
- Time-based generation triggering
- Story aggregation integration
- Database persistence
- Retry logic for failures
- Configuration options
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

from app.workers.scheduled_generator import (
    ScheduledGenerator,
    start_scheduler,
    stop_scheduler,
    get_scheduler,
)
from app.services.story_aggregator import StoryAggregator
from app.services.sitrep_generator import SitrepGenerationError
from app.schemas.story import TopStory
from app.schemas.sitrep import SitrepResponse


class TestScheduledGeneratorInit:
    """Tests for ScheduledGenerator initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        assert scheduler.aggregator is aggregator
        assert scheduler.generation_hour == 6  # Default from config
        assert scheduler.top_stories_count == 10  # Default from config
        assert scheduler.min_cluster_size == 3  # Default from config
        assert not scheduler.is_running
        assert scheduler._last_generation_date is None

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(
            aggregator,
            generation_hour=8,
            top_stories_count=15,
            min_cluster_size=5,
        )

        assert scheduler.generation_hour == 8
        assert scheduler.top_stories_count == 15
        assert scheduler.min_cluster_size == 5

    def test_init_lazy_initialization(self):
        """Test that generator and repository are lazily initialized."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        # Should be None initially
        assert scheduler._generator is None
        assert scheduler._repository is None


class TestScheduledGeneratorLifecycle:
    """Tests for scheduler start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_creates_background_task(self):
        """Test that start() creates a background task."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        await scheduler.start()

        assert scheduler.is_running
        assert scheduler._task is not None
        assert not scheduler._task.done()

        # Cleanup
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_raises_if_already_running(self):
        """Test that start() raises error if already running."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        await scheduler.start()

        with pytest.raises(RuntimeError, match="already running"):
            await scheduler.start()

        # Cleanup
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_background_task(self):
        """Test that stop() cancels the background task."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        await scheduler.start()
        assert scheduler.is_running

        await scheduler.stop()

        assert not scheduler.is_running
        assert scheduler._task is None

    @pytest.mark.asyncio
    async def test_stop_is_safe_when_not_running(self):
        """Test that stop() is safe to call when not running."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        # Should not raise
        await scheduler.stop()

        assert not scheduler.is_running


class TestShouldGenerate:
    """Tests for generation time checking."""

    def test_should_generate_at_correct_hour(self):
        """Test that _should_generate returns True at correct hour."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        # 6 AM UTC
        now = datetime(2025, 1, 5, 6, 30, 0, tzinfo=timezone.utc)

        assert scheduler._should_generate(now) is True

    def test_should_not_generate_at_wrong_hour(self):
        """Test that _should_generate returns False at wrong hour."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        # 5 AM UTC
        now = datetime(2025, 1, 5, 5, 30, 0, tzinfo=timezone.utc)
        assert scheduler._should_generate(now) is False

        # 7 AM UTC
        now = datetime(2025, 1, 5, 7, 30, 0, tzinfo=timezone.utc)
        assert scheduler._should_generate(now) is False

    def test_should_not_generate_twice_same_day(self):
        """Test that generation only happens once per day."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        now = datetime(2025, 1, 5, 6, 30, 0, tzinfo=timezone.utc)

        # First check should return True
        assert scheduler._should_generate(now) is True

        # Simulate generation completed
        scheduler._last_generation_date = now.date()

        # Second check should return False
        assert scheduler._should_generate(now) is False

    def test_should_generate_next_day(self):
        """Test that generation is allowed on the next day."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        yesterday = datetime(2025, 1, 4, 6, 30, 0, tzinfo=timezone.utc)
        today = datetime(2025, 1, 5, 6, 30, 0, tzinfo=timezone.utc)

        # Simulate generation yesterday
        scheduler._last_generation_date = yesterday.date()

        # Today should be allowed
        assert scheduler._should_generate(today) is True


class TestGetNextGenerationTime:
    """Tests for next generation time calculation."""

    def test_next_generation_later_today(self):
        """Test next generation time when it's still before generation hour."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        # Mock current time to 4 AM
        mock_now = datetime(2025, 1, 5, 4, 0, 0, tzinfo=timezone.utc)

        with patch('app.workers.scheduled_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            next_gen = scheduler.get_next_generation_time()

            # Should be 6 AM today
            expected = datetime(2025, 1, 5, 6, 0, 0, tzinfo=timezone.utc)
            assert next_gen == expected

    def test_next_generation_tomorrow(self):
        """Test next generation time when it's past generation hour."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        # Mock current time to 8 AM
        mock_now = datetime(2025, 1, 5, 8, 0, 0, tzinfo=timezone.utc)

        with patch('app.workers.scheduled_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            next_gen = scheduler.get_next_generation_time()

            # Should be 6 AM tomorrow
            expected = datetime(2025, 1, 6, 6, 0, 0, tzinfo=timezone.utc)
            assert next_gen == expected


class TestGenerateSitrep:
    """Tests for SITREP generation logic."""

    @pytest.fixture
    def mock_stories(self):
        """Create mock stories for testing."""
        return [
            TopStory(
                cluster_id=uuid4(),
                title=f"Story {i}",
                article_count=5 + i,
                first_seen_at=datetime.now(timezone.utc),
                last_updated_at=datetime.now(timezone.utc),
                tension_score=5.0,
                relevance_score=0.8,
                is_breaking=i == 0,
                category="default",
            )
            for i in range(3)
        ]

    @pytest.fixture
    def mock_sitrep_response(self):
        """Create mock SITREP response for testing."""
        return SitrepResponse(
            id=uuid4(),
            report_date=datetime.now(timezone.utc).date(),
            report_type="daily",
            title="Daily SITREP",
            executive_summary="Test summary",
            content_markdown="# Test",
            key_developments=[],
            top_stories=[],
            key_entities=[],
            sentiment_summary={"overall": "neutral"},
            generation_model="gpt-4",
            generation_time_ms=1000,
            prompt_tokens=500,
            completion_tokens=500,
            articles_analyzed=15,
            confidence_score=0.8,
            human_reviewed=False,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_generate_sitrep_success(self, mock_stories, mock_sitrep_response):
        """Test successful SITREP generation."""
        aggregator = AsyncMock(spec=StoryAggregator)
        aggregator.get_top_stories.return_value = mock_stories

        scheduler = ScheduledGenerator(aggregator)

        # Mock generator
        mock_generator = AsyncMock()
        mock_generator.generate.return_value = mock_sitrep_response
        scheduler._generator = mock_generator

        # Mock repository
        mock_repo = AsyncMock()
        mock_saved = MagicMock()
        mock_saved.id = mock_sitrep_response.id
        mock_saved.report_type = "daily"
        mock_repo.save.return_value = mock_saved
        scheduler._repository = mock_repo

        # Mock database session
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch('app.workers.scheduled_generator.async_session_maker', return_value=mock_session):
            result = await scheduler.generate_sitrep()

        assert result is True
        aggregator.get_top_stories.assert_called_once()
        mock_generator.generate.assert_called_once_with(
            stories=mock_stories,
            report_type="daily",
        )
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_sitrep_no_stories(self):
        """Test generate_sitrep returns False when no stories available."""
        aggregator = AsyncMock(spec=StoryAggregator)
        aggregator.get_top_stories.return_value = []

        scheduler = ScheduledGenerator(aggregator)

        result = await scheduler.generate_sitrep()

        assert result is False
        aggregator.get_top_stories.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_sitrep_llm_failure(self, mock_stories):
        """Test generate_sitrep raises on LLM failure."""
        aggregator = AsyncMock(spec=StoryAggregator)
        aggregator.get_top_stories.return_value = mock_stories

        scheduler = ScheduledGenerator(aggregator)

        # Mock generator to fail
        mock_generator = AsyncMock()
        mock_generator.generate.side_effect = SitrepGenerationError("LLM failed")
        scheduler._generator = mock_generator

        with pytest.raises(SitrepGenerationError, match="LLM failed"):
            await scheduler.generate_sitrep()


class TestGenerateWithRetry:
    """Tests for retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that generation is retried on failure."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        # Make MAX_RETRIES smaller for testing
        scheduler.MAX_RETRIES = 2
        scheduler.RETRY_DELAY_SECONDS = 0.01  # Very short for testing

        # Mock generate_sitrep to fail first, succeed second
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return True

        scheduler.generate_sitrep = mock_generate

        result = await scheduler._generate_with_retry()

        assert result is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that generation fails after max retries."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        # Make retries faster for testing
        scheduler.MAX_RETRIES = 2
        scheduler.RETRY_DELAY_SECONDS = 0.01

        # Mock generate_sitrep to always fail
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")

        scheduler.generate_sitrep = mock_generate

        result = await scheduler._generate_with_retry()

        assert result is False
        assert call_count == 2  # MAX_RETRIES attempts


class TestTriggerImmediate:
    """Tests for manual immediate generation."""

    @pytest.mark.asyncio
    async def test_trigger_immediate_calls_generate(self):
        """Test that trigger_immediate calls generate_sitrep."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        # Mock generate_sitrep
        scheduler.generate_sitrep = AsyncMock(return_value=True)

        result = await scheduler.trigger_immediate(report_type="breaking")

        assert result is True
        scheduler.generate_sitrep.assert_called_once_with(report_type="breaking")


class TestSchedulerStatus:
    """Tests for scheduler status reporting."""

    @pytest.mark.asyncio
    async def test_get_status_when_running(self):
        """Test status when scheduler is running."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(
            aggregator,
            generation_hour=6,
            top_stories_count=10,
            min_cluster_size=3,
        )

        await scheduler.start()

        status = scheduler.get_status()

        assert status["running"] is True
        assert status["generation_hour"] == 6
        assert status["top_stories_count"] == 10
        assert status["min_cluster_size"] == 3
        assert status["current_story_count"] == 0
        assert "next_generation_time" in status
        assert "time_until_next" in status

        await scheduler.stop()

    def test_get_status_when_stopped(self):
        """Test status when scheduler is stopped."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator)

        status = scheduler.get_status()

        assert status["running"] is False
        assert status["last_generation_date"] is None


class TestGlobalSchedulerFunctions:
    """Tests for module-level scheduler functions."""

    @pytest.mark.asyncio
    async def test_start_scheduler_creates_global_instance(self):
        """Test that start_scheduler creates and starts global instance."""
        aggregator = StoryAggregator()

        scheduler = await start_scheduler(aggregator)

        assert scheduler is not None
        assert scheduler.is_running
        assert get_scheduler() is scheduler

        # Cleanup
        await stop_scheduler()

    @pytest.mark.asyncio
    async def test_stop_scheduler_cleans_up(self):
        """Test that stop_scheduler stops and cleans up."""
        aggregator = StoryAggregator()

        await start_scheduler(aggregator)
        assert get_scheduler() is not None

        await stop_scheduler()

        assert get_scheduler() is None

    @pytest.mark.asyncio
    async def test_stop_scheduler_safe_when_not_started(self):
        """Test that stop_scheduler is safe when not started."""
        # Should not raise
        await stop_scheduler()

        assert get_scheduler() is None


class TestSchedulerLoopIntegration:
    """Integration tests for scheduler loop behavior."""

    @pytest.mark.asyncio
    async def test_scheduler_loop_checks_time_periodically(self):
        """Test that scheduler loop checks generation time periodically."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        # Make check interval very short for testing
        scheduler.CHECK_INTERVAL_SECONDS = 0.01

        # Track _should_generate calls
        call_count = 0
        original_should_generate = scheduler._should_generate

        def mock_should_generate(now):
            nonlocal call_count
            call_count += 1
            return False  # Never trigger generation

        scheduler._should_generate = mock_should_generate

        await scheduler.start()

        # Wait a bit for multiple checks
        await asyncio.sleep(0.05)

        await scheduler.stop()

        # Should have been called multiple times
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_scheduler_handles_generation_error_gracefully(self):
        """Test that scheduler continues after generation error."""
        aggregator = StoryAggregator()
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        # Make intervals short for testing
        scheduler.CHECK_INTERVAL_SECONDS = 0.01
        scheduler.RETRY_DELAY_SECONDS = 0.01
        scheduler.MAX_RETRIES = 1

        # Force generation to trigger
        scheduler._should_generate = lambda now: True

        # Mock generate_sitrep to fail
        error_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal error_count
            error_count += 1
            # After first error, prevent more triggers
            scheduler._last_generation_date = datetime.now(timezone.utc).date()
            raise Exception("Test error")

        scheduler.generate_sitrep = mock_generate

        await scheduler.start()

        # Wait for error to happen
        await asyncio.sleep(0.1)

        # Scheduler should still be running
        assert scheduler.is_running

        await scheduler.stop()

        # Error should have been handled
        assert error_count >= 1


class TestSchedulerConfiguration:
    """Tests for scheduler configuration options."""

    def test_generation_hour_boundary_values(self):
        """Test generation hour at boundary values."""
        aggregator = StoryAggregator()

        # Hour 0 (midnight)
        scheduler_midnight = ScheduledGenerator(aggregator, generation_hour=0)
        assert scheduler_midnight.generation_hour == 0

        # Hour 23 (11 PM)
        scheduler_late = ScheduledGenerator(aggregator, generation_hour=23)
        assert scheduler_late.generation_hour == 23

    def test_custom_stories_count(self):
        """Test custom top stories count configuration."""
        aggregator = StoryAggregator()

        scheduler = ScheduledGenerator(aggregator, top_stories_count=20)
        assert scheduler.top_stories_count == 20

    def test_custom_min_cluster_size(self):
        """Test custom minimum cluster size configuration."""
        aggregator = StoryAggregator()

        scheduler = ScheduledGenerator(aggregator, min_cluster_size=10)
        assert scheduler.min_cluster_size == 10

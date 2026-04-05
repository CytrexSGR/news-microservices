# services/sitrep-service/app/workers/scheduled_generator.py
"""Scheduled SITREP generation using AsyncIO scheduler.

Provides scheduled generation of daily SITREPs without Celery dependency.
Uses AsyncIO-based scheduling for lightweight, in-process task execution.

Features:
    - Configurable generation time (default 6 AM UTC)
    - Uses StoryAggregator for top stories retrieval
    - Uses SitrepGenerator for LLM-powered report generation
    - Persists results via SitrepRepository
    - Graceful shutdown handling
    - Retry logic for failed generations

Example:
    >>> from app.workers.scheduled_generator import ScheduledGenerator
    >>> scheduler = ScheduledGenerator(aggregator)
    >>> await scheduler.start()
    >>> # Scheduler runs in background task
    >>> await scheduler.stop()
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.config import settings
from app.db.session import async_session_maker
from app.repositories.sitrep_repository import SitrepRepository
from app.services.sitrep_generator import SitrepGenerator, SitrepGenerationError
from app.services.story_aggregator import StoryAggregator

logger = logging.getLogger(__name__)


class ScheduledGenerator:
    """
    AsyncIO-based scheduler for daily SITREP generation.

    Runs a background task that triggers SITREP generation at a configurable
    hour (default 6 AM UTC). Uses the StoryAggregator for story retrieval,
    SitrepGenerator for LLM generation, and SitrepRepository for persistence.

    Attributes:
        aggregator: StoryAggregator instance for getting top stories
        generation_hour: Hour (0-23) to trigger daily generation (UTC)
        top_stories_count: Number of top stories to include in SITREP
        min_cluster_size: Minimum articles required for story inclusion
        _task: Background asyncio task
        _running: Flag indicating if scheduler is active

    Example:
        >>> aggregator = StoryAggregator()
        >>> scheduler = ScheduledGenerator(aggregator)
        >>> await scheduler.start()
        >>> # Later...
        >>> await scheduler.stop()
    """

    # Retry configuration for failed generations
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 300  # 5 minutes

    # Check interval when waiting for generation time
    CHECK_INTERVAL_SECONDS = 60  # Check every minute

    def __init__(
        self,
        aggregator: StoryAggregator,
        generation_hour: Optional[int] = None,
        top_stories_count: Optional[int] = None,
        min_cluster_size: Optional[int] = None,
    ):
        """
        Initialize the scheduled generator.

        Args:
            aggregator: StoryAggregator instance for story retrieval
            generation_hour: Hour to trigger generation (0-23 UTC), defaults to config
            top_stories_count: Number of stories to include, defaults to config
            min_cluster_size: Minimum articles per story, defaults to config
        """
        self.aggregator = aggregator
        self.generation_hour = generation_hour if generation_hour is not None else settings.SITREP_GENERATION_HOUR
        self.top_stories_count = top_stories_count if top_stories_count is not None else settings.SITREP_TOP_STORIES_COUNT
        self.min_cluster_size = min_cluster_size if min_cluster_size is not None else settings.SITREP_MIN_CLUSTER_SIZE

        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_generation_date: Optional[datetime] = None

        # Lazy-initialized components
        self._generator: Optional[SitrepGenerator] = None
        self._repository: Optional[SitrepRepository] = None

    @property
    def generator(self) -> SitrepGenerator:
        """Get or create SitrepGenerator instance (lazy initialization)."""
        if self._generator is None:
            self._generator = SitrepGenerator()
        return self._generator

    @property
    def repository(self) -> SitrepRepository:
        """Get or create SitrepRepository instance (lazy initialization)."""
        if self._repository is None:
            self._repository = SitrepRepository()
        return self._repository

    @property
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self._running and self._task is not None and not self._task.done()

    async def start(self) -> None:
        """
        Start the scheduler background task.

        Creates and starts an asyncio task that runs the scheduler loop.
        The task checks hourly for the generation time and triggers
        SITREP generation when the configured hour is reached.

        Raises:
            RuntimeError: If scheduler is already running
        """
        if self._running:
            raise RuntimeError("Scheduler is already running")

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(
            f"Scheduled SITREP generator started (generation hour: {self.generation_hour:02d}:00 UTC, "
            f"top_stories: {self.top_stories_count}, min_cluster_size: {self.min_cluster_size})"
        )

    async def stop(self) -> None:
        """
        Stop the scheduler background task gracefully.

        Cancels the running task and waits for it to complete.
        Safe to call even if scheduler is not running.
        """
        self._running = False

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Scheduled SITREP generator stopped")

    async def _scheduler_loop(self) -> None:
        """
        Main scheduler loop - checks periodically for generation time.

        Runs until stop() is called. Checks the current time against
        the configured generation hour and triggers generation once
        per day at that hour.
        """
        logger.debug("Scheduler loop started")

        while self._running:
            try:
                now = datetime.now(timezone.utc)

                # Check if it's time for generation
                if self._should_generate(now):
                    logger.info(
                        f"Triggering scheduled SITREP generation at {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    )
                    await self._generate_with_retry()
                    self._last_generation_date = now.date()

                # Wait before next check
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)

            except asyncio.CancelledError:
                logger.debug("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in scheduler loop: {e}")
                # Wait a bit before retrying to avoid tight error loops
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)

    def _should_generate(self, now: datetime) -> bool:
        """
        Determine if SITREP generation should be triggered.

        Checks if:
        1. Current hour matches generation hour
        2. Generation hasn't already run today

        Args:
            now: Current UTC datetime

        Returns:
            True if generation should be triggered, False otherwise
        """
        # Check if it's the right hour
        if now.hour != self.generation_hour:
            return False

        # Check if we already generated today
        if self._last_generation_date == now.date():
            return False

        return True

    async def _generate_with_retry(self) -> bool:
        """
        Generate SITREP with retry logic.

        Attempts to generate a SITREP up to MAX_RETRIES times,
        with exponential backoff between attempts.

        Returns:
            True if generation succeeded, False otherwise
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                success = await self.generate_sitrep()
                if success:
                    return True

                logger.warning(
                    f"SITREP generation attempt {attempt + 1}/{self.MAX_RETRIES} failed (no stories)"
                )

            except Exception as e:
                logger.error(
                    f"SITREP generation attempt {attempt + 1}/{self.MAX_RETRIES} failed: {e}"
                )

            # Wait before retry (exponential backoff)
            if attempt < self.MAX_RETRIES - 1:
                delay = self.RETRY_DELAY_SECONDS * (2 ** attempt)
                logger.info(f"Retrying SITREP generation in {delay} seconds...")
                await asyncio.sleep(delay)

        logger.error(f"SITREP generation failed after {self.MAX_RETRIES} attempts")
        return False

    async def generate_sitrep(self, report_type: str = "daily") -> bool:
        """
        Generate a SITREP from current aggregated stories.

        Gets top stories from the aggregator, generates a SITREP using
        the LLM, and persists the result to the database.

        Args:
            report_type: Type of report to generate (daily, weekly, breaking)

        Returns:
            True if SITREP was generated and saved, False if no stories available

        Raises:
            SitrepGenerationError: If LLM generation fails
            Exception: If database persistence fails
        """
        # Get top stories from aggregator
        stories = await self.aggregator.get_top_stories(
            limit=self.top_stories_count,
            min_article_count=self.min_cluster_size,
        )

        if not stories:
            logger.warning(
                f"No stories available for SITREP generation "
                f"(min_cluster_size={self.min_cluster_size})"
            )
            return False

        logger.info(
            f"Generating {report_type} SITREP from {len(stories)} stories "
            f"({sum(s.article_count for s in stories)} total articles)"
        )

        # Generate SITREP
        try:
            sitrep = await self.generator.generate(
                stories=stories,
                report_type=report_type,
            )
        except SitrepGenerationError as e:
            logger.error(f"SITREP generation failed: {e}")
            raise

        # Persist to database
        async with async_session_maker() as session:
            saved = await self.repository.save(session, sitrep)
            logger.info(
                f"Saved scheduled SITREP: id={saved.id}, "
                f"type={saved.report_type}, "
                f"stories={len(sitrep.top_stories)}, "
                f"generation_time={sitrep.generation_time_ms}ms"
            )

        return True

    async def trigger_immediate(self, report_type: str = "daily") -> bool:
        """
        Trigger immediate SITREP generation (bypasses schedule).

        Useful for manual triggering or testing.

        Args:
            report_type: Type of report to generate

        Returns:
            True if generation succeeded, False otherwise
        """
        logger.info(f"Immediate SITREP generation triggered (type={report_type})")
        return await self.generate_sitrep(report_type=report_type)

    def get_next_generation_time(self) -> datetime:
        """
        Calculate the next scheduled generation time.

        Returns:
            Next generation datetime in UTC
        """
        now = datetime.now(timezone.utc)
        today_generation = now.replace(
            hour=self.generation_hour,
            minute=0,
            second=0,
            microsecond=0,
        )

        if now.hour < self.generation_hour:
            # Later today
            return today_generation
        else:
            # Tomorrow
            return today_generation + timedelta(days=1)

    def get_status(self) -> dict:
        """
        Get current scheduler status.

        Returns:
            Dict with scheduler status information
        """
        now = datetime.now(timezone.utc)
        next_gen = self.get_next_generation_time()

        return {
            "running": self.is_running,
            "generation_hour": self.generation_hour,
            "top_stories_count": self.top_stories_count,
            "min_cluster_size": self.min_cluster_size,
            "last_generation_date": self._last_generation_date.isoformat() if self._last_generation_date else None,
            "next_generation_time": next_gen.isoformat(),
            "time_until_next": str(next_gen - now),
            "current_story_count": self.aggregator.story_count,
        }


# Global scheduler instance
_scheduler: Optional[ScheduledGenerator] = None


async def start_scheduler(aggregator: StoryAggregator) -> ScheduledGenerator:
    """
    Start the global scheduler instance.

    Creates and starts the ScheduledGenerator with the provided aggregator.

    Args:
        aggregator: StoryAggregator instance for story retrieval

    Returns:
        ScheduledGenerator instance
    """
    global _scheduler

    _scheduler = ScheduledGenerator(aggregator)
    await _scheduler.start()

    return _scheduler


async def stop_scheduler() -> None:
    """
    Stop the global scheduler instance.

    Stops the scheduler and cleans up resources.
    Safe to call even if scheduler is not running.
    """
    global _scheduler

    if _scheduler is not None:
        await _scheduler.stop()
        _scheduler = None

    logger.info("Scheduled SITREP generator stopped")


def get_scheduler() -> Optional[ScheduledGenerator]:
    """
    Get the global scheduler instance.

    Returns:
        ScheduledGenerator if running, None otherwise
    """
    return _scheduler

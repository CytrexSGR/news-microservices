"""
Feed scheduler service - migrated and improved from monolith

Handles automatic scheduling of feed fetches based on intervals.
Now includes intelligent scheduling optimizer to prevent thundering herd problems.
"""
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Feed, FeedStatus
from app.config import settings
from app.services.feed_fetcher import FeedFetcher

logger = logging.getLogger(__name__)


class FeedScheduler:
    """Service for scheduling automatic feed fetches."""

    def __init__(self):
        self.is_running = False
        self.check_interval_seconds = settings.SCHEDULER_CHECK_INTERVAL_SECONDS
        self.fetcher = FeedFetcher()
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Feed scheduler is already running")
            return

        logger.info("Starting feed scheduler")
        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())

    async def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping feed scheduler")
        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_scheduler(self):
        """Main scheduler loop."""
        try:
            while self.is_running:
                await self._check_and_fetch_feeds()
                await asyncio.sleep(self.check_interval_seconds)
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled")
        except Exception as e:
            logger.error(f"Feed scheduler error: {e}")
        finally:
            self.is_running = False
            logger.info("Feed scheduler stopped")

    async def _check_and_fetch_feeds(self):
        """Check which feeds need fetching and fetch them."""
        try:
            async with AsyncSessionLocal() as session:
                feeds_to_fetch = await self._get_feeds_to_fetch(session)

                if feeds_to_fetch:
                    active_count = sum(1 for f in feeds_to_fetch if f.status == FeedStatus.ACTIVE.value)
                    error_count = sum(1 for f in feeds_to_fetch if f.status == FeedStatus.ERROR.value)
                    logger.info(
                        f"Scheduled fetch for {len(feeds_to_fetch)} feeds "
                        f"({active_count} active, {error_count} error retries)"
                    )
                    await self._fetch_feeds_batch(feeds_to_fetch)

        except Exception as e:
            logger.error(f"Error checking feeds for scheduled fetch: {e}")

    async def _get_feeds_to_fetch(self, session: AsyncSession) -> List[Feed]:
        """Get list of feeds that need to be fetched."""
        now = datetime.now(timezone.utc)
        feeds_to_fetch = []

        # Get active and error feeds (for retry)
        result = await session.execute(
            select(Feed).where(
                and_(
                    Feed.is_active == True,
                    or_(
                        Feed.status == FeedStatus.ACTIVE.value,
                        Feed.status == FeedStatus.ERROR.value
                    ),
                    Feed.fetch_interval > 0
                )
            )
        )
        feeds = result.scalars().all()

        for feed in feeds:
            if self._should_fetch_feed(feed, now):
                feeds_to_fetch.append(feed)

        return feeds_to_fetch

    def _should_fetch_feed(self, feed: Feed, now: datetime) -> bool:
        """Determine if a feed should be fetched now."""
        if not feed.fetch_interval or feed.fetch_interval <= 0:
            return False

        if not feed.last_fetched_at:
            # Never fetched, fetch immediately
            return True

        # Calculate fetch interval with exponential backoff for error feeds
        fetch_interval_minutes = feed.fetch_interval

        # Apply exponential backoff for feeds in ERROR status
        if feed.status == FeedStatus.ERROR.value:
            # Increase interval based on consecutive failures
            backoff_multiplier = min(2 ** feed.consecutive_failures, 64)  # Max 64x normal interval
            fetch_interval_minutes *= backoff_multiplier
            logger.debug(
                f"Feed {feed.id} in ERROR status with {feed.consecutive_failures} failures - "
                f"using backoff interval: {fetch_interval_minutes} minutes"
            )

        # Ensure last_fetched_at is timezone-aware
        last_fetched = feed.last_fetched_at
        if last_fetched.tzinfo is None:
            last_fetched = last_fetched.replace(tzinfo=timezone.utc)

        # Calculate next fetch time
        next_fetch_time = last_fetched + timedelta(minutes=fetch_interval_minutes)

        # Use configurable tolerance from settings (default 30 seconds)
        # This prevents timing issues while respecting configured intervals
        tolerance = timedelta(seconds=settings.SCHEDULER_FETCH_TOLERANCE_SECONDS)
        return now >= (next_fetch_time - tolerance)

    async def _fetch_feeds_batch(self, feeds: List[Feed]):
        """Fetch a batch of feeds."""
        # Create tasks for concurrent fetching
        tasks = []
        for feed in feeds[:10]:  # Limit concurrent fetches to 10
            tasks.append(self._fetch_feed_with_delay(feed))

        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process remaining feeds if any
        if len(feeds) > 10:
            await asyncio.sleep(2)  # Brief pause before next batch
            await self._fetch_feeds_batch(feeds[10:])

    async def _fetch_feed_with_delay(self, feed: Feed):
        """Fetch a feed with a small random delay to avoid thundering herd."""
        try:
            # Add small random delay (0-2 seconds)
            import random
            await asyncio.sleep(random.uniform(0, 2))

            logger.debug(f"Scheduled fetch for feed {feed.id} ({feed.name})")
            success, items_count = await self.fetcher.fetch_feed(feed.id)

            if success:
                logger.info(f"Scheduled fetch for feed {feed.id} completed: {items_count} new items")
            else:
                logger.warning(f"Scheduled fetch for feed {feed.id} failed")

        except Exception as e:
            logger.error(f"Error in scheduled fetch for feed {feed.id}: {e}")

    async def get_next_fetch_times(self, limit: int = 10) -> List[dict]:
        """Get upcoming fetch times for feeds."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Feed).where(
                        and_(
                            Feed.is_active == True,
                            Feed.status == FeedStatus.ACTIVE.value,
                            Feed.fetch_interval > 0
                        )
                    ).limit(limit)
                )
                feeds = result.scalars().all()

                now = datetime.now(timezone.utc)
                next_fetches = []

                for feed in feeds:
                    if feed.last_fetched_at and feed.fetch_interval:
                        # Ensure timezone-aware
                        last_fetched = feed.last_fetched_at
                        if last_fetched.tzinfo is None:
                            last_fetched = last_fetched.replace(tzinfo=timezone.utc)

                        next_fetch = last_fetched + timedelta(minutes=feed.fetch_interval)
                        is_due = now >= next_fetch

                        next_fetches.append({
                            "feed_id": feed.id,
                            "feed_name": feed.name,
                            "last_fetched": feed.last_fetched_at,
                            "fetch_interval_minutes": feed.fetch_interval,
                            "next_fetch": next_fetch,
                            "is_due": is_due,
                        })

                # Sort by next fetch time
                next_fetches.sort(key=lambda x: x["next_fetch"])
                return next_fetches

        except Exception as e:
            logger.error(f"Error getting next fetch times: {e}")
            return []

    def get_scheduler_status(self) -> dict:
        """Get current scheduler status."""
        return {
            "is_running": self.is_running,
            "check_interval_seconds": self.check_interval_seconds,
            "fetcher_active": self.fetcher is not None,
        }


# Global scheduler instance
_scheduler_instance: Optional[FeedScheduler] = None


def get_scheduler() -> FeedScheduler:
    """Get global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = FeedScheduler()
    return _scheduler_instance


# ============================================================================
# Feed Schedule Optimizer - Prevents Thundering Herd
# ============================================================================

class FeedScheduleOptimizer:
    """
    Optimizes feed fetch schedules to prevent resource contention.

    Algorithm:
    1. Group feeds by fetch_interval
    2. Within each group, distribute feeds evenly across the interval
    3. Apply offsets to prevent clustering
    4. Respect priority for critical feeds
    """

    def __init__(self, max_concurrent_feeds: int = 7):
        """
        Initialize the optimizer.

        Args:
            max_concurrent_feeds: Maximum feeds allowed to fetch simultaneously (default: 7)
        """
        self.max_concurrent_feeds = max_concurrent_feeds
        self.clustering_window_seconds = 60  # Consider feeds within 60s as clustered

    async def calculate_optimal_distribution(
        self,
        session: AsyncSession,
        apply_immediately: bool = False
    ) -> Dict[str, any]:
        """
        Calculate optimal distribution for all active feeds.

        Args:
            session: Database session
            apply_immediately: If True, apply changes to database

        Returns:
            Dictionary with optimization results and statistics
        """
        logger.info("Starting feed schedule optimization")

        # Get all active feeds
        result = await session.execute(
            select(Feed).where(
                and_(
                    Feed.is_active == True,
                    Feed.fetch_interval > 0
                )
            ).order_by(Feed.scheduling_priority.desc(), Feed.fetch_interval)
        )
        feeds = result.scalars().all()

        if not feeds:
            logger.warning("No active feeds found for optimization")
            return {"status": "no_feeds", "feeds_optimized": 0}

        logger.info(f"Optimizing schedule for {len(feeds)} active feeds")

        # Calculate BEFORE stats
        before_stats = await self.get_distribution_stats(session)
        before_max_concurrent = before_stats.get("max_concurrent_feeds", 0)
        before_score = before_stats.get("distribution_score", 0)

        # Check if optimization is needed
        if before_score >= 90:
            logger.info(f"Distribution already excellent (score: {before_score}), no optimization needed")
            return {
                "feeds_analyzed": len(feeds),
                "feeds_optimized": 0,
                "before": {
                    "max_concurrent": before_max_concurrent,
                    "distribution_score": before_score
                },
                "after": {
                    "max_concurrent": before_max_concurrent,
                    "distribution_score": before_score
                },
                "improvement_percentage": 0.0,
                "preview": None,
                "message": "Distribution already excellent (score ≥ 90), no optimization needed"
            }

        # Group feeds by interval
        feeds_by_interval = defaultdict(list)
        for feed in feeds:
            feeds_by_interval[feed.fetch_interval].append(feed)

        # Calculate optimal offsets for each interval group
        optimization_plan = []
        total_changes = 0

        for interval, feed_group in feeds_by_interval.items():
            logger.info(f"Optimizing {len(feed_group)} feeds with {interval}-minute interval")

            # Calculate stagger time between feeds
            stagger_minutes = interval / len(feed_group)

            # Apply offsets
            for i, feed in enumerate(feed_group):
                old_offset = feed.schedule_offset_minutes
                new_offset = int(i * stagger_minutes)

                if old_offset != new_offset:
                    feed.schedule_offset_minutes = new_offset

                    # Calculate new next_fetch_at
                    if feed.last_fetched_at:
                        base_time = feed.last_fetched_at + timedelta(minutes=interval)
                    else:
                        base_time = datetime.now(timezone.utc)

                    feed.next_fetch_at = base_time + timedelta(minutes=new_offset)
                    total_changes += 1

                    optimization_plan.append({
                        "feed_id": str(feed.id),
                        "feed_name": feed.name,
                        "old_offset": old_offset,
                        "new_offset": new_offset,
                        "old_next_fetch": (base_time + timedelta(minutes=old_offset)).isoformat() if feed.last_fetched_at else None,
                        "new_next_fetch": feed.next_fetch_at.isoformat()
                    })

        # Calculate AFTER stats (before committing, to show preview)
        after_stats = await self.get_distribution_stats(session)
        after_max_concurrent = after_stats.get("max_concurrent_feeds", 0)
        after_score = after_stats.get("distribution_score", 0)

        # Calculate improvement (handle both improvement and degradation)
        if before_max_concurrent > 0:
            if after_max_concurrent <= before_max_concurrent:
                # Improvement case
                improvement = ((before_max_concurrent - after_max_concurrent) / before_max_concurrent) * 100
            else:
                # Degradation case (after is worse than before)
                improvement = -((after_max_concurrent - before_max_concurrent) / before_max_concurrent) * 100
        else:
            improvement = 0

        # Apply changes if requested
        if apply_immediately and total_changes > 0:
            await session.commit()
            logger.info(f"Applied optimization: {total_changes} feeds updated")
        else:
            # Rollback changes if not applying (preview mode)
            await session.rollback()

        result = {
            "feeds_analyzed": len(feeds),
            "feeds_optimized": total_changes,
            "before": {
                "max_concurrent": before_max_concurrent,
                "distribution_score": before_score
            },
            "after": {
                "max_concurrent": after_max_concurrent,
                "distribution_score": after_score
            },
            "improvement_percentage": round(improvement, 1),
            "preview": optimization_plan if not apply_immediately else None,
            "message": f"Optimized {total_changes} of {len(feeds)} feeds" if apply_immediately else f"Preview: {total_changes} feeds will be adjusted"
        }

        logger.info(f"Optimization complete: {result}")
        return result

    async def detect_clustering(self, session: AsyncSession) -> List[List[Feed]]:
        """
        Detect clusters of feeds scheduled too close together.

        Returns:
            List of clusters, each cluster is a list of Feed objects
        """
        # Get all active feeds sorted by next_fetch_at
        result = await session.execute(
            select(Feed)
            .where(
                and_(
                    Feed.is_active == True,
                    Feed.next_fetch_at.isnot(None)
                )
            )
            .order_by(Feed.next_fetch_at)
        )
        feeds = result.scalars().all()

        if not feeds:
            return []

        # Group feeds within clustering window
        clusters = []
        current_cluster = [feeds[0]]

        for i in range(1, len(feeds)):
            time_diff = (feeds[i].next_fetch_at - feeds[i-1].next_fetch_at).total_seconds()

            if time_diff <= self.clustering_window_seconds:
                # Add to current cluster
                current_cluster.append(feeds[i])
            else:
                # Check if current cluster exceeds threshold
                if len(current_cluster) > self.max_concurrent_feeds:
                    clusters.append(current_cluster)

                # Start new cluster
                current_cluster = [feeds[i]]

        # Check last cluster
        if len(current_cluster) > self.max_concurrent_feeds:
            clusters.append(current_cluster)

        if clusters:
            logger.warning(
                f"Detected {len(clusters)} clusters with >{self.max_concurrent_feeds} feeds. "
                f"Largest cluster: {max([len(c) for c in clusters])} feeds"
            )

        return clusters

    async def suggest_rebalancing(self, session: AsyncSession) -> Dict[str, any]:
        """
        Analyze current schedule and suggest improvements.

        Returns:
            Dictionary with suggestions and impact analysis
        """
        clusters = await self.detect_clustering(session)

        if not clusters:
            return {
                "needs_rebalancing": False,
                "reason": "No clustering detected"
            }

        # Analyze cluster composition
        cluster_analysis = []
        for cluster in clusters:
            intervals = defaultdict(int)
            for feed in cluster:
                intervals[feed.fetch_interval] += 1

            cluster_analysis.append({
                "size": len(cluster),
                "time": cluster[0].next_fetch_at.isoformat(),
                "interval_distribution": dict(intervals),
                "feeds": [{"id": str(f.id), "name": f.name, "interval": f.fetch_interval}
                         for f in cluster]
            })

        return {
            "needs_rebalancing": True,
            "clusters_found": len(clusters),
            "max_cluster_size": max([len(c) for c in clusters]),
            "cluster_details": cluster_analysis,
            "recommendation": "Run calculate_optimal_distribution with apply_immediately=True"
        }

    async def get_distribution_stats(self, session: AsyncSession) -> Dict[str, any]:
        """
        Calculate statistics about current schedule distribution.

        Returns:
            Dictionary with distribution metrics
        """
        result = await session.execute(
            select(Feed).where(
                and_(
                    Feed.is_active == True,
                    Feed.next_fetch_at.isnot(None)
                )
            )
        )
        feeds = list(result.scalars().all())

        if not feeds:
            return {"status": "no_active_feeds"}

        # Calculate time-based distribution (5-minute buckets for next 24 hours)
        now = datetime.now(timezone.utc)
        buckets = defaultdict(int)

        for feed in feeds:
            if feed.next_fetch_at > now and feed.next_fetch_at < now + timedelta(hours=24):
                # Round to 5-minute bucket
                bucket_time = feed.next_fetch_at.replace(second=0, microsecond=0)
                bucket_minutes = bucket_time.minute - (bucket_time.minute % 5)
                bucket_time = bucket_time.replace(minute=bucket_minutes)
                buckets[bucket_time] += 1

        # Find peak load
        max_concurrent = max(buckets.values()) if buckets else 0
        peak_times = [k.isoformat() for k, v in buckets.items() if v == max_concurrent]

        # Calculate load distribution score (0-100, higher is better)
        if buckets:
            avg_load = sum(buckets.values()) / len(buckets)
            variance = sum((v - avg_load) ** 2 for v in buckets.values()) / len(buckets)
            std_dev = variance ** 0.5

            # Normalize to 0-100 (lower variance = higher score)
            distribution_score = max(0, 100 - (std_dev * 10))
        else:
            distribution_score = 0

        return {
            "total_active_feeds": len(feeds),
            "feeds_in_next_24h": sum(buckets.values()),
            "max_concurrent_feeds": max_concurrent,
            "peak_times": peak_times,
            "distribution_score": round(distribution_score, 2),
            "recommendation": (
                "Excellent distribution" if distribution_score > 80 else
                "Good distribution" if distribution_score > 60 else
                "Fair distribution - consider optimization" if distribution_score > 40 else
                "Poor distribution - optimization recommended"
            )
        }
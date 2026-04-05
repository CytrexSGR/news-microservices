"""
Celery tasks for feed processing

These tasks run asynchronously in Celery workers.
"""
import asyncio
import logging
from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from celery import current_task

from app.celery_app import celery_app
from app.services.feed_fetcher import FeedFetcher
from app.services.event_publisher import get_event_publisher
from app.db import AsyncSessionLocal
from app.models import Feed, FeedItem, FeedStatus
from sqlalchemy import select, and_, delete

logger = logging.getLogger(__name__)


def convert_decimals_to_float(obj):
    """Recursively convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    else:
        return obj


@celery_app.task(
    name="feed.fetch_single",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fetch_feed_task(self, feed_id: int) -> Dict[str, Any]:
    """
    Celery task to fetch a single feed.

    Args:
        feed_id: ID of the feed to fetch

    Returns:
        Dictionary with fetch results
    """
    try:
        logger.info(f"Starting fetch task for feed {feed_id}")

        # ✅ FIX: Reuse existing event loop instead of creating new one
        # Creating new_event_loop() for every task causes "different loop" errors
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        fetcher = FeedFetcher()
        success, items_count = loop.run_until_complete(
            fetcher.fetch_feed(feed_id)
        )

        result = {
            "feed_id": feed_id,
            "success": success,
            "items_count": items_count,
            "task_id": current_task.request.id,
        }

        logger.info(f"Fetch task completed for feed {feed_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in fetch task for feed {feed_id}: {e}")
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(
    name="feed.fetch_all_active",
    bind=True,
    max_retries=1,
)
def fetch_all_active_feeds_task(self) -> Dict[str, Any]:
    """
    Celery task to fetch all active feeds.

    This task is typically scheduled to run periodically (e.g., every hour).

    Returns:
        Dictionary with overall fetch results
    """
    try:
        logger.info("Starting fetch all active feeds task")

        # ✅ FIX: Reuse existing event loop instead of creating new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        results = loop.run_until_complete(_fetch_all_active_feeds())
        logger.info(f"Fetch all feeds task completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Error in fetch all feeds task: {e}")
        raise


async def _fetch_all_active_feeds() -> Dict[str, Any]:
    """Async helper to fetch all active feeds."""
    async with AsyncSessionLocal() as session:
        # Get all active feeds (we'll filter by individual fetch_interval below)
        now = datetime.now(timezone.utc)

        result = await session.execute(
            select(Feed).where(
                and_(
                    Feed.is_active == True,
                    Feed.status == FeedStatus.ACTIVE.value,
                    Feed.fetch_interval > 0,
                    Feed.feed_type != "web",  # Web sources handled by fetch_web_sources task
                )
            )
        )
        all_feeds = result.scalars().all()

        # Filter feeds based on next_fetch_at (intelligent scheduling)
        feeds_to_fetch = []
        for feed in all_feeds:
            # Use next_fetch_at if available (new intelligent scheduling)
            if feed.next_fetch_at is not None:
                if now >= feed.next_fetch_at:
                    feeds_to_fetch.append(feed)
                    logger.debug(
                        f"Feed {feed.name} (ID: {feed.id}) is due for fetching "
                        f"(scheduled at {feed.next_fetch_at})"
                    )
            # Fallback to old logic for feeds without next_fetch_at
            elif feed.last_fetched_at is None:
                # Never fetched before
                feeds_to_fetch.append(feed)
            else:
                # Calculate time since last fetch (legacy behavior)
                time_since_fetch = now - feed.last_fetched_at
                fetch_interval_delta = timedelta(minutes=feed.fetch_interval)

                # Check if it's time to fetch based on individual interval
                if time_since_fetch >= fetch_interval_delta:
                    feeds_to_fetch.append(feed)
                    logger.debug(
                        f"Feed {feed.name} (ID: {feed.id}) is due for fetching (legacy). "
                        f"Interval: {feed.fetch_interval}min, Last fetch: {time_since_fetch.total_seconds()/60:.1f}min ago"
                    )

        feeds = feeds_to_fetch
        logger.info(f"Found {len(feeds)} feeds due for fetching (out of {len(all_feeds)} active feeds)")

        # Fetch feeds concurrently (with limit)
        fetcher = FeedFetcher()
        tasks = []
        results = {
            "total_feeds": len(feeds),
            "successful": 0,
            "failed": 0,
            "total_new_items": 0,
            "feed_results": [],
        }

        # Process in batches of 10
        for i in range(0, len(feeds), 10):
            batch = feeds[i:i+10]
            batch_tasks = [fetcher.fetch_feed(feed.id) for feed in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for feed, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["feed_results"].append({
                        "feed_id": feed.id,
                        "success": False,
                        "error": str(result),
                    })
                else:
                    success, items_count = result
                    if success:
                        results["successful"] += 1
                        results["total_new_items"] += items_count
                    else:
                        results["failed"] += 1

                    results["feed_results"].append({
                        "feed_id": feed.id,
                        "success": success,
                        "items_count": items_count,
                    })

            # Brief pause between batches
            if i + 10 < len(feeds):
                await asyncio.sleep(2)

        return results


@celery_app.task(
    name="feed.cleanup_old_items",
    bind=True,
    max_retries=1,
)
def cleanup_old_items_task(self, retention_days: int = 90) -> Dict[str, Any]:
    """
    Celery task to clean up old feed items.

    This task removes feed items older than the retention period to
    prevent the database from growing indefinitely.

    Args:
        retention_days: Number of days to retain items (default: 90)

    Returns:
        Dictionary with cleanup results
    """
    try:
        logger.info(f"Starting cleanup task with {retention_days} days retention")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(
                _cleanup_old_items(retention_days)
            )
            logger.info(f"Cleanup task completed: {results}")
            return results
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise


async def _cleanup_old_items(retention_days: int) -> Dict[str, Any]:
    """Async helper to clean up old items."""
    async with AsyncSessionLocal() as session:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Count items to delete
        count_result = await session.execute(
            select(FeedItem).where(FeedItem.created_at < cutoff_date)
        )
        items_to_delete = len(count_result.scalars().all())

        if items_to_delete > 0:
            # Delete old items
            await session.execute(
                delete(FeedItem).where(FeedItem.created_at < cutoff_date)
            )
            await session.commit()

            # Publish cleanup event
            publisher = await get_event_publisher()
            await publisher.publish_event(
                "feed.items_cleaned",
                {
                    "items_deleted": items_to_delete,
                    "cutoff_date": cutoff_date.isoformat(),
                    "retention_days": retention_days,
                }
            )

        return {
            "items_deleted": items_to_delete,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": retention_days,
        }


@celery_app.task(
    name="feed.auto_recover_failed_feeds",
    bind=True,
    max_retries=1,
)
def auto_recover_failed_feeds_task(self, cooldown_minutes: int = 60) -> Dict[str, Any]:
    """
    Celery task to automatically recover feeds that failed due to network outages.

    This task runs periodically to detect and recover feeds that were marked as ERROR
    due to temporary network issues. It implements intelligent recovery by:
    - Only recovering feeds that have been in ERROR state for > cooldown_minutes
    - Verifying network connectivity before recovery
    - Resetting error counters and health scores

    This prevents permanent ERROR states after internet outages and reduces
    manual intervention.

    Args:
        cooldown_minutes: Minimum time (in minutes) a feed must be in ERROR state
                         before attempting recovery (default: 60)

    Returns:
        Dictionary with recovery summary
    """
    try:
        logger.info(f"Starting auto-recovery task (cooldown: {cooldown_minutes} minutes)")

        # ✅ FIX: Reuse existing event loop instead of creating new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        results = loop.run_until_complete(
            _auto_recover_failed_feeds(cooldown_minutes)
        )
        logger.info(f"Auto-recovery task completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Error in auto-recovery task: {e}", exc_info=True)
        raise


async def _auto_recover_failed_feeds(cooldown_minutes: int = 60) -> Dict[str, Any]:
    """
    Async helper to recover feeds from ERROR state.

    Recovery strategy:
    1. Find feeds with status=ERROR and is_active=true
    2. Filter for feeds that have been in ERROR state for > cooldown_minutes
    3. Check if network is available (by checking recent successful fetches)
    4. Reset feeds to ACTIVE state with clean error counters
    """
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        cooldown_threshold = now - timedelta(minutes=cooldown_minutes)

        # Find feeds that are stuck in ERROR state
        result = await session.execute(
            select(Feed).where(
                and_(
                    Feed.is_active == True,
                    Feed.status == FeedStatus.ERROR.value,
                    Feed.last_error_at <= cooldown_threshold,  # In ERROR for > cooldown_minutes
                )
            )
        )
        error_feeds = result.scalars().all()

        if not error_feeds:
            logger.info("No feeds found in ERROR state requiring recovery")
            return {
                "feeds_checked": 0,
                "feeds_recovered": 0,
                "network_available": None,
            }

        logger.info(f"Found {len(error_feeds)} feeds in ERROR state for >{cooldown_minutes} minutes")

        # Check if network is available by looking for recent successful fetches
        # (within last 10 minutes)
        recent_threshold = now - timedelta(minutes=10)
        network_check = await session.execute(
            select(Feed).where(
                and_(
                    Feed.is_active == True,
                    Feed.status == FeedStatus.ACTIVE.value,
                    Feed.last_fetched_at >= recent_threshold,
                )
            )
        )
        recent_successful_feeds = len(network_check.scalars().all())
        network_available = recent_successful_feeds > 0

        if not network_available:
            logger.warning(
                f"Network may still be unavailable (no successful fetches in last 10 minutes). "
                f"Skipping recovery to avoid immediate re-failures."
            )
            return {
                "feeds_checked": len(error_feeds),
                "feeds_recovered": 0,
                "network_available": False,
                "reason": "Network connectivity not verified",
            }

        # Network is available, recover the feeds
        recovered_count = 0
        recovered_feeds = []

        for feed in error_feeds:
            try:
                # Reset feed to healthy state
                feed.status = FeedStatus.ACTIVE.value
                feed.consecutive_failures = 0
                feed.health_score = 100
                feed.last_error_message = None
                feed.last_error_at = None

                await session.commit()
                recovered_count += 1
                recovered_feeds.append({
                    "feed_id": str(feed.id),
                    "feed_name": feed.name,
                    "error_duration_minutes": int((now - feed.last_error_at).total_seconds() / 60) if feed.last_error_at else None,
                })

                logger.info(
                    f"✅ Recovered feed: {feed.name} "
                    f"(was in ERROR for ~{int((now - feed.last_error_at).total_seconds() / 60)} minutes)"
                )

            except Exception as e:
                logger.error(f"❌ Failed to recover feed {feed.name}: {e}")
                await session.rollback()

        # Publish recovery event
        if recovered_count > 0:
            publisher = await get_event_publisher()
            await publisher.publish_event(
                "feed.auto_recovery_completed",
                {
                    "feeds_recovered": recovered_count,
                    "recovered_feeds": recovered_feeds,
                    "timestamp": now.isoformat(),
                    "cooldown_minutes": cooldown_minutes,
                }
            )

        return {
            "feeds_checked": len(error_feeds),
            "feeds_recovered": recovered_count,
            "network_available": True,
            "recovered_feeds": recovered_feeds,
        }


# Scheduled tasks configuration
@celery_app.task(name="feed.health_check")
def health_check_task() -> Dict[str, Any]:
    """Simple health check task for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "feed-service-celery",
    }


@celery_app.task(
    name="feed.calculate_quality_scores",
    bind=True,
    max_retries=1,
)
def calculate_quality_scores_task(self, days: int = 30) -> Dict[str, Any]:
    """
    Celery task to calculate Feed Quality V2 scores for all active feeds.

    This task runs nightly to update comprehensive quality scores based on:
    - Article quality from content-analysis-v2
    - Source credibility from research service
    - Operational reliability from feed health
    - Freshness & consistency from publishing patterns

    Args:
        days: Number of days to analyze (default: 30)

    Returns:
        Dictionary with calculation summary
    """
    try:
        logger.info(f"Starting quality calculation task for all active feeds (days={days})")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(
                _calculate_all_quality_scores(days)
            )
            logger.info(f"Quality calculation task completed: {results}")
            return results
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in quality calculation task: {e}", exc_info=True)
        raise


async def _calculate_all_quality_scores(days: int = 30) -> Dict[str, Any]:
    """
    Async helper to calculate quality scores for all active feeds.

    Updates the following fields in the feeds table:
    - quality_score_v2
    - quality_confidence
    - quality_trend
    - quality_calculated_at
    - article_quality_stats (JSONB)

    Args:
        days: Number of days to analyze

    Returns:
        Summary with success/failure counts
    """
    from app.services.feed_quality_v2 import FeedQualityScorerV2

    async with AsyncSessionLocal() as session:
        scorer = FeedQualityScorerV2()

        # Get all active feeds
        result = await session.execute(
            select(Feed).where(Feed.is_active == True)
        )
        feeds = result.scalars().all()

        if not feeds:
            logger.warning("No active feeds found for quality calculation")
            return {"total": 0, "successful": 0, "failed": 0}

        logger.info(f"Calculating quality scores for {len(feeds)} active feeds")

        successful = 0
        failed = 0
        results = []

        for feed in feeds:
            try:
                # Calculate comprehensive quality
                quality_data = await scorer.calculate_comprehensive_quality(
                    session=session,
                    feed_id=feed.id,
                    days=days
                )

                # Update feed record
                feed.quality_score_v2 = int(quality_data['quality_score'])
                feed.quality_confidence = quality_data['confidence']
                feed.quality_trend = quality_data['trend']
                feed.quality_calculated_at = datetime.now(timezone.utc)
                # Convert Decimals to float for JSON serialization
                feed.article_quality_stats = convert_decimals_to_float({
                    'component_scores': quality_data['component_scores'],
                    'quality_distribution': quality_data['quality_distribution'],
                    'red_flags': quality_data['red_flags'],
                    'trends': {
                        'trend_label': quality_data['trends']['trend_label'],
                        'trend_value': quality_data['trends']['trend_value'],
                        'quality_7d_vs_30d': quality_data['trends']['quality_7d_vs_30d']
                    },
                    'data_stats': {
                        'articles_analyzed': quality_data['data_stats']['articles_analyzed'],
                        'total_articles': quality_data['data_stats']['total_articles'],
                        'coverage_percentage': quality_data['data_stats']['coverage_percentage']
                    }
                })

                await session.commit()
                successful += 1

                results.append({
                    'feed_id': str(feed.id),
                    'feed_name': feed.name,
                    'quality_score': quality_data['quality_score'],
                    'admiralty_code': quality_data['admiralty_code']['code'],
                    'confidence': quality_data['confidence']
                })

                logger.info(f"✅ Updated quality for {feed.name}: "
                           f"Score={quality_data['quality_score']:.1f}, "
                           f"Code={quality_data['admiralty_code']['code']}, "
                           f"Confidence={quality_data['confidence']}")

            except Exception as e:
                failed += 1
                logger.error(f"❌ Failed to calculate quality for {feed.name}: {e}")
                await session.rollback()

        # Log summary
        logger.info(f"Quality calculation summary: Total={len(feeds)}, "
                   f"Successful={successful}, Failed={failed}")

        return {
            "total": len(feeds),
            "successful": successful,
            "failed": failed,
            "results": results
        }

@celery_app.task(name="feed.fetch_web_sources", bind=True, max_retries=1)
def fetch_web_sources(self):
    """Fetch all active web sources that are due."""
    try:
        logger.info("Starting web source fetch task")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        results = loop.run_until_complete(_fetch_web_sources())
        logger.info(f"Web source fetch task completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Error in web source fetch task: {e}", exc_info=True)
        raise


async def _fetch_web_sources() -> Dict[str, Any]:
    """Async helper to fetch all active web sources."""
    from app.services.web_fetcher import WebFetcher
    from uuid import uuid4
    from sqlalchemy import text

    logger.info("Starting web source fetch cycle")
    fetcher = WebFetcher()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, url, name, fetch_interval
                FROM feeds
                WHERE feed_type = 'web' AND is_active = true AND status = 'ACTIVE'
                  AND (next_fetch_at IS NULL OR next_fetch_at <= now())
            """)
        )
        web_sources = result.fetchall()
        if not web_sources:
            logger.debug("No web sources due for fetching")
            return {"total": 0, "fetched": 0, "skipped": 0, "failed": 0}

        logger.info(f"Found {len(web_sources)} web sources to fetch")
        fetched = 0
        skipped = 0
        failed = 0

        for source in web_sources:
            feed_id = str(source.id)
            url = source.url
            try:
                scrape_result = await fetcher.fetch_page(url)
                if scrape_result.get("status") != "success":
                    logger.warning(
                        f"Scrape failed for {url}: {scrape_result.get('error_message')}"
                    )
                    failed += 1
                    continue

                content = scrape_result.get("content") or ""
                title = scrape_result.get("extracted_title") or source.name
                links = scrape_result.get("extracted_links") or []
                content_hash = fetcher.compute_content_hash(content)

                # Change detection
                existing = await session.execute(
                    text(
                        "SELECT id, content_hash FROM feed_items "
                        "WHERE feed_id = :feed_id AND depth = 0 AND source_type = 'web' "
                        "ORDER BY created_at DESC LIMIT 1"
                    ),
                    {"feed_id": feed_id},
                )
                existing_row = existing.first()
                if existing_row and not fetcher.content_has_changed(
                    content, existing_row.content_hash
                ):
                    logger.debug(f"No changes for {url}, skipping")
                    await session.execute(
                        text(
                            "UPDATE feeds SET next_fetch_at = now() + make_interval(mins => fetch_interval) "
                            "WHERE id = :id"
                        ),
                        {"id": feed_id},
                    )
                    await session.commit()
                    skipped += 1
                    continue

                crawl_session_id = await fetcher.create_crawl_session(
                    session, feed_id, url
                )
                item_id = str(uuid4())
                await session.execute(
                    text("""
                        INSERT INTO feed_items
                            (id, feed_id, title, link, content, content_hash,
                             source_type, depth, crawl_session_id)
                        VALUES
                            (:id, :feed_id, :title, :link, :content, :content_hash,
                             'web', 0, :crawl_session_id)
                        ON CONFLICT (content_hash) DO NOTHING
                    """),
                    {
                        "id": item_id,
                        "feed_id": feed_id,
                        "title": title,
                        "link": url,
                        "content": content,
                        "content_hash": content_hash,
                        "crawl_session_id": crawl_session_id,
                    },
                )
                await fetcher.update_crawl_session(session, crawl_session_id, url)
                await session.execute(
                    text(
                        "UPDATE feeds SET next_fetch_at = now() + make_interval(mins => fetch_interval) "
                        "WHERE id = :id"
                    ),
                    {"id": feed_id},
                )
                await session.commit()

                # Publish to Nemesis (outside transaction)
                await fetcher.publish_links_to_nemesis(
                    source_id=feed_id,
                    feed_id=feed_id,
                    item_id=item_id,
                    url=url,
                    title=title,
                    content_preview=content[:500],
                    links=links,
                    depth=0,
                    crawl_session_id=crawl_session_id,
                )
                fetched += 1
                logger.info(f"Fetched web source {url}: {len(links)} links extracted")

            except Exception as e:
                logger.error(f"Error fetching web source {url}: {e}", exc_info=True)
                await session.rollback()
                failed += 1

        return {
            "total": len(web_sources),
            "fetched": fetched,
            "skipped": skipped,
            "failed": failed,
        }

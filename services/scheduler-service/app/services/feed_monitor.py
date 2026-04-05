"""
Feed Monitor Service

Monitors feeds from Feed Service and triggers analysis when new articles are found.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import sys
import os
# Add project root to path for database imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.core.config import settings
from app.core.database import SessionLocal
from database.models import FeedScheduleState
from database.models import AnalysisJobQueue, JobType, JobStatus

logger = logging.getLogger(__name__)


class FeedMonitor:
    """
    Monitors feeds and schedules analysis jobs for new articles.

    Runs every FEED_CHECK_INTERVAL seconds (default: 60)
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.http_client: Optional[httpx.AsyncClient] = None
        self._is_running = False

    async def start(self):
        """Start the feed monitor scheduler"""
        if self._is_running:
            logger.warning("Feed monitor already running")
            return

        logger.info("Starting feed monitor")

        # Initialize HTTP client
        headers = {"X-Service-Name": "scheduler-service"}
        if settings.FEED_SERVICE_API_KEY:
            headers["X-Service-Key"] = settings.FEED_SERVICE_API_KEY

        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=headers
        )

        # Schedule feed checking job
        self.scheduler.add_job(
            self._check_feeds,
            trigger=IntervalTrigger(seconds=settings.FEED_CHECK_INTERVAL),
            id="feed_monitor",
            name="Feed Monitor Job",
            replace_existing=True,
            max_instances=1  # Prevent overlapping executions
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(f"Feed monitor started (interval: {settings.FEED_CHECK_INTERVAL}s)")

    async def stop(self):
        """Stop the feed monitor scheduler"""
        if not self._is_running:
            return

        logger.info("Stopping feed monitor")
        self.scheduler.shutdown(wait=True)

        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

        self._is_running = False
        logger.info("Feed monitor stopped")

    async def _check_feeds(self):
        """
        Check all active feeds for new articles.

        Called periodically by scheduler.
        """
        db = SessionLocal()
        try:
            logger.info("Starting feed check cycle")

            # Get all active feeds from Feed Service
            feeds = await self._fetch_active_feeds()

            if not feeds:
                logger.info("No active feeds found")
                return

            logger.info(f"Found {len(feeds)} active feeds to check")

            # Process each feed
            new_articles_total = 0
            for feed in feeds:
                try:
                    new_articles = await self._process_feed(db, feed)
                    new_articles_total += new_articles
                except Exception as e:
                    logger.error(f"Error processing feed {feed.get('id')}: {e}")

            logger.info(f"Feed check cycle complete: {new_articles_total} new articles found")

        except Exception as e:
            logger.error(f"Error in feed check cycle: {e}")
        finally:
            db.close()

    async def _fetch_active_feeds(self) -> List[Dict[str, Any]]:
        """
        Fetch all active feeds from Feed Service.

        Returns:
            List of feed dictionaries
        """
        try:
            url = f"{settings.FEED_SERVICE_URL}/api/v1/feeds"
            params = {"is_active": True}

            logger.info(f"Fetching active feeds from {url} with params={params}")
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()

            logger.info(f"Response status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")

            # Feed Service returns list directly, not wrapped in dict
            feeds = response.json()
            logger.info(f"Response type: {type(feeds)}, length: {len(feeds) if isinstance(feeds, list) else 'N/A'}")

            if not isinstance(feeds, list):
                logger.error(f"Unexpected response format: {type(feeds)}, value: {feeds}")
                return []

            logger.info(f"Fetched {len(feeds)} active feeds from Feed Service")
            return feeds

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching feeds: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching active feeds: {e}")
            return []

    async def _process_feed(self, db: Session, feed: Dict[str, Any]) -> int:
        """
        Process a single feed - check for new articles since last check.

        Args:
            db: Database session
            feed: Feed dictionary from Feed Service

        Returns:
            Number of new articles found
        """
        feed_id = feed.get("id")

        # Get or create schedule state for this feed
        schedule_state = db.query(FeedScheduleState).filter(
            FeedScheduleState.feed_id == feed_id
        ).first()

        if not schedule_state:
            schedule_state = FeedScheduleState(feed_id=feed_id)
            db.add(schedule_state)
            db.commit()
            db.refresh(schedule_state)

        # Get articles from feed (only new ones since last check)
        articles = await self._fetch_feed_articles(feed_id, schedule_state.last_checked_at)

        if not articles:
            # Update last checked time even if no new articles
            schedule_state.last_checked_at = datetime.now(timezone.utc)
            db.commit()
            return 0

        logger.info(f"Feed {feed_id}: Found {len(articles)} new articles")

        # Schedule analysis jobs for new articles
        jobs_created = 0
        for article in articles:
            if await self._schedule_analysis(db, feed_id, feed, article):
                jobs_created += 1

        # Update schedule state
        schedule_state.last_checked_at = datetime.now(timezone.utc)
        schedule_state.last_article_processed_at = datetime.now(timezone.utc)
        schedule_state.total_articles_processed += jobs_created
        db.commit()

        logger.info(f"Feed {feed_id}: Scheduled {jobs_created} analysis jobs")
        return jobs_created

    async def _fetch_feed_articles(
        self,
        feed_id: str,
        since: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from Feed Service for a specific feed.

        Args:
            feed_id: Feed UUID
            since: Only fetch articles published after this time (optional)

        Returns:
            List of article dictionaries
        """
        try:
            # Feed Service uses /items endpoint, not /articles
            url = f"{settings.FEED_SERVICE_URL}/api/v1/feeds/{feed_id}/items"
            params = {}

            if since:
                params["since"] = since.isoformat()

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()

            # Feed Service returns list directly
            articles = response.json()
            if not isinstance(articles, list):
                logger.error(f"Unexpected response format for articles: {type(articles)}")
                return []

            return articles

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching articles for feed {feed_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching articles for feed {feed_id}: {e}")
            return []

    async def _schedule_analysis(
        self,
        db: Session,
        feed_id: str,
        feed: Dict[str, Any],
        article: Dict[str, Any]
    ) -> bool:
        """
        Schedule analysis jobs for an article based on feed category.

        Implements 3-stage pipeline:
        1. Categorization (if enabled)
        2. Specialized Sentiment (based on category)
        3. Standard Sentiment (always)

        Args:
            db: Database session
            feed_id: Feed UUID
            feed: Feed dictionary (contains category info)
            article: Article dictionary

        Returns:
            True if jobs were scheduled successfully
        """
        article_id = article.get("id")

        try:
            # Stage 1: Categorization (if needed)
            category = feed.get("category")
            if not category or category == "general":
                # Schedule categorization job (priority 10 - highest)
                job = AnalysisJobQueue(
                    feed_id=feed_id,
                    article_id=article_id,
                    job_type=JobType.CATEGORIZATION,
                    status=JobStatus.PENDING,
                    priority=10
                )
                db.add(job)
                logger.debug(f"Scheduled categorization for article {article_id}")

            # Stage 2: Specialized Sentiment (based on category)
            if category == "finance":
                job = AnalysisJobQueue(
                    feed_id=feed_id,
                    article_id=article_id,
                    job_type=JobType.FINANCE_SENTIMENT,
                    status=JobStatus.PENDING,
                    priority=8
                )
                db.add(job)
                logger.debug(f"Scheduled finance sentiment for article {article_id}")

            elif category == "geopolitics":
                job = AnalysisJobQueue(
                    feed_id=feed_id,
                    article_id=article_id,
                    job_type=JobType.GEOPOLITICAL_SENTIMENT,
                    status=JobStatus.PENDING,
                    priority=8
                )
                db.add(job)
                logger.debug(f"Scheduled geopolitical sentiment for article {article_id}")

            # Stage 3: Standard Sentiment (always)
            job = AnalysisJobQueue(
                feed_id=feed_id,
                article_id=article_id,
                job_type=JobType.STANDARD_SENTIMENT,
                status=JobStatus.PENDING,
                priority=5
            )
            db.add(job)
            logger.debug(f"Scheduled standard sentiment for article {article_id}")

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error scheduling analysis for article {article_id}: {e}")
            db.rollback()
            return False

    def is_running(self) -> bool:
        """Check if feed monitor is currently running"""
        return self._is_running

    def get_status(self) -> Dict[str, Any]:
        """Get current status of feed monitor"""
        return {
            "is_running": self._is_running,
            "check_interval_seconds": settings.FEED_CHECK_INTERVAL,
            "next_run": None  # APScheduler can provide this if needed
        }


# Global instance
feed_monitor = FeedMonitor()

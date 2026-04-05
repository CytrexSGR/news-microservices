"""
Failure Tracker Service

Tracks scraping failures per feed and automatically disables scraping
after exceeding failure threshold.
"""
import logging
from typing import Optional
import redis.asyncio as redis
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class FailureTracker:
    """
    Tracks scraping failures and auto-disables feeds.

    Uses Redis for fast, distributed failure counting.
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Initialize Redis connection"""
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        if settings.REDIS_PASSWORD:
            redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

        self.redis_client = redis.from_url(redis_url, decode_responses=True)

        # HTTP client for Feed Service API
        headers = {"X-Service-Name": "scraping-service"}
        if settings.FEED_SERVICE_API_KEY:
            headers["X-Service-Key"] = settings.FEED_SERVICE_API_KEY

        self.http_client = httpx.AsyncClient(
            base_url=settings.FEED_SERVICE_URL,
            headers=headers,
            timeout=30.0
        )

        logger.info("Failure tracker initialized")

    async def stop(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.aclose()

        if self.http_client:
            await self.http_client.aclose()

        logger.info("Failure tracker stopped")

    async def record_success(self, feed_id: str):
        """
        Record successful scraping.

        Resets failure counter for the feed in both Redis and database.
        Issue P1-6: Graceful degradation on Redis/HTTP errors.
        """
        # Reset Redis counter (with error handling)
        key = f"scrape_failures:{feed_id}"
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
        except redis.RedisError as e:
            logger.warning(f"Redis error resetting failure counter for feed {feed_id}: {e}")
            # Continue - database update may still work

        # Reset database counter
        try:
            response = await self.http_client.patch(
                f"/api/v1/feeds/{feed_id}",
                json={
                    "scrape_failure_count": 0,
                    "scrape_last_failure_at": None,
                    "scrape_disabled_reason": None  # Clear any auto-disable reason
                }
            )
            response.raise_for_status()
            logger.debug(f"Reset failure counter for feed {feed_id}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to reset database failure counter for feed {feed_id}: {e}")

    async def record_failure(self, feed_id: str) -> bool:
        """
        Record scraping failure in both Redis and database.

        Args:
            feed_id: Feed UUID

        Returns:
            True if threshold exceeded and feed disabled

        Issue P1-6: Graceful degradation on Redis errors.
        """
        key = f"scrape_failures:{feed_id}"

        # Increment Redis counter (for fast tracking) with error handling
        failures = 1  # Default if Redis fails
        try:
            if self.redis_client:
                failures = await self.redis_client.incr(key)

                # Set expiry (24 hours) - failures older than this are forgotten
                if failures == 1:
                    await self.redis_client.expire(key, 86400)
        except redis.RedisError as e:
            logger.warning(f"Redis error incrementing failure counter for feed {feed_id}: {e}")
            # Continue with database update - Redis is just for fast tracking

        # Update database counter and timestamp
        from datetime import datetime, timezone
        try:
            response = await self.http_client.patch(
                f"/api/v1/feeds/{feed_id}",
                json={
                    "scrape_failure_count": failures,
                    "scrape_last_failure_at": datetime.now(timezone.utc).isoformat()
                }
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to update database failure counter for feed {feed_id}: {e}")

        # Get feed-specific threshold (with caching)
        feed_threshold = await self._get_feed_threshold(feed_id)

        logger.warning(f"Scraping failure recorded for feed {feed_id}: {failures}/{feed_threshold} failures")

        # Check threshold (feed-specific)
        if failures >= feed_threshold:
            logger.error(
                f"Feed {feed_id} exceeded failure threshold "
                f"({failures}/{feed_threshold}). Disabling scraping."
            )

            # Disable scraping for this feed
            await self._disable_feed_scraping(feed_id)
            return True

        return False

    async def get_failure_count(self, feed_id: str) -> int:
        """
        Get current failure count for feed.

        Issue P1-6: Returns 0 on Redis errors (graceful degradation).
        """
        key = f"scrape_failures:{feed_id}"
        try:
            if self.redis_client:
                count = await self.redis_client.get(key)
                return int(count) if count else 0
            return 0
        except redis.RedisError as e:
            logger.warning(f"Redis error getting failure count for feed {feed_id}: {e}")
            return 0  # Graceful degradation - return 0 if Redis unavailable

    async def reset_failures(self, feed_id: str):
        """
        Manually reset failure counter.

        Issue P1-6: Graceful degradation on Redis errors.
        """
        key = f"scrape_failures:{feed_id}"
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
                logger.info(f"Manually reset failure counter for feed {feed_id}")
        except redis.RedisError as e:
            logger.warning(f"Redis error resetting failure counter for feed {feed_id}: {e}")

    async def _get_feed_threshold(self, feed_id: str) -> int:
        """
        Get feed-specific failure threshold with Redis caching.

        Args:
            feed_id: Feed UUID

        Returns:
            Feed-specific threshold or default fallback

        Issue P1-6: Graceful degradation on Redis cache errors.
        """
        cache_key = f"feed_threshold:{feed_id}"

        # Try cache first (with error handling)
        try:
            if self.redis_client:
                cached_threshold = await self.redis_client.get(cache_key)
                if cached_threshold:
                    return int(cached_threshold)
        except redis.RedisError as e:
            logger.warning(f"Redis cache read error for threshold {feed_id}: {e}")
            # Continue to fetch from API

        # Fetch from Feed Service API
        try:
            response = await self.http_client.get(
                f"/api/v1/feeds/{feed_id}/threshold"
            )
            response.raise_for_status()
            data = response.json()
            threshold = data.get("scrape_failure_threshold", settings.SCRAPING_FAILURE_THRESHOLD)

            # Cache for 1 hour (with error handling)
            try:
                if self.redis_client:
                    await self.redis_client.setex(cache_key, 3600, threshold)
            except redis.RedisError as e:
                logger.warning(f"Redis cache write error for threshold {feed_id}: {e}")
                # Continue - threshold was fetched successfully

            logger.debug(f"Fetched threshold for feed {feed_id}: {threshold}")
            return threshold

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch threshold for feed {feed_id}: {e}. Using default: {settings.SCRAPING_FAILURE_THRESHOLD}")
            return settings.SCRAPING_FAILURE_THRESHOLD

    async def _disable_feed_scraping(self, feed_id: str):
        """
        Disable scraping for a feed via Feed Service API.

        Updates feed to set scrape_full_content=False and marks reason as "auto_threshold".
        """
        try:
            response = await self.http_client.patch(
                f"/api/v1/feeds/{feed_id}",
                json={
                    "scrape_full_content": False,
                    "scrape_disabled_reason": "auto_threshold"
                }
            )
            response.raise_for_status()

            logger.info(f"Successfully disabled scraping for feed {feed_id} (reason: auto_threshold)")

        except httpx.HTTPError as e:
            logger.error(f"Failed to disable scraping for feed {feed_id}: {e}")


# Global failure tracker instance
failure_tracker = FailureTracker()

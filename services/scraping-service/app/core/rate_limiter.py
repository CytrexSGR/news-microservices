"""
Redis-based Rate Limiting for Scraping Service.

Prevents overwhelming target sites with requests by:
- Limiting scrapes per domain per time window
- Global scraping rate limit (all domains)
- Per-feed custom rate limits
- Redis-backed tracking for distributed rate limiting
"""

import logging
import time
from typing import Optional, Dict
import redis.asyncio as aioredis
from urllib.parse import urlparse

from app.core.config import settings

logger = logging.getLogger(__name__)


class AsyncRateLimiter:
    """
    Async rate limiter using Redis with sliding window algorithm.

    Features:
    - Per-domain rate limiting
    - Global rate limiting
    - Custom rate limits per feed
    - Graceful degradation (fail open if Redis unavailable)
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("✅ Rate limiter connected to Redis")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                # Fail open - continue without rate limiting
                self.redis = None

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Rate limiter disconnected from Redis")

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, int, Optional[int]]:
        """
        Check if request is allowed based on rate limit.

        Uses sliding window algorithm with sorted sets.

        Args:
            key: Unique identifier (e.g., domain, feed_id)
            limit: Maximum requests allowed
            window: Time window in seconds (default 60)

        Returns:
            (allowed: bool, remaining: int, retry_after: Optional[int])
                allowed: True if request should be allowed
                remaining: Number of requests remaining in window
                retry_after: Seconds until next request allowed (if rate limited)
        """
        # Fail open if Redis unavailable
        if not self.redis:
            logger.debug("Redis unavailable, allowing request (fail open)")
            return True, limit, None

        current_time = int(time.time())
        window_start = current_time - window

        # Use sorted set to track requests in time window
        rate_key = f"rate_limit:scraping:{key}"

        try:
            # Remove old entries outside window
            await self.redis.zremrangebyscore(rate_key, 0, window_start)

            # Count requests in current window
            count = await self.redis.zcard(rate_key)

            if count < limit:
                # Add current request
                await self.redis.zadd(rate_key, {str(current_time): current_time})
                await self.redis.expire(rate_key, window + 10)  # Cleanup buffer
                remaining = limit - count - 1
                return True, remaining, None
            else:
                # Rate limited - calculate retry_after
                # Get oldest request in window
                oldest_entries = await self.redis.zrange(rate_key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_time = int(oldest_entries[0][1])
                    retry_after = max(1, (oldest_time + window) - current_time)
                else:
                    retry_after = window

                logger.warning(
                    f"🚦 Rate limit exceeded for {key}: "
                    f"{count}/{limit} requests in {window}s window. "
                    f"Retry after {retry_after}s"
                )
                return False, 0, retry_after

        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Fail open - allow request if Redis operation fails
            return True, limit, None

    async def check_scrape_allowed(
        self,
        url: str,
        feed_id: Optional[str] = None,
        custom_limit: Optional[int] = None
    ) -> tuple[bool, str, Optional[int]]:
        """
        Check if scraping is allowed for a URL.

        Checks both domain-level and global rate limits.

        Args:
            url: URL to scrape
            feed_id: Optional feed ID for per-feed limits
            custom_limit: Optional custom rate limit (overrides default)

        Returns:
            (allowed: bool, reason: str, retry_after: Optional[int])
        """
        # Extract domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]

        # Check domain-level rate limit
        domain_limit = custom_limit or settings.SCRAPING_RATE_LIMIT_PER_DOMAIN
        domain_window = settings.SCRAPING_RATE_LIMIT_WINDOW

        allowed, remaining, retry_after = await self.is_allowed(
            key=f"domain:{domain}",
            limit=domain_limit,
            window=domain_window
        )

        if not allowed:
            return False, f"Domain rate limit exceeded for {domain}", retry_after

        # Check global rate limit
        global_limit = settings.SCRAPING_RATE_LIMIT_GLOBAL
        global_window = settings.SCRAPING_RATE_LIMIT_WINDOW

        allowed, remaining, retry_after = await self.is_allowed(
            key="global",
            limit=global_limit,
            window=global_window
        )

        if not allowed:
            return False, "Global scraping rate limit exceeded", retry_after

        # Check per-feed rate limit (if feed_id provided)
        if feed_id:
            feed_limit = custom_limit or settings.SCRAPING_RATE_LIMIT_PER_FEED
            feed_window = settings.SCRAPING_RATE_LIMIT_WINDOW

            allowed, remaining, retry_after = await self.is_allowed(
                key=f"feed:{feed_id}",
                limit=feed_limit,
                window=feed_window
            )

            if not allowed:
                return False, f"Feed rate limit exceeded for feed {feed_id}", retry_after

        return True, "allowed", None

    async def get_stats(self, key: str) -> Dict[str, int]:
        """
        Get current rate limit statistics for a key.

        Args:
            key: Rate limit key (e.g., "domain:example.com")

        Returns:
            dict: Statistics including current count and window
        """
        if not self.redis:
            return {"count": 0, "window_start": 0}

        try:
            rate_key = f"rate_limit:scraping:{key}"
            current_time = int(time.time())
            window = settings.SCRAPING_RATE_LIMIT_WINDOW
            window_start = current_time - window

            # Remove old entries
            await self.redis.zremrangebyscore(rate_key, 0, window_start)

            # Get count
            count = await self.redis.zcard(rate_key)

            return {
                "count": count,
                "window_start": window_start,
                "window_seconds": window,
            }

        except Exception as e:
            logger.error(f"Failed to get rate limit stats: {e}")
            return {"count": 0, "window_start": 0}


# Global rate limiter instance
rate_limiter = AsyncRateLimiter(
    redis_url=settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
)

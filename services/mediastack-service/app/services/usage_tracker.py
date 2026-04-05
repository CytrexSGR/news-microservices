"""Usage tracking for MediaStack API rate limiting."""

import redis.asyncio as redis
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from calendar import monthrange

from app.core.config import settings

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Track MediaStack API usage with Redis.

    Uses monthly counter with automatic reset.
    Free plan: 10,000 calls/month
    """

    def __init__(self):
        self.monthly_limit = settings.MEDIASTACK_MONTHLY_LIMIT
        self._redis: Optional[redis.Redis] = None
        self._key_prefix = "mediastack:usage"

    async def connect(self):
        """Connect to Redis."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False
            )
            logger.info("Usage tracker connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _get_month_key(self) -> str:
        """Get Redis key for current month."""
        now = datetime.utcnow()
        return f"{self._key_prefix}:{now.year}:{now.month:02d}"

    def _get_month_end(self) -> datetime:
        """Get end of current month for TTL."""
        now = datetime.utcnow()
        _, last_day = monthrange(now.year, now.month)
        return datetime(now.year, now.month, last_day, 23, 59, 59)

    async def can_make_request(self) -> bool:
        """
        Check if we can make another API request.

        Returns:
            True if within monthly limit
        """
        if not self._redis:
            await self.connect()

        key = self._get_month_key()
        current = await self._redis.get(key)
        count = int(current) if current else 0

        return count < self.monthly_limit

    async def record_request(self) -> int:
        """
        Record an API request.

        Returns:
            New total count for the month
        """
        if not self._redis:
            await self.connect()

        key = self._get_month_key()
        count = await self._redis.incr(key)

        # Set expiry at end of month (first call only)
        if count == 1:
            month_end = self._get_month_end()
            await self._redis.expireat(key, month_end)

        logger.debug(f"API call recorded: {count}/{self.monthly_limit}")
        return count

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.

        Returns:
            Usage stats including current count, limit, remaining
        """
        if not self._redis:
            await self.connect()

        key = self._get_month_key()
        current = await self._redis.get(key)
        count = int(current) if current else 0

        remaining = max(0, self.monthly_limit - count)
        percentage = (count / self.monthly_limit * 100) if self.monthly_limit > 0 else 0

        now = datetime.utcnow()
        _, last_day = monthrange(now.year, now.month)
        days_remaining = last_day - now.day + 1

        return {
            "current_calls": count,
            "monthly_limit": self.monthly_limit,
            "remaining": remaining,
            "percentage": round(percentage, 2),
            "month": f"{now.year}-{now.month:02d}",
            "days_remaining": days_remaining,
            "calls_per_day_remaining": remaining // days_remaining if days_remaining > 0 else 0,
            "status": "critical" if percentage >= 90 else "warning" if percentage >= 70 else "ok"
        }


# Singleton
_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get singleton usage tracker."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker

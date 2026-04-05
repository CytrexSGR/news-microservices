"""
Redis async client for analytics-service.

Provides async Redis client for intelligence features:
- Burst detection caching
- Novelty score fingerprints
- Cross-validation tracking
"""

import redis.asyncio as redis
from typing import Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Singleton Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get async Redis client.

    Uses singleton pattern to reuse connection pool.
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        logger.info("Redis async client initialized", url=settings.REDIS_URL[:30] + "...")

    return _redis_client


async def close_redis():
    """
    Close Redis connection pool gracefully.

    Call this on application shutdown.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis async client closed")


async def health_check() -> bool:
    """
    Check Redis connection health.
    """
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False

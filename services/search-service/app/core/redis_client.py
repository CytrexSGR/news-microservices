"""
Redis client for caching
"""
import json
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client singleton.

    Returns:
        redis.Redis: Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Optional[Any]: Cached value or None
    """
    client = await get_redis_client()
    value = await client.get(key)

    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    return None


async def cache_set(key: str, value: Any, ttl: Optional[int] = None):
    """
    Set value in cache.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (optional)
    """
    client = await get_redis_client()

    if isinstance(value, (dict, list)):
        value = json.dumps(value)

    if ttl:
        await client.setex(key, ttl, value)
    else:
        await client.set(key, value)


async def cache_delete(key: str):
    """
    Delete value from cache.

    Args:
        key: Cache key
    """
    client = await get_redis_client()
    await client.delete(key)


async def close_redis_client():
    """Close Redis connection"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

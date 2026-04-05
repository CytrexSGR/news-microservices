"""
Redis cache client for News Microservices Platform.

Provides async Redis operations with JSON serialization support.

Task 403: Caching Strategy Implementation
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import os
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Async Redis cache client with JSON serialization.

    Features:
    - Async/await support for all operations
    - Automatic JSON serialization/deserialization
    - TTL-based expiration
    - Pattern-based batch operations
    - Connection pooling

    Example:
        ```python
        cache = RedisCache()
        await cache.set("user:123", {"name": "Andreas"}, ttl=300)
        user = await cache.get("user:123")
        await cache.delete("user:123")
        ```
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis client.

        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env var)
        """
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL", "redis://redis:6379/0"
        )
        self._redis: Optional[redis.Redis] = None

    async def _ensure_connection(self):
        """Ensure Redis connection is established."""
        if self._redis is None:
            try:
                self._redis = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                )
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    async def get(self, key: str) -> Optional[dict]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value as dict, or None if not found
        """
        await self._ensure_connection()
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode cache value for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: int = 300
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 5 minutes)

        Returns:
            True if successful, False otherwise
        """
        await self._ensure_connection()
        try:
            serialized = json.dumps(value)
            await self._redis.setex(key, ttl, serialized)
            logger.debug(f"Cached key {key} with TTL {ttl}s")
            return True
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize value for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        await self._ensure_connection()
        try:
            result = await self._redis.delete(key)
            logger.debug(f"Deleted cache key {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*", "feed:123:*")

        Returns:
            Number of keys deleted
        """
        await self._ensure_connection()
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                deleted = await self._redis.delete(*keys)
                logger.info(
                    f"Deleted {deleted} keys matching pattern {pattern}"
                )
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        await self._ensure_connection()
        try:
            result = await self._redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, -1 if key has no expiry, -2 if key doesn't exist
        """
        await self._ensure_connection()
        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2

    async def info(self) -> dict:
        """
        Get Redis server info.

        Returns:
            Redis INFO dict with server statistics
        """
        await self._ensure_connection()
        try:
            return await self._redis.info()
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Closed Redis connection")


# Global cache instance
cache = RedisCache()

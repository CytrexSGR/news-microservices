"""Redis cache manager for MCP Intelligence Server."""

import json
import logging
import time
from typing import Any, Optional, Callable
from functools import wraps
import hashlib

import redis.asyncio as redis
from redis.exceptions import RedisError

from .config import settings
from .metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    CACHE_LATENCY,
    CACHE_ERRORS,
    CACHE_SIZE,
    REDIS_CONNECTED,
    REDIS_OPERATIONS_TOTAL,
)

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis cache manager with async support.

    Provides caching functionality for MCP Intelligence Server to reduce
    load on backend services and improve response times.

    Cache Strategy:
    - SHORT (5min):  Fast-changing data (event clusters, latest events)
    - MEDIUM (30min): Moderate data (entity clusters, narrative frames)
    - LONG (1h):     Stable data (overviews, statistics)
    """

    def __init__(self):
        """Initialize Redis connection pool."""
        self.redis: Optional[redis.Redis] = None
        self._enabled = True  # Cache can be disabled if Redis unavailable

    async def connect(self):
        """Establish Redis connection."""
        try:
            # Build connection kwargs
            conn_kwargs = {
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db,
                "decode_responses": True,  # Auto-decode bytes to str
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            }
            # Only add password if it's not empty
            if settings.redis_password:
                conn_kwargs["password"] = settings.redis_password

            self.redis = redis.Redis(**conn_kwargs)
            # Test connection
            await self.redis.ping()

            # Update connection metric
            REDIS_CONNECTED.set(1)
            REDIS_OPERATIONS_TOTAL.labels(operation="connect", status="success").inc()

            logger.info(
                f"Redis cache connected: {settings.redis_host}:{settings.redis_port} DB={settings.redis_db}"
            )
        except RedisError as e:
            # Update connection metric
            REDIS_CONNECTED.set(0)
            REDIS_OPERATIONS_TOTAL.labels(operation="connect", status="failure").inc()

            logger.warning(
                f"Redis connection failed: {e}. Cache disabled, will fallback to direct calls.",
                extra={"error": str(e)},
            )
            self._enabled = False
            self.redis = None

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.aclose()
            logger.info("Redis cache connection closed")

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments.

        Args:
            prefix: Cache key prefix (usually function name)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create deterministic key from args/kwargs
        key_parts = [prefix]

        # Add positional args
        if args:
            key_parts.extend(str(arg) for arg in args)

        # Add sorted keyword args
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

        # Hash for very long keys
        key_str = ":".join(key_parts)
        if len(key_str) > 200:
            key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
            return f"{prefix}:{key_hash}"

        return key_str

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found/expired
        """
        if not self._enabled or not self.redis:
            return None

        # Extract key prefix for metrics
        key_prefix = key.split(":")[0] if ":" in key else "unknown"

        start_time = time.perf_counter()
        try:
            value = await self.redis.get(key)
            elapsed = time.perf_counter() - start_time

            # Record latency
            CACHE_LATENCY.labels(operation="get").observe(elapsed)
            REDIS_OPERATIONS_TOTAL.labels(operation="get", status="success").inc()

            if value:
                # Cache HIT
                CACHE_HITS.labels(key_prefix=key_prefix).inc()
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                # Cache MISS
                CACHE_MISSES.labels(key_prefix=key_prefix).inc()
                logger.debug(f"Cache MISS: {key}")
                return None
        except (RedisError, json.JSONDecodeError) as e:
            # Record error
            error_type = type(e).__name__
            CACHE_ERRORS.labels(operation="get", error_type=error_type).inc()
            REDIS_OPERATIONS_TOTAL.labels(operation="get", status="failure").inc()

            logger.warning(
                f"Cache GET failed for {key}: {e}",
                extra={"key": key, "error": str(e)},
            )
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        if not self._enabled or not self.redis:
            return

        start_time = time.perf_counter()
        try:
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            elapsed = time.perf_counter() - start_time

            # Record metrics
            CACHE_LATENCY.labels(operation="set").observe(elapsed)
            REDIS_OPERATIONS_TOTAL.labels(operation="set", status="success").inc()

            logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
        except (RedisError, json.JSONEncodeError, TypeError) as e:
            # Record error
            error_type = type(e).__name__
            CACHE_ERRORS.labels(operation="set", error_type=error_type).inc()
            REDIS_OPERATIONS_TOTAL.labels(operation="set", status="failure").inc()

            logger.warning(
                f"Cache SET failed for {key}: {e}",
                extra={"key": key, "ttl": ttl, "error": str(e)},
            )

    async def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if not self._enabled or not self.redis:
            return

        start_time = time.perf_counter()
        try:
            await self.redis.delete(key)
            elapsed = time.perf_counter() - start_time

            # Record metrics
            CACHE_LATENCY.labels(operation="delete").observe(elapsed)
            REDIS_OPERATIONS_TOTAL.labels(operation="delete", status="success").inc()

            logger.debug(f"Cache DELETE: {key}")
        except RedisError as e:
            # Record error
            error_type = type(e).__name__
            CACHE_ERRORS.labels(operation="delete", error_type=error_type).inc()
            REDIS_OPERATIONS_TOTAL.labels(operation="delete", status="failure").inc()

            logger.warning(
                f"Cache DELETE failed for {key}: {e}",
                extra={"key": key, "error": str(e)},
            )

    async def clear_pattern(self, pattern: str):
        """
        Clear all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "intelligence:*")
        """
        if not self._enabled or not self.redis:
            return

        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break

            if deleted > 0:
                logger.info(f"Cleared {deleted} cache keys matching: {pattern}")
        except RedisError as e:
            logger.warning(
                f"Cache CLEAR failed for pattern {pattern}: {e}",
                extra={"pattern": pattern, "error": str(e)},
            )

    def cached(
        self,
        ttl: int = 300,
        key_prefix: Optional[str] = None,
    ) -> Callable:
        """
        Decorator to cache function results.

        Usage:
            @cache_manager.cached(ttl=1800, key_prefix="intelligence")
            async def get_event_clusters(self, limit: int = 50):
                # ... expensive operation ...
                return result

        Args:
            ttl: Cache TTL in seconds (default: 5 minutes)
            key_prefix: Optional key prefix (defaults to function name)

        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Use function name as default prefix
                prefix = key_prefix or func.__qualname__

                # Generate cache key from function args
                cache_key = self._generate_key(prefix, *args[1:], **kwargs)

                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Cache miss - call original function
                result = await func(*args, **kwargs)

                # Cache result
                await self.set(cache_key, result, ttl=ttl)

                return result

            return wrapper
        return decorator


# Global cache manager instance
cache_manager = CacheManager()

"""Redis cache manager for MCP Orchestration Server."""

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
    REDIS_CONNECTED,
    REDIS_OPERATIONS_TOTAL,
)

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager with async support."""

    def __init__(self):
        """Initialize Redis connection pool."""
        self.redis: Optional[redis.Redis] = None
        self._enabled = True

    async def connect(self):
        """Establish Redis connection."""
        try:
            conn_kwargs = {
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db,
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            }

            if settings.redis_password:
                conn_kwargs["password"] = settings.redis_password

            self.redis = redis.Redis(**conn_kwargs)
            await self.redis.ping()

            REDIS_CONNECTED.set(1)
            REDIS_OPERATIONS_TOTAL.labels(operation="connect", status="success").inc()

            logger.info(
                f"Redis cache connected: {settings.redis_host}:{settings.redis_port} DB={settings.redis_db}"
            )
        except RedisError as e:
            REDIS_CONNECTED.set(0)
            REDIS_OPERATIONS_TOTAL.labels(operation="connect", status="failure").inc()

            logger.warning(
                f"Redis connection failed: {e}. Cache disabled.",
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
        """Generate cache key from function arguments."""
        key_parts = [prefix]

        if args:
            key_parts.extend(str(arg) for arg in args)

        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

        key_str = ":".join(key_parts)
        if len(key_str) > 200:
            key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
            return f"{prefix}:{key_hash}"

        return key_str

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._enabled or not self.redis:
            return None

        key_prefix = key.split(":")[0] if ":" in key else "unknown"

        start_time = time.perf_counter()
        try:
            value = await self.redis.get(key)
            elapsed = time.perf_counter() - start_time

            CACHE_LATENCY.labels(operation="get").observe(elapsed)
            REDIS_OPERATIONS_TOTAL.labels(operation="get", status="success").inc()

            if value:
                CACHE_HITS.labels(key_prefix=key_prefix).inc()
                return json.loads(value)
            else:
                CACHE_MISSES.labels(key_prefix=key_prefix).inc()
                return None
        except (RedisError, json.JSONDecodeError) as e:
            error_type = type(e).__name__
            CACHE_ERRORS.labels(operation="get", error_type=error_type).inc()
            REDIS_OPERATIONS_TOTAL.labels(operation="get", status="failure").inc()
            return None

    async def set(self, key: str, value: Any, ttl: int = 60):
        """Set value in cache with TTL."""
        if not self._enabled or not self.redis:
            return

        start_time = time.perf_counter()
        try:
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            elapsed = time.perf_counter() - start_time

            CACHE_LATENCY.labels(operation="set").observe(elapsed)
            REDIS_OPERATIONS_TOTAL.labels(operation="set", status="success").inc()
        except (RedisError, TypeError) as e:
            error_type = type(e).__name__
            CACHE_ERRORS.labels(operation="set", error_type=error_type).inc()
            REDIS_OPERATIONS_TOTAL.labels(operation="set", status="failure").inc()

    async def delete(self, key: str):
        """Delete value from cache."""
        if not self._enabled or not self.redis:
            return

        try:
            await self.redis.delete(key)
            REDIS_OPERATIONS_TOTAL.labels(operation="delete", status="success").inc()
        except RedisError:
            REDIS_OPERATIONS_TOTAL.labels(operation="delete", status="failure").inc()


# Global cache manager instance
cache_manager = CacheManager()

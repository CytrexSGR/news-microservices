"""
Caching decorators for News Microservices Platform.

Provides decorators for automatic response caching with Redis.

Task 403: Caching Strategy Implementation
"""

from functools import wraps
from typing import Optional, Callable, Any, List
import hashlib
import json
import logging

from .redis_client import cache

logger = logging.getLogger(__name__)


def _serialize_for_cache(value: Any) -> Any:
    """
    Serialize value for Redis cache, handling Pydantic models.

    Args:
        value: Value to serialize (can be Pydantic model, list of models, or plain data)

    Returns:
        JSON-serializable representation of the value
    """
    # Handle Pydantic v2 models (model_dump)
    if hasattr(value, 'model_dump'):
        return value.model_dump(mode='json')

    # Handle Pydantic v1 models (dict)
    if hasattr(value, 'dict') and callable(value.dict):
        return value.dict()

    # Handle lists/tuples of Pydantic models
    if isinstance(value, (list, tuple)):
        return [_serialize_for_cache(item) for item in value]

    # Handle dicts with potential Pydantic model values
    if isinstance(value, dict):
        return {k: _serialize_for_cache(v) for k, v in value.items()}

    # Return as-is for primitive types
    return value


def _generate_cache_key(
    prefix: str, args: tuple, kwargs: dict
) -> str:
    """
    Generate deterministic cache key from function arguments.

    Args:
        prefix: Key prefix (usually function name)
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Cache key in format: prefix:hash
    """
    # Create deterministic representation of arguments
    key_data = {
        "args": args,
        "kwargs": {k: v for k, v in sorted(kwargs.items())}
    }

    # Hash the arguments for compact key
    key_json = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_json.encode()).hexdigest()[:12]

    return f"{prefix}:{key_hash}"


def cached(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    key_builder: Optional[Callable] = None
) -> Callable:
    """
    Decorator to cache function results in Redis.

    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
        key_prefix: Custom cache key prefix (default: function name)
        key_builder: Custom function to build cache key from args

    Returns:
        Decorated function with caching

    Example:
        ```python
        @cached(ttl=300, key_prefix="feeds:list")
        async def list_feeds(skip: int, limit: int):
            # This will be cached for 5 minutes
            return await db.query(Feed).offset(skip).limit(limit).all()
        ```

    Cache Behavior:
        - On cache hit: Returns cached result immediately
        - On cache miss: Calls function, stores result, returns
        - On error: Logs error and calls function (cache bypass)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build cache key
            prefix = key_prefix or func.__name__

            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Filter out non-cacheable args (like DB sessions)
                cacheable_kwargs = {
                    k: v for k, v in kwargs.items()
                    if not k in ['db', 'session', 'request', 'background_tasks']
                }
                cache_key = _generate_cache_key(prefix, args, cacheable_kwargs)

            # Try cache
            try:
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached_result
            except Exception as e:
                logger.error(f"Cache get failed for {cache_key}: {e}")

            # Cache miss: Call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache (serialize Pydantic models first)
            try:
                cacheable_result = _serialize_for_cache(result)
                await cache.set(cache_key, cacheable_result, ttl)
            except Exception as e:
                logger.error(f"Cache set failed for {cache_key}: {e}")

            return result

        # Add cache key inspection for debugging
        wrapper._cache_prefix = key_prefix or func.__name__
        wrapper._cache_ttl = ttl

        return wrapper
    return decorator


async def cache_invalidate(pattern: str) -> int:
    """
    Invalidate cache keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "feed:*", "article:123:*")

    Returns:
        Number of keys deleted

    Example:
        ```python
        # Invalidate all feed caches
        await cache_invalidate("feed:*")

        # Invalidate specific feed
        await cache_invalidate(f"feed:{feed_id}:*")
        ```
    """
    try:
        deleted = await cache.clear_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache keys matching {pattern}")
        return deleted
    except Exception as e:
        logger.error(f"Cache invalidation failed for {pattern}: {e}")
        return 0


def cache_key_for(func_name: str, *args, **kwargs) -> str:
    """
    Generate cache key for manual cache operations.

    Args:
        func_name: Function name or key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string

    Example:
        ```python
        key = cache_key_for("feeds:list", skip=0, limit=100)
        await cache.delete(key)
        ```
    """
    return _generate_cache_key(func_name, args, kwargs)

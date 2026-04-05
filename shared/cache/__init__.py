"""
Shared caching utilities for News Microservices Platform.

Provides Redis-based caching with async support and decorators.
"""

from .redis_client import RedisCache, cache
from .decorators import cached, cache_invalidate

__all__ = ["RedisCache", "cache", "cached", "cache_invalidate"]

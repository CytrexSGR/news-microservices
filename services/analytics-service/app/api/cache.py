"""
Cache monitoring API endpoints

Provides real-time metrics for Redis cache performance.

Task 403: Caching Strategy Implementation - Phase 5
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])
logger = logging.getLogger(__name__)

# Import cache client
try:
    from shared.cache import cache
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    logger.warning("shared.cache not available - cache monitoring disabled")


def _calculate_hit_rate(info: dict) -> float:
    """
    Calculate cache hit rate from Redis INFO stats.

    Args:
        info: Redis INFO dict

    Returns:
        Hit rate as percentage (0-100)
    """
    keyspace_hits = info.get("keyspace_hits", 0)
    keyspace_misses = info.get("keyspace_misses", 0)

    total_requests = keyspace_hits + keyspace_misses
    if total_requests == 0:
        return 0.0

    return (keyspace_hits / total_requests) * 100


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get Redis cache statistics.

    Returns comprehensive cache metrics including:
    - Memory usage
    - Hit rate
    - Total keys
    - Evicted keys
    - Uptime

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "used_memory": "15.2M",
        "used_memory_peak": "18.4M",
        "hit_rate": 67.8,
        "total_keys": 142,
        "evicted_keys": 23,
        "expired_keys": 89,
        "connected_clients": 5,
        "uptime_seconds": 86400,
        "ops_per_sec": 125,
        "cache_enabled": true
    }
    ```

    **Status Codes:**
    - 200: Success
    - 503: Cache not available
    """
    if not CACHING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Caching is not enabled or Redis is not available"
        )

    try:
        # Get Redis INFO
        info = await cache.info()

        # Extract relevant metrics
        stats = {
            "status": "healthy",
            "cache_enabled": True,

            # Memory metrics
            "used_memory": info.get("used_memory_human", "N/A"),
            "used_memory_peak": info.get("used_memory_peak_human", "N/A"),
            "used_memory_rss": info.get("used_memory_rss_human", "N/A"),
            "maxmemory": info.get("maxmemory_human", "N/A"),
            "maxmemory_policy": info.get("maxmemory_policy", "N/A"),

            # Performance metrics
            "hit_rate": round(_calculate_hit_rate(info), 2),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "ops_per_sec": info.get("instantaneous_ops_per_sec", 0),

            # Key metrics
            "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0,
            "evicted_keys": info.get("evicted_keys", 0),
            "expired_keys": info.get("expired_keys", 0),

            # Connection metrics
            "connected_clients": info.get("connected_clients", 0),
            "blocked_clients": info.get("blocked_clients", 0),

            # Server metrics
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "redis_version": info.get("redis_version", "unknown"),
        }

        return stats

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to cache: {str(e)}"
        )


@router.get("/health")
async def check_cache_health() -> Dict[str, str]:
    """
    Health check for cache availability.

    Returns simple status indicator.

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "message": "Cache is operational"
    }
    ```

    **Status Codes:**
    - 200: Cache is healthy
    - 503: Cache unavailable
    """
    if not CACHING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cache not available"
        )

    try:
        # Simple ping test
        info = await cache.info()
        return {
            "status": "healthy",
            "message": "Cache is operational",
            "uptime_seconds": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cache health check failed: {str(e)}"
        )


@router.post("/clear")
async def clear_cache_pattern(pattern: str = "*") -> Dict[str, Any]:
    """
    Clear cache keys matching a pattern.

    **Warning:** This is a destructive operation. Use with caution.

    **Args:**
    - pattern: Redis key pattern (default: "*" clears all)

    **Example Patterns:**
    - `*` - Clear all keys
    - `feeds:*` - Clear all feed-related caches
    - `feed:items:*` - Clear all feed item caches
    - `feed:items:123:*` - Clear caches for specific feed

    **Example Response:**
    ```json
    {
        "status": "cleared",
        "pattern": "feeds:*",
        "keys_deleted": 42
    }
    ```

    **Status Codes:**
    - 200: Cache cleared successfully
    - 503: Cache not available
    """
    if not CACHING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cache not available"
        )

    try:
        from shared.cache import cache_invalidate
        deleted = await cache_invalidate(pattern)

        return {
            "status": "cleared",
            "pattern": pattern,
            "keys_deleted": deleted
        }
    except Exception as e:
        logger.error(f"Failed to clear cache pattern {pattern}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

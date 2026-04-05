"""
Redis Cache Manager for Narrative Service
Provides caching for narrative analysis results
"""
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class NarrativeCacheManager:
    """
    Cache manager for narrative analysis results

    Cache keys:
    - narrative:frame:{text_hash} - Frame detection results
    - narrative:bias:{text_hash}:{source_hash} - Bias analysis results
    - narrative:cluster:{params_hash} - Cluster results
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

        # Cache TTL settings (in seconds)
        self.ttl_frame_detection = 3600  # 1 hour
        self.ttl_bias_analysis = 3600    # 1 hour
        self.ttl_cluster = 1800          # 30 minutes
        self.ttl_overview = 300          # 5 minutes

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            await self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis cache: {e}")
            self.redis_client = None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache connection closed")

    def _generate_hash(self, data: str) -> str:
        """Generate hash for cache key"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def _get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    async def _set(self, key: str, value: Dict[str, Any], ttl: int):
        """Set value in cache with TTL"""
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")

    async def get_frame_detection(self, text: str) -> Optional[Dict[str, Any]]:
        """Get cached frame detection results"""
        text_hash = self._generate_hash(text)
        key = f"narrative:frame:{text_hash}"
        return await self._get(key)

    async def set_frame_detection(self, text: str, result: Dict[str, Any]):
        """Cache frame detection results"""
        text_hash = self._generate_hash(text)
        key = f"narrative:frame:{text_hash}"
        await self._set(key, result, self.ttl_frame_detection)

    async def get_bias_analysis(self, text: str, source: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached bias analysis results"""
        text_hash = self._generate_hash(text)
        source_hash = self._generate_hash(source or "")
        key = f"narrative:bias:{text_hash}:{source_hash}"
        return await self._get(key)

    async def set_bias_analysis(self, text: str, source: Optional[str], result: Dict[str, Any]):
        """Cache bias analysis results"""
        text_hash = self._generate_hash(text)
        source_hash = self._generate_hash(source or "")
        key = f"narrative:bias:{text_hash}:{source_hash}"
        await self._set(key, result, self.ttl_bias_analysis)

    async def get_overview(self, params: str) -> Optional[Dict[str, Any]]:
        """Get cached overview results"""
        params_hash = self._generate_hash(params)
        key = f"narrative:overview:{params_hash}"
        return await self._get(key)

    async def set_overview(self, params: str, result: Dict[str, Any]):
        """Cache overview results"""
        params_hash = self._generate_hash(params)
        key = f"narrative:overview:{params_hash}"
        await self._set(key, result, self.ttl_overview)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        if not self.redis_client:
            return

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching: {pattern}")
        except Exception as e:
            logger.warning(f"Cache invalidation error for pattern {pattern}: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"error": "Redis not connected"}

        try:
            info = await self.redis_client.info("stats")

            # Count keys by type
            frame_keys = await self.redis_client.keys("narrative:frame:*")
            bias_keys = await self.redis_client.keys("narrative:bias:*")
            overview_keys = await self.redis_client.keys("narrative:overview:*")

            return {
                "connected": True,
                "total_keys": len(frame_keys) + len(bias_keys) + len(overview_keys),
                "frame_detection_cached": len(frame_keys),
                "bias_analysis_cached": len(bias_keys),
                "overview_cached": len(overview_keys),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
cache_manager: Optional[NarrativeCacheManager] = None


def get_cache_manager() -> Optional[NarrativeCacheManager]:
    """Get cache manager instance"""
    return cache_manager

# services/clustering-service/app/services/embedding_service.py
"""
OpenAI Embedding Service for Semantic Topic Search

Generates embeddings for search queries using OpenAI text-embedding-3-small.
Uses LRU caching to minimize API costs for repeated queries.

Usage:
    service = get_embedding_service()
    embedding = await service.embed_query("federal reserve interest rates")
    # embedding = [0.123, -0.456, ..., 0.789]  # 1536 floats
"""

import hashlib
import logging
from typing import List, Optional

from cachetools import LRUCache
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    OpenAI embedding service with LRU caching for semantic topic search.

    Features:
    - text-embedding-3-small model (1536 dimensions, $0.02/1M tokens)
    - LRU cache for repeated queries
    - MD5 hash normalization for cache keys
    """

    def __init__(self):
        """Initialize OpenAI client and LRU cache."""
        if not settings.OPENAI_API_KEY:
            logger.warning(
                "OPENAI_API_KEY not set - semantic search will be unavailable"
            )
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        self.cache: LRUCache = LRUCache(maxsize=settings.EMBEDDING_CACHE_SIZE)
        self.model = settings.EMBEDDING_MODEL

        # Metrics
        self._cache_hits = 0
        self._cache_misses = 0
        self._api_calls = 0

        logger.info(
            f"EmbeddingService initialized (model={self.model}, "
            f"cache_size={settings.EMBEDDING_CACHE_SIZE}, "
            f"api_available={self.client is not None})"
        )

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text using MD5 hash."""
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def is_available(self) -> bool:
        """Check if embedding service is available (API key configured)."""
        return self.client is not None

    async def embed_query(self, query: str) -> Optional[List[float]]:
        """
        Generate embedding for search query with caching.

        Args:
            query: Search query text

        Returns:
            Embedding vector (1536 dimensions) or None if unavailable

        Example:
            embedding = await service.embed_query("finance stocks market")
            # embedding = [0.123, -0.456, ..., 0.789]  # 1536 floats
        """
        if not self.client:
            logger.warning("Embedding unavailable - OPENAI_API_KEY not configured")
            return None

        # Check cache first
        cache_key = self._get_cache_key(query)

        if cache_key in self.cache:
            self._cache_hits += 1
            logger.debug(f"Cache HIT for query '{query[:50]}...'")
            return self.cache[cache_key]

        # Cache miss - call OpenAI API
        self._cache_misses += 1
        logger.debug(f"Cache MISS for query '{query[:50]}...' - calling OpenAI API")

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=query,
                encoding_format="float"
            )

            self._api_calls += 1

            # Extract embedding vector
            embedding = response.data[0].embedding

            # Cache result
            self.cache[cache_key] = embedding

            logger.debug(
                f"Embedded query (dim={len(embedding)}, "
                f"cache_hit_rate={self.get_cache_hit_rate():.1%})"
            )

            return embedding

        except Exception as e:
            logger.error(f"OpenAI API error for query '{query[:50]}...': {e}")
            return None

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        return self._cache_hits / total

    def get_metrics(self) -> dict:
        """Get service metrics for monitoring."""
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": self.get_cache_hit_rate(),
            "cache_size": len(self.cache),
            "cache_maxsize": self.cache.maxsize,
            "api_calls": self._api_calls,
            "model": self.model,
            "available": self.is_available(),
        }


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create singleton EmbeddingService instance.

    Returns:
        EmbeddingService singleton
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service

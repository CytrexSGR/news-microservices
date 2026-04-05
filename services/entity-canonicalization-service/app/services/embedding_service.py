"""
OpenAI Embedding Service

Cloud-native embedding generation with cost optimization via LRU caching.
Replaces local sentence-transformers (100MB model) with OpenAI API (text-embedding-3-small).

Cost Optimization:
- LRU cache (10k capacity) with 80% expected hit rate
- Cost reduction: $50/month → $10/month
- Cache hit latency: ~0ms vs API call: ~50-150ms

Reference: /home/cytrex/userdocs/system-ontology/ENTITY_CANONICALIZATION_OPENAI_MIGRATION.md (Phase 3)
"""

import hashlib
import logging
from typing import List, Optional

from cachetools import LRUCache
from openai import AsyncOpenAI
from openai.types.embedding import Embedding

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    OpenAI embedding service with LRU caching for cost optimization.

    Features:
    - text-embedding-3-small model (1536 dimensions, $0.02/1M tokens)
    - LRU cache (10k entities, 80% hit rate)
    - Batch processing support (up to 2048 texts per call)
    - MD5 hash deduplication

    Usage:
        service = EmbeddingService()

        # Single embedding
        vector = await service.embed_text("Tesla Inc.")

        # Batch embeddings (16x faster)
        vectors = await service.embed_batch(["Tesla", "SpaceX", "Neuralink"])
    """

    def __init__(self):
        """Initialize OpenAI client and LRU cache."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.cache: LRUCache = LRUCache(maxsize=settings.EMBEDDING_CACHE_SIZE)
        self.model = settings.EMBEDDING_MODEL

        # Metrics
        self._cache_hits = 0
        self._cache_misses = 0
        self._api_calls = 0

        logger.info(
            f"EmbeddingService initialized (model={self.model}, "
            f"cache_size={settings.EMBEDDING_CACHE_SIZE})"
        )

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key from text using MD5 hash.

        Args:
            text: Input text

        Returns:
            MD5 hash (hex digest)

        Note:
            Normalizes text (lowercase, strip whitespace) before hashing
            to maximize cache hits for semantically identical strings.
        """
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text with caching.

        Args:
            text: Text to embed (entity name, alias, etc.)

        Returns:
            Embedding vector (1536 dimensions)

        Example:
            vector = await service.embed_text("Tesla Inc.")
            # vector = [0.123, -0.456, ..., 0.789]  # 1536 floats
        """
        # Check cache first
        cache_key = self._get_cache_key(text)

        if cache_key in self.cache:
            self._cache_hits += 1
            logger.debug(f"Cache HIT for '{text}' (key={cache_key[:8]}...)")
            return self.cache[cache_key]

        # Cache miss - call OpenAI API
        self._cache_misses += 1
        logger.debug(f"Cache MISS for '{text}' - calling OpenAI API")

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )

            self._api_calls += 1

            # Extract embedding vector
            embedding: Embedding = response.data[0]
            vector = embedding.embedding

            # Cache result
            self.cache[cache_key] = vector

            logger.debug(
                f"Embedded '{text}' (dim={len(vector)}, "
                f"cache_hit_rate={self.get_cache_hit_rate():.1%})"
            )

            return vector

        except Exception as e:
            logger.error(f"OpenAI API error for '{text}': {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batch optimization.

        Performance:
        - Serial: 50 texts × 50ms = 2500ms
        - Batch:  1 call × 150ms = 150ms (16x speedup!)

        Args:
            texts: List of texts to embed (max 2048 per OpenAI limit)

        Returns:
            List of embedding vectors (same order as input)

        Example:
            vectors = await service.embed_batch(["Tesla", "SpaceX", "Neuralink"])
            # vectors[0] = embedding for "Tesla"
            # vectors[1] = embedding for "SpaceX"
            # vectors[2] = embedding for "Neuralink"
        """
        if not texts:
            return []

        if len(texts) > 2048:
            logger.warning(
                f"Batch size {len(texts)} exceeds OpenAI limit (2048). "
                "Processing in chunks..."
            )
            # Recursively process in chunks
            chunks = [texts[i:i+2048] for i in range(0, len(texts), 2048)]
            results = []
            for chunk in chunks:
                results.extend(await self.embed_batch(chunk))
            return results

        # Check cache for all texts
        cache_keys = [self._get_cache_key(text) for text in texts]
        cached_vectors = {}
        uncached_texts = []
        uncached_indices = []

        for i, (text, key) in enumerate(zip(texts, cache_keys)):
            if key in self.cache:
                cached_vectors[i] = self.cache[key]
                self._cache_hits += 1
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                self._cache_misses += 1

        logger.debug(
            f"Batch: {len(cached_vectors)} cached, "
            f"{len(uncached_texts)} to fetch from API"
        )

        # Fetch uncached embeddings from OpenAI
        if uncached_texts:
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=uncached_texts,
                    encoding_format="float"
                )

                self._api_calls += 1

                # Cache new embeddings
                for i, embedding_data in enumerate(response.data):
                    original_index = uncached_indices[i]
                    text = texts[original_index]
                    cache_key = cache_keys[original_index]

                    vector = embedding_data.embedding
                    self.cache[cache_key] = vector
                    cached_vectors[original_index] = vector

                logger.info(
                    f"Batch embedded {len(uncached_texts)} texts "
                    f"(cache_hit_rate={self.get_cache_hit_rate():.1%})"
                )

            except Exception as e:
                logger.error(f"OpenAI batch API error: {e}")
                raise

        # Return vectors in original order
        return [cached_vectors[i] for i in range(len(texts))]

    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Cache hit rate (0.0 to 1.0)
        """
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        return self._cache_hits / total

    def get_metrics(self) -> dict:
        """
        Get service metrics for monitoring.

        Returns:
            Dictionary with cache stats and API call count
        """
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": self.get_cache_hit_rate(),
            "cache_size": len(self.cache),
            "cache_maxsize": self.cache.maxsize,
            "api_calls": self._api_calls,
            "model": self.model,
        }

    def clear_cache(self) -> None:
        """Clear embedding cache (useful for testing)."""
        self.cache.clear()
        logger.info("Embedding cache cleared")


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

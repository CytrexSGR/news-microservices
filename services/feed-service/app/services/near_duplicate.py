"""
Near-Duplicate Detection Service for feed-service.

Detects semantically similar articles using SimHash.
Used to identify rewrites, syndication, and duplicate content.

SimHash reduces article text to a 64-bit fingerprint.
Hamming distance <= 3 indicates near-duplicate.
"""

import re
from typing import Optional, Tuple, Dict, Any
import structlog

from app.core.redis import get_redis

logger = structlog.get_logger()


class NearDuplicateDetector:
    """
    Detects near-duplicate articles using SimHash.

    SimHash creates a 64-bit fingerprint from text.
    Articles with Hamming distance <= 3 are considered duplicates.
    """

    HAMMING_THRESHOLD = 3
    CACHE_TTL_HOURS = 48
    CACHE_KEY = "simhash:articles"

    def __init__(self):
        """Initialize detector."""
        self._simhash_available = True
        try:
            from simhash import Simhash
            self._Simhash = Simhash
        except ImportError:
            logger.warning("simhash library not installed, using fallback")
            self._simhash_available = False

    def _tokenize(self, text: str) -> list:
        """
        Tokenize and clean text for SimHash.

        Args:
            text: Raw article text

        Returns:
            List of cleaned tokens
        """
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove special chars
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Split into tokens, filter short ones
        tokens = [t for t in text.split() if len(t) > 3]

        return tokens

    def calculate_simhash(self, text: str) -> int:
        """
        Calculate 64-bit SimHash fingerprint.

        Args:
            text: Article text

        Returns:
            64-bit integer hash
        """
        if not self._simhash_available:
            # Fallback: simple hash
            import hashlib
            tokens = self._tokenize(text)
            h = hashlib.sha256(' '.join(tokens).encode())
            return int.from_bytes(h.digest()[:8], 'big')

        tokens = self._tokenize(text)
        if not tokens:
            return 0

        return self._Simhash(tokens).value

    def hamming_distance(self, hash1: int, hash2: int) -> int:
        """
        Calculate Hamming distance between two hashes.

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            Number of differing bits
        """
        return bin(hash1 ^ hash2).count('1')

    async def is_near_duplicate(
        self,
        text: str,
        article_id: str
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if text is a near-duplicate of any cached article.

        Args:
            text: Article text (title + content)
            article_id: Article ID

        Returns:
            Tuple of (is_duplicate, original_article_id, hamming_distance)
        """
        new_hash = self.calculate_simhash(text)

        if new_hash == 0:
            logger.warning("Empty hash generated", article_id=article_id)
            return False, None, None

        try:
            redis_client = await get_redis()

            # Scan cached hashes
            cursor = 0
            while True:
                cursor, items = await redis_client.hscan(
                    self.CACHE_KEY,
                    cursor,
                    count=1000
                )

                for stored_id, stored_hash in items.items():
                    try:
                        stored_hash_int = int(stored_hash)
                        distance = self.hamming_distance(new_hash, stored_hash_int)

                        if distance <= self.HAMMING_THRESHOLD:
                            logger.info(
                                "Near-duplicate detected",
                                article_id=article_id,
                                duplicate_of=stored_id,
                                hamming_distance=distance
                            )
                            return True, stored_id, distance
                    except (ValueError, TypeError):
                        continue

                if cursor == 0:
                    break

            # Not a duplicate - cache this hash
            await redis_client.hset(self.CACHE_KEY, article_id, str(new_hash))

            # Set expiry on individual entries is complex with HSET
            # Instead, we use periodic cleanup

            logger.debug(
                "Article cached for dedup",
                article_id=article_id,
                simhash=new_hash
            )

            return False, None, None

        except Exception as e:
            logger.error("Near-duplicate check failed", error=str(e), article_id=article_id)
            return False, None, None

    async def check_similarity(
        self,
        text1: str,
        text2: str
    ) -> Dict[str, Any]:
        """
        Compare two texts for similarity.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Dict with hash values and distance
        """
        hash1 = self.calculate_simhash(text1)
        hash2 = self.calculate_simhash(text2)
        distance = self.hamming_distance(hash1, hash2)

        return {
            "hash1": hash1,
            "hash2": hash2,
            "hamming_distance": distance,
            "is_similar": distance <= self.HAMMING_THRESHOLD,
            "similarity_score": 1.0 - (distance / 64)  # Normalize to 0-1
        }

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get SimHash cache statistics.

        Returns:
            Dict with cache size info
        """
        try:
            redis_client = await get_redis()
            count = await redis_client.hlen(self.CACHE_KEY)

            return {
                "cached_articles": count,
                "hamming_threshold": self.HAMMING_THRESHOLD,
                "ttl_hours": self.CACHE_TTL_HOURS
            }
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"error": str(e)}

    async def cleanup_old_hashes(self, max_entries: int = 100000):
        """
        Remove old hashes if cache exceeds max size.

        Args:
            max_entries: Maximum entries to keep
        """
        try:
            redis_client = await get_redis()
            count = await redis_client.hlen(self.CACHE_KEY)

            if count > max_entries:
                # Get all keys and remove oldest (by assuming insertion order)
                # This is a simple LRU approximation
                to_remove = count - max_entries

                cursor = 0
                removed = 0
                while removed < to_remove:
                    cursor, items = await redis_client.hscan(
                        self.CACHE_KEY,
                        cursor,
                        count=1000
                    )

                    for key in list(items.keys())[:to_remove - removed]:
                        await redis_client.hdel(self.CACHE_KEY, key)
                        removed += 1

                    if cursor == 0:
                        break

                logger.info("Cleaned up old simhash entries", removed=removed)

        except Exception as e:
            logger.error("Cleanup failed", error=str(e))


# Singleton instance
near_duplicate_detector = NearDuplicateDetector()

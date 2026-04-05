"""
Novelty Scoring Service for analytics-service.

Determines if information is "new" vs. already reported.
Uses entity + event type fingerprinting to find similar
previously reported stories.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib
import structlog

from app.core.redis import get_redis

logger = structlog.get_logger()


@dataclass
class NoveltyResult:
    """Represents novelty calculation result."""
    article_id: str
    novelty_score: float      # 0.0 (duplicate) to 1.0 (completely new)
    is_novel: bool            # novelty_score > threshold
    similar_article_id: Optional[str]
    hours_since_similar: Optional[float]
    reason: str
    fingerprint: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "article_id": self.article_id,
            "novelty_score": round(self.novelty_score, 4),
            "is_novel": self.is_novel,
            "similar_article_id": self.similar_article_id,
            "hours_since_similar": round(self.hours_since_similar, 2) if self.hours_since_similar else None,
            "reason": self.reason,
            "fingerprint": self.fingerprint,
        }


class NoveltyScorer:
    """
    Calculates how "new" an article's information is.

    Uses entity + event type fingerprinting to find similar
    previously reported stories in Redis cache.
    """

    NOVELTY_THRESHOLD = 0.5
    CACHE_TTL_HOURS = 48
    CACHE_PREFIX = "novelty:fingerprint:"

    def _create_fingerprint(
        self,
        entities: List[str],
        event_type: str,
        primary_topic: str
    ) -> str:
        """
        Create a fingerprint for an article based on key elements.

        Args:
            entities: List of entity names
            event_type: Event type (BREAKING, EARNINGS, etc.)
            primary_topic: Primary topic/category

        Returns:
            16-character hash fingerprint
        """
        # Normalize and sort entities (top 5)
        normalized = sorted([e.lower().strip() for e in entities[:5] if e])

        # Create hash
        content = f"{event_type.upper()}|{primary_topic.lower()}|{','.join(normalized)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def calculate_novelty(
        self,
        article_id: str,
        entities: List[str],
        event_type: str,
        primary_topic: str,
        published_at: datetime
    ) -> NoveltyResult:
        """
        Calculate novelty score for an article.

        Args:
            article_id: Article ID
            entities: Entity names mentioned
            event_type: Article event type
            primary_topic: Primary topic
            published_at: Publication timestamp

        Returns:
            NoveltyResult with score and similar article info
        """
        fingerprint = self._create_fingerprint(entities, event_type, primary_topic)
        cache_key = f"{self.CACHE_PREFIX}{fingerprint}"

        try:
            redis = await get_redis()
            cached = await redis.hgetall(cache_key)

            if cached:
                # Found similar article in cache
                cached_time = datetime.fromisoformat(cached['timestamp'])
                cached_article_id = cached['article_id']

                # Handle timezone
                if published_at.tzinfo is not None:
                    published_at = published_at.replace(tzinfo=None)

                hours_since = (published_at - cached_time).total_seconds() / 3600

                # Calculate novelty based on time since similar article
                # More time passed = higher novelty
                # Full novelty after 24h
                novelty_score = min(1.0, max(0.0, hours_since / 24))

                result = NoveltyResult(
                    article_id=article_id,
                    novelty_score=novelty_score,
                    is_novel=novelty_score > self.NOVELTY_THRESHOLD,
                    similar_article_id=cached_article_id,
                    hours_since_similar=hours_since,
                    reason=f"Similar to article from {hours_since:.1f}h ago",
                    fingerprint=fingerprint
                )

                logger.debug(
                    "Found similar article",
                    article_id=article_id,
                    similar_id=cached_article_id,
                    hours_since=round(hours_since, 2),
                    novelty_score=round(novelty_score, 2)
                )

                return result

            # No similar article found - completely novel
            # Store this fingerprint in cache
            await redis.hset(cache_key, mapping={
                'article_id': article_id,
                'timestamp': published_at.isoformat()
            })
            await redis.expire(cache_key, int(self.CACHE_TTL_HOURS * 3600))

            result = NoveltyResult(
                article_id=article_id,
                novelty_score=1.0,
                is_novel=True,
                similar_article_id=None,
                hours_since_similar=None,
                reason="No similar articles found in last 48h",
                fingerprint=fingerprint
            )

            logger.info(
                "Novel article detected",
                article_id=article_id,
                fingerprint=fingerprint,
                entities=entities[:3]
            )

            return result

        except Exception as e:
            logger.error(
                "Error calculating novelty",
                article_id=article_id,
                error=str(e)
            )
            # On error, assume novel to avoid blocking
            return NoveltyResult(
                article_id=article_id,
                novelty_score=1.0,
                is_novel=True,
                similar_article_id=None,
                hours_since_similar=None,
                reason=f"Error during novelty check: {str(e)}",
                fingerprint=fingerprint
            )

    async def batch_calculate(
        self,
        articles: List[Dict[str, Any]]
    ) -> List[NoveltyResult]:
        """
        Calculate novelty for multiple articles.

        Args:
            articles: List of article dicts with id, entities, event_type, topic, published_at

        Returns:
            List of NoveltyResults
        """
        results = []

        for article in articles:
            try:
                result = await self.calculate_novelty(
                    article_id=str(article.get('id', '')),
                    entities=article.get('entities', []),
                    event_type=article.get('event_type', 'DEFAULT'),
                    primary_topic=article.get('primary_topic', ''),
                    published_at=article.get('published_at', datetime.utcnow())
                )
                results.append(result)
            except Exception as e:
                logger.error("Error in batch novelty calculation", error=str(e))

        return results

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get novelty cache statistics.

        Returns:
            Dict with cache size and memory usage
        """
        try:
            redis = await get_redis()

            # Count fingerprint keys
            cursor = 0
            count = 0
            while True:
                cursor, keys = await redis.scan(
                    cursor,
                    match=f"{self.CACHE_PREFIX}*",
                    count=1000
                )
                count += len(keys)
                if cursor == 0:
                    break

            return {
                "fingerprint_count": count,
                "ttl_hours": self.CACHE_TTL_HOURS,
                "cache_prefix": self.CACHE_PREFIX
            }

        except Exception as e:
            logger.error("Error getting cache stats", error=str(e))
            return {"error": str(e)}


# Singleton instance
novelty_scorer = NoveltyScorer()

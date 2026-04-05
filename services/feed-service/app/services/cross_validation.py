"""
Cross-Validation Service for feed-service.

Tracks multi-source confirmation for breaking news.
An event is "validated" when reported by 2+ independent publishers
within a short time window.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import structlog

from app.core.redis import get_redis

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    """Represents cross-validation check result."""
    event_fingerprint: str
    is_validated: bool
    source_count: int
    sources: List[str]
    publishers: List[str]
    confidence: float
    first_seen: datetime
    time_window_minutes: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "event_fingerprint": self.event_fingerprint,
            "is_validated": self.is_validated,
            "source_count": self.source_count,
            "sources": self.sources,
            "publishers": self.publishers,
            "confidence": round(self.confidence, 2),
            "first_seen": self.first_seen.isoformat(),
            "time_window_minutes": self.time_window_minutes
        }


class CrossValidationService:
    """
    Tracks multi-source confirmation for breaking news.

    An event is "validated" when reported by 2+ independent publishers
    within a configurable time window.
    """

    MIN_SOURCES = 2
    TIME_WINDOW_MINUTES = 30
    CACHE_PREFIX = "crossval:"

    def __init__(self, time_window_minutes: int = 30, min_sources: int = 2):
        """
        Initialize cross-validation service.

        Args:
            time_window_minutes: Time window for validation
            min_sources: Minimum sources needed for validation
        """
        self.time_window_minutes = time_window_minutes
        self.min_sources = min_sources

    async def report_event(
        self,
        event_fingerprint: str,
        source_url: str,
        publisher: str,
        timestamp: Optional[datetime] = None
    ) -> ValidationResult:
        """
        Report an event occurrence and check for cross-validation.

        Args:
            event_fingerprint: Unique event identifier (hash of key facts)
            source_url: URL of the article
            publisher: Publisher name/domain
            timestamp: Event timestamp (defaults to now)

        Returns:
            ValidationResult indicating if event is cross-validated
        """
        timestamp = timestamp or datetime.utcnow()
        cache_key = f"{self.CACHE_PREFIX}{event_fingerprint}"

        try:
            redis_client = await get_redis()

            # Get existing reports for this event
            existing = await redis_client.hgetall(cache_key)

            # Add this source (use publisher as key to prevent same publisher counting twice)
            data_value = f"{source_url}|{timestamp.isoformat()}"
            await redis_client.hset(cache_key, publisher, data_value)
            await redis_client.expire(cache_key, self.time_window_minutes * 60)

            # Parse existing sources
            sources = [source_url]
            publishers = [publisher]
            first_seen = timestamp

            for pub, data in existing.items():
                try:
                    src, ts = data.split('|', 1)
                    sources.append(src)
                    publishers.append(pub)

                    # Track first seen time
                    event_time = datetime.fromisoformat(ts)
                    if event_time < first_seen:
                        first_seen = event_time
                except (ValueError, TypeError):
                    continue

            # Deduplicate
            unique_publishers = list(set(publishers))
            unique_sources = list(set(sources))

            # Check if validated
            is_validated = len(unique_publishers) >= self.min_sources

            # Calculate confidence (3+ sources = 100%)
            confidence = min(1.0, len(unique_publishers) / 3)

            result = ValidationResult(
                event_fingerprint=event_fingerprint,
                is_validated=is_validated,
                source_count=len(unique_publishers),
                sources=unique_sources,
                publishers=unique_publishers,
                confidence=confidence,
                first_seen=first_seen,
                time_window_minutes=self.time_window_minutes
            )

            if is_validated:
                logger.info(
                    "Event cross-validated",
                    fingerprint=event_fingerprint,
                    publishers=unique_publishers,
                    source_count=len(unique_publishers)
                )

            return result

        except Exception as e:
            logger.error("Cross-validation check failed", error=str(e))
            return ValidationResult(
                event_fingerprint=event_fingerprint,
                is_validated=False,
                source_count=1,
                sources=[source_url],
                publishers=[publisher],
                confidence=0.33,
                first_seen=timestamp,
                time_window_minutes=self.time_window_minutes
            )

    async def check_event(
        self,
        event_fingerprint: str
    ) -> Optional[ValidationResult]:
        """
        Check validation status of an event without adding a new source.

        Args:
            event_fingerprint: Event identifier

        Returns:
            ValidationResult if event exists, None otherwise
        """
        cache_key = f"{self.CACHE_PREFIX}{event_fingerprint}"

        try:
            redis_client = await get_redis()
            existing = await redis_client.hgetall(cache_key)

            if not existing:
                return None

            sources = []
            publishers = []
            first_seen = datetime.utcnow()

            for pub, data in existing.items():
                try:
                    src, ts = data.split('|', 1)
                    sources.append(src)
                    publishers.append(pub)

                    event_time = datetime.fromisoformat(ts)
                    if event_time < first_seen:
                        first_seen = event_time
                except (ValueError, TypeError):
                    continue

            unique_publishers = list(set(publishers))
            is_validated = len(unique_publishers) >= self.min_sources

            return ValidationResult(
                event_fingerprint=event_fingerprint,
                is_validated=is_validated,
                source_count=len(unique_publishers),
                sources=list(set(sources)),
                publishers=unique_publishers,
                confidence=min(1.0, len(unique_publishers) / 3),
                first_seen=first_seen,
                time_window_minutes=self.time_window_minutes
            )

        except Exception as e:
            logger.error("Event check failed", error=str(e))
            return None

    async def get_validated_events(
        self,
        limit: int = 50
    ) -> List[ValidationResult]:
        """
        Get all currently validated events.

        Args:
            limit: Maximum events to return

        Returns:
            List of validated events
        """
        try:
            redis_client = await get_redis()

            # Scan for all crossval keys
            validated = []
            cursor = 0

            while len(validated) < limit:
                cursor, keys = await redis_client.scan(
                    cursor,
                    match=f"{self.CACHE_PREFIX}*",
                    count=100
                )

                for key in keys:
                    fingerprint = key.replace(self.CACHE_PREFIX, "")
                    result = await self.check_event(fingerprint)

                    if result and result.is_validated:
                        validated.append(result)

                        if len(validated) >= limit:
                            break

                if cursor == 0:
                    break

            return sorted(validated, key=lambda x: x.source_count, reverse=True)

        except Exception as e:
            logger.error("Failed to get validated events", error=str(e))
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cross-validation statistics.

        Returns:
            Dict with stats
        """
        try:
            redis_client = await get_redis()

            # Count all tracked events
            cursor = 0
            total_events = 0
            validated_count = 0

            while True:
                cursor, keys = await redis_client.scan(
                    cursor,
                    match=f"{self.CACHE_PREFIX}*",
                    count=100
                )

                for key in keys:
                    total_events += 1
                    fingerprint = key.replace(self.CACHE_PREFIX, "")
                    result = await self.check_event(fingerprint)
                    if result and result.is_validated:
                        validated_count += 1

                if cursor == 0:
                    break

            return {
                "total_tracked_events": total_events,
                "validated_events": validated_count,
                "validation_rate": validated_count / total_events if total_events > 0 else 0,
                "time_window_minutes": self.time_window_minutes,
                "min_sources": self.min_sources
            }

        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {"error": str(e)}


# Singleton instance
cross_validation_service = CrossValidationService()

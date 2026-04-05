"""
Sentiment Momentum Service for analytics-service.

Calculates sentiment momentum (first derivative) to detect
turnaround signals in entity sentiment.

A stock may have negative sentiment, but if it's becoming
LESS negative, that signals a potential turnaround.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np
import structlog

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


@dataclass
class MomentumResult:
    """Represents sentiment momentum calculation result."""
    entity: str
    current_sentiment: float      # Latest sentiment (-1 to 1)
    momentum: float               # Rate of change
    signal: str                   # "improving" | "deteriorating" | "stable" | "insufficient_data"
    trend_direction: str          # "positive" | "negative" | "neutral"
    confidence: float             # Based on data points consistency
    daily_sentiments: List[float] # Historical data
    data_points: int              # Number of days with data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "entity": self.entity,
            "current_sentiment": round(self.current_sentiment, 4),
            "momentum": round(self.momentum, 4),
            "signal": self.signal,
            "trend_direction": self.trend_direction,
            "confidence": round(self.confidence, 4),
            "daily_sentiments": [round(s, 4) for s in self.daily_sentiments],
            "data_points": self.data_points,
        }


class SentimentMomentumService:
    """
    Calculates sentiment momentum (first derivative).

    Detects when sentiment is changing direction, which
    often precedes price reversals.
    """

    THRESHOLD = 0.1  # Minimum change to be considered significant

    async def calculate_momentum(
        self,
        entity: str,
        days: int = 7,
        db: AsyncSession = None
    ) -> MomentumResult:
        """
        Calculate sentiment momentum for an entity.

        Args:
            entity: Entity name
            days: Number of days to analyze
            db: Database session

        Returns:
            MomentumResult with momentum value and signal interpretation
        """
        if db is None:
            return self._insufficient_data_result(entity)

        # Get daily average sentiments
        daily_sentiments = await self._get_daily_sentiments(entity, days, db)

        if len(daily_sentiments) < 3:
            return MomentumResult(
                entity=entity,
                current_sentiment=daily_sentiments[-1] if daily_sentiments else 0,
                momentum=0.0,
                signal="insufficient_data",
                trend_direction="neutral",
                confidence=0.0,
                daily_sentiments=daily_sentiments,
                data_points=len(daily_sentiments)
            )

        # Calculate first derivative (changes between days)
        changes = np.diff(daily_sentiments)
        momentum = float(np.mean(changes))

        # Determine signal
        if momentum > self.THRESHOLD:
            signal = "improving"
        elif momentum < -self.THRESHOLD:
            signal = "deteriorating"
        else:
            signal = "stable"

        # Trend direction (is latest change positive or negative?)
        latest_change = changes[-1] if len(changes) > 0 else 0
        if latest_change > 0.02:
            trend_direction = "positive"
        elif latest_change < -0.02:
            trend_direction = "negative"
        else:
            trend_direction = "neutral"

        # Confidence based on consistency
        confidence = self._calculate_confidence(changes)

        result = MomentumResult(
            entity=entity,
            current_sentiment=daily_sentiments[-1],
            momentum=momentum,
            signal=signal,
            trend_direction=trend_direction,
            confidence=confidence,
            daily_sentiments=daily_sentiments,
            data_points=len(daily_sentiments)
        )

        logger.info(
            "Calculated sentiment momentum",
            entity=entity,
            momentum=round(momentum, 4),
            signal=signal,
            confidence=round(confidence, 2)
        )

        return result

    def _calculate_confidence(self, changes: np.ndarray) -> float:
        """
        Higher confidence if changes are consistent (same direction).
        """
        if len(changes) == 0:
            return 0.0

        # Count how many changes are in the same direction as the mean
        mean_direction = np.sign(np.mean(changes))
        if mean_direction == 0:
            return 0.5

        consistent = np.sum(np.sign(changes) == mean_direction)
        return float(consistent / len(changes))

    async def get_momentum_leaders(
        self,
        direction: str = "improving",  # "improving" | "deteriorating"
        days: int = 7,
        limit: int = 10,
        db: AsyncSession = None
    ) -> List[MomentumResult]:
        """
        Get entities with strongest momentum in given direction.

        Use for "Sentiment Turnaround" alerts.

        Args:
            direction: "improving" or "deteriorating"
            days: Analysis window
            limit: Max results
            db: Database session

        Returns:
            Entities sorted by absolute momentum
        """
        if db is None:
            return []

        # Get all entities with recent coverage
        entities = await self._get_covered_entities(days, db)

        logger.info(
            "Scanning for momentum leaders",
            direction=direction,
            entity_count=len(entities),
            days=days
        )

        results = []
        for entity in entities:
            try:
                momentum = await self.calculate_momentum(entity, days, db)
                if momentum.signal == direction and momentum.confidence > 0.4:
                    results.append(momentum)
            except Exception as e:
                logger.error("Error calculating momentum", entity=entity, error=str(e))

        # Sort by absolute momentum
        results.sort(key=lambda m: abs(m.momentum), reverse=True)

        return results[:limit]

    async def _get_daily_sentiments(
        self,
        entity: str,
        days: int,
        db: AsyncSession
    ) -> List[float]:
        """
        Get daily average sentiment scores for an entity.
        """
        # Note: days is interpolated directly (it's a validated integer)
        query = text(f"""
            SELECT
                DATE(created_at) as day,
                AVG(
                    COALESCE((tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bullish_ratio')::float, 0.5)
                    - COALESCE((tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bearish_ratio')::float, 0.5)
                ) as avg_sentiment
            FROM article_analysis
            WHERE tier1_results->'entities' @> :entity_json
              AND created_at > NOW() - INTERVAL '{days} days'
              AND tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bullish_ratio' IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """)

        entity_json = f'[{{"name": "{entity}"}}]'

        result = await db.execute(query, {
            "entity_json": entity_json
        })

        return [float(row.avg_sentiment) for row in result.fetchall()]

    async def _get_covered_entities(
        self,
        days: int,
        db: AsyncSession,
        min_data_points: int = 3
    ) -> List[str]:
        """
        Get all entities with sentiment data in the time period.
        """
        # Note: days is interpolated directly (it's a validated integer)
        query = text(f"""
            WITH entity_sentiments AS (
                SELECT
                    jsonb_array_elements(tier1_results->'entities')->>'name' as entity,
                    DATE(created_at) as day
                FROM article_analysis
                WHERE created_at > NOW() - INTERVAL '{days} days'
                  AND tier2_results->'SENTIMENT_ANALYZER' IS NOT NULL
            )
            SELECT entity, COUNT(DISTINCT day) as days_covered
            FROM entity_sentiments
            WHERE entity IS NOT NULL
            GROUP BY entity
            HAVING COUNT(DISTINCT day) >= :min_data_points
            ORDER BY days_covered DESC
            LIMIT 200
        """)

        result = await db.execute(query, {
            "min_data_points": min_data_points
        })

        return [row.entity for row in result.fetchall()]

    def _insufficient_data_result(self, entity: str) -> MomentumResult:
        """Return result for insufficient data case."""
        return MomentumResult(
            entity=entity,
            current_sentiment=0,
            momentum=0.0,
            signal="insufficient_data",
            trend_direction="neutral",
            confidence=0.0,
            daily_sentiments=[],
            data_points=0
        )


# Singleton instance
sentiment_momentum_service = SentimentMomentumService()

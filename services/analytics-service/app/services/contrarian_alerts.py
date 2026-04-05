"""
Contrarian Alerts Service for analytics-service.

Detects extreme sentiment conditions (>3 standard deviations).
When sentiment is at historical extremes, it often signals
a reversal opportunity.

EUPHORIA: Sentiment >3 std above mean
PANIC: Sentiment >3 std below mean
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np
import structlog

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


@dataclass
class ContrarianAlert:
    """Represents an extreme sentiment detection."""
    entity: str
    alert_type: str          # "EUPHORIA" | "PANIC"
    current_sentiment: float
    historical_mean: float
    historical_std: float
    z_score: float
    message: str
    detected_at: datetime
    days_analyzed: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "entity": self.entity,
            "alert_type": self.alert_type,
            "current_sentiment": round(self.current_sentiment, 4),
            "historical_mean": round(self.historical_mean, 4),
            "historical_std": round(self.historical_std, 4),
            "z_score": round(self.z_score, 2),
            "message": self.message,
            "detected_at": self.detected_at.isoformat(),
            "days_analyzed": self.days_analyzed,
        }


class ContrarianAlertService:
    """
    Detects extreme sentiment conditions.

    When sentiment exceeds 3 standard deviations from the mean,
    it often signals a reversal opportunity.
    """

    Z_THRESHOLD = 3.0
    MIN_HISTORY_DAYS = 30

    async def check_entity(
        self,
        entity: str,
        history_days: int = 90,
        db: AsyncSession = None
    ) -> Optional[ContrarianAlert]:
        """
        Check if entity has extreme sentiment.

        Args:
            entity: Entity name
            history_days: Historical data to analyze
            db: Database session

        Returns:
            ContrarianAlert if extreme sentiment detected, None otherwise
        """
        if db is None:
            logger.warning("No database session provided")
            return None

        # Get historical sentiment data
        sentiments = await self._get_historical_sentiments(entity, history_days, db)

        if len(sentiments) < self.MIN_HISTORY_DAYS:
            logger.debug(
                "Insufficient history for contrarian analysis",
                entity=entity,
                days=len(sentiments),
                required=self.MIN_HISTORY_DAYS
            )
            return None

        current = sentiments[-1]
        mean = float(np.mean(sentiments))
        std = float(np.std(sentiments))

        if std == 0:
            return None

        z_score = (current - mean) / std

        if z_score > self.Z_THRESHOLD:
            alert = ContrarianAlert(
                entity=entity,
                alert_type="EUPHORIA",
                current_sentiment=current,
                historical_mean=mean,
                historical_std=std,
                z_score=z_score,
                message=f"Extreme positive sentiment for {entity} - highest in {history_days} days. Z-score: {z_score:.1f}",
                detected_at=datetime.utcnow(),
                days_analyzed=len(sentiments)
            )
            logger.warning("EUPHORIA alert detected", **alert.to_dict())
            return alert

        elif z_score < -self.Z_THRESHOLD:
            alert = ContrarianAlert(
                entity=entity,
                alert_type="PANIC",
                current_sentiment=current,
                historical_mean=mean,
                historical_std=std,
                z_score=z_score,
                message=f"Extreme negative sentiment for {entity} - lowest in {history_days} days. Z-score: {z_score:.1f}",
                detected_at=datetime.utcnow(),
                days_analyzed=len(sentiments)
            )
            logger.warning("PANIC alert detected", **alert.to_dict())
            return alert

        return None

    async def scan_all_entities(
        self,
        history_days: int = 90,
        limit: int = 50,
        db: AsyncSession = None
    ) -> List[ContrarianAlert]:
        """
        Scan all entities for contrarian signals.

        Args:
            history_days: Historical window
            limit: Max alerts to return
            db: Database session

        Returns:
            All alerts sorted by absolute z-score
        """
        if db is None:
            return []

        entities = await self._get_tracked_entities(db, history_days)

        logger.info(
            "Scanning for contrarian alerts",
            entity_count=len(entities),
            history_days=history_days
        )

        alerts = []
        for entity in entities:
            try:
                alert = await self.check_entity(entity, history_days, db)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                logger.error("Error checking entity", entity=entity, error=str(e))

        # Sort by absolute z-score
        sorted_alerts = sorted(alerts, key=lambda a: abs(a.z_score), reverse=True)

        logger.info(
            "Contrarian scan completed",
            euphoria_count=len([a for a in alerts if a.alert_type == "EUPHORIA"]),
            panic_count=len([a for a in alerts if a.alert_type == "PANIC"])
        )

        return sorted_alerts[:limit]

    async def _get_historical_sentiments(
        self,
        entity: str,
        history_days: int,
        db: AsyncSession
    ) -> List[float]:
        """
        Get historical daily sentiment values for an entity.
        """
        # Note: history_days is interpolated directly (it's a validated integer)
        query = text(f"""
            SELECT
                DATE(created_at) as day,
                AVG(
                    COALESCE((tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bullish_ratio')::float, 0.5)
                    - COALESCE((tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bearish_ratio')::float, 0.5)
                ) as sentiment
            FROM article_analysis
            WHERE tier1_results->'entities' @> :entity_json
              AND created_at > NOW() - INTERVAL '{history_days} days'
              AND tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bullish_ratio' IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """)

        entity_json = f'[{{"name": "{entity}"}}]'

        result = await db.execute(query, {
            "entity_json": entity_json
        })

        return [float(row.sentiment) for row in result.fetchall()]

    async def _get_tracked_entities(
        self,
        db: AsyncSession,
        history_days: int = 90
    ) -> List[str]:
        """
        Get entities with sufficient historical data (>30 days coverage).
        """
        # Note: history_days is interpolated directly (it's a validated integer)
        query = text(f"""
            WITH entity_coverage AS (
                SELECT
                    jsonb_array_elements(tier1_results->'entities')->>'name' as entity,
                    DATE(created_at) as day
                FROM article_analysis
                WHERE created_at > NOW() - INTERVAL '{history_days} days'
                  AND tier2_results->'SENTIMENT_ANALYZER' IS NOT NULL
            )
            SELECT entity, COUNT(DISTINCT day) as days_covered
            FROM entity_coverage
            WHERE entity IS NOT NULL
            GROUP BY entity
            HAVING COUNT(DISTINCT day) >= :min_days
            ORDER BY days_covered DESC
            LIMIT 100
        """)

        result = await db.execute(query, {
            "min_days": self.MIN_HISTORY_DAYS
        })

        return [row.entity for row in result.fetchall()]


# Singleton instance
contrarian_alert_service = ContrarianAlertService()

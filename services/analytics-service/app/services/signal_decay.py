"""
Signal Decay Service for analytics-service.

Calculates time-based relevance decay for articles.
Breaking news decays faster than feature articles.

Half-lives by event type:
- BREAKING: 4 hours (fast decay)
- EARNINGS: 12 hours
- ANALYSIS: 24 hours
- FEATURE: 48 hours (slow decay)
"""

import math
from datetime import datetime
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()


class SignalDecayService:
    """
    Calculates time-based relevance decay for articles.

    Formula: e^(-lambda * t) where lambda = ln(2) / half_life
    """

    HALF_LIVES = {
        "BREAKING": 4,
        "EARNINGS": 12,
        "ANALYSIS": 24,
        "FEATURE": 48,
        "DEFAULT": 24,
    }

    def calculate_decay(
        self,
        published_at: datetime,
        event_type: str = "DEFAULT",
        now: Optional[datetime] = None
    ) -> float:
        """
        Returns decay weight between 0.0 and 1.0.

        Args:
            published_at: Article publication timestamp
            event_type: Article event type (BREAKING, EARNINGS, etc.)
            now: Current time (defaults to utcnow)

        Returns:
            Decay weight (1.0 = fresh, 0.0 = very old)
        """
        now = now or datetime.utcnow()

        # Handle timezone-naive datetime
        if published_at.tzinfo is not None:
            published_at = published_at.replace(tzinfo=None)

        age_hours = (now - published_at).total_seconds() / 3600

        # Negative age shouldn't happen, but handle gracefully
        if age_hours < 0:
            return 1.0

        half_life = self.HALF_LIVES.get(event_type.upper(), self.HALF_LIVES["DEFAULT"])
        lambda_decay = math.log(2) / half_life

        decay = math.exp(-lambda_decay * age_hours)

        logger.debug(
            "Calculated decay",
            age_hours=round(age_hours, 2),
            event_type=event_type,
            half_life=half_life,
            decay=round(decay, 4)
        )

        return decay

    def weighted_score(
        self,
        base_score: float,
        published_at: datetime,
        event_type: str = "DEFAULT"
    ) -> float:
        """
        Applies decay to a base relevance score.

        Args:
            base_score: Original score (0-10)
            published_at: Article publication timestamp
            event_type: Article event type

        Returns:
            Decayed score
        """
        decay = self.calculate_decay(published_at, event_type)
        return base_score * decay

    def rank_articles(
        self,
        articles: List[Dict[str, Any]],
        score_field: str = "priority_score",
        published_field: str = "published_at",
        event_type_field: str = "event_type"
    ) -> List[Dict[str, Any]]:
        """
        Rank articles by decay-weighted score.

        Args:
            articles: List of article dicts
            score_field: Field containing base score
            published_field: Field containing publication datetime
            event_type_field: Field containing event type

        Returns:
            Articles sorted by weighted_score DESC
        """
        ranked = []

        for article in articles:
            base_score = float(article.get(score_field, 0))
            published_at = article.get(published_field)
            event_type = article.get(event_type_field, "DEFAULT")

            if published_at is None:
                weighted = base_score
            elif isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    weighted = self.weighted_score(base_score, published_at, event_type)
                except ValueError:
                    weighted = base_score
            else:
                weighted = self.weighted_score(base_score, published_at, event_type)

            article_copy = article.copy()
            article_copy["weighted_score"] = round(weighted, 4)
            article_copy["decay_applied"] = True
            ranked.append(article_copy)

        return sorted(ranked, key=lambda x: x["weighted_score"], reverse=True)


# Singleton instance
signal_decay_service = SignalDecayService()

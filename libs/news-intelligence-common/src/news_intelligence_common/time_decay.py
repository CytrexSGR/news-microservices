# libs/news-intelligence-common/src/news_intelligence_common/time_decay.py
"""Time-decay scoring for article relevance."""

from datetime import datetime, timezone
from math import exp
from typing import Any, Dict, List, Optional


class TimeDecayScorer:
    """
    Exponential time-decay for relevance scoring.

    Formula: score = base_score * exp(-decay_rate * hours_old)

    Decay rates (half-life):
    - 0.01: ~70 hours (slow decay, evergreen content)
    - 0.05: ~14 hours (recommended for news)
    - 0.10: ~7 hours (fast decay, breaking news)
    - 0.15: ~5 hours (very fast, flash updates)

    Example:
        >>> scorer = TimeDecayScorer()
        >>> from datetime import datetime, timezone, timedelta
        >>> now = datetime.now(timezone.utc)
        >>> old = now - timedelta(hours=24)
        >>> scorer.calculate_score(1.0, old, now)
        0.30...  # Approximately
    """

    DECAY_RATES: Dict[str, float] = {
        "breaking_news": 0.15,  # 5h half-life
        "geopolitics": 0.03,  # 24h half-life
        "analysis": 0.01,  # 70h half-life
        "default": 0.05,  # 14h half-life
    }

    MAX_AGE_HOURS: int = 720  # 30 days

    def __init__(self, decay_rate: float = 0.05) -> None:
        """
        Initialize scorer with decay rate.

        Args:
            decay_rate: Decay rate (higher = faster decay)
        """
        self.decay_rate = decay_rate

    def calculate_score(
        self,
        base_score: float,
        published_at: datetime,
        now: Optional[datetime] = None,
    ) -> float:
        """
        Calculate time-weighted relevance score.

        Args:
            base_score: Initial relevance score (clamped to 0-1 range)
            published_at: Article publication timestamp
            now: Current time (defaults to UTC now)

        Returns:
            Time-decayed score in range [0, 1]
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Ensure timezone-aware comparison
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        # Clamp base_score to valid range
        base_score = max(0.0, min(1.0, base_score))

        hours_old = (now - published_at).total_seconds() / 3600

        # Handle future dates (clock skew, timezone issues)
        if hours_old < 0:
            hours_old = 0

        # Prevent float underflow for very old articles
        if hours_old > self.MAX_AGE_HOURS:
            return 0.0

        time_factor = exp(-self.decay_rate * hours_old)

        return base_score * time_factor

    def rank_articles(
        self,
        articles: List[Dict[str, Any]],
        score_field: str = "similarity",
        time_field: str = "published_at",
    ) -> List[Dict[str, Any]]:
        """
        Rank articles by time-weighted score.

        Args:
            articles: List of article dictionaries
            score_field: Field name for base score
            time_field: Field name for publication time

        Returns:
            Articles sorted by relevance_score descending
        """
        if not articles:
            return []

        now = datetime.now(timezone.utc)

        for article in articles:
            base = article.get(score_field, 1.0)
            pub_time = article.get(time_field)

            if pub_time:
                article["relevance_score"] = self.calculate_score(base, pub_time, now)
            else:
                article["relevance_score"] = base * 0.5  # Penalty for missing time

        return sorted(articles, key=lambda x: x["relevance_score"], reverse=True)

    @classmethod
    def get_decay_rate(cls, category: str) -> float:
        """
        Get decay rate for article category.

        Args:
            category: Article category name

        Returns:
            Decay rate for category (or default)
        """
        return cls.DECAY_RATES.get(category, cls.DECAY_RATES["default"])

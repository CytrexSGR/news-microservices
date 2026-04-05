"""
Relevance Score Calculator

Calculates time-decay relevance scores for articles using the
TimeDecayScorer from news-intelligence-common.

Category-specific decay rates (half-life in hours):
- breaking_news: ~12 hours (fast decay)
- market_update: ~18 hours
- earnings: ~24 hours
- analysis: ~7 days (slow decay for in-depth content)
- research: ~10 days (slowest, evergreen content)
- default: ~2 days (medium decay)

The decay rate formula: half_life_hours = ln(2) / decay_rate
So decay_rate = ln(2) / half_life_hours = 0.693 / half_life_hours
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from news_intelligence_common.time_decay import TimeDecayScorer

logger = logging.getLogger(__name__)


# Category-specific decay rates (per hour)
# Higher rate = faster decay
# decay_rate = ln(2) / half_life_hours
CATEGORY_DECAY_RATES: Dict[str, float] = {
    "breaking_news": 0.058,  # ~12 hour half-life (0.693 / 12)
    "market_update": 0.039,  # ~18 hour half-life (0.693 / 18)
    "earnings": 0.029,       # ~24 hour half-life (0.693 / 24)
    "analysis": 0.004,       # ~7 day half-life (0.693 / 168)
    "research": 0.003,       # ~10 day half-life (0.693 / 240)
    "default": 0.014,        # ~2 day half-life (0.693 / 48)
}


class RelevanceCalculator:
    """
    Calculate relevance scores for articles using time-decay.

    The score combines:
    - Time decay: Exponential decay based on article age
    - Article quality: Optional quality multiplier
    - Category weighting: Different decay rates per category

    Example:
        >>> calculator = RelevanceCalculator()
        >>> from datetime import datetime, timezone, timedelta
        >>> published = datetime.now(timezone.utc) - timedelta(hours=6)
        >>> score = calculator.calculate_score(published, category="breaking_news")
        >>> print(f"Score: {score:.4f}")  # Score: ~0.7 for 6 hours old breaking news
    """

    def __init__(self, decay_rates: Optional[Dict[str, float]] = None) -> None:
        """
        Initialize calculator.

        Args:
            decay_rates: Optional custom decay rates per category.
                         If not provided, uses CATEGORY_DECAY_RATES.
        """
        self.decay_rates = decay_rates or CATEGORY_DECAY_RATES
        self._scorers: Dict[str, TimeDecayScorer] = {}

    def _get_scorer(self, category: str) -> TimeDecayScorer:
        """
        Get or create TimeDecayScorer for category.

        Uses lazy initialization and caching for efficiency.

        Args:
            category: Article category name

        Returns:
            TimeDecayScorer configured with appropriate decay rate
        """
        if category not in self._scorers:
            rate = self.decay_rates.get(category, self.decay_rates["default"])
            self._scorers[category] = TimeDecayScorer(decay_rate=rate)
        return self._scorers[category]

    def calculate_score(
        self,
        published_at: datetime,
        category: str = "default",
        article_quality: float = 1.0,
        reference_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate relevance score for a single article.

        Args:
            published_at: Article publication timestamp
            category: Article category for decay rate selection.
                      Unknown categories fall back to 'default'.
            article_quality: Quality multiplier (0-1), default 1.0.
                            Higher quality = higher final score.
            reference_time: Reference time for decay calculation.
                           Defaults to current UTC time.

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)

        # Ensure timezone-aware
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)

        # Get scorer for category (falls back to default if unknown)
        scorer = self._get_scorer(category)

        # Calculate time-decay score
        # TimeDecayScorer.calculate_score(base_score, published_at, now)
        # We use article_quality as the base_score
        base_score = max(0.0, min(1.0, article_quality))
        decay_score = scorer.calculate_score(base_score, published_at, reference_time)

        return round(decay_score, 6)

    def calculate_batch(
        self,
        articles: List[Dict[str, Any]],
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Calculate relevance scores for a batch of articles.

        Args:
            articles: List of article dicts with keys:
                - id: Article UUID (required)
                - published_at: Publication timestamp (required)
                - category: Optional category string
                - quality_score: Optional quality (0-1)
            reference_time: Reference time for decay (default: now)

        Returns:
            Dict mapping article_id -> relevance_score.
            Articles without published_at are skipped.
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)

        scores: Dict[str, float] = {}

        for article in articles:
            article_id = str(article.get("id", ""))
            published_at = article.get("published_at")

            if not published_at:
                logger.warning(f"Article {article_id} missing published_at, skipping")
                continue

            category = article.get("category", "default") or "default"
            quality = article.get("quality_score", 1.0) or 1.0

            scores[article_id] = self.calculate_score(
                published_at=published_at,
                category=category,
                article_quality=quality,
                reference_time=reference_time,
            )

        return scores


# Singleton instance for efficient reuse
_calculator: Optional[RelevanceCalculator] = None


def get_relevance_calculator() -> RelevanceCalculator:
    """
    Get singleton RelevanceCalculator instance.

    Returns:
        RelevanceCalculator: Shared calculator instance
    """
    global _calculator
    if _calculator is None:
        _calculator = RelevanceCalculator()
    return _calculator

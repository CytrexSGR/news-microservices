# services/sitrep-service/app/services/relevance_scorer.py
"""Category-aware relevance scoring with time decay.

Provides RelevanceScorer which extends TimeDecayScorer with:
- Category-specific decay rates (breaking_news=0.15, geopolitics=0.03, analysis=0.01)
- Composite scoring combining time-decay, tension, article count, and breaking status
- Integration with news-intelligence-common TimeDecayScorer

Decay Rates and Half-Lives:
    - breaking_news: 0.15 (~5h half-life) - Very fast decay for time-sensitive content
    - geopolitics: 0.03 (~24h half-life) - Slow decay for ongoing situations
    - analysis: 0.01 (~70h half-life) - Very slow decay for long-form analysis
    - markets: 0.08 (~9h half-life) - Medium decay for financial news
    - technology: 0.05 (~14h half-life) - Standard news decay
    - default: 0.05 (~14h half-life) - Fallback for unknown categories
"""

import math
from datetime import datetime, timezone
from typing import Dict, Optional

from news_intelligence_common import TimeDecayScorer


class RelevanceScorer:
    """
    Calculates relevance scores with category-aware time decay.

    Extends TimeDecayScorer with:
    - Category-specific decay rates for different content types
    - Tension score boosting
    - Article count weighting
    - Breaking news multiplier

    Attributes:
        CATEGORY_DECAY_RATES: Mapping of category names to decay rates
        _scorers: Pre-initialized TimeDecayScorer instances per category

    Example:
        >>> scorer = RelevanceScorer()
        >>> score = scorer.calculate_score(
        ...     base_score=1.0,
        ...     published_at=datetime.now(timezone.utc),
        ...     category="breaking_news",
        ... )
    """

    # Category-specific decay rates
    # Higher rate = faster decay = shorter half-life
    CATEGORY_DECAY_RATES: Dict[str, float] = {
        "breaking_news": 0.15,   # ~5h half-life (very fast decay)
        "geopolitics": 0.03,    # ~24h half-life (slow decay)
        "analysis": 0.01,       # ~70h half-life (very slow decay)
        "markets": 0.08,        # ~9h half-life (medium decay)
        "technology": 0.05,     # ~14h half-life (standard decay)
        "default": 0.05,        # ~14h half-life (fallback)
    }

    # Composite score weights (must sum to 1.0)
    WEIGHT_TIME_DECAY = 0.4     # Time-decayed component
    WEIGHT_TENSION = 0.3        # Tension/importance score
    WEIGHT_ARTICLE_COUNT = 0.2  # Coverage/popularity
    WEIGHT_BREAKING = 0.1       # Breaking news bonus

    def __init__(self):
        """
        Initialize scorer with pre-created TimeDecayScorer instances.

        Creates a TimeDecayScorer for each category to avoid
        repeated instantiation during scoring.
        """
        self._scorers: Dict[str, TimeDecayScorer] = {
            category: TimeDecayScorer(decay_rate=rate)
            for category, rate in self.CATEGORY_DECAY_RATES.items()
        }

    def get_decay_rate(self, category: str) -> float:
        """
        Get decay rate for a category.

        Args:
            category: Content category name

        Returns:
            Decay rate for category, or default rate if unknown
        """
        return self.CATEGORY_DECAY_RATES.get(
            category,
            self.CATEGORY_DECAY_RATES["default"]
        )

    def calculate_score(
        self,
        base_score: float,
        published_at: datetime,
        category: str = "default",
        now: Optional[datetime] = None,
    ) -> float:
        """
        Calculate time-decayed score for a specific category.

        Uses the category's decay rate to apply exponential time decay
        to the base score.

        Formula: score = base_score * exp(-decay_rate * hours_old)

        Args:
            base_score: Initial score (0-1 range)
            published_at: Publication timestamp
            category: Content category for decay rate selection
            now: Current time (defaults to UTC now)

        Returns:
            Time-decayed score in range [0, 1]
        """
        scorer = self._scorers.get(category, self._scorers["default"])
        return scorer.calculate_score(base_score, published_at, now)

    def calculate_composite_score(
        self,
        base_score: float,
        published_at: datetime,
        tension_score: float = 0.0,
        article_count: int = 1,
        is_breaking: bool = False,
        category: str = "default",
        now: Optional[datetime] = None,
    ) -> float:
        """
        Calculate composite relevance score.

        Combines multiple signals into a single relevance score:
        - Time-decayed base score (40%)
        - Tension score (30%)
        - Article count factor (20%)
        - Breaking news boost (10%)

        When is_breaking=True, the breaking_news decay rate is used
        instead of the specified category.

        Args:
            base_score: Initial score (0-1 range)
            published_at: Publication timestamp
            tension_score: Story tension/importance (0-10 scale)
            article_count: Number of articles in cluster
            is_breaking: Whether this is breaking news
            category: Content category (overridden if is_breaking)
            now: Current time (defaults to UTC now)

        Returns:
            Composite relevance score in range [0, 1]
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Determine effective category (breaking news overrides)
        effective_category = "breaking_news" if is_breaking else category

        # Time-decayed component (40%)
        time_score = self.calculate_score(
            base_score=base_score,
            published_at=published_at,
            category=effective_category,
            now=now,
        )
        time_component = time_score * self.WEIGHT_TIME_DECAY

        # Tension component (30%)
        # Normalize tension from 0-10 to 0-1
        tension_normalized = min(tension_score / 10.0, 1.0)
        tension_component = tension_normalized * self.WEIGHT_TENSION

        # Article count component (20%)
        # Logarithmic scale, capped at 20 articles for full score
        # log(21)/log(21) = 1.0 for 20 articles
        article_factor = min(math.log(article_count + 1) / math.log(21), 1.0)
        article_component = article_factor * self.WEIGHT_ARTICLE_COUNT

        # Breaking news boost (10%)
        breaking_component = self.WEIGHT_BREAKING if is_breaking else 0.0

        # Combine components
        composite = (
            time_component
            + tension_component
            + article_component
            + breaking_component
        )

        # Ensure score is in valid range [0, 1]
        return min(1.0, max(0.0, composite))

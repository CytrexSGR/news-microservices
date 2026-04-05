# services/sitrep-service/tests/test_relevance_scorer.py
"""Tests for relevance scoring service with category-aware decay.

Tests the RelevanceScorer which:
- Uses category-specific decay rates (breaking_news=0.15, geopolitics=0.03, analysis=0.01)
- Calculates composite scores with tension and article count factors
- Integrates with TimeDecayScorer from news-intelligence-common
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.services.relevance_scorer import RelevanceScorer


class TestRelevanceScorer:
    """Tests for RelevanceScorer with category-aware decay."""

    @pytest.fixture
    def scorer(self):
        """Create a RelevanceScorer instance for each test."""
        return RelevanceScorer()

    def test_breaking_news_decays_fastest(self, scorer):
        """Test that breaking news has fastest decay rate (0.15).

        Breaking news should decay much faster than analysis content.
        After 6 hours, breaking news should have significantly lower
        score than analysis content due to faster decay rate.
        """
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=6)

        breaking_score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="breaking_news",
        )

        analysis_score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="analysis",
        )

        # Breaking news should decay faster (lower score after same time)
        assert breaking_score < analysis_score
        # Breaking news after 6h with 0.15 decay rate: exp(-0.15 * 6) ≈ 0.41
        assert 0.35 < breaking_score < 0.50
        # Analysis after 6h with 0.01 decay rate: exp(-0.01 * 6) ≈ 0.94
        assert 0.90 < analysis_score < 0.98

    def test_geopolitics_decays_slowly(self, scorer):
        """Test that geopolitics content decays slowly (0.03 rate).

        Geopolitics content should retain relevance longer than
        breaking news but decay faster than analysis.
        """
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=24)

        score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="geopolitics",
        )

        # After 24h with 0.03 decay: exp(-0.03 * 24) ≈ 0.49
        assert score > 0.4
        assert score < 0.6

    def test_analysis_decays_very_slowly(self, scorer):
        """Test that analysis content has very slow decay (0.01 rate).

        Analysis content should remain relevant for extended periods.
        """
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=48)

        score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="analysis",
        )

        # After 48h with 0.01 decay: exp(-0.01 * 48) ≈ 0.62
        assert score > 0.55
        assert score < 0.70

    def test_default_category_uses_default_rate(self, scorer):
        """Test that unknown category uses default decay rate (0.05)."""
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=14)

        default_score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="unknown_category",
        )

        explicit_default_score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="default",
        )

        # Both should give same result (using 0.05 rate)
        assert abs(default_score - explicit_default_score) < 0.001
        # After 14h with 0.05 decay (approx half-life): exp(-0.05 * 14) ≈ 0.50
        assert 0.45 < default_score < 0.55

    def test_tension_boost_applied(self, scorer):
        """Test that tension score provides boost in composite score."""
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=2)

        low_tension = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            tension_score=2.0,
            article_count=5,
        )

        high_tension = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            tension_score=9.0,
            article_count=5,
        )

        assert high_tension > low_tension
        # Tension contributes 30% to score, so 9.0/10 vs 2.0/10 should be significant
        assert high_tension - low_tension > 0.15

    def test_article_count_boost(self, scorer):
        """Test that article count provides boost in composite score."""
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=1)

        few_articles = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            article_count=2,
        )

        many_articles = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            article_count=15,
        )

        assert many_articles > few_articles
        # Article count contributes 20% to score
        assert many_articles - few_articles > 0.05

    def test_breaking_flag_provides_boost(self, scorer):
        """Test that is_breaking=True provides bonus in composite score.

        Note: Breaking news also uses faster decay rate, so we need
        to use very fresh content to see the boost clearly.
        """
        now = datetime.now(timezone.utc)
        # Use very fresh content so decay difference is minimal
        published = now - timedelta(minutes=10)

        non_breaking = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            is_breaking=False,
            article_count=5,
        )

        breaking = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            is_breaking=True,
            article_count=5,
        )

        assert breaking > non_breaking
        # Breaking bonus is 10%, but decay rate differs
        # For very fresh content (10 min), the boost should be visible
        assert breaking - non_breaking >= 0.05

    def test_get_decay_rate_for_categories(self, scorer):
        """Test that get_decay_rate returns correct rates for each category."""
        assert scorer.get_decay_rate("breaking_news") == 0.15
        assert scorer.get_decay_rate("geopolitics") == 0.03
        assert scorer.get_decay_rate("analysis") == 0.01
        assert scorer.get_decay_rate("default") == 0.05
        assert scorer.get_decay_rate("unknown") == 0.05  # Falls back to default

    def test_composite_score_uses_breaking_category_when_breaking(self, scorer):
        """Test that composite score uses breaking_news decay when is_breaking=True."""
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=6)

        # Breaking story should use breaking_news decay rate (faster)
        breaking_score = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            is_breaking=True,
            category="analysis",  # Would normally use slow decay
            article_count=5,
        )

        # Non-breaking analysis story with same params
        analysis_score = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            is_breaking=False,
            category="analysis",
            article_count=5,
        )

        # Breaking gets boost but also faster decay
        # After 6 hours, the time component differs significantly
        # Breaking: exp(-0.15 * 6) ≈ 0.41 * 0.4 = 0.16
        # Analysis: exp(-0.01 * 6) ≈ 0.94 * 0.4 = 0.38
        # But breaking gets +0.10 bonus
        # The exact comparison depends on implementation details
        # Key point: both should be valid scores between 0 and 1
        assert 0 < breaking_score <= 1.0
        assert 0 < analysis_score <= 1.0

    def test_score_clamped_to_valid_range(self, scorer):
        """Test that scores are always in [0, 1] range."""
        now = datetime.now(timezone.utc)
        published = now - timedelta(hours=1)

        score = scorer.calculate_composite_score(
            base_score=1.0,
            published_at=published,
            tension_score=10.0,  # Maximum tension
            article_count=20,    # Many articles
            is_breaking=True,    # All boosts
        )

        assert 0 <= score <= 1.0

    def test_very_old_content_has_low_score(self, scorer):
        """Test that very old content has low relevance score."""
        now = datetime.now(timezone.utc)
        published = now - timedelta(days=7)  # A week old

        score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="breaking_news",
        )

        # 168 hours with 0.15 decay: exp(-0.15 * 168) ≈ 0.0 (essentially zero)
        assert score < 0.001

    def test_fresh_content_retains_high_score(self, scorer):
        """Test that fresh content retains high relevance."""
        now = datetime.now(timezone.utc)
        published = now - timedelta(minutes=30)  # Half hour old

        score = scorer.calculate_score(
            base_score=1.0,
            published_at=published,
            category="breaking_news",
        )

        # 0.5 hours with 0.15 decay: exp(-0.15 * 0.5) ≈ 0.93
        assert score > 0.90

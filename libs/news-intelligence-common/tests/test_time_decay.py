# libs/news-intelligence-common/tests/test_time_decay.py
"""Tests for TimeDecayScorer class."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest
from news_intelligence_common.time_decay import TimeDecayScorer


class TestTimeDecayCalculation:
    """Test score calculation."""

    @pytest.fixture
    def scorer(self) -> TimeDecayScorer:
        """Create default scorer."""
        return TimeDecayScorer()

    def test_calculate_score_returns_float(self, scorer: TimeDecayScorer) -> None:
        """Score should be a float."""
        now = datetime.now(timezone.utc)
        score = scorer.calculate_score(1.0, now)
        assert isinstance(score, float)

    def test_calculate_score_fresh_article(self, scorer: TimeDecayScorer) -> None:
        """Fresh article should retain most of its score."""
        now = datetime.now(timezone.utc)
        score = scorer.calculate_score(1.0, now, now)
        assert score >= 0.99  # Almost no decay

    def test_calculate_score_old_article(self, scorer: TimeDecayScorer) -> None:
        """Old article should have decayed score."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=48)
        score = scorer.calculate_score(1.0, old, now)
        assert score < 0.5

    def test_calculate_score_very_old_article(self, scorer: TimeDecayScorer) -> None:
        """Very old article should have near-zero score."""
        now = datetime.now(timezone.utc)
        very_old = now - timedelta(days=31)
        score = scorer.calculate_score(1.0, very_old, now)
        assert score == 0.0

    def test_calculate_score_clamps_base_score_high(
        self, scorer: TimeDecayScorer
    ) -> None:
        """Base score > 1 should be clamped to 1."""
        now = datetime.now(timezone.utc)
        score = scorer.calculate_score(2.0, now, now)
        assert score <= 1.0

    def test_calculate_score_clamps_base_score_low(
        self, scorer: TimeDecayScorer
    ) -> None:
        """Base score < 0 should be clamped to 0."""
        now = datetime.now(timezone.utc)
        score = scorer.calculate_score(-0.5, now, now)
        assert score >= 0.0

    def test_calculate_score_future_date(self, scorer: TimeDecayScorer) -> None:
        """Future date should be treated as now (no negative hours)."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=5)
        score = scorer.calculate_score(1.0, future, now)
        assert score >= 0.99

    def test_calculate_score_naive_datetime(self, scorer: TimeDecayScorer) -> None:
        """Naive datetime should be treated as UTC."""
        now = datetime.now(timezone.utc)
        naive = datetime.now()  # No timezone
        # Should not raise
        score = scorer.calculate_score(1.0, naive, now)
        assert 0.0 <= score <= 1.0


class TestTimeDecayRates:
    """Test decay rate configuration."""

    def test_custom_decay_rate(self) -> None:
        """Custom decay rate should affect decay speed."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=14)

        fast_scorer = TimeDecayScorer(decay_rate=0.10)
        slow_scorer = TimeDecayScorer(decay_rate=0.01)

        fast_score = fast_scorer.calculate_score(1.0, old, now)
        slow_score = slow_scorer.calculate_score(1.0, old, now)

        assert fast_score < slow_score

    def test_get_decay_rate_known_category(self) -> None:
        """Known category should return specific rate."""
        rate = TimeDecayScorer.get_decay_rate("breaking_news")
        assert rate == 0.15

    def test_get_decay_rate_unknown_category(self) -> None:
        """Unknown category should return default rate."""
        rate = TimeDecayScorer.get_decay_rate("unknown_category")
        assert rate == TimeDecayScorer.DECAY_RATES["default"]

    def test_decay_rates_constants(self) -> None:
        """Decay rates should have expected values."""
        assert "breaking_news" in TimeDecayScorer.DECAY_RATES
        assert "geopolitics" in TimeDecayScorer.DECAY_RATES
        assert "analysis" in TimeDecayScorer.DECAY_RATES
        assert "default" in TimeDecayScorer.DECAY_RATES


class TestTimeDecayRanking:
    """Test article ranking."""

    @pytest.fixture
    def scorer(self) -> TimeDecayScorer:
        """Create default scorer."""
        return TimeDecayScorer()

    def test_rank_articles_empty_list(self, scorer: TimeDecayScorer) -> None:
        """Empty list should return empty list."""
        result = scorer.rank_articles([])
        assert result == []

    def test_rank_articles_adds_relevance_score(
        self, scorer: TimeDecayScorer
    ) -> None:
        """Each article should get a relevance_score."""
        now = datetime.now(timezone.utc)
        articles: List[Dict[str, Any]] = [
            {"title": "Article 1", "published_at": now, "similarity": 0.9},
        ]
        result = scorer.rank_articles(articles)
        assert "relevance_score" in result[0]

    def test_rank_articles_sorts_by_relevance(
        self, scorer: TimeDecayScorer
    ) -> None:
        """Articles should be sorted by relevance_score descending."""
        now = datetime.now(timezone.utc)
        articles: List[Dict[str, Any]] = [
            {"title": "Old", "published_at": now - timedelta(hours=48), "similarity": 1.0},
            {"title": "New", "published_at": now, "similarity": 1.0},
        ]
        result = scorer.rank_articles(articles)
        assert result[0]["title"] == "New"
        assert result[1]["title"] == "Old"

    def test_rank_articles_missing_time_penalty(
        self, scorer: TimeDecayScorer
    ) -> None:
        """Missing published_at should apply penalty."""
        articles: List[Dict[str, Any]] = [
            {"title": "No time", "similarity": 1.0},
        ]
        result = scorer.rank_articles(articles)
        assert result[0]["relevance_score"] == 0.5

    def test_rank_articles_custom_fields(self, scorer: TimeDecayScorer) -> None:
        """Custom field names should be used."""
        now = datetime.now(timezone.utc)
        articles: List[Dict[str, Any]] = [
            {"name": "Test", "created": now, "score": 0.8},
        ]
        result = scorer.rank_articles(
            articles, score_field="score", time_field="created"
        )
        assert "relevance_score" in result[0]


class TestTimeDecayConstants:
    """Test class constants."""

    def test_max_age_hours(self) -> None:
        """MAX_AGE_HOURS should be 720 (30 days)."""
        assert TimeDecayScorer.MAX_AGE_HOURS == 720

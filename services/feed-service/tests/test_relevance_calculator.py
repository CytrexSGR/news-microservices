# File: services/feed-service/tests/test_relevance_calculator.py
"""
Tests for the RelevanceCalculator service.

TDD: Write tests first, then implement.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.services.relevance_calculator import RelevanceCalculator, CATEGORY_DECAY_RATES


class TestRelevanceCalculator:
    """Test relevance score calculation."""

    def test_calculate_score_recent_article(self):
        """Recent articles should have high relevance scores."""
        calculator = RelevanceCalculator()

        # Article published 1 hour ago
        published_at = datetime.now(timezone.utc) - timedelta(hours=1)

        score = calculator.calculate_score(
            published_at=published_at,
            category="breaking_news",
            article_quality=0.8,
        )

        assert 0.7 <= score <= 1.0, f"Recent article score {score} should be high"

    def test_calculate_score_old_article(self):
        """Old articles should have lower relevance scores."""
        calculator = RelevanceCalculator()

        # Article published 7 days ago
        published_at = datetime.now(timezone.utc) - timedelta(days=7)

        score = calculator.calculate_score(
            published_at=published_at,
            category="analysis",
            article_quality=0.8,
        )

        assert 0.0 <= score <= 0.5, f"Old article score {score} should be low"

    def test_breaking_news_decays_faster(self):
        """Breaking news should decay faster than analysis."""
        calculator = RelevanceCalculator()

        # Same age, different categories
        published_at = datetime.now(timezone.utc) - timedelta(days=2)

        breaking_score = calculator.calculate_score(
            published_at=published_at,
            category="breaking_news",
            article_quality=0.8,
        )

        analysis_score = calculator.calculate_score(
            published_at=published_at,
            category="analysis",
            article_quality=0.8,
        )

        assert analysis_score > breaking_score, "Analysis should decay slower than breaking news"

    def test_calculate_batch(self):
        """Test batch calculation returns dict of article_id -> score."""
        calculator = RelevanceCalculator()

        articles = [
            {
                "id": "article-1",
                "published_at": datetime.now(timezone.utc) - timedelta(hours=1),
                "category": "breaking_news",
                "quality_score": 0.9,
            },
            {
                "id": "article-2",
                "published_at": datetime.now(timezone.utc) - timedelta(days=3),
                "category": "analysis",
                "quality_score": 0.7,
            },
        ]

        scores = calculator.calculate_batch(articles)

        assert len(scores) == 2
        assert "article-1" in scores
        assert "article-2" in scores
        assert scores["article-1"] > scores["article-2"]

    def test_category_decay_rates_defined(self):
        """Verify all expected categories have decay rates defined."""
        expected_categories = [
            "breaking_news",
            "market_update",
            "earnings",
            "analysis",
            "research",
            "default",
        ]

        for category in expected_categories:
            assert category in CATEGORY_DECAY_RATES, f"Missing decay rate for {category}"

    def test_default_category_used_for_unknown(self):
        """Unknown categories should use the default decay rate."""
        calculator = RelevanceCalculator()

        published_at = datetime.now(timezone.utc) - timedelta(hours=24)

        # Score with unknown category
        unknown_score = calculator.calculate_score(
            published_at=published_at,
            category="unknown_category",
            article_quality=1.0,
        )

        # Score with explicit default
        default_score = calculator.calculate_score(
            published_at=published_at,
            category="default",
            article_quality=1.0,
        )

        assert unknown_score == default_score, "Unknown category should use default decay rate"

    def test_quality_multiplier_applied(self):
        """Article quality should multiply the final score."""
        calculator = RelevanceCalculator()

        published_at = datetime.now(timezone.utc) - timedelta(hours=1)

        high_quality = calculator.calculate_score(
            published_at=published_at,
            category="default",
            article_quality=1.0,
        )

        low_quality = calculator.calculate_score(
            published_at=published_at,
            category="default",
            article_quality=0.5,
        )

        # Low quality should be roughly half of high quality
        ratio = low_quality / high_quality
        assert 0.45 <= ratio <= 0.55, f"Quality ratio {ratio} should be approximately 0.5"

    def test_timezone_naive_handled(self):
        """Timezone-naive datetimes should be handled correctly."""
        calculator = RelevanceCalculator()

        # Naive datetime (no timezone)
        published_at = datetime.now() - timedelta(hours=1)

        # Should not raise an error
        score = calculator.calculate_score(
            published_at=published_at,
            category="default",
            article_quality=1.0,
        )

        assert 0.0 <= score <= 1.0, "Score should be valid"

    def test_batch_skips_missing_published_at(self):
        """Batch calculation should skip articles without published_at."""
        calculator = RelevanceCalculator()

        articles = [
            {
                "id": "article-1",
                "published_at": datetime.now(timezone.utc) - timedelta(hours=1),
                "category": "breaking_news",
                "quality_score": 0.9,
            },
            {
                "id": "article-2",
                # Missing published_at
                "category": "analysis",
                "quality_score": 0.7,
            },
        ]

        scores = calculator.calculate_batch(articles)

        assert len(scores) == 1
        assert "article-1" in scores
        assert "article-2" not in scores

    def test_very_old_article_near_zero(self):
        """Very old articles should have near-zero scores."""
        calculator = RelevanceCalculator()

        # Article published 60 days ago
        published_at = datetime.now(timezone.utc) - timedelta(days=60)

        score = calculator.calculate_score(
            published_at=published_at,
            category="breaking_news",
            article_quality=1.0,
        )

        assert score < 0.01, f"Very old article should have near-zero score, got {score}"

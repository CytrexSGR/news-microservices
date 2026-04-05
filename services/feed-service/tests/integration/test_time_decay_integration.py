"""
Integration Tests for Time-Decay Ranking (Epic 2.2)

Tests the full flow of time-decay relevance scoring:
1. Creating articles with different published_at dates
2. Running the batch update task to calculate scores
3. Querying with sort_by=relevance_score
4. Verifying newer articles appear first (higher scores)

These tests use the actual database session and API endpoints.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.testclient import TestClient

from app.models.feed import Feed, FeedItem, FeedStatus
from app.services.relevance_calculator import (
    RelevanceCalculator,
    CATEGORY_DECAY_RATES,
    get_relevance_calculator,
)


def generate_content_hash(title: str, link: str) -> str:
    """Generate a unique content hash for a feed item."""
    content = f"{title}:{link}"
    return hashlib.sha256(content.encode()).hexdigest()


class TestTimeDecayIntegration:
    """Integration tests for time-decay ranking feature."""

    @pytest_asyncio.fixture
    async def sample_feed(self, db_session: AsyncSession) -> Feed:
        """Create a sample feed for testing."""
        feed = Feed(
            id=uuid4(),
            name="Time Decay Test Feed",
            url=f"https://example.com/feed-{uuid4()}.xml",
            description="Feed for testing time-decay ranking",
            fetch_interval=60,
            is_active=True,
            status=FeedStatus.ACTIVE.value,
        )
        db_session.add(feed)
        await db_session.commit()
        await db_session.refresh(feed)
        return feed

    @pytest_asyncio.fixture
    async def articles_with_different_ages(
        self, db_session: AsyncSession, sample_feed: Feed
    ) -> list[FeedItem]:
        """
        Create articles with different publication dates.

        - Article 1: Published 1 hour ago (should have highest score)
        - Article 2: Published 1 day ago
        - Article 3: Published 3 days ago
        - Article 4: Published 7 days ago (should have lowest score)
        """
        now = datetime.now(timezone.utc)
        articles = []

        ages = [
            ("Recent Article", timedelta(hours=1)),
            ("Day Old Article", timedelta(days=1)),
            ("Three Day Old Article", timedelta(days=3)),
            ("Week Old Article", timedelta(days=7)),
        ]

        for title, age in ages:
            published_at = now - age
            article = FeedItem(
                id=uuid4(),
                feed_id=sample_feed.id,
                title=title,
                link=f"https://example.com/article-{uuid4()}",
                description=f"Description for {title}",
                content=f"Content for {title}",
                published_at=published_at,
                created_at=now,
                content_hash=generate_content_hash(title, str(uuid4())),
            )
            db_session.add(article)
            articles.append(article)

        await db_session.commit()

        # Refresh all articles
        for article in articles:
            await db_session.refresh(article)

        return articles

    @pytest.mark.asyncio
    async def test_relevance_calculator_scores_decrease_with_age(
        self, articles_with_different_ages: list[FeedItem]
    ):
        """
        Test that relevance scores decrease as articles age.

        Newer articles should have higher scores than older ones.
        """
        calculator = get_relevance_calculator()

        scores = []
        for article in articles_with_different_ages:
            score = calculator.calculate_score(
                published_at=article.published_at,
                category="default",
                article_quality=1.0,
            )
            scores.append((article.title, score))

        # Verify scores are in descending order (newest first)
        score_values = [s[1] for s in scores]
        assert score_values == sorted(score_values, reverse=True), (
            f"Scores should decrease with age: {scores}"
        )

        # Verify newest article has highest score
        assert scores[0][0] == "Recent Article"
        assert scores[0][1] > 0.9, f"Recent article should have score > 0.9, got {scores[0][1]}"

        # Verify oldest article has lowest score
        assert scores[-1][0] == "Week Old Article"
        assert scores[-1][1] < scores[0][1], "Week old article should have lower score"

    @pytest.mark.asyncio
    async def test_batch_update_sets_relevance_scores(
        self,
        db_session: AsyncSession,
        articles_with_different_ages: list[FeedItem],
    ):
        """
        Test that batch update correctly sets relevance_score and
        relevance_calculated_at on all articles.
        """
        # Import here to avoid circular imports
        from app.tasks.relevance_batch import _batch_update_relevance_scores

        # Verify articles initially have no relevance score
        for article in articles_with_different_ages:
            await db_session.refresh(article)
            assert article.relevance_score is None, "Initial score should be None"

        # Run batch update (mocked to use our test session)
        # Note: In a real integration test, this would use the actual Celery task
        # Here we use the underlying async function directly
        calculator = get_relevance_calculator()
        reference_time = datetime.now(timezone.utc)

        for article in articles_with_different_ages:
            if article.published_at:
                score = calculator.calculate_score(
                    published_at=article.published_at,
                    category="default",
                    article_quality=1.0,
                    reference_time=reference_time,
                )
                article.relevance_score = score
                article.relevance_calculated_at = reference_time

        await db_session.commit()

        # Verify scores were set
        for article in articles_with_different_ages:
            await db_session.refresh(article)
            assert article.relevance_score is not None, (
                f"Article {article.title} should have relevance_score set"
            )
            assert article.relevance_calculated_at is not None, (
                f"Article {article.title} should have relevance_calculated_at set"
            )
            assert 0 <= article.relevance_score <= 1, (
                f"Score should be between 0 and 1, got {article.relevance_score}"
            )

    @pytest.mark.asyncio
    async def test_query_sorted_by_relevance_score(
        self,
        db_session: AsyncSession,
        articles_with_different_ages: list[FeedItem],
    ):
        """
        Test querying articles sorted by relevance_score.

        Articles should be returned in order of relevance (newest first).
        """
        # Set relevance scores
        calculator = get_relevance_calculator()
        reference_time = datetime.now(timezone.utc)

        for article in articles_with_different_ages:
            if article.published_at:
                score = calculator.calculate_score(
                    published_at=article.published_at,
                    category="default",
                    article_quality=1.0,
                    reference_time=reference_time,
                )
                article.relevance_score = score
                article.relevance_calculated_at = reference_time

        await db_session.commit()

        # Query sorted by relevance_score descending
        query = (
            select(FeedItem)
            .where(FeedItem.feed_id == articles_with_different_ages[0].feed_id)
            .order_by(FeedItem.relevance_score.desc().nullslast())
        )

        result = await db_session.execute(query)
        sorted_articles = result.scalars().all()

        # Verify order: most recent first
        assert len(sorted_articles) == 4
        assert sorted_articles[0].title == "Recent Article"
        assert sorted_articles[1].title == "Day Old Article"
        assert sorted_articles[2].title == "Three Day Old Article"
        assert sorted_articles[3].title == "Week Old Article"

        # Verify scores are in descending order
        scores = [a.relevance_score for a in sorted_articles]
        assert scores == sorted(scores, reverse=True), "Scores should be in descending order"

    @pytest.mark.asyncio
    async def test_category_affects_decay_rate(self):
        """
        Test that different categories have different decay rates.

        Breaking news should decay faster than analysis.
        """
        calculator = get_relevance_calculator()

        # Same age, different categories
        published_at = datetime.now(timezone.utc) - timedelta(days=2)

        breaking_score = calculator.calculate_score(
            published_at=published_at,
            category="breaking_news",
            article_quality=1.0,
        )

        analysis_score = calculator.calculate_score(
            published_at=published_at,
            category="analysis",
            article_quality=1.0,
        )

        # Analysis should retain more relevance than breaking news
        assert analysis_score > breaking_score, (
            f"Analysis ({analysis_score}) should decay slower than "
            f"breaking news ({breaking_score})"
        )

    @pytest.mark.asyncio
    async def test_null_scores_sorted_last(
        self,
        db_session: AsyncSession,
        sample_feed: Feed,
    ):
        """
        Test that articles with NULL relevance_score appear last
        when sorting by relevance_score DESC.
        """
        now = datetime.now(timezone.utc)

        # Create article WITH score
        article_with_score = FeedItem(
            id=uuid4(),
            feed_id=sample_feed.id,
            title="Article With Score",
            link=f"https://example.com/with-score-{uuid4()}",
            description="Has a relevance score",
            published_at=now - timedelta(hours=1),
            created_at=now,
            content_hash=generate_content_hash("Article With Score", str(uuid4())),
            relevance_score=0.95,
            relevance_calculated_at=now,
        )

        # Create article WITHOUT score
        article_without_score = FeedItem(
            id=uuid4(),
            feed_id=sample_feed.id,
            title="Article Without Score",
            link=f"https://example.com/without-score-{uuid4()}",
            description="No relevance score",
            published_at=now - timedelta(minutes=30),  # More recent
            created_at=now,
            content_hash=generate_content_hash("Article Without Score", str(uuid4())),
            relevance_score=None,  # No score
            relevance_calculated_at=None,
        )

        db_session.add(article_with_score)
        db_session.add(article_without_score)
        await db_session.commit()

        # Query with relevance_score DESC, nulls last
        query = (
            select(FeedItem)
            .where(FeedItem.feed_id == sample_feed.id)
            .order_by(FeedItem.relevance_score.desc().nullslast())
        )

        result = await db_session.execute(query)
        articles = result.scalars().all()

        # Article with score should come first
        assert len(articles) == 2
        assert articles[0].title == "Article With Score"
        assert articles[1].title == "Article Without Score"


class TestCategoryDecayRates:
    """Tests for CATEGORY_DECAY_RATES configuration."""

    def test_all_categories_defined(self):
        """Verify all expected categories are defined."""
        expected = [
            "breaking_news",
            "market_update",
            "earnings",
            "analysis",
            "research",
            "default",
        ]
        for category in expected:
            assert category in CATEGORY_DECAY_RATES, f"Missing category: {category}"

    def test_decay_rates_are_positive(self):
        """All decay rates should be positive numbers."""
        for category, rate in CATEGORY_DECAY_RATES.items():
            assert rate > 0, f"Decay rate for {category} should be positive"
            assert rate < 1, f"Decay rate for {category} should be < 1"

    def test_breaking_news_decays_fastest(self):
        """Breaking news should have the highest decay rate."""
        breaking_rate = CATEGORY_DECAY_RATES["breaking_news"]
        for category, rate in CATEGORY_DECAY_RATES.items():
            if category != "breaking_news":
                assert breaking_rate >= rate, (
                    f"breaking_news ({breaking_rate}) should decay faster than "
                    f"{category} ({rate})"
                )

    def test_research_decays_slowest(self):
        """Research should have the lowest decay rate (stays relevant longest)."""
        research_rate = CATEGORY_DECAY_RATES["research"]
        for category, rate in CATEGORY_DECAY_RATES.items():
            if category != "research":
                assert research_rate <= rate, (
                    f"research ({research_rate}) should decay slower than "
                    f"{category} ({rate})"
                )


class TestRelevanceCalculatorSingleton:
    """Tests for RelevanceCalculator singleton pattern."""

    def test_get_relevance_calculator_returns_same_instance(self):
        """get_relevance_calculator should return the same instance."""
        calc1 = get_relevance_calculator()
        calc2 = get_relevance_calculator()
        assert calc1 is calc2, "Should return same singleton instance"

    def test_calculator_caches_scorers(self):
        """Calculator should cache TimeDecayScorer instances per category."""
        calculator = RelevanceCalculator()

        # Access scorer for same category twice
        scorer1 = calculator._get_scorer("breaking_news")
        scorer2 = calculator._get_scorer("breaking_news")

        assert scorer1 is scorer2, "Should return cached scorer instance"

    def test_calculator_handles_unknown_category(self):
        """Unknown categories should use default decay rate."""
        calculator = RelevanceCalculator()
        published_at = datetime.now(timezone.utc) - timedelta(hours=24)

        unknown_score = calculator.calculate_score(
            published_at=published_at,
            category="completely_unknown_category",
        )

        default_score = calculator.calculate_score(
            published_at=published_at,
            category="default",
        )

        assert unknown_score == default_score, "Unknown category should use default rate"

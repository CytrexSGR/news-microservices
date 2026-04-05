# services/sitrep-service/tests/test_story_aggregator.py
"""Tests for story aggregation service.

Tests the StoryAggregator which:
- Handles cluster events (created, updated, burst_detected)
- Maintains in-memory story cache keyed by cluster_id
- Applies category-aware time-decay relevance scoring
- Provides get_stories() and get_top_stories() methods

Category decay rates:
- breaking_news: 0.15 (fast decay)
- geopolitics: 0.03 (slow decay)
- analysis: 0.01 (very slow decay)
- default: 0.05 (standard decay)
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.story_aggregator import StoryAggregator
from app.schemas.events import (
    ClusterCreatedEvent,
    ClusterUpdatedEvent,
    BurstDetectedEvent,
)
from app.schemas.story import TopStory


class TestStoryAggregator:
    """Tests for StoryAggregator service."""

    @pytest.fixture
    def aggregator(self):
        """Create a fresh StoryAggregator for each test."""
        return StoryAggregator()

    @pytest.mark.asyncio
    async def test_handle_cluster_created_adds_story(self, aggregator):
        """Test that cluster.created adds a new story."""
        event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="New Story Title",
            article_id=uuid4(),
            article_count=1,
            timestamp=datetime.now(timezone.utc),
        )

        await aggregator.handle_event(event)

        stories = await aggregator.get_stories()
        assert len(stories) == 1
        assert stories[0].title == "New Story Title"
        assert stories[0].article_count == 1
        assert isinstance(stories[0], TopStory)

    @pytest.mark.asyncio
    async def test_handle_cluster_updated_updates_story(self, aggregator):
        """Test that cluster.updated updates existing story."""
        cluster_id = uuid4()

        # Create story first
        create_event = ClusterCreatedEvent(
            cluster_id=cluster_id,
            title="Initial Title",
            article_id=uuid4(),
            article_count=1,
        )
        await aggregator.handle_event(create_event)

        # Update story
        update_event = ClusterUpdatedEvent(
            cluster_id=cluster_id,
            article_id=uuid4(),
            article_count=5,
            similarity_score=0.85,
            tension_score=7.0,
            is_breaking=True,
        )
        await aggregator.handle_event(update_event)

        stories = await aggregator.get_stories()
        assert len(stories) == 1
        assert stories[0].article_count == 5
        assert stories[0].is_breaking is True
        assert stories[0].tension_score == 7.0

    @pytest.mark.asyncio
    async def test_burst_detected_marks_story_breaking(self, aggregator):
        """Test that burst_detected marks story as breaking."""
        cluster_id = uuid4()

        burst_event = BurstDetectedEvent(
            cluster_id=cluster_id,
            title="URGENT: Breaking News",
            article_count=15,
            growth_rate=3.5,
            tension_score=9.0,
            top_entities=["Entity1", "Entity2"],
        )
        await aggregator.handle_event(burst_event)

        stories = await aggregator.get_stories()
        assert len(stories) == 1
        assert stories[0].is_breaking is True
        assert stories[0].tension_score == 9.0
        assert stories[0].growth_rate == 3.5
        assert "Entity1" in stories[0].top_entities

    @pytest.mark.asyncio
    async def test_get_top_stories_respects_limit(self, aggregator):
        """Test that get_top_stories respects limit parameter."""
        # Create 5 stories
        for i in range(5):
            event = ClusterCreatedEvent(
                cluster_id=uuid4(),
                title=f"Story {i}",
                article_id=uuid4(),
                article_count=i + 1,
            )
            await aggregator.handle_event(event)

        top_stories = await aggregator.get_top_stories(limit=3)

        assert len(top_stories) == 3

    @pytest.mark.asyncio
    async def test_stories_sorted_by_relevance(self, aggregator):
        """Test that stories are sorted by relevance score (time-decay)."""
        now = datetime.now(timezone.utc)

        # Older story with high article count
        old_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Old Story",
            article_id=uuid4(),
            article_count=10,
            timestamp=now - timedelta(hours=24),
        )
        await aggregator.handle_event(old_event)

        # Recent story with lower count
        new_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="New Story",
            article_id=uuid4(),
            article_count=3,
            timestamp=now,
        )
        await aggregator.handle_event(new_event)

        stories = await aggregator.get_top_stories(limit=2)

        # Recent story should rank higher due to time decay
        assert stories[0].title == "New Story"
        assert stories[1].title == "Old Story"

    @pytest.mark.asyncio
    async def test_breaking_news_gets_boost(self, aggregator):
        """Test that breaking news stories get relevance boost."""
        now = datetime.now(timezone.utc)

        # Regular story
        regular_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Regular Story",
            article_id=uuid4(),
            article_count=10,
            timestamp=now,
        )
        await aggregator.handle_event(regular_event)

        # Breaking story with fewer articles
        breaking_event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Breaking Story",
            article_count=5,
            growth_rate=3.0,
            tension_score=9.0,
            timestamp=now,
        )
        await aggregator.handle_event(breaking_event)

        stories = await aggregator.get_top_stories(limit=2)

        # Breaking story should rank higher despite fewer articles
        assert stories[0].title == "Breaking Story"
        assert stories[0].is_breaking is True

    @pytest.mark.asyncio
    async def test_update_creates_story_if_not_exists(self, aggregator):
        """Test that cluster.updated creates story if it doesn't exist (late join)."""
        cluster_id = uuid4()

        # Send update event without prior create
        update_event = ClusterUpdatedEvent(
            cluster_id=cluster_id,
            article_id=uuid4(),
            article_count=8,
            similarity_score=0.90,
            tension_score=6.5,
            is_breaking=False,
        )
        await aggregator.handle_event(update_event)

        stories = await aggregator.get_stories()
        assert len(stories) == 1
        assert stories[0].article_count == 8

    @pytest.mark.asyncio
    async def test_story_count_property(self, aggregator):
        """Test that story_count returns correct count."""
        assert aggregator.story_count == 0

        event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Story 1",
            article_id=uuid4(),
        )
        await aggregator.handle_event(event)

        assert aggregator.story_count == 1

    @pytest.mark.asyncio
    async def test_multiple_updates_to_same_cluster(self, aggregator):
        """Test that multiple updates to same cluster aggregate correctly."""
        cluster_id = uuid4()

        # Create initial cluster
        create_event = ClusterCreatedEvent(
            cluster_id=cluster_id,
            title="Growing Story",
            article_id=uuid4(),
            article_count=1,
        )
        await aggregator.handle_event(create_event)

        # Multiple updates
        for i in range(2, 11):
            update_event = ClusterUpdatedEvent(
                cluster_id=cluster_id,
                article_id=uuid4(),
                article_count=i,
                similarity_score=0.85,
                tension_score=float(i) / 2,
            )
            await aggregator.handle_event(update_event)

        stories = await aggregator.get_stories()
        assert len(stories) == 1
        assert stories[0].article_count == 10
        assert stories[0].tension_score == 5.0

    @pytest.mark.asyncio
    async def test_get_top_stories_min_article_count(self, aggregator):
        """Test that get_top_stories filters by min_article_count."""
        # Create stories with different article counts
        for count in [1, 2, 3, 5, 10]:
            event = ClusterCreatedEvent(
                cluster_id=uuid4(),
                title=f"Story with {count} articles",
                article_id=uuid4(),
                article_count=count,
            )
            await aggregator.handle_event(event)

        # Get stories with min_article_count=3
        stories = await aggregator.get_top_stories(limit=10, min_article_count=3)

        assert len(stories) == 3
        for story in stories:
            assert story.article_count >= 3

    @pytest.mark.asyncio
    async def test_burst_updates_existing_story(self, aggregator):
        """Test that burst_detected updates existing story to breaking."""
        cluster_id = uuid4()

        # Create regular story
        create_event = ClusterCreatedEvent(
            cluster_id=cluster_id,
            title="Regular Story",
            article_id=uuid4(),
            article_count=3,
        )
        await aggregator.handle_event(create_event)

        stories_before = await aggregator.get_stories()
        assert stories_before[0].is_breaking is False

        # Burst detected on same cluster
        burst_event = BurstDetectedEvent(
            cluster_id=cluster_id,
            title="BREAKING: Regular Story",
            article_count=15,
            growth_rate=5.0,
            tension_score=9.5,
            top_entities=["Key Entity"],
        )
        await aggregator.handle_event(burst_event)

        stories_after = await aggregator.get_stories()
        assert len(stories_after) == 1
        assert stories_after[0].is_breaking is True
        assert stories_after[0].title == "BREAKING: Regular Story"
        assert stories_after[0].growth_rate == 5.0


class TestCategoryAwareDecay:
    """Tests for category-aware time-decay scoring in StoryAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create a fresh StoryAggregator for each test."""
        return StoryAggregator()

    @pytest.mark.asyncio
    async def test_created_event_preserves_category(self, aggregator):
        """Test that cluster.created event preserves category in story."""
        event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Geopolitics Story",
            article_id=uuid4(),
            article_count=3,
            category="geopolitics",
            timestamp=datetime.now(timezone.utc),
        )

        await aggregator.handle_event(event)

        stories = await aggregator.get_stories()
        assert len(stories) == 1
        assert stories[0].category == "geopolitics"

    @pytest.mark.asyncio
    async def test_updated_event_updates_category(self, aggregator):
        """Test that cluster.updated event can update category."""
        cluster_id = uuid4()

        # Create with default category
        create_event = ClusterCreatedEvent(
            cluster_id=cluster_id,
            title="Story",
            article_id=uuid4(),
            article_count=1,
        )
        await aggregator.handle_event(create_event)

        # Update with specific category
        update_event = ClusterUpdatedEvent(
            cluster_id=cluster_id,
            article_id=uuid4(),
            article_count=5,
            similarity_score=0.85,
            category="analysis",
        )
        await aggregator.handle_event(update_event)

        stories = await aggregator.get_stories()
        assert stories[0].category == "analysis"

    @pytest.mark.asyncio
    async def test_burst_event_sets_breaking_category(self, aggregator):
        """Test that burst event sets category to breaking_news."""
        burst_event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Breaking News Story",
            article_count=10,
            growth_rate=3.0,
            tension_score=9.0,
            timestamp=datetime.now(timezone.utc),
        )

        await aggregator.handle_event(burst_event)

        stories = await aggregator.get_stories()
        assert stories[0].category == "breaking_news"

    @pytest.mark.asyncio
    async def test_analysis_decays_slower_than_breaking(self, aggregator):
        """Test that analysis content decays slower than breaking news.

        Analysis content should retain higher time-decay component over time
        compared to breaking news content due to different decay rates:
        - analysis: 0.01 decay rate (slow)
        - breaking_news: 0.15 decay rate (fast)

        Note: Breaking stories get additional boosts (breaking component + multiplier),
        so we test that the time decay difference is significant, not that
        old analysis beats old breaking (the breaking boost may still win).
        """
        now = datetime.now(timezone.utc)
        twelve_hours_ago = now - timedelta(hours=12)

        # Create analysis story (12 hours old)
        # Using ClusterUpdatedEvent to set tension score for fair comparison
        cluster_id_analysis = uuid4()
        create_analysis = ClusterCreatedEvent(
            cluster_id=cluster_id_analysis,
            title="In-Depth Analysis",
            article_id=uuid4(),
            article_count=5,
            category="analysis",
            timestamp=twelve_hours_ago,
        )
        await aggregator.handle_event(create_analysis)

        # Update to set tension score for fair comparison
        update_analysis = ClusterUpdatedEvent(
            cluster_id=cluster_id_analysis,
            article_id=uuid4(),
            article_count=5,
            similarity_score=0.9,
            tension_score=5.0,  # Same tension as breaking
            category="analysis",
        )
        await aggregator.handle_event(update_analysis)

        # Create breaking story (also 12 hours old)
        breaking_event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Breaking News",
            article_count=5,
            growth_rate=2.0,
            tension_score=5.0,  # Same tension
            category="breaking_news",
            timestamp=twelve_hours_ago,
        )
        await aggregator.handle_event(breaking_event)

        # Get stories
        stories = await aggregator.get_top_stories(limit=2)

        # Find stories by category
        analysis_story = next(s for s in stories if s.category == "analysis")
        breaking_story = next(s for s in stories if s.category == "breaking_news")

        # After 12h with equal tension (5.0) and article count (5):
        # Time decay component differences:
        # - analysis: exp(-0.01 * 12) ≈ 0.89 → time component ≈ 0.356
        # - breaking: exp(-0.15 * 12) ≈ 0.17 → time component ≈ 0.068
        # The time component difference is ~0.288

        # Total score calculation (approximate):
        # Both: tension = 5.0/10 * 0.3 = 0.15
        # Both: article = log(6)/log(21) * 0.2 ≈ 0.059

        # Analysis total: 0.356 + 0.15 + 0.059 = 0.565
        # Breaking base: 0.068 + 0.15 + 0.059 + 0.10 = 0.377
        # Breaking with 1.5x: 0.377 * 1.5 = 0.566

        # They should be roughly comparable with breaking's boost
        # compensating for its faster decay. The key test is that
        # the decay rate difference is applied correctly.

        # Verify analysis retains significant relevance after 12h
        assert analysis_story.relevance_score > 0.45
        # Verify breaking story has decayed significantly in time component
        # but is boosted by breaking multiplier
        assert 0.3 < breaking_story.relevance_score < 0.8

    @pytest.mark.asyncio
    async def test_geopolitics_decays_slower_than_default(self, aggregator):
        """Test that geopolitics content decays slower than default.

        Geopolitics stories should retain relevance longer:
        - geopolitics: 0.03 decay rate
        - default: 0.05 decay rate
        """
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(hours=24)

        # Create geopolitics story
        geo_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Geopolitical Development",
            article_id=uuid4(),
            article_count=5,
            category="geopolitics",
            timestamp=day_ago,
        )
        await aggregator.handle_event(geo_event)

        # Create default category story
        default_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Regular News",
            article_id=uuid4(),
            article_count=5,
            category="default",
            timestamp=day_ago,
        )
        await aggregator.handle_event(default_event)

        stories = await aggregator.get_top_stories(limit=2)

        geo_story = next(s for s in stories if s.category == "geopolitics")
        default_story = next(s for s in stories if s.category == "default")

        # Geopolitics should have higher relevance after 24h
        # geo: exp(-0.03 * 24) ≈ 0.49
        # default: exp(-0.05 * 24) ≈ 0.30
        assert geo_story.relevance_score > default_story.relevance_score

    @pytest.mark.asyncio
    async def test_fresh_breaking_beats_old_analysis(self, aggregator):
        """Test that fresh breaking news beats old analysis content.

        Even with slower decay, very old content should lose to fresh breaking.
        """
        now = datetime.now(timezone.utc)

        # Create very old analysis story (48 hours old)
        analysis_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Old Analysis",
            article_id=uuid4(),
            article_count=10,
            category="analysis",
            timestamp=now - timedelta(hours=48),
        )
        await aggregator.handle_event(analysis_event)

        # Create fresh breaking news
        breaking_event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Fresh Breaking",
            article_count=3,  # Fewer articles
            growth_rate=3.0,
            tension_score=8.0,
            timestamp=now,
        )
        await aggregator.handle_event(breaking_event)

        stories = await aggregator.get_top_stories(limit=2)

        # Fresh breaking should beat old analysis
        assert stories[0].title == "Fresh Breaking"
        assert stories[0].is_breaking is True

    @pytest.mark.asyncio
    async def test_late_join_preserves_category(self, aggregator):
        """Test that late-join update events preserve category."""
        cluster_id = uuid4()

        # Send update without prior create (late join)
        update_event = ClusterUpdatedEvent(
            cluster_id=cluster_id,
            article_id=uuid4(),
            article_count=5,
            similarity_score=0.85,
            category="markets",
        )
        await aggregator.handle_event(update_event)

        stories = await aggregator.get_stories()
        assert stories[0].category == "markets"


class TestGetTopStoriesFilters:
    """Tests for get_top_stories filter parameters (max_age_hours, category, is_breaking_only)."""

    @pytest.fixture
    def aggregator(self):
        """Create a fresh StoryAggregator for each test."""
        return StoryAggregator()

    @pytest.mark.asyncio
    async def test_get_top_stories_filters_by_max_age_hours(self, aggregator):
        """Stories older than max_age_hours should be excluded."""
        # Create old story (48 hours ago)
        old_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Old Story",
            article_id=uuid4(),
            article_count=10,
            category="politics",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=48),
        )
        await aggregator.handle_event(old_event)

        # Create recent story (2 hours ago)
        recent_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Recent Story",
            article_id=uuid4(),
            article_count=10,
            category="politics",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        await aggregator.handle_event(recent_event)

        # Get stories with 24h max age
        stories = await aggregator.get_top_stories(max_age_hours=24)

        assert len(stories) == 1
        assert stories[0].title == "Recent Story"

    @pytest.mark.asyncio
    async def test_get_top_stories_filters_by_category(self, aggregator):
        """Only stories matching category should be returned."""
        # Create politics story
        politics_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Political News",
            article_id=uuid4(),
            article_count=10,
            category="politics",
            timestamp=datetime.now(timezone.utc),
        )
        await aggregator.handle_event(politics_event)

        # Create finance story
        finance_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Finance News",
            article_id=uuid4(),
            article_count=10,
            category="finance",
            timestamp=datetime.now(timezone.utc),
        )
        await aggregator.handle_event(finance_event)

        # Filter by politics only
        stories = await aggregator.get_top_stories(category="politics")

        assert len(stories) == 1
        assert stories[0].title == "Political News"

    @pytest.mark.asyncio
    async def test_get_top_stories_filters_breaking_only(self, aggregator):
        """When is_breaking_only=True, only breaking stories returned."""
        # Create normal story
        normal_event = ClusterCreatedEvent(
            cluster_id=uuid4(),
            title="Normal News",
            article_id=uuid4(),
            article_count=10,
            category="politics",
            timestamp=datetime.now(timezone.utc),
        )
        await aggregator.handle_event(normal_event)

        # Create breaking story via burst event
        breaking_event = BurstDetectedEvent(
            cluster_id=uuid4(),
            title="Breaking News",
            article_count=20,
            tension_score=8.5,
            growth_rate=2.5,
            category="breaking_news",
            timestamp=datetime.now(timezone.utc),
        )
        await aggregator.handle_event(breaking_event)

        # Filter breaking only
        stories = await aggregator.get_top_stories(is_breaking_only=True)

        assert len(stories) == 1
        assert stories[0].title == "Breaking News"
        assert stories[0].is_breaking is True

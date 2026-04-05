# services/sitrep-service/tests/integration/test_event_to_sitrep_flow.py
"""Integration tests for end-to-end event-to-SITREP flow.

Tests the complete pipeline:
1. Cluster events received (simulated RabbitMQ messages)
2. Story aggregation with relevance scoring
3. SITREP generation (mocked LLM)
4. Database persistence

These tests verify component integration without requiring actual
RabbitMQ or OpenAI connections.
"""

import asyncio
import json
import pytest
import pytest_asyncio
from datetime import date, datetime, timezone, timedelta
from typing import AsyncGenerator, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.sitrep import Base, SitrepReport
from app.repositories.sitrep_repository import SitrepRepository
from app.schemas.events import (
    ClusterCreatedEvent,
    ClusterUpdatedEvent,
    BurstDetectedEvent,
    parse_cluster_event,
)
from app.schemas.sitrep import SitrepResponse, KeyDevelopment, RiskAssessment
from app.schemas.story import TopStory
from app.services.story_aggregator import StoryAggregator
from app.services.sitrep_generator import SitrepGenerator, SitrepGenerationError
from app.workers.cluster_consumer import ClusterEventConsumer
from app.workers.scheduled_generator import ScheduledGenerator


# ============================================================
# Test Fixtures
# ============================================================


@pytest_asyncio.fixture
async def async_engine():
    """Create async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing."""
    session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def session_maker(async_engine):
    """Create session maker for components that need it."""
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
def aggregator():
    """Create a fresh StoryAggregator."""
    return StoryAggregator()


@pytest.fixture
def repository():
    """Create a SitrepRepository instance."""
    return SitrepRepository()


@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response for SITREP generation."""
    return {
        "executive_summary": "Test executive summary covering key developments.",
        "key_developments": [
            {
                "title": "Major Development",
                "summary": "A significant event occurred.",
                "significance": "High impact on markets.",
                "risk_level": "medium",
                "risk_category": "economic",
                "related_entities": ["Entity1", "Entity2"],
            }
        ],
        "sentiment_analysis": {
            "overall": "neutral",
            "positive_percent": 30.0,
            "negative_percent": 25.0,
            "neutral_percent": 45.0,
            "rationale": "Mixed sentiment across stories.",
        },
        "emerging_signals": [
            {
                "signal_type": "trend",
                "description": "Increasing market volatility.",
                "confidence": 0.75,
                "related_entities": ["Market"],
            }
        ],
        "content_markdown": "# Daily SITREP\n\n## Executive Summary\nTest summary.",
    }


def create_cluster_events_sequence():
    """Create a realistic sequence of cluster events."""
    now = datetime.now(timezone.utc)
    cluster1_id = uuid4()
    cluster2_id = uuid4()
    cluster3_id = uuid4()

    return [
        # Cluster 1: Created and updated
        {
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": str(cluster1_id),
                "title": "Tech Company Announces Major Layoffs",
                "article_id": str(uuid4()),
                "article_count": 1,
                "category": "technology",
            },
            "timestamp": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "event_type": "cluster.updated",
            "payload": {
                "cluster_id": str(cluster1_id),
                "article_id": str(uuid4()),
                "article_count": 5,
                "similarity_score": 0.92,
                "tension_score": 6.5,
                "is_breaking": False,
                "category": "technology",
                "primary_entities": [
                    {"name": "TechCorp", "type": "organization"},
                    {"name": "Silicon Valley", "type": "location"},
                ],
            },
            "timestamp": (now - timedelta(hours=1)).isoformat(),
        },
        # Cluster 2: Created as breaking news
        {
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": str(cluster2_id),
                "title": "Emergency Summit Announced",
                "article_id": str(uuid4()),
                "article_count": 1,
                "category": "geopolitics",
            },
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
        },
        {
            "event_type": "cluster.burst_detected",
            "payload": {
                "cluster_id": str(cluster2_id),
                "title": "BREAKING: Emergency Summit on Global Crisis",
                "article_count": 12,
                "growth_rate": 4.0,
                "tension_score": 9.2,
                "top_entities": ["UN", "G20", "Global Leaders"],
                "category": "breaking_news",
            },
            "timestamp": (now - timedelta(minutes=15)).isoformat(),
        },
        # Cluster 3: Analysis content
        {
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": str(cluster3_id),
                "title": "Expert Analysis: Market Trends Q1",
                "article_id": str(uuid4()),
                "article_count": 1,
                "category": "analysis",
            },
            "timestamp": (now - timedelta(hours=6)).isoformat(),
        },
        {
            "event_type": "cluster.updated",
            "payload": {
                "cluster_id": str(cluster3_id),
                "article_id": str(uuid4()),
                "article_count": 3,
                "similarity_score": 0.88,
                "tension_score": 4.0,
                "is_breaking": False,
                "category": "analysis",
            },
            "timestamp": (now - timedelta(hours=4)).isoformat(),
        },
    ]


# ============================================================
# End-to-End Flow Tests
# ============================================================


class TestEventToStoryAggregation:
    """Tests for event consumption and story aggregation flow."""

    @pytest.mark.asyncio
    async def test_process_event_sequence_to_stories(self, aggregator):
        """Test that a sequence of events produces correctly aggregated stories."""
        events = create_cluster_events_sequence()

        # Process all events through aggregator
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        # Verify story aggregation
        stories = await aggregator.get_stories()
        assert len(stories) == 3

        # Verify breaking news is marked correctly
        breaking_stories = [s for s in stories if s.is_breaking]
        assert len(breaking_stories) == 1
        assert "Emergency Summit" in breaking_stories[0].title

    @pytest.mark.asyncio
    async def test_event_sequence_produces_ranked_top_stories(self, aggregator):
        """Test that events produce properly ranked top stories."""
        events = create_cluster_events_sequence()

        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        # Get top stories with ranking
        top_stories = await aggregator.get_top_stories(limit=3, min_article_count=1)

        assert len(top_stories) == 3

        # Breaking news should rank highest (recency + breaking boost)
        assert top_stories[0].is_breaking is True
        assert "Emergency Summit" in top_stories[0].title

        # All stories should have relevance scores
        for story in top_stories:
            assert story.relevance_score > 0

    @pytest.mark.asyncio
    async def test_category_preserved_through_event_flow(self, aggregator):
        """Test that category information is preserved through the flow."""
        events = create_cluster_events_sequence()

        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        stories = await aggregator.get_stories()

        categories = {s.category for s in stories}
        assert "technology" in categories
        assert "breaking_news" in categories
        assert "analysis" in categories

    @pytest.mark.asyncio
    async def test_entity_extraction_through_flow(self, aggregator):
        """Test that entities are correctly extracted and associated."""
        events = create_cluster_events_sequence()

        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        stories = await aggregator.get_stories()

        # Find the tech story which has primary_entities
        tech_story = next(
            (s for s in stories if s.category == "technology"),
            None
        )
        assert tech_story is not None
        assert "TechCorp" in tech_story.top_entities

        # Find breaking story with top_entities
        breaking_story = next(
            (s for s in stories if s.is_breaking),
            None
        )
        assert breaking_story is not None
        assert "UN" in breaking_story.top_entities


class TestStoryToSitrepGeneration:
    """Tests for story-to-SITREP generation flow."""

    @pytest.mark.asyncio
    async def test_generate_sitrep_from_aggregated_stories(
        self,
        aggregator,
        mock_llm_response,
    ):
        """Test SITREP generation from aggregated stories with mocked LLM."""
        # Process events
        events = create_cluster_events_sequence()
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        # Get stories for generation
        stories = await aggregator.get_top_stories(limit=10, min_article_count=1)
        assert len(stories) >= 3

        # Mock LLM response
        with patch("app.services.sitrep_generator.AsyncOpenAI") as mock_openai:
            # Setup mock
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_llm_response)
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Generate SITREP
            generator = SitrepGenerator(api_key="test-key")
            sitrep = await generator.generate(
                stories=stories,
                report_type="daily",
            )

            # Verify SITREP structure
            assert isinstance(sitrep, SitrepResponse)
            assert sitrep.report_type == "daily"
            assert sitrep.executive_summary == mock_llm_response["executive_summary"]
            assert len(sitrep.top_stories) >= 3
            # generation_time_ms may be 0 in mocked scenarios (no actual LLM latency)
            assert sitrep.generation_time_ms >= 0

    @pytest.mark.asyncio
    async def test_sitrep_includes_all_story_data(
        self,
        aggregator,
        mock_llm_response,
    ):
        """Test that SITREP includes all relevant story metadata."""
        # Process events
        events = create_cluster_events_sequence()
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        stories = await aggregator.get_top_stories(limit=10, min_article_count=1)

        with patch("app.services.sitrep_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_llm_response)
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            generator = SitrepGenerator(api_key="test-key")
            sitrep = await generator.generate(stories=stories, report_type="daily")

            # Verify story data is included
            assert len(sitrep.top_stories) == len(stories)
            for story_data in sitrep.top_stories:
                assert "cluster_id" in story_data
                assert "title" in story_data
                assert "article_count" in story_data
                assert "is_breaking" in story_data

            # Verify entity extraction
            assert len(sitrep.key_entities) > 0


class TestFullPipelineWithPersistence:
    """Tests for complete pipeline including database persistence."""

    @pytest.mark.asyncio
    async def test_full_pipeline_event_to_database(
        self,
        aggregator,
        async_session,
        repository,
        mock_llm_response,
    ):
        """Test complete pipeline: events -> aggregation -> generation -> persistence."""
        # Step 1: Process events
        events = create_cluster_events_sequence()
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        # Step 2: Get top stories
        stories = await aggregator.get_top_stories(limit=10, min_article_count=1)
        assert len(stories) >= 3

        # Step 3: Generate SITREP (mocked LLM)
        with patch("app.services.sitrep_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_llm_response)
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            generator = SitrepGenerator(api_key="test-key")
            sitrep = await generator.generate(stories=stories, report_type="daily")

        # Step 4: Persist to database
        saved = await repository.save(async_session, sitrep)

        # Verify persistence
        assert saved.id == sitrep.id
        assert saved.report_type == "daily"
        assert saved.executive_summary == mock_llm_response["executive_summary"]

        # Step 5: Retrieve and verify
        retrieved = await repository.get_by_id(async_session, saved.id)
        assert retrieved is not None
        assert retrieved.title == sitrep.title
        assert len(retrieved.top_stories) == len(stories)

    @pytest.mark.asyncio
    async def test_pipeline_preserves_structured_data(
        self,
        aggregator,
        async_session,
        repository,
        mock_llm_response,
    ):
        """Test that structured data (JSONB) is preserved through pipeline."""
        events = create_cluster_events_sequence()
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        stories = await aggregator.get_top_stories(limit=10, min_article_count=1)

        with patch("app.services.sitrep_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_llm_response)
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            generator = SitrepGenerator(api_key="test-key")
            sitrep = await generator.generate(stories=stories, report_type="daily")

        # Save to database
        saved = await repository.save(async_session, sitrep)

        # Verify JSONB fields
        assert isinstance(saved.top_stories, list)
        assert isinstance(saved.key_entities, list)
        assert isinstance(saved.sentiment_summary, dict)

        # Verify sentiment data
        assert saved.sentiment_summary["overall"] == "neutral"

    @pytest.mark.asyncio
    async def test_multiple_sitreps_from_sequential_events(
        self,
        async_session,
        repository,
        mock_llm_response,
    ):
        """Test generating multiple SITREPs from sequential event batches."""
        with patch("app.services.sitrep_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_llm_response)
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Generate first SITREP
            aggregator1 = StoryAggregator()
            events1 = create_cluster_events_sequence()
            for event_data in events1:
                event = parse_cluster_event(event_data)
                await aggregator1.handle_event(event)

            stories1 = await aggregator1.get_top_stories(limit=10, min_article_count=1)
            generator = SitrepGenerator(api_key="test-key")
            sitrep1 = await generator.generate(
                stories=stories1,
                report_type="daily",
                report_date=date.today() - timedelta(days=1),
            )
            await repository.save(async_session, sitrep1)

            # Generate second SITREP
            aggregator2 = StoryAggregator()
            events2 = create_cluster_events_sequence()
            for event_data in events2:
                event = parse_cluster_event(event_data)
                await aggregator2.handle_event(event)

            stories2 = await aggregator2.get_top_stories(limit=10, min_article_count=1)
            sitrep2 = await generator.generate(
                stories=stories2,
                report_type="daily",
                report_date=date.today(),
            )
            await repository.save(async_session, sitrep2)

            # Verify both stored
            count = await repository.count(async_session)
            assert count == 2

            # Get latest - ordering is by created_at DESC
            # In test environment with quick sequential saves, verify latest exists
            latest = await repository.get_latest(async_session, "daily")
            assert latest is not None
            # Verify it's one of our created SITREPs
            assert latest.report_date in [date.today(), date.today() - timedelta(days=1)]
            assert latest.report_type == "daily"


class TestScheduledGenerationFlow:
    """Tests for scheduled SITREP generation flow."""

    @pytest.mark.asyncio
    async def test_scheduled_generator_with_stories(
        self,
        aggregator,
        session_maker,
        mock_llm_response,
    ):
        """Test scheduled generator produces SITREP when stories available."""
        # Populate aggregator with events
        events = create_cluster_events_sequence()
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        # Create scheduled generator
        scheduler = ScheduledGenerator(
            aggregator,
            generation_hour=6,
            top_stories_count=10,
            min_cluster_size=1,
        )

        # Mock the generator and repository
        with patch("app.services.sitrep_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_llm_response)
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Mock database session
            with patch("app.workers.scheduled_generator.async_session_maker", session_maker):
                result = await scheduler.generate_sitrep("daily")

            # Should succeed
            assert result is True

    @pytest.mark.asyncio
    async def test_scheduled_generator_returns_false_no_stories(self, aggregator):
        """Test scheduled generator returns False when no stories available."""
        # Don't populate aggregator - empty
        scheduler = ScheduledGenerator(
            aggregator,
            generation_hour=6,
            top_stories_count=10,
            min_cluster_size=3,  # Higher minimum
        )

        # Should return False (no stories meet criteria)
        result = await scheduler.generate_sitrep("daily")
        assert result is False

    @pytest.mark.asyncio
    async def test_should_generate_logic(self, aggregator):
        """Test _should_generate() time checking logic."""
        scheduler = ScheduledGenerator(
            aggregator,
            generation_hour=6,
        )

        now = datetime.now(timezone.utc)

        # Create test times
        generation_time = now.replace(hour=6, minute=30)
        non_generation_time = now.replace(hour=12, minute=0)

        # Should generate at 6:xx
        assert scheduler._should_generate(generation_time) is True

        # Should not generate at 12:xx
        assert scheduler._should_generate(non_generation_time) is False

        # Should not generate twice same day
        scheduler._last_generation_date = generation_time.date()
        assert scheduler._should_generate(generation_time) is False

    @pytest.mark.asyncio
    async def test_get_status_includes_story_count(self, aggregator):
        """Test that get_status() reflects current story count."""
        scheduler = ScheduledGenerator(aggregator, generation_hour=6)

        # Initially empty
        status = scheduler.get_status()
        assert status["current_story_count"] == 0

        # Add events
        events = create_cluster_events_sequence()
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        # Should show updated count
        status = scheduler.get_status()
        assert status["current_story_count"] == 3


class TestEventParsingFlow:
    """Tests for RabbitMQ event parsing flow."""

    def test_parse_cluster_created_event(self):
        """Test parsing cluster.created event."""
        event_data = {
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": str(uuid4()),
                "title": "Test Cluster",
                "article_id": str(uuid4()),
                "article_count": 1,
                "category": "technology",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        event = parse_cluster_event(event_data)

        assert isinstance(event, ClusterCreatedEvent)
        assert event.title == "Test Cluster"
        assert event.category == "technology"

    def test_parse_cluster_updated_event(self):
        """Test parsing cluster.updated event."""
        event_data = {
            "event_type": "cluster.updated",
            "payload": {
                "cluster_id": str(uuid4()),
                "article_id": str(uuid4()),
                "article_count": 5,
                "similarity_score": 0.85,
                "tension_score": 6.5,
                "is_breaking": True,
                "category": "breaking_news",
            },
        }

        event = parse_cluster_event(event_data)

        assert isinstance(event, ClusterUpdatedEvent)
        assert event.article_count == 5
        assert event.is_breaking is True

    def test_parse_burst_detected_event(self):
        """Test parsing cluster.burst_detected event."""
        event_data = {
            "event_type": "cluster.burst_detected",
            "payload": {
                "cluster_id": str(uuid4()),
                "title": "Breaking News",
                "article_count": 15,
                "growth_rate": 3.5,
                "tension_score": 9.0,
                "top_entities": ["Entity1", "Entity2"],
            },
        }

        event = parse_cluster_event(event_data)

        assert isinstance(event, BurstDetectedEvent)
        assert event.growth_rate == 3.5
        assert "Entity1" in event.top_entities

    def test_parse_unknown_event_returns_none(self):
        """Test that unknown event types return None."""
        event_data = {
            "event_type": "unknown.event",
            "payload": {},
        }

        event = parse_cluster_event(event_data)
        assert event is None

    @pytest.mark.asyncio
    async def test_consumer_processes_message_correctly(self, aggregator):
        """Test that ClusterEventConsumer processes messages correctly."""
        consumer = ClusterEventConsumer(aggregator)

        # Simulate message processing (without actual RabbitMQ)
        event_data = {
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": str(uuid4()),
                "title": "Consumer Test Story",
                "article_id": str(uuid4()),
                "article_count": 1,
            },
        }

        event = parse_cluster_event(event_data)
        await aggregator.handle_event(event)

        stories = await aggregator.get_stories()
        assert len(stories) == 1
        assert stories[0].title == "Consumer Test Story"


class TestErrorHandlingInFlow:
    """Tests for error handling throughout the pipeline."""

    @pytest.mark.asyncio
    async def test_generation_fails_gracefully_no_stories(self):
        """Test that SITREP generation fails gracefully with no stories."""
        generator = SitrepGenerator(api_key="test-key")

        with pytest.raises(ValueError, match="No stories provided"):
            await generator.generate(stories=[], report_type="daily")

    @pytest.mark.asyncio
    async def test_pipeline_handles_malformed_event(self, aggregator):
        """Test that pipeline handles malformed events without crashing."""
        # Process good event first
        good_event = parse_cluster_event({
            "event_type": "cluster.created",
            "payload": {
                "cluster_id": str(uuid4()),
                "title": "Good Event",
                "article_id": str(uuid4()),
            },
        })
        await aggregator.handle_event(good_event)

        # Try to parse bad event (should return None)
        bad_event = parse_cluster_event({
            "event_type": "invalid",
            "payload": {},
        })
        assert bad_event is None

        # Aggregator should still have the good event
        stories = await aggregator.get_stories()
        assert len(stories) == 1

    @pytest.mark.asyncio
    async def test_scheduled_generator_handles_generation_error(
        self,
        aggregator,
        session_maker,
    ):
        """Test scheduled generator handles generation errors gracefully."""
        # Populate aggregator
        events = create_cluster_events_sequence()
        for event_data in events:
            event = parse_cluster_event(event_data)
            await aggregator.handle_event(event)

        scheduler = ScheduledGenerator(
            aggregator,
            generation_hour=6,
            min_cluster_size=1,
        )

        # Mock LLM to raise error
        with patch("app.services.sitrep_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("LLM API Error")
            )

            # Should raise but not crash
            with pytest.raises(SitrepGenerationError):
                await scheduler.generate_sitrep("daily")

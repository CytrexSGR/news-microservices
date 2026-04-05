# services/sitrep-service/tests/test_sitrep_generator.py
"""Tests for SITREP generator.

Tests the SitrepGenerator which:
- Takes top stories from StoryAggregator
- Generates intelligence briefings using OpenAI GPT-4
- Returns structured SITREP with executive summary, key developments, risk assessment

Tests cover:
- Prompt building with story data
- Entity extraction from stories
- LLM response parsing
- Error handling for API failures
- Token management
"""

import pytest
from datetime import datetime, timezone, date
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.sitrep_generator import SitrepGenerator, SitrepGenerationError
from app.schemas.story import TopStory


class TestSitrepGenerator:
    """Tests for SitrepGenerator service."""

    @pytest.fixture
    def generator(self):
        """Create a SitrepGenerator instance with test API key."""
        return SitrepGenerator(api_key="test-api-key")

    @pytest.fixture
    def sample_stories(self):
        """Create sample stories for testing."""
        now = datetime.now(timezone.utc)
        return [
            TopStory(
                cluster_id=uuid4(),
                title="Major Economic Policy Announced",
                article_count=15,
                first_seen_at=now,
                last_updated_at=now,
                tension_score=8.5,
                relevance_score=0.9,
                is_breaking=True,
                category="breaking_news",
                top_entities=["Federal Reserve", "Jerome Powell", "USD"],
            ),
            TopStory(
                cluster_id=uuid4(),
                title="Tech Company Reports Earnings",
                article_count=8,
                first_seen_at=now,
                last_updated_at=now,
                tension_score=5.0,
                relevance_score=0.7,
                is_breaking=False,
                category="markets",
                top_entities=["Apple Inc", "Tim Cook", "NASDAQ"],
            ),
            TopStory(
                cluster_id=uuid4(),
                title="Geopolitical Tensions in Eastern Europe",
                article_count=12,
                first_seen_at=now,
                last_updated_at=now,
                tension_score=9.0,
                relevance_score=0.85,
                is_breaking=False,
                category="geopolitics",
                top_entities=["NATO", "European Union", "Ukraine"],
            ),
        ]

    def test_build_prompt_includes_stories(self, generator, sample_stories):
        """Test that prompt includes all stories."""
        prompt = generator.build_prompt(sample_stories)

        # All story titles should be in prompt
        assert "Major Economic Policy Announced" in prompt
        assert "Tech Company Reports Earnings" in prompt
        assert "Geopolitical Tensions in Eastern Europe" in prompt

        # Key entities should be included
        assert "Federal Reserve" in prompt
        assert "Apple Inc" in prompt
        assert "NATO" in prompt

    def test_build_prompt_marks_breaking_news(self, generator, sample_stories):
        """Test that breaking news is marked in prompt."""
        prompt = generator.build_prompt(sample_stories)

        assert "[BREAKING NEWS]" in prompt

    def test_build_prompt_includes_statistics(self, generator, sample_stories):
        """Test that prompt includes summary statistics."""
        prompt = generator.build_prompt(sample_stories)

        # Should include cluster count
        assert "Total Clusters: 3" in prompt
        # Should include total article count (15 + 8 + 12 = 35)
        assert "Total Articles: 35" in prompt
        # Should include breaking news count
        assert "Breaking News Items: 1" in prompt

    def test_build_prompt_includes_tension_scores(self, generator, sample_stories):
        """Test that tension scores are included in prompt."""
        prompt = generator.build_prompt(sample_stories)

        assert "Tension Score: 8.5/10" in prompt
        assert "Tension Score: 5.0/10" in prompt
        assert "Tension Score: 9.0/10" in prompt

    def test_build_prompt_includes_categories(self, generator, sample_stories):
        """Test that categories are included in prompt."""
        prompt = generator.build_prompt(sample_stories)

        assert "[BREAKING_NEWS]" in prompt
        assert "Category: markets" in prompt
        assert "Category: geopolitics" in prompt

    def test_build_prompt_includes_json_instructions(self, generator, sample_stories):
        """Test that JSON output instructions are included."""
        prompt = generator.build_prompt(sample_stories)

        assert "JSON" in prompt
        assert "executive_summary" in prompt
        assert "key_developments" in prompt
        assert "sentiment_analysis" in prompt

    def test_extract_entities_from_stories(self, generator, sample_stories):
        """Test entity extraction from stories."""
        entities = generator.extract_entities(sample_stories)

        # Should extract all unique entities
        assert "Federal Reserve" in entities
        assert "Jerome Powell" in entities
        assert "Apple Inc" in entities
        assert "Tim Cook" in entities
        assert "NATO" in entities
        assert "Ukraine" in entities

        # Should be sorted
        assert entities == sorted(entities)

    def test_extract_entities_deduplicates(self, generator):
        """Test that entity extraction removes duplicates."""
        now = datetime.now(timezone.utc)
        stories = [
            TopStory(
                cluster_id=uuid4(),
                title="Story 1",
                article_count=5,
                first_seen_at=now,
                last_updated_at=now,
                top_entities=["Entity A", "Entity B"],
            ),
            TopStory(
                cluster_id=uuid4(),
                title="Story 2",
                article_count=5,
                first_seen_at=now,
                last_updated_at=now,
                top_entities=["Entity A", "Entity C"],  # Entity A is duplicate
            ),
        ]

        entities = generator.extract_entities(stories)

        # Should have 3 unique entities, not 4
        assert len(entities) == 3
        assert entities.count("Entity A") == 1

    def test_extract_entities_handles_empty_stories(self, generator):
        """Test entity extraction with no stories."""
        entities = generator.extract_entities([])
        assert entities == []

    @pytest.mark.asyncio
    async def test_generate_returns_valid_sitrep(self, generator, sample_stories):
        """Test that generate returns valid SITREP structure."""
        # Mock OpenAI response
        mock_response = {
            "content": {
                "executive_summary": "Major economic developments today with Federal Reserve policy changes and tech earnings reports.",
                "key_developments": [
                    {
                        "title": "Major Economic Policy Announced",
                        "summary": "The Federal Reserve announced significant policy changes.",
                        "significance": "This will impact global markets.",
                        "risk_level": "high",
                        "risk_category": "economic",
                        "related_entities": ["Federal Reserve", "Jerome Powell"],
                    },
                    {
                        "title": "Tech Company Reports Earnings",
                        "summary": "Apple Inc reported quarterly earnings.",
                        "significance": "Signals tech sector health.",
                        "risk_level": "medium",
                        "risk_category": "economic",
                        "related_entities": ["Apple Inc", "Tim Cook"],
                    },
                ],
                "sentiment_analysis": {
                    "overall": "mixed",
                    "positive_percent": 40.0,
                    "negative_percent": 30.0,
                    "neutral_percent": 30.0,
                    "rationale": "Mixed signals from economic and tech sectors.",
                },
                "emerging_signals": [
                    {
                        "signal_type": "trend",
                        "description": "Increased volatility expected in tech sector",
                        "confidence": 0.75,
                        "related_entities": ["NASDAQ"],
                    }
                ],
                "content_markdown": "# Daily Intelligence Briefing\n\n## Executive Summary\nMajor economic developments today...",
            },
            "usage": {
                "prompt_tokens": 500,
                "completion_tokens": 800,
                "total_tokens": 1300,
            },
        }

        with patch.object(generator, "_call_llm", return_value=mock_response):
            result = await generator.generate(
                stories=sample_stories,
                report_type="daily",
            )

        # Verify structure
        assert result is not None
        assert result.report_type == "daily"
        assert result.executive_summary == mock_response["content"]["executive_summary"]
        assert "Executive Summary" in result.content_markdown

        # Verify top stories
        assert len(result.top_stories) == 3
        assert result.top_stories[0]["title"] == "Major Economic Policy Announced"

        # Verify key developments
        assert len(result.key_developments) == 2
        assert result.key_developments[0].title == "Major Economic Policy Announced"
        assert result.key_developments[0].risk_assessment is not None
        assert result.key_developments[0].risk_assessment.level == "high"

        # Verify sentiment
        assert result.sentiment_summary["overall"] == "mixed"
        assert result.sentiment_summary["positive_percent"] == 40.0

        # Verify emerging signals
        assert result.emerging_signals is not None
        assert len(result.emerging_signals) == 1
        assert result.emerging_signals[0]["signal_type"] == "trend"

        # Verify token tracking
        assert result.prompt_tokens == 500
        assert result.completion_tokens == 800

        # Verify article count
        assert result.articles_analyzed == 35  # 15 + 8 + 12

    @pytest.mark.asyncio
    async def test_generate_raises_on_empty_stories(self, generator):
        """Test that generate raises ValueError for empty stories."""
        with pytest.raises(ValueError, match="No stories provided"):
            await generator.generate(stories=[], report_type="daily")

    @pytest.mark.asyncio
    async def test_generate_uses_provided_date(self, generator, sample_stories):
        """Test that generate uses provided report_date."""
        mock_response = {
            "content": {
                "executive_summary": "Test summary",
                "key_developments": [],
                "sentiment_analysis": {"overall": "neutral"},
                "emerging_signals": [],
                "content_markdown": "# Test",
            },
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

        custom_date = date(2026, 1, 1)

        with patch.object(generator, "_call_llm", return_value=mock_response):
            result = await generator.generate(
                stories=sample_stories,
                report_type="daily",
                report_date=custom_date,
            )

        assert result.report_date == custom_date
        assert "2026-01-01" in result.title

    @pytest.mark.asyncio
    async def test_generate_handles_llm_error(self, generator, sample_stories):
        """Test that generate raises SitrepGenerationError on LLM failure."""
        with patch.object(
            generator,
            "_call_llm",
            side_effect=SitrepGenerationError("API error"),
        ):
            with pytest.raises(SitrepGenerationError, match="API error"):
                await generator.generate(stories=sample_stories, report_type="daily")

    @pytest.mark.asyncio
    async def test_generate_calculates_generation_time(self, generator, sample_stories):
        """Test that generation time is calculated."""
        import asyncio

        mock_response = {
            "content": {
                "executive_summary": "Test",
                "key_developments": [],
                "sentiment_analysis": {"overall": "neutral"},
                "emerging_signals": [],
                "content_markdown": "# Test",
            },
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

        async def delayed_response(*args, **kwargs):
            """Simulate LLM latency."""
            await asyncio.sleep(0.01)  # 10ms delay
            return mock_response

        with patch.object(generator, "_call_llm", side_effect=delayed_response):
            result = await generator.generate(
                stories=sample_stories,
                report_type="daily",
            )

        # Should have a positive generation time (at least 10ms from delay)
        assert result.generation_time_ms >= 10

    def test_build_prompt_different_report_types(self, generator, sample_stories):
        """Test prompt building for different report types."""
        daily_prompt = generator.build_prompt(sample_stories, report_type="daily")
        weekly_prompt = generator.build_prompt(sample_stories, report_type="weekly")
        breaking_prompt = generator.build_prompt(sample_stories, report_type="breaking")

        assert "DAILY SITREP" in daily_prompt
        assert "WEEKLY SITREP" in weekly_prompt
        assert "BREAKING SITREP" in breaking_prompt

    def test_build_prompt_includes_growth_rate(self, generator):
        """Test that growth rate is included when present."""
        now = datetime.now(timezone.utc)
        stories = [
            TopStory(
                cluster_id=uuid4(),
                title="Breaking Story",
                article_count=20,
                first_seen_at=now,
                last_updated_at=now,
                growth_rate=3.5,
            ),
        ]

        prompt = generator.build_prompt(stories)

        assert "Growth Rate: 3.5x" in prompt


class TestSitrepGeneratorAPIIntegration:
    """Tests for SitrepGenerator API integration (mocked)."""

    @pytest.fixture
    def generator(self):
        """Create a SitrepGenerator instance."""
        return SitrepGenerator(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_call_llm_parses_json_response(self, generator):
        """Test that _call_llm parses JSON response correctly."""
        mock_message = MagicMock()
        mock_message.content = '{"executive_summary": "Test", "key_developments": []}'

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.object(generator, "_client", mock_client):
            result = await generator._call_llm("Test prompt")

        assert result["content"]["executive_summary"] == "Test"
        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 50

    @pytest.mark.asyncio
    async def test_call_llm_raises_on_invalid_json(self, generator):
        """Test that _call_llm raises error on invalid JSON."""
        mock_message = MagicMock()
        mock_message.content = "This is not JSON"

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.object(generator, "_client", mock_client):
            with pytest.raises(SitrepGenerationError, match="Invalid JSON"):
                await generator._call_llm("Test prompt")


class TestKeyDevelopmentParsing:
    """Tests for key development parsing."""

    @pytest.fixture
    def generator(self):
        """Create a SitrepGenerator instance."""
        return SitrepGenerator(api_key="test-api-key")

    @pytest.fixture
    def sample_stories(self):
        """Create sample stories for testing."""
        now = datetime.now(timezone.utc)
        return [
            TopStory(
                cluster_id=uuid4(),
                title="Economic Policy Change",
                article_count=10,
                first_seen_at=now,
                last_updated_at=now,
            ),
        ]

    def test_parse_key_developments_creates_risk_assessment(self, generator, sample_stories):
        """Test that risk assessment is created from development data."""
        developments_data = [
            {
                "title": "Economic Policy Change",
                "summary": "Major policy shift",
                "significance": "Market impact expected",
                "risk_level": "high",
                "risk_category": "economic",
                "related_entities": ["Federal Reserve"],
            }
        ]

        developments = generator._parse_key_developments(developments_data, sample_stories)

        assert len(developments) == 1
        assert developments[0].title == "Economic Policy Change"
        assert developments[0].risk_assessment is not None
        assert developments[0].risk_assessment.level == "high"
        assert developments[0].risk_assessment.category == "economic"

    def test_parse_key_developments_limits_to_five(self, generator, sample_stories):
        """Test that only top 5 developments are parsed."""
        developments_data = [
            {"title": f"Development {i}", "summary": "Test", "significance": "Test"}
            for i in range(10)
        ]

        developments = generator._parse_key_developments(developments_data, sample_stories)

        assert len(developments) == 5

    def test_parse_key_developments_handles_missing_fields(self, generator, sample_stories):
        """Test parsing with missing optional fields."""
        developments_data = [
            {
                "title": "Minimal Development",
                # Missing summary, significance, risk_level, etc.
            }
        ]

        developments = generator._parse_key_developments(developments_data, sample_stories)

        assert len(developments) == 1
        assert developments[0].title == "Minimal Development"
        assert developments[0].summary == ""
        assert developments[0].risk_assessment is None

    def test_parse_key_developments_matches_cluster_ids(self, generator):
        """Test that cluster IDs are matched to developments."""
        now = datetime.now(timezone.utc)
        cluster_id = uuid4()
        stories = [
            TopStory(
                cluster_id=cluster_id,
                title="Specific Story Title",
                article_count=10,
                first_seen_at=now,
                last_updated_at=now,
            ),
        ]

        developments_data = [
            {
                "title": "Specific Story Title",  # Matches story title
                "summary": "Test",
                "significance": "Test",
            }
        ]

        developments = generator._parse_key_developments(developments_data, stories)

        assert len(developments) == 1
        assert developments[0].source_cluster_id == cluster_id


class TestGenerateSummaryOnly:
    """Tests for summary-only generation."""

    @pytest.fixture
    def generator(self):
        """Create a SitrepGenerator instance."""
        return SitrepGenerator(api_key="test-api-key")

    @pytest.fixture
    def sample_stories(self):
        """Create sample stories for testing."""
        now = datetime.now(timezone.utc)
        return [
            TopStory(
                cluster_id=uuid4(),
                title="Story One",
                article_count=10,
                first_seen_at=now,
                last_updated_at=now,
                is_breaking=True,
            ),
            TopStory(
                cluster_id=uuid4(),
                title="Story Two",
                article_count=5,
                first_seen_at=now,
                last_updated_at=now,
                is_breaking=False,
            ),
        ]

    @pytest.mark.asyncio
    async def test_generate_summary_only_returns_string(self, generator, sample_stories):
        """Test that generate_summary_only returns a string."""
        mock_message = MagicMock()
        mock_message.content = "This is a test summary of the top news stories."

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.object(generator, "_client", mock_client):
            result = await generator.generate_summary_only(sample_stories)

        assert isinstance(result, str)
        assert result == "This is a test summary of the top news stories."

    @pytest.mark.asyncio
    async def test_generate_summary_only_handles_empty_stories(self, generator):
        """Test summary generation with no stories."""
        result = await generator.generate_summary_only([])

        assert "No stories available" in result

    @pytest.mark.asyncio
    async def test_generate_summary_only_handles_error(self, generator, sample_stories):
        """Test that generate_summary_only handles errors gracefully."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with patch.object(generator, "_client", mock_client):
            result = await generator.generate_summary_only(sample_stories)

        assert "failed" in result.lower()

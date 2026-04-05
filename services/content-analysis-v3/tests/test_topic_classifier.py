"""
Tests for TOPIC_CLASSIFIER Specialist
"""

import pytest
from uuid import uuid4

from app.pipeline.tier2.specialists.topic_classifier import TopicClassifierSpecialist
from app.models.schemas import Tier1Results, Topic
from app.pipeline.tier2.models import SpecialistType


@pytest.fixture
def specialist():
    """Create TopicClassifierSpecialist instance."""
    return TopicClassifierSpecialist()


@pytest.fixture
def sample_tier1_results():
    """Sample Tier1Results with topics."""
    return Tier1Results(
        entities=[],
        relations=[],
        topics=[
            Topic(keyword="FINANCE", confidence=0.95, parent_category="Economic"),
            Topic(keyword="TECHNOLOGY", confidence=0.85, parent_category="Innovation")
        ],
        impact_score=7.5,
        credibility_score=8.0,
        urgency_score=6.0
    )


@pytest.fixture
def sample_article():
    """Sample article data."""
    return {
        "id": uuid4(),
        "title": "Bitcoin Surges Past $50,000 as Federal Reserve Signals Rate Cuts",
        "content": """
        Bitcoin prices exceeded $50,000 for the first time this year as the Federal
        Reserve signaled potential interest rate cuts in the coming months. The
        cryptocurrency market rally comes amid growing institutional adoption and
        declining inflation rates. Analysts predict continued volatility but remain
        optimistic about long-term growth prospects. Major technology companies are
        increasing their blockchain investments, further supporting market sentiment.
        """
    }


def test_specialist_initialization(specialist):
    """Test specialist initializes correctly."""
    assert specialist.specialist_type == SpecialistType.TOPIC_CLASSIFIER
    assert specialist.provider is not None
    assert specialist.total_tokens_used == 0


@pytest.mark.asyncio
async def test_quick_check_with_topics(specialist, sample_article, sample_tier1_results):
    """Test quick_check identifies relevant article."""
    result = await specialist.quick_check(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=sample_tier1_results
    )

    assert result.is_relevant is True
    assert result.confidence > 0.5
    assert len(result.reasoning) > 0
    assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_quick_check_without_topics(specialist, sample_article):
    """Test quick_check with no Tier1 topics."""
    tier1_empty = Tier1Results(
        entities=[],
        relations=[],
        topics=[],  # No topics
        impact_score=3.0,
        credibility_score=5.0,
        urgency_score=2.0
    )

    result = await specialist.quick_check(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=tier1_empty
    )

    # Should be marked as not relevant if no topics
    assert result.is_relevant is False or result.confidence < 0.6
    assert result.tokens_used >= 0


@pytest.mark.asyncio
async def test_deep_dive_analysis(specialist, sample_article, sample_tier1_results):
    """Test deep_dive produces valid topic classification."""
    findings = await specialist.deep_dive(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=sample_tier1_results,
        max_tokens=1500
    )

    # Verify findings structure
    assert findings.specialist_type == SpecialistType.TOPIC_CLASSIFIER
    assert findings.topic_classification is not None
    assert findings.tokens_used > 0
    assert findings.cost_usd >= 0.0
    assert len(findings.model) > 0

    # Check topics
    topics = findings.topic_classification.topics
    assert isinstance(topics, list)

    # If topics were extracted, verify structure
    if len(topics) > 0:
        assert len(topics) <= 5, "Should not exceed 5 topics"

        for topic_item in topics:
            assert "topic" in topic_item
            assert "parent_topic" in topic_item
            assert "confidence" in topic_item
            assert 0.0 <= topic_item["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_full_analyze_workflow(specialist, sample_article, sample_tier1_results):
    """Test complete analyze() workflow (quick_check + deep_dive)."""
    findings = await specialist.analyze(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=sample_tier1_results,
        max_tokens=1700
    )

    # With relevant topics, should return findings
    if findings is not None:
        assert findings.specialist_type == SpecialistType.TOPIC_CLASSIFIER
        assert findings.topic_classification is not None
        assert specialist.total_tokens_used > 0


@pytest.mark.asyncio
async def test_token_tracking(specialist, sample_article, sample_tier1_results):
    """Test token usage tracking across multiple calls."""
    # Reset counter
    specialist.reset_token_counter()
    assert specialist.total_tokens_used == 0

    # Run analysis
    await specialist.analyze(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=sample_tier1_results,
        max_tokens=1700
    )

    # Tokens should be tracked
    assert specialist.total_tokens_used > 0

    # Reset and verify
    specialist.reset_token_counter()
    assert specialist.total_tokens_used == 0


@pytest.mark.asyncio
async def test_budget_enforcement(specialist, sample_article, sample_tier1_results):
    """Test specialist respects token budget."""
    # Very low budget should skip deep_dive
    findings = await specialist.analyze(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=sample_tier1_results,
        max_tokens=100  # Too low for deep dive
    )

    # Should return None or empty findings due to budget
    if findings is None:
        assert specialist.total_tokens_used < 300  # Only quick_check


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

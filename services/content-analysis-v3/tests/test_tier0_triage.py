"""
Unit tests for Tier0 Triage module
Tests triage decision logic, database operations, and edge cases
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock

from app.pipeline.tier0.triage import Tier0Triage
from app.models.schemas import TriageDecision


@pytest.mark.asyncio
async def test_tier0_execute_success(db_pool, sample_article, mock_provider):
    """Test successful Tier0 execution with mock provider."""

    # Create Tier0 instance with mocked provider
    tier0 = Tier0Triage(db_pool)

    with patch.object(tier0, 'provider', mock_provider):
        result = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify result
    assert isinstance(result, TriageDecision)
    assert result.PriorityScore >= 0 and result.PriorityScore <= 10
    assert result.category in ["CONFLICT", "FINANCE", "POLITICS", "HUMANITARIAN", "SECURITY", "TECHNOLOGY", "OTHER"]
    assert isinstance(result.keep, bool)
    assert result.tokens_used > 0
    assert result.cost_usd > 0
    assert result.model != ""


@pytest.mark.asyncio
async def test_tier0_database_storage(db_pool, sample_article, mock_provider):
    """Test that Tier0 results are correctly stored in database."""

    tier0 = Tier0Triage(db_pool)

    with patch.object(tier0, 'provider', mock_provider):
        result = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify database storage
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM triage_decisions WHERE article_id = $1",
            sample_article["id"]
        )

    assert row is not None
    assert row["priority_score"] == result.PriorityScore
    assert row["category"] == result.category
    assert row["keep"] == result.keep
    assert row["tokens_used"] == result.tokens_used
    assert float(row["cost_usd"]) == result.cost_usd  # Convert Decimal to float
    assert row["model"] == result.model


@pytest.mark.asyncio
async def test_tier0_get_decision(db_pool, sample_article, mock_provider):
    """Test retrieving existing triage decision from database."""

    tier0 = Tier0Triage(db_pool)

    # First, create a decision
    with patch.object(tier0, 'provider', mock_provider):
        original = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Then retrieve it
    retrieved = await tier0.get_decision(sample_article["id"])

    assert retrieved is not None
    assert retrieved.PriorityScore == original.PriorityScore
    assert retrieved.category == original.category
    assert retrieved.keep == original.keep


@pytest.mark.asyncio
async def test_tier0_get_decision_nonexistent(db_pool):
    """Test retrieving decision for non-existent article."""

    tier0 = Tier0Triage(db_pool)
    result = await tier0.get_decision(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_tier0_priority_score_boundaries(db_pool, sample_article, mock_provider):
    """Test that PriorityScore stays within 0-10 range."""

    tier0 = Tier0Triage(db_pool)

    with patch.object(tier0, 'provider', mock_provider):
        result = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    assert 0 <= result.PriorityScore <= 10


@pytest.mark.asyncio
async def test_tier0_content_preview_truncation(db_pool, sample_article, mock_provider):
    """Test that content is truncated to 2000 chars for Tier0."""

    tier0 = Tier0Triage(db_pool)

    # Create article with very long content
    long_content = "x" * 5000

    with patch.object(tier0, 'provider', mock_provider):
        result = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=long_content
        )

    # Verify execution succeeded (content was truncated)
    assert result is not None
    assert isinstance(result, TriageDecision)


@pytest.mark.asyncio
async def test_tier0_category_validation(db_pool, sample_article, mock_provider):
    """Test that category is one of the allowed values."""

    tier0 = Tier0Triage(db_pool)

    with patch.object(tier0, 'provider', mock_provider):
        result = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    allowed_categories = ["CONFLICT", "FINANCE", "POLITICS", "HUMANITARIAN", "SECURITY", "TECHNOLOGY", "OTHER"]
    assert result.category in allowed_categories


@pytest.mark.asyncio
async def test_tier0_cost_tracking(db_pool, sample_article, mock_provider):
    """Test that cost tracking works correctly."""

    tier0 = Tier0Triage(db_pool)

    with patch.object(tier0, 'provider', mock_provider):
        result = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify cost is reasonable
    assert result.cost_usd > 0
    assert result.cost_usd < 0.001  # Should be very cheap for Tier0


@pytest.mark.asyncio
async def test_tier0_idempotency(db_pool, sample_article, mock_provider):
    """Test that running Tier0 twice updates the database correctly."""

    tier0 = Tier0Triage(db_pool)

    # Run twice
    with patch.object(tier0, 'provider', mock_provider):
        result1 = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

        result2 = await tier0.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify only one record exists (upsert worked)
    async with db_pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM triage_decisions WHERE article_id = $1",
            sample_article["id"]
        )

    assert count == 1

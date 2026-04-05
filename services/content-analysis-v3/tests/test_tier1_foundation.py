"""
Unit tests for Tier1 Foundation module
Tests entity/relation/topic extraction, database operations, and edge cases
"""

import pytest
from uuid import uuid4
from unittest.mock import patch

from app.pipeline.tier1.foundation import Tier1Foundation
from app.models.schemas import Tier1Results, Entity, Relation, Topic


@pytest.mark.asyncio
async def test_tier1_execute_success(db_pool, sample_article, mock_provider):
    """Test successful Tier1 execution with mock provider."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify result structure
    assert isinstance(result, Tier1Results)
    assert isinstance(result.entities, list)
    assert isinstance(result.relations, list)
    assert isinstance(result.topics, list)
    assert isinstance(result.impact_score, float)
    assert isinstance(result.credibility_score, float)
    assert isinstance(result.urgency_score, float)


@pytest.mark.asyncio
async def test_tier1_entity_extraction(db_pool, sample_article, mock_provider):
    """Test entity extraction and validation."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify entities
    assert len(result.entities) > 0

    for entity in result.entities:
        assert isinstance(entity, Entity)
        assert entity.name != ""
        assert entity.type in ["PERSON", "ORGANIZATION", "LOCATION", "EVENT"]
        assert 0.0 <= entity.confidence <= 1.0
        assert entity.mentions >= 1
        assert isinstance(entity.aliases, list)


@pytest.mark.asyncio
async def test_tier1_relation_extraction(db_pool, sample_article, mock_provider):
    """Test relation extraction and validation."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify relations
    assert len(result.relations) > 0

    for relation in result.relations:
        assert isinstance(relation, Relation)
        assert relation.subject != ""
        assert relation.predicate != ""
        assert relation.object != ""
        assert 0.0 <= relation.confidence <= 1.0


@pytest.mark.asyncio
async def test_tier1_topic_classification(db_pool, sample_article, mock_provider):
    """Test topic classification and validation."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify topics
    assert len(result.topics) > 0

    for topic in result.topics:
        assert isinstance(topic, Topic)
        assert topic.keyword != ""
        assert 0.0 <= topic.confidence <= 1.0
        assert topic.parent_category != ""


@pytest.mark.asyncio
async def test_tier1_score_ranges(db_pool, sample_article, mock_provider):
    """Test that all scores are within 0-10 range."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    assert 0.0 <= result.impact_score <= 10.0
    assert 0.0 <= result.credibility_score <= 10.0
    assert 0.0 <= result.urgency_score <= 10.0


@pytest.mark.asyncio
async def test_tier1_database_storage(db_pool, sample_article, mock_provider):
    """Test that Tier1 results are correctly stored in database."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    async with db_pool.acquire() as conn:
        # Verify entities stored
        entities_count = await conn.fetchval(
            "SELECT COUNT(*) FROM tier1_entities WHERE article_id = $1",
            sample_article["id"]
        )
        assert entities_count == len(result.entities)

        # Verify relations stored
        relations_count = await conn.fetchval(
            "SELECT COUNT(*) FROM tier1_relations WHERE article_id = $1",
            sample_article["id"]
        )
        assert relations_count == len(result.relations)

        # Verify topics stored
        topics_count = await conn.fetchval(
            "SELECT COUNT(*) FROM tier1_topics WHERE article_id = $1",
            sample_article["id"]
        )
        assert topics_count == len(result.topics)

        # Verify scores stored
        scores = await conn.fetchrow(
            "SELECT * FROM tier1_scores WHERE article_id = $1",
            sample_article["id"]
        )
        assert scores is not None
        assert float(scores["impact_score"]) == result.impact_score
        assert float(scores["credibility_score"]) == result.credibility_score
        assert float(scores["urgency_score"]) == result.urgency_score


@pytest.mark.asyncio
async def test_tier1_get_results(db_pool, sample_article, mock_provider):
    """Test retrieving existing Tier1 results from database."""

    tier1 = Tier1Foundation(db_pool)

    # First, create results
    with patch.object(tier1, 'provider', mock_provider):
        original = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Then retrieve them
    retrieved = await tier1.get_results(sample_article["id"])

    assert retrieved is not None
    assert len(retrieved.entities) == len(original.entities)
    assert len(retrieved.relations) == len(original.relations)
    assert len(retrieved.topics) == len(original.topics)
    assert retrieved.impact_score == original.impact_score


@pytest.mark.asyncio
async def test_tier1_get_results_nonexistent(db_pool):
    """Test retrieving results for non-existent article."""

    tier1 = Tier1Foundation(db_pool)
    result = await tier1.get_results(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_tier1_entity_aliases_handling(db_pool, sample_article, mock_provider):
    """Test that entity aliases are correctly stored and retrieved."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify alias storage
    async with db_pool.acquire() as conn:
        entities = await conn.fetch(
            "SELECT name, aliases FROM tier1_entities WHERE article_id = $1",
            sample_article["id"]
        )

    for entity_row in entities:
        # Aliases should be stored as JSONB array
        assert entity_row["aliases"] is not None


@pytest.mark.asyncio
async def test_tier1_cost_tracking(db_pool, sample_article, mock_provider):
    """Test that cost tracking works correctly."""

    tier1 = Tier1Foundation(db_pool)

    with patch.object(tier1, 'provider', mock_provider):
        result = await tier1.execute(
            article_id=sample_article["id"],
            title=sample_article["title"],
            url=sample_article["url"],
            content=sample_article["content"]
        )

    # Verify cost is reasonable
    assert result.cost_usd > 0
    assert result.cost_usd < 0.001  # Should be cheap for Tier1


@pytest.mark.asyncio
async def test_tier1_empty_entities_handling(db_pool, sample_article):
    """Test handling of articles with no extractable entities."""

    tier1 = Tier1Foundation(db_pool)

    # Mock provider that returns empty entities
    async def mock_generate_empty(prompt, max_tokens, response_format=None, temperature=0.0):
        from app.providers.base import ProviderMetadata

        response = """{
            "entities": [],
            "relations": [],
            "topics": [],
            "impact_score": 3.0,
            "credibility_score": 5.0,
            "urgency_score": 2.0
        }"""

        metadata = ProviderMetadata(
            tokens_used=500,
            cost_usd=0.00001,
            model="test",
            latency_ms=100,
            provider="test"
        )

        return response, metadata

    tier1.provider.generate = mock_generate_empty

    result = await tier1.execute(
        article_id=sample_article["id"],
        title=sample_article["title"],
        url=sample_article["url"],
        content=sample_article["content"]
    )

    # Should handle empty results gracefully
    assert isinstance(result, Tier1Results)
    assert len(result.entities) == 0
    assert len(result.relations) == 0
    assert len(result.topics) == 0

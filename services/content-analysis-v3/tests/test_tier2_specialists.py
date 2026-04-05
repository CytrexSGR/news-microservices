"""
Unit tests for Tier2 Specialists
Tests individual specialists and orchestrator
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock
import json

from app.pipeline.tier2.orchestrator import Tier2Orchestrator
from app.pipeline.tier2.specialists.topic_classifier import TopicClassifierSpecialist
from app.pipeline.tier2.specialists.entity_extractor import EntityExtractorSpecialist
from app.pipeline.tier2.specialists.financial_analyst import FinancialAnalyst
from app.pipeline.tier2.specialists.geopolitical_analyst import GeopoliticalAnalyst
from app.pipeline.tier2.specialists.sentiment_analyzer import SentimentAnalyzerSpecialist
from app.pipeline.tier2.models import (
    SpecialistType,
    QuickCheckResult,
    SpecialistFindings,
    TopicClassification
)


# Fixtures

@pytest.fixture
def financial_article_tier1(mock_tier1_results):
    """Tier1 results for a financial article."""
    from app.models.schemas import Topic

    # Modify mock to have FINANCE topic
    mock_tier1_results.topics = [
        Topic(keyword="FINANCE", confidence=0.95, parent_category="Economic Policy"),
        Topic(keyword="MARKETS", confidence=0.85, parent_category="Economic")
    ]
    return mock_tier1_results


@pytest.fixture
def geopolitical_article_tier1(mock_tier1_results):
    """Tier1 results for a geopolitical article."""
    from app.models.schemas import Topic

    mock_tier1_results.topics = [
        Topic(keyword="CONFLICT", confidence=0.90, parent_category="Security"),
        Topic(keyword="DIPLOMACY", confidence=0.75, parent_category="Politics")
    ]
    return mock_tier1_results


@pytest.fixture
def mock_topic_response():
    """Mock response for topic classification."""
    return json.dumps({
        "topics": [
            {
                "topic": "Bitcoin Price Analysis",
                "parent_topic": "Economics and Finance",
                "confidence": 0.95
            },
            {
                "topic": "Federal Reserve Policy",
                "parent_topic": "Economics and Finance",
                "confidence": 0.85
            }
        ]
    })


@pytest.fixture
def mock_financial_response():
    """Mock response for financial analysis."""
    return json.dumps({
        "metrics": {
            "market_impact": 7.5,
            "volatility_expected": 6.0,
            "sector_affected": "FINANCE",
            "price_direction": "BEARISH"
        },
        "affected_symbols": ["SPY", "DIA", "QQQ"]
    })


# Topic Classifier Tests

@pytest.mark.asyncio
async def test_topic_classifier_quick_check(db_pool, sample_article, mock_tier1_results, mock_provider):
    """Test TopicClassifier quick_check method."""

    specialist = TopicClassifierSpecialist()

    # Mock provider response
    async def mock_generate(prompt, max_tokens, temperature=0.0):
        response = "YES - Article has multiple classifiable topics"
        from app.providers.base import ProviderMetadata
        metadata = ProviderMetadata(
            tokens_used=50,
            cost_usd=0.000001,
            model="gemini-2.0-flash-exp",
            latency_ms=100,
            provider="gemini"
        )
        return response, metadata

    with patch.object(specialist.provider, 'generate', mock_generate):
        result = await specialist.quick_check(
            article_id=sample_article["id"],
            title=sample_article["title"],
            content=sample_article["content"],
            tier1_results=mock_tier1_results
        )

    assert isinstance(result, QuickCheckResult)
    assert result.is_relevant is True
    assert result.confidence > 0.0
    assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_topic_classifier_deep_dive(db_pool, sample_article, mock_tier1_results, mock_topic_response):
    """Test TopicClassifier deep_dive method."""

    specialist = TopicClassifierSpecialist()

    # Mock provider response
    async def mock_generate(prompt, max_tokens, temperature=0.0):
        from app.providers.base import ProviderMetadata
        metadata = ProviderMetadata(
            tokens_used=1200,
            cost_usd=0.000045,
            model="gemini-2.0-flash-exp",
            latency_ms=500,
            provider="gemini"
        )
        return mock_topic_response, metadata

    with patch.object(specialist.provider, 'generate', mock_generate):
        result = await specialist.deep_dive(
            article_id=sample_article["id"],
            title=sample_article["title"],
            content=sample_article["content"],
            tier1_results=mock_tier1_results,
            max_tokens=1500
        )

    assert isinstance(result, SpecialistFindings)
    assert result.specialist_type == SpecialistType.TOPIC_CLASSIFIER
    assert result.topic_classification is not None
    assert len(result.topic_classification.topics) == 2
    assert result.tokens_used > 0
    assert result.cost_usd > 0


# Financial Analyst Tests

@pytest.mark.asyncio
async def test_financial_analyst_quick_check_heuristic(
    db_pool, sample_article, financial_article_tier1
):
    """Test FinancialAnalyst quick_check with heuristic path (no LLM call)."""

    specialist = FinancialAnalyst()

    result = await specialist.quick_check(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=financial_article_tier1
    )

    # Should skip LLM call and use heuristic
    assert isinstance(result, QuickCheckResult)
    assert result.is_relevant is True
    assert result.confidence == 0.9
    assert result.tokens_used == 0  # No LLM call
    assert "Financial topics detected" in result.reasoning


@pytest.mark.asyncio
async def test_financial_analyst_deep_dive(
    db_pool, sample_article, financial_article_tier1, mock_financial_response
):
    """Test FinancialAnalyst deep_dive method."""

    specialist = FinancialAnalyst()

    # Mock provider response
    async def mock_generate(prompt, max_tokens, temperature=0.0):
        from app.providers.base import ProviderMetadata
        metadata = ProviderMetadata(
            tokens_used=1400,
            cost_usd=0.000053,
            model="gemini-2.0-flash-exp",
            latency_ms=600,
            provider="gemini"
        )
        return mock_financial_response, metadata

    with patch.object(specialist.provider, 'generate', mock_generate):
        result = await specialist.deep_dive(
            article_id=sample_article["id"],
            title=sample_article["title"],
            content=sample_article["content"],
            tier1_results=financial_article_tier1,
            max_tokens=1500
        )

    assert isinstance(result, SpecialistFindings)
    assert result.specialist_type == SpecialistType.FINANCIAL_ANALYST
    assert result.financial_metrics is not None
    assert result.financial_metrics.metrics["market_impact"] == 7.5
    assert result.financial_metrics.metrics["sector_affected"] == "FINANCE"
    assert len(result.financial_metrics.affected_symbols) == 3


# Orchestrator Tests

@pytest.mark.asyncio
async def test_orchestrator_initialization(db_pool):
    """Test Tier2Orchestrator initialization."""

    orchestrator = Tier2Orchestrator(db_pool)

    assert len(orchestrator.specialists) == 5
    assert SpecialistType.TOPIC_CLASSIFIER in orchestrator.specialists
    assert SpecialistType.FINANCIAL_ANALYST in orchestrator.specialists
    assert orchestrator.total_budget == 8000
    assert orchestrator.base_allocation == 1600


@pytest.mark.asyncio
async def test_orchestrator_budget_redistribution(
    db_pool, sample_article, mock_tier1_results, mock_topic_response
):
    """Test that orchestrator redistributes budget from skipped specialists."""

    orchestrator = Tier2Orchestrator(db_pool)

    # Mock all quick_checks: only TOPIC_CLASSIFIER relevant
    async def mock_quick_check_relevant(article_id, title, content, tier1_results):
        return QuickCheckResult(
            is_relevant=True,
            confidence=0.9,
            reasoning="Relevant",
            tokens_used=50
        )

    async def mock_quick_check_irrelevant(article_id, title, content, tier1_results):
        return QuickCheckResult(
            is_relevant=False,
            confidence=0.3,
            reasoning="Not relevant",
            tokens_used=50
        )

    # Mock deep_dive
    async def mock_deep_dive(article_id, title, content, tier1_results, max_tokens):
        from app.providers.base import ProviderMetadata
        metadata = ProviderMetadata(
            tokens_used=max_tokens - 100,
            cost_usd=0.000045,
            model="gemini-2.0-flash-exp",
            latency_ms=500,
            provider="gemini"
        )

        specialist = TopicClassifierSpecialist()
        with patch.object(specialist.provider, 'generate', return_value=(mock_topic_response, metadata)):
            return await specialist.deep_dive(
                article_id=article_id,
                title=title,
                content=content,
                tier1_results=tier1_results,
                max_tokens=max_tokens
            )

    # Only TOPIC_CLASSIFIER is relevant
    with patch.object(
        orchestrator.specialists[SpecialistType.TOPIC_CLASSIFIER],
        'quick_check',
        mock_quick_check_relevant
    ):
        with patch.object(
            orchestrator.specialists[SpecialistType.ENTITY_EXTRACTOR],
            'quick_check',
            mock_quick_check_irrelevant
        ):
            with patch.object(
                orchestrator.specialists[SpecialistType.FINANCIAL_ANALYST],
                'quick_check',
                mock_quick_check_irrelevant
            ):
                with patch.object(
                    orchestrator.specialists[SpecialistType.GEOPOLITICAL_ANALYST],
                    'quick_check',
                    mock_quick_check_irrelevant
                ):
                    with patch.object(
                        orchestrator.specialists[SpecialistType.SENTIMENT_ANALYZER],
                        'quick_check',
                        mock_quick_check_irrelevant
                    ):
                        with patch.object(
                            orchestrator.specialists[SpecialistType.TOPIC_CLASSIFIER],
                            'analyze',
                            mock_deep_dive
                        ):
                            results = await orchestrator.analyze_article(
                                article_id=sample_article["id"],
                                title=sample_article["title"],
                                content=sample_article["content"],
                                tier1_results=mock_tier1_results
                            )

    # Verify budget redistribution
    # 5 quick checks * 50 tokens = 250 tokens
    # Remaining: 8000 - 250 = 7750 tokens
    # 1 active specialist gets all remaining budget

    assert len(results.active_specialists) == 1
    assert SpecialistType.TOPIC_CLASSIFIER.value in results.active_specialists


@pytest.mark.asyncio
async def test_orchestrator_database_storage(
    db_pool, sample_article, mock_tier1_results, mock_topic_response
):
    """Test that orchestrator stores results in database."""

    orchestrator = Tier2Orchestrator(db_pool)

    # Mock all specialists to be irrelevant except TOPIC_CLASSIFIER
    async def mock_quick_check_relevant(article_id, title, content, tier1_results):
        return QuickCheckResult(
            is_relevant=True,
            confidence=0.9,
            reasoning="Relevant",
            tokens_used=50
        )

    async def mock_quick_check_irrelevant(article_id, title, content, tier1_results):
        return QuickCheckResult(
            is_relevant=False,
            confidence=0.3,
            reasoning="Not relevant",
            tokens_used=50
        )

    # Mock analyze method
    async def mock_analyze(article_id, title, content, tier1_results, max_tokens):
        from app.providers.base import ProviderMetadata

        specialist = TopicClassifierSpecialist()
        metadata = ProviderMetadata(
            tokens_used=1200,
            cost_usd=0.000045,
            model="gemini-2.0-flash-exp",
            latency_ms=500,
            provider="gemini"
        )

        with patch.object(specialist.provider, 'generate', return_value=(mock_topic_response, metadata)):
            return await specialist.deep_dive(
                article_id=article_id,
                title=title,
                content=content,
                tier1_results=tier1_results,
                max_tokens=max_tokens
            )

    with patch.object(
        orchestrator.specialists[SpecialistType.TOPIC_CLASSIFIER],
        'quick_check',
        mock_quick_check_relevant
    ):
        for specialist_type in [
            SpecialistType.ENTITY_EXTRACTOR,
            SpecialistType.FINANCIAL_ANALYST,
            SpecialistType.GEOPOLITICAL_ANALYST,
            SpecialistType.SENTIMENT_ANALYZER
        ]:
            with patch.object(
                orchestrator.specialists[specialist_type],
                'quick_check',
                mock_quick_check_irrelevant
            ):
                pass

        with patch.object(
            orchestrator.specialists[SpecialistType.TOPIC_CLASSIFIER],
            'analyze',
            mock_analyze
        ):
            await orchestrator.analyze_article(
                article_id=sample_article["id"],
                title=sample_article["title"],
                content=sample_article["content"],
                tier1_results=mock_tier1_results
            )

    # Verify database storage
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT specialist_type, specialist_data, tokens_used, cost_usd, model
            FROM tier2_specialist_results
            WHERE article_id = $1 AND specialist_type = $2
            """,
            sample_article["id"],
            SpecialistType.TOPIC_CLASSIFIER.value
        )

    assert row is not None
    assert row["specialist_type"] == SpecialistType.TOPIC_CLASSIFIER.value
    assert row["specialist_data"] is not None
    assert row["tokens_used"] > 0
    assert float(row["cost_usd"]) > 0


@pytest.mark.asyncio
async def test_orchestrator_get_results(
    db_pool, sample_article, mock_tier1_results, mock_topic_response
):
    """Test retrieving existing Tier2 results from database."""

    orchestrator = Tier2Orchestrator(db_pool)

    # First, create results (same as database storage test)
    async def mock_quick_check_relevant(article_id, title, content, tier1_results):
        return QuickCheckResult(
            is_relevant=True,
            confidence=0.9,
            reasoning="Relevant",
            tokens_used=50
        )

    async def mock_quick_check_irrelevant(article_id, title, content, tier1_results):
        return QuickCheckResult(
            is_relevant=False,
            confidence=0.3,
            reasoning="Not relevant",
            tokens_used=50
        )

    async def mock_analyze(article_id, title, content, tier1_results, max_tokens):
        from app.providers.base import ProviderMetadata

        specialist = TopicClassifierSpecialist()
        metadata = ProviderMetadata(
            tokens_used=1200,
            cost_usd=0.000045,
            model="gemini-2.0-flash-exp",
            latency_ms=500,
            provider="gemini"
        )

        with patch.object(specialist.provider, 'generate', return_value=(mock_topic_response, metadata)):
            return await specialist.deep_dive(
                article_id=article_id,
                title=title,
                content=content,
                tier1_results=tier1_results,
                max_tokens=max_tokens
            )

    with patch.object(
        orchestrator.specialists[SpecialistType.TOPIC_CLASSIFIER],
        'quick_check',
        mock_quick_check_relevant
    ):
        for specialist_type in [
            SpecialistType.ENTITY_EXTRACTOR,
            SpecialistType.FINANCIAL_ANALYST,
            SpecialistType.GEOPOLITICAL_ANALYST,
            SpecialistType.SENTIMENT_ANALYZER
        ]:
            with patch.object(
                orchestrator.specialists[specialist_type],
                'quick_check',
                mock_quick_check_irrelevant
            ):
                pass

        with patch.object(
            orchestrator.specialists[SpecialistType.TOPIC_CLASSIFIER],
            'analyze',
            mock_analyze
        ):
            await orchestrator.analyze_article(
                article_id=sample_article["id"],
                title=sample_article["title"],
                content=sample_article["content"],
                tier1_results=mock_tier1_results
            )

    # Then retrieve it
    retrieved = await orchestrator.get_results(sample_article["id"])

    assert retrieved is not None
    assert retrieved.topic_classification is not None
    assert len(retrieved.topic_classification.topic_classification.topics) == 2
    assert retrieved.total_tokens_used > 0
    assert retrieved.total_cost_usd > 0


@pytest.mark.asyncio
async def test_orchestrator_no_relevant_specialists(
    db_pool, sample_article, mock_tier1_results
):
    """Test orchestrator when no specialists are relevant."""

    orchestrator = Tier2Orchestrator(db_pool)

    # Mock all quick_checks to return irrelevant
    async def mock_quick_check_irrelevant(article_id, title, content, tier1_results):
        return QuickCheckResult(
            is_relevant=False,
            confidence=0.3,
            reasoning="Not relevant",
            tokens_used=50
        )

    for specialist_type in orchestrator.specialists.keys():
        with patch.object(
            orchestrator.specialists[specialist_type],
            'quick_check',
            mock_quick_check_irrelevant
        ):
            pass

    results = await orchestrator.analyze_article(
        article_id=sample_article["id"],
        title=sample_article["title"],
        content=sample_article["content"],
        tier1_results=mock_tier1_results
    )

    # Should return empty results with only quick check tokens
    assert len(results.active_specialists) == 0
    assert results.total_tokens_used == 250  # 5 specialists * 50 tokens
    assert results.total_cost_usd == 0.0

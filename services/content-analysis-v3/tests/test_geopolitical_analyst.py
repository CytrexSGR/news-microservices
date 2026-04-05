"""
Unit tests for GEOPOLITICAL_ANALYST specialist
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
import json

from app.pipeline.tier2.specialists.geopolitical_analyst import (
    GeopoliticalAnalyst,
    GEOPOLITICAL_KEYWORDS
)
from app.pipeline.tier2.models import (
    QuickCheckResult,
    SpecialistFindings,
    SpecialistType,
    GeopoliticalMetrics
)
from app.models.schemas import (
    Tier1Results,
    Entity,
    Relation,
    Topic
)


@pytest.fixture
def mock_provider():
    """Mock LLM provider for testing."""
    provider = MagicMock()
    provider.generate = AsyncMock()
    return provider


@pytest.fixture
def geopolitical_analyst(mock_provider):
    """Create GeopoliticalAnalyst with mocked provider."""
    analyst = GeopoliticalAnalyst()
    analyst.provider = mock_provider
    return analyst


@pytest.fixture
def tier1_geopolitical_results():
    """Sample Tier1 results for geopolitical article."""
    return Tier1Results(
        entities=[
            Entity(
                name="Ukraine",
                type="LOCATION",
                confidence=0.95,
                mentions=5
            ),
            Entity(
                name="Russia",
                type="LOCATION",
                confidence=0.95,
                mentions=4
            ),
            Entity(
                name="NATO",
                type="ORGANIZATION",
                confidence=0.90,
                mentions=3
            ),
        ],
        relations=[
            Relation(
                subject="NATO",
                predicate="SUPPORTS",
                object="Ukraine",
                confidence=0.90
            ),
            Relation(
                subject="Russia",
                predicate="OPPOSES",
                object="NATO",
                confidence=0.85
            ),
        ],
        topics=[
            Topic(
                keyword="CONFLICT",
                confidence=0.95,
                parent_category="Security"
            ),
            Topic(
                keyword="POLITICS",
                confidence=0.85,
                parent_category="International"
            ),
        ],
        impact_score=9.5,
        credibility_score=8.0,
        urgency_score=9.0,
        tokens_used=1500,
        cost_usd=0.00005,
        model="gemini-2.0-flash-exp"
    )


@pytest.fixture
def tier1_non_geopolitical_results():
    """Sample Tier1 results for non-geopolitical article."""
    return Tier1Results(
        entities=[
            Entity(
                name="Apple Inc.",
                type="ORGANIZATION",
                confidence=0.95,
                mentions=5
            ),
            Entity(
                name="iPhone 15",
                type="EVENT",
                confidence=0.90,
                mentions=3
            ),
        ],
        relations=[
            Relation(
                subject="Apple Inc.",
                predicate="LAUNCHES",
                object="iPhone 15",
                confidence=0.95
            ),
        ],
        topics=[
            Topic(
                keyword="TECHNOLOGY",
                confidence=0.95,
                parent_category="Technology"
            ),
        ],
        impact_score=6.0,
        credibility_score=8.0,
        urgency_score=5.0,
        tokens_used=1200,
        cost_usd=0.00004,
        model="gemini-2.0-flash-exp"
    )


@pytest.mark.asyncio
async def test_quick_check_relevant_geopolitical(
    geopolitical_analyst,
    mock_provider,
    tier1_geopolitical_results
):
    """Test quick_check identifies geopolitical content as relevant."""
    article_id = uuid4()
    title = "NATO Expands Support for Ukraine Amid Escalating Conflict"

    # Mock provider response
    mock_provider.generate.return_value = (
        json.dumps({
            "is_relevant": True,
            "confidence": 0.95,
            "reasoning": "Article discusses NATO-Ukraine relations and military conflict"
        }),
        MagicMock(tokens_used=150)
    )

    result = await geopolitical_analyst.quick_check(
        article_id=article_id,
        title=title,
        content="",
        tier1_results=tier1_geopolitical_results
    )

    assert isinstance(result, QuickCheckResult)
    assert result.is_relevant is True
    assert result.confidence >= 0.7  # Should be boosted due to geopolitical topics
    assert result.tokens_used == 150


@pytest.mark.asyncio
async def test_quick_check_not_relevant(
    geopolitical_analyst,
    mock_provider,
    tier1_non_geopolitical_results
):
    """Test quick_check identifies non-geopolitical content as irrelevant."""
    article_id = uuid4()
    title = "Apple Announces New iPhone 15 with Advanced Features"

    # Mock provider response
    mock_provider.generate.return_value = (
        json.dumps({
            "is_relevant": False,
            "confidence": 0.85,
            "reasoning": "Article about consumer technology, no geopolitical implications"
        }),
        MagicMock(tokens_used=120)
    )

    result = await geopolitical_analyst.quick_check(
        article_id=article_id,
        title=title,
        content="",
        tier1_results=tier1_non_geopolitical_results
    )

    assert isinstance(result, QuickCheckResult)
    assert result.is_relevant is False
    assert result.confidence > 0.5
    assert result.tokens_used == 120


@pytest.mark.asyncio
async def test_deep_dive_full_analysis(
    geopolitical_analyst,
    mock_provider,
    tier1_geopolitical_results
):
    """Test deep_dive performs comprehensive geopolitical analysis."""
    article_id = uuid4()
    title = "NATO Expands Support for Ukraine Amid Escalating Conflict"
    content = """
    NATO members agreed to provide additional military aid to Ukraine
    as tensions with Russia continue to escalate. The decision was made
    during an emergency summit in Brussels, where alliance leaders
    condemned Russian aggression and reaffirmed their commitment to
    collective defense under Article 5.
    """

    # Mock provider response
    mock_provider.generate.return_value = (
        json.dumps({
            "metrics": {
                "conflict_severity": 8.5,
                "diplomatic_impact": 7.0,
                "regional_stability_risk": 9.0,
                "international_attention": 9.5,
                "economic_implications": 7.5
            },
            "countries_involved": ["Ukraine", "Russia", "NATO members"],
            "relations": [
                {
                    "subject": "NATO",
                    "predicate": "OPPOSES",
                    "object": "Russia",
                    "confidence": 0.95
                },
                {
                    "subject": "NATO",
                    "predicate": "SUPPORTS",
                    "object": "Ukraine",
                    "confidence": 0.90
                }
            ]
        }),
        MagicMock(
            tokens_used=1200,
            cost_usd=0.00004,
            model="gemini-2.0-flash-exp"
        )
    )

    findings = await geopolitical_analyst.deep_dive(
        article_id=article_id,
        title=title,
        content=content,
        tier1_results=tier1_geopolitical_results,
        max_tokens=1500
    )

    assert isinstance(findings, SpecialistFindings)
    assert findings.specialist_type == SpecialistType.GEOPOLITICAL_ANALYST
    assert findings.geopolitical_metrics is not None

    # Check metrics
    metrics = findings.geopolitical_metrics.metrics
    assert "conflict_severity" in metrics
    assert metrics["conflict_severity"] == 8.5
    assert metrics["diplomatic_impact"] == 7.0
    assert metrics["regional_stability_risk"] == 9.0

    # Check countries
    assert len(findings.geopolitical_metrics.countries_involved) == 3
    assert "Ukraine" in findings.geopolitical_metrics.countries_involved

    # Check relations
    assert len(findings.geopolitical_metrics.relations) == 2

    # Check metadata
    assert findings.tokens_used == 1200
    assert findings.cost_usd == 0.00004
    assert findings.model == "gemini-2.0-flash-exp"


@pytest.mark.asyncio
async def test_deep_dive_handles_parse_error(
    geopolitical_analyst,
    mock_provider,
    tier1_geopolitical_results
):
    """Test deep_dive handles JSON parse errors gracefully."""
    article_id = uuid4()
    title = "Test Article"
    content = "Test content"

    # Mock provider returns invalid JSON
    mock_provider.generate.return_value = (
        "Invalid JSON response",
        MagicMock(
            tokens_used=800,
            cost_usd=0.00003,
            model="gemini-2.0-flash-exp"
        )
    )

    findings = await geopolitical_analyst.deep_dive(
        article_id=article_id,
        title=title,
        content=content,
        tier1_results=tier1_geopolitical_results,
        max_tokens=1500
    )

    # Should return empty findings but preserve metadata
    assert isinstance(findings, SpecialistFindings)
    assert findings.geopolitical_metrics is not None
    assert findings.geopolitical_metrics.metrics == {}
    assert findings.geopolitical_metrics.countries_involved == []
    assert findings.tokens_used == 800


@pytest.mark.asyncio
async def test_quick_check_fallback_on_parse_error(
    geopolitical_analyst,
    mock_provider,
    tier1_geopolitical_results
):
    """Test quick_check uses fallback logic on parse errors."""
    article_id = uuid4()
    title = "Test Article"

    # Mock provider returns invalid JSON
    mock_provider.generate.return_value = (
        "Invalid JSON",
        MagicMock(tokens_used=100)
    )

    result = await geopolitical_analyst.quick_check(
        article_id=article_id,
        title=title,
        content="",
        tier1_results=tier1_geopolitical_results
    )

    # Should use fallback: Tier1 has CONFLICT topic
    assert isinstance(result, QuickCheckResult)
    assert result.is_relevant is True  # Has geopolitical topics
    assert result.confidence == 0.6
    assert "Fallback" in result.reasoning


def test_geopolitical_keywords_constant():
    """Test GEOPOLITICAL_KEYWORDS contains expected terms."""
    assert "CONFLICT" in GEOPOLITICAL_KEYWORDS
    assert "POLITICS" in GEOPOLITICAL_KEYWORDS
    assert "DIPLOMACY" in GEOPOLITICAL_KEYWORDS
    assert "SECURITY" in GEOPOLITICAL_KEYWORDS
    assert "WAR" in GEOPOLITICAL_KEYWORDS
    assert len(GEOPOLITICAL_KEYWORDS) >= 15


def test_specialist_type():
    """Test GeopoliticalAnalyst uses correct specialist type."""
    analyst = GeopoliticalAnalyst()
    assert analyst.specialist_type == SpecialistType.GEOPOLITICAL_ANALYST

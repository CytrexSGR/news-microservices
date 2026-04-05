"""Unit tests for IntelligenceContextService."""
import pytest
from unittest.mock import AsyncMock
from app.services.intelligence_context import IntelligenceContextService

@pytest.fixture
def mock_search_results():
    return [
        {
            "title": "Rheinmetall sees record orders",
            "url": "https://example.com/1",
            "content": "Defense spending increases...",
            "published_at": "2026-01-25T10:00:00Z",
            "similarity": 0.89,
            "sentiment": 0.6,
        },
        {
            "title": "NATO defense budget rises",
            "url": "https://example.com/2",
            "content": "European nations commit...",
            "published_at": "2026-01-24T14:00:00Z",
            "similarity": 0.82,
            "sentiment": 0.4,
        },
    ]

@pytest.fixture
def mock_intel_summary():
    return {
        "bursts": {"count": 2, "items": [{"entity": "Rheinmetall", "level": 3}]},
        "momentum": {"improving": ["Rheinmetall"], "deteriorating": []},
        "contrarian": {"count": 0},
    }

@pytest.mark.asyncio
async def test_get_context_returns_structured_data(mock_search_results, mock_intel_summary):
    """Test that get_context returns properly structured data without LLM call."""
    service = IntelligenceContextService()

    # Mock the internal methods
    service._semantic_search = AsyncMock(return_value=mock_search_results)
    service._get_intelligence_summary = AsyncMock(return_value=mock_intel_summary)

    result = await service.get_context(
        question="What are risks for Defense ETFs?",
        limit=10,
    )

    # Verify structure
    assert "question" in result
    assert "articles" in result
    assert "total_found" in result
    assert "showing" in result
    assert "has_more" in result
    assert "intelligence_summary" in result

    # Verify no LLM answer field
    assert "answer" not in result

    # Verify article structure
    assert len(result["articles"]) == 2
    assert result["articles"][0]["title"] == "Rheinmetall sees record orders"
    assert result["articles"][0]["similarity"] == 0.89

@pytest.mark.asyncio
async def test_get_context_respects_limit(mock_search_results, mock_intel_summary):
    """Test that limit parameter is respected."""
    service = IntelligenceContextService()
    service._semantic_search = AsyncMock(return_value=mock_search_results)
    service._get_intelligence_summary = AsyncMock(return_value=mock_intel_summary)

    result = await service.get_context(
        question="Test query",
        limit=1,
    )

    assert result["showing"] == 1
    assert result["has_more"] is True
    assert len(result["articles"]) == 1

@pytest.mark.asyncio
async def test_get_context_empty_results():
    """Test handling of no results."""
    service = IntelligenceContextService()
    service._semantic_search = AsyncMock(return_value=[])
    service._get_intelligence_summary = AsyncMock(return_value={"bursts": {}, "momentum": {}, "contrarian": {}})

    result = await service.get_context(question="Unknown topic")

    assert result["total_found"] == 0
    assert result["showing"] == 0
    assert result["has_more"] is False
    assert result["articles"] == []

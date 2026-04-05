"""Tests for MCP tool implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.mcp.tools import (
    analyze_article,
    extract_entities,
    get_analysis_status,
    canonicalize_entity,
    get_entity_clusters,
    detect_intelligence_patterns,
    analyze_graph_quality,
    # Intelligence tools
    get_event_clusters,
    get_cluster_details,
    get_latest_events,
    get_intelligence_overview,
    # Narrative tools
    analyze_text_narrative,
    get_narrative_frames,
    get_bias_analysis,
    get_narrative_overview,
)


@pytest.mark.asyncio
async def test_analyze_article_success():
    """Test analyze_article tool success case."""
    # Mock client
    mock_client = AsyncMock()
    mock_client.analyze_article.return_value = {
        "article_id": "test-123",
        "entities": [],
        "sentiment": {"score": 0.5},
    }

    result = await analyze_article(article_id="test-123", client=mock_client)

    assert result.success is True
    assert result.data is not None
    assert result.error is None
    mock_client.analyze_article.assert_called_once_with("test-123")


@pytest.mark.asyncio
async def test_analyze_article_failure():
    """Test analyze_article tool failure case."""
    mock_client = AsyncMock()
    mock_client.analyze_article.side_effect = Exception("Service unavailable")

    result = await analyze_article(article_id="test-123", client=mock_client)

    assert result.success is False
    assert result.data is None
    assert "Service unavailable" in result.error


@pytest.mark.asyncio
async def test_extract_entities_success():
    """Test extract_entities tool success case."""
    mock_client = AsyncMock()
    mock_client.extract_entities.return_value = {
        "article_id": "test-123",
        "entities": [
            {"name": "Tesla", "type": "ORG"},
            {"name": "Elon Musk", "type": "PERSON"},
        ],
    }

    result = await extract_entities(article_id="test-123", client=mock_client)

    assert result.success is True
    assert result.data is not None
    assert len(result.data["entities"]) == 2


@pytest.mark.asyncio
async def test_canonicalize_entity_success():
    """Test canonicalize_entity tool success case."""
    mock_client = AsyncMock()
    mock_client.canonicalize_entity.return_value = {
        "canonical_name": "Elon Musk",
        "similarity_score": 1.0,
        "variants": ["Elon", "E. Musk"],
    }

    result = await canonicalize_entity(
        entity_name="Elon", entity_type="PERSON", client=mock_client
    )

    assert result.success is True
    assert result.data["canonical_name"] == "Elon Musk"
    mock_client.canonicalize_entity.assert_called_once_with("Elon", "PERSON")


@pytest.mark.asyncio
async def test_detect_intelligence_patterns_success():
    """Test detect_intelligence_patterns tool success case."""
    mock_client = AsyncMock()
    mock_client.detect_patterns.return_value = {
        "patterns": [
            {"type": "coordinated_activity", "confidence": 0.85},
        ],
    }

    result = await detect_intelligence_patterns(
        entity_id="entity-123", timeframe_days=30, client=mock_client
    )

    assert result.success is True
    assert "patterns" in result.data
    mock_client.detect_patterns.assert_called_once_with("entity-123", 30)


@pytest.mark.asyncio
async def test_analyze_graph_quality_success():
    """Test analyze_graph_quality tool success case."""
    mock_client = AsyncMock()
    mock_client.analyze_graph_quality.return_value = {
        "total_entities": 23315,
        "unknown_entities": 0,
        "quality_score": 0.95,
    }

    result = await analyze_graph_quality(client=mock_client)

    assert result.success is True
    assert result.data["unknown_entities"] == 0
    mock_client.analyze_graph_quality.assert_called_once()


# ============================================================================
# Intelligence Service Tools Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_event_clusters_success():
    """Test get_event_clusters tool success case."""
    mock_client = AsyncMock()
    mock_client.get_event_clusters.return_value = {
        "clusters": [
            {
                "cluster_id": "cluster-1",
                "article_count": 15,
                "entities": ["Tesla", "Elon Musk"],
            },
            {
                "cluster_id": "cluster-2",
                "article_count": 8,
                "entities": ["Apple", "Tim Cook"],
            },
        ],
        "total": 2,
    }

    result = await get_event_clusters(limit=50, min_articles=3, client=mock_client)

    assert result.success is True
    assert result.data is not None
    assert len(result.data["clusters"]) == 2
    assert result.data["total"] == 2
    mock_client.get_event_clusters.assert_called_once_with(50, 3)


@pytest.mark.asyncio
async def test_get_event_clusters_failure():
    """Test get_event_clusters tool failure case."""
    mock_client = AsyncMock()
    mock_client.get_event_clusters.side_effect = Exception("Connection timeout")

    result = await get_event_clusters(limit=50, min_articles=3, client=mock_client)

    assert result.success is False
    assert "Connection timeout" in result.error


@pytest.mark.asyncio
async def test_get_cluster_details_success():
    """Test get_cluster_details tool success case."""
    mock_client = AsyncMock()
    mock_client.get_cluster_details.return_value = {
        "cluster_id": "cluster-1",
        "articles": [
            {"article_id": "art-1", "title": "Tesla News"},
            {"article_id": "art-2", "title": "Elon Musk Interview"},
        ],
        "entities": ["Tesla", "Elon Musk"],
        "timeline": ["2024-01-01", "2024-01-02"],
    }

    result = await get_cluster_details(cluster_id="cluster-1", client=mock_client)

    assert result.success is True
    assert result.data["cluster_id"] == "cluster-1"
    assert len(result.data["articles"]) == 2
    mock_client.get_cluster_details.assert_called_once_with("cluster-1")


@pytest.mark.asyncio
async def test_get_latest_events_success():
    """Test get_latest_events tool success case."""
    mock_client = AsyncMock()
    mock_client.get_latest_events.return_value = {
        "events": [
            {
                "event_id": "evt-1",
                "summary": "Tech company announcement",
                "timestamp": "2024-01-15T10:00:00Z",
            },
            {
                "event_id": "evt-2",
                "summary": "Market update",
                "timestamp": "2024-01-15T09:30:00Z",
            },
        ],
        "total": 2,
    }

    result = await get_latest_events(limit=20, client=mock_client)

    assert result.success is True
    assert len(result.data["events"]) == 2
    mock_client.get_latest_events.assert_called_once_with(20)


@pytest.mark.asyncio
async def test_get_intelligence_overview_success():
    """Test get_intelligence_overview tool success case."""
    mock_client = AsyncMock()
    mock_client.get_intelligence_overview.return_value = {
        "total_clusters": 145,
        "total_events": 523,
        "top_clusters": [
            {"cluster_id": "cluster-1", "article_count": 25},
            {"cluster_id": "cluster-2", "article_count": 18},
        ],
        "trending_entities": ["Tesla", "Apple", "Google"],
    }

    result = await get_intelligence_overview(client=mock_client)

    assert result.success is True
    assert result.data["total_clusters"] == 145
    assert len(result.data["trending_entities"]) == 3
    mock_client.get_intelligence_overview.assert_called_once()


# ============================================================================
# Narrative Service Tools Tests
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_text_narrative_success():
    """Test analyze_text_narrative tool success case."""
    mock_client = AsyncMock()
    mock_client.analyze_text.return_value = {
        "frames": [
            {"frame": "economic_progress", "confidence": 0.85},
            {"frame": "innovation", "confidence": 0.78},
        ],
        "bias_score": 0.32,
        "propaganda_signals": [],
    }

    result = await analyze_text_narrative(
        text="Tesla announces breakthrough in battery technology", client=mock_client
    )

    assert result.success is True
    assert len(result.data["frames"]) == 2
    assert result.data["bias_score"] == 0.32
    mock_client.analyze_text.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_text_narrative_failure():
    """Test analyze_text_narrative tool failure case."""
    mock_client = AsyncMock()
    mock_client.analyze_text.side_effect = Exception("API timeout")

    result = await analyze_text_narrative(text="Test text", client=mock_client)

    assert result.success is False
    assert "API timeout" in result.error


@pytest.mark.asyncio
async def test_get_narrative_frames_success():
    """Test get_narrative_frames tool success case."""
    mock_client = AsyncMock()
    mock_client.get_narrative_frames.return_value = {
        "frames": [
            {
                "frame_name": "economic_progress",
                "frequency": 145,
                "examples": ["article-1", "article-2"],
            },
            {
                "frame_name": "conflict",
                "frequency": 89,
                "examples": ["article-3"],
            },
        ],
        "total": 2,
    }

    result = await get_narrative_frames(limit=50, category=None, client=mock_client)

    assert result.success is True
    assert len(result.data["frames"]) == 2
    mock_client.get_narrative_frames.assert_called_once_with(50, None)


@pytest.mark.asyncio
async def test_get_bias_analysis_success():
    """Test get_bias_analysis tool success case."""
    mock_client = AsyncMock()
    mock_client.get_bias_analysis.return_value = {
        "distribution": {
            "left": 23,
            "center": 145,
            "right": 18,
        },
        "average_bias": 0.12,
        "trends": [
            {"date": "2024-01-15", "bias": 0.15},
            {"date": "2024-01-14", "bias": 0.09},
        ],
    }

    result = await get_bias_analysis(
        start_date="2024-01-01", end_date="2024-01-15", client=mock_client
    )

    assert result.success is True
    assert result.data["average_bias"] == 0.12
    assert len(result.data["trends"]) == 2
    mock_client.get_bias_analysis.assert_called_once_with("2024-01-01", "2024-01-15")


@pytest.mark.asyncio
async def test_get_narrative_overview_success():
    """Test get_narrative_overview tool success case."""
    mock_client = AsyncMock()
    mock_client.get_narrative_overview.return_value = {
        "top_frames": [
            {"frame": "economic_progress", "count": 245},
            {"frame": "innovation", "count": 189},
        ],
        "bias_distribution": {"left": 34, "center": 156, "right": 28},
        "total_analyses": 218,
    }

    result = await get_narrative_overview(client=mock_client)

    assert result.success is True
    assert len(result.data["top_frames"]) == 2
    assert result.data["total_analyses"] == 218
    mock_client.get_narrative_overview.assert_called_once()

"""Tests for RAG intelligence service."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.rag_service import RAGService, RAGResponse


@pytest.mark.asyncio
async def test_rag_service_brief_response():
    """Test RAG service returns brief response."""
    service = RAGService()

    # Mock dependencies
    service.search_client = AsyncMock()
    service.search_client.semantic_search.return_value = {
        "results": [
            {"title": "Test Article", "content": "Test content", "similarity": 0.9}
        ]
    }
    service.llm_client = AsyncMock()
    service.llm_client.invoke.return_value = ("Brief answer here.", 100)

    result = await service.ask("What are Defense sector risks?", depth="brief")

    assert isinstance(result, RAGResponse)
    assert result.answer is not None
    assert len(result.answer) < 500  # Brief should be short
    assert result.sources is not None


@pytest.mark.asyncio
async def test_rag_service_detailed_response():
    """Test RAG service returns detailed response."""
    service = RAGService()

    service.search_client = AsyncMock()
    service.search_client.semantic_search.return_value = {
        "results": [
            {"title": "Test Article", "content": "Test content", "similarity": 0.9}
        ] * 10
    }
    service.llm_client = AsyncMock()
    service.llm_client.invoke.return_value = ("Detailed analysis...", 500)

    result = await service.ask("Analyze Rheinmetall sentiment", depth="detailed")

    assert isinstance(result, RAGResponse)
    assert result.depth == "detailed"
    assert len(result.sources) <= 10


@pytest.mark.asyncio
async def test_rag_service_no_results():
    """Test RAG service handles no search results gracefully."""
    service = RAGService()

    service.search_client = AsyncMock()
    service.search_client.semantic_search.return_value = {"results": []}

    result = await service.ask("Obscure topic with no data", depth="brief")

    assert result.answer is not None
    assert "no relevant" in result.answer.lower() or "not found" in result.answer.lower()


@pytest.mark.asyncio
async def test_rag_service_sources_limited():
    """Test that sources are limited to 5 in the response."""
    service = RAGService()

    # Return 15 articles from search
    service.search_client = AsyncMock()
    service.search_client.semantic_search.return_value = {
        "results": [
            {"title": f"Article {i}", "content": f"Content {i}", "similarity": 0.9 - i * 0.01}
            for i in range(15)
        ]
    }
    service.llm_client = AsyncMock()
    service.llm_client.invoke.return_value = ("Analysis of many articles.", 800)

    result = await service.ask("Large query", depth="detailed")

    # Should have max 5 sources even with more articles
    assert len(result.sources) <= 5
    assert result.context_articles == 15  # But context had all 15


@pytest.mark.asyncio
async def test_rag_service_metadata():
    """Test that response includes proper metadata."""
    service = RAGService()

    service.search_client = AsyncMock()
    service.search_client.semantic_search.return_value = {
        "results": [{"title": "Test", "content": "Content", "similarity": 0.85}]
    }
    service.llm_client = AsyncMock()
    service.llm_client.invoke.return_value = ("Answer.", 150)

    result = await service.ask("Test question", depth="brief")

    assert "model" in result.metadata
    assert result.tokens_used == 150
    assert result.context_articles == 1


@pytest.mark.asyncio
async def test_rag_service_caching():
    """Test that identical questions use cache."""
    service = RAGService()

    service.search_client = AsyncMock()
    service.search_client.semantic_search.return_value = {
        "results": [{"title": "Test", "content": "Content", "similarity": 0.9}]
    }
    service.llm_client = AsyncMock()
    service.llm_client.invoke.return_value = ("Cached answer.", 100)

    # First call
    result1 = await service.ask("Same question?", depth="brief")

    # Second call with same question
    result2 = await service.ask("Same question?", depth="brief")

    # LLM should only be called once (second is cached)
    assert service.llm_client.invoke.call_count == 1
    assert result1.answer == result2.answer


@pytest.mark.asyncio
async def test_rag_service_different_depth_not_cached():
    """Test that different depths are not cached together."""
    service = RAGService()

    service.search_client = AsyncMock()
    service.search_client.semantic_search.return_value = {
        "results": [{"title": "Test", "content": "Content", "similarity": 0.9}]
    }
    service.llm_client = AsyncMock()
    service.llm_client.invoke.side_effect = [
        ("Brief answer.", 100),
        ("Detailed answer with more content.", 500)
    ]

    # Call with brief
    result1 = await service.ask("Question?", depth="brief")

    # Call with detailed (same question, different depth)
    result2 = await service.ask("Question?", depth="detailed")

    # LLM should be called twice (different cache keys)
    assert service.llm_client.invoke.call_count == 2
    assert result1.depth == "brief"
    assert result2.depth == "detailed"

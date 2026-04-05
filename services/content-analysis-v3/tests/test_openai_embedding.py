"""Tests for OpenAI embedding generation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_generate_embedding_returns_vector():
    """Test that generate_embedding returns a 1536-dimension vector."""
    from app.providers.openai.provider import OpenAIProvider

    # Mock the OpenAI client response
    mock_embedding = [0.1] * 1536  # 1536 dimensions
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=mock_embedding)]
    mock_response.usage = MagicMock(prompt_tokens=15)

    with patch.object(OpenAIProvider, '__init__', lambda self, *args, **kwargs: None):
        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider.client = AsyncMock()
        provider.client.embeddings.create = AsyncMock(return_value=mock_response)
        provider.timeout = 30

        result = await provider.generate_embedding("Test article about Tesla")

        assert isinstance(result, list)
        assert len(result) == 1536
        assert all(isinstance(v, float) for v in result)


@pytest.mark.asyncio
async def test_generate_embedding_truncates_long_text():
    """Test that text longer than 8000 chars is truncated."""
    from app.providers.openai.provider import OpenAIProvider

    mock_embedding = [0.1] * 1536
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=mock_embedding)]
    mock_response.usage = MagicMock(prompt_tokens=100)

    with patch.object(OpenAIProvider, '__init__', lambda self, *args, **kwargs: None):
        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider.client = AsyncMock()
        provider.client.embeddings.create = AsyncMock(return_value=mock_response)
        provider.timeout = 30

        # Very long text
        long_text = "x" * 10000
        await provider.generate_embedding(long_text)

        # Verify the call used truncated text
        call_args = provider.client.embeddings.create.call_args
        assert len(call_args.kwargs["input"]) <= 8000


@pytest.mark.asyncio
async def test_generate_embedding_uses_correct_model():
    """Test that text-embedding-3-small model is used."""
    from app.providers.openai.provider import OpenAIProvider

    mock_embedding = [0.1] * 1536
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=mock_embedding)]
    mock_response.usage = MagicMock(prompt_tokens=15)

    with patch.object(OpenAIProvider, '__init__', lambda self, *args, **kwargs: None):
        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider.client = AsyncMock()
        provider.client.embeddings.create = AsyncMock(return_value=mock_response)
        provider.timeout = 30

        await provider.generate_embedding("Test text")

        call_args = provider.client.embeddings.create.call_args
        assert call_args.kwargs["model"] == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_generate_embedding_handles_timeout():
    """Test that timeout is handled gracefully."""
    import asyncio
    from app.providers.openai.provider import OpenAIProvider
    from app.providers.base import ProviderTimeoutError

    with patch.object(OpenAIProvider, '__init__', lambda self, *args, **kwargs: None):
        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider.client = AsyncMock()
        provider.client.embeddings.create = AsyncMock(side_effect=asyncio.TimeoutError())
        provider.timeout = 30

        with pytest.raises(ProviderTimeoutError):
            await provider.generate_embedding("Test text")


@pytest.mark.asyncio
async def test_generate_embedding_handles_api_error():
    """Test that API errors are wrapped in ProviderError."""
    from app.providers.openai.provider import OpenAIProvider
    from app.providers.base import ProviderError

    with patch.object(OpenAIProvider, '__init__', lambda self, *args, **kwargs: None):
        provider = OpenAIProvider.__new__(OpenAIProvider)
        provider.client = AsyncMock()
        provider.client.embeddings.create = AsyncMock(side_effect=Exception("API error"))
        provider.timeout = 30

        with pytest.raises(ProviderError) as exc_info:
            await provider.generate_embedding("Test text")

        assert "API error" in str(exc_info.value)

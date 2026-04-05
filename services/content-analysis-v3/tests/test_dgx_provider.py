import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_dgx_provider_generates_2048d_embedding():
    from app.providers.dgx.provider import DGXEmbeddingProvider
    provider = DGXEmbeddingProvider(base_url="http://localhost:8766", model="Qwen/Qwen3-Embedding-0.6B", timeout=30)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": [{"embedding": [0.1] * 2048}], "usage": {"total_tokens": 42}}
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        result = await provider.generate_embedding("Test article about Bitcoin price movement")
        assert len(result) == 2048
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)


@pytest.mark.asyncio
async def test_dgx_provider_truncates_long_text():
    from app.providers.dgx.provider import DGXEmbeddingProvider
    provider = DGXEmbeddingProvider(base_url="http://localhost:8766")
    long_text = "x" * 10000
    truncated = provider._prepare_text(long_text)
    assert len(truncated) <= 8000


@pytest.mark.asyncio
async def test_dgx_provider_batch_embedding():
    from app.providers.dgx.provider import DGXEmbeddingProvider
    provider = DGXEmbeddingProvider(base_url="http://localhost:8766")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": [{"embedding": [0.1] * 2048}, {"embedding": [0.2] * 2048}]}
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        results = await provider.generate_embeddings_batch(["text1", "text2"])
        assert len(results) == 2
        assert len(results[0]) == 2048

"""
Tests for Perplexity AI client.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from datetime import datetime

from app.services.perplexity import PerplexityClient


class TestPerplexityClient:
    """Tests for PerplexityClient."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = PerplexityClient()
        assert client.api_key is not None
        assert client.base_url == "https://api.perplexity.ai"
        assert client.timeout == 60
        assert client.max_retries == 3

    @pytest.mark.asyncio
    async def test_research_success(self):
        """Test successful research query."""
        client = PerplexityClient()

        mock_response = {
            "choices": [{
                "message": {
                    "content": "This is the research result.",
                    "citations": [
                        {
                            "url": "https://example.com/article",
                            "title": "Example Article",
                            "snippet": "Relevant excerpt"
                        }
                    ]
                }
            }],
            "usage": {
                "total_tokens": 1500
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await client.research(
                query="What is AI?",
                model="sonar",
                depth="standard"
            )

            assert "content" in result
            assert "citations" in result
            assert "sources" in result
            assert "tokens_used" in result
            assert result["tokens_used"] == 1500
            assert "cost" in result

    @pytest.mark.asyncio
    async def test_research_with_custom_parameters(self):
        """Test research with custom parameters."""
        client = PerplexityClient()

        mock_response = {
            "choices": [{
                "message": {
                    "content": "Deep research result",
                    "citations": []
                }
            }],
            "usage": {"total_tokens": 2000}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await client.research(
                query="Deep research query",
                model="sonar-pro",
                depth="deep",
                max_tokens=8000
            )

            assert result["model"] == "sonar-pro"
            assert result["tokens_used"] == 2000

    @pytest.mark.asyncio
    async def test_research_no_api_key(self):
        """Test research without API key."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.PERPLEXITY_API_KEY = None

            client = PerplexityClient()

            with pytest.raises(ValueError, match="PERPLEXITY_API_KEY not configured"):
                await client.research("Test query")

    @pytest.mark.asyncio
    async def test_research_rate_limit_retry(self):
        """Test retry on rate limit."""
        client = PerplexityClient()

        # First call returns 429, second succeeds
        mock_response_success = {
            "choices": [{
                "message": {
                    "content": "Success after retry",
                    "citations": []
                }
            }],
            "usage": {"total_tokens": 1000}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()

            # First call raises 429
            rate_limit_error = httpx.HTTPStatusError(
                "Rate limit",
                request=MagicMock(),
                response=MagicMock(status_code=429)
            )

            # Second call succeeds
            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = mock_response_success
            success_response.raise_for_status = MagicMock()

            mock_post.side_effect = [rate_limit_error, success_response]
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock):
                result = await client.research("Test query")

                assert result["content"] == "Success after retry"

    @pytest.mark.asyncio
    async def test_research_max_retries_exceeded(self):
        """Test max retries exceeded."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.side_effect = httpx.RequestError("Connection failed")

            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="Max retries exceeded"):
                    await client.research("Test query")

    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """Test health check success."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.status_code = 200

            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await client.check_health()

            assert result is True

    @pytest.mark.asyncio
    async def test_check_health_failure(self):
        """Test health check failure."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.status_code = 500

            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await client.check_health()

            assert result is False

    @pytest.mark.asyncio
    async def test_check_health_no_api_key(self):
        """Test health check without API key."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.PERPLEXITY_API_KEY = None

            client = PerplexityClient()
            result = await client.check_health()

            assert result is False

    def test_parse_response(self):
        """Test response parsing."""
        client = PerplexityClient()

        raw_response = {
            "choices": [{
                "message": {
                    "content": "Research content",
                    "citations": [
                        {
                            "url": "https://example.com/1",
                            "title": "Article 1",
                            "snippet": "Snippet 1"
                        },
                        {
                            "url": "https://example.com/2",
                            "title": "Article 2",
                            "snippet": "Snippet 2"
                        }
                    ]
                }
            }],
            "usage": {
                "total_tokens": 1500
            }
        }

        result = client._parse_response(raw_response, "sonar")

        assert result["content"] == "Research content"
        assert len(result["citations"]) == 2
        assert len(result["sources"]) == 2
        assert result["tokens_used"] == 1500
        assert result["model"] == "sonar"

    def test_extract_sources(self):
        """Test source extraction from citations."""
        client = PerplexityClient()

        citations = [
            {
                "url": "https://example.com/1",
                "title": "Article 1",
                "snippet": "Snippet 1"
            },
            {
                "url": "https://example.com/1",  # Duplicate
                "title": "Article 1",
                "snippet": "Snippet 1"
            },
            {
                "url": "https://example.com/2",
                "title": "Article 2",
                "snippet": "Snippet 2"
            }
        ]

        sources = client._extract_sources(citations)

        assert len(sources) == 2  # Duplicates removed
        assert sources[0]["url"] == "https://example.com/1"
        assert sources[1]["url"] == "https://example.com/2"

    def test_get_temperature_for_depth(self):
        """Test temperature selection based on depth."""
        client = PerplexityClient()

        assert client._get_temperature_for_depth("quick") == 0.3
        assert client._get_temperature_for_depth("standard") == 0.5
        assert client._get_temperature_for_depth("deep") == 0.7
        assert client._get_temperature_for_depth("unknown") == 0.5  # Default

    def test_get_recency_filter(self):
        """Test recency filter based on depth."""
        client = PerplexityClient()

        assert client._get_recency_filter("quick") == "day"
        assert client._get_recency_filter("standard") == "week"
        assert client._get_recency_filter("deep") == "month"

    @pytest.mark.asyncio
    async def test_backoff(self):
        """Test exponential backoff."""
        client = PerplexityClient()

        import time
        start = time.time()
        await client._backoff(0)  # 2^0 = 1 second
        elapsed = time.time() - start

        assert elapsed >= 1.0
        assert elapsed < 1.5

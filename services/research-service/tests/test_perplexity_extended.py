"""
Extended tests for Perplexity API integration.
Tests error handling, timeouts, structured output, and edge cases.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from datetime import datetime
import json

from app.services.perplexity import PerplexityClient
from pydantic import BaseModel


class TestPerplexityExtended:
    """Extended tests for Perplexity client."""

    @pytest.mark.asyncio
    async def test_research_with_response_format(self):
        """Test research with structured JSON response format."""
        client = PerplexityClient()

        response_schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "key_points": {"type": "array"}
            }
        }

        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"summary": "Test", "key_points": ["a", "b"]}',
                    "citations": []
                }
            }],
            "usage": {"total_tokens": 1000}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await client.research(
                query="Test query",
                response_format=response_schema
            )

            assert result["content"] is not None
            mock_post.assert_called_once()

            # Verify response_format was passed
            call_args = mock_post.call_args
            assert "response_format" in call_args[1]["json"]

    @pytest.mark.asyncio
    async def test_research_timeout_handling(self):
        """Test timeout handling."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="Max retries exceeded"):
                    await client.research("Test query")

    @pytest.mark.asyncio
    async def test_research_500_error_retry(self):
        """Test retry on 500 server error."""
        client = PerplexityClient()

        success_response = {
            "choices": [{
                "message": {
                    "content": "Success",
                    "citations": []
                }
            }],
            "usage": {"total_tokens": 500}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()

            # First attempt: 500 error
            error_response = MagicMock()
            error_response.status_code = 500
            error = httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=error_response
            )

            # Second attempt: success
            success_resp = MagicMock()
            success_resp.status_code = 200
            success_resp.json.return_value = success_response
            success_resp.raise_for_status = MagicMock()

            mock_post.side_effect = [error, success_resp]
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock):
                result = await client.research("Test query")

                assert result["content"] == "Success"
                assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_research_429_rate_limit_backoff(self):
        """Test exponential backoff on rate limit."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()

            error_response = MagicMock()
            error_response.status_code = 429
            error = httpx.HTTPStatusError(
                "Rate limit",
                request=MagicMock(),
                response=error_response
            )

            mock_post.side_effect = error
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock) as mock_backoff:
                with pytest.raises(httpx.HTTPStatusError):
                    await client.research("Test query")

                # Verify backoff was called
                assert mock_backoff.call_count == 2  # max_retries - 1

    @pytest.mark.asyncio
    async def test_research_structured_with_validation(self):
        """Test structured research with Pydantic validation."""

        class OutputSchema(BaseModel):
            title: str
            summary: str
            confidence: float

        client = PerplexityClient()

        mock_response = {
            "choices": [{
                "message": {
                    "content": '''```json
                    {
                        "title": "Test Title",
                        "summary": "Test summary",
                        "confidence": 0.95
                    }
                    ```''',
                    "citations": []
                }
            }],
            "usage": {"total_tokens": 1200}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await client.research_structured(
                query="Test query",
                output_schema=OutputSchema
            )

            assert result["validation_status"] == "valid"
            assert result["structured_data"]["title"] == "Test Title"
            assert result["structured_data"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_research_structured_validation_failure(self):
        """Test structured research with invalid data."""

        class OutputSchema(BaseModel):
            required_field: str
            numeric_field: int

        client = PerplexityClient()

        # Invalid JSON - missing required fields
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"wrong_field": "value"}',
                    "citations": []
                }
            }],
            "usage": {"total_tokens": 800}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await client.research_structured(
                query="Test query",
                output_schema=OutputSchema
            )

            assert "invalid" in result["validation_status"]

    @pytest.mark.asyncio
    async def test_extract_json_from_code_block(self):
        """Test JSON extraction from markdown code blocks."""
        client = PerplexityClient()

        text = '''Here is the analysis:
        ```json
        {
            "result": "success",
            "value": 123
        }
        ```
        End of analysis.'''

        result = client._extract_json(text)

        assert result["result"] == "success"
        assert result["value"] == 123

    @pytest.mark.asyncio
    async def test_extract_json_inline(self):
        """Test JSON extraction from inline text."""
        client = PerplexityClient()

        text = 'The result is {"status": "ok", "count": 5} and more text'

        result = client._extract_json(text)

        assert result["status"] == "ok"
        assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_extract_json_no_json_found(self):
        """Test JSON extraction when no JSON present."""
        client = PerplexityClient()

        text = "This is just plain text without any JSON"

        with pytest.raises(ValueError, match="No JSON content found"):
            client._extract_json(text)

    @pytest.mark.asyncio
    async def test_extract_json_invalid_json(self):
        """Test JSON extraction with malformed JSON."""
        client = PerplexityClient()

        text = '{"invalid": json}'

        with pytest.raises(ValueError, match="Invalid JSON"):
            client._extract_json(text)

    @pytest.mark.asyncio
    async def test_parse_response_empty_choices(self):
        """Test parsing response with empty choices."""
        client = PerplexityClient()

        response = {
            "choices": [],
            "usage": {"total_tokens": 0}
        }

        result = client._parse_response(response, "sonar")

        assert result["content"] == ""
        assert result["citations"] == []
        assert result["tokens_used"] == 0

    @pytest.mark.asyncio
    async def test_parse_response_missing_fields(self):
        """Test parsing response with missing fields."""
        client = PerplexityClient()

        response = {
            "choices": [{"message": {}}],
            "usage": {}
        }

        result = client._parse_response(response, "sonar")

        assert result["content"] == ""
        assert result["citations"] == []
        assert result["tokens_used"] == 0

    @pytest.mark.asyncio
    async def test_extract_sources_deduplication(self):
        """Test source deduplication by URL."""
        client = PerplexityClient()

        citations = [
            {"url": "https://example.com/1", "title": "A", "snippet": "X"},
            {"url": "https://example.com/1", "title": "A", "snippet": "Y"},  # Duplicate
            {"url": "https://example.com/2", "title": "B", "snippet": "Z"},
        ]

        sources = client._extract_sources(citations)

        assert len(sources) == 2
        urls = [s["url"] for s in sources]
        assert "https://example.com/1" in urls
        assert "https://example.com/2" in urls

    @pytest.mark.asyncio
    async def test_extract_sources_empty_citations(self):
        """Test source extraction with no citations."""
        client = PerplexityClient()

        sources = client._extract_sources([])

        assert sources == []

    @pytest.mark.asyncio
    async def test_backoff_timing(self):
        """Test exponential backoff timing."""
        client = PerplexityClient()

        import time

        # Test backoff for attempt 0 (2^0 = 1 second)
        start = time.time()
        await client._backoff(0)
        elapsed = time.time() - start
        assert 0.9 < elapsed < 1.2

        # Test backoff for attempt 1 (2^1 = 2 seconds)
        start = time.time()
        await client._backoff(1)
        elapsed = time.time() - start
        assert 1.9 < elapsed < 2.2

    @pytest.mark.asyncio
    async def test_research_with_all_parameters(self):
        """Test research with all optional parameters."""
        client = PerplexityClient()

        mock_response = {
            "choices": [{
                "message": {
                    "content": "Complete result",
                    "citations": [
                        {"url": "https://test.com", "title": "Test", "snippet": "Snippet"}
                    ]
                }
            }],
            "usage": {"total_tokens": 3000}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await client.research(
                query="Full test query",
                model="sonar-reasoning-pro",
                depth="deep",
                max_tokens=8000,
                response_format={"type": "json_object"}
            )

            assert result["content"] == "Complete result"
            assert result["model"] == "sonar-reasoning-pro"
            assert len(result["citations"]) == 1

    @pytest.mark.asyncio
    async def test_check_health_network_error(self):
        """Test health check with network error."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_get.side_effect = httpx.NetworkError("Network failed")

            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await client.check_health()

            assert result is False

    @pytest.mark.asyncio
    async def test_temperature_affects_payload(self):
        """Test that depth affects temperature in payload."""
        client = PerplexityClient()

        # We can't directly test the payload, but we can verify the function
        assert client._get_temperature_for_depth("quick") < client._get_temperature_for_depth("standard")
        assert client._get_temperature_for_depth("standard") < client._get_temperature_for_depth("deep")

    @pytest.mark.asyncio
    async def test_recency_filter_affects_payload(self):
        """Test that depth affects recency filter."""
        client = PerplexityClient()

        # Quick should be most recent
        assert client._get_recency_filter("quick") == "day"
        assert client._get_recency_filter("standard") == "week"
        assert client._get_recency_filter("deep") == "month"

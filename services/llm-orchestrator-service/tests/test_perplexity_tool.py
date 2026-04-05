"""
Tests for Perplexity Deep Search Tool

Coverage:
- API integration (mocked)
- Error handling
- Confidence calculation
- Response parsing
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import httpx

from app.tools.perplexity_tool import perplexity_deep_search, _calculate_confidence


class TestPerplexityTool:
    """Test Perplexity deep search tool."""

    @pytest.mark.asyncio
    async def test_perplexity_search_success(
        self,
        mock_httpx_client,
        mock_perplexity_response,
        mock_settings
    ):
        """Test successful Perplexity API call."""
        mock_httpx_client.post = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value=mock_perplexity_response)
        mock_httpx_client.post.return_value = mock_response

        with patch('app.tools.perplexity_tool.settings', mock_settings):
            with patch('app.tools.perplexity_tool.httpx.AsyncClient', return_value=mock_httpx_client):
                result = await perplexity_deep_search(
                    query="Tesla Q3 2024 earnings actual amount"
                )

        assert result.success is True
        assert result.tool_name == "perplexity_deep_search"
        assert result.execution_time_ms > 0
        assert result.confidence > 0.0
        assert len(result.source_citations) > 0
        assert "answer" in result.result_data
        assert "Tesla" in result.result_data["answer"]

    @pytest.mark.asyncio
    async def test_perplexity_search_with_domain_filter(
        self,
        mock_httpx_client,
        mock_perplexity_response,
        mock_settings
    ):
        """Test Perplexity search with domain filter."""
        mock_httpx_client.post = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value=mock_perplexity_response)
        mock_httpx_client.post.return_value = mock_response

        with patch('app.tools.perplexity_tool.settings', mock_settings):
            with patch('app.tools.perplexity_tool.httpx.AsyncClient', return_value=mock_httpx_client):
                result = await perplexity_deep_search(
                    query="Tesla earnings",
                    search_domain_filter=["sec.gov", "ir.tesla.com"]
                )

        assert result.success is True
        # Verify domain filter was passed to API
        call_args = mock_httpx_client.post.call_args
        request_data = call_args[1]["json"]
        assert "search_domain_filter" in request_data
        assert request_data["search_domain_filter"] == ["sec.gov", "ir.tesla.com"]

    @pytest.mark.asyncio
    async def test_perplexity_search_with_recency_filter(
        self,
        mock_httpx_client,
        mock_perplexity_response,
        mock_settings
    ):
        """Test Perplexity search with recency filter."""
        mock_httpx_client.post = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value=mock_perplexity_response)
        mock_httpx_client.post.return_value = mock_response

        with patch('app.tools.perplexity_tool.settings', mock_settings):
            with patch('app.tools.perplexity_tool.httpx.AsyncClient', return_value=mock_httpx_client):
                result = await perplexity_deep_search(
                    query="Tesla earnings",
                    search_recency_filter="month"
                )

        assert result.success is True
        # Verify recency filter was passed
        call_args = mock_httpx_client.post.call_args
        request_data = call_args[1]["json"]
        assert "search_recency_filter" in request_data
        assert request_data["search_recency_filter"] == "month"

    @pytest.mark.asyncio
    async def test_perplexity_search_api_error(self, mock_settings):
        """Test handling of Perplexity API errors."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "500 Server Error",
                request=Mock(),
                response=mock_response
            )
        )
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch('app.tools.perplexity_tool.settings', mock_settings):
            with patch('app.tools.perplexity_tool.httpx.AsyncClient', return_value=mock_client):
                result = await perplexity_deep_search(query="test query")

        assert result.success is False
        assert result.confidence == 0.0
        assert len(result.source_citations) == 0
        assert "500" in result.error_message

    @pytest.mark.asyncio
    async def test_perplexity_search_missing_api_key(self, mock_settings):
        """Test error when API key is not configured."""
        mock_settings_no_key = mock_settings.model_copy()
        mock_settings_no_key.PERPLEXITY_API_KEY = None
        mock_settings_no_key.OPENAI_API_KEY = None

        with patch('app.tools.perplexity_tool.settings', mock_settings_no_key):
            result = await perplexity_deep_search(query="test query")

        assert result.success is False
        assert "API key not configured" in result.error_message

    @pytest.mark.asyncio
    async def test_perplexity_search_timeout(self, mock_settings):
        """Test handling of timeout errors."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch('app.tools.perplexity_tool.settings', mock_settings):
            with patch('app.tools.perplexity_tool.httpx.AsyncClient', return_value=mock_client):
                result = await perplexity_deep_search(query="test query")

        assert result.success is False
        assert "timeout" in result.error_message.lower()


class TestConfidenceCalculation:
    """Test confidence score calculation based on citations."""

    def test_confidence_no_citations(self):
        """Test confidence when no citations are provided."""
        confidence = _calculate_confidence([], None)
        assert confidence == 0.2  # Low confidence

    def test_confidence_with_authoritative_sources(self):
        """Test confidence boost for authoritative domains."""
        citations = [
            "https://sec.gov/filing1",
            "https://sec.gov/filing2",
            "https://bloomberg.com/article"
        ]
        confidence = _calculate_confidence(citations, None)

        # Base (0.5) + authority boost (0.3) = 0.8+
        assert confidence >= 0.7

    def test_confidence_with_domain_filter_match(self):
        """Test confidence boost when all citations match domain filter."""
        citations = [
            "https://sec.gov/filing1",
            "https://sec.gov/filing2"
        ]
        domain_filter = ["sec.gov"]

        confidence = _calculate_confidence(citations, domain_filter)

        # Base (0.5) + authority (0.2) + filter match (0.2) = 0.9+
        assert confidence >= 0.85

    def test_confidence_with_partial_filter_match(self):
        """Test confidence when only some citations match filter."""
        citations = [
            "https://sec.gov/filing1",
            "https://example.com/article"
        ]
        domain_filter = ["sec.gov"]

        confidence = _calculate_confidence(citations, domain_filter)

        # No filter match boost (not all citations match)
        assert confidence < 0.75

    def test_confidence_capped_at_95(self):
        """Test that confidence is capped at 0.95."""
        # Many authoritative citations
        citations = [
            "https://sec.gov/filing1",
            "https://sec.gov/filing2",
            "https://sec.gov/filing3",
            "https://sec.gov/filing4"
        ]
        domain_filter = ["sec.gov"]

        confidence = _calculate_confidence(citations, domain_filter)

        assert confidence <= 0.95

    def test_confidence_various_domains(self):
        """Test confidence calculation with various domain types."""
        # Government domains (.gov, .edu)
        gov_citations = ["https://sec.gov/file", "https://example.edu/paper"]
        gov_confidence = _calculate_confidence(gov_citations, None)

        # News domains
        news_citations = ["https://reuters.com/article", "https://ft.com/article"]
        news_confidence = _calculate_confidence(news_citations, None)

        # Unknown domains
        unknown_citations = ["https://blog.example.com/post"]
        unknown_confidence = _calculate_confidence(unknown_citations, None)

        # Government should have highest confidence
        assert gov_confidence > news_confidence > unknown_confidence

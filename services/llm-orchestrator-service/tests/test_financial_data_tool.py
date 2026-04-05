"""
Tests for Financial Data Lookup Tool

Coverage:
- Alpha Vantage API integration (mocked)
- Period matching logic
- Response parsing
- Error handling
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import httpx

from app.tools.financial_data_tool import (
    financial_data_lookup,
    _build_request,
    _parse_response,
    _matches_period
)


class TestFinancialDataTool:
    """Test financial data lookup tool."""

    @pytest.mark.asyncio
    async def test_financial_lookup_quote_success(
        self,
        mock_httpx_client,
        mock_alpha_vantage_quote_response,
        mock_settings
    ):
        """Test successful quote lookup."""
        mock_httpx_client.get = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value=mock_alpha_vantage_quote_response)
        mock_httpx_client.get.return_value = mock_response

        with patch('app.tools.financial_data_tool.settings', mock_settings):
            with patch('app.tools.financial_data_tool.httpx.AsyncClient', return_value=mock_httpx_client):
                result = await financial_data_lookup(
                    company="TSLA",
                    metric="quote"
                )

        assert result.success is True
        assert result.tool_name == "financial_data_lookup"
        assert result.confidence == 0.9  # High confidence for official data
        assert result.result_data["company"] == "TSLA"
        assert result.result_data["metric"] == "quote"
        assert "price" in result.result_data["data"]
        assert len(result.source_citations) > 0

    @pytest.mark.asyncio
    async def test_financial_lookup_earnings_success(
        self,
        mock_httpx_client,
        mock_alpha_vantage_earnings_response,
        mock_settings
    ):
        """Test successful earnings lookup."""
        mock_httpx_client.get = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value=mock_alpha_vantage_earnings_response)
        mock_httpx_client.get.return_value = mock_response

        with patch('app.tools.financial_data_tool.settings', mock_settings):
            with patch('app.tools.financial_data_tool.httpx.AsyncClient', return_value=mock_httpx_client):
                result = await financial_data_lookup(
                    company="TSLA",
                    metric="earnings",
                    period="Q3 2024"
                )

        assert result.success is True
        assert result.result_data["company"] == "TSLA"
        assert result.result_data["metric"] == "earnings"
        assert "reported_eps" in result.result_data["data"]
        assert result.result_data["data"]["fiscal_date_ending"] == "2024-09-30"

    @pytest.mark.asyncio
    async def test_financial_lookup_unknown_metric(self, mock_settings):
        """Test error handling for unknown metric."""
        with patch('app.tools.financial_data_tool.settings', mock_settings):
            result = await financial_data_lookup(
                company="TSLA",
                metric="invalid_metric"
            )

        assert result.success is False
        assert "Unknown metric" in result.error_message

    @pytest.mark.asyncio
    async def test_financial_lookup_api_error(self, mock_settings):
        """Test handling of Alpha Vantage API errors."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "500 Server Error",
                request=Mock(),
                response=mock_response
            )
        )
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch('app.tools.financial_data_tool.settings', mock_settings):
            with patch('app.tools.financial_data_tool.httpx.AsyncClient', return_value=mock_client):
                result = await financial_data_lookup(
                    company="TSLA",
                    metric="quote"
                )

        assert result.success is False
        assert "500" in result.error_message

    @pytest.mark.asyncio
    async def test_financial_lookup_rate_limit(self, mock_httpx_client, mock_settings):
        """Test handling of rate limit errors."""
        rate_limit_response = {
            "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute..."
        }

        mock_httpx_client.get = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value=rate_limit_response)
        mock_httpx_client.get.return_value = mock_response

        with patch('app.tools.financial_data_tool.settings', mock_settings):
            with patch('app.tools.financial_data_tool.httpx.AsyncClient', return_value=mock_httpx_client):
                result = await financial_data_lookup(
                    company="TSLA",
                    metric="quote"
                )

        assert result.success is False
        assert "rate limit" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_financial_lookup_demo_key_warning(self, mock_httpx_client, mock_settings):
        """Test warning when using demo API key."""
        # Remove API keys to trigger demo key usage
        mock_settings_no_key = mock_settings.model_copy()
        mock_settings_no_key.ALPHA_VANTAGE_API_KEY = None

        mock_httpx_client.get = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={"Global Quote": {}})
        mock_httpx_client.get.return_value = mock_response

        with patch('app.tools.financial_data_tool.settings', mock_settings_no_key):
            with patch('app.tools.financial_data_tool.httpx.AsyncClient', return_value=mock_httpx_client):
                result = await financial_data_lookup(
                    company="TSLA",
                    metric="quote"
                )

        # Verify demo key was used
        call_args = mock_httpx_client.get.call_args
        params = call_args[1]["params"]
        assert params["apikey"] == "demo"


class TestRequestBuilding:
    """Test Alpha Vantage request building."""

    def test_build_request_quote(self):
        """Test building quote request."""
        endpoint, params = _build_request("TSLA", "quote", "test-key")

        assert endpoint == "https://www.alphavantage.co/query"
        assert params["function"] == "GLOBAL_QUOTE"
        assert params["symbol"] == "TSLA"
        assert params["apikey"] == "test-key"

    def test_build_request_earnings(self):
        """Test building earnings request."""
        endpoint, params = _build_request("AAPL", "earnings", "test-key")

        assert params["function"] == "EARNINGS"
        assert params["symbol"] == "AAPL"

    def test_build_request_unknown_metric(self):
        """Test error for unknown metric."""
        with pytest.raises(ValueError, match="Unknown metric"):
            _build_request("TSLA", "unknown", "test-key")

    def test_build_request_case_insensitive(self):
        """Test that company ticker is uppercased."""
        endpoint, params = _build_request("tsla", "quote", "test-key")

        assert params["symbol"] == "TSLA"  # Should be uppercased


class TestResponseParsing:
    """Test Alpha Vantage response parsing."""

    def test_parse_quote_response(self, mock_alpha_vantage_quote_response):
        """Test parsing quote response."""
        parsed = _parse_response(mock_alpha_vantage_quote_response, "quote", None)

        assert parsed["symbol"] == "TSLA"
        assert parsed["price"] == "242.84"
        assert parsed["volume"] == "102847291"
        assert parsed["latest_trading_day"] == "2024-10-30"

    def test_parse_earnings_response_latest(self, mock_alpha_vantage_earnings_response):
        """Test parsing earnings response (latest quarter)."""
        parsed = _parse_response(mock_alpha_vantage_earnings_response, "earnings", None)

        # Should return latest quarter
        assert parsed["fiscal_date_ending"] == "2024-09-30"
        assert parsed["reported_eps"] == "2.17"
        assert parsed["surprise"] == "0.32"

    def test_parse_earnings_response_specific_period(self, mock_alpha_vantage_earnings_response):
        """Test parsing earnings response for specific period."""
        parsed = _parse_response(mock_alpha_vantage_earnings_response, "earnings", "Q3 2024")

        # Should return Q3 2024 data
        assert parsed["fiscal_date_ending"] == "2024-09-30"
        assert parsed["reported_eps"] == "2.17"

    def test_parse_earnings_response_q2(self, mock_alpha_vantage_earnings_response):
        """Test parsing earnings for Q2."""
        parsed = _parse_response(mock_alpha_vantage_earnings_response, "earnings", "Q2 2024")

        # Should return Q2 2024 data
        assert parsed["fiscal_date_ending"] == "2024-06-30"
        assert parsed["reported_eps"] == "1.91"

    def test_parse_earnings_response_no_match(self):
        """Test parsing earnings when period doesn't match."""
        response = {
            "quarterlyEarnings": [
                {"fiscalDateEnding": "2024-06-30", "reportedEPS": "1.91"}
            ]
        }

        parsed = _parse_response(response, "earnings", "Q1 2025")

        # No match found - should return empty dict
        assert parsed == {}


class TestPeriodMatching:
    """Test period matching logic."""

    def test_matches_period_q1(self):
        """Test Q1 period matching."""
        assert _matches_period("2024-03-31", "Q1 2024") is True
        assert _matches_period("2024-01-31", "Q1 2024") is True
        assert _matches_period("2024-06-30", "Q1 2024") is False

    def test_matches_period_q2(self):
        """Test Q2 period matching."""
        assert _matches_period("2024-06-30", "Q2 2024") is True
        assert _matches_period("2024-04-30", "Q2 2024") is True
        assert _matches_period("2024-09-30", "Q2 2024") is False

    def test_matches_period_q3(self):
        """Test Q3 period matching."""
        assert _matches_period("2024-09-30", "Q3 2024") is True
        assert _matches_period("2024-07-31", "Q3 2024") is True
        assert _matches_period("2024-12-31", "Q3 2024") is False

    def test_matches_period_q4(self):
        """Test Q4 period matching."""
        assert _matches_period("2024-12-31", "Q4 2024") is True
        assert _matches_period("2024-10-31", "Q4 2024") is True
        assert _matches_period("2024-03-31", "Q4 2024") is False

    def test_matches_period_case_insensitive(self):
        """Test that period matching is case-insensitive."""
        assert _matches_period("2024-09-30", "q3 2024") is True
        assert _matches_period("2024-09-30", "Q3 2024") is True

    def test_matches_period_invalid_inputs(self):
        """Test handling of invalid inputs."""
        assert _matches_period(None, "Q3 2024") is False
        assert _matches_period("2024-09-30", None) is False
        assert _matches_period("2024-09-30", "Invalid") is False

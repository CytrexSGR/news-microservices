"""Tests for FMP client symbol resolution."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.clients.fmp import FMPClient


class TestFMPClientSymbolResolution:
    """Test FMP client resolves symbol aliases."""

    @pytest.fixture
    def fmp_client(self):
        """Create FMP client instance."""
        return FMPClient()

    @pytest.mark.asyncio
    async def test_get_quote_resolves_gold_alias(self, fmp_client):
        """get_quote('GOLD') should call FMP with 'GCUSD'."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            # Use MagicMock for response since json() is synchronous
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"symbol": "GCUSD", "price": 4982}
            mock_get.return_value = mock_response

            result = await fmp_client.get_quote("GOLD")

            # Verify the client called with resolved symbol
            mock_get.assert_called_once_with("/api/v1/market/quotes/GCUSD")
            assert result["symbol"] == "GCUSD"

    @pytest.mark.asyncio
    async def test_get_quote_passes_through_unknown_symbol(self, fmp_client):
        """get_quote('AAPL') should call FMP with 'AAPL' unchanged."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"symbol": "AAPL", "price": 150}
            mock_get.return_value = mock_response

            result = await fmp_client.get_quote("AAPL")

            mock_get.assert_called_once_with("/api/v1/market/quotes/AAPL")
            assert result["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_get_quote_resolves_oil_alias(self, fmp_client):
        """get_quote('OIL') should call FMP with 'CLUSD'."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"symbol": "CLUSD", "price": 61}
            mock_get.return_value = mock_response

            result = await fmp_client.get_quote("OIL")

            mock_get.assert_called_once_with("/api/v1/market/quotes/CLUSD")
            assert result["symbol"] == "CLUSD"

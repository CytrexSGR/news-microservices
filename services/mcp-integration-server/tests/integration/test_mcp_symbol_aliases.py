"""
Integration tests for MCP symbol alias resolution.

These tests verify the end-to-end flow from MCP tool to FMP service.
Requires: fmp-service running (uses app settings for URL)

Run with:
    cd services/mcp-integration-server
    python -m pytest tests/integration/test_mcp_symbol_aliases.py -v -m integration

    # Or inside Docker:
    docker compose exec mcp-integration-server python -m pytest tests/integration/ -v
"""
import pytest
import httpx

from app.clients.fmp import FMPClient
from app.clients.symbol_aliases import resolve_symbol_alias, COMMODITY_ALIASES
from app.config import settings


def is_fmp_service_available() -> bool:
    """
    Check if FMP service is available.

    Uses the same FMP service URL configured in app settings.
    """
    try:
        health_url = f"{settings.fmp_service_url}/api/v1/system/health"
        response = httpx.get(health_url, timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# Check service availability once at module load
_fmp_available = is_fmp_service_available()

# Skip entire module if FMP service is not available
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _fmp_available,
        reason=f"FMP service not available at {settings.fmp_service_url}"
    ),
]


class TestMCPSymbolAliasIntegration:
    """Integration tests for symbol aliases."""

    @pytest.fixture
    def fmp_client(self):
        """Create real FMP client."""
        return FMPClient()

    @pytest.mark.asyncio
    async def test_gold_alias_returns_quote(self, fmp_client):
        """
        get_quote('GOLD') should return GCUSD data.

        This tests the full flow:
        1. User calls get_market_quote("GOLD")
        2. MCP resolves GOLD -> GCUSD
        3. FMP service returns gold futures quote
        """
        try:
            result = await fmp_client.get_quote("GOLD")

            # Verify we got gold data
            assert result["symbol"] == "GCUSD"
            assert "price" in result
            # FMP API returns price as string, convert for comparison
            assert float(result["price"]) > 0
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip("FMP service does not have GCUSD data")
            raise

    @pytest.mark.asyncio
    async def test_silver_alias_returns_quote(self, fmp_client):
        """
        get_quote('SILVER') should return SIUSD data.
        """
        try:
            result = await fmp_client.get_quote("SILVER")

            assert result["symbol"] == "SIUSD"
            assert "price" in result
            # FMP API returns price as string, convert for comparison
            assert float(result["price"]) > 0
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip("FMP service does not have SIUSD data")
            raise

    @pytest.mark.asyncio
    async def test_oil_alias_returns_quote(self, fmp_client):
        """
        get_quote('OIL') should return CLUSD (WTI Crude) data.
        """
        try:
            result = await fmp_client.get_quote("OIL")

            assert result["symbol"] == "CLUSD"
            assert "price" in result
            # FMP API returns price as string, convert for comparison
            assert float(result["price"]) > 0
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip("FMP service does not have CLUSD data")
            raise

    @pytest.mark.asyncio
    async def test_all_commodity_aliases_resolve_correctly(self):
        """Verify all commodity aliases map to valid FMP symbols."""
        for alias, fmp_symbol in COMMODITY_ALIASES.items():
            resolved = resolve_symbol_alias(alias)
            assert resolved == fmp_symbol, f"{alias} should resolve to {fmp_symbol}"

    @pytest.mark.asyncio
    async def test_lowercase_alias_resolves(self):
        """Verify lowercase aliases also resolve correctly."""
        assert resolve_symbol_alias("gold") == "GCUSD"
        assert resolve_symbol_alias("silver") == "SIUSD"
        assert resolve_symbol_alias("oil") == "CLUSD"

    @pytest.mark.asyncio
    async def test_direct_gcusd_still_works(self, fmp_client):
        """Direct GCUSD queries should still work."""
        try:
            result = await fmp_client.get_quote("GCUSD")
            assert result["symbol"] == "GCUSD"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip("FMP service does not have GCUSD data")
            raise

    @pytest.mark.asyncio
    async def test_unknown_symbol_passes_through(self, fmp_client):
        """Unknown symbols should pass through unchanged."""
        # Test with a common stock symbol
        try:
            result = await fmp_client.get_quote("AAPL")
            # If AAPL is available, symbol should be AAPL (not an alias)
            assert result["symbol"] == "AAPL"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip("FMP service does not have AAPL data")
            raise

    @pytest.mark.asyncio
    async def test_already_resolved_symbol_unchanged(self):
        """
        Already-resolved FMP symbols should pass through unchanged.

        This ensures the resolution is idempotent.
        """
        # Direct FMP symbols should remain unchanged
        assert resolve_symbol_alias("GCUSD") == "GCUSD"
        assert resolve_symbol_alias("SIUSD") == "SIUSD"
        assert resolve_symbol_alias("CLUSD") == "CLUSD"
        assert resolve_symbol_alias("HGUSD") == "HGUSD"
        assert resolve_symbol_alias("NGUSD") == "NGUSD"

    @pytest.mark.asyncio
    async def test_energy_aliases_resolve_consistently(self):
        """
        Verify energy commodity aliases (OIL, CRUDE, WTI) all resolve to CLUSD.
        """
        energy_aliases = ["OIL", "CRUDE", "CRUDEOIL", "WTI"]
        for alias in energy_aliases:
            resolved = resolve_symbol_alias(alias)
            assert resolved == "CLUSD", f"{alias} should resolve to CLUSD, got {resolved}"

    @pytest.mark.asyncio
    async def test_gas_aliases_resolve_consistently(self):
        """
        Verify natural gas aliases (NATGAS, GAS, NATURALGAS) all resolve to NGUSD.
        """
        gas_aliases = ["NATGAS", "GAS", "NATURALGAS"]
        for alias in gas_aliases:
            resolved = resolve_symbol_alias(alias)
            assert resolved == "NGUSD", f"{alias} should resolve to NGUSD, got {resolved}"

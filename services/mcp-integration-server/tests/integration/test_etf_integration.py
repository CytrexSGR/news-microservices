"""
Integration tests for ETF MCP tools.

These tests verify the end-to-end flow from MCP tool to FMP service for ETF data.
Requires: fmp-service running with seeded ETF data (15 ETFs from Task 4)

Run with:
    cd services/mcp-integration-server
    python -m pytest tests/integration/test_etf_integration.py -v -m integration

    # Or inside Docker:
    docker compose exec mcp-integration-server python -m pytest tests/integration/test_etf_integration.py -v
"""
import pytest
import httpx

from app.clients.fmp import FMPClient
from app.mcp.tools import search_etfs, get_etf_details
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


class TestETFSearchIntegration:
    """Integration tests for ETF search functionality."""

    @pytest.fixture
    def fmp_client(self):
        """Create real FMP client."""
        return FMPClient()

    @pytest.mark.asyncio
    async def test_search_defense_etfs_via_client(self, fmp_client):
        """
        Test searching ETFs by sector=Defense via FMPClient.

        Should find VanEck Defense (NATO) ETF.
        """
        result = await fmp_client.search_etfs(sector="Defense")

        assert "etfs" in result
        assert "count" in result
        assert result["count"] >= 1

        # Verify we found the NATO ETF
        tickers = [e["ticker"] for e in result["etfs"]]
        assert "NATO" in tickers, "NATO ETF should be found for Defense sector"

        # Verify sector is Defense for all returned ETFs
        for etf in result["etfs"]:
            assert etf["sector"] == "Defense"

    @pytest.mark.asyncio
    async def test_search_rare_earth_etfs_via_client(self, fmp_client):
        """
        Test searching ETFs by theme="Rare Earth" via FMPClient.

        Should find REMX ETF.
        """
        result = await fmp_client.search_etfs(theme="Rare Earth")

        assert "etfs" in result
        assert result["count"] >= 1

        # Verify we found the REMX ETF
        tickers = [e["ticker"] for e in result["etfs"]]
        assert "REMX" in tickers, "REMX ETF should be found for Rare Earth theme"

    @pytest.mark.asyncio
    async def test_search_ai_etfs_via_client(self, fmp_client):
        """
        Test searching ETFs by theme="AI" via FMPClient.

        Should find WisdomTree AI ETF (WTAI).
        """
        result = await fmp_client.search_etfs(theme="AI")

        assert "etfs" in result
        assert result["count"] >= 1

        # Verify we found AI-related ETFs
        tickers = [e["ticker"] for e in result["etfs"]]
        assert "WTAI" in tickers, "WTAI ETF should be found for AI theme"

    @pytest.mark.asyncio
    async def test_search_etfs_by_keyword(self, fmp_client):
        """
        Test searching ETFs by keyword via FMPClient.

        Should find ETFs matching search term.
        """
        result = await fmp_client.search_etfs(search="VanEck")

        assert "etfs" in result
        assert result["count"] >= 1

        # All results should have VanEck in name or issuer
        for etf in result["etfs"]:
            assert (
                "VanEck" in etf["name"] or etf["issuer"] == "VanEck"
            ), f"ETF {etf['ticker']} should have VanEck in name or as issuer"

    @pytest.mark.asyncio
    async def test_search_etfs_with_limit(self, fmp_client):
        """
        Test ETF search respects limit parameter.
        """
        result = await fmp_client.search_etfs(limit=2)

        assert "etfs" in result
        assert len(result["etfs"]) <= 2


class TestETFDetailsIntegration:
    """Integration tests for ETF details functionality."""

    @pytest.fixture
    def fmp_client(self):
        """Create real FMP client."""
        return FMPClient()

    @pytest.mark.asyncio
    async def test_get_etf_by_isin_nato(self, fmp_client):
        """
        Test getting NATO ETF by ISIN via FMPClient.

        ISIN: IE000YYE6WK5 should return VanEck Defense UCITS ETF.
        """
        result = await fmp_client.get_etf(isin="IE000YYE6WK5")

        assert result["isin"] == "IE000YYE6WK5"
        assert result["ticker"] == "NATO"
        assert result["name"] == "VanEck Defense UCITS ETF"
        assert result["sector"] == "Defense"
        assert result["theme"] == "NATO/Military"
        assert result["issuer"] == "VanEck"
        assert result["domicile"] == "Ireland"
        assert result["replication"] == "Physical"
        assert result["distribution"] == "Accumulating"

    @pytest.mark.asyncio
    async def test_get_etf_by_isin_remx(self, fmp_client):
        """
        Test getting REMX ETF by ISIN via FMPClient.

        ISIN: IE00BMC38736 should return VanEck Rare Earth ETF.
        """
        result = await fmp_client.get_etf(isin="IE00BMC38736")

        assert result["isin"] == "IE00BMC38736"
        assert result["ticker"] == "REMX"
        assert result["sector"] == "Materials"
        assert result["theme"] == "Rare Earth"

    @pytest.mark.asyncio
    async def test_get_etf_by_isin_with_holdings(self, fmp_client):
        """
        Test getting ETF with top_holdings data.

        NATO ETF should have top holdings populated.
        """
        result = await fmp_client.get_etf(isin="IE000YYE6WK5")

        assert "top_holdings" in result
        assert result["top_holdings"] is not None
        assert len(result["top_holdings"]) > 0

        # Check holding structure
        first_holding = result["top_holdings"][0]
        assert "ticker" in first_holding
        assert "name" in first_holding
        assert "weight" in first_holding

    @pytest.mark.asyncio
    async def test_get_etf_invalid_isin(self, fmp_client):
        """
        Test getting ETF with invalid ISIN returns 404.
        """
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await fmp_client.get_etf(isin="INVALID_ISIN_12345")

        assert exc_info.value.response.status_code == 404


class TestETFMCPToolsIntegration:
    """Integration tests for ETF MCP tools."""

    @pytest.fixture
    def fmp_client(self):
        """Create real FMP client."""
        return FMPClient()

    @pytest.mark.asyncio
    async def test_search_etfs_tool_defense_sector(self, fmp_client):
        """
        Test search_etfs MCP tool with sector="Defense".

        Should return successful result with NATO ETF.
        """
        result = await search_etfs(sector="Defense", client=fmp_client)

        assert result.success is True
        assert result.data["count"] >= 1
        assert result.metadata["tool"] == "search_etfs"
        assert result.metadata["filters"]["sector"] == "Defense"

        # Should find VanEck Defense
        tickers = [e["ticker"] for e in result.data["etfs"]]
        assert "NATO" in tickers or any(
            "defense" in e["name"].lower() for e in result.data["etfs"]
        )

    @pytest.mark.asyncio
    async def test_search_etfs_tool_rare_earth_theme(self, fmp_client):
        """
        Test search_etfs MCP tool with theme="Rare Earth".

        Should return successful result with REMX ETF.
        """
        result = await search_etfs(theme="Rare Earth", client=fmp_client)

        assert result.success is True
        assert result.data["count"] >= 1
        assert result.metadata["filters"]["theme"] == "Rare Earth"

        # Should find REMX
        tickers = [e["ticker"] for e in result.data["etfs"]]
        assert "REMX" in tickers

    @pytest.mark.asyncio
    async def test_search_etfs_tool_with_search(self, fmp_client):
        """
        Test search_etfs MCP tool with search parameter.
        """
        result = await search_etfs(search="Semiconductor", client=fmp_client)

        assert result.success is True
        assert result.metadata["filters"]["search"] == "Semiconductor"

    @pytest.mark.asyncio
    async def test_get_etf_details_tool(self, fmp_client):
        """
        Test get_etf_details MCP tool with valid ISIN.

        Should return NATO ETF details.
        """
        result = await get_etf_details(isin="IE000YYE6WK5", client=fmp_client)

        assert result.success is True
        assert result.data["ticker"] == "NATO"
        assert result.data["sector"] == "Defense"
        assert result.metadata["tool"] == "get_etf_details"
        assert result.metadata["isin"] == "IE000YYE6WK5"

    @pytest.mark.asyncio
    async def test_get_etf_details_tool_invalid_isin(self, fmp_client):
        """
        Test get_etf_details MCP tool with invalid ISIN.

        Should return unsuccessful result with error.
        """
        result = await get_etf_details(isin="INVALID_ISIN", client=fmp_client)

        assert result.success is False
        assert result.error is not None


class TestETFDataQuality:
    """Integration tests for ETF data quality and completeness."""

    @pytest.fixture
    def fmp_client(self):
        """Create real FMP client."""
        return FMPClient()

    @pytest.mark.asyncio
    async def test_all_seeded_etfs_retrievable(self, fmp_client):
        """
        Verify all 15 seeded ETFs are retrievable.
        """
        result = await fmp_client.search_etfs(limit=50)

        # We seeded 15 ETFs in Task 4
        assert result["count"] >= 15, f"Expected at least 15 ETFs, got {result['count']}"

    @pytest.mark.asyncio
    async def test_etf_data_has_required_fields(self, fmp_client):
        """
        Verify ETF data has all required fields.
        """
        result = await fmp_client.get_etf(isin="IE000YYE6WK5")

        required_fields = [
            "isin", "ticker", "name", "issuer", "sector", "theme",
            "ter", "currency", "domicile", "replication", "distribution"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_sectors_available(self, fmp_client):
        """
        Verify expected sectors exist in ETF data.
        """
        expected_sectors = ["Defense", "Tech", "Materials", "Healthcare", "Energy"]

        for sector in expected_sectors:
            result = await fmp_client.search_etfs(sector=sector)
            assert result["count"] >= 1, f"No ETFs found for sector: {sector}"

    @pytest.mark.asyncio
    async def test_themes_available(self, fmp_client):
        """
        Verify expected themes exist in ETF data.
        """
        expected_themes = [
            "NATO/Military", "AI", "Rare Earth", "Semiconductors",
            "Clean Energy", "Cybersecurity"
        ]

        for theme in expected_themes:
            result = await fmp_client.search_etfs(theme=theme)
            assert result["count"] >= 1, f"No ETFs found for theme: {theme}"

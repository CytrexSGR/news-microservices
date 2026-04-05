"""Tests for ETF MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.clients.fmp import FMPClient


class TestETFMCPTools:
    """Test ETF MCP tool registration and execution."""

    def test_search_etfs_tool_registered(self):
        """Test search_etfs MCP tool is registered."""
        from app.mcp.tools import tool_registry

        assert "search_etfs" in tool_registry
        tool_def = tool_registry["search_etfs"]["definition"]
        assert tool_def.category == "market"
        assert tool_def.service == "fmp-service"

        # Check parameters
        param_names = [p.name for p in tool_def.parameters]
        assert "sector" in param_names
        assert "theme" in param_names
        assert "search" in param_names
        assert "limit" in param_names

    def test_get_etf_details_tool_registered(self):
        """Test get_etf_details MCP tool is registered."""
        from app.mcp.tools import tool_registry

        assert "get_etf_details" in tool_registry
        tool_def = tool_registry["get_etf_details"]["definition"]
        assert tool_def.category == "market"
        assert tool_def.service == "fmp-service"

        # Check parameters
        param_names = [p.name for p in tool_def.parameters]
        assert "isin" in param_names


class TestFMPClientETFMethods:
    """Test FMPClient ETF methods."""

    @pytest.fixture
    def fmp_client(self):
        """Create FMP client instance."""
        return FMPClient()

    @pytest.mark.asyncio
    async def test_search_etfs_by_sector(self, fmp_client):
        """Test searching ETFs by sector."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "etfs": [{"ticker": "NATO", "name": "VanEck Defense", "sector": "Defense"}],
                "count": 1,
                "filters": {"sector": "Defense", "theme": None, "search": None},
            }
            mock_get.return_value = mock_response

            result = await fmp_client.search_etfs(sector="Defense")

            mock_get.assert_called_once_with(
                "/api/v1/etfs",
                params={"limit": 20, "sector": "Defense"}
            )
            assert result["count"] == 1
            assert result["etfs"][0]["ticker"] == "NATO"

    @pytest.mark.asyncio
    async def test_search_etfs_by_theme(self, fmp_client):
        """Test searching ETFs by theme."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "etfs": [{"ticker": "WTAI", "name": "WisdomTree AI", "theme": "AI"}],
                "count": 1,
            }
            mock_get.return_value = mock_response

            result = await fmp_client.search_etfs(theme="AI")

            mock_get.assert_called_once_with(
                "/api/v1/etfs",
                params={"limit": 20, "theme": "AI"}
            )
            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_search_etfs_by_keyword(self, fmp_client):
        """Test searching ETFs by keyword."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "etfs": [{"ticker": "SMH", "name": "VanEck Semiconductor"}],
                "count": 1,
            }
            mock_get.return_value = mock_response

            result = await fmp_client.search_etfs(search="NVIDIA")

            mock_get.assert_called_once_with(
                "/api/v1/etfs",
                params={"limit": 20, "search": "NVIDIA"}
            )
            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_search_etfs_with_limit(self, fmp_client):
        """Test searching ETFs with custom limit."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"etfs": [], "count": 0}
            mock_get.return_value = mock_response

            await fmp_client.search_etfs(sector="Tech", limit=50)

            mock_get.assert_called_once_with(
                "/api/v1/etfs",
                params={"limit": 50, "sector": "Tech"}
            )

    @pytest.mark.asyncio
    async def test_get_etf_by_isin(self, fmp_client):
        """Test getting ETF by ISIN."""
        with patch.object(fmp_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "isin": "IE000YYE6WK5",
                "ticker": "NATO",
                "name": "VanEck Defense UCITS ETF",
                "sector": "Defense",
                "theme": "NATO/Military",
                "top_holdings": [
                    {"ticker": "RHM.DE", "name": "Rheinmetall", "weight": 8.5},
                ],
            }
            mock_get.return_value = mock_response

            result = await fmp_client.get_etf(isin="IE000YYE6WK5")

            mock_get.assert_called_once_with("/api/v1/etfs/IE000YYE6WK5")
            assert result["isin"] == "IE000YYE6WK5"
            assert result["ticker"] == "NATO"
            assert result["sector"] == "Defense"
            assert len(result["top_holdings"]) == 1


class TestSearchETFsTool:
    """Test search_etfs MCP tool execution."""

    @pytest.mark.asyncio
    async def test_search_etfs_tool_success(self):
        """Test search_etfs tool returns successful result."""
        from app.mcp.tools import search_etfs

        mock_client = MagicMock(spec=FMPClient)
        mock_client.search_etfs = AsyncMock(return_value={
            "etfs": [{"ticker": "NATO", "name": "VanEck Defense", "sector": "Defense"}],
            "count": 1,
        })

        result = await search_etfs(sector="Defense", client=mock_client)

        assert result.success is True
        assert result.data["count"] == 1
        assert result.metadata["tool"] == "search_etfs"
        assert result.metadata["filters"]["sector"] == "Defense"

    @pytest.mark.asyncio
    async def test_search_etfs_tool_error_handling(self):
        """Test search_etfs tool handles errors gracefully."""
        from app.mcp.tools import search_etfs

        mock_client = MagicMock(spec=FMPClient)
        mock_client.search_etfs = AsyncMock(side_effect=Exception("FMP service unavailable"))

        result = await search_etfs(sector="Defense", client=mock_client)

        assert result.success is False
        assert "FMP service unavailable" in result.error


class TestGetETFDetailsTool:
    """Test get_etf_details MCP tool execution."""

    @pytest.mark.asyncio
    async def test_get_etf_details_tool_success(self):
        """Test get_etf_details tool returns successful result."""
        from app.mcp.tools import get_etf_details

        mock_client = MagicMock(spec=FMPClient)
        mock_client.get_etf = AsyncMock(return_value={
            "isin": "IE000YYE6WK5",
            "ticker": "NATO",
            "name": "VanEck Defense UCITS ETF",
            "sector": "Defense",
        })

        result = await get_etf_details(isin="IE000YYE6WK5", client=mock_client)

        assert result.success is True
        assert result.data["isin"] == "IE000YYE6WK5"
        assert result.data["ticker"] == "NATO"
        assert result.metadata["tool"] == "get_etf_details"
        assert result.metadata["isin"] == "IE000YYE6WK5"

    @pytest.mark.asyncio
    async def test_get_etf_details_tool_not_found(self):
        """Test get_etf_details tool handles 404 errors."""
        from app.mcp.tools import get_etf_details

        mock_client = MagicMock(spec=FMPClient)
        mock_client.get_etf = AsyncMock(side_effect=Exception("ETF not found"))

        result = await get_etf_details(isin="INVALID_ISIN", client=mock_client)

        assert result.success is False
        assert "ETF not found" in result.error

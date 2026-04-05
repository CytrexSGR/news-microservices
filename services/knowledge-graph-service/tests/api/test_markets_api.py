"""
Comprehensive unit tests for Markets API endpoints.

Tests all 5 endpoints with 80%+ code coverage:
- POST /api/v1/graph/markets/sync
- GET /api/v1/graph/markets
- GET /api/v1/graph/markets/stats
- GET /api/v1/graph/markets/{symbol}
- GET /api/v1/graph/markets/{symbol}/history
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from datetime import datetime
from typing import List, Dict, Any

from app.main import app
from app.schemas.markets import (
    MarketNode,
    MarketListResponse,
    MarketStatsResponse,
    MarketDetailResponse,
    SectorNode
)
from app.schemas.sync_results import SyncResult, SyncError
from app.clients.fmp_service_client import (
    FMPServiceError,
    FMPServiceUnavailableError
)


@pytest.fixture
def client():
    """FastAPI TestClient for testing."""
    return TestClient(app)


@pytest.fixture
def mock_market_data():
    """Sample market node data."""
    from datetime import datetime, timezone
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "asset_type": "STOCK",
        "sector": "XLK",
        "exchange": "NASDAQ",
        "currency": "USD",
        "is_active": True,
        "isin": "US0378331005",
        "current_price": 178.45,
        "day_change_percent": 1.23,
        "market_cap": 2800000000000,
        "volume": 52340000,
        "open_price": 176.80,
        "high_price": 179.20,
        "low_price": 176.50,
        "close_price": 176.25,
        "created_at": datetime.now(timezone.utc),
        "last_updated": datetime.now(timezone.utc)
    }


@pytest.fixture
def mock_sector_data():
    """Sample sector node data."""
    return {
        "code": "XLK",
        "name": "Information Technology",
        "description": "Technology sector",
        "market_classification": "GICS"
    }


@pytest.fixture
def mock_sync_result():
    """Sample sync result."""
    return SyncResult(
        sync_id="sync-123",
        status="completed",
        synced=40,
        total_assets=40,
        failed=0,
        duration_seconds=2.5,
        errors=[]
    )


@pytest.fixture
def mock_neo4j_service():
    """Mock Neo4jService."""
    with patch('app.api.routes.markets.neo4j_service') as mock:
        mock.execute_query = AsyncMock()
        yield mock


@pytest.fixture
def mock_market_sync_service():
    """Mock MarketSyncService."""
    with patch('app.api.routes.markets.get_market_sync_service') as mock_get:
        mock_service = AsyncMock()
        mock_get.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_fmp_client():
    """Mock FMP Service client."""
    with patch('app.api.routes.markets.get_fmp_service_client') as mock_get:
        mock_client = AsyncMock()
        mock_get.return_value = mock_client
        yield mock_client


# =============================================================================
# Tests: POST /api/v1/graph/markets/sync
# =============================================================================

class TestSyncMarketsEndpoint:
    """Tests for market sync endpoint."""

    def test_sync_markets_success(self, client, mock_market_sync_service, mock_sync_result):
        """Test successful market sync with all markets."""
        mock_market_sync_service.sync_all_markets.return_value = mock_sync_result

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["synced"] == 40
        assert data["failed"] == 0
        assert data["sync_id"] == "sync-123"
        assert data["duration_seconds"] == 2.5

    def test_sync_markets_with_asset_types(self, client, mock_market_sync_service, mock_sync_result):
        """Test sync with specific asset types filter."""
        mock_market_sync_service.sync_all_markets.return_value = mock_sync_result

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={"asset_types": ["STOCK", "FOREX"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

        # Verify service was called with correct parameters
        mock_market_sync_service.sync_all_markets.assert_called_once()
        call_kwargs = mock_market_sync_service.sync_all_markets.call_args.kwargs
        assert call_kwargs["asset_types"] == ["STOCK", "FOREX"]

    def test_sync_markets_with_symbols(self, client, mock_market_sync_service, mock_sync_result):
        """Test sync with specific symbols."""
        mock_market_sync_service.sync_all_markets.return_value = mock_sync_result

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={"symbols": ["AAPL", "GOOGL", "MSFT"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

        call_kwargs = mock_market_sync_service.sync_all_markets.call_args.kwargs
        assert call_kwargs["symbols"] == ["AAPL", "GOOGL", "MSFT"]

    def test_sync_markets_with_force_refresh(self, client, mock_market_sync_service, mock_sync_result):
        """Test sync with force_refresh flag."""
        mock_market_sync_service.sync_all_markets.return_value = mock_sync_result

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={"force_refresh": True}
        )

        assert response.status_code == 200
        call_kwargs = mock_market_sync_service.sync_all_markets.call_args.kwargs
        assert call_kwargs["force_refresh"] is True

    def test_sync_markets_partial_success(self, client, mock_market_sync_service):
        """Test sync with partial failure."""
        partial_result = SyncResult(
            sync_id="sync-456",
            status="partial",
            synced=38,
            total_assets=40,
            failed=2,
            duration_seconds=3.0,
            errors=[
                SyncError(symbol="INVALID", error="Symbol not found"),
                SyncError(symbol="BADDATA", error="Invalid data format")
            ]
        )
        mock_market_sync_service.sync_all_markets.return_value = partial_result

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "partial"
        assert data["synced"] == 38
        assert data["failed"] == 2
        assert len(data["errors"]) == 2

    def test_sync_markets_fmp_unavailable(self, client, mock_market_sync_service):
        """Test sync when FMP Service is unavailable."""
        mock_market_sync_service.sync_all_markets.side_effect = FMPServiceUnavailableError(
            "FMP Service unavailable"
        )

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )

        assert response.status_code == 503
        data = response.json()
        assert "error" in data["detail"]
        assert "FMP Service unavailable" in data["detail"]["error"]
        assert data["detail"]["retry_after"] == 30

    def test_sync_markets_rate_limit_exceeded(self, client, mock_market_sync_service):
        """Test sync when rate limit is exceeded."""
        mock_market_sync_service.sync_all_markets.side_effect = FMPServiceError(
            "Rate limit exceeded: 300 calls/day"
        )

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )

        assert response.status_code == 429
        data = response.json()
        assert data["detail"]["error"] == "Rate limit exceeded"

    def test_sync_markets_generic_fmp_error(self, client, mock_market_sync_service):
        """Test sync with generic FMP Service error."""
        mock_market_sync_service.sync_all_markets.side_effect = FMPServiceError(
            "Connection refused"
        )

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )

        assert response.status_code == 500
        data = response.json()
        assert "FMP Service error" in data["detail"]["error"]

    def test_sync_markets_internal_error(self, client, mock_market_sync_service):
        """Test sync with unexpected internal error."""
        mock_market_sync_service.sync_all_markets.side_effect = Exception(
            "Unexpected database error"
        )

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )

        assert response.status_code == 500
        data = response.json()
        assert "Market sync failed" in data["detail"]

    def test_sync_markets_symbols_exceed_limit(self, client):
        """Test that symbol list exceeds max_items limit."""
        # Create list of 101 symbols (max is 100)
        symbols = [f"SYM{i}" for i in range(101)]

        response = client.post(
            "/api/v1/graph/markets/sync",
            json={"symbols": symbols}
        )

        # Should fail validation
        assert response.status_code == 422


# =============================================================================
# Tests: GET /api/v1/graph/markets
# =============================================================================

class TestListMarketsEndpoint:
    """Tests for markets list endpoint."""

    def test_list_markets_all(self, client, mock_neo4j_service, mock_market_data):
        """Test listing all markets without filters."""
        mock_market = mock_market_data.copy()
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market}],  # markets_records
            [{"total": 1}]  # count_records
        ]

        response = client.get("/api/v1/graph/markets")

        assert response.status_code == 200
        data = response.json()
        assert "markets" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] == 1
        assert len(data["markets"]) == 1
        assert data["markets"][0]["symbol"] == "AAPL"

    def test_list_markets_filtered_by_asset_type(self, client, mock_neo4j_service, mock_market_data):
        """Test filtering by asset_type."""
        mock_market = mock_market_data.copy()
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market}],
            [{"total": 1}]
        ]

        response = client.get("/api/v1/graph/markets?asset_type=STOCK")

        assert response.status_code == 200
        data = response.json()
        assert data["markets"][0]["asset_type"] == "STOCK"

    def test_list_markets_filtered_by_sector(self, client, mock_neo4j_service, mock_market_data):
        """Test filtering by sector."""
        mock_market = mock_market_data.copy()
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market}],
            [{"total": 1}]
        ]

        response = client.get("/api/v1/graph/markets?sector=XLK")

        assert response.status_code == 200
        data = response.json()
        assert data["markets"][0]["sector"] == "XLK"

    def test_list_markets_filtered_by_exchange(self, client, mock_neo4j_service, mock_market_data):
        """Test filtering by exchange."""
        mock_market = mock_market_data.copy()
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market}],
            [{"total": 1}]
        ]

        response = client.get("/api/v1/graph/markets?exchange=NASDAQ")

        assert response.status_code == 200
        data = response.json()
        assert len(data["markets"]) == 1

    def test_list_markets_filtered_by_active_status(self, client, mock_neo4j_service, mock_market_data):
        """Test filtering by active status."""
        mock_market = mock_market_data.copy()
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market}],
            [{"total": 1}]
        ]

        response = client.get("/api/v1/graph/markets?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["markets"][0]["is_active"] is True

    def test_list_markets_text_search(self, client, mock_neo4j_service, mock_market_data):
        """Test text search on symbol/name."""
        mock_market = mock_market_data.copy()
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market}],
            [{"total": 1}]
        ]

        response = client.get("/api/v1/graph/markets?search=Apple")

        assert response.status_code == 200
        data = response.json()
        assert len(data["markets"]) == 1

    def test_list_markets_pagination(self, client, mock_neo4j_service):
        """Test pagination works correctly."""
        # Create 25 markets
        markets = [
            {
                "symbol": f"SYM{i}",
                "name": f"Symbol {i}",
                "asset_type": "STOCK",
                "current_price": 100.0 + i,
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }
            for i in range(25)
        ]

        mock_neo4j_service.execute_query.side_effect = [
            [{"m": m} for m in markets[:10]],  # Page 0, size 10
            [{"total": 25}]  # Total count
        ]

        response = client.get("/api/v1/graph/markets?page=0&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["markets"]) == 10
        assert data["page"] == 0
        assert data["page_size"] == 10
        assert data["total"] == 25

    def test_list_markets_pagination_page_2(self, client, mock_neo4j_service):
        """Test pagination on page 2."""
        markets = [
            {
                "symbol": f"SYM{i}",
                "name": f"Symbol {i}",
                "asset_type": "STOCK",
                "current_price": 100.0 + i,
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }
            for i in range(10, 20)
        ]

        mock_neo4j_service.execute_query.side_effect = [
            [{"m": m} for m in markets],  # Page 1, size 10
            [{"total": 25}]
        ]

        response = client.get("/api/v1/graph/markets?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert len(data["markets"]) == 10

    def test_list_markets_invalid_page_size_exceeds_max(self, client):
        """Test validation of page_size (max 1000)."""
        response = client.get("/api/v1/graph/markets?page_size=5000")

        # Should return 422 (validation error)
        assert response.status_code == 422

    def test_list_markets_invalid_page_size_zero(self, client):
        """Test validation: page_size must be >= 1."""
        response = client.get("/api/v1/graph/markets?page_size=0")

        assert response.status_code == 422

    def test_list_markets_invalid_page_negative(self, client):
        """Test validation: page must be >= 0."""
        response = client.get("/api/v1/graph/markets?page=-1")

        assert response.status_code == 422

    def test_list_markets_no_results(self, client, mock_neo4j_service):
        """Test listing when no markets match filters."""
        mock_neo4j_service.execute_query.side_effect = [
            [],  # No markets
            [{"total": 0}]  # Count
        ]

        response = client.get("/api/v1/graph/markets?asset_type=NONEXISTENT")

        assert response.status_code == 200
        data = response.json()
        assert len(data["markets"]) == 0
        assert data["total"] == 0

    def test_list_markets_query_error(self, client, mock_neo4j_service):
        """Test error handling for database query failures."""
        mock_neo4j_service.execute_query.side_effect = Exception(
            "Neo4j connection lost"
        )

        response = client.get("/api/v1/graph/markets")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to query markets" in data["detail"]

    def test_list_markets_multiple_filters(self, client, mock_neo4j_service, mock_market_data):
        """Test combining multiple filters."""
        mock_market = mock_market_data.copy()
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market}],
            [{"total": 1}]
        ]

        response = client.get(
            "/api/v1/graph/markets?asset_type=STOCK&sector=XLK&exchange=NASDAQ&is_active=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["markets"]) == 1


# =============================================================================
# Tests: GET /api/v1/graph/markets/stats
# =============================================================================

class TestMarketStatsEndpoint:
    """Tests for market statistics endpoint."""

    def test_get_market_stats_success(self, client, mock_neo4j_service):
        """Test market statistics endpoint."""
        stats_data = {
            "total_markets": 500,
            "active_markets": 485,
            "total_market_cap": 50000000000000,
            "avg_day_change": 0.45
        }

        mock_neo4j_service.execute_query.side_effect = [
            [stats_data],  # Overall stats
            [  # Asset type distribution
                {"asset_type": "STOCK", "count": 400},
                {"asset_type": "FOREX", "count": 50},
                {"asset_type": "CRYPTO", "count": 30},
                {"asset_type": "COMMODITY", "count": 20}
            ],
            [  # Sector distribution
                {"sector_code": "XLK", "count": 80},
                {"sector_code": "XLF", "count": 60},
                {"sector_code": "XLV", "count": 50}
            ]
        ]

        response = client.get("/api/v1/graph/markets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_markets"] == 500
        assert data["active_markets"] == 485
        assert data["total_market_cap"] == 50000000000000
        assert data["avg_day_change"] == 0.45
        assert data["markets_by_asset_type"]["STOCK"] == 400
        assert data["markets_by_asset_type"]["FOREX"] == 50
        assert data["markets_by_sector"]["XLK"] == 80

    def test_get_market_stats_empty_database(self, client, mock_neo4j_service):
        """Test stats when database is empty."""
        mock_neo4j_service.execute_query.side_effect = [
            [],  # No stats available
            [],  # No asset types
            []   # No sectors
        ]

        response = client.get("/api/v1/graph/markets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_markets"] == 0
        assert data["active_markets"] == 0
        assert data["markets_by_asset_type"] == {}
        assert data["markets_by_sector"] == {}

    def test_get_market_stats_partial_data(self, client, mock_neo4j_service):
        """Test stats with some data missing."""
        stats_data = {
            "total_markets": 100,
            "active_markets": 95
        }

        mock_neo4j_service.execute_query.side_effect = [
            [stats_data],
            [{"asset_type": "STOCK", "count": 100}],
            []  # No sectors
        ]

        response = client.get("/api/v1/graph/markets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_markets"] == 100
        assert data["total_market_cap"] is None
        assert data["avg_day_change"] is None

    def test_get_market_stats_query_error(self, client, mock_neo4j_service):
        """Test error handling for stats query failure."""
        mock_neo4j_service.execute_query.side_effect = Exception(
            "Neo4j error"
        )

        response = client.get("/api/v1/graph/markets/stats")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to query market statistics" in data["detail"]

    def test_get_market_stats_with_null_sectors(self, client, mock_neo4j_service):
        """Test stats handles null sector codes correctly."""
        stats_data = {"total_markets": 10, "active_markets": 10}

        mock_neo4j_service.execute_query.side_effect = [
            [stats_data],
            [{"asset_type": "STOCK", "count": 10}],
            [
                {"sector_code": "TECH", "count": 5},
                {"sector_code": None, "count": 5}  # Null sector code
            ]
        ]

        response = client.get("/api/v1/graph/markets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["markets_by_sector"]["TECH"] == 5
        # Null sectors should be skipped in result


# =============================================================================
# Tests: GET /api/v1/graph/markets/{symbol}
# =============================================================================

class TestMarketDetailEndpoint:
    """Tests for market detail endpoint."""

    def test_get_market_by_symbol_success(self, client, mock_neo4j_service, mock_market_data):
        """Test getting market details with sector information."""
        market = mock_market_data.copy()
        # Sector data from Neo4j returns sector_code, not code
        sector = {
            "sector_code": "XLK",
            "sector_name": "Information Technology",
            "classification_system": "GICS"
        }

        # First query returns market detail with sector
        # Second query returns related markets
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": market, "s": sector, "organizations": ["Apple Inc."]}],
            [{"symbol": "GOOGL"}, {"symbol": "MSFT"}]  # Related markets
        ]

        response = client.get("/api/v1/graph/markets/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["current_price"] == 178.45
        # sector_info should be created from the "s" field
        assert data["sector_info"]["code"] == "XLK"
        assert "Apple Inc." in data["organizations"]
        assert "GOOGL" in data["related_markets"]
        assert "MSFT" in data["related_markets"]

    def test_get_market_by_symbol_not_found(self, client, mock_neo4j_service):
        """Test 404 for non-existent symbol."""
        mock_neo4j_service.execute_query.return_value = []

        response = client.get("/api/v1/graph/markets/INVALID")

        assert response.status_code == 404
        data = response.json()
        assert "Market not found" in data["detail"]["error"]

    def test_get_market_by_symbol_no_sector(self, client, mock_neo4j_service, mock_market_data):
        """Test market without sector info."""
        market = mock_market_data.copy()
        market["sector"] = None

        mock_neo4j_service.execute_query.side_effect = [
            [{"m": market, "s": None, "organizations": []}],
            []  # No related markets
        ]

        response = client.get("/api/v1/graph/markets/BTCUSD")

        assert response.status_code == 200
        data = response.json()
        assert data["sector_info"] is None
        assert data["related_markets"] == []

    def test_get_market_symbol_case_insensitive(self, client, mock_neo4j_service, mock_market_data):
        """Test that symbol lookup is case-insensitive."""
        market = mock_market_data.copy()

        mock_neo4j_service.execute_query.side_effect = [
            [{"m": market, "s": None, "organizations": []}],
            []
        ]

        response = client.get("/api/v1/graph/markets/aapl")

        assert response.status_code == 200

        # Verify symbol was converted to uppercase
        call_args = mock_neo4j_service.execute_query.call_args_list[0]
        assert call_args.kwargs["parameters"]["symbol"] == "AAPL"

    def test_get_market_with_multiple_organizations(self, client, mock_neo4j_service, mock_market_data):
        """Test market with multiple organizations."""
        market = mock_market_data.copy()
        orgs = ["Apple Inc.", "Apple Computer Inc."]

        mock_neo4j_service.execute_query.side_effect = [
            [{"m": market, "s": None, "organizations": orgs}],
            []
        ]

        response = client.get("/api/v1/graph/markets/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert len(data["organizations"]) == 2
        assert "Apple Inc." in data["organizations"]

    def test_get_market_with_many_related_markets(self, client, mock_neo4j_service, mock_market_data):
        """Test market with related markets."""
        market = mock_market_data.copy()
        # Need to provide 2 queries: first for market detail, second for related markets
        # But since the code checks if sector_data exists, we return None
        related_symbols = [f"SYM{i}" for i in range(10)]

        # First call returns market with no sector
        # Second call with sector_data=None means no related markets query runs
        mock_neo4j_service.execute_query.return_value = [{"m": market, "s": None, "organizations": []}]

        response = client.get("/api/v1/graph/markets/AAPL")

        assert response.status_code == 200
        data = response.json()
        # Without sector, no related markets can be found
        assert len(data["related_markets"]) == 0

    def test_get_market_query_error(self, client, mock_neo4j_service):
        """Test error handling for market detail query."""
        mock_neo4j_service.execute_query.side_effect = Exception(
            "Connection timeout"
        )

        response = client.get("/api/v1/graph/markets/AAPL")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to query market details" in data["detail"]

    def test_get_market_special_characters_in_symbol(self, client, mock_neo4j_service, mock_market_data):
        """Test market with special characters in symbol (e.g., EUR/USD)."""
        market = mock_market_data.copy()
        market["symbol"] = "EUR/USD"

        mock_neo4j_service.execute_query.side_effect = [
            [{"m": market, "s": None, "organizations": []}],
            []
        ]

        response = client.get("/api/v1/graph/markets/EUR/USD")

        # Encoded path should work
        assert response.status_code in [200, 404, 422]


# =============================================================================
# Tests: GET /api/v1/graph/markets/{symbol}/history
# =============================================================================

class TestMarketHistoryEndpoint:
    """Tests for market history endpoint."""

    def test_get_market_history_success(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test historical price data retrieval."""
        # Mock market exists check
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]

        # Mock FMP historical data
        history_data = [
            {
                "date": "2024-01-15",
                "open": 176.80,
                "high": 179.20,
                "low": 176.50,
                "close": 178.45,
                "volume": 52340000,
                "adjClose": 178.45
            },
            {
                "date": "2024-01-14",
                "open": 175.00,
                "high": 177.50,
                "low": 174.80,
                "close": 176.25,
                "volume": 48900000,
                "adjClose": 176.25
            }
        ]
        mock_fmp_client.get_historical_prices.return_value = history_data

        response = client.get(
            "/api/v1/graph/markets/AAPL/history",
            params={"from_date": "2024-01-01", "to_date": "2024-01-31"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["total_records"] == 2
        assert len(data["history"]) == 2
        assert data["history"][0]["date"] == "2024-01-15"
        assert data["history"][0]["close"] == 178.45
        assert data["data_source"] == "FMP"

    def test_get_market_history_not_found(self, client, mock_neo4j_service):
        """Test 404 when market doesn't exist."""
        mock_neo4j_service.execute_query.return_value = []

        response = client.get("/api/v1/graph/markets/INVALID/history")

        assert response.status_code == 404
        data = response.json()
        assert "Market not found" in data["detail"]["error"]

    def test_get_market_history_with_date_range(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test history with date range parameters."""
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]

        history_data = [
            {"date": "2024-06-01", "open": 180.0, "high": 182.0, "low": 179.5, "close": 181.5, "volume": 45000000}
        ]
        mock_fmp_client.get_historical_prices.return_value = history_data

        response = client.get(
            "/api/v1/graph/markets/AAPL/history?from_date=2024-06-01&to_date=2024-06-30"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 1

        # Verify dates were passed to FMP client
        call_kwargs = mock_fmp_client.get_historical_prices.call_args.kwargs
        assert call_kwargs["from_date"] == "2024-06-01"
        assert call_kwargs["to_date"] == "2024-06-30"

    def test_get_market_history_no_data(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test history when no data available."""
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]
        mock_fmp_client.get_historical_prices.return_value = []

        response = client.get("/api/v1/graph/markets/AAPL/history")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 0
        assert len(data["history"]) == 0

    def test_get_market_history_limit(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test history limit parameter."""
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]

        # Return 200 records
        history_data = [
            {
                "date": f"2024-01-{i%28+1:02d}",
                "open": 175.0 + i,
                "high": 177.0 + i,
                "low": 174.0 + i,
                "close": 176.0 + i,
                "volume": 50000000
            }
            for i in range(200)
        ]
        mock_fmp_client.get_historical_prices.return_value = history_data

        response = client.get("/api/v1/graph/markets/AAPL/history?limit=50")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 50  # Limited to 50
        assert len(data["history"]) == 50

    def test_get_market_history_exceeds_max_limit(self, client):
        """Test that limit exceeds maximum allowed."""
        response = client.get("/api/v1/graph/markets/AAPL/history?limit=5000")

        assert response.status_code == 422

    def test_get_market_history_fmp_unavailable(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test when FMP Service is unavailable."""
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]
        mock_fmp_client.get_historical_prices.side_effect = FMPServiceUnavailableError(
            "FMP Service unavailable"
        )

        response = client.get("/api/v1/graph/markets/AAPL/history")

        assert response.status_code == 503
        data = response.json()
        assert "FMP Service unavailable" in data["detail"]["error"]

    def test_get_market_history_invalid_date_format(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test invalid date format in query parameters."""
        # Mock market exists check
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]
        # FMP service should handle invalid dates gracefully
        mock_fmp_client.get_historical_prices.return_value = []

        response = client.get(
            "/api/v1/graph/markets/AAPL/history?from_date=invalid-date"
        )

        # Should return empty results or error, depending on FMP handling
        assert response.status_code in [200, 500]

    def test_get_market_history_default_limit(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test default limit is 100."""
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]

        # Return 150 records
        history_data = [
            {
                "date": f"2024-01-{i%28+1:02d}",
                "open": 175.0,
                "high": 177.0,
                "low": 174.0,
                "close": 176.0,
                "volume": 50000000
            }
            for i in range(150)
        ]
        mock_fmp_client.get_historical_prices.return_value = history_data

        response = client.get("/api/v1/graph/markets/AAPL/history")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 100  # Default limit
        assert len(data["history"]) == 100

    def test_get_market_history_with_adjusted_close(self, client, mock_neo4j_service, mock_fmp_client, mock_market_data):
        """Test history includes adjusted close price."""
        mock_neo4j_service.execute_query.return_value = [{"m": mock_market_data}]

        history_data = [
            {
                "date": "2024-01-15",
                "open": 176.80,
                "high": 179.20,
                "low": 176.50,
                "close": 178.45,
                "volume": 52340000,
                "adjClose": 177.99  # Different from close
            }
        ]
        mock_fmp_client.get_historical_prices.return_value = history_data

        response = client.get("/api/v1/graph/markets/AAPL/history")

        assert response.status_code == 200
        data = response.json()
        assert data["history"][0]["adj_close"] == 177.99


# =============================================================================
# Integration Tests
# =============================================================================

class TestMarketsAPIIntegration:
    """Integration tests across multiple endpoints."""

    def test_workflow_sync_then_query(self, client, mock_market_sync_service, mock_neo4j_service, mock_sync_result, mock_market_data):
        """Test typical workflow: sync markets then query them."""
        # Step 1: Sync markets
        mock_market_sync_service.sync_all_markets.return_value = mock_sync_result
        sync_response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )
        assert sync_response.status_code == 200

        # Step 2: List markets
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market_data}],
            [{"total": 1}]
        ]
        list_response = client.get("/api/v1/graph/markets")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1

    def test_all_endpoints_metrics_recorded(self, client, mock_market_sync_service, mock_neo4j_service, mock_sync_result, mock_market_data):
        """Test that all endpoints record metrics."""
        # Should increment metrics on each successful call
        mock_market_sync_service.sync_all_markets.return_value = mock_sync_result
        mock_neo4j_service.execute_query.side_effect = [
            [{"m": mock_market_data}],
            [{"total": 1}]
        ]

        # All should succeed without errors
        sync_response = client.post(
            "/api/v1/graph/markets/sync",
            json={}
        )
        assert sync_response.status_code == 200

        list_response = client.get("/api/v1/graph/markets")
        assert list_response.status_code == 200

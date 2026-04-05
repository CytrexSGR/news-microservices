"""
Unit tests for FMP Service HTTP Client.

Tests circuit breaker, retry logic, and error handling.
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.clients import (
    FMPServiceClient,
    FMPClientConfig,
    FMPServiceUnavailableError,
    FMPRateLimitError,
    FMPNotFoundError,
    CircuitBreakerOpenError
)
from app.clients.circuit_breaker import CircuitState


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fmp_config():
    """FMP client configuration for testing."""
    return FMPClientConfig(
        fmp_base_url="http://test-fmp-service:8113",
        fmp_timeout=5,
        fmp_max_retries=3,
        fmp_circuit_breaker_threshold=3,  # Lower threshold for tests
        fmp_circuit_breaker_timeout=1  # Faster recovery for tests
    )


@pytest.fixture
async def fmp_client(fmp_config):
    """FMP client instance for testing."""
    client = FMPServiceClient(fmp_config)
    yield client
    await client.close()


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(fmp_client):
    """Test that circuit breaker opens after threshold failures."""
    # Mock httpx to raise network errors
    with patch.object(
        fmp_client.client,
        'get',
        side_effect=httpx.NetworkError("Connection refused")
    ):
        # Make requests until circuit opens
        for i in range(3):
            with pytest.raises(httpx.NetworkError):
                await fmp_client.fetch_market_quote("AAPL")

        # Circuit should now be OPEN
        assert fmp_client.circuit_breaker.state == CircuitState.OPEN

        # Next request should raise CircuitBreakerOpenError
        with pytest.raises(FMPServiceUnavailableError):
            await fmp_client.fetch_market_quote("AAPL")


@pytest.mark.asyncio
async def test_circuit_breaker_recovers(fmp_client):
    """Test that circuit breaker transitions to HALF_OPEN after timeout."""
    # Open the circuit
    with patch.object(
        fmp_client.client,
        'get',
        side_effect=httpx.NetworkError("Connection refused")
    ):
        for i in range(3):
            with pytest.raises(httpx.NetworkError):
                await fmp_client.fetch_market_quote("AAPL")

    assert fmp_client.circuit_breaker.state == CircuitState.OPEN

    # Wait for recovery timeout (1 second in test config)
    import asyncio
    await asyncio.sleep(1.1)

    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "symbol": "AAPL",
        "price": 150.0,
        "change": 2.5,
        "change_percent": 1.7,
        "timestamp": datetime.now().isoformat()
    }

    with patch.object(
        fmp_client.client,
        'get',
        return_value=mock_response
    ):
        # This should transition to HALF_OPEN and then CLOSED
        result = await fmp_client.fetch_market_quote("AAPL")
        assert result.symbol == "AAPL"
        assert fmp_client.circuit_breaker.state == CircuitState.CLOSED


# ============================================================================
# Retry Logic Tests
# ============================================================================

@pytest.mark.asyncio
async def test_retry_on_network_error(fmp_client):
    """Test retry logic on network errors."""
    # Mock: First 2 attempts fail, 3rd succeeds
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "asset_type": "STOCK",
        "sector": "Technology"
    }]

    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.NetworkError("Connection timeout")
        return mock_response

    with patch.object(fmp_client.client, 'get', side_effect=mock_get):
        result = await fmp_client.fetch_asset_metadata(["AAPL"])
        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert call_count == 3  # Should have retried twice


@pytest.mark.asyncio
async def test_no_retry_on_4xx_errors(fmp_client):
    """Test that 4xx errors are not retried."""
    # Mock 404 response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found",
        request=MagicMock(),
        response=mock_response
    )

    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_response

    with patch.object(fmp_client.client, 'get', side_effect=mock_get):
        with pytest.raises(FMPNotFoundError):
            await fmp_client.fetch_market_quote("INVALID")

        # Should NOT have retried (only 1 call)
        assert call_count == 1


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limit_error(fmp_client):
    """Test handling of 429 Rate Limit errors."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate Limit",
        request=MagicMock(),
        response=mock_response
    )

    with patch.object(fmp_client.client, 'get', return_value=mock_response):
        with pytest.raises(FMPRateLimitError):
            await fmp_client.fetch_market_quote("AAPL")


@pytest.mark.asyncio
async def test_service_unavailable_error(fmp_client):
    """Test handling of 503 Service Unavailable errors."""
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service Unavailable",
        request=MagicMock(),
        response=mock_response
    )

    with patch.object(fmp_client.client, 'get', return_value=mock_response):
        with pytest.raises(FMPServiceUnavailableError):
            await fmp_client.fetch_market_quote("AAPL")


# ============================================================================
# API Method Tests
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_asset_metadata(fmp_client):
    """Test fetching asset metadata."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "asset_type": "STOCK",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "exchange": "NASDAQ",
            "currency": "USD"
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "asset_type": "STOCK",
            "sector": "Technology",
            "industry": "Internet Content & Information",
            "exchange": "NASDAQ",
            "currency": "USD"
        }
    ]

    with patch.object(fmp_client.client, 'get', return_value=mock_response):
        result = await fmp_client.fetch_asset_metadata(["AAPL", "GOOGL"])

        assert len(result) == 2
        assert result[0].symbol == "AAPL"
        assert result[0].asset_type == "STOCK"
        assert result[1].symbol == "GOOGL"


@pytest.mark.asyncio
async def test_fetch_market_quote(fmp_client):
    """Test fetching market quote."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "symbol": "AAPL",
        "price": 175.50,
        "change": 3.25,
        "change_percent": 1.89,
        "volume": 50000000,
        "timestamp": datetime.now().isoformat()
    }

    with patch.object(fmp_client.client, 'get', return_value=mock_response):
        result = await fmp_client.fetch_market_quote("AAPL")

        assert result.symbol == "AAPL"
        assert result.price == 175.50
        assert result.change == 3.25
        assert result.volume == 50000000


@pytest.mark.asyncio
async def test_fetch_market_history(fmp_client):
    """Test fetching market history."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "symbol": "AAPL",
            "date": "2025-11-15",
            "open": 170.0,
            "high": 175.0,
            "low": 169.5,
            "close": 174.0,
            "volume": 45000000
        },
        {
            "symbol": "AAPL",
            "date": "2025-11-14",
            "open": 168.0,
            "high": 171.0,
            "low": 167.5,
            "close": 170.0,
            "volume": 42000000
        }
    ]

    with patch.object(fmp_client.client, 'get', return_value=mock_response):
        start = date(2025, 11, 14)
        end = date(2025, 11, 15)

        result = await fmp_client.fetch_market_history("AAPL", start, end)

        assert len(result) == 2
        assert result[0].symbol == "AAPL"
        assert result[0].close == 174.0
        assert result[1].close == 170.0


@pytest.mark.asyncio
async def test_health_check(fmp_client):
    """Test health check endpoint."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(fmp_client.client, 'get', return_value=mock_response):
        is_healthy = await fmp_client.health_check()
        assert is_healthy is True


@pytest.mark.asyncio
async def test_health_check_failure(fmp_client):
    """Test health check when service is down."""
    with patch.object(
        fmp_client.client,
        'get',
        side_effect=httpx.NetworkError("Connection refused")
    ):
        is_healthy = await fmp_client.health_check()
        assert is_healthy is False


# ============================================================================
# Context Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_context_manager(fmp_config):
    """Test async context manager usage."""
    async with FMPServiceClient(fmp_config) as client:
        assert client.client is not None

        # Mock successful health check
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client.client, 'get', return_value=mock_response):
            is_healthy = await client.health_check()
            assert is_healthy is True

    # Client should be closed after context exit
    # Note: httpx.AsyncClient doesn't have is_closed in all versions


# ============================================================================
# Utility Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_circuit_breaker_stats(fmp_client):
    """Test retrieving circuit breaker statistics."""
    stats = fmp_client.get_circuit_breaker_stats()

    assert stats["service_name"] == "fmp-service"
    assert stats["state"] == CircuitState.CLOSED
    assert stats["failure_count"] == 0
    assert stats["failure_threshold"] == 3


@pytest.mark.asyncio
async def test_reset_circuit_breaker(fmp_client):
    """Test manual circuit breaker reset."""
    # Open the circuit
    with patch.object(
        fmp_client.client,
        'get',
        side_effect=httpx.NetworkError("Connection refused")
    ):
        for i in range(3):
            with pytest.raises(httpx.NetworkError):
                await fmp_client.fetch_market_quote("AAPL")

    assert fmp_client.circuit_breaker.state == CircuitState.OPEN

    # Reset manually
    fmp_client.reset_circuit_breaker()

    assert fmp_client.circuit_breaker.state == CircuitState.CLOSED
    assert fmp_client.circuit_breaker._failure_count == 0

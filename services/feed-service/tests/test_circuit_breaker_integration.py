"""
Integration Tests for Circuit Breaker Pattern

Tests circuit breaker behavior with real HTTP calls (using httpbin/mock servers).

Task 406: Circuit Breaker Integration Tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerOpenError,
    ResilientHttpClient,
    RetryConfig,
)


# =============================================================================
# Circuit Breaker Tests
# =============================================================================

@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """Test circuit breaker in CLOSED state allows requests"""
    cb = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=3,
        timeout_seconds=1,
        enable_metrics=False,
    ))

    assert cb.stats.state == CircuitBreakerState.CLOSED
    assert await cb.can_execute() is True


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures"""
    cb = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=3,
        timeout_seconds=1,
        enable_metrics=False,
    ))

    # Record failures
    for i in range(3):
        await cb.record_failure()

    # Circuit should be OPEN
    assert cb.stats.state == CircuitBreakerState.OPEN
    assert await cb.can_execute() is False


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_transition():
    """Test circuit breaker transitions to HALF_OPEN after timeout"""
    cb = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        timeout_seconds=0.1,  # Short timeout for testing
        enable_metrics=False,
    ))

    # Open circuit
    await cb.record_failure()
    await cb.record_failure()
    assert cb.stats.state == CircuitBreakerState.OPEN

    # Wait for timeout
    await asyncio.sleep(0.15)

    # Should transition to HALF_OPEN
    assert await cb.can_execute() is True


@pytest.mark.asyncio
async def test_circuit_breaker_closes_after_successes():
    """Test circuit breaker closes after success threshold in HALF_OPEN"""
    cb = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout_seconds=0.1,
        enable_metrics=False,
    ))

    # Open circuit
    await cb.record_failure()
    await cb.record_failure()
    assert cb.stats.state == CircuitBreakerState.OPEN

    # Wait for HALF_OPEN
    await asyncio.sleep(0.15)
    await cb.can_execute()  # Trigger HALF_OPEN transition

    # Record successes
    await cb.record_success()
    await cb.record_success()

    # Should be CLOSED
    assert cb.stats.state == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_reopens_on_failure_in_half_open():
    """Test circuit breaker reopens on failure in HALF_OPEN state"""
    cb = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        timeout_seconds=0.1,
        enable_metrics=False,
    ))

    # Open circuit
    await cb.record_failure()
    await cb.record_failure()

    # Wait for HALF_OPEN
    await asyncio.sleep(0.15)
    await cb.can_execute()

    # Fail in HALF_OPEN
    await cb.record_failure()

    # Should reopen
    assert cb.stats.state == CircuitBreakerState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_context_manager_success():
    """Test circuit breaker context manager with successful operation"""
    cb = CircuitBreaker(CircuitBreakerConfig(enable_metrics=False))

    async with cb:
        # Simulate successful operation
        pass

    assert cb.stats.total_successes == 1
    assert cb.stats.total_failures == 0


@pytest.mark.asyncio
async def test_circuit_breaker_context_manager_failure():
    """Test circuit breaker context manager with failed operation"""
    cb = CircuitBreaker(CircuitBreakerConfig(enable_metrics=False))

    with pytest.raises(ValueError):
        async with cb:
            raise ValueError("Test error")

    assert cb.stats.total_successes == 0
    assert cb.stats.total_failures == 1


@pytest.mark.asyncio
async def test_circuit_breaker_context_manager_when_open():
    """Test circuit breaker raises error when open"""
    cb = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        enable_metrics=False,
    ))

    # Open circuit
    await cb.record_failure()
    await cb.record_failure()

    # Should raise CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        async with cb:
            pass


# =============================================================================
# ResilientHttpClient Tests
# =============================================================================

@pytest.mark.asyncio
async def test_resilient_http_client_success():
    """Test ResilientHttpClient with successful request"""
    client = ResilientHttpClient(
        circuit_breaker_config=CircuitBreakerConfig(enable_metrics=False),
        retry_config=RetryConfig(max_retries=1),
        timeout=5.0,
    )

    async with client:
        # Use httpbin.org for testing (real HTTP request)
        response = await client.get("https://httpbin.org/status/200")
        assert response.status_code == 200

    # Check circuit breaker stats
    stats = client.get_stats()
    assert stats["total_successes"] == 1
    assert stats["total_failures"] == 0


@pytest.mark.asyncio
async def test_resilient_http_client_retry_on_failure():
    """Test ResilientHttpClient retries on transient failures"""
    client = ResilientHttpClient(
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=5,
            enable_metrics=False,
        ),
        retry_config=RetryConfig(
            max_retries=2,
            initial_delay=0.1,
        ),
        timeout=2.0,
    )

    async with client:
        # Use httpbin.org 500 error endpoint
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("https://httpbin.org/status/500")

    # Should have retried 3 times (initial + 2 retries)
    stats = client.get_stats()
    assert stats["total_failures"] >= 1


@pytest.mark.asyncio
async def test_resilient_http_client_circuit_breaker_opens():
    """Test ResilientHttpClient opens circuit breaker after failures"""
    client = ResilientHttpClient(
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=2,
            enable_metrics=False,
        ),
        retry_config=RetryConfig(max_retries=0),
        timeout=2.0,
    )

    async with client:
        # Cause failures to open circuit
        for i in range(2):
            try:
                await client.get("https://httpbin.org/status/500")
            except httpx.HTTPStatusError:
                pass

        # Circuit should be OPEN now
        with pytest.raises(CircuitBreakerOpenError):
            await client.get("https://httpbin.org/status/200")


@pytest.mark.asyncio
async def test_resilient_http_client_conditional_headers():
    """Test ResilientHttpClient preserves conditional headers"""
    client = ResilientHttpClient(
        circuit_breaker_config=CircuitBreakerConfig(enable_metrics=False),
        retry_config=RetryConfig(max_retries=0),
        timeout=5.0,
    )

    async with client:
        # Test If-None-Match header
        response = await client.get(
            "https://httpbin.org/headers",
            headers={"If-None-Match": "test-etag"}
        )
        assert response.status_code == 200

        # Verify header was sent
        data = response.json()
        assert "If-None-Match" in data["headers"]


# =============================================================================
# Feed Fetcher Integration Tests (with mocks)
# =============================================================================

@pytest.mark.asyncio
async def test_feed_fetcher_uses_circuit_breaker():
    """Test FeedFetcher integrates with circuit breaker"""
    from app.services.feed_fetcher import FeedFetcher
    from app.models import Feed, FeedStatus
    from unittest.mock import AsyncMock, MagicMock

    fetcher = FeedFetcher()

    # Mock database
    mock_session = AsyncMock()
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = "https://httpbin.org/status/500"
    mock_feed.etag = None
    mock_feed.last_modified = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_feed
    mock_session.execute.return_value = mock_result

    # Test that circuit breaker is used
    http_client = fetcher.get_http_client(feed_id=1, feed_url=str(mock_feed.url))
    assert http_client is not None
    assert http_client.circuit_breaker is not None


@pytest.mark.asyncio
async def test_feed_fetcher_handles_circuit_breaker_open():
    """Test FeedFetcher handles open circuit breaker gracefully"""
    from app.services.feed_fetcher import FeedFetcher

    fetcher = FeedFetcher()

    # Get HTTP client and open circuit breaker manually
    http_client = fetcher.get_http_client(feed_id=999, feed_url="https://example.com")

    # Open circuit breaker
    for i in range(5):
        await http_client.circuit_breaker.record_failure()

    # Fetch should return (False, 0) instead of crashing
    success, count = await fetcher.fetch_feed(999)
    assert success is False
    assert count == 0


# =============================================================================
# Retry Logic Tests
# =============================================================================

@pytest.mark.asyncio
async def test_retry_with_exponential_backoff():
    """Test retry logic with exponential backoff"""
    from app.resilience.retry import retry_with_backoff, RetryConfig
    import time

    call_count = 0
    call_times = []

    async def flaky_function():
        nonlocal call_count
        call_count += 1
        call_times.append(time.time())

        if call_count < 3:
            raise ValueError("Temporary error")

        return "Success"

    config = RetryConfig(
        max_retries=3,
        initial_delay=0.1,
        exponential_base=2.0,
        jitter=False,
    )

    result = await retry_with_backoff(flaky_function, config)

    assert result == "Success"
    assert call_count == 3

    # Check backoff times
    if len(call_times) >= 3:
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Delays should increase exponentially
        assert delay1 >= 0.1  # First retry: 0.1s
        assert delay2 >= 0.2  # Second retry: 0.2s


@pytest.mark.asyncio
async def test_retry_exhaustion():
    """Test retry exhaustion raises last exception"""
    from app.resilience.retry import retry_with_backoff, RetryConfig

    async def always_fails():
        raise ValueError("Always fails")

    config = RetryConfig(max_retries=2, initial_delay=0.01)

    with pytest.raises(ValueError, match="Always fails"):
        await retry_with_backoff(always_fails, config)


# =============================================================================
# End-to-End Integration Tests
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_feed_fetch_with_circuit_breaker_e2e():
    """
    End-to-end test: Fetch real feed with circuit breaker protection.

    This test requires network access and uses a real RSS feed.
    Skip if network is unavailable.
    """
    from app.services.feed_fetcher import FeedFetcher
    from app.models import Feed

    fetcher = FeedFetcher()

    # Use a reliable test feed
    test_feed_url = "https://feeds.bbci.co.uk/news/rss.xml"

    # Get HTTP client for this feed
    http_client = fetcher.get_http_client(feed_id=1, feed_url=test_feed_url)

    try:
        async with http_client:
            response = await http_client.get(test_feed_url)
            assert response.status_code == 200
            assert "xml" in response.headers.get("content-type", "").lower()

        # Check circuit breaker stayed closed
        stats = http_client.get_stats()
        assert stats["state"] == CircuitBreakerState.CLOSED.value
        assert stats["total_successes"] >= 1

    except httpx.HTTPError:
        pytest.skip("Network unavailable or feed unreachable")


@pytest.mark.asyncio
async def test_rabbitmq_consumer_with_retry():
    """Test RabbitMQ consumer retry logic (mocked)"""
    from app.workers.rabbitmq_base_consumer import BaseRabbitMQConsumer, MessageAction
    from unittest.mock import AsyncMock, MagicMock

    class TestConsumer(BaseRabbitMQConsumer):
        def __init__(self):
            super().__init__(
                rabbitmq_url="amqp://test",
                queue_name="test_queue",
                routing_keys=["test.event"],
                enable_metrics=False,
            )
            self.call_count = 0

        async def process_message(self, message_data):
            self.call_count += 1
            if self.call_count < 2:
                return MessageAction.RETRY
            return MessageAction.ACK

    consumer = TestConsumer()

    # Mock message
    mock_message = MagicMock()
    mock_message.body = b'{"payload": {"test": "data"}}'
    mock_message.headers = {}
    mock_message.ack = AsyncMock()
    mock_message.reject = AsyncMock()

    # Mock channel
    consumer.channel = AsyncMock()
    consumer.channel.default_exchange.publish = AsyncMock()

    # Process message
    await consumer.handle_message(mock_message)

    # Should have tried to retry (call_count = 1, action = RETRY)
    assert consumer.call_count == 1

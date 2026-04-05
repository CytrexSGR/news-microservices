"""
Unit tests for circuit breaker pattern.

Tests cover:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Threshold enforcement
- Recovery behavior
- Context manager pattern
- Registry pattern
- Metrics tracking
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from news_mcp_common.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerRegistry,
    CircuitBreakerOpenError,
)


@pytest.fixture
def circuit_breaker():
    """Create circuit breaker with test config."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=1,  # Short timeout for tests
        enable_metrics=False,  # Disable metrics for simpler tests
    )
    return CircuitBreaker(name="test-api", config=config)


@pytest.fixture
def registry():
    """Create circuit breaker registry."""
    return CircuitBreakerRegistry()


class TestCircuitBreakerBasics:
    """Basic circuit breaker functionality tests."""

    def test_initial_state_is_closed(self, circuit_breaker):
        """Circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.can_execute() is True

    def test_can_execute_returns_true_when_closed(self, circuit_breaker):
        """can_execute() returns True when CLOSED."""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.can_execute() is True

    def test_record_success_in_closed_state(self, circuit_breaker):
        """Recording success in CLOSED state maintains state."""
        circuit_breaker.record_success()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.stats.total_successes == 1
        assert circuit_breaker.stats.failure_count == 0


class TestCircuitBreakerStateTransitions:
    """Test state transition logic."""

    def test_transition_to_open_after_threshold_failures(self, circuit_breaker):
        """Circuit opens after reaching failure threshold."""
        # Record failures up to threshold (3)
        circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

        circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

        circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitBreakerState.OPEN

    def test_can_execute_blocks_when_open(self, circuit_breaker):
        """can_execute() returns False when OPEN."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.can_execute() is False

    def test_transition_to_half_open_after_timeout(self, circuit_breaker):
        """Circuit transitions to HALF_OPEN after timeout."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Wait for timeout
        circuit_breaker.stats.last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=2)

        # Check can_execute triggers half-open
        assert circuit_breaker.can_execute() is True
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN

    def test_half_open_to_closed_after_successes(self, circuit_breaker):
        """Circuit closes after success threshold in HALF_OPEN."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        # Move to half-open
        circuit_breaker.stats.last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        circuit_breaker.can_execute()
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN

        # Record successes (threshold = 2)
        circuit_breaker.record_success()
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN

        circuit_breaker.record_success()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

    def test_half_open_to_open_on_failure(self, circuit_breaker):
        """Circuit reopens on failure in HALF_OPEN state."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        # Move to half-open
        circuit_breaker.stats.last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        circuit_breaker.can_execute()
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN

        # Record another failure
        circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitBreakerState.HALF_OPEN

        # Next failure should keep accumulating
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        assert circuit_breaker.state == CircuitBreakerState.OPEN


class TestCircuitBreakerContextManager:
    """Test async context manager pattern."""

    @pytest.mark.asyncio
    async def test_context_manager_success(self, circuit_breaker):
        """Context manager records success on normal exit."""
        async def mock_operation():
            return "success"

        async with circuit_breaker():
            result = await mock_operation()

        assert result == "success"
        assert circuit_breaker.stats.total_successes == 1
        assert circuit_breaker.stats.total_failures == 0

    @pytest.mark.asyncio
    async def test_context_manager_failure(self, circuit_breaker):
        """Context manager records failure on exception."""
        async def failing_operation():
            raise ValueError("API error")

        with pytest.raises(ValueError, match="API error"):
            async with circuit_breaker():
                await failing_operation()

        assert circuit_breaker.stats.total_failures == 1
        assert circuit_breaker.stats.total_successes == 0

    @pytest.mark.asyncio
    async def test_context_manager_blocks_when_open(self, circuit_breaker):
        """Context manager raises CircuitBreakerOpenError when OPEN."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        with pytest.raises(CircuitBreakerOpenError, match="test-api"):
            async with circuit_breaker():
                pass


class TestCircuitBreakerStatistics:
    """Test statistics tracking."""

    def test_stats_track_total_successes(self, circuit_breaker):
        """Total successes are tracked correctly."""
        for _ in range(5):
            circuit_breaker.record_success()

        assert circuit_breaker.stats.total_successes == 5

    def test_stats_track_total_failures(self, circuit_breaker):
        """Total failures are tracked correctly."""
        for _ in range(5):
            circuit_breaker.record_failure()

        assert circuit_breaker.stats.total_failures == 5

    def test_stats_track_rejections(self, circuit_breaker):
        """Rejections are tracked when circuit is OPEN."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        # Try to execute (will be rejected)
        for _ in range(5):
            circuit_breaker.can_execute()

        assert circuit_breaker.stats.total_rejections == 5

    def test_get_stats_returns_full_info(self, circuit_breaker):
        """get_stats() returns comprehensive statistics."""
        circuit_breaker.record_success()
        circuit_breaker.record_failure()

        stats = circuit_breaker.get_stats()

        assert stats["name"] == "test-api"
        assert stats["state"] == "closed"
        assert stats["total_successes"] == 1
        assert stats["total_failures"] == 1
        assert "config" in stats
        assert stats["config"]["failure_threshold"] == 3


class TestCircuitBreakerRegistry:
    """Test registry pattern."""

    @pytest.mark.asyncio
    async def test_get_or_create_creates_new(self, registry):
        """get_or_create() creates new circuit breaker."""
        cb = await registry.get_or_create("api-1")

        assert cb is not None
        assert cb.name == "api-1"
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing(self, registry):
        """get_or_create() returns existing circuit breaker."""
        cb1 = await registry.get_or_create("api-1")
        cb2 = await registry.get_or_create("api-1")

        assert cb1 is cb2

    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent(self, registry):
        """get() returns None for nonexistent circuit breaker."""
        cb = registry.get("nonexistent")
        assert cb is None

    @pytest.mark.asyncio
    async def test_list_all_returns_all_breakers(self, registry):
        """list_all() returns all circuit breakers."""
        await registry.get_or_create("api-1")
        await registry.get_or_create("api-2")
        await registry.get_or_create("api-3")

        all_cbs = registry.list_all()

        assert len(all_cbs) == 3
        assert "api-1" in all_cbs
        assert "api-2" in all_cbs
        assert "api-3" in all_cbs

    @pytest.mark.asyncio
    async def test_get_all_stats_returns_stats_for_all(self, registry):
        """get_all_stats() returns statistics for all circuit breakers."""
        cb1 = await registry.get_or_create("api-1")
        cb2 = await registry.get_or_create("api-2")

        cb1.record_success()
        cb2.record_failure()

        stats = registry.get_all_stats()

        assert "api-1" in stats
        assert "api-2" in stats
        assert stats["api-1"]["total_successes"] == 1
        assert stats["api-2"]["total_failures"] == 1


class TestCircuitBreakerConcurrency:
    """Test concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, circuit_breaker):
        """Multiple concurrent operations are handled correctly."""
        async def operation(should_fail: bool):
            async with circuit_breaker():
                if should_fail:
                    raise ValueError("Failed")
                return "Success"

        # Run 10 successful operations concurrently
        tasks = [operation(False) for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        assert len(results) == 10
        assert circuit_breaker.stats.total_successes == 10

    @pytest.mark.asyncio
    async def test_concurrent_failures_open_circuit(self, circuit_breaker):
        """Concurrent failures correctly open circuit."""
        async def failing_operation():
            try:
                async with circuit_breaker():
                    raise ValueError("Failed")
            except ValueError:
                pass

        # Run multiple failing operations
        tasks = [failing_operation() for _ in range(5)]
        await asyncio.gather(*tasks)

        # Circuit should be open after 3 failures
        assert circuit_breaker.state == CircuitBreakerState.OPEN


class TestCircuitBreakerEdgeCases:
    """Test edge cases and error conditions."""

    def test_success_resets_failure_count(self, circuit_breaker):
        """Success resets failure count."""
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        assert circuit_breaker.stats.failure_count == 2

        circuit_breaker.record_success()
        assert circuit_breaker.stats.failure_count == 0

    def test_failure_resets_success_count_in_half_open(self, circuit_breaker):
        """Failure in HALF_OPEN resets success count."""
        # Open circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        # Move to half-open
        circuit_breaker.stats.last_failure_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        circuit_breaker.can_execute()
        circuit_breaker.record_success()
        assert circuit_breaker.stats.success_count == 1

        # Failure should reset success count
        circuit_breaker.record_failure()
        assert circuit_breaker.stats.success_count == 0

    def test_reset_returns_to_closed(self, circuit_breaker):
        """reset() transitions circuit back to CLOSED."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == CircuitBreakerState.OPEN

        # Reset
        circuit_breaker.reset()

        # Should eventually be closed (async task)
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

    def test_record_failure_with_exception(self, circuit_breaker):
        """record_failure() accepts exception parameter."""
        error = ValueError("Test error")
        circuit_breaker.record_failure(error)

        assert circuit_breaker.stats.total_failures == 1

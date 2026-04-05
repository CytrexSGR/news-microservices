"""Tests for Jittered Backoff"""
import pytest
from app.core.retry import calculate_backoff_with_jitter, RetryConfig


class TestJitteredBackoff:
    def test_jitter_adds_randomness(self):
        config = RetryConfig(base_delay=1.0, max_delay=10.0, exponential_base=2.0)

        # Generate multiple backoff values for same attempt
        delays = [calculate_backoff_with_jitter(attempt=2, config=config) for _ in range(20)]

        # Should have variety (jitter)
        unique_delays = set(delays)
        assert len(unique_delays) > 1, "Jitter should produce varied delays"

    def test_jitter_respects_max_delay(self):
        config = RetryConfig(base_delay=1.0, max_delay=5.0, exponential_base=2.0)

        for attempt in range(10):
            delay = calculate_backoff_with_jitter(attempt=attempt, config=config)
            assert delay <= config.max_delay * 1.5, f"Delay {delay} exceeds max with jitter buffer"

    def test_jitter_increases_with_attempts(self):
        config = RetryConfig(base_delay=1.0, max_delay=60.0, exponential_base=2.0)

        avg_delay_1 = sum(calculate_backoff_with_jitter(1, config) for _ in range(10)) / 10
        avg_delay_5 = sum(calculate_backoff_with_jitter(5, config) for _ in range(10)) / 10

        assert avg_delay_5 > avg_delay_1, "Later attempts should have longer average delay"

    def test_jitter_range(self):
        """Verify jitter is between 50% and 100% of calculated delay"""
        config = RetryConfig(base_delay=2.0, max_delay=100.0, exponential_base=2.0)

        for attempt in range(5):
            exp_delay = min(config.base_delay * (config.exponential_base ** attempt), config.max_delay)

            for _ in range(20):
                delay = calculate_backoff_with_jitter(attempt, config)
                # Should be between 50% and 100% of capped delay
                assert delay >= exp_delay * 0.5 - 0.001, f"Delay {delay} too low"
                assert delay <= exp_delay + 0.001, f"Delay {delay} too high"

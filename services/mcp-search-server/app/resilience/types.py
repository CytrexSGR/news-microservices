"""
Type definitions for resilience module.
"""

from enum import Enum


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half-open"  # Testing if service recovered

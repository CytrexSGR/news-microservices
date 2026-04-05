"""
Resilience patterns for Feed Service

Implements:
- Circuit Breaker Pattern for external API calls
- Retry logic with exponential backoff
- Health monitoring and metrics
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerOpenError,
)
from .retry import (
    RetryConfig,
    retry_with_backoff,
)
from .http_client import ResilientHttpClient

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "CircuitBreakerOpenError",
    "RetryConfig",
    "retry_with_backoff",
    "ResilientHttpClient",
]

"""
Resilience patterns for news-microservices.

Provides circuit breakers, rate limiters, and retry logic.
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitBreakerConfig,
    CircuitBreakerStats,
)
from .types import CircuitBreakerState
from .metrics import CircuitBreakerMetrics
from .exceptions import CircuitBreakerError, CircuitBreakerOpenError
from .http_circuit_breaker import (
    ResilientHTTPClient,
    HTTPCircuitBreakerError,
    create_resilient_http_client,
)
from .rabbitmq_circuit_breaker import (
    ResilientRabbitMQPublisher,
    RabbitMQCircuitBreakerError,
    create_resilient_rabbitmq_publisher,
)
from .database_circuit_breaker import (
    ResilientDatabaseManager,
    DatabaseCircuitBreakerError,
    create_resilient_database_manager,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitBreakerConfig",
    "CircuitBreakerStats",
    "CircuitBreakerState",
    "CircuitBreakerMetrics",
    "CircuitBreakerError",
    "CircuitBreakerOpenError",
    "ResilientHTTPClient",
    "HTTPCircuitBreakerError",
    "create_resilient_http_client",
    "ResilientRabbitMQPublisher",
    "RabbitMQCircuitBreakerError",
    "create_resilient_rabbitmq_publisher",
    "ResilientDatabaseManager",
    "DatabaseCircuitBreakerError",
    "create_resilient_database_manager",
]

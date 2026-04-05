"""
Circuit Breaker Pattern Implementation for Resilient Service Communication.

Implements the circuit breaker pattern to prevent cascading failures when
calling external services (other microservices, external APIs).

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are rejected immediately
- HALF_OPEN: Testing if service has recovered, limited requests allowed
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Service failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Open after N failures
    success_threshold: int = 2  # Close after N successes in half-open
    timeout: int = 60  # Seconds before retrying from open state
    name: str = "default"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Implements circuit breaker pattern for resilient service calls.

    Usage:
        breaker = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout=60,
            name="feed-service"
        ))

        async with breaker.guard():
            response = await http_client.get("http://feed-service:8101/api/v1/feed")
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.last_state_change_time = datetime.utcnow()
        self._lock = asyncio.Lock()

        logger.info(
            f"CircuitBreaker '{config.name}' initialized: "
            f"failure_threshold={config.failure_threshold}, "
            f"success_threshold={config.success_threshold}, "
            f"timeout={config.timeout}s"
        )

    async def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: Any exception raised by the function
        """
        async with self._lock:
            # Check state and transition if needed
            await self._check_state_transition()

            if self.state == CircuitBreakerState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.config.name}' is OPEN"
                )

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise

    async def record_success(self):
        """Record successful request"""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                logger.debug(
                    f"CircuitBreaker '{self.config.name}': "
                    f"Success in HALF_OPEN state ({self.success_count}/{self.config.success_threshold})"
                )

                if self.success_count >= self.config.success_threshold:
                    await self._close()
            elif self.state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                if self.failure_count > 0:
                    self.failure_count = 0
                    logger.debug(
                        f"CircuitBreaker '{self.config.name}': "
                        "Failure count reset to 0 after success"
                    )

    async def record_failure(self):
        """Record failed request"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            logger.warning(
                f"CircuitBreaker '{self.config.name}': "
                f"Failure recorded ({self.failure_count}/{self.config.failure_threshold})"
            )

            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    await self._open()
            elif self.state == CircuitBreakerState.HALF_OPEN:
                # One failure in half-open reopens circuit
                await self._open()

    async def _open(self):
        """Transition to OPEN state"""
        self.state = CircuitBreakerState.OPEN
        self.success_count = 0
        self.last_state_change_time = datetime.utcnow()
        logger.error(
            f"CircuitBreaker '{self.config.name}' is now OPEN. "
            f"Will retry after {self.config.timeout}s"
        )

    async def _close(self):
        """Transition to CLOSED state"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change_time = datetime.utcnow()
        logger.info(
            f"CircuitBreaker '{self.config.name}' is now CLOSED. "
            f"Service recovered."
        )

    async def _half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change_time = datetime.utcnow()
        logger.info(
            f"CircuitBreaker '{self.config.name}' is now HALF_OPEN. "
            f"Testing service recovery..."
        )

    async def _check_state_transition(self):
        """Check if state should transition (OPEN -> HALF_OPEN)"""
        if self.state == CircuitBreakerState.OPEN:
            time_since_open = datetime.utcnow() - self.last_state_change_time
            if time_since_open >= timedelta(seconds=self.config.timeout):
                logger.info(
                    f"CircuitBreaker '{self.config.name}': "
                    f"Timeout reached ({self.config.timeout}s), transitioning to HALF_OPEN"
                )
                await self._half_open()

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.config.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change_time": self.last_state_change_time.isoformat(),
            "failure_threshold": self.config.failure_threshold,
            "success_threshold": self.config.success_threshold,
            "timeout": self.config.timeout,
        }

    async def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        async with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.last_state_change_time = datetime.utcnow()
            logger.info(f"CircuitBreaker '{self.config.name}' manually reset to CLOSED")

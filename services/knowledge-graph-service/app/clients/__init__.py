"""
HTTP clients for external service communication.
"""

# New implementation with circuit breaker and resilience patterns
from .fmp_client import FMPServiceClient, FMPClientConfig
from .exceptions import (
    FMPServiceError,
    FMPServiceUnavailableError,
    FMPRateLimitError,
    FMPNotFoundError,
    CircuitBreakerOpenError
)

# Legacy implementation (deprecated, use fmp_client.FMPServiceClient)
from .fmp_service_client import FMPServiceClient as LegacyFMPServiceClient

__all__ = [
    # New implementation (recommended)
    "FMPServiceClient",
    "FMPClientConfig",
    "FMPServiceError",
    "FMPServiceUnavailableError",
    "FMPRateLimitError",
    "FMPNotFoundError",
    "CircuitBreakerOpenError",
    # Legacy
    "LegacyFMPServiceClient",
]

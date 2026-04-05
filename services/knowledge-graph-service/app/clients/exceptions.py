"""
Custom exceptions for FMP Service client.
"""


class FMPServiceError(Exception):
    """Base exception for FMP Service errors."""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FMPServiceUnavailableError(FMPServiceError):
    """
    FMP Service is unavailable (circuit breaker open or 503 response).

    Raised when:
    - Circuit breaker is in OPEN state
    - FMP Service returns 503 Service Unavailable
    - Network connectivity issues persist
    """

    def __init__(self, message: str = "FMP Service is unavailable"):
        super().__init__(message, status_code=503)


class FMPRateLimitError(FMPServiceError):
    """
    FMP API rate limit exceeded.

    FMP has a quota of 300 API calls per day. This exception is raised
    when the daily quota has been exhausted.
    """

    def __init__(
        self,
        message: str = "FMP API rate limit exceeded",
        retry_after: int = None
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after  # Seconds until quota resets


class FMPNotFoundError(FMPServiceError):
    """
    Requested resource not found (404).

    Raised when:
    - Asset symbol does not exist
    - Endpoint does not exist
    - FMP API returns 404
    """

    def __init__(self, message: str = "Resource not found", resource: str = None):
        super().__init__(message, status_code=404)
        self.resource = resource


class CircuitBreakerOpenError(FMPServiceError):
    """
    Circuit breaker is open, preventing requests.

    The circuit breaker has detected too many failures and is preventing
    new requests to allow the service to recover.
    """

    def __init__(
        self,
        service_name: str,
        recovery_timeout: int = 30
    ):
        message = (
            f"Circuit breaker for '{service_name}' is OPEN. "
            f"Service will be retried after {recovery_timeout} seconds."
        )
        super().__init__(message, status_code=503)
        self.service_name = service_name
        self.recovery_timeout = recovery_timeout

"""
Standardized Error Handling

Post-Incident #18: Provides consistent error formatting across all consumers
and API endpoints for better observability and debugging.

Error Format Standard:
{
    "error_type": "CypherSyntaxError",
    "message": "Cypher validation failed: ON CREATE SET after SET",
    "context": {
        "article_id": "12345",
        "event_type": "finance.company.updated",
        "symbol": "AAPL"
    },
    "retriable": false,
    "timestamp": "2025-11-25T10:30:00Z"
}
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """
    Standard context for error logging.

    Always include relevant identifiers to trace errors back to
    their source (article_id, event_type, symbol, etc.)
    """
    article_id: Optional[str] = None
    event_type: Optional[str] = None
    symbol: Optional[str] = None
    query_preview: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.article_id:
            result["article_id"] = self.article_id
        if self.event_type:
            result["event_type"] = self.event_type
        if self.symbol:
            result["symbol"] = self.symbol
        if self.query_preview:
            result["query_preview"] = self.query_preview
        if self.extra:
            result.update(self.extra)
        return result


@dataclass
class StandardizedError:
    """
    Standard error format for logging and monitoring.

    Used by consumers and API endpoints to ensure consistent
    error reporting across the service.
    """
    error_type: str
    message: str
    retriable: bool
    context: ErrorContext = field(default_factory=ErrorContext)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "retriable": self.retriable,
            "context": self.context.to_dict(),
            "timestamp": self.timestamp.isoformat()
        }

    def log(self, level: str = "error"):
        """Log the error with standard format."""
        log_func = getattr(logger, level, logger.error)
        log_func(
            f"[{self.error_type}] {self.message}",
            extra=self.to_dict()
        )


def format_consumer_error(
    error: Exception,
    context: ErrorContext,
    retriable: bool = True
) -> StandardizedError:
    """
    Create a standardized error from an exception.

    Args:
        error: The caught exception
        context: Error context (article_id, event_type, etc.)
        retriable: Whether the error is retriable

    Returns:
        StandardizedError ready for logging

    Example:
        try:
            await process_message(msg)
        except Exception as e:
            err = format_consumer_error(
                error=e,
                context=ErrorContext(article_id=msg.article_id),
                retriable=False
            )
            err.log()
    """
    return StandardizedError(
        error_type=type(error).__name__,
        message=str(error),
        retriable=retriable,
        context=context
    )


# Pre-defined error types for common scenarios
class ErrorTypes:
    """Standard error type constants."""

    # Cypher/Neo4j errors
    CYPHER_SYNTAX = "CypherSyntaxError"
    CYPHER_TIMEOUT = "CypherTimeoutError"
    NEO4J_CONNECTION = "Neo4jConnectionError"

    # Message/Event errors
    MESSAGE_DECODE = "MessageDecodeError"
    INVALID_PAYLOAD = "InvalidPayloadError"
    MISSING_FIELD = "MissingFieldError"

    # Rate/Resource errors
    RATE_LIMIT = "RateLimitExceeded"
    RESOURCE_EXHAUSTED = "ResourceExhaustedError"

    # External service errors
    FMP_SERVICE = "FMPServiceError"
    EXTERNAL_TIMEOUT = "ExternalServiceTimeout"


def is_retriable_error(error: Exception) -> bool:
    """
    Determine if an error should be retried.

    Non-retriable errors should go to DLQ immediately.

    Args:
        error: The exception to check

    Returns:
        True if the error might succeed on retry
    """
    from app.services.cypher_validator import CypherSyntaxError
    import json
    import asyncio

    # Non-retriable: these will always fail
    non_retriable_types = (
        CypherSyntaxError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
        TypeError,
    )

    if isinstance(error, non_retriable_types):
        return False

    # Potentially retriable: might succeed after backoff
    retriable_types = (
        asyncio.TimeoutError,
        ConnectionError,
        OSError,
    )

    if isinstance(error, retriable_types):
        return True

    # Default: assume retriable for unknown errors
    return True

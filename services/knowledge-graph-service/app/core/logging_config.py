"""
Structured logging configuration for Knowledge-Graph Service.

Provides JSON-formatted logging with correlation IDs, user context,
and integration with FastAPI request lifecycle.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
import uuid

# Context variables for request-scoped data
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format with standardized fields:
    - timestamp: ISO 8601 format
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - service: Service name
    - message: Log message
    - correlation_id: Request correlation ID (if available)
    - user_id: User ID (if available)
    - extra fields: Any additional context
    """

    def __init__(self, service_name: str = "knowledge-graph-service"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add user ID if available
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add common extra attributes
        for attr in ['asset_type', 'symbol', 'sync_status', 'query_type', 'duration_ms']:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    service_name: str = "knowledge-graph-service",
    json_format: bool = True
) -> None:
    """
    Configure logging for the service.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Service name for log entries
        json_format: Use JSON formatting (True) or simple text (False)
    """
    root_logger = logging.getLogger()

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if json_format:
        formatter = JSONFormatter(service_name=service_name)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, level.upper()))

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standardized configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for the current context.

    Args:
        correlation_id: Correlation ID or None to generate new UUID

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id_var.get()


def set_user_id(user_id: Optional[str]) -> None:
    """Set user ID for the current context."""
    user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Get the current user ID."""
    return user_id_var.get()


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra_fields
) -> None:
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level (logging.DEBUG, logging.INFO, etc.)
        message: Log message
        **extra_fields: Additional fields to include in JSON output
    """
    # Create log record with extra fields
    extra = {'extra_fields': extra_fields} if extra_fields else {}
    logger.log(level, message, extra=extra)


# Convenience functions
def log_sync_operation(
    logger: logging.Logger,
    operation: str,
    asset_type: Optional[str] = None,
    symbols_count: Optional[int] = None,
    duration_ms: Optional[float] = None,
    status: str = "success",
    error: Optional[str] = None
) -> None:
    """
    Log a sync operation with standardized fields.

    Args:
        logger: Logger instance
        operation: Operation name (sync_markets, sync_quotes, etc.)
        asset_type: Asset type being synced
        symbols_count: Number of symbols processed
        duration_ms: Operation duration in milliseconds
        status: Operation status (success, partial, failed)
        error: Error message if failed
    """
    fields = {
        'operation': operation,
        'status': status,
    }

    if asset_type:
        fields['asset_type'] = asset_type
    if symbols_count is not None:
        fields['symbols_count'] = symbols_count
    if duration_ms is not None:
        fields['duration_ms'] = round(duration_ms, 2)
    if error:
        fields['error'] = error

    level = logging.ERROR if status == 'failed' else logging.INFO
    log_with_context(logger, level, f"Sync operation: {operation}", **fields)


def log_neo4j_query(
    logger: logging.Logger,
    query_type: str,
    duration_ms: float,
    error: Optional[str] = None
) -> None:
    """
    Log a Neo4j query execution.

    Args:
        logger: Logger instance
        query_type: Type of query executed
        duration_ms: Query duration in milliseconds
        error: Error message if query failed
    """
    fields = {
        'query_type': query_type,
        'duration_ms': round(duration_ms, 2),
    }

    if error:
        fields['error'] = error
        level = logging.ERROR
        message = f"Neo4j query failed: {query_type}"
    else:
        level = logging.DEBUG
        message = f"Neo4j query executed: {query_type}"

    log_with_context(logger, level, message, **fields)

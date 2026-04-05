"""Standardized event envelope for RabbitMQ messages."""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class EventEnvelope:
    """
    Standard event envelope for all RabbitMQ messages.

    Ensures consistency across all services.

    Example:
        >>> envelope = EventEnvelope(
        ...     event_type="article.created",
        ...     payload={"article_id": "123", "title": "Test"}
        ... )
        >>> envelope.to_dict()
        {'event_id': '...', 'event_type': 'article.created', ...}
    """

    # Required fields (must be provided)
    event_type: str
    payload: Dict[str, Any]

    # Auto-generated fields with sensible defaults
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_version: str = "1.0"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Source identification (from environment)
    source_service: str = field(
        default_factory=lambda: os.getenv("SERVICE_NAME", "unknown")
    )
    source_instance: str = field(
        default_factory=lambda: os.getenv("HOSTNAME", "local")
    )

    # Tracing
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    causation_id: Optional[str] = None

    # Metadata (default to empty dict, not None)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate event envelope after initialization."""
        # Validate event_type format (lowercase, dot-separated, 2+ parts)
        # Allows: article.created, feed.item.created, analysis.v3.request
        if not re.match(r"^[a-z0-9]+(\.[a-z0-9_]+)+$", self.event_type):
            raise ValueError(
                f"Invalid event_type '{self.event_type}'. "
                "Must be dot-notation like 'article.created' or 'feed.item.created'"
            )

        # Validate event_version format
        if not re.match(r"^\d+\.\d+$", self.event_version):
            raise ValueError(
                f"Invalid event_version '{self.event_version}'. "
                "Must be semantic version like '1.0'"
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all envelope fields
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "source_service": self.source_service,
            "source_instance": self.source_instance,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "payload": self.payload,
            "metadata": self.metadata,
        }


# JSON Schema for validation
EVENT_ENVELOPE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": [
        "event_id",
        "event_type",
        "event_version",
        "source_service",
        "timestamp",
        "payload",
    ],
    "properties": {
        "event_id": {"type": "string", "format": "uuid"},
        "event_type": {"type": "string", "pattern": "^[a-z0-9]+(\\.[a-z0-9_]+)+$"},
        "event_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "source_service": {"type": "string"},
        "source_instance": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "correlation_id": {"type": "string"},
        "causation_id": {"type": ["string", "null"]},
        "payload": {"type": "object"},
        "metadata": {"type": "object"},
    },
}

"""Event publisher wrapper using EventEnvelope."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from news_intelligence_common.event_envelope import EventEnvelope
from news_intelligence_common.schemas.validator import EventValidator

# aio_pika is optional - only needed at runtime
try:
    import aio_pika
    from aio_pika import Message, DeliveryMode

    HAS_AIOPIKA = True
except ImportError:
    HAS_AIOPIKA = False
    aio_pika = None  # type: ignore[assignment]
    Message = None  # type: ignore[assignment, misc]
    DeliveryMode = None  # type: ignore[assignment, misc]


def create_event(
    event_type: str,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> EventEnvelope:
    """
    Create an EventEnvelope with the given parameters.

    Args:
        event_type: Event type (e.g., "article.created")
        payload: Event payload data
        correlation_id: Optional correlation ID for tracing
        causation_id: Optional ID of event that caused this one
        metadata: Optional additional metadata

    Returns:
        EventEnvelope instance

    Raises:
        ValueError: If event_type format is invalid
    """
    kwargs: Dict[str, Any] = {
        "event_type": event_type,
        "payload": payload,
    }
    if correlation_id:
        kwargs["correlation_id"] = correlation_id
    if causation_id:
        kwargs["causation_id"] = causation_id
    if metadata:
        kwargs["metadata"] = metadata

    return EventEnvelope(**kwargs)


class EventPublisherWrapper:
    """
    Wrapper for publishing events with EventEnvelope.

    Handles:
    - Wrapping payloads in EventEnvelope
    - JSON serialization
    - aio_pika message creation
    - Optional validation

    Example:
        >>> async with connection.channel() as channel:
        ...     publisher = EventPublisherWrapper(channel, "feed-service")
        ...     await publisher.initialize()
        ...     await publisher.publish("article.created", {"article_id": "123"})
    """

    DEFAULT_EXCHANGE = "news.events"

    def __init__(
        self,
        channel: Any,  # aio_pika.Channel
        service_name: str,
        exchange_name: Optional[str] = None,
        validate: bool = False,
    ) -> None:
        """
        Initialize publisher.

        Args:
            channel: aio_pika channel
            service_name: Name of publishing service
            exchange_name: Exchange name (default: news.events)
            validate: If True, validate events before publishing

        Raises:
            ImportError: If aio_pika is not installed
        """
        if not HAS_AIOPIKA:
            raise ImportError("aio_pika required for EventPublisherWrapper")

        self._channel = channel
        self._service_name = service_name
        self._exchange_name = exchange_name or self.DEFAULT_EXCHANGE
        self._exchange: Optional[Any] = None
        self._validator = EventValidator(strict=validate) if validate else None

        # Set SERVICE_NAME env for EventEnvelope
        os.environ.setdefault("SERVICE_NAME", service_name)

    async def initialize(self) -> None:
        """Initialize exchange."""
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def _publish_envelope_internal(self, envelope: EventEnvelope) -> str:
        """
        Internal method to publish an EventEnvelope.

        Args:
            envelope: EventEnvelope to publish

        Returns:
            event_id of published event
        """
        if self._exchange is None:
            await self.initialize()

        # Validate if enabled
        if self._validator:
            is_valid, errors = self._validator.validate(envelope.to_dict())
            if not is_valid:
                raise ValueError(f"Event validation failed: {errors}")

        # Create message
        message_body = json.dumps(envelope.to_dict()).encode()
        message = Message(
            body=message_body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=envelope.event_id,
            timestamp=datetime.now(timezone.utc),
            app_id=self._service_name,
            type=envelope.event_type,
            correlation_id=envelope.correlation_id,
            headers={
                "event_type": envelope.event_type,
                "event_version": envelope.event_version,
                "source_service": envelope.source_service,
            },
        )

        # Publish (exchange is guaranteed to be set after initialize())
        assert self._exchange is not None
        await self._exchange.publish(message, routing_key=envelope.event_type)

        return envelope.event_id

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Publish event wrapped in EventEnvelope.

        Args:
            event_type: Event type (e.g., "article.created")
            payload: Event payload data
            correlation_id: Optional correlation ID
            causation_id: Optional causation ID
            metadata: Optional metadata

        Returns:
            event_id of published event

        Raises:
            ValueError: If event_type invalid or validation fails
        """
        # Create envelope (this validates event_type format)
        envelope = create_event(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
            metadata=metadata,
        )

        return await self._publish_envelope_internal(envelope)

    async def publish_envelope(self, envelope: EventEnvelope) -> str:
        """
        Publish pre-created EventEnvelope.

        Args:
            envelope: EventEnvelope to publish

        Returns:
            event_id of published event
        """
        return await self._publish_envelope_internal(envelope)

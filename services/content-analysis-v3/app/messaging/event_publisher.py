"""
Event Publisher for Content-Analysis-V3

Publishes analysis completion and failure events to RabbitMQ for consumption
by downstream services (feed-service, notification-service, etc.).

Event Types:
- analysis.v3.completed: V3 analysis pipeline finished successfully
- analysis.v3.failed: V3 analysis pipeline encountered error

Epic 0.3 (Event Schema Standardization):
- All events are wrapped in EventEnvelope from news-intelligence-common
- Standardized event format with event_id, event_version, timestamp, etc.
- Enables distributed tracing via correlation_id and causation_id

Message Format (EventEnvelope):
    {
        "event_id": "uuid",
        "event_type": "analysis.v3.completed",
        "event_version": "1.0",
        "source_service": "content-analysis-v3",
        "source_instance": "hostname",
        "timestamp": "2025-11-19T09:00:00.000Z",
        "correlation_id": "uuid",
        "causation_id": null,
        "payload": {
            "article_id": "550e8400-e29b-41d4-a716-446655440000",
            "success": true,
            "pipeline_version": "3.0",
            "tier0": {...},
            "tier1": {...},
            "tier2": {...},
            "metrics": {...}
        },
        "metadata": {}
    }
"""
import json
import logging
import os
import aio_pika
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.config import settings
from news_intelligence_common import create_event, EventEnvelope

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Async event publisher for RabbitMQ.

    Publishes V3 analysis events to "news.events" topic exchange for consumption
    by downstream services.

    Epic 0.3: Uses EventEnvelope from news-intelligence-common for standardized
    event messaging across all services.
    """

    SERVICE_NAME = "content-analysis-v3"

    def __init__(self):
        """Initialize EventPublisher."""
        # Set SERVICE_NAME environment variable for EventEnvelope
        os.environ.setdefault("SERVICE_NAME", self.SERVICE_NAME)

        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._is_connected = False

    async def connect(self):
        """
        Connect to RabbitMQ and declare the "news.events" topic exchange.

        Uses robust connection for automatic reconnection on failure.
        """
        try:
            # Build RabbitMQ URL
            rabbitmq_url = (
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
                f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            )

            # Create robust connection (auto-reconnects)
            self.connection = await aio_pika.connect_robust(
                rabbitmq_url,
                client_properties={"service": "content-analysis-v3"},
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange (should already exist, but ensure it)
            self.exchange = await self.channel.declare_exchange(
                "news.events",
                type=aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            self._is_connected = True
            logger.info("✓ Connected to RabbitMQ exchange: news.events")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self._is_connected = False
            raise

    async def disconnect(self):
        """Gracefully disconnect from RabbitMQ."""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            self._is_connected = False
            logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Publish an event to the "news.events" topic exchange wrapped in EventEnvelope.

        Epic 0.3: All events are now wrapped in EventEnvelope for standardization.
        The envelope includes event_id, event_version, timestamp, source_service,
        correlation_id, causation_id, and metadata fields.

        Args:
            event_type: Type of event (routing key):
                - "analysis.v3.completed": Analysis finished successfully
                - "analysis.v3.failed": Analysis pipeline error
            payload: Event payload data (must be JSON-serializable)
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional ID of the event that caused this one
            metadata: Optional additional metadata

        Returns:
            bool: True if published successfully, False on error
        """
        if not self._is_connected or not self.exchange:
            logger.error("Cannot publish event: Not connected to RabbitMQ")
            return False

        try:
            # Epic 0.3: Wrap payload in EventEnvelope for standardization
            envelope = create_event(
                event_type=event_type,
                payload=payload,
                correlation_id=correlation_id,
                causation_id=causation_id,
                metadata=metadata,
            )

            # Create message with envelope as body
            message = aio_pika.Message(
                body=json.dumps(envelope.to_dict()).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Survive broker restart
                message_id=envelope.event_id,
                timestamp=datetime.now(timezone.utc),
                app_id=self.SERVICE_NAME,
                type=event_type,
                correlation_id=envelope.correlation_id,
                headers={
                    "event_type": event_type,
                    "event_version": envelope.event_version,
                    "source_service": envelope.source_service,
                },
            )

            # Publish to exchange with routing key = event_type
            await self.exchange.publish(
                message,
                routing_key=event_type,
            )

            logger.info(f"✓ Published event: {event_type} for article {payload.get('article_id')}")
            return True

        except ValueError as e:
            # Invalid event format (EventEnvelope validation)
            logger.error(f"Invalid event format for {event_type}: {e}")
            return False

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if publisher is connected to RabbitMQ."""
        return self._is_connected


# Global publisher instance
_publisher_instance: Optional[EventPublisher] = None


async def get_event_publisher() -> EventPublisher:
    """
    Get or create global singleton EventPublisher instance.

    Singleton pattern ensures one publisher per service process for connection reuse.

    Returns:
        EventPublisher: Global singleton publisher instance (connected if RabbitMQ available)
    """
    global _publisher_instance

    if _publisher_instance is None:
        _publisher_instance = EventPublisher()
        try:
            await _publisher_instance.connect()
        except Exception as e:
            # Allow service to start even if RabbitMQ is not available (local dev mode)
            logger.warning(
                f"RabbitMQ not available, event publishing disabled: {e}. "
                "This is normal for local development without Docker."
            )

    return _publisher_instance


async def close_event_publisher():
    """
    Close global singleton EventPublisher instance.

    Call during service shutdown to gracefully disconnect from RabbitMQ.
    """
    global _publisher_instance

    if _publisher_instance:
        await _publisher_instance.disconnect()
        _publisher_instance = None

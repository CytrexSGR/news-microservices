"""
Event publisher service for RabbitMQ integration

Publishes events to RabbitMQ for other services to consume.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal

import aio_pika
from aio_pika import Message, ExchangeType

from app.core.config import settings

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID, datetime, and Decimal objects."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class EventPublisher:
    """Service for publishing events to RabbitMQ."""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        """Connect to RabbitMQ and set up exchange."""
        try:
            # Build RabbitMQ URL
            rabbitmq_url = (
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@"
                f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{settings.RABBITMQ_VHOST}"
            )

            # Create connection
            self.connection = await aio_pika.connect_robust(
                rabbitmq_url,
                client_properties={"service": "scraping-service"},
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange (topic type for routing flexibility)
            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE,
                type=ExchangeType.TOPIC,
                durable=True,
            )

            logger.info(f"Connected to RabbitMQ exchange: {settings.RABBITMQ_EXCHANGE}")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("Disconnected from RabbitMQ")

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish an event to RabbitMQ.

        Args:
            event_type: Type of event (e.g., "item.scraped", "scraping.failed")
            payload: Event payload data
            correlation_id: Optional correlation ID for tracking

        Returns:
            True if published successfully, False otherwise

        Event types:
            - item.scraped: Item content was successfully scraped
            - scraping.failed: Scraping failed for an item
        """
        try:
            # Ensure connected
            if not self.exchange:
                await self.connect()

            # Prepare message
            message_body = {
                "event_type": event_type,
                "service": "scraping-service",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }

            if correlation_id:
                message_body["correlation_id"] = correlation_id

            # Create message (use custom encoder for UUID/datetime/Decimal)
            message = Message(
                body=json.dumps(message_body, cls=JSONEncoder).encode(),
                content_type="application/json",
                delivery_mode=2,  # Persistent
                timestamp=datetime.now(timezone.utc),
                app_id="scraping-service",
                type=event_type,
            )

            # Publish to exchange with routing key
            routing_key = event_type.replace(".", "_")
            await self.exchange.publish(
                message,
                routing_key=routing_key,
            )

            logger.debug(f"Published event: {event_type} with routing key: {routing_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False

    async def publish_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Publish multiple events in a batch.

        Args:
            events: List of events, each with "event_type" and "payload"

        Returns:
            Number of successfully published events
        """
        success_count = 0

        for event in events:
            if await self.publish_event(
                event.get("event_type"),
                event.get("payload"),
                event.get("correlation_id"),
            ):
                success_count += 1

        return success_count


# Global publisher instance
_publisher_instance: Optional[EventPublisher] = None


async def get_event_publisher() -> EventPublisher:
    """Get or create global event publisher instance."""
    global _publisher_instance

    if _publisher_instance is None:
        _publisher_instance = EventPublisher()
        await _publisher_instance.connect()

    return _publisher_instance


async def close_event_publisher():
    """Close global event publisher."""
    global _publisher_instance

    if _publisher_instance:
        await _publisher_instance.disconnect()
        _publisher_instance = None

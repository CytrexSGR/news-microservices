"""
Event publisher service for RabbitMQ integration

Publishes events to RabbitMQ for other services to consume.

Issue P1-7: Added connection recovery with automatic reconnection.

Epic 0.3 (Event Schema Standardization):
- All events are wrapped in EventEnvelope from news-intelligence-common
- Standardized event format with event_id, event_version, timestamp, etc.
- Enables distributed tracing via correlation_id and causation_id
"""
import json
import logging
import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal

import aio_pika
from aio_pika import Message, ExchangeType
from aio_pika.exceptions import AMQPConnectionError, ChannelClosed

from app.core.config import settings
from news_intelligence_common import create_event, EventEnvelope

logger = logging.getLogger(__name__)

# Set SERVICE_NAME for EventEnvelope
SERVICE_NAME = "scraping-service"
os.environ.setdefault("SERVICE_NAME", SERVICE_NAME)

# Connection recovery settings
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY_BASE = 1.0  # seconds
RECONNECT_DELAY_MAX = 10.0  # seconds


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
    """
    Service for publishing events to RabbitMQ.

    Issue P1-7: Includes automatic connection recovery with exponential backoff.
    """

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._connecting = False  # Lock to prevent concurrent reconnection attempts

    async def connect(self):
        """Connect to RabbitMQ and set up exchange."""
        try:
            # Build RabbitMQ URL
            rabbitmq_url = (
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@"
                f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{settings.RABBITMQ_VHOST}"
            )

            # Create connection with robust reconnection
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

    def _is_connected(self) -> bool:
        """Check if connection is healthy."""
        return (
            self.connection is not None
            and not self.connection.is_closed
            and self.channel is not None
            and not self.channel.is_closed
            and self.exchange is not None
        )

    async def _ensure_connected(self) -> bool:
        """
        Ensure connection is established, with automatic reconnection.

        Issue P1-7: Implements exponential backoff for reconnection attempts.

        Returns:
            True if connected, False if all reconnection attempts failed
        """
        if self._is_connected():
            return True

        # Prevent concurrent reconnection attempts
        if self._connecting:
            # Wait for ongoing reconnection
            for _ in range(50):  # Wait up to 5 seconds
                await asyncio.sleep(0.1)
                if self._is_connected():
                    return True
            return False

        self._connecting = True
        try:
            for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
                try:
                    # Close existing broken connections
                    await self._cleanup_connection()

                    # Reconnect
                    await self.connect()
                    logger.info(f"✅ RabbitMQ reconnection successful (attempt {attempt})")
                    return True

                except (AMQPConnectionError, ChannelClosed, Exception) as e:
                    delay = min(RECONNECT_DELAY_BASE * (2 ** (attempt - 1)), RECONNECT_DELAY_MAX)
                    logger.warning(
                        f"RabbitMQ reconnection attempt {attempt}/{MAX_RECONNECT_ATTEMPTS} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    if attempt < MAX_RECONNECT_ATTEMPTS:
                        await asyncio.sleep(delay)

            logger.error(f"❌ RabbitMQ reconnection failed after {MAX_RECONNECT_ATTEMPTS} attempts")
            return False
        finally:
            self._connecting = False

    async def _cleanup_connection(self):
        """Clean up existing connection resources."""
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
        except Exception:
            pass

        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
        except Exception:
            pass

        self.channel = None
        self.connection = None
        self.exchange = None

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
        causation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish an event to RabbitMQ wrapped in EventEnvelope.

        Epic 0.3: All events are now wrapped in EventEnvelope for standardization.

        Args:
            event_type: Type of event (e.g., "scraping.item_scraped", "scraping.failed")
            payload: Event payload data
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional ID of the event that caused this one

        Returns:
            True if published successfully, False otherwise

        Event types:
            - scraping.item_scraped: Item content was successfully scraped
            - scraping.failed: Scraping failed for an item

        Issue P1-7: Uses automatic reconnection on connection failures.
        """
        try:
            # Ensure connected with automatic reconnection (P1-7)
            if not await self._ensure_connected():
                logger.error(f"Cannot publish event {event_type}: RabbitMQ connection unavailable")
                return False

            # Epic 0.3: Wrap payload in EventEnvelope for standardization
            envelope = create_event(
                event_type=event_type,
                payload=payload,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

            # Create message (use custom encoder for UUID/datetime/Decimal)
            message = Message(
                body=json.dumps(envelope.to_dict(), cls=JSONEncoder).encode(),
                content_type="application/json",
                delivery_mode=2,  # Persistent
                timestamp=datetime.now(timezone.utc),
                app_id=SERVICE_NAME,
                type=event_type,
            )

            # Publish to exchange with routing key (use event_type directly for topic routing)
            await self.exchange.publish(
                message,
                routing_key=event_type,
            )

            logger.debug(f"Published event: {event_type} [event_id={envelope.event_id}]")
            return True

        except ValueError as e:
            # Invalid event_type format (EventEnvelope validation)
            logger.error(f"Invalid event format for {event_type}: {e}")
            return False

        except (AMQPConnectionError, ChannelClosed) as e:
            # Connection lost during publish - try to reconnect and retry once
            logger.warning(f"Connection lost during publish of {event_type}: {e}. Attempting reconnection...")
            if await self._ensure_connected():
                try:
                    # Retry publish after reconnection
                    await self.exchange.publish(
                        message,
                        routing_key=event_type,
                    )
                    logger.info(f"Successfully published {event_type} after reconnection")
                    return True
                except Exception as retry_error:
                    logger.error(f"Failed to publish {event_type} after reconnection: {retry_error}")
                    return False
            return False

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

"""Event publishing and consuming utilities using RabbitMQ."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import uuid4

import aio_pika
from aio_pika import ExchangeType, Message
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """Base event model."""
    event_id: str
    event_type: str
    service_name: str
    timestamp: datetime
    correlation_id: Optional[str] = None
    user_id: Optional[int] = None
    data: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None


class EventPublisher:
    """Publish events to RabbitMQ."""

    def __init__(
        self,
        service_name: str,
        connection_url: Optional[str] = None,
        exchange_name: str = "news_mcp_events",
        exchange_type: ExchangeType = ExchangeType.TOPIC,
    ):
        """Initialize event publisher.

        Args:
            service_name: Name of the publishing service
            connection_url: RabbitMQ connection URL
            exchange_name: Exchange name for publishing
            exchange_type: Exchange type (topic, direct, fanout)
        """
        self.service_name = service_name
        self.connection_url = connection_url or settings.rabbitmq_url
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self._connection: Optional[aio_pika.Connection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            return

        try:
            self._connection = await aio_pika.connect_robust(
                self.connection_url,
                client_properties={"service": self.service_name},
            )
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                type=self.exchange_type,
                durable=True,
            )
            logger.info(f"Connected to RabbitMQ exchange: {self.exchange_name}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish(
        self,
        event_type: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
        user_id: Optional[int] = None,
        routing_key: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Publish an event.

        Args:
            event_type: Type of event (e.g., "feed.article.created")
            data: Event data payload
            correlation_id: Correlation ID for tracking related events
            user_id: User ID associated with the event
            routing_key: Custom routing key (defaults to event_type)
            metadata: Additional metadata

        Returns:
            Event ID
        """
        await self.connect()

        event = Event(
            event_id=str(uuid4()),
            event_type=event_type,
            service_name=self.service_name,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id or str(uuid4()),
            user_id=user_id,
            data=data,
            metadata=metadata or {},
        )

        message = Message(
            body=event.model_dump_json().encode(),
            content_type="application/json",
            correlation_id=event.correlation_id,
            message_id=event.event_id,
            timestamp=event.timestamp,
            app_id=self.service_name,
            headers={
                "event_type": event_type,
                "service": self.service_name,
            },
        )

        routing_key = routing_key or event_type
        await self._exchange.publish(message, routing_key=routing_key)

        logger.info(f"Published event: {event_type} (ID: {event.event_id})")
        return event.event_id

    async def publish_batch(
        self,
        events: list[tuple[str, dict[str, Any]]],
        correlation_id: Optional[str] = None,
    ) -> list[str]:
        """Publish multiple events.

        Args:
            events: List of (event_type, data) tuples
            correlation_id: Shared correlation ID

        Returns:
            List of event IDs
        """
        correlation_id = correlation_id or str(uuid4())
        event_ids = []

        for event_type, data in events:
            event_id = await self.publish(
                event_type=event_type,
                data=data,
                correlation_id=correlation_id,
            )
            event_ids.append(event_id)

        return event_ids

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class EventConsumer:
    """Consume events from RabbitMQ."""

    def __init__(
        self,
        service_name: str,
        queue_name: Optional[str] = None,
        connection_url: Optional[str] = None,
        exchange_name: str = "news_mcp_events",
        exchange_type: ExchangeType = ExchangeType.TOPIC,
        prefetch_count: int = 10,
    ):
        """Initialize event consumer.

        Args:
            service_name: Name of the consuming service
            queue_name: Queue name (defaults to service_name_events)
            connection_url: RabbitMQ connection URL
            exchange_name: Exchange name to bind to
            exchange_type: Exchange type
            prefetch_count: Number of messages to prefetch
        """
        self.service_name = service_name
        self.queue_name = queue_name or f"{service_name}_events"
        self.connection_url = connection_url or settings.rabbitmq_url
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.prefetch_count = prefetch_count
        self._connection: Optional[aio_pika.Connection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._queue: Optional[aio_pika.Queue] = None
        self._consumer_tag: Optional[str] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            return

        try:
            self._connection = await aio_pika.connect_robust(
                self.connection_url,
                client_properties={"service": self.service_name},
            )
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self.prefetch_count)

            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                type=self.exchange_type,
                durable=True,
            )

            self._queue = await self._channel.declare_queue(
                self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": f"{self.exchange_name}.dlx",
                    "x-message-ttl": 86400000,  # 24 hours
                },
            )

            logger.info(f"Connected to RabbitMQ queue: {self.queue_name}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._consumer_tag:
            await self._queue.cancel(self._consumer_tag)
            self._consumer_tag = None

        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def subscribe(
        self,
        routing_pattern: str,
        callback: Callable[[Event], Any],
        auto_ack: bool = False,
    ) -> None:
        """Subscribe to events matching a routing pattern.

        Args:
            routing_pattern: Routing pattern (e.g., "feed.*", "*.created")
            callback: Async callback function to handle events
            auto_ack: Automatically acknowledge messages
        """
        await self.connect()

        # Bind queue to exchange with routing pattern
        await self._queue.bind(self._exchange, routing_key=routing_pattern)
        logger.info(f"Subscribed to pattern: {routing_pattern}")

        async def process_message(message: aio_pika.IncomingMessage):
            """Process incoming message."""
            try:
                # Parse event
                event_data = json.loads(message.body)
                event = Event(**event_data)

                # Call callback
                result = await callback(event)

                # Acknowledge message if not auto-ack
                if not auto_ack:
                    await message.ack()

                logger.debug(f"Processed event: {event.event_type} (ID: {event.event_id})")

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Reject message and send to dead letter queue
                if not auto_ack:
                    await message.reject(requeue=False)

        # Start consuming
        self._consumer_tag = await self._queue.consume(
            process_message,
            no_ack=auto_ack,
        )

    async def consume(
        self,
        routing_patterns: list[str],
        handlers: dict[str, Callable[[Event], Any]],
        default_handler: Optional[Callable[[Event], Any]] = None,
    ) -> None:
        """Consume events with multiple handlers.

        Args:
            routing_patterns: List of routing patterns to subscribe to
            handlers: Dict mapping event types to handler functions
            default_handler: Default handler for unmatched events
        """
        await self.connect()

        # Bind all routing patterns
        for pattern in routing_patterns:
            await self._queue.bind(self._exchange, routing_key=pattern)
            logger.info(f"Subscribed to pattern: {pattern}")

        async def process_message(message: aio_pika.IncomingMessage):
            """Process incoming message with appropriate handler."""
            try:
                # Parse event
                event_data = json.loads(message.body)
                event = Event(**event_data)

                # Find and call appropriate handler
                handler = handlers.get(event.event_type, default_handler)
                if handler:
                    await handler(event)
                    await message.ack()
                    logger.debug(f"Processed event: {event.event_type}")
                else:
                    logger.warning(f"No handler for event type: {event.event_type}")
                    await message.reject(requeue=False)

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.reject(requeue=False)

        # Start consuming
        self._consumer_tag = await self._queue.consume(process_message)
        logger.info("Started consuming events")

    async def run_forever(self) -> None:
        """Run consumer forever."""
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            await self.disconnect()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Event handler decorators
def event_handler(event_type: str):
    """Decorator for event handler functions."""
    def decorator(func: Callable):
        func.event_type = event_type
        return func
    return decorator


# Export convenience items
__all__ = [
    "Event",
    "EventPublisher",
    "EventConsumer",
    "event_handler",
]
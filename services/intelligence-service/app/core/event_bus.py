"""
Event-Driven Communication via RabbitMQ.

Provides publisher and subscriber functionality for asynchronous communication
between microservices using RabbitMQ message broker.

Event Types:
- event.detected: Published when new intelligence events are detected
- cluster.updated: Published when cluster is updated with new information
- risk.changed: Published when risk score changes significantly
- event.articles.analyzed: Subscribed from analytics/feed services
"""

import json
import logging
from typing import Callable, Dict, Any, Optional
from abc import ABC, abstractmethod
import aio_pika
from aio_pika import Channel, Exchange, Queue
from contextlib import asynccontextmanager

from .config import settings

logger = logging.getLogger(__name__)


class EventBusError(Exception):
    """Base exception for event bus errors"""
    pass


class EventPublisher:
    """
    Publishes events to RabbitMQ exchange.

    Events are published to a central exchange that multiple subscribers can listen to.
    """

    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None

    async def initialize(self):
        """Initialize publisher (create channel and exchange)"""
        try:
            self.channel = await self.connection.channel()

            # Create exchange for events
            self.exchange = await self.channel.declare_exchange(
                name="intelligence.events",
                type=aio_pika.ExchangeType.TOPIC,
                durable=True,
                auto_delete=False,
            )

            logger.info("EventPublisher initialized. Exchange: intelligence.events")

        except Exception as e:
            logger.error(f"Failed to initialize EventPublisher: {e}")
            raise EventBusError(f"EventPublisher initialization failed: {e}") from e

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        routing_key: Optional[str] = None,
    ):
        """
        Publish event to exchange.

        Args:
            event_type: Type of event (e.g., "event.detected", "cluster.updated")
            data: Event data (will be JSON encoded)
            routing_key: RabbitMQ routing key (if None, uses event_type)

        Raises:
            EventBusError: If publish fails
        """
        if not self.channel or not self.exchange:
            raise EventBusError("Publisher not initialized. Call initialize() first.")

        try:
            # Use event_type as routing key if not provided
            routing_key = routing_key or event_type

            # Create message with metadata
            message_body = {
                "event_type": event_type,
                "data": data,
                "source": "intelligence-service",
            }

            # Create AMQP message
            message = aio_pika.Message(
                body=json.dumps(message_body).encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )

            # Publish
            await self.exchange.publish(message, routing_key=routing_key)

            logger.debug(
                f"Published event: {event_type} (routing_key: {routing_key})"
            )

        except Exception as e:
            logger.error(
                f"Failed to publish event {event_type}: {e}"
            )
            raise EventBusError(f"Failed to publish event: {e}") from e

    async def close(self):
        """Close publisher"""
        if self.channel:
            await self.channel.close()


class EventSubscriber:
    """
    Subscribes to events from RabbitMQ.

    Creates a queue bound to the central exchange with specific routing patterns.
    """

    def __init__(
        self,
        connection: aio_pika.Connection,
        subscriber_name: str,
    ):
        self.connection = connection
        self.subscriber_name = subscriber_name
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None
        self.queue: Optional[Queue] = None
        self.handlers: Dict[str, Callable] = {}

    async def initialize(self):
        """Initialize subscriber (create channel, queue, and bind to exchange)"""
        try:
            self.channel = await self.connection.channel()

            # Get or create exchange
            self.exchange = await self.channel.declare_exchange(
                name="intelligence.events",
                type=aio_pika.ExchangeType.TOPIC,
                durable=True,
                auto_delete=False,
            )

            # Create queue for this subscriber
            queue_name = f"intelligence.{self.subscriber_name}"
            self.queue = await self.channel.declare_queue(
                name=queue_name,
                durable=True,
                auto_delete=False,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hours
                    "x-dead-letter-exchange": "intelligence.dlx",
                },
            )

            logger.info(
                f"EventSubscriber initialized. "
                f"Subscriber: {self.subscriber_name}, Queue: {queue_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize EventSubscriber: {e}")
            raise EventBusError(f"EventSubscriber initialization failed: {e}") from e

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        routing_pattern: Optional[str] = None,
    ):
        """
        Register handler for event type.

        Args:
            event_type: Event type to listen for
            handler: Async handler function(event_type: str, data: dict)
            routing_pattern: RabbitMQ routing pattern (if None, uses event_type)
        """
        routing_pattern = routing_pattern or event_type
        self.handlers[event_type] = {
            "handler": handler,
            "routing_pattern": routing_pattern,
        }
        logger.debug(f"Subscribed to {event_type} (pattern: {routing_pattern})")

    async def start_listening(self):
        """
        Start listening for events.

        Binds queue to exchange for all registered patterns and starts consuming.
        """
        if not self.queue or not self.exchange:
            raise EventBusError("Subscriber not initialized. Call initialize() first.")

        try:
            # Bind queue to exchange for each handler
            for event_type, handler_info in self.handlers.items():
                routing_pattern = handler_info["routing_pattern"]
                await self.queue.bind(self.exchange, routing_key=routing_pattern)
                logger.debug(
                    f"Queue bound to exchange: {event_type} -> {routing_pattern}"
                )

            # Start consuming
            await self.queue.consume(self._on_message, no_ack=False)
            logger.info(f"EventSubscriber {self.subscriber_name} started listening")

        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            raise EventBusError(f"Failed to start listening: {e}") from e

    async def _on_message(self, message: aio_pika.IncomingMessage):
        """Internal message handler"""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode("utf-8"))
                event_type = body.get("event_type")
                data = body.get("data", {})

                # Find and call handler
                if event_type in self.handlers:
                    handler = self.handlers[event_type]["handler"]
                    await handler(event_type, data)
                    logger.debug(f"Processed event: {event_type}")
                else:
                    logger.warning(f"No handler for event type: {event_type}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                raise

    async def close(self):
        """Close subscriber"""
        if self.channel:
            await self.channel.close()


class EventBus:
    """
    Central event bus for intelligence service.

    Manages both publishing and subscribing to events via RabbitMQ.
    """

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.publisher: Optional[EventPublisher] = None
        self.subscriber: Optional[EventSubscriber] = None
        self._initialized = False

    async def initialize(self, subscriber_name: str = "intelligence-service"):
        """
        Initialize event bus (connect to RabbitMQ, set up publisher and subscriber).

        Args:
            subscriber_name: Name for this subscriber
        """
        try:
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(
                settings.rabbitmq_url
            )

            logger.info(
                f"Connected to RabbitMQ: {settings.RABBITMQ_HOST}:"
                f"{settings.RABBITMQ_PORT}"
            )

            # Initialize publisher
            self.publisher = EventPublisher(self.connection)
            await self.publisher.initialize()

            # Initialize subscriber
            self.subscriber = EventSubscriber(self.connection, subscriber_name)
            await self.subscriber.initialize()

            self._initialized = True
            logger.info("EventBus initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize EventBus: {e}")
            raise EventBusError(f"EventBus initialization failed: {e}") from e

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        routing_key: Optional[str] = None,
    ):
        """Publish event"""
        if not self._initialized or not self.publisher:
            raise EventBusError("EventBus not initialized")
        await self.publisher.publish(event_type, data, routing_key)

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        routing_pattern: Optional[str] = None,
    ):
        """Subscribe to event type"""
        if not self._initialized or not self.subscriber:
            raise EventBusError("EventBus not initialized")
        self.subscriber.subscribe(event_type, handler, routing_pattern)

    async def start(self):
        """Start listening for events"""
        if not self._initialized or not self.subscriber:
            raise EventBusError("EventBus not initialized")
        await self.subscriber.start_listening()

    async def close(self):
        """Close event bus"""
        if self.publisher:
            await self.publisher.close()
        if self.subscriber:
            await self.subscriber.close()
        if self.connection:
            await self.connection.close()
        logger.info("EventBus closed")


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_event_bus() -> EventBus:
    """Get or create global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def initialize_event_bus(subscriber_name: str = "intelligence-service"):
    """Initialize global event bus"""
    global _event_bus
    _event_bus = EventBus()
    await _event_bus.initialize(subscriber_name)
    return _event_bus


@asynccontextmanager
async def event_bus_context(subscriber_name: str = "intelligence-service"):
    """Context manager for event bus"""
    bus = EventBus()
    await bus.initialize(subscriber_name)
    try:
        yield bus
    finally:
        await bus.close()

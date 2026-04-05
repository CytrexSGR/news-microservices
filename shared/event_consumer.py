"""
Event Consumer Library for News Microservices
Provides async RabbitMQ consumption with handler registration and error handling
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import aio_pika
from aio_pika import ExchangeType, IncomingMessage

logger = logging.getLogger(__name__)


class EventConsumer:
    """Async event consumer for RabbitMQ with handler registration"""

    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str,
        exchange_name: str = "news.events",
        service_name: Optional[str] = None,
        prefetch_count: int = 10,
    ):
        """
        Initialize event consumer

        Args:
            rabbitmq_url: RabbitMQ connection URL (amqp://...)
            queue_name: Name of the queue to consume from
            exchange_name: Name of the exchange
            service_name: Name of the service consuming events
            prefetch_count: Number of messages to prefetch
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.service_name = service_name or "unknown-service"
        self.prefetch_count = prefetch_count

        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._queue: Optional[aio_pika.Queue] = None
        self._handlers: Dict[str, Callable] = {}
        self._is_running = False

    async def initialize(self):
        """Initialize connection, channel, and queue"""
        if self._connection:
            return

        logger.info(
            f"Initializing event consumer for {self.service_name} (queue={self.queue_name})"
        )

        # Create connection
        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)

        # Create channel
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=self.prefetch_count)

        # Declare exchange
        exchange = await self._channel.declare_exchange(
            self.exchange_name,
            ExchangeType.TOPIC,
            durable=True,
            auto_delete=False,
        )

        # Declare queue
        self._queue = await self._channel.declare_queue(
            self.queue_name,
            durable=True,
        )

        logger.info(
            f"Event consumer initialized for {self.service_name} (queue={self.queue_name})"
        )

    async def close(self):
        """Close connection and channel"""
        logger.info(f"Closing event consumer for {self.service_name}")

        self._is_running = False

        if self._channel:
            await self._channel.close()

        if self._connection:
            await self._connection.close()

        logger.info(f"Event consumer closed for {self.service_name}")

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler

        Args:
            event_type: Event type to handle (e.g., 'article.created')
            handler: Async function to handle the event (receives event dict)
        """
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def start_consuming(self):
        """Start consuming events from the queue"""
        if not self._connection:
            await self.initialize()

        if self._is_running:
            logger.warning(f"Consumer already running for {self.service_name}")
            return

        self._is_running = True
        logger.info(
            f"Starting event consumer for {self.service_name} (queue={self.queue_name})"
        )

        await self._queue.consume(self._process_message)

        logger.info(f"Event consumer started for {self.service_name}")

    async def _process_message(self, message: IncomingMessage):
        """
        Process incoming message

        Args:
            message: Incoming RabbitMQ message
        """
        async with message.process():
            try:
                # Parse message
                event = json.loads(message.body.decode("utf-8"))

                event_type = event.get("event_type")
                event_id = event.get("event_id")

                if not event_type:
                    logger.error("Received message without event_type")
                    return

                logger.debug(
                    f"Processing event {event_type} with ID {event_id} "
                    f"in {self.service_name}"
                )

                # Find handler
                handler = self._handlers.get(event_type)

                if not handler:
                    logger.warning(
                        f"No handler registered for event type: {event_type} "
                        f"in {self.service_name}"
                    )
                    return

                # Call handler
                await handler(event)

                logger.info(
                    f"Successfully processed event {event_type} with ID {event_id} "
                    f"in {self.service_name}"
                )

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message JSON: {e}")
                # Message will be rejected and moved to DLQ

            except Exception as e:
                logger.error(
                    f"Error processing message in {self.service_name}: {e}",
                    exc_info=True,
                )
                # Message will be requeued or moved to DLQ based on retry count

    async def run_forever(self):
        """
        Run consumer forever (blocking)
        Handles reconnection on connection loss
        """
        await self.start_consuming()

        logger.info(f"Consumer running forever for {self.service_name}")

        # Keep running until stopped
        while self._is_running:
            await asyncio.sleep(1)

        logger.info(f"Consumer stopped for {self.service_name}")


class MultiEventConsumer:
    """Consumer for multiple event types with routing"""

    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str,
        routing_keys: list[str],
        exchange_name: str = "news.events",
        service_name: Optional[str] = None,
        prefetch_count: int = 10,
    ):
        """
        Initialize multi-event consumer

        Args:
            rabbitmq_url: RabbitMQ connection URL
            queue_name: Queue name
            routing_keys: List of routing keys to bind
            exchange_name: Exchange name
            service_name: Service name
            prefetch_count: Prefetch count
        """
        self.consumer = EventConsumer(
            rabbitmq_url=rabbitmq_url,
            queue_name=queue_name,
            exchange_name=exchange_name,
            service_name=service_name,
            prefetch_count=prefetch_count,
        )
        self.routing_keys = routing_keys

    async def initialize(self):
        """Initialize consumer and bind routing keys"""
        await self.consumer.initialize()

        # Bind routing keys
        exchange = await self.consumer._channel.get_exchange(self.consumer.exchange_name)

        for routing_key in self.routing_keys:
            await self.consumer._queue.bind(exchange, routing_key=routing_key)
            logger.info(
                f"Bound queue {self.consumer.queue_name} to routing key {routing_key}"
            )

    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.consumer.register_handler(event_type, handler)

    async def start_consuming(self):
        """Start consuming events"""
        await self.consumer.start_consuming()

    async def run_forever(self):
        """Run consumer forever"""
        await self.consumer.run_forever()

    async def close(self):
        """Close consumer"""
        await self.consumer.close()


# Helper function to create and run consumer
async def create_consumer(
    rabbitmq_url: str,
    queue_name: str,
    routing_keys: list[str],
    handlers: Dict[str, Callable],
    service_name: Optional[str] = None,
) -> MultiEventConsumer:
    """
    Create and initialize a multi-event consumer

    Args:
        rabbitmq_url: RabbitMQ connection URL
        queue_name: Queue name
        routing_keys: List of routing keys
        handlers: Dict mapping event types to handler functions
        service_name: Service name

    Returns:
        Initialized MultiEventConsumer
    """
    consumer = MultiEventConsumer(
        rabbitmq_url=rabbitmq_url,
        queue_name=queue_name,
        routing_keys=routing_keys,
        service_name=service_name,
    )

    await consumer.initialize()

    # Register all handlers
    for event_type, handler in handlers.items():
        consumer.register_handler(event_type, handler)

    return consumer

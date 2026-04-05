# services/sitrep-service/app/workers/cluster_consumer.py
"""RabbitMQ consumer for cluster events.

Consumes cluster events from the news.events exchange and forwards them
to the StoryAggregator for processing and ranking.

Events Consumed:
    - cluster.created: routing key "cluster.created"
    - cluster.updated: routing key "cluster.updated"
    - cluster.burst_detected: routing key "cluster.burst_detected"

Example:
    >>> from app.workers.cluster_consumer import start_consumer, stop_consumer
    >>> await start_consumer()
    >>> # Consumer runs in background task
    >>> await stop_consumer()
"""

import asyncio
import json
import logging
from typing import Optional

import aio_pika
from aio_pika import IncomingMessage

from app.config import settings
from app.schemas.events import parse_cluster_event, ClusterEvent
from app.services.story_aggregator import StoryAggregator

logger = logging.getLogger(__name__)

# Global consumer instance
_consumer: Optional["ClusterEventConsumer"] = None
_aggregator: Optional[StoryAggregator] = None


class ClusterEventConsumer:
    """
    Consumer for cluster events from RabbitMQ.

    Connects to the news.events exchange and binds to cluster event
    routing keys. Processes incoming messages and forwards parsed
    events to the StoryAggregator.

    Attributes:
        aggregator: StoryAggregator instance for handling events
        connection: RabbitMQ connection
        channel: RabbitMQ channel
        queue: Bound queue for cluster events
    """

    def __init__(self, aggregator: StoryAggregator):
        """
        Initialize consumer with aggregator.

        Args:
            aggregator: StoryAggregator to handle parsed events
        """
        self.aggregator = aggregator
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self._consuming = False

    async def connect(self):
        """
        Connect to RabbitMQ and setup queue bindings.

        Creates a robust connection, declares the exchange (if not exists),
        creates a durable queue, and binds to cluster event routing keys.

        Raises:
            aio_pika.AMQPError: If connection fails
        """
        logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_HOST}...")

        # Create robust connection (auto-reconnect)
        self.connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL,
            client_properties={"connection_name": f"{settings.SERVICE_NAME}-consumer"},
        )

        # Create channel with prefetch
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        # Declare exchange (idempotent - uses existing if present)
        exchange = await self.channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Declare durable queue
        self.queue = await self.channel.declare_queue(
            settings.RABBITMQ_CLUSTER_QUEUE,
            durable=True,
        )

        # Bind to cluster event routing keys
        routing_keys = [
            "cluster.created",
            "cluster.updated",
            "cluster.burst_detected",
        ]

        for routing_key in routing_keys:
            await self.queue.bind(exchange, routing_key=routing_key)
            logger.debug(f"Bound to routing key: {routing_key}")

        logger.info(
            f"Connected to RabbitMQ, exchange: {settings.RABBITMQ_EXCHANGE}, "
            f"queue: {settings.RABBITMQ_CLUSTER_QUEUE}"
        )

    async def start_consuming(self):
        """
        Start consuming messages from the queue.

        Runs in a loop processing messages until stop_consuming() is called.
        Messages are acknowledged after successful processing.

        Raises:
            RuntimeError: If not connected to RabbitMQ
        """
        if not self.queue:
            raise RuntimeError("Not connected to RabbitMQ - call connect() first")

        self._consuming = True
        await self.queue.consume(self._process_message)
        logger.info("Started consuming cluster events")

    async def _process_message(self, message: IncomingMessage):
        """
        Process incoming cluster event message.

        Parses the message body, extracts the event, and forwards
        to the aggregator for handling.

        Args:
            message: Incoming RabbitMQ message
        """
        async with message.process():
            try:
                # Parse message body
                body = json.loads(message.body.decode())
                event = parse_cluster_event(body)

                if event is None:
                    logger.warning(
                        f"Unknown event type: {body.get('event_type')}, "
                        f"routing_key: {message.routing_key}"
                    )
                    return

                # Forward to aggregator
                await self.aggregator.handle_event(event)

                logger.debug(
                    f"Processed event: {type(event).__name__}, "
                    f"routing_key: {message.routing_key}"
                )

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message body: {e}")
            except Exception as e:
                logger.exception(f"Error processing message: {e}")

    async def disconnect(self):
        """
        Disconnect from RabbitMQ gracefully.

        Stops consuming and closes the connection.
        """
        self._consuming = False

        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")


async def start_consumer() -> StoryAggregator:
    """
    Start the global consumer instance.

    Creates a StoryAggregator, connects to RabbitMQ, and starts
    consuming messages in a background task.

    Returns:
        StoryAggregator instance for accessing aggregated stories
    """
    global _consumer, _aggregator

    # Create aggregator
    _aggregator = StoryAggregator()

    # Create and connect consumer
    _consumer = ClusterEventConsumer(_aggregator)
    await _consumer.connect()

    # Run consumer in background task
    asyncio.create_task(_consumer.start_consuming())

    logger.info("Cluster event consumer started")
    return _aggregator


async def stop_consumer():
    """
    Stop the global consumer instance.

    Disconnects from RabbitMQ and cleans up resources.
    """
    global _consumer, _aggregator

    if _consumer:
        await _consumer.disconnect()
        _consumer = None

    _aggregator = None
    logger.info("Cluster event consumer stopped")


def get_aggregator() -> Optional[StoryAggregator]:
    """
    Get the global StoryAggregator instance.

    Returns:
        StoryAggregator if consumer is running, None otherwise
    """
    return _aggregator

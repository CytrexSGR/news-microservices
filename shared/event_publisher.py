"""
Event Publisher Library for News Microservices
Provides async RabbitMQ publishing with connection pooling, retry logic, and validation
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
from aio_pika.pool import Pool

logger = logging.getLogger(__name__)


class EventPublisher:
    """Async event publisher for RabbitMQ with connection pooling and retry logic"""

    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str = "news.events",
        service_name: Optional[str] = None,
        max_connections: int = 5,
        max_channels: int = 10,
    ):
        """
        Initialize event publisher

        Args:
            rabbitmq_url: RabbitMQ connection URL (amqp://...)
            exchange_name: Name of the exchange to publish to
            service_name: Name of the service publishing events
            max_connections: Maximum number of connections in pool
            max_channels: Maximum number of channels per connection
        """
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.service_name = service_name or "unknown-service"
        self.max_connections = max_connections
        self.max_channels = max_channels

        self._connection_pool: Optional[Pool] = None
        self._channel_pool: Optional[Pool] = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._is_initialized = False

    async def initialize(self):
        """Initialize connection and channel pools"""
        if self._is_initialized:
            return

        logger.info(f"Initializing event publisher for {self.service_name}")

        # Create connection pool
        async def get_connection():
            return await aio_pika.connect_robust(self.rabbitmq_url)

        self._connection_pool = Pool(get_connection, max_size=self.max_connections)

        # Create channel pool
        async def get_channel() -> aio_pika.Channel:
            async with self._connection_pool.acquire() as connection:
                return await connection.channel()

        self._channel_pool = Pool(get_channel, max_size=self.max_channels)

        # Declare exchange
        async with self._channel_pool.acquire() as channel:
            self._exchange = await channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True,
                auto_delete=False,
            )

        self._is_initialized = True
        logger.info(f"Event publisher initialized for {self.service_name}")

    async def close(self):
        """Close connection and channel pools"""
        if not self._is_initialized:
            return

        logger.info(f"Closing event publisher for {self.service_name}")

        if self._channel_pool:
            await self._channel_pool.close()

        if self._connection_pool:
            await self._connection_pool.close()

        self._is_initialized = False
        logger.info(f"Event publisher closed for {self.service_name}")

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        routing_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> bool:
        """
        Publish an event to RabbitMQ

        Args:
            event_type: Type of event (e.g., 'article.created')
            data: Event data payload
            routing_key: Routing key (defaults to event_type)
            correlation_id: Correlation ID for request tracing
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            True if published successfully, False otherwise
        """
        if not self._is_initialized:
            await self.initialize()

        routing_key = routing_key or event_type

        # Build event message
        event = {
            "event_type": event_type,
            "event_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_service": self.service_name,
            "correlation_id": correlation_id,
            "data": data,
        }

        # Validate event structure
        if not self._validate_event(event):
            logger.error(f"Invalid event structure for {event_type}")
            return False

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                await self._publish_message(event, routing_key)
                logger.info(
                    f"Published event {event_type} with ID {event['event_id']} "
                    f"(routing_key={routing_key})"
                )
                return True

            except Exception as e:
                logger.warning(
                    f"Failed to publish event {event_type} (attempt {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = retry_delay * (2**attempt)
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to publish event {event_type} after {max_retries} attempts"
                    )
                    return False

        return False

    async def _publish_message(self, event: Dict[str, Any], routing_key: str):
        """Internal method to publish message to RabbitMQ"""
        message_body = json.dumps(event).encode("utf-8")

        message = Message(
            body=message_body,
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=event["event_id"],
            timestamp=datetime.utcnow(),
            headers={
                "event_type": event["event_type"],
                "source_service": self.service_name,
            },
        )

        async with self._channel_pool.acquire() as channel:
            exchange = await channel.get_exchange(self.exchange_name)
            await exchange.publish(message, routing_key=routing_key)

    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """
        Validate event structure

        Args:
            event: Event dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "event_type",
            "event_id",
            "timestamp",
            "source_service",
            "data",
        ]

        for field in required_fields:
            if field not in event:
                logger.error(f"Missing required field: {field}")
                return False

        if not isinstance(event["data"], dict):
            logger.error("Event data must be a dictionary")
            return False

        return True

    async def publish_batch(
        self,
        events: list[tuple[str, Dict[str, Any]]],
        correlation_id: Optional[str] = None,
    ) -> int:
        """
        Publish multiple events in batch

        Args:
            events: List of (event_type, data) tuples
            correlation_id: Correlation ID for request tracing

        Returns:
            Number of successfully published events
        """
        if not self._is_initialized:
            await self.initialize()

        success_count = 0

        tasks = [
            self.publish(event_type, data, correlation_id=correlation_id)
            for event_type, data in events
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if result is True:
                success_count += 1
            elif isinstance(result, Exception):
                logger.error(f"Batch publish error: {result}")

        logger.info(f"Batch published {success_count}/{len(events)} events")
        return success_count


# Singleton instance
_publisher: Optional[EventPublisher] = None


def get_event_publisher(
    rabbitmq_url: str,
    exchange_name: str = "news.events",
    service_name: Optional[str] = None,
) -> EventPublisher:
    """
    Get singleton event publisher instance

    Args:
        rabbitmq_url: RabbitMQ connection URL
        exchange_name: Exchange name
        service_name: Service name

    Returns:
        EventPublisher instance
    """
    global _publisher

    if _publisher is None:
        _publisher = EventPublisher(
            rabbitmq_url=rabbitmq_url,
            exchange_name=exchange_name,
            service_name=service_name,
        )

    return _publisher


async def publish_event(
    event_type: str,
    data: Dict[str, Any],
    rabbitmq_url: str,
    service_name: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> bool:
    """
    Helper function to publish a single event

    Args:
        event_type: Event type
        data: Event data
        rabbitmq_url: RabbitMQ connection URL
        service_name: Service name
        correlation_id: Correlation ID

    Returns:
        True if published successfully
    """
    publisher = get_event_publisher(rabbitmq_url, service_name=service_name)

    if not publisher._is_initialized:
        await publisher.initialize()

    return await publisher.publish(event_type, data, correlation_id=correlation_id)

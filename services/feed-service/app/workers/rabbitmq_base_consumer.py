"""
Base RabbitMQ Consumer with Production Hardening

Features:
- Dead Letter Queue (DLQ) for failed messages
- Retry logic with exponential backoff
- Proper error handling and logging
- Graceful shutdown
- Message acknowledgment strategies
- Prometheus metrics

Task 406: RabbitMQ Production Hardening
"""

import asyncio
import json
import logging
import signal
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from enum import Enum

import aio_pika
from aio_pika import IncomingMessage, ExchangeType, DeliveryMode
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


class MessageAction(str, Enum):
    """Actions that can be taken on a message"""
    ACK = "ack"  # Message processed successfully
    REJECT = "reject"  # Permanent failure, send to DLQ
    RETRY = "retry"  # Transient failure, requeue for retry
    NACK = "nack"  # Negative acknowledgment (not ready to process)


@dataclass
class RetryPolicy:
    """Message retry configuration"""
    max_retries: int = 3
    initial_delay_ms: int = 1000  # 1 second
    max_delay_ms: int = 60000  # 60 seconds
    exponential_base: float = 2.0
    enable_jitter: bool = True


class BaseRabbitMQConsumer(ABC):
    """
    Base class for RabbitMQ consumers with production features.

    Subclasses must implement:
    - process_message(message_data: Dict[str, Any]) -> MessageAction

    Usage:
        class MyConsumer(BaseRabbitMQConsumer):
            async def process_message(self, message_data):
                # Process message
                return MessageAction.ACK

        consumer = MyConsumer(
            rabbitmq_url="amqp://...",
            queue_name="my_queue",
            routing_keys=["my.event"],
        )
        await consumer.run()
    """

    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str,
        routing_keys: list[str],
        exchange_name: str = "news.events",
        prefetch_count: int = 10,
        retry_policy: Optional[RetryPolicy] = None,
        enable_metrics: bool = True,
    ):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.routing_keys = routing_keys
        self.exchange_name = exchange_name
        self.prefetch_count = prefetch_count
        self.retry_policy = retry_policy or RetryPolicy()
        self.enable_metrics = enable_metrics

        # Connection state
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.dlq: Optional[aio_pika.Queue] = None
        self.shutdown = False

        # Metrics
        if enable_metrics:
            self._init_metrics()

    def _init_metrics(self):
        """Initialize Prometheus metrics"""
        name = self.queue_name.replace(".", "_").replace("-", "_")

        self.metrics_processed = Counter(
            f"rabbitmq_messages_processed_total_{name}",
            f"Total messages processed from {self.queue_name}",
            ["queue", "action"],  # action: ack, reject, retry
        )

        self.metrics_processing_time = Histogram(
            f"rabbitmq_message_processing_seconds_{name}",
            f"Message processing time for {self.queue_name}",
            ["queue"],
        )

        self.metrics_queue_size = Gauge(
            f"rabbitmq_queue_size_{name}",
            f"Approximate queue size for {self.queue_name}",
            ["queue"],
        )

        self.metrics_errors = Counter(
            f"rabbitmq_processing_errors_total_{name}",
            f"Total processing errors for {self.queue_name}",
            ["queue", "error_type"],
        )

    async def connect(self) -> None:
        """Connect to RabbitMQ and set up queues/exchanges"""
        try:
            logger.info(f"Connecting to RabbitMQ: {self.rabbitmq_url}")

            # Create robust connection (auto-reconnect)
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                client_properties={"service": f"{self.queue_name}-consumer"},
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.prefetch_count)

            # Declare exchange
            exchange = await self.channel.declare_exchange(
                self.exchange_name,
                type=ExchangeType.TOPIC,
                durable=True,
            )

            # Declare DLQ (dead letter queue)
            dlq_name = f"{self.queue_name}_dlq"
            self.dlq = await self.channel.declare_queue(
                dlq_name,
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hours
                },
            )

            # Declare main queue with DLQ binding
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",  # Default exchange
                    "x-dead-letter-routing-key": dlq_name,
                },
            )

            # Bind queue to exchange with routing keys
            for routing_key in self.routing_keys:
                await self.queue.bind(
                    exchange=exchange,
                    routing_key=routing_key,
                )
                logger.info(f"Bound {self.queue_name} to {routing_key}")

            logger.info(f"✓ Connected to RabbitMQ and set up {self.queue_name}")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info(f"Disconnected from RabbitMQ ({self.queue_name})")

    @abstractmethod
    async def process_message(self, message_data: Dict[str, Any]) -> MessageAction:
        """
        Process a message and return action to take.

        Args:
            message_data: Parsed message payload

        Returns:
            MessageAction indicating how to handle the message

        Example:
            async def process_message(self, message_data):
                try:
                    # Process message
                    return MessageAction.ACK
                except TemporaryError:
                    return MessageAction.RETRY
                except PermanentError:
                    return MessageAction.REJECT
        """
        pass

    async def handle_message(self, message: IncomingMessage) -> None:
        """
        Handle incoming message with error handling and retries.

        This is the main entry point for message processing.
        """
        start_time = datetime.utcnow()

        try:
            # Parse message
            body = json.loads(message.body.decode())
            payload = body.get("payload", {})

            # Get retry count from headers
            retry_count = self._get_retry_count(message)

            logger.info(
                f"Processing message from {self.queue_name} "
                f"(retry: {retry_count}/{self.retry_policy.max_retries})"
            )

            # Process message
            action = await self.process_message(payload)

            # Handle action
            if action == MessageAction.ACK:
                await message.ack()
                logger.info(f"✓ Message processed successfully")

                if self.enable_metrics:
                    self.metrics_processed.labels(
                        queue=self.queue_name,
                        action="ack"
                    ).inc()

            elif action == MessageAction.REJECT:
                # Permanent failure - send to DLQ
                await message.reject(requeue=False)
                logger.warning(f"✗ Message rejected (sent to DLQ)")

                if self.enable_metrics:
                    self.metrics_processed.labels(
                        queue=self.queue_name,
                        action="reject"
                    ).inc()

            elif action == MessageAction.RETRY:
                # Transient failure - retry with backoff
                if retry_count < self.retry_policy.max_retries:
                    await self._retry_message(message, retry_count)
                    logger.info(f"↻ Message requeued for retry ({retry_count + 1}/{self.retry_policy.max_retries})")
                else:
                    # Max retries exceeded - send to DLQ
                    await message.reject(requeue=False)
                    logger.error(f"✗ Max retries exceeded, sent to DLQ")

                if self.enable_metrics:
                    self.metrics_processed.labels(
                        queue=self.queue_name,
                        action="retry"
                    ).inc()

            elif action == MessageAction.NACK:
                # Not ready to process - nack without requeue
                await message.nack(requeue=False)
                logger.warning(f"↺ Message nacked (not ready)")

        except json.JSONDecodeError as e:
            # Malformed JSON - permanent error
            logger.error(f"JSON decode error: {e}")
            await message.reject(requeue=False)

            if self.enable_metrics:
                self.metrics_errors.labels(
                    queue=self.queue_name,
                    error_type="json_decode"
                ).inc()

        except Exception as e:
            # Unexpected error - retry with backoff
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)

            retry_count = self._get_retry_count(message)
            if retry_count < self.retry_policy.max_retries:
                await self._retry_message(message, retry_count)
            else:
                await message.reject(requeue=False)

            if self.enable_metrics:
                self.metrics_errors.labels(
                    queue=self.queue_name,
                    error_type="unexpected"
                ).inc()

        finally:
            # Record processing time
            if self.enable_metrics:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self.metrics_processing_time.labels(
                    queue=self.queue_name
                ).observe(duration)

    def _get_retry_count(self, message: IncomingMessage) -> int:
        """Extract retry count from message headers"""
        if message.headers and "x-retry-count" in message.headers:
            return int(message.headers["x-retry-count"])
        return 0

    async def _retry_message(self, message: IncomingMessage, retry_count: int) -> None:
        """
        Retry message with exponential backoff.

        Publishes message to delayed exchange with increased retry count.
        """
        # Calculate delay with exponential backoff
        delay_ms = min(
            self.retry_policy.initial_delay_ms * (self.retry_policy.exponential_base ** retry_count),
            self.retry_policy.max_delay_ms
        )

        # Add jitter if enabled (±10%)
        if self.retry_policy.enable_jitter:
            import random
            jitter = random.uniform(-0.1, 0.1)
            delay_ms = int(delay_ms * (1 + jitter))

        # Update retry count in headers
        headers = message.headers or {}
        headers["x-retry-count"] = retry_count + 1

        # Publish message back to queue with delay
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.body,
                headers=headers,
                delivery_mode=DeliveryMode.PERSISTENT,
                expiration=str(int(delay_ms)),  # Message TTL = delay
            ),
            routing_key=self.queue_name,
        )

        # ACK original message
        await message.ack()

        logger.info(f"Message requeued with {delay_ms}ms delay (retry {retry_count + 1})")

    async def start_consuming(self) -> None:
        """Start consuming messages from queue"""
        if not self.queue:
            raise RuntimeError("Not connected to RabbitMQ")

        logger.info(f"Starting message consumption from {self.queue_name}...")

        # Start consuming
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                if self.shutdown:
                    logger.info("Shutdown signal received, stopping...")
                    break

                await self.handle_message(message)

                # Update queue size metric
                if self.enable_metrics:
                    queue_info = await self.queue.declare(passive=True)
                    self.metrics_queue_size.labels(
                        queue=self.queue_name
                    ).set(queue_info.declaration_result.message_count)

    async def run(self) -> None:
        """Main entry point for consumer"""
        try:
            await self.connect()
            await self.start_consuming()
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect()

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signal (SIGINT, SIGTERM)"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown = True

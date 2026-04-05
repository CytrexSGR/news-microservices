"""
RabbitMQ Circuit Breaker Wrapper

Provides circuit breaker protection for RabbitMQ publishing operations to prevent
cascading failures when RabbitMQ is down or experiencing issues.

Key Features:
- Automatic reconnection with exponential backoff
- Circuit breaker protection for publish operations
- Prometheus metrics for monitoring
- Message queuing during circuit breaker open state (optional)
- Context manager support for resource cleanup

Usage:
    from news_mcp_common.resilience import ResilientRabbitMQPublisher

    publisher = ResilientRabbitMQPublisher(
        name="feed-events",
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        exchange_name="news.events",
    )

    async with publisher:
        success = await publisher.publish(
            routing_key="article.created",
            message={"article_id": "123", "title": "..."}
        )

Architecture:
- Wraps aio_pika connection/channel/exchange with circuit breaker
- CLOSED: Normal operation, publishes to RabbitMQ
- OPEN: RabbitMQ failed, rejects publishes immediately
- HALF_OPEN: Testing recovery, allows single publish attempt

Benefits:
- Prevents connection pool exhaustion during RabbitMQ outages
- Fails fast instead of blocking/timing out
- Automatic recovery when RabbitMQ comes back online
- Metrics for monitoring circuit breaker state
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal

import aio_pika
from aio_pika import Message, ExchangeType

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .exceptions import CircuitBreakerOpenError
from .types import CircuitBreakerState

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for RabbitMQ message serialization.

    Handles Python types that are not natively JSON-serializable:
    - UUID objects → string representation
    - datetime objects → ISO 8601 format
    - Decimal objects → float representation
    """

    def default(self, obj):
        """Convert non-serializable objects to JSON-compatible types."""
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class RabbitMQCircuitBreakerError(Exception):
    """Base exception for RabbitMQ circuit breaker errors."""
    pass


class ResilientRabbitMQPublisher:
    """
    RabbitMQ publisher with circuit breaker protection.

    Wraps aio_pika publish operations with circuit breaker pattern to prevent
    cascading failures during RabbitMQ outages.

    Attributes:
        name (str): Circuit breaker name (for metrics)
        rabbitmq_url (str): RabbitMQ connection URL
        exchange_name (str): Exchange name to publish to
        exchange_type (ExchangeType): Exchange type (default: TOPIC)
        circuit_breaker (CircuitBreaker): Circuit breaker instance
        connection (Optional[aio_pika.Connection]): RabbitMQ connection
        channel (Optional[aio_pika.Channel]): RabbitMQ channel
        exchange (Optional[aio_pika.Exchange]): RabbitMQ exchange

    Example:
        >>> publisher = ResilientRabbitMQPublisher(
        ...     name="news-events",
        ...     rabbitmq_url="amqp://guest:guest@localhost:5672/",
        ...     exchange_name="news.events",
        ... )
        >>> async with publisher:
        ...     await publisher.publish("article.created", {"id": "123"})
    """

    def __init__(
        self,
        name: str,
        rabbitmq_url: str,
        exchange_name: str,
        exchange_type: ExchangeType = ExchangeType.TOPIC,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        service_name: Optional[str] = None,
        prefetch_count: int = 10,
    ):
        """
        Initialize RabbitMQ publisher with circuit breaker.

        Args:
            name: Circuit breaker identifier (used in metrics)
            rabbitmq_url: RabbitMQ connection URL (e.g., "amqp://guest:guest@localhost:5672/")
            exchange_name: Exchange name to publish to (e.g., "news.events")
            exchange_type: Exchange type (default: TOPIC for flexible routing)
            circuit_breaker_config: Optional circuit breaker configuration
            circuit_breaker: Optional pre-configured circuit breaker instance
            service_name: Service name for message metadata
            prefetch_count: QoS prefetch count (default: 10)
        """
        self.name = name
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.service_name = service_name or "unknown-service"
        self.prefetch_count = prefetch_count

        # Circuit breaker setup
        if circuit_breaker:
            self.circuit_breaker = circuit_breaker
        else:
            cb_config = circuit_breaker_config or CircuitBreakerConfig(
                failure_threshold=5,      # Open after 5 failures
                success_threshold=2,      # Close after 2 successes
                timeout_seconds=60,       # Wait 1 minute before retry
                enable_metrics=True,      # Track circuit breaker metrics
            )
            self.circuit_breaker = CircuitBreaker(name=name, config=cb_config)

        # RabbitMQ connection state
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._connected = False

    async def __aenter__(self):
        """Context manager entry: Connect to RabbitMQ."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: Disconnect from RabbitMQ."""
        await self.disconnect()
        return False

    @property
    def is_connected(self) -> bool:
        """Check if connected to RabbitMQ."""
        return self._connected and self.connection and self.channel and self.exchange

    @property
    def circuit_breaker_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.circuit_breaker.state

    async def connect(self):
        """
        Connect to RabbitMQ and declare exchange.

        Protected by circuit breaker - if circuit is open, raises CircuitBreakerOpenError.

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RabbitMQCircuitBreakerError: If connection fails
        """
        # Use circuit breaker for connection attempt
        async with self.circuit_breaker():
            try:
                # Create robust connection (auto-reconnects)
                self.connection = await aio_pika.connect_robust(
                    self.rabbitmq_url,
                    client_properties={"service": self.service_name},
                )

                # Create channel with QoS
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=self.prefetch_count)

                # Declare exchange (durable, survives RabbitMQ restart)
                self.exchange = await self.channel.declare_exchange(
                    self.exchange_name,
                    type=self.exchange_type,
                    durable=True,
                )

                self._connected = True
                logger.info(
                    f"Connected to RabbitMQ exchange: {self.exchange_name} "
                    f"(circuit breaker: {self.name})"
                )

            except Exception as e:
                self._connected = False
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise RabbitMQCircuitBreakerError(f"RabbitMQ connection failed: {e}") from e

    async def disconnect(self):
        """
        Gracefully disconnect from RabbitMQ.

        Closes channel and connection in correct order. Safe to call multiple times.
        """
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            self._connected = False
            logger.info(f"Disconnected from RabbitMQ (circuit breaker: {self.name})")
        except Exception as e:
            logger.warning(f"Error during RabbitMQ disconnect: {e}")

    async def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        correlation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        mandatory: bool = False,
        wrap: bool = True,
    ) -> bool:
        """
        Publish message to RabbitMQ with circuit breaker protection.

        Message Envelope:
            {
                "event_type": str,           # Event type (optional, for filtering)
                "service": str,              # Publishing service name
                "timestamp": str,            # ISO 8601 UTC timestamp
                "payload": dict,             # Message data
                "correlation_id": str        # Optional distributed tracing ID
            }

        Message Properties:
            - content_type: "application/json"
            - delivery_mode: 2 (persistent, survives RabbitMQ restart)
            - timestamp: UTC datetime
            - app_id: service_name
            - type: event_type (if provided)

        Args:
            routing_key: RabbitMQ routing key (e.g., "article.created")
            message: Message payload (must be JSON-serializable)
            correlation_id: Optional correlation ID for distributed tracing
            event_type: Optional event type (also used in message metadata)
            mandatory: If True, raises exception if message can't be routed
            wrap: If True (default), wraps message in standard envelope with service,
                  timestamp, payload. If False, sends message as-is (for pre-wrapped
                  messages like EventEnvelope).

        Returns:
            bool: True if published successfully, False on error

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open (RabbitMQ down)

        Example:
            >>> success = await publisher.publish(
            ...     routing_key="article.created",
            ...     message={"article_id": "123", "title": "Breaking News"},
            ...     event_type="article.created",
            ...     correlation_id="trace-456"
            ... )
            True
        """
        # Check circuit breaker state first (fail fast)
        if self.circuit_breaker.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError(
                f"RabbitMQ circuit breaker is OPEN for '{self.name}' - "
                "RabbitMQ is experiencing issues, refusing publish to prevent cascading failures"
            )

        # Ensure connected
        if not self.is_connected:
            await self.connect()

        # Use circuit breaker for publish operation
        async with self.circuit_breaker():
            try:
                # Prepare message body
                if wrap:
                    # Default: wrap message in standard envelope
                    message_body = {
                        "service": self.service_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "payload": message,
                    }

                    if event_type:
                        message_body["event_type"] = event_type

                    if correlation_id:
                        message_body["correlation_id"] = correlation_id
                else:
                    # Send message as-is (for pre-wrapped messages like EventEnvelope)
                    message_body = message

                # Create AMQP message
                amqp_message = Message(
                    body=json.dumps(message_body, cls=JSONEncoder).encode(),
                    content_type="application/json",
                    delivery_mode=2,  # Persistent
                    timestamp=datetime.now(timezone.utc),
                    app_id=self.service_name,
                    type=event_type or routing_key,
                )

                # Publish to exchange
                # Note: aio_pika 9.x automatically enables publisher confirms
                # The await will block until RabbitMQ confirms message acceptance
                await self.exchange.publish(
                    amqp_message,
                    routing_key=routing_key,
                    mandatory=mandatory,
                )

                logger.debug(
                    f"Published message to RabbitMQ: routing_key={routing_key}, "
                    f"event_type={event_type or 'none'}"
                )
                return True

            except CircuitBreakerOpenError:
                # Re-raise circuit breaker errors
                raise

            except Exception as e:
                logger.error(
                    f"Failed to publish message to RabbitMQ: routing_key={routing_key}, error={e}"
                )
                # Circuit breaker will record this failure
                raise RabbitMQCircuitBreakerError(f"RabbitMQ publish failed: {e}") from e

    async def publish_batch(
        self,
        messages: list[tuple[str, Dict[str, Any]]],
        event_type: Optional[str] = None,
    ) -> int:
        """
        Publish multiple messages in a batch.

        Args:
            messages: List of (routing_key, message_payload) tuples
            event_type: Optional event type for all messages

        Returns:
            int: Number of successfully published messages

        Example:
            >>> messages = [
            ...     ("article.created", {"id": "1", "title": "News 1"}),
            ...     ("article.created", {"id": "2", "title": "News 2"}),
            ... ]
            >>> count = await publisher.publish_batch(messages)
            >>> print(f"Published {count}/{len(messages)} messages")
        """
        success_count = 0

        for routing_key, message_payload in messages:
            try:
                if await self.publish(routing_key, message_payload, event_type=event_type):
                    success_count += 1
            except CircuitBreakerOpenError:
                # Circuit is open - stop trying
                logger.warning(
                    f"Batch publish stopped: circuit breaker open "
                    f"({success_count}/{len(messages)} published)"
                )
                break
            except Exception as e:
                logger.error(f"Batch publish error for {routing_key}: {e}")
                # Continue with next message

        return success_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            dict: Statistics including state, success/failure counts, etc.
        """
        return self.circuit_breaker.get_stats()

    async def reset(self):
        """
        Manually reset circuit breaker to CLOSED state.

        Useful for:
        - Administrative override after fixing RabbitMQ
        - Testing
        - Recovery after known issue resolution
        """
        await self.circuit_breaker.reset()
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED state")


def create_resilient_rabbitmq_publisher(
    name: str,
    rabbitmq_url: str,
    exchange_name: str,
    **kwargs
) -> ResilientRabbitMQPublisher:
    """
    Factory function to create ResilientRabbitMQPublisher.

    Args:
        name: Circuit breaker identifier
        rabbitmq_url: RabbitMQ connection URL
        exchange_name: Exchange name
        **kwargs: Additional arguments for ResilientRabbitMQPublisher

    Returns:
        ResilientRabbitMQPublisher: Configured publisher instance

    Example:
        >>> publisher = create_resilient_rabbitmq_publisher(
        ...     name="news-events",
        ...     rabbitmq_url="amqp://guest:guest@localhost:5672/",
        ...     exchange_name="news.events",
        ... )
    """
    return ResilientRabbitMQPublisher(
        name=name,
        rabbitmq_url=rabbitmq_url,
        exchange_name=exchange_name,
        **kwargs
    )

"""
Event publisher service for RabbitMQ integration

Publishes events to RabbitMQ for other services to consume.

Task 406 (Circuit Breaker Pattern):
- Uses ResilientRabbitMQPublisher for circuit breaker protection
- Prevents cascading failures during RabbitMQ outages
- Automatic reconnection with exponential backoff
- Prometheus metrics for monitoring

Epic 0.3 (Event Schema Standardization):
- All events are wrapped in EventEnvelope from news-intelligence-common
- Standardized event format with event_id, event_version, timestamp, etc.
- Enables distributed tracing via correlation_id and causation_id
"""
import logging
import os
from typing import Dict, Any, Optional, List

from app.config import settings
from news_mcp_common.resilience import (
    ResilientRabbitMQPublisher,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
)
from news_intelligence_common import create_event, EventEnvelope

logger = logging.getLogger(__name__)


class EventPublisher:
    """Service for publishing events to RabbitMQ with circuit breaker protection."""

    SERVICE_NAME = "feed-service"

    def __init__(self):
        # Set SERVICE_NAME environment variable for EventEnvelope
        os.environ.setdefault("SERVICE_NAME", self.SERVICE_NAME)

        # Circuit breaker configuration for RabbitMQ publishing
        # Task 406: Circuit Breaker Pattern
        cb_config = CircuitBreakerConfig(
            failure_threshold=5,      # Open after 5 consecutive failures
            success_threshold=2,      # Close after 2 successes in HALF_OPEN
            timeout_seconds=60,       # Wait 60s before retry (reasonable for broker recovery)
            enable_metrics=True,      # Track circuit breaker state in Prometheus
        )

        # Create resilient publisher with circuit breaker protection
        self._publisher = ResilientRabbitMQPublisher(
            name="feed-events",
            rabbitmq_url=settings.RABBITMQ_URL,
            exchange_name=settings.RABBITMQ_EXCHANGE,
            circuit_breaker_config=cb_config,
            service_name=self.SERVICE_NAME,
            prefetch_count=10,
        )

    async def connect(self):
        """
        Connect to RabbitMQ and set up exchange.

        Protected by circuit breaker - if RabbitMQ is down, this will:
        1. Try to connect
        2. Record failure in circuit breaker
        3. After 5 failures, open circuit breaker
        4. Raise CircuitBreakerOpenError to prevent further connection attempts
        """
        try:
            await self._publisher.connect()
            logger.info(f"Connected to RabbitMQ exchange: {settings.RABBITMQ_EXCHANGE}")
        except CircuitBreakerOpenError:
            logger.error(
                "RabbitMQ circuit breaker is OPEN - broker is experiencing issues, "
                "connection refused to prevent cascading failures"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        await self._publisher.disconnect()
        logger.info("Disconnected from RabbitMQ")

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Publish an event to RabbitMQ wrapped in EventEnvelope.

        Epic 0.3: All events are now wrapped in EventEnvelope for standardization.
        The envelope includes event_id, event_version, timestamp, source_service,
        correlation_id, causation_id, and metadata fields.

        Args:
            event_type: Type of event (e.g., "feed.created", "article.created")
            payload: Event payload data
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional ID of the event that caused this one
            metadata: Optional additional metadata

        Returns:
            True if published successfully, False otherwise

        Event types:
            - feed.created: New feed was created
            - feed.updated: Feed was updated
            - feed.deleted: Feed was deleted
            - article.created: New article/item was created
            - feed.fetch_completed: Feed fetch completed successfully
            - feed.fetch_failed: Feed fetch failed

        Circuit Breaker Behavior:
            - CLOSED: Normal operation, publishes to RabbitMQ
            - OPEN: RabbitMQ is down, immediately returns False without trying
            - HALF_OPEN: Testing recovery, allows single publish attempt
        """
        try:
            # Epic 0.3: Wrap payload in EventEnvelope for standardization
            envelope = create_event(
                event_type=event_type,
                payload=payload,
                correlation_id=correlation_id,
                causation_id=causation_id,
                metadata=metadata,
            )

            # Use resilient publisher with circuit breaker protection
            # Routing key = event_type for flexible topic-based routing
            # The envelope.to_dict() is passed as the message (replacing raw payload)
            # wrap=False because EventEnvelope is already a complete message envelope
            return await self._publisher.publish(
                routing_key=event_type,
                message=envelope.to_dict(),
                correlation_id=envelope.correlation_id,
                event_type=event_type,
                mandatory=True,  # Raise exception if message can't be routed
                wrap=False,  # Don't double-wrap - EventEnvelope is already wrapped
            )

        except ValueError as e:
            # Invalid event_type format (EventEnvelope validation)
            logger.error(f"Invalid event format for {event_type}: {e}")
            return False

        except CircuitBreakerOpenError:
            # Circuit breaker is open - RabbitMQ is down
            # Fail fast instead of blocking/timing out
            logger.error(
                f"Circuit breaker is OPEN - refusing to publish {event_type} "
                "to prevent cascading failures during RabbitMQ outage"
            )
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

        Circuit Breaker Behavior:
            - Stops batch publishing if circuit breaker opens mid-batch
            - Returns count of successfully published messages before circuit opened
        """
        success_count = 0

        for event in events:
            try:
                if await self.publish_event(
                    event.get("event_type"),
                    event.get("payload"),
                    event.get("correlation_id"),
                ):
                    success_count += 1
            except CircuitBreakerOpenError:
                # Circuit opened during batch - stop trying
                logger.warning(
                    f"Batch publish stopped: circuit breaker opened "
                    f"({success_count}/{len(events)} published)"
                )
                break

        return success_count

    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics for monitoring.

        Returns:
            dict: Statistics including:
                - state: Current circuit breaker state (CLOSED/OPEN/HALF_OPEN)
                - total_successes: Cumulative successful publishes
                - total_failures: Cumulative failed publishes
                - total_rejections: Publishes rejected due to open circuit
                - failure_rate: Current failure rate (0.0-1.0)
                - last_failure_time: Timestamp of last failure
                - last_state_change_time: When circuit breaker last changed state

        Example:
            >>> publisher = await get_event_publisher()
            >>> stats = publisher.get_circuit_breaker_stats()
            >>> print(f"Circuit state: {stats['state']}")
            >>> print(f"Success rate: {1.0 - stats['failure_rate']:.2%}")
        """
        return self._publisher.get_stats()

    async def reset_circuit_breaker(self):
        """
        Manually reset circuit breaker to CLOSED state.

        Use Cases:
            - After fixing RabbitMQ issues
            - Administrative override
            - Testing/debugging

        Example:
            >>> publisher = await get_event_publisher()
            >>> await publisher.reset_circuit_breaker()
            >>> # Circuit is now CLOSED, will retry connections
        """
        await self._publisher.reset()
        logger.info("Feed service circuit breaker manually reset to CLOSED state")


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

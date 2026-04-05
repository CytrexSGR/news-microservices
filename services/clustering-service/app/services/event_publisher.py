# services/clustering-service/app/services/event_publisher.py
"""Event publisher for clustering events.

Uses news_intelligence_common for EventEnvelope and news_mcp_common for
resilient RabbitMQ publishing with circuit breaker protection.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from news_intelligence_common import create_event
from news_mcp_common.resilience import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    ResilientRabbitMQPublisher,
)

from app.config import settings

logger = logging.getLogger(__name__)


class ClusterEventPublisher:
    """
    Publisher for cluster-related events.

    Publishes events using EventEnvelope wrapper and ResilientRabbitMQPublisher
    with circuit breaker protection for fault tolerance.

    Events Published:
        - cluster.created: New cluster created from first article
        - cluster.updated: Article added to existing cluster
        - cluster.burst_detected: Breaking news detected (rapid growth)

    Example:
        >>> publisher = ClusterEventPublisher()
        >>> await publisher.connect()
        >>> await publisher.publish_cluster_created(
        ...     cluster_id="123",
        ...     title="Breaking News",
        ...     article_id="456"
        ... )
        >>> await publisher.disconnect()
    """

    SERVICE_NAME = "clustering-service"

    def __init__(self):
        """Initialize event publisher with circuit breaker configuration."""
        # Set SERVICE_NAME env for EventEnvelope
        os.environ.setdefault("SERVICE_NAME", self.SERVICE_NAME)

        # Configure circuit breaker
        cb_config = CircuitBreakerConfig(
            failure_threshold=5,      # Open after 5 failures
            success_threshold=2,      # Close after 2 successes
            timeout_seconds=60,       # Wait 1 minute before retry
            enable_metrics=True,      # Track circuit breaker metrics
        )

        self._publisher = ResilientRabbitMQPublisher(
            name="cluster-events",
            rabbitmq_url=settings.RABBITMQ_URL,
            exchange_name=settings.RABBITMQ_EXCHANGE,
            circuit_breaker_config=cb_config,
            service_name=self.SERVICE_NAME,
            prefetch_count=10,
        )

    async def connect(self):
        """
        Connect to RabbitMQ.

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RabbitMQCircuitBreakerError: If connection fails
        """
        try:
            await self._publisher.connect()
            logger.info(
                f"Connected to RabbitMQ exchange: {settings.RABBITMQ_EXCHANGE}"
            )
        except CircuitBreakerOpenError:
            logger.error("RabbitMQ circuit breaker is OPEN - cannot connect")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Disconnect from RabbitMQ gracefully."""
        await self._publisher.disconnect()
        logger.info("Disconnected from RabbitMQ")

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish event with EventEnvelope wrapper.

        Creates a standardized EventEnvelope and publishes via RabbitMQ
        with circuit breaker protection.

        Args:
            event_type: Event type (e.g., "cluster.created")
            payload: Event payload data
            correlation_id: Correlation ID for distributed tracing
            causation_id: ID of event that caused this one

        Returns:
            True if published successfully, False on error

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
        """
        try:
            # Create EventEnvelope using news_intelligence_common
            envelope = create_event(
                event_type=event_type,
                payload=payload,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

            # Publish via resilient publisher
            # wrap=False because we already have an EventEnvelope
            return await self._publisher.publish(
                routing_key=event_type,
                message=envelope.to_dict(),
                correlation_id=envelope.correlation_id,
                event_type=event_type,
                mandatory=True,
                wrap=False,
            )

        except CircuitBreakerOpenError:
            logger.error(
                f"Circuit breaker OPEN - refusing to publish {event_type}"
            )
            return False
        except ValueError as e:
            logger.error(f"Invalid event format for {event_type}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to publish {event_type}: {e}")
            return False

    async def publish_cluster_created(
        self,
        cluster_id: str,
        title: str,
        article_id: str,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish cluster.created event.

        Emitted when a new cluster is created from the first article.

        Args:
            cluster_id: UUID of the new cluster
            title: Cluster title (from first article)
            article_id: UUID of the first article
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if published successfully
        """
        return await self.publish_event(
            event_type="cluster.created",
            payload={
                "cluster_id": cluster_id,
                "title": title,
                "article_id": article_id,
                "article_count": 1,
            },
            correlation_id=correlation_id,
        )

    async def publish_cluster_updated(
        self,
        cluster_id: str,
        article_id: str,
        article_count: int,
        similarity_score: float,
        tension_score: Optional[float] = None,
        is_breaking: bool = False,
        primary_entities: Optional[List[Dict[str, Any]]] = None,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish cluster.updated event.

        Emitted when an article is added to an existing cluster.

        Args:
            cluster_id: UUID of the updated cluster
            article_id: UUID of the added article
            article_count: Total articles in cluster after update
            similarity_score: Cosine similarity score for the match
            tension_score: Tension/importance score (0-10)
            is_breaking: Whether cluster is now breaking news
            primary_entities: Top entities in the cluster
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if published successfully
        """
        return await self.publish_event(
            event_type="cluster.updated",
            payload={
                "cluster_id": cluster_id,
                "article_id": article_id,
                "article_count": article_count,
                "similarity_score": similarity_score,
                "tension_score": tension_score,
                "is_breaking": is_breaking,
                "primary_entities": primary_entities,
            },
            correlation_id=correlation_id,
        )

    async def publish_burst_detected(
        self,
        cluster_id: str,
        title: str,
        article_count: int,
        growth_rate: float,
        tension_score: float,
        top_entities: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish cluster.burst_detected event.

        Emitted when a cluster shows rapid growth indicating breaking news.
        Downstream services (notification, dashboard) can react to this.

        Args:
            cluster_id: UUID of the cluster
            title: Cluster title
            article_count: Current article count
            growth_rate: Growth rate (articles / threshold)
            tension_score: Tension/importance score (0-10)
            top_entities: Top entity names in the cluster
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if published successfully
        """
        return await self.publish_event(
            event_type="cluster.burst_detected",
            payload={
                "cluster_id": cluster_id,
                "title": title,
                "article_count": article_count,
                "growth_rate": growth_rate,
                "tension_score": tension_score,
                "detection_method": "frequency_spike",
                "top_entities": top_entities,
                "recommended_action": "immediate_alert",
            },
            correlation_id=correlation_id,
        )


# -----------------------------------------------------------------------------
# Global Instance Management
# -----------------------------------------------------------------------------

_publisher: Optional[ClusterEventPublisher] = None


async def get_event_publisher() -> ClusterEventPublisher:
    """
    Get or create global event publisher instance.

    Creates a singleton publisher and connects to RabbitMQ on first call.
    Subsequent calls return the same connected instance.

    Returns:
        Connected ClusterEventPublisher instance

    Example:
        >>> publisher = await get_event_publisher()
        >>> await publisher.publish_cluster_created(...)
    """
    global _publisher

    if _publisher is None:
        _publisher = ClusterEventPublisher()
        await _publisher.connect()

    return _publisher


async def close_event_publisher():
    """
    Close global event publisher and clean up resources.

    Safe to call multiple times. Should be called during application shutdown.

    Example:
        >>> await close_event_publisher()
    """
    global _publisher

    if _publisher:
        await _publisher.disconnect()
        _publisher = None

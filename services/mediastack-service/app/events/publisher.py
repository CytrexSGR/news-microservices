"""RabbitMQ event publisher for n8n workflow integration.

Epic 0.3 (Event Schema Standardization):
- All events are wrapped in EventEnvelope from news-intelligence-common
- Standardized event format with event_id, event_version, timestamp, etc.
- Enables distributed tracing via correlation_id and causation_id
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType

from app.core.config import settings
from news_intelligence_common import create_event, EventEnvelope

logger = logging.getLogger(__name__)

# Set SERVICE_NAME for EventEnvelope
SERVICE_NAME = "mediastack-service"
os.environ.setdefault("SERVICE_NAME", SERVICE_NAME)


class EventPublisher:
    """Publishes news events to RabbitMQ for n8n workflow consumption."""

    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._exchange_name = "news"

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            return

        try:
            self._connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                client_properties={"connection_name": settings.SERVICE_NAME}
            )
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                self._exchange_name,
                ExchangeType.TOPIC,
                durable=True
            )
            logger.info(f"Connected to RabbitMQ, exchange: {self._exchange_name}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Close RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish(
        self,
        routing_key: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> None:
        """
        Publish event to RabbitMQ wrapped in EventEnvelope.

        Epic 0.3: All events are now wrapped in EventEnvelope for standardization.

        Args:
            routing_key: Event routing key (e.g., 'news.articles_fetched')
            data: Event payload
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional ID of the event that caused this one
        """
        if not self._exchange:
            await self.connect()

        try:
            # Epic 0.3: Wrap payload in EventEnvelope for standardization
            envelope = create_event(
                event_type=routing_key,
                payload=data,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

            message_body = json.dumps(envelope.to_dict(), default=str).encode()
            message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                correlation_id=envelope.correlation_id,
                timestamp=datetime.utcnow()
            )

            await self._exchange.publish(message, routing_key=routing_key)
            logger.debug(f"Published event: {routing_key} [event_id={envelope.event_id}]")

        except ValueError as e:
            # Invalid event_type format (EventEnvelope validation)
            logger.error(f"Invalid event format for {routing_key}: {e}")
            raise

    async def publish_articles_fetched(
        self,
        articles: List[Dict[str, Any]],
        source: str = "live",
        query_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publish event when articles are fetched from MediaStack.

        This event triggers n8n workflows for:
        - URL extraction and forwarding to scraping service
        - Deduplication checks
        - Source tracking

        Args:
            articles: List of article data from MediaStack
            source: Either 'live' or 'historical'
            query_params: Original query parameters used
        """
        # Epic 0.3: Event type format: domain.event_name (no redundant event_type in payload)
        event_data = {
            "source": f"mediastack_{source}",
            "article_count": len(articles),
            "query_params": query_params or {},
            "articles": articles
        }
        await self.publish("news.articles_fetched", event_data)
        logger.info(f"Published {len(articles)} articles from {source} fetch")

    async def publish_urls_discovered(
        self,
        urls: List[Dict[str, str]],
        batch_id: Optional[str] = None
    ) -> None:
        """
        Publish event for discovered URLs to be scraped.

        Each URL includes metadata for the scraping service.

        Args:
            urls: List of dicts with 'url', 'title', 'source' keys
            batch_id: Optional batch identifier for tracking
        """
        # Epic 0.3: Event type format: domain.event_name (no redundant event_type in payload)
        event_data = {
            "batch_id": batch_id or datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "url_count": len(urls),
            "urls": urls
        }
        await self.publish("news.urls_discovered", event_data)
        logger.info(f"Published {len(urls)} URLs for scraping")


# Singleton instance
_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get singleton EventPublisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher

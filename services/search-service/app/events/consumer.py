"""
RabbitMQ event consumer for Search Service

Listens for article creation, updates, and analysis completion events
to trigger real-time indexing.
"""
import aio_pika
import json
import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)


class SearchServiceConsumer:
    """Consumer for RabbitMQ events from other microservices"""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                client_properties={"service": "search-service"}
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange for events (same as Feed Service)
            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            logger.info(f"Connected to RabbitMQ exchange: {settings.RABBITMQ_EXCHANGE}")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def start_consuming(self):
        """Start consuming events from configured routing keys"""
        if not self.channel or not self.exchange:
            await self.connect()

        # Declare queue for search indexing events
        queue = await self.channel.declare_queue(
            "search_indexing_events",
            durable=True,
            arguments={
                "x-message-ttl": 3600000,  # 1 hour TTL
                "x-max-length": 10000,  # Max 10k messages
            }
        )

        # Bind to event topics we care about
        routing_keys = [
            "article.created",      # New article from Feed Service
            "article.updated",      # Article updated in Feed Service
            "analysis.completed",   # Analysis completed from Content Analysis Service
            "feed.fetch_completed", # Feed fetch completed (batch indexing)
        ]

        for routing_key in routing_keys:
            await queue.bind(self.exchange, routing_key=routing_key)
            logger.info(f"Bound to routing key: {routing_key}")

        # Start consuming messages
        await queue.consume(self.process_message)
        logger.info("Started consuming RabbitMQ events for search indexing")

    async def process_message(self, message: aio_pika.IncomingMessage):
        """
        Process incoming RabbitMQ message

        Expected message format:
        {
            "event_type": "article.created",
            "service": "feed-service",
            "timestamp": "2025-10-12T19:00:00Z",
            "payload": {
                "item_id": 123,
                "feed_id": 456,
                ...
            }
        }
        """
        async with message.process():
            try:
                payload = json.loads(message.body.decode())
                event_type = payload.get("event_type")
                event_payload = payload.get("payload", {})
                service = payload.get("service", "unknown")

                logger.info(f"Processing event: {event_type} from {service}")

                # Route to appropriate handler
                if event_type == "article.created":
                    await self.handle_article_created(event_payload)
                elif event_type == "article.updated":
                    await self.handle_article_updated(event_payload)
                elif event_type == "analysis.completed":
                    await self.handle_analysis_completed(event_payload)
                elif event_type == "feed.fetch_completed":
                    await self.handle_feed_fetch_completed(event_payload)
                else:
                    logger.debug(f"Ignoring event type: {event_type}")

            except json.JSONDecodeError:
                logger.error("Invalid JSON in RabbitMQ message")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)

    async def handle_article_created(self, payload: dict):
        """
        Handle article.created event by indexing the article

        Payload format:
        {
            "item_id": 123,
            "feed_id": 456
        }
        """
        item_id = payload.get("item_id")
        feed_id = payload.get("feed_id")

        if not item_id:
            logger.warning("article.created event missing item_id")
            return

        logger.info(f"Indexing new article {item_id} from feed {feed_id}")

        try:
            # Fetch article details from Feed Service
            article_data = await self._fetch_article_from_feed_service(item_id, feed_id)

            if not article_data:
                logger.warning(f"Could not fetch article {item_id} from Feed Service")
                return

            # Index the article
            async with AsyncSessionLocal() as db:
                indexing_service = IndexingService(db)
                await indexing_service.index_article(article_data)
                await db.commit()

            logger.info(f"Successfully indexed article {item_id}")

        except Exception as e:
            logger.error(f"Error indexing article {item_id}: {e}", exc_info=True)

    async def handle_article_updated(self, payload: dict):
        """
        Handle article.updated event by re-indexing the article

        Payload format:
        {
            "item_id": 123,
            "feed_id": 456,
            "updated_fields": ["title", "content"]
        }
        """
        item_id = payload.get("item_id")
        feed_id = payload.get("feed_id")

        if not item_id:
            logger.warning("article.updated event missing item_id")
            return

        logger.info(f"Re-indexing updated article {item_id}")

        try:
            # Fetch updated article details
            article_data = await self._fetch_article_from_feed_service(item_id, feed_id)

            if not article_data:
                logger.warning(f"Could not fetch article {item_id} from Feed Service")
                return

            # Re-index the article
            async with AsyncSessionLocal() as db:
                indexing_service = IndexingService(db)
                await indexing_service.index_article(article_data)
                await db.commit()

            logger.info(f"Successfully re-indexed article {item_id}")

        except Exception as e:
            logger.error(f"Error re-indexing article {item_id}: {e}", exc_info=True)

    async def handle_analysis_completed(self, payload: dict):
        """
        Handle analysis.completed event by updating article index with analysis data

        Payload format:
        {
            "article_id": 123,
            "sentiment": "positive",
            "entities": [...]
        }
        """
        article_id = payload.get("article_id")

        if not article_id:
            logger.warning("analysis.completed event missing article_id")
            return

        logger.info(f"Updating article {article_id} with analysis data")

        try:
            # Re-index to pick up new analysis data
            # The IndexingService will fetch the latest analysis
            article_data = await self._fetch_article_from_feed_service(article_id)

            if article_data:
                async with AsyncSessionLocal() as db:
                    indexing_service = IndexingService(db)
                    await indexing_service.index_article(article_data)
                    await db.commit()

                logger.info(f"Successfully updated article {article_id} with analysis")

        except Exception as e:
            logger.error(f"Error updating article {article_id} with analysis: {e}", exc_info=True)

    async def handle_feed_fetch_completed(self, payload: dict):
        """
        Handle feed.fetch_completed event for batch indexing

        Payload format:
        {
            "feed_id": 456,
            "items_found": 10,
            "items_new": 5,
            "item_ids": [123, 124, 125, 126, 127]
        }
        """
        feed_id = payload.get("feed_id")
        item_ids = payload.get("item_ids", [])
        items_new = payload.get("items_new", 0)

        logger.info(f"Feed {feed_id} fetch completed with {items_new} new articles")

        # Individual articles will be indexed via article.created events
        # This is just for logging/metrics
        if items_new > 0:
            logger.info(f"Expecting {items_new} article.created events for feed {feed_id}")

    async def _fetch_article_from_feed_service(
        self,
        item_id: int,
        feed_id: Optional[int] = None
    ) -> Optional[dict]:
        """
        Fetch article details from Feed Service

        Args:
            item_id: The feed item ID
            feed_id: The feed ID (optional, ignored - kept for backward compatibility)

        Returns:
            Article data dictionary or None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use correct Feed Service endpoint: /api/v1/feeds/items/{item_id}
                # This endpoint exists at feeds.py:811 and does not require feed_id
                url = f"{settings.FEED_SERVICE_URL}/api/v1/feeds/items/{item_id}"

                response = await client.get(url)
                response.raise_for_status()
                item_data = response.json()

                logger.debug(f"Successfully fetched article {item_id} from Feed Service")
                return item_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching article {item_id} from Feed Service: "
                f"{e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching article {item_id} from Feed Service: {e}")
            return None

    async def close(self):
        """Close RabbitMQ connection"""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("RabbitMQ connection closed")


# Singleton instance
_consumer_instance: Optional[SearchServiceConsumer] = None


def get_consumer() -> SearchServiceConsumer:
    """Get or create global consumer instance"""
    global _consumer_instance

    if _consumer_instance is None:
        _consumer_instance = SearchServiceConsumer()

    return _consumer_instance


async def close_consumer():
    """Close global consumer"""
    global _consumer_instance

    if _consumer_instance:
        await _consumer_instance.close()
        _consumer_instance = None

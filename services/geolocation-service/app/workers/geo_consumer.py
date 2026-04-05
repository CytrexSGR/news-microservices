"""
Geo Consumer Worker for Geolocation Service

Consumes analysis.v3.completed events from RabbitMQ, extracts LOCATION entities,
resolves them to ISO country codes, and creates article_locations mappings.

Event Flow:
1. content-analysis-v3 publishes analysis.v3.completed
2. This worker consumes the event
3. Extracts LOCATION entities from tier1.entities
4. Resolves locations to ISO codes via entity-canonicalization-service
5. Creates article_locations mappings in PostGIS
6. Updates country_stats
7. Broadcasts to WebSocket clients (if connected)
"""
import asyncio
import json
import logging
import signal
import sys
from typing import Dict, Any, Optional
from uuid import UUID

import aio_pika
from aio_pika import IncomingMessage, ExchangeType
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.core.config import settings
from app.services.article_locator import process_article_locations
from app.services.stats_aggregator import update_country_stats, get_country_centroid
from app.services.geo_event_publisher import publish_article_located

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GeoConsumer:
    """Consumes analysis events and processes location data."""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.shutdown = False

    async def connect(self) -> None:
        """Connect to RabbitMQ and set up queue."""
        try:
            rabbitmq_url = (
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
                f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            )
            logger.info(f"Connecting to RabbitMQ: {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")

            # Create robust connection (auto-reconnect)
            self.connection = await aio_pika.connect_robust(
                rabbitmq_url,
                client_properties={"service": "geolocation-service"},
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange (should already exist)
            exchange = await self.channel.declare_exchange(
                "news.events",
                type=ExchangeType.TOPIC,
                durable=True,
            )

            # Declare DLQ for failed messages
            await self.channel.declare_queue(
                "geo_article_queue_dlq",
                durable=True,
                arguments={"x-message-ttl": 86400000},  # 24 hours
            )

            # Declare main queue
            self.queue = await self.channel.declare_queue(
                "geo.article.process",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": "geo_article_queue_dlq",
                },
            )

            # Bind to analysis.v3.completed events
            await self.queue.bind(
                exchange=exchange,
                routing_key="analysis.v3.completed",
            )

            logger.info("Connected to RabbitMQ and bound to analysis.v3.completed")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("Disconnected from RabbitMQ")

    async def handle_message(self, message: IncomingMessage) -> None:
        """
        Handle incoming analysis.v3.completed events.

        Expected message format:
        {
            "event_type": "analysis.v3.completed",
            "payload": {
                "article_id": "uuid",
                "success": true,
                "tier1": {
                    "entities": [
                        {"type": "LOCATION", "name": "Ukraine", "confidence": 0.95},
                        {"type": "PERSON", "name": "...", ...}
                    ]
                },
                ...
            }
        }
        """
        try:
            # Parse message
            body = json.loads(message.body.decode())
            payload = body.get("payload", {})

            article_id_str = payload.get("article_id")
            success = payload.get("success", False)

            if not article_id_str:
                logger.warning("Message missing article_id, rejecting")
                await message.reject(requeue=False)
                return

            # Validate UUID
            try:
                article_id = UUID(article_id_str)
            except ValueError:
                logger.warning(f"Invalid UUID format: {article_id_str}, rejecting")
                await message.reject(requeue=False)
                return

            # Skip failed analyses
            if not success:
                logger.debug(f"Skipping failed analysis for {article_id}")
                await message.ack()
                return

            # Extract entities from tier1
            tier1 = payload.get("tier1", {})
            entities = tier1.get("entities", [])

            if not entities:
                logger.debug(f"No entities in analysis for {article_id}")
                await message.ack()
                return

            logger.info(f"Processing article {article_id} with {len(entities)} entities")

            # Process locations - commit first, then update stats separately
            async with AsyncSessionLocal() as db:
                mapped_countries = await process_article_locations(db, article_id, entities)

                if mapped_countries:
                    # Commit location mappings first (critical data)
                    await db.commit()
                    logger.info(f"Article {article_id} mapped to {len(mapped_countries)} countries: {mapped_countries}")

            # Update stats in separate session (non-critical, can fail gracefully)
            if mapped_countries:
                try:
                    async with AsyncSessionLocal() as stats_db:
                        for iso_code in mapped_countries:
                            await update_country_stats(stats_db, iso_code)
                        await stats_db.commit()
                except Exception as stats_error:
                    logger.warning(f"Stats update failed (non-fatal): {stats_error}")

                # Publish to RabbitMQ for geospatial-service
                try:
                    async with AsyncSessionLocal() as pub_db:
                        await publish_article_located(
                            self.channel, pub_db, article_id, mapped_countries
                        )
                except Exception as pub_error:
                    logger.warning(f"Publish to geospatial failed (non-fatal): {pub_error}")

            await message.ack()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            await message.reject(requeue=False)
        except Exception as e:
            logger.error(f"Failed to handle message: {e}", exc_info=True)
            await message.reject(requeue=True)  # Retry transient errors

    async def start_consuming(self) -> None:
        """Start consuming messages from queue."""
        if not self.queue:
            raise RuntimeError("Not connected to RabbitMQ")

        logger.info("Starting message consumption...")

        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                if self.shutdown:
                    logger.info("Shutdown signal received, stopping...")
                    break
                await self.handle_message(message)

    async def run(self) -> None:
        """Main entry point for worker."""
        try:
            await self.connect()
            await self.start_consuming()
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect()

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signal."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown = True


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Geo Consumer Worker")
    logger.info("=" * 60)
    logger.info(f"Service: geolocation-service")
    logger.info(f"Queue: geo.article.process")
    logger.info(f"Routing Key: analysis.v3.completed")
    logger.info("=" * 60)

    consumer = GeoConsumer()

    # Register shutdown handlers
    signal.signal(signal.SIGINT, consumer.handle_shutdown)
    signal.signal(signal.SIGTERM, consumer.handle_shutdown)

    try:
        await consumer.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

"""
Article Scraped Event Consumer

Consumes 'article.scraped' events from RabbitMQ (published by scraping-service)
and stores article data in the database.

Event Flow:
1. scraping-service scrapes an article and publishes article.scraped event
2. This consumer receives the event
3. Extracts article data from event payload
4. Stores article in feed_items table
5. ACKs message after processing

Message Format:
{
  "event_type": "article.scraped",
  "service": "scraping-service",
  "timestamp": "2025-11-24T10:00:00.000Z",
  "payload": {
    "article_id": "uuid",  # Optional, will be generated if missing
    "url": "https://example.com/article",
    "title": "Article Title",
    "content": "Article content...",
    "author": "Author Name",
    "published_date": "2025-11-24T09:00:00.000Z",
    "feed_id": "uuid",  # Feed this article belongs to
    "source_name": "Example News",
    "metadata": {...}  # Additional metadata
  }
}
"""
import asyncio
import json
import logging
import signal
import sys
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage, ExchangeType
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DataError, IntegrityError

from app.db import AsyncSessionLocal
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ArticleScrapedConsumer:
    """
    Consumes article.scraped events and stores articles in database.

    Workflow:
    1. Receive article.scraped event from RabbitMQ
    2. Validate article data
    3. Store article in feed_items table
    4. ACK message on success
    """

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.shutdown = False

    async def connect(self) -> None:
        """Connect to RabbitMQ and set up queue."""
        try:
            logger.info(f"Connecting to RabbitMQ: {settings.RABBITMQ_URL}")

            # Create robust connection (auto-reconnect)
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                client_properties={"service": "feed-service-article-consumer"},
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)  # Process 10 messages concurrently

            # Declare exchange (should already exist)
            exchange = await self.channel.declare_exchange(
                "news.events",
                type=ExchangeType.TOPIC,
                durable=True,
            )

            # Declare DLQ (dead letter queue) for failed messages
            dlq = await self.channel.declare_queue(
                "article_scraped_queue_dlq",
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hours
                },
            )

            # Declare main queue with DLQ binding
            self.queue = await self.channel.declare_queue(
                "article_scraped_queue",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",  # Default exchange
                    "x-dead-letter-routing-key": "article_scraped_queue_dlq",
                },
            )

            # Bind queue to exchange with routing key
            await self.queue.bind(
                exchange=exchange,
                routing_key="article.scraped",
            )

            logger.info("✓ Connected to RabbitMQ and bound to article.scraped events")

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
        Handle incoming article.scraped events.

        Validates article data and stores in database.
        """
        try:
            # Parse message
            body = json.loads(message.body.decode())
            payload = body.get("payload", {})

            # Extract article data
            article_id = payload.get("article_id")
            url = payload.get("url")
            title = payload.get("title")
            content = payload.get("content")
            feed_id = payload.get("feed_id")

            # Validate required fields
            if not url or not title:
                logger.error(f"Invalid message: missing url or title")
                await message.reject(requeue=False)  # Send to DLQ
                return

            # Generate article_id if not provided
            if not article_id:
                article_id = str(uuid4())
                logger.info(f"Generated article_id: {article_id}")

            # Validate UUIDs
            try:
                UUID(article_id)
                if feed_id:
                    UUID(feed_id)
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid UUID format: {e}. Rejecting to DLQ."
                )
                await message.reject(requeue=False)
                return

            logger.info(
                f"Received article.scraped: {article_id} - {title[:50]}..."
            )

            # Store article in database
            async with AsyncSessionLocal() as db:
                await self._store_article(db, payload, article_id)
                await db.commit()

            logger.info(f"✓ Stored article {article_id}")

            # ACK message
            await message.ack()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            await message.reject(requeue=False)  # Malformed JSON -> DLQ
        except IntegrityError as e:
            # Duplicate article (URL constraint violation)
            logger.warning(f"Duplicate article, skipping: {e}")
            await message.ack()  # ACK to avoid reprocessing
        except DataError as e:
            # Database data errors are permanent
            logger.error(f"Database data error (permanent): {e}")
            await message.reject(requeue=False)  # Don't retry, send to DLQ
        except Exception as e:
            logger.error(f"Failed to handle message: {e}", exc_info=True)
            # Reject with requeue for transient errors
            await message.reject(requeue=True)

    async def _store_article(
        self,
        db: AsyncSession,
        payload: Dict[str, Any],
        article_id: str,
    ) -> None:
        """
        Store article in feed_items table.

        Uses INSERT with ON CONFLICT DO UPDATE to handle duplicates (idempotent).
        """
        # Extract fields from payload
        url = payload.get("url")
        title = payload.get("title")
        content = payload.get("content", "")
        author = payload.get("author")
        published_date = payload.get("published_date")
        feed_id = payload.get("feed_id")
        source_name = payload.get("source_name")
        metadata = payload.get("metadata", {})

        # Parse published_date if string
        if isinstance(published_date, str):
            try:
                published_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                published_date = None

        # UPSERT query (idempotent - safe for duplicate messages)
        query = text("""
            INSERT INTO feed_items (
                id,
                feed_id,
                title,
                url,
                content,
                author,
                published_date,
                source_name,
                metadata,
                created_at,
                updated_at
            ) VALUES (
                :id,
                :feed_id,
                :title,
                :url,
                :content,
                :author,
                :published_date,
                :source_name,
                CAST(:metadata AS jsonb),
                NOW(),
                NOW()
            )
            ON CONFLICT (url)
            DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                author = EXCLUDED.author,
                published_date = EXCLUDED.published_date,
                source_name = EXCLUDED.source_name,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
        """)

        await db.execute(query, {
            "id": article_id,
            "feed_id": feed_id,
            "title": title,
            "url": url,
            "content": content,
            "author": author,
            "published_date": published_date,
            "source_name": source_name,
            "metadata": json.dumps(metadata) if metadata else None,
        })

    async def start_consuming(self) -> None:
        """Start consuming messages from queue."""
        if not self.queue:
            raise RuntimeError("Not connected to RabbitMQ")

        logger.info("Starting message consumption...")

        # Start consuming
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
        """Handle shutdown signal (SIGINT, SIGTERM)."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown = True


async def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Article Scraped Event Consumer")
    logger.info("=" * 80)
    logger.info("Service: feed-service")
    logger.info("Purpose: Store scraped articles in database")
    logger.info("Queue: article_scraped_queue")
    logger.info("Routing Keys:")
    logger.info("  - article.scraped")
    logger.info("=" * 80)

    consumer = ArticleScrapedConsumer()

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

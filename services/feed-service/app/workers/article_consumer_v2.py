"""
Article Scraped Event Consumer V2 - Production Ready

Improvements from V1 (Task 406):
- Uses BaseRabbitMQConsumer with DLQ and retry logic
- Proper error handling with message actions
- Exponential backoff for transient failures
- Prometheus metrics
- Idempotent message processing

Consumes 'article.scraped' events from RabbitMQ and stores articles in database.
"""

import logging
import sys
from typing import Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError

from app.db import AsyncSessionLocal
from app.config import settings
from app.workers.rabbitmq_base_consumer import (
    BaseRabbitMQConsumer,
    MessageAction,
    RetryPolicy,
)

logger = logging.getLogger(__name__)


class ArticleScrapedConsumer(BaseRabbitMQConsumer):
    """
    Consumes article.scraped events and stores articles in database.

    Message Flow:
    1. Receive article.scraped event
    2. Validate article data
    3. Store in feed_items table (idempotent UPSERT)
    4. Return ACK (success) or REJECT (permanent error) or RETRY (transient error)
    """

    def __init__(self):
        super().__init__(
            rabbitmq_url=settings.RABBITMQ_URL,
            queue_name="article_scraped_queue",
            routing_keys=["article.scraped"],
            exchange_name=settings.RABBITMQ_EXCHANGE,
            prefetch_count=10,
            retry_policy=RetryPolicy(
                max_retries=3,
                initial_delay_ms=1000,
                max_delay_ms=30000,
                exponential_base=2.0,
                enable_jitter=True,
            ),
            enable_metrics=True,
        )

    async def process_message(self, message_data: Dict[str, Any]) -> MessageAction:
        """
        Process article.scraped event and store in database.

        Returns:
            MessageAction.ACK: Article stored successfully
            MessageAction.REJECT: Permanent error (invalid data)
            MessageAction.RETRY: Transient error (database unavailable)
        """
        # Extract article data
        article_id = message_data.get("article_id")
        url = message_data.get("url")
        title = message_data.get("title")
        content = message_data.get("content")
        feed_id = message_data.get("feed_id")

        # Validate required fields
        if not url or not title:
            logger.error(f"Invalid message: missing url or title")
            return MessageAction.REJECT  # Permanent error

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
            logger.warning(f"Invalid UUID format: {e}")
            return MessageAction.REJECT  # Permanent error

        logger.info(f"Processing article.scraped: {article_id} - {title[:50]}...")

        # Store article in database
        try:
            async with AsyncSessionLocal() as db:
                await self._store_article(db, message_data, article_id)
                await db.commit()

            logger.info(f"✓ Stored article {article_id}")
            return MessageAction.ACK

        except IntegrityError as e:
            # Duplicate article (URL constraint violation)
            # This is expected due to idempotent processing - ACK to avoid reprocessing
            logger.info(f"Duplicate article (idempotent), skipping: {article_id}")
            return MessageAction.ACK

        except DataError as e:
            # Database data errors are permanent
            logger.error(f"Database data error (permanent): {e}")
            return MessageAction.REJECT

        except Exception as e:
            # Transient errors (database connection, etc.) - retry
            logger.error(f"Transient error storing article: {e}", exc_info=True)
            return MessageAction.RETRY

    async def _store_article(
        self,
        db,
        payload: Dict[str, Any],
        article_id: str,
    ) -> None:
        """
        Store article in feed_items table (idempotent UPSERT).

        Uses INSERT ... ON CONFLICT DO UPDATE for idempotency.
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

        import json
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


async def main():
    """Main entry point"""
    import signal

    logger.info("=" * 80)
    logger.info("Article Scraped Event Consumer V2 (Production Ready)")
    logger.info("=" * 80)
    logger.info("Service: feed-service")
    logger.info("Purpose: Store scraped articles in database")
    logger.info("Queue: article_scraped_queue")
    logger.info("Routing Keys: article.scraped")
    logger.info("Features:")
    logger.info("  - Dead Letter Queue (DLQ)")
    logger.info("  - Retry with exponential backoff")
    logger.info("  - Prometheus metrics")
    logger.info("  - Idempotent processing")
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

    logger.info("Consumer shutdown complete")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

#!/usr/bin/env python3
"""
Republish article.created events for orphaned articles (created but not analyzed).

This script identifies articles that were created during system downtime
and republishes their events to trigger v2 analysis.

Usage:
    # Inside feed-service container:
    python3 /app/scripts/republish_orphaned_articles.py

    # From host (copy to container first):
    docker cp scripts/republish_orphaned_articles.py news-feed-service:/tmp/
    docker exec -i news-feed-service python3 /tmp/republish_orphaned_articles.py

Safety:
    - Queries database to find articles without analysis
    - Asks for confirmation before publishing events
    - Safe to run multiple times (idempotent)
    - Only publishes events, doesn't modify database
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

import asyncpg
import aio_pika
from aio_pika import Message, ExchangeType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DB_URL = "postgresql://news_user:your_db_password@postgres:5432/news_mcp"
RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"
EXCHANGE_NAME = "news.events"


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for UUID and datetime."""
    def default(self, obj):
        if hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)


async def get_orphaned_articles(pool):
    """Get articles without v2 analysis."""
    query = """
    SELECT
        fi.id as item_id,
        fi.feed_id,
        fi.title,
        fi.link,
        fi.content IS NOT NULL as has_content,
        f.enable_analysis_v2
    FROM feed_items fi
    JOIN feeds f ON fi.feed_id = f.id
    WHERE fi.id NOT IN (
        SELECT article_id
        FROM content_analysis_v2.pipeline_executions
    )
    ORDER BY fi.created_at
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        return rows


async def publish_event(channel, exchange, article):
    """Publish article.created event for one article."""

    # Build analysis_config from feed settings
    # For v2, we just need enable_analysis_v2 flag
    analysis_config = {
        "enable_analysis_v2": article["enable_analysis_v2"]
    }

    # Build message body
    message_body = {
        "event_type": "article.created",
        "service": "feed-service-replay",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "item_id": str(article["item_id"]),
            "feed_id": str(article["feed_id"]),
            "title": article["title"],
            "link": article["link"],
            "has_content": article["has_content"],
            "analysis_config": analysis_config,
        }
    }

    # Create message
    message = Message(
        body=json.dumps(message_body, cls=JSONEncoder).encode(),
        content_type="application/json",
        delivery_mode=2,  # Persistent
        timestamp=datetime.now(timezone.utc),
        app_id="feed-service-replay",
        type="article.created",
    )

    # Publish with routing key
    await exchange.publish(message, routing_key="article.created")


async def main():
    """Main execution."""

    # Connect to database
    logger.info("Connecting to database...")
    pool = await asyncpg.create_pool(DB_URL)

    # Connect to RabbitMQ
    logger.info("Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(
        RABBITMQ_URL,
        client_properties={"service": "replay-script"}
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        type=ExchangeType.TOPIC,
        durable=True
    )

    # Get orphaned articles
    logger.info("Fetching orphaned articles...")
    articles = await get_orphaned_articles(pool)
    logger.info(f"Found {len(articles)} orphaned articles")

    if not articles:
        logger.info("No orphaned articles found. Exiting.")
        return

    # Ask for confirmation
    print(f"\n⚠️  About to republish {len(articles)} article.created events")
    print("This will trigger v2 analysis for these articles.")
    response = input("Continue? (yes/no): ")

    if response.lower() != "yes":
        logger.info("Aborted by user")
        return

    # Publish events
    logger.info("Publishing events...")
    success_count = 0

    for i, article in enumerate(articles, 1):
        try:
            await publish_event(channel, exchange, article)
            success_count += 1

            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(articles)}")

        except Exception as e:
            logger.error(f"Failed to publish event for {article['item_id']}: {e}")

    logger.info(f"✅ Successfully published {success_count}/{len(articles)} events")

    # Cleanup
    await connection.close()
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())

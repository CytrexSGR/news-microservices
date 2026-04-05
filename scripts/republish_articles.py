#!/usr/bin/env python3
"""
Republish articles without analysis to RabbitMQ queue.

Usage:
    python scripts/republish_articles.py --limit 129
    python scripts/republish_articles.py --days 7  # Only last 7 days
"""

import asyncio
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import aio_pika
import json
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration (use postgres hostname in Docker network)
DATABASE_URL = "postgresql://news_user:your_db_password@postgres:5432/news_mcp"

# RabbitMQ configuration (use rabbitmq hostname in Docker network)
RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"
EXCHANGE_NAME = "news.events"
ROUTING_KEY = "article.created"


async def get_articles_without_analysis(days=None, limit=None):
    """Get feed items that don't have analysis."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    query = """
        SELECT
            fi.id,
            fi.title,
            fi.link,
            fi.published_at,
            fi.created_at,
            fi.feed_id
        FROM feed_items fi
        LEFT JOIN article_analysis aa ON fi.id = aa.article_id
        WHERE aa.id IS NULL
    """

    if days:
        query += f" AND fi.created_at > NOW() - INTERVAL '{days} days'"

    query += " ORDER BY fi.created_at DESC"

    if limit:
        query += f" LIMIT {limit}"

    result = session.execute(text(query))
    articles = [dict(row._mapping) for row in result]
    session.close()

    return articles


async def publish_article_event(channel, article):
    """Publish article.created event to RabbitMQ."""
    exchange = await channel.get_exchange(EXCHANGE_NAME)

    # Match exact ResilientRabbitMQPublisher envelope format
    # See: shared/news-mcp-common/news_mcp_common/resilience/rabbitmq_circuit_breaker.py
    message_envelope = {
        "event_type": "article.created",
        "service": "backfill-script",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": None,
        "payload": {
            # Match feed_fetcher.py article.created payload
            "item_id": str(article["id"]),
            "feed_id": str(article["feed_id"]),
            "title": article["title"],
            "link": article["link"],
            "has_content": True,  # Assume articles have content
            "analysis_config": {
                "republished": True,
                "republish_reason": "backfill_missing_analysis"
            }
        }
    }

    message = aio_pika.Message(
        body=json.dumps(message_envelope).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )

    await exchange.publish(
        message,
        routing_key=ROUTING_KEY
    )

    logger.info(f"Published: {article['title'][:60]}...")


async def main():
    parser = argparse.ArgumentParser(description="Republish articles without analysis")
    parser.add_argument("--limit", type=int, help="Maximum number of articles to republish")
    parser.add_argument("--days", type=int, help="Only republish articles from last N days")
    parser.add_argument("--dry-run", action="store_true", help="Show articles without publishing")
    args = parser.parse_args()

    # Get articles
    logger.info("Fetching articles without analysis...")
    articles = await get_articles_without_analysis(days=args.days, limit=args.limit)

    if not articles:
        logger.info("No articles found without analysis.")
        return

    logger.info(f"Found {len(articles)} articles without analysis")

    if args.dry_run:
        logger.info("\n=== DRY RUN - Articles that would be republished ===")
        for i, article in enumerate(articles, 1):
            logger.info(f"{i}. {article['title'][:60]} (ID: {article['id']})")
        return

    # Connect to RabbitMQ
    logger.info("Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()

        # Publish articles
        logger.info(f"Publishing {len(articles)} articles to queue...")
        for i, article in enumerate(articles, 1):
            await publish_article_event(channel, article)
            if i % 10 == 0:
                logger.info(f"Published {i}/{len(articles)} articles...")

        logger.info(f"\n✓ Successfully published {len(articles)} articles to {EXCHANGE_NAME}")
        logger.info(f"  Routing key: {ROUTING_KEY}")
        logger.info(f"  Articles will be processed by content-analysis-v2 workers")


if __name__ == "__main__":
    asyncio.run(main())

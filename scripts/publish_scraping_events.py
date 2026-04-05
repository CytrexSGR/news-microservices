#!/usr/bin/env python3
"""
Publish scraping events for all articles in a feed.
This triggers the scraping-service to scrape content for each article.
"""
import asyncio
import json
import sys
import aio_pika
import psycopg


async def publish_scraping_events(feed_id: str):
    """Publish article.created events for all articles in feed"""

    # Get all articles from database
    conn = await psycopg.AsyncConnection.connect(
        "postgresql://news_user:your_db_password@localhost:5432/news_mcp"
    )

    cursor = await conn.execute(
        "SELECT id, link FROM feed_items WHERE feed_id = %s",
        (feed_id,)
    )
    articles = await cursor.fetchall()

    print(f"Found {len(articles)} articles to scrape")

    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@localhost:5672/"
    )

    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "news.events",
        aio_pika.ExchangeType.TOPIC,
        durable=True
    )

    # Publish event for each article
    success_count = 0
    for article_id, url in articles:
        try:
            event = {
                "event_type": "article.created",
                "payload": {
                    "feed_id": feed_id,
                    "item_id": str(article_id),
                    "url": url,
                    "scrape_method": "auto"
                },
                "correlation_id": str(article_id)
            }

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event).encode(),
                    content_type="application/json",
                    correlation_id=str(article_id)
                ),
                routing_key="article.created"
            )

            success_count += 1
            print(f"Published event {success_count}/{len(articles)}: {article_id}")

        except Exception as e:
            print(f"Failed to publish event for {article_id}: {e}")

    await connection.close()
    await conn.close()

    print(f"\n✅ Published {success_count} scraping events")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python publish_scraping_events.py <feed_id>")
        sys.exit(1)

    feed_id = sys.argv[1]
    asyncio.run(publish_scraping_events(feed_id))

#!/usr/bin/env python3
"""
Direct RabbitMQ Event Test

Bypasses Feed Service and directly publishes an 'article.created' event
to test the Content Analysis Consumer.
"""

import asyncio
import json
from datetime import datetime, timezone
import aio_pika

RABBITMQ_URL = "amqp://admin:rabbit_secret_2024@localhost:5673/news_mcp"
EXCHANGE_NAME = "news.events"


async def publish_test_event():
    """Publish a test article.created event."""

    print("=" * 70)
    print("  RabbitMQ Event Publisher - Direct Test")
    print("=" * 70)
    print()

    # Connect to RabbitMQ
    print("📡 Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # Get exchange
    exchange = await channel.get_exchange(EXCHANGE_NAME)
    print(f"✅ Connected to exchange: {EXCHANGE_NAME}")
    print()

    # Create test event
    event_body = {
        "event_type": "article.created",
        "service": "test-script",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "item_id": 99999,  # Test ID
            "feed_id": 1,
            "title": "Test Article - Cloud-Native Event-Driven Architecture",
            "content": """
            This is a test article to verify the event-driven architecture.

            The Content Analysis Service should receive this message via RabbitMQ
            and automatically trigger comprehensive analysis including:

            1. Sentiment Analysis - Detecting emotional tone and bias
            2. Entity Extraction - Identifying people, organizations, locations
            3. Topic Classification - Categorizing content into topics
            4. Summarization - Creating short summaries
            5. Fact Extraction - Extracting key facts and claims

            This architecture enables horizontal scaling, fault tolerance, and
            loose coupling between microservices, making it perfect for
            Kubernetes deployments.
            """,
            "url": "https://example.com/test-article",
            "published_at": datetime.now(timezone.utc).isoformat()
        }
    }

    # Create message
    message = aio_pika.Message(
        body=json.dumps(event_body).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        timestamp=datetime.now(timezone.utc),
        app_id="test-script",
        type="article.created",
    )

    # Publish message
    print("📨 Publishing test event...")
    print(f"   Event Type: {event_body['event_type']}")
    print(f"   Article ID: {event_body['payload']['item_id']}")
    print(f"   Title: {event_body['payload']['title']}")
    print()

    await exchange.publish(
        message,
        routing_key="article_created"
    )

    print("✅ Event published successfully!")
    print()
    print("🔍 Next Steps:")
    print("   1. Check consumer logs:")
    print("      docker-compose logs -f content-analysis-service")
    print()
    print("   2. Look for:")
    print("      - '📨 Received message: article.created'")
    print("      - 'Processing article.created: item_id=99999'")
    print("      - Analysis completion logs")
    print()
    print("   3. Check RabbitMQ Management UI:")
    print("      http://localhost:15673/#/queues/%2Fnews_mcp/article_created_queue")
    print("      (admin / rabbit_secret_2024)")
    print()
    print("   4. View Prometheus metrics:")
    print("      http://localhost:8102/metrics")
    print()

    # Close connection
    await connection.close()


if __name__ == "__main__":
    asyncio.run(publish_test_event())

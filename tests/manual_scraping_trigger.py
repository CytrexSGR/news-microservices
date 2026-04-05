#!/usr/bin/env python3
"""
Manual scraping trigger for testing.
Publishes a scraping event directly to RabbitMQ.
"""
import pika
import json
import uuid
from datetime import datetime, timezone

def publish_scraping_event():
    # Connection parameters
    credentials = pika.PlainCredentials('news_user', 'news_password')
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        virtual_host='/',
        credentials=credentials
    )

    # Test data
    feed_id = "a447ee36-27d7-4301-af2e-f2654cbe19f4"
    item_id = "146833a4-79e9-42b2-af99-09812dbec1d2"
    url = "https://arstechnica.com/gaming/2025/09/meet-the-first-person-to-own-over-40000-paid-steam-games/"

    # Event message
    event = {
        "event_type": "feed_item_created",
        "service": "manual-test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "feed_id": feed_id,
            "item_id": item_id,
            "url": url,
            "scrape_full_content": True
        }
    }

    # Connect and publish
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare exchange (idempotent)
    channel.exchange_declare(
        exchange='news.events',
        exchange_type='topic',
        durable=True
    )

    # Publish event
    channel.basic_publish(
        exchange='news.events',
        routing_key='feed_item_created',
        body=json.dumps(event),
        properties=pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2  # persistent
        )
    )

    print(f"✅ Published scraping event:")
    print(f"   - Exchange: news.events")
    print(f"   - Routing Key: feed_item_created")
    print(f"   - Item ID: {item_id}")
    print(f"   - URL: {url}")

    connection.close()

if __name__ == "__main__":
    try:
        publish_scraping_event()
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

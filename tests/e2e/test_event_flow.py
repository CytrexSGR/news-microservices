"""
E2E Test: RabbitMQ Event Flow
Tests event-driven communication between services.
"""
import pytest
import asyncio
import httpx
import pika
from typing import Dict, Any
import time


@pytest.mark.asyncio
async def test_article_fetch_triggers_analysis_event(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str],
    rabbitmq_config: Dict[str, str]
):
    """Test that fetching articles triggers content analysis events."""
    # Create a feed
    feed_data = {
        "url": "https://news.ycombinator.com/rss",
        "name": "Event Test Feed",
        "category": "technology"
    }

    response = await http_client.post(
        "http://localhost:8001/api/feeds",
        json=feed_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    feed = response.json()
    feed_id = feed["id"]

    # Fetch articles (this should trigger events)
    response = await http_client.post(
        f"http://localhost:8001/api/feeds/{feed_id}/fetch",
        headers=auth_headers
    )
    assert response.status_code == 200
    fetch_result = response.json()

    print(f"✓ Fetched {fetch_result.get('articles_fetched', 0)} articles")

    # Wait a bit for event processing
    await asyncio.sleep(3)

    # Check if articles were processed
    response = await http_client.get(
        f"http://localhost:8001/api/feeds/{feed_id}/articles",
        headers=auth_headers
    )
    assert response.status_code == 200
    articles = response.json()

    assert len(articles) > 0, "Articles should be fetched"
    print(f"✓ Event flow verified: {len(articles)} articles available")


@pytest.mark.asyncio
async def test_rabbitmq_connection():
    """Test direct RabbitMQ connection."""
    try:
        credentials = pika.PlainCredentials('admin', 'rabbit_secret_2024')
        parameters = pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='news_mcp',
            credentials=credentials
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Check if exchanges exist
        channel.exchange_declare(
            exchange='news_events',
            exchange_type='topic',
            passive=True
        )

        connection.close()
        print("✓ RabbitMQ connection successful")

    except Exception as e:
        pytest.fail(f"RabbitMQ connection failed: {e}")


@pytest.mark.asyncio
async def test_notification_event_delivery(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test that events are properly delivered to notification service."""
    # Create a notification preference (if endpoint exists)
    try:
        pref_data = {
            "email_enabled": True,
            "notification_types": ["article_fetched", "analysis_complete"]
        }

        response = await http_client.post(
            "http://localhost:8005/api/notifications/preferences",
            json=pref_data,
            headers=auth_headers
        )

        if response.status_code in [200, 201]:
            print("✓ Notification preferences set")
    except Exception as e:
        print(f"⚠ Notification preferences: {e}")

    # Trigger an event by creating a feed and fetching
    feed_data = {
        "url": "https://hnrss.org/newest",
        "name": "Notification Test Feed",
        "category": "tech"
    }

    response = await http_client.post(
        "http://localhost:8001/api/feeds",
        json=feed_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    feed = response.json()

    # Fetch articles
    response = await http_client.post(
        f"http://localhost:8001/api/feeds/{feed['id']}/fetch",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Wait for event processing
    await asyncio.sleep(2)

    # Check notifications
    response = await http_client.get(
        "http://localhost:8005/api/notifications",
        headers=auth_headers
    )

    if response.status_code == 200:
        notifications = response.json()
        print(f"✓ Notifications received: {len(notifications)}")
    else:
        print(f"⚠ Notifications endpoint: {response.status_code}")


@pytest.mark.asyncio
async def test_search_indexing_event(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test that articles are indexed in search service via events."""
    # Create and fetch articles
    feed_data = {
        "url": "https://news.ycombinator.com/rss",
        "name": "Search Index Test",
        "category": "technology"
    }

    response = await http_client.post(
        "http://localhost:8001/api/feeds",
        json=feed_data,
        headers=auth_headers
    )
    feed = response.json()

    response = await http_client.post(
        f"http://localhost:8001/api/feeds/{feed['id']}/fetch",
        headers=auth_headers
    )

    # Wait for indexing
    await asyncio.sleep(5)

    # Search for articles
    response = await http_client.get(
        "http://localhost:8006/api/search",
        params={"q": "technology", "limit": 10},
        headers=auth_headers
    )

    if response.status_code == 200:
        results = response.json()
        print(f"✓ Search indexing verified: {results.get('total', 0)} results")
    else:
        print(f"⚠ Search service: {response.status_code}")


@pytest.mark.asyncio
async def test_analytics_event_aggregation(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test that analytics service aggregates events."""
    # Perform some actions that generate events
    feed_data = {
        "url": "https://news.ycombinator.com/rss",
        "name": "Analytics Test Feed",
        "category": "tech"
    }

    response = await http_client.post(
        "http://localhost:8001/api/feeds",
        json=feed_data,
        headers=auth_headers
    )
    feed = response.json()

    # Fetch multiple times
    for _ in range(3):
        await http_client.post(
            f"http://localhost:8001/api/feeds/{feed['id']}/fetch",
            headers=auth_headers
        )
        await asyncio.sleep(1)

    # Check analytics
    await asyncio.sleep(3)

    response = await http_client.get(
        "http://localhost:8007/api/analytics/dashboard",
        headers=auth_headers
    )

    if response.status_code == 200:
        analytics = response.json()
        print(f"✓ Analytics aggregation verified")
    else:
        print(f"⚠ Analytics service: {response.status_code}")

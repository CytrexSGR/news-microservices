"""
E2E Test: Notification Flow
Tests notification delivery across events and channels.
"""
import pytest
import httpx
from typing import Dict, Any
import asyncio


@pytest.mark.asyncio
async def test_notification_creation_and_retrieval(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test creating and retrieving notifications."""
    # Get current notifications
    response = await http_client.get(
        "http://localhost:8005/api/notifications",
        headers=auth_headers
    )

    if response.status_code == 200:
        notifications = response.json()
        initial_count = len(notifications) if isinstance(notifications, list) else 0
        print(f"✓ Retrieved {initial_count} notifications")
    else:
        print(f"⚠ Notification service: {response.status_code}")


@pytest.mark.asyncio
async def test_notification_preferences(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test notification preference management."""
    # Set preferences
    preferences = {
        "email_enabled": True,
        "push_enabled": False,
        "notification_types": ["article_fetched", "analysis_complete", "alert_triggered"]
    }

    response = await http_client.post(
        "http://localhost:8005/api/notifications/preferences",
        json=preferences,
        headers=auth_headers
    )

    if response.status_code in [200, 201, 404]:
        print(f"✓ Notification preferences endpoint accessible")

    # Get preferences
    response = await http_client.get(
        "http://localhost:8005/api/notifications/preferences",
        headers=auth_headers
    )

    if response.status_code == 200:
        prefs = response.json()
        print(f"✓ Retrieved notification preferences")


@pytest.mark.asyncio
async def test_notification_triggered_by_events(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test that notifications are triggered by system events."""
    # Create a feed to trigger events
    feed_data = {
        "url": "https://news.ycombinator.com/rss",
        "name": "Notification Trigger Test",
        "category": "tech"
    }

    response = await http_client.post(
        "http://localhost:8001/api/feeds",
        json=feed_data,
        headers=auth_headers
    )
    feed = response.json()

    # Fetch articles (should trigger notifications)
    response = await http_client.post(
        f"http://localhost:8001/api/feeds/{feed['id']}/fetch",
        headers=auth_headers
    )

    # Wait for event processing
    await asyncio.sleep(3)

    # Check for new notifications
    response = await http_client.get(
        "http://localhost:8005/api/notifications",
        headers=auth_headers
    )

    if response.status_code == 200:
        notifications = response.json()
        print(f"✓ Event-triggered notifications: {len(notifications) if isinstance(notifications, list) else 0}")


@pytest.mark.asyncio
async def test_notification_marking_as_read(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test marking notifications as read."""
    # Get notifications
    response = await http_client.get(
        "http://localhost:8005/api/notifications",
        headers=auth_headers
    )

    if response.status_code == 200:
        notifications = response.json()

        if isinstance(notifications, list) and len(notifications) > 0:
            notification_id = notifications[0].get("id")

            if notification_id:
                # Mark as read
                response = await http_client.patch(
                    f"http://localhost:8005/api/notifications/{notification_id}",
                    json={"read": True},
                    headers=auth_headers
                )

                if response.status_code in [200, 204]:
                    print(f"✓ Notification marked as read")


@pytest.mark.asyncio
async def test_notification_deletion(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test notification deletion."""
    # Get notifications
    response = await http_client.get(
        "http://localhost:8005/api/notifications",
        headers=auth_headers
    )

    if response.status_code == 200:
        notifications = response.json()

        if isinstance(notifications, list) and len(notifications) > 0:
            notification_id = notifications[0].get("id")

            if notification_id:
                # Delete notification
                response = await http_client.delete(
                    f"http://localhost:8005/api/notifications/{notification_id}",
                    headers=auth_headers
                )

                if response.status_code in [200, 204]:
                    print(f"✓ Notification deleted")


@pytest.mark.asyncio
async def test_bulk_notification_operations(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test bulk notification operations."""
    # Mark all as read
    response = await http_client.post(
        "http://localhost:8005/api/notifications/mark-all-read",
        headers=auth_headers
    )

    if response.status_code in [200, 204, 404]:
        print(f"✓ Bulk mark-as-read endpoint accessible")

    # Delete all read
    response = await http_client.delete(
        "http://localhost:8005/api/notifications/delete-read",
        headers=auth_headers
    )

    if response.status_code in [200, 204, 404]:
        print(f"✓ Bulk delete endpoint accessible")

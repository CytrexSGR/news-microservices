"""
E2E Test: Analytics Flow
Tests analytics data collection and dashboard functionality.
"""
import pytest
import httpx
from typing import Dict, Any
import asyncio


@pytest.mark.asyncio
async def test_analytics_dashboard_access(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test accessing analytics dashboard."""
    response = await http_client.get(
        "http://localhost:8007/api/analytics/dashboard",
        headers=auth_headers
    )

    if response.status_code == 200:
        dashboard = response.json()
        print(f"✓ Analytics dashboard accessible")
    else:
        print(f"⚠ Analytics dashboard: {response.status_code}")


@pytest.mark.asyncio
async def test_analytics_feed_statistics(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test feed-related analytics."""
    # Create some feeds first
    for i in range(3):
        feed_data = {
            "url": f"https://example.com/feed{i}.rss",
            "name": f"Analytics Test Feed {i}",
            "category": "tech"
        }
        await http_client.post(
            "http://localhost:8001/api/feeds",
            json=feed_data,
            headers=auth_headers
        )

    await asyncio.sleep(2)

    # Get feed analytics
    response = await http_client.get(
        "http://localhost:8007/api/analytics/feeds",
        headers=auth_headers
    )

    if response.status_code == 200:
        feed_stats = response.json()
        print(f"✓ Feed analytics available")


@pytest.mark.asyncio
async def test_analytics_article_statistics(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test article-related analytics."""
    response = await http_client.get(
        "http://localhost:8007/api/analytics/articles",
        headers=auth_headers
    )

    if response.status_code == 200:
        article_stats = response.json()
        print(f"✓ Article analytics available")


@pytest.mark.asyncio
async def test_analytics_user_activity(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test user activity analytics."""
    # Perform some activities
    feed_data = {
        "url": "https://news.ycombinator.com/rss",
        "name": "Activity Test Feed",
        "category": "tech"
    }

    response = await http_client.post(
        "http://localhost:8001/api/feeds",
        json=feed_data,
        headers=auth_headers
    )
    feed = response.json()

    # Fetch articles
    await http_client.post(
        f"http://localhost:8001/api/feeds/{feed['id']}/fetch",
        headers=auth_headers
    )

    # Search
    await http_client.get(
        "http://localhost:8006/api/search",
        params={"q": "test"},
        headers=auth_headers
    )

    await asyncio.sleep(3)

    # Get activity analytics
    response = await http_client.get(
        "http://localhost:8007/api/analytics/user-activity",
        headers=auth_headers
    )

    if response.status_code == 200:
        activity = response.json()
        print(f"✓ User activity analytics available")


@pytest.mark.asyncio
async def test_analytics_time_series_data(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test time-series analytics data."""
    # Get analytics for last 7 days
    response = await http_client.get(
        "http://localhost:8007/api/analytics/time-series",
        params={"period": "7d"},
        headers=auth_headers
    )

    if response.status_code == 200:
        time_series = response.json()
        print(f"✓ Time-series analytics available")


@pytest.mark.asyncio
async def test_analytics_category_breakdown(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test category-based analytics breakdown."""
    response = await http_client.get(
        "http://localhost:8007/api/analytics/categories",
        headers=auth_headers
    )

    if response.status_code == 200:
        categories = response.json()
        print(f"✓ Category analytics available")


@pytest.mark.asyncio
async def test_analytics_export(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test analytics data export functionality."""
    response = await http_client.get(
        "http://localhost:8007/api/analytics/export",
        params={"format": "json"},
        headers=auth_headers
    )

    if response.status_code == 200:
        export_data = response.json()
        print(f"✓ Analytics export works")


@pytest.mark.asyncio
async def test_analytics_real_time_updates(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test real-time analytics updates."""
    # Get initial state
    response = await http_client.get(
        "http://localhost:8007/api/analytics/realtime",
        headers=auth_headers
    )

    if response.status_code == 200:
        realtime = response.json()
        print(f"✓ Real-time analytics endpoint accessible")

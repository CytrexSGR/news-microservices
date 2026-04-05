"""
Test for feed_fetcher 304 Not Modified handling

This test verifies that last_fetched_at is updated even when the feed
returns 304 Not Modified (no new content).

Bug Fix: HTTP 304 was incorrectly treated as error by ResilientHttpClient
Date: 2025-11-02 (original), 2025-12-26 (updated for ResilientHttpClient)
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.feed_fetcher import FeedFetcher
from app.models import Feed, FeedItem, FetchLog, FeedHealth, FeedStatus


@pytest.mark.asyncio
async def test_304_not_modified_updates_last_fetched_at():
    """
    Test that last_fetched_at is updated even for 304 Not Modified responses.

    Scenario:
    1. Feed exists with old last_fetched_at (1 day ago)
    2. HTTP request returns 304 Not Modified
    3. Expected: last_fetched_at should be updated to current time
    4. Expected: fetch should be marked as successful (not ERROR)

    NOTE: This test patches ResilientHttpClient, which is the actual HTTP
    layer used by FeedFetcher. Previously this test patched httpx.AsyncClient
    directly, which bypassed the ResilientHttpClient layer where the 304 bug
    existed.
    """
    # Setup
    fetcher = FeedFetcher()
    feed_id = "test-feed-id-123"

    # Create mock feed with old last_fetched_at
    old_timestamp = datetime.now(timezone.utc) - timedelta(days=1)
    mock_feed = MagicMock(spec=Feed)
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed.xml"
    mock_feed.etag = "old-etag"
    mock_feed.last_modified = "Thu, 01 Nov 2025 12:00:00 GMT"
    mock_feed.last_fetched_at = old_timestamp
    mock_feed.next_fetch_at = None
    mock_feed.fetch_interval = 60
    mock_feed.status = FeedStatus.ACTIVE.value

    # Mock FetchLog
    mock_fetch_log = MagicMock(spec=FetchLog)
    mock_fetch_log.id = "log-123"

    # Mock FeedHealth
    mock_health = MagicMock(spec=FeedHealth)
    mock_health.health_score = 100
    mock_health.consecutive_failures = 0

    # Mock database session
    mock_session = AsyncMock()

    # Setup execute to return different objects based on query
    async def mock_execute(stmt):
        result = AsyncMock()
        # Check what's being queried by inspecting the statement
        stmt_str = str(stmt)
        if 'feed_health' in stmt_str.lower():
            result.scalar_one_or_none.return_value = mock_health
        else:
            result.scalar_one_or_none.return_value = mock_feed
        return result

    mock_session.execute = mock_execute
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    # Mock HTTP response for 304
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 304
    mock_response.headers = {}

    # Patch ResilientHttpClient (the actual HTTP layer used by FeedFetcher)
    with patch('app.services.feed_fetcher.ResilientHttpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Execute
        success, items_count = await fetcher._fetch_feed_internal(
            mock_session, feed_id
        )

    # Assertions
    assert success is True, "304 response should be treated as success"
    assert items_count == 0, "304 response should have 0 new items"

    # CRITICAL: Verify last_fetched_at was updated
    assert mock_feed.last_fetched_at is not None, \
        "last_fetched_at should be set"
    assert mock_feed.last_fetched_at != old_timestamp, \
        "last_fetched_at should be updated from old timestamp"

    time_diff = datetime.now(timezone.utc) - mock_feed.last_fetched_at
    assert time_diff.total_seconds() < 5, \
        f"last_fetched_at should be recent (within 5s), but was {time_diff.total_seconds()}s ago"

    # Verify feed status was NOT set to ERROR
    assert mock_feed.status != FeedStatus.ERROR.value, \
        "Feed status should NOT be ERROR for 304 response"

    print(f"✅ Test passed: last_fetched_at was updated from {old_timestamp} to {mock_feed.last_fetched_at}")


@pytest.mark.asyncio
async def test_200_ok_also_updates_last_fetched_at():
    """
    Test that last_fetched_at is updated for 200 OK responses (baseline behavior).

    This ensures the fix doesn't break existing functionality.
    """
    # Setup
    fetcher = FeedFetcher()
    feed_id = "test-feed-id-456"

    # Create mock feed
    old_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
    mock_feed = MagicMock(spec=Feed)
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed.xml"
    mock_feed.etag = None
    mock_feed.last_modified = None
    mock_feed.last_fetched_at = old_timestamp
    mock_feed.next_fetch_at = None
    mock_feed.fetch_interval = 60
    mock_feed.status = FeedStatus.ACTIVE.value
    mock_feed.name = "Test Feed"
    mock_feed.description = "Test Description"
    mock_feed.scrape_full_content = False

    # Mock FeedHealth
    mock_health = MagicMock(spec=FeedHealth)
    mock_health.health_score = 100
    mock_health.consecutive_failures = 0

    # Mock database session
    mock_session = AsyncMock()

    async def mock_execute(stmt):
        result = AsyncMock()
        stmt_str = str(stmt)
        if 'feed_health' in stmt_str.lower():
            result.scalar_one_or_none.return_value = mock_health
        elif 'feed_item' in stmt_str.lower():
            result.scalar_one_or_none.return_value = None
            result.scalars.return_value.all.return_value = []
        else:
            result.scalar_one_or_none.return_value = mock_feed
        return result

    mock_session.execute = mock_execute
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    # Mock HTTP client to return 200 OK with minimal RSS feed
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.content = b"""<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>https://example.com</link>
            <description>Test</description>
        </channel>
    </rss>
    """

    # Patch ResilientHttpClient and feedparser
    with patch('app.services.feed_fetcher.ResilientHttpClient') as mock_client_class, \
         patch('app.services.feed_fetcher.feedparser.parse') as mock_parse:

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Mock feedparser to return empty feed
        mock_parsed = MagicMock()
        mock_parsed.bozo = False
        mock_parsed.feed = {"title": "Test Feed", "description": "Test"}
        mock_parsed.entries = []
        mock_parse.return_value = mock_parsed

        # Execute
        success, items_count = await fetcher._fetch_feed_internal(
            mock_session, feed_id
        )

    # Assertions
    assert success is True
    assert items_count == 0

    # Verify last_fetched_at was updated
    assert mock_feed.last_fetched_at is not None
    assert mock_feed.last_fetched_at != old_timestamp

    time_diff = datetime.now(timezone.utc) - mock_feed.last_fetched_at
    assert time_diff.total_seconds() < 5

    print(f"✅ Test passed: last_fetched_at updated for 200 OK from {old_timestamp} to {mock_feed.last_fetched_at}")


if __name__ == "__main__":
    # Run tests manually
    import asyncio

    print("Running test_304_not_modified_updates_last_fetched_at...")
    asyncio.run(test_304_not_modified_updates_last_fetched_at())

    print("\nRunning test_200_ok_also_updates_last_fetched_at...")
    asyncio.run(test_200_ok_also_updates_last_fetched_at())

    print("\n✅ All tests passed!")

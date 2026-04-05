"""
Tests for relevance_score sorting in the Feed Items API

Epic 2.2 Task 2.2.1: Add relevance_score to sort_by enum
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import hashlib

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feed, FeedItem


def generate_content_hash(content: str) -> str:
    """Generate a content hash for testing."""
    return hashlib.sha256(content.encode()).hexdigest()


@pytest.fixture
def auth_headers():
    """Mock auth headers for API calls."""
    return {"Authorization": "Bearer test-token"}


@pytest_asyncio.fixture
async def sample_feed_with_relevance_items(db_session: AsyncSession) -> Feed:
    """
    Create a feed with items that have different relevance_score values.

    This fixture creates items with known relevance scores to verify sorting:
    - Item 1: relevance_score = 0.95 (highest)
    - Item 2: relevance_score = 0.50 (medium)
    - Item 3: relevance_score = 0.10 (lowest)
    - Item 4: relevance_score = None (should appear last with DESC, first with ASC)
    """
    # Create feed
    feed = Feed(
        id=uuid4(),
        name="Test Feed for Relevance Sorting",
        url="https://example.com/feed.xml",
        is_active=True,
    )
    db_session.add(feed)
    await db_session.flush()

    now = datetime.now(timezone.utc)

    # Create items with different relevance scores
    items = [
        FeedItem(
            id=uuid4(),
            feed_id=feed.id,
            title="High Relevance Article",
            link="https://example.com/article1",
            description="Most relevant article",
            guid="guid-1",
            published_at=now - timedelta(hours=1),
            content_hash=generate_content_hash("high-relevance-content"),
            relevance_score=0.95,
            relevance_calculated_at=now,
        ),
        FeedItem(
            id=uuid4(),
            feed_id=feed.id,
            title="Medium Relevance Article",
            link="https://example.com/article2",
            description="Medium relevant article",
            guid="guid-2",
            published_at=now - timedelta(hours=2),
            content_hash=generate_content_hash("medium-relevance-content"),
            relevance_score=0.50,
            relevance_calculated_at=now,
        ),
        FeedItem(
            id=uuid4(),
            feed_id=feed.id,
            title="Low Relevance Article",
            link="https://example.com/article3",
            description="Least relevant article",
            guid="guid-3",
            published_at=now - timedelta(hours=3),
            content_hash=generate_content_hash("low-relevance-content"),
            relevance_score=0.10,
            relevance_calculated_at=now,
        ),
        FeedItem(
            id=uuid4(),
            feed_id=feed.id,
            title="No Relevance Score Article",
            link="https://example.com/article4",
            description="Article without relevance score",
            guid="guid-4",
            published_at=now - timedelta(hours=4),
            content_hash=generate_content_hash("no-relevance-content"),
            relevance_score=None,
            relevance_calculated_at=None,
        ),
    ]

    for item in items:
        db_session.add(item)

    await db_session.commit()
    return feed


class TestRelevanceScoreSorting:
    """Tests for sorting articles by relevance_score."""

    @pytest.mark.asyncio
    async def test_sort_by_relevance_score_descending(
        self,
        client: TestClient,
        sample_feed_with_relevance_items: Feed,
    ):
        """
        Test that items can be sorted by relevance_score in descending order.

        Expected order:
        1. High (0.95)
        2. Medium (0.50)
        3. Low (0.10)
        4. None (NULL values last)
        """
        response = client.get(
            "/api/v1/feeds/items",
            params={"sort_by": "relevance_score", "order": "desc", "limit": 10},
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        items = response.json()
        assert len(items) >= 4, f"Expected at least 4 items, got {len(items)}"

        # Extract relevance scores from v3_analysis (where the score is stored in response)
        scores = []
        for item in items:
            v3_analysis = item.get("v3_analysis") or {}
            score = v3_analysis.get("relevance_score")
            scores.append(score)

        # Verify non-NULL scores are in descending order
        non_null_scores = [s for s in scores if s is not None]
        assert non_null_scores == sorted(non_null_scores, reverse=True), \
            f"Non-NULL scores should be in descending order: {non_null_scores}"

    @pytest.mark.asyncio
    async def test_sort_by_relevance_score_ascending(
        self,
        client: TestClient,
        sample_feed_with_relevance_items: Feed,
    ):
        """
        Test that items can be sorted by relevance_score in ascending order.

        Expected order:
        1. None (NULL values first with NULLSFIRST)
        2. Low (0.10)
        3. Medium (0.50)
        4. High (0.95)
        """
        response = client.get(
            "/api/v1/feeds/items",
            params={"sort_by": "relevance_score", "order": "asc", "limit": 10},
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        items = response.json()
        assert len(items) >= 4, f"Expected at least 4 items, got {len(items)}"

        # Extract relevance scores from v3_analysis
        scores = []
        for item in items:
            v3_analysis = item.get("v3_analysis") or {}
            score = v3_analysis.get("relevance_score")
            scores.append(score)

        # Verify non-NULL scores are in ascending order
        non_null_scores = [s for s in scores if s is not None]
        assert non_null_scores == sorted(non_null_scores), \
            f"Non-NULL scores should be in ascending order: {non_null_scores}"

    def test_sort_by_relevance_score_validation(
        self,
        client: TestClient,
    ):
        """
        Test that 'relevance_score' is accepted as a valid sort_by value.

        The regex validation should accept 'relevance_score' without returning 422.
        """
        response = client.get(
            "/api/v1/feeds/items",
            params={"sort_by": "relevance_score", "limit": 5},
        )

        # Should NOT return 422 (validation error)
        assert response.status_code != 422, \
            f"'relevance_score' should be a valid sort_by value. Got: {response.text}"

        # Should return 200 (success)
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"

    def test_invalid_sort_by_rejected(
        self,
        client: TestClient,
    ):
        """Test that invalid sort_by values are still rejected."""
        response = client.get(
            "/api/v1/feeds/items",
            params={"sort_by": "invalid_field", "limit": 5},
        )

        # Should return 422 (validation error)
        assert response.status_code == 422, \
            f"Invalid sort_by should return 422, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_default_sorting_still_works(
        self,
        client: TestClient,
        sample_feed_with_relevance_items: Feed,
    ):
        """Test that default sorting (created_at) still works."""
        response = client.get(
            "/api/v1/feeds/items",
            params={"limit": 10},
        )

        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1

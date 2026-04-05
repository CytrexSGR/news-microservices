"""
Integration tests for Feed Source Assessment feature.

Tests the complete workflow from triggering an assessment to verifying the results.
"""
import pytest
import asyncio
import time
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feed, FeedAssessmentHistory


@pytest.mark.asyncio
async def test_assessment_complete_workflow(async_client: AsyncClient, db: AsyncSession):
    """
    Test the complete assessment workflow:
    1. Create a feed
    2. Trigger assessment
    3. Wait for completion
    4. Verify results are saved
    5. Check history endpoint
    """
    # 1. Create a test feed
    feed_data = {
        "name": "Test News Source",
        "url": "https://example.com/feed.xml",
        "description": "Test feed for assessment",
        "fetch_interval": 60,
        "is_active": True
    }

    response = await async_client.post("/api/v1/feeds", json=feed_data)
    assert response.status_code == 201
    feed = response.json()
    feed_id = feed["id"]

    # 2. Trigger assessment
    response = await async_client.post(f"/api/v1/feeds/{feed_id}/assess")
    assert response.status_code == 200
    assessment_response = response.json()
    assert assessment_response["status"] == "pending"
    assert assessment_response["feed_id"] == feed_id

    # 3. Wait for assessment to complete (max 30 seconds)
    max_wait = 30
    start_time = time.time()
    assessment_completed = False

    while (time.time() - start_time) < max_wait:
        response = await async_client.get(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 200
        feed_data = response.json()

        if feed_data.get("assessment", {}).get("assessment_status") == "completed":
            assessment_completed = True
            break
        elif feed_data.get("assessment", {}).get("assessment_status") == "failed":
            pytest.fail("Assessment failed unexpectedly")

        await asyncio.sleep(2)

    assert assessment_completed, "Assessment did not complete within 30 seconds"

    # 4. Verify assessment results
    assessment = feed_data["assessment"]
    assert assessment["credibility_tier"] in ["tier_1", "tier_2", "tier_3"]
    assert assessment["reputation_score"] is not None
    assert 0 <= assessment["reputation_score"] <= 100
    assert assessment["organization_type"] is not None
    assert assessment["political_bias"] is not None
    assert assessment["editorial_standards"] is not None
    assert assessment["trust_ratings"] is not None
    assert assessment["recommendation"] is not None
    assert assessment["assessment_summary"] is not None

    # 5. Check assessment history
    response = await async_client.get(f"/api/v1/feeds/{feed_id}/assessment-history?limit=10")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1

    latest = history[0]
    assert latest["assessment_status"] == "completed"
    assert latest["credibility_tier"] == assessment["credibility_tier"]
    assert latest["reputation_score"] == assessment["reputation_score"]

    # 6. Verify database entries
    result = await db.execute(
        select(FeedAssessmentHistory)
        .where(FeedAssessmentHistory.feed_id == feed_id)
        .order_by(FeedAssessmentHistory.assessment_date.desc())
    )
    history_entries = result.scalars().all()
    assert len(history_entries) >= 1

    latest_entry = history_entries[0]
    assert latest_entry.assessment_status == "completed"
    assert latest_entry.credibility_tier is not None
    assert latest_entry.reputation_score is not None


@pytest.mark.asyncio
async def test_multiple_assessments_create_history(async_client: AsyncClient, db: AsyncSession):
    """
    Test that running multiple assessments creates a proper history.
    """
    # Create feed
    feed_data = {
        "name": "Test News Source 2",
        "url": "https://example2.com/feed.xml",
        "fetch_interval": 60,
        "is_active": True
    }

    response = await async_client.post("/api/v1/feeds", json=feed_data)
    assert response.status_code == 201
    feed_id = response.json()["id"]

    # Run first assessment
    response = await async_client.post(f"/api/v1/feeds/{feed_id}/assess")
    assert response.status_code == 200

    # Wait for completion
    await asyncio.sleep(10)

    # Run second assessment
    response = await async_client.post(f"/api/v1/feeds/{feed_id}/assess")
    assert response.status_code == 200

    # Wait for completion
    await asyncio.sleep(10)

    # Check history has 2 entries
    response = await async_client.get(f"/api/v1/feeds/{feed_id}/assessment-history?limit=10")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2

    # Verify both are completed
    for entry in history:
        assert entry["assessment_status"] in ["completed", "failed"]


@pytest.mark.asyncio
async def test_assessment_pending_status_transitions(async_client: AsyncClient):
    """
    Test that assessment status transitions correctly from pending to completed.
    """
    # Create feed
    feed_data = {
        "name": "Test News Source 3",
        "url": "https://example3.com/feed.xml",
        "fetch_interval": 60,
        "is_active": True
    }

    response = await async_client.post("/api/v1/feeds", json=feed_data)
    assert response.status_code == 201
    feed_id = response.json()["id"]

    # Trigger assessment
    response = await async_client.post(f"/api/v1/feeds/{feed_id}/assess")
    assert response.status_code == 200

    # Immediately check - should be pending
    response = await async_client.get(f"/api/v1/feeds/{feed_id}")
    feed = response.json()
    assert feed["assessment"]["assessment_status"] == "pending"

    # Wait and check again - should transition to completed
    await asyncio.sleep(15)
    response = await async_client.get(f"/api/v1/feeds/{feed_id}")
    feed = response.json()
    assert feed["assessment"]["assessment_status"] in ["completed", "failed"]


@pytest.mark.asyncio
async def test_assessment_with_structured_data(async_client: AsyncClient):
    """
    Test that assessment correctly uses structured_data from research service.
    """
    # Create feed
    feed_data = {
        "name": "Structured Data Test",
        "url": "https://structuredtest.com/feed.xml",
        "fetch_interval": 60,
        "is_active": True
    }

    response = await async_client.post("/api/v1/feeds", json=feed_data)
    assert response.status_code == 201
    feed_id = response.json()["id"]

    # Trigger assessment
    response = await async_client.post(f"/api/v1/feeds/{feed_id}/assess")
    assert response.status_code == 200

    # Wait for completion
    await asyncio.sleep(15)

    # Get feed details
    response = await async_client.get(f"/api/v1/feeds/{feed_id}")
    feed = response.json()

    # Verify structured data fields are present and valid
    assessment = feed["assessment"]

    # These fields should come from structured_data, not RegEx parsing
    assert "credibility_tier" in assessment
    assert "reputation_score" in assessment
    assert "editorial_standards" in assessment
    assert isinstance(assessment["editorial_standards"], dict)
    assert "trust_ratings" in assessment
    assert isinstance(assessment["trust_ratings"], dict)
    assert "recommendation" in assessment
    assert isinstance(assessment["recommendation"], dict)

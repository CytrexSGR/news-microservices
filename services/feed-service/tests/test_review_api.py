# File: services/feed-service/tests/test_review_api.py
"""
Tests for HITL Review Queue API endpoints.

Epic 2.3 Task 2.3.3: Review Queue API
Endpoints:
- GET /api/v1/review/queue - List pending items (paginated)
- GET /api/v1/review/queue/{item_id} - Get single item
- POST /api/v1/review/queue/{item_id}/decision - Submit review decision
- GET /api/v1/review/stats - Queue statistics
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.intelligence import PublicationReviewQueue


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def auth_headers():
    """Create a mock JWT token for testing."""
    payload = {
        "sub": "test-user-id",
        "username": "testuser",
        "roles": ["admin"],
        "exp": datetime(2030, 1, 1, 0, 0, 0).timestamp(),
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_review_items(db_session: AsyncSession) -> list:
    """
    Create sample review queue items with different risk scores.

    Returns list of item IDs for use in tests.
    """
    now = datetime.now(timezone.utc)

    items = [
        PublicationReviewQueue(
            id=uuid4(),
            article_id=uuid4(),  # Maps to target_id in schema
            target="sitrep",  # Maps to target_type in schema
            risk_score=0.85,  # High risk
            content="High-risk SITREP content preview...",
            risk_factors={"factors": ["ai_generated", "sensitive_entity", "financial_claim"]},
            status="pending",
            created_at=now,
        ),
        PublicationReviewQueue(
            id=uuid4(),
            article_id=uuid4(),
            target="summary",
            risk_score=0.45,  # Medium risk
            content="Medium-risk summary preview...",
            risk_factors={"factors": ["ai_generated"]},
            status="pending",
            created_at=now,
        ),
        PublicationReviewQueue(
            id=uuid4(),
            article_id=uuid4(),
            target="alert",
            risk_score=0.15,  # Low risk
            content="Low-risk alert content...",
            risk_factors={"factors": []},
            status="pending",
            created_at=now,
        ),
    ]

    for item in items:
        db_session.add(item)

    await db_session.commit()

    # Refresh to get IDs
    for item in items:
        await db_session.refresh(item)

    return items


@pytest_asyncio.fixture
async def sample_pending_item(db_session: AsyncSession) -> PublicationReviewQueue:
    """Create a single pending review item for decision tests."""
    now = datetime.now(timezone.utc)

    item = PublicationReviewQueue(
        id=uuid4(),
        article_id=uuid4(),
        target="sitrep",
        risk_score=0.55,
        content="Sample SITREP for decision test...",
        risk_factors={"factors": ["ai_generated", "market_prediction"]},
        status="pending",
        created_at=now,
    )

    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    return item


# =============================================================================
# Test: GET /api/v1/review/queue - List pending items
# =============================================================================


class TestListPendingReviews:
    """Tests for GET /api/v1/review/queue endpoint."""

    def test_list_pending_reviews_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test listing pending review items returns paginated results."""
        response = client.get(
            "/api/v1/review/queue",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "items" in data
        assert "total" in data
        assert "pending_count" in data
        assert "high_risk_count" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_more" in data

        # Verify items returned (all 3 are pending)
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["pending_count"] == 3

    def test_list_pending_reviews_sorted_by_risk_desc(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test that items are sorted by risk_score descending (highest first)."""
        response = client.get(
            "/api/v1/review/queue",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]

        # Verify descending risk score order
        risk_scores = [item["risk_score"] for item in items]
        assert risk_scores == sorted(risk_scores, reverse=True)

        # Highest risk (0.85) should be first
        assert items[0]["risk_score"] == 0.85
        assert items[0]["target_type"] == "sitrep"

    def test_list_pending_reviews_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test pagination with page and page_size parameters."""
        response = client.get(
            "/api/v1/review/queue",
            params={"page": 1, "page_size": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["has_more"] is True  # 3 total, showing 2

    def test_list_pending_reviews_filter_by_min_risk(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test filtering by minimum risk score."""
        response = client.get(
            "/api/v1/review/queue",
            params={"min_risk_score": 0.4},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Only items with risk >= 0.4 (0.85 and 0.45)
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["risk_score"] >= 0.4

    def test_list_pending_reviews_filter_by_target_type(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test filtering by target_type."""
        response = client.get(
            "/api/v1/review/queue",
            params={"target_type": "sitrep"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["target_type"] == "sitrep"

    def test_list_pending_reviews_requires_auth(
        self,
        client: TestClient,
    ):
        """Test that endpoint requires authentication."""
        response = client.get("/api/v1/review/queue")

        assert response.status_code == 403  # No auth header

    def test_list_pending_reviews_high_risk_count(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test that high_risk_count is correctly calculated."""
        response = client.get(
            "/api/v1/review/queue",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Only 1 item has risk >= 0.7 (the 0.85 one)
        assert data["high_risk_count"] == 1


# =============================================================================
# Test: GET /api/v1/review/queue/{item_id} - Get single item
# =============================================================================


class TestGetReviewItem:
    """Tests for GET /api/v1/review/queue/{item_id} endpoint."""

    def test_get_review_item_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test getting a specific review item by ID."""
        response = client.get(
            f"/api/v1/review/queue/{sample_pending_item.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(sample_pending_item.id)
        assert data["target_type"] == "sitrep"
        assert data["risk_score"] == 0.55
        assert data["status"] == "pending"
        assert data["content_preview"] == "Sample SITREP for decision test..."
        assert "risk_factors" in data

    def test_get_review_item_includes_risk_level(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test that risk_level is calculated from risk_score."""
        response = client.get(
            f"/api/v1/review/queue/{sample_pending_item.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # 0.55 is medium risk (0.3 <= score < 0.7)
        assert data["risk_level"] == "medium"

    def test_get_review_item_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test 404 for non-existent item."""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/review/queue/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_review_item_requires_auth(
        self,
        client: TestClient,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test that endpoint requires authentication."""
        response = client.get(
            f"/api/v1/review/queue/{sample_pending_item.id}"
        )

        assert response.status_code == 403


# =============================================================================
# Test: POST /api/v1/review/queue/{item_id}/decision - Submit decision
# =============================================================================


class TestSubmitReviewDecision:
    """Tests for POST /api/v1/review/queue/{item_id}/decision endpoint."""

    def test_approve_decision_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test approving a review item."""
        response = client.post(
            f"/api/v1/review/queue/{sample_pending_item.id}/decision",
            json={
                "decision": "approve",
                "reviewer_notes": "Content verified as accurate.",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "approved"
        assert data["reviewer_notes"] == "Content verified as accurate."
        assert data["reviewed_at"] is not None

    def test_reject_decision_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test rejecting a review item with required reason."""
        response = client.post(
            f"/api/v1/review/queue/{sample_pending_item.id}/decision",
            json={
                "decision": "reject",
                "rejection_reason": "Contains unverified financial claims.",
                "reviewer_notes": "Flagged for inaccurate market predictions.",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rejected"

    def test_reject_requires_reason(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test that rejection requires rejection_reason."""
        response = client.post(
            f"/api/v1/review/queue/{sample_pending_item.id}/decision",
            json={
                "decision": "reject",
                # Missing rejection_reason
            },
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_approve_with_edits_decision(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test approving with content edits."""
        response = client.post(
            f"/api/v1/review/queue/{sample_pending_item.id}/decision",
            json={
                "decision": "approve_with_edits",
                "reviewer_notes": "Minor corrections applied.",
                "edited_content": {
                    "executive_summary": "Corrected summary text...",
                    "key_findings": ["Updated finding 1", "Updated finding 2"],
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "edited"

    def test_escalate_decision(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test escalating for further review."""
        response = client.post(
            f"/api/v1/review/queue/{sample_pending_item.id}/decision",
            json={
                "decision": "escalate",
                "reviewer_notes": "Needs senior analyst review due to high impact.",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Escalate keeps it pending but records the action
        assert data["status"] == "pending"

    def test_decision_item_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test 404 for non-existent item."""
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/review/queue/{fake_id}/decision",
            json={"decision": "approve"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_decision_requires_auth(
        self,
        client: TestClient,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test that endpoint requires authentication."""
        response = client.post(
            f"/api/v1/review/queue/{sample_pending_item.id}/decision",
            json={"decision": "approve"},
        )

        assert response.status_code == 403

    def test_decision_invalid_decision_type(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_pending_item: PublicationReviewQueue,
    ):
        """Test validation error for invalid decision type."""
        response = client.post(
            f"/api/v1/review/queue/{sample_pending_item.id}/decision",
            json={"decision": "invalid_decision"},
            headers=auth_headers,
        )

        assert response.status_code == 422


# =============================================================================
# Test: GET /api/v1/review/stats - Queue statistics
# =============================================================================


class TestGetReviewStats:
    """Tests for GET /api/v1/review/stats endpoint."""

    def test_get_stats_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test getting review queue statistics."""
        response = client.get(
            "/api/v1/review/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "total_pending" in data
        assert "total_reviewed_today" in data
        assert "auto_approved_count" in data
        assert "rejected_count" in data
        assert "risk_distribution" in data

        # Verify counts
        assert data["total_pending"] == 3

    def test_get_stats_risk_distribution(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test that risk_distribution counts are correct."""
        response = client.get(
            "/api/v1/review/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        risk_dist = data["risk_distribution"]

        # Sample items: 0.85 (high), 0.45 (medium), 0.15 (low)
        assert risk_dist["low"] == 1
        assert risk_dist["medium"] == 1
        assert risk_dist["high"] == 1

    def test_get_stats_empty_queue(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test stats with empty queue."""
        response = client.get(
            "/api/v1/review/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_pending"] == 0

    def test_get_stats_requires_auth(
        self,
        client: TestClient,
    ):
        """Test that endpoint requires authentication."""
        response = client.get("/api/v1/review/stats")

        assert response.status_code == 403


# =============================================================================
# Test: GET /api/v1/review/dashboard - Review Queue Dashboard
# Epic 2.3 Task 2.3.7: Create Review Queue Dashboard Endpoint
# =============================================================================


class TestGetReviewDashboard:
    """Tests for GET /api/v1/review/dashboard endpoint."""

    def test_get_dashboard_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test getting review dashboard data with all expected fields."""
        response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Dashboard should include summary stats
        assert "stats" in data
        assert "recent_items" in data
        assert "risk_distribution" in data

        # Verify stats structure
        stats = data["stats"]
        assert "total_pending" in stats
        assert "high_risk_count" in stats
        assert "reviewed_today" in stats
        assert "auto_approved_count" in stats

        # Verify recent_items is a list
        assert isinstance(data["recent_items"], list)

        # Verify risk_distribution structure
        risk_dist = data["risk_distribution"]
        assert "low" in risk_dist
        assert "medium" in risk_dist
        assert "high" in risk_dist

    def test_get_dashboard_stats_values(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test that dashboard stats contain correct values."""
        response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # With 3 sample items (0.85, 0.45, 0.15 risk scores)
        assert data["stats"]["total_pending"] == 3
        assert data["stats"]["high_risk_count"] == 1  # Only 0.85 >= 0.7

    def test_get_dashboard_recent_items_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test that recent_items have the expected structure."""
        response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return recent high-priority items
        recent_items = data["recent_items"]
        assert len(recent_items) <= 5  # Limited to 5 items

        # Each item should have required fields
        if len(recent_items) > 0:
            item = recent_items[0]
            assert "id" in item
            assert "target_type" in item
            assert "risk_score" in item
            assert "risk_level" in item
            assert "created_at" in item

    def test_get_dashboard_recent_items_sorted_by_risk(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test that recent_items are sorted by risk score descending."""
        response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        recent_items = data["recent_items"]
        if len(recent_items) > 1:
            risk_scores = [item["risk_score"] for item in recent_items]
            assert risk_scores == sorted(risk_scores, reverse=True), \
                "Recent items should be sorted by risk_score descending"

    def test_get_dashboard_risk_distribution_counts(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_review_items: list,
    ):
        """Test that risk_distribution counts are accurate."""
        response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        risk_dist = data["risk_distribution"]

        # Sample items: 0.85 (high), 0.45 (medium), 0.15 (low)
        assert risk_dist["low"] == 1
        assert risk_dist["medium"] == 1
        assert risk_dist["high"] == 1

    def test_get_dashboard_empty_queue(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test dashboard with empty queue returns valid structure."""
        response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should still have valid structure even with no items
        assert data["stats"]["total_pending"] == 0
        assert data["stats"]["high_risk_count"] == 0
        assert len(data["recent_items"]) == 0
        assert data["risk_distribution"]["low"] == 0
        assert data["risk_distribution"]["medium"] == 0
        assert data["risk_distribution"]["high"] == 0

    def test_get_dashboard_requires_auth(
        self,
        client: TestClient,
    ):
        """Test that dashboard endpoint requires authentication."""
        response = client.get("/api/v1/review/dashboard")

        assert response.status_code == 403

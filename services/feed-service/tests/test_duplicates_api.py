# services/feed-service/tests/test_duplicates_api.py
"""Tests for duplicate review API endpoints.

Epic 1.2: Deduplication Pipeline - Task 5
Tests for HITL (Human-in-the-Loop) review endpoints.

Test coverage:
- GET /api/v1/duplicates - List pending near-duplicates
- GET /api/v1/duplicates/stats - Get duplicate detection statistics
- GET /api/v1/duplicates/{id} - Get single candidate with details
- PUT /api/v1/duplicates/{id} - Submit review decision
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.feed import Feed, FeedItem, DuplicateCandidate


class TestDuplicatesAPINoAuth:
    """Tests for duplicate review API without authentication."""

    def test_list_duplicates_requires_auth(self, client):
        """Should return 403 when no auth token provided."""
        response = client.get("/api/v1/duplicates")
        assert response.status_code == 403  # HTTPBearer returns 403 when no token

    def test_get_stats_requires_auth(self, client):
        """Should return 403 when no auth token provided."""
        response = client.get("/api/v1/duplicates/stats")
        assert response.status_code == 403

    def test_get_candidate_requires_auth(self, client):
        """Should return 403 when no auth token provided."""
        response = client.get(f"/api/v1/duplicates/{uuid4()}")
        assert response.status_code == 403

    def test_review_duplicate_requires_auth(self, client):
        """Should return 403 when no auth token provided."""
        response = client.put(
            f"/api/v1/duplicates/{uuid4()}",
            json={"decision": "keep_both"},
        )
        assert response.status_code == 403


class TestDuplicatesAPIWithAuth:
    """Tests for duplicate review API with authentication."""

    @pytest.fixture
    def auth_header(self):
        """Create a mock JWT token for testing with admin role."""
        from jose import jwt
        from app.config import settings

        token = jwt.encode(
            {"sub": "1", "exp": 9999999999, "roles": ["admin", "user"]},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def non_admin_auth_header(self):
        """Create a mock JWT token for testing without admin role."""
        from jose import jwt
        from app.config import settings

        token = jwt.encode(
            {"sub": "2", "exp": 9999999999, "roles": ["user"]},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return {"Authorization": f"Bearer {token}"}

    @pytest_asyncio.fixture
    async def test_data(self, db_session):
        """Create test data: feed, articles, and duplicate candidates."""
        # Create a feed
        feed = Feed(
            name="Test Feed for Duplicates",
            url="https://example.com/feed-duplicates-" + str(uuid4())[:8] + ".xml",
        )
        db_session.add(feed)
        await db_session.flush()

        # Create articles
        article1 = FeedItem(
            feed_id=feed.id,
            title="Original Article",
            link="https://example.com/original-" + str(uuid4())[:8],
            description="This is the original article description",
            content_hash="original_hash_" + str(uuid4())[:40],
            simhash_fingerprint=1234567890,
            pub_status="usable",
        )
        article2 = FeedItem(
            feed_id=feed.id,
            title="Near Duplicate Article",
            link="https://example.com/duplicate-" + str(uuid4())[:8],
            description="This is a near duplicate article",
            content_hash="duplicate_hash_" + str(uuid4())[:40],
            simhash_fingerprint=1234567895,
            pub_status="usable",
        )
        article3 = FeedItem(
            feed_id=feed.id,
            title="Another Article",
            link="https://example.com/another-" + str(uuid4())[:8],
            description="This is another unrelated article",
            content_hash="another_hash_" + str(uuid4())[:40],
            simhash_fingerprint=9876543210,
            pub_status="usable",
        )
        db_session.add(article1)
        db_session.add(article2)
        db_session.add(article3)
        await db_session.flush()

        # Create duplicate candidate (pending)
        candidate1 = DuplicateCandidate(
            new_article_id=article2.id,
            existing_article_id=article1.id,
            hamming_distance=5,
            simhash_new=1234567895,
            simhash_existing=1234567890,
            status="pending",
        )
        # Create already reviewed candidate
        candidate2 = DuplicateCandidate(
            new_article_id=article3.id,
            existing_article_id=article1.id,
            hamming_distance=7,
            simhash_new=9876543210,
            simhash_existing=1234567890,
            status="reviewed",
            reviewed_by=1,
            reviewed_at=datetime.now(timezone.utc),
            review_decision="keep_both",
        )
        db_session.add(candidate1)
        db_session.add(candidate2)
        await db_session.flush()

        return {
            "feed": feed,
            "articles": [article1, article2, article3],
            "candidates": [candidate1, candidate2],
        }

    # =========================================================================
    # List Duplicates Endpoint Tests
    # =========================================================================

    def test_list_duplicates_empty(self, client, auth_header):
        """Should return empty list when no duplicates exist."""
        response = client.get("/api/v1/duplicates", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_list_duplicates_with_data(
        self, client, auth_header, db_session, test_data
    ):
        """Should return list of duplicate candidates."""
        response = client.get("/api/v1/duplicates", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        # Default filter is 'pending', so only 1 result
        assert len(data["items"]) == 1
        assert data["total"] == 1
        item = data["items"][0]
        assert item["status"] == "pending"
        assert item["hamming_distance"] == 5

    @pytest.mark.asyncio
    async def test_list_duplicates_filter_all(
        self, client, auth_header, db_session, test_data
    ):
        """Should return all duplicates when filter is 'all'."""
        response = client.get(
            "/api/v1/duplicates?status=all", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_duplicates_filter_reviewed(
        self, client, auth_header, db_session, test_data
    ):
        """Should return only reviewed duplicates."""
        response = client.get(
            "/api/v1/duplicates?status=reviewed", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "reviewed"

    def test_list_duplicates_invalid_status(self, client, auth_header):
        """Should return 400 for invalid status filter."""
        response = client.get(
            "/api/v1/duplicates?status=invalid", headers=auth_header
        )
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_duplicates_pagination(
        self, client, auth_header, db_session, test_data
    ):
        """Should respect pagination parameters."""
        response = client.get(
            "/api/v1/duplicates?status=all&page=1&page_size=1",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 1

    # =========================================================================
    # Get Stats Endpoint Tests
    # =========================================================================

    def test_get_stats_empty(self, client, auth_header):
        """Should return zero counts when no data exists."""
        response = client.get("/api/v1/duplicates/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["pending_count"] == 0
        assert data["reviewed_count"] == 0
        assert data["auto_resolved_count"] == 0
        assert data["total_count"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_data(
        self, client, auth_header, db_session, test_data
    ):
        """Should return correct counts."""
        response = client.get("/api/v1/duplicates/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["pending_count"] == 1
        assert data["reviewed_count"] == 1
        assert data["auto_resolved_count"] == 0
        assert data["total_count"] == 2

    # =========================================================================
    # Get Single Candidate Endpoint Tests
    # =========================================================================

    def test_get_candidate_not_found(self, client, auth_header):
        """Should return 404 when candidate not found."""
        response = client.get(
            f"/api/v1/duplicates/{uuid4()}", headers=auth_header
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_candidate_with_details(
        self, client, auth_header, db_session, test_data
    ):
        """Should return candidate with article details."""
        candidate = test_data["candidates"][0]
        response = client.get(
            f"/api/v1/duplicates/{candidate.id}", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()

        # Check basic fields
        assert data["id"] == str(candidate.id)
        assert data["hamming_distance"] == 5
        assert data["status"] == "pending"

        # Check article details are included
        assert data["new_article_title"] == "Near Duplicate Article"
        assert data["existing_article_title"] == "Original Article"

        # Check simhash values
        assert data["simhash_new"] == 1234567895
        assert data["simhash_existing"] == 1234567890

    # =========================================================================
    # Review Endpoint Tests
    # =========================================================================

    def test_review_not_found(self, client, auth_header):
        """Should return 404 when candidate not found."""
        response = client.put(
            f"/api/v1/duplicates/{uuid4()}",
            headers=auth_header,
            json={"decision": "keep_both"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_review_keep_both(
        self, client, auth_header, db_session, test_data
    ):
        """Should mark candidate as reviewed with keep_both decision."""
        candidate = test_data["candidates"][0]
        article2 = test_data["articles"][1]  # New article

        response = client.put(
            f"/api/v1/duplicates/{candidate.id}",
            headers=auth_header,
            json={"decision": "keep_both", "notes": "False positive"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["decision"] == "keep_both"
        assert data["candidate_id"] == str(candidate.id)

        # Verify article was NOT changed
        await db_session.refresh(article2)
        assert article2.pub_status == "usable"

    @pytest.mark.asyncio
    async def test_review_reject_new(
        self, client, auth_header, db_session, test_data
    ):
        """Should mark new article as withheld."""
        candidate = test_data["candidates"][0]
        article2 = test_data["articles"][1]  # New article

        response = client.put(
            f"/api/v1/duplicates/{candidate.id}",
            headers=auth_header,
            json={"decision": "reject_new", "notes": "True duplicate"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["decision"] == "reject_new"

        # Verify article was marked as withheld
        await db_session.refresh(article2)
        assert article2.pub_status == "withheld"

    @pytest.mark.asyncio
    async def test_review_merge(
        self, client, auth_header, db_session, test_data
    ):
        """Should mark candidate as reviewed with merge decision."""
        candidate = test_data["candidates"][0]

        response = client.put(
            f"/api/v1/duplicates/{candidate.id}",
            headers=auth_header,
            json={"decision": "merge"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["decision"] == "merge"

    @pytest.mark.asyncio
    async def test_review_already_reviewed(
        self, client, auth_header, db_session, test_data
    ):
        """Should return 400 when trying to review already reviewed candidate."""
        candidate = test_data["candidates"][1]  # Already reviewed

        response = client.put(
            f"/api/v1/duplicates/{candidate.id}",
            headers=auth_header,
            json={"decision": "keep_both"},
        )
        assert response.status_code == 400
        assert "already been reviewed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_review_invalid_decision(
        self, client, auth_header, db_session, test_data
    ):
        """Should return 422 for invalid decision value."""
        candidate = test_data["candidates"][0]

        response = client.put(
            f"/api/v1/duplicates/{candidate.id}",
            headers=auth_header,
            json={"decision": "invalid_decision"},
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_review_with_notes(
        self, client, auth_header, db_session, test_data
    ):
        """Should save reviewer notes."""
        candidate = test_data["candidates"][0]

        response = client.put(
            f"/api/v1/duplicates/{candidate.id}",
            headers=auth_header,
            json={
                "decision": "keep_both",
                "notes": "This is a false positive - articles cover different topics",
            },
        )
        assert response.status_code == 200

        # Verify notes were saved
        await db_session.refresh(candidate)
        assert (
            candidate.review_notes
            == "This is a false positive - articles cover different topics"
        )
        assert candidate.reviewed_by == 1

    @pytest.mark.asyncio
    async def test_review_requires_admin_role(
        self, client, non_admin_auth_header, db_session, test_data
    ):
        """Should return 403 when user doesn't have admin role."""
        candidate = test_data["candidates"][0]

        response = client.put(
            f"/api/v1/duplicates/{candidate.id}",
            headers=non_admin_auth_header,
            json={"decision": "keep_both"},
        )
        assert response.status_code == 403
        assert "Admin role required" in response.json()["detail"]

    def test_list_duplicates_works_without_admin(self, client, non_admin_auth_header):
        """Non-admin users can still list duplicates."""
        response = client.get("/api/v1/duplicates", headers=non_admin_auth_header)
        assert response.status_code == 200

    def test_get_stats_works_without_admin(self, client, non_admin_auth_header):
        """Non-admin users can still get stats."""
        response = client.get("/api/v1/duplicates/stats", headers=non_admin_auth_header)
        assert response.status_code == 200


class TestDuplicatesAPISchemas:
    """Tests for Pydantic schema validation."""

    def test_review_decision_valid_values(self):
        """Should accept valid decision values."""
        from app.api.duplicates import ReviewDecision

        # Test all valid values
        for decision in ["keep_both", "merge", "reject_new"]:
            rd = ReviewDecision(decision=decision)
            assert rd.decision == decision

    def test_review_decision_with_notes(self):
        """Should accept optional notes."""
        from app.api.duplicates import ReviewDecision

        rd = ReviewDecision(decision="keep_both", notes="Test notes")
        assert rd.notes == "Test notes"

    def test_review_decision_notes_max_length(self):
        """Should enforce max length on notes."""
        from app.api.duplicates import ReviewDecision
        from pydantic import ValidationError

        # 1000 characters should be ok
        rd = ReviewDecision(decision="keep_both", notes="x" * 1000)
        assert len(rd.notes) == 1000

        # 1001 characters should fail
        with pytest.raises(ValidationError):
            ReviewDecision(decision="keep_both", notes="x" * 1001)

    def test_duplicate_candidate_response(self):
        """Should create valid response schema."""
        from app.api.duplicates import DuplicateCandidateResponse

        now = datetime.now(timezone.utc)
        response = DuplicateCandidateResponse(
            id=uuid4(),
            new_article_id=uuid4(),
            existing_article_id=uuid4(),
            hamming_distance=5,
            status="pending",
            created_at=now,
        )
        assert response.hamming_distance == 5
        assert response.status == "pending"

    def test_duplicate_stats_response(self):
        """Should create valid stats response."""
        from app.api.duplicates import DuplicateStatsResponse

        stats = DuplicateStatsResponse(
            pending_count=10,
            reviewed_count=5,
            auto_resolved_count=2,
            total_count=17,
        )
        assert stats.pending_count == 10
        assert stats.total_count == 17

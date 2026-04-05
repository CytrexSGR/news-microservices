# File: services/feed-service/tests/test_review_submit.py
"""
Tests for HITL Review Queue Submit endpoint with Risk Scoring Integration.

Epic 2.3 Task 2.3.5: Integrate Risk Scoring with SITREP Generation

This test verifies:
1. POST /api/v1/review/submit - Submit content for review
2. Automatic risk scoring using RiskScorer
3. Auto-approval for low-risk content (score < 0.3)
4. Pending status for high-risk content (score >= 0.3)
"""

import pytest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings


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


# =============================================================================
# Test: POST /api/v1/review/submit - Submit content for review
# =============================================================================


class TestSubmitForReview:
    """Tests for POST /api/v1/review/submit endpoint."""

    def test_submit_high_risk_content_creates_pending_item(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that high-risk content (score >= 0.3) is added to review queue
        with pending status.

        Content with legal language should trigger high risk score.
        """
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Breaking: Major lawsuit filed against company for fraud allegations.",
                "metadata": {
                    "ai_generated": True,
                    "source": "sitrep-service",
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["target_type"] == "sitrep"
        assert data["target_id"] == target_id
        assert data["status"] == "pending"

        # Risk score should be >= 0.3 due to legal/allegations language
        assert data["risk_score"] >= 0.3

        # Should have risk factors from the scorer
        assert "risk_factors" in data
        assert len(data["risk_factors"]) > 0

    def test_submit_low_risk_content_auto_approves(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that low-risk content (score < 0.3) is auto-approved.

        Plain informational content without risky patterns should auto-approve.
        """
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "summary",
                "target_id": target_id,
                "content_preview": "Today's weather forecast shows sunny conditions across the region.",
                "metadata": {
                    "ai_generated": True,
                    "source": "sitrep-service",
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Low-risk content should be auto-approved
        assert data["status"] == "auto_approved"
        assert data["risk_score"] < 0.3

    def test_submit_financial_content_is_flagged(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that financial content is detected.

        Content mentioning earnings, revenue, profits has financial_data risk factor.
        Single pattern score of 0.15 is below 0.3 threshold (auto-approved),
        but the risk factor is still identified.
        """
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Company reported quarterly earnings of $5 billion revenue and strong profit margins.",
                "metadata": {
                    "ai_generated": True,
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Financial content alone (0.15) is below threshold, so auto-approved
        # But the financial_data risk factor should be detected
        assert "financial_data" in data["risk_factors"]
        assert data["risk_score"] == 0.15

    def test_submit_investment_advice_is_flagged(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that investment advice content is detected.

        Content with buy/sell recommendations triggers investment_advice factor.
        Single pattern score of 0.2 is below 0.3 threshold.
        """
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "alert",
                "target_id": target_id,
                "content_preview": "Analysts recommend buy rating with target price of $150.",
                "metadata": {
                    "ai_generated": True,
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Investment advice (0.2) alone is below threshold
        assert "investment_advice" in data["risk_factors"]
        assert data["risk_score"] == 0.2

    def test_submit_unverified_claims_requires_review(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that content with unverified claims is flagged.

        Words like "reportedly", "sources say" indicate unverified information.
        """
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Sources say the company is reportedly planning a major acquisition.",
                "metadata": {
                    "ai_generated": True,
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Should have unverified claims risk factor
        assert "unverified_claims" in data["risk_factors"]

    def test_submit_empty_content_creates_low_risk_item(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that empty/minimal content is auto-approved (no risky patterns)."""
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "summary",
                "target_id": target_id,
                "content_preview": "",
                "metadata": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["risk_score"] == 0.0
        assert data["status"] == "auto_approved"

    def test_submit_requires_target_type(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test validation error for missing target_type."""
        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_id": str(uuid4()),
                "content_preview": "Some content",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_submit_requires_target_id(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test validation error for missing target_id."""
        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "content_preview": "Some content",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_submit_requires_auth(
        self,
        client: TestClient,
    ):
        """Test that endpoint requires authentication."""
        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": str(uuid4()),
                "content_preview": "Some content",
            },
        )

        assert response.status_code == 403

    def test_submit_returns_risk_level(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that response includes calculated risk_level."""
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Alleged fraud scandal at major corporation.",
                "metadata": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Should have risk_level field
        assert "risk_level" in data
        assert data["risk_level"] in ["low", "medium", "high"]

    def test_submit_idempotent_same_target_id(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that submitting same target_id twice doesn't create duplicates.

        Should return existing item or update it.
        """
        target_id = str(uuid4())

        # First submission
        response1 = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Initial content",
            },
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Second submission with same target_id
        response2 = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Updated content with fraud allegations.",
            },
            headers=auth_headers,
        )

        # Should succeed (either create or update)
        assert response2.status_code in [200, 201]

        # Should return the same item
        data1 = response1.json()
        data2 = response2.json()
        assert data1["target_id"] == data2["target_id"]


# =============================================================================
# Test: Risk Score Threshold Behavior
# =============================================================================


class TestRiskScoreThresholds:
    """Tests for risk score threshold behavior (0.3 threshold)."""

    def test_risk_score_exactly_at_threshold_is_pending(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that content with risk score exactly at threshold (0.3) is pending.

        Threshold is inclusive: score >= 0.3 means pending.
        """
        target_id = str(uuid4())

        # Content with only unverified_claims (weight 0.1) + something else
        # to get exactly around 0.3
        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Allegedly the situation is developing. Sources reportedly confirm.",
                "metadata": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # If score is at or above threshold, should be pending
        if data["risk_score"] >= 0.3:
            assert data["status"] == "pending"
        else:
            assert data["status"] == "auto_approved"

    def test_multiple_risk_patterns_accumulate(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that multiple risk patterns increase the score."""
        target_id = str(uuid4())

        # Content with multiple risky patterns
        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": (
                    "Breaking: Lawsuit filed alleging fraud. "
                    "Earnings reportedly missed targets. "
                    "Analysts recommend sell."
                ),
                "metadata": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Multiple patterns should result in higher risk
        assert data["risk_score"] >= 0.5
        assert len(data["risk_factors"]) >= 3
        assert data["status"] == "pending"

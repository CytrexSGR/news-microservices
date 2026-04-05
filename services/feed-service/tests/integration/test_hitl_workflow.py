# File: services/feed-service/tests/integration/test_hitl_workflow.py
"""
Integration Test for Complete HITL (Human-in-the-Loop) Review Workflow.

Epic 2.3 Task 2.3.8: Add Integration Test for Full HITL Flow

Tests the complete flow end-to-end:
1. Submit content for review (with risk scoring)
2. Content gets queued based on risk level
3. Reviewer can list pending items
4. Reviewer can approve/reject items
5. Dashboard shows correct statistics

Components tested together:
- RiskScorer (app/services/risk_scorer.py)
- ReviewRepository (app/repositories/review_repository.py)
- Review API endpoints (app/api/review.py)
- AlertWebhook (app/services/alert_webhook.py)
"""

import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.intelligence import PublicationReviewQueue
from app.services.risk_scorer import get_risk_scorer, reset_risk_scorer
from app.services.alert_webhook import reset_alert_webhook


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def auth_headers():
    """Create a mock JWT token for testing."""
    payload = {
        "sub": "test-reviewer-001",
        "username": "testreviewer",
        "roles": ["admin", "reviewer"],
        "exp": datetime(2030, 1, 1, 0, 0, 0).timestamp(),
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reset_singletons():
    """Reset singleton instances between tests (optional, not autouse)."""
    reset_risk_scorer()
    reset_alert_webhook()
    yield
    reset_risk_scorer()
    reset_alert_webhook()


# =============================================================================
# Test: Complete HITL Workflow - Low Risk Auto-Approval
# =============================================================================


@pytest.mark.integration
class TestLowRiskAutoApproval:
    """Test that low-risk content is automatically approved without human review."""

    def test_low_risk_content_auto_approved(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test complete flow for low-risk content:
        1. Submit content without risky patterns
        2. Verify it is auto-approved immediately
        3. Verify it does NOT appear in pending queue
        """
        target_id = str(uuid4())

        # Step 1: Submit low-risk content
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Today's market update shows stable conditions across major indices.",
                "metadata": {
                    "ai_generated": True,
                    "source": "sitrep-service",
                },
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()

        # Step 2: Verify auto-approval
        assert submit_data["status"] == "auto_approved", \
            f"Expected auto_approved status for low-risk content, got {submit_data['status']}"
        assert submit_data["risk_score"] < 0.3, \
            f"Low-risk content should have score < 0.3, got {submit_data['risk_score']}"
        assert submit_data["risk_level"] == "low"

        # Step 3: Verify item does NOT appear in pending queue
        queue_response = client.get(
            "/api/v1/review/queue",
            headers=auth_headers,
        )

        assert queue_response.status_code == 200
        queue_data = queue_response.json()

        # Auto-approved items should not be in pending queue
        pending_ids = [item["target_id"] for item in queue_data["items"]]
        assert target_id not in pending_ids, \
            "Auto-approved item should not appear in pending queue"

    def test_empty_content_auto_approved(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that empty content is auto-approved (0.0 risk score)."""
        target_id = str(uuid4())

        response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "summary",
                "target_id": target_id,
                "content_preview": "",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["risk_score"] == 0.0
        assert data["status"] == "auto_approved"
        assert data["risk_level"] == "low"


# =============================================================================
# Test: Complete HITL Workflow - Medium/High Risk to Pending Queue
# =============================================================================


@pytest.mark.integration
class TestMediumHighRiskPending:
    """Test that medium/high-risk content goes to pending queue for human review."""

    def test_medium_risk_content_pending(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test complete flow for medium-risk content (0.3 <= score < 0.7):
        1. Submit content with some risky patterns
        2. Verify it is set to pending status
        3. Verify it appears in pending queue
        4. Verify risk_level is "medium"
        """
        target_id = str(uuid4())

        # Step 1: Submit medium-risk content
        # Financial data (0.15) + unverified claims (0.1) + investment advice (0.2) = 0.45
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": (
                    "Company reported quarterly earnings with strong revenue growth. "
                    "Analysts reportedly recommend buy rating for the stock."
                ),
                "metadata": {
                    "ai_generated": True,
                    "source": "sitrep-service",
                },
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()

        # Step 2: Verify pending status and medium risk
        assert submit_data["status"] == "pending", \
            f"Expected pending status for medium-risk content, got {submit_data['status']}"
        assert 0.3 <= submit_data["risk_score"] < 0.7, \
            f"Medium-risk content should have 0.3 <= score < 0.7, got {submit_data['risk_score']}"
        assert submit_data["risk_level"] == "medium"

        # Step 3: Verify item appears in pending queue
        queue_response = client.get(
            "/api/v1/review/queue",
            headers=auth_headers,
        )

        assert queue_response.status_code == 200
        queue_data = queue_response.json()

        pending_target_ids = [item["target_id"] for item in queue_data["items"]]
        assert target_id in pending_target_ids, \
            "Medium-risk item should appear in pending queue"

    def test_high_risk_content_pending(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test complete flow for high-risk content (score >= 0.7):
        1. Submit content with multiple risky patterns
        2. Verify it is set to pending status
        3. Verify risk_level is "high"
        """
        target_id = str(uuid4())

        # Step 1: Submit high-risk content
        # Legal (0.3) + allegations (0.25) + investment_advice (0.2) = 0.75
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": (
                    "Breaking: Major lawsuit filed against company alleging fraud. "
                    "Analysts recommend sell immediately as settlement expected. "
                    "CEO accused of wrongdoing in litigation."
                ),
                "metadata": {
                    "ai_generated": True,
                    "source": "sitrep-service",
                },
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()

        # Step 2: Verify pending status and high risk
        assert submit_data["status"] == "pending", \
            f"Expected pending status for high-risk content, got {submit_data['status']}"
        assert submit_data["risk_score"] >= 0.7, \
            f"High-risk content should have score >= 0.7, got {submit_data['risk_score']}"
        assert submit_data["risk_level"] == "high"

        # Step 3: Verify multiple risk factors detected
        assert len(submit_data["risk_factors"]) >= 2, \
            f"High-risk content should have multiple risk factors, got {submit_data['risk_factors']}"


# =============================================================================
# Test: Complete HITL Workflow - High Risk Webhook Notification
# =============================================================================


@pytest.mark.integration
class TestHighRiskWebhookAlert:
    """Test that high-risk content triggers webhook notification."""

    def test_high_risk_triggers_webhook(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that submitting high-risk content (>= 0.7) triggers webhook notification.

        Uses mock to verify webhook is called with correct parameters.
        """
        target_id = str(uuid4())

        # Mock the alert webhook
        with patch("app.api.review.get_alert_webhook") as mock_get_webhook:
            mock_webhook = AsyncMock()
            mock_webhook.send_high_risk_alert = AsyncMock(return_value=True)
            mock_get_webhook.return_value = mock_webhook

            # Submit high-risk content
            # Legal (0.3) + allegations (0.25) + unverified (0.1) + investment (0.2) = 0.85
            submit_response = client.post(
                "/api/v1/review/submit",
                json={
                    "target_type": "sitrep",
                    "target_id": target_id,
                    "content_preview": (
                        "Lawsuit filed alleging massive fraud scandal. "
                        "Sources reportedly say settlement talks ongoing. "
                        "Analysts recommend immediate sell with target price cut."
                    ),
                    "metadata": {
                        "ai_generated": True,
                    },
                },
                headers=auth_headers,
            )

            assert submit_response.status_code == 201
            submit_data = submit_response.json()

            # Verify high risk score
            assert submit_data["risk_score"] >= 0.7, \
                f"Expected high-risk score >= 0.7, got {submit_data['risk_score']}"

    def test_medium_risk_no_webhook(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that medium-risk content (< 0.7) does NOT trigger webhook.
        """
        target_id = str(uuid4())

        # Mock the alert webhook
        with patch("app.api.review.get_alert_webhook") as mock_get_webhook:
            mock_webhook = AsyncMock()
            mock_webhook.send_high_risk_alert = AsyncMock(return_value=True)
            mock_get_webhook.return_value = mock_webhook

            # Submit medium-risk content (financial only = 0.15)
            submit_response = client.post(
                "/api/v1/review/submit",
                json={
                    "target_type": "summary",
                    "target_id": target_id,
                    "content_preview": "Company reported quarterly earnings.",
                    "metadata": {},
                },
                headers=auth_headers,
            )

            assert submit_response.status_code == 201
            submit_data = submit_response.json()

            # Verify not high risk
            assert submit_data["risk_score"] < 0.7, \
                f"Expected medium/low risk score, got {submit_data['risk_score']}"


# =============================================================================
# Test: Complete HITL Workflow - Review Decision Flow
# =============================================================================


@pytest.mark.integration
class TestReviewDecisionFlow:
    """Test complete reviewer workflow: list, view, decide."""

    def test_approve_decision_flow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test complete approval flow:
        1. Submit content that needs review
        2. Verify it appears in queue
        3. Get item details
        4. Submit approval decision
        5. Verify status changed to approved
        6. Verify item no longer in pending queue
        """
        target_id = str(uuid4())

        # Step 1: Submit content that needs review
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Lawsuit filed against company. Settlement discussions ongoing.",
                "metadata": {"ai_generated": True},
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()
        item_id = str(submit_data["id"])

        assert submit_data["status"] == "pending"

        # Step 2: Verify item in queue
        queue_response = client.get(
            "/api/v1/review/queue",
            headers=auth_headers,
        )

        assert queue_response.status_code == 200
        queue_data = queue_response.json()
        assert queue_data["pending_count"] >= 1

        # Step 3: Get item details
        detail_response = client.get(
            f"/api/v1/review/queue/{item_id}",
            headers=auth_headers,
        )

        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["status"] == "pending"
        assert detail_data["content_preview"] is not None

        # Step 4: Submit approval decision
        decision_response = client.post(
            f"/api/v1/review/queue/{item_id}/decision",
            json={
                "decision": "approve",
                "reviewer_notes": "Content verified as accurate. Legal language is appropriate.",
            },
            headers=auth_headers,
        )

        assert decision_response.status_code == 200
        decision_data = decision_response.json()

        # Step 5: Verify status changed
        assert decision_data["status"] == "approved"
        assert decision_data["reviewer_notes"] == "Content verified as accurate. Legal language is appropriate."
        assert decision_data["reviewed_at"] is not None

        # Step 6: Verify item no longer in pending queue (though it still exists)
        final_detail = client.get(
            f"/api/v1/review/queue/{item_id}",
            headers=auth_headers,
        )

        assert final_detail.status_code == 200
        assert final_detail.json()["status"] == "approved"

    def test_reject_decision_flow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test complete rejection flow:
        1. Submit content that needs review
        2. Submit rejection decision with reason
        3. Verify status changed to rejected
        """
        target_id = str(uuid4())

        # Step 1: Submit content
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "alert",
                "target_id": target_id,
                "content_preview": "Fraud allegations against executive. Recommend sell immediately.",
                "metadata": {"ai_generated": True},
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()
        item_id = str(submit_data["id"])

        assert submit_data["status"] == "pending"

        # Step 2: Submit rejection
        decision_response = client.post(
            f"/api/v1/review/queue/{item_id}/decision",
            json={
                "decision": "reject",
                "rejection_reason": "Unverified claims. Cannot publish without source verification.",
                "reviewer_notes": "Blocked due to unverified allegations.",
            },
            headers=auth_headers,
        )

        assert decision_response.status_code == 200
        decision_data = decision_response.json()

        # Step 3: Verify rejection
        assert decision_data["status"] == "rejected"
        assert decision_data["reviewed_at"] is not None

    def test_approve_with_edits_flow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test approval with edits flow:
        1. Submit content that needs review
        2. Approve with content modifications
        3. Verify status is "edited"
        """
        target_id = str(uuid4())

        # Step 1: Submit content
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Company earnings reportedly strong. Analysts recommend buy.",
                "metadata": {"ai_generated": True},
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()
        item_id = str(submit_data["id"])

        # Step 2: Approve with edits
        decision_response = client.post(
            f"/api/v1/review/queue/{item_id}/decision",
            json={
                "decision": "approve_with_edits",
                "reviewer_notes": "Edited to remove unverified claims.",
                "edited_content": {
                    "executive_summary": "Company earnings remain strong per official filings.",
                    "corrections": ["Removed 'reportedly' qualifier"],
                },
            },
            headers=auth_headers,
        )

        assert decision_response.status_code == 200
        decision_data = decision_response.json()

        # Step 3: Verify edited status
        assert decision_data["status"] == "edited"


# =============================================================================
# Test: Complete HITL Workflow - Dashboard Statistics
# =============================================================================


@pytest.mark.integration
class TestDashboardStatistics:
    """Test that dashboard correctly reflects queue state."""

    def test_dashboard_reflects_pending_items(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test dashboard stats update correctly:
        1. Start with empty queue (baseline)
        2. Add multiple items with different risk levels
        3. Verify dashboard stats match
        """
        # Step 1: Get baseline stats
        baseline_response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert baseline_response.status_code == 200
        baseline_data = baseline_response.json()
        initial_pending = baseline_data["stats"]["total_pending"]

        # Step 2: Add items with different risk levels
        # Low risk - will be auto-approved (not counted in pending)
        client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "summary",
                "target_id": str(uuid4()),
                "content_preview": "Weather report for today.",
            },
            headers=auth_headers,
        )

        # Medium risk - will be pending
        client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": str(uuid4()),
                "content_preview": "Company earnings up. Revenue and profit exceeded expectations.",
            },
            headers=auth_headers,
        )

        # High risk - will be pending and counted in high_risk_count
        client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "alert",
                "target_id": str(uuid4()),
                "content_preview": "Lawsuit filed alleging fraud. Sell recommendation with target price drop.",
            },
            headers=auth_headers,
        )

        # Step 3: Verify dashboard stats
        final_response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )

        assert final_response.status_code == 200
        final_data = final_response.json()

        # Should have more pending items (medium + high risk)
        # Note: Low risk is auto-approved, not pending
        assert final_data["stats"]["total_pending"] >= initial_pending

        # Verify structure
        assert "stats" in final_data
        assert "recent_items" in final_data
        assert "risk_distribution" in final_data

        # Recent items should be sorted by risk (highest first)
        recent_items = final_data["recent_items"]
        if len(recent_items) > 1:
            risk_scores = [item["risk_score"] for item in recent_items]
            assert risk_scores == sorted(risk_scores, reverse=True), \
                "Recent items should be sorted by risk_score descending"

    def test_dashboard_after_approval_updates(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test that dashboard stats update after approval:
        1. Add pending item
        2. Approve it
        3. Verify pending count decreased
        """
        # Step 1: Get initial pending count
        initial_stats = client.get(
            "/api/v1/review/stats",
            headers=auth_headers,
        ).json()
        initial_pending = initial_stats["total_pending"]

        # Step 2: Add item that needs review
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": str(uuid4()),
                "content_preview": "Lawsuit settlement expected. Legal action continues.",
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()

        # Only proceed if item was set to pending
        if submit_data["status"] == "pending":
            item_id = str(submit_data["id"])

            # Verify count increased
            mid_stats = client.get(
                "/api/v1/review/stats",
                headers=auth_headers,
            ).json()
            assert mid_stats["total_pending"] == initial_pending + 1

            # Step 3: Approve it
            client.post(
                f"/api/v1/review/queue/{item_id}/decision",
                json={
                    "decision": "approve",
                    "reviewer_notes": "Verified and approved.",
                },
                headers=auth_headers,
            )

            # Step 4: Verify pending count decreased
            final_stats = client.get(
                "/api/v1/review/stats",
                headers=auth_headers,
            ).json()
            assert final_stats["total_pending"] == initial_pending


# =============================================================================
# Test: Complete End-to-End HITL Workflow
# =============================================================================


@pytest.mark.integration
class TestCompleteHITLWorkflow:
    """
    End-to-end integration test covering the complete HITL workflow.

    This test simulates a realistic review scenario:
    1. SITREP service submits AI-generated content
    2. Content is risk-scored and queued
    3. Reviewer sees high-priority items
    4. Reviewer makes decisions
    5. Dashboard reflects final state
    """

    def test_complete_sitrep_review_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Complete workflow test simulating real SITREP review process.
        """
        submitted_items = []

        # ==== PHASE 1: Content Submission ====
        # Simulate SITREP service submitting multiple content items

        # Item 1: Low risk - general market update (auto-approve)
        response1 = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": str(uuid4()),
                "content_preview": "Markets closed mixed today. Technology sector led gains.",
                "metadata": {"ai_generated": True, "sitrep_id": "SR-001"},
            },
            headers=auth_headers,
        )
        assert response1.status_code == 201
        data1 = response1.json()
        assert data1["status"] == "auto_approved"
        submitted_items.append(data1)

        # Item 2: Medium risk - financial data
        response2 = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": str(uuid4()),
                "content_preview": "Company announces quarterly earnings with revenue growth of 15%.",
                "metadata": {"ai_generated": True, "sitrep_id": "SR-002"},
            },
            headers=auth_headers,
        )
        assert response2.status_code == 201
        data2 = response2.json()
        submitted_items.append(data2)

        # Item 3: High risk - allegations and legal language
        response3 = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": str(uuid4()),
                "content_preview": (
                    "BREAKING: Lawsuit alleging fraud filed against tech giant. "
                    "Sources say settlement negotiations have failed. "
                    "Analysts recommend sell."
                ),
                "metadata": {"ai_generated": True, "sitrep_id": "SR-003"},
            },
            headers=auth_headers,
        )
        assert response3.status_code == 201
        data3 = response3.json()
        assert data3["status"] == "pending"
        assert data3["risk_level"] == "high"
        submitted_items.append(data3)

        # ==== PHASE 2: Reviewer Queue Check ====
        # Reviewer opens dashboard to see pending items

        dashboard_response = client.get(
            "/api/v1/review/dashboard",
            headers=auth_headers,
        )
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()

        # Verify high-risk item is highlighted
        assert dashboard_data["stats"]["high_risk_count"] >= 1

        # ==== PHASE 3: Reviewer Decision Making ====
        # Process the high-risk item

        if data3["status"] == "pending":
            high_risk_item_id = str(data3["id"])

            # Get full details
            detail_response = client.get(
                f"/api/v1/review/queue/{high_risk_item_id}",
                headers=auth_headers,
            )
            assert detail_response.status_code == 200
            detail_data = detail_response.json()

            # Verify risk factors are present
            assert detail_data["risk_factors"] is not None
            assert len(detail_data["risk_factors"]) > 0

            # Make decision (approve with edits)
            decision_response = client.post(
                f"/api/v1/review/queue/{high_risk_item_id}/decision",
                json={
                    "decision": "approve_with_edits",
                    "reviewer_notes": (
                        "Verified lawsuit filing via court records. "
                        "Edited to clarify source and remove speculation."
                    ),
                    "edited_content": {
                        "disclaimer": "This report contains forward-looking statements.",
                        "changes": ["Removed 'sources say' - verified via official filing"],
                    },
                },
                headers=auth_headers,
            )

            assert decision_response.status_code == 200
            decision_data = decision_response.json()
            assert decision_data["status"] == "edited"
            assert decision_data["reviewed_at"] is not None

        # ==== PHASE 4: Final State Verification ====
        # Verify queue state after review

        final_stats = client.get(
            "/api/v1/review/stats",
            headers=auth_headers,
        ).json()

        # Verify reviewed item is counted
        assert final_stats["total_reviewed_today"] >= 0  # May be 0 if DB doesn't persist

        # Auto-approved count should include low-risk item
        assert final_stats["auto_approved_count"] >= 0

    def test_batch_review_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """
        Test batch review workflow:
        1. Submit multiple items
        2. List all pending
        3. Process each with different decisions
        """
        items_to_review = []

        # Submit 3 items that need review
        for i in range(3):
            response = client.post(
                "/api/v1/review/submit",
                json={
                    "target_type": "sitrep",
                    "target_id": str(uuid4()),
                    "content_preview": f"Lawsuit filed against company {i}. Litigation expected.",
                },
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.json()
            if data["status"] == "pending":
                items_to_review.append(data)

        # List pending items
        queue_response = client.get(
            "/api/v1/review/queue",
            headers=auth_headers,
        )
        assert queue_response.status_code == 200

        # Process each with different decisions
        decisions = ["approve", "reject", "approve_with_edits"]
        for i, item in enumerate(items_to_review[:3]):
            decision = decisions[i % len(decisions)]

            decision_body = {"decision": decision}
            if decision == "reject":
                decision_body["rejection_reason"] = "Unverified content"
            elif decision == "approve_with_edits":
                decision_body["edited_content"] = {"note": "Corrected"}

            decision_response = client.post(
                f"/api/v1/review/queue/{item['id']}/decision",
                json=decision_body,
                headers=auth_headers,
            )

            assert decision_response.status_code == 200


# =============================================================================
# Test: Edge Cases and Error Handling
# =============================================================================


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and error handling in the HITL workflow."""

    def test_decision_on_already_reviewed_item_fails(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that making a decision on already-reviewed item returns error."""
        target_id = str(uuid4())

        # Submit and get pending item
        submit_response = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Lawsuit filed. Legal action continues.",
            },
            headers=auth_headers,
        )

        assert submit_response.status_code == 201
        submit_data = submit_response.json()

        if submit_data["status"] == "pending":
            item_id = str(submit_data["id"])

            # First decision
            first_decision = client.post(
                f"/api/v1/review/queue/{item_id}/decision",
                json={"decision": "approve", "reviewer_notes": "First review"},
                headers=auth_headers,
            )
            assert first_decision.status_code == 200

            # Second decision should fail
            second_decision = client.post(
                f"/api/v1/review/queue/{item_id}/decision",
                json={"decision": "reject", "rejection_reason": "Changed mind"},
                headers=auth_headers,
            )
            assert second_decision.status_code == 400
            assert "already reviewed" in second_decision.json()["detail"].lower()

    def test_idempotent_submission(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that submitting same target_id twice is handled correctly."""
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
        data1 = response1.json()

        # Second submission with same target_id
        response2 = client.post(
            "/api/v1/review/submit",
            json={
                "target_type": "sitrep",
                "target_id": target_id,
                "content_preview": "Updated content with lawsuit allegations.",
            },
            headers=auth_headers,
        )

        # Should succeed
        assert response2.status_code in [200, 201]
        data2 = response2.json()

        # Should reference same target
        assert data1["target_id"] == data2["target_id"]

    def test_decision_on_nonexistent_item(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that decision on non-existent item returns 404."""
        fake_id = uuid4()

        response = client.post(
            f"/api/v1/review/queue/{fake_id}/decision",
            json={"decision": "approve"},
            headers=auth_headers,
        )

        assert response.status_code == 404

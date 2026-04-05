# File: services/feed-service/tests/test_review_schemas.py
"""
Tests for HITL Review Workflow Pydantic Schemas.

Task 2.3.1: Create Review Queue Pydantic Schemas
TDD approach: Test first, then implement.

Schemas being tested:
- ReviewStatus (Enum)
- ReviewDecision (Enum)
- RiskLevel (Enum)
- ReviewItemCreate
- ReviewItemResponse
- ReviewDecisionRequest
- ReviewQueueListResponse
- ReviewStatsResponse
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError


class TestReviewStatus:
    """Test ReviewStatus enum values."""

    def test_review_status_values(self):
        """Test all ReviewStatus enum values are accessible."""
        from app.schemas.review import ReviewStatus

        assert ReviewStatus.PENDING == "pending"
        assert ReviewStatus.IN_REVIEW == "in_review"
        assert ReviewStatus.APPROVED == "approved"
        assert ReviewStatus.REJECTED == "rejected"
        assert ReviewStatus.AUTO_APPROVED == "auto_approved"


class TestRiskLevel:
    """Test RiskLevel enum values."""

    def test_risk_level_values(self):
        """Test all RiskLevel enum values are accessible."""
        from app.schemas.review import RiskLevel

        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"


class TestReviewDecision:
    """Test ReviewDecision enum values."""

    def test_review_decision_values(self):
        """Test all ReviewDecision enum values are accessible."""
        from app.schemas.review import ReviewDecision

        assert ReviewDecision.APPROVE == "approve"
        assert ReviewDecision.REJECT == "reject"
        assert ReviewDecision.APPROVE_WITH_EDITS == "approve_with_edits"
        assert ReviewDecision.ESCALATE == "escalate"


class TestReviewItemCreate:
    """Test ReviewItemCreate schema."""

    def test_create_valid_review_item(self):
        """Test creating a valid review item."""
        from app.schemas.review import ReviewItemCreate

        item = ReviewItemCreate(
            target_type="sitrep",
            target_id=uuid4(),
            risk_score=0.45,
            risk_factors=["ai_generated", "sensitive_entity"],
            content_preview="Preview of the SITREP content...",
        )

        assert item.target_type == "sitrep"
        assert 0.0 <= item.risk_score <= 1.0
        assert len(item.risk_factors) == 2

    def test_risk_score_must_be_in_range(self):
        """Test that risk_score must be between 0 and 1."""
        from app.schemas.review import ReviewItemCreate

        # Risk score > 1 should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewItemCreate(
                target_type="sitrep",
                target_id=uuid4(),
                risk_score=1.5,
            )
        assert "risk_score" in str(exc_info.value)

        # Risk score < 0 should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewItemCreate(
                target_type="sitrep",
                target_id=uuid4(),
                risk_score=-0.1,
            )
        assert "risk_score" in str(exc_info.value)

    def test_content_preview_max_length(self):
        """Test that content_preview has max length of 500."""
        from app.schemas.review import ReviewItemCreate

        # Exactly 500 chars should work
        item = ReviewItemCreate(
            target_type="sitrep",
            target_id=uuid4(),
            risk_score=0.5,
            content_preview="x" * 500,
        )
        assert len(item.content_preview) == 500

        # 501 chars should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewItemCreate(
                target_type="sitrep",
                target_id=uuid4(),
                risk_score=0.5,
                content_preview="x" * 501,
            )
        assert "content_preview" in str(exc_info.value)


class TestReviewItemResponse:
    """Test ReviewItemResponse schema."""

    def test_review_item_response_schema(self):
        """Test ReviewItemResponse schema validation."""
        from app.schemas.review import ReviewItemResponse, ReviewStatus

        data = {
            "id": uuid4(),
            "target_type": "sitrep",
            "target_id": uuid4(),
            "risk_score": 0.45,
            "risk_factors": ["ai_generated", "sensitive_entity"],
            "status": ReviewStatus.PENDING,
            "created_at": datetime.now(timezone.utc),
        }

        item = ReviewItemResponse(**data)

        assert item.status == ReviewStatus.PENDING
        assert 0.0 <= item.risk_score <= 1.0

    def test_risk_level_auto_calculated_low(self):
        """Test that risk_level is auto-calculated from risk_score for low risk."""
        from app.schemas.review import ReviewItemResponse, ReviewStatus, RiskLevel

        item = ReviewItemResponse(
            id=uuid4(),
            target_type="sitrep",
            target_id=uuid4(),
            risk_score=0.2,  # Low risk
            status=ReviewStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        assert item.risk_level == RiskLevel.LOW

    def test_risk_level_auto_calculated_medium(self):
        """Test that risk_level is auto-calculated from risk_score for medium risk."""
        from app.schemas.review import ReviewItemResponse, ReviewStatus, RiskLevel

        item = ReviewItemResponse(
            id=uuid4(),
            target_type="sitrep",
            target_id=uuid4(),
            risk_score=0.5,  # Medium risk
            status=ReviewStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        assert item.risk_level == RiskLevel.MEDIUM

    def test_risk_level_auto_calculated_high(self):
        """Test that risk_level is auto-calculated from risk_score for high risk."""
        from app.schemas.review import ReviewItemResponse, ReviewStatus, RiskLevel

        item = ReviewItemResponse(
            id=uuid4(),
            target_type="sitrep",
            target_id=uuid4(),
            risk_score=0.85,  # High risk
            status=ReviewStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        assert item.risk_level == RiskLevel.HIGH

    def test_risk_score_out_of_range(self):
        """Test that risk_score must be between 0 and 1."""
        from app.schemas.review import ReviewItemResponse, ReviewStatus

        with pytest.raises(ValidationError):
            ReviewItemResponse(
                id=uuid4(),
                target_type="sitrep",
                target_id=uuid4(),
                risk_score=1.5,  # Invalid: > 1.0
                status=ReviewStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )


class TestReviewDecisionRequest:
    """Test ReviewDecisionRequest schema."""

    def test_approve_decision(self):
        """Test approve decision validation."""
        from app.schemas.review import ReviewDecisionRequest, ReviewDecision

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE,
            reviewer_notes="Looks good, factually accurate.",
        )
        assert decision.decision == ReviewDecision.APPROVE

    def test_reject_requires_reason(self):
        """Test that reject decision requires rejection_reason."""
        from app.schemas.review import ReviewDecisionRequest, ReviewDecision

        with pytest.raises(ValidationError) as exc_info:
            ReviewDecisionRequest(
                decision=ReviewDecision.REJECT,
                # Missing rejection_reason
            )
        assert "rejection_reason" in str(exc_info.value)

    def test_reject_with_reason(self):
        """Test reject decision with valid reason."""
        from app.schemas.review import ReviewDecisionRequest, ReviewDecision

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.REJECT,
            rejection_reason="Contains factual inaccuracies about the timeline.",
            reviewer_notes="Source dates don't match.",
        )
        assert decision.decision == ReviewDecision.REJECT
        assert decision.rejection_reason is not None

    def test_approve_with_edits(self):
        """Test ReviewDecisionRequest with content edits."""
        from app.schemas.review import ReviewDecisionRequest, ReviewDecision

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE_WITH_EDITS,
            reviewer_notes="Minor corrections made.",
            edited_content={"executive_summary": "Corrected summary text..."},
        )

        assert decision.edited_content is not None
        assert "executive_summary" in decision.edited_content

    def test_escalate_decision(self):
        """Test escalate decision."""
        from app.schemas.review import ReviewDecisionRequest, ReviewDecision

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.ESCALATE,
            reviewer_notes="Needs legal review before publication.",
        )
        assert decision.decision == ReviewDecision.ESCALATE

    def test_reviewer_notes_max_length(self):
        """Test that reviewer_notes has max length of 1000."""
        from app.schemas.review import ReviewDecisionRequest, ReviewDecision

        # Exactly 1000 chars should work
        decision = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE,
            reviewer_notes="x" * 1000,
        )
        assert len(decision.reviewer_notes) == 1000

        # 1001 chars should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewDecisionRequest(
                decision=ReviewDecision.APPROVE,
                reviewer_notes="x" * 1001,
            )
        assert "reviewer_notes" in str(exc_info.value)


class TestReviewQueueListResponse:
    """Test ReviewQueueListResponse schema."""

    def test_list_response_schema(self):
        """Test ReviewQueueListResponse with sample data."""
        from app.schemas.review import (
            ReviewQueueListResponse,
            ReviewItemResponse,
            ReviewStatus,
        )

        items = [
            ReviewItemResponse(
                id=uuid4(),
                target_type="sitrep",
                target_id=uuid4(),
                risk_score=0.45,
                status=ReviewStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            ),
            ReviewItemResponse(
                id=uuid4(),
                target_type="sitrep",
                target_id=uuid4(),
                risk_score=0.75,
                status=ReviewStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        response = ReviewQueueListResponse(
            items=items,
            total=10,
            pending_count=5,
            high_risk_count=2,
            page=1,
            page_size=20,
            has_more=False,
        )

        assert len(response.items) == 2
        assert response.total == 10
        assert response.pending_count == 5
        assert response.high_risk_count == 2

    def test_empty_list_response(self):
        """Test ReviewQueueListResponse with empty items."""
        from app.schemas.review import ReviewQueueListResponse

        response = ReviewQueueListResponse(
            items=[],
            total=0,
            pending_count=0,
            high_risk_count=0,
            page=1,
            page_size=20,
            has_more=False,
        )

        assert len(response.items) == 0
        assert response.total == 0


class TestReviewStatsResponse:
    """Test ReviewStatsResponse schema."""

    def test_stats_response_schema(self):
        """Test ReviewStatsResponse with sample data."""
        from app.schemas.review import ReviewStatsResponse

        stats = ReviewStatsResponse(
            total_pending=15,
            total_reviewed_today=8,
            auto_approved_count=3,
            rejected_count=2,
            average_review_time_minutes=4.5,
            risk_distribution={"low": 5, "medium": 7, "high": 3},
        )

        assert stats.total_pending == 15
        assert stats.total_reviewed_today == 8
        assert stats.average_review_time_minutes == 4.5
        assert stats.risk_distribution["high"] == 3

    def test_stats_response_defaults(self):
        """Test ReviewStatsResponse with default values."""
        from app.schemas.review import ReviewStatsResponse

        stats = ReviewStatsResponse(
            total_pending=0,
            total_reviewed_today=0,
            auto_approved_count=0,
            rejected_count=0,
        )

        assert stats.average_review_time_minutes is None
        assert stats.risk_distribution == {"low": 0, "medium": 0, "high": 0}

# File: services/feed-service/app/schemas/review.py
"""
Pydantic schemas for HITL Review Workflow.

Defines request/response models for the publication review queue API.
These schemas map to the publication_review_queue table from V001 migration.

Schemas:
- ReviewStatus: Enum for review queue item status
- ReviewDecision: Enum for reviewer decision types
- RiskLevel: Enum for risk level categories
- ReviewItemCreate: Create a new review queue item
- ReviewItemResponse: Review queue item response
- ReviewDecisionRequest: Request to submit a review decision
- ReviewQueueListResponse: Paginated list of review queue items
- ReviewStatsResponse: Review queue statistics

Risk-based routing thresholds:
- Low risk (< 0.3): Auto-approve
- Medium risk (0.3-0.7): Human review
- High risk (> 0.7): Block + alert
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ReviewStatus(str, Enum):
    """Review queue item status.

    Maps to publication_review_queue.status constraint:
    ('pending', 'approved', 'rejected', 'edited', 'auto_approved', 'blocked')
    """

    PENDING = "pending"
    IN_REVIEW = "in_review"  # Claimed by reviewer, not yet decided
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"  # Approved with edits applied
    AUTO_APPROVED = "auto_approved"
    BLOCKED = "blocked"  # High-risk content blocked


class ReviewDecision(str, Enum):
    """Reviewer decision types."""

    APPROVE = "approve"
    REJECT = "reject"
    APPROVE_WITH_EDITS = "approve_with_edits"
    ESCALATE = "escalate"


class RiskLevel(str, Enum):
    """Risk level categories.

    Thresholds:
    - LOW: 0.0 - 0.3 (auto-approve candidates)
    - MEDIUM: 0.3 - 0.7 (human review required)
    - HIGH: 0.7 - 1.0 (block + alert)
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewItemCreate(BaseModel):
    """Create a new review queue item.

    Used when submitting content for review, typically after
    risk scoring indicates human review is needed.

    Attributes:
        target_type: Type of content (sitrep, summary, alert, etc.)
        target_id: UUID of the target content
        risk_score: Calculated risk score between 0 and 1
        risk_factors: List of risk factor labels
        content_preview: Short preview of the content (max 500 chars)
        metadata: Additional metadata for the review
    """

    target_type: str = Field(..., description="Type: sitrep, summary, alert")
    target_id: UUID = Field(..., description="ID of the target content")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score 0-1")
    risk_factors: Optional[List[str]] = Field(
        default=None, description="Risk factor labels"
    )
    content_preview: Optional[str] = Field(default=None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ReviewItemResponse(BaseModel):
    """Review queue item response.

    Full representation of a review queue item including
    calculated fields like risk_level.

    Attributes:
        id: Unique identifier for the review item
        target_type: Type of content being reviewed
        target_id: UUID of the target content
        risk_score: Calculated risk score (0-1)
        risk_level: Derived risk level (low/medium/high)
        risk_factors: List of risk factor labels
        status: Current review status
        content_preview: Short preview of the content
        reviewer_id: ID of the reviewer (if claimed)
        reviewer_notes: Notes from the reviewer
        reviewed_at: When the review was completed
        created_at: When the item was added to queue
        updated_at: Last update timestamp
    """

    id: UUID
    target_type: str
    target_id: UUID
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: Optional[RiskLevel] = None
    risk_factors: Optional[List[str]] = None
    status: ReviewStatus
    content_preview: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @model_validator(mode="after")
    def calculate_risk_level(self):
        """Calculate risk level from score if not provided."""
        if self.risk_level is None:
            if self.risk_score < 0.3:
                self.risk_level = RiskLevel.LOW
            elif self.risk_score < 0.7:
                self.risk_level = RiskLevel.MEDIUM
            else:
                self.risk_level = RiskLevel.HIGH
        return self

    model_config = {"from_attributes": True}


class ReviewDecisionRequest(BaseModel):
    """Request to submit a review decision.

    Validators ensure rejection_reason is provided when rejecting.

    Attributes:
        decision: The decision type (approve, reject, etc.)
        reviewer_notes: Optional notes from the reviewer (max 1000 chars)
        rejection_reason: Required when decision is 'reject' (max 500 chars)
        edited_content: Optional dict with edited content fields
    """

    decision: ReviewDecision
    reviewer_notes: Optional[str] = Field(default=None, max_length=1000)
    rejection_reason: Optional[str] = Field(default=None, max_length=500)
    edited_content: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_rejection_reason(self):
        """Require rejection_reason when rejecting."""
        if self.decision == ReviewDecision.REJECT and not self.rejection_reason:
            raise ValueError("rejection_reason is required when rejecting")
        return self

    model_config = {"from_attributes": True}


class ReviewQueueListResponse(BaseModel):
    """Paginated list of review queue items.

    Includes summary statistics for the queue.

    Attributes:
        items: List of review items
        total: Total number of items matching filters
        pending_count: Number of pending items
        high_risk_count: Number of high-risk pending items
        page: Current page number
        page_size: Items per page
        has_more: Whether more pages exist
    """

    items: List[ReviewItemResponse]
    total: int
    pending_count: int
    high_risk_count: int
    page: int
    page_size: int
    has_more: bool

    model_config = {"from_attributes": True}


class ReviewStatsResponse(BaseModel):
    """Review queue statistics.

    Provides overview metrics for the review queue dashboard.

    Attributes:
        total_pending: Total items awaiting review
        total_reviewed_today: Items reviewed today
        auto_approved_count: Items auto-approved (low risk)
        rejected_count: Items rejected
        average_review_time_minutes: Average time to review
        risk_distribution: Count by risk level
    """

    total_pending: int
    total_reviewed_today: int
    auto_approved_count: int
    rejected_count: int
    average_review_time_minutes: Optional[float] = None
    risk_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"low": 0, "medium": 0, "high": 0}
    )

    model_config = {"from_attributes": True}


class ReviewSubmitRequest(BaseModel):
    """Request to submit content for risk scoring and review.

    Used by sitrep-service and other content generators to submit
    AI-generated content for risk assessment and potential human review.

    The content_preview is analyzed for risky patterns (legal language,
    financial data, investment advice, unverified claims) to calculate
    a risk score. Based on the score:
    - score < 0.3: Auto-approved
    - score >= 0.3: Added to review queue with pending status

    Attributes:
        target_type: Type of content (sitrep, summary, alert)
        target_id: UUID of the target content
        content_preview: Content text to analyze for risk (max 5000 chars)
        metadata: Additional metadata for the review
    """

    target_type: str = Field(
        ...,
        description="Content type: sitrep, summary, alert, etc.",
        examples=["sitrep", "summary", "alert"],
    )
    target_id: str = Field(
        ...,
        description="UUID of the target content",
    )
    content_preview: Optional[str] = Field(
        default="",
        max_length=5000,
        description="Content text to analyze for risk patterns",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (ai_generated, source, etc.)",
    )

    model_config = {"from_attributes": True}


class ReviewSubmitResponse(BaseModel):
    """Response from content submission with risk scoring.

    Includes the calculated risk score, risk factors, and resulting
    status (auto_approved or pending for human review).

    Attributes:
        id: UUID of the review queue item
        target_type: Type of content submitted
        target_id: UUID of the target content
        risk_score: Calculated risk score (0.0-1.0)
        risk_level: Risk level category (low/medium/high)
        risk_factors: List of detected risk factor labels
        status: Resulting status (auto_approved or pending)
        content_preview: Preview of submitted content
        created_at: When the item was created
    """

    id: UUID
    target_type: str
    target_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    risk_factors: List[str] = Field(default_factory=list)
    status: ReviewStatus
    content_preview: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Dashboard Response Schemas
# Epic 2.3 Task 2.3.7: Create Review Queue Dashboard Endpoint
# =============================================================================


class DashboardStatsResponse(BaseModel):
    """Dashboard summary statistics.

    Provides key metrics for the review queue overview.

    Attributes:
        total_pending: Total items awaiting review
        high_risk_count: Count of high-risk pending items (risk >= 0.7)
        reviewed_today: Items reviewed today
        auto_approved_count: Items auto-approved (low risk)
    """

    total_pending: int
    high_risk_count: int
    reviewed_today: int
    auto_approved_count: int

    model_config = {"from_attributes": True}


class DashboardRecentItemResponse(BaseModel):
    """Recent review item for dashboard display.

    Lightweight representation for dashboard listing.

    Attributes:
        id: Review item UUID
        target_type: Type of content (sitrep, summary, alert)
        risk_score: Calculated risk score (0-1)
        risk_level: Risk level category (low/medium/high)
        created_at: When the item was created
    """

    id: UUID
    target_type: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewDashboardResponse(BaseModel):
    """Review queue dashboard overview data.

    Provides comprehensive dashboard data including:
    - Summary statistics (pending count, risk counts)
    - Recent high-priority items
    - Risk distribution across pending items

    Used by the frontend Review Queue Dashboard page.

    Attributes:
        stats: Summary statistics for the queue
        recent_items: List of recent pending items sorted by risk
        risk_distribution: Count of items by risk level
    """

    stats: DashboardStatsResponse
    recent_items: List[DashboardRecentItemResponse]
    risk_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"low": 0, "medium": 0, "high": 0}
    )

    model_config = {"from_attributes": True}

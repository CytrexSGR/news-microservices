# File: services/feed-service/app/repositories/review_repository.py
"""
Review Queue Repository

CRUD operations for the publication_review_queue table.
Supports the HITL review workflow for AI-generated content.

IMPORTANT: Field Mapping Between Schema and Database Model

The Pydantic schemas use different field names than the database model:

Schema Field     | DB Model Field  | Description
-----------------|-----------------|------------------------------
target_type      | target          | Type of content (sitrep, summary, etc.)
target_id        | article_id      | UUID of the target content
content_preview  | content         | Short preview of content
reviewer_id      | reviewed_by     | ID of the reviewer

This repository handles the bidirectional mapping transparently.

Database Status Constraint:
('pending', 'approved', 'rejected', 'edited', 'auto_approved', 'blocked')
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import PublicationReviewQueue
from app.schemas.review import (
    ReviewItemCreate,
    ReviewItemResponse,
    ReviewDecisionRequest,
    ReviewQueueListResponse,
    ReviewStatsResponse,
    ReviewStatus,
    ReviewDecision,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class ReviewRepository:
    """
    Repository for review queue operations.

    Provides CRUD operations with automatic field mapping between
    Pydantic schemas and SQLAlchemy models.
    """

    # Risk thresholds for categorization
    LOW_RISK_THRESHOLD = 0.3
    HIGH_RISK_THRESHOLD = 0.7

    # Status mapping: ReviewDecision -> DB status string
    DECISION_TO_STATUS = {
        ReviewDecision.APPROVE: "approved",
        ReviewDecision.REJECT: "rejected",
        ReviewDecision.APPROVE_WITH_EDITS: "edited",
        ReviewDecision.ESCALATE: "pending",  # Escalate keeps it pending but flags it
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    def _model_to_response(
        self, item: PublicationReviewQueue
    ) -> ReviewItemResponse:
        """
        Map database model to response schema.

        Handles field name mapping:
        - target -> target_type
        - article_id -> target_id
        - content -> content_preview
        - reviewed_by -> reviewer_id
        """
        # Extract risk_factors list from JSONB
        risk_factors = None
        if item.risk_factors:
            if isinstance(item.risk_factors, dict):
                risk_factors = item.risk_factors.get("factors", [])
            elif isinstance(item.risk_factors, list):
                risk_factors = item.risk_factors

        return ReviewItemResponse(
            id=item.id,
            target_type=item.target,  # DB: target -> Schema: target_type
            target_id=item.article_id,  # DB: article_id -> Schema: target_id
            risk_score=item.risk_score,
            risk_factors=risk_factors,
            status=ReviewStatus(item.status),
            content_preview=item.content,  # DB: content -> Schema: content_preview
            reviewer_id=item.reviewed_by,  # DB: reviewed_by -> Schema: reviewer_id
            reviewer_notes=item.reviewer_notes,
            reviewed_at=item.reviewed_at,
            created_at=item.created_at,
            updated_at=None,  # Not in current DB model
        )

    async def add_to_queue(
        self, data: ReviewItemCreate
    ) -> PublicationReviewQueue:
        """
        Add a new item to the review queue.

        Maps schema fields to database model:
        - target_type -> target
        - target_id -> article_id
        - content_preview -> content

        Args:
            data: Review item creation data

        Returns:
            Created database model instance
        """
        # Prepare risk_factors as JSONB
        risk_factors_json = None
        if data.risk_factors:
            risk_factors_json = {"factors": data.risk_factors}
        if data.metadata:
            if risk_factors_json:
                risk_factors_json.update(data.metadata)
            else:
                risk_factors_json = data.metadata

        item = PublicationReviewQueue(
            article_id=data.target_id,  # Schema: target_id -> DB: article_id
            target=data.target_type,  # Schema: target_type -> DB: target
            content=data.content_preview or "",  # Schema: content_preview -> DB: content
            risk_score=data.risk_score,
            risk_factors=risk_factors_json,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        logger.info(
            f"Created review item: id={item.id}, target={data.target_type}, "
            f"risk_score={data.risk_score}"
        )
        return item

    async def get_item(self, item_id: UUID) -> Optional[ReviewItemResponse]:
        """
        Get a review item by ID.

        Args:
            item_id: Review item UUID

        Returns:
            Review item response schema or None if not found
        """
        query = select(PublicationReviewQueue).where(
            PublicationReviewQueue.id == item_id
        )
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()

        if item is None:
            return None

        return self._model_to_response(item)

    async def list_pending(
        self,
        page: int = 1,
        page_size: int = 20,
        min_risk_score: Optional[float] = None,
        target_type: Optional[str] = None,
    ) -> ReviewQueueListResponse:
        """
        List pending review items with pagination.

        Items are ordered by risk_score descending (highest risk first).

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            min_risk_score: Filter by minimum risk score
            target_type: Filter by target type

        Returns:
            Paginated list response with counts
        """
        # Base query for pending items
        base_conditions = [PublicationReviewQueue.status == "pending"]

        if min_risk_score is not None:
            base_conditions.append(
                PublicationReviewQueue.risk_score >= min_risk_score
            )

        if target_type:
            base_conditions.append(
                PublicationReviewQueue.target == target_type
            )

        # Count total matching items
        count_query = select(func.count(PublicationReviewQueue.id)).where(
            and_(*base_conditions)
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Count high-risk items
        high_risk_query = select(func.count(PublicationReviewQueue.id)).where(
            and_(
                PublicationReviewQueue.status == "pending",
                PublicationReviewQueue.risk_score >= self.HIGH_RISK_THRESHOLD,
            )
        )
        high_risk_result = await self.db.execute(high_risk_query)
        high_risk_count = high_risk_result.scalar() or 0

        # Fetch paginated items
        offset = (page - 1) * page_size
        items_query = (
            select(PublicationReviewQueue)
            .where(and_(*base_conditions))
            .order_by(PublicationReviewQueue.risk_score.desc())
            .offset(offset)
            .limit(page_size)
        )
        items_result = await self.db.execute(items_query)
        items = items_result.scalars().all()

        # Map to response schemas
        response_items = [self._model_to_response(item) for item in items]

        return ReviewQueueListResponse(
            items=response_items,
            total=total,
            pending_count=total,  # All returned items are pending
            high_risk_count=high_risk_count,
            page=page,
            page_size=page_size,
            has_more=(offset + len(items)) < total,
        )

    async def update_decision(
        self,
        item_id: UUID,
        decision: ReviewDecisionRequest,
        reviewer_id: str,
    ) -> Optional[ReviewItemResponse]:
        """
        Update a review item with a decision.

        Maps:
        - reviewer_id -> reviewed_by (DB)
        - ReviewDecision -> status string

        Args:
            item_id: Review item UUID
            decision: Decision request with reviewer notes
            reviewer_id: ID of the reviewer making the decision

        Returns:
            Updated review item response or None if not found
        """
        # Fetch the item
        query = select(PublicationReviewQueue).where(
            PublicationReviewQueue.id == item_id
        )
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()

        if item is None:
            logger.warning(f"Review item not found: {item_id}")
            return None

        # Map decision to status
        new_status = self.DECISION_TO_STATUS.get(
            decision.decision, "pending"
        )

        # Update fields
        item.status = new_status
        item.reviewed_by = reviewer_id  # Schema: reviewer_id -> DB: reviewed_by
        item.reviewer_notes = decision.reviewer_notes
        item.reviewed_at = datetime.now(timezone.utc)

        # Store edited content if provided
        if decision.edited_content:
            # Store as JSON string in edited_content field
            import json
            item.edited_content = json.dumps(decision.edited_content)

        await self.db.commit()
        await self.db.refresh(item)

        logger.info(
            f"Updated review decision: id={item_id}, decision={decision.decision}, "
            f"reviewer={reviewer_id}"
        )
        return self._model_to_response(item)

    async def get_stats(self) -> ReviewStatsResponse:
        """
        Get review queue statistics.

        Returns statistics including:
        - Total pending items
        - Items reviewed today
        - Auto-approved count
        - Rejected count
        - Risk distribution

        Returns:
            Review statistics response
        """
        # Count pending items
        pending_query = select(func.count(PublicationReviewQueue.id)).where(
            PublicationReviewQueue.status == "pending"
        )
        pending_result = await self.db.execute(pending_query)
        total_pending = pending_result.scalar() or 0

        # Count items reviewed today
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        reviewed_today_query = select(
            func.count(PublicationReviewQueue.id)
        ).where(
            and_(
                PublicationReviewQueue.reviewed_at.isnot(None),
                PublicationReviewQueue.reviewed_at >= today_start,
            )
        )
        reviewed_today_result = await self.db.execute(reviewed_today_query)
        total_reviewed_today = reviewed_today_result.scalar() or 0

        # Count auto-approved
        auto_approved_query = select(
            func.count(PublicationReviewQueue.id)
        ).where(PublicationReviewQueue.status == "auto_approved")
        auto_approved_result = await self.db.execute(auto_approved_query)
        auto_approved_count = auto_approved_result.scalar() or 0

        # Count rejected
        rejected_query = select(func.count(PublicationReviewQueue.id)).where(
            PublicationReviewQueue.status == "rejected"
        )
        rejected_result = await self.db.execute(rejected_query)
        rejected_count = rejected_result.scalar() or 0

        # Calculate risk distribution for pending items
        risk_distribution = {"low": 0, "medium": 0, "high": 0}

        # Low risk: score < 0.3
        low_query = select(func.count(PublicationReviewQueue.id)).where(
            and_(
                PublicationReviewQueue.status == "pending",
                PublicationReviewQueue.risk_score < self.LOW_RISK_THRESHOLD,
            )
        )
        low_result = await self.db.execute(low_query)
        risk_distribution["low"] = low_result.scalar() or 0

        # Medium risk: 0.3 <= score < 0.7
        medium_query = select(func.count(PublicationReviewQueue.id)).where(
            and_(
                PublicationReviewQueue.status == "pending",
                PublicationReviewQueue.risk_score >= self.LOW_RISK_THRESHOLD,
                PublicationReviewQueue.risk_score < self.HIGH_RISK_THRESHOLD,
            )
        )
        medium_result = await self.db.execute(medium_query)
        risk_distribution["medium"] = medium_result.scalar() or 0

        # High risk: score >= 0.7
        high_query = select(func.count(PublicationReviewQueue.id)).where(
            and_(
                PublicationReviewQueue.status == "pending",
                PublicationReviewQueue.risk_score >= self.HIGH_RISK_THRESHOLD,
            )
        )
        high_result = await self.db.execute(high_query)
        risk_distribution["high"] = high_result.scalar() or 0

        # TODO: Calculate average review time (requires more complex query)
        average_review_time = None

        return ReviewStatsResponse(
            total_pending=total_pending,
            total_reviewed_today=total_reviewed_today,
            auto_approved_count=auto_approved_count,
            rejected_count=rejected_count,
            average_review_time_minutes=average_review_time,
            risk_distribution=risk_distribution,
        )

    async def auto_approve_low_risk(
        self, threshold: float = 0.3
    ) -> int:
        """
        Auto-approve items below risk threshold.

        Args:
            threshold: Risk score threshold (default: 0.3)

        Returns:
            Number of items auto-approved
        """
        from sqlalchemy import update

        query = (
            update(PublicationReviewQueue)
            .where(
                and_(
                    PublicationReviewQueue.status == "pending",
                    PublicationReviewQueue.risk_score < threshold,
                )
            )
            .values(
                status="auto_approved",
                reviewed_at=datetime.now(timezone.utc),
                reviewer_notes="Auto-approved: risk score below threshold",
            )
        )

        result = await self.db.execute(query)
        await self.db.commit()

        count = result.rowcount
        logger.info(f"Auto-approved {count} low-risk items (threshold={threshold})")
        return count

    async def submit_for_review(
        self,
        target_type: str,
        target_id: str,
        risk_score: float,
        risk_factors: List[str],
        content_preview: Optional[str] = None,
        metadata: Optional[dict] = None,
        threshold: float = 0.3,
    ) -> PublicationReviewQueue:
        """
        Submit content for review with risk-based routing.

        Determines status based on risk_score:
        - score < threshold (0.3): auto_approved
        - score >= threshold: pending (requires human review)

        Args:
            target_type: Type of content (sitrep, summary, alert)
            target_id: UUID string of the target content
            risk_score: Calculated risk score (0.0-1.0)
            risk_factors: List of detected risk factor labels
            content_preview: Preview text of the content
            metadata: Additional metadata dict
            threshold: Risk threshold for auto-approval (default: 0.3)

        Returns:
            Created or updated PublicationReviewQueue item
        """
        from uuid import UUID as PyUUID

        # Determine status based on risk score
        if risk_score < threshold:
            status = "auto_approved"
            reviewed_at = datetime.now(timezone.utc)
            reviewer_notes = f"Auto-approved: risk score {risk_score:.3f} below threshold {threshold}"
        else:
            status = "pending"
            reviewed_at = None
            reviewer_notes = None

        # Prepare risk_factors as JSONB
        risk_factors_json = {"factors": risk_factors}
        if metadata:
            risk_factors_json.update(metadata)

        # Check if item already exists for this target_id
        try:
            target_uuid = PyUUID(target_id)
        except ValueError:
            # Generate new UUID if invalid format
            from uuid import uuid4
            target_uuid = uuid4()
            logger.warning(f"Invalid target_id format '{target_id}', generated new UUID")

        existing_query = select(PublicationReviewQueue).where(
            PublicationReviewQueue.article_id == target_uuid
        )
        existing_result = await self.db.execute(existing_query)
        existing_item = existing_result.scalar_one_or_none()

        if existing_item:
            # Update existing item
            existing_item.target = target_type
            existing_item.content = content_preview or ""
            existing_item.risk_score = risk_score
            existing_item.risk_factors = risk_factors_json
            # Only update status if not already reviewed
            if existing_item.status in ("pending", "auto_approved"):
                existing_item.status = status
                if status == "auto_approved":
                    existing_item.reviewed_at = reviewed_at
                    existing_item.reviewer_notes = reviewer_notes

            await self.db.commit()
            await self.db.refresh(existing_item)

            logger.info(
                f"Updated review item: id={existing_item.id}, target={target_type}, "
                f"risk_score={risk_score}, status={existing_item.status}"
            )
            return existing_item

        # Create new item
        item = PublicationReviewQueue(
            article_id=target_uuid,
            target=target_type,
            content=content_preview or "",
            risk_score=risk_score,
            risk_factors=risk_factors_json,
            status=status,
            reviewed_at=reviewed_at,
            reviewer_notes=reviewer_notes,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        logger.info(
            f"Created review item: id={item.id}, target={target_type}, "
            f"risk_score={risk_score}, status={status}"
        )
        return item

    async def get_recent_pending(
        self,
        limit: int = 5,
    ) -> List[ReviewItemResponse]:
        """
        Get recent pending review items sorted by risk score descending.

        Used by the dashboard to show high-priority items that need attention.

        Args:
            limit: Maximum number of items to return (default: 5)

        Returns:
            List of recent pending review items sorted by risk_score DESC
        """
        query = (
            select(PublicationReviewQueue)
            .where(PublicationReviewQueue.status == "pending")
            .order_by(PublicationReviewQueue.risk_score.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        items = result.scalars().all()

        return [self._model_to_response(item) for item in items]

    async def get_dashboard_data(self) -> dict:
        """
        Get comprehensive dashboard data in a single method.

        Optimized to reduce database round-trips by combining multiple queries.

        Returns:
            Dictionary with stats, recent_items, and risk_distribution
        """
        # Get stats (reuse existing method)
        stats = await self.get_stats()

        # Get recent pending items sorted by risk
        recent_items = await self.get_recent_pending(limit=5)

        return {
            "stats": {
                "total_pending": stats.total_pending,
                "high_risk_count": stats.risk_distribution.get("high", 0),
                "reviewed_today": stats.total_reviewed_today,
                "auto_approved_count": stats.auto_approved_count,
            },
            "recent_items": recent_items,
            "risk_distribution": stats.risk_distribution,
        }

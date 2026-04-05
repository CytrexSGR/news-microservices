# File: services/feed-service/tests/test_review_repository.py
"""
Tests for Review Queue Repository.

Tests CRUD operations for the publication_review_queue table,
with proper field mapping between schema and database model.

DB Model Field Mapping:
- target (DB) <-> target_type (schema)
- article_id (DB) <-> target_id (schema)
- content (DB) <-> content_preview (schema)
- reviewed_by (DB) <-> reviewer_id (schema)
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feed import Feed, FeedItem
from app.models.intelligence import PublicationReviewQueue
from app.schemas.review import (
    ReviewItemCreate,
    ReviewDecisionRequest,
    ReviewDecision,
    ReviewStatus,
)


def generate_content_hash(content: str) -> str:
    """Generate a SHA-256 hash for content."""
    return hashlib.sha256(content.encode()).hexdigest()


@pytest_asyncio.fixture
async def sample_feed_item(db_session: AsyncSession) -> FeedItem:
    """Create a sample feed item for testing review queue items."""
    # First create a feed (required for feed_item FK)
    feed = Feed(
        id=uuid4(),
        name="Test Feed",
        url="https://example.com/feed.xml",
        fetch_interval=3600,
        is_active=True,
    )
    db_session.add(feed)
    await db_session.flush()

    # Create feed item with all required fields
    unique_link = f"https://example.com/article/{uuid4()}"
    item = FeedItem(
        id=uuid4(),
        feed_id=feed.id,
        title="Test Article for Review",
        link=unique_link,
        published_at=datetime.now(timezone.utc),
        content_hash=generate_content_hash(unique_link),  # Required field
    )
    db_session.add(item)
    await db_session.commit()
    return item


@pytest_asyncio.fixture
async def sample_review_item(
    db_session: AsyncSession, sample_feed_item: FeedItem
) -> PublicationReviewQueue:
    """Create a sample review queue item."""
    review_item = PublicationReviewQueue(
        id=uuid4(),
        article_id=sample_feed_item.id,
        target="sitrep",
        content="This is a preview of the content to review.",
        risk_score=0.5,
        risk_factors={"factors": ["ai_generated", "sensitive_topic"]},
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(review_item)
    await db_session.commit()
    await db_session.refresh(review_item)
    return review_item


class TestReviewRepositoryCreate:
    """Test ReviewRepository.add_to_queue method."""

    @pytest.mark.asyncio
    async def test_add_to_queue_creates_item(
        self, db_session: AsyncSession, sample_feed_item: FeedItem
    ):
        """Test creating a review queue item maps schema fields correctly."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        create_data = ReviewItemCreate(
            target_type="sitrep",
            target_id=sample_feed_item.id,
            risk_score=0.45,
            risk_factors=["ai_generated", "market_sensitive"],
            content_preview="Short preview of the content...",
            metadata={"source": "sitrep-service"},
        )

        result = await repo.add_to_queue(create_data)

        assert result is not None
        assert result.id is not None
        # Verify field mapping: schema -> DB
        assert result.target == "sitrep"  # target_type -> target
        assert result.article_id == sample_feed_item.id  # target_id -> article_id
        assert result.content == "Short preview of the content..."  # content_preview -> content
        assert result.risk_score == 0.45
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_add_to_queue_without_optional_fields(
        self, db_session: AsyncSession, sample_feed_item: FeedItem
    ):
        """Test creating item without optional fields."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        create_data = ReviewItemCreate(
            target_type="summary",
            target_id=sample_feed_item.id,
            risk_score=0.3,
        )

        result = await repo.add_to_queue(create_data)

        assert result is not None
        assert result.target == "summary"
        assert result.risk_factors is None
        assert result.content == ""  # Empty string when not provided


class TestReviewRepositoryGet:
    """Test ReviewRepository.get_item method."""

    @pytest.mark.asyncio
    async def test_get_item_returns_response_schema(
        self, db_session: AsyncSession, sample_review_item: PublicationReviewQueue
    ):
        """Test getting an item returns proper schema with field mapping."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        result = await repo.get_item(sample_review_item.id)

        assert result is not None
        # Verify reverse field mapping: DB -> schema
        assert result.target_type == "sitrep"  # target -> target_type
        assert result.target_id == sample_review_item.article_id  # article_id -> target_id
        assert result.content_preview == sample_review_item.content  # content -> content_preview
        assert result.status == ReviewStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_item_not_found_returns_none(
        self, db_session: AsyncSession
    ):
        """Test getting non-existent item returns None."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        result = await repo.get_item(uuid4())

        assert result is None


class TestReviewRepositoryListPending:
    """Test ReviewRepository.list_pending method."""

    @pytest.mark.asyncio
    async def test_list_pending_returns_paginated_response(
        self, db_session: AsyncSession, sample_review_item: PublicationReviewQueue
    ):
        """Test listing pending items returns paginated response."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        result = await repo.list_pending(page=1, page_size=10)

        assert result is not None
        assert hasattr(result, 'items')
        assert hasattr(result, 'total')
        assert hasattr(result, 'pending_count')
        assert hasattr(result, 'high_risk_count')
        assert hasattr(result, 'page')
        assert hasattr(result, 'page_size')
        assert hasattr(result, 'has_more')
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_list_pending_empty_queue(self, db_session: AsyncSession):
        """Test listing when queue is empty."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        result = await repo.list_pending(page=1, page_size=10)

        assert result is not None
        assert result.items == []
        assert result.total == 0
        assert result.pending_count == 0

    @pytest.mark.asyncio
    async def test_list_pending_orders_by_risk_score_desc(
        self, db_session: AsyncSession, sample_feed_item: FeedItem
    ):
        """Test that pending items are ordered by risk_score descending."""
        from app.repositories.review_repository import ReviewRepository

        # Create items with different risk scores
        low_risk = PublicationReviewQueue(
            article_id=sample_feed_item.id,
            target="summary",
            content="Low risk content",
            risk_score=0.2,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        high_risk = PublicationReviewQueue(
            article_id=sample_feed_item.id,
            target="alert",
            content="High risk content",
            risk_score=0.9,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add_all([low_risk, high_risk])
        await db_session.commit()

        repo = ReviewRepository(db_session)
        result = await repo.list_pending(page=1, page_size=10)

        # High risk should come first
        assert len(result.items) >= 2
        scores = [item.risk_score for item in result.items]
        assert scores == sorted(scores, reverse=True), "Items should be sorted by risk_score DESC"


class TestReviewRepositoryUpdateDecision:
    """Test ReviewRepository.update_decision method."""

    @pytest.mark.asyncio
    async def test_update_decision_approve(
        self, db_session: AsyncSession, sample_review_item: PublicationReviewQueue
    ):
        """Test approving a review item."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE,
            reviewer_notes="Content looks accurate and well-sourced.",
        )

        result = await repo.update_decision(
            item_id=sample_review_item.id,
            decision=decision,
            reviewer_id="reviewer-123",
        )

        assert result is not None
        assert result.status == ReviewStatus.APPROVED
        assert result.reviewer_id == "reviewer-123"  # reviewed_by -> reviewer_id
        assert result.reviewer_notes == "Content looks accurate and well-sourced."
        assert result.reviewed_at is not None

    @pytest.mark.asyncio
    async def test_update_decision_reject_with_reason(
        self, db_session: AsyncSession, sample_review_item: PublicationReviewQueue
    ):
        """Test rejecting a review item requires reason."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.REJECT,
            reviewer_notes="Content contains factual errors.",
            rejection_reason="Inaccurate market data cited.",
        )

        result = await repo.update_decision(
            item_id=sample_review_item.id,
            decision=decision,
            reviewer_id="reviewer-456",
        )

        assert result is not None
        assert result.status == ReviewStatus.REJECTED

    @pytest.mark.asyncio
    async def test_update_decision_approve_with_edits(
        self, db_session: AsyncSession, sample_review_item: PublicationReviewQueue
    ):
        """Test approving with edits stores edited content."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE_WITH_EDITS,
            reviewer_notes="Made minor corrections.",
            edited_content={"summary": "Corrected summary text here..."},
        )

        result = await repo.update_decision(
            item_id=sample_review_item.id,
            decision=decision,
            reviewer_id="editor-789",
        )

        assert result is not None
        # APPROVE_WITH_EDITS maps to 'edited' status in DB
        assert result.status == ReviewStatus.EDITED

    @pytest.mark.asyncio
    async def test_update_decision_not_found(
        self, db_session: AsyncSession
    ):
        """Test updating non-existent item returns None."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        decision = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE,
        )

        result = await repo.update_decision(
            item_id=uuid4(),
            decision=decision,
            reviewer_id="reviewer-xxx",
        )

        assert result is None


class TestReviewRepositoryStats:
    """Test ReviewRepository.get_stats method."""

    @pytest.mark.asyncio
    async def test_get_stats_returns_all_metrics(
        self, db_session: AsyncSession, sample_review_item: PublicationReviewQueue
    ):
        """Test getting stats returns all expected metrics."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        result = await repo.get_stats()

        assert result is not None
        assert hasattr(result, 'total_pending')
        assert hasattr(result, 'total_reviewed_today')
        assert hasattr(result, 'auto_approved_count')
        assert hasattr(result, 'rejected_count')
        assert hasattr(result, 'risk_distribution')
        assert result.total_pending >= 1

    @pytest.mark.asyncio
    async def test_get_stats_empty_queue(self, db_session: AsyncSession):
        """Test stats for empty queue."""
        from app.repositories.review_repository import ReviewRepository

        repo = ReviewRepository(db_session)

        result = await repo.get_stats()

        assert result is not None
        assert result.total_pending == 0
        assert result.total_reviewed_today == 0

    @pytest.mark.asyncio
    async def test_get_stats_risk_distribution(
        self, db_session: AsyncSession, sample_feed_item: FeedItem
    ):
        """Test that risk distribution counts items correctly."""
        from app.repositories.review_repository import ReviewRepository

        # Create items with different risk levels
        low_risk = PublicationReviewQueue(
            article_id=sample_feed_item.id,
            target="summary",
            content="Low risk",
            risk_score=0.2,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        medium_risk = PublicationReviewQueue(
            article_id=sample_feed_item.id,
            target="summary",
            content="Medium risk",
            risk_score=0.5,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        high_risk = PublicationReviewQueue(
            article_id=sample_feed_item.id,
            target="alert",
            content="High risk",
            risk_score=0.85,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add_all([low_risk, medium_risk, high_risk])
        await db_session.commit()

        repo = ReviewRepository(db_session)
        result = await repo.get_stats()

        assert result.risk_distribution["low"] >= 1
        assert result.risk_distribution["medium"] >= 1
        assert result.risk_distribution["high"] >= 1


class TestReviewRepositoryAutoApprove:
    """Test ReviewRepository.auto_approve_low_risk method."""

    @pytest.mark.asyncio
    async def test_auto_approve_low_risk_items(
        self, db_session: AsyncSession, sample_feed_item: FeedItem
    ):
        """Test that low-risk items are auto-approved."""
        from app.repositories.review_repository import ReviewRepository

        # Create a low-risk item
        low_risk_item = PublicationReviewQueue(
            article_id=sample_feed_item.id,
            target="summary",
            content="Low risk content for auto-approval",
            risk_score=0.15,  # Below 0.3 threshold
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(low_risk_item)
        await db_session.commit()

        repo = ReviewRepository(db_session)
        count = await repo.auto_approve_low_risk(threshold=0.3)

        assert count >= 1

        # Verify item was auto-approved
        result = await repo.get_item(low_risk_item.id)
        assert result is not None
        assert result.status == ReviewStatus.AUTO_APPROVED

    @pytest.mark.asyncio
    async def test_auto_approve_skips_high_risk_items(
        self, db_session: AsyncSession, sample_feed_item: FeedItem
    ):
        """Test that high-risk items are not auto-approved."""
        from app.repositories.review_repository import ReviewRepository

        # Create a high-risk item
        high_risk_item = PublicationReviewQueue(
            article_id=sample_feed_item.id,
            target="alert",
            content="High risk content - needs human review",
            risk_score=0.8,  # Above threshold
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(high_risk_item)
        await db_session.commit()

        repo = ReviewRepository(db_session)
        await repo.auto_approve_low_risk(threshold=0.3)

        # Verify high-risk item is still pending
        result = await repo.get_item(high_risk_item.id)
        assert result is not None
        assert result.status == ReviewStatus.PENDING

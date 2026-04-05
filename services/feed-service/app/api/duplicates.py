# services/feed-service/app/api/duplicates.py
"""API endpoints for duplicate review management (HITL).

Epic 1.2: Deduplication Pipeline - Task 5
Provides endpoints for human-in-the-loop review of near-duplicate articles.

Endpoints:
- GET /api/v1/duplicates - List pending near-duplicates (requires auth)
- GET /api/v1/duplicates/{id} - Get single candidate with article details
- PUT /api/v1/duplicates/{id} - Submit review decision (requires admin role)
- GET /api/v1/duplicates/stats - Get duplicate detection statistics
"""

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models.feed import DuplicateCandidate, FeedItem
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/duplicates", tags=["duplicates"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class DuplicateCandidateResponse(BaseModel):
    """Response schema for a duplicate candidate."""

    id: UUID
    new_article_id: UUID
    existing_article_id: UUID
    hamming_distance: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DuplicateCandidateDetailResponse(BaseModel):
    """Detailed response schema including article information."""

    id: UUID
    new_article_id: UUID
    new_article_title: Optional[str] = None
    new_article_link: Optional[str] = None
    new_article_description: Optional[str] = None
    existing_article_id: UUID
    existing_article_title: Optional[str] = None
    existing_article_link: Optional[str] = None
    existing_article_description: Optional[str] = None
    hamming_distance: int
    simhash_new: int
    simhash_existing: int
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_decision: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DuplicateListResponse(BaseModel):
    """Paginated duplicate candidates response."""

    items: List[DuplicateCandidateResponse]
    total: int
    page: int
    page_size: int


class ReviewDecision(BaseModel):
    """Schema for duplicate review decision.

    Decisions:
    - keep_both: Both articles are kept (false positive)
    - merge: Articles should be merged (future feature)
    - reject_new: New article is marked as withheld (true duplicate)
    """

    decision: Literal["keep_both", "merge", "reject_new"] = Field(
        ..., description="Review decision for the duplicate candidate"
    )
    notes: Optional[str] = Field(
        None, max_length=1000, description="Optional reviewer notes"
    )


class ReviewResponse(BaseModel):
    """Response after submitting a review decision."""

    status: str
    decision: str
    candidate_id: UUID
    reviewed_at: datetime


class DuplicateStatsResponse(BaseModel):
    """Statistics about duplicate detection."""

    pending_count: int
    reviewed_count: int
    auto_resolved_count: int
    total_count: int


# =============================================================================
# Helper Functions
# =============================================================================

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Extract user info including roles from JWT token.

    The JWT payload contains:
    - sub: user ID
    - roles: list of role names (admin, user, moderator)
    - username: optional username

    Returns dict with user_id and roles for RBAC checks.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract roles from JWT payload (defaults to empty list)
        roles = payload.get("roles", [])

        return {
            "user_id": int(user_id) if str(user_id).isdigit() else 0,
            "roles": roles,
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin_role(user: dict = Depends(get_current_user)) -> dict:
    """Dependency to require admin role for review actions."""
    if "admin" not in user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for review actions",
        )
    return user


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("", response_model=DuplicateListResponse)
async def list_pending_duplicates(
    status_filter: str = Query(
        "pending",
        alias="status",
        description="Filter by status: pending, reviewed, auto_resolved, or all",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List duplicate candidates for review.

    Requires authentication. Returns paginated list of near-duplicate
    candidates that have been flagged for human review.

    Parameters:
    - **status**: Filter by status (pending, reviewed, auto_resolved, all)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    offset = (page - 1) * page_size

    # Build base query
    query = select(DuplicateCandidate)

    # Apply status filter
    if status_filter != "all":
        valid_statuses = ["pending", "reviewed", "auto_resolved"]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses} or 'all'",
            )
        query = query.where(DuplicateCandidate.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(DuplicateCandidate.created_at.desc())
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    candidates = result.scalars().all()

    # Build response
    items = [
        DuplicateCandidateResponse(
            id=c.id,
            new_article_id=c.new_article_id,
            existing_article_id=c.existing_article_id,
            hamming_distance=c.hamming_distance,
            status=c.status,
            created_at=c.created_at,
        )
        for c in candidates
    ]

    return DuplicateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=DuplicateStatsResponse)
async def get_duplicate_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get duplicate detection statistics.

    Requires authentication. Returns counts of duplicate candidates
    grouped by status.
    """
    # Count by status
    pending_result = await db.execute(
        select(func.count()).where(DuplicateCandidate.status == "pending")
    )
    reviewed_result = await db.execute(
        select(func.count()).where(DuplicateCandidate.status == "reviewed")
    )
    auto_resolved_result = await db.execute(
        select(func.count()).where(DuplicateCandidate.status == "auto_resolved")
    )
    total_result = await db.execute(select(func.count(DuplicateCandidate.id)))

    return DuplicateStatsResponse(
        pending_count=pending_result.scalar() or 0,
        reviewed_count=reviewed_result.scalar() or 0,
        auto_resolved_count=auto_resolved_result.scalar() or 0,
        total_count=total_result.scalar() or 0,
    )


@router.get("/{candidate_id}", response_model=DuplicateCandidateDetailResponse)
async def get_duplicate_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single duplicate candidate with article details.

    Requires authentication. Returns detailed information about
    the candidate including both articles' titles and descriptions.
    """
    # Get candidate
    candidate = await db.get(DuplicateCandidate, candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=404, detail=f"Duplicate candidate {candidate_id} not found"
        )

    # Get article details
    new_article = await db.get(FeedItem, candidate.new_article_id)
    existing_article = await db.get(FeedItem, candidate.existing_article_id)

    return DuplicateCandidateDetailResponse(
        id=candidate.id,
        new_article_id=candidate.new_article_id,
        new_article_title=new_article.title if new_article else None,
        new_article_link=new_article.link if new_article else None,
        new_article_description=new_article.description if new_article else None,
        existing_article_id=candidate.existing_article_id,
        existing_article_title=existing_article.title if existing_article else None,
        existing_article_link=existing_article.link if existing_article else None,
        existing_article_description=existing_article.description if existing_article else None,
        hamming_distance=candidate.hamming_distance,
        simhash_new=candidate.simhash_new,
        simhash_existing=candidate.simhash_existing,
        status=candidate.status,
        reviewed_by=candidate.reviewed_by,
        reviewed_at=candidate.reviewed_at,
        review_decision=candidate.review_decision,
        review_notes=candidate.review_notes,
        created_at=candidate.created_at,
    )


@router.put("/{candidate_id}", response_model=ReviewResponse)
async def review_duplicate(
    candidate_id: UUID,
    review: ReviewDecision,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(require_admin_role),
):
    """
    Submit review decision for duplicate candidate.

    Requires admin role. Updates the candidate status and applies
    the decision:

    - **keep_both**: Both articles are kept (marks as reviewed, no action)
    - **merge**: Articles should be merged (future feature, marks as reviewed)
    - **reject_new**: New article is marked as withheld (pub_status='withheld')

    Returns the review result with timestamp.
    """
    # Get candidate
    candidate = await db.get(DuplicateCandidate, candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=404, detail=f"Duplicate candidate {candidate_id} not found"
        )

    # Check if already reviewed
    if candidate.status == "reviewed":
        raise HTTPException(
            status_code=400,
            detail=f"Candidate {candidate_id} has already been reviewed",
        )

    # Update candidate
    now = datetime.now(timezone.utc)
    candidate.status = "reviewed"
    candidate.reviewed_by = current_user.get("user_id")
    candidate.reviewed_at = now
    candidate.review_decision = review.decision
    candidate.review_notes = review.notes

    # Apply decision
    if review.decision == "reject_new":
        new_article = await db.get(FeedItem, candidate.new_article_id)
        if new_article:
            new_article.pub_status = "withheld"
            logger.info(
                f"Article {candidate.new_article_id} marked as withheld "
                f"(duplicate of {candidate.existing_article_id})"
            )
    elif review.decision == "merge":
        # Future feature: implement merge logic
        logger.info(
            f"Merge requested for {candidate.new_article_id} -> "
            f"{candidate.existing_article_id} (not yet implemented)"
        )
    else:
        # keep_both - just mark as reviewed, no action needed
        logger.info(
            f"Keeping both articles: {candidate.new_article_id} and "
            f"{candidate.existing_article_id} (false positive)"
        )

    await db.commit()

    return ReviewResponse(
        status="reviewed",
        decision=review.decision,
        candidate_id=candidate.id,
        reviewed_at=now,
    )

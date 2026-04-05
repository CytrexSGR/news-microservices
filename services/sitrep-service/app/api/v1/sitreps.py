# services/sitrep-service/app/api/v1/sitreps.py
"""REST API endpoints for SITREP reports.

Provides CRUD operations and generation endpoints for intelligence briefings:
- GET /api/v1/sitreps - List SITREPs (paginated)
- GET /api/v1/sitreps/{id} - Get SITREP by ID
- GET /api/v1/sitreps/latest - Get latest SITREP
- POST /api/v1/sitreps/generate - Trigger manual generation

All endpoints require JWT authentication.

Example:
    curl -H "Authorization: Bearer <token>" \\
         http://localhost:8115/api/v1/sitreps?limit=10
"""

import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db, get_story_aggregator
from app.config import settings
from app.constants import REPORT_TIME_RANGES, SITREP_CATEGORIES
from app.repositories.sitrep_repository import SitrepRepository
from app.schemas.sitrep import SitrepResponse
from app.services.sitrep_generator import SitrepGenerator, SitrepGenerationError
from app.services.story_aggregator import StoryAggregator

logger = logging.getLogger(__name__)

router = APIRouter()

# Repository instance (singleton pattern)
_repository = SitrepRepository()


# ============================================================
# Response Models for OpenAPI documentation
# ============================================================


class SitrepListItem(BaseModel):
    """Summary item for SITREP list responses."""

    id: UUID
    report_date: date
    report_type: str
    category: Optional[str] = None
    title: str
    executive_summary: str
    articles_analyzed: int
    confidence_score: Optional[float] = None
    human_reviewed: bool
    generation_model: str
    generation_time_ms: int

    model_config = {"from_attributes": True}


class SitrepListResponse(BaseModel):
    """Paginated list of SITREPs."""

    sitreps: List[SitrepListItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class GenerateRequest(BaseModel):
    """Request body for SITREP generation."""

    report_type: str = Field(
        default="daily",
        description="Type of report: daily, weekly, or breaking",
        pattern="^(daily|weekly|breaking)$",
    )
    category: Optional[str] = Field(
        default=None,
        description="Category filter: conflict, finance, politics, humanitarian, security, technology, other, crypto",
        pattern="^(conflict|finance|politics|humanitarian|security|technology|other|crypto)$",
    )
    report_date: Optional[date] = Field(
        default=None,
        description="Date for the report (defaults to today)",
    )
    top_stories_count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of top stories to include",
    )
    min_cluster_size: int = Field(
        default=3,
        ge=1,
        description="Minimum articles required per cluster",
    )


class GenerateResponse(BaseModel):
    """Response for SITREP generation."""

    success: bool
    message: str
    sitrep_id: Optional[UUID] = None
    sitrep: Optional[SitrepResponse] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str


# ============================================================
# API Endpoints
# ============================================================


@router.get(
    "/sitreps",
    response_model=SitrepListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: {"model": ErrorResponse, "description": "Invalid category"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="List SITREP reports",
    description="Get a paginated list of SITREP reports with optional filtering by type and category.",
)
async def list_sitreps(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    report_type: Optional[str] = Query(
        default=None,
        description="Filter by report type (daily, weekly, breaking)",
        pattern="^(daily|weekly|breaking)$",
    ),
    category: Optional[str] = Query(
        default=None,
        description="Filter by category (conflict, finance, politics, humanitarian, security, technology, other, crypto)",
    ),
) -> SitrepListResponse:
    """
    List SITREP reports with pagination.

    Returns a paginated list of SITREP reports, ordered by creation date descending.
    Optionally filter by report type and/or category.

    Args:
        user_id: Authenticated user ID (from JWT)
        db: Database session
        limit: Maximum number of results (1-100, default 20)
        offset: Number of results to skip (default 0)
        report_type: Optional filter for report type
        category: Optional filter for category (conflict, finance, politics, humanitarian, security, technology, other, crypto)

    Returns:
        SitrepListResponse with paginated SITREP summaries

    Raises:
        HTTPException: 422 if category is invalid
    """
    logger.debug(f"User {user_id} listing SITREPs: limit={limit}, offset={offset}, category={category}")

    # Validate category if provided
    if category is not None and category not in SITREP_CATEGORIES:
        valid_categories = ", ".join(SITREP_CATEGORIES.keys())
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category '{category}'. Valid categories: {valid_categories}",
        )

    try:
        # Get paginated results
        sitreps = await _repository.list_all(
            db,
            limit=limit,
            offset=offset,
            report_type=report_type,
            category=category,
        )

        # Get total count for pagination
        total = await _repository.count(db, report_type=report_type, category=category)

        # Convert to list items (summary view)
        items = [
            SitrepListItem(
                id=s.id,
                report_date=s.report_date,
                report_type=s.report_type,
                category=s.category,
                title=s.title,
                executive_summary=s.executive_summary or "",
                articles_analyzed=s.articles_analyzed,
                confidence_score=s.confidence_score,
                human_reviewed=s.human_reviewed,
                generation_model=s.generation_model,
                generation_time_ms=s.generation_time_ms,
            )
            for s in sitreps
        ]

        return SitrepListResponse(
            sitreps=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    except Exception as e:
        logger.exception(f"Error listing SITREPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list SITREPs: {str(e)}",
        )


@router.get(
    "/sitreps/latest",
    response_model=SitrepResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "No SITREP found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get latest SITREP",
    description="Get the most recently created SITREP report of specified type.",
)
async def get_latest_sitrep(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    report_type: str = Query(
        default="daily",
        description="Report type to get (daily, weekly, breaking)",
        pattern="^(daily|weekly|breaking)$",
    ),
) -> SitrepResponse:
    """
    Get the latest SITREP of specified type.

    Returns the most recently created SITREP report matching the specified type.

    Args:
        user_id: Authenticated user ID (from JWT)
        db: Database session
        report_type: Type of report to retrieve (default: daily)

    Returns:
        Full SitrepResponse for the latest report

    Raises:
        HTTPException: 404 if no SITREP found for the type
    """
    logger.debug(f"User {user_id} getting latest {report_type} SITREP")

    try:
        sitrep = await _repository.get_latest(db, report_type=report_type)

        if sitrep is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {report_type} SITREP found",
            )

        return _repository.model_to_response(sitrep)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting latest SITREP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest SITREP: {str(e)}",
        )


@router.get(
    "/sitreps/{sitrep_id}",
    response_model=SitrepResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "SITREP not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get SITREP by ID",
    description="Get a specific SITREP report by its UUID.",
)
async def get_sitrep_by_id(
    sitrep_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SitrepResponse:
    """
    Get a SITREP by its ID.

    Retrieves the full SITREP report including content, entities,
    and generation metadata.

    Args:
        sitrep_id: UUID of the SITREP to retrieve
        user_id: Authenticated user ID (from JWT)
        db: Database session

    Returns:
        Full SitrepResponse

    Raises:
        HTTPException: 404 if SITREP not found
    """
    logger.debug(f"User {user_id} getting SITREP {sitrep_id}")

    try:
        sitrep = await _repository.get_by_id(db, sitrep_id)

        if sitrep is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SITREP {sitrep_id} not found",
            )

        return _repository.model_to_response(sitrep)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting SITREP {sitrep_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SITREP: {str(e)}",
        )


@router.post(
    "/sitreps/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Generate SITREP",
    description="Trigger manual SITREP generation from current aggregated stories.",
)
async def generate_sitrep(
    request: GenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    aggregator: StoryAggregator = Depends(get_story_aggregator),
) -> GenerateResponse:
    """
    Trigger manual SITREP generation.

    Generates a new SITREP from the currently aggregated story clusters.
    Uses the OpenAI API to create the intelligence briefing.

    Args:
        request: Generation parameters
        user_id: Authenticated user ID (from JWT)
        db: Database session
        aggregator: Story aggregator with current clusters

    Returns:
        GenerateResponse with created SITREP

    Raises:
        HTTPException: 400 if not enough stories available
        HTTPException: 503 if aggregator not available
    """
    logger.info(
        f"User {user_id} triggering {request.report_type} SITREP generation"
        f" (category={request.category})"
    )

    try:
        # Determine max_age_hours from report_type
        max_age_hours = REPORT_TIME_RANGES.get(request.report_type)
        is_breaking_only = request.report_type == "breaking"

        # Get top stories from aggregator with filters
        stories = await aggregator.get_top_stories(
            limit=request.top_stories_count,
            min_article_count=request.min_cluster_size,
            max_age_hours=max_age_hours,
            category=request.category,
            is_breaking_only=is_breaking_only,
        )

        if not stories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No stories available for SITREP generation. "
                "Ensure cluster events are being received.",
            )

        logger.info(f"Found {len(stories)} stories for SITREP generation")

        # Generate SITREP
        generator = SitrepGenerator()
        sitrep = await generator.generate(
            stories=stories,
            report_type=request.report_type,
            report_date=request.report_date or date.today(),
            category=request.category,
        )

        # Save to database
        saved = await _repository.save(db, sitrep)
        logger.info(f"Saved SITREP {saved.id}")

        return GenerateResponse(
            success=True,
            message=f"Successfully generated {request.report_type} SITREP "
            f"from {len(stories)} stories",
            sitrep_id=saved.id,
            sitrep=_repository.model_to_response(saved),
        )

    except HTTPException:
        raise
    except SitrepGenerationError as e:
        logger.error(f"SITREP generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SITREP generation failed: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"Unexpected error during SITREP generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.patch(
    "/sitreps/{sitrep_id}/review",
    response_model=SitrepResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "SITREP not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Mark SITREP as reviewed",
    description="Mark a SITREP as human-reviewed.",
)
async def mark_sitrep_reviewed(
    sitrep_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    reviewed: bool = Query(default=True, description="Review status to set"),
) -> SitrepResponse:
    """
    Mark a SITREP as human-reviewed.

    Updates the human_reviewed flag on the specified SITREP.

    Args:
        sitrep_id: UUID of the SITREP to update
        user_id: Authenticated user ID (from JWT)
        db: Database session
        reviewed: Review status to set (default True)

    Returns:
        Updated SitrepResponse

    Raises:
        HTTPException: 404 if SITREP not found
    """
    logger.info(f"User {user_id} marking SITREP {sitrep_id} as reviewed={reviewed}")

    try:
        sitrep = await _repository.mark_reviewed(db, sitrep_id, reviewed)

        if sitrep is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SITREP {sitrep_id} not found",
            )

        return _repository.model_to_response(sitrep)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error marking SITREP reviewed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update SITREP: {str(e)}",
        )


@router.delete(
    "/sitreps/{sitrep_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "SITREP not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Delete SITREP",
    description="Delete a SITREP report by ID.",
)
async def delete_sitrep(
    sitrep_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a SITREP by ID.

    Permanently removes the specified SITREP from the database.

    Args:
        sitrep_id: UUID of the SITREP to delete
        user_id: Authenticated user ID (from JWT)
        db: Database session

    Raises:
        HTTPException: 404 if SITREP not found
    """
    logger.info(f"User {user_id} deleting SITREP {sitrep_id}")

    try:
        deleted = await _repository.delete(db, sitrep_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SITREP {sitrep_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting SITREP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete SITREP: {str(e)}",
        )

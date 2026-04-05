"""Research Run API endpoints."""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.schemas.research import (
    ResearchRunCreate, ResearchRunResponse, ResearchRunList,
    ResearchRunStatus
)
from app.services.run_service import run_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/", response_model=ResearchRunResponse, status_code=status.HTTP_201_CREATED)
async def create_research_run(
    run_data: ResearchRunCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new research run from a template."""
    try:
        run = await run_service.create_run(
            db=db,
            user_id=current_user.user_id,
            template_id=run_data.template_id,
            parameters=run_data.parameters,
            model_name=run_data.model_name,
            depth=run_data.depth,
            scheduled_at=run_data.scheduled_at,
            is_recurring=run_data.is_recurring,
            recurrence_pattern=run_data.recurrence_pattern,
            metadata=run_data.metadata
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create research run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create research run"
        )


@router.get("/{run_id}", response_model=ResearchRunResponse)
async def get_research_run(
    run_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific research run."""
    run = await run_service.get_run(db, run_id, current_user.user_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/{run_id}/status", response_model=ResearchRunStatus)
async def get_run_status(
    run_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current status of a research run."""
    status_data = await run_service.get_run_status(db, run_id, current_user.user_id)
    if not status_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return ResearchRunStatus(**status_data)


@router.get("/", response_model=ResearchRunList)
async def list_research_runs(
    status: str = Query(None, regex="^(pending|running|completed|failed|cancelled)$"),
    template_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List research runs with pagination."""
    skip = (page - 1) * page_size
    runs, total = await run_service.list_runs(
        db, current_user.user_id, status, template_id, skip, page_size
    )

    return ResearchRunList(
        runs=runs,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(skip + len(runs)) < total
    )


@router.post("/{run_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_research_run(
    run_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending or running research run."""
    try:
        success = await run_service.cancel_run(db, run_id, current_user.user_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel research run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel research run"
        )


@router.get("/template/{template_id}", response_model=list[ResearchRunResponse])
async def get_template_runs(
    template_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get research runs for a specific template."""
    runs, _ = await run_service.list_runs(
        db, current_user.user_id, template_id=template_id, limit=limit
    )
    return runs

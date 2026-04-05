"""Research API endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.models.research import ResearchTask
from app.schemas.research import (
    ResearchTaskCreate, ResearchTaskBatchCreate, ResearchTaskResponse,
    ResearchTaskList, UsageStats
)
from app.services.research import research_service

# Import shared contracts for validation
try:
    from shared.contracts import validate_research_request
    SHARED_CONTRACTS_AVAILABLE = True
except ImportError:
    SHARED_CONTRACTS_AVAILABLE = False
    logging.warning("shared.contracts not available - using local validation only")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_research_task(
    task_data: ResearchTaskCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new research task."""
    try:
        # RAW BODY DIAGNOSTIC: Log exactly what arrives before Pydantic parsing
        from fastapi import Request
        logger.info(f"[RESEARCH] Received task creation request")
        logger.info(f"[RESEARCH] task_data.research_function: {task_data.research_function}")
        logger.info(f"[RESEARCH] has function_parameters: {task_data.function_parameters is not None}")

        # GUARDRAIL 1: Fail-fast validation using shared contracts (if available)
        # This catches contract violations before they propagate into the system
        if SHARED_CONTRACTS_AVAILABLE:
            try:
                validate_research_request(task_data.model_dump())
                logger.info("[RESEARCH GUARDRAIL] ✓ Shared contract validation passed")
            except ValueError as e:
                logger.warning(f"[RESEARCH GUARDRAIL] ✗ Contract violation: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request contract violation: {str(e)}"
                )

        # GUARDRAIL 2: Local validation fallback (if shared contracts unavailable)
        # This prevents silent creation of standard tasks when specialized function was intended
        # Root cause from incident 2025-10-18-20: function_parameters were dropped silently
        if hasattr(task_data, 'function_parameters') and task_data.function_parameters and not task_data.research_function:
            logger.warning("[RESEARCH GUARDRAIL] function_parameters present but research_function missing - rejecting")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "function_parameters provided but research_function is missing. "
                    "Valid values: feed_source_assessment, fact_check, trend_analysis"
                )
            )

        # Handle specialized research functions
        if task_data.research_function:
            from app.services.specialized_functions import FeedSourceAssessment

            if task_data.research_function == 'feed_source_assessment':
                logger.info("Creating FeedSourceAssessment function")
                function = FeedSourceAssessment()
                logger.info(f"FeedSourceAssessment created, output_schema: {function.output_schema}")
                # Merge function_parameters with feed/article IDs
                params = {
                    **(task_data.function_parameters or {}),
                    'feed_id': task_data.feed_id,
                    'legacy_feed_id': task_data.legacy_feed_id,
                    'article_id': task_data.article_id,
                    'legacy_article_id': task_data.legacy_article_id,
                }
                logger.info(f"Calling function.execute with params: {list(params.keys())}")
                result = await function.execute(
                    db=db,
                    user_id=current_user.user_id,
                    **params
                )
                logger.info(f"function.execute returned, task_id: {result.get('task_id')}")
                # Get the created task
                task = db.query(ResearchTask).filter(ResearchTask.id == result['task_id']).first()
                return task

        # Standard research task
        task = await research_service.create_research_task(
            db=db,
            user_id=current_user.user_id,
            query=task_data.query,
            model_name=task_data.model_name,
            depth=task_data.depth,
            feed_id=task_data.feed_id,
            legacy_feed_id=task_data.legacy_feed_id,
            article_id=task_data.article_id,
            legacy_article_id=task_data.legacy_article_id,
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create research task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create research task"
        )


@router.get("/{task_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    task_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific research task."""
    task = await research_service.get_task(db, task_id, current_user.user_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # DEBUG: Check what we're returning
    logger.info(f"[DEBUG GET {task_id}] Task status: {task.status}")
    logger.info(f"[DEBUG GET {task_id}] Has structured_data attr: {hasattr(task, 'structured_data')}")
    logger.info(f"[DEBUG GET {task_id}] structured_data is None: {task.structured_data is None}")
    logger.info(f"[DEBUG GET {task_id}] structured_data type: {type(task.structured_data)}")
    if task.structured_data:
        logger.info(f"[DEBUG GET {task_id}] structured_data keys: {list(task.structured_data.keys()) if isinstance(task.structured_data, dict) else 'not a dict'}")

    return task


@router.get("/", response_model=ResearchTaskList)
async def list_research_tasks(
    status: Optional[str] = Query(None, regex="^(pending|processing|completed|failed)$"),
    feed_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List research tasks with pagination."""
    skip = (page - 1) * page_size
    tasks, total = await research_service.list_tasks(
        db, current_user.user_id, status, feed_id, skip, page_size
    )

    return ResearchTaskList(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(skip + len(tasks)) < total
    )


@router.post("/batch", response_model=list[ResearchTaskResponse])
async def batch_research_tasks(
    batch_data: ResearchTaskBatchCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple research tasks."""
    tasks = []
    for query in batch_data.queries:
        try:
            task = await research_service.create_research_task(
                db=db,
                user_id=current_user.user_id,
                query=query,
                model_name=batch_data.model_name,
                depth=batch_data.depth,
                feed_id=batch_data.feed_id,
                legacy_feed_id=batch_data.legacy_feed_id,
            )
            tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to create task for query '{query}': {e}")
    
    return tasks


@router.get("/feed/{feed_id}", response_model=list[ResearchTaskResponse])
async def get_feed_research_tasks(
    feed_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get research tasks for a specific feed."""
    tasks, _ = await research_service.list_tasks(
        db, current_user.user_id, feed_id=feed_id, limit=limit
    )
    return tasks


@router.get("/history", response_model=ResearchTaskList)
async def get_research_history(
    days: int = Query(30, ge=1, le=365),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get research history."""
    skip = (page - 1) * page_size
    tasks, total = await research_service.list_tasks(
        db, current_user.user_id, skip=skip, limit=page_size
    )
    
    return ResearchTaskList(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(skip + len(tasks)) < total
    )


@router.get("/stats", response_model=UsageStats)
async def get_usage_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics."""
    stats = await research_service.get_usage_stats(db, current_user.user_id, days)
    return UsageStats(**stats)

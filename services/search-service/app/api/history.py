"""
Search history API endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.search import SearchHistory
from app.schemas.search import SearchHistoryResponse, SearchHistoryItem

router = APIRouter()


@router.get("", response_model=SearchHistoryResponse)
async def get_search_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get search history for current user.

    Args:
        page: Page number
        page_size: Results per page

    Returns:
        SearchHistoryResponse: Search history
    """
    user_id = current_user['user_id']

    # Get total count
    count_stmt = select(func.count()).select_from(SearchHistory).where(
        SearchHistory.user_id == user_id
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    stmt = select(SearchHistory).where(
        SearchHistory.user_id == user_id
    ).order_by(
        SearchHistory.created_at.desc()
    ).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    history_items = result.scalars().all()

    return SearchHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[SearchHistoryItem.model_validate(item) for item in history_items]
    )


@router.delete("", status_code=204)
async def clear_search_history(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Clear all search history for current user.
    """
    user_id = current_user['user_id']

    stmt = select(SearchHistory).where(SearchHistory.user_id == user_id)
    result = await db.execute(stmt)
    history_items = result.scalars().all()

    for item in history_items:
        await db.delete(item)

    await db.commit()

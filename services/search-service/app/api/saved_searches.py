"""
Saved searches API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.saved_search_service import SavedSearchService
from app.schemas.search import (
    SavedSearchCreate, SavedSearchUpdate,
    SavedSearchResponse, SavedSearchListResponse,
    SearchResponse
)

router = APIRouter()


@router.post("", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    data: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a saved search.

    Args:
        data: Saved search data

    Returns:
        SavedSearchResponse: Created saved search
    """
    service = SavedSearchService(db)
    return await service.create_saved_search(current_user['user_id'], data)


@router.get("", response_model=SavedSearchListResponse)
async def list_saved_searches(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all saved searches for current user.

    Returns:
        SavedSearchListResponse: List of saved searches
    """
    service = SavedSearchService(db)
    return await service.list_saved_searches(current_user['user_id'])


@router.get("/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a saved search by ID.

    Args:
        search_id: Saved search ID

    Returns:
        SavedSearchResponse: Saved search

    Raises:
        HTTPException: 404 if not found
    """
    service = SavedSearchService(db)
    saved_search = await service.get_saved_search(current_user['user_id'], search_id)

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return saved_search


@router.put("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: int,
    data: SavedSearchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a saved search.

    Args:
        search_id: Saved search ID
        data: Update data

    Returns:
        SavedSearchResponse: Updated saved search

    Raises:
        HTTPException: 404 if not found
    """
    service = SavedSearchService(db)
    saved_search = await service.update_saved_search(current_user['user_id'], search_id, data)

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    return saved_search


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a saved search.

    Args:
        search_id: Saved search ID

    Raises:
        HTTPException: 404 if not found
    """
    service = SavedSearchService(db)
    deleted = await service.delete_saved_search(current_user['user_id'], search_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )


@router.post("/{search_id}/run", response_model=SearchResponse)
async def run_saved_search(
    search_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Run a saved search and return results.

    Args:
        search_id: Saved search ID
        page: Page number (default: 1)
        page_size: Results per page (default: 20)

    Returns:
        SearchResponse: Search results

    Raises:
        HTTPException: 404 if saved search not found
    """
    service = SavedSearchService(db)
    saved_search = await service.get_saved_search(current_user['user_id'], search_id)

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )

    # Run the search with saved parameters
    from app.services.search_service import SearchService
    from app.schemas.search import SearchRequest, SearchFilters

    # Build filters from saved search
    filters = None
    if saved_search.filters:
        filters = SearchFilters(**saved_search.filters)

    search_request = SearchRequest(
        query=saved_search.query,
        page=page,
        page_size=page_size,
        filters=filters,
    )

    search_service = SearchService(db)
    result = await search_service.search(search_request, current_user['user_id'])

    # Update last run time
    await service.update_last_run(current_user['user_id'], search_id)

    return result

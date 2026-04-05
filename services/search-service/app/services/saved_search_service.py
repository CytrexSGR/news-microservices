"""
Saved search service
"""
import json
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import SavedSearch
from app.schemas.search import (
    SavedSearchCreate, SavedSearchUpdate,
    SavedSearchResponse, SavedSearchListResponse
)

logger = logging.getLogger(__name__)


class SavedSearchService:
    """Service for managing saved searches"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_saved_search(
        self,
        user_id: str,
        data: SavedSearchCreate
    ) -> SavedSearchResponse:
        """
        Create a saved search.

        Args:
            user_id: User ID
            data: Saved search data

        Returns:
            SavedSearchResponse: Created saved search
        """
        saved_search = SavedSearch(
            user_id=user_id,
            name=data.name,
            query=data.query,
            filters=json.dumps(data.filters.model_dump()) if data.filters else None,
            notifications_enabled=data.notifications_enabled,
        )

        self.db.add(saved_search)
        await self.db.commit()
        await self.db.refresh(saved_search)

        return SavedSearchResponse.model_validate(saved_search)

    async def get_saved_search(
        self,
        user_id: str,
        search_id: int
    ) -> Optional[SavedSearchResponse]:
        """
        Get a saved search by ID.

        Args:
            user_id: User ID
            search_id: Saved search ID

        Returns:
            Optional[SavedSearchResponse]: Saved search or None
        """
        stmt = select(SavedSearch).where(
            and_(
                SavedSearch.id == search_id,
                SavedSearch.user_id == user_id
            )
        )

        result = await self.db.execute(stmt)
        saved_search = result.scalar_one_or_none()

        if saved_search:
            return SavedSearchResponse.model_validate(saved_search)

        return None

    async def list_saved_searches(
        self,
        user_id: str
    ) -> SavedSearchListResponse:
        """
        List all saved searches for a user.

        Args:
            user_id: User ID

        Returns:
            SavedSearchListResponse: List of saved searches
        """
        stmt = select(SavedSearch).where(
            SavedSearch.user_id == user_id
        ).order_by(SavedSearch.created_at.desc())

        result = await self.db.execute(stmt)
        saved_searches = result.scalars().all()

        return SavedSearchListResponse(
            total=len(saved_searches),
            items=[SavedSearchResponse.model_validate(s) for s in saved_searches]
        )

    async def update_saved_search(
        self,
        user_id: str,
        search_id: int,
        data: SavedSearchUpdate
    ) -> Optional[SavedSearchResponse]:
        """
        Update a saved search.

        Args:
            user_id: User ID
            search_id: Saved search ID
            data: Update data

        Returns:
            Optional[SavedSearchResponse]: Updated saved search or None
        """
        stmt = select(SavedSearch).where(
            and_(
                SavedSearch.id == search_id,
                SavedSearch.user_id == user_id
            )
        )

        result = await self.db.execute(stmt)
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            return None

        # Update fields
        if data.name is not None:
            saved_search.name = data.name
        if data.query is not None:
            saved_search.query = data.query
        if data.filters is not None:
            saved_search.filters = json.dumps(data.filters.model_dump())
        if data.notifications_enabled is not None:
            saved_search.notifications_enabled = data.notifications_enabled

        saved_search.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(saved_search)

        return SavedSearchResponse.model_validate(saved_search)

    async def delete_saved_search(
        self,
        user_id: str,
        search_id: int
    ) -> bool:
        """
        Delete a saved search.

        Args:
            user_id: User ID
            search_id: Saved search ID

        Returns:
            bool: True if deleted, False if not found
        """
        stmt = select(SavedSearch).where(
            and_(
                SavedSearch.id == search_id,
                SavedSearch.user_id == user_id
            )
        )

        result = await self.db.execute(stmt)
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            return False

        await self.db.delete(saved_search)
        await self.db.commit()

        return True

    async def update_last_run(
        self,
        user_id: str,
        search_id: int
    ) -> bool:
        """
        Update the last run timestamp for a saved search.

        Args:
            user_id: User ID
            search_id: Saved search ID

        Returns:
            bool: True if updated, False if not found
        """
        stmt = select(SavedSearch).where(
            and_(
                SavedSearch.id == search_id,
                SavedSearch.user_id == user_id
            )
        )

        result = await self.db.execute(stmt)
        saved_search = result.scalar_one_or_none()

        if not saved_search:
            return False

        saved_search.updated_at = datetime.utcnow()
        await self.db.commit()

        return True

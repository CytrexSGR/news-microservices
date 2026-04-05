"""Repository for SITREP persistence.

Implements the repository pattern for CRUD operations on SITREP reports.
Uses SQLAlchemy 2.0 async patterns for database access.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sitrep import SitrepReport
from app.schemas.sitrep import SitrepResponse

logger = logging.getLogger(__name__)


def _serialize_for_json(obj: Any) -> Any:
    """
    Recursively serialize objects for JSON storage.

    Converts UUID and datetime objects to strings for JSONB columns.

    Args:
        obj: Object to serialize (dict, list, or primitive)

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    return obj


class SitrepRepository:
    """
    Repository for SITREP database operations.

    Provides CRUD operations for the sitrep_reports table
    using SQLAlchemy 2.0 async patterns.

    Methods:
        save: Create a new SITREP record
        get_by_id: Retrieve SITREP by UUID
        get_latest: Get most recent SITREP by type
        get_by_date_range: Query SITREPs within date range
        get_by_date: Get SITREPs for a specific date
        list_all: List all SITREPs with pagination
        mark_reviewed: Mark SITREP as human-reviewed
        delete: Remove a SITREP record
    """

    async def save(
        self,
        session: AsyncSession,
        sitrep: SitrepResponse,
    ) -> SitrepReport:
        """
        Save a SITREP to the database.

        Creates a new SitrepReport record from the SitrepResponse schema.

        Args:
            session: Async database session
            sitrep: SITREP response schema to persist

        Returns:
            Created SitrepReport model instance

        Raises:
            SQLAlchemyError: On database errors
        """
        # Serialize key_developments to JSON-safe dicts
        key_developments_json = None
        if sitrep.key_developments:
            key_developments_json = [
                _serialize_for_json(kd.model_dump()) for kd in sitrep.key_developments
            ]

        # Convert schema to model with JSON-safe values
        db_sitrep = SitrepReport(
            id=sitrep.id,
            report_date=sitrep.report_date,
            report_type=sitrep.report_type,
            category=sitrep.category,
            title=sitrep.title,
            executive_summary=sitrep.executive_summary,
            content_markdown=sitrep.content_markdown,
            content_html=sitrep.content_html,
            top_stories=_serialize_for_json(sitrep.top_stories),
            key_entities=_serialize_for_json(sitrep.key_entities),
            sentiment_summary=_serialize_for_json(sitrep.sentiment_summary),
            emerging_signals=_serialize_for_json(sitrep.emerging_signals),
            key_developments=key_developments_json,
            generation_model=sitrep.generation_model,
            generation_time_ms=sitrep.generation_time_ms,
            prompt_tokens=sitrep.prompt_tokens,
            completion_tokens=sitrep.completion_tokens,
            articles_analyzed=sitrep.articles_analyzed,
            confidence_score=sitrep.confidence_score,
            human_reviewed=sitrep.human_reviewed,
        )

        session.add(db_sitrep)
        await session.commit()
        await session.refresh(db_sitrep)

        logger.info(f"Saved SITREP: {db_sitrep.id} ({db_sitrep.report_type})")
        return db_sitrep

    async def get_by_id(
        self,
        session: AsyncSession,
        sitrep_id: UUID,
    ) -> Optional[SitrepReport]:
        """
        Retrieve a SITREP by its UUID.

        Args:
            session: Async database session
            sitrep_id: UUID of the SITREP to retrieve

        Returns:
            SitrepReport if found, None otherwise
        """
        stmt = select(SitrepReport).where(SitrepReport.id == sitrep_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest(
        self,
        session: AsyncSession,
        report_type: str = "daily",
    ) -> Optional[SitrepReport]:
        """
        Get the most recent SITREP of specified type.

        Args:
            session: Async database session
            report_type: Type filter (daily, weekly, breaking)

        Returns:
            Most recent SitrepReport or None
        """
        stmt = (
            select(SitrepReport)
            .where(SitrepReport.report_type == report_type)
            .order_by(desc(SitrepReport.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        report_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[SitrepReport]:
        """
        Query SITREPs within a date range.

        Args:
            session: Async database session
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            report_type: Optional type filter
            limit: Maximum results to return

        Returns:
            List of SitrepReport records
        """
        conditions = [
            SitrepReport.report_date >= start_date,
            SitrepReport.report_date <= end_date,
        ]

        if report_type:
            conditions.append(SitrepReport.report_type == report_type)

        stmt = (
            select(SitrepReport)
            .where(and_(*conditions))
            .order_by(desc(SitrepReport.report_date), desc(SitrepReport.created_at))
            .limit(limit)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_date(
        self,
        session: AsyncSession,
        report_date: date,
        report_type: Optional[str] = None,
    ) -> List[SitrepReport]:
        """
        Get all SITREPs for a specific date.

        Args:
            session: Async database session
            report_date: Specific date to query
            report_type: Optional type filter

        Returns:
            List of SitrepReport records for that date
        """
        return await self.get_by_date_range(
            session,
            start_date=report_date,
            end_date=report_date,
            report_type=report_type,
        )

    async def list_all(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        report_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[SitrepReport]:
        """
        List all SITREPs with pagination.

        Args:
            session: Async database session
            limit: Maximum records to return
            offset: Number of records to skip
            report_type: Optional type filter
            category: Optional category filter (politics, finance, etc.)

        Returns:
            List of SitrepReport records
        """
        stmt = select(SitrepReport)

        if report_type:
            stmt = stmt.where(SitrepReport.report_type == report_type)

        if category:
            stmt = stmt.where(SitrepReport.category == category)

        stmt = (
            stmt.order_by(desc(SitrepReport.created_at)).offset(offset).limit(limit)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def mark_reviewed(
        self,
        session: AsyncSession,
        sitrep_id: UUID,
        reviewed: bool = True,
    ) -> Optional[SitrepReport]:
        """
        Mark a SITREP as human-reviewed.

        Args:
            session: Async database session
            sitrep_id: UUID of SITREP to update
            reviewed: Review status to set

        Returns:
            Updated SitrepReport or None if not found
        """
        sitrep = await self.get_by_id(session, sitrep_id)
        if sitrep is None:
            return None

        sitrep.human_reviewed = reviewed
        await session.commit()
        await session.refresh(sitrep)

        logger.info(f"Marked SITREP {sitrep_id} as reviewed={reviewed}")
        return sitrep

    async def delete(
        self,
        session: AsyncSession,
        sitrep_id: UUID,
    ) -> bool:
        """
        Delete a SITREP by ID.

        Args:
            session: Async database session
            sitrep_id: UUID of SITREP to delete

        Returns:
            True if deleted, False if not found
        """
        sitrep = await self.get_by_id(session, sitrep_id)
        if sitrep is None:
            return False

        await session.delete(sitrep)
        await session.commit()

        logger.info(f"Deleted SITREP: {sitrep_id}")
        return True

    async def count(
        self,
        session: AsyncSession,
        report_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """
        Count total SITREP records.

        Args:
            session: Async database session
            report_type: Optional type filter
            category: Optional category filter (politics, finance, etc.)

        Returns:
            Count of matching records
        """
        from sqlalchemy import func as sqlfunc

        stmt = select(sqlfunc.count(SitrepReport.id))

        if report_type:
            stmt = stmt.where(SitrepReport.report_type == report_type)

        if category:
            stmt = stmt.where(SitrepReport.category == category)

        result = await session.execute(stmt)
        return result.scalar() or 0

    def model_to_response(self, model: SitrepReport) -> SitrepResponse:
        """
        Convert a SitrepReport model to SitrepResponse schema.

        Args:
            model: SQLAlchemy model instance

        Returns:
            Pydantic SitrepResponse schema
        """
        from app.schemas.sitrep import KeyDevelopment

        key_developments = []
        if model.key_developments:
            key_developments = [
                KeyDevelopment(**kd) for kd in model.key_developments
            ]

        # Ensure key_entities is always a list (DB may have {} for empty)
        key_entities = model.key_entities
        if not isinstance(key_entities, list):
            key_entities = [] if not key_entities else list(key_entities.values()) if isinstance(key_entities, dict) else []

        return SitrepResponse(
            id=model.id,
            report_date=model.report_date,
            report_type=model.report_type,
            category=model.category,
            title=model.title,
            executive_summary=model.executive_summary or "",
            content_markdown=model.content_markdown,
            content_html=model.content_html,
            key_developments=key_developments,
            top_stories=model.top_stories,
            key_entities=key_entities,
            sentiment_summary=model.sentiment_summary,
            emerging_signals=model.emerging_signals,
            generation_model=model.generation_model,
            generation_time_ms=model.generation_time_ms,
            prompt_tokens=model.prompt_tokens,
            completion_tokens=model.completion_tokens,
            articles_analyzed=model.articles_analyzed,
            confidence_score=model.confidence_score,
            human_reviewed=model.human_reviewed,
            created_at=model.created_at,
        )

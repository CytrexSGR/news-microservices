"""Event logging service for entity merge tracking."""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import EntityMergeEvent

logger = logging.getLogger(__name__)


class EventLogger:
    """Logs entity merge events to PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_merge_event(
        self,
        entity_name: str,
        entity_type: str,
        canonical_id: int,
        merge_method: str,
        confidence: float,
        source_entity: str,
        target_entity: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EntityMergeEvent:
        """
        Log entity merge event.

        Args:
            entity_name: Name of the entity being merged
            entity_type: Type of entity (PERSON, ORGANIZATION, LOCATION, etc.)
            canonical_id: ID of the canonical entity
            merge_method: Method used for merging (exact, fuzzy, semantic, wikidata)
            confidence: Confidence score of the merge (0.0 - 1.0)
            source_entity: Source entity name (being merged)
            target_entity: Target canonical entity name
            metadata: Optional additional metadata as dict

        Returns:
            EntityMergeEvent: The created merge event

        Raises:
            Exception: If logging fails
        """
        try:
            event = EntityMergeEvent(
                event_type="merge",
                entity_name=entity_name,
                entity_type=entity_type,
                canonical_id=canonical_id,
                merge_method=merge_method,
                confidence=confidence,
                source_entity=source_entity,
                target_entity=target_entity,
                event_metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.utcnow()
            )

            self.session.add(event)
            await self.session.commit()
            await self.session.refresh(event)

            logger.info(
                f"Logged merge event: {source_entity} -> {target_entity} "
                f"(method={merge_method}, confidence={confidence:.2f})"
            )
            return event

        except Exception as e:
            logger.error(f"Failed to log merge event: {e}")
            await self.session.rollback()
            raise

    async def log_alias_added(
        self,
        entity_name: str,
        entity_type: str,
        canonical_id: int,
        alias: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EntityMergeEvent:
        """
        Log alias addition event.

        Args:
            entity_name: Name of the canonical entity
            entity_type: Type of entity
            canonical_id: ID of the canonical entity
            alias: Alias being added
            metadata: Optional additional metadata

        Returns:
            EntityMergeEvent: The created event

        Raises:
            Exception: If logging fails
        """
        try:
            event = EntityMergeEvent(
                event_type="alias_added",
                entity_name=entity_name,
                entity_type=entity_type,
                canonical_id=canonical_id,
                merge_method=None,
                confidence=None,
                source_entity=alias,
                target_entity=entity_name,
                event_metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.utcnow()
            )

            self.session.add(event)
            await self.session.commit()
            await self.session.refresh(event)

            logger.info(f"Logged alias addition: {alias} -> {entity_name}")
            return event

        except Exception as e:
            logger.error(f"Failed to log alias addition: {e}")
            await self.session.rollback()
            raise

"""Event logging service for Knowledge Graph operations."""
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import KnowledgeGraphEvent

logger = logging.getLogger(__name__)


class EventLogger:
    """Service for logging Knowledge Graph events."""

    @staticmethod
    async def log_enrichment(
        db: AsyncSession,
        entity1_name: str,
        entity2_name: str,
        relationship_type: str,
        old_confidence: Optional[float],
        new_confidence: float,
        enrichment_source: str,
        enrichment_summary: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> KnowledgeGraphEvent:
        """
        Log an enrichment operation.

        Args:
            db: Database session
            entity1_name: First entity name
            entity2_name: Second entity name
            relationship_type: Type of relationship
            old_confidence: Previous confidence score (if any)
            new_confidence: New confidence score
            enrichment_source: Source of enrichment (wikipedia, perplexity, manual)
            enrichment_summary: Brief description of what changed
            user_id: User ID if manual enrichment

        Returns:
            Created event record
        """
        event = KnowledgeGraphEvent(
            timestamp=datetime.utcnow(),
            event_type="enrichment_applied",
            entity1_name=entity1_name,
            entity2_name=entity2_name,
            relationship_type=relationship_type,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            enrichment_source=enrichment_source,
            enrichment_summary=enrichment_summary,
            user_id=user_id
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)

        logger.info(
            f"Enrichment logged: {entity1_name} -> {entity2_name} "
            f"({relationship_type}), confidence: {old_confidence} -> {new_confidence}"
        )

        return event

    @staticmethod
    async def log_relationship_created(
        db: AsyncSession,
        entity1_name: str,
        entity2_name: str,
        relationship_type: str,
        confidence: float,
        source: str = "automatic"
    ) -> KnowledgeGraphEvent:
        """
        Log a new relationship creation.

        Args:
            db: Database session
            entity1_name: First entity name
            entity2_name: Second entity name
            relationship_type: Type of relationship
            confidence: Confidence score
            source: Source of relationship (automatic, manual, enriched)

        Returns:
            Created event record
        """
        event = KnowledgeGraphEvent(
            timestamp=datetime.utcnow(),
            event_type="relationship_created",
            entity1_name=entity1_name,
            entity2_name=entity2_name,
            relationship_type=relationship_type,
            new_confidence=confidence,
            enrichment_source=source
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)

        logger.info(
            f"Relationship created: {entity1_name} -> {entity2_name} "
            f"({relationship_type}), confidence: {confidence}"
        )

        return event

    @staticmethod
    async def log_manual_edit(
        db: AsyncSession,
        entity1_name: str,
        entity2_name: str,
        relationship_type: str,
        old_relationship_type: Optional[str],
        old_confidence: Optional[float],
        new_confidence: float,
        user_id: str,
        summary: Optional[str] = None
    ) -> KnowledgeGraphEvent:
        """
        Log a manual edit operation.

        Args:
            db: Database session
            entity1_name: First entity name
            entity2_name: Second entity name
            relationship_type: New relationship type
            old_relationship_type: Previous relationship type (if changed)
            old_confidence: Previous confidence
            new_confidence: New confidence
            user_id: User who made the edit
            summary: Description of changes

        Returns:
            Created event record
        """
        event = KnowledgeGraphEvent(
            timestamp=datetime.utcnow(),
            event_type="manual_edit",
            entity1_name=entity1_name,
            entity2_name=entity2_name,
            relationship_type=relationship_type,
            old_relationship_type=old_relationship_type,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            enrichment_source="manual",
            enrichment_summary=summary,
            user_id=user_id
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)

        logger.info(
            f"Manual edit logged by {user_id}: {entity1_name} -> {entity2_name} "
            f"({old_relationship_type} -> {relationship_type})"
        )

        return event


# Global instance
event_logger = EventLogger()

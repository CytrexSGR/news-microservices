"""Process articles and create location mappings."""
import logging
from typing import List, Dict, Any, Set
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.location_resolver import resolve_location_to_country

logger = logging.getLogger(__name__)


async def process_article_locations(
    db: AsyncSession,
    article_id: UUID,
    entities: List[Dict[str, Any]],
) -> List[str]:
    """
    Extract LOCATION entities and create article_locations mappings.

    Args:
        db: Database session
        article_id: UUID of the article
        entities: List of entity dicts from analysis payload (tier1.entities)

    Returns:
        List of ISO codes that were mapped
    """
    mapped_countries: Set[str] = set()

    # Filter LOCATION entities
    locations = [e for e in entities if e.get("type") == "LOCATION"]
    logger.info(f"Processing {len(locations)} LOCATION entities for article {article_id}")

    for entity in locations:
        name = entity.get("name") or entity.get("text", "")
        if not name:
            continue

        # Resolve to ISO code (direct DB lookup, no external service)
        iso_code = await resolve_location_to_country(db, name)
        if not iso_code:
            logger.debug(f"Could not resolve location '{name}' to country")
            continue

        # Skip if already mapped
        if iso_code in mapped_countries:
            continue

        # Insert mapping (ON CONFLICT = ignore duplicates)
        try:
            await db.execute(
                text("""
                    INSERT INTO article_locations (article_id, country_code, confidence, source)
                    VALUES (:article_id, :country_code, :confidence, 'entity_extraction')
                    ON CONFLICT (article_id, country_code) DO NOTHING
                """),
                {
                    "article_id": str(article_id),
                    "country_code": iso_code,
                    "confidence": entity.get("confidence", 1.0),
                },
            )
            mapped_countries.add(iso_code)
            logger.info(f"Mapped article {article_id} to {iso_code} (from '{name}')")
        except Exception as e:
            logger.error(f"Failed to insert article_location: {e}")

    return list(mapped_countries)

"""Entity fragmentation analysis and metrics."""
import logging
from typing import Dict, List, Optional
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CanonicalEntity, EntityAlias
from app.services.fuzzy_matcher import get_fuzzy_matcher

logger = logging.getLogger(__name__)


class FragmentationMetrics:
    """
    Analyze and measure entity fragmentation.

    Fragmentation Score:
    - 1.0 = Perfect (each entity has exactly 1 alias)
    - 0.5 = Moderate (average 2 aliases per entity)
    - < 0.3 = High fragmentation risk

    Goal: Reduce fragmentation by 30% through improved matching.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.fuzzy_matcher = get_fuzzy_matcher()

    async def calculate_fragmentation_score(
        self,
        entity_type: Optional[str] = None
    ) -> float:
        """
        Calculate fragmentation score for entity type.

        Score = 1 / (avg_aliases_per_entity)

        Args:
            entity_type: Entity type to analyze (None = all)

        Returns:
            Fragmentation score (0-1, higher is better)
        """
        # Count entities and aliases
        if entity_type:
            entity_stmt = select(func.count(CanonicalEntity.id)).where(
                CanonicalEntity.type == entity_type
            )
            alias_stmt = (
                select(func.count(EntityAlias.id))
                .join(CanonicalEntity)
                .where(CanonicalEntity.type == entity_type)
            )
        else:
            entity_stmt = select(func.count(CanonicalEntity.id))
            alias_stmt = select(func.count(EntityAlias.id))

        entities_result = await self.session.execute(entity_stmt)
        total_entities = entities_result.scalar_one()

        aliases_result = await self.session.execute(alias_stmt)
        total_aliases = aliases_result.scalar_one()

        if total_entities == 0:
            return 1.0  # No entities = no fragmentation

        avg_aliases = total_aliases / total_entities

        # Score: 1/avg_aliases (capped at 1.0)
        score = min(1.0, 1.0 / avg_aliases) if avg_aliases > 0 else 1.0

        logger.info(
            f"Fragmentation score for {entity_type or 'all'}: {score:.3f} "
            f"(entities={total_entities}, aliases={total_aliases}, avg={avg_aliases:.2f})"
        )

        return score

    async def find_potential_duplicates(
        self,
        entity_type: str,
        threshold: float = 0.90,
        limit: int = 100
    ) -> List[Dict]:
        """
        Find entities that might be duplicates.

        Uses fuzzy matching between entity names.

        Args:
            entity_type: Entity type to analyze
            threshold: Similarity threshold
            limit: Max pairs to return

        Returns:
            List of potential duplicate pairs with similarity score
        """
        # Get all entity names
        stmt = select(CanonicalEntity.id, CanonicalEntity.name).where(
            CanonicalEntity.type == entity_type
        )
        result = await self.session.execute(stmt)
        entities = [(row[0], row[1]) for row in result.all()]

        # Compare all pairs (O(n^2) - limit to reasonable size)
        if len(entities) > 500:
            logger.warning(f"Large entity set ({len(entities)}), limiting to first 500")
            entities = entities[:500]

        duplicates = []
        seen_pairs = set()

        for i, (id1, name1) in enumerate(entities):
            candidates = [name for _, name in entities[i+1:]]
            if not candidates:
                continue

            matches = self.fuzzy_matcher.get_top_matches(
                name1,
                candidates,
                top_k=5,
                threshold=threshold
            )

            for match_name, score in matches:
                # Find match entity
                match_entity = next(
                    (e for e in entities if e[1] == match_name),
                    None
                )
                if match_entity:
                    id2 = match_entity[0]
                    pair_key = tuple(sorted([id1, id2]))
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        duplicates.append({
                            "entity_id_1": id1,
                            "name1": name1,
                            "entity_id_2": id2,
                            "name2": match_name,
                            "similarity": score
                        })

            if len(duplicates) >= limit:
                break

        # Sort by similarity descending
        duplicates.sort(key=lambda x: x["similarity"], reverse=True)
        return duplicates[:limit]

    async def get_singleton_entities(
        self,
        entity_type: str,
        limit: int = 100
    ) -> List[CanonicalEntity]:
        """
        Find entities with only 1 alias.

        These are high-fragmentation candidates.

        Args:
            entity_type: Entity type
            limit: Max entities to return

        Returns:
            List of singleton entities
        """
        stmt = (
            select(CanonicalEntity)
            .join(EntityAlias)
            .where(CanonicalEntity.type == entity_type)
            .group_by(CanonicalEntity.id)
            .having(func.count(EntityAlias.id) == 1)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def generate_report(
        self,
        entity_type: Optional[str] = None
    ) -> Dict:
        """
        Generate comprehensive fragmentation report.

        Args:
            entity_type: Entity type (None = all types)

        Returns:
            Report dictionary with metrics
        """
        # Calculate core metrics
        score = await self.calculate_fragmentation_score(entity_type)

        # Entity and alias counts
        if entity_type:
            entity_stmt = select(func.count(CanonicalEntity.id)).where(
                CanonicalEntity.type == entity_type
            )
            alias_stmt = (
                select(func.count(EntityAlias.id))
                .join(CanonicalEntity)
                .where(CanonicalEntity.type == entity_type)
            )
        else:
            entity_stmt = select(func.count(CanonicalEntity.id))
            alias_stmt = select(func.count(EntityAlias.id))

        entities_result = await self.session.execute(entity_stmt)
        total_entities = entities_result.scalar_one()

        aliases_result = await self.session.execute(alias_stmt)
        total_aliases = aliases_result.scalar_one()

        avg_aliases = total_aliases / total_entities if total_entities > 0 else 0

        # Singleton count
        singletons = await self.get_singleton_entities(entity_type or "ORGANIZATION")
        singleton_count = len(singletons)

        # Potential duplicates
        if entity_type:
            potential_dupes = await self.find_potential_duplicates(entity_type, limit=20)
        else:
            potential_dupes = []

        return {
            "entity_type": entity_type or "all",
            "fragmentation_score": round(score, 4),
            "total_entities": total_entities,
            "total_aliases": total_aliases,
            "avg_aliases_per_entity": round(avg_aliases, 2),
            "singleton_count": singleton_count,
            "singleton_percentage": round(singleton_count / total_entities * 100, 2) if total_entities > 0 else 0,
            "potential_duplicates": potential_dupes[:10],  # Top 10 only
            "potential_duplicate_count": len(potential_dupes),
            "improvement_target": "30% reduction in singletons"
        }

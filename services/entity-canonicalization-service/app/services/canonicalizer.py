"""Main entity canonicalization service."""
import logging
import time
from typing import Optional, List, Tuple
from app.models.entities import EntityCanonical
from app.services.wikidata_client import WikidataClient
from app.services.embedding_service import EmbeddingService
from app.services.fuzzy_matcher import FuzzyMatcher
from app.services.alias_store import AliasStore
from app.config import settings

logger = logging.getLogger(__name__)


class EntityCanonicalizer:
    """
    Main entity canonicalization service.

    Multi-stage canonicalization pipeline:
    1. Exact match in alias store (cache)
    2. Fuzzy string matching (RapidFuzz)
    3. Wikidata entity linking
    4. [Future] Semantic similarity matching (OpenAI Embeddings + Neo4j Vector Search)
    5. Create new canonical entity

    Note: Semantic matching deferred until graph_memory.py implementation.
    """

    def __init__(
        self,
        alias_store: AliasStore,
        wikidata_client: WikidataClient,
        embedding_service: EmbeddingService,
        fuzzy_matcher: FuzzyMatcher
    ):
        self.alias_store = alias_store
        self.wikidata_client = wikidata_client
        self.embedding_service = embedding_service
        self.fuzzy_matcher = fuzzy_matcher
        self.wikidata_threshold = settings.WIKIDATA_CONFIDENCE_THRESHOLD

    async def canonicalize(
        self,
        entity_name: str,
        entity_type: str,
        language: str = "de"
    ) -> EntityCanonical:
        """
        Canonicalize entity name through multi-stage matching.

        Priority order:
        1. Exact match in alias store
        2. Fuzzy + semantic similarity matching
        3. Wikidata entity linking
        4. Create new canonical form

        Args:
            entity_name: Entity name to canonicalize
            entity_type: Entity type (PERSON, ORGANIZATION, LOCATION, etc.)
            language: Language code for Wikidata search

        Returns:
            EntityCanonical with canonical name and metadata
        """
        start_time = time.time()

        logger.debug(f"Canonicalizing: '{entity_name}' (type={entity_type})")

        # Stage 1: Exact match in cache
        canonical = await self.alias_store.find_exact(entity_name)
        if canonical:
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✓ Exact match: '{entity_name}' → '{canonical.name}' "
                f"({duration_ms:.1f}ms)"
            )
            return EntityCanonical(
                canonical_name=canonical.name,
                canonical_id=canonical.wikidata_id,
                aliases=[entity_name],
                confidence=1.0,
                source="exact",
                entity_type=entity_type
            )

        # Get candidates for similarity matching (limited by config)
        candidates = await self.alias_store.get_candidate_names(entity_type)

        # Stage 2: Fuzzy matching (RapidFuzz)
        # Note: Semantic matching (OpenAI Embeddings) deferred until graph_memory.py
        if candidates:
            match_result = self.fuzzy_matcher.fuzzy_match(
                entity_name,
                candidates
            )

            if match_result:
                best_match, score = match_result

                # Find the canonical entity
                canonical = await self.alias_store.find_by_name(
                    best_match,
                    entity_type
                )

                if canonical:
                    # Add new alias
                    await self.alias_store.add_alias(
                        canonical.name,
                        entity_type,
                        entity_name
                    )

                    duration_ms = (time.time() - start_time) * 1000
                    logger.info(
                        f"✓ Fuzzy match: '{entity_name}' → '{canonical.name}' "
                        f"(confidence={score:.2f}, {duration_ms:.1f}ms)"
                    )

                    return EntityCanonical(
                        canonical_name=canonical.name,
                        canonical_id=canonical.wikidata_id,
                        aliases=[entity_name],
                        confidence=score,
                        source="fuzzy",
                        entity_type=entity_type
                    )

        # Stage 3: Wikidata linking
        wikidata_match = await self.wikidata_client.search_entity(
            entity_name,
            entity_type,
            language
        )

        if wikidata_match and wikidata_match.confidence >= self.wikidata_threshold:
            canonical_label = wikidata_match.label

            # Store in database
            canonical = await self.alias_store.store_canonical(
                name=canonical_label,
                wikidata_id=wikidata_match.id,
                entity_type=entity_type,
                aliases=[entity_name] + wikidata_match.aliases
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✓ Wikidata match: '{entity_name}' → '{canonical_label}' "
                f"({wikidata_match.id}, confidence={wikidata_match.confidence:.2f}, "
                f"{duration_ms:.1f}ms)"
            )

            return EntityCanonical(
                canonical_name=canonical_label,
                canonical_id=wikidata_match.id,
                aliases=[entity_name] + wikidata_match.aliases,
                confidence=wikidata_match.confidence,
                source="wikidata",
                entity_type=entity_type
            )

        # Stage 4: No match found - create new canonical
        canonical = await self.alias_store.store_canonical(
            name=entity_name,
            wikidata_id=None,
            entity_type=entity_type,
            aliases=[]
        )

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"✓ New canonical: '{entity_name}' (type={entity_type}, {duration_ms:.1f}ms)"
        )

        return EntityCanonical(
            canonical_name=entity_name,
            canonical_id=None,
            aliases=[],
            confidence=1.0,
            source="new",
            entity_type=entity_type
        )

    async def canonicalize_batch(
        self,
        entities: List[Tuple[str, str, str]]  # [(name, type, language), ...]
    ) -> List[EntityCanonical]:
        """
        Batch canonicalization for multiple entities.

        Note: Batch optimization deferred until semantic matching implemented.
        Currently processes sequentially.

        Args:
            entities: List of (entity_name, entity_type, language) tuples

        Returns:
            List of EntityCanonical results
        """
        results = []

        for entity_name, entity_type, language in entities:
            result = await self.canonicalize(entity_name, entity_type, language)
            results.append(result)

        return results

    async def get_aliases(self, canonical_name: str, entity_type: str) -> List[str]:
        """
        Get all known aliases for a canonical entity.

        Args:
            canonical_name: Canonical entity name
            entity_type: Entity type

        Returns:
            List of aliases
        """
        canonical = await self.alias_store.find_by_name(canonical_name, entity_type)
        if not canonical:
            return []

        aliases = await self.alias_store.get_aliases(canonical.id)
        return [alias.alias for alias in aliases]

    async def get_stats(self) -> dict:
        """
        Get canonicalization statistics.

        Returns:
            Dictionary with statistics
        """
        total_entities, total_aliases, wikidata_linked = await self.alias_store.get_stats()

        coverage_percentage = (
            (total_aliases / total_entities * 100)
            if total_entities > 0
            else 0.0
        )

        return {
            "total_canonical_entities": total_entities,
            "total_aliases": total_aliases,
            "wikidata_linked": wikidata_linked,
            "coverage_percentage": coverage_percentage
        }

    async def get_detailed_stats(self) -> dict:
        """
        Get detailed canonicalization statistics for admin dashboard.

        Returns:
            Dictionary with detailed statistics including:
            - Basic stats (entities, aliases, wikidata coverage)
            - Entity type distribution
            - Top deduplicated entities
            - Performance metrics
            - Cost savings estimates
        """
        return await self.alias_store.get_detailed_stats()

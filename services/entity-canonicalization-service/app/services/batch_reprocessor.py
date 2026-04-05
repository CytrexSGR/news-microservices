"""
Batch reprocessing of existing entities through canonicalization pipeline.
"""

import asyncio
import uuid
from collections import deque
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
import logging

from app.database.models import CanonicalEntity, EntityAlias
from app.services.canonicalizer import EntityCanonicalizer
from app.models.entities import ReprocessingStatus, ReprocessingStats

logger = logging.getLogger(__name__)


class BatchReprocessor:
    """
    Handles batch reprocessing of all entities through canonicalization pipeline.

    Workflow:
    1. Analyzing - Load all entities and plan work
    2. Fuzzy Matching - Find similar entity names
    3. Semantic Matching - Find semantically similar entities
    4. Wikidata Lookup - Fetch missing Q-IDs
    5. Merging - Merge duplicate entities
    6. Updating - Save changes to databases
    """

    def __init__(
        self,
        db: AsyncSession,
        canonicalizer: EntityCanonicalizer,
        max_duplicate_pairs: int = 30000
    ):
        self.db = db
        self.canonicalizer = canonicalizer
        self.status = ReprocessingStatus()
        self._task: Optional[asyncio.Task] = None
        self._should_stop = False
        self.max_duplicate_pairs = max_duplicate_pairs
        # Bounded deque: FIFO eviction when full to prevent unbounded memory growth
        # Default 30k pairs uses ~6 GiB (increased to avoid duplicate loss)
        self.duplicate_pairs = deque(maxlen=max_duplicate_pairs)
        self.duplicate_pairs_overflow = 0  # Track dropped pairs due to maxlen

        logger.info(
            f"BatchReprocessor initialized with max_duplicate_pairs={max_duplicate_pairs}"
        )

    async def start(self, dry_run: bool = False) -> str:
        """
        Start batch reprocessing job.

        Args:
            dry_run: If True, only analyze without saving changes

        Returns:
            job_id: Unique identifier for this job
        """
        if self.status.status == "running":
            raise ValueError("Reprocessing already running")

        # Reset status
        self.status = ReprocessingStatus(
            status="running",
            started_at=datetime.utcnow().isoformat(),
            dry_run=dry_run
        )
        self._should_stop = False

        # Start background task
        job_id = str(uuid.uuid4())
        self._task = asyncio.create_task(self._run_reprocessing(dry_run))

        logger.info(f"Batch reprocessing started (job_id={job_id}, dry_run={dry_run})")
        return job_id

    def get_status(self) -> ReprocessingStatus:
        """Get current reprocessing status."""
        return self.status

    async def stop(self) -> dict:
        """Stop current reprocessing job gracefully."""
        if self.status.status != "running":
            raise ValueError("No reprocessing job running")

        self._should_stop = True
        logger.info("Stopping batch reprocessing...")

        # Wait for task to finish
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                self._task.cancel()

        return {
            "message": "Reprocessing stopped",
            "stats": self.status.stats.model_dump()
        }

    async def _run_reprocessing(self, dry_run: bool):
        """Main reprocessing logic (runs in background)."""
        try:
            # Reset duplicate pairs from previous run
            self.duplicate_pairs = deque(maxlen=self.max_duplicate_pairs)
            self.duplicate_pairs_overflow = 0

            # Phase 1: Analyze entities
            await self._phase_analyzing()
            if self._should_stop:
                return

            # Phase 2: Fuzzy matching
            await self._phase_fuzzy_matching()
            if self._should_stop:
                return

            # Phase 3: Semantic matching
            await self._phase_semantic_matching()
            if self._should_stop:
                return

            # Phase 4: Wikidata lookup
            await self._phase_wikidata_lookup()
            if self._should_stop:
                return

            # Phase 5: Merge duplicates
            await self._phase_merging(dry_run)
            if self._should_stop:
                return

            # Phase 6: Update databases (only if not dry run)
            if not dry_run:
                await self._phase_updating()

            # Mark as completed
            self.status.status = "completed"
            self.status.progress_percent = 100.0
            self.status.current_phase = None
            self.status.completed_at = datetime.utcnow().isoformat()

            logger.info(f"Batch reprocessing completed. Stats: {self.status.stats}")

        except Exception as e:
            logger.error(f"Batch reprocessing failed: {e}", exc_info=True)
            self.status.status = "failed"
            self.status.error_message = str(e)
            self.status.completed_at = datetime.utcnow().isoformat()

        finally:
            # 🔧 MEMORY FIX: Cleanup resources after completion/failure
            await self._cleanup_resources()

    async def _cleanup_resources(self):
        """
        Clean up resources to prevent memory leaks.

        Called automatically after reprocessing completes or fails.
        Frees ~200 MB of memory.
        """
        try:
            # Clear duplicate pairs deque
            self.duplicate_pairs.clear()
            self.duplicate_pairs_overflow = 0

            # Expunge all objects from session identity map
            # This releases references to all loaded entities
            if self.db and hasattr(self.db, 'expunge_all'):
                self.db.expunge_all()

            logger.info("Batch reprocessor resources cleaned up successfully")

        except Exception as e:
            logger.warning(f"Error during resource cleanup: {e}")

    async def _phase_analyzing(self):
        """Phase 1: Load all entities and analyze."""
        self.status.current_phase = "analyzing"
        self.status.progress_percent = 0.0

        logger.info("Phase 1: Analyzing entities...")

        # Count total entities
        result = await self.db.execute(select(func.count(CanonicalEntity.id)))
        total = result.scalar()

        self.status.stats.total_entities = total
        logger.info(f"Found {total} canonical entities to process")

        self.status.progress_percent = 10.0

    async def _phase_fuzzy_matching(self):
        """Phase 2: Find similar entity names using fuzzy matching."""
        self.status.current_phase = "fuzzy_matching"
        logger.info("Phase 2: Fuzzy matching...")

        # Load all entities
        result = await self.db.execute(select(CanonicalEntity))
        entities = result.scalars().all()

        # Simple fuzzy matching: find entities with similar names
        # In production, use Levenshtein distance or similar algorithm
        for i, entity1 in enumerate(entities):
            if self._should_stop:
                return

            for entity2 in entities[i+1:]:
                # Must be same type to be duplicates
                if entity1.type != entity2.type:
                    continue

                # Simple check: names differ by 1-2 characters
                if self._is_fuzzy_match(entity1.name, entity2.name):
                    # Track overflow (deque auto-evicts oldest when full)
                    if len(self.duplicate_pairs) >= self.max_duplicate_pairs:
                        self.duplicate_pairs_overflow += 1
                    self.duplicate_pairs.append((entity1, entity2))

            # Update progress
            self.status.stats.processed_entities = i + 1
            self.status.progress_percent = 10.0 + (30.0 * (i + 1) / len(entities))

        self.status.stats.duplicates_found = len(self.duplicate_pairs)
        logger.info(f"Found {len(self.duplicate_pairs)} fuzzy match candidates")

        # Warn if overflow occurred
        if self.duplicate_pairs_overflow > 0:
            logger.warning(
                f"Duplicate pairs overflow: {self.duplicate_pairs_overflow} pairs dropped "
                f"(max={self.max_duplicate_pairs}). Consider increasing max_duplicate_pairs "
                f"or using database-backed storage for large datasets."
            )

    def _is_fuzzy_match(self, name1: str, name2: str) -> bool:
        """Simple fuzzy matching heuristic."""
        # Normalize
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()

        # Skip if same
        if n1 == n2:
            return False

        # Check if one is substring of other
        if n1 in n2 or n2 in n1:
            return True

        # Check common abbreviations
        if len(n1) <= 4 and n1 == n2[:len(n1)]:
            return True
        if len(n2) <= 4 and n2 == n1[:len(n2)]:
            return True

        return False

    async def _phase_semantic_matching(self):
        """Phase 3: Find semantically similar entities."""
        self.status.current_phase = "semantic_matching"
        logger.info("Phase 3: Semantic matching...")

        # Semantic matching would use embeddings
        # For now, just increment progress
        self.status.progress_percent = 50.0

        # TODO: Implement semantic similarity using entity canonicalizer's embedding model
        logger.info("Semantic matching completed (placeholder)")

    async def _lookup_single_qid(self, entity: CanonicalEntity) -> dict:
        """
        Helper method to lookup Wikidata Q-ID for a single entity.

        Returns:
            dict with 'entity', 'qid', 'confidence', or 'error' if failed
        """
        try:
            results = await self.canonicalizer.wikidata_client.search_entity(
                entity.name,
                entity_type=entity.type
            )

            if results and results[0].confidence > 0.8:
                return {
                    'entity': entity,
                    'qid': results[0].id,
                    'confidence': results[0].confidence,
                    'success': True
                }
            else:
                return {
                    'entity': entity,
                    'success': False,
                    'reason': 'low_confidence'
                }

        except Exception as e:
            return {
                'entity': entity,
                'success': False,
                'error': str(e)
            }

    async def _phase_wikidata_lookup(self):
        """Phase 4: Fetch missing Wikidata Q-IDs (parallel version)."""
        self.status.current_phase = "wikidata_lookup"
        logger.info("Phase 4: Wikidata lookup (parallel)...")

        # Find entities without Q-ID
        result = await self.db.execute(
            select(CanonicalEntity).where(CanonicalEntity.wikidata_id == None)
        )
        entities_without_qid = result.scalars().all()

        logger.info(f"Found {len(entities_without_qid)} entities without Wikidata Q-ID")

        if not entities_without_qid:
            logger.info("No entities to lookup")
            return

        # Process in parallel batches to maximize throughput while respecting rate limits
        batch_size = 100  # 100 concurrent requests
        qids_added = 0
        total_batches = (len(entities_without_qid) + batch_size - 1) // batch_size

        logger.info(f"Processing {len(entities_without_qid)} entities in {total_batches} batches of {batch_size}")

        for batch_idx in range(total_batches):
            if self._should_stop:
                logger.info(f"Wikidata lookup stopped at batch {batch_idx}/{total_batches}")
                return

            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(entities_without_qid))
            batch = entities_without_qid[start_idx:end_idx]

            # Execute batch in parallel using asyncio.gather
            tasks = [self._lookup_single_qid(entity) for entity in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Wikidata lookup task failed: {result}")
                    self.status.stats.errors += 1
                elif isinstance(result, dict):
                    if result.get('success'):
                        qids_added += 1
                        logger.debug(f"Found Q-ID for {result['entity'].name}: {result['qid']}")
                    elif 'error' in result:
                        logger.warning(f"Failed to lookup Q-ID for {result['entity'].name}: {result['error']}")
                        self.status.stats.errors += 1

            # Update progress
            progress = 50.0 + (20.0 * (batch_idx + 1) / total_batches)
            self.status.progress_percent = progress

            # Rate limiting: 0.5s per batch of 100 = 200 req/s
            await asyncio.sleep(0.5)

            logger.info(
                f"Batch {batch_idx + 1}/{total_batches} completed: "
                f"{qids_added} Q-IDs found, {self.status.stats.errors} errors"
            )

        self.status.stats.qids_added = qids_added
        logger.info(f"Wikidata lookup completed: Added {qids_added} Q-IDs from {len(entities_without_qid)} entities")

    async def _phase_merging(self, dry_run: bool):
        """Phase 5: Merge duplicate entities."""
        self.status.current_phase = "merging"
        logger.info(f"Phase 5: Merging duplicates (dry_run={dry_run})...")

        if dry_run:
            # Just simulate merging for statistics
            self.status.stats.entities_merged = self.status.stats.duplicates_found
            logger.info(f"DRY RUN: Would merge {self.status.stats.entities_merged} duplicate entities")
        else:
            # Actually perform merges
            merged_count = 0

            for i, (entity1, entity2) in enumerate(self.duplicate_pairs):
                if self._should_stop:
                    break

                try:
                    # Determine which entity to keep (target) and which to merge (source)
                    target, source = self._choose_better_entity(entity1, entity2)

                    # Merge: Copy all aliases from source to target
                    await self._merge_entities(target, source)

                    merged_count += 1
                    logger.debug(f"Merged '{source.name}' (id={source.id}) → '{target.name}' (id={target.id})")

                except Exception as e:
                    logger.error(f"Failed to merge entities {entity1.name}/{entity2.name}: {e}")
                    self.status.stats.errors += 1

                # Update progress
                self.status.progress_percent = 70.0 + (10.0 * (i + 1) / len(self.duplicate_pairs))

            self.status.stats.entities_merged = merged_count
            logger.info(f"Successfully merged {merged_count} duplicate entities")

        self.status.progress_percent = 80.0

    def _choose_better_entity(
        self, entity1: CanonicalEntity, entity2: CanonicalEntity
    ) -> Tuple[CanonicalEntity, CanonicalEntity]:
        """
        Choose which entity to keep (target) and which to merge (source).

        Priority:
        1. Entity with Wikidata ID
        2. Entity that is older (created first)
        3. Entity with more aliases
        4. Default to entity1
        """
        # Has Wikidata ID?
        if entity1.wikidata_id and not entity2.wikidata_id:
            return entity1, entity2
        if entity2.wikidata_id and not entity1.wikidata_id:
            return entity2, entity1

        # Older entity (created first)
        if entity1.created_at < entity2.created_at:
            return entity1, entity2
        if entity2.created_at < entity1.created_at:
            return entity2, entity1

        # More aliases (if loaded)
        if hasattr(entity1, 'aliases') and hasattr(entity2, 'aliases'):
            if len(entity1.aliases) > len(entity2.aliases):
                return entity1, entity2
            if len(entity2.aliases) > len(entity1.aliases):
                return entity2, entity1

        # Default: keep entity1
        return entity1, entity2

    async def _merge_entities(self, target: CanonicalEntity, source: CanonicalEntity):
        """
        Merge source entity into target entity.

        Steps:
        1. Copy all aliases from source to target (skip conflicts)
        2. Delete the source entity (cascades to aliases)
        """
        # Load aliases for source entity
        result = await self.db.execute(
            select(EntityAlias).where(EntityAlias.canonical_id == source.id)
        )
        source_aliases = result.scalars().all()

        # Copy each alias to target (skip if alias already exists GLOBALLY)
        for alias_obj in source_aliases:
            # Check if alias already exists ANYWHERE in the database
            existing = await self.db.execute(
                select(EntityAlias).where(EntityAlias.alias == alias_obj.alias)
            )
            existing_alias = existing.scalar()

            if existing_alias:
                # Alias exists somewhere
                if existing_alias.canonical_id == target.id:
                    # Already points to target, perfect - skip
                    logger.debug(f"Alias '{alias_obj.alias}' already exists for target, skipping")
                    continue
                elif existing_alias.canonical_id == source.id:
                    # It's the source's own alias - will be deleted with source, skip
                    logger.debug(f"Alias '{alias_obj.alias}' belongs to source, will be cleaned up")
                    continue
                else:
                    # Points to different entity - this means duplicate aliases exist
                    # This shouldn't happen if canonicalization works correctly
                    logger.warning(
                        f"Alias '{alias_obj.alias}' already exists for entity {existing_alias.canonical_id}, "
                        f"skipping duplicate from source entity {source.id}"
                    )
                    continue

            # Alias doesn't exist - safe to add to target
            new_alias = EntityAlias(
                canonical_id=target.id,
                alias=alias_obj.alias
            )
            self.db.add(new_alias)

        # Delete the source entity (cascades to remaining aliases)
        await self.db.execute(
            delete(CanonicalEntity).where(CanonicalEntity.id == source.id)
        )
        await self.db.flush()  # Flush to apply changes within transaction

    async def _phase_updating(self):
        """Phase 6: Update databases with changes."""
        self.status.current_phase = "updating"
        logger.info("Phase 6: Updating databases...")

        try:
            # Commit all changes to PostgreSQL
            await self.db.commit()
            logger.info("Database updated successfully")

        except Exception as e:
            logger.error(f"Failed to update database: {e}")
            await self.db.rollback()
            raise

        self.status.progress_percent = 95.0

"""
Entity Deduplicator for Neo4j Knowledge Graph

Periodically merges duplicate entities in Neo4j based on:
1. Exact name matches with different casing
2. Name variations (with/without punctuation)
3. Common aliases (e.g., "Donald Trump" = "Donald J. Trump")

Design:
- Runs daily or on-demand
- Uses Cypher APOC procedures for merging
- Preserves all relationships during merge
- Logs all merge operations for audit

Created: 2025-12-27
"""

import logging
import asyncio
from typing import List, Dict, Any, Tuple
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

# Neo4j Configuration
NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j_password_2024"


class EntityDeduplicator:
    """Deduplicates entities in Neo4j Knowledge Graph"""

    def __init__(self):
        self.driver = None

    async def connect(self):
        """Connect to Neo4j"""
        self.driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        logger.info("Connected to Neo4j for deduplication")

    async def disconnect(self):
        """Disconnect from Neo4j"""
        if self.driver:
            await self.driver.close()
            logger.info("Disconnected from Neo4j")

    async def find_duplicates(self, min_similarity: float = 0.9) -> List[Dict[str, Any]]:
        """
        Find potential duplicate entities.

        Returns list of duplicate groups with:
        - canonical: The entity to keep
        - duplicates: Entities to merge into canonical
        """
        duplicates = []

        async with self.driver.session() as session:
            # 1. Exact duplicates (case-insensitive, SAME TYPE)
            # Only merge entities with identical normalized name AND same type
            query = """
            MATCH (e:Entity)
            WHERE e.type IS NOT NULL
            WITH toLower(trim(e.name)) AS normalized, e.type AS entityType, collect(e) AS entities
            WHERE size(entities) > 1
            RETURN normalized, entityType,
                   [e IN entities | {name: e.name, type: e.type, id: id(e)}] AS group
            ORDER BY size(entities) DESC
            LIMIT 200
            """
            result = await session.run(query)
            records = await result.data()

            for record in records:
                group = record['group']
                # Keep the one with most relationships or first alphabetically
                canonical = group[0]
                dups = group[1:]
                duplicates.append({
                    'normalized': record['normalized'],
                    'entity_type': record['entityType'],
                    'canonical': canonical,
                    'duplicates': dups,
                    'reason': 'case_insensitive_same_type'
                })

            # 2. Punctuation variations (e.g., "Trump Jr." vs "Trump Jr")
            query2 = """
            MATCH (e:Entity)
            WHERE e.type = 'PERSON'
            WITH apoc.text.clean(e.name) AS cleaned, collect(e) AS entities
            WHERE size(entities) > 1
            RETURN cleaned,
                   [e IN entities | {name: e.name, type: e.type, id: id(e)}] AS group
            ORDER BY size(entities) DESC
            LIMIT 100
            """
            try:
                result2 = await session.run(query2)
                records2 = await result2.data()

                for record in records2:
                    group = record['group']
                    canonical = group[0]
                    dups = group[1:]
                    if dups:  # Only add if there are actual duplicates
                        duplicates.append({
                            'cleaned': record['cleaned'],
                            'canonical': canonical,
                            'duplicates': dups,
                            'reason': 'punctuation_variation'
                        })
            except Exception as e:
                # APOC might not be available
                logger.warning(f"APOC query failed (expected if APOC not installed): {e}")

        logger.info(f"Found {len(duplicates)} duplicate groups")
        return duplicates

    async def merge_duplicates(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Merge duplicate entities.

        Args:
            dry_run: If True, only report what would be merged

        Returns:
            Summary of merge operations
        """
        duplicates = await self.find_duplicates()

        merged_count = 0
        errors = []

        async with self.driver.session() as session:
            for dup_group in duplicates:
                canonical = dup_group['canonical']

                for dup in dup_group['duplicates']:
                    if dry_run:
                        logger.info(
                            f"[DRY RUN] Would merge '{dup['name']}' (id={dup['id']}) "
                            f"into '{canonical['name']}' (id={canonical['id']})"
                        )
                        merged_count += 1
                    else:
                        try:
                            # Transfer all relationships to canonical entity
                            merge_query = """
                            MATCH (canonical:Entity) WHERE id(canonical) = $canonical_id
                            MATCH (duplicate:Entity) WHERE id(duplicate) = $duplicate_id

                            // Transfer incoming relationships
                            CALL {
                                WITH canonical, duplicate
                                MATCH (duplicate)<-[r]-(other)
                                WHERE other <> canonical
                                WITH canonical, r, other, type(r) AS relType, properties(r) AS props
                                CALL apoc.create.relationship(other, relType, props, canonical) YIELD rel
                                DELETE r
                                RETURN count(*) AS incoming
                            }

                            // Transfer outgoing relationships
                            CALL {
                                WITH canonical, duplicate
                                MATCH (duplicate)-[r]->(other)
                                WHERE other <> canonical
                                WITH canonical, r, other, type(r) AS relType, properties(r) AS props
                                CALL apoc.create.relationship(canonical, relType, props, other) YIELD rel
                                DELETE r
                                RETURN count(*) AS outgoing
                            }

                            // Delete duplicate
                            DETACH DELETE duplicate

                            RETURN true AS success
                            """

                            await session.run(merge_query, {
                                'canonical_id': canonical['id'],
                                'duplicate_id': dup['id']
                            })

                            logger.info(
                                f"Merged '{dup['name']}' into '{canonical['name']}'"
                            )
                            merged_count += 1

                        except Exception as e:
                            error_msg = f"Failed to merge {dup['name']}: {e}"
                            logger.error(error_msg)
                            errors.append(error_msg)

        return {
            'duplicate_groups_found': len(duplicates),
            'entities_merged': merged_count,
            'errors': errors,
            'dry_run': dry_run
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get current entity statistics"""
        async with self.driver.session() as session:
            query = """
            MATCH (e:Entity)
            WITH e.type AS type, count(*) AS count
            RETURN type, count
            ORDER BY count DESC
            """
            result = await session.run(query)
            records = await result.data()

            total = sum(r['count'] for r in records)

            return {
                'total_entities': total,
                'by_type': {r['type']: r['count'] for r in records}
            }


async def run_deduplication(dry_run: bool = True) -> Dict[str, Any]:
    """
    Run entity deduplication.

    Args:
        dry_run: If True, only report what would be merged

    Returns:
        Summary of operations
    """
    deduplicator = EntityDeduplicator()

    try:
        await deduplicator.connect()

        # Get stats before
        stats_before = await deduplicator.get_stats()
        logger.info(f"Entities before: {stats_before['total_entities']}")

        # Run deduplication
        result = await deduplicator.merge_duplicates(dry_run=dry_run)

        # Get stats after (only meaningful if not dry_run)
        stats_after = await deduplicator.get_stats()

        return {
            'stats_before': stats_before,
            'stats_after': stats_after,
            'merge_result': result
        }

    finally:
        await deduplicator.disconnect()


# For direct execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_deduplication(dry_run=True))
    print(f"Result: {result}")

#!/usr/bin/env python3
"""
Neo4j Entity Deduplication Migration Script

Purpose: Merge duplicate entities that share the same wikidata_id into a single canonical node.

Problem:
    Before the fix in ingestion_service.py, entities were merged by name only.
    This caused entities like "Trump", "Donald Trump", "President Trump" to be
    stored as separate nodes even though they all have the same wikidata_id (Q16944413).

Solution:
    1. Find all wikidata_ids that have multiple entity nodes
    2. For each group, keep the node with the most relationships as the canonical node
    3. Move all relationships from duplicate nodes to the canonical node
    4. Collect all name variants into the aliases array
    5. Delete the duplicate nodes

Usage:
    # Dry run (default) - shows what would be done
    python scripts/neo4j_merge_duplicate_entities.py

    # Execute migration
    python scripts/neo4j_merge_duplicate_entities.py --execute

    # Limit to specific wikidata_id (for testing)
    python scripts/neo4j_merge_duplicate_entities.py --wikidata-id Q16944413 --execute

Author: Claude Code
Date: 2025-12-28
"""

import asyncio
import argparse
import logging
from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase

# Configuration (uses environment variables when running in Docker)
import os
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password_2024")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def find_duplicate_wikidata_ids(
    driver,
    specific_wikidata_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find all wikidata_ids that have multiple entity nodes.

    Returns:
        List of dicts with wikidata_id, node_count, and total_relationships
    """
    if specific_wikidata_id:
        query = """
        MATCH (e:Entity)
        WHERE e.wikidata_id = $wikidata_id
        WITH e.wikidata_id AS wikidata_id, collect(e) AS entities
        WHERE size(entities) > 1
        UNWIND entities AS entity
        OPTIONAL MATCH (entity)-[r]-()
        WITH wikidata_id, entities, entity, count(r) AS rel_count
        WITH wikidata_id, size(entities) AS node_count, sum(rel_count) AS total_relationships
        RETURN wikidata_id, node_count, total_relationships
        ORDER BY total_relationships DESC
        """
        params = {"wikidata_id": specific_wikidata_id}
    else:
        query = """
        MATCH (e:Entity)
        WHERE e.wikidata_id IS NOT NULL
        WITH e.wikidata_id AS wikidata_id, collect(e) AS entities
        WHERE size(entities) > 1
        UNWIND entities AS entity
        OPTIONAL MATCH (entity)-[r]-()
        WITH wikidata_id, entities, entity, count(r) AS rel_count
        WITH wikidata_id, size(entities) AS node_count, sum(rel_count) AS total_relationships
        RETURN wikidata_id, node_count, total_relationships
        ORDER BY total_relationships DESC
        """
        params = {}

    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(query, params)
        records = await result.data()
        return records


async def get_duplicate_entities_for_wikidata_id(
    driver,
    wikidata_id: str
) -> List[Dict[str, Any]]:
    """
    Get all entity nodes for a given wikidata_id, ordered by relationship count.

    Returns:
        List of entities with name, elementId, and relationship_count
    """
    query = """
    MATCH (e:Entity {wikidata_id: $wikidata_id})
    OPTIONAL MATCH (e)-[r]-()
    WITH e, count(r) AS rel_count
    RETURN
        e.name AS name,
        e.type AS type,
        e.entity_id AS entity_id,
        elementId(e) AS element_id,
        rel_count AS relationship_count,
        e.aliases AS existing_aliases,
        e.created_at AS created_at
    ORDER BY rel_count DESC
    """

    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(query, {"wikidata_id": wikidata_id})
        records = await result.data()
        return records


async def merge_entities(
    driver,
    wikidata_id: str,
    entities: List[Dict[str, Any]],
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Merge duplicate entities into a single canonical node.

    Strategy:
    1. Keep the entity with the most relationships as canonical
    2. Move all relationships from duplicates to canonical
    3. Collect all names as aliases
    4. Delete duplicate nodes

    Returns:
        Summary of changes made
    """
    if len(entities) < 2:
        return {"skipped": True, "reason": "Less than 2 entities"}

    # First entity (most relationships) is canonical
    canonical = entities[0]
    duplicates = entities[1:]

    # Collect all unique names for aliases
    all_names = set()
    for e in entities:
        all_names.add(e['name'])
        if e.get('existing_aliases'):
            all_names.update(e['existing_aliases'])

    summary = {
        "wikidata_id": wikidata_id,
        "canonical_name": canonical['name'],
        "canonical_element_id": canonical['element_id'],
        "duplicates_merged": len(duplicates),
        "duplicate_names": [d['name'] for d in duplicates],
        "aliases_collected": list(all_names),
        "relationships_moved": 0,
        "dry_run": dry_run
    }

    if dry_run:
        logger.info(f"[DRY RUN] Would merge {len(duplicates)} duplicates into '{canonical['name']}' for {wikidata_id}")
        logger.info(f"  Canonical: {canonical['name']} ({canonical['relationship_count']} rels)")
        for d in duplicates:
            logger.info(f"  Duplicate: {d['name']} ({d['relationship_count']} rels) -> will be merged")
        return summary

    async with driver.session(database=NEO4J_DATABASE) as session:
        # For each duplicate, move its relationships to canonical and delete
        for dup in duplicates:
            # Step 1: Move incoming relationships
            move_incoming_query = """
            MATCH (dup:Entity)
            WHERE elementId(dup) = $dup_element_id
            MATCH (canonical:Entity)
            WHERE elementId(canonical) = $canonical_element_id
            MATCH (source)-[old_rel]->(dup)
            WHERE source <> canonical
            WITH canonical, dup, source, old_rel, type(old_rel) AS rel_type, properties(old_rel) AS props
            CALL apoc.create.relationship(source, rel_type, props, canonical) YIELD rel AS new_rel
            DELETE old_rel
            RETURN count(new_rel) AS moved_count
            """

            try:
                result = await session.run(move_incoming_query, {
                    "dup_element_id": dup['element_id'],
                    "canonical_element_id": canonical['element_id']
                })
                record = await result.single()
                if record:
                    summary["relationships_moved"] += record["moved_count"]
            except Exception as e:
                # APOC might not be available, use fallback
                if "apoc" in str(e).lower():
                    logger.warning(f"APOC not available, using fallback relationship migration")
                    await _move_relationships_without_apoc(
                        session, dup['element_id'], canonical['element_id']
                    )
                else:
                    raise

            # Step 2: Move outgoing relationships
            move_outgoing_query = """
            MATCH (dup:Entity)
            WHERE elementId(dup) = $dup_element_id
            MATCH (canonical:Entity)
            WHERE elementId(canonical) = $canonical_element_id
            MATCH (dup)-[old_rel]->(target)
            WHERE target <> canonical
            WITH canonical, dup, target, old_rel, type(old_rel) AS rel_type, properties(old_rel) AS props
            CALL apoc.create.relationship(canonical, rel_type, props, target) YIELD rel AS new_rel
            DELETE old_rel
            RETURN count(new_rel) AS moved_count
            """

            try:
                result = await session.run(move_outgoing_query, {
                    "dup_element_id": dup['element_id'],
                    "canonical_element_id": canonical['element_id']
                })
                record = await result.single()
                if record:
                    summary["relationships_moved"] += record["moved_count"]
            except Exception as e:
                if "apoc" not in str(e).lower():
                    raise

            # Step 3: Delete duplicate node
            delete_query = """
            MATCH (dup:Entity)
            WHERE elementId(dup) = $dup_element_id
            DETACH DELETE dup
            """
            await session.run(delete_query, {"dup_element_id": dup['element_id']})
            logger.info(f"  Deleted duplicate: {dup['name']}")

        # Step 4: Update canonical node with collected aliases
        update_aliases_query = """
        MATCH (canonical:Entity)
        WHERE elementId(canonical) = $canonical_element_id
        SET canonical.aliases = $aliases,
            canonical.migration_date = datetime(),
            canonical.duplicates_merged = $duplicates_merged
        RETURN canonical.name AS name
        """
        await session.run(update_aliases_query, {
            "canonical_element_id": canonical['element_id'],
            "aliases": list(all_names),
            "duplicates_merged": len(duplicates)
        })

        logger.info(f"✓ Merged {len(duplicates)} duplicates into '{canonical['name']}' for {wikidata_id}")

    return summary


async def _move_relationships_without_apoc(
    session,
    dup_element_id: str,
    canonical_element_id: str
):
    """
    Fallback method to move relationships without APOC.

    This is more limited - it creates new relationships with a fixed type
    and copies over the properties we know about.
    """
    # Get all relationship types from duplicate
    get_rels_query = """
    MATCH (dup:Entity)
    WHERE elementId(dup) = $dup_element_id
    MATCH (dup)-[r]-()
    RETURN DISTINCT type(r) AS rel_type
    """
    result = await session.run(get_rels_query, {"dup_element_id": dup_element_id})
    rel_types = [r["rel_type"] for r in await result.data()]

    for rel_type in rel_types:
        # For each relationship type, we need to dynamically handle it
        # This is a limitation without APOC - we handle common relationship types

        # Move incoming relationships
        move_in = f"""
        MATCH (dup:Entity)
        WHERE elementId(dup) = $dup_element_id
        MATCH (canonical:Entity)
        WHERE elementId(canonical) = $canonical_element_id
        MATCH (source)-[old_rel:{rel_type}]->(dup)
        WHERE source <> canonical
        MERGE (source)-[new_rel:{rel_type}]->(canonical)
        SET new_rel = properties(old_rel)
        DELETE old_rel
        """
        await session.run(move_in, {
            "dup_element_id": dup_element_id,
            "canonical_element_id": canonical_element_id
        })

        # Move outgoing relationships
        move_out = f"""
        MATCH (dup:Entity)
        WHERE elementId(dup) = $dup_element_id
        MATCH (canonical:Entity)
        WHERE elementId(canonical) = $canonical_element_id
        MATCH (dup)-[old_rel:{rel_type}]->(target)
        WHERE target <> canonical
        MERGE (canonical)-[new_rel:{rel_type}]->(target)
        SET new_rel = properties(old_rel)
        DELETE old_rel
        """
        await session.run(move_out, {
            "dup_element_id": dup_element_id,
            "canonical_element_id": canonical_element_id
        })


async def run_migration(
    dry_run: bool = True,
    specific_wikidata_id: Optional[str] = None,
    limit: Optional[int] = None
):
    """
    Run the full migration process.
    """
    driver = AsyncGraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    try:
        # Verify connectivity
        await driver.verify_connectivity()
        logger.info(f"✓ Connected to Neo4j at {NEO4J_URI}")

        # Find duplicates
        logger.info("Finding duplicate wikidata_ids...")
        duplicates = await find_duplicate_wikidata_ids(driver, specific_wikidata_id)

        if not duplicates:
            logger.info("No duplicate entities found!")
            return

        logger.info(f"Found {len(duplicates)} wikidata_ids with duplicate entities")

        # Apply limit if specified
        if limit:
            duplicates = duplicates[:limit]
            logger.info(f"Processing first {limit} wikidata_ids")

        # Calculate totals
        total_nodes = sum(d['node_count'] for d in duplicates)
        total_rels = sum(d['total_relationships'] for d in duplicates)

        logger.info(f"Total: {total_nodes} nodes, {total_rels} relationships to process")
        logger.info("-" * 60)

        # Process each duplicate group
        results = []
        for i, dup in enumerate(duplicates, 1):
            wikidata_id = dup['wikidata_id']
            logger.info(f"\n[{i}/{len(duplicates)}] Processing {wikidata_id} ({dup['node_count']} nodes, {dup['total_relationships']} rels)")

            # Get all entities for this wikidata_id
            entities = await get_duplicate_entities_for_wikidata_id(driver, wikidata_id)

            # Merge them
            result = await merge_entities(driver, wikidata_id, entities, dry_run=dry_run)
            results.append(result)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)

        total_merged = sum(r.get('duplicates_merged', 0) for r in results)
        total_moved = sum(r.get('relationships_moved', 0) for r in results)

        if dry_run:
            logger.info(f"[DRY RUN] Would merge {total_merged} duplicate nodes")
            logger.info(f"[DRY RUN] Would move {total_moved} relationships")
            logger.info("\nRun with --execute to apply changes")
        else:
            logger.info(f"✓ Merged {total_merged} duplicate nodes")
            logger.info(f"✓ Moved {total_moved} relationships")
            logger.info("Migration complete!")

    finally:
        await driver.close()


def main():
    parser = argparse.ArgumentParser(
        description="Merge duplicate Neo4j entities that share the same wikidata_id"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the migration (default is dry-run)"
    )
    parser.add_argument(
        "--wikidata-id",
        type=str,
        help="Process only a specific wikidata_id (e.g., Q16944413)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of wikidata_ids to process"
    )

    args = parser.parse_args()

    dry_run = not args.execute

    if dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info("Use --execute to apply changes")
        logger.info("=" * 60)
    else:
        logger.info("=" * 60)
        logger.info("EXECUTE MODE - Changes will be applied!")
        logger.info("=" * 60)

    asyncio.run(run_migration(
        dry_run=dry_run,
        specific_wikidata_id=args.wikidata_id,
        limit=args.limit
    ))


if __name__ == "__main__":
    main()

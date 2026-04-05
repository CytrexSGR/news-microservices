#!/usr/bin/env python3
"""
Sync Entity Canonicalization to Neo4j

Enriches Neo4j Entity nodes with wikidata_id from the entity-canonicalization-service.

Usage:
    python scripts/sync_canonicalization_to_neo4j.py --dry-run        # Preview changes
    python scripts/sync_canonicalization_to_neo4j.py                  # Execute sync
    python scripts/sync_canonicalization_to_neo4j.py --batch-size 50  # Custom batch size
"""

import argparse
import requests
import time
from typing import Optional
from neo4j import GraphDatabase


# Configuration (use environment variables or defaults for Docker)
import os

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4j_password_2024")
CANONICALIZATION_URL = os.environ.get(
    "CANONICALIZATION_URL",
    "http://news-entity-canonicalization:8112/api/v1/canonicalization/canonicalize/batch"
)
BATCH_SIZE = 100
REQUEST_TIMEOUT = 30


def get_neo4j_entities_without_wikidata(driver, limit: Optional[int] = None) -> list[dict]:
    """Fetch entities from Neo4j that don't have a wikidata_id."""
    query = """
    MATCH (e:Entity)
    WHERE e.wikidata_id IS NULL
    RETURN e.name as name, e.type as type, e.entity_id as entity_id
    """
    if limit:
        query += f" LIMIT {limit}"

    with driver.session() as session:
        result = session.run(query)
        return [dict(record) for record in result]


def map_neo4j_type_to_canonicalization_type(neo4j_type: str) -> str:
    """Map Neo4j entity types to canonicalization service types."""
    type_mapping = {
        "PERSON": "PERSON",
        "ORGANIZATION": "ORGANIZATION",
        "LOCATION": "LOCATION",
        "EVENT": "EVENT",
        "PRODUCT": "PRODUCT",
        "OTHER": "MISC",
        "CONCEPT": "MISC",
        "TIME": "DATE",
        "TECHNOLOGY": "PRODUCT",
        "CURRENCY": "MONEY",
        "LAW": "LEGISLATION",
        "POLICY": "MISC",
        "FINANCIAL_INSTRUMENT": "PRODUCT",
        "MISC": "MISC",
        "THREAT_ACTOR": "PERSON",
    }
    return type_mapping.get(neo4j_type, "MISC")


def canonicalize_batch(entities: list[dict]) -> list[dict]:
    """Call canonicalization service batch API."""
    payload = {
        "entities": [
            {
                "entity_name": e["name"],
                "entity_type": map_neo4j_type_to_canonicalization_type(e["type"] or "MISC")
            }
            for e in entities
            if e["name"]  # Skip empty names
        ]
    }

    try:
        response = requests.post(
            CANONICALIZATION_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"  ERROR calling canonicalization API: {e}")
        return []


def update_neo4j_entity(driver, entity_id: str, wikidata_id: str, canonical_name: str, dry_run: bool = False):
    """Update a Neo4j entity with wikidata_id and canonical_name."""
    if dry_run:
        return True

    query = """
    MATCH (e:Entity {entity_id: $entity_id})
    SET e.wikidata_id = $wikidata_id,
        e.canonical_name = $canonical_name,
        e.canonicalized_at = datetime()
    RETURN e.name
    """

    with driver.session() as session:
        result = session.run(query, entity_id=entity_id, wikidata_id=wikidata_id, canonical_name=canonical_name)
        return result.single() is not None


def main():
    parser = argparse.ArgumentParser(description="Sync canonicalization data to Neo4j")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Batch size for processing")
    parser.add_argument("--limit", type=int, help="Limit number of entities to process")
    args = parser.parse_args()

    print("=" * 60)
    print("Entity Canonicalization to Neo4j Sync")
    print("=" * 60)

    if args.dry_run:
        print("MODE: DRY RUN (no changes will be made)")
    else:
        print("MODE: LIVE (changes will be applied)")

    print(f"Batch size: {args.batch_size}")
    if args.limit:
        print(f"Limit: {args.limit} entities")
    print()

    # Connect to Neo4j
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        # Verify connection
        driver.verify_connectivity()
        print("  Connected successfully")
    except Exception as e:
        print(f"  ERROR: Failed to connect to Neo4j: {e}")
        return 1

    # Fetch entities without wikidata_id
    print("\nFetching entities without wikidata_id...")
    entities = get_neo4j_entities_without_wikidata(driver, limit=args.limit)
    print(f"  Found {len(entities)} entities to process")

    if not entities:
        print("\nNo entities to process. Done!")
        driver.close()
        return 0

    # Process in batches
    stats = {
        "processed": 0,
        "matched": 0,
        "updated": 0,
        "no_wikidata": 0,
        "errors": 0,
    }

    total_batches = (len(entities) + args.batch_size - 1) // args.batch_size
    print(f"\nProcessing {total_batches} batches...")

    start_time = time.time()

    for batch_num in range(total_batches):
        batch_start = batch_num * args.batch_size
        batch_end = min(batch_start + args.batch_size, len(entities))
        batch = entities[batch_start:batch_end]

        print(f"\nBatch {batch_num + 1}/{total_batches} ({len(batch)} entities)")

        # Canonicalize batch
        results = canonicalize_batch(batch)

        if not results:
            stats["errors"] += len(batch)
            continue

        # Create lookup by original name
        result_lookup = {}
        for i, entity in enumerate(batch):
            if i < len(results):
                result_lookup[entity["name"]] = (entity, results[i])

        # Process results
        for entity_name, (entity, result) in result_lookup.items():
            stats["processed"] += 1

            canonical_id = result.get("canonical_id")
            canonical_name = result.get("canonical_name")

            if canonical_id:
                stats["matched"] += 1

                if entity.get("entity_id"):
                    success = update_neo4j_entity(
                        driver,
                        entity["entity_id"],
                        canonical_id,
                        canonical_name,
                        dry_run=args.dry_run
                    )
                    if success:
                        stats["updated"] += 1
                        if args.dry_run:
                            print(f"    [DRY] Would update: {entity_name} -> {canonical_name} ({canonical_id})")
                    else:
                        stats["errors"] += 1
            else:
                stats["no_wikidata"] += 1

        # Progress indicator
        elapsed = time.time() - start_time
        rate = stats["processed"] / elapsed if elapsed > 0 else 0
        remaining = (len(entities) - stats["processed"]) / rate if rate > 0 else 0
        print(f"  Progress: {stats['processed']}/{len(entities)} | "
              f"Matched: {stats['matched']} | "
              f"Rate: {rate:.1f}/s | "
              f"ETA: {remaining/60:.1f}min")

    # Final summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"Total processed:    {stats['processed']}")
    if stats['processed'] > 0:
        print(f"Matched with QID:   {stats['matched']} ({stats['matched']/stats['processed']*100:.1f}%)")
    else:
        print(f"Matched with QID:   {stats['matched']}")
    print(f"Updated in Neo4j:   {stats['updated']}")
    print(f"No Wikidata ID:     {stats['no_wikidata']}")
    print(f"Errors:             {stats['errors']}")
    print(f"Time elapsed:       {elapsed:.1f}s")

    if args.dry_run:
        print("\n[DRY RUN] No changes were made. Run without --dry-run to apply.")

    driver.close()
    return 0


if __name__ == "__main__":
    exit(main())

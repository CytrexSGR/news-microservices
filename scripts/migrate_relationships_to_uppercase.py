#!/usr/bin/env python3
"""
Migration Script: Relationship Types to UPPERCASE

Migrates all lowercase relationship types to UPPERCASE in Neo4j.
Resolves case-inconsistency duplicates by merging lowercase → UPPERCASE.

Problem:
  RELATED_TO: 1400  |  related_to: 1036  ← DUPLICATES

Solution:
  RELATED_TO: 2436  ✅ MERGED

Usage:
  python scripts/migrate_relationships_to_uppercase.py

Date: 2025-10-25
Reason: Code changed from relationship_type.name to .value
"""

import asyncio
import sys
from neo4j import AsyncGraphDatabase

# Configuration
NEO4J_URI = "bolt://neo4j:7687"  # Use Docker service name instead of localhost
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j_password_2024"


async def migrate_relationships_to_uppercase():
    """
    Migrate all lowercase relationship types to UPPERCASE in Neo4j.

    Strategy:
    1. Find all unique relationship types (case-insensitive groups)
    2. For each group with duplicates: merge lowercase → UPPERCASE
    3. Aggregate mention_count and keep highest confidence
    4. Delete lowercase variants after merging
    """

    print("="*70)
    print("   Neo4j Relationship Type Migration: lowercase → UPPERCASE")
    print("="*70)
    print()

    driver = AsyncGraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    try:
        async with driver.session() as session:
            # Step 1: Find all relationship types
            print("📊 Step 1: Analyzing relationship types...")
            result = await session.run("""
                MATCH ()-[r]->()
                RETURN DISTINCT type(r) AS rel_type, count(r) AS count
                ORDER BY count DESC
            """)

            all_types = [(record["rel_type"], record["count"]) async for record in result]

            print(f"   Found {len(all_types)} distinct relationship types")
            print()

            # Step 2: Group by uppercase variant
            print("🔍 Step 2: Identifying duplicates...")
            type_groups = {}
            for rel_type, count in all_types:
                uppercase = rel_type.upper()
                if uppercase not in type_groups:
                    type_groups[uppercase] = []
                type_groups[uppercase].append((rel_type, count))

            # Find groups with duplicates
            duplicates = {
                uppercase: variants
                for uppercase, variants in type_groups.items()
                if len(variants) > 1
            }

            if not duplicates:
                print("   ✅ No duplicates found! All relationship types are consistent.")
                return

            print(f"   Found {len(duplicates)} relationship types with case-inconsistency:")
            for uppercase, variants in duplicates.items():
                total_count = sum(count for _, count in variants)
                print(f"   - {uppercase}: {total_count} total")
                for variant, count in variants:
                    marker = "✅" if variant == uppercase else "❌"
                    print(f"     {marker} {variant}: {count}")
            print()

            # Step 3: Migrate duplicates
            print("🔄 Step 3: Migrating relationships...")
            total_migrated = 0
            total_deleted = 0

            for uppercase, variants in duplicates.items():
                # Skip if only uppercase variant exists
                lowercase_variants = [v for v, _ in variants if v != uppercase]
                if not lowercase_variants:
                    continue

                print(f"\n   Migrating: {[v for v, _ in variants]} → {uppercase}")

                # For each lowercase variant
                for lowercase_variant in lowercase_variants:
                    # Count relationships
                    count_result = await session.run(f"""
                        MATCH ()-[r:`{lowercase_variant}`]->()
                        RETURN count(r) AS count
                    """)
                    count_data = await count_result.single()
                    count = count_data["count"] if count_data else 0

                    if count == 0:
                        print(f"      ⚠️  '{lowercase_variant}': 0 relationships, skipping")
                        continue

                    print(f"      🔄 '{lowercase_variant}': {count} relationships...")

                    # Migrate: Create UPPERCASE variant and merge properties
                    migration_query = f"""
                    MATCH (subject)-[old_rel:`{lowercase_variant}`]->(object)

                    // Create or update UPPERCASE relationship
                    MERGE (subject)-[new_rel:`{uppercase}`]->(object)
                    ON CREATE SET
                        new_rel.confidence = old_rel.confidence,
                        new_rel.mention_count = old_rel.mention_count,
                        new_rel.created_at = old_rel.created_at,
                        new_rel.evidence = old_rel.evidence,
                        new_rel.source_url = old_rel.source_url,
                        new_rel.article_id = old_rel.article_id,
                        new_rel.last_seen = old_rel.last_seen
                    ON MATCH SET
                        // Aggregate mention counts
                        new_rel.mention_count = new_rel.mention_count + old_rel.mention_count,
                        // Keep highest confidence
                        new_rel.confidence = CASE
                            WHEN old_rel.confidence > new_rel.confidence THEN old_rel.confidence
                            ELSE new_rel.confidence
                        END,
                        // Update last_seen to most recent
                        new_rel.last_seen = CASE
                            WHEN old_rel.last_seen > new_rel.last_seen THEN old_rel.last_seen
                            ELSE new_rel.last_seen
                        END

                    // Delete old lowercase relationship
                    DELETE old_rel

                    RETURN count(*) AS migrated
                    """

                    try:
                        result = await session.run(migration_query)
                        migrated_data = await result.single()
                        migrated_count = migrated_data["migrated"] if migrated_data else 0

                        print(f"         ✅ Migrated: {migrated_count} relationships")
                        total_migrated += migrated_count
                        total_deleted += migrated_count

                    except Exception as e:
                        print(f"         ❌ Error: {e}")
                        continue

            print()
            print("="*70)
            print("   ✅ MIGRATION COMPLETE")
            print("="*70)
            print(f"   Total relationships migrated: {total_migrated}")
            print(f"   Total lowercase relationships deleted: {total_deleted}")
            print()

            # Step 4: Verify final state
            print("📊 Step 4: Verification - Final relationship counts:")
            final_result = await session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS rel_type, count(r) AS count
                ORDER BY count DESC
                LIMIT 30
            """)

            final_types = [(record["rel_type"], record["count"]) async for record in final_result]

            for rel_type, count in final_types:
                # Check if uppercase
                is_uppercase = rel_type == rel_type.upper()
                marker = "✅" if is_uppercase else "⚠️ "
                print(f"   {marker} {rel_type}: {count}")

            # Check for remaining lowercase
            remaining_lowercase = [
                (rel_type, count)
                for rel_type, count in final_types
                if rel_type != rel_type.upper()
            ]

            print()
            if remaining_lowercase:
                print("⚠️  WARNING: Still found lowercase relationship types:")
                for rel_type, count in remaining_lowercase:
                    print(f"   - {rel_type}: {count}")
                print("   (These might be single-case types without UPPERCASE variants)")
            else:
                print("✅ SUCCESS: All relationship types are now UPPERCASE!")

            print()
            print("="*70)

    finally:
        await driver.close()


if __name__ == "__main__":
    try:
        asyncio.run(migrate_relationships_to_uppercase())
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

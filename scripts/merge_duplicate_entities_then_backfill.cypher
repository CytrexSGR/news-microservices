// ============================================================
// Merge Duplicate Entities THEN Backfill Types
// ============================================================
// Problem: Duplicate entities (same name) prevent backfill due to UNIQUENESS constraint
// Solution: Merge duplicates first, then backfill types
// Date: 2025-11-19
// ============================================================

// ============================================================
// STEP 1: Analyze Duplicates
// ============================================================

// Count duplicate entities (same name, multiple nodes)
MATCH (e:Entity)
WITH e.name AS name, COLLECT(e) AS entities
WHERE SIZE(entities) > 1
RETURN COUNT(name) AS duplicate_names, SUM(SIZE(entities)) AS total_duplicate_nodes;

// Show top duplicates
MATCH (e:Entity)
WITH e.name AS name, COLLECT(e) AS entities
WHERE SIZE(entities) > 1
RETURN name, SIZE(entities) AS count
ORDER BY count DESC
LIMIT 20;

// ============================================================
// STEP 2: Drop UNIQUENESS Constraint (Temporarily)
// ============================================================
// This allows us to SET e.type without constraint violations

DROP CONSTRAINT entity_unique IF EXISTS;

// ============================================================
// STEP 3: Backfill Types (Now Safe Without Constraint)
// ============================================================

// Backfill in one batch (constraint is dropped, so no violations)
MATCH (e:Entity)
WHERE e.entity_type IS NOT NULL AND e.type IS NULL
SET e.type = e.entity_type
RETURN COUNT(e) AS backfilled;

// ============================================================
// STEP 4: Merge Duplicates
// ============================================================
// Now that all entities have e.type set, merge duplicates by (name, type)

// Find and merge duplicate entities with same (name, type)
CALL apoc.periodic.iterate(
    "MATCH (e:Entity) WITH e.name AS name, e.type AS type, COLLECT(e) AS entities WHERE SIZE(entities) > 1 RETURN name, type, entities",
    "
    WITH entities[0] AS primary, entities[1..] AS duplicates

    // Merge relationships from duplicates to primary
    UNWIND duplicates AS dup
    CALL {
        WITH dup, primary
        MATCH (dup)-[r]-(other)
        MERGE (primary)-[newRel:TYPE(r)]-(other)
        ON CREATE SET newRel = properties(r)
        ON MATCH SET newRel.mention_count = newRel.mention_count + r.mention_count
        DELETE r
    }

    // Merge properties (keep most recent last_seen)
    WITH primary, duplicates
    UNWIND duplicates AS dup
    SET primary.last_seen = CASE
        WHEN dup.last_seen > primary.last_seen THEN dup.last_seen
        ELSE primary.last_seen
    END

    // Delete duplicate nodes
    WITH dup
    DETACH DELETE dup
    ",
    {batchSize: 100, parallel: false}
)
YIELD batches, total
RETURN batches, total;

// Alternative without APOC (manual merging):
// Run this multiple times until no duplicates remain

MATCH (e:Entity)
WITH e.name AS name, e.type AS type, COLLECT(e) AS entities
WHERE SIZE(entities) > 1
WITH entities[0] AS primary, entities[1] AS dup
LIMIT 100

// Copy relationships from duplicate to primary
CALL {
    WITH dup, primary
    MATCH (dup)-[r]->(other)
    WHERE NOT (primary)-[:TYPE(r)]->(other)
    MERGE (primary)-[newRel:TYPE(r)]->(other)
    SET newRel = properties(r)
}

CALL {
    WITH dup, primary
    MATCH (other)-[r]->(dup)
    WHERE NOT (other)-[:TYPE(r)]->(primary)
    MERGE (other)-[newRel:TYPE(r)]->(primary)
    SET newRel = properties(r)
}

// Update last_seen to most recent
SET primary.last_seen = CASE
    WHEN dup.last_seen > primary.last_seen THEN dup.last_seen
    ELSE primary.last_seen
END

// Delete duplicate
WITH dup
DETACH DELETE dup
RETURN COUNT(dup) AS merged;

// ============================================================
// STEP 5: Recreate UNIQUENESS Constraint
// ============================================================

CREATE CONSTRAINT entity_unique IF NOT EXISTS
FOR (e:Entity)
REQUIRE (e.name, e.type) IS UNIQUE;

// ============================================================
// STEP 6: Verify
// ============================================================

// Check no duplicates remain
MATCH (e:Entity)
WITH e.name AS name, e.type AS type, COLLECT(e) AS entities
WHERE SIZE(entities) > 1
RETURN COUNT(*) AS remaining_duplicates;
// Expected: 0

// Check all entities have type
MATCH (e:Entity)
WHERE e.type IS NULL
RETURN COUNT(e) AS entities_without_type;
// Expected: 0

// Show type distribution
MATCH (e:Entity)
WHERE e.type IS NOT NULL
RETURN e.type AS type, COUNT(e) AS count
ORDER BY count DESC
LIMIT 20;

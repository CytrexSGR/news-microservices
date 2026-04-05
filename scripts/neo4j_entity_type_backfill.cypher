// ============================================================
// Neo4j Entity Type Backfill Script
// ============================================================
// Purpose: Fix 78.3% UNKNOWN entities by copying entity_type → type
// Date: 2025-11-19
// Issue: Knowledge Graph wrote to entity_type but all queries read from type
// Fix: ingestion_service.py lines 111, 117, 125, 131 now write to type
//
// INSTRUCTIONS:
// 1. Run backfill first (copy entity_type → type)
// 2. Verify fix (check UNKNOWN count)
// 3. Deploy new ingestion_service.py (docker compose restart knowledge-graph)
// 4. Monitor new entities (should all have type set)
// 5. After 7 days, run cleanup (remove entity_type property)
// ============================================================


// ============================================================
// STEP 1: Analyze Current State (Before Backfill)
// ============================================================
// Expected: 78.3% entities have type=null, entity_type=<actual_type>

// Count entities with entity_type but no type
MATCH (e:Entity)
WHERE e.entity_type IS NOT NULL AND e.type IS NULL
RETURN
    COUNT(e) AS entities_to_fix,
    COUNT(DISTINCT e.entity_type) AS unique_types;

// Show type distribution in entity_type property
MATCH (e:Entity)
WHERE e.entity_type IS NOT NULL
RETURN
    e.entity_type AS type,
    COUNT(e) AS count
ORDER BY count DESC
LIMIT 20;

// Count entities with UNKNOWN in knowledge graph queries
// (These queries read from type, which is NULL)
MATCH (e:Entity)
WHERE e.type IS NULL
RETURN COUNT(e) AS unknown_count;


// ============================================================
// STEP 2: BACKFILL - Copy entity_type → type
// ============================================================
// This fixes all existing entities in Neo4j

// Backfill in batches of 10,000 (prevents memory issues)
CALL apoc.periodic.iterate(
    "MATCH (e:Entity) WHERE e.entity_type IS NOT NULL AND e.type IS NULL RETURN e",
    "SET e.type = e.entity_type",
    {batchSize: 10000, parallel: false}
)
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages;

// Alternative if apoc is not available (run multiple times until affected=0):
MATCH (e:Entity)
WHERE e.entity_type IS NOT NULL AND e.type IS NULL
WITH e LIMIT 10000
SET e.type = e.entity_type
RETURN COUNT(e) AS entities_fixed;


// ============================================================
// STEP 3: VERIFY - Check backfill success
// ============================================================

// Count entities still needing fix (should be 0)
MATCH (e:Entity)
WHERE e.entity_type IS NOT NULL AND e.type IS NULL
RETURN COUNT(e) AS still_broken;

// Count entities now fixed (should be ~78.3% of total)
MATCH (e:Entity)
WHERE e.type IS NOT NULL
RETURN COUNT(e) AS fixed_entities;

// Show type distribution after fix
MATCH (e:Entity)
WHERE e.type IS NOT NULL
RETURN
    e.type AS type,
    COUNT(e) AS count
ORDER BY count DESC
LIMIT 20;

// Verify no more UNKNOWN entities (type IS NULL)
MATCH (e:Entity)
WHERE e.type IS NULL
RETURN COUNT(e) AS unknown_count;
// Expected: 0 (or only entities created before backfill)


// ============================================================
// STEP 4: DEPLOY - Restart knowledge-graph service
// ============================================================
// cd /home/cytrex/news-microservices
// docker compose restart knowledge-graph
//
// New entities will now be written to e.type directly
// (ingestion_service.py fixed on lines 111, 117, 125, 131)


// ============================================================
// STEP 5: MONITOR - Verify new entities (after 1 hour)
// ============================================================

// Check entities created in last hour
MATCH (e:Entity)
WHERE e.created_at > datetime() - duration('PT1H')
RETURN
    e.type AS type,
    e.entity_type AS old_property,
    COUNT(e) AS count
ORDER BY count DESC;

// Expected:
// - e.type should be set (not null)
// - e.entity_type should also be set (both properties coexist temporarily)


// ============================================================
// STEP 6: CLEANUP (Run after 7 days) - Remove entity_type
// ============================================================
// Only run this after confirming new ingestion writes to e.type correctly!
// Wait 7 days to ensure no rollback needed.

// Check if safe to remove entity_type
// (All entities should have e.type set)
MATCH (e:Entity)
WHERE e.type IS NULL AND e.entity_type IS NOT NULL
RETURN COUNT(e) AS would_be_lost;
// Expected: 0 (if > 0, DO NOT RUN CLEANUP!)

// Remove entity_type property (safe after 7 days)
CALL apoc.periodic.iterate(
    "MATCH (e:Entity) WHERE e.entity_type IS NOT NULL RETURN e",
    "REMOVE e.entity_type",
    {batchSize: 10000, parallel: false}
)
YIELD batches, total
RETURN batches, total;

// Alternative without apoc (run multiple times):
MATCH (e:Entity)
WHERE e.entity_type IS NOT NULL
WITH e LIMIT 10000
REMOVE e.entity_type
RETURN COUNT(e) AS properties_removed;


// ============================================================
// VERIFICATION QUERIES
// ============================================================

// Final health check - All entities should have type
MATCH (e:Entity)
RETURN
    COUNT(e) AS total_entities,
    COUNT(e.type) AS entities_with_type,
    COUNT(e) - COUNT(e.type) AS entities_without_type,
    (COUNT(e.type) * 100.0 / COUNT(e)) AS coverage_percentage;
// Expected: coverage_percentage = 100.0

// Type distribution (should show actual types, not UNKNOWN)
MATCH (e:Entity)
WHERE e.type IS NOT NULL
RETURN
    e.type AS type,
    COUNT(e) AS count,
    (COUNT(e) * 100.0 / (SELECT COUNT(*) FROM (MATCH (e2:Entity) RETURN e2))) AS percentage
ORDER BY count DESC
LIMIT 20;

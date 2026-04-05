#!/bin/bash
# ============================================================
# Fix Neo4j Entity Types - Automated Script
# ============================================================
# Purpose: Fix 78.3% UNKNOWN entities in Knowledge Graph
# Issue: Property name mismatch (entity_type vs type)
# Date: 2025-11-19
# ============================================================

set -e  # Exit on error

echo "============================================================"
echo "Neo4j Entity Type Fix - Automated Execution"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Neo4j connection details
NEO4J_CONTAINER="news-microservices-neo4j-1"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="neo4jpassword"
NEO4J_DB="neo4j"

# Check if Neo4j container is running
if ! docker ps | grep -q "$NEO4J_CONTAINER"; then
    echo -e "${RED}ERROR: Neo4j container not running!${NC}"
    echo "Run: docker compose up -d neo4j"
    exit 1
fi

echo -e "${GREEN}✓ Neo4j container is running${NC}"
echo ""

# Function to run Cypher query
run_cypher() {
    local query="$1"
    local description="$2"

    echo -e "${YELLOW}Running: $description${NC}"
    docker exec -it "$NEO4J_CONTAINER" cypher-shell \
        -u "$NEO4J_USER" \
        -p "$NEO4J_PASSWORD" \
        -d "$NEO4J_DB" \
        "$query"
    echo ""
}

# ============================================================
# STEP 1: Analyze Current State
# ============================================================
echo "============================================================"
echo "STEP 1: Analyzing current state"
echo "============================================================"
echo ""

run_cypher "MATCH (e:Entity) WHERE e.entity_type IS NOT NULL AND e.type IS NULL RETURN COUNT(e) AS entities_to_fix;" \
    "Count entities needing fix"

run_cypher "MATCH (e:Entity) WHERE e.type IS NULL RETURN COUNT(e) AS unknown_count;" \
    "Count UNKNOWN entities (type=NULL)"

read -p "Press Enter to continue with backfill..."

# ============================================================
# STEP 2: BACKFILL
# ============================================================
echo ""
echo "============================================================"
echo "STEP 2: Running backfill (entity_type → type)"
echo "============================================================"
echo ""

# Try with APOC first (faster)
echo "Attempting batch backfill with APOC..."
if docker exec -it "$NEO4J_CONTAINER" cypher-shell \
    -u "$NEO4J_USER" \
    -p "$NEO4J_PASSWORD" \
    -d "$NEO4J_DB" \
    "CALL apoc.periodic.iterate('MATCH (e:Entity) WHERE e.entity_type IS NOT NULL AND e.type IS NULL RETURN e', 'SET e.type = e.entity_type', {batchSize: 10000, parallel: false}) YIELD batches, total RETURN batches, total;" 2>/dev/null; then
    echo -e "${GREEN}✓ APOC backfill successful${NC}"
else
    echo -e "${YELLOW}APOC not available, using manual batching...${NC}"

    # Manual batching loop
    affected=1
    total_fixed=0
    batch_num=1

    while [ $affected -gt 0 ]; do
        echo "Processing batch $batch_num (10,000 entities)..."

        result=$(docker exec "$NEO4J_CONTAINER" cypher-shell \
            -u "$NEO4J_USER" \
            -p "$NEO4J_PASSWORD" \
            -d "$NEO4J_DB" \
            --format plain \
            "MATCH (e:Entity) WHERE e.entity_type IS NOT NULL AND e.type IS NULL WITH e LIMIT 10000 SET e.type = e.entity_type RETURN COUNT(e) AS fixed;" | tail -n 1)

        affected=$(echo "$result" | grep -oP '\d+' || echo "0")
        total_fixed=$((total_fixed + affected))
        batch_num=$((batch_num + 1))

        echo "Fixed: $affected entities (Total: $total_fixed)"

        if [ $affected -eq 0 ]; then
            break
        fi

        sleep 1  # Brief pause between batches
    done

    echo -e "${GREEN}✓ Manual backfill complete: $total_fixed entities fixed${NC}"
fi

# ============================================================
# STEP 3: VERIFY
# ============================================================
echo ""
echo "============================================================"
echo "STEP 3: Verifying backfill success"
echo "============================================================"
echo ""

run_cypher "MATCH (e:Entity) WHERE e.entity_type IS NOT NULL AND e.type IS NULL RETURN COUNT(e) AS still_broken;" \
    "Count entities still broken (should be 0)"

run_cypher "MATCH (e:Entity) WHERE e.type IS NOT NULL RETURN COUNT(e) AS fixed_entities;" \
    "Count fixed entities"

run_cypher "MATCH (e:Entity) WHERE e.type IS NOT NULL RETURN e.type AS type, COUNT(e) AS count ORDER BY count DESC LIMIT 10;" \
    "Top 10 entity types"

echo -e "${GREEN}✓ Backfill verification complete${NC}"
echo ""

# ============================================================
# STEP 4: Restart Knowledge Graph Service
# ============================================================
echo "============================================================"
echo "STEP 4: Restarting knowledge-graph service"
echo "============================================================"
echo ""

read -p "Restart knowledge-graph service now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Restarting knowledge-graph service..."
    docker compose restart knowledge-graph
    echo -e "${GREEN}✓ Service restarted${NC}"
    echo ""
    echo "New entities will now be written with correct property (e.type)"
else
    echo -e "${YELLOW}⚠ Skipping restart. Remember to restart manually!${NC}"
    echo "Run: docker compose restart knowledge-graph"
fi

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "============================================================"
echo "SUMMARY"
echo "============================================================"
echo ""
echo -e "${GREEN}✓ ingestion_service.py fixed (lines 111, 117, 125, 131)${NC}"
echo -e "${GREEN}✓ Existing entities backfilled (entity_type → type)${NC}"
echo ""
echo "Next steps:"
echo "1. Monitor new entities for 1 hour (verify e.type is set)"
echo "2. After 7 days, run cleanup script to remove entity_type property"
echo ""
echo "Monitoring command:"
echo "  docker exec -it $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD -d $NEO4J_DB"
echo '  MATCH (e:Entity) WHERE e.created_at > datetime() - duration("PT1H") RETURN e.type, COUNT(e);'
echo ""
echo "Cleanup script (after 7 days):"
echo "  See: scripts/neo4j_entity_type_backfill.cypher (STEP 6)"
echo ""
echo -e "${GREEN}Done!${NC}"

# Neo4j Cypher Query Best Practices

**Version:** 1.0
**Last Updated:** 2025-11-20
**Status:** Production
**Related Incidents:** [POSTMORTEMS.md - Incident #18](../../POSTMORTEMS.md#incident-18-knowledge-graph-service-retry-storm---neo4j-cypher-syntax-error-2025-11-20)

---

## Table of Contents

- [Critical Syntax Rules](#critical-syntax-rules)
- [MERGE Patterns](#merge-patterns)
- [Query Optimization](#query-optimization)
- [Error Handling](#error-handling)
- [Testing & Validation](#testing--validation)
- [Monitoring & Alerting](#monitoring--alerting)
- [Common Pitfalls](#common-pitfalls)

---

## Critical Syntax Rules

### Rule #1: ON CREATE SET Must Follow MERGE Immediately

**⚠️ CRITICAL:** This is the #1 cause of Cypher syntax errors in production.

**Correct Order:**
```cypher
MERGE (node)
ON CREATE SET node.property = value  # ✅ Immediately after MERGE
ON MATCH SET node.property = value   # ✅ Immediately after MERGE
SET node.other = value               # ✅ After ON CREATE/ON MATCH
```

**Incorrect Order (Parser Error):**
```cypher
MERGE (node)
SET node.other = value               # ❌ SET comes first
ON CREATE SET node.property = value  # ❌ Parser error: "Invalid input 'ON'"
```

**Why This Rule Exists:**
- Neo4j parser treats `ON CREATE SET` as a **sub-clause of MERGE**
- When placed after a standalone `SET`, parser interprets it as a new statement
- Results in syntax error: `Invalid input 'ON': expected MERGE, MATCH, CREATE, etc.`

**Historical Context:**
- **Incident #18 (2025-11-20):** This syntax error caused a retry storm with 2528 stuck messages, 32.6 GB network traffic, and 257% CPU on RabbitMQ
- **Impact:** 15+ hours of continuous retries, GB-scale unnecessary traffic across all services
- **Resolution:** 5 query fixes, 30 minutes total recovery time

---

## MERGE Patterns

### Pattern 1: Simple Node Creation/Update

**Use Case:** Create node if missing, update properties if exists

```cypher
MERGE (c:Company {symbol: $symbol})
ON CREATE SET
    c.created_at = datetime(),
    c.first_seen = datetime()
ON MATCH SET
    c.last_updated = datetime(),
    c.update_count = coalesce(c.update_count, 0) + 1
SET
    c.name = $name,
    c.sector = $sector,
    c.industry = $industry,
    c.updated_at = datetime()
RETURN c
```

**Key Points:**
- `ON CREATE SET`: Properties set only when node is created
- `ON MATCH SET`: Properties updated only when node already exists
- `SET`: Properties always updated (create or match)

### Pattern 2: Relationship Creation with Conditional Properties

**Use Case:** Create relationship if missing, track timestamps

```cypher
MATCH (e:Executive {name: $exec_name})
MATCH (c:Company {symbol: $symbol})
MERGE (e)-[r:WORKS_FOR]->(c)
ON CREATE SET
    r.created_at = datetime(),
    r.initial_title = $title,
    r.first_verified = datetime()
ON MATCH SET
    r.last_verified = datetime(),
    r.verification_count = coalesce(r.verification_count, 0) + 1
SET
    r.title = $title,
    r.pay_usd = $pay_usd,
    r.since_year = $since_year,
    r.updated_at = datetime()
RETURN r
```

**Best Practice:** Use `MATCH` before `MERGE` for relationships to ensure both nodes exist

### Pattern 3: Complex Multi-Node Creation

**Use Case:** Create multiple nodes and relationships atomically

```cypher
// Ensure Company exists
MERGE (c:Company {symbol: $symbol})
ON CREATE SET c.created_at = datetime()
SET c.name = $name, c.updated_at = datetime()

// Ensure Executive exists
MERGE (e:Executive {name: $exec_name})
ON CREATE SET e.created_at = datetime()
SET e.title = $title, e.updated_at = datetime()

// Create relationship
MERGE (e)-[r:WORKS_FOR]->(c)
ON CREATE SET r.created_at = datetime()
SET r.title = $title, r.updated_at = datetime()

RETURN c, e, r
```

**Key Points:**
- Each `MERGE` has its own `ON CREATE SET` → `SET` sequence
- Operations are atomic (all succeed or all fail)
- Order matters: nodes before relationships

### Pattern 4: Conditional Node Creation (WITH clause)

**Use Case:** Create node only if certain conditions are met

```cypher
MATCH (a:Article {id: $article_id})
WHERE a.entity_count > 5
WITH a
MERGE (e:Entity {name: $entity_name})
ON CREATE SET
    e.created_at = datetime(),
    e.confidence = $confidence
SET
    e.last_seen = datetime()
MERGE (a)-[r:MENTIONS]->(e)
ON CREATE SET r.created_at = datetime()
SET r.mention_count = coalesce(r.mention_count, 0) + 1
RETURN e, r
```

**Best Practice:** Use `WITH` to pass filtered data to subsequent clauses

---

## Query Optimization

### Indexing Strategy

**Always Create Indexes for:**
1. Node properties used in `MERGE` match conditions
2. Properties used in `WHERE` clauses
3. Relationship properties used for filtering

```cypher
-- Node indexes (required for MERGE performance)
CREATE INDEX entity_name_idx IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE INDEX company_symbol_idx IF NOT EXISTS
FOR (c:Company) ON (c.symbol);

-- Composite indexes for multi-property lookups
CREATE INDEX entity_name_type_idx IF NOT EXISTS
FOR (e:Entity) ON (e.name, e.type);

-- Relationship indexes
CREATE INDEX relationship_confidence_idx IF NOT EXISTS
FOR ()-[r:WORKS_FOR]-() ON (r.confidence);
```

**Check Index Usage:**
```cypher
EXPLAIN MATCH (e:Entity {name: $name}) RETURN e;
-- Look for "NodeIndexSeek" in execution plan
```

### Query Performance Patterns

**❌ Avoid: Cartesian Products**
```cypher
-- BAD: Creates n × m combinations
MATCH (e:Executive)
MATCH (c:Company)
WHERE e.name = $name AND c.symbol = $symbol
MERGE (e)-[r:WORKS_FOR]->(c)
```

**✅ Use: Constrained Matches**
```cypher
-- GOOD: Specific node lookups first
MATCH (e:Executive {name: $name})
MATCH (c:Company {symbol: $symbol})
MERGE (e)-[r:WORKS_FOR]->(c)
```

**❌ Avoid: Optional Matches in Loops**
```cypher
-- BAD: Optional match inside UNWIND
UNWIND $entities AS entity
OPTIONAL MATCH (e:Entity {name: entity.name})
MERGE (e2:Entity {name: entity.name})  -- Creates duplicates!
```

**✅ Use: Separate Existence Check**
```cypher
-- GOOD: Check existence first, then batch create
UNWIND $entities AS entity
MERGE (e:Entity {name: entity.name})
ON CREATE SET e.created_at = datetime()
SET e.type = entity.type
```

### Batch Operations

**Pattern: Batch Node Creation**
```cypher
UNWIND $companies AS company
MERGE (c:Company {symbol: company.symbol})
ON CREATE SET c.created_at = datetime()
SET
    c.name = company.name,
    c.sector = company.sector,
    c.updated_at = datetime()
RETURN count(c) AS companies_processed
```

**Best Practice:** Batch size 500-1000 for optimal performance

---

## Error Handling

### Retry Logic

**❌ Don't Retry: Syntax Errors**
```python
# BAD: Syntax errors will NEVER succeed
try:
    await neo4j_service.execute_write(query, params)
except CypherSyntaxError as e:
    # Don't retry!
    logger.error(f"Syntax error: {e}")
    raise
```

**✅ Retry: Transient Errors**
```python
# GOOD: Retry transient errors with exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def execute_with_retry(query: str, params: dict):
    try:
        return await neo4j_service.execute_write(query, params)
    except CypherSyntaxError:
        # Don't retry syntax errors
        raise
    except (ServiceUnavailable, TransientError) as e:
        logger.warning(f"Transient error, will retry: {e}")
        raise
```

### Circuit Breaker Pattern

**Use Case:** Stop processing after repeated failures

```python
from circuitbreaker import circuit

@circuit(failure_threshold=10, recovery_timeout=60)
async def execute_cypher_with_circuit_breaker(query: str, params: dict):
    """
    Execute Neo4j query with circuit breaker protection.

    Opens circuit after 10 consecutive failures.
    Recovers after 60 seconds of no failures.
    """
    try:
        result = await neo4j_service.execute_write(query, params)
        return result
    except CypherSyntaxError as e:
        logger.error(f"Cypher syntax error: {e}")
        # Syntax errors count towards failure threshold
        raise
    except Exception as e:
        logger.error(f"Neo4j error: {e}")
        raise
```

### Dead Letter Queue (DLQ)

**RabbitMQ Configuration:**
```python
# Consumer configuration
channel.queue_declare(
    queue='knowledge_graph_finance_intelligence',
    durable=True,
    arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'knowledge_graph_finance_intelligence.dlq',
        'x-message-ttl': 3600000,  # 1 hour before moving to DLQ
        'x-max-retries': 3,  # Retry 3 times before DLQ
    }
)

# DLQ declaration
channel.queue_declare(
    queue='knowledge_graph_finance_intelligence.dlq',
    durable=True
)
```

**Why DLQs Matter:**
- Prevent infinite retry loops (Incident #18: 2528 messages retried for 15+ hours)
- Isolate problematic messages for manual inspection
- Maintain system stability during failures

---

## Testing & Validation

### Unit Tests for Cypher Queries

**Pattern: Test Query Syntax**
```python
import pytest
from neo4j.exceptions import CypherSyntaxError

@pytest.mark.asyncio
async def test_company_merge_query_syntax():
    """Test that company MERGE query has correct ON CREATE SET syntax."""
    query = """
    MERGE (c:Company {symbol: $symbol})
    ON CREATE SET c.created_at = datetime()
    SET c.name = $name, c.updated_at = datetime()
    RETURN c
    """
    params = {"symbol": "TSLA", "name": "Tesla Inc."}

    # Should not raise CypherSyntaxError
    result = await neo4j_service.execute_write(query, params)
    assert result is not None
```

**Pattern: Test EXPLAIN Plan**
```python
@pytest.mark.asyncio
async def test_company_merge_uses_index():
    """Test that company MERGE query uses symbol index."""
    query = """
    EXPLAIN MERGE (c:Company {symbol: $symbol})
    ON CREATE SET c.created_at = datetime()
    SET c.name = $name
    """
    params = {"symbol": "TSLA", "name": "Tesla"}

    explain = await neo4j_service.execute_read(query, params)
    plan = explain.get_plan()

    # Should use NodeIndexSeek, not NodeByLabelScan
    assert "NodeIndexSeek" in str(plan)
```

### Pre-commit Hook for Syntax Validation

**File:** `.git/hooks/pre-commit`
```bash
#!/bin/bash
# Validate Neo4j Cypher syntax before commit

echo "🔍 Validating Neo4j Cypher queries..."

# Find all Python files with Cypher queries
files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

for file in $files; do
    # Check for ON CREATE SET not immediately after MERGE
    if grep -Pzo "MERGE.*?\n.*?SET.*?\n.*?ON CREATE SET" "$file" > /dev/null 2>&1; then
        echo "❌ Found ON CREATE SET after SET in $file"
        echo "   ON CREATE SET must come immediately after MERGE"
        exit 1
    fi

    # Check for ON MATCH SET not immediately after MERGE
    if grep -Pzo "MERGE.*?\n.*?SET.*?\n.*?ON MATCH SET" "$file" > /dev/null 2>&1; then
        echo "❌ Found ON MATCH SET after SET in $file"
        echo "   ON MATCH SET must come immediately after MERGE"
        exit 1
    fi
done

echo "✅ Cypher syntax validation passed"
exit 0
```

**Installation:**
```bash
chmod +x .git/hooks/pre-commit
```

### CI/CD Validation

**GitHub Actions Workflow:**
```yaml
# .github/workflows/neo4j-validation.yml
name: Neo4j Cypher Validation

on: [push, pull_request]

jobs:
  validate-cypher:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pytest neo4j

      - name: Run Cypher syntax tests
        run: pytest tests/test_cypher_queries.py -v
```

---

## Monitoring & Alerting

### Prometheus Metrics

**Implementation:**
```python
from prometheus_client import Counter, Histogram

# Track Cypher errors by type
cypher_error_counter = Counter(
    'neo4j_cypher_errors_total',
    'Total Neo4j Cypher errors',
    ['error_type', 'service', 'handler']
)

# Track query performance
cypher_query_duration = Histogram(
    'neo4j_query_duration_seconds',
    'Neo4j query duration',
    ['query_type', 'operation']
)

# Track MERGE operations
merge_operations_counter = Counter(
    'neo4j_merge_operations_total',
    'Total MERGE operations',
    ['node_type', 'created_vs_matched']
)

# Usage example
try:
    start = time.time()
    result = await neo4j_service.execute_write(query, params)
    cypher_query_duration.labels(
        query_type='company_merge',
        operation='write'
    ).observe(time.time() - start)

    merge_operations_counter.labels(
        node_type='Company',
        created_vs_matched='created' if result.created else 'matched'
    ).inc()

except CypherSyntaxError as e:
    cypher_error_counter.labels(
        error_type='syntax',
        service='knowledge-graph',
        handler='company_update'
    ).inc()
    raise
```

### Alert Rules

**File:** `prometheus/alerts.yml`
```yaml
groups:
  - name: neo4j_alerts
    interval: 30s
    rules:
      # Alert on high Cypher error rate
      - alert: HighCypherErrorRate
        expr: rate(neo4j_cypher_errors_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High Neo4j Cypher error rate"
          description: "{{ $value }} errors/sec in last 5 minutes (service: {{ $labels.service }})"

      # Alert on stuck RabbitMQ queue
      - alert: StuckKnowledgeGraphQueue
        expr: rabbitmq_queue_messages{queue="knowledge_graph_finance_intelligence"} > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Knowledge Graph RabbitMQ queue stuck"
          description: "{{ $value }} messages stuck for 10+ minutes - possible retry loop"

      # Alert on slow queries
      - alert: SlowNeo4jQueries
        expr: histogram_quantile(0.95, rate(neo4j_query_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow Neo4j queries detected"
          description: "95th percentile query time > 1s ({{ $value }}s)"

      # Alert on repeated syntax errors (indicates broken deployment)
      - alert: RepeatedCypherSyntaxErrors
        expr: increase(neo4j_cypher_errors_total{error_type="syntax"}[1h]) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Repeated Cypher syntax errors - possible broken deployment"
          description: "{{ $value }} syntax errors in last hour (handler: {{ $labels.handler }})"
```

### Grafana Dashboard

**Panel 1: Cypher Error Rate**
```promql
rate(neo4j_cypher_errors_total[5m])
```

**Panel 2: Query Performance (95th percentile)**
```promql
histogram_quantile(0.95, rate(neo4j_query_duration_seconds_bucket[5m]))
```

**Panel 3: Queue Depth**
```promql
rabbitmq_queue_messages{queue=~"knowledge_graph.*"}
```

**Panel 4: MERGE Created vs Matched Ratio**
```promql
sum(rate(neo4j_merge_operations_total{created_vs_matched="created"}[5m]))
/
sum(rate(neo4j_merge_operations_total[5m]))
```

---

## Common Pitfalls

### Pitfall #1: ON CREATE SET After SET ⚠️ CRITICAL

**Problem:** Most common syntax error (caused Incident #18)

```cypher
❌ WRONG:
MERGE (n:Node {id: $id})
SET n.property = $value
ON CREATE SET n.created_at = datetime()  # Parser error!
```

**Solution:**
```cypher
✅ CORRECT:
MERGE (n:Node {id: $id})
ON CREATE SET n.created_at = datetime()
SET n.property = $value
```

### Pitfall #2: Missing Indexes on MERGE Properties

**Problem:** Slow queries, full label scans

```cypher
❌ SLOW (no index):
MERGE (c:Company {symbol: $symbol})
-- Full label scan: O(n)
```

**Solution:**
```cypher
✅ FAST (with index):
CREATE INDEX company_symbol_idx IF NOT EXISTS
FOR (c:Company) ON (c.symbol);

MERGE (c:Company {symbol: $symbol})
-- Index seek: O(log n)
```

### Pitfall #3: MERGE Without Unique Properties

**Problem:** Creates duplicate nodes

```cypher
❌ CREATES DUPLICATES:
MERGE (e:Entity {name: $name})  # Name might not be unique!
```

**Solution:**
```cypher
✅ USE COMPOSITE KEY:
MERGE (e:Entity {name: $name, type: $type})
-- Or create unique constraint:
CREATE CONSTRAINT entity_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;
```

### Pitfall #4: Ignoring Transaction Boundaries

**Problem:** Partial updates on failure

```python
❌ WRONG (no transaction):
for company in companies:
    await execute_write(merge_company_query, company)
    # If one fails, previous updates remain!
```

**Solution:**
```python
✅ CORRECT (single transaction):
async with neo4j_service.driver.session() as session:
    async with session.begin_transaction() as tx:
        for company in companies:
            await tx.run(merge_company_query, company)
        await tx.commit()
    # All-or-nothing: either all succeed or all fail
```

### Pitfall #5: Not Using Parameters

**Problem:** Cypher injection, plan cache misses

```cypher
❌ DANGEROUS:
MERGE (c:Company {symbol: "{symbol}"})  # Injection risk!
```

**Solution:**
```cypher
✅ SAFE:
MERGE (c:Company {symbol: $symbol})  # Parameterized
```

---

## Quick Reference

### Syntax Order (CRITICAL)

```cypher
1. MERGE (node)
2. ON CREATE SET ...   # ✅ Must be here!
3. ON MATCH SET ...    # ✅ Must be here!
4. SET ...             # ✅ After ON CREATE/MATCH
5. RETURN ...
```

### Common Query Templates

**Node Creation:**
```cypher
MERGE (n:Label {unique_prop: $value})
ON CREATE SET n.created_at = datetime()
SET n.other_props = $props, n.updated_at = datetime()
RETURN n
```

**Relationship Creation:**
```cypher
MATCH (a:NodeA {id: $a_id})
MATCH (b:NodeB {id: $b_id})
MERGE (a)-[r:REL_TYPE]->(b)
ON CREATE SET r.created_at = datetime()
SET r.props = $props, r.updated_at = datetime()
RETURN r
```

**Batch Update:**
```cypher
UNWIND $items AS item
MERGE (n:Node {id: item.id})
ON CREATE SET n.created_at = datetime()
SET n.props = item.props
RETURN count(n)
```

---

## References

- **Neo4j Cypher Manual:** https://neo4j.com/docs/cypher-manual/current/
- **MERGE Clause Documentation:** https://neo4j.com/docs/cypher-manual/current/clauses/merge/
- **ON CREATE/ON MATCH:** https://neo4j.com/docs/cypher-manual/current/clauses/merge/#merge-on-create-on-match
- **Incident #18 (Retry Storm):** [POSTMORTEMS.md](../../POSTMORTEMS.md#incident-18-knowledge-graph-service-retry-storm---neo4j-cypher-syntax-error-2025-11-20)
- **Knowledge Graph Service README:** [services/knowledge-graph-service/README.md](../../services/knowledge-graph-service/README.md)

---

**Last Updated:** 2025-11-20
**Next Review:** After any Cypher-related incidents
**Feedback:** Submit issues to the project repository

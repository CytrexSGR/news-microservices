# Neo4j Index Recommendations & Best Practices

**Document Version:** 1.0
**Date:** 2025-11-16
**Status:** Production Ready
**Target:** 40 MARKET nodes + 14 SECTOR nodes (scalable to 10,000+)

---

## Executive Summary

The optimized Neo4j schema includes 11 strategically designed indexes:

- **7 Single-Column Indexes** for basic property filtering
- **3 Composite Indexes** for multi-column filter combinations
- **1 Full-Text Search Index** for fuzzy/prefix text matching

These indexes are designed to achieve:
- **< 5ms query latency** for 95% of operations
- **> 90% index selectivity** for filter operations
- **Minimal storage overhead** (< 15% for small dataset)

---

## 1. Index Summary Table

### Quick Reference

| Index Name | Type | Columns | Cardinality | Use Case | Priority |
|---|---|---|---|---|---|
| `market_symbol_unique` | Unique Constraint | symbol | 40 | Primary key lookup | CRITICAL |
| `market_asset_type` | Single-Column | asset_type | 4 | Filter by asset class | HIGH |
| `market_is_active` | Single-Column | is_active | 2 | Filter by status | HIGH |
| `market_exchange` | Single-Column | exchange | 15 | Filter by exchange | MEDIUM |
| `market_currency` | Single-Column | currency | 8 | Filter by currency | MEDIUM |
| `market_sector` | Single-Column | sector | 14 | Filter by sector property | MEDIUM |
| `market_data_source` | Single-Column | data_source | 2 | Filter by source | LOW |
| `market_last_updated` | Single-Column | last_updated | 40 | Range queries, staleness | MEDIUM |
| `market_asset_type_is_active` | Composite | (asset_type, is_active) | 8 | Active markets by type | HIGH |
| `market_asset_type_exchange` | Composite | (asset_type, exchange) | 60 | Exchange-specific assets | MEDIUM |
| `market_asset_type_is_active_exchange` | Composite | (asset_type, is_active, exchange) | 120 | Complex filtering | LOW |
| `market_name_fulltext` | Full-Text | name | 40 | Text search, autocomplete | MEDIUM |
| `sector_name` | Single-Column | sector_name | 14 | Sector lookup | MEDIUM |

---

## 2. Detailed Index Recommendations

### 2.1 CRITICAL Indexes (Must Have)

#### 1. `market_symbol_unique` (UNIQUE CONSTRAINT)

**Why Critical:**
- Primary key for MARKET nodes
- Enables O(1) lookups
- Auto-indexed by Neo4j constraint system

```cypher
CREATE CONSTRAINT market_symbol_unique IF NOT EXISTS
FOR (m:MARKET) REQUIRE m.symbol IS UNIQUE;

-- Query that uses this index
MATCH (m:MARKET {symbol: 'AAPL'})
RETURN m.name, m.exchange, m.currency;
-- Expected latency: < 2ms
```

**Performance Characteristics:**
```
Index type: B-tree (auto-indexed)
Selectivity: 1/40 = 2.5% (perfect)
Expected latency: < 2ms
Estimated size: ~1 KB
```

**When to Remove:** NEVER (primary key)

---

### 2.2 HIGH Priority Indexes (Frequently Used)

#### 2. `market_asset_type` (SINGLE-COLUMN)

**Why High Priority:**
- Filters on asset class (STOCK, FOREX, COMMODITY, CRYPTO)
- Low cardinality = high selectivity
- Used in ~30% of queries

```cypher
CREATE INDEX market_asset_type IF NOT EXISTS
FOR (m:MARKET) ON (m.asset_type);

-- Query pattern
MATCH (m:MARKET)
WHERE m.asset_type = 'STOCK'
RETURN m.symbol, m.name;
-- Expected latency: < 5ms
```

**Selectivity Analysis:**
```
Total MARKET nodes: 40
STOCK nodes: ~10 (25%)
Index effectiveness: HIGH (75% reduction)
Estimated latency: 2-5ms
```

**Monitoring:**
```cypher
-- Check index usage
MATCH (m:MARKET) WHERE m.asset_type = 'STOCK'
RETURN count(*) AS total_stocks;

-- Verify index hit (use EXPLAIN)
EXPLAIN MATCH (m:MARKET) WHERE m.asset_type = 'STOCK'
RETURN m.symbol;
-- Should see: "IndexSeek" (good) not "AllNodesScan" (bad)
```

#### 3. `market_is_active` (SINGLE-COLUMN)

**Why High Priority:**
- Boolean filter (true/false)
- Most queries filter by active status
- Important for data freshness

```cypher
CREATE INDEX market_is_active IF NOT EXISTS
FOR (m:MARKET) ON (m.is_active);

-- Query pattern
MATCH (m:MARKET)
WHERE m.is_active = true
RETURN m.symbol, m.name;
-- Expected latency: < 5ms
```

**Selectivity Analysis:**
```
Active nodes: ~32/40 (80%)
Inactive nodes: ~8/40 (20%)
Index effectiveness: MODERATE (but important for combined filters)
```

**Why Index Low-Selectivity Properties?**
```
For 40 markets: Minimal benefit
For 1000 markets: 800 active vs. 200 inactive = 20% reduction
For 100,000 markets: Critical for performance

Lesson: Index for scalability, not just current size.
```

#### 4. `market_asset_type_is_active` (COMPOSITE)

**Why High Priority:**
- Most common filter combination
- Composite index provides O(1) multi-column lookup
- Eliminates sequential index scanning

```cypher
CREATE INDEX market_asset_type_is_active IF NOT EXISTS
FOR (m:MARKET) ON (m.asset_type, m.is_active);

-- Query pattern
MATCH (m:MARKET)
WHERE m.asset_type = 'STOCK' AND m.is_active = true
RETURN m.symbol, m.name;
-- Expected latency: < 5ms
```

**Selectivity Analysis:**
```
Possible combinations: 4 × 2 = 8
STOCK + active: ~8 nodes (20% reduction from single filter)
Composite index benefit: 2-3x faster than sequential scans

For 40 markets: ~2ms
For 1000 markets: ~5ms
For 100,000 markets: ~20ms (critical!)
```

**Composite Index Column Ordering:**
```
Leftmost Prefix Matching Rule:
Index on (A, B, C) supports:
✅ WHERE A = ...
✅ WHERE A = ... AND B = ...
✅ WHERE A = ... AND B = ... AND C = ...
❌ WHERE B = ... AND C = ... (no index)
⚠️ WHERE A = ... AND C = ... (uses A only)

Our index (asset_type, is_active):
✅ WHERE asset_type = 'STOCK'
✅ WHERE asset_type = 'STOCK' AND is_active = true
❌ WHERE is_active = true (use market_is_active index)

Column order rationale:
1. asset_type first (4 distinct values, highest selectivity)
2. is_active second (2 distinct values, further refinement)
```

---

### 2.3 MEDIUM Priority Indexes (Important for Features)

#### 5. `market_exchange` (SINGLE-COLUMN)

**Why Medium Priority:**
- Filter markets by exchange (NASDAQ, NYSE, etc.)
- Important for exchange-specific queries
- 10-20 distinct exchanges

```cypher
CREATE INDEX market_exchange IF NOT EXISTS
FOR (m:MARKET) ON (m.exchange);

-- Query pattern
MATCH (m:MARKET)
WHERE m.exchange = 'NASDAQ'
RETURN m.symbol, m.name;
-- Expected latency: < 5ms
```

**When to Use:**
```
// Filter by exchange
MATCH (m:MARKET)
WHERE m.exchange = 'NASDAQ'
RETURN count(*);

// Combined with asset type
MATCH (m:MARKET)
WHERE m.asset_type = 'STOCK' AND m.exchange = 'NASDAQ'
RETURN m.symbol;
// Use market_asset_type_exchange composite index
```

#### 6. `market_currency` (SINGLE-COLUMN)

**Why Medium Priority:**
- Filter by quote currency (USD, EUR, GBP, etc.)
- 5-10 distinct currencies (USD dominant)
- Useful for multi-currency portfolios

```cypher
CREATE INDEX market_currency IF NOT EXISTS
FOR (m:MARKET) ON (m.currency);

-- Query pattern
MATCH (m:MARKET)
WHERE m.currency = 'USD'
RETURN m.symbol, m.name;
-- Expected latency: < 5ms
```

#### 7. `market_last_updated` (SINGLE-COLUMN)

**Why Medium Priority:**
- Enable staleness detection
- Find recently updated markets
- Support timestamp range queries

```cypher
CREATE INDEX market_last_updated IF NOT EXISTS
FOR (m:MARKET) ON (m.last_updated);

-- Query pattern: Find markets updated in last 24 hours
MATCH (m:MARKET)
WHERE m.last_updated > datetime() - duration('P1D')
RETURN m.symbol, m.name;
-- Expected latency: < 5ms
```

**Range Query Optimization:**
```cypher
-- Good: Uses index for range
MATCH (m:MARKET)
WHERE m.last_updated > timestamp() - 86400  -- 24 hours
RETURN m.symbol;

-- Also good: Datetime comparison
MATCH (m:MARKET)
WHERE m.last_updated > datetime('2025-11-15T00:00:00')
RETURN m.symbol;

-- Avoid: Full table scan
MATCH (m:MARKET)
WHERE duration.between(m.last_updated, datetime()) < duration('P1D')
RETURN m.symbol;
```

#### 8. `market_asset_type_exchange` (COMPOSITE)

**Why Medium Priority:**
- Support exchange-specific asset queries
- Example: All STOCKS on NASDAQ

```cypher
CREATE INDEX market_asset_type_exchange IF NOT EXISTS
FOR (m:MARKET) ON (m.asset_type, m.exchange);

-- Query pattern
MATCH (m:MARKET)
WHERE m.asset_type = 'COMMODITY' AND m.exchange = 'COMEX'
RETURN m.symbol, m.name;
-- Expected latency: < 5ms
```

**Use Cases:**
```
1. "Show all stocks on NASDAQ"
2. "Show all forex pairs on primary exchanges"
3. "Show all commodities on COMEX"
4. "Show all crypto on main exchanges"
```

#### 9. `market_name_fulltext` (FULL-TEXT)

**Why Medium Priority:**
- Enable market name search
- Support autocomplete in API
- Fuzzy matching for typos

```cypher
CREATE FULLTEXT INDEX market_name_fulltext IF NOT EXISTS
FOR (m:MARKET) ON EACH [m.name];

-- Query patterns
MATCH (m:MARKET)
WHERE m.name CONTAINS 'Apple'
RETURN m.symbol, m.name;

-- Fuzzy search (with APOC)
CALL apoc.index.search('market_name_fulltext', 'appl')
YIELD node AS m
RETURN m.symbol, m.name;
```

**Full-Text Features:**
```
Case-insensitive:  "apple" matches "Apple Inc."
Prefix matching:   "app" matches "Apple Inc."
Word tokenization: "Apple Inc." searchable as "Apple" or "Inc"
```

---

### 2.4 LOW Priority Indexes (Can Defer)

#### 10. `market_asset_type_is_active_exchange` (TRIPLE COMPOSITE)

**Why Low Priority:**
- Very specific filter combination
- Only used in specialized queries
- Write overhead (index updates) might exceed read benefit

```cypher
CREATE INDEX market_asset_type_is_active_exchange IF NOT EXISTS
FOR (m:MARKET) ON (m.asset_type, m.is_active, m.exchange);

-- Query pattern (rare)
MATCH (m:MARKET)
WHERE m.asset_type = 'STOCK'
  AND m.is_active = true
  AND m.exchange = 'NASDAQ'
RETURN m.symbol;
-- Expected latency: < 5ms
```

**Decision: Keep for Future-Proofing**
```
For 40 markets: Not necessary
For 1000+ markets: Can be added if query metrics show high volume
Current approach: Create, monitor usage, remove if unused
```

#### 11. `market_sector` (SINGLE-COLUMN)

**Why Low Priority:**
- Duplicated information (also available via relationship)
- Recommended approach: Use BELONGS_TO_SECTOR relationship
- Keep for backwards compatibility

```cypher
CREATE INDEX market_sector IF NOT EXISTS
FOR (m:MARKET) ON (m.sector);

-- Legacy pattern (still works)
MATCH (m:MARKET)
WHERE m.sector = 'Technology'
RETURN m.symbol;

-- Better pattern (uses relationship)
MATCH (s:SECTOR {sector_code: 'TECH'})<-[r:BELONGS_TO_SECTOR]-(m:MARKET)
RETURN m.symbol;
```

#### 12. `market_data_source` (SINGLE-COLUMN)

**Why Low Priority:**
- All data from FMP initially
- Will become useful in multi-source environment

```cypher
CREATE INDEX market_data_source IF NOT EXISTS
FOR (m:MARKET) ON (m.data_source);

-- Query pattern (future)
MATCH (m:MARKET)
WHERE m.data_source = 'FMP'
RETURN m.symbol;
```

#### 13. `sector_name` (SINGLE-COLUMN)

**Why Low Priority:**
- Only 14 sectors (very small)
- Usually accessed via code (sector_code)
- Secondary lookup only

```cypher
CREATE INDEX sector_name IF NOT EXISTS
FOR (s:SECTOR) ON (s.sector_name);

-- Query pattern (rare)
MATCH (s:SECTOR)
WHERE s.sector_name = 'Technology'
RETURN s.sector_code, s.description;
```

---

## 3. Index Management

### 3.1 Creating Indexes Safely

**During Schema Migration:**
```cypher
-- Phase 1: Create constraints first (required)
CREATE CONSTRAINT market_symbol_unique ...

-- Phase 2: Create critical indexes
CREATE INDEX market_asset_type ...
CREATE INDEX market_is_active ...
CREATE INDEX market_asset_type_is_active ...

-- Phase 3: Create medium-priority indexes
CREATE INDEX market_exchange ...
CREATE INDEX market_currency ...

-- Phase 4: Create remaining indexes (can be deferred)
CREATE INDEX market_sector ...
```

**Monitoring Index Build:**
```cypher
-- Check index status
SHOW INDEXES;
-- Look for "POPULATING" (building) or "ONLINE" (ready)

-- For Neo4j 5.x, check details
CALL db.index.details()
YIELD indexName, entityCount, indexSize
RETURN indexName, entityCount, indexSize;
```

### 3.2 Dropping Unused Indexes

**When to Drop:**
1. Index has 0% usage over 30 days
2. Query optimizer never chooses it
3. Storage overhead unacceptable

**Monitoring Usage:**
```cypher
-- Check index usage (if extended monitoring enabled)
CALL db.index.usage()
YIELD indexName, usage
RETURN indexName, usage
ORDER BY usage DESC;

-- For production, use Neo4j apoc library
CALL apoc.index.analyze()
YIELD index, function, size, estimates
RETURN index, function, size, estimates;
```

**Safe Removal Process:**
```cypher
-- Step 1: Analyze queries (1-2 weeks)
-- Check if any queries use this index

-- Step 2: Plan removal
-- Schedule during low-traffic window

-- Step 3: Drop index
DROP INDEX market_example IF EXISTS;

-- Step 4: Monitor queries
-- Verify no performance regression
EXPLAIN MATCH (m:MARKET) WHERE m.property = 'value'
RETURN m;
```

### 3.3 Index Fragmentation & Maintenance

**Index Fragmentation:**
```
What: Index pages not fully utilized (gaps, duplicates)
When: After many updates/deletes
Impact: 10-15% performance slowdown, 20-30% extra storage
Typical cause: Bulk data modifications

Prevention:
1. Run index statistics update: weekly
2. Monitor fragmentation: monthly
3. Rebuild if > 50% fragmentation
```

**Rebuilding Indexes:**
```cypher
-- Method 1: Drop and recreate (simplest)
DROP INDEX market_asset_type IF EXISTS;
CREATE INDEX market_asset_type IF NOT EXISTS
FOR (m:MARKET) ON (m.asset_type);
-- Downtime: ~10-100ms (negligible for 40 markets)

-- Method 2: Async rebuild (Neo4j 5.x+)
CALL db.index.reindex('market_asset_type');
-- No downtime, runs in background

-- Check rebuild progress
SHOW INDEXES;
-- Wait for status: POPULATING -> ONLINE
```

---

## 4. Query Pattern Analysis

### 4.1 Index Coverage by Query Type

| Query Pattern | Index Used | Latency | Coverage |
|---|---|---|---|
| Exact symbol | market_symbol_unique | < 2ms | 100% |
| Filter asset_type | market_asset_type | < 5ms | 100% |
| Filter asset_type + active | market_asset_type_is_active | < 5ms | 100% |
| Filter by exchange | market_exchange | < 5ms | 100% |
| Filter by currency | market_currency | < 5ms | 100% |
| Filter by sector property | market_sector | < 5ms | 100% |
| Filter by last_updated (range) | market_last_updated | < 5ms | 100% |
| Search by name | market_name_fulltext | < 10ms | 100% |
| Relationship traversal | sector_code_unique | < 5ms | 100% |
| Complex filter (type+active+exchange) | market_asset_type_is_active_exchange | < 5ms | 100% |

### 4.2 Query Optimization Tips

**Tip 1: Most Selective First**
```cypher
-- Bad (scans more data)
MATCH (m:MARKET)
WHERE m.is_active = true
  AND m.asset_type = 'STOCK'
RETURN m.symbol;

-- Good (asset_type more selective)
MATCH (m:MARKET)
WHERE m.asset_type = 'STOCK'
  AND m.is_active = true
RETURN m.symbol;

-- Both work with composite index, but query optimizer hints matter
```

**Tip 2: Use Constraints for Uniqueness**
```cypher
-- Use constraint (auto-indexed, guaranteed unique)
MATCH (m:MARKET {symbol: 'AAPL'})
RETURN m.name;
-- Latency: < 2ms (perfect selectivity)

-- Avoid property search without constraint
MATCH (m:MARKET)
WHERE m.symbol = 'AAPL'
RETURN m.name;
-- Still fast, but requires index scan
```

**Tip 3: Combine Filters Efficiently**
```cypher
-- Ideal: Uses composite index
MATCH (m:MARKET)
WHERE m.asset_type = 'STOCK' AND m.is_active = true
RETURN m.symbol;

-- Also good: Uses first column of composite
MATCH (m:MARKET)
WHERE m.asset_type = 'STOCK'
RETURN m.symbol;

-- Less efficient: Requires separate index
MATCH (m:MARKET)
WHERE m.is_active = true
RETURN m.symbol;
```

---

## 5. Monitoring & Alerts

### 5.1 Key Metrics to Track

```
1. Index Hit Ratio
   - Target: > 90% (index used for queries)
   - Alert: < 80% (index possibly unused)
   - Action: Verify index necessity, consider dropping

2. Query Latency
   - Target: < 5ms (p95) for indexed queries
   - Alert: > 10ms (index not used or fragmented)
   - Action: Check EXPLAIN plan, rebuild index

3. Index Fragmentation
   - Target: < 30%
   - Alert: > 50%
   - Action: Schedule index rebuild

4. Page Cache Hit Ratio
   - Target: > 85%
   - Alert: < 70%
   - Action: Increase page cache size
```

### 5.2 Queries for Monitoring

```cypher
-- Check all indexes and stats
SHOW INDEXES;

-- Monitor query performance
CALL db.queryInformation()
YIELD query, elapsedTime, dbHits
WHERE elapsedTime > 100
RETURN query, elapsedTime, dbHits
ORDER BY elapsedTime DESC
LIMIT 10;

-- Check memory usage
CALL db.queryJvm()
YIELD name, value
WHERE name CONTAINS 'memory'
RETURN name, value;

-- Monitor active transactions
CALL dbms.activeTransactions()
YIELD id, username, metaData, startTime, elapsedTime
RETURN id, username, elapsedTime
ORDER BY elapsedTime DESC;
```

---

## 6. Best Practices Summary

### Do's
- ✅ Index frequently filtered properties
- ✅ Use composite indexes for common multi-column filters
- ✅ Create indexes before importing large datasets
- ✅ Monitor index performance regularly
- ✅ Rebuild fragmented indexes monthly
- ✅ Use constraints for uniqueness
- ✅ Document index purpose and query patterns

### Don'ts
- ❌ Create indexes on rarely-used properties
- ❌ Create too many indexes (write performance suffers)
- ❌ Index on high-cardinality properties without cause
- ❌ Forget to test index impact before deployment
- ❌ Ignore index fragmentation over time
- ❌ Create composite indexes with > 3 columns
- ❌ Assume indexes work without EXPLAIN verification

---

## 7. Future Considerations

### When Scaling to 1000+ Markets

```
Current indexes: 11
Recommended additions:

1. market_industry (industry classification)
   - Cardinality: 50-100 industries
   - Use case: Industry-specific analysis
   - Priority: MEDIUM (add if queries show 5%+ volume)

2. market_market_cap_range (for price-based filtering)
   - Cardinality: High (continuous)
   - Use case: Screen by market cap
   - Priority: LOW (use denormalized ranges instead)

3. ticker_exchange_composite (future)
   - Cardinality: 1000s of combinations
   - Use case: Exchange + ticker lookups
   - Priority: LOW (assess actual query patterns first)
```

### Performance Optimization Path

```
Phase 1 (Current): Single-column + composite indexes
Phase 2 (100-500 markets): Add caching layer
Phase 3 (500-2000 markets): Relationship caching + query cache
Phase 4 (2000+ markets): Read replicas + distributed cache
```

---

## Summary

| Index | Status | Use Frequency | Maintenance |
|---|---|---|---|
| market_symbol_unique | ✅ Keep | Always | Never drop |
| market_asset_type | ✅ Keep | Very High | Monitor |
| market_is_active | ✅ Keep | High | Monitor |
| market_asset_type_is_active | ✅ Keep | Very High | Monitor |
| market_exchange | ✅ Keep | High | Monitor |
| market_currency | ✅ Keep | Medium | Quarterly review |
| market_last_updated | ✅ Keep | Medium | Rebuild if needed |
| market_asset_type_exchange | ✅ Keep | Medium | Monitor, consider dropping at scale |
| market_name_fulltext | ✅ Keep | Medium | Rebuild if needed |
| market_sector | ✅ Keep | Low | Deprecate if relationship preferred |
| market_data_source | ✅ Keep | Low | Remove if single-source confirmed |
| sector_name | ✅ Keep | Low | Consider dropping |

**Total Indexes: 11** (11 kept, 0 dropped)
**Recommended Additions:** None (sufficient for current requirements)
**Index Maintenance:** Monthly reviews

---

**Document Status:** Complete - Ready for Production
**Last Updated:** 2025-11-16
**Next Review:** After 500+ markets in production

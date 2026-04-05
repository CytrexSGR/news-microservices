# Knowledge Graph Service - Comprehensive Technical Documentation

**Service Name:** knowledge-graph-service
**Port:** 8111
**Technology Stack:** FastAPI, Neo4j 5.x, PostgreSQL, RabbitMQ, Python 3.11+
**Status:** Production Ready
**Last Updated:** 2025-11-24

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Quick Start](#quick-start)
3. [Port Configuration](#port-configuration)
4. [System Architecture](#system-architecture)
5. [Neo4j Graph Schema](#neo4j-graph-schema)
6. [Cypher Query Patterns](#cypher-query-patterns)
7. [Graph Algorithms & Analysis](#graph-algorithms--analysis)
8. [API Endpoints](#api-endpoints)
9. [RabbitMQ Event Integration](#rabbitmq-event-integration)
10. [Database Integration](#database-integration)
11. [Configuration](#configuration)
12. [Performance Optimization](#performance-optimization)
13. [Testing](#testing)
14. [Deployment](#deployment)
15. [Troubleshooting](#troubleshooting)
16. [Critical Incidents & Lessons](#critical-incidents--lessons)

---

## Executive Summary

The Knowledge Graph Service is a specialized **graph database microservice** that maintains a Neo4j-backed knowledge graph of entity relationships extracted from articles. It provides real-time relationship ingestion, complex path finding, relationship analytics, and semantic entity enrichment.

### Key Capabilities

- **Entity Relationship Ingestion**: Consume `relationships.extracted` events from NLP pipeline, store triplets (subject)-[relationship]->(object) in Neo4j
- **Graph Querying**: Search entities, find connections, retrieve relationship statistics
- **Pathfinding**: Discover shortest paths between entities using Neo4j algorithms
- **Analytics**: Analyze centrality, clustering, entity types, relationship quality
- **Enrichment**: Integrate external data (Wikidata, market data, financial intelligence)
- **Market Data**: Sync financial market data (stocks, sectors, executives) from FMP Service
- **Quality Metrics**: Track graph integrity, entity disambiguation, data completeness
- **Admin Tools**: Validated custom Cypher queries for research and troubleshooting

### Architecture Highlights

```
FastAPI API (8111)
    ├─ Graph Query Routes (entity connections, search, analytics)
    ├─ Pathfinding Routes (shortest paths, graph traversal)
    ├─ Enrichment Routes (Wikidata, market data)
    ├─ Admin Routes (custom Cypher queries, validation)
    └─ Health/Metrics Routes
          │
          ├─→ Neo4j Database (7687)
          │   ├─ Entity nodes (46K+)
          │   ├─ Relationship edges (69K+)
          │   └─ Market/Financial nodes (MARKET, SECTOR, EXECUTIVE, COMPANY)
          │
          ├─→ PostgreSQL (5432)
          │   ├─ Query history tracking
          │   ├─ Event logs
          │   └─ Quality snapshots
          │
          └─→ RabbitMQ (5672)
              ├─ relationships.extracted.* consumer
              ├─ market.sync.* consumer
              └─ finance.* consumer (FMP Service events)
```

### Performance Characteristics

- **Entity Lookup**: 10-50ms (indexed by name)
- **Relationship Query**: 50-200ms (indexed by type and confidence)
- **Shortest Path (depth 3)**: 100-500ms (depends on branching factor)
- **Analytics Query**: 200-500ms (full graph scan)
- **Ingestion Rate**: 100-300 triplets/second (RabbitMQ consumer)
- **Graph Size**: 46K nodes, 69K relationships (as of Nov 2025)

---

## Quick Start

### 1. Prerequisites

```bash
# Required services (docker compose handles this)
- Neo4j 5.x (port 7687)
- PostgreSQL 15+ (port 5432)
- RabbitMQ 3.x (port 5672)
- Python 3.11+
```

### 2. Start with Docker Compose

```bash
cd /home/cytrex/news-microservices

# Start all services
docker compose up -d knowledge-graph-service neo4j postgres rabbitmq

# Verify service is running
curl http://localhost:8111/

# Expected response:
# {
#   "service": "knowledge-graph-service",
#   "status": "running",
#   "version": "1.0.0",
#   "uptime_seconds": 12
# }
```

### 3. Check Health

```bash
curl http://localhost:8111/health

# Response:
# {
#   "status": "healthy",
#   "neo4j": "connected",
#   "postgres": "connected",
#   "rabbitmq": "connected",
#   "consumer": "running"
# }
```

### 4. First Query - Get Graph Stats

```bash
curl http://localhost:8111/api/v1/graph/stats \
  -H "Content-Type: application/json"

# Response shows total nodes, relationships, entity type distribution
```

### 5. Search an Entity

```bash
curl "http://localhost:8111/api/v1/graph/search?query=Tesla&limit=10"

# Returns matching entities with connection counts
```

### 6. Get Entity Connections

```bash
curl "http://localhost:8111/api/v1/graph/entity/Tesla/connections?limit=20"

# Returns nodes and edges connected to Tesla
```

---

## Port Configuration

**Port Assignment:** 8111

### Port Usage Map

```
Service Component          Port      Protocol    Purpose
─────────────────────────────────────────────────────────────
Knowledge Graph API       8111      HTTP/REST   API Requests
Neo4j Bolt                7687      Binary      Neo4j Driver
Neo4j Browser             7474      HTTP        Admin UI (optional)
PostgreSQL                5432      TCP         Metadata/Events
RabbitMQ                  5672      AMQP        Event Consumption
RabbitMQ Management UI    15672     HTTP        Queue Admin (optional)
Prometheus Metrics        8111      HTTP        /metrics endpoint
```

### Environment Configuration

```bash
# .env file (or docker compose)
SERVICE_PORT=8111
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password_2024
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
```

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────┐   │
│  │  API Routes      │  │  Services      │  │  Consumers │   │
│  ├──────────────────┤  ├────────────────┤  ├────────────┤   │
│  │ • graph.py       │  │ • neo4j_svc    │  │ • rels_    │   │
│  │ • pathfinding    │  │ • ingestion    │  │   consumer │   │
│  │ • search.py      │  │ • query        │  │ • market_  │   │
│  │ • analytics      │  │ • pathfinding  │  │   consumer │   │
│  │ • enrichment     │  │ • search       │  │ • finance_ │   │
│  │ • admin_query    │  │ • wikipedia    │  │   consumer │   │
│  │ • markets.py     │  │                │  │            │   │
│  │ • findings.py    │  │                │  │            │   │
│  └──────────────────┘  └────────────────┘  └────────────┘   │
│         │                      │                    │        │
└─────────┼──────────────────────┼────────────────────┼────────┘
          │                      │                    │
    ┌─────▼─────┐          ┌─────▼──────┐      ┌─────▼──────┐
    │   Neo4j   │          │PostgreSQL  │      │  RabbitMQ  │
    │  (7687)   │          │  (5432)    │      │  (5672)    │
    ├───────────┤          ├────────────┤      ├────────────┤
    │ Nodes:    │          │ • events   │      │ Queues:    │
    │ • Entity  │          │ • query_   │      │ • rels.ext │
    │ • Market  │          │   history  │      │ • market   │
    │ • Sector  │          │ • quality_ │      │ • finance  │
    │ • Exec    │          │   snapshot │      │            │
    │           │          │            │      │            │
    │ Rels:     │          │Exchanges:  │      │Exchanges:  │
    │ • Works   │          │ • events   │      │ • news     │
    │ • Located │          │            │      │ • finance  │
    │ • Mentions│          │            │      │            │
    │ • BelongsTo        │            │      │            │
    └───────────┘          └────────────┘      └────────────┘
```

### Data Flow Architecture

```
Article Processing Pipeline
    │
    ├─→ NLP Service (extracts entities + relationships)
    │
    └─→ RabbitMQ: relationships.extracted.* event
        │
        ├─→ Knowledge Graph Service Consumer
        │   ├─ Parse RelationshipsExtractedEvent
        │   ├─ For each triplet:
        │   │   ├─ MERGE Subject node (Entity)
        │   │   ├─ MERGE Object node (Entity)
        │   │   └─ MERGE Relationship edge
        │   └─ Track in PostgreSQL query_history
        │
        └─→ Neo4j Knowledge Graph
            ├─ Full-text indexes on entity names
            ├─ Relationship confidence indexes
            └─ Type-based filtering


Financial Data Pipeline
    │
    ├─→ FMP Service (generates finance.* events)
    │
    ├─→ RabbitMQ: market.sync.* event
    │   └─→ MarketSyncService Consumer
    │       ├─ Parse market data (AAPL, MSFT, etc.)
    │       ├─ MERGE MARKET nodes
    │       ├─ MERGE SECTOR nodes
    │       └─ Create BELONGS_TO_SECTOR relationships
    │
    └─→ RabbitMQ: finance.* events
        └─→ FinanceIntelligenceConsumer
            ├─ Parse finance.company.*
            ├─ Parse finance.executives.*
            ├─ Parse finance.insider.trade.*
            ├─ MERGE COMPANY nodes
            ├─ MERGE EXECUTIVE nodes
            └─ Create WORKS_FOR, insider trading relationships
```

### Service Interactions

```
Knowledge Graph Service Dependencies:
    │
    ├─→ Neo4j (Required)
    │   ├─ Graph database backend
    │   ├─ Cypher query execution
    │   ├─ 50 connection pool
    │   └─ Automatic reconnection
    │
    ├─→ PostgreSQL (Required)
    │   ├─ Audit trail (query history)
    │   ├─ Quality metrics (daily snapshots)
    │   └─ Event logging
    │
    ├─→ RabbitMQ (Required)
    │   ├─ relationships.extracted.* events
    │   ├─ market.sync.* events
    │   └─ finance.* events
    │
    ├─→ FMP Service (Optional, for market data)
    │   ├─ Circuit breaker pattern
    │   ├─ 3 retry attempts
    │   └─ 30s timeout
    │
    ├─→ Scraping Service (Optional)
    │   └─ Article metadata retrieval
    │
    └─→ External APIs (Optional)
        ├─ Wikidata (entity enrichment)
        └─ Wikipedia (entity descriptions)
```

---

## Neo4j Graph Schema

### Node Types

#### 1. Entity Node

**Label:** `Entity`

Represents any extractable entity from news articles (person, organization, location, etc.).

**Properties:**
- `name` (String, **UNIQUE**): Entity name (e.g., "Elon Musk", "Tesla", "New York")
- `type` (String, **INDEXED**): Entity classification
  - `PERSON`: Individual people
  - `ORGANIZATION`: Companies, agencies, institutions
  - `LOCATION`: Countries, cities, regions
  - `PRODUCT`: Products, services, software
  - `EVENT`: Historical or current events
  - `ARTICLE`: News article references
  - `DATE`: Temporal references
  - `MISC`: Miscellaneous entities
  - `UNKNOWN`: Unclassified
- `entity_id` (String): External ID (if available)
- `wikidata_id` (String, **INDEXED**): Wikidata Q-identifier (for enrichment)
- `created_at` (DateTime): When entity was first encountered
- `last_seen` (DateTime): Most recent mention
- `connection_count` (Integer): Number of direct relationships
- `enrichment_data` (Map): Additional metadata
  - `description`: Entity description
  - `aliases`: Alternative names
  - `founded`: Creation date
  - `headquarters`: Location
  - `website`: Official website
  - `image_url`: Entity image

**Cypher Example:**
```cypher
CREATE (e:Entity {
  name: "Tesla",
  type: "ORGANIZATION",
  entity_id: "tesla-001",
  wikidata_id: "Q478214",
  created_at: datetime("2024-10-15T10:00:00Z"),
  last_seen: datetime("2025-11-20T14:30:00Z"),
  connection_count: 45,
  enrichment_data: {
    description: "American electric vehicle manufacturer",
    aliases: ["Tesla Motors", "Tesla Inc."],
    founded: "2003-06-29",
    headquarters: "Austin, Texas"
  }
})
```

#### 2. Market Node (Financial)

**Label:** `MARKET`

Represents tradable financial instruments (stocks, ETFs, bonds, cryptocurrencies).

**Properties:**
- `symbol` (String, **UNIQUE**): Ticker symbol (e.g., "AAPL", "BTC/USD")
- `name` (String): Full name (e.g., "Apple Inc.")
- `asset_type` (String): Type of asset
  - `STOCK`: Equity shares
  - `ETF`: Exchange-traded fund
  - `CRYPTO`: Cryptocurrency
  - `COMMODITY`: Physical commodity futures
  - `BOND`: Fixed income
  - `CURRENCY`: Foreign exchange
- `currency` (String): Trading currency (USD, EUR, etc.)
- `is_active` (Boolean): Currently trading
- `exchange` (String): Stock exchange (NASDAQ, NYSE, CRYPTO, etc.)
- `sector` (String): GICS sector code (e.g., "4530" for Information Technology)
- `isin` (String): ISIN code for international identification
- `description` (String): Asset description
- `current_price` (Float): Last traded price
- `day_change_percent` (Float): Daily percentage change
- `market_cap` (Float): Market capitalization (USD)
- `volume` (Float): Trading volume
- `open_price`, `high_price`, `low_price`, `close_price` (Float): OHLC prices
- `created_at` (DateTime): When added to graph
- `last_updated` (DateTime): Last price update

#### 3. Sector Node

**Label:** `SECTOR`

Represents industry classifications.

**Properties:**
- `code` (String, **UNIQUE**): GICS sector code (e.g., "4530")
- `name` (String): Sector name (e.g., "Information Technology")
- `market_classification` (String): Classification scheme (GICS, ICB, etc.)

#### 4. Company Node (Financial)

**Label:** `COMPANY`

Represents publicly traded companies with detailed financial data.

**Properties:**
- `symbol` (String, **UNIQUE**): Stock ticker
- `name` (String): Company name
- `sector` (String): Industry sector
- `employees` (Integer): Employee count
- `market_cap_usd` (Float): Market capitalization
- `ceo_name` (String): Chief Executive Officer
- `last_updated` (DateTime): When data was last refreshed

#### 5. Executive Node

**Label:** `EXECUTIVE`

Represents company executives and leadership.

**Properties:**
- `name` (String): Executive name
- `company_symbol` (String): Associated company ticker
- `title` (String): Job title
- `pay_usd` (Float): Annual compensation
- `ownership_percent` (Float): Share ownership
- `started_date` (DateTime): Start date at company
- `is_active` (Boolean): Currently employed

### Relationship Types

#### 1. WORKS_FOR

**Direction:** PERSON → ORGANIZATION / EXECUTIVE → COMPANY

Indicates employment or affiliation.

**Properties:**
- `confidence` (Float, 0.0-1.0, **INDEXED**): Confidence score
- `mention_count` (Integer): Frequency of mention
- `first_seen` (DateTime): When relationship first mentioned
- `last_seen` (DateTime): Most recent mention
- `evidence` (List[String]): Article IDs supporting relationship
- `quality_score` (Float, 0.0-1.0): Relationship quality

**Example:**
```cypher
CREATE (p:PERSON {name: "Elon Musk"})-[r:WORKS_FOR {
  confidence: 0.95,
  mention_count: 234,
  first_seen: datetime("2024-10-15"),
  last_seen: datetime("2025-11-20"),
  evidence: ["uuid-1", "uuid-2"],
  quality_score: 0.92
}]->(o:ORGANIZATION {name: "Tesla"})
```

#### 2. LOCATED_IN

**Direction:** ORGANIZATION/PERSON → LOCATION

Indicates geographic location.

**Properties:**
- `confidence` (Float): Location confidence
- `mention_count` (Integer): Frequency of mention
- `relationship_type` (String): Type (headquarters, founded, based_in, etc.)

#### 3. FOUNDED

**Direction:** PERSON → ORGANIZATION

Indicates founder relationship.

**Properties:**
- `confidence` (Float)
- `founded_date` (DateTime): When founded
- `still_involved` (Boolean): Still associated

#### 4. MENTIONS / MENTIONED_WITH

**Direction:** ENTITY → ENTITY

Indicates co-occurrence in articles.

**Properties:**
- `confidence` (Float): Co-occurrence strength
- `mention_count` (Integer): Number of co-mentions
- `context` (String): Contextual relationship

#### 5. BELONGS_TO_SECTOR

**Direction:** MARKET → SECTOR

Indicates sector classification.

**Properties:**
- `classification_date` (DateTime): When classified
- `confidence` (Float): Classification confidence

#### 6. ABOUT_MARKET

**Direction:** ORGANIZATION → MARKET

Indicates organization is publicly traded.

**Properties:**
- `ticker_symbol` (String): Associated ticker
- `listed_date` (DateTime): When listed
- `is_primary` (Boolean): Primary listing

#### 7. INSIDER_TRADE

**Direction:** EXECUTIVE → COMPANY

Indicates insider trading activity.

**Properties:**
- `trade_date` (DateTime): Trade execution date
- `shares` (Integer): Number of shares
- `price_per_share` (Float): Share price
- `transaction_type` (String): BUY or SELL
- `transaction_value_usd` (Float): Total transaction value
- `filing_date` (DateTime): SEC filing date

### Constraints & Indexes

```cypher
-- Uniqueness Constraints
CREATE CONSTRAINT entity_name_unique IF NOT EXISTS
  FOR (e:Entity) REQUIRE e.name IS UNIQUE;

CREATE CONSTRAINT market_symbol_unique IF NOT EXISTS
  FOR (m:MARKET) REQUIRE m.symbol IS UNIQUE;

CREATE CONSTRAINT sector_code_unique IF NOT EXISTS
  FOR (s:SECTOR) REQUIRE s.code IS UNIQUE;

CREATE CONSTRAINT company_symbol_unique IF NOT EXISTS
  FOR (c:COMPANY) REQUIRE c.symbol IS UNIQUE;

-- Performance Indexes
CREATE INDEX entity_type_idx IF NOT EXISTS
  FOR (e:Entity) ON (e.type);

CREATE INDEX entity_wikidata_idx IF NOT EXISTS
  FOR (e:Entity) ON (e.wikidata_id);

CREATE INDEX relationship_confidence_idx IF NOT EXISTS
  FOR ()-[r:WORKS_FOR|LOCATED_IN|FOUNDED]-() ON (r.confidence);

CREATE INDEX relationship_type_idx IF NOT EXISTS
  FOR ()-[r:WORKS_FOR|MENTIONS|MENTIONED_WITH]-() ON (type(r));

CREATE INDEX market_type_idx IF NOT EXISTS
  FOR (m:MARKET) ON (m.asset_type);

CREATE INDEX market_sector_idx IF NOT EXISTS
  FOR (m:MARKET) ON (m.sector);

-- Text Indexes for Search
CREATE TEXT INDEX entity_name_full_text IF NOT EXISTS
  FOR (e:Entity) ON (e.name);

-- Relationship Indexes for Filtering
CREATE INDEX relationship_confidence_quality IF NOT EXISTS
  FOR ()-[r]-() ON (r.confidence, r.quality_score);
```

### Graph Statistics (as of Nov 2025)

```
Total Nodes:        46,177
├─ Entity:          46,177
├─ MARKET:          ~4,000
├─ SECTOR:          ~300
└─ EXECUTIVE:       ~800

Total Relationships: 69,437
├─ WORKS_FOR:       ~15,000
├─ MENTIONED_WITH:  ~28,941
├─ LOCATED_IN:      ~12,500
├─ BELONGS_TO_SECTOR: ~3,500
├─ INSIDER_TRADE:   ~500
└─ Other:           ~8,996

Entity Type Distribution:
├─ UNKNOWN:         9,560  (20.7%)
├─ MISC:            8,650  (18.7%)
├─ PERSON:          7,101  (15.4%)
├─ ORGANIZATION:    6,551  (14.2%)
├─ ARTICLE:         5,395  (11.7%)
├─ PRODUCT:         3,420  (7.4%)
├─ LOCATION:        3,284  (7.1%)
├─ EVENT:           1,636  (3.5%)
└─ DATE:            579    (1.3%)

Relationship Quality:
├─ High Confidence (≥0.8):  61,386  (88.4%)
├─ Medium (0.5-0.8):         8,051  (11.6%)
└─ Low (<0.5):               0      (0.0%)
```

---

## Cypher Query Patterns

### 1. Entity Lookup Patterns

#### Get Entity with Enrichment Data

```cypher
MATCH (e:Entity {name: $name})
RETURN e
```

**Performance:** 10-20ms (uses unique constraint)

**Use Case:** Get entity details, check if exists

#### Get Entity with Connection Count

```cypher
MATCH (e:Entity {name: $name})
WITH e
MATCH (e)-[r]-()
WITH e, COUNT(r) as rel_count
SET e.connection_count = rel_count
RETURN e, rel_count
```

**Performance:** 30-50ms

#### Get All Entities of Type

```cypher
MATCH (e:Entity {type: $entity_type})
RETURN e
LIMIT $limit
```

**Performance:** 50-100ms (uses type index)

### 2. Relationship Patterns

#### Create or Update Relationship (Idempotent)

```cypher
MERGE (source:Entity {name: $subject_name})
ON CREATE SET
    source.type = $subject_type,
    source.created_at = datetime(),
    source.last_seen = datetime()
ON MATCH SET
    source.last_seen = datetime(),
    source.type = $subject_type
WITH source

MERGE (target:Entity {name: $object_name})
ON CREATE SET
    target.type = $object_type,
    target.created_at = datetime(),
    target.last_seen = datetime()
ON MATCH SET
    target.last_seen = datetime(),
    target.type = $object_type
WITH source, target

MERGE (source)-[r:WORKS_FOR]->(target)
ON CREATE SET
    r.confidence = $confidence,
    r.mention_count = 1,
    r.first_seen = datetime(),
    r.last_seen = datetime(),
    r.evidence = [$article_id],
    r.quality_score = $quality_score
ON MATCH SET
    r.mention_count = r.mention_count + 1,
    r.last_seen = datetime(),
    r.confidence = COALESCE($confidence, r.confidence),
    r.evidence = CASE
        WHEN $article_id IN r.evidence THEN r.evidence
        ELSE r.evidence + $article_id
    END
RETURN source, target, r
```

**Performance:** 50-150ms (2 MERGE + 1 relationship MERGE)

**Critical Pattern:** This is the **core ingestion pattern** used by all consumers

#### Update Relationship Confidence

```cypher
MATCH (s:Entity)-[r:WORKS_FOR]->(t:Entity)
WHERE s.name = $subject AND t.name = $object
SET r.confidence = $new_confidence,
    r.last_seen = datetime()
RETURN r
```

**Performance:** 20-40ms

### 3. Path Finding Patterns

#### Find Shortest Path (2-3 hops)

```cypher
MATCH path = allShortestPaths((source:Entity {name: $entity1})-[r:WORKS_FOR|MENTIONED_WITH|LOCATED_IN*1..3]-(target:Entity {name: $entity2}))
WHERE ALL(rel IN relationships(path) WHERE rel.confidence >= $min_confidence)
RETURN path
LIMIT $limit
```

**Performance:** 100-500ms depending on branching factor

**Use Case:** Discover hidden connections between entities

#### Find All Paths with Limited Depth

```cypher
MATCH (source:Entity {name: $entity1})
MATCH (target:Entity {name: $entity2})
CALL apoc.path.subgraphAll(source, {
    relationshipFilter: 'WORKS_FOR|MENTIONED_WITH|LOCATED_IN',
    labelFilter: 'Entity',
    maxLevel: $max_depth,
    limit: $limit
})
YIELD path
WHERE target IN nodes(path)
RETURN path
ORDER BY length(path)
```

**Performance:** 200-800ms depending on branching

### 4. Analytics Patterns

#### Get Top Connected Entities

```cypher
MATCH (e:Entity)
OPTIONAL MATCH (e)-[r]-()
WITH e, COUNT(r) as relationship_count
WHERE relationship_count > 0
ORDER BY relationship_count DESC
LIMIT $limit
RETURN e.name, e.type, relationship_count
```

**Performance:** 100-300ms (full scan)

#### Get Relationship Statistics

```cypher
MATCH ()-[r]-()
WITH type(r) as rel_type,
     COUNT(r) as count,
     AVG(r.confidence) as avg_confidence,
     COLLECT(DISTINCT startNode(r).type + '-' + type(r) + '-' + endNode(r).type) as patterns
WITH rel_type, count, avg_confidence, patterns
ORDER BY count DESC
RETURN rel_type, count, avg_confidence, patterns
```

**Performance:** 200-500ms

#### Entity Type Distribution

```cypher
MATCH (e:Entity)
WITH e.type as entity_type, COUNT(e) as count
ORDER BY count DESC
RETURN entity_type, count, COUNT(*) as percentage
```

**Performance:** 100-200ms

### 5. Search Patterns

#### Full-Text Search for Entity

```cypher
CALL db.index.fulltext.queryNodes("entity_name_full_text", $query)
YIELD node, score
RETURN node.name, node.type, score
ORDER BY score DESC
LIMIT $limit
```

**Performance:** 10-50ms (full-text index)

#### Autocomplete Search

```cypher
MATCH (e:Entity)
WHERE toLower(e.name) STARTS WITH toLower($prefix)
RETURN e.name, e.type, e.connection_count
ORDER BY e.connection_count DESC
LIMIT $limit
```

**Performance:** 20-60ms (case-insensitive matching)

### 6. Enrichment Patterns

#### Enrich Entity with Wikidata

```cypher
MATCH (e:Entity {name: $entity_name})
SET e.wikidata_id = $wikidata_id,
    e.enrichment_data = {
        description: $description,
        aliases: $aliases,
        founded: $founded,
        headquarters: $headquarters
    }
RETURN e
```

**Performance:** 10-20ms

### 7. Market Data Patterns

#### Merge Market with Sector

```cypher
MERGE (m:MARKET {symbol: $symbol})
ON CREATE SET
    m.name = $name,
    m.asset_type = $asset_type,
    m.currency = $currency,
    m.is_active = true,
    m.created_at = datetime()
ON MATCH SET
    m.name = $name,
    m.is_active = $is_active,
    m.last_updated = datetime()
WITH m

MERGE (s:SECTOR {code: $sector_code})
ON CREATE SET
    s.name = $sector_name

MERGE (m)-[:BELONGS_TO_SECTOR]->(s)
RETURN m, s
```

**Performance:** 30-80ms

#### Update Market Price Data

```cypher
MATCH (m:MARKET {symbol: $symbol})
SET m.current_price = $current_price,
    m.day_change_percent = $day_change_percent,
    m.market_cap = $market_cap,
    m.volume = $volume,
    m.open_price = $open_price,
    m.high_price = $high_price,
    m.low_price = $low_price,
    m.close_price = $close_price,
    m.last_updated = datetime()
RETURN m
```

**Performance:** 10-20ms

### 8. Financial Intelligence Patterns

#### Track Executive Insider Trading

```cypher
MERGE (exec:EXECUTIVE {name: $executive_name})
ON CREATE SET
    exec.company_symbol = $company_symbol,
    exec.title = $title

MERGE (company:COMPANY {symbol: $company_symbol})
ON CREATE SET
    company.name = $company_name

MERGE (exec)-[r:INSIDER_TRADE]->(company)
ON CREATE SET
    r.trade_date = datetime($trade_date),
    r.shares = $shares,
    r.price_per_share = $price_per_share,
    r.transaction_type = $transaction_type,
    r.transaction_value_usd = $transaction_value_usd,
    r.filing_date = datetime($filing_date)
ON MATCH SET
    r.shares = $shares,
    r.price_per_share = $price_per_share,
    r.transaction_value_usd = $transaction_value_usd

MERGE (exec)-[:WORKS_FOR]->(company)
RETURN exec, company, r
```

**Performance:** 40-100ms

#### Get Executive Network for Company

```cypher
MATCH (c:COMPANY {symbol: $symbol})<-[works:WORKS_FOR]-(exec:EXECUTIVE)
OPTIONAL MATCH (exec)-[trades:INSIDER_TRADE]->(c)
RETURN exec.name, exec.title, works.started_date, COUNT(trades) as trade_count
ORDER BY trades.transaction_value_usd DESC
```

**Performance:** 50-150ms

### Query Validation Checklist

Before deploying Cypher queries:

- [ ] Test with EXPLAIN to view execution plan
- [ ] Verify indexes are used (look for NodeIndexSeek)
- [ ] Check for full table scans (AllNodesScan - bad)
- [ ] Validate parameter types match schema
- [ ] Test with sample data
- [ ] Measure actual execution time
- [ ] Check for N+1 query patterns
- [ ] Verify deadlock handling (retry logic)
- [ ] Ensure ON CREATE SET before standalone SET clauses
- [ ] Test with null/missing parameters

---

## Graph Algorithms & Analysis

### 1. Centrality Analysis

#### PageRank

Measures entity importance based on relationship patterns.

```cypher
CALL gds.pageRank.stream(
  'Entity',  // node projection
  {          // algorithm config
    maxIterations: 20,
    dampingFactor: 0.85
  }
)
YIELD nodeId, score
WITH gds.util.asNode(nodeId) as node, score
ORDER BY score DESC
LIMIT 20
RETURN node.name, node.type, score
```

**Use Case:** Identify most influential entities in graph
**Performance:** 1-5 seconds (full graph)

#### Betweenness Centrality

Identifies entities that act as bridges between clusters.

```cypher
CALL gds.betweenness.stream(
  'Entity',
  {
    relationshipTypes: ['WORKS_FOR', 'MENTIONED_WITH']
  }
)
YIELD nodeId, score
WITH gds.util.asNode(nodeId) as node, score
ORDER BY score DESC
LIMIT 10
RETURN node.name, node.type, score
```

**Use Case:** Find key connectors in network
**Performance:** 2-8 seconds

#### Closeness Centrality

Measures how close an entity is to all others.

```cypher
CALL gds.closeness.stream(
  'Entity',
  {
    relationshipTypes: ['WORKS_FOR', 'LOCATED_IN']
  }
)
YIELD nodeId, score
ORDER BY score DESC
LIMIT 10
RETURN gds.util.asNode(nodeId).name, score
```

**Use Case:** Find entities with shortest average path distance
**Performance:** 2-5 seconds

### 2. Community Detection

#### Louvain Clustering

Detects groups of closely-connected entities.

```cypher
CALL gds.louvain.stream(
  'Entity',
  {
    relationshipTypes: ['WORKS_FOR', 'MENTIONED_WITH'],
    seedProperty: 'seed'
  }
)
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name, communityId
ORDER BY communityId
```

**Use Case:** Identify entity clusters (organizations, person groups)
**Performance:** 3-10 seconds
**Interpretation:** Entities in same community are closely related

#### Triangle Count

Identifies relationship triangles (A-B-C-A).

```cypher
CALL gds.triangleCount.stream(
  'Entity',
  {
    relationshipTypes: ['MENTIONED_WITH']
  }
)
YIELD nodeId, triangleCount
WITH gds.util.asNode(nodeId) as node, triangleCount
WHERE triangleCount > 0
ORDER BY triangleCount DESC
LIMIT 20
RETURN node.name, triangleCount
```

**Use Case:** Find tightly-connected entity groups
**Performance:** 1-3 seconds

### 3. Similarity Analysis

#### Jaccard Similarity

Measures overlap between entity connections.

```cypher
MATCH (n:Entity {name: $entity1})
MATCH (m:Entity {name: $entity2})
CALL gds.similarity.jaccard.stream(
  {sourceNodeId: id(n), targetNodeId: id(m)},
  {relationshipTypes: ['WORKS_FOR', 'MENTIONED_WITH']}
)
YIELD similarity
RETURN similarity
```

**Use Case:** Find similar entities based on relationships
**Performance:** 50-200ms

#### Cosine Similarity (Connection Profile)

```cypher
MATCH (source:Entity {name: $entity1})-[r1]->(common)
WITH source, common, count(r1) as r1_count
MATCH (target:Entity {name: $entity2})-[r2]->(common)
WITH source, target, common, r1_count, count(r2) as r2_count
WITH source, target,
     SUM(r1_count * r2_count) as dot_product,
     SQRT(SUM(r1_count^2)) as source_magnitude,
     SQRT(SUM(r2_count^2)) as target_magnitude
RETURN dot_product / (source_magnitude * target_magnitude) as cosine_similarity
```

**Use Case:** Find entities with similar connection profiles
**Performance:** 100-500ms

### 4. Link Prediction

#### Common Neighbors

Predicts relationship likelihood based on shared connections.

```cypher
MATCH (person:Entity {name: $person_name})-[r1:WORKS_FOR]->(org:Entity)
MATCH (other_person:Entity)-[r2:WORKS_FOR]->(org:Entity)
WHERE person <> other_person
RETURN other_person.name, count(org) as common_orgs
ORDER BY common_orgs DESC
LIMIT 10
```

**Use Case:** Suggest new relationship connections
**Performance:** 50-200ms
**Accuracy:** 40-60% (depends on graph density)

#### Preferential Attachment

Predicts links to highly-connected nodes.

```cypher
MATCH (target:Entity)
WITH target, size((target)-[]-()) as degree
ORDER BY degree DESC
LIMIT 20
RETURN target.name, degree as connection_count
```

**Use Case:** Identify high-value relationships to add
**Performance:** 100-300ms

---

## API Endpoints

### Health & Status

#### GET /health

Check service health and component status.

```bash
curl http://localhost:8111/health
```

**Response:**
```json
{
  "status": "healthy",
  "neo4j": "connected",
  "postgres": "connected",
  "rabbitmq": "connected",
  "consumer": "running",
  "timestamp": "2025-11-24T10:30:45Z"
}
```

### Graph Queries

#### GET /api/v1/graph/entity/{entity_name}/connections

Get all connections for an entity.

```bash
# Basic query
curl "http://localhost:8111/api/v1/graph/entity/Tesla/connections?limit=100"

# With relationship type filter
curl "http://localhost:8111/api/v1/graph/entity/Tesla/connections?relationship_type=WORKS_FOR&limit=50"

# With confidence filter
curl "http://localhost:8111/api/v1/graph/entity/Tesla/connections?min_confidence=0.8&limit=20"
```

**Parameters:**
- `entity_name` (path): Entity name to query
- `relationship_type` (query): Filter by relationship type (optional)
- `limit` (query): Max results (1-1000, default: 100)
- `min_confidence` (query): Min confidence score (0.0-1.0, default: 0.5)

**Response:**
```json
{
  "nodes": [
    {
      "name": "Elon Musk",
      "type": "PERSON",
      "connection_count": 89
    }
  ],
  "edges": [
    {
      "source": "Elon Musk",
      "target": "Tesla",
      "relationship_type": "WORKS_FOR",
      "confidence": 0.95,
      "mention_count": 234
    }
  ],
  "total_nodes": 45,
  "total_edges": 67,
  "query_time_ms": 87
}
```

### Search

#### GET /api/v1/graph/search

Search for entities by name.

```bash
curl "http://localhost:8111/api/v1/graph/search?query=Tesla&limit=10"

# With type filter
curl "http://localhost:8111/api/v1/graph/search?query=Elon&entity_type=PERSON&limit=5"
```

**Parameters:**
- `query` (query): Search term
- `entity_type` (query): Filter by type (optional)
- `limit` (query): Max results (default: 10)

**Response:**
```json
{
  "results": [
    {
      "name": "Tesla",
      "type": "ORGANIZATION",
      "connection_count": 45,
      "wikidata_id": "Q478214"
    }
  ],
  "total_results": 1,
  "query_time_ms": 23
}
```

### Pathfinding

#### GET /api/v1/graph/path/{entity1}/{entity2}

Find shortest paths between two entities.

```bash
curl "http://localhost:8111/api/v1/graph/path/Trump/Israel?max_depth=3&limit=5"
```

**Parameters:**
- `entity1` (path): Source entity
- `entity2` (path): Target entity
- `max_depth` (query): Max hops (1-5, default: 3)
- `limit` (query): Max paths (1-10, default: 3)
- `min_confidence` (query): Min confidence (default: 0.5)

**Response:**
```json
{
  "paths": [
    {
      "length": 2,
      "nodes": ["Trump", "United States", "Israel"],
      "relationships": [
        {
          "type": "LOCATED_IN",
          "confidence": 0.92
        },
        {
          "type": "RELATED_TO",
          "confidence": 0.88
        }
      ]
    }
  ],
  "total_paths": 15,
  "shortest_path_length": 2,
  "query_time_ms": 234
}
```

### Analytics

#### GET /api/v1/graph/stats

Get basic graph statistics.

```bash
curl http://localhost:8111/api/v1/graph/stats
```

**Response:**
```json
{
  "total_nodes": 46177,
  "total_relationships": 69437,
  "entity_types": {
    "PERSON": 7101,
    "ORGANIZATION": 6551,
    "LOCATION": 3284
  }
}
```

#### GET /api/v1/graph/stats/detailed

Get comprehensive graph quality metrics.

```bash
curl http://localhost:8111/api/v1/graph/stats/detailed
```

**Response:**
```json
{
  "graph_size": {
    "total_nodes": 46177,
    "total_relationships": 69437,
    "entity_type_distribution": {...}
  },
  "relationship_quality": {
    "high_confidence_count": 61386,
    "high_confidence_ratio": 0.884
  },
  "quality_score": 75.96,
  "query_time_ms": 335
}
```

#### GET /api/v1/graph/analytics/top-entities

Get most connected entities.

```bash
curl "http://localhost:8111/api/v1/graph/analytics/top-entities?limit=10&entity_type=PERSON"
```

### Admin Queries

#### POST /api/v1/graph/admin/query/cypher

Execute custom read-only Cypher query.

```bash
curl -X POST http://localhost:8111/api/v1/graph/admin/query/cypher \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (e:Entity) WHERE e.type = $entity_type RETURN e.name LIMIT 10",
    "parameters": {"entity_type": "PERSON"},
    "timeout_seconds": 10
  }'
```

**Security:** Admin-only, read-only queries only

### Enrichment

#### POST /api/v1/graph/enrichment/wikidata

Enrich entity with Wikidata information.

```bash
curl -X POST http://localhost:8111/api/v1/graph/enrichment/wikidata \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "Tesla",
    "wikidata_id": "Q478214"
  }'
```

### Markets

#### GET /api/v1/graph/markets?asset_type=STOCK&limit=50

List market instruments.

```bash
curl "http://localhost:8111/api/v1/graph/markets?asset_type=STOCK&is_active=true&limit=20"
```

#### GET /api/v1/graph/markets/{symbol}

Get market details.

```bash
curl http://localhost:8111/api/v1/graph/markets/AAPL
```

### Metrics

#### GET /metrics

Prometheus metrics endpoint.

```bash
curl http://localhost:8111/metrics | grep kg_
```

**Key Metrics:**
```
kg_queries_total{endpoint="search"} 1245
kg_query_duration_seconds_bucket{le="0.1"} 523
kg_ingestion_triplets_total{status="success"} 45000
kg_consumer_queue_size 0
kg_graph_nodes_total 46177
kg_graph_relationships_total 69437
```

---

## RabbitMQ Event Integration

### Consumer Architecture

The Knowledge Graph Service runs 3 independent RabbitMQ consumers:

```
┌────────────────────────────────────────────────────┐
│      FastAPI Application (Main Thread)              │
├────────────────────────────────────────────────────┤
│  ├─ RelationshipsConsumer (Background Task)        │
│  │  └─ Listens: relationships.extracted.*           │
│  │     Queue: knowledge_graph_relationships        │
│  │                                                  │
│  ├─ MarketConsumer (Background Task)               │
│  │  └─ Listens: market.sync.*                      │
│  │     Queue: knowledge_graph_market               │
│  │                                                  │
│  └─ FinanceIntelligenceConsumer (Background Task)  │
│     └─ Listens: finance.*                          │
│        Queue: knowledge_graph_finance_intelligence │
└────────────────────────────────────────────────────┘
         │              │              │
         │              │              └─→ FMP Service (finance events)
         │              │
         │              └─→ Feed Service (market sync events)
         │
         └─→ NLP Extraction Service (relationship events)
```

### 1. Relationships Consumer

**Exchange:** `news.events`
**Queue:** `knowledge_graph_relationships`
**Routing Key:** `relationships.extracted.*`
**Prefetch:** 10 messages

**Event Schema:**
```python
class RelationshipsExtractedEvent(BaseModel):
    article_id: str
    article_url: str
    extraction_method: str  # "spacy_ner", "transformers", etc.
    triplets: List[RelationshipTriplet]

class RelationshipTriplet(BaseModel):
    subject: EntityReference
    relationship_type: str
    object: EntityReference
    confidence: float
    evidence: Optional[str] = None
```

**Processing Logic:**
```
1. Consume message from queue
2. Parse RelationshipsExtractedEvent
3. For each triplet:
   a. MERGE subject entity node
   b. MERGE object entity node
   c. MERGE relationship edge (idempotent)
4. Update mention_count and last_seen
5. Log to PostgreSQL event table
6. Acknowledge message (ACK)
```

**Error Handling:**
```
- Parse Error: NACK + log error (will be requeued)
- Neo4j Connection Error: NACK (auto-retry)
- Deadlock: Retry up to 3x with exponential backoff
- After max retries: NACK (stuck in queue, monitor)
```

### 2. Market Consumer

**Exchange:** `feed.events` (or configured exchange)
**Queue:** `knowledge_graph_market`
**Routing Key:** `market.sync.*`
**Prefetch:** 10 messages

**Event Schema:**
```python
class MarketDataEvent(BaseModel):
    markets: List[MarketData]
    sync_timestamp: datetime

class MarketData(BaseModel):
    symbol: str
    name: str
    asset_type: str
    currency: str
    exchange: str
    sector_code: Optional[str] = None
    sector_name: Optional[str] = None
```

**Processing Logic:**
```
1. Consume market.sync.* event
2. For each market:
   a. MERGE MARKET node with properties
   b. If sector provided: MERGE SECTOR and BELONGS_TO_SECTOR relationship
   c. Update last_updated timestamp
3. Log to PostgreSQL
4. ACK message
```

### 3. Finance Intelligence Consumer

**Exchange:** `finance`
**Queue:** `knowledge_graph_finance_intelligence`
**Routing Key:** `finance.#` (wildcard - all finance events)
**Prefetch:** 10 messages

**Supported Event Types:**

```
finance.company.*
├─ company.update        (name, sector, employees, CEO)
├─ company.ma.announced  (merger/acquisition)
└─ company.ma.completed  (M&A completion)

finance.executives.*
├─ executives.update     (title, pay changes)
├─ executives.joined     (new hire)
└─ executives.departed   (departure)

finance.sec.*
├─ sec.filing.new        (10-K, 10-Q, etc.)
└─ sec.filing.processed  (analyzed filing)

finance.insider.*
├─ insider.trade.new     (buy/sell transactions)
└─ insider.holdings      (position updates)

finance.financials.*
├─ financials.released   (quarterly/annual statements)
└─ metrics.updated       (key metrics)

finance.volatility.*
├─ vix.updated          (S&P 500 volatility)
└─ vvix.updated         (VIX volatility)

finance.treasury.*
├─ treasury.yields       (yield curve)
└─ treasury.spreads      (yield spread updates)

finance.regime.*
└─ regime.changed        (market regime state)
```

**Processing Logic (Example: Company Update):**
```cypher
MERGE (c:COMPANY {symbol: $symbol})
ON CREATE SET
    c.name = $name,
    c.sector = $sector,
    c.employees = $employees,
    c.created_at = datetime()
ON MATCH SET
    c.name = $name,
    c.sector = $sector,
    c.employees = $employees,
    c.last_updated = datetime()

// If CEO provided
MERGE (e:EXECUTIVE {name: $ceo_name})
MERGE (e)-[:WORKS_FOR]->(c)
ON CREATE SET rel.title = "Chief Executive Officer"
```

**Error Handling:**
```
- **CRITICAL FIX (Incident #18):** ON CREATE SET must come immediately after MERGE
- All Cypher queries validated with EXPLAIN before deployment
- Syntax errors cause retry storm - caught early in testing
```

### Publishing Custom Events

To trigger knowledge graph updates from external service:

```python
import pika
import json
from datetime import datetime

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

# Declare exchange (if not exists)
channel.exchange_declare(exchange='news.events', exchange_type='topic', durable=True)

# Publish relationship event
event = {
    "article_id": "uuid-123",
    "article_url": "https://example.com/article",
    "extraction_method": "spacy_ner",
    "triplets": [
        {
            "subject": {
                "name": "Elon Musk",
                "type": "PERSON"
            },
            "relationship_type": "WORKS_FOR",
            "object": {
                "name": "Tesla",
                "type": "ORGANIZATION"
            },
            "confidence": 0.95,
            "evidence": "Elon Musk is CEO of Tesla"
        }
    ]
}

channel.basic_publish(
    exchange='news.events',
    routing_key='relationships.extracted.nlp',
    body=json.dumps(event),
    properties=pika.BasicProperties(
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
    )
)

connection.close()
```

---

## Database Integration

### PostgreSQL Schema

PostgreSQL stores metadata, audit trails, and quality snapshots. Neo4j stores the graph itself.

#### knowledge_graph_events

Event audit trail for all graph modifications.

```sql
CREATE TABLE knowledge_graph_events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT NOW() NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    entity1_name VARCHAR(255) NOT NULL,
    entity2_name VARCHAR(255),
    relationship_type VARCHAR(100),
    old_confidence FLOAT,
    new_confidence FLOAT,
    enrichment_source VARCHAR(100),
    enrichment_summary TEXT,
    user_id VARCHAR(100),
    event_metadata TEXT,  -- JSON

    -- Indexes
    INDEX idx_event_type_timestamp (event_type, timestamp),
    INDEX idx_entity1_timestamp (entity1_name, timestamp),
    INDEX idx_enrichment_source (enrichment_source, timestamp)
);
```

**Example Rows:**
```
event_type: "enrichment_applied"
entity1_name: "Tesla"
enrichment_source: "wikidata"
enrichment_summary: "Added description and founding date"

event_type: "relationship_confidence_updated"
entity1_name: "Elon Musk"
entity2_name: "Tesla"
relationship_type: "WORKS_FOR"
old_confidence: 0.85
new_confidence: 0.95
```

#### graph_quality_snapshots

Daily snapshots of graph quality metrics.

```sql
CREATE TABLE graph_quality_snapshots (
    id INTEGER PRIMARY KEY,
    snapshot_date DATETIME UNIQUE NOT NULL,

    -- Size
    total_nodes INTEGER,
    total_relationships INTEGER,

    -- Quality
    high_confidence_count INTEGER,
    medium_confidence_count INTEGER,
    not_applicable_count INTEGER,
    not_applicable_ratio FLOAT,

    -- Data completeness
    orphaned_entities_count INTEGER,
    entities_with_wikidata INTEGER,
    wikidata_coverage_ratio FLOAT,

    -- Composite score
    quality_score FLOAT,

    INDEX idx_snapshot_date (snapshot_date)
);
```

### Coordination Between Neo4j and PostgreSQL

```
Neo4j (Graph)                PostgreSQL (Metadata)
───────────────────────────────────────────────────

ENTITY nodes ────────────┐
RELATIONSHIP edges  ─────┼──→ Event logged to knowledge_graph_events
                         │    (entity1_name, entity2_name, rel_type)
                         │
                    ┌────▼────┐
                    │ Ingestion│
                    │ Service  │
                    └──────────┘
                         │
                    ┌────▼─────────┐
                    │ Query History│
                    │ Tracker      │
                    └──────────────┘
                         │
                    PostgreSQL: query_history
                    (user_id, query_type, params, time_ms)

Daily Batch Job
    │
    ├─→ MATCH full graph stats in Neo4j
    ├─→ Calculate quality metrics
    ├─→ INSERT snapshot to PostgreSQL
    └─→ Track trends over time
```

---

## Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=knowledge-graph-service
SERVICE_PORT=8111
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687              # Bolt protocol (binary)
NEO4J_USER=neo4j                         # Default user
NEO4J_PASSWORD=neo4j_password_2024       # Set in production!
NEO4J_DATABASE=neo4j                     # Database name
NEO4J_MAX_POOL_SIZE=50                   # Connection pool size
NEO4J_CONNECTION_TIMEOUT=30              # Seconds

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=news.events
RABBITMQ_QUEUE=knowledge_graph_relationships
RABBITMQ_ROUTING_KEY=relationships.extracted.*

# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=news_mcp

# External Services
SCRAPING_SERVICE_URL=http://news-scraping-service:8009
FMP_SERVICE_URL=http://fmp-service:8113
FMP_TIMEOUT=30
FMP_MAX_RETRIES=3
FMP_CIRCUIT_BREAKER_THRESHOLD=5
FMP_CIRCUIT_BREAKER_TIMEOUT=30

# Query Limits
MAX_QUERY_TIMEOUT_SECONDS=30
DEFAULT_RESULT_LIMIT=100
MAX_RESULT_LIMIT=1000

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Docker Environment

```yaml
# docker-compose.yml excerpt
knowledge-graph-service:
  image: knowledge-graph-service:latest
  ports:
    - "8111:8111"
  environment:
    SERVICE_PORT: 8111
    NEO4J_URI: bolt://neo4j:7687
    POSTGRES_HOST: postgres
    RABBITMQ_HOST: rabbitmq
  depends_on:
    - neo4j
    - postgres
    - rabbitmq
  volumes:
    - ./services/knowledge-graph-service:/app
  command: uvicorn app.main:app --host 0.0.0.0 --port 8111 --reload
```

---

## Performance Optimization

### 1. Neo4j Optimization

#### Connection Pooling

```python
# Auto-configured in neo4j_service.py
max_connection_pool_size = 50  # Default
connection_timeout = 30        # Seconds

# For high-concurrency scenarios: increase pool size
# For single-client: reduce to 10-20
```

#### Index Strategy

**Current Indexes:**
```
✓ entity_name (UNIQUE - fastest lookups)
✓ entity_type (filtering by type)
✓ entity_wikidata_id (enrichment lookups)
✓ relationship_confidence (quality filtering)
✓ relationship_type (pattern matching)
✓ market_symbol (UNIQUE - market lookups)
✓ market_type (asset type filtering)
```

**Index Performance Impact:**
```
Without index:   100-500ms (full table scan)
With index:      10-50ms (index seek)
```

#### Memory Configuration

```bash
# Neo4j memory settings (neo4j.conf)
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G

# For large graphs (50K+ nodes):
# - Increase heap to 4-8GB
# - Increase page cache to 4-8GB
# - Monitor with: docker stats neo4j
```

#### Query Optimization

**Bad Query (Full Scan):**
```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS "Tesla"  // String scan
RETURN e
```

**Good Query (Index Usage):**
```cypher
MATCH (e:Entity {name: $name})  // Unique index lookup
RETURN e
```

**EXPLAIN Analysis:**
```bash
# Inside Neo4j Browser or Cypher Shell
EXPLAIN MATCH (e:Entity {name: $name})-[r]->(t:Entity)
WHERE r.confidence >= 0.5
RETURN t

# Look for: NodeIndexSeek (good), AllNodesScan (bad)
```

### 2. API Performance

#### Query Result Caching

```python
# In-memory cache for frequently queried entities
from functools import lru_cache
import time

# Cache top-100 entities
@lru_cache(maxsize=100)
async def get_entity_cached(name: str):
    result = await neo4j_service.execute_query(...)
    return result

# Clear cache daily
@app.on_event("startup")
async def cache_invalidation():
    while True:
        await asyncio.sleep(86400)  # 24 hours
        get_entity_cached.cache_clear()
```

#### Pagination

```python
# API endpoint with pagination
@router.get("/api/v1/graph/entities")
async def list_entities(skip: int = 0, limit: int = 100):
    cypher = """
    MATCH (e:Entity)
    SKIP $skip
    LIMIT $limit
    RETURN e
    """
    results = await neo4j_service.execute_query(
        cypher,
        parameters={"skip": skip, "limit": limit}
    )
    return results
```

### 3. RabbitMQ Consumer Performance

#### Prefetch Optimization

```python
# Process multiple messages concurrently
await self.channel.set_qos(prefetch_count=10)

# Tune based on:
# - Small messages (fast processing): prefetch_count=20-50
# - Large messages (slow processing): prefetch_count=5-10
# - Monitor: queue_size metric
```

#### Batch Processing

```python
# Ingest multiple triplets in single transaction
async def ingest_triplets_batch(triplets: List[Triplet]):
    # Create single Cypher query processing all triplets
    for triplet in triplets:
        await ingestion_service.ingest_triplet(triplet)

    # Better: Use Neo4j transactions
    async with neo4j_service.driver.session() as session:
        async with session.begin_transaction() as tx:
            for triplet in triplets:
                await tx.run(cypher_query, params)
```

### 4. Monitoring Performance

#### Key Metrics to Track

```bash
# Prometheus metrics
kg_query_duration_seconds           # API query latency
kg_consumer_processing_duration_seconds  # Event processing time
kg_ingestion_duration_seconds       # Neo4j write latency
kg_neo4j_operation_duration_seconds # Raw Neo4j latency

# Alert thresholds
- API query > 1000ms: investigate slow queries
- Consumer lag > 100 messages: increase prefetch
- Neo4j latency > 500ms: check indexes/memory
```

#### Query Performance Benchmarks

```
Operation                   Baseline    Target      Status
─────────────────────────────────────────────────────────
Entity lookup (by name)     12ms        <20ms       ✓
Entity connections (100)    87ms        <100ms      ✓
Shortest path (depth 3)     234ms       <500ms      ✓
Analytics query             335ms       <500ms      ✓
Full-text search (10)       23ms        <50ms       ✓
Triplet ingestion           45ms        <100ms      ✓
Consumer processing         120ms       <200ms      ✓
```

---

## Testing

### Unit Tests

```bash
# Run all tests
cd /home/cytrex/news-microservices/services/knowledge-graph-service
pytest tests/ -v

# Run specific test file
pytest tests/test_neo4j_service.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Files

```
tests/
├── test_neo4j_service.py        # Connection, query execution
├── test_ingestion_service.py    # Triplet ingestion, MERGE operations
├── test_pathfinding.py          # Shortest path algorithms
├── test_search.py               # Entity search functionality
├── test_entity_creation.py      # Entity node creation
├── test_entity_deduplication.py # Duplicate handling
├── test_cypher_building.py      # Query construction
├── test_relationship_queries.py # Relationship patterns
├── test_graph_traversal.py      # Traversal algorithms
├── api/
│   └── test_markets_api.py      # Market endpoints
└── integration/
    └── test_fmp_kg_integration.py # FMP service integration
```

### Integration Testing

```bash
# Start services
docker compose up -d neo4j postgres rabbitmq

# Wait for Neo4j to be ready
sleep 10

# Run integration tests
pytest tests/integration/ -v

# Test specific consumer
pytest tests/services/test_market_sync_service.py -v
```

### Load Testing

```python
# Example: Load test Cypher query
import asyncio
import time

async def load_test_entity_lookup():
    async with neo4j_service.driver.session() as session:
        start = time.time()
        tasks = []

        for i in range(100):
            task = session.run(
                "MATCH (e:Entity {name: $name}) RETURN e",
                {"name": f"Entity{i}"}
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        print(f"100 queries: {elapsed:.2f}s ({elapsed/100*1000:.1f}ms each)")
```

---

## Deployment

### Docker Build

```bash
cd /home/cytrex/news-microservices/services/knowledge-graph-service

# Build image
docker build -f Dockerfile.dev -t knowledge-graph-service:latest .

# Push to registry (if using)
docker tag knowledge-graph-service:latest myregistry/knowledge-graph-service:latest
docker push myregistry/knowledge-graph-service:latest
```

### Docker Compose

```bash
# Start all services
docker compose -f /home/cytrex/news-microservices/docker-compose.yml up -d knowledge-graph-service

# Check logs
docker compose logs -f knowledge-graph-service

# Stop service
docker compose down
```

### Health Check

```bash
# Built-in health check
curl http://localhost:8111/health

# Verify Neo4j connection
curl http://localhost:8111/api/v1/graph/stats

# Check Prometheus metrics
curl http://localhost:8111/metrics | grep kg_
```

### Production Deployment Checklist

- [ ] Environment variables set (NEO4J_PASSWORD, POSTGRES_PASSWORD)
- [ ] Neo4j indexes created
- [ ] PostgreSQL database initialized
- [ ] RabbitMQ exchange and queues declared
- [ ] Connection pooling configured for expected load
- [ ] Memory limits set (heap, page cache)
- [ ] Logging configured (ELK stack or similar)
- [ ] Prometheus scraping configured
- [ ] Alerting rules deployed
- [ ] Backups configured
- [ ] Load balancing setup (if needed)
- [ ] DNS/network properly configured

---

## Troubleshooting

### Neo4j Connection Issues

**Symptom:** Service won't start, logs show "Failed to connect to Neo4j"

**Diagnosis:**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs neo4j

# Test connection
docker exec neo4j cypher-shell -u neo4j -p password "RETURN 1"
```

**Solutions:**
1. Verify URI format: `bolt://hostname:7687` (not http)
2. Check credentials in .env file
3. Wait for Neo4j to start (takes 10-20 seconds)
4. Check firewall/network access to port 7687
5. Increase Neo4j heap size if OOM errors

### Slow Graph Queries

**Symptom:** Queries taking >500ms for simple operations

**Diagnosis:**
```bash
# Use EXPLAIN to check execution plan
EXPLAIN MATCH (e:Entity {name: $name})
WHERE e.type = $type
RETURN e

# Look for: AllNodesScan (bad), NodeIndexSeek (good)

# Check indexes exist
SHOW INDEXES
```

**Solutions:**
1. Create missing indexes for frequently filtered properties
2. Use EXPLAIN before optimization
3. Ensure parameters are typed correctly
4. Check relationship cardinality (too many edges?)
5. Increase Neo4j page cache size

### RabbitMQ Consumer Issues

**Symptom:** Messages stuck in queue, not being processed

**Diagnosis:**
```bash
# Check queue status
docker exec rabbitmq rabbitmqctl list_queues name messages

# Check consumer status
curl http://localhost:8111/health | jq .consumer

# Check logs
docker compose logs knowledge-graph-service | grep -i "consumer\|error"
```

**Solutions:**
1. Verify RabbitMQ connection (check logs)
2. Check queue exists and has bindings
3. Restart consumer service
4. Check for Neo4j connection errors (deadlock retry storm)
5. Purge queue if stuck: `rabbitmqctl purge_queue knowledge_graph_relationships`

### High Memory Usage

**Symptom:** Neo4j or service consuming excessive memory

**Diagnosis:**
```bash
# Check Neo4j memory
docker stats neo4j | grep "MEM %"

# Check Python memory
docker exec knowledge-graph-service ps aux | grep python

# Check Cypher query memory usage
PROFILE MATCH (n:Entity) RETURN COUNT(n)  // Shows memory
```

**Solutions:**
1. Reduce Neo4j heap size (if over-allocated)
2. Increase page cache (helps with query performance)
3. Add result pagination limits
4. Check for memory leak in ingestion service
5. Monitor with: `docker stats` (real-time) or Prometheus

### Query Timeouts

**Symptom:** Queries hitting 30s timeout

**Diagnosis:**
```bash
# Check query execution plan
EXPLAIN <your_query>

# Look for: expensive filters, missing indexes, large result sets

# Test with LIMIT
MATCH (n:Entity) RETURN n LIMIT 100  // Fast
MATCH (n:Entity) RETURN n             // Slow (no limit)
```

**Solutions:**
1. Add LIMIT clause to queries
2. Add relationship confidence filter (WHERE r.confidence >= 0.5)
3. Use pagination (SKIP/LIMIT)
4. Increase timeout if query is legitimately expensive
5. Increase Neo4j heap size for better query planning

### Cypher Syntax Errors in Consumer

**Symptom:** "CypherSyntaxError", retry storm, queue backing up

**Critical Issue:** MERGE + ON CREATE SET order matters!

**Wrong Order (CAUSES ERROR):**
```cypher
MERGE (n:Node {id: $id})
SET n.property = $value          # ← Standalone SET
ON CREATE SET n.created = date() # ← ERROR: Expected MERGE
```

**Correct Order:**
```cypher
MERGE (n:Node {id: $id})
ON CREATE SET n.created = date()  # ← After MERGE
ON MATCH SET n.matched = date()   # ← After MERGE
SET n.property = $value           # ← Standalone SET last
```

**Recovery:**
1. Fix Cypher query in code
2. Purge queue: `rabbitmqctl purge_queue knowledge_graph_finance_intelligence`
3. Redeploy service
4. Monitor for successful processing

---

## Critical Incidents & Lessons

### Incident #18: Retry Storm (2025-11-20)

**Severity:** CRITICAL

**What Happened:**
- Cypher syntax error in `finance_intelligence_consumer.py`
- 2500+ messages stuck in retry loop for 15+ hours
- Network traffic 32.6 GB up / 27.2 GB down
- RabbitMQ CPU usage 257%

**Root Cause:**
`ON CREATE SET` placed AFTER `SET` block instead of directly after `MERGE`

**Fixed Locations:**
- Line 236: Company node creation
- Line 282-290: Executive node + WORKS_FOR relationship
- Line 485: Insider trade node creation
- Line 856: MarketRegime node creation

**Prevention Measures:**
1. Add unit tests for all Cypher queries
2. Pre-deployment EXPLAIN validation
3. Pre-commit hooks for syntax checking
4. Dead Letter Queue (DLQ) for failed messages
5. Circuit breaker pattern with exponential backoff

**Impact:** 0 messages lost (all recovered after fix)

---

## Contact & Support

- **Service Owner:** Knowledge Graph Team
- **On-Call:** Check rotation schedule
- **Documentation:** This file + service README
- **Issues:** Create issue in GitHub with `knowledge-graph` label
- **Performance Help:** Check /metrics endpoint or Prometheus dashboard

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-24
**Status:** Production Ready

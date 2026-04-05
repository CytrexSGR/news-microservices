# Knowledge Graph Service - Complete Service Architecture

**Service:** knowledge-graph-service
**Port:** 8111
**Version:** 2.0.0
**Status:** ✅ Production (Implemented)
**Last Updated:** 2025-12-22

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Data Flow](#data-flow)
5. [Neo4j Data Model](#neo4j-data-model)
6. [Component Architecture](#component-architecture)
7. [RabbitMQ Integration](#rabbitmq-integration)
8. [Market Integration Module](#market-integration-module)
9. [Finance Intelligence Consumer](#finance-intelligence-consumer)
10. [Symbolic Findings Ingestion](#symbolic-findings-ingestion)
11. [API Architecture](#api-architecture)
12. [Configuration](#configuration)
13. [Deployment](#deployment)
14. [Monitoring & Metrics](#monitoring--metrics)
15. [Manual Enrichment Workflow](#manual-enrichment-workflow)
16. [Performance Characteristics](#performance-characteristics)
17. [Troubleshooting](#troubleshooting)
18. [Future Enhancements](#future-enhancements)

---

## Overview

### Purpose

The **Knowledge Graph Service** serves as the **central persistent memory** of the news analysis platform with three primary integration channels:

1. **Entity Relationships** - Ingests entity relationship triplets from content-analysis-service
2. **Financial Intelligence** - Consumes all finance.* events from FMP Service for market data integration
3. **Symbolic Findings** - Ingests structured intelligence findings from Intelligence Synthesizer

The service provides query APIs for:

- **Frontend dashboards** - Graph visualization, entity connections, analytics, market data
- **LLM orchestration agents** - Complex multi-hop graph traversal queries
- **Admin tools** - Manual enrichment of relationship quality, custom Cypher queries
- **Financial analysis** - Market indicators, correlations, regime detection

### Key Features

- 📊 **Multi-Domain Graph Storage**: Entities, markets, financial indicators, intelligence findings
- 🔄 **Event-Driven Ingestion**: Three RabbitMQ consumers (relationships, market data, finance intelligence)
- ⚡ **Idempotent Writes**: MERGE-based ingestion prevents duplicates
- 🔍 **Rich Query API**: 37+ endpoints covering entities, markets, analytics, pathfinding
- 🤖 **Manual Enrichment**: Admin workflow for improving NOT_APPLICABLE relationships
- 📈 **Real-Time Analytics**: Entity growth, top entities, relationship distribution
- 💹 **Market Integration**: Sync with FMP Service for stocks, forex, commodities, crypto
- 🌐 **Financial Intelligence**: Track company data, executives, SEC filings, market indicators
- 🎯 **Symbolic Findings**: Ingest structured intelligence findings from OSINT analysis
- 🔎 **Pathfinding**: Find shortest paths between entities in the graph
- 🛡️ **Quality Checks**: Disambiguation analysis, integrity checks
- ⚙️ **Admin Query Tool**: Execute custom read-only Cypher queries
- ✅ **Wikidata Integration**: Q-ID enrichment from upstream canonicalization
- 🚦 **Health Monitoring**: Kubernetes-style liveness/readiness probes

### System Context

```
Content Analysis → relationships.extracted → Knowledge Graph → Graph Query APIs
FMP Service     → finance.*               ↗   (Neo4j)         (REST)
Intelligence    → findings.analyzed       ↗
Synthesizer
```

The service integrates data from three major pipelines into a unified knowledge graph.

---

## Architecture

### System Architecture Diagram

```mermaid
graph TB
    subgraph "Content Analysis Pipeline"
        ContentAnalysis[Content Analysis Service<br/>Port 8102]
        IntSynth[Intelligence Synthesizer]
    end

    subgraph "Financial Data Pipeline"
        FMP[FMP Service<br/>Port 8109]
    end

    subgraph "Message Bus"
        RabbitMQ[RabbitMQ<br/>Port 5672]
    end

    subgraph "Knowledge Graph Service (Port 8111)"
        API[FastAPI Application<br/>CORS Enabled]

        Consumer1[Relationships<br/>Consumer]
        Consumer2[Market Data<br/>Consumer]
        Consumer3[Finance Intelligence<br/>Consumer]

        Neo4jService[Neo4j Service<br/>Connection Pool]
        IngestionService[Ingestion Service<br/>Idempotent MERGE]
        EnrichmentService[Enrichment Service<br/>Wikipedia Integration]
        MarketSyncService[Market Sync Service<br/>FMP Integration]

        Consumer1 -->|Triplets| IngestionService
        Consumer2 -->|Market Data| MarketSyncService
        Consumer3 -->|Finance Events| Neo4jService
        IngestionService -->|Cypher| Neo4jService
        MarketSyncService -->|Cypher| Neo4jService
        API -->|Queries| Neo4jService
        API -->|Manual Enrichment| EnrichmentService
        EnrichmentService -->|Updates| Neo4jService
    end

    subgraph "Storage"
        Neo4j[(Neo4j Graph DB<br/>Port 7687<br/>Multi-Domain Model)]
    end

    subgraph "Clients"
        Frontend[Frontend Dashboard<br/>Port 3000]
        LLMAgent[LLM Orchestrator<br/>Port 8113]
    end

    %% Data Flow
    ContentAnalysis -->|relationships.extracted| RabbitMQ
    IntSynth -->|findings.analyzed| RabbitMQ
    FMP -->|finance.*| RabbitMQ
    RabbitMQ -->|Consume| Consumer1
    RabbitMQ -->|Consume| Consumer2
    RabbitMQ -->|Consume| Consumer3
    Neo4jService -->|Read/Write| Neo4j

    Frontend -->|GET /api/v1/graph/*| API
    LLMAgent -->|GET /api/v1/graph/*| API

    style API fill:#00ff00,stroke:#333,stroke-width:2px
    style Neo4j fill:#4581C3,stroke:#333,stroke-width:2px
    style Neo4jService fill:#90EE90,stroke:#333,stroke-width:2px
```

### Component Overview

| Component | Purpose | Technology | Key Features |
|-----------|---------|------------|--------------|
| **FastAPI App** | HTTP API server | FastAPI 0.115+ | CORS, Prometheus, JWT auth, 37+ endpoints |
| **Relationships Consumer** | Entity relationship ingestion | aio-pika 9.4+ | Prefetch QoS, graceful ACK |
| **Market Data Consumer** | Market metadata sync | aio-pika 9.4+ | Idempotent market node creation |
| **Finance Intelligence Consumer** | Financial events ingestion | aio-pika 9.4+ | 37 event handlers, wildcard routing |
| **Neo4j Service** | Database connection | neo4j-driver 5.25+ | Connection pooling, retry logic |
| **Ingestion Service** | Entity graph writes | Cypher MERGE | Idempotent, transactional |
| **Market Sync Service** | FMP integration | HTTP client | Batch sync, error handling |
| **Enrichment Service** | Quality improvement | Wikipedia API | NOT_APPLICABLE analysis |
| **Pathfinding Service** | Graph traversal | Neo4j allShortestPaths | Multi-hop pathfinding |
| **Analytics Routes** | Statistics API | FastAPI routes | Entity/market stats, growth trends |
| **Health Routes** | K8s probes | FastAPI routes | Liveness, readiness checks |

### File Structure

```
services/knowledge-graph-service/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app + lifespan (3 consumers)
│   ├── config.py                        # Pydantic settings
│   │
│   ├── api/
│   │   ├── dependencies.py              # DI, JWT validation
│   │   └── routes/
│   │       ├── health.py                # 6 health check endpoints
│   │       ├── graph.py                 # 2 entity query endpoints
│   │       ├── analytics.py             # 7 analytics endpoints
│   │       ├── enrichment.py            # 4 enrichment endpoints
│   │       ├── markets.py               # 5 market endpoints (NEW)
│   │       ├── pathfinding.py           # 1 pathfinding endpoint (NEW)
│   │       ├── admin_query.py           # 4 admin query endpoints (NEW)
│   │       ├── quality.py               # 2 quality check endpoints (NEW)
│   │       ├── findings.py              # 1 findings ingestion endpoint (NEW)
│   │       ├── articles.py              # 2 article query endpoints
│   │       ├── search.py                # 1 entity search endpoint
│   │       └── history.py               # 2 history endpoints
│   │
│   ├── consumers/
│   │   ├── relationships_consumer.py    # Entity relationships
│   │   ├── market_consumer.py           # Market data sync (NEW)
│   │   ├── finance_intelligence_consumer.py  # Finance events (NEW)
│   │   └── event_schemas.py             # Pydantic event models
│   │
│   ├── services/
│   │   ├── neo4j_service.py             # Neo4j driver wrapper
│   │   ├── ingestion_service.py         # Triplet ingestion logic
│   │   ├── enrichment_service.py        # Wikipedia + enrichment
│   │   ├── wikipedia_client.py          # Wikipedia API client
│   │   ├── pathfinding_service.py       # Path finding (NEW)
│   │   ├── query_service.py             # Custom Cypher execution (NEW)
│   │   ├── query_validator.py           # Cypher validation (NEW)
│   │   ├── cypher_validator.py          # Syntax validation (NEW)
│   │   ├── search_service.py            # Entity search (NEW)
│   │   ├── article_service.py           # Article queries (NEW)
│   │   ├── event_logger.py              # Event tracking (NEW)
│   │   └── fmp_integration/             # FMP Service integration (NEW)
│   │       ├── __init__.py
│   │       └── market_sync_service.py   # Market sync orchestration
│   │
│   ├── clients/
│   │   └── fmp_service_client.py        # FMP HTTP client (NEW)
│   │
│   ├── models/
│   │   ├── graph.py                     # Entity, Relationship, Triplet
│   │   ├── events.py                    # RabbitMQ event schemas
│   │   ├── requests.py                  # API request models
│   │   ├── responses.py                 # API response models
│   │   ├── findings.py                  # Symbolic findings models (NEW)
│   │   ├── pathfinding.py               # Pathfinding models (NEW)
│   │   ├── admin_query.py               # Admin query models (NEW)
│   │   ├── enums.py                     # AssetType, ExchangeType enums (NEW)
│   │   └── neo4j_queries.py             # Pre-built Cypher queries (NEW)
│   │
│   ├── schemas/
│   │   ├── markets.py                   # Market/Sector schemas (NEW)
│   │   └── sync_results.py              # Sync result schemas (NEW)
│   │
│   ├── database/
│   │   └── models.py                    # SQLAlchemy models (event log) (NEW)
│   │
│   └── core/
│       ├── metrics.py                   # Prometheus metrics
│       ├── errors.py                    # Custom exceptions (NEW)
│       ├── rate_limiting.py             # SlowAPI limiter (NEW)
│       └── logging_config.py            # Structured logging (NEW)
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_neo4j_service.py
│   ├── test_api.py
│   ├── test_market_sync.py             # Market sync tests (NEW)
│   ├── test_finance_consumer.py        # Finance consumer tests (NEW)
│   └── test_pathfinding.py             # Pathfinding tests (NEW)
│
├── scripts/
│   └── migrate_relationships_to_uppercase.py  # Data migration
│
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Technology Stack

### Core Technologies

| Technology | Version | Purpose | Justification |
|-----------|---------|---------|---------------|
| **Python** | 3.11+ | Service language | Platform standard, async support |
| **FastAPI** | 0.115+ | Web framework | High performance, auto docs, async |
| **Neo4j** | 5.25 Community | Graph database | Native graph storage, Cypher queries |
| **neo4j-driver** | 5.25+ | DB driver | Official async Python driver |
| **aio-pika** | 9.4+ | RabbitMQ client | Async message consumption |
| **Pydantic** | 2.8+ | Data validation | Type safety, settings management |
| **Prometheus Client** | 0.20+ | Metrics | Monitoring integration |
| **Tenacity** | 9.0+ | Retry logic | Connection resilience |
| **httpx** | 0.27+ | HTTP client | Async FMP Service calls |
| **SlowAPI** | 0.1+ | Rate limiting | Admin endpoint protection |

### Why Neo4j?

**Neo4j was chosen because:**

1. **Native Graph Storage** - Relationships are first-class citizens, not foreign keys
2. **Cypher Query Language** - Declarative, SQL-like syntax for graph patterns
3. **Performance** - O(1) relationship traversal, optimized for connected data
4. **Production-Ready** - ACID transactions, clustering support (Enterprise)
5. **Community Edition** - Free for production use with full feature set
6. **Property Graph Model** - Perfect for multi-domain data (entities, markets, events)

**Alternatives considered:**
- ❌ PostgreSQL + pg_graph: Poor traversal performance for multi-hop queries
- ❌ Amazon Neptune: Vendor lock-in, complex setup
- ⚠️ ArangoDB: Multi-model flexible, but less mature graph features
- ✅ **Neo4j**: Best-in-class for property graphs

### Dependencies

```toml
# Key dependencies from requirements.txt

# Web Framework
fastapi==0.115.0
uvicorn[standard]==0.30.0

# Graph Database
neo4j==5.25.0

# Message Queue
aio-pika==9.4.0

# Data Validation
pydantic==2.8.0
pydantic-settings==2.4.0

# HTTP Client
httpx==0.27.0

# Monitoring
prometheus-client==0.20.0

# Rate Limiting
slowapi==0.1.9

# Utilities
tenacity==9.0.0

# Database (Event Log)
sqlalchemy==2.0.23
asyncpg==0.29.0
```

---

## Data Flow

### Event-Driven Ingestion Flow (Entities)

```mermaid
sequenceDiagram
    participant CA as Content Analysis<br/>Service
    participant MQ as RabbitMQ<br/>news.events
    participant Consumer as Relationships<br/>Consumer
    participant Ingestion as Ingestion<br/>Service
    participant Neo4j as Neo4j<br/>Database

    Note over CA: Article analyzed,<br/>entities extracted

    CA->>MQ: Publish relationships.extracted<br/>{article_id, triplets[...]}
    Note over MQ: Exchange: news.events<br/>Routing: relationships.extracted.*

    MQ->>Consumer: Deliver message<br/>(prefetch: 10)

    Consumer->>Consumer: Parse Pydantic model<br/>RelationshipsExtractedEvent

    loop For each triplet
        Consumer->>Ingestion: ingest_triplet(triplet)

        Ingestion->>Neo4j: MERGE (subject:Entity)<br/>ON CREATE SET ...<br/>ON MATCH SET ...
        Ingestion->>Neo4j: MERGE (object:Entity)<br/>ON CREATE SET ...<br/>ON MATCH SET ...
        Ingestion->>Neo4j: MERGE (subject)-[rel:TYPE]->(object)<br/>ON CREATE/MATCH ...

        Neo4j-->>Ingestion: Summary (nodes/rels created)
        Ingestion-->>Consumer: Success
    end

    Consumer->>MQ: ACK message
    Note over Consumer: Prometheus metrics:<br/>kg_events_consumed_total<br/>kg_consumer_processing_duration

    Note over Neo4j: Knowledge graph updated,<br/>ready for queries
```

### Market Data Flow (Finance Integration)

```mermaid
sequenceDiagram
    participant FMP as FMP Service<br/>Background Jobs
    participant MQ as RabbitMQ<br/>finance exchange
    participant Consumer as Finance Intelligence<br/>Consumer
    participant Neo4j as Neo4j<br/>Database

    Note over FMP: Scheduled job:<br/>Sync market data

    FMP->>MQ: Publish finance.company.profile.updated<br/>{symbol, company_data}
    FMP->>MQ: Publish finance.key_metrics.updated<br/>{symbol, metrics}
    FMP->>MQ: Publish finance.volatility.updated<br/>{date, vix, vvix, move}

    Note over MQ: Exchange: finance (Topic)<br/>Routing: finance.#

    MQ->>Consumer: Deliver message<br/>(wildcard subscription)

    Consumer->>Consumer: Parse event_type<br/>Route to handler

    alt Company Profile Event
        Consumer->>Neo4j: MERGE (c:Company {symbol: ...})<br/>SET name, sector, industry...
    else Market Indicator Event
        Consumer->>Neo4j: CREATE (i:MarketIndicator {<br/>type: 'VIX', value: ...})
    else Regime Change Event
        Consumer->>Neo4j: MERGE (r:MarketRegime {date: ...})<br/>SET regime_type, signals...
    end

    Consumer->>MQ: ACK message

    Note over Neo4j: Financial graph updated:<br/>Companies, Indicators, Regimes
```

### Query Flow (Frontend → Graph API)

```mermaid
sequenceDiagram
    participant Frontend as Frontend<br/>Dashboard
    participant API as Graph API<br/>(FastAPI)
    participant Neo4jSvc as Neo4j<br/>Service
    participant Neo4j as Neo4j<br/>Database

    Note over Frontend: User views entity<br/>connections page

    Frontend->>API: GET /api/v1/graph/entity/Microsoft/connections<br/>?relationship_type=WORKS_FOR&limit=50

    API->>API: JWT validation<br/>(if enabled)

    API->>Neo4jSvc: execute_query(<br/>cypher, parameters)

    Neo4jSvc->>Neo4j: MATCH (e:Entity {name: "Microsoft"})<br/><-[r:WORKS_FOR]-(p:Entity)<br/>RETURN p, r<br/>LIMIT 50

    Neo4j-->>Neo4jSvc: Query results<br/>(nodes + relationships)

    Neo4jSvc-->>API: List[Dict]<br/>(parsed records)

    API->>API: Transform to<br/>GraphResponse model

    API-->>Frontend: JSON response:<br/>{nodes: [...], edges: [...]}

    Note over Frontend: Render graph<br/>visualization
```

---

## Neo4j Data Model

### Current Implementation Status

**✅ Multi-Domain Graph Model Implemented:**

| Domain | Node Labels | Status | Count (Est.) |
|--------|-------------|--------|--------------|
| **Entity Graph** | `:Entity` | ✅ Production | 3,867+ nodes |
| **Market Data** | `:Market`, `:Sector`, `:Company`, `:Executive` | ✅ Production | 500+ nodes |
| **Financial Indicators** | `:MarketIndicator`, `:MarketRegime` | ✅ Production | 1,000+ nodes |
| **Intelligence Findings** | `:Event:*`, `:IHL_VIOLATION`, `:FINANCIAL_EVENT`, `:HUMANITARIAN_CRISIS` | ✅ Production | 50+ nodes |
| **Article Nodes** | `:Article` | ❌ **NOT IMPLEMENTED** | - |

### Entity Node Schema

**All entities stored as `:Entity` label with type property:**

```cypher
(:Entity {
    name: String,              // Unique entity name (e.g., "Elon Musk")
    type: String,              // Entity type (PERSON, ORGANIZATION, LOCATION, etc.)
    created_at: DateTime,      // First appearance in graph
    last_seen: DateTime,       // Most recent mention
    wikidata_id: String?       // Optional Q-ID from canonicalization
})
```

#### Entity Types (from EntityType Enum)

```
PERSON, ORGANIZATION, LOCATION, EVENT, PRODUCT,
LEGISLATION, LEGAL_CASE, MOVIE, PLATFORM, NATIONALITY,
MONEY, PERCENT, QUANTITY, DATE
```

**Example Entity Nodes:**

```cypher
(:Entity {
    name: "Elon Musk",
    type: "PERSON",
    created_at: datetime("2025-01-15T10:30:00Z"),
    last_seen: datetime("2025-10-24T12:00:00Z"),
    wikidata_id: "Q317521"
})

(:Entity {
    name: "Tesla",
    type: "ORGANIZATION",
    created_at: datetime("2025-01-15T10:30:00Z"),
    last_seen: datetime("2025-10-24T12:00:00Z"),
    wikidata_id: "Q478214"
})
```

### Market Node Schema (NEW)

**Market nodes represent tradable assets:**

```cypher
(:Market {
    symbol: String,            // Ticker symbol (e.g., "AAPL", "EURUSD")
    name: String,              // Full name (e.g., "Apple Inc.")
    asset_type: String,        // STOCK, FOREX, COMMODITY, CRYPTO
    exchange: String?,         // Primary exchange (NASDAQ, NYSE, etc.)
    currency: String,          // Price denomination (default: USD)
    is_active: Boolean,        // Currently tradable
    isin: String?,             // International Securities ID
    sector: String?,           // Sector code (for BELONGS_TO_SECTOR)

    // Price data (optional)
    current_price: Float?,
    day_change_percent: Float?,
    market_cap: Integer?,
    volume: Integer?,

    // Timestamps
    created_at: DateTime,
    last_updated: DateTime
})
```

**Example Market Nodes:**

```cypher
(:Market {
    symbol: "AAPL",
    name: "Apple Inc.",
    asset_type: "STOCK",
    exchange: "NASDAQ",
    currency: "USD",
    is_active: true,
    isin: "US0378331005",
    sector: "XLK",
    current_price: 178.45,
    day_change_percent: 1.23,
    market_cap: 2800000000000,
    volume: 52340000,
    created_at: datetime("2024-01-15T10:30:00Z"),
    last_updated: datetime("2025-12-22T16:00:00Z")
})

(:Market {
    symbol: "EURUSD",
    name: "Euro/US Dollar",
    asset_type: "FOREX",
    exchange: null,
    currency: "USD",
    is_active: true,
    created_at: datetime("2024-01-15T10:30:00Z"),
    last_updated: datetime("2025-12-22T16:00:00Z")
})
```

### Company Node Schema (NEW)

**Company nodes store corporate metadata:**

```cypher
(:Company {
    symbol: String,            // Stock symbol (primary key)
    name: String,              // Company name
    cik: String?,              // SEC Central Index Key
    sector: String?,           // Business sector
    industry: String?,         // Specific industry
    country: String?,          // HQ country
    exchange: String?,         // Primary exchange
    market_cap: Integer?,      // Market capitalization
    employees: Integer?,       // Employee count
    created_at: DateTime,
    updated_at: DateTime
})
```

**Example Company Node:**

```cypher
(:Company {
    symbol: "AAPL",
    name: "Apple Inc.",
    cik: "0000320193",
    sector: "Technology",
    industry: "Consumer Electronics",
    country: "US",
    exchange: "NASDAQ",
    market_cap: 2800000000000,
    employees: 161000,
    created_at: datetime("2024-01-15T10:30:00Z"),
    updated_at: datetime("2025-12-22T12:00:00Z")
})
```

### Executive Node Schema (NEW)

**Executive nodes track company leadership:**

```cypher
(:Executive {
    name: String,              // Full name
    title: String?,            // Position title
    age: Integer?,             // Age
    since_year: Integer?,      // Start year in position
    pay_usd: Integer?,         // Annual compensation
    created_at: DateTime,
    updated_at: DateTime
})
```

### Market Indicator Node Schema (NEW)

**Market indicator nodes track economic metrics:**

```cypher
(:MarketIndicator {
    indicator_id: String,      // Unique ID (e.g., "VIX_2025-12-22")
    indicator_type: String,    // VIX, VVIX, MOVE, DXY, TREASURY_10Y, etc.
    date: Date,                // Observation date
    value: Float,              // Indicator value
    created_at: DateTime
})
```

**Example Market Indicator Nodes:**

```cypher
(:MarketIndicator {
    indicator_id: "VIX_2025-12-22",
    indicator_type: "VIX",
    date: date("2025-12-22"),
    value: 18.75,
    created_at: datetime("2025-12-22T16:00:00Z")
})

(:MarketIndicator {
    indicator_id: "TREASURY_10Y_2025-12-22",
    indicator_type: "TREASURY_10Y",
    date: date("2025-12-22"),
    value: 4.25,
    created_at: datetime("2025-12-22T16:00:00Z")
})
```

### Market Regime Node Schema (NEW)

**Market regime nodes track market state:**

```cypher
(:MarketRegime {
    date: Date,                // Regime date (primary key)
    regime_type: String,       // RISK_ON, RISK_OFF, TRANSITION
    regime_score: Float,       // Confidence score (0-1)

    // Individual signals
    vix_signal: String?,       // VIX interpretation
    correlation_signal: String?,
    yield_curve_signal: String?,
    dxy_signal: String?,
    carry_trade_signal: String?,

    created_at: DateTime,
    updated_at: DateTime
})
```

### Sector Node Schema (NEW)

**Sector nodes classify markets:**

```cypher
(:Sector {
    code: String,              // Sector code (e.g., "XLK", "XLF")
    name: String,              // Sector name (e.g., "Information Technology")
    description: String?,      // Detailed description
    market_classification: String  // GICS, ICB, etc. (default: GICS)
})
```

**Example Sector Node:**

```cypher
(:Sector {
    code: "XLK",
    name: "Information Technology",
    description: "Companies that develop software, provide IT services, manufacture technology hardware and equipment, and semiconductor components",
    market_classification: "GICS"
})
```

### Intelligence Finding Node Schemas (NEW)

**Intelligence findings are stored as specialized event nodes:**

```cypher
// Conflict Event
(:Event:MilitaryAction {
    event_id: String,
    event_type: String,        // MISSILE_STRIKE, DRONE_ATTACK, etc.
    target_type: String,       // INFRASTRUCTURE, CIVILIAN, etc.
    severity: String,          // CRITICAL, HIGH, MEDIUM, LOW
    casualties: Integer?,
    location: String,
    article_id: String,
    confidence: Float,
    created_at: DateTime
})

// IHL Violation
(:IHL_VIOLATION {
    name: String,
    violation_type: String,    // CIVILIAN_TARGET, PROTECTED_SITE, etc.
    created_at: DateTime
})

// Financial Event
(:FINANCIAL_EVENT {
    name: String,
    volatility: String,        // HIGH, MEDIUM, LOW
    created_at: DateTime
})

// Humanitarian Crisis
(:HUMANITARIAN_CRISIS {
    name: String,
    crisis_type: String,       // DISPLACEMENT, FOOD_SHORTAGE, etc.
    severity: String,
    created_at: DateTime
})
```

### Relationship Schema

**Relationships stored with dynamic types:**

```cypher
(:Entity)-[relationship_type]->(:Entity)

Relationship Properties:
{
    confidence: Float,          // 0.0-1.0 extraction confidence
    mention_count: Integer,     // Number of times mentioned
    created_at: DateTime,       // First extraction
    last_seen: DateTime,        // Most recent mention
    evidence: String,           // Source text supporting relationship
    source_url: String,         // Article URL
    article_id: String,         // Article UUID
    enrichment_source: String?, // "manual_enrichment" if enriched
    enriched_at: DateTime?      // When enrichment was applied
}
```

#### Relationship Types

**Core Relationships:**
```
WORKS_FOR, LOCATED_IN, OWNS, MEMBER_OF, PARTNER_OF, RELATED_TO
```

**Business Relationships:**
```
REPORTS_TO, PRODUCES, FOUNDED_BY, FOUNDED_IN, OWNED_BY,
ACQUIRED, INVESTED_IN, COMPETES_WITH
```

**Market Relationships (NEW):**
```
BELONGS_TO_SECTOR    (:Market)-[:BELONGS_TO_SECTOR]->(:Sector)
TICKER               (:Organization)-[:TICKER]->(:Market)
```

**Company Relationships (NEW):**
```
WORKS_FOR     (:Executive)-[:WORKS_FOR {title, pay_usd}]->(:Company)
FILED         (:Company)-[:FILED {filing_type, date}]->(:SECFiling)
ACQUIRED      (:Company)-[:ACQUIRED {deal_value, date}]->(:Company)
TRADES_IN     (:Executive)-[:TRADES_IN {shares, price}]->(:InsiderTrade)
OF_COMPANY    (:InsiderTrade)-[:OF_COMPANY]->(:Company)
```

**Intelligence Relationships (NEW):**
```
ATTACKS              (:Location)-[:ATTACKS {event_type, casualties}]->(:Location)
VIOLATES_IHL         (:Location)-[:VIOLATES_IHL {violation_type}]->(:IHL_VIOLATION)
AFFECTS_REGIONALLY   (:Location)-[:AFFECTS_REGIONALLY {spillover_risk}]->(:Location)
IMPACTS_MARKET       (:Event)-[:IMPACTS_MARKET {change_percentage}]->(:Market)
INFLUENCES_POLICY    (:Location)-[:INFLUENCES_POLICY {policy_area}]->(:Location)
THREATENS            (:Location)-[:THREATENS {threat_type}]->(:Location)
OCCURS_AT            (:Crisis)-[:OCCURS_AT {affected_population}]->(:Location)
```

**Generic Fallback:**
```
NOT_APPLICABLE  // Requires manual enrichment
```

### Neo4j Indexes & Constraints

**Created automatically on service startup:**

```cypher
// Index on entity names for fast lookups
CREATE INDEX entity_name_index IF NOT EXISTS
FOR (e:Entity)
ON (e.name);

// Unique constraint on (name, type) combination
CREATE CONSTRAINT entity_unique IF NOT EXISTS
FOR (e:Entity)
REQUIRE (e.name, e.type) IS UNIQUE;

// Index on market symbols
CREATE INDEX market_symbol_index IF NOT EXISTS
FOR (m:Market)
ON (m.symbol);

// Index on company symbols
CREATE INDEX company_symbol_index IF NOT EXISTS
FOR (c:Company)
ON (c.symbol);

// Index on indicator types and dates
CREATE INDEX indicator_type_index IF NOT EXISTS
FOR (i:MarketIndicator)
ON (i.indicator_type);

CREATE INDEX indicator_date_index IF NOT EXISTS
FOR (i:MarketIndicator)
ON (i.date);
```

### Query Examples

**Find all entities connected to an organization:**

```cypher
MATCH (e:Entity {name: "Tesla"})-[r]-(connected:Entity)
RETURN connected.name, type(r) AS relationship, r.confidence
ORDER BY r.confidence DESC
LIMIT 20
```

**Find markets in a sector:**

```cypher
MATCH (m:Market)-[:BELONGS_TO_SECTOR]->(s:Sector {code: "XLK"})
RETURN m.symbol, m.name, m.current_price
ORDER BY m.market_cap DESC
LIMIT 20
```

**Find company executives:**

```cypher
MATCH (e:Executive)-[r:WORKS_FOR]->(c:Company {symbol: "AAPL"})
RETURN e.name, r.title, r.pay_usd
ORDER BY r.pay_usd DESC
```

**Find recent market indicators:**

```cypher
MATCH (i:MarketIndicator)
WHERE i.indicator_type = 'VIX'
  AND i.date >= date('2025-12-01')
RETURN i.date, i.value
ORDER BY i.date DESC
```

**Find intelligence findings by location:**

```cypher
MATCH (loc:LOCATION {iso_code: "UA"})<-[r:ATTACKS]-(aggressor:LOCATION)
RETURN aggressor.name, r.event_type, r.casualties, r.severity
ORDER BY r.created_at DESC
LIMIT 10
```

---

## Component Architecture

### 1. FastAPI Application (main.py)

**Purpose**: HTTP server with async lifecycle management for 3 RabbitMQ consumers

**Key Features:**
- Async lifespan context manager for startup/shutdown
- CORS middleware for frontend access
- Prometheus metrics endpoint at `/metrics`
- Route registration for 11 route modules
- Three consumer initialization and management

**Startup Sequence:**
```python
async def lifespan(app: FastAPI):
    # 1. Create PostgreSQL tables (event log)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Connect to Neo4j
    await neo4j_service.connect()
    # Creates driver, verifies connectivity, creates indexes

    # 3. Connect to RabbitMQ (Consumer 1: Relationships)
    await relationships_consumer.connect()
    await relationships_consumer.start_consuming()

    # 4. Connect to RabbitMQ (Consumer 2: Market Data)
    market_sync_service = MarketSyncService()
    market_consumer = await get_market_consumer(market_sync_service)
    await market_consumer.start_consuming()

    # 5. Connect to RabbitMQ (Consumer 3: Finance Intelligence)
    finance_consumer = await get_finance_intelligence_consumer()
    await finance_consumer.start_consuming()

    # 6. Mark services as healthy
    kg_health_status.labels(component='overall').set(1)

    yield  # App runs here

    # Shutdown: Graceful disconnect
    await relationships_consumer.disconnect()
    await close_market_consumer()
    await close_finance_intelligence_consumer()
    await neo4j_service.disconnect()
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/main.py`

---

### 2. Neo4j Service (neo4j_service.py)

**Purpose**: Manages Neo4j driver connection, query execution, health checks

**Key Features:**
- Async connection pooling (max 50 connections)
- Automatic retry logic with exponential backoff (3 attempts)
- Automatic index creation on startup
- Read and write query methods

**Connection Management:**

```python
class Neo4jService:
    async def connect(self):
        """Establish Neo4j connection."""
        self.driver = AsyncGraphDatabase.driver(
            uri=settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_pool_size=settings.NEO4J_MAX_POOL_SIZE,
            connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT
        )
        await self.driver.verify_connectivity()
        await self._create_indexes()
```

**Query Methods:**

```python
# Read query with automatic retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def execute_query(query: str, parameters: Dict) -> List[Dict]:
    """Execute Cypher query, return results as dictionaries."""
    async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
        result = await session.run(query, parameters)
        records = await result.data()
        return records

# Write query with transaction summary
async def execute_write(query: str, parameters: Dict) -> Dict:
    """Execute write transaction, return summary."""
    async with self.driver.session() as session:
        result = await session.run(query, parameters)
        summary = await result.consume()
        return {
            "nodes_created": summary.counters.nodes_created,
            "relationships_created": summary.counters.relationships_created,
            "properties_set": summary.counters.properties_set
        }
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/services/neo4j_service.py`

---

### 3. Ingestion Service (ingestion_service.py)

**Purpose**: Writes entity triplets to Neo4j using idempotent MERGE queries

**Key Features:**
- MERGE-based ingestion (idempotent - no duplicates)
- Automatic mention_count increment for repeated relationships
- Confidence score updates (keeps highest)
- **Relationship type normalization to UPPERCASE** (prevents case-inconsistency duplicates)
- Prometheus metrics for ingestion rate and duration

**Idempotent MERGE Logic:**

```python
async def ingest_triplet(triplet: Triplet) -> Dict:
    """Ingest single triplet using MERGE."""

    cypher = """
    // Create or update subject entity
    MERGE (subject:Entity {name: $subject_name, type: $subject_type})
    ON CREATE SET
        subject.created_at = datetime(),
        subject.last_seen = datetime(),
        subject.wikidata_id = $subject_wikidata_id
    ON MATCH SET
        subject.last_seen = datetime(),
        subject.wikidata_id = COALESCE(subject.wikidata_id, $subject_wikidata_id)

    // Create or update object entity
    MERGE (object:Entity {name: $object_name, type: $object_type})
    ON CREATE SET
        object.created_at = datetime(),
        object.last_seen = datetime(),
        object.wikidata_id = $object_wikidata_id
    ON MATCH SET
        object.last_seen = datetime(),
        object.wikidata_id = COALESCE(object.wikidata_id, $object_wikidata_id)

    // Create or update relationship
    MERGE (subject)-[rel:{rel_type}]->(object)
    ON CREATE SET
        rel.confidence = $confidence,
        rel.mention_count = 1,
        rel.created_at = datetime(),
        rel.evidence = $evidence,
        rel.source_url = $source_url,
        rel.article_id = $article_id
    ON MATCH SET
        rel.mention_count = rel.mention_count + 1,
        rel.last_seen = datetime(),
        rel.confidence = CASE
            WHEN $confidence > rel.confidence THEN $confidence
            ELSE rel.confidence
        END

    RETURN subject, rel, object
    """

    # CRITICAL: Normalize to UPPERCASE
    relationship_type_normalized = triplet.relationship.relationship_type.upper()
    cypher_final = cypher.replace("{rel_type}", relationship_type_normalized)

    summary = await neo4j_service.execute_write(cypher_final, parameters)
    return summary
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/services/ingestion_service.py`

---

### 4. Market Sync Service (market_sync_service.py) - NEW

**Purpose**: Orchestrates market data sync from FMP Service to Neo4j

**Key Features:**
- Batch sync of market metadata (stocks, forex, commodities, crypto)
- Idempotent MERGE operations for market nodes
- Sector relationship creation (BELONGS_TO_SECTOR)
- Error handling and retry logic
- Sync tracking and statistics

**Market Sync Flow:**

```python
async def sync_all_markets(
    self,
    symbols: List[str] = None,
    asset_types: List[str] = None,
    force_refresh: bool = False
) -> SyncResult:
    """
    Sync market data from FMP Service to Neo4j.

    Args:
        symbols: Optional list of specific symbols to sync
        asset_types: Optional list of asset types (STOCK, FOREX, etc.)
        force_refresh: Force fresh data from FMP API

    Returns:
        SyncResult with sync statistics
    """
    sync_id = str(uuid4())
    start_time = time.time()

    # Fetch market data from FMP Service
    fmp_client = get_fmp_service_client()
    markets_data = await fmp_client.list_assets(
        asset_types=asset_types,
        symbols=symbols,
        force_refresh=force_refresh
    )

    # Sync each market to Neo4j
    synced_count = 0
    errors = []

    for market_data in markets_data:
        try:
            await self._sync_single_market(market_data)
            synced_count += 1
        except Exception as e:
            errors.append(f"{market_data['symbol']}: {str(e)}")

    duration = time.time() - start_time

    return SyncResult(
        sync_id=sync_id,
        status='completed' if not errors else 'partial',
        total_assets=len(markets_data),
        synced=synced_count,
        failed=len(errors),
        duration_seconds=duration,
        errors=errors[:10]  # Limit error list
    )

async def _sync_single_market(self, market_data: Dict) -> None:
    """Sync single market to Neo4j."""

    cypher = """
    // Create or update Market node
    MERGE (m:Market {symbol: $symbol})
    ON CREATE SET
        m.created_at = datetime()
    SET
        m.name = $name,
        m.asset_type = $asset_type,
        m.exchange = $exchange,
        m.currency = $currency,
        m.is_active = $is_active,
        m.isin = $isin,
        m.sector = $sector,
        m.last_updated = datetime()

    // Create sector relationship if sector exists
    WITH m
    WHERE $sector IS NOT NULL
    MERGE (s:Sector {code: $sector})
    ON CREATE SET s.name = $sector, s.market_classification = 'GICS'
    MERGE (m)-[:BELONGS_TO_SECTOR]->(s)

    RETURN m
    """

    await neo4j_service.execute_write(cypher, {
        'symbol': market_data['symbol'],
        'name': market_data['name'],
        'asset_type': market_data['asset_type'],
        'exchange': market_data.get('exchange'),
        'currency': market_data.get('currency', 'USD'),
        'is_active': market_data.get('is_active', True),
        'isin': market_data.get('isin'),
        'sector': market_data.get('sector')
    })
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/services/fmp_integration/market_sync_service.py`

---

### 5. Pathfinding Service (pathfinding_service.py) - NEW

**Purpose**: Find shortest paths between entities in the knowledge graph

**Key Features:**
- Uses Neo4j's `allShortestPaths()` algorithm
- Confidence filtering (min_confidence parameter)
- Multi-path discovery (up to limit paths)
- Performance-optimized with max depth limits

**Pathfinding Implementation:**

```python
async def find_paths(
    self,
    entity1: str,
    entity2: str,
    max_depth: int = 3,
    limit: int = 3,
    min_confidence: float = 0.5
) -> List[Path]:
    """
    Find shortest paths between two entities.

    Args:
        entity1: Source entity name
        entity2: Target entity name
        max_depth: Maximum path length (1-5 hops)
        limit: Maximum number of paths to return (1-10)
        min_confidence: Minimum relationship confidence (0.0-1.0)

    Returns:
        List of Path objects with nodes and relationships
    """

    cypher = """
    MATCH (start:Entity {name: $entity1}), (end:Entity {name: $entity2})
    MATCH path = allShortestPaths((start)-[*..%d]-(end))
    WHERE ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
    WITH path, length(path) AS path_length
    ORDER BY path_length
    LIMIT $limit

    RETURN [node IN nodes(path) | {
        name: node.name,
        type: node.type
    }] AS nodes,

    [rel IN relationships(path) | {
        type: type(rel),
        confidence: rel.confidence,
        evidence: rel.evidence
    }] AS relationships,

    path_length
    """ % max_depth

    results = await neo4j_service.execute_query(cypher, {
        'entity1': entity1,
        'entity2': entity2,
        'min_confidence': min_confidence,
        'limit': limit
    })

    paths = []
    for record in results:
        paths.append(Path(
            length=record['path_length'],
            nodes=record['nodes'],
            relationships=record['relationships']
        ))

    return paths
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/services/pathfinding_service.py`

---

### 6. Query Service (query_service.py) - NEW

**Purpose**: Execute custom read-only Cypher queries with security validation

**Key Features:**
- Query validation (blocks write operations)
- Syntax checking with cypher_validator
- Timeout enforcement (max 30 seconds)
- Query hashing for logging and auditing
- Forbidden pattern detection

**Custom Query Execution:**

```python
async def execute_cypher_query(
    self,
    query: str,
    parameters: Dict[str, Any] = None,
    limit: int = 100,
    timeout_seconds: int = 10
) -> Dict[str, Any]:
    """
    Execute custom Cypher query with safety checks.

    Args:
        query: Cypher query string (read-only)
        parameters: Query parameters
        limit: Max results (1-1000)
        timeout_seconds: Max execution time (1-30s)

    Returns:
        Dict with results, metadata, and query hash

    Raises:
        HTTPException 400: Query validation failed
        HTTPException 408: Query timeout
    """

    # Validate query syntax and security
    validation_result = query_validator.validate(query)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Query validation failed: {validation_result.error}"
        )

    # Generate query hash for logging
    query_hash = hashlib.sha256(query.encode()).hexdigest()

    # Apply limit if not present
    if "LIMIT" not in query.upper():
        query += f" LIMIT {limit}"

    # Execute with timeout
    start_time = time.time()
    try:
        results = await asyncio.wait_for(
            neo4j_service.execute_query(query, parameters or {}),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"Query exceeded timeout of {timeout_seconds}s"
        )

    query_time_ms = int((time.time() - start_time) * 1000)

    return {
        'results': results,
        'total_results': len(results),
        'query_time_ms': query_time_ms,
        'query_hash': query_hash,
        'limit_applied': limit
    }
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/services/query_service.py`

---

## RabbitMQ Integration

### Consumer 1: Relationships Consumer (relationships_consumer.py)

**Purpose**: Consumes `relationships.extracted` events, ingests entity triplets to Neo4j

**Configuration:**
- **Exchange**: `news.events` (topic)
- **Queue**: `knowledge_graph_relationships`
- **Routing Key**: `relationships.extracted.*`
- **Prefetch**: 10 concurrent messages

**Consumer Setup:**

```python
class RelationshipsConsumer:
    async def connect(self):
        """Connect to RabbitMQ and setup queue."""
        self.connection = await connect_robust(
            settings.rabbitmq_url,
            timeout=30
        )

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        exchange = await self.channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            ExchangeType.TOPIC,
            durable=True
        )

        self.queue = await self.channel.declare_queue(
            settings.RABBITMQ_QUEUE,
            durable=True
        )

        await self.queue.bind(exchange, routing_key=settings.RABBITMQ_ROUTING_KEY)
```

**Event Schema:**

```json
{
  "event_type": "relationships.extracted",
  "timestamp": "2025-12-22T10:30:00Z",
  "payload": {
    "article_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "source_url": "https://techcrunch.com/article",
    "extracted_at": "2025-12-22T10:29:45Z",
    "triplets": [
      {
        "subject": {
          "text": "Elon Musk",
          "type": "PERSON",
          "normalized_text": "elon_musk",
          "wikidata_id": "Q317521"
        },
        "relationship": {
          "type": "WORKS_FOR",
          "confidence": 0.95,
          "evidence": "Elon Musk serves as CEO of Tesla"
        },
        "object": {
          "text": "Tesla",
          "type": "ORGANIZATION",
          "normalized_text": "tesla",
          "wikidata_id": "Q478214"
        }
      }
    ]
  }
}
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/consumers/relationships_consumer.py`

---

### Consumer 2: Market Data Consumer (market_consumer.py) - NEW

**Purpose**: Consumes `finance.market.data.updated` events from FMP Service

**Configuration:**
- **Exchange**: `finance` (topic)
- **Queue**: `knowledge_graph_market_updates`
- **Routing Key**: `finance.market.data.updated`
- **Prefetch**: 10 concurrent messages

**Consumer Setup:**

```python
class MarketDataConsumer:
    """
    RabbitMQ consumer for market data update events.

    Routing: finance.market.data.updated
    Queue: knowledge_graph_market_updates
    Exchange: finance (Topic)
    """

    def __init__(self, market_sync_service: MarketSyncService):
        self.market_sync_service = market_sync_service
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self):
        """Establish connection to RabbitMQ."""
        self.connection = await aio_pika.connect_robust(
            settings.rabbitmq_url,
            timeout=30
        )

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        self.exchange = await self.channel.declare_exchange(
            'finance',
            ExchangeType.TOPIC,
            durable=True
        )

        self.queue = await self.channel.declare_queue(
            'knowledge_graph_market_updates',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'finance.dlx',
                'x-message-ttl': 86400000  # 24 hours
            }
        )

        await self.queue.bind(
            self.exchange,
            routing_key='finance.market.data.updated'
        )
```

**Message Handling:**

```python
async def _handle_message(self, message: AbstractIncomingMessage):
    """Handle incoming market data update event."""
    try:
        body = json.loads(message.body.decode())
        symbol = body.get('symbol')

        # Extract market data from event
        market_data = {
            'symbol': symbol,
            'name': body.get('name'),
            'asset_type': body.get('asset_type'),
            'exchange': body.get('exchange'),
            'currency': body.get('currency'),
            'is_active': body.get('is_active', True)
        }

        # Sync to Neo4j
        result = await self.market_sync_service.sync_single_market(market_data)

        if result:
            logger.info(f"Market {symbol} synced to Neo4j via event")
            await message.ack()
        else:
            logger.error(f"Failed to sync market {symbol}")
            await message.reject(requeue=False)

    except Exception as e:
        logger.error(f"Error processing market data event: {e}", exc_info=True)
        # Retry with exponential backoff (up to 3 attempts)
        await self._retry_message(message, retry_count + 1)
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/consumers/market_consumer.py`

---

### Consumer 3: Finance Intelligence Consumer (finance_intelligence_consumer.py) - NEW

**Purpose**: Consumes ALL `finance.*` events from FMP Service background jobs

**Configuration:**
- **Exchange**: `finance` (topic)
- **Queue**: `knowledge_graph_finance_intelligence`
- **Routing Key**: `finance.#` (wildcard - matches all finance events)
- **Prefetch**: 10 concurrent messages

**Supported Event Types (37 handlers):**

```python
# Company Intelligence Events
'finance.company.profile.updated'       # Company metadata
'finance.company.executives.updated'    # Executive changes
'finance.company.market_cap.updated'    # Market cap updates
'finance.company.employees.updated'     # Employee count

# SEC & Insider Trading
'finance.sec.filing.new'                # SEC filings
'finance.insider.trade.new'             # Insider trading

# Financial Statements
'finance.financials.income.updated'     # Income statements
'finance.financials.balance.updated'    # Balance sheets
'finance.financials.cashflow.updated'   # Cash flow statements
'finance.financials.ratios.updated'     # Financial ratios
'finance.financials.growth.updated'     # Growth metrics

# Key Metrics
'finance.key_metrics.updated'           # TTM key metrics

# Market Indicators
'finance.volatility.updated'            # VIX, VVIX, MOVE
'finance.indices.dxy.updated'           # Dollar Index
'finance.carry_trade.updated'           # AUD/JPY carry trade
'finance.treasury.yields.updated'       # Treasury yields + spreads
'finance.inflation.breakeven.updated'   # Inflation expectations
'finance.real_rates.updated'            # TIPS yields

# Correlations & Regime
'finance.correlation.updated'           # Asset correlations
'finance.regime.changed'                # Market regime state
```

**Consumer Implementation:**

```python
class FinanceIntelligenceConsumer:
    """
    RabbitMQ consumer for all finance.* events from FMP Service.

    Routing: finance.# (wildcard - matches all finance.* events)
    Queue: knowledge_graph_finance_intelligence
    Exchange: finance (Topic)
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

        # Event handling statistics
        self.stats = {
            'total_processed': 0,
            'total_success': 0,
            'total_failed': 0,
            'by_event_type': {}
        }

    async def connect(self):
        """Establish connection to RabbitMQ."""
        self.connection = await aio_pika.connect_robust(
            settings.rabbitmq_url,
            timeout=30
        )

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        self.exchange = await self.channel.declare_exchange(
            'finance',
            ExchangeType.TOPIC,
            durable=True
        )

        self.queue = await self.channel.declare_queue(
            'knowledge_graph_finance_intelligence',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'finance.dlx',
                'x-message-ttl': 86400000  # 24 hours
            }
        )

        # Bind queue to exchange with wildcard routing key
        await self.queue.bind(
            self.exchange,
            routing_key='finance.#'  # Matches ALL finance.* events
        )
```

**Event Handler Routing:**

```python
def _get_handler(self, event_type: str):
    """Get handler function for event type."""
    handler_map = {
        # Company Intelligence
        'finance.company.profile.updated': self._handle_company_update,
        'finance.company.executives.updated': self._handle_executives_update,
        'finance.company.market_cap.updated': self._handle_marketcap_update,

        # Market Indicators
        'finance.volatility.updated': self._handle_volatility,
        'finance.treasury.yields.updated': self._handle_treasury_yields,

        # Regime Detection
        'finance.regime.changed': self._handle_regime_change,

        # ... 30+ more handlers
    }
    return handler_map.get(event_type)
```

**Example Handler: Company Update**

```python
async def _handle_company_update(self, event: Dict[str, Any]):
    """
    Handle finance.company.profile.updated event.

    Creates or updates Company node in Neo4j.
    """
    symbol = event.get('symbol')
    company_data = event.get('company_data', {})

    if not symbol:
        logger.warning("Missing symbol in company update event")
        return

    # Build Cypher query to MERGE Company node
    query = """
    MERGE (c:Company {symbol: $symbol})
    ON CREATE SET c.created_at = datetime()
    SET c.name = $name,
        c.cik = $cik,
        c.sector = $sector,
        c.industry = $industry,
        c.country = $country,
        c.exchange = $exchange,
        c.market_cap = $market_cap,
        c.employees = $employees,
        c.updated_at = datetime()
    RETURN c
    """

    params = {
        'symbol': symbol,
        'name': company_data.get('name'),
        'cik': company_data.get('cik'),
        'sector': company_data.get('sector'),
        'industry': company_data.get('industry'),
        'country': company_data.get('country'),
        'exchange': company_data.get('exchange'),
        'market_cap': company_data.get('market_cap'),
        'employees': company_data.get('employees')
    }

    await neo4j_service.execute_write(query, params)
    logger.info(f"Updated Company node: {symbol}")
```

**Example Handler: Market Indicators**

```python
async def _handle_volatility(self, event: Dict[str, Any]):
    """
    Handle finance.volatility.updated event.

    Creates MarketIndicator nodes for VIX, VVIX, MOVE.
    """
    event_date = event.get('date')
    vix = event.get('vix')
    vvix = event.get('vvix')
    move = event.get('move')

    if not event_date:
        return

    # Create indicator nodes for each value
    indicators = []
    if vix is not None:
        indicators.append(('VIX', vix))
    if vvix is not None:
        indicators.append(('VVIX', vvix))
    if move is not None:
        indicators.append(('MOVE', move))

    for indicator_type, value in indicators:
        query = """
        CREATE (i:MarketIndicator {
            indicator_id: $indicator_id,
            indicator_type: $indicator_type,
            date: date($date),
            value: $value,
            created_at: datetime()
        })
        RETURN i
        """

        params = {
            'indicator_id': f"{indicator_type}_{event_date}",
            'indicator_type': indicator_type,
            'date': event_date,
            'value': value
        }

        await neo4j_service.execute_write(query, params)

    logger.debug(f"Created {len(indicators)} volatility indicators for {event_date}")
```

**Error Handling:**

```python
async def _handle_message(self, message: AbstractIncomingMessage):
    """Handle incoming finance event."""
    event_type = "unknown"
    symbol = "unknown"

    try:
        body = json.loads(message.body.decode())
        event_type = body.get("event_type", "unknown")
        symbol = body.get("symbol", "unknown")

        logger.info(f"📥 Received: {event_type} ({symbol})")

        # Route to appropriate handler
        handler = self._get_handler(event_type)

        if handler:
            await handler(body)
            self.stats['total_success'] += 1
            logger.info(f"✅ Processed: {event_type}")
        else:
            logger.warning(f"⚠️ No handler for event type: {event_type}")

        # Acknowledge message
        await message.ack()

    except NON_RETRIABLE_ERRORS as e:
        # Non-retriable error - send to DLQ
        logger.error(f"✗ Non-retriable error for {event_type}: {e}")
        await message.reject(requeue=False)

    except Exception as e:
        # Unknown error - requeue for retry
        logger.error(f"✗ Unexpected error for {event_type}: {e}")
        await message.reject(requeue=True)
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/consumers/finance_intelligence_consumer.py`

---

## Market Integration Module

### Overview

The Market Integration Module provides seamless integration between the Knowledge Graph Service and FMP Service, enabling:

1. **Market Metadata Sync**: Sync asset metadata (stocks, forex, commodities, crypto) from FMP to Neo4j
2. **Real-Time Market Data**: Track current prices, market cap, volume, day changes
3. **Sector Classification**: Organize markets by industry sectors (GICS classification)
4. **Historical Price Data**: Fetch historical OHLCV data from FMP on demand
5. **Market Statistics**: Aggregate stats across asset types and sectors

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Market Integration Module                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────────────┐     │
│  │  Markets API     │         │  Market Sync Service     │     │
│  │  (routes/        │────────▶│  (fmp_integration/       │     │
│  │   markets.py)    │         │   market_sync_service.py)│     │
│  └──────────────────┘         └──────────────────────────┘     │
│          │                              │                       │
│          │                              │                       │
│          ▼                              ▼                       │
│  ┌──────────────────┐         ┌──────────────────────────┐     │
│  │  FMP Service     │         │  Neo4j Service           │     │
│  │  Client          │         │  (Market/Sector nodes)   │     │
│  │  (HTTP)          │         │                          │     │
│  └──────────────────┘         └──────────────────────────┘     │
│          │                              │                       │
│          └──────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API Endpoints

#### 1. POST /api/v1/graph/markets/sync

Trigger market metadata sync from FMP Service to Neo4j.

**Request:**
```json
{
  "asset_types": ["STOCK", "FOREX"],
  "symbols": null,
  "force_refresh": false
}
```

**Response:**
```json
{
  "sync_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total_assets": 485,
  "synced": 485,
  "failed": 0,
  "duration_seconds": 12.45,
  "errors": [],
  "timestamp": "2025-12-22T16:00:00Z"
}
```

**Permissions Required:** `markets:write`

---

#### 2. GET /api/v1/graph/markets

Query market nodes from Neo4j with filters and pagination.

**Query Parameters:**
- `asset_type`: Filter by asset type (STOCK, FOREX, COMMODITY, CRYPTO)
- `sector`: Filter by sector code (e.g., XLK, XLF)
- `exchange`: Filter by exchange (NASDAQ, NYSE, etc.)
- `is_active`: Filter by active status
- `search`: Text search on name or symbol
- `page`: Page number (0-indexed)
- `page_size`: Items per page (max 1000)

**Response:**
```json
{
  "markets": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "asset_type": "STOCK",
      "exchange": "NASDAQ",
      "currency": "USD",
      "is_active": true,
      "current_price": 178.45,
      "day_change_percent": 1.23,
      "market_cap": 2800000000000,
      "volume": 52340000,
      "created_at": "2024-01-15T10:30:00Z",
      "last_updated": "2025-12-22T16:00:00Z"
    }
  ],
  "total": 485,
  "page": 0,
  "page_size": 50
}
```

**Performance:** < 100ms (p95)

**Permissions Required:** `markets:read`

---

#### 3. GET /api/v1/graph/markets/{symbol}

Get detailed market information with relationships.

**Response:**
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "asset_type": "STOCK",
  "exchange": "NASDAQ",
  "current_price": 178.45,
  "day_change_percent": 1.23,
  "market_cap": 2800000000000,
  "sector_info": {
    "code": "XLK",
    "name": "Information Technology",
    "market_classification": "GICS"
  },
  "organizations": ["Apple Inc."],
  "related_markets": ["QQQ", "SPY", "MSFT", "GOOGL"]
}
```

**Performance:** < 50ms (p95)

**Permissions Required:** `markets:read`

---

#### 4. GET /api/v1/graph/markets/{symbol}/history

Get historical price data for a market symbol.

**Query Parameters:**
- `from_date`: Start date (YYYY-MM-DD)
- `to_date`: End date (YYYY-MM-DD)
- `limit`: Max results (1-1000)

**Response:**
```json
{
  "symbol": "AAPL",
  "history": [
    {
      "date": "2025-12-22",
      "open": 176.80,
      "high": 179.20,
      "low": 176.50,
      "close": 178.45,
      "volume": 52340000,
      "adj_close": 178.45
    }
  ],
  "total_records": 100,
  "data_source": "FMP"
}
```

**Note:** Historical data is fetched from FMP Service, not stored in Neo4j.

**Permissions Required:** `markets:read`

---

#### 5. GET /api/v1/graph/markets/stats

Get aggregated market statistics.

**Response:**
```json
{
  "total_markets": 500,
  "active_markets": 485,
  "markets_by_asset_type": {
    "STOCK": 400,
    "FOREX": 50,
    "CRYPTO": 30,
    "COMMODITY": 20
  },
  "markets_by_sector": {
    "XLK": 80,
    "XLF": 60,
    "XLV": 50,
    "XLE": 40
  },
  "total_market_cap": 50000000000000,
  "avg_day_change": 0.45
}
```

**Permissions Required:** `markets:admin`

---

### FMP Service Client

**Purpose**: HTTP client for FMP Service API

**Key Features:**
- Async HTTP requests using httpx
- Automatic retry logic (3 attempts)
- Error handling (503, 429, 500)
- Rate limit detection

**Implementation:**

```python
class FMPServiceClient:
    """HTTP client for FMP Service."""

    def __init__(self, base_url: str = "http://fmp-service:8109"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def list_assets(
        self,
        asset_types: List[str] = None,
        symbols: List[str] = None,
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        List asset metadata from FMP Service.

        Args:
            asset_types: Filter to specific asset types
            symbols: Filter to specific symbols
            force_refresh: Force fresh data from FMP API

        Returns:
            List of asset metadata dictionaries
        """
        params = {
            'force_refresh': force_refresh
        }
        if asset_types:
            params['asset_types'] = ','.join(asset_types)
        if symbols:
            params['symbols'] = ','.join(symbols)

        response = await self.client.get(
            f"{self.base_url}/api/v1/assets",
            params=params
        )

        if response.status_code == 503:
            raise FMPServiceUnavailableError("FMP Service is unavailable")

        if response.status_code == 429:
            raise FMPServiceError("Rate limit exceeded")

        response.raise_for_status()
        return response.json()['assets']

    async def get_historical_prices(
        self,
        symbol: str,
        from_date: str = None,
        to_date: str = None
    ) -> List[Dict]:
        """
        Get historical price data from FMP Service.

        Args:
            symbol: Market symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of historical price data points
        """
        params = {}
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date

        response = await self.client.get(
            f"{self.base_url}/api/v1/historical/{symbol}",
            params=params
        )

        response.raise_for_status()
        return response.json()['historical']
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/clients/fmp_service_client.py`

---

## Finance Intelligence Consumer

**Comprehensive coverage in [RabbitMQ Integration - Consumer 3](#consumer-3-finance-intelligence-consumer-finance_intelligence_consumerpy---new) section above.**

### Event Handler Summary

| Event Category | Event Count | Node Types Created | Relationship Types |
|----------------|-------------|-------------------|-------------------|
| **Company Intelligence** | 5 events | Company, Executive | WORKS_FOR |
| **SEC & Insider Trading** | 2 events | SECFiling, InsiderTrade | FILED, TRADES_IN, OF_COMPANY |
| **Financial Statements** | 5 events | (notification only) | - |
| **Key Metrics** | 1 event | (notification only) | - |
| **Market Indicators** | 6 events | MarketIndicator | - |
| **Correlations & Regime** | 2 events | MarketRegime | - |

**Total: 21 unique event types, 37 handlers (including backward compatibility)**

### Key Features

1. **Wildcard Routing**: Single consumer subscribes to all `finance.*` events
2. **Event Type Dispatch**: Dynamic handler routing based on event_type field
3. **Idempotent Ingestion**: MERGE operations prevent duplicates
4. **Error Handling**: Distinguishes retriable vs non-retriable errors
5. **Statistics Tracking**: Per-event-type success/failure counters
6. **Logging**: INFO-level production visibility

---

## Symbolic Findings Ingestion

### Overview

The Symbolic Findings Ingestion module enables Knowledge Graph Service to ingest structured intelligence findings from the Intelligence Synthesizer. This creates a multi-domain graph connecting:

- **Entity Relationships** (from content analysis)
- **Market Data** (from FMP Service)
- **Intelligence Findings** (from Intelligence Synthesizer)

### Endpoint

#### POST /api/v1/graph/findings

Ingest symbolic findings into knowledge graph.

**Request:**
```json
{
  "article_id": "123e4567-e89b-12d3-a456-426614174000",
  "findings": [
    {
      "finding_id": "F1",
      "category": "event_type",
      "confidence": 0.95,
      "supporting_agents": ["CONFLICT_EVENT_ANALYST"],
      "priority": "critical",
      "symbolic": {
        "event_type": "MISSILE_STRIKE",
        "target": "INFRASTRUCTURE",
        "severity": "CRITICAL",
        "actors": {
          "RU": "aggressor",
          "UA": "defender"
        },
        "location": "UA_KHARKIV",
        "casualties": 15
      }
    }
  ]
}
```

**Response:**
```json
{
  "article_id": "123e4567-e89b-12d3-a456-426614174000",
  "findings_processed": 1,
  "nodes_created": [
    {
      "node_id": "12345",
      "node_type": "LOCATION",
      "name": "RU"
    },
    {
      "node_id": "12346",
      "node_type": "LOCATION",
      "name": "UA"
    }
  ],
  "relationships_created": [
    {
      "relationship_id": "67890",
      "relationship_type": "ATTACKS",
      "source_node": "RU",
      "target_node": "UA",
      "confidence": 0.95
    }
  ],
  "processing_time_ms": 125,
  "errors": []
}
```

### Supported Finding Categories

| Category | Symbolic Fields | Node Types | Relationship Types |
|----------|----------------|------------|-------------------|
| **event_type** | event_type, target, severity, casualties, location, actors | LOCATION | ATTACKS |
| **ihl_concern** | ihl_type, violation_level, affected_population, actors | LOCATION, IHL_VIOLATION | VIOLATES_IHL |
| **regional_impact** | impact_type, severity, spillover_risk, affected_countries | LOCATION | AFFECTS_REGIONALLY |
| **financial_impact** | markets, volatility, duration | FINANCIAL_EVENT, MARKET | IMPACTS_MARKET |
| **political_development** | policy_area, direction, alignment, actors | LOCATION | INFLUENCES_POLICY |
| **security_threat** | threat_type, severity, imminence, source, target | LOCATION | THREATENS |
| **humanitarian_crisis** | crisis_type, severity, affected_population, location | HUMANITARIAN_CRISIS, LOCATION | OCCURS_AT |

### Example Handler: Event Type

```python
async def _ingest_event_type(
    finding: KeyFinding,
    article_id: str,
    nodes_created: List[GraphNodeCreated],
    relationships_created: List[GraphRelationshipCreated]
):
    """Ingest event_type symbolic finding into Neo4j."""
    symbolic: EventTypeSymbolic = finding.symbolic

    # Find aggressor and affected actors
    aggressors = [code for code, role in symbolic.actors.items() if role == ActorRole.AGGRESSOR]
    targets = [code for code, role in symbolic.actors.items() if role in [ActorRole.DEFENDER, ActorRole.AFFECTED]]

    # Create ATTACKS relationships: Aggressor -> Target
    for aggressor in aggressors:
        for target in targets:
            cypher = """
            MERGE (source:LOCATION {name: $aggressor, iso_code: $aggressor})
            MERGE (target:LOCATION {name: $target, iso_code: $target})
            CREATE (source)-[r:ATTACKS {
                event_type: $event_type,
                target_type: $target_type,
                severity: $severity,
                casualties: $casualties,
                location: $location,
                article_id: $article_id,
                confidence: $confidence,
                created_at: datetime()
            }]->(target)
            RETURN id(source) AS source_id, id(target) AS target_id, id(r) AS rel_id
            """

            result = await neo4j_service.execute_query(cypher, parameters={
                "aggressor": aggressor,
                "target": target,
                "event_type": symbolic.event_type.value,
                "target_type": symbolic.target.value,
                "severity": symbolic.severity.value,
                "casualties": symbolic.casualties,
                "location": symbolic.location,
                "article_id": article_id,
                "confidence": finding.confidence
            })
```

**Location**: `/home/cytrex/news-microservices/services/knowledge-graph-service/app/api/routes/findings.py`

---

## API Architecture

### Complete Endpoint Inventory (37 endpoints)

| Route Module | Endpoints | Purpose |
|-------------|-----------|---------|
| **health.py** | 6 endpoints | Kubernetes health checks |
| **graph.py** | 2 endpoints | Entity connections, graph stats |
| **analytics.py** | 7 endpoints | Entity/market analytics, growth trends |
| **enrichment.py** | 4 endpoints | Manual enrichment workflow |
| **markets.py** | 5 endpoints | Market data query & sync (NEW) |
| **pathfinding.py** | 1 endpoint | Entity pathfinding (NEW) |
| **admin_query.py** | 4 endpoints | Custom Cypher execution (NEW) |
| **quality.py** | 2 endpoints | Disambiguation, integrity checks (NEW) |
| **findings.py** | 1 endpoint | Symbolic findings ingestion (NEW) |
| **articles.py** | 2 endpoints | Article query (placeholder) |
| **search.py** | 1 endpoint | Entity text search |
| **history.py** | 2 endpoints | Enrichment history |

### Health Endpoints (health.py)

```
GET /health                    - Comprehensive health check
GET /health/live               - Kubernetes liveness probe
GET /health/ready              - Kubernetes readiness probe
GET /health/neo4j              - Neo4j-specific health check
GET /health/rabbitmq           - RabbitMQ-specific health check
GET /health/startup            - Startup readiness check
```

### Entity Graph Endpoints (graph.py)

```
GET /api/v1/graph/entity/{entity_name}/connections  - Entity connections
GET /api/v1/graph/stats                             - Graph statistics
```

### Analytics Endpoints (analytics.py)

```
GET /api/v1/graph/analytics/top-entities              - Top connected entities
GET /api/v1/graph/analytics/growth-history            - Entity growth over time
GET /api/v1/graph/analytics/relationship-stats        - Relationship distribution
GET /api/v1/graph/analytics/cross-article-coverage    - Cross-article analytics (placeholder)
GET /api/v1/graph/analytics/not-applicable-trends     - NOT_APPLICABLE trends
GET /api/v1/graph/analytics/relationship-quality-trends  - Quality metrics
GET /api/v1/graph/stats/detailed                      - Detailed graph statistics
```

### Enrichment Endpoints (enrichment.py)

```
POST /api/v1/enrichment/analyze        - Analyze NOT_APPLICABLE candidates
POST /api/v1/enrichment/execute-tool   - Execute enrichment tool
POST /api/v1/enrichment/apply          - Apply enrichment to relationships
GET  /api/v1/enrichment/stats          - Enrichment statistics
```

### Market Endpoints (markets.py) - NEW

```
POST /api/v1/graph/markets/sync                  - Trigger market sync
GET  /api/v1/graph/markets                       - List markets with filters
GET  /api/v1/graph/markets/{symbol}              - Get market details
GET  /api/v1/graph/markets/{symbol}/history      - Get historical prices
GET  /api/v1/graph/markets/stats                 - Market statistics
```

### Pathfinding Endpoints (pathfinding.py) - NEW

```
GET /api/v1/graph/path/{entity1}/{entity2}  - Find paths between entities
```

### Admin Query Endpoints (admin_query.py) - NEW

```
POST /api/v1/graph/admin/query/cypher    - Execute custom Cypher query
POST /api/v1/graph/admin/query/validate  - Validate Cypher query
GET  /api/v1/graph/admin/query/clauses   - Get allowed/forbidden clauses
GET  /api/v1/graph/admin/query/examples  - Get example queries
```

### Quality Check Endpoints (quality.py) - NEW

```
GET /api/v1/graph/quality/disambiguation  - Analyze entity disambiguation
GET /api/v1/graph/quality/integrity       - Perform integrity checks
```

### Findings Endpoints (findings.py) - NEW

```
POST /api/v1/graph/findings  - Ingest symbolic findings
```

### Search Endpoints (search.py)

```
GET /api/v1/graph/search  - Entity text search
```

### Article Endpoints (articles.py)

```
GET /api/v1/graph/articles/{article_id}       - Get article graph
GET /api/v1/graph/articles/{article_id}/info  - Get article metadata
```

### History Endpoints (history.py)

```
GET /api/v1/graph/history/enrichments  - Enrichment history
GET /api/v1/graph/history/stats        - History statistics
```

### API Versioning

**Base Path**: `/api/v1/*`

All endpoints are versioned under `/api/v1/` prefix to support future API changes without breaking existing clients.

### Authentication

**JWT Token Validation** (optional, configured per deployment):

```python
from app.api.dependencies import get_current_user_id

@router.get("/api/v1/graph/entity/{entity_name}/connections")
async def get_entity_connections(
    entity_name: str,
    user_id: str = Depends(get_current_user_id)  # JWT validation
):
    # Only authenticated users can query graph
    pass
```

### Rate Limiting

**Admin endpoints protected with SlowAPI rate limiter:**

```python
from app.core.rate_limiting import limiter, RateLimits

@router.post("/api/v1/graph/admin/query/cypher")
@limiter.limit(RateLimits.ADMIN)  # 10 req/minute
async def execute_custom_cypher_query(request: Request, query_request: CypherQueryRequest):
    pass
```

**Rate Limits:**
- Admin endpoints: 10 req/minute
- General endpoints: No limit (production: add per-user limits)

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Allowed Origins:**
- `http://localhost:3000` - Local development
- `http://localhost:3000` - LAN access for remote development

### OpenAPI Documentation

**Auto-Generated API Docs:**
- **Swagger UI**: `http://localhost:8111/docs`
- **ReDoc**: `http://localhost:8111/redoc`
- **OpenAPI JSON**: `http://localhost:8111/openapi.json`

---

## Finance & Market Integration

The knowledge-graph-service provides comprehensive financial market integration through:
1. **Market Data Sync** - Real-time market metadata (stocks, forex, commodities, crypto)
2. **Finance Intelligence Events** - Company data, executives, SEC filings, market indicators
3. **Market Analytics** - Sector analysis, market statistics

### Market Node Types

#### `:MARKET` Node
Represents tradable assets across multiple asset classes.

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| symbol | String | Ticker symbol (Primary Key) |
| name | String | Full market name |
| asset_type | Enum | STOCK, FOREX, COMMODITY, CRYPTO |
| sector | String | Sector code (e.g., "TECH") |
| exchange | String | Trading exchange |
| currency | String | Price denomination |
| is_active | Boolean | Trading status |
| current_price | Float | Current price |
| market_cap | Integer | Market capitalization |

#### `:SECTOR` Node
Industry classification for market grouping.

**Standard Sectors:** TECH, FINANCE, HEALTHCARE, ENERGY, CONSUMER_DISC, CONSUMER_STAPLES, INDUSTRIALS, MATERIALS, UTILITIES, REAL_ESTATE, TELECOM, FOREX, COMMODITY, CRYPTO

#### `:MarketIndicator` Node
Time-series market indicators and macro signals.

**Indicator Types:**
- **Volatility:** VIX, VVIX, MOVE
- **Currency:** DXY, AUDJPY
- **Rates:** TREASURY_3M/2Y/10Y, SPREAD_10Y2Y/10Y3M
- **Inflation:** INFLATION_5Y/10Y, TIPS_10Y

#### `:MarketRegime` Node
Market regime classification (risk-on/risk-off states).

**Properties:** regime_type, regime_score, vix_signal, yield_curve_signal, dxy_signal

#### Event Nodes
- `:Event:MergerAcquisition` - M&A transactions
- `:Event:SECFiling` - SEC regulatory filings
- `:Event:InsiderTrade` - Insider trading transactions

### Market Endpoints

#### `POST /api/v1/graph/markets/sync`
Sync markets from FMP Service.

**Request:**
```json
{"asset_types": ["STOCK", "FOREX"], "force_refresh": false}
```

**Response (200 OK):**
```json
{
  "sync_id": "sync_20241222_143052",
  "status": "completed",
  "total_assets": 40,
  "synced": 40,
  "nodes_created": 35,
  "nodes_updated": 5
}
```

---

#### `GET /api/v1/graph/markets`
Query markets with filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| asset_type | string | STOCK, FOREX, COMMODITY, CRYPTO |
| sector | string | Filter by sector code |
| exchange | string | Filter by exchange |
| is_active | bool | Filter active/inactive |
| page, page_size | int | Pagination |

---

#### `GET /api/v1/graph/markets/{symbol}`
Get market details with sector info and related markets.

---

#### `GET /api/v1/graph/markets/{symbol}/history`
Get historical prices (from FMP Service).

---

#### `GET /api/v1/graph/markets/stats`
Get market statistics (total markets, by asset type, by sector).

### Finance RabbitMQ Consumers

#### Market Data Consumer
- **Queue:** `knowledge_graph_market_updates`
- **Routing Key:** `finance.market.data.updated`
- **Purpose:** Auto-sync market data on FMP updates

#### Finance Intelligence Consumer
- **Queue:** `knowledge_graph_finance_intelligence`
- **Routing Key:** `finance.#` (wildcard)
- **Supported Events (37 types):**
  - Company: profile, executives, market_cap, employees, M&A
  - SEC: filings, insider trades
  - Financials: income, balance, cashflow, ratios
  - Market: volatility, treasury yields, inflation, regime changes

### Market Relationships

| Relationship | Pattern | Description |
|--------------|---------|-------------|
| BELONGS_TO_SECTOR | (MARKET)->(SECTOR) | Industry classification |
| ACQUIRED | (Company)->(Company) | M&A relationships |
| FILED | (Company)->(SECFiling) | SEC filing links |
| TRADES_IN | (Executive)->(InsiderTrade) | Insider trading |

---

## Configuration

### Environment Variables

```python
# Service Configuration
SERVICE_NAME: str = "knowledge-graph-service"
SERVICE_PORT: int = 8111
LOG_LEVEL: str = "INFO"

# Neo4j Configuration
NEO4J_URI: str = "bolt://neo4j:7687"
NEO4J_USER: str = "neo4j"
NEO4J_PASSWORD: str = "neo4j_password_2024"
NEO4J_DATABASE: str = "neo4j"
NEO4J_MAX_POOL_SIZE: int = 50
NEO4J_CONNECTION_TIMEOUT: int = 30

# RabbitMQ Configuration (Entity Relationships)
RABBITMQ_HOST: str = "rabbitmq"
RABBITMQ_PORT: int = 5672
RABBITMQ_USER: str = "guest"
RABBITMQ_PASSWORD: str = "guest"
RABBITMQ_EXCHANGE: str = "news.events"
RABBITMQ_QUEUE: str = "knowledge_graph_relationships"
RABBITMQ_ROUTING_KEY: str = "relationships.extracted.*"

# API Configuration
CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:3000"]'

# External Services
SCRAPING_SERVICE_URL: str = "http://news-scraping-service:8009"
FMP_SERVICE_URL: str = "http://fmp-service:8109"

# Query Limits
MAX_QUERY_TIMEOUT_SECONDS: int = 30
DEFAULT_RESULT_LIMIT: int = 100
MAX_RESULT_LIMIT: int = 1000

# Database (Event Log)
DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/news_db"
```

### .env.example

```bash
# Service Configuration
SERVICE_NAME=knowledge-graph-service
SERVICE_PORT=8111
LOG_LEVEL=INFO

# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password_2024
NEO4J_DATABASE=neo4j
NEO4J_MAX_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=news.events
RABBITMQ_QUEUE=knowledge_graph_relationships
RABBITMQ_ROUTING_KEY=relationships.extracted.*

# API Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3000"]

# External Services
SCRAPING_SERVICE_URL=http://news-scraping-service:8009
FMP_SERVICE_URL=http://fmp-service:8109

# Query Limits
MAX_QUERY_TIMEOUT_SECONDS=30
DEFAULT_RESULT_LIMIT=100
MAX_RESULT_LIMIT=1000

# Database (Event Log)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/news_db
```

---

## Deployment

### Docker Compose Integration

**Service Definition:**

```yaml
services:
  knowledge-graph-service:
    build:
      context: .
      dockerfile: services/knowledge-graph-service/Dockerfile.dev
    container_name: news-knowledge-graph-service
    ports:
      - "8111:8111"
    environment:
      SERVICE_PORT: 8111
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: neo4j_password_2024
      RABBITMQ_HOST: rabbitmq
      FMP_SERVICE_URL: http://fmp-service:8109
      CORS_ORIGINS: '["http://localhost:3000", "http://localhost:3000"]'
    volumes:
      - ./services/knowledge-graph-service/app:/app/app:ro
    depends_on:
      neo4j:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      fmp-service:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8111/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - news-network
```

### Startup Commands

```bash
# Start entire stack
cd /home/cytrex/news-microservices
docker compose up -d

# Start only Knowledge Graph + dependencies
docker compose up -d neo4j rabbitmq fmp-service knowledge-graph-service

# Rebuild after code changes
docker compose up -d --build knowledge-graph-service

# View logs
docker compose logs -f knowledge-graph-service
```

### Neo4j Browser Access

**URL**: http://localhost:7474
**Username**: neo4j
**Password**: neo4j_password_2024

---

## Monitoring & Metrics

### Prometheus Metrics

**Endpoint**: `http://localhost:8111/metrics`

#### Ingestion Metrics

```
kg_ingestion_triplets_total{status="success|failed"}
kg_ingestion_duration_seconds
kg_ingestion_batch_size
kg_nodes_created_total{entity_type}
kg_relationships_created_total{relationship_type}
```

#### Consumer Metrics

```
kg_events_consumed_total{status="success|failed"}
kg_consumer_processing_duration
kg_consumer_triplets_per_event
```

#### Query Metrics

```
kg_queries_total{endpoint, status="success|error"}
kg_query_duration_seconds{endpoint}
kg_query_results_size{endpoint}
```

#### Health Metrics

```
kg_health_status{component="neo4j|rabbitmq|consumer|overall"}
kg_uptime_seconds
```

### Logging

**Structured Logging** (using Python logging):

```python
logger.info(
    f"Ingested {summary['triplets_processed']}/{len(triplets)} triplets "
    f"in {duration:.2f}s. Nodes: +{summary['nodes_created']}, "
    f"Rels: +{summary['relationships_created']}"
)
```

**Log Levels:**
- **DEBUG**: Detailed query execution, triplet details
- **INFO**: Ingestion summaries, health checks, startup/shutdown
- **WARNING**: Retry attempts, degraded performance
- **ERROR**: Failed queries, consumer failures, connectivity issues

---

## Manual Enrichment Workflow

**Comprehensive documentation in original section preserved above.**

### Quick Reference

1. **Analyze Candidates**: `GET /api/v1/enrichment/analyze?limit=100&min_occurrence=5`
2. **Execute Tool**: `POST /api/v1/enrichment/execute-tool` (Wikipedia, Perplexity)
3. **Apply Enrichment**: `POST /api/v1/enrichment/apply` (Update relationships)

**Goal**: Replace `NOT_APPLICABLE` relationships with specific types using external tools.

---

## Performance Characteristics

### Ingestion Performance

**Single Triplet**: 15-50ms (avg), 80ms (p95), 150ms (p99)
**Batch (10 triplets)**: 200-500ms (avg), 800ms (p95), 1.5s (p99)
**Event Processing**: 200-600ms (end-to-end)

### Query Performance

**Entity Connections (1-hop)**: 15-30ms (avg), 50ms (p95), 100ms (p99)
**Analytics Queries**: 30-100ms
**Pathfinding (2-hop)**: 100-200ms
**Pathfinding (3-hop)**: 300-500ms

### Throughput Targets

**Ingestion**: >100 triplets/second (target), ~50-80 triplets/second (current)
**Query API**: >1000 QPS (target), ~200-400 QPS (current)

### Resource Usage

**CPU**: 1-2% (idle), 5-10% (light), 30-50% (heavy)
**Memory**: 150-200MB (base), 250-350MB (10k entities), 500-800MB (100k entities)
**Neo4j**: 100MB (10k entities), 1GB (100k entities), 10GB (1M entities)

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Symptom**: `✗ Failed to connect to Neo4j: ...`

**Solutions:**
1. Ensure Neo4j container is running and healthy
2. Verify credentials match in .env and docker-compose.yml
3. Check Neo4j logs for startup errors
4. Wait for Neo4j initialization (30-60s)

---

#### 2. Consumer Not Processing Messages

**Symptom**: `✓ RabbitMQ consumer started` but no ingestion logs

**Diagnosis:**
```bash
docker exec -it rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged
```

**Solutions:**
1. Verify queue is bound to correct exchange
2. Check content-analysis-service is publishing events
3. Check for consumer errors in logs

---

#### 3. Slow Query Performance

**Symptom**: Query execution > 1 second

**Diagnosis:**
```cypher
EXPLAIN MATCH (e:Entity {name: "Tesla"}) RETURN e
```

**Solutions:**
1. Ensure indexes are created
2. Use LIMIT clauses
3. Avoid unbounded path queries: `MATCH (a)-[*]->(b)`
4. Use specific relationship types

---

#### 4. Market Sync Fails

**Symptom**: `✗ FMP Service unavailable`

**Diagnosis:**
```bash
curl http://localhost:8109/health
```

**Solutions:**
1. Verify FMP Service is running
2. Check FMP Service logs
3. Verify network connectivity between containers

---

#### 5. Finance Intelligence Consumer Not Processing

**Symptom**: No finance events being processed

**Diagnosis:**
```bash
docker logs news-knowledge-graph-service | grep "finance.intelligence"
```

**Solutions:**
1. Verify FMP Service is publishing finance.* events
2. Check consumer is bound to finance.# wildcard
3. Check for handler errors in logs

---

## Future Enhancements

### Phase 1: Data Model Completion

**1. Article Node Implementation**

Add `:Article` nodes to enable cross-article analytics:

```cypher
(:Article {
    id: String,
    url: String,
    title: String,
    published_at: DateTime
})

(:Entity)-[:EXTRACTED_FROM]->(:Article)
```

**Prerequisites**: Feed service publishes `article.published` events

**Estimated Effort**: 2-3 days

---

### Phase 2: Query Enhancements

**2. Graph Algorithms (Neo4j GDS)**

Implement:
- **PageRank**: Find most influential entities
- **Community Detection**: Find clusters
- **Similarity**: Recommend similar entities
- **Betweenness Centrality**: Find bridge entities

**Estimated Effort**: 3-4 days

---

**3. Temporal Queries**

Track relationship evolution over time:

```
GET /api/v1/graph/analytics/temporal?entity=Tesla&relationship_type=WORKS_FOR&range=7d
```

**Estimated Effort**: 2 days

---

### Phase 3: Quality Improvements

**4. Automated Enrichment**

Nightly job to auto-enrich high-occurrence NOT_APPLICABLE relationships using Wikipedia.

**Estimated Effort**: 3-4 days

---

**5. Entity Resolution & Deduplication**

Merge duplicate entities using fuzzy matching and embeddings.

**Estimated Effort**: 1 week

---

### Phase 4: Market Integration Enhancements

**6. Real-Time Price Updates**

Subscribe to FMP WebSocket for real-time price updates.

**Estimated Effort**: 3-4 days

---

**7. Price History Storage**

Store historical OHLCV data in Neo4j for performance.

**Estimated Effort**: 1 week

---

## References

### Related Documentation

- **API Documentation**: `docs/api/knowledge-graph-service-api.md`
- **Entity Canonicalization Service**: `docs/services/entity-canonicalization-service.md`
- **Content Analysis Service**: `docs/services/content-analysis-service.md`
- **FMP Service**: `docs/services/fmp-service.md`
- **Intelligence Synthesizer**: `docs/services/intelligence-synthesizer.md`
- **Frontend Knowledge Graph Admin**: `docs/frontend/knowledge-graph-admin-dashboard.md`

### External Resources

- **Neo4j Cypher Manual**: https://neo4j.com/docs/cypher-manual/current/
- **Neo4j Python Driver**: https://neo4j.com/docs/api/python-driver/current/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **RabbitMQ aio-pika**: https://aio-pika.readthedocs.io/

---

**Document Status**: ✅ Complete
**Version**: 2.0.0
**Last Review**: 2025-12-22
**Next Review**: 2026-01-22 (or after significant architecture changes)
**Recent Changes**:
- Added Market Integration Module (5 endpoints)
- Added Finance Intelligence Consumer (37 event handlers)
- Added Symbolic Findings Ingestion (7 categories)
- Added Pathfinding Service (1 endpoint)
- Added Admin Query Service (4 endpoints)
- Added Quality Check Endpoints (2 endpoints)
- Documented 6 new Neo4j node labels
- Documented 3 RabbitMQ consumers
- Updated file structure with 62 Python files
- Comprehensive API inventory (37 endpoints)

# News Microservices Architecture

**Last Updated:** 2026-02-24
**Version:** 2.1
**Status:** Production (News Intelligence System - Phase 2 Complete)

> **📚 Quick Links:**
> - [README](README.md) - Project overview and getting started
> - [API Documentation](docs/api/API_LANDSCAPE.md) - Complete API reference
> - [Service Documentation](docs/services/) - Per-service guides
> - [Deployment Guide](docs/guides/DEPLOYMENT_GUIDE.md) - Production deployment

---

## 🎯 Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         News Microservices Platform                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Frontend (React)          API Gateway Layer        Event Bus            │
│  ┌──────────┐              ┌────────────┐          ┌──────────┐         │
│  │ Main UI  │◄────────────►│ 20+ FastAPI│◄────────►│ RabbitMQ │         │
│  │ (3000)   │              │  Services  │          │ (15672)  │         │
│  │ Analytics│              │ (8100-8123)│          └──────────┘         │
│  │ (5173)   │              └────────────┘                │               │
│  └──────────┘                     │                      │               │
│                                    ▼                      ▼               │
│                         ┌──────────────────┐   ┌──────────────┐         │
│                         │   PostgreSQL     │   │    Neo4j     │         │
│                         │   (80+ tables)   │   │   (Graph)    │         │
│                         │   Shared Schema  │   │  (7474)      │         │
│                         └──────────────────┘   └──────────────┘         │
│                                                                           │
│  Orchestration: n8n (5678) | Cache: Redis (6379)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Stats:**
- **57 Containers** (default profile: 36 services/workers + 8 MCP servers + 8 infrastructure + 2 frontends + 3 V3 consumers; +5 via optional profiles)
- **145,671 Articles** processed and analyzed
- **137,967 Analyzed Articles** (95% coverage)
- **21,619 Intelligence Clusters** (active story groupings)
- **61 RSS Feeds** configured
- **~250 API Endpoints** (OpenAPI documented)
- **12 RabbitMQ Exchanges** (event-driven architecture)
- **80+ Database Tables** (Shared public schema + intelligence schema)

---

## 📋 Table of Contents

1. [News Intelligence System](#1-news-intelligence-system) ⭐ NEW
2. [System Components](#2-system-components)
3. [Service Landscape](#3-service-landscape)
4. [Event-Driven Architecture](#4-event-driven-architecture)
5. [Database Architecture](#5-database-architecture)
6. [Critical Paths](#6-critical-paths)
7. [Integration Points](#7-integration-points)
8. [Deployment Topology](#8-deployment-topology)
9. [Known Issues](#9-known-issues)

---

## 1. News Intelligence System

> **🎯 Major Feature:** Completed January 2026 across 3 phases (Phase 0-2)

### Overview

The News Intelligence System transforms raw news articles into actionable intelligence through automated clustering, deduplication, entity resolution, and time-decay ranking.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      News Intelligence Pipeline                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RSS Feeds ──► Feed Service ──► Content Analysis ──► Intelligence Layer     │
│     (61)         (8101)           (8117)              │                     │
│                     │                │                 │                     │
│                     ▼                ▼                 ▼                     │
│              ┌──────────────────────────────────────────────┐               │
│              │           Event Bus (RabbitMQ)               │               │
│              └──────────────────────────────────────────────┘               │
│                     │                │                 │                     │
│         ┌──────────┼────────────────┼─────────────────┼──────────┐         │
│         ▼          ▼                ▼                 ▼          ▼         │
│    ┌─────────┐ ┌─────────┐   ┌───────────┐   ┌─────────┐  ┌──────────┐    │
│    │Clustering│ │Duplicate│   │  Entity   │   │ SITREP  │  │ Time-    │    │
│    │ Service │ │Detection│   │Resolution │   │ Service │  │ Decay    │    │
│    │ (8122)  │ │         │   │  (8112)   │   │ (8123)  │  │ Ranking  │    │
│    └─────────┘ └─────────┘   └───────────┘   └─────────┘  └──────────┘    │
│         │                           │              │             │          │
│         ▼                           ▼              ▼             ▼          │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │                    Intelligence Dashboard                         │    │
│    │                    http://localhost:3000/intelligence             │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase Summary

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| **0** | Foundation | ✅ COMPLETE | Database schema, shared library, event standards |
| **1** | Core Intelligence | ✅ COMPLETE | Clustering, deduplication, burst detection, entity resolution, SITREP |
| **2** | Advanced Features | ✅ COMPLETE | Time-decay ranking, HITL review workflow, semantic search |
| **3** | Integration & Polish | 🔜 PLANNED | Frontend integration, dashboards, documentation |

### New Services (Phase 0-2)

| Service | Port | Purpose | Phase |
|---------|------|---------|-------|
| **clustering-service** | 8122 | Article clustering, burst detection | Phase 1 |
| **sitrep-service** | 8123 | Intelligence briefing generation | Phase 1 |
| **intelligence-service** | 8118 | Risk scoring, overview, subcategories | Existing |

### Key Features

#### 1. Article Clustering (Phase 1)
- **Algorithm:** Single-Pass Clustering with cosine similarity (threshold: 0.75)
- **Centroid Update:** Welford's incremental algorithm
- **Burst Detection:** Time-windowed velocity tracking with severity levels
- **Events:** `cluster.created`, `cluster.updated`, `cluster.burst_detected`

#### 2. Deduplication Pipeline (Phase 1)
- **Method:** SimHash fingerprinting (64-bit)
- **Exact Duplicates:** Hamming distance ≤ 3 → rejected
- **Near-Duplicates:** Hamming distance 4-7 → flagged for HITL review
- **Performance:** < 10ms per article check

#### 3. Time-Decay Ranking (Phase 2)
- **Library:** `news-intelligence-common.TimeDecayScorer`
- **Decay Rates:** Category-specific (breaking news decays faster than analysis)
- **Batch Update:** Celery task every 30 minutes
- **API:** `GET /api/v1/feeds/items?sort_by=relevance_score`

#### 4. HITL Review Workflow (Phase 2)
- **Risk Levels:** Low (< 0.3 auto-approve), Medium (0.3-0.7 queue), High (> 0.7 alert)
- **Queue:** `publication_review_queue` table
- **API:** `/api/v1/reviews/*` endpoints
- **Integration:** n8n webhooks for alerts

#### 5. SITREP Generation (Phase 1)
- **Trigger:** Scheduled (daily) or manual via API
- **LLM:** OpenAI GPT-4o-mini for briefing generation
- **Content:** Top stories by time-decay score, key entities, sentiment
- **API:** `GET /api/v1/sitrep/latest`, `POST /api/v1/sitrep/generate`

### Shared Library

**Package:** `libs/news-intelligence-common/`

| Component | Purpose |
|-----------|---------|
| `SimHasher` | Fingerprinting, Hamming distance calculation |
| `TimeDecayScorer` | Exponential decay with category-specific rates |
| `EventEnvelope` | Standardized message format with validation |
| `EventValidator` | JSON schema validation for all event types |

### Database Schema Extensions (Phase 0)

```sql
-- Key new tables (V001 migration)
CREATE TABLE article_clusters (...)       -- Cluster metadata
CREATE TABLE cluster_memberships (...)    -- Article-cluster mapping
CREATE TABLE article_versions (...)       -- Version history
CREATE TABLE publication_review_queue (...) -- HITL workflow
CREATE TABLE sitrep_reports (...)         -- Generated briefings
CREATE TABLE duplicate_candidates (...)   -- Near-duplicate tracking
CREATE TABLE burst_alerts (...)           -- Breaking news alerts
```

### Event Flows

```
article.created → clustering-service → cluster.created/updated
                → duplicate-detector → duplicate.detected (if match)

analysis.v3.completed → clustering-service → cluster.burst_detected (if velocity high)
                      → sitrep-service → story aggregation

cluster.* events → sitrep-service → sitrep.generated
                 → intelligence-service → overview update
```

### API Endpoints Summary

| Service | Endpoint | Purpose |
|---------|----------|---------|
| **clustering** | `GET /api/v1/clusters` | List all clusters |
| **clustering** | `GET /api/v1/clusters/{id}` | Cluster details |
| **clustering** | `GET /api/v1/bursts` | Burst alerts |
| **sitrep** | `GET /api/v1/sitrep/latest` | Latest briefing |
| **sitrep** | `POST /api/v1/sitrep/generate` | Trigger generation |
| **intelligence** | `GET /api/v1/intelligence/overview` | Dashboard data |
| **intelligence** | `GET /api/v1/intelligence/clusters` | Cluster list |
| **intelligence** | `GET /api/v1/intelligence/events/latest` | Recent events |
| **feed** | `GET /api/v1/feeds/items?sort_by=relevance_score` | Time-decay sorted |
| **feed** | `GET /api/v1/reviews/pending` | HITL queue |
| **feed** | `POST /api/v1/reviews/{id}/decision` | Review decision |

### Metrics

| Metric | Current Value |
|--------|---------------|
| Total Articles | 145,671 |
| Analyzed Articles | 137,967 (95%) |
| Intelligence Clusters | 21,619 |
| Narrative Clusters | 1,432,463 |
| Batch Clusters | 112,019 |
| RSS Feeds | 61 |

### Documentation

- **Master Roadmap:** [docs/plans/2026-01-04-news-intelligence-master-roadmap.md](docs/plans/2026-01-04-news-intelligence-master-roadmap.md)
- **Foundation Design:** [docs/plans/2026-01-04-news-intelligence-foundation-design.md](docs/plans/2026-01-04-news-intelligence-foundation-design.md)
- **Phase 2 Plan:** [docs/plans/2026-01-22-phase-2-advanced-features.md](docs/plans/2026-01-22-phase-2-advanced-features.md)
- **Clustering Service:** [services/clustering-service/README.md](services/clustering-service/README.md)
- **SITREP Service:** [services/sitrep-service/README.md](services/sitrep-service/README.md)

---

## 2. System Components

### Core Services (7 active + 2 archived)

| Service | Port | LOC | Purpose | Status |
|---------|------|-----|---------|--------|
| **auth-service** | 8100 | 3.1k | JWT authentication, RBAC | ✅ Healthy |
| **feed-service** | 8101 | 9.7k | RSS/Atom feed management | ✅ Healthy |
| **content-analysis-v3** | 8117 | - | AI content analysis (3 consumers) | ✅ Healthy |
| **research-service** | 8103 | 8.5k | Perplexity API integration | 🔴 Slow (1.2s) |
| **search-service** | 8106 | 4.9k | Full-text search (PostgreSQL) | ⚠️ No health endpoint |
| **analytics-service** | 8107 | 3.9k | Usage metrics, dashboards | ✅ Healthy |
| **scheduler-service** | 8108 | 2.9k | Celery beat scheduling | ✅ Healthy |
| **content-analysis-v2** | ~~8114~~ | 237k | ~~AI-powered content analysis~~ | 🗄️ ARCHIVED (2025-11-24) → replaced by V3 |
| **notification-service** | ~~8105~~ | - | ~~Email/webhook notifications~~ | 🗄️ ARCHIVED (2026-01-03) → n8n workflows |

### Intelligence & AI Services (5 active + 1 archived)

| Service | Port | LOC | Purpose | Status |
|---------|------|-----|---------|--------|
| **knowledge-graph-service** | 8111 | 9.3k | Neo4j relationship extraction | ✅ Healthy |
| **entity-canonicalization** | 8112 | 8.2k | Entity deduplication | ✅ Stable (1.2 GB, resolved) |
| **intelligence-service** | 8118 | - | Risk scoring, intelligence overview | ✅ Healthy |
| **narrative-service** | 8119 | - | Narrative framing, bias analysis | ✅ Healthy |
| **narrative-intelligence-gateway** | 8114 | - | Gateway for narrative intelligence | ✅ Healthy |
| **llm-orchestrator** | 8109 | 4.7k | Multi-LLM orchestration | ⚠️ Optional (profile: dia) |

> ⚠️ **Archived:** osint-service (8104) was archived on 2026-01-03 - service contained only placeholder code with no actual OSINT functionality

### Data Services (7)

| Service | Port | LOC | Purpose | Status |
|---------|------|-----|---------|--------|
| **fmp-service** | 8113 | 6.8k | Financial Market data (FMP API, host network) | ✅ Healthy |
| **mediastack-service** | 8121 | - | Mediastack news API integration | ✅ Healthy |
| **scraping-service** | N/A | 5.0k | Web content scraping | ⚠️ No tests |
| **geolocation-service** | 8115 | - | Geolocation extraction | ✅ Healthy |
| **ontology-proposals-service** | 8109 | - | OSS Ontology proposals | ✅ Healthy |
| **oss-service** | 8110 | - | Open-source intelligence service | ✅ Healthy |
| **nexus-agent** | 8120 | - | Agent orchestration | ✅ Healthy |

### Predictive Analytics Services (1)

| Service | Port | LOC | Purpose | Status | Phase |
|---------|------|-----|---------|--------|-------|
| **prediction-service** | 8116 | 2.8k | ML price forecasting, trading signals, event impact, portfolio optimization | ⚠️ DISABLED (profile: prediction, since 2026-02-08) | Phase 4 |

> ⚠️ **Disabled:** prediction-service and related workers (strategy-evaluator, celery-worker, celery-beat) are gated behind `profiles: ["prediction"]` since 2026-02-08 due to build errors. Start with: `docker compose --profile prediction up`

**Features (when enabled):**
- ✅ **Phase 1:** Feature engineering, database schema, service clients
- ✅ **Phase 2:** 3 ML models (Sentiment, Topic Volume, ARIMA)
- ✅ **Phase 3:** Backtesting, performance metrics, outcome tracking
- ✅ **Phase 4:** Trading signals, event impact, portfolio optimization (MPT)

### Frontend Applications (2 + n8n)

| Application | Port | LOC | Framework | Purpose |
|-------------|------|-----|-----------|---------|
| **frontend** | 3000 | 380k | React/Vite | Main UI application |
| **intelligence-frontend** | 5173 | N/A | React/Vite | Intelligence dashboard |
| **n8n** | 5678 | N/A | Node.js | Workflow automation (infrastructure) |

### Infrastructure (5)

| Component | Port | Purpose |
|-----------|------|---------|
| **PostgreSQL** | 5432 | Relational database (80+ tables) |
| **Neo4j** | 7474 | Graph database (relationships) |
| **RabbitMQ** | 15672 | Message broker (event bus) |
| **Redis** | 6379 | Cache & session store |
| **n8n** | 5678 | Workflow automation engine |

### Resilience Infrastructure

**Circuit Breaker Pattern (Production-Ready)**
- **Library:** `news-mcp-common/resilience/` (1,876 LOC)
- **Coverage:** 4 specialized wrappers (LLM, HTTP, RabbitMQ, Database)
- **Metrics:** Prometheus integration (5 metrics exposed)
- **Monitoring:** 16-panel Grafana dashboard
- **Documentation:** [ADR-035](docs/decisions/ADR-035-circuit-breaker-pattern.md)

**Protected Dependencies:**
- **LLM Providers:** OpenAI, Gemini (automatic failover)
- **HTTP APIs:** Perplexity, webhooks (per-URL isolation)
- **RabbitMQ:** Connection pool protection (feed-service, content-analysis-v3)
- **PostgreSQL:** Connection exhaustion prevention (all services)

**Business Impact:**
- 90% cost reduction during LLM outages ($25 → $2.50)
- 97% faster recovery (30s vs 25 min)
- Automatic failover (no manual intervention)

---

## 3. Service Landscape

### Service Dependencies (Port Mapping)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Service Layer (FastAPI)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Auth & Core                Intelligence & AI         Data & Search  │
│  ┌──────────┐              ┌─────────────────┐      ┌─────────────┐ │
│  │ auth     │              │ content-analysis│      │ fmp         │ │
│  │ (8100)   │              │ v3 (8117)       │      │ (8113)      │ │
│  └──────────┘              │ 3x consumers    │      └─────────────┘ │
│  ┌──────────┐              └─────────────────┘      ┌─────────────┐ │
│  │ feed     │              ┌─────────────────┐      │ search      │ │
│  │ (8101)   │              │ knowledge-graph │      │ (8106)      │ │
│  └──────────┘              │ (8111)          │      └─────────────┘ │
│  ┌──────────┐              └─────────────────┘      ┌─────────────┐ │
│  │ research │              ┌─────────────────┐      │ scraping    │ │
│  │ (8103)   │              │ entity-canon    │      │ (worker)    │ │
│  └──────────┘              │ (8112)          │      └─────────────┘ │
│  ┌──────────┐              └─────────────────┘      ┌─────────────┐ │
│  │ scheduler│              ┌─────────────────┐      │ mediastack  │ │
│  │ (8108)   │              │ intelligence    │      │ (8121)      │ │
│  └──────────┘              │ (8118)          │      └─────────────┘ │
│  ┌──────────┐              └─────────────────┘      ┌─────────────┐ │
│  │ analytics│              ┌─────────────────┐      │ geolocation │ │
│  │ (8107)   │              │ narrative       │      │ (8115)      │ │
│  └──────────┘              │ (8119)          │      └─────────────┘ │
│                             └─────────────────┘                      │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **Framework:** FastAPI (Python 3.11+)
- **API Docs:** OpenAPI 3.0 (Swagger UI at `/docs`)
- **Async:** Uvicorn ASGI server
- **Testing:** pytest (518 test functions across 51 files)

**Frontend:**
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite (HMR < 1 second)
- **State Management:** Context API, React Query
- **UI Library:** Custom components + Material-UI

**Infrastructure:**
- **Container Runtime:** Docker Compose
- **Message Broker:** RabbitMQ 3.12 (AMQP 0-9-1)
- **Database:** PostgreSQL 15, Neo4j 5.9.0
- **Cache:** Redis 7-alpine
- **Orchestration:** n8n (latest)

---

## 4. Event-Driven Architecture

### Message Broker Topology

**RabbitMQ Configuration:**
- **Exchanges:** 9 (1 custom: `news.events`)
- **Queues:** 7 active queues
- **Consumers:** 8 active
- **Messages Processed:** 36k+ (news.events exchange)

### Key Event Flows

#### Flow 1: Article Processing Pipeline (Primary)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Article Processing Pipeline                        │
└─────────────────────────────────────────────────────────────────────────┘

1. RSS Feed Ingestion:
   ┌──────────────┐
   │ feed-service │ ──[poll RSS/Atom]──► External RSS Feeds
   │   (8101)     │
   └──────┬───────┘
          │
          │ [Outbox Pattern - Transactional]
          │
          ▼
   ┌──────────────────────────────────────────┐
   │  PostgreSQL: feed_items table            │
   │  + outbox_events table (Transactional)   │
   └──────────────────────────────────────────┘
          │
          │ [Background Worker publishes]
          │
          ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ RabbitMQ: news.events exchange                              │
   │   Event: article.created                                    │
   │   Routing: article.created, feed.item.created               │
   └─────────────────────────────────────────────────────────────┘
          │
          ├──────────────┬──────────────────┬─────────────────┐
          │              │                  │                 │
          ▼              ▼                  ▼                 ▼
   ┌──────────┐   ┌────────────┐    ┌──────────┐     ┌──────────┐
   │ content  │   │ scraping   │    │ search   │     │ knowledge│
   │ analysis │   │ service    │    │ service  │     │ graph    │
   │ v3       │   │ (workers)  │    │ (8106)   │     │ (8111)   │
   │ (8117)   │   └────────────┘    └──────────┘     └──────────┘
   │ 3 workers│
   └─────┬────┘
         │
         │ [AI Analysis Complete]
         │
         ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ RabbitMQ: news.events exchange                              │
   │   Event: analysis.v3.completed                              │
   │   Routing: analysis.v3.completed                            │
   └─────────────────────────────────────────────────────────────┘
         │
         ├──────────────┬──────────────────┐
         │              │                  │
         ▼              ▼                  ▼
   ┌──────────┐   ┌────────────┐    ┌──────────┐
   │ feed     │   │ search     │    │ knowledge│
   │ service  │   │ indexing   │    │ graph    │
   │ consumer │   │ (8106)     │    │ consumer │
   │          │   │            │    │ (8111)   │
   └──────────┘   └────────────┘    └──────────┘
```

**Key Patterns:**
- **Outbox Pattern:** feed-service uses transactional outbox for guaranteed event publishing
- **Horizontal Scaling:** content-analysis-v3 has 3 consumer workers for parallel processing
- **Dead Letter Queue (DLQ):** All queues have DLQ configured for failed messages
- **Topic Exchange:** news.events uses topic routing (e.g., `article.created`, `analysis.completed`)

#### Flow 1b: V3 Analysis Pipeline (Event-Driven, Parallel to V2)

**⚠️ Important:** V3 uses event-driven architecture with NO direct database writes. All data flows through RabbitMQ events.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Content Analysis V3 Pipeline (Event-Driven)                 │
└─────────────────────────────────────────────────────────────────────────┘

1. Analysis Request (Triggered by article.created):
   ┌──────────────┐
   │ feed-service │ ──[article.created]──► RabbitMQ: news.events
   │   (8101)     │                        └─► analysis_v3_requests_queue
   └──────────────┘

2. V3 Worker Processing (3 parallel workers):
   ┌────────────────────────────────────────┐
   │ content-analysis-v3 (3 workers)        │
   │   Worker 1, 2, 3 (Prefetch: 10 each)   │
   │   Total Capacity: 30 concurrent         │
   └────────┬───────────────────────────────┘
            │
            │ [Progressive Analysis Pipeline]
            │
            ├─► Tier 0: Triage (keep/discard, priority_score, category)
            │   - Budget: 800 tokens (~$0.0002/article)
            │   - Model: gpt-4.1-nano
            │   - Time: 2-3s
            │
            ├─► Tier 1: Foundation (entities, relations, topics, scores)
            │   - Budget: 2500 tokens (~$0.0005/article)
            │   - Model: gpt-4.1-nano
            │   - Time: 5-7s
            │
            └─► Tier 2: Specialists (5 specialist types, conditional)
                - ENTITY_EXTRACTOR: Entity enrichment
                - TOPIC_CLASSIFIER: Topic classification
                - FINANCIAL_ANALYST: Financial metrics (optional)
                - GEOPOLITICAL_ANALYST: Geopolitical analysis (optional)
                - SENTIMENT_ANALYZER: Sentiment metrics (optional)
                - Budget: 2500 tokens total (~$0.0004/article)
                - Time: 8-10s
                │
                │ [Total: 15-20s, ~$0.001/article]
                │
                ▼

3. Event Publishing (analysis.v3.completed):
   ┌─────────────────────────────────────────────────────────────┐
   │ RabbitMQ: news.events exchange                              │
   │   Event: analysis.v3.completed                              │
   │   Routing Key: analysis.v3.completed                        │
   │   Payload: {                                                │
   │     article_id, success, pipeline_version: "3.0",           │
   │     tier0: {priority_score, category, keep, ...},           │
   │     tier1: {entities[], relations[], topics[], scores},     │
   │     tier2: {ENTITY_EXTRACTOR, TOPIC_CLASSIFIER, ...},       │
   │     metrics: {costs, tokens, timing}                        │
   │   }                                                         │
   └─────────────────────────────────────────────────────────────┘
                │
                │
                ▼

4. Storage (Unified Table via Event Consumer):
   ┌────────────────────────────────────────┐
   │ feed-service analysis_consumer         │
   │   Queue: analysis_results_queue        │
   └────────┬───────────────────────────────┘
            │
            │ [Store results in unified table]
            │
            ▼
   ┌────────────────────────────────────────┐
   │ PostgreSQL: public.article_analysis    │
   │   Columns:                             │
   │   - article_id, pipeline_version       │
   │   - triage_results (tier0 JSONB)       │
   │   - tier1_results (tier1 JSONB)        │
   │   - tier2_results (tier2 JSONB)        │
   │   - metrics (cost/time JSONB)          │
   └────────────────────────────────────────┘
            │
            │ [Direct database read - NO proxy]
            │
            ▼

5. Frontend Access (via feed-service API):
   ┌────────────────────────────────────────┐
   │ frontend → GET /api/v1/feeds/{id}/items│
   │   Response includes both:              │
   │   - pipeline_execution (V2 legacy)     │
   │   - v3_analysis (V3 active)            │
   └────────────────────────────────────────┘
```

**V3 vs V2 Architecture Comparison** (V2 archived 2025-11-24, V3 is the sole active pipeline):

| Aspect | V2 (Legacy) | V3 (Active) |
|--------|-------------|-------------|
| **Database Writes** | Direct to content_analysis_v2.pipeline_executions | Event-driven via RabbitMQ → feed-service consumer |
| **Storage Table** | Separate schema (content_analysis_v2) | Unified table (public.article_analysis) |
| **Event Pattern** | Worker writes DB → publishes event | Worker publishes event → consumer writes DB |
| **Workers** | 4 workers | 3 workers |
| **Throughput** | 4x parallel | 3x parallel (30 concurrent via prefetch) |
| **Frontend Access** | Proxy API call to content-analysis-v2 | Direct DB read via feed-service (30-40x faster) |
| **Cost** | ~$0.005/article | ~$0.001/article (5x cheaper) |
| **Processing Time** | 5-15s | 15-20s (more thorough analysis) |

**Performance Metrics (V3):**
- **API Response Time:** 4-5ms sequential, 93ms concurrent (30-40x faster than V2)
- **Database Query:** 0.145ms
- **Worker Processing:** 15-20s per article (Tier0+Tier1+Tier2)
- **Total Capacity:** 30 concurrent analyses (3 workers × 10 prefetch)

**See Also:**
- [services/content-analysis-v3/README.md](services/content-analysis-v3/README.md) - V3 Pipeline Documentation
- [services/feed-service/README.md](services/feed-service/README.md) - V3 Analysis API
- the incident postmortem (archived) - V3 Production Issues & Fixes

#### Flow 2: Knowledge Graph Extraction

```
┌────────────────────────────────────────────────────────────────┐
│              Knowledge Graph Relationship Extraction            │
└────────────────────────────────────────────────────────────────┘

content-analysis-v3 (8117)
  │
  │ [Extract entities & relationships from article]
  │
  ▼
RabbitMQ: news.events
  Event: analysis.relationships.extracted
  Payload: {entities: [...], relationships: [...]}
  │
  │
  ▼
knowledge-graph-service (8111)
  │
  │ [Store in Neo4j]
  │
  ▼
Neo4j Graph Database (7474)
  Nodes: Entities (Person, Organization, Location, Event)
  Edges: Relationships (WORKS_FOR, LOCATED_IN, PARTICIPATED_IN)
```

#### Flow 3: Entity Canonicalization

```
┌────────────────────────────────────────────────────────────────┐
│                    Entity Deduplication Flow                    │
└────────────────────────────────────────────────────────────────┘

knowledge-graph-service (8111)
  │
  │ [New entities detected]
  │
  ▼
entity-canonicalization-service (8112)
  │
  │ [Deduplicate & merge similar entities]
  │ Example: "Donald Trump" = "Trump" = "D. Trump"
  │
  ▼
PostgreSQL: canonical_entities table
  └──► Update knowledge graph references
```

### Producer/Consumer Matrix

| Service | Produces Events | Consumes Events |
|---------|----------------|-----------------|
| **feed-service** | article.created, feed.item.created | analysis.v3.completed (analysis_results_queue) |
| **content-analysis-v3** | analysis.v3.completed | article.created (analysis_v3_requests_queue) |
| **scraping-service** | scraping.completed | article.created, feed.item.created (scraping.jobs) |
| **knowledge-graph** | - | analysis.relationships.extracted (knowledge_graph_relationships) |
| **search-service** | - | analysis.completed (search_indexing_events) |
| **fmp-service** | market.data.updated | - |

---

## 5. Database Architecture

### PostgreSQL (Shared Schema Pattern)

**Configuration:**
- **Database:** `news_mcp` (single shared database)
- **Schemas:** 1 active schema
  - `public` schema: 80+ tables (shared by all services, includes intelligence tables)
  - `content_analysis_v2` schema: 🗄️ DEPRECATED (service archived 2025-11-24, tables renamed to `_deprecated`)
- **Size:** 300 MB
- **Active Connections:** 13

#### Key Tables (Public Schema)

```
┌─────────────────────────────────────────────────────────────────┐
│                       PostgreSQL Schema                          │
└─────────────────────────────────────────────────────────────────┘

Core Entities:
  ┌──────────┐     ┌──────────┐     ┌──────────────┐
  │  users   │────►│  feeds   │────►│  feed_items  │
  └──────────┘     └──────────┘     └──────────────┘
       │                                     │
       │                                     │
       ▼                                     ▼
  ┌──────────┐                      ┌──────────────┐
  │  roles   │                      │   articles   │
  └──────────┘                      └──────────────┘
                                            │
                                            │
                    ┌───────────────────────┼─────────────────────┐
                    │                       │                     │
                    ▼                       ▼                     ▼
           ┌─────────────────┐    ┌─────────────┐    ┌──────────────────┐
           │ article_analysis│    │   entities  │    │ entity_mentions  │
           └─────────────────┘    └─────────────┘    └──────────────────┘

Support Tables:
  - notifications (email, webhook tracking)
  - analytics_metrics (usage tracking)
  - search_indices (full-text search)
  - outbox_events (transactional event publishing)
  - scheduler_tasks (Celery beat schedules)
```

**Architectural Decision:**
- **Single Shared Database** instead of 14 separate databases per service
- **Pros:** Simpler operations, ACID guarantees, no distributed transactions
- **Cons:** Potential contention (not observed yet at current scale)
- **Mitigation:** Was schema-level separation for content-analysis-v2 (now archived; `public.article_analysis` is the unified data store)

#### Content Analysis V2 Schema (ARCHIVED)

> 🗄️ **Archived 2025-11-24:** This schema belongs to the decommissioned content-analysis-v2 service. Tables were renamed to `_deprecated`. All analysis data now lives in `public.article_analysis` (unified table, V3 pipeline).

```
content_analysis_v2 schema (DEPRECATED):
  - pipeline_jobs → _deprecated
  - tier1_results → _deprecated
  - tier2_results → _deprecated
  - entity_extractions → _deprecated
  - relationship_candidates → _deprecated
  - quality_metrics → _deprecated
```

### Neo4j (Graph Database)

**Configuration:**
- **Port:** 7474 (HTTP), 7687 (Bolt)
- **Size:** 1.146 GiB
- **Purpose:** Entity relationship graph

**Schema:**
```
┌─────────────────────────────────────────────────────────────────┐
│                         Neo4j Graph Schema                       │
└─────────────────────────────────────────────────────────────────┘

Node Types:
  (:Person)
  (:Organization)
  (:Location)
  (:Event)
  (:Topic)

Relationship Types:
  -[:WORKS_FOR]->      (Person → Organization)
  -[:LOCATED_IN]->     (Entity → Location)
  -[:PARTICIPATED_IN]-> (Person → Event)
  -[:RELATED_TO]->     (Entity → Entity)
  -[:MENTIONS]->       (Article → Entity)

Example Query:
  MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)-[:LOCATED_IN]->(l:Location)
  WHERE l.name = "United States"
  RETURN p.name, o.name
```

---

## 6. Critical Paths

### Path 1: Article Ingestion to Analysis (End-to-End)

**SLA Target:** < 30 seconds (article published → analysis completed)

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Article Processing Critical Path                     │
└──────────────────────────────────────────────────────────────────────┘

Time: T+0s
  └─► RSS Feed polled by feed-service (scheduler triggers)

Time: T+1s
  └─► New article detected, saved to feed_items table
      └─► Outbox event created (transactional)

Time: T+2s
  └─► Outbox worker publishes article.created event to RabbitMQ

Time: T+3s
  └─► content-analysis-v3 consumer picks up event
      └─► 3 consumers available (prefetch: 10 each = 30 concurrent)

Time: T+3s - T+23s
  └─► V3 Progressive Analysis Pipeline:
      1. Tier 0 (Triage): 2-3s
         - Keep/discard decision
         - Priority scoring, category

      2. Tier 1 (Foundation): 5-7s
         - Entities, relations, topics, scores

      3. Tier 2 (Specialists): 8-10s
         - Conditional: entity enrichment, topic classification
         - Optional: financial, geopolitical, sentiment

Time: T+23s
  └─► analysis.v3.completed event published

Time: T+24s - T+28s
  └─► Parallel Consumers:
      - feed-service analysis consumer stores results (1s)
      - search-service indexes article (1s)
      - knowledge-graph stores entities (2s)

Total: 25-30 seconds (well within SLA)
```

### Path 2: User Query to Response

**SLA Target:** < 100ms (user search → results displayed)

```
User Query (Frontend)
  │
  │ [HTTP GET /api/v1/search?q=...]
  │
  ▼
search-service (8106)
  │
  │ [PostgreSQL full-text search]
  │ [Response: 5-10ms]
  │
  ▼
Frontend displays results

Total: < 100ms (well within SLA)
```

---

## 7. Integration Points

### External APIs

| Service | API | Purpose | SLA |
|---------|-----|---------|-----|
| **research-service** | Perplexity API | AI research queries | 🔴 1243ms (SLOW) |
| **content-analysis-v3** | OpenAI GPT-4.1-nano | V3 pipeline (Tier 0-2) | ~15-20s |
| **fmp-service** | Financial Modeling Prep | Market data | ~50-100ms |
| **scraping-service** | Various | Web scraping | Variable |

### Internal Service Communication

**Primary:** Event-driven via RabbitMQ (async)
**Secondary:** HTTP/REST for synchronous queries (rare)

**Authentication:**
- All API endpoints protected by JWT (issued by auth-service:8100)
- Internal service-to-service: Shared secret or service accounts

### Frontend ↔ Backend

```
Frontend (React) ──[HTTP/REST]──► API Gateway Pattern (multiple FastAPI services)
                   [JWT Token in Authorization header]

Example:
  GET /api/v1/feeds
  Authorization: Bearer eyJhbGc...

Response:
  200 OK
  Content-Type: application/json
  {
    "items": [...],
    "total": 150,
    "page": 1
  }
```

---

## 8. Deployment Topology

### Development Environment (Current)

```
┌────────────────────────────────────────────────────────────────────┐
│                    Docker Compose - Development                     │
└────────────────────────────────────────────────────────────────────┘

docker-compose.yml (Volume Mounts - Hot Reload)
  │
  ├─► services/*/app/*.py ──[mapped]──► Container /app
  ├─► frontend/src/*.tsx ──[mapped]──► Container /app
  │
  └─► All services run with:
      - Uvicorn --reload (< 1 second restart)
      - Vite HMR (< 100ms hot module replacement)

Networks:
  - news-network (bridge) - All services connected
  - Host ports exposed: 3000, 5173, 5678, 8100-8123, 9001-9008, 15672, 5432, 7474, 6379

Volumes:
  - postgres-data (persistent database)
  - neo4j-data (persistent graph)
  - redis-data (persistent cache)
  - rabbitmq-data (persistent queues)

Special Mounts:
  - /var/run/docker.sock:ro → analytics-service (Health monitoring)
    Security: Read-only, GID 988, cannot control containers
    See: ADR-038-docker-api-health-monitoring.md
```

### Production Environment (Target)

```
docker-compose.prod.yml (Optimized Builds - No Volume Mounts)
  │
  ├─► Multi-stage Docker builds (smaller images)
  ├─► No --reload flags (production mode)
  ├─► Health checks enforced
  ├─► Resource limits (CPU/Memory)
  └─► Logging to centralized system
```

### Resource Usage (Current Baseline)

| Component | CPU % | Memory | Network I/O |
|-----------|-------|--------|-------------|
| **entity-canonicalization** | 2.44% | ✅ 1.24 GiB | 370 MB / 60.6 MB |
| **feed-service** | 2.94% | 148.8 MiB | 3.06 GB / 403 MB |
| **content-analysis-v3** (3x) | - | - | N/A |
| **postgres** | 0.12% | 278 MiB | 911 MB / 19 GB |
| **redis** | 0.76% | 33 MiB | 657 MB / 613 MB |

**Previous Issue (Resolved 2025-10-30):** entity-canonicalization memory leak fixed (8.5 GB → 1.2 GB)

---

## 9. Known Issues

### 🔴 Critical (P0)

1. **entity-canonicalization Memory Leak** ✅ **RESOLVED (2025-10-30)**
   - **Was:** 8.55 GiB (43.82% of total system memory)
   - **Now:** 1.24 GiB (6.35%) - stable for 19+ hours
   - **Resolution:** Singleton pattern for SentenceTransformer model (Commit: 788a6ce)
   - **Root Cause:** Each async batch job created new 420 MB model instance
   - **Fix Applied:** Dependency injection with shared model across all jobs
   - **Remaining:** Baseline higher than optimal (no urgent action needed)
   - **Future Optimization:** Candidate + Embedding caching (target: 500-800 MB)
   - **Resilience Note:** Circuit breaker pattern protects against cascading failures during resource exhaustion (see [ADR-035](docs/decisions/ADR-035-circuit-breaker-pattern.md))

2. **research-service Performance**
   - **Current:** 1243ms average response time
   - **Expected:** < 50ms
   - **Impact:** Poor user experience, API timeouts
   - **Root Cause:** Perplexity API latency + no caching
   - **Mitigation:** Circuit breaker prevents cascade (fail-fast in 0s vs 30s timeout)
   - **Fix:** Phase 2 Quick Win (Priority #2) - Add caching layer

3. **content-analysis-v2 Test Coverage** ✅ **RESOLVED (2025-11-24)**
   - **Was:** 5 test functions for 237k LOC
   - **Resolution:** Service archived → `services/_archived/content-analysis-v2-20251124`
   - **Successor:** content-analysis-v3 (8117) is the sole active analysis pipeline

### 🟡 Medium (P1)

4. **Missing Health Endpoints**
   - **Services:** search-service (8106)
   - **Impact:** Manual health checks, no automated monitoring
   - **Fix:** Phase 2 Quick Win (1-2 hours)

5. **No Test Coverage Measurement**
   - **Current:** pytest-cov missing from requirements.txt
   - **Impact:** Unknown actual coverage %
   - **Fix:** Phase 2 Quick Win (<1 hour)

6. **Technical Debt**
   - **Current:** ~740 active TODO/FIXME comments (712 frontend + remaining services)
   - **Note:** 677 content-analysis-v2 TODOs excluded (service archived 2025-11-24)
   - **Impact:** Code maintainability
   - **Fix:** Phase 3 Structural Refactoring
   - **Comprehensive Analysis:** [docs/technical-debt/TECHNICAL_DEBT_ANALYSIS_2025.md](docs/technical-debt/TECHNICAL_DEBT_ANALYSIS_2025.md) ⭐ NEW

7. **V3 Schema Drift — Intelligence Analytics** ✅ **RESOLVED (2026-02-24)**
   - **Was:** 6 bugs across analytics/search/intelligence services — V2 JSONB field names in queries, wrong sentiment path, missing feed_items JOIN, auth on internal calls, outdated risk normalization, missing trending_entities
   - **Resolution:** All 6 bugs fixed, 11 files changed. See the incident postmortem (archived)
   - **Root Cause:** V2→V3 schema change not propagated to downstream consumers (silent failures, no errors logged)
   - **Prevention:** Schema migration checklist, silent failure metrics, integration smoke tests

---

## 🚀 Week 2 & Week 3 Improvements (2025-11-24)

### Week 2: Tier 1 Services to GREEN

**Achievement:** Converted 5 Tier 1 services to production-ready status using parallel Task agents.

#### Feed Service
- ✅ **Circuit Breaker Pattern:** Complete state machine (CLOSED → OPEN → HALF_OPEN)
- ✅ **RabbitMQ Hardening:** DLQ + Retry with exponential backoff
- ✅ **Error Handling:** Standardized responses across all endpoints
- ✅ **Testing:** 58 integration tests covering happy path + failure scenarios
- **Status:** RED → **GREEN**

#### Scraping Service
- ✅ **Memory Leak Fixed:** Browser contexts properly closed in finally blocks
- ✅ **Rate Limiting:** Multi-level (domain, feed, global) with max 5 parallel jobs
- ✅ **Monitoring:** Health endpoints with memory tracking
- **Status:** RED → **GREEN**

#### FMP Service
- ✅ **DCC-GARCH Performance:** **0.154s** (6-7x better than 1s target!)
- ✅ **Data Retention:** Comprehensive policy with dry-run safety
- ✅ **Market Hours:** Optimized (no duplicates)
- **Status:** YELLOW → **GREEN**

#### Auth Service
- ✅ **Secrets Manager:** AWS + Vault support with rotation
- ✅ **JWT Key Rotation:** 30-day grace period for zero-downtime
- ✅ **Redis Persistence:** AOF + RDB for data durability
- **Status:** YELLOW → **GREEN**

#### Content-Analysis-V3
- ✅ **Authentication:** JWT on all analysis endpoints
- ✅ **Integration:** Seamless with feed-service
- **Status:** YELLOW → **GREEN**

**Metrics:**
- Production Code: 5,050 lines
- Test Code: 1,850 lines (58+ tests)
- Documentation: 50 KB (6 comprehensive docs)

---

### Week 3: Eliminate All RED Services

**Achievement:** Eliminated all RED services and hardened 5 Tier 2 services to production-ready status.

#### Scheduler Service
- ✅ **Test Coverage:** 85% (130+ tests)
- ✅ **Monitoring:** 40+ Prometheus metrics (job_executions, failures, latency)
- ✅ **Error Handling:** Retry logic + Circuit breaker pattern
- ✅ **Health Checks:** Multi-level (basic, detailed, ready)
- **Status:** RED → **GREEN**

#### Notification Service (ARCHIVED 2026-01-03)
- 🗄️ **Replaced by:** n8n workflows (`n8n-workflows/narrative-intelligence/`)
- 📁 **Archived to:** `services/_archived/notification-service-20260103/`
- **Reason:** Service received 0 successful API calls; n8n handles all notifications
- **Status:** ARCHIVED

#### Analytics Service
- ✅ **WebSocket Stability:** 30-second heartbeat, auto-cleanup of dead connections
- ✅ **Circuit Breaker:** Prevents cascade failures
- ✅ **Performance:** 99.9% stability with 100+ concurrent connections
- ✅ **Connection Pool:** Auto-cleanup of dead connections
- **Status:** YELLOW → **GREEN**

#### Prediction Service
- ✅ **Redis Caching:** 30-40x speedup on cache hits (5-15ms vs 350-450ms)
- ✅ **Batch Predictions:** 2.7x speedup vs sequential
- ✅ **Model Loading:** Singleton pattern (already optimal)
- ✅ **Error Handling:** Comprehensive retry logic
- **Status:** YELLOW → **GREEN**

#### Narrative Service
- ✅ **Performance:** ~150ms uncached, 3-5ms cached (13x better than 2s target!)
- ✅ **Parallel Execution:** Frame detection + Bias analysis concurrently
- ✅ **Redis Caching:** Intelligent cache key design
- ✅ **Testing:** 40+ integration tests covering edge cases
- **Status:** YELLOW → **GREEN**

#### Quick Wins (Research, OSINT, Intelligence)
- ✅ **Research:** Rate limiting verified (10 req/min), cost tracking ($50/day max)
- ✅ **OSINT:** Security hardening (input validation, auth, security headers)
- ✅ **Intelligence:** Integration architecture (circuit breaker, event bus, service clients)
- **Status:** All YELLOW → **GREEN**

**Metrics:**
- Production Code: 15,000+ lines
- Test Code: 150+ tests
- Documentation: 100+ KB (10+ comprehensive docs)

**Result:** **ZERO RED SERVICES** ✅

---

### Systematic Code Quality Audit (2026-02-20)

**Achievement:** Comprehensive 3-phase code quality audit across 18+ services. Two commits: `6c62cd6` (44 files) and `7afd939` (7 files).

#### Phase 1: Critical Security Fixes

- ✅ **SQL Injection (P0):** Fixed `ARRAY{user_input}` interpolation in geolocation-service and unsafe `INTERVAL` interpolation in clustering-service. Replaced with parameterized queries (`:param` binding).
- ✅ **JWT Secret Fragmentation (P0):** 7 services had inconsistent/weak JWT secret defaults. Unified all to match `docker-compose.yml` secret. Fixed env var name mismatch in narrative-service (`JWT_SECRET_NARRATIVE` → `JWT_SECRET_KEY`).
- ✅ **CORS Misconfiguration (P0):** 20 services had `allow_origins=["*"]` + `allow_credentials=True` (forbidden by CORS spec). Replaced with explicit origins `["http://localhost:3000", "http://localhost:5173"]`.
- ✅ **Pickle Deserialization (P0):** prediction-service `specialized_gate_service.py` used raw `pickle.load()`. Replaced with `secure_load()` from existing `SecureModelLoader` (path validation, size limits, audit logging).
- ✅ **Rate Limit Bypass (P1):** `X-Service-Name` header could be spoofed to bypass rate limits. Now only Docker-internal IPs grant bypass; header used for logging only.

#### Phase 2: Performance & Resource Fixes

- ✅ **Celery Memory Limits:** Added `worker_max_memory_per_child` to 6 services (200-400 MB based on ML requirements).
- ✅ **Fork-Unsafe Async Engine:** prediction-service `database.py` had module-level `create_async_engine()`. Applied lazy proxy pattern (same as intelligence/feed-service fixes).
- ✅ **N+1 Query Elimination:**
  - intelligence-service ingestion: 500 duplicate-check queries → 1 batch query + in-memory set
  - intelligence-service enrichment: N cross-DB joins → 1 batch query + dict matching
  - intelligence-service clusters: N timeline queries → 1 GROUP BY batch query
  - analytics-service trend: 24 loop queries → 1 query + Python bucketing
  - analytics-service metrics overview: 28 loop queries → 1 GROUP BY query
- ✅ **HTTP Timeouts:** Added `timeout=30.0` to clustering-service `fmp_correlation_service.py`.

#### Phase 3: Code Quality & Maintainability

- ✅ **Bare Except Blocks:** Fixed `except:` → specific exceptions in 8 files across 5 services.
- ✅ **Dead Code Cleanup:** Removed 3 deprecated auto-trading endpoints, deprecated `app.indicators` module (expired 2025-01-19), commented-out APScheduler code.
- ℹ️ **Skipped:** FMP admin auth (read-only monitoring in LAN, low risk), lazy ML imports (already correct).

**Metrics:**
- Files Changed: 51 across 18+ services
- Security Fixes: 5 critical vulnerabilities
- Query Optimizations: ~500+ queries/request eliminated
- Dead Code Removed: ~60 lines

---

## 📚 Additional Resources

### Documentation

- **Service Details:** [reports/phase-1-inventory/SERVICE_INVENTORY_SUMMARY.md](reports/phase-1-inventory/SERVICE_INVENTORY_SUMMARY.md)
- **Database Schema:** Task 102 (coming soon)
- **RabbitMQ Topology:** [reports/phase-1-inventory/rabbitmq-producers-consumers.md](reports/phase-1-inventory/rabbitmq-producers-consumers.md)
- **API Endpoints:** `http://localhost:<port>/docs` (Swagger UI)
- **Resilience Patterns:** [ADR-035: Circuit Breaker Pattern](docs/decisions/ADR-035-circuit-breaker-pattern.md)
- **Week 2 Retrospective:** [reports/tasks/WEEK2_RETROSPECTIVE.md](reports/tasks/WEEK2_RETROSPECTIVE.md)
- **Week 3 Retrospective:** [reports/tasks/WEEK3_RETROSPECTIVE.md](reports/tasks/WEEK3_RETROSPECTIVE.md)

### Development Guides

- **Getting Started:** [README.md](README.md)
- **Guides:** [docs/guides/](docs/guides/) — Deployment, security, scaling, backup

### Operational

- **Health Check:** `./scripts/health_check.sh` — Check all services
- **API Reference:** [docs/api/API_LANDSCAPE.md](docs/api/API_LANDSCAPE.md) — All 250+ endpoints

---

## 🔄 Maintenance & Updates

**This document should be updated when:**
- New services are added or removed
- Architecture patterns change (e.g., move from shared DB to per-service DBs)
- Critical paths are modified (e.g., new event flows)
- Major refactoring completed (Phase 2-5)

**Update Frequency:** After each Phase completion or major architectural change

**Owner:** Architecture Team (currently: Refactoring Project)

---

**Last Review:** 2026-02-24
**Next Review:** After next major feature completion
**Version History:**
- v1.4 (2026-02-24): Documentation accuracy cleanup - removed stale V2 references (archived 2025-11-24), fixed port assignments (fmp→8113, llm-orchestrator→optional), added missing services to tables, updated container count (57), marked prediction-service as disabled
- v1.3 (2026-02-20): Added Systematic Code Quality Audit section
- v1.2 (2026-01-22): News Intelligence System Phase 2
- v1.0 (2025-10-30): Initial version based on Task 101 Service Inventory

# API Landscape - News Microservices Platform

**Last Updated:** 2026-02-09
**Total Services:** 25 active (+ 8 MCP servers)
**Total REST Endpoints:** ~250+
**Total MCP Tools:** ~270+
**API Protocol:** REST (FastAPI/OpenAPI 3.0)
**Authentication:** JWT Bearer Token (via auth-service)

---

## Table of Contents

1. [Service Overview](#1-service-overview)
2. [Authentication & Authorization](#2-authentication--authorization)
3. [Core Services](#3-core-services)
   - [auth-service (8100)](#31-auth-service-port-8100)
   - [feed-service (8101)](#32-feed-service-port-8101)
   - [search-service (8106)](#33-search-service-port-8106)
   - [scheduler-service (8108)](#34-scheduler-service-port-8108)
4. [Analysis & Intelligence Services](#4-analysis--intelligence-services)
   - [content-analysis-v3 (8117)](#41-content-analysis-v3-port-8117)
   - [intelligence-service (8118)](#42-intelligence-service-port-8118)
   - [clustering-service (8122)](#43-clustering-service-port-8122)
   - [sitrep-service (8123)](#44-sitrep-service-port-8123)
5. [Knowledge & Entity Services](#5-knowledge--entity-services)
   - [entity-canonicalization-service (8112)](#51-entity-canonicalization-service-port-8112)
   - [knowledge-graph-service (8111)](#52-knowledge-graph-service-port-8111)
   - [ontology-proposals-service (8109)](#53-ontology-proposals-service-port-8109)
6. [Financial & Market Services](#6-financial--market-services)
   - [fmp-service (8113)](#61-fmp-service-port-8113)
   - [prediction-service (8116)](#62-prediction-service-port-8116)
7. [Data Acquisition Services](#7-data-acquisition-services)
   - [scraping-service](#71-scraping-service)
   - [research-service (8103)](#72-research-service-port-8103)
   - [mediastack-service (8120)](#73-mediastack-service-port-8120)
8. [Analytics & Monitoring](#8-analytics--monitoring)
   - [analytics-service (8107)](#81-analytics-service-port-8107)
9. [Narrative & Geolocation Services](#9-narrative--geolocation-services)
   - [narrative-service (8119)](#91-narrative-service-port-8119)
   - [narrative-intelligence-gateway (8114)](#92-narrative-intelligence-gateway-port-8114)
   - [geolocation-service (8115)](#93-geolocation-service-port-8115)
10. [Auxiliary Services](#10-auxiliary-services)
    - [oss-service (8109)](#101-oss-service-port-8109)
    - [llm-orchestrator-service (8121)](#102-llm-orchestrator-service-port-8121)
    - [nexus-agent (8124)](#103-nexus-agent-port-8124)
11. [MCP Server Layer](#11-mcp-server-layer)
12. [Event-Driven Architecture (RabbitMQ)](#12-event-driven-architecture-rabbitmq)
13. [Cross-Cutting Concerns](#13-cross-cutting-concerns)

---

## 1. Service Overview

```
Port Map:

8100  auth-service              JWT, RBAC, API Keys
8101  feed-service              RSS/Atom feeds, HITL review, articles
8103  research-service          Perplexity AI research
8106  search-service            Full-text + semantic search
8107  analytics-service         Metrics, dashboards, intelligence signals
8108  scheduler-service         Cron jobs, feed monitoring
8109  ontology-proposals        Ontology change proposals
8111  knowledge-graph-service   Neo4j graph queries
8112  entity-canonicalization   Entity dedup, fuzzy matching
8113  fmp-service               Financial market data (FMP API)
8114  narrative-gateway         Narrative analysis aggregation
8115  geolocation-service       Geographic visualization
8116  prediction-service        Predictive analytics, trading signals
8117  content-analysis-v3       4-tier AI analysis pipeline
8118  intelligence-service      Risk scoring, event detection
8119  narrative-service         Frame detection, bias analysis
8120  mediastack-service        MediaStack news API
8121  llm-orchestrator          DIA orchestration
8122  clustering-service        Article clustering, burst detection
8123  sitrep-service            Intelligence briefings (SITREP)
8124  nexus-agent               AI Co-Pilot

MCP Servers:
9001  mcp-intelligence-server   Intelligence analysis tools
      mcp-analytics-server      Analytics & prediction tools
      mcp-content-server        Feed management tools
      mcp-core-server           Auth & system tools
      mcp-search-server         Search & research tools
      mcp-integration-server    FMP & notification tools
      mcp-knowledge-graph       Neo4j graph tools
      mcp-orchestration-server  Scheduler & scraping tools
```

### Health Check Convention

All services implement consistent health endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Basic health check |
| `GET /health/live` | Kubernetes liveness probe |
| `GET /health/ready` | Kubernetes readiness probe |
| `GET /metrics` | Prometheus metrics |
| `GET /` | Root endpoint with service info |

---

## 2. Authentication & Authorization

**Provider:** auth-service (port 8100)
**Method:** JWT Bearer Token + optional API Key
**Token Refresh:** Via `/api/v1/auth/refresh`

### Auth Flow

```
1. POST /api/v1/auth/login → {access_token, refresh_token}
2. Authorization: Bearer <access_token>
3. POST /api/v1/auth/refresh → {new_access_token} (when expired)
```

### Auth Requirement per Service

| Service | Auth Required | Notes |
|---------|---------------|-------|
| auth-service | Partial | Login/register: no, management: yes |
| feed-service | Partial | Read: no, write/actions: yes |
| search-service | Partial | Search: no, saved searches: yes |
| scheduler-service | Partial | Status: no, actions: service auth |
| content-analysis-v3 | Partial | Status: optional, analysis: yes |
| intelligence-service | No | All endpoints public |
| clustering-service | Yes | All endpoints require JWT |
| sitrep-service | Yes | All endpoints require JWT |
| entity-canonicalization | No | All endpoints public |
| knowledge-graph-service | Partial | Admin endpoints only |
| fmp-service | No | All endpoints public |
| prediction-service | Yes | Most endpoints require JWT |
| analytics-service | Partial | Intelligence/dashboards: partial |
| research-service | Yes | All endpoints require JWT |
| narrative-service | Yes | All endpoints require JWT |
| geolocation-service | No | All endpoints public |

---

## 3. Core Services

### 3.1 auth-service (Port 8100)

**Purpose:** JWT authentication, RBAC, API key management, JWT key rotation

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login, get tokens | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| POST | `/api/v1/auth/logout` | Logout (blacklist token) | Yes |
| GET | `/api/v1/auth/me` | Current user profile | Yes |
| GET | `/api/v1/auth/stats` | Service statistics | No |
| POST | `/api/v1/auth/api-keys` | Create API key | Yes |
| GET | `/api/v1/auth/api-keys` | List API keys | Yes |
| DELETE | `/api/v1/auth/api-keys/{key_id}` | Delete API key | Yes |
| GET | `/api/v1/users` | List users | Admin |
| GET | `/api/v1/users/{user_id}` | Get user by ID | Yes |
| PUT | `/api/v1/users/{user_id}` | Update user | Yes |
| POST | `/api/v1/admin/rotate-jwt-key` | Rotate JWT key | Admin |
| GET | `/api/v1/admin/rotation-status` | JWT rotation status | Admin |

**Endpoints:** 14 | **Swagger:** `http://localhost:8100/docs`

---

### 3.2 feed-service (Port 8101)

**Purpose:** RSS/Atom feed management, article processing, HITL review, source assessment, Admiralty codes, scheduling

#### Feed Management

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/feeds` | List feeds (filter, paginate) | No |
| POST | `/api/v1/feeds` | Create feed | Yes |
| GET | `/api/v1/feeds/{feed_id}` | Get feed details | No |
| PUT | `/api/v1/feeds/{feed_id}` | Update feed | Yes |
| DELETE | `/api/v1/feeds/{feed_id}` | Delete feed | Yes |
| POST | `/api/v1/feeds/{feed_id}/fetch` | Trigger manual fetch | Yes |
| POST | `/api/v1/feeds/bulk-fetch` | Bulk fetch feeds | Yes |
| POST | `/api/v1/feeds/{feed_id}/reset-error` | Reset error status | Yes |

#### Feed Health & Quality

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/feeds/{feed_id}/health` | Feed health metrics | No |
| GET | `/api/v1/feeds/{feed_id}/quality` | Quality score (V1) | No |
| GET | `/api/v1/feeds/quality-v2/overview` | Quality metrics (V2) | No |

#### Articles

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/feeds/items` | List articles across feeds | No |
| GET | `/api/v1/feeds/{feed_id}/items` | Articles for specific feed | No |
| GET | `/api/v1/feeds/items/{item_id}` | Article details | No |
| PUT | `/api/v1/feeds/items/{item_id}` | Update article | Yes |
| POST | `/api/v1/feeds/items/{item_id}/analyze` | Trigger V3 analysis | Yes |
| POST | `/api/v1/feeds/items/research` | Create research article | Yes |

#### Source Management

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/sources` | List news sources | No |
| POST | `/api/v1/sources` | Create source | Yes |
| GET | `/api/v1/sources/{source_id}` | Source details | No |
| PUT | `/api/v1/sources/{source_id}` | Update source | Yes |
| GET | `/api/v1/sources/by-domain/{domain}` | Source by domain | No |
| GET | `/api/v1/source-feeds` | List source feeds | No |
| POST | `/api/v1/source-feeds` | Create source feed | Yes |

#### Source Assessment

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/feeds/{feed_id}/assess` | Trigger credibility assessment | Yes |
| GET | `/api/v1/feeds/{feed_id}/assessment-history` | Assessment history | No |
| GET | `/api/v1/assessment-status/{task_id}` | Poll task status | No |

#### Admiralty Code System

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/admiralty-codes/thresholds` | All thresholds | No |
| GET | `/api/v1/admiralty-codes/thresholds/{code}` | Threshold (A-F) | No |
| PUT | `/api/v1/admiralty-codes/thresholds/{code}` | Update threshold | Yes |
| GET | `/api/v1/admiralty-codes/weights` | Quality weights | No |
| PUT | `/api/v1/admiralty-codes/weights/{factor}` | Update weight | Yes |

#### Scheduling

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/scheduling/timeline` | Schedule timeline | No |
| GET | `/api/v1/scheduling/distribution` | Distribution stats | No |
| POST | `/api/v1/scheduling/optimize` | Optimize schedule | Yes |

#### Scraping Management

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/feeds/{feed_id}/threshold` | Scraping threshold | No |
| POST | `/api/v1/feeds/{feed_id}/scraping/reset` | Reset failures | Yes |

#### Duplicate Review (HITL)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/duplicates` | List near-duplicates | Yes |
| GET | `/api/v1/duplicates/{id}` | Duplicate details | Yes |
| PUT | `/api/v1/duplicates/{id}` | Submit decision | Admin |
| GET | `/api/v1/duplicates/stats` | Detection statistics | No |

#### Review Queue (HITL)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/review/submit` | Submit for review | Yes |
| GET | `/api/v1/review/queue` | List pending reviews | Yes |
| GET | `/api/v1/review/queue/{item_id}` | Review item details | Yes |
| POST | `/api/v1/review/queue/{item_id}/decision` | Submit decision | Admin |
| GET | `/api/v1/review/stats` | Review statistics | Yes |
| GET | `/api/v1/review/dashboard` | Dashboard summary | Yes |

**Endpoints:** 50+ | **Swagger:** `http://localhost:8101/docs`

**RabbitMQ:** Publishes `article.scraped`, `analysis.v3.request` | Consumes `analysis.completed`, `analysis.v3.completed`

---

### 3.3 search-service (Port 8106)

**Purpose:** Full-text search, semantic search, saved searches, entity graph integration

#### Search

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/search` | Full-text search | No |
| POST | `/api/v1/search/advanced` | Advanced search (AND/OR/phrase) | No |
| GET | `/api/v1/search/suggest` | Autocomplete suggestions | No |

#### Semantic Search

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/search/semantic` | Semantic similarity search | No |
| POST | `/api/v1/search/entities/enrich` | Entity enrichment | No |
| GET | `/api/v1/search/entities/{entity_id}/connections` | Entity relationships (Neo4j) | No |
| GET | `/api/v1/search/entities/{entity_id}/paths` | Entity connection paths | No |
| GET | `/api/v1/search/articles/{article_id}/entities` | Article entities | No |

#### Saved Searches

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/search/saved` | Create saved search | Yes |
| GET | `/api/v1/search/saved` | List saved searches | Yes |
| GET | `/api/v1/search/saved/{search_id}` | Get saved search | Yes |
| PUT | `/api/v1/search/saved/{search_id}` | Update saved search | Yes |
| DELETE | `/api/v1/search/saved/{search_id}` | Delete saved search | Yes |
| POST | `/api/v1/search/saved/{search_id}/execute` | Execute saved search | Yes |

#### Search History

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/search/history` | Get search history | Yes |
| DELETE | `/api/v1/search/history` | Clear history | Yes |

#### Admin

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/admin/reindex` | Reindex all articles | Admin |
| POST | `/api/v1/admin/sync` | Sync new articles | Admin |
| GET | `/api/v1/admin/stats/index` | Index statistics | No |
| GET | `/api/v1/admin/stats/analytics` | Search analytics | No |
| POST | `/api/v1/admin/cache/clear` | Clear cache | Admin |

**Endpoints:** 20+ | **Swagger:** `http://localhost:8106/docs`

---

### 3.4 scheduler-service (Port 8108)

**Purpose:** Feed monitoring, analysis job orchestration, cron scheduling, entity deduplication

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/scheduler/status` | Scheduler status | No |
| GET | `/api/v1/scheduler/jobs/stats` | Job queue statistics | No |
| GET | `/api/v1/scheduler/jobs` | List jobs (filter by status) | No |
| POST | `/api/v1/scheduler/feeds/{feed_id}/check` | Force feed check | Service |
| POST | `/api/v1/scheduler/jobs/{job_id}/retry` | Retry failed job | Service |
| POST | `/api/v1/scheduler/jobs/{job_id}/cancel` | Cancel job | Service |
| GET | `/api/v1/scheduler/cron/jobs` | List cron jobs | No |
| POST | `/api/v1/scheduler/neo4j/entities/deduplicate` | Entity dedup | No |

**Background Jobs:** Feed monitor (60s), Job processor (30s), Entity KG processor (30s), Entity dedup (daily 3AM), Proposal auto-approver (5min)

**Endpoints:** 9 | **Swagger:** `http://localhost:8108/docs`

---

## 4. Analysis & Intelligence Services

### 4.1 content-analysis-v3 (Port 8117)

**Purpose:** 4-tier AI content analysis pipeline (Triage → Foundation → Specialist → Intelligence)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/analyze` | Submit article for analysis | Yes |
| GET | `/api/v1/status/{article_id}` | Analysis status | Optional |
| GET | `/api/v1/results/{article_id}` | Complete results (all tiers) | Yes |
| GET | `/api/v1/results/{article_id}/tier0` | Tier 0: Triage results | Yes |
| GET | `/api/v1/results/{article_id}/tier1` | Tier 1: Foundation results | Yes |
| GET | `/api/v1/results/{article_id}/tier2` | Tier 2: Specialist results | Yes |
| GET | `/health/detailed` | Detailed health (DB, providers) | No |
| GET | `/health/ready` | Readiness probe | No |
| GET | `/health/live` | Liveness probe | No |

**Endpoints:** 10 | **Swagger:** `http://localhost:8117/docs`

**RabbitMQ:** Publishes `analysis.v3.completed`, `analysis.v3.failed`, `narrative.frame.detected`

---

### 4.2 intelligence-service (Port 8118)

**Purpose:** Risk scoring, event detection, cluster analytics, intelligence overview

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/intelligence/overview` | Dashboard stats (global risk, top clusters) | No |
| GET | `/api/v1/intelligence/events/latest` | Latest events (last N hours) | No |
| POST | `/api/v1/intelligence/events/detect` | Detect events from text | No |
| POST | `/api/v1/intelligence/risk/calculate` | Calculate risk score (0-100) | No |
| GET | `/api/v1/intelligence/clusters` | List intelligence clusters | No |
| GET | `/api/v1/intelligence/clusters/{cluster_id}` | Cluster details | No |
| GET | `/api/v1/intelligence/clusters/{cluster_id}/events` | Cluster events | No |
| GET | `/api/v1/intelligence/subcategories` | Top sub-topics per category | No |
| GET | `/api/v1/intelligence/risk-history` | Historical risk scores | No |

**Endpoints:** 10 | **Swagger:** `http://localhost:8118/docs`

---

### 4.3 clustering-service (Port 8122)

**Purpose:** Real-time article clustering, burst detection, topic discovery (UMAP+HDBSCAN), semantic profiles, escalation analysis

#### Real-Time Clustering

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/clusters/articles` | Assign article to cluster | Yes |
| GET | `/api/v1/clusters` | List clusters | Yes |
| GET | `/api/v1/clusters/{cluster_id}` | Cluster details | Yes |
| GET | `/api/v1/clusters/{cluster_id}/articles` | Cluster articles | Yes |

#### Burst Detection

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/bursts` | List burst alerts | Yes |
| GET | `/api/v1/bursts/active` | Active (unacknowledged) bursts | Yes |
| GET | `/api/v1/bursts/stats` | Burst statistics | Yes |
| GET | `/api/v1/bursts/{burst_id}` | Burst details | Yes |
| POST | `/api/v1/bursts/{burst_id}/acknowledge` | Acknowledge burst | Yes |
| GET | `/api/v1/bursts/cluster/{cluster_id}` | Burst history for cluster | Yes |

#### Topic Discovery (Batch)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/topics` | List topic clusters | Yes |
| GET | `/api/v1/topics/search` | Search topics (semantic/keyword) | Yes |
| GET | `/api/v1/topics/batches` | List batch runs | Yes |
| GET | `/api/v1/topics/similar/{article_id}` | Similar topics for article | Yes |
| GET | `/api/v1/topics/article/{article_id}` | Topic for article | Yes |
| GET | `/api/v1/topics/{cluster_id}` | Topic cluster details | Yes |
| POST | `/api/v1/topics/{cluster_id}/feedback` | Correct cluster label | Yes |

#### Semantic Profiles

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/profiles` | List profiles | Yes |
| POST | `/api/v1/profiles` | Create profile | Yes |
| GET | `/api/v1/profiles/{name}` | Profile details | Yes |
| PUT | `/api/v1/profiles/{name}` | Update profile | Yes |
| DELETE | `/api/v1/profiles/{name}` | Delete profile | Yes |
| GET | `/api/v1/profiles/{name}/matches` | Matching clusters | Yes |
| GET | `/api/v1/profiles/matches/all` | All profile matches | Yes |
| POST | `/api/v1/profiles/embed` | Generate embeddings | Yes |

#### Escalation

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/escalation/summary` | Aggregated escalation summary | No |
| GET | `/api/v1/escalation/clusters/{cluster_id}` | Cluster escalation data | No |

**Endpoints:** 30+ | **Swagger:** `http://localhost:8122/docs`

**RabbitMQ:** Consumes `analysis_complete` | Publishes cluster events

---

### 4.4 sitrep-service (Port 8123)

**Purpose:** Intelligence briefing generation (daily/weekly/breaking) from aggregated clusters

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/sitreps` | List SITREPs | Yes |
| GET | `/api/v1/sitreps/latest` | Latest SITREP by type | Yes |
| GET | `/api/v1/sitreps/{sitrep_id}` | SITREP details | Yes |
| POST | `/api/v1/sitreps/generate` | Generate SITREP manually | Yes |
| PATCH | `/api/v1/sitreps/{sitrep_id}/review` | Mark as reviewed | Yes |
| DELETE | `/api/v1/sitreps/{sitrep_id}` | Delete SITREP | Yes |

**Endpoints:** 6 | **Swagger:** `http://localhost:8123/docs`

**RabbitMQ:** Consumes cluster events from clustering-service

---

## 5. Knowledge & Entity Services

### 5.1 entity-canonicalization-service (Port 8112)

**Purpose:** Entity deduplication, fuzzy matching, Wikidata lookup, batch processing (Celery)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/canonicalization/canonicalize` | Single entity canonicalization | No |
| POST | `/api/v1/canonicalization/canonicalize/batch` | Batch (sync) | No |
| POST | `/api/v1/canonicalization/canonicalize/batch/async` | Batch (async, Celery) | No |
| GET | `/api/v1/canonicalization/jobs/{job_id}/status` | Job status | No |
| GET | `/api/v1/canonicalization/jobs/{job_id}/result` | Job results | No |
| GET | `/api/v1/canonicalization/aliases/{canonical_name}` | Get aliases | No |
| GET | `/api/v1/canonicalization/stats` | Statistics | No |
| GET | `/api/v1/canonicalization/stats/detailed` | Detailed statistics | No |
| GET | `/api/v1/canonicalization/stats/usage` | Alias usage stats | No |
| POST | `/api/v1/canonicalization/admin/cleanup-memory` | Memory cleanup | No |
| POST | `/api/v1/canonicalization/reprocess/start` | Start reprocessing | No |
| GET | `/api/v1/canonicalization/reprocess/status` | Reprocess status | No |
| POST | `/api/v1/canonicalization/reprocess/stop` | Stop reprocessing | No |
| GET | `/api/v1/canonicalization/reprocess/celery-status/{task_id}` | Celery task status | No |
| GET | `/api/v1/canonicalization/trends/entity-types` | Entity type trends | No |
| GET | `/api/v1/canonicalization/history/merges` | Merge history | No |
| GET | `/api/v1/canonicalization/fragmentation/report` | Fragmentation report | No |
| GET | `/api/v1/canonicalization/fragmentation/duplicates` | Potential duplicates | No |
| GET | `/api/v1/canonicalization/fragmentation/singletons` | Singleton entities | No |

**Endpoints:** 20 | **Swagger:** `http://localhost:8112/docs`

---

### 5.2 knowledge-graph-service (Port 8111)

**Purpose:** Neo4j graph queries, entity relationships, market data integration, narrative analysis

#### Core & Search

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/graph/entity/{entity_name}/connections` | Entity connections | No |
| GET | `/api/v1/graph/stats` | Graph statistics | No |
| GET | `/api/v1/graph/search` | Full-text entity search | No |
| GET | `/api/v1/graph/path/{entity1}/{entity2}` | Shortest paths | No |

#### Analytics

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/graph/analytics/top-entities` | Top entities by connections | No |
| GET | `/api/v1/graph/analytics/growth-history` | Graph growth over time | No |
| GET | `/api/v1/graph/analytics/relationship-stats` | Relationship distribution | No |
| GET | `/api/v1/graph/analytics/cross-article-coverage` | Entity coverage | No |
| GET | `/api/v1/graph/analytics/not-applicable-trends` | N/A relationship trends | No |
| GET | `/api/v1/graph/analytics/relationship-quality-trends` | Quality distribution | No |
| GET | `/api/v1/graph/stats/detailed` | Comprehensive stats | No |

#### Articles

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/graph/articles/{article_id}/entities` | Article entities | No |
| GET | `/api/v1/graph/articles/{article_id}/info` | Article info | No |

#### Markets

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/graph/markets/sync` | Sync market data from FMP | No |
| GET | `/api/v1/graph/markets` | Query MARKET nodes | No |
| GET | `/api/v1/graph/markets/{symbol}` | Market details | No |
| GET | `/api/v1/graph/markets/{symbol}/history` | Price history | No |
| GET | `/api/v1/graph/markets/stats` | Market statistics | No |

#### Narratives

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/graph/narratives/frames/{entity_name}` | Narrative frames | No |
| GET | `/api/v1/graph/narratives/distribution` | Frame type distribution | No |
| GET | `/api/v1/graph/narratives/entity-framing/{entity_name}` | Entity framing analysis | No |
| GET | `/api/v1/graph/narratives/cooccurrence` | Co-occurrence patterns | No |
| GET | `/api/v1/graph/narratives/high-tension` | High tension narratives | No |
| GET | `/api/v1/graph/narratives/stats` | Narrative statistics | No |
| GET | `/api/v1/graph/narratives/top-entities` | Top narrative entities | No |

#### Quality

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/graph/quality/disambiguation` | Disambiguation quality | No |
| GET | `/api/v1/graph/quality/integrity` | Integrity checks | No |

#### Admin

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/graph/admin/enrichment/analyze` | Enrichment analysis | Admin |
| POST | `/api/v1/graph/admin/enrichment/execute-tool` | Execute enrichment | Admin |
| GET | `/api/v1/graph/admin/enrichment/stats` | Enrichment stats | Admin |
| POST | `/api/v1/graph/admin/query/cypher` | Execute Cypher query | Admin |
| POST | `/api/v1/graph/admin/query/validate` | Validate Cypher | Admin |
| GET | `/api/v1/graph/admin/query/clauses` | Allowed clauses | No |
| GET | `/api/v1/graph/admin/query/examples` | Example queries | No |

#### Findings & History

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/graph/findings` | Ingest symbolic findings | No |
| GET | `/api/v1/graph/history/enrichments` | Enrichment history | No |
| GET | `/api/v1/graph/history/stats` | History statistics | No |

**Endpoints:** 59 | **Swagger:** `http://localhost:8111/docs`

**RabbitMQ:** Consumes relationships, market, finance intelligence, narrative events

---

### 5.3 ontology-proposals-service (Port 8109)

**Purpose:** Ontology change proposal management (CRUD + Neo4j implementation)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/ontology/proposals` | Create proposal | No |
| GET | `/api/v1/ontology/proposals` | List proposals (filter) | No |
| GET | `/api/v1/ontology/proposals/{proposal_id}` | Get proposal | No |
| PUT | `/api/v1/ontology/proposals/{proposal_id}` | Update proposal | No |
| POST | `/api/v1/ontology/proposals/{proposal_id}/implement` | Implement in Neo4j | Admin |
| GET | `/api/v1/ontology/proposals/statistics` | Proposal statistics | No |

**Endpoints:** 6 | **Swagger:** `http://localhost:8109/docs`

---

## 6. Financial & Market Services

### 6.1 fmp-service (Port 8113)

**Purpose:** Financial market data (FMP API) - quotes, OHLCV, earnings, news, macro indicators

#### Market Quotes

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/market/quotes` | Quotes by asset type | No |
| GET | `/api/v1/market/quotes/{symbol}` | Symbol quote | No |
| GET | `/api/v1/market/quotes/{symbol}/history` | Historical quotes | No |
| GET | `/api/v1/market/status` | Market hours status | No |

#### OHLCV Candles

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/market/candles/{symbol}` | OHLCV candles | No |
| GET | `/api/v1/market/candles/{symbol}/latest` | Latest candle | No |
| GET | `/api/v1/market/candles/asset-type/{asset_type}` | Candles by asset type | No |
| GET | `/api/v1/market/candles/{symbol}/timerange` | Candles in time range | No |

#### Symbol Discovery

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/market/symbols/search` | Search symbols | No |
| GET | `/api/v1/market/symbols/list` | List all symbols | No |

#### Historical Data

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/history/{symbol}` | Historical EOD data | No |
| POST | `/api/v1/history/{symbol}/backfill` | Trigger backfill | No |

#### Earnings

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/earnings/calendar` | Earnings calendar | No |
| GET | `/api/v1/earnings/{symbol}/history` | Earnings history | No |
| POST | `/api/v1/earnings/sync` | Sync earnings data | No |

#### Financial News

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/news` | Latest news (DB) | No |
| GET | `/api/v1/news/stock` | Stock news | No |
| GET | `/api/v1/news/by-symbol/{symbol}` | News by symbol | No |
| GET | `/api/v1/news/sentiment/{sentiment}` | News by sentiment | No |
| GET | `/api/v1/news/live/general` | Live general news (FMP) | No |
| GET | `/api/v1/news/live/stock` | Live stock news (FMP) | No |
| GET | `/api/v1/news/live/forex` | Live forex news (FMP) | No |
| GET | `/api/v1/news/live/crypto` | Live crypto news (FMP) | No |
| GET | `/api/v1/news/live/mergers-acquisitions` | Live M&A news (FMP) | No |
| POST | `/api/v1/news/sync` | Sync news from FMP | No |

#### Backfill Operations

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/backfill/indices` | Backfill indices | No |
| POST | `/api/v1/backfill/symbols` | Backfill symbols | No |
| POST | `/api/v1/backfill/macro-indicators` | Backfill macros | No |
| GET | `/api/v1/backfill/status` | Backfill status | No |

**Endpoints:** 30+ | **Swagger:** `http://localhost:8113/docs`

**RabbitMQ:** Publishes 18+ finance event types (company profiles, earnings, treasury yields, regime changes, etc.)

---

### 6.2 prediction-service (Port 8116)

**Purpose:** Predictive analytics, multi-horizon forecasts, trading signals, strategy backtesting

#### Features

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/features/{symbol}` | Extract features for symbol | Yes |
| GET | `/api/v1/features/geopolitical/context` | Geopolitical features | Yes |
| GET | `/api/v1/features/health` | Feature system health | Yes |

#### Trading

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/trading/positions` | Trading positions | Yes |
| POST | `/api/v1/trading/orders` | Create order | Yes |
| GET | `/api/v1/unified-trading/signals` | Unified trading signals | Yes |
| POST | `/api/v1/strategy-lab/backtest` | Run backtest | Yes |
| POST | `/api/v1/ml-lab/train` | Train ML model | Yes |
| GET | `/api/v1/paper-trading/portfolio` | Paper trading portfolio | Yes |
| POST | `/api/v1/paper-trading/orders` | Place paper trade | Yes |

#### Market Data & Signals

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/market-data/ohlc` | OHLC price data | Yes |
| GET | `/api/v1/order-flow/summary` | Order flow summary | Yes |
| GET | `/api/v1/order-flow/levels` | Order flow levels | Yes |
| GET | `/api/v1/signals` | Get prediction signals | Yes |
| POST | `/api/v1/signals` | Create signal | Yes |
| GET | `/api/v1/performance/{signal_id}` | Signal performance | Yes |
| GET | `/api/v1/analytics/consensus` | Multi-indicator consensus | Yes |

**Endpoints:** 20+ | **Swagger:** `http://localhost:8116/docs`

---

## 7. Data Acquisition Services

### 7.1 scraping-service

**Purpose:** Multi-strategy web scraping (httpx, Playwright, newspaper4k, trafilatura), priority queue, source profiles

#### Direct Scraping

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/scrape` | Scrape URL (sync) | No |
| GET | `/api/v1/scrape/test` | Service readiness test | No |

#### Priority Queue

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/queue/stats` | Queue statistics | No |
| POST | `/api/v1/queue/enqueue` | Add job to queue | No |
| GET | `/api/v1/queue/job/{job_id}` | Job status | No |
| DELETE | `/api/v1/queue/job/{job_id}` | Cancel job | No |
| POST | `/api/v1/queue/dequeue` | Dequeue next job | No |
| POST | `/api/v1/queue/complete/{job_id}` | Mark completed | No |
| POST | `/api/v1/queue/clear` | Clear pending jobs | No |
| GET | `/api/v1/queue/pending` | List pending jobs | No |

#### Source Profiles

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/sources/` | List source profiles | No |
| GET | `/api/v1/sources/statistics` | Source statistics | No |
| GET | `/api/v1/sources/lookup` | Lookup by URL | No |
| GET | `/api/v1/sources/config` | Scraping config for URL | No |
| GET | `/api/v1/sources/{domain}` | Profile by domain | No |
| PATCH | `/api/v1/sources/{domain}` | Update profile | No |
| POST | `/api/v1/sources/seed` | Seed German sources | No |
| DELETE | `/api/v1/sources/cache` | Clear cache | No |

#### Monitoring

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/monitoring/metrics` | Service metrics | No |
| GET | `/api/v1/monitoring/rate-limits/{key}` | Rate limit stats | No |
| GET | `/api/v1/monitoring/active-jobs` | Active jobs | No |
| POST | `/api/v1/monitoring/reset-stats` | Reset statistics | No |
| GET | `/api/v1/monitoring/failures/{feed_id}` | Feed failure count | No |

**Endpoints:** 22+ | **Additional routers:** `/api/v1/dlq`, `/api/v1/cache`, `/api/v1/proxy`, `/api/v1/wikipedia`

**RabbitMQ:** Publishes `scraping.item_scraped`, `scraping.failed`, `analysis.v3.request`

---

### 7.2 research-service (Port 8103)

**Purpose:** AI-powered research via Perplexity AI, templates, batch processing, cost tracking

#### Research Tasks

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/research/` | Create research task | Yes |
| GET | `/api/v1/research/{task_id}` | Get task result | Yes |
| GET | `/api/v1/research/` | List tasks | Yes |
| POST | `/api/v1/research/batch` | Batch research | Yes |
| GET | `/api/v1/research/feed/{feed_id}` | Tasks for feed | Yes |
| GET | `/api/v1/research/history` | Research history | Yes |
| GET | `/api/v1/research/stats` | Usage statistics | Yes |

#### Templates

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/templates/` | Create template | Yes |
| GET | `/api/v1/templates/` | List templates | Yes |
| GET | `/api/v1/templates/{template_id}` | Get template | Yes |
| GET | `/api/v1/templates/functions` | Specialized functions | No |
| PUT | `/api/v1/templates/{template_id}` | Update template | Yes |
| DELETE | `/api/v1/templates/{template_id}` | Delete template | Yes |
| POST | `/api/v1/templates/{template_id}/preview` | Preview template | Yes |
| POST | `/api/v1/templates/{template_id}/apply` | Apply template | Yes |

#### Research Runs

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/runs/` | Create research run | Yes |
| GET | `/api/v1/runs/{run_id}` | Get run | Yes |
| GET | `/api/v1/runs/{run_id}/status` | Run status | Yes |
| GET | `/api/v1/runs/` | List runs | Yes |
| POST | `/api/v1/runs/{run_id}/cancel` | Cancel run | Yes |
| GET | `/api/v1/runs/template/{template_id}` | Runs for template | Yes |

**Rate Limits:** Authenticated: 60 req/min, 500/hour, 5000/day | Perplexity: 10 req/min

**Cost Limits:** Per-request: $0.50 | Daily: $50 | Monthly: $500

**Endpoints:** 20+ | **Swagger:** `http://localhost:8103/docs`

---

### 7.3 mediastack-service (Port 8120)

**Purpose:** MediaStack API integration for mass URL discovery

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|-----------|
| GET | `/api/v1/news/live` | Live news | No | 10k/month |
| GET | `/api/v1/news/historical` | Historical news (PAID) | No | 10k/month |
| GET | `/api/v1/news/sources` | Available sources | No | 10k/month |
| GET | `/api/v1/news/usage` | API usage stats | No | - |

**Endpoints:** 5 | **Swagger:** `http://localhost:8120/docs`

---

## 8. Analytics & Monitoring

### 8.1 analytics-service (Port 8107)

**Purpose:** Metrics aggregation, dashboards, reports, intelligence signals (bursts, momentum, contrarian alerts), RAG-powered Q&A

#### Core Analytics

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/analytics/overview` | System-wide overview | Yes |
| GET | `/api/v1/analytics/trends` | Metric trends | Yes |
| GET | `/api/v1/analytics/service/{service_name}` | Service metrics | Yes |
| POST | `/api/v1/analytics/metrics` | Store metric | Yes |

#### Dashboards

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/dashboards` | Create dashboard | Yes |
| GET | `/api/v1/dashboards` | List dashboards | Optional |
| GET | `/api/v1/dashboards/{id}` | Get dashboard | Optional |
| GET | `/api/v1/dashboards/{id}/data` | Dashboard with live data | Optional |
| PUT | `/api/v1/dashboards/{id}` | Update dashboard | Yes |
| DELETE | `/api/v1/dashboards/{id}` | Delete dashboard | Yes |
| WS | `/api/v1/dashboards/{id}/ws` | Real-time WebSocket | No |

#### Reports

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/reports` | Create report | Yes |
| GET | `/api/v1/reports` | List reports | Yes |
| GET | `/api/v1/reports/{report_id}` | Get report | Yes |
| GET | `/api/v1/reports/{report_id}/download` | Download (CSV/JSON/MD) | Yes |

#### Intelligence Signals

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/intelligence/top-stories` | Top stories with signal decay | Yes |
| GET | `/api/v1/intelligence/bursts` | Entity mention bursts (Kleinberg) | Yes |
| GET | `/api/v1/intelligence/momentum` | Sentiment momentum | Yes |
| GET | `/api/v1/intelligence/contrarian-alerts` | Extreme sentiment detection | Yes |
| POST | `/api/v1/intelligence/novelty` | Article novelty score | Yes |
| GET | `/api/v1/intelligence/novelty/stats` | Novelty cache stats | Yes |
| GET | `/api/v1/intelligence/entity-sentiment-history` | Entity sentiment timeseries | No |
| GET | `/api/v1/intelligence/summary` | Combined intelligence summary | Yes |
| GET | `/api/v1/intelligence/ask` | RAG-powered Q&A | No |
| GET | `/api/v1/intelligence/context` | Raw intelligence context | No |

#### Monitoring

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/monitoring/circuit-breakers` | Circuit breaker status | Yes |
| GET | `/api/v1/monitoring/query-performance` | DB query performance | Yes |
| POST | `/api/v1/monitoring/query-performance/reset` | Reset query stats | Yes |
| GET | `/api/v1/monitoring/websocket` | WebSocket stats | Yes |
| GET | `/api/v1/monitoring/health` | Comprehensive health | Yes |

#### Cache

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/cache/stats` | Redis cache stats | No |
| GET | `/api/v1/cache/health` | Cache health | No |
| POST | `/api/v1/cache/clear` | Clear cache | No |

**Endpoints:** 30+ | **Swagger:** `http://localhost:8107/docs`

---

## 9. Narrative & Geolocation Services

### 9.1 narrative-service (Port 8119)

**Purpose:** Narrative frame detection, bias analysis, propaganda detection

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/narrative/analyze/text` | Analyze text for frames & bias | Yes |
| GET | `/api/v1/narrative/overview` | Overview statistics | Yes |
| GET | `/api/v1/narrative/frames` | List narrative frames | Yes |
| POST | `/api/v1/narrative/frames` | Create frame | Yes |
| GET | `/api/v1/narrative/clusters` | List narrative clusters | Yes |
| POST | `/api/v1/narrative/clusters/update` | Update clusters | Yes |
| GET | `/api/v1/narrative/bias` | Bias comparison across sources | Yes |
| GET | `/api/v1/narrative/cache/stats` | Cache statistics | Yes |
| POST | `/api/v1/narrative/cache/clear` | Clear cache | Yes |

**Endpoints:** 11 | **RabbitMQ:** Consumes `narrative.frame.detected`

---

### 9.2 narrative-intelligence-gateway (Port 8114)

**Purpose:** Unified API gateway for narrative analysis (proxies to knowledge-graph-service)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/narratives/stats` | Narrative statistics | No |
| GET | `/api/v1/narratives/distribution` | Frame type distribution | No |
| GET | `/api/v1/narratives/high-tension` | High tension narratives | No |
| GET | `/api/v1/narratives/top-entities` | Top entities | No |
| GET | `/api/v1/entity/{entity_name}` | Entity narratives | No |
| GET | `/api/v1/entity/{entity_name}/framing` | Entity framing analysis | No |
| GET | `/api/v1/entity/{entity_name}/history` | Entity tension history | No |
| GET | `/api/v1/cooccurrence` | Entity co-occurrence | No |
| GET | `/api/v1/dashboard/overview` | Dashboard data | No |
| POST | `/api/v1/webhooks/subscribe` | Register webhook | No |
| GET | `/api/v1/webhooks` | List webhooks | No |
| DELETE | `/api/v1/webhooks/{webhook_id}` | Remove webhook | No |

**Endpoints:** 14

---

### 9.3 geolocation-service (Port 8115)

**Purpose:** Geographic visualization, security events, threat monitoring, watchlists

#### Map & Countries

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/geo/countries` | Countries with statistics | No |
| GET | `/api/v1/geo/countries/{iso_code}` | Country details | No |
| GET | `/api/v1/geo/countries/{iso_code}/articles` | Country articles | No |
| GET | `/api/v1/geo/map/countries` | GeoJSON FeatureCollection | No |
| GET | `/api/v1/geo/map/markers` | Article markers | No |
| GET | `/api/v1/geo/map/heatmap` | Heatmap data | No |
| GET | `/api/v1/geo/filters/regions` | Available regions | No |
| GET | `/api/v1/geo/filters/categories` | Categories with counts | No |

#### Security View

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/geo/security/overview` | Global security overview | No |
| GET | `/api/v1/geo/security/events` | Paginated security events | No |
| GET | `/api/v1/geo/security/countries` | Threat data per country | No |
| GET | `/api/v1/geo/security/country/{iso_code}` | Country threat profile | No |
| GET | `/api/v1/geo/security/markers` | Security markers | No |
| GET | `/api/v1/geo/security/anomalies` | Anomaly detection | No |
| GET | `/api/v1/geo/security/entity-graph` | Entity relationship graph | No |

#### Watchlist

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/geo/watchlist` | Watchlist items | No |
| POST | `/api/v1/geo/watchlist` | Add item | No |
| DELETE | `/api/v1/geo/watchlist/{item_id}` | Remove item | No |
| GET | `/api/v1/geo/watchlist/alerts` | Watchlist alerts | No |
| POST | `/api/v1/geo/watchlist/alerts/read` | Mark alerts read | No |
| GET | `/api/v1/geo/watchlist/stats` | Alert statistics | No |

**Endpoints:** 30+ | **Swagger:** `http://localhost:8115/docs`

---

## 10. Auxiliary Services

### 10.1 oss-service (Port 8109)

**Purpose:** Ontology Suggestion System - analyzes Neo4j knowledge graph to suggest improvements

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|-----------|
| POST | `/api/v1/analysis/run` | Trigger analysis cycle | No | 5/min |
| GET | `/api/v1/analysis/status` | Service status | No | 60/min |
| GET | `/api/v1/analysis/deduplication/stats` | Dedup cache stats | No | 60/min |
| POST | `/api/v1/analysis/deduplication/clear` | Clear dedup cache | No | 5/min |
| GET | `/api/v1/analysis/queue/status` | Retry queue status | No | 60/min |
| POST | `/api/v1/analysis/queue/retry` | Trigger retry | No | 5/min |
| GET | `/api/v1/analysis/queue/failed` | Failed proposals | No | 60/min |
| POST | `/api/v1/analysis/queue/clear` | Clear retry queue | No | 5/min |

**Endpoints:** 10

---

### 10.2 llm-orchestrator-service (Port 8121)

**Purpose:** DIA (Dynamic Intelligence Augmentation) orchestration - primarily event-driven

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Health check | No |
| GET | `/health/ready` | Readiness check | No |

**Endpoints:** 4 (minimal REST, mainly RabbitMQ consumer)

**RabbitMQ:** Consumes `verification.required`

---

### 10.3 nexus-agent (Port 8124)

**Purpose:** AI Co-Pilot for the platform with memory persistence

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/chat` | Process chat message | No |
| POST | `/api/v1/chat/confirm` | Confirm execution plan | No |
| GET | `/api/v1/memory/search` | Semantic memory search | No |
| POST | `/api/v1/memory/facts` | Add fact to memory | No |
| GET | `/api/v1/memory/stats` | Memory statistics | No |

**Endpoints:** 6

---

## 11. MCP Server Layer

The MCP (Model Context Protocol) servers provide a unified tool interface for AI agents. Each server wraps one or more backend services.

| MCP Server | Port | Backend Services | Tools | Key Capabilities |
|------------|------|------------------|-------|-------------------|
| **mcp-core-server** | 8100 | Auth, Analytics | 40+ | Auth, dashboards, discovery, system context |
| **mcp-content-server** | 8101 | Feed | 62+ | Feed CRUD, quality, Admiralty codes, scheduling |
| **mcp-search-server** | 8106 | Search, Feed, Research | 21+ | Full-text, semantic, saved searches, research |
| **mcp-analytics-server** | 8107 | Analytics, Prediction | 32 | Metrics, prediction, execution, model drift |
| **mcp-orchestration-server** | 8108 | Scheduler, MediaStack, Scraping | 50+ | Jobs, news, scraping, DLQ, proxy, Wikipedia |
| **mcp-intelligence-server** | 9001 | Content Analysis, Entity, Intel | Dynamic | Analysis, canonicalization, risk, narratives |
| **mcp-integration-server** | 8113 | FMP, Research, Notification | 50+ | Market data, earnings, macros, notifications |
| **mcp-knowledge-graph** | 8111 | Knowledge Graph (Neo4j) | 24 | Entity graph, narratives, markets, quality |

**Total MCP Tools: ~270+**

### MCP Protocol Convention

All MCP servers implement:
- `GET /mcp/tools/list` - List available tools
- `POST /mcp/tools/call` - Execute tool
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

---

## 12. Event-Driven Architecture (RabbitMQ)

### Key Event Flows

```
Article Ingestion:
  feed-service → article.scraped → scraping-service
  scraping-service → scraping.item_scraped → feed-service
  feed-service → analysis.v3.request → content-analysis-v3

Analysis Pipeline:
  content-analysis-v3 → analysis.v3.completed → feed-service
  content-analysis-v3 → analysis.v3.completed → clustering-service
  content-analysis-v3 → narrative.frame.detected → narrative-service

Intelligence:
  clustering-service → cluster.created/updated → intelligence-service
  clustering-service → cluster.burst_detected → sitrep-service

Financial:
  fmp-service → finance.*.updated → knowledge-graph-service (18+ event types)

Knowledge Graph:
  scheduler-service → entity relationships → knowledge-graph-service
```

### Event Categories

| Category | Events | Publishers | Consumers |
|----------|--------|------------|-----------|
| Article lifecycle | `article.scraped`, `article.analyzed` | feed, scraping | search, clustering |
| Analysis | `analysis.v3.completed/failed` | content-analysis-v3 | feed, clustering |
| Narrative | `narrative.frame.detected` | content-analysis-v3 | narrative-service |
| Clustering | `cluster.created/updated/burst_detected` | clustering | intelligence, sitrep |
| Finance | `finance.*` (18+ types) | fmp-service | knowledge-graph |
| Verification | `verification.required` | various | llm-orchestrator |

---

## 13. Cross-Cutting Concerns

### Pagination

Two patterns used across services:

```
Pattern A (offset-based): ?skip=0&limit=50
Pattern B (page-based):   ?page=1&page_size=50
```

### Error Response Format

```json
{
  "detail": "Error description",
  "status_code": 422
}
```

### Common Query Parameters

| Parameter | Services | Description |
|-----------|----------|-------------|
| `skip` / `offset` | Most | Pagination offset |
| `limit` / `page_size` | Most | Items per page (max varies: 50-1000) |
| `sort_by` / `order` | feed, search | Sort field and direction |
| `date_from` / `date_to` | feed, search, fmp | Date range filtering |
| `hours` / `days` | intelligence, clustering, analytics | Time window |

### Performance Characteristics

| Service | Avg Response | Cache |
|---------|-------------|-------|
| feed-service (reads) | 4-5ms | Redis |
| search (cached) | 10-50ms | Redis |
| search (uncached) | 50-200ms | - |
| narrative (cached) | 3-5ms | Redis |
| narrative (cold) | 150ms | - |
| research (Perplexity) | 2-10s | - |
| content-analysis-v3 | Async | - |
| intelligence | 50-200ms | - |

### Swagger UI Access

All services expose interactive API documentation:

```
http://localhost:{port}/docs     (Swagger UI)
http://localhost:{port}/redoc    (ReDoc)
http://localhost:{port}/openapi.json  (OpenAPI spec)
```

---

*Generated: 2026-02-09 | Source: Codebase analysis of all active services*

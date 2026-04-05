# News MCP — Modular News Intelligence Platform

![Services](https://img.shields.io/badge/services-34-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

A production-grade news intelligence platform that ingests RSS/Atom feeds, runs them through a multi-stage AI analysis pipeline, resolves and deduplicates entities against Wikidata, builds a knowledge graph, clusters stories in real-time, detects narratives and bias, and produces automated intelligence briefings — all as independently deployable microservices connected via RabbitMQ.

---

## Architecture

### Service Map

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INGESTION LAYER                                    │
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ feed-service │  │  scraping-   │  │  mediastack- │  │  research-   │       │
│  │    :8101     │  │   service    │  │   service    │  │   service    │       │
│  │  RSS/Atom    │  │  Headless    │  │  :8120       │  │    :8103     │       │
│  │  61+ feeds   │  │  Browser     │  │  News API    │  │  Perplexity  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         └──────────────────┴─────────────────┴─────────────────┘               │
│                                     │                                           │
│                                     ▼                                           │
│                        ┌────────────────────────┐                               │
│                        │   RabbitMQ Event Bus   │                               │
│                        │   12 Exchanges          │                               │
│                        └───────────┬────────────┘                               │
│                                    │                                            │
├────────────────────────────────────┼────────────────────────────────────────────┤
│                           ANALYSIS LAYER                                        │
│                                    │                                            │
│    ┌───────────────────────────────┼───────────────────────────────┐            │
│    ▼                               ▼                               ▼            │
│  ┌──────────────┐  ┌──────────────────────┐  ┌──────────────┐                  │
│  │content-      │  │ entity-              │  │ narrative-   │                  │
│  │analysis-v3   │  │ canonicalization     │  │ service      │                  │
│  │   :8117      │  │       :8112          │  │    :8119     │                  │
│  │ 4-Tier AI    │  │ 5-Stage Dedup       │  │ Frame/Bias   │                  │
│  │ Triage→Spec  │  │ Wikidata            │  │ Propaganda   │                  │
│  └──────┬───────┘  └──────────┬───────────┘  └──────┬───────┘                  │
│         └──────────────────────┼──────────────────────┘                          │
│                                ▼                                                │
├────────────────────────────────┼────────────────────────────────────────────────┤
│                       INTELLIGENCE LAYER                                        │
│                                │                                                │
│  ┌──────────────┐  ┌──────────┴───┐  ┌──────────────┐  ┌──────────────┐       │
│  │ intelligence │  │ clustering-  │  │   sitrep-    │  │  knowledge-  │       │
│  │   service    │  │  service     │  │   service    │  │  graph       │       │
│  │    :8118     │  │    :8122     │  │    :8123     │  │    :8111     │       │
│  │ Risk/Events  │  │ UMAP+HDBSCAN│  │ AI Briefings │  │   Neo4j     │       │
│  │ Overview     │  │ Burst Detect │  │ Daily/Weekly │  │ Entity Rels  │       │
│  └──────────────┘  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                          PLATFORM LAYER                                         │
│                                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │  auth    │ │ search   │ │analytics │ │scheduler │ │  osint   │ │  llm-  │ │
│  │  :8100   │ │  :8106   │ │  :8107   │ │  :8108   │ │  :8104   │ │  orch  │ │
│  │ JWT/RBAC │ │ FT+Sem   │ │ Trends   │ │ 40+ Cron │ │ 50+ Tpl  │ │ :8121  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │   fmp    │ │prediction│ │ ontology │ │  geoloc  │ │    8 MCP Servers   │  │
│  │  :8113   │ │  :8116   │ │  :8109   │ │  :8115   │ │   :9001-9008      │  │
│  │ Markets  │ │ Signals  │ │ Schema   │ │ GeoResolv│ │   200+ AI Tools   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────────────────┘  │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              DATA LAYER                                         │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐          │
│  │   PostgreSQL     │  │    Neo4j     │  │  Redis   │  │   n8n    │          │
│  │   80+ tables     │  │   Graph DB   │  │  Cache   │  │  :5678   │          │
│  │  Shared Schema   │  │  Entities    │  │  :6379   │  │ Workflows│          │
│  └──────────────────┘  └──────────────┘  └──────────┘  └──────────┘          │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────────────┐         │
│  │   Prometheus     │  │   Grafana    │  │   React Frontend :3000  │         │
│  │    Metrics       │  │  Dashboards  │  │   KG Admin, Trading UI  │         │
│  └──────────────────┘  └──────────────┘  └──────────────────────────┘         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Platform Overview

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

### Intelligence Pipeline

```
                           ┌─────────────────────────────────────────────────┐
                           │              News MCP Platform                  │
                           └─────────────────────────────────────────────────┘

  ┌──────────┐    ┌──────────────┐    ┌─────────────────────┐    ┌───────────────────┐
  │ RSS/Atom │───►│ Feed Service │───►│  Triage (Tier 0)    │───►│ Foundation (T1)   │
  │ 61+ Feeds│    │ Circuit Break│    │  Keep/Discard       │    │ Entities, Topics  │
  │          │    │ Celery Workers│    │  Priority 0-10      │    │ Impact, Urgency   │
  └──────────┘    │ Dedup (SHA256)│    │  60% filtered out   │    └────────┬──────────┘
                  └──────────────┘    └─────────────────────┘             │
       ┌──────────────────────────────────────────────────────────────────┘
       │
       ▼
  ┌─────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
  │ Specialist (Tier 2) │───►│ Entity Canonicalize  │───►│ Knowledge Graph      │
  │ 6 Analysis Modules  │    │ 5-Stage Pipeline     │    │ Neo4j                │
  │ Weighted Budgets    │    │ Fuzzy + Semantic      │    │ Entity Relations     │
  │ 94.5% token savings │    │ Wikidata Enrichment   │    │ Analytics APIs       │
  └─────────────────────┘    └──────────────────────┘    └──────────────────────┘
       │
       ▼
  ┌─────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
  │ Clustering          │───►│ Narrative Analysis   │───►│ SITREP Generator     │
  │ Single-Pass (O(n))  │    │ Frame Detection      │    │ GPT-4 Briefings      │
  │ UMAP + HDBSCAN      │    │ Bias Scoring         │    │ Daily + On-Demand    │
  │ Burst Detection     │    │ Propaganda Detection │    │ Risk Assessments     │
  └─────────────────────┘    └──────────────────────┘    └──────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────────┐
  │                         RabbitMQ Event Bus (12 Exchanges)                    │
  │     PostgreSQL (80+ tables)  │  Neo4j (Graph)  │  Redis (Cache)             │
  └──────────────────────────────────────────────────────────────────────────────┘
```

## Key Features

### Feed Management & Ingestion
- **RSS/Atom Feed Manager** — Full CRUD for 61+ feeds with health monitoring, quality scoring, and scheduling optimization
- **Source Assessment** — Admiralty Code System (A-F reliability rating) with configurable thresholds and credibility scoring
- **Intelligent Scheduling** — Per-feed fetch intervals with circuit breakers, exponential backoff, and schedule optimization
- **Content Deduplication** — SHA-256 hash dedup + near-duplicate detection with HITL (Human-in-the-Loop) review queue
- **Full-Content Scraping** — Headless browser extraction for truncated or paywalled articles via scraping-service
- **Dead Letter Queue** — Failed messages preserved for investigation and replay
- **MediaStack Integration** — Alternative news source via MediaStack API with n8n workflows

### AI Analysis Pipeline (4-Tier Progressive)
- **Tier 0 — Triage** (~800 tokens) — Fast keep/discard decision, priority scoring 0-10, filters ~60% of noise
- **Tier 1 — Foundation** (~2,000 tokens) — Core entity/relation/topic extraction, impact/credibility/urgency scoring
- **Tier 2 — Specialist** (~8,000 tokens) — 6 specialized analysis modules with weighted budget allocation, 94.5% token savings on irrelevant content via quick checks
- **Tier 3 — Intelligence** (planned) — Event timeline construction, cross-article synthesis
- **Multi-LLM Support** — Pluggable providers: OpenAI (GPT-4o-mini default), Anthropic (Claude), Ollama (local)
- **96.7% Cost Reduction** — V3 pipeline costs $0.00028/article vs $0.0085 in V2

### Entity Resolution & Knowledge Graph
- **5-Stage Canonicalization** — Exact match → fuzzy matching → semantic similarity → Wikidata enrichment → batch reprocessing
- **Wikidata Integration** — Automated entity linking and metadata enrichment
- **Neo4j Knowledge Graph** — Entity relationships with automated ingestion from analysis pipeline
- **Ontology Proposals** — OSS (Ontology Suggestion System) for schema evolution with proposal/review workflow

### Intelligence & Clustering
- **Risk Scoring & Event Detection** — Real-time global risk calculation (0-100), automated event detection from text, intelligence overview dashboard
- **Dual-Mode Clustering** — Single-pass O(n) for real-time article grouping + UMAP/HDBSCAN batch for semantic topic discovery
- **Burst Detection** — Automatic breaking news identification based on growth rate (Welford's algorithm), with acknowledge/dismiss workflow
- **Semantic Profiles** — Custom topic profiles with embedding-based matching against live clusters
- **Escalation Analysis** — Aggregated escalation summaries across clusters
- **21,000+ Active Clusters** — Story groupings with time-decay ranking

### Narrative Intelligence
- **Frame Detection** — Identifies narrative frames per article: victim, hero, threat, solution, conflict, economic
- **Political Bias Scoring** — Left-to-right spectrum analysis with confidence scores
- **Propaganda Detection** — Automated propaganda pattern identification
- **Narrative Gateway** — Aggregation layer across narrative analysis results
- **SITREP Generation** — AI-powered situation reports (daily/weekly/breaking) with key developments, risk assessments, and sentiment analysis

### OSINT & Research
- **OSINT Service** — 50+ investigation templates, APScheduler-driven monitoring, anomaly detection hooks
- **Research Automation** — Perplexity AI integration with templates and cost tracking
- **LLM Orchestrator** — DIA (Dynamic Intelligence Augmentation) with two-stage planning for AI-powered verification
- **Geolocation Extraction** — Geographic entity resolution and mapping from article content

### Search & Analytics
- **Full-Text + Semantic Search** — Real-time indexing, advanced queries (AND/OR/phrase), semantic similarity via embeddings, autocomplete
- **Saved Searches** — Persistent search configurations with scheduled execution
- **Entity Graph Search** — Neo4j-backed entity connections, relationship paths, article-entity linking
- **Analytics Service** — Trend analytics, intelligence signals, dashboard metrics, production-optimized queries
- **Search History** — Per-user search history with management API

### Financial & Predictive Analytics
- **FMP Service** — Financial Modeling Prep integration: macro indicators, market indices, sector data for context enrichment
- **Prediction Service** — Predictive analytics engine with trading signals, consensus predictions, strategy backtesting
- **Strategy Lab** — Frontend for exploring and debugging prediction strategies

### Alerts & Delivery
- **Telegram Alerts** — High-tension narrative alerts, breaking news bursts, SITREP delivery via n8n → Telegram Bot
- **Multi-Channel** — Telegram, Slack, Discord, Email, Webhooks — all via n8n native integrations

### Workflow Automation
- **n8n Integration** — Visual workflow engine for feed orchestration, content pipelines, alert routing, and scheduled jobs
- **MediaStack Workflows** — Automated news discovery via n8n → MediaStack API → feed ingestion

### Platform & Integration
- **8 MCP Servers** — 200+ tools via Model Context Protocol for AI agent integration (intelligence, search, analytics, knowledge graph, content, core, integration, orchestration)
- **React Frontend** — Knowledge graph admin, entity management, trading signals, strategy debugger
- **Auth & RBAC** — JWT access/refresh tokens, API keys, per-service secrets, role-based access
- **Nexus Agent** — Autonomous agent for cross-service orchestration
- **Observability** — Prometheus metrics on every service, Grafana dashboards, Loki log aggregation

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Celery, SQLAlchemy 2.0 |
| Frontend | React 18, TypeScript, Vite |
| Database | PostgreSQL (80+ tables), Neo4j (Knowledge Graph) |
| Messaging | RabbitMQ (12 exchanges, event-driven) |
| Cache | Redis |
| AI/ML | OpenAI, Anthropic, Ollama, Perplexity, UMAP, HDBSCAN |
| Workflow Automation | n8n (visual workflow engine) |
| Orchestration | Docker Compose, Kubernetes (Tilt) |
| Monitoring | Prometheus, Grafana, Loki |

## Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| **Core** | | |
| auth-service | 8100 | JWT auth, API keys, RBAC, key rotation |
| feed-service | 8101 | RSS/Atom feed management, ingestion, HITL review, Admiralty codes |
| search-service | 8106 | Full-text + semantic search, saved searches, entity graph queries |
| scheduler-service | 8108 | Cron jobs, feed monitoring, entity dedup scheduling |
| **Analysis & Intelligence** | | |
| content-analysis-v3 | 8117 | 4-tier AI analysis pipeline (triage → foundation → specialist) |
| intelligence-service | 8118 | Risk scoring, event detection, intelligence overview |
| clustering-service | 8122 | Dual-mode clustering, burst detection, semantic profiles, escalation |
| sitrep-service | 8123 | AI-generated intelligence briefings (daily/weekly/breaking) |
| **Knowledge & Entities** | | |
| entity-canonicalization | 8112 | 5-stage entity dedup, fuzzy matching, Wikidata, batch processing |
| knowledge-graph | 8111 | Neo4j entity graph, analytics APIs, manual enrichment |
| ontology-proposals | 8109 | Schema evolution proposals + review workflow |
| oss-service | 8110 | Ontology Suggestion System |
| **Financial & Predictive** | | |
| fmp-service | 8113 | Financial Modeling Prep: macro indicators, market data |
| prediction-service | 8116 | Predictive analytics, trading signals, consensus |
| **Narrative & Geolocation** | | |
| narrative-service | 8119 | Frame detection, bias analysis, propaganda detection |
| narrative-intel-gateway | 8114 | Narrative analysis aggregation |
| geolocation-service | 8115 | Geographic entity resolution + visualization |
| **Data Acquisition** | | |
| scraping-service | — | Headless browser full-content extraction |
| research-service | 8103 | Perplexity AI research automation |
| mediastack-service | 8120 | MediaStack news API wrapper |
| **Analytics & Monitoring** | | |
| analytics-service | 8107 | Trend analytics, dashboards, intelligence signals |
| **Orchestration & Agents** | | |
| llm-orchestrator | 8121 | Multi-LLM orchestration, DIA verification |
| nexus-agent | 8124 | Autonomous AI co-pilot for cross-service tasks |
| osint-service | 8104 | 50+ OSINT investigation templates, anomaly monitoring |
| **MCP Servers** | 9001-9008 | 8 servers, 200+ tools for AI agent integration |

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

### Quick Start

```bash
git clone https://github.com/CytrexSGR/news-microservices.git
cd news-microservices
cp .env.example .env    # Add your API keys
docker compose up --build
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required for content analysis (pick one or more)
OPENAI_API_KEY=sk-...           # GPT-4o-mini for triage + analysis
ANTHROPIC_API_KEY=sk-ant-...    # optional, multi-provider support
# Or use Ollama for fully local LLMs (no API key needed)

# Optional integrations
PERPLEXITY_API_KEY=pplx-...     # for research automation
FMP_API_KEY=...                 # for financial market data

# Database (defaults work with Docker Compose)
DATABASE_URL=postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Auth API | http://localhost:8100 |
| Feed API | http://localhost:8101 |
| Content Analysis | http://localhost:8117 |
| Knowledge Graph | http://localhost:8111 |
| Search | http://localhost:8106 |
| Analytics | http://localhost:8107 |
| RabbitMQ Management | http://localhost:15672 |
| Neo4j Browser | http://localhost:7474 |
| n8n Workflow Editor | http://localhost:5678 |

## Project Structure

```
news-microservices/
├── services/                   # 30 FastAPI microservices
│   ├── feed-service/           #   RSS/Atom ingestion + management
│   ├── content-analysis-v3/    #   4-tier AI analysis pipeline
│   ├── entity-canonicalization-service/  # 5-stage entity dedup
│   ├── knowledge-graph-service/#   Neo4j graph + analytics
│   ├── clustering-service/     #   UMAP/HDBSCAN + real-time clustering
│   ├── narrative-service/      #   Frame, bias, propaganda detection
│   ├── sitrep-service/         #   AI intelligence briefings
│   ├── search-service/         #   Full-text search + indexing
│   ├── analytics-service/      #   Trend analytics + metrics
│   ├── research-service/       #   Perplexity AI integration
│   ├── osint-service/          #   OSINT monitoring + templates
│   ├── auth-service/           #   JWT auth, API keys, RBAC
│   ├── mcp-*-server/ (x8)     #   Model Context Protocol servers
│   └── ...                     #   + scheduler, scraping, notifications, etc.
├── frontend/                   # React 18 + Vite + TypeScript
├── shared/                     # Shared packages (auth, events, DB helpers)
├── gateway/                    # API gateway configuration
├── k8s/                        # Kubernetes manifests + Tilt
├── monitoring/                 # Prometheus, Grafana, Loki configs
├── scripts/                    # Maintenance, backfill, migration scripts
├── tests/                      # Cross-service integration + e2e tests
├── docker-compose.yml          # Full stack (57 containers)
├── Makefile                    # lint, test, build, deploy
└── Tiltfile                    # Live-reload K8s development
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Full system architecture, data flows, database schema
- **[docs/guides/](docs/guides/)** — Deployment, security, scaling, backup guides
- **[docs/services/](docs/services/)** — Per-service documentation
- **[docs/api/](docs/api/)** — API references
- **[docs/architecture/](docs/architecture/)** — Design decisions, event-driven patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run linting & tests: `make lint && make test`
4. Submit a pull request

See individual service READMEs for service-specific development instructions.

## License

**Dual Licensed:**
- **AGPL v3** — Open source, copyleft. If you run this as a service, you must publish your modifications.
- **Commercial License** — For proprietary use without AGPL obligations, [contact CytrexSGR](https://github.com/CytrexSGR).

See [LICENSE](LICENSE) for details.

---

## Authors

**Andreas** — Architecture, Design, Direction
**[Claude Code](https://claude.ai/code)** (Anthropic) — Implementation Partner

> This project was built using vibe coding — human vision and AI implementation working as equals.

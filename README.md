# News MCP — Modular News Intelligence Platform

![Services](https://img.shields.io/badge/services-34-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![License](https://img.shields.io/badge/License-MIT-green)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

A production-grade news intelligence platform that ingests RSS/Atom feeds, runs them through a multi-stage AI analysis pipeline, resolves and deduplicates entities against Wikidata, builds a knowledge graph, clusters stories in real-time, detects narratives and bias, and produces automated intelligence briefings — all as independently deployable microservices connected via RabbitMQ.

---

## Architecture

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
- **RSS/Atom Feed Manager** — CRUD for 61+ feeds with health monitoring and quality scoring
- **Intelligent Scheduling** — Per-feed fetch intervals with circuit breakers and exponential backoff
- **Content Deduplication** — SHA-256 based dedup to prevent duplicate article processing
- **Full-Content Scraping** — Headless browser extraction for truncated or paywalled articles
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
- **Dual-Mode Clustering** — Single-pass O(n) for real-time + UMAP/HDBSCAN batch for topic discovery
- **Burst Detection** — Automatic breaking news identification based on growth rate (Welford's algorithm)
- **21,000+ Active Clusters** — Story groupings with time-decay ranking
- **Narrative Detection** — Frame analysis (victim/hero/threat/solution/conflict/economic), political bias scoring, propaganda detection
- **SITREP Generation** — AI-powered situation reports with key developments, risk assessments, and sentiment analysis

### OSINT & Research
- **OSINT Service** — 50+ investigation templates, APScheduler-driven monitoring, anomaly detection hooks
- **Research Automation** — Perplexity AI integration with templates and cost tracking
- **LLM Orchestrator** — DIA (Dynamic Intelligence Augmentation) with two-stage planning for AI-powered verification
- **Geolocation Extraction** — Geographic entity resolution and mapping from article content

### Search & Analytics
- **Full-Text Search** — Real-time indexing with saved searches and trend analytics
- **Analytics Service** — Metrics APIs, production-optimized queries, Alembic migrations
- **FMP Market Data** — Financial Modeling Prep integration for market context enrichment

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
| Orchestration | Docker Compose, Kubernetes (Tilt) |
| Monitoring | Prometheus, Grafana, Loki |

## Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| auth-service | 8100 | JWT auth, API keys, RBAC |
| feed-service | 8101 | RSS/Atom feed management and ingestion |
| content-analysis-v3 | 8114 | 4-tier AI analysis pipeline |
| entity-canonicalization | 8112 | 5-stage entity dedup + Wikidata |
| knowledge-graph | 8111 | Neo4j entity graph + analytics |
| intelligence-service | — | Clustering, dedup, story grouping |
| clustering-service | 8122 | UMAP/HDBSCAN + single-pass clustering |
| narrative-service | 8119 | Frame, bias, propaganda detection |
| sitrep-service | 8123 | AI-generated intelligence briefings |
| search-service | 8106 | Full-text search + saved searches |
| analytics-service | 8107 | Trend analytics + metrics |
| research-service | 8103 | Perplexity AI research automation |
| osint-service | 8104 | OSINT monitoring + investigation |
| scheduler-service | 8108 | Job scheduling for feeds + analysis |
| scraping-service | — | Headless browser content extraction |
| llm-orchestrator | 8109 | Multi-LLM orchestration + DIA |
| notification-service | 8105 | Email/webhook delivery |
| geolocation-service | — | Geographic entity resolution |
| ontology-proposals | 8109 | Schema evolution proposals |
| oss-service | 8110 | Ontology Suggestion System |
| mediastack-service | — | MediaStack news API wrapper |
| nexus-agent | — | Autonomous cross-service agent |
| narrative-intel-gateway | — | Narrative intelligence aggregation |
| mcp-\*-server (x8) | 9001-9008 | Model Context Protocol servers |

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
| Content Analysis | http://localhost:8114 |
| Knowledge Graph | http://localhost:8111 |
| Search | http://localhost:8106 |
| Analytics | http://localhost:8107 |
| RabbitMQ Management | http://localhost:15672 |
| Neo4j Browser | http://localhost:7474 |

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

MIT License — see [LICENSE](LICENSE) for details.

---

## Authors

**Andreas** — Architecture, Design, Direction
**[Claude Code](https://claude.ai/code)** (Anthropic) — Implementation Partner

> This project was built using vibe coding — human vision and AI implementation working as equals.

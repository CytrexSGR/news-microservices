# News MCP — Modular News Intelligence Platform

![Services](https://img.shields.io/badge/services-34-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![License](https://img.shields.io/badge/License-MIT-green)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

A production-grade news intelligence platform that transforms raw RSS/Atom feeds into structured, searchable intelligence through automated NLP pipelines, entity resolution, knowledge graphs, and real-time clustering.

Built as a microservices architecture with 34 independently deployable services, event-driven communication via RabbitMQ, and a React frontend for exploration and administration.

---

## Architecture

```
RSS/Atom Feeds ──► Feed Ingestion ──► Content Analysis (Multi-LLM) ──► Intelligence Layer
     (61+)          Circuit Breaker      Sentiment, Entities,            Clustering,
                    Celery Workers       Topics, Summaries               Deduplication
                         │                      │                            │
                         ▼                      ▼                            ▼
                    PostgreSQL            Knowledge Graph              Search & Analytics
                    (80+ tables)          Neo4j + Wikidata             Real-time Indexing
                         │                      │                            │
                         └──────────── RabbitMQ Event Bus ───────────────────┘
                                      (12 Exchanges)
```

## Key Features

### Intelligence Pipeline
- **Multi-LLM Content Analysis** — Pluggable providers (OpenAI, Anthropic, Ollama) for sentiment, entity extraction, topic classification, and summarization
- **Entity Canonicalization** — 5-stage deduplication: exact match, fuzzy matching, semantic similarity, Wikidata enrichment, batch reprocessing
- **Knowledge Graph** — Neo4j-backed entity relationships with automated ingestion from the analysis pipeline
- **Intelligence Clustering** — DBSCAN-based story grouping with time-decay ranking across 21,000+ clusters
- **Narrative Detection** — Cross-article narrative thread identification and tracking

### Data Collection
- **Feed Ingestion** — High-throughput RSS/Atom with circuit breakers, retry logic, and Celery workers
- **Full-Content Scraping** — Headless browser extraction for paywalled or truncated articles
- **OSINT Monitoring** — 50+ investigation templates, scheduled monitoring, anomaly detection hooks

### Research & Analysis
- **Research Automation** — Perplexity AI integration with templates and cost tracking
- **LLM Orchestration** — DIA (Dynamic Intelligence Augmentation) with two-stage planning for AI-powered verification
- **Geolocation Extraction** — Geographic entity resolution and mapping

### Platform
- **8 MCP Servers** — Model Context Protocol interfaces (200+ tools) for AI agent integration
- **React Frontend** — Knowledge graph admin, entity management, trading signals dashboard
- **Auth & RBAC** — JWT access/refresh tokens, API keys, role-based access control
- **Observability** — Prometheus metrics, Grafana dashboards, Loki log aggregation

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Celery, SQLAlchemy |
| Frontend | React 18, TypeScript, Vite |
| Database | PostgreSQL (80+ tables), Neo4j (Knowledge Graph) |
| Messaging | RabbitMQ (12 exchanges, event-driven) |
| Cache | Redis |
| AI/ML | OpenAI, Anthropic, Ollama, Perplexity |
| Orchestration | Docker Compose, Kubernetes (Tilt) |
| Monitoring | Prometheus, Grafana, Loki |

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

### Quick Start

```bash
git clone https://github.com/CytrexSGR/news-microservices.git
cd news-microservices
cp .env.example .env    # Add your API keys (OpenAI, Anthropic, etc.)
docker compose up --build
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Auth API | http://localhost:8100 |
| Feed API | http://localhost:8101 |
| Content Analysis API | http://localhost:8114 |
| Knowledge Graph API | http://localhost:8111 |
| Search API | http://localhost:8106 |
| Analytics API | http://localhost:8107 |
| RabbitMQ Management | http://localhost:15672 |
| Neo4j Browser | http://localhost:7474 |

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required for content analysis
OPENAI_API_KEY=sk-...        # or use Ollama for local LLMs
ANTHROPIC_API_KEY=sk-ant-... # optional, for multi-provider

# Required for research automation
PERPLEXITY_API_KEY=pplx-...  # optional

# Database (defaults work with Docker Compose)
DATABASE_URL=postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp
```

## Project Structure

```
news-microservices/
├── services/                   # 34 FastAPI microservices
│   ├── auth-service/           #   JWT auth, API keys, RBAC
│   ├── feed-service/           #   RSS/Atom ingestion, Celery workers
│   ├── content-analysis-v3/    #   Multi-LLM NLP pipeline
│   ├── entity-canonicalization-service/  # 5-stage entity dedup
│   ├── knowledge-graph-service/#   Neo4j graph management
│   ├── intelligence-service/   #   Clustering, deduplication
│   ├── search-service/         #   Full-text search, indexing
│   ├── analytics-service/      #   Trend analytics, metrics
│   ├── research-service/       #   Perplexity AI integration
│   ├── osint-service/          #   OSINT monitoring, templates
│   ├── narrative-service/      #   Cross-article narrative detection
│   ├── mcp-*-server/           #   8 MCP protocol servers
│   └── ...                     #   + scheduler, scraping, notifications, etc.
├── frontend/                   # React 18 + Vite
├── shared/                     # Shared Python packages (auth, events, DB)
├── gateway/                    # API gateway configuration
├── k8s/                        # Kubernetes manifests
├── monitoring/                 # Prometheus, Grafana configs
├── scripts/                    # Maintenance & data pipeline scripts
├── tests/                      # Cross-service integration tests
├── docker-compose.yml          # Full stack (34 services + infra)
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

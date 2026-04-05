# News MCP – Microservices Platform

![Services](https://img.shields.io/badge/services-34-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18-61DAFB)
![License](https://img.shields.io/badge/License-MIT-green)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

News MCP is a modular news intelligence platform composed of independent FastAPI services, a React/Vite frontend, and an event-driven backbone built on RabbitMQ. The repository contains everything required to run the full stack locally (Docker Compose) or in Kubernetes (manifests + Tilt).

---

## 📚 **Documentation**

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Complete system architecture overview
- **[docs/](docs/)** — API docs, guides, service documentation
- **[docs/guides/](docs/guides/)** — Deployment, security, scaling guides

---

## Features at a Glance

- **Authentication & Authorization** – JWT access/refresh tokens, API keys, RBAC (`services/auth-service`)
- **Feed Ingestion** – High-throughput RSS/Atom ingestion with circuit breakers, Celery-powered background jobs, and UUID data model (`services/feed-service`)
- **Content Analysis** – Multi-LLM pipeline (OpenAI/Anthropic/Ollama) with sentiment, entity, topic and summary extraction plus Prometheus metrics (`services/content-analysis-service`)
- **LLM Orchestration** – DIA (Dynamic Intelligence Augmentation) system with two-stage LLM planning for AI-powered content verification (`services/llm-orchestrator-service`)
- **Entity Canonicalization** – 5-stage deduplication pipeline with fuzzy/semantic matching, Wikidata enrichment, and batch reprocessing (`services/entity-canonicalization-service`)
- **Knowledge Graph** – Neo4j-backed entity relationship graph with RabbitMQ ingestion, analytics APIs, and manual enrichment workflow (`services/knowledge-graph-service`)
- **Research Automation** – Perplexity AI integration, research templates, cost tracking (`services/research-service`)
- **OSINT Monitoring** – 50+ investigation templates, APScheduler-driven monitoring, anomaly hooks (`services/osint-service`)
- **Notifications** – Email/webhook delivery, preference management, RabbitMQ consumer for system events (`services/notification-service`)
- **Search & Analytics** – Real-time indexing, saved searches, trend analytics, metrics APIs (`services/search-service`, `services/analytics-service`)
- **Orchestration & Scraping** – Scheduler for feed/analysis jobs and scraping workers for full-content extraction (`services/scheduler-service`, `services/scraping-service`)
- **Frontend** – React 18 + Vite app with Knowledge Graph Admin dashboard, shared UI/state/API packages (`frontend/`)

Shared tooling lives in `shared/news-mcp-common` (auth, database, event, observability helpers).

---

## Getting Started

### 1. Prerequisites

- Docker / Docker Compose
- Python 3.11+ (for local tooling)
- Node.js 18+ (for frontend development)

### 2. Clone and bootstrap

```bash
git clone <repo-url> news-microservices
cd news-microservices

# Optional: install Tilt for live-reload K8s workflows
curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
```

### 3. Run the stack (Docker Compose)

```bash
# Bring up infrastructure + services + frontend
docker-compose up --build

# Access points
Frontend: http://localhost:3000
Auth API: http://localhost:8100
Feed API: http://localhost:8101
Content Analysis V2 API: http://localhost:8114
Research API: http://localhost:8103
OSINT API: http://localhost:8104
Notification API: http://localhost:8105
Search API: http://localhost:8106
Analytics API: http://localhost:8107
Scheduler API: http://localhost:8108
LLM Orchestrator API: http://localhost:8109
Knowledge Graph API: http://localhost:8111
Entity Canonicalization API: http://localhost:8112
RabbitMQ UI: http://localhost:15672  (guest/guest)
Neo4j Browser: http://localhost:7474  (neo4j/neo4j_password)
```

Compose mounts source directories for hot reload. Stop with `docker-compose down`.

### 4. Development workflows

- **Backend**: activate the service `venv`, run `pytest`, or start FastAPI with `uvicorn` for debugging.
- **Frontend**: `cd frontend && npm install && npm run dev`.
- **Tilt**: run `tilt up` to orchestrate builds and live reload across services (requires Docker/Kubernetes context).
- **Testing**: each service contains a `tests/` folder; integration tests live under `tests/` at repo root.

---

## Project Structure

```
news-microservices/
├── docker-compose.yml          # Local runtime (services + infra + frontend)
├── k8s/                        # Base & overlay manifests for Kubernetes
├── services/                   # FastAPI microservices (auth, feed, analysis, etc.)
├── frontend/                   # React/Turborepo workspace
├── shared/                     # Shared Python packages (events, auth, utils)
├── docs/                       # Architecture, status, deployment, runbooks
├── scripts/                    # Maintenance and data pipeline scripts
├── tests/                      # Cross-service integration tests
├── Makefile                    # Common tasks (lint, test, build, deploy)
└── Tiltfile                    # Tilt development configuration
```

Key documentation:
- `docs/ARCHITECTURE_DIAGRAM.md` – current system topology
- `docs/EVENT_DRIVEN_ARCHITECTURE.md` – RabbitMQ producers/consumers
- `docs/DATABASE_ARCHITECTURE.md` – data ownership and migration plan
- `docs/PROJECT_STATUS.md` – latest project health summary

---

## Deployment Notes

- **Secrets**: sample `.env` files exist in each service. Replace with environment-specific secrets for production.
- **Observability**: Prometheus, Grafana, and Loki configurations are available via optional Compose services; OpenTelemetry hooks can be enabled per service.
- **Scaling**: Kubernetes manifests define Deployments, HPAs, and Traefik ingress routes. Content Analysis and Search services are event-driven and horizontally scalable.
- **Backups**: refer to `docs/DEPLOYMENT_GUIDE.md` and `docs/DATABASE_ARCHITECTURE.md` for PostgreSQL backup procedures.

---

## Contributing

1. Branch from `main` and keep changes focused.
2. Run linting & tests (`make lint`, `make test`) before opening a PR.
3. Update documentation when you introduce new components or flows.

For questions or onboarding help, consult the runbooks under `docs/` or reach out to the platform team.


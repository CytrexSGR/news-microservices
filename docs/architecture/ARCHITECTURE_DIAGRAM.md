# News Microservices – System Architecture

_Last updated: 2025-10-18_

The News MCP platform now runs as a stable set of FastAPI microservices behind a Traefik gateway. Each service has a clearly scoped responsibility, shares core infrastructure (PostgreSQL, Redis, RabbitMQ), and publishes/consumes domain events to keep the system loosely coupled.

---

## 1. High-Level Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                            Client Experiences                           │
│  Web Frontend (React/Vite) · CLI/Automation · Partner Integrations      │
└───────────────┬────────────────────────────────────────────────────────┘
                │ HTTPS (Traefik routes /api/*)
                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Traefik API Gateway (80/443)                    │
│  - TLS termination & routing (Docker & K8s providers)                   │
│  - ForwardAuth / JWT validation (extension-ready)                      │
│  - Prometheus metrics & access logs                                     │
└───────────────┬────────────────────────────────────────────────────────┘
                │ Internal network: `news_network`
┌───────────────┼────────────────────────────────────────────────────────┤
│               │                                                        │
│          REST / gRPC                                            Events │
│               │                                                        │
│               ▼                                                        ▼
│  ┌──────────────────────┐    ┌────────────────────┐    ┌──────────────────────┐
│  │ User & Auth (8000)   │    │ Feed Ingestion      │    │ Content Analysis     │
│  │ - JWT auth/RBAC      │    │ Feed (8001)         │    │ (8002)               │
│  │ - API keys, audit    │    │ Scheduler (8108)    │    │ - Multi-LLM          │
│  └──────────────────────┘    │ Scraper (8109)      │    │ - Event consumers    │
│                              └────────────────────┘    └──────────────────────┘
│
│  ┌──────────────────────┐    ┌────────────────────┐    ┌──────────────────────┐
│  │ Research (8003)      │    │ OSINT (8004)        │    │ Notification (8005)  │
│  │ - Perplexity client  │    │ - 50+ templates     │    │ - Email/Webhook      │
│  │ - Cost tracking      │    │ - APScheduler       │    │ - RabbitMQ consumer  │
│  └──────────────────────┘    └────────────────────┘    └──────────────────────┘
│
│  ┌──────────────────────┐    ┌────────────────────┐
│  │ Search (8006)        │    │ Analytics (8007)   │
│  │ - Real-time indexing │    │ - Metrics & trends │
│  │ - Redis + Postgres   │    │ - Service insights │
│  └──────────────────────┘    └────────────────────┘
└───────────────┬────────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────────┐
│                      Shared Infrastructure (Docker Compose)             │
│  PostgreSQL 15 (news_mcp) · Redis 7 · RabbitMQ 3 mgmt · MinIO (opt)     │
│  Prometheus/Loki/Grafana ready via docker-compose extras                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Responsibilities

| Service (Port) | Core Capabilities | Key Integrations |
| --- | --- | --- |
| **Auth** (8000) | FastAPI + SQLAlchemy models for users, roles, API keys; JWT + refresh tokens; audit logging; service-to-service auth helpers | PostgreSQL (`users`, `roles`), Redis (session cache), shared library `news_mcp_common.auth` |
| **Feed** (8001) | UUID-based feeds & items, async fetching (httpx + feedparser), circuit breaker, Celery tasks, scheduler integration | PostgreSQL feed tables, Redis caching, RabbitMQ publisher (`news.events`), Celery via Redis |
| **Content Analysis** (8002) | LLM-backed sentiment/entities/topics, RabbitMQ consumers (`article.created`, `item.scraped`), Prometheus metrics | SQLAlchemy models, RabbitMQ, OpenAI/Anthropic/Ollama adapters, Prometheus `/metrics` |
| **Research** (8003) | Perplexity API client (`app/services/perplexity.py`), async health checks, research run persistence | PostgreSQL research tables, external Perplexity API |
| **OSINT** (8004) | Template loader (`app/templates`), APScheduler-based monitoring, anomaly detection hooks | PostgreSQL OSINT tables, scheduler manager, optional alert events |
| **Notification** (8005) | Multi-channel delivery (email/webhook), template bootstrap, RabbitMQ consumer (`news.events`), Celery-driven workers | PostgreSQL notification tables, Redis rate limiting, SMTP/Webhook, RabbitMQ |
| **Search** (8006) | Full-text & vector-ready indexing, async event consumer (`search_indexing_events`), Redis cache, background indexing | PostgreSQL search schema, Redis, RabbitMQ, feed-service HTTP client |
| **Analytics** (8007) | Metrics ingestion (`MetricCreate`), trend analysis, dashboards/reports routers, RBAC via Auth | PostgreSQL analytics tables, Auth service for JWT validation |
| **Scheduler** (8108) | Feed monitor, job processor, cron scheduler to orchestrate fetch/analysis pipelines | Posts analysis jobs to RabbitMQ, interacts with feed/content services |
| **Scraping** (8109) | Dedicated scraping workers (Playwright/httpx) feeding item scraped events | RabbitMQ publisher, PostgreSQL for scrape metadata |
| **Frontend** (3000) | React + Vite app, proxies API calls via Traefik | Auth, Feed, Analysis, Research, OSINT, Notification, Search, Analytics APIs |

> **Shared code** lives in `shared/news-mcp-common` (auth helpers, DB session factories, event publishers/consumers, observability utilities).

---

## 3. Communication Patterns

### REST / HTTP
- Traefik routes `https://{env}/api/{service}` to the respective FastAPI service (`traefik.yml` static config).
- Services call Auth for token validation via `Authorization: Bearer` or service keys (see `news_mcp_common.auth`).
- Search fetches article details from Feed Service (`SearchServiceConsumer._fetch_article_from_feed_service`).
- Notification service exposes `/api/v1/notifications/*` for management and `/metrics` for Prometheus.

### Event-Driven Messaging (RabbitMQ `news.events`)

```
Feed Service ── article.created / feed.fetch_completed ─┐
Scraping Service ── item.scraped ───────────────────────┼─►  RabbitMQ
Content Analysis ── analysis.completed / anomalies ─────┤
Research Service ── research.completed ─────────────────┘
      │                        │
      ▼                        ▼
Search Service         Notification Service
 (real-time index)      (email/webhook delivery)
      │                        │
      └────► Analytics Service aggregates metrics ◄────┘
```

- Producers use `aio_pika` via `EventPublisher` (e.g. `feed-service/app/services/event_publisher.py`).
- Consumers (`content-analysis` workers, `search-service/app/events/consumer.py`, `notification-service/app/events/rabbitmq_consumer.py`) bind durable queues with TTL/back-pressure settings.
- Scheduler service publishes orchestration events to coordinate batch analysis. Celery workers (feed + notification + scraping) rely on Redis for broker/result backends.

---

## 4. Data & Storage Model

- **PostgreSQL (`news_mcp`)** remains the shared database in the current deployment. Each service owns a schema section via SQLAlchemy models (`services/*/app/models`). Feed-related tables already use UUID primary keys; Auth still uses integer IDs to stay compatible with existing data.
- **Redis** serves multiple roles: caching feed/search data, Celery broker/result store, rate limiting (notification), and lightweight job queues.
- **RabbitMQ** is the event backbone. Exchanges:
  - `news.events` (topic) – primary domain events (feeds, analysis, research, notifications).
  - Service-specific queues (e.g. `content-analysis.article_created`, `search_indexing_events`, `notification_events`) enforce retry & DLQ policies.
- **Object storage (MinIO)** is optional; scraping workers stream HTML/artifacts when enabled.
- Backup/restore scripts live in `database/` and `scripts/`, with status tracked in `docs/DATABASE_ARCHITECTURE.md`.

---

## 5. Observability & Operations

- **Metrics:** Content Analysis exposes `/metrics` (Prometheus client). Traefik publishes gateway metrics on `:8082`. Scheduler, Feed, and Search log structured JSON when `LOG_FORMAT=json`.
- **Logging:** Centralized via Loki/Promtail stack (see `docker-compose.prod.yml` and docs) with log rotation shipped per-service.
- **Health & Readiness:** Every service exposes `/health`; critical services provide additional probes (`/health/ready`, `/health/rabbitmq` in Content Analysis).
- **Tracing:** Shared library (`news_mcp_common.observability`) provides OpenTelemetry hooks; enable per-service in config.
- **Testing:** Service-specific pytest suites live under `services/*/tests`. Integration tests and e2e scripts reside in `tests/` and `docs/integration_test_script.py`.

---

## 6. Deployment Surfaces

- **Local Development:** `docker-compose.yml` launches infrastructure + all services with live code mounts and hot reload.
- **Tilt Support:** `Tiltfile` wires rapid dev loops (build → deploy → sync) around Kubernetes or Compose targets.
- **Kubernetes:** Manifests under `k8s/base` (with `overlays/`) configure Deployments, HPAs, Services, and Traefik IngressRoutes. Content Analysis includes HPA-friendly readiness probes and graceful shutdown (see `app/main.py`).
- **CI/CD Hooks:** `Makefile` targets for linting, testing, container builds, and environment provisioning.

---

## 7. Next Architectural Steps

1. **Database Boundary Hardening:** Gradually migrate services from the shared `news_mcp` schema to service-specific databases once dual-write and data export pipelines are in place.
2. **Event Catalog Governance:** Finalize schema registry for `news.events` messages to guarantee backward compatibility.
3. **Central Observability:** Roll out OpenTelemetry tracing across all services and publish dashboards for SLA/SLO tracking.
4. **Secrets Management:** Replace `.env` mounts with Vault-backed secrets or Kubernetes `SealedSecrets` in production.

This document reflects the current, working implementation in the repository and supersedes earlier status notes from the migration phase.


# Service Documentation Index

**Quick Reference:** [CLAUDE.md](../../CLAUDE.md) | [ARCHITECTURE.md](../../ARCHITECTURE.md) | [Backend Guide](../../CLAUDE.backend.md)

---

## 📖 About This Directory

This directory contains **service-specific documentation** for all microservices in the platform.

For general backend development, see [CLAUDE.backend.md](../../CLAUDE.backend.md).
For architectural decisions, see [../decisions/](../decisions/).

---

## 🎯 Service Documentation Structure

Each service has comprehensive README documentation in `services/<service-name>/README.md`:

### Core Services

- **[auth-service](../../services/auth-service/README.md)** (Port 8100)
  - JWT authentication, RBAC, API keys

- **[feed-service](../../services/feed-service/README.md)** (Port 8101)
  - RSS/Atom ingestion, circuit breakers, Celery workers

- **[content-analysis-v3](../../services/content-analysis-v3/README.md)** (Port 8114)
  - Multi-LLM pipeline (OpenAI/Anthropic/Ollama)
  - Sentiment, entity, topic extraction

- **[research-service](../../services/research-service/README.md)** (Port 8103)
  - Perplexity AI integration, research templates

### Intelligence & Analysis

- **[llm-orchestrator](../../services/llm-orchestrator/README.md)** (Port 8109)
  - DIA (Dynamic Intelligence Augmentation)
  - Two-stage LLM planning

- **[knowledge-graph-service](../../services/knowledge-graph-service/README.md)** (Port 8111)
  - Neo4j-backed entity relationships
  - RabbitMQ ingestion, analytics APIs

- **[entity-canonicalization](../../services/entity-canonicalization-service/README.md)** (Port 8112)
  - 5-stage deduplication pipeline
  - Fuzzy/semantic matching, Wikidata enrichment

### Search & Analytics

- **[search-service](../../services/search-service/README.md)** (Port 8106)
  - Real-time indexing, saved searches

- **[analytics-service](../../services/analytics-service/README.md)** (Port 8107)
  - Trend analytics, metrics APIs

### Supporting Services

- **[notification-service](../../services/notification-service/README.md)** (Port 8105)
  - Email/webhook delivery, RabbitMQ consumer

- **[osint-service](../../services/osint-service/README.md)** (Port 8104)
  - 50+ investigation templates, APScheduler

- **[scheduler-service](../../services/scheduler-service/README.md)** (Port 8108)
  - Celery beat, cron jobs

- **[scraping-service](../../services/scraping-service/README.md)**
  - Full-content extraction workers

---

## 📊 Service Inventory

For comprehensive service metrics, see:
- **[Service Inventory Summary](../../reports/phase-1-inventory/SERVICE_INVENTORY_SUMMARY.md)**
  - Test coverage, lines of code, technical debt
  - Performance baselines, dependencies

---

## 🔍 Quick Reference

### Find Service by Functionality

| Need to... | Use Service |
|------------|-------------|
| Authenticate users | [auth-service](../../services/auth-service/README.md) |
| Ingest RSS feeds | [feed-service](../../services/feed-service/README.md) |
| Analyze content with LLMs | [content-analysis-v3](../../services/content-analysis-v3/README.md) |
| Research topics | [research-service](../../services/research-service/README.md) |
| Build knowledge graph | [knowledge-graph-service](../../services/knowledge-graph-service/README.md) |
| Deduplicate entities | [entity-canonicalization](../../services/entity-canonicalization-service/README.md) |
| Search articles | [search-service](../../services/search-service/README.md) |
| Send notifications | [notification-service](../../services/notification-service/README.md) |

### Find Service by Port

| Port | Service |
|------|---------|
| 8100 | auth-service |
| 8101 | feed-service |
| 8103 | research-service |
| 8104 | osint-service |
| 8105 | notification-service |
| 8106 | search-service |
| 8107 | analytics-service |
| 8108 | scheduler-service |
| 8109 | llm-orchestrator |
| 8111 | knowledge-graph-service |
| 8112 | entity-canonicalization |
| 8114 | content-analysis-v3 |

---

## 🛠️ Service Development

### Quick Start

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d <service-name>

# View logs
docker compose logs -f <service-name>

# Rebuild after dependency changes
docker compose up -d --build <service-name>
```

### Testing

```bash
# Test specific service
cd services/<service-name>
pytest tests/ -v

# Integration tests
pytest tests/integration/ -v
```

### API Documentation

Each service exposes Swagger UI at:
```
http://localhost:<port>/docs
```

---

## 📚 Related Documentation

- **API Contracts:** [../api/](../api/) - OpenAPI specifications
- **Architecture Decisions:** [../decisions/](../decisions/) - ADRs affecting services
- **Deployment Guides:** [../guides/deployment/](../guides/deployment/) - Service deployment
- **Runbooks:** [../runbooks/](../runbooks/) - Operational procedures (if directory exists)

---

## 🧪 Service Health

Check service health:
```bash
# All services
./scripts/health_check.sh

# Specific service
curl http://localhost:<port>/health
```

System health dashboard:
```
http://localhost:3000/admin/health
```

---

**Last Updated:** 2025-12-07
**Service Count:** 16 services (12 active, 4 archived/planned)
**Maintainer:** Backend Team

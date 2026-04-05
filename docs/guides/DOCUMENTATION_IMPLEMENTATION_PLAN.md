# Documentation Implementation Plan - News Microservices

## 🎯 Execution Strategy

### Parallel Agent Coordination mit Claude Code Task Tool

**Prinzip:**
- **1 Sprint = 1 Message = Alle Agents parallel**
- Jeder Agent dokumentiert einen spezifischen Bereich
- Agents koordinieren via Claude Flow Memory
- Maximale Effizienz durch parallele Ausführung

---

## 📋 Sprint 1: Critical Frontend Dependencies (P0)

**Zeitrahmen:** ~7 Stunden (parallel: ~2 Stunden)
**Ziel:** Frontend kann mit Auth + Feed-Management starten

### Agent-Architektur (Parallel Execution)

```javascript
// Single Message - 6 Agents parallel
[Parallel Agent Execution]:

  // Agent 1: Auth-Service Analyst
  Task("Auth Service Analyst", `
    TASK: Analyze auth-service code and create comprehensive README

    STEPS:
    1. Read all files in services/auth-service/app/
    2. Analyze: main.py, api/auth.py, api/users.py, models/, schemas/
    3. Extract: Endpoints, Models, Auth-Flow, Dependencies
    4. Create: services/auth-service/README.md

    STRUCTURE:
    - Overview (JWT, RBAC, User Management)
    - Architecture (FastAPI, SQLAlchemy, Alembic)
    - API Endpoints (Login, Register, Token Refresh, User CRUD)
    - Data Models (User, Role, Permission)
    - Authentication Flow (Diagram in markdown)
    - Environment Variables
    - Development Setup
    - Testing

    COORDINATION:
    - Store endpoint list in memory: "auth-service/endpoints"
    - Store models in memory: "auth-service/models"
    - Use hooks: pre-task, post-edit, post-task
  `, "code-analyzer")

  // Agent 2: Auth OpenAPI Generator
  Task("Auth OpenAPI Generator", `
    TASK: Generate OpenAPI 3.0 specification for auth-service

    STEPS:
    1. Read services/auth-service/app/api/*.py
    2. Extract all FastAPI routes with decorators
    3. Document request/response schemas from Pydantic models
    4. Generate OpenAPI YAML with complete examples
    5. Create: services/auth-service/docs/openapi.yaml

    OPENAPI STRUCTURE:
    - Info (title, version, description)
    - Servers (localhost:8100)
    - Security Schemes (Bearer JWT)
    - Paths (all endpoints with full schemas)
    - Components (reusable schemas)
    - Examples (realistic request/response data)

    COORDINATION:
    - Retrieve endpoint list from memory: "auth-service/endpoints"
    - Store OpenAPI in memory: "auth-service/openapi"
  `, "api-docs")

  // Agent 3: Feed-Service Analyst
  Task("Feed Service Analyst", `
    TASK: Analyze feed-service code and create comprehensive README

    STEPS:
    1. Read all files in services/feed-service/app/
    2. Analyze: main.py, api/feeds.py, services/feed_scheduler.py, celery tasks
    3. Extract: Endpoints, Models, Feed-Fetch-Flow, Celery Tasks
    4. Create: services/feed-service/README.md

    STRUCTURE:
    - Overview (RSS/Atom management, scheduling)
    - Architecture (FastAPI, Celery, RabbitMQ events)
    - API Endpoints (Feed CRUD, Fetch operations)
    - Data Models (Feed, FeedEntry, FetchResult)
    - Feed Processing Flow (Diagram)
    - Celery Tasks (scheduled_feed_fetch, fetch_feed)
    - Event Publishing (RabbitMQ integration)
    - Environment Variables
    - Development Setup
    - Testing

    COORDINATION:
    - Store endpoint list in memory: "feed-service/endpoints"
    - Store models in memory: "feed-service/models"
    - Store events in memory: "feed-service/events"
  `, "code-analyzer")

  // Agent 4: Feed OpenAPI Generator
  Task("Feed OpenAPI Generator", `
    TASK: Generate OpenAPI 3.0 specification for feed-service

    STEPS:
    1. Read services/feed-service/app/api/*.py
    2. Extract all routes including query params, filters
    3. Document Pydantic schemas (FeedCreate, FeedUpdate, FeedResponse)
    4. Generate OpenAPI YAML with scheduler endpoints
    5. Create: services/feed-service/docs/openapi.yaml

    OPENAPI STRUCTURE:
    - Info + Servers
    - Security (Bearer JWT - same as auth)
    - Paths:
      - GET /api/v1/feeds (list with pagination)
      - POST /api/v1/feeds (create)
      - GET /api/v1/feeds/{id} (detail)
      - PUT /api/v1/feeds/{id} (update)
      - DELETE /api/v1/feeds/{id} (delete)
      - POST /api/v1/feeds/{id}/fetch (manual fetch)
      - GET /api/v1/feeds/{id}/entries (feed entries)
    - Components (all schemas with examples)

    COORDINATION:
    - Retrieve endpoints from memory: "feed-service/endpoints"
    - Store OpenAPI in memory: "feed-service/openapi"
  `, "api-docs")

  // Agent 5: API Catalog Architect
  Task("API Catalog Architect", `
    TASK: Create central API catalog for all services

    STEPS:
    1. Retrieve from memory:
       - "auth-service/endpoints"
       - "feed-service/endpoints"
    2. Read existing docs/ARCHITECTURE_DIAGRAM.md for service overview
    3. Create comprehensive API catalog
    4. Create: docs/API_CATALOG.md

    STRUCTURE:
    - Services Overview Table (Name, Port, Base URL, Status, Docs Link)
    - Authentication Flow (Diagram + Steps)
    - API Request Patterns:
      - Headers (Authorization: Bearer <token>)
      - Error Responses (401, 403, 404, 500 standards)
      - Pagination (limit/offset pattern)
      - Filtering & Sorting
    - Service Details (per service):
      - Auth Service (8100)
        - Endpoints list
        - Auth flow
        - Token handling
      - Feed Service (8101)
        - Endpoints list
        - Feed lifecycle
        - Scheduler integration
      - [Placeholders for other services]
    - Integration Patterns
    - Error Handling Standards
    - Rate Limiting (if applicable)

    COORDINATION:
    - Store catalog in memory: "api-catalog/main"
  `, "system-architect")

  // Agent 6: Integration Validator
  Task("Integration Validator", `
    TASK: Validate all generated documentation for consistency

    STEPS:
    1. Wait for other agents to complete
    2. Read generated files:
       - services/auth-service/README.md
       - services/auth-service/docs/openapi.yaml
       - services/feed-service/README.md
       - services/feed-service/docs/openapi.yaml
       - docs/API_CATALOG.md
    3. Validate:
       - Cross-references are correct
       - Port numbers consistent (8100, 8101)
       - Auth flow matches between docs
       - OpenAPI schemas match README descriptions
       - All links work
    4. Create validation report
    5. Fix any inconsistencies found

    VALIDATION CHECKLIST:
    - [ ] Auth endpoints in OpenAPI match README
    - [ ] Feed endpoints in OpenAPI match README
    - [ ] API Catalog links to correct OpenAPI files
    - [ ] JWT security scheme consistent across services
    - [ ] Example requests use correct base URLs
    - [ ] Model schemas match between services

    COORDINATION:
    - Store validation results in memory: "sprint1/validation"
    - Report issues for fixing
  `, "reviewer")
```

---

## 📋 Sprint 2: High-Priority Services (P1)

**Zeitrahmen:** ~7 Stunden (parallel: ~2.5 Stunden)
**Ziel:** Frontend kann Event-Analyse & Research integrieren

### Agent-Architektur (Parallel Execution)

```javascript
[Parallel Agent Execution - Sprint 2]:

  // Agent 1: Frontend Integration Guide Author
  Task("Frontend Integration Guide", `
    TASK: Create comprehensive frontend integration guide

    STEPS:
    1. Retrieve from memory: "api-catalog/main"
    2. Create practical guide for frontend developers
    3. Include code examples in JavaScript/TypeScript
    4. Create: docs/FRONTEND_INTEGRATION.md

    STRUCTURE:
    - Quick Start (3 steps to first API call)
    - Authentication Setup:
      - Login flow with code example
      - Token storage (localStorage vs. httpOnly cookies)
      - Token refresh logic
      - Auto-logout on 401
    - API Client Setup:
      - Axios/Fetch configuration
      - Base URL configuration
      - Auth interceptor
      - Error handling interceptor
    - Common Patterns:
      - Authenticated requests
      - File uploads
      - Pagination handling
      - Real-time updates (WebSocket/SSE)
    - Error Handling:
      - Standard error structure
      - User-friendly error messages
      - Retry logic
    - State Management Integration:
      - Redux example
      - React Query example
      - Zustand example
    - Testing:
      - Mocking API calls
      - Integration tests

    CODE EXAMPLES:
    \`\`\`javascript
    // Login example
    async function login(email, password) {
      const response = await fetch('http://localhost:8100/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const { access_token } = await response.json();
      localStorage.setItem('token', access_token);
    }

    // Authenticated API call
    async function getFeeds(token) {
      const response = await fetch('http://localhost:8101/api/v1/feeds', {
        headers: { 'Authorization': \`Bearer \${token}\` }
      });
      return response.json();
    }
    \`\`\`
  `, "api-docs")

  // Agent 2: Content-Analysis Service Analyst
  Task("Content-Analysis Service Analyst", `
    TASK: Document content-analysis-service

    STEPS:
    1. Read services/content-analysis-service/app/
    2. Analyze AI/ML integration, event processing
    3. Create README + OpenAPI

    FOCUS:
    - Event-driven architecture
    - OpenAI/Perplexity integration
    - Content analysis workflow
    - Queue processing
  `, "code-analyzer")

  // Agent 3: Content-Analysis OpenAPI Generator
  Task("Content-Analysis OpenAPI Generator", `
    TASK: Generate OpenAPI for content-analysis-service

    ENDPOINTS:
    - GET /api/v1/event-analysis/events (list analyzed events)
    - GET /api/v1/event-analysis/events/{id} (detail)
    - POST /api/v1/event-analysis/requeue/{id} (reprocess)
    - GET /api/v1/event-analysis/stats (statistics)
  `, "api-docs")

  // Agent 4: Research Service Analyst
  Task("Research Service Analyst", `
    TASK: Document research-service

    STEPS:
    1. Read services/research-service/app/
    2. Analyze Perplexity API integration
    3. Create README + OpenAPI

    FOCUS:
    - Perplexity API usage
    - Research query handling
    - Citation management
    - Rate limiting
  `, "code-analyzer")

  // Agent 5: Research OpenAPI Generator
  Task("Research OpenAPI Generator", `
    TASK: Generate OpenAPI for research-service

    ENDPOINTS:
    - POST /api/v1/research/query (research request)
    - GET /api/v1/research/results/{id} (get results)
    - GET /api/v1/research/history (user research history)
  `, "api-docs")

  // Agent 6: API Catalog Updater
  Task("API Catalog Updater", `
    TASK: Update API_CATALOG.md with Sprint 2 services

    STEPS:
    1. Read newly created docs
    2. Update docs/API_CATALOG.md
    3. Add Content-Analysis & Research sections
    4. Validate cross-references
  `, "reviewer")
```

---

## 📋 Sprint 3: Complete Coverage (P2-P3)

**Zeitrahmen:** ~12 Stunden (parallel: ~4 Stunden)
**Ziel:** Vollständige Dokumentation aller Services + Architektur-Docs

### Agent-Architektur (Parallel Execution)

```javascript
[Parallel Agent Execution - Sprint 3]:

  // 4 Service Documentation Agents (parallel)
  Task("OSINT Service Docs", "...", "code-analyzer")
  Task("Notification Service Docs", "...", "code-analyzer")
  Task("Search Service Docs", "...", "code-analyzer")
  Task("Analytics Service Docs", "...", "code-analyzer")

  // 4 OpenAPI Generation Agents (parallel)
  Task("OSINT OpenAPI", "...", "api-docs")
  Task("Notification OpenAPI", "...", "api-docs")
  Task("Search OpenAPI", "...", "api-docs")
  Task("Analytics OpenAPI", "...", "api-docs")

  // Architecture Documentation Agents
  Task("Database Architecture Updater", `
    TASK: Update DATABASE_ARCHITECTURE.md

    STEPS:
    1. Analyze all SQLAlchemy models across services
    2. Generate ER diagrams (Mermaid syntax)
    3. Document relationships, indices, constraints
    4. Update docs/DATABASE_ARCHITECTURE.md

    CONTENT:
    - Per-Service schemas
    - Cross-service relationships
    - Migration history
    - Performance indices
  `, "system-architect")

  Task("Event Architecture Updater", `
    TASK: Update EVENT_DRIVEN_ARCHITECTURE.md

    STEPS:
    1. Analyze RabbitMQ event publishers/consumers
    2. Document all events with schemas
    3. Create event flow diagrams
    4. Update docs/EVENT_DRIVEN_ARCHITECTURE.md

    CONTENT:
    - Event Catalog (all events with JSON schemas)
    - Exchange/Queue Topology
    - Event Flow Diagrams (Mermaid)
    - Retry & Error Handling
  `, "system-architect")

  Task("Environment Variables Documenter", `
    TASK: Create ENVIRONMENT_VARIABLES.md

    STEPS:
    1. Extract all env vars from all services
    2. Categorize: Global, Service-specific
    3. Document defaults, required/optional
    4. Create docs/ENVIRONMENT_VARIABLES.md

    STRUCTURE:
    - Global Variables (DB, RabbitMQ, Redis)
    - Per-Service Variables
    - Security Variables (JWT secrets, API keys)
    - Development vs. Production
  `, "researcher")

  Task("Code Examples Creator", `
    TASK: Create FRONTEND_EXAMPLES.md

    STEPS:
    1. Create practical code examples
    2. Cover all common use cases
    3. Include error handling
    4. Create docs/examples/FRONTEND_EXAMPLES.md

    EXAMPLES:
    - Authentication (login, logout, refresh)
    - Feed Management (CRUD operations)
    - Event Subscription (WebSocket/polling)
    - File Uploads (if applicable)
    - Pagination & Filtering
    - Error Recovery
  `, "coder")

  // Final Validation & Integration
  Task("Documentation Validator", `
    TASK: Final validation of all documentation

    STEPS:
    1. Read ALL generated documentation
    2. Validate completeness
    3. Check cross-references
    4. Test code examples
    5. Generate completion report

    VALIDATION:
    - All services have README + OpenAPI
    - API_CATALOG.md is complete
    - Cross-references work
    - Code examples are valid
    - Architecture docs match code
  `, "reviewer")
```

---

## 🚀 Execution Commands

### Sprint 1 (Start jetzt)
```bash
# Wird als Single Message mit 6 parallel Tasks ausgeführt
# Siehe oben: Agent 1-6 parallel
```

### Sprint 2 (Nach Sprint 1 Completion)
```bash
# Single Message mit 6 parallel Tasks
```

### Sprint 3 (Nach Sprint 2 Completion)
```bash
# Single Message mit 12+ parallel Tasks
```

---

## 📊 Progress Tracking

### Memory-basierte Koordination

**Memory Keys:**
```
sprint1/auth-service/readme        -> README content
sprint1/auth-service/openapi       -> OpenAPI spec
sprint1/feed-service/readme        -> README content
sprint1/feed-service/openapi       -> OpenAPI spec
sprint1/api-catalog                -> Central catalog
sprint1/validation/status          -> Validation results

sprint2/content-analysis/readme    -> ...
sprint2/research/readme            -> ...
sprint2/frontend-guide             -> Integration guide

sprint3/completion/status          -> Final checklist
```

### Hooks Integration

**Pre-Task:**
```bash
npx claude-flow@alpha hooks pre-task --description "Sprint 1: Auth + Feed + API Catalog"
```

**Post-Edit (per file):**
```bash
npx claude-flow@alpha hooks post-edit \
  --file "services/auth-service/README.md" \
  --memory-key "sprint1/auth-service/readme"
```

**Post-Task:**
```bash
npx claude-flow@alpha hooks post-task \
  --task-id "sprint1-documentation" \
  --metrics-export true
```

---

## ✅ Quality Criteria

### README Checklist (per Service)
- [ ] Overview section (2-3 sentences)
- [ ] Architecture overview
- [ ] Complete endpoint list
- [ ] Data models documented
- [ ] Auth requirements clear
- [ ] Environment variables listed
- [ ] Development setup instructions
- [ ] Testing instructions

### OpenAPI Checklist (per Service)
- [ ] OpenAPI 3.0+ compliant
- [ ] All endpoints documented
- [ ] Request/Response schemas complete
- [ ] Security schemes defined
- [ ] Realistic examples included
- [ ] Error responses documented
- [ ] Validates with Swagger Editor

### Integration Checklist
- [ ] Cross-references between docs work
- [ ] Port numbers consistent
- [ ] Auth flow consistent across services
- [ ] Code examples tested
- [ ] No broken links

---

## 🎯 Success Metrics

**Sprint 1 Success:**
- Frontend-Entwickler können sofort mit Auth + Feed starten
- 0 Rückfragen zu Basis-Endpoints
- OpenAPI-Specs validieren ohne Fehler

**Sprint 2 Success:**
- Event-Analyse & Research integrierbar
- Frontend Integration Guide reduziert Setup-Zeit um 80%

**Sprint 3 Success:**
- 100% Service-Coverage
- Alle Architektur-Docs aktuell
- Code-Beispiele für alle Use Cases

---

## 📅 Zeitplan

| Sprint | Dauer (parallel) | Deliverables | Start |
|--------|------------------|--------------|-------|
| Sprint 1 | ~2h | Auth + Feed Docs + API Catalog | Sofort |
| Sprint 2 | ~2.5h | Frontend Guide + Content/Research | Nach Sprint 1 |
| Sprint 3 | ~4h | Alle Services + Architektur | Nach Sprint 2 |

**Total:** ~8.5 Stunden (parallel) vs. ~26h sequentiell

---

## 🚀 Ready to Execute?

**Nächster Schritt:**
- Bestätigung → Ich starte **Sprint 1** in einer einzigen Nachricht
- Alle 6 Agents arbeiten parallel
- Ergebnis: Auth-Service + Feed-Service vollständig dokumentiert + Zentraler API-Katalog

**Estimated Completion:** 2 Stunden

Soll ich **Sprint 1 jetzt starten**?

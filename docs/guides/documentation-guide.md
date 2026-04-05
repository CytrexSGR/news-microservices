# Documentation Guide - News Microservices

> **"Frontend failed completely due to missing docs. Rebuilding from scratch takes weeks. Documenting takes 10 minutes."**
> — From POSTMORTEMS.md

## 📋 Table of Contents

- [Quick Reference](#quick-reference)
- [When to Document](#when-to-document)
- [What to Document](#what-to-document)
- [How to Document](#how-to-document)
- [Documentation Workflow](#documentation-workflow)
- [Templates](#templates)
- [Best Practices](#best-practices)
- [Common Mistakes](#common-mistakes)

---

## ⚡ Quick Reference

### For Backend Services

```bash
# 1. New service created?
cp docs/templates/service-template.md docs/services/YOUR-SERVICE.md
# Fill in the template (10-15 minutes)

# 2. API endpoints added/changed?
cp docs/templates/api-template.md docs/api/YOUR-SERVICE-api.md
# Document all endpoints with examples

# 3. Database schema changed?
# Update docs/services/YOUR-SERVICE.md → Database Tables section
# Or update database/README.md if shared schema
```

### For Frontend

```bash
# 1. New frontend feature?
# Create docs/services/analytics-frontend.md
# Document: Routes, Components, State Management, API Integration

# 2. New page/route added?
# Update routing documentation in service docs

# 3. API integration changed?
# Document in service docs under "API Integration" section
```

### For Architecture Decisions

```bash
# Made a significant technical decision?
cp docs/templates/architecture-template.md docs/decisions/ADR-XXX-title.md
# Document: Context, Decision, Alternatives, Consequences
```

---

## 📅 When to Document

### ✅ ALWAYS Document (Immediately)

| Trigger | Documentation Required | Time |
|---------|----------------------|------|
| **New service created** | Service README | 10-15 min |
| **New API endpoint** | Update API docs | 5 min |
| **Database migration** | Update schema docs | 5 min |
| **Architecture decision** | ADR (Architecture Decision Record) | 10 min |
| **Critical bug fix** | Incident report | 10 min |
| **New frontend feature** | Component/page docs | 10 min |

### ⚠️ Document Before Commit

```bash
# WRONG:
git add .
git commit -m "feat: add analytics service"
git push
# → Undocumented service, team blocked

# RIGHT:
# 1. Implement feature
# 2. Document it (see below)
# 3. Then commit:
git add services/analytics/ docs/services/analytics-service.md
git commit -m "feat: add analytics service with documentation"
git push
```

### 🔄 Update When

- API endpoint changes (request/response format)
- Configuration changes (new env vars)
- Dependencies change (new external service)
- Deployment process changes

---

## 📝 What to Document

### For Backend Services

**Minimum Required (Service README):**

1. **Overview** - One sentence: What does this service do?
2. **Key Responsibilities** - 3-5 bullet points
3. **Quick Start** - How to run it locally
4. **API Endpoints** - List all with HTTP method + path
5. **Database Tables** - List tables this service owns
6. **Configuration** - All environment variables
7. **Dependencies** - Other services it depends on

**Optional but Recommended:**

- Architecture diagrams (Mermaid)
- Event integration (published/consumed events)
- Troubleshooting common issues
- Performance considerations

### For Frontend

**Minimum Required:**

1. **Overview** - What is this frontend for?
2. **Tech Stack** - React, Vite, TailwindCSS, etc.
3. **Project Structure** - Folder organization
4. **Routes** - All application routes
5. **API Integration** - Which backend endpoints are used
6. **State Management** - How state is managed
7. **Environment Variables** - Required for build/dev

**Optional but Recommended:**

- Component architecture
- Authentication flow
- Testing strategy
- Build & deployment

### For Architecture Decisions

Use ADR (Architecture Decision Record) template for:

- Choosing technologies (Why PostgreSQL over MongoDB?)
- Architectural patterns (Why microservices?)
- Security decisions (Why JWT over sessions?)
- Infrastructure choices (Why Docker Compose over Kubernetes for dev?)

---

## 🛠️ How to Document

### Step-by-Step: New Backend Service

**Total Time: ~15 minutes**

#### 1. Create Service README (10 min)

```bash
# Copy template
cp docs/templates/service-template.md docs/services/analytics-service.md

# Replace placeholders
sed -i 's/{{SERVICE_NAME}}/analytics/g' docs/services/analytics-service.md
sed -i 's/{{PORT}}/8107/g' docs/services/analytics-service.md
```

**Fill in sections:**

```markdown
## Overview

Analytics service provides system-wide metrics, dashboards, and reports for monitoring platform health and usage.

**Key Responsibilities:**
- Aggregate metrics from all services
- Generate custom dashboards
- Create PDF/CSV reports
- Provide real-time statistics API

## Quick Start

### Installation

```bash
docker compose up -d analytics-service
curl http://localhost:8107/health
```

## API Endpoints

### Core Operations

- `GET /api/v1/analytics/overview` - System overview metrics
- `GET /api/v1/analytics/dashboards` - List user dashboards
- `GET /api/v1/analytics/dashboards/{id}` - Dashboard details
- `POST /api/v1/analytics/reports` - Generate report
- `GET /api/v1/analytics/reports/{id}/download` - Download report

### Health & Status

- `GET /health` - Service health check

**Full API Reference:** [analytics-api.md](../api/analytics-api.md)

## Database Tables

- `dashboards` - User-created dashboards
- `dashboard_widgets` - Dashboard widget configurations
- `reports` - Generated reports
- `metrics_cache` - Cached metric calculations

## Configuration

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection for caching |
| `JWT_SECRET_KEY` | JWT signing secret |

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SERVICE_PORT` | 8107 | HTTP server port |
| `CACHE_TTL` | 300 | Cache expiry in seconds |
```

#### 2. Create API Documentation (5 min)

```bash
cp docs/templates/api-template.md docs/api/analytics-api.md
```

**Document each endpoint:**

```markdown
## GET /api/v1/analytics/overview

Get system-wide overview metrics.

### Request

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `period` - Time period (1h, 24h, 7d, 30d) - default: 24h

### Response

**Status:** 200 OK

```json
{
  "total_users": 1250,
  "active_feeds": 342,
  "total_articles": 45230,
  "articles_today": 823
}
```

**Status:** 401 Unauthorized - Invalid or missing token
```

#### 3. Verify Documentation (2 min)

**Checklist:**

- [ ] Service README exists in `docs/services/`
- [ ] API docs exist in `docs/api/`
- [ ] All placeholders replaced
- [ ] Code examples are correct
- [ ] Links between docs work

### Step-by-Step: New Frontend Feature

**Total Time: ~10 minutes**

#### 1. Update Service Documentation

If `docs/services/analytics-frontend.md` doesn't exist, create it:

```markdown
# Analytics Frontend

## Overview

React-based frontend for the News Analytics platform.

## Tech Stack

- **Framework:** React 18
- **Build Tool:** Vite 5
- **Styling:** TailwindCSS 3
- **State Management:** Zustand
- **API Client:** React Query + Axios
- **Routing:** React Router 6

## Project Structure

```
src/
├── api/              # API client configuration
├── components/       # Reusable UI components
│   ├── ui/          # Shadcn UI components
│   └── layout/      # Layout components
├── features/         # Feature-based modules
│   ├── auth/        # Authentication
│   ├── dashboards/  # Dashboard management
│   └── reports/     # Report management
├── pages/           # Route-level pages
├── store/           # Zustand stores
└── lib/             # Utilities
```

## Routes

| Path | Component | Protected | Description |
|------|-----------|-----------|-------------|
| `/login` | LoginPage | No | User login |
| `/` | HomePage | Yes | Overview dashboard |
| `/dashboards` | DashboardListPage | Yes | Dashboard list |
| `/dashboards/:id` | DashboardDetailPage | Yes | Dashboard detail |
| `/reports` | ReportsPage | Yes | Reports list |

## API Integration

### Backend Services

- **Auth Service** (8100) - User authentication
- **Analytics Service** (8107) - Metrics, dashboards, reports
- **Feed Service** (8101) - Feed statistics

### API Client Setup

```typescript
// src/api/axios.ts
import axios from 'axios'

const analyticsApi = axios.create({
  baseURL: import.meta.env.VITE_ANALYTICS_API_URL,
})

analyticsApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

## State Management

Uses Zustand for:
- **authStore** - User authentication state
- Other state via React Query cache

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build
```

## Environment Variables

```
VITE_AUTH_API_URL=http://localhost:8100/api/v1
VITE_ANALYTICS_API_URL=http://localhost:8107/api/v1
VITE_FEED_API_URL=http://localhost:8101/api/v1
```
```

---

## 🔄 Documentation Workflow

### Daily Development Flow

```
┌─────────────────────┐
│  Write Code         │
│  (Feature/Fix)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Document Changes   │◄──── 10 minutes!
│  - Update README    │
│  - Update API docs  │
│  - Add examples     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Test Documentation │
│  - Links work?      │
│  - Examples correct?│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Commit Together    │
│  git add code + docs│
│  git commit         │
└─────────────────────┘
```

### Git Commit Pattern

```bash
# ✅ GOOD - Code + Docs together
git add services/analytics/ docs/services/analytics-service.md docs/api/analytics-api.md
git commit -m "feat(analytics): add dashboard management API

- Add GET/POST/PUT/DELETE /dashboards endpoints
- Implement dashboard CRUD operations
- Add real-time metrics WebSocket
- Document all endpoints in analytics-api.md"

# ❌ BAD - Code without docs
git add services/analytics/
git commit -m "feat: add analytics service"
# → Team can't use it without docs
```

---

## 📚 Templates

All templates are in `docs/templates/`:

### 1. service-template.md

**Use for:** New backend service or frontend application

**Sections:**
- Overview & Key Responsibilities
- Quick Start & Installation
- Architecture (Components, Database)
- API Endpoints
- Configuration (Environment Variables)
- Event Integration (if applicable)
- Deployment
- Troubleshooting
- Tech Stack

**Replace placeholders:**
- `{{SERVICE_NAME}}` → Service name
- `{{PORT}}` → Port number
- `{{API_PREFIX}}` → API path prefix
- `{{TABLE_NAME}}` → Database tables

### 2. api-template.md

**Use for:** Detailed API endpoint documentation

**Sections per endpoint:**
- Endpoint description
- HTTP method + path
- Request (headers, params, body)
- Response (success + errors with examples)
- Authorization requirements
- Rate limiting (if applicable)

### 3. architecture-template.md

**Use for:** Architecture Decision Records (ADRs)

**Sections:**
- Context (Why do we need to decide?)
- Decision (What did we choose?)
- Alternatives Considered (What else did we evaluate?)
- Consequences (What are the trade-offs?)
- Status (Proposed/Accepted/Deprecated)

---

## ✅ Best Practices

### 1. Write for Your Future Self

```markdown
# ❌ Bad
"The service handles events."

# ✅ Good
"The service consumes `item_scraped` events from RabbitMQ and
analyzes article content using OpenAI. Results are stored in
the `event_analysis` table and published as `analysis_completed` events."
```

### 2. Include Realistic Examples

```markdown
# ❌ Bad
POST /api/v1/users - Creates a user

# ✅ Good
POST /api/v1/users - Creates a new user

Request:
```json
{
  "email": "andreas@test.com",
  "password": "securepass123",
  "full_name": "Andreas"
}
```

Response (201 Created):
```json
{
  "id": "uuid-here",
  "email": "andreas@test.com",
  "full_name": "Andreas",
  "created_at": "2024-10-19T10:30:00Z"
}
```
```

### 3. Document Configuration

Always document ALL environment variables:

```markdown
## Configuration

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost:5432/db` |
| `JWT_SECRET_KEY` | JWT signing secret (min 32 chars) | `your-super-secret-key-here` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `CACHE_TTL` | `300` | Cache expiration in seconds |
```

### 4. Link Related Docs

Create a documentation network:

```markdown
## Related Documentation

- [API Reference](../api/analytics-api.md) ← Full endpoint docs
- [Database Schema](../architecture/database.md) ← Table definitions
- [Event Specifications](../architecture/events.md) ← Event formats
- [Deployment Guide](../guides/DEPLOYMENT_GUIDE.md) ← Production setup
```

### 5. Keep It Current

```bash
# When you change code, update docs IMMEDIATELY
# Not "later", not "tomorrow", NOW.

# Example: Added new endpoint
vim services/analytics/app/api/reports.py  # Add endpoint
vim docs/api/analytics-api.md              # Document it
git add services/analytics/ docs/api/
git commit -m "feat: add PDF report generation"
```

### 6. Use Diagrams

Mermaid diagrams render on GitHub:

```markdown
## Architecture

```mermaid
graph TD
    A[Client] -->|HTTP| B[Analytics API]
    B -->|Query| C[PostgreSQL]
    B -->|Cache| D[Redis]
    B -->|Events| E[RabbitMQ]
```
```

---

## ⚠️ Common Mistakes

### ❌ Mistake 1: "I'll document it later"

**Problem:** You forget, team is blocked, you waste time explaining

**Solution:** Document immediately (10 minutes vs. hours of explanation)

### ❌ Mistake 2: Documenting only "what" without "why"

```markdown
# ❌ Bad
Uses PostgreSQL database.

# ✅ Good
Uses PostgreSQL for ACID compliance and complex queries on relational data.
Considered MongoDB but need JOINs for cross-service analytics.
```

### ❌ Mistake 3: Outdated Examples

```markdown
# ❌ Bad (after API changed)
POST /api/v1/users
{"username": "test"}  # ← username field removed 3 months ago

# ✅ Good (updated)
POST /api/v1/users
{"email": "test@example.com", "full_name": "Test User"}
```

### ❌ Mistake 4: Missing Prerequisites

```markdown
# ❌ Bad
docker compose up -d analytics-service

# ✅ Good
# Prerequisites:
# - Database migrations must be run first
# - Redis and RabbitMQ must be running

# Start dependencies
docker compose up -d postgres redis rabbitmq

# Run migrations
docker exec -it news-postgres psql -U news_user -d news_mcp < migrations/analytics.sql

# Start service
docker compose up -d analytics-service
```

### ❌ Mistake 5: No Error Documentation

```markdown
# ❌ Bad
Returns 200 on success.

# ✅ Good
**Success:** 200 OK
**Errors:**
- 400 Bad Request - Invalid dashboard configuration
- 401 Unauthorized - Missing or invalid token
- 404 Not Found - Dashboard does not exist
- 500 Internal Server Error - Database connection failed
```

---

## 📖 Reference

### Documentation Structure

```
docs/
├── services/              # Per-service documentation
│   ├── auth-service.md
│   ├── analytics-service.md
│   └── analytics-frontend.md
├── api/                   # API endpoint details
│   ├── auth-api.md
│   └── analytics-api.md
├── architecture/          # Architecture docs
│   ├── database.md
│   ├── events.md
│   └── system-overview.md
├── decisions/             # ADRs (Architecture Decision Records)
│   ├── ADR-001-use-postgresql.md
│   └── ADR-002-microservices.md
├── guides/                # How-to guides
│   ├── DEPLOYMENT_GUIDE.md
│   ├── DEVELOPMENT_WORKFLOW.md
│   └── documentation-guide.md (this file)
├── templates/             # Documentation templates
│   ├── service-template.md
│   ├── api-template.md
│   └── architecture-template.md
└── README.md              # Documentation overview
```

### Quick Commands

```bash
# Create new service docs
cp docs/templates/service-template.md docs/services/YOUR-SERVICE.md

# Create API docs
cp docs/templates/api-template.md docs/api/YOUR-SERVICE-api.md

# Create ADR
cp docs/templates/architecture-template.md docs/decisions/ADR-XXX-title.md

# Validate all markdown
find docs -name "*.md" -exec markdown-lint {} \;
```

---

## 🎯 Success Criteria

**Your documentation is good when:**

✅ A new developer can set up the service in < 15 minutes
✅ The frontend team can integrate without asking questions
✅ You can return to the code after 6 months and understand it
✅ Your future self thanks you

**Your documentation is BAD when:**

❌ Team asks "How do I run this?"
❌ Integration breaks because API changed undocumented
❌ You spend 30 minutes explaining what 10 minutes of docs would solve

---

## 📞 Need Help?

- **Templates:** See `docs/templates/`
- **Examples:** See `services/notification-service/docs/` (reference implementation)
- **Questions:** Check existing service docs for patterns
- **CLAUDE.md:** Project-wide development guidelines

---

**Remember:** *"Documenting takes 10 minutes. Rebuilding from scratch takes weeks."*

Document now, deploy confidently.

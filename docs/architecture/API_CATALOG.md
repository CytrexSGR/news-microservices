# API Catalog - News MCP Microservices

## Overview

News MCP is a microservices-based news aggregation and analysis platform with 11 specialized services orchestrated through event-driven architecture.

**Architecture:** Event-driven microservices with shared authentication (JWT)
**Message Bus:** RabbitMQ for inter-service communication
**Database:** PostgreSQL (shared database with service-specific schemas)
**Cache:** Redis

---

## Services Overview

| Service | Port | Base URL | Status | Documentation |
|---------|------|----------|--------|---------------|
| **Auth Service** | 8100 | http://localhost:8100/api/v1 | ✅ Implemented | [README](../services/auth-service/README.md) |
| **Feed Service** | 8101 | http://localhost:8101/api/v1 | ✅ Implemented | [README](../services/feed-service/README.md) |
| **Content Analysis V2** | 8114 | http://localhost:8114 | ✅ Implemented | [README](../services/content-analysis-v2/README.md) |
| **Research Service** | 8103 | http://localhost:8103/api/v1 | ✅ Implemented | [README](../services/research-service/README.md) |
| **OSINT Service** | 8104 | http://localhost:8104/api/v1 | ✅ Implemented | [README](../services/osint-service/README.md) |
| **Notification Service** | 8105 | http://localhost:8105/api/v1 | 🚧 Planned | [README](../services/notification-service/README.md) |
| **Search Service** | 8106 | http://localhost:8106/api/v1 | 🚧 Planned | - |
| **Analytics Service** | 8107 | http://localhost:8107/api/v1 | 🚧 Planned | [README](../services/analytics-service/README.md) |
| **LLM Orchestrator** | 8109 | http://localhost:8109/api/v1 | ✅ Implemented | [README](../services/llm-orchestrator-service/README.md) |
| **Knowledge Graph** | 8111 | http://localhost:8111/api/v1 | ✅ Implemented | [API Docs](../api/knowledge-graph-service-api.md) |
| **Entity Canonicalization** | 8112 | http://localhost:8112/api/v1 | ✅ Implemented | [API Docs](../api/entity-canonicalization-service-api.md) |

---

## Authentication Flow

All services (except Auth Service public endpoints) require JWT authentication.

### 1. User Registration & Login

```mermaid
sequenceDiagram
    participant Client
    participant AuthService
    participant Database

    Client->>AuthService: POST /api/v1/auth/register
    AuthService->>Database: Create user
    Database-->>AuthService: User created
    AuthService-->>Client: 201 Created

    Client->>AuthService: POST /api/v1/auth/login
    AuthService->>Database: Validate credentials
    Database-->>AuthService: User validated
    AuthService-->>Client: 200 OK + JWT tokens
```

### 2. Authenticated API Requests

```mermaid
sequenceDiagram
    participant Client
    participant FeedService
    participant Database

    Client->>FeedService: GET /api/v1/feeds<br/>Authorization: Bearer <token>
    FeedService->>FeedService: Validate JWT signature
    FeedService->>Database: Fetch feeds for user
    Database-->>FeedService: Feeds data
    FeedService-->>Client: 200 OK + Feeds
```

### 3. Token Lifecycle

1. **Login:** POST `/api/v1/auth/login` → Returns access_token + refresh_token
2. **Use:** Include token in `Authorization: Bearer <token>` header
3. **Expiration:** Access token expires after 30 minutes (configurable)
4. **Refresh:** POST `/api/v1/auth/refresh` with refresh_token → Returns new access_token
5. **Logout:** POST `/api/v1/auth/logout` → Blacklists token in Redis

---

## API Request Patterns

### Standard Headers

**All Authenticated Requests:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

### Pagination

**Query Parameters:**
- `limit` - Number of items to return (default: 20, max: 100)
- `offset` - Number of items to skip (default: 0)

**Example:**
```http
GET /api/v1/feeds?limit=50&offset=100
```

**Response:**
```json
{
  "items": [...],
  "total": 250,
  "limit": 50,
  "offset": 100
}
```

### Filtering & Search

**Common Query Parameters:**
- `search` - Full-text search in title/description
- `created_after` - Filter by creation date (ISO 8601)
- `is_active` - Filter by active status (boolean)

**Example:**
```http
GET /api/v1/feeds?search=technology&is_active=true
```

### Sorting

**Query Parameters:**
- `sort_by` - Field to sort by
- `order` - Sort order (asc/desc)

**Example:**
```http
GET /api/v1/feeds?sort_by=created_at&order=desc
```

---

## Error Handling Standards

### Standard Error Response Format

```json
{
  "detail": "Human-readable error message",
  "type": "error_type_code"
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET/PUT request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Error Examples

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated",
  "type": "authentication_error"
}
```

**404 Not Found:**
```json
{
  "detail": "Feed not found",
  "type": "not_found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

---

## Service Details

### Auth Service (Port 8100)

**Purpose:** User authentication, JWT token management, user CRUD, API key management

#### Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login and get tokens | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| POST | `/api/v1/auth/logout` | Logout and blacklist token | Yes |
| GET | `/api/v1/auth/me` | Get current user profile | Yes |
| POST | `/api/v1/auth/api-keys` | Create API key | Yes |
| GET | `/api/v1/auth/api-keys` | List user's API keys | Yes |
| DELETE | `/api/v1/auth/api-keys/{id}` | Delete API key | Yes |
| GET | `/api/v1/users` | List all users (admin only) | Yes |
| GET | `/api/v1/users/{id}` | Get user by ID | Yes |
| PUT | `/api/v1/users/{id}` | Update user | Yes |

#### Example: Register User

```bash
curl -X POST http://localhost:8100/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### Example: Login

```bash
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Database Schema:**
- `users` - User accounts and credentials
- `roles` - Available roles (admin, user, moderator)
- `user_roles` - User-role associations
- `api_keys` - API keys for programmatic access
- `auth_audit_log` - Audit trail of authentication events

**Documentation:** [Auth Service README](../services/auth-service/README.md)

---

### Feed Service (Port 8101)

**Purpose:** RSS/Atom feed management, automatic fetching, entry storage, feed health monitoring

#### Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/feeds` | List all feeds with filters | Yes |
| POST | `/api/v1/feeds` | Create new feed | Yes |
| GET | `/api/v1/feeds/{id}` | Get feed by ID | Yes |
| PUT | `/api/v1/feeds/{id}` | Update feed | Yes |
| DELETE | `/api/v1/feeds/{id}` | Delete feed | Yes |
| POST | `/api/v1/feeds/{id}/fetch` | Trigger manual fetch | Yes |
| GET | `/api/v1/feeds/{id}/items` | Get feed items | Yes |
| GET | `/api/v1/feeds/{id}/health` | Get health metrics | Yes |
| GET | `/api/v1/feeds/{id}/quality` | Get quality score | Yes |
| POST | `/api/v1/feeds/bulk-fetch` | Bulk fetch feeds | Yes |

#### Example: Create Feed

```bash
curl -X POST http://localhost:8101/api/v1/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://feeds.bbci.co.uk/news/rss.xml",
    "title": "BBC News",
    "category": "news",
    "fetch_interval_minutes": 60
  }'
```

#### Example: Manual Fetch

```bash
curl -X POST http://localhost:8101/api/v1/feeds/{feed_id}/fetch \
  -H "Authorization: Bearer $TOKEN"
```

**Background Processing:**
- Celery scheduler fetches feeds every N minutes (configurable)
- Circuit breaker pattern prevents cascading failures
- Content deduplication using SHA-256 hashing

**Events Published:**
- `feed.created` - New feed added
- `feed.updated` - Feed configuration updated
- `feed.deleted` - Feed removed
- `article.created` - New article/item discovered
- `feed.fetch_completed` - Fetch completed successfully
- `feed.fetch_failed` - Fetch failed

**Database Schema:**
- `feeds` - Feed configurations and metadata
- `feed_items` - RSS/Atom entries (immutable)
- `fetch_log` - Fetch operation history
- `feed_health` - Health metrics and uptime
- `feed_categories` - Feed categorization
- `feed_schedules` - Custom cron schedules

**Documentation:** [Feed Service README](../services/feed-service/README.md)

---

### Content Analysis Service (Port 8102)

**Purpose:** AI-powered content analysis of feed entries using multiple LLM providers

#### Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/analyze` | Comprehensive content analysis | Yes |
| POST | `/api/v1/analyze/batch` | Batch analysis for multiple articles | Yes |
| GET | `/api/v1/analyze/{id}` | Get analysis result by ID | Yes |
| GET | `/api/v1/analyze/feed/{feed_id}` | Get all analyses for a feed | Yes |
| POST | `/api/v1/analyze/sentiment` | Sentiment analysis only | Yes |
| POST | `/api/v1/analyze/entities` | Entity extraction only | Yes |
| POST | `/api/v1/analyze/topics` | Topic classification only | Yes |
| POST | `/api/v1/analyze/summarize` | Generate summaries | Yes |
| POST | `/api/v1/analyze/facts` | Extract facts | Yes |
| POST | `/api/v1/analyze/keywords` | Extract keywords | Yes |

#### Example: Full Analysis

```bash
curl -X POST http://localhost:8102/api/v1/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your article content here...",
    "analysis_type": "full",
    "use_cache": true
  }'
```

#### Example: Sentiment Analysis

```bash
curl -X POST http://localhost:8102/api/v1/analyze/sentiment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your article content here...",
    "detect_bias": true,
    "detect_emotion": true
  }'
```

**LLM Providers:**
- OpenAI GPT-4 (primary)
- Anthropic Claude (alternative)
- Ollama (local models for development)

**Analysis Types:**
- **Sentiment Analysis:** Positive/Negative/Neutral with bias detection
- **Entity Extraction:** People, organizations, locations, dates
- **Topic Classification:** Automatic categorization
- **Summarization:** Short, medium, and long summaries
- **Fact Extraction:** Claims, statistics, quotes
- **Keyword Extraction:** Key terms and phrases

**Event Consumers:**
- Subscribes to `feed.new_entries` from Feed Service
- Analyzes content using configured LLM
- Publishes `content.analyzed` events

**Caching Strategy:**

| Analysis Type | Cache TTL | Rationale |
|--------------|-----------|-----------|
| Sentiment | 30 days | Content sentiment rarely changes |
| Entities | 14 days | Entities are stable |
| Topics | 14 days | Topics are stable |
| Summaries | 7 days | May want fresher summaries |
| Facts | 7 days | Facts may need verification |

**Database Schema:**
- `analysis_results` - Main analysis results and metadata
- `sentiment_analysis` - Detailed sentiment scores
- `extracted_entities` - Named entities
- `entity_relationships` - Relationships between entities
- `topic_classifications` - Topic categories
- `summaries` - Multi-length summaries
- `extracted_facts` - Claims, statistics, quotes

**Documentation:** [Content Analysis README](../services/content-analysis-service/README.md)

---

### Research Service (Port 8103)

**Purpose:** Perplexity AI integration for deep research queries on news content

#### Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/research` | Create research task | Yes |
| GET | `/api/v1/research/{id}` | Get research result | Yes |
| POST | `/api/v1/research/batch` | Batch research requests | Yes |
| GET | `/api/v1/research/feed/{feed_id}` | Get research for feed | Yes |
| GET | `/api/v1/research/history` | Get research history | Yes |
| GET | `/api/v1/research/stats` | Get usage statistics | Yes |
| POST | `/api/v1/templates` | Create template | Yes |
| GET | `/api/v1/templates` | List templates | Yes |
| GET | `/api/v1/templates/{id}` | Get template | Yes |
| PUT | `/api/v1/templates/{id}` | Update template | Yes |
| DELETE | `/api/v1/templates/{id}` | Delete template | Yes |
| POST | `/api/v1/templates/{id}/preview` | Preview template with variables | Yes |
| POST | `/api/v1/templates/{id}/apply` | Apply template and create research | Yes |

#### Example: Research Query

```bash
curl -X POST http://localhost:8103/api/v1/research \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze recent developments in AI regulation",
    "model": "sonar-pro",
    "max_results": 10
  }'
```

#### Example: Using Templates

```bash
curl -X POST http://localhost:8103/api/v1/templates/123/apply \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "topic": "Climate Change",
      "timeframe": "past month"
    }
  }'
```

**Perplexity Models:**

| Model | Cost per 1K tokens | Speed | Use Case |
|-------|-------------------|-------|----------|
| sonar | $0.005 | Fast | General research, news summaries |
| sonar-pro | $0.015 | Medium | Detailed analysis, complex queries |
| sonar-reasoning-pro | $0.025 | Slower | Deep research, multi-step reasoning |

**Cost Optimization:**
- 7-day result caching in Redis
- Intelligent model selection based on query complexity
- Rate limiting (10 requests/minute)
- Daily and monthly cost limits
- Cost tracking per user

**Database Schema:**
- `research_tasks` - Tracks all research queries
- `research_templates` - Reusable query templates
- `research_cache` - 7-day cache of results
- `cost_tracking` - Per-user cost monitoring

**Documentation:** [Research Service README](../services/research-service/README.md)

---

### OSINT Service (Port 8104)

**Purpose:** Open-Source Intelligence gathering and monitoring with 50+ pre-built templates

#### Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/templates/` | List all OSINT templates | Yes |
| GET | `/api/v1/templates/categories` | List template categories | Yes |
| GET | `/api/v1/templates/{name}` | Get specific template | Yes |
| GET | `/api/v1/templates/?search=query` | Search templates | Yes |
| POST | `/api/v1/templates/reload` | Reload templates from disk | Yes |
| POST | `/api/v1/schedules/` | Schedule template execution | Yes |
| GET | `/api/v1/schedules/` | List scheduled jobs | Yes |
| GET | `/api/v1/schedules/{job_id}` | Get job details | Yes |
| DELETE | `/api/v1/schedules/{job_id}` | Remove schedule | Yes |
| POST | `/api/v1/schedules/{job_id}/pause` | Pause job | Yes |
| POST | `/api/v1/schedules/{job_id}/resume` | Resume job | Yes |
| GET | `/api/v1/anomalies/baselines` | Get baseline statistics | Yes |
| GET | `/api/v1/anomalies/baselines/{template}/{metric}` | Get metric baseline | Yes |
| DELETE | `/api/v1/anomalies/baselines/{template}` | Reset baseline | Yes |
| GET | `/api/v1/alerts/` | List alerts (with filters) | Yes |
| GET | `/api/v1/alerts/stats` | Get alert statistics | Yes |
| GET | `/api/v1/alerts/{alert_id}` | Get specific alert | Yes |
| POST | `/api/v1/alerts/{alert_id}/acknowledge` | Acknowledge alert | Yes |

#### Example: Schedule Twitter Monitor

```bash
curl -X POST http://localhost:8104/api/v1/schedules/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "Twitter Account Monitoring",
    "parameters": {
      "username": "example_user",
      "monitor_followers": true
    },
    "trigger_type": "interval",
    "interval": "30m"
  }'
```

#### Example: Check Alerts

```bash
curl "http://localhost:8104/api/v1/alerts/?level=critical&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Template Categories (50+ templates):**
- **Social Media:** Twitter, LinkedIn, Facebook, Instagram, Reddit, YouTube, TikTok, Telegram, GitHub, Discord
- **Domain Analysis:** WHOIS, DNS, SSL certificates, website changes, technology stack
- **Threat Intelligence:** Malware hashes, IP reputation, CVE monitoring, phishing detection
- **Data Breach:** Have I Been Pwned, credential leaks, database leaks
- **Network Analysis:** Port scanning, subdomain enumeration, ASN monitoring
- **Email Analysis:** Email verification, header analysis, MX records
- **Dark Web:** Onion site monitoring, marketplace tracking
- **Cryptocurrency:** Wallet monitoring, exchange tracking
- **Geolocation:** IP geolocation, device tracking

**Features:**
- APScheduler 3.10+ for cron-based scheduling
- Z-score anomaly detection (configurable threshold)
- Multi-level alerting (info, warning, critical, emergency)
- Alert acknowledgement and statistics
- Template reload without service restart

**Database Schema:**
- `osint_templates` - Template definitions
- `osint_instances` - Scheduled monitoring instances
- `osint_executions` - Execution history
- `osint_data` - Collected intelligence data
- `osint_alerts` - Generated alerts
- `osint_correlations` - Data correlation tracking

**Documentation:** [OSINT Service README](../services/osint-service/README.md)

---

### Notification Service (Port 8105)

**Purpose:** Email, webhook, and push notifications for system events

**Status:** 🚧 Planned for Sprint 2

#### Planned Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/notifications` | List user notifications | Yes |
| POST | `/api/v1/notifications/preferences` | Set notification preferences | Yes |
| POST | `/api/v1/webhooks` | Register webhook | Yes |
| GET | `/api/v1/webhooks` | List user webhooks | Yes |
| DELETE | `/api/v1/webhooks/{id}` | Delete webhook | Yes |

**Planned Features:**
- Email notifications (SMTP)
- Webhook delivery
- Push notifications (Firebase)
- Notification preferences per user
- Template system for notifications
- Delivery tracking and retry logic

**Event Consumers:**
- `feed.new_entries` - New articles notification
- `content.analyzed` - Analysis complete notification
- `osint.alert` - OSINT alert notification
- `research.completed` - Research complete notification

---

### Search Service (Port 8106)

**Purpose:** Full-text search across feeds and entries

**Status:** 🚧 Planned for Sprint 2

#### Planned Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/search` | Full-text search | Yes |
| GET | `/api/v1/search/suggestions` | Search suggestions | Yes |
| POST | `/api/v1/search/index` | Reindex content | Yes |

**Planned Features:**
- Full-text search using PostgreSQL FTS
- Search suggestions based on history
- Filter by feed, date, sentiment, topics
- Search history tracking
- Relevance scoring

---

### Analytics Service (Port 8107)

**Purpose:** Usage metrics, statistics, and reporting

**Status:** 🚧 Planned for Sprint 3

#### Planned Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/analytics/dashboard` | Dashboard metrics | Yes |
| GET | `/api/v1/analytics/feeds/{id}/stats` | Feed statistics | Yes |
| GET | `/api/v1/analytics/users/{id}/activity` | User activity | Yes |

**Planned Features:**
- User engagement metrics
- Feed performance statistics
- LLM cost tracking
- System performance monitoring
- Custom dashboard builder

---

### Knowledge Graph Service (Port 8111)

**Purpose:** Neo4j-backed entity relationship graph with analytics and manual enrichment

**Status:** ✅ Implemented

#### Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/graph/analytics/stats` | Graph statistics (entity/relationship counts) | Yes |
| GET | `/api/v1/graph/analytics/top-entities` | Most connected entities | Yes |
| GET | `/api/v1/graph/analytics/growth-history` | Entity growth over time | Yes |
| GET | `/api/v1/graph/analytics/relationship-stats` | Relationship type distribution | Yes |
| GET | `/api/v1/graph/analytics/cross-article-coverage` | Cross-article entity statistics | Yes |
| GET | `/api/v1/graph/entities/{id}` | Get entity details | Yes |
| GET | `/api/v1/graph/entities/{id}/relationships` | Get entity relationships | Yes |
| POST | `/api/v1/graph/entities/search` | Search entities by name | Yes |
| POST | `/api/v1/graph/enrichment/analyze` | Analyze relationship for enrichment | Yes |
| POST | `/api/v1/graph/enrichment/execute-tool` | Execute enrichment tool | Yes |
| POST | `/api/v1/graph/enrichment/apply` | Apply enrichment changes | Yes |
| GET | `/api/v1/graph/health` | Service health check | No |
| GET | `/api/v1/graph/health/neo4j` | Neo4j connection health | Yes |
| GET | `/api/v1/graph/health/rabbitmq` | RabbitMQ connection health | Yes |

#### Example: Get Graph Statistics

```bash
curl -X GET http://localhost:8111/api/v1/graph/analytics/stats \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "total_entities": 3867,
  "total_relationships": 8542,
  "entity_types": {
    "PERSON": 1245,
    "ORGANIZATION": 892,
    "LOCATION": 654,
    "EVENT": 432,
    "PRODUCT": 321,
    "OTHER": 323
  },
  "relationship_types": {
    "WORKS_FOR": 1234,
    "LOCATED_IN": 892,
    "OWNS": 543,
    "RELATED_TO": 2341
  },
  "avg_connections_per_entity": 2.21
}
```

#### Example: Search Entities

```bash
curl -X POST http://localhost:8111/api/v1/graph/entities/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "United Nations",
    "entity_type": "ORGANIZATION",
    "limit": 10
  }'
```

**Neo4j Data Model:**
- Entity nodes: `(:Entity {name, type, wikidata_id, created_at, last_seen})`
- 28 relationship types: WORKS_FOR, LOCATED_IN, OWNS, etc.
- Idempotent MERGE queries prevent duplicates
- Mention count tracking per relationship

**RabbitMQ Integration:**
- Consumes `relationships.extracted` events from Content Analysis Service
- Exchange: `relationships_exchange` (topic)
- Queue: `relationships_queue` (durable)
- Ingestion: 15-50ms per triplet

**Database:** Neo4j graph database (bolt://neo4j:7687)

**Documentation:**
- API Docs: [knowledge-graph-service-api.md](../api/knowledge-graph-service-api.md)
- Service Docs: [knowledge-graph-service.md](../services/knowledge-graph-service.md)

---

### Entity Canonicalization Service (Port 8112)

**Purpose:** Entity deduplication and standardization with Wikidata enrichment

**Status:** ✅ Implemented

#### Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/canonicalization/canonicalize` | Canonicalize single entity | Yes |
| POST | `/api/v1/canonicalization/batch` | Batch canonicalize (up to 100) | Yes |
| GET | `/api/v1/canonicalization/{id}` | Get canonical entity by ID | Yes |
| GET | `/api/v1/canonicalization/search` | Search canonical entities | Yes |
| GET | `/api/v1/canonicalization/stats` | Service statistics | Yes |
| GET | `/api/v1/canonicalization/trends/entity-types` | Entity type growth trends | Yes |
| POST | `/api/v1/canonicalization/reprocess/start` | Start batch reprocessing | Yes |
| GET | `/api/v1/canonicalization/reprocess/status` | Get reprocessing status | Yes |
| POST | `/api/v1/canonicalization/reprocess/stop` | Stop batch reprocessing | Yes |

#### Example: Canonicalize Entity

```bash
curl -X POST http://localhost:8112/api/v1/canonicalization/canonicalize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "UN",
    "entity_type": "ORGANIZATION"
  }'
```

**Response:**
```json
{
  "canonical_entity": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "United Nations",
    "type": "ORGANIZATION",
    "wikidata_id": "Q1065",
    "aliases": ["UN", "U.N.", "United Nations Organization"]
  },
  "confidence": 0.95,
  "method": "fuzzy_match"
}
```

#### Example: Start Batch Reprocessing

```bash
curl -X POST http://localhost:8112/api/v1/canonicalization/reprocess/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": false
  }'
```

**Response (202 Accepted):**
```json
{
  "status": "started",
  "job_id": "660e8400-e29b-41d4-a716-446655440002",
  "dry_run": false,
  "message": "Batch reprocessing started"
}
```

**Canonicalization Pipeline (5 Stages):**
1. **Exact Match**: Cache lookup (2.1ms avg, 89% hit rate)
2. **Fuzzy Match**: Levenshtein distance < 0.8
3. **Semantic Match**: BERT embeddings, cosine similarity > 0.9
4. **Wikidata Lookup**: Q-ID enrichment (confidence > 0.8)
5. **Create New**: Fallback for unique entities

**Batch Reprocessing (6 Phases):**
1. Analyzing (0-10% progress)
2. Fuzzy Matching (10-40%)
3. Semantic Matching (40-50%)
4. Wikidata Lookup (50-70%)
5. Merging (70-80%)
6. Updating (80-100%)

**Performance:**
- Single canonicalization: 2-500ms (depends on stage)
- Batch reprocessing: ~8.5 minutes for 3,867 entities
- Cache hit rate: 89% (Stage 1 exact match)

**Results (First Batch Run):**
- Duplicates merged: 217 (5.6% of entities)
- Wikidata Q-IDs added: 1,200
- Coverage improved: 60% → 95%

**Database Schema:**
- `canonical_entities`: Canonical entity records
- `entity_aliases`: Alternative names for entities

**Documentation:**
- API Docs: [entity-canonicalization-service-api.md](../api/entity-canonicalization-service-api.md)
- Service Docs: [entity-canonicalization-service.md](../services/entity-canonicalization-service.md)

---

## Event-Driven Architecture

### RabbitMQ Integration

**Exchange:** `news.events`
**Exchange Type:** `topic`
**Routing Pattern:** `<service>.<event_type>`

### Key Events

#### feed.new_entries
**Published by:** Feed Service
**Consumed by:** Content Analysis, Notification, Search

**Payload:**
```json
{
  "event_type": "feed.new_entries",
  "service": "feed-service",
  "timestamp": "2025-10-15T10:30:00Z",
  "payload": {
    "feed_id": 123,
    "item_ids": [456, 457, 458],
    "items_count": 3
  }
}
```

#### article.created
**Published by:** Feed Service
**Consumed by:** Content Analysis, Notification

**Payload:**
```json
{
  "event_type": "article.created",
  "service": "feed-service",
  "timestamp": "2025-10-15T10:30:00Z",
  "payload": {
    "item_id": 456,
    "feed_id": 123,
    "title": "Article Title",
    "content": "Article content...",
    "url": "https://example.com/article",
    "published_at": "2025-10-15T09:00:00Z"
  }
}
```

#### content.analyzed
**Published by:** Content Analysis Service
**Consumed by:** Notification, Analytics

**Payload:**
```json
{
  "event_type": "content.analyzed",
  "service": "content-analysis-service",
  "timestamp": "2025-10-15T10:35:00Z",
  "payload": {
    "item_id": 456,
    "feed_id": 123,
    "analysis_id": 789,
    "analyses_completed": ["sentiment", "entities", "topics", "summary"],
    "sentiment": "positive",
    "entity_count": 12,
    "topic": "technology"
  }
}
```

**Full Event Catalog:** See [Event-Driven Architecture](EVENT_DRIVEN_ARCHITECTURE.md)

---

## Frontend Integration

### Quick Start (3 Steps)

**1. Authenticate:**
```javascript
const response = await fetch('http://localhost:8100/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'johndoe',
    password: 'SecurePassword123!'
  })
});
const { access_token, refresh_token } = await response.json();
```

**2. Store Tokens:**
```javascript
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);
```

**3. Make Authenticated Requests:**
```javascript
const token = localStorage.getItem('access_token');
const feeds = await fetch('http://localhost:8101/api/v1/feeds', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

**Token Refresh (when 401):**
```javascript
async function refreshToken() {
  const refresh_token = localStorage.getItem('refresh_token');
  const response = await fetch('http://localhost:8100/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });
  const { access_token } = await response.json();
  localStorage.setItem('access_token', access_token);
  return access_token;
}
```

---

## Development Setup

### Prerequisites
- Docker & Docker Compose v2.24+
- Python 3.12+
- PostgreSQL 15+
- RabbitMQ 3.12+
- Redis 7+

### Quick Start

```bash
# Clone repository
git clone <repo-url>
cd news-microservices

# Start infrastructure (PostgreSQL, RabbitMQ, Redis)
docker-compose up -d postgres rabbitmq redis

# Start all services (development mode with hot reload)
~/.local/bin/docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Detailed Setup:** See [Docker Setup Guide](DOCKER_SETUP.md)

---

## API Testing

### Using Swagger UI

Each service provides interactive API documentation:

- Auth Service: http://localhost:8100/docs
- Feed Service: http://localhost:8101/docs
- Content Analysis: http://localhost:8102/docs
- Research Service: http://localhost:8103/docs
- OSINT Service: http://localhost:8104/docs

### Using cURL

**Register User:**
```bash
curl -X POST http://localhost:8100/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

**Create Feed (with token):**
```bash
TOKEN="your-jwt-token"
curl -X POST http://localhost:8101/api/v1/feeds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://feeds.bbci.co.uk/news/rss.xml",
    "title": "BBC News"
  }'
```

---

## Rate Limiting

**Current Status:** Not implemented
**Planned:** Sprint 2

**Planned Limits:**
- Anonymous requests: 10 requests/minute
- Authenticated requests: 100 requests/minute
- Premium accounts: 1000 requests/minute

Implementation will use Redis with sliding window algorithm.

---

## Monitoring & Observability

**Health Checks:** All services expose `/health` endpoint

```bash
# Check service health
curl http://localhost:8100/health  # Auth Service
curl http://localhost:8101/health  # Feed Service
curl http://localhost:8102/health  # Content Analysis
```

**Logging:** Structured JSON logging to stdout

**Metrics:** Prometheus metrics at `/metrics` (Content Analysis implemented)

**RabbitMQ Management UI:** http://localhost:15673 (admin / rabbit_secret_2024)

**Planned (Sprint 3):**
- Grafana dashboards
- Distributed tracing with OpenTelemetry
- Alerting with Prometheus Alertmanager

---

## Support & Resources

- **Documentation:** `/docs` directory
- **Architecture:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)
- **Development Workflow:** [EFFICIENT_WORKFLOW.md](EFFICIENT_WORKFLOW.md)
- **Event Architecture:** [EVENT_DRIVEN_ARCHITECTURE.md](EVENT_DRIVEN_ARCHITECTURE.md)
- **Database Schema:** [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)
- **Docker Setup:** [DOCKER_SETUP.md](DOCKER_SETUP.md)

---

## Changelog

### Sprint 1 (Completed)
- ✅ Auth Service fully implemented
- ✅ Feed Service fully implemented with Celery background tasks
- ✅ Content Analysis Service with multi-LLM support
- ✅ Research Service with Perplexity AI integration
- ✅ OSINT Service with 50+ templates
- ✅ LLM Orchestrator Service with DIA (Dynamic Intelligence Augmentation)
- ✅ Knowledge Graph Service with Neo4j backend
- ✅ Entity Canonicalization Service with Wikidata enrichment
- ✅ RabbitMQ event-driven architecture
- ✅ Knowledge Graph Admin Dashboard (React frontend)

### Sprint 2 (Planned)
- 🚧 Notification Service
- 🚧 Search Service with full-text search
- 🚧 Rate limiting implementation
- 🚧 Frontend integration guide

### Sprint 3 (Planned)
- 🚧 Analytics Service
- 🚧 Prometheus + Grafana monitoring
- 🚧 OpenTelemetry distributed tracing
- 🚧 Kubernetes deployment manifests

---

**Last Updated:** 2025-10-24
**API Version:** v1
**Platform Version:** 1.2.0
**Services Implemented:** 8 of 11 (Auth, Feed, Content Analysis, Research, OSINT, LLM Orchestrator, Knowledge Graph, Entity Canonicalization)

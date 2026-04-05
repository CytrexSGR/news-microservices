# Database Architecture Analysis
**Date:** 2025-10-22
**Status:** Current State Documentation
**Database:** Shared PostgreSQL `news_mcp` (41 tables)

## Executive Summary

The news-microservices system currently uses a **shared database architecture** where all services access a single PostgreSQL database (`news_mcp`). While this simplifies development and cross-service queries, it creates tight coupling and violates microservices database isolation principles.

**Critical Finding:** Multiple services directly query tables "owned" by other services, creating implicit dependencies that prevent independent deployment and scaling.

---

## Service-Table Ownership Matrix

### 🔐 Auth Service (Port 8100)
**Owned Tables:**
- `users` - User accounts and authentication
- `roles` - Role definitions (admin, user, etc.)
- `user_roles` - User-role associations
- `api_keys` - API key management
- `auth_audit_log` - Authentication event logging

**Cross-Service Reads:** None identified
**Cross-Service Writes:** None
**Architecture Pattern:** ✅ Clean - No cross-service dependencies

---

### 📡 Feed Service (Port 8101)
**Owned Tables:**
- `feeds` - RSS/Atom feed configurations
- `feed_items` - Article entries from feeds
- `fetch_log` - Feed fetch operation history
- `feed_health` - Feed reliability metrics
- `feed_categories` - Feed organization/categorization
- `feed_schedules` - Custom cron-based fetch schedules
- `feed_assessment_history` - Feed credibility assessment history
- `admiralty_code_thresholds` - Quality score thresholds
- `quality_score_weights` - Quality calculation weights

**Cross-Service Reads:**
- ⚠️ **READS from content-analysis-service tables:**
  - `analysis_results` (via `analysis_loader.py:40-48`)
  - `sentiment_analysis` (via `analysis_loader.py:60-88`)
  - `finance_sentiment` (via `analysis_loader.py:90-116`)
  - `geopolitical_sentiment` (via `analysis_loader.py:118-151`)
  - `category_classification` (via `analysis_loader.py:40-58`)
  - `event_analyses` (via `analysis_loader.py:153-187`)
  - `summaries` (via `analysis_loader.py:189-215`)
  - `topic_classifications` (via `analysis_loader.py:217-243`)
  - `extracted_entities` (inferred from loader pattern)

**Method:** Direct SQL queries via SQLAlchemy `text()` - bypasses ORM

**Justification Found in Code:**
```python
# services/feed-service/app/services/analysis_loader.py:13-28
async def load_analysis_data(db: AsyncSession, item_id: UUID) -> Dict[str, Any]:
    """
    Load ALL analysis data for a feed item.
    Returns a dict with all fields from:
    - category_analysis, sentiment_analysis, finance_sentiment,
    - geopolitical_sentiment, event_analysis, summaries, topic_classifications
    """
```

**Architecture Pattern:** ❌ **ANTI-PATTERN** - Direct cross-service database access

---

### 🧠 Content-Analysis Service (Port 8102)
**Owned Tables:**
- `analysis_results` - Central tracking table (article_id → analysis_id)
- `sentiment_analysis` - Standard sentiment analysis results
- `finance_sentiment` - Financial market sentiment analysis
- `geopolitical_sentiment` - Geopolitical stability analysis
- `category_classification` - Article categorization (6 categories)
- `event_analyses` - OSINT event analysis (Admiralty Code)
- `extracted_entities` - Named entity extraction (persons, orgs, locations)
- `entity_relationships` - Relationships between entities
- `extracted_facts` - Key facts and claims extraction
- `summaries` - Article summaries (multiple types)
- `topic_classifications` - Topic/keyword classification
- `analysis_job_queue` - Background job queue

**Cross-Service Reads:**
- ⚠️ **READS from feed-service tables:**
  - `feeds` (to get analysis configuration flags)
  - `feed_items` (to get article content)

**Example:**
```python
# services/content-analysis-service/app/services/message_handler.py:96-111
result = config_db.execute(
    text("""
        SELECT
            f.enable_summary, f.enable_entity_extraction,
            f.enable_topic_classification, f.enable_categorization,
            f.enable_finance_sentiment, f.enable_geopolitical_sentiment,
            f.enable_osint_analysis
        FROM feed_items fi
        JOIN feeds f ON fi.feed_id = f.id
        WHERE fi.id = :item_id
    """),
    {"item_id": item_id}
)
```

**Architecture Pattern:** ❌ **ANTI-PATTERN** - Reads feed configuration directly instead of receiving via event

---

### 📊 Analytics Service (Port 8107)
**Owned Tables:**
- `analytics_metrics` - Time-series metrics storage
- `analytics_reports` - Generated reports
- `analytics_dashboards` - Custom user dashboards
- `analytics_alerts` - Alert configurations

**Cross-Service Reads:**
- ⚠️ **Suspected cross-service reads** (not yet analyzed in detail)
- Likely reads from: `feeds`, `feed_items`, `analysis_results` for metrics

**Architecture Pattern:** ⚠️ **NEEDS INVESTIGATION**

---

### 🔍 Research Service (Port 8103)
**Owned Tables:**
- `research_tasks` - Perplexity research tasks
- `research_templates` - Reusable research templates
- `research_cache` - Cached research results
- `research_runs` - Automated/scheduled research runs
- `cost_tracking` - API cost tracking

**Cross-Service Reads:**
- ⚠️ **Writes assessment data to feed-service:**
  - Updates `feeds.assessment_status`, `feeds.assessment_date`, etc.
  - Creates entries in `feed_assessment_history`

**Architecture Pattern:** ❌ **ANTI-PATTERN** - Writes to feed-service tables

---

### 🔔 Notification Service (Port 8105)
**Owned Tables:**
- `notification_preferences` - User notification settings
- `notification_templates` - Message templates
- `notification_logs` - Notification history
- `delivery_attempts` - Delivery tracking

**Cross-Service Reads:** Not yet analyzed
**Architecture Pattern:** ⚠️ **NEEDS INVESTIGATION**

---

## Critical Cross-Service Dependencies

### 1. Feed-Service ➔ Content-Analysis Tables
**Impact:** HIGH
**Files:** `services/feed-service/app/services/analysis_loader.py`
**Method:** Direct SQL queries via SQLAlchemy `text()`

**Problem:**
- Feed-service cannot be deployed independently of content-analysis-service
- Schema changes in content-analysis break feed-service
- No API contract - implicit coupling via database schema

**Evidence:**
```python
# Feed-service directly queries content-analysis tables
query = text("""
    SELECT sa.overall_sentiment, sa.confidence, ...
    FROM sentiment_analysis sa
    JOIN analysis_results ar ON sa.analysis_id = ar.id
    WHERE ar.article_id = :item_id
""")
```

**Why This Exists:**
- Frontend expects feed items WITH analysis data in single response
- Avoids N+1 query problem (fetching analysis for each article separately)
- Performance optimization at cost of architectural purity

---

### 2. Content-Analysis-Service ➔ Feed Configuration
**Impact:** MEDIUM
**Files:** `services/content-analysis-service/app/services/message_handler.py`
**Method:** Direct SQL queries to `feeds` table

**Problem:**
- Content-analysis needs feed configuration (which analyses to run)
- Currently queries `feeds` table directly instead of receiving via event

**Current Flow:**
1. Event: `article.created` with `feed_id` and `item_id`
2. Content-analysis queries database to get feed configuration
3. Runs enabled analyses based on flags

**Better Flow:**
1. Event: `article.created` with `feed_id`, `item_id`, AND `analysis_config`
2. Content-analysis uses config from event
3. No database query to feed-service tables

---

### 3. Research-Service ➔ Feed Assessment Storage
**Impact:** LOW
**Files:** Research-service API routes (not yet analyzed in detail)
**Method:** Writes to `feeds` table and `feed_assessment_history`

**Problem:**
- Research-service writes assessment results to feed-service tables
- Creates bidirectional dependency

**Better Flow:**
1. Research-service stores assessment in its own table
2. Publishes event: `feed.assessment.completed`
3. Feed-service subscribes and updates own tables

---

## Database Design Patterns Found

### ✅ Good Patterns

1. **Foreign Key Chain for Analysis Data:**
   ```
   feed_items.id ← analysis_results.article_id ← sentiment_analysis.analysis_id
   ```
   - Central `analysis_results` table tracks all analyses for an article
   - Each analysis type in separate table (normalized)
   - `ORDER BY created_at DESC LIMIT 1` handles duplicates gracefully

2. **Append-Only Feed Items:**
   - `feed_items` has no `updated_at` - immutable once created
   - Content hash prevents duplicates
   - Simplifies caching and replication

3. **Audit Logging:**
   - `auth_audit_log` tracks all authentication events
   - `fetch_log` tracks all feed fetch operations
   - Good for debugging and compliance

### ❌ Anti-Patterns

1. **Shared Database Across Services:**
   - All services connect to same `news_mcp` database
   - No isolation - schema changes affect multiple services
   - Cannot scale services independently

2. **Direct Cross-Service SQL Queries:**
   - Feed-service reads content-analysis tables
   - Content-analysis reads feed tables
   - Research-service writes to feed tables
   - Creates tight coupling, prevents independent deployment

3. **Missing Event-Carried State Transfer:**
   - Events don't carry enough data (e.g., feed config not in `article.created`)
   - Forces consumers to query database
   - Violates event sourcing best practices

4. **Duplicate Analysis Entries (700+ found):**
   - No duplicate check before running analyses
   - If event received multiple times → analyses run multiple times
   - Wastes storage, API costs, query performance

---

## Microservices Database Best Practices Comparison

### Industry Standard: Database-Per-Service
**What it is:**
- Each microservice has its own database
- No shared tables between services
- Cross-service data access ONLY via APIs or events

**Benefits:**
- Independent deployment and scaling
- Schema changes don't affect other services
- Technology flexibility (different DB types per service)
- Clear ownership and responsibility

**Drawbacks:**
- Distributed transactions are complex
- JOINs across services require multiple queries or denormalization
- Data consistency requires eventual consistency patterns

### Current Implementation: Shared Database
**What we have:**
- Single PostgreSQL database `news_mcp`
- All services connect with same credentials
- Direct SQL queries across service boundaries

**Benefits:**
- Simple development (no distributed queries)
- ACID transactions across services
- Easy JOINs for analytics

**Drawbacks:**
- Cannot deploy services independently
- Schema changes affect multiple services
- Scaling bottleneck (single database)
- Unclear ownership of tables

---

## Migration Path Options

### Option 1: Keep Shared DB, Add API Layer
**Effort:** LOW
**Risk:** LOW

**Changes:**
1. Feed-service exposes API: `GET /api/v1/analysis/{item_id}`
2. Content-analysis exposes API: `GET /api/v1/feeds/{feed_id}/config`
3. Replace direct SQL queries with HTTP calls
4. Keep shared database for now

**Pros:**
- Minimal code changes
- Establishes clear service boundaries via APIs
- Prepares for future database separation

**Cons:**
- Still coupled at database level
- Performance impact (HTTP calls vs SQL)
- Doesn't solve scaling issues

---

### Option 2: Database-Per-Service with Event Sourcing
**Effort:** HIGH
**Risk:** HIGH

**Changes:**
1. Create separate databases: `news_auth`, `news_feeds`, `news_analysis`, etc.
2. Migrate tables to respective databases
3. Implement event-carried state transfer
4. Add read models (denormalization) for cross-service queries
5. Implement saga pattern for distributed transactions

**Example:**
```
Event: article.created
{
  "item_id": "...",
  "feed_id": "...",
  "title": "...",
  "content": "...",
  "analysis_config": {          ← Carry state in event
    "enable_sentiment": true,
    "enable_finance": true,
    ...
  }
}
```

**Pros:**
- True microservices architecture
- Independent scaling and deployment
- Clear ownership and isolation

**Cons:**
- Complex migration (6-8 weeks)
- Eventual consistency challenges
- Need to rewrite queries that JOIN across services

---

### Option 3: Hybrid - Separate Critical Services Only
**Effort:** MEDIUM
**Risk:** MEDIUM

**Changes:**
1. Separate `news_auth` database first (auth-service)
2. Keep `news_mcp` for feeds + analysis (read-heavy, tightly coupled)
3. Separate `news_analytics` later when scaling needed

**Pros:**
- Gradual migration, lower risk
- Auth service isolated (security benefit)
- Keep performance-critical JOINs in shared DB

**Cons:**
- Still partial coupling
- Need to decide where to draw boundaries

---

## Recommendations

### Immediate Actions (This Sprint)

1. **Document Current State** ✅ (This document)
   - Service-table ownership matrix
   - Cross-service dependencies
   - Anti-patterns identified

2. **Add Duplicate Prevention in Content-Analysis**
   - Check if analysis already exists before running
   - Prevents 700+ redundant entries issue
   - File: `services/content-analysis-service/app/services/message_handler.py`

3. **Enrich Event with Feed Configuration**
   - Add `analysis_config` to `article.created` event
   - Eliminates content-analysis → feed database query
   - File: `services/feed-service/app/services/feed_fetcher.py:289`

### Medium-Term (Next 2-4 Weeks)

4. **Create Feed-Service Analysis API**
   - Endpoint: `GET /api/v1/feeds/items/{item_id}/analysis`
   - Returns analysis data (currently loaded via direct SQL)
   - Establishes API contract

5. **Migrate Feed-Service to Use Analysis API**
   - Replace `analysis_loader.py` direct SQL queries
   - Call content-analysis-service HTTP API
   - Measures: Add caching, batch requests for performance

6. **Create ADR for Database Strategy**
   - Document decision: Shared DB vs Database-Per-Service
   - Evaluate trade-offs for this specific system
   - Define migration timeline if separation chosen

### Long-Term (2-3 Months)

7. **Evaluate Analytics Service Pattern**
   - Determine if analytics needs real-time JOINs
   - Consider read replicas or materialized views
   - May use CQRS pattern (separate read/write models)

8. **Implement Event-Carried State Transfer**
   - All events carry necessary data
   - Services don't query other services' databases
   - Foundation for database separation

9. **Gradual Database Separation**
   - Start with auth-service (clear boundary)
   - Evaluate performance impact
   - Continue with other services based on results

---

## Appendix: Full Table List (41 Tables)

### Auth Domain (5 tables)
- users, roles, user_roles, api_keys, auth_audit_log

### Feed Domain (9 tables)
- feeds, feed_items, fetch_log, feed_health, feed_categories
- feed_schedules, feed_assessment_history
- admiralty_code_thresholds, quality_score_weights

### Analysis Domain (12 tables)
- analysis_results, analysis_job_queue
- sentiment_analysis, finance_sentiment, geopolitical_sentiment
- category_classification, event_analyses
- extracted_entities, entity_relationships, extracted_facts
- summaries, topic_classifications

### Analytics Domain (4 tables)
- analytics_metrics, analytics_reports, analytics_dashboards, analytics_alerts

### Research Domain (5 tables)
- research_tasks, research_templates, research_cache, research_runs, cost_tracking

### Notification Domain (4 tables)
- notification_preferences, notification_templates, notification_logs, delivery_attempts

### System (2 tables)
- alembic_version (migrations)
- feed_schedule_state (scheduler state)

---

## References

- **Code Evidence:** All file paths and line numbers verified as of 2025-10-22
- **Previous Incident:** ADR-009 - Event publishing race condition (fixed)
- **Related Docs:**
  - `docs/services/feed-service.md`
  - `docs/services/content-analysis-service.md`
  - `POSTMORTEMS.md` - Frontend rebuild incident

---

**Next Steps:** Create ADR-010 documenting database architecture decision.

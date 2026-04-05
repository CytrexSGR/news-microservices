# Changelog

All notable changes to the News Microservices platform.

## [Unreleased] - 2025-10-24

### Added - LLM Orchestrator Service & DIA System (Phase 1)

**Feature:** Dynamic Intelligence Augmentation (DIA) system for AI-powered content verification

**Components:**
- New service: `llm-orchestrator-service` (Port 8109)
- Two-stage LLM planning architecture:
  - Stage 1: Root Cause Analysis (GPT-4o-mini, temp 0.3)
  - Stage 2: Plan Generation (GPT-4o-mini, temp 0.2)
- RabbitMQ event-driven architecture:
  - Exchange: `verification_exchange` (topic)
  - Queue: `verification_queue` (durable, with DLQ)
  - Routing key: `verification.required.*`
- Event schema: `models/verification_events.py` (Pydantic models)
- System prompts for analytical reasoning and structured planning
- Health check and readiness endpoints

**Integration:**
- Consumes `verification.required` events from content-analysis-service
- Triggered when UQ confidence score < 0.65
- Transforms vague uncertainty factors into precise problem hypotheses
- Generates structured, executable verification plans

**Architecture:**
```
Content Analysis → RabbitMQ → LLM Orchestrator → [Verifier - Phase 2]
                              (Stage 1 + Stage 2)
```

**Performance:**
- Stage 1 latency: 3-5 seconds (root cause analysis)
- Stage 2 latency: 4-6 seconds (plan generation)
- Total processing: 7-11 seconds per verification
- Retry logic: 3 attempts with exponential backoff

**Configuration:**
```bash
PORT=8109
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
DIA_STAGE1_TEMPERATURE=0.3
DIA_STAGE2_TEMPERATURE=0.2
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

**Documentation:**
- ADR-018: DIA-Planner & Verifier Architecture
- Service docs: `docs/services/llm-orchestrator-service.md`
- API docs: `docs/api/llm-orchestrator-api.md`
- Setup script: `scripts/setup-rabbitmq.sh`
- Test script: `scripts/test_dia_planner.py`

**Testing:**
- Integration test with Tesla earnings example (factual error detection)
- Stage 1 output: `hypothesis_type=factual_error` (confidence: 0.85)
- Stage 2 output: 3 verification methods, critical priority
- Adversarial test framework integration (Phase 3)

**Git Commits:**
- Service creation: Phase 1.1-1.6
- Port conflict fix: scraping-service (8009:8009)
- RabbitMQ credentials: guest:guest
- Pydantic validation: Stage 2 prompt fix

**Refs:**
- ADR-016: Uncertainty Quantification Module
- ADR-017: Adversarial Test Framework
- models/adversarial_test_case.py (VerificationPlan schema)

### Added - Entity Canonicalization Service

**Feature:** Deduplicate and standardize entity names with Wikidata enrichment

**Components:**
- New service: `entity-canonicalization-service` (Port 8112)
- 5-stage canonicalization pipeline:
  1. Exact Match (cache lookup, 2.1ms avg, 89% hit rate)
  2. Fuzzy Match (Levenshtein distance < 0.8)
  3. Semantic Match (BERT embeddings, cosine > 0.9)
  4. Wikidata Lookup (Q-ID enrichment, confidence > 0.8)
  5. Create New (fallback for unique entities)
- Batch reprocessing with 6 phases:
  - Analyzing → Fuzzy Matching → Semantic Matching → Wikidata Lookup → Merging → Updating
  - Dry-run support for safe preview
  - Real-time progress tracking (0-100%)
  - Graceful stop capability
- PostgreSQL storage:
  - `canonical_entities` table (3,867 entities)
  - `entity_aliases` table (12,000+ aliases)
  - Indexes on name, type, wikidata_id

**API Endpoints:**
```
POST   /api/v1/canonicalization/canonicalize         # Single entity canonicalization
POST   /api/v1/canonicalization/batch                # Batch canonicalization (up to 100)
GET    /api/v1/canonicalization/{id}                 # Get canonical entity
GET    /api/v1/canonicalization/search               # Search by name/type
GET    /api/v1/canonicalization/stats                # Service statistics
GET    /api/v1/canonicalization/trends/entity-types  # Entity type growth trends
POST   /api/v1/canonicalization/reprocess/start      # Start batch reprocessing
GET    /api/v1/canonicalization/reprocess/status     # Check job status
POST   /api/v1/canonicalization/reprocess/stop       # Stop running job
```

**Performance:**
- Stage 1 (Exact Match): 2.1ms average, 89% success rate
- Stage 2 (Fuzzy Match): 15-30ms per entity
- Stage 3 (Semantic): 50-100ms per entity (embedding generation)
- Stage 4 (Wikidata): 200-500ms per entity (API latency)
- Batch reprocessing: 8.5 minutes for 3,867 entities

**Results (First Batch Run):**
- Duplicates merged: 217 (5.6% of entities)
- Wikidata Q-IDs added: 1,200 (coverage 60% → 95%)
- Processing time: 8 minutes 32 seconds
- Errors: 23 (failed Wikidata lookups)

**Configuration:**
```bash
PORT=8112
DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp
WIKIDATA_API_URL=https://www.wikidata.org/w/api.php
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
FUZZY_MATCH_THRESHOLD=0.8
SEMANTIC_MATCH_THRESHOLD=0.9
```

**Documentation:**
- ADR-020: Batch Reprocessing Implementation
- Service docs: `docs/services/entity-canonicalization-service.md`
- API docs: `docs/api/entity-canonicalization-service-api.md`

**Integration:**
- Used by content-analysis-service for entity extraction
- Provides canonical names for knowledge graph ingestion
- Ensures consistent entity references across articles

---

### Added - Knowledge Graph Service

**Feature:** Neo4j-backed knowledge graph for entity relationships and graph analytics

**Components:**
- New service: `knowledge-graph-service` (Port 8111)
- Neo4j graph database integration:
  - Entity nodes: 3,867 (PERSON, ORGANIZATION, LOCATION, EVENT, PRODUCT, OTHER)
  - Relationship types: 28 (WORKS_FOR, LOCATED_IN, OWNS, etc.)
  - Idempotent MERGE queries (prevents duplicates)
- RabbitMQ event-driven ingestion:
  - Exchange: `relationships_exchange` (topic)
  - Queue: `relationships_queue` (durable)
  - Consumes `relationships.extracted` events
  - 15-50ms per triplet ingestion
- Manual enrichment workflow:
  1. Analyze relationship (LLM-powered suggestions)
  2. Execute enrichment tool (Wikidata, web search)
  3. Apply changes to graph
- Health checks: Neo4j, RabbitMQ, Service

**API Endpoints:**
```
# Analytics
GET    /api/v1/graph/analytics/stats                    # Graph statistics
GET    /api/v1/graph/analytics/top-entities             # Most connected entities
GET    /api/v1/graph/analytics/growth-history           # Entity growth over time
GET    /api/v1/graph/analytics/relationship-stats       # Relationship type distribution
GET    /api/v1/graph/analytics/cross-article-coverage   # Cross-article entity stats

# Graph Queries
GET    /api/v1/graph/entities/{id}                      # Get entity details
GET    /api/v1/graph/entities/{id}/relationships        # Get entity relationships
POST   /api/v1/graph/entities/search                    # Search entities by name

# Manual Enrichment
POST   /api/v1/graph/enrichment/analyze                 # Analyze relationship
POST   /api/v1/graph/enrichment/execute-tool            # Execute enrichment tool
POST   /api/v1/graph/enrichment/apply                   # Apply changes

# Health
GET    /api/v1/graph/health                             # Service health
GET    /api/v1/graph/health/neo4j                       # Neo4j connection
GET    /api/v1/graph/health/rabbitmq                    # RabbitMQ connection
```

**Neo4j Data Model:**
```cypher
// Entity Node
(:Entity {
  name: STRING,
  type: ENUM,
  wikidata_id: STRING,
  created_at: DATETIME,
  last_seen: DATETIME
})

// Relationship Example
(subject:Entity)-[rel:WORKS_FOR {
  confidence: FLOAT,
  mention_count: INT,
  first_seen: DATETIME,
  last_updated: DATETIME
}]->(object:Entity)
```

**Performance:**
- Ingestion: 15-50ms per triplet
- Analytics queries: 50-200ms
- Entity search: 10-30ms (indexed)
- Manual enrichment: 2-5 seconds (LLM latency)

**Known Limitations:**
- ⚠️ Article nodes NOT implemented (graph contains only Entity nodes)
- Impact: `cross-article-coverage` endpoint returns empty data
- Required: Add Article nodes with EXTRACTED_FROM relationships

**Configuration:**
```bash
PORT=8111
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
OPENAI_API_KEY=sk-proj-...  # For manual enrichment
```

**Documentation:**
- Service docs: `docs/services/knowledge-graph-service.md`
- API docs: `docs/api/knowledge-graph-service-api.md`

**Integration:**
- Consumes entity relationships from content-analysis-service
- Provides graph analytics for admin dashboard
- Enables entity-centric article discovery (future)

---

### Added - Knowledge Graph Admin Dashboard

**Feature:** React admin interface for monitoring and managing Knowledge Graph and Entity Canonicalization

**Components:**
- Frontend location: `frontend/src/pages/admin/KnowledgeGraphAdminPage.tsx`
- 4 main tabs:
  1. **Live Operations** - Service health monitoring
  2. **Statistics & Analytics** - Graph metrics and trends (3 sub-tabs)
  3. **Manual Enrichment** - LLM-assisted relationship improvement
  4. **Graph Explorer** - Phase 3 (disabled)

**Key Features:**

**Tab 1: Live Operations**
- ServiceHealthCard (auto-refresh 10s)
- GraphStatsCard (3,867 entities, 28 relationship types)
- Neo4jHealthCard (connection status, version)
- RabbitMQHealthCard (queue status, message counts)

**Tab 2: Statistics & Analytics**

*Sub-Tab 2.1: Graph Metrics*
- Top Entities by connection count (filterable by type)
- Relationship Statistics (distribution by type)
- Entity type breakdown

*Sub-Tab 2.2: Canonicalization*
- **BatchReprocessing Component** (4 states):
  - Idle: Start button, dry-run checkbox
  - Running: Live progress bar (0-100%), phase indicator, stop button
  - Completed: Results summary, run again button
  - Failed: Error message, try again button
- Smart polling: 2s when running, stops when idle
- Force polling: 1s for 30s after start (catches fast jobs)
- CanonicalizationStatsCard (merge stats, Q-ID coverage)
- EntityMergeHistory (⚠️ Mock - event logging missing)
- DisambiguationQuality (⚠️ Mock - quality tracking missing)

*Sub-Tab 2.3: Trends*
- GrowthHistoryChart (30-day entity growth)
- **EntityTypeTrends Component** (✅ Real API data):
  - Multi-line chart showing entity type growth over time
  - 6 entity types tracked (PERSON, ORGANIZATION, LOCATION, EVENT, PRODUCT, OTHER)
  - Configurable time range (7/30/90 days)
  - Color-coded lines with legend
- CrossArticleCoverage (⚠️ Mock - Article nodes missing)

**Tab 3: Manual Enrichment**
- 3-step workflow: Analyze → Execute Tool → Apply
- LLM-powered relationship suggestions
- Wikidata and web search tools
- Real-time preview before applying

**Mock Data Strategy:**
- 3 components display mock data with clear warnings
- Yellow alert banners: "⚠️ Mock Data - Backend Feature Missing"
- Warnings explain what's missing and required implementation
- Status tracking: `frontend/MOCK_DATA_STATUS.md`

**React Query Hooks:**
- `useServiceHealth` (10s refresh)
- `useGraphStats` (30s refresh)
- `useReprocessingStatus` (smart polling: 2s when running, stop when idle)
- `useEntityTypeTrends` (60s refresh, real API data)
- All hooks support manual refetch and error handling

**Technology Stack:**
- React 18 + TypeScript
- TanStack Query (React Query) for data fetching
- Recharts for data visualization
- Tailwind CSS + shadcn/ui components
- Lucide React icons

**Configuration:**
```bash
VITE_ENTITY_CANONICALIZATION_API_URL=http://localhost:8112/api/v1
VITE_KNOWLEDGE_GRAPH_API_URL=http://localhost:8111/api/v1
```

**Documentation:**
- ADR-019: Mock Data Strategy
- Frontend docs: `docs/frontend/knowledge-graph-admin-dashboard.md`
- Mock status: `frontend/MOCK_DATA_STATUS.md`

**User Experience:**
- Transparent mock data indication
- Real-time progress tracking for long-running jobs
- Auto-refresh with smart polling (stops when not needed)
- Responsive design for desktop and mobile

---

### Documentation

**Architecture Decision Records:**
- **ADR-019**: Mock Data Strategy in Admin Dashboards
  - Context: Incremental backend development requires UI-first approach
  - Decision: Use yellow warning banners to indicate mock data
  - Consequences: Transparent UX, parallel development, easy migration
  - Location: `docs/decisions/ADR-019-mock-data-strategy.md`

- **ADR-020**: Batch Reprocessing Implementation
  - Context: 217 duplicate entities, 1,547 missing Q-IDs
  - Decision: 6-phase pipeline with dry-run and progress tracking
  - Performance: 8.5 minutes for 3,867 entities
  - Results: 95% Wikidata coverage, zero duplicates
  - Location: `docs/decisions/ADR-020-batch-reprocessing-implementation.md`

**Service Documentation:**
- Entity Canonicalization Service: `docs/services/entity-canonicalization-service.md` (1,500 lines)
- Knowledge Graph Service: `docs/services/knowledge-graph-service.md` (2,100 lines)

**API Documentation:**
- Entity Canonicalization API: `docs/api/entity-canonicalization-service-api.md` (1,200 lines)
- Knowledge Graph API: `docs/api/knowledge-graph-service-api.md` (1,300 lines)

**Frontend Documentation:**
- Knowledge Graph Admin Dashboard: `docs/frontend/knowledge-graph-admin-dashboard.md` (1,800 lines)
- Mock Data Status: `frontend/MOCK_DATA_STATUS.md`

**Total Documentation:** 8+ documents, ~9,000 lines of comprehensive technical documentation

## [Unreleased] - 2025-10-22

### Removed
- **auth-service-v2** - Duplicate authentication service
  - Lightweight stateless prototype, never used in production
  - 392 LOC, 13 files removed (584 deletions)
  - Main auth-service remains as canonical authentication service
  - Reason: Duplicate functionality, no active development, creates confusion
  - Backup: `/home/cytrex/backups/auth-service-v2-archive-20251022.tar.gz`
  - Git commits: Deprecation (6893120), Removal (44e2042)
  - Incident report: `docs/incidents/2025-10-22-auth-service-v2-removal.md`
  - Refs: Phase 1, Task 1 of `docs/refactoring/REFACTORING-ANALYSIS-2025-10-22.md`

## [1.2.0] - 2025-10-22

### Added - Newspaper4k Intelligent Scraping Integration

**Feature:** NLP-powered article extraction with automatic cookie banner handling

**Components:**
- Newspaper4k integration in scraping-service (replaces httpx)
- Per-feed configurable failure thresholds (1-20, default: 5)
- Automatic metadata extraction (authors, images, publish dates)
- Feed-level failure tracking with auto-disable
- New API endpoints for threshold management and reset
- Enhanced JSONB metadata storage in feed_items

**Scraping Methods:**
- `newspaper4k` (default) - NLP-based extraction, 80-90% success rate, automatic cookie handling
- `playwright` - Headless browser for JavaScript-heavy sites, 95%+ success rate

**New API Endpoints:**
- `GET /api/v1/feeds/{feed_id}/threshold` - Get scraping threshold configuration
- `POST /api/v1/feeds/{feed_id}/scraping/reset` - Reset failure counter and re-enable scraping

**Database Changes:**
```sql
-- Migration: 20251022_010_add_scraping_enhancements.py
ALTER TABLE feeds ADD COLUMN scrape_failure_threshold INTEGER DEFAULT 5;
ALTER TABLE feed_items ADD COLUMN scraped_metadata JSONB;
CREATE INDEX ix_feed_items_scraped_metadata ON feed_items USING gin (scraped_metadata);

-- Migrate existing methods
UPDATE feeds SET scrape_method = 'newspaper4k' WHERE scrape_method IN ('auto', 'httpx');
```

**Schema Updates:**
- `FeedBase.scrape_method`: Now validates `^(newspaper4k|playwright)$` pattern
- `FeedBase.scrape_failure_threshold`: New field with `ge=1, le=20` validation
- `FeedResponse`: Added failure tracking fields (count, timestamp, reason)
- `FeedItemResponse.scraped_metadata`: JSONB field for newspaper4k extras

**Performance Improvements:**
- 80-90% success rate (up from 30-40% with httpx)
- Automatic cookie banner handling (no manual intervention)
- 200-800ms avg scraping time (vs 2-5s with Playwright)
- Low memory usage: ~80MB per worker (vs 500MB+ with Playwright)

**Frontend Changes:**
- `ScrapingSettings` component for configuration management
- Dynamic threshold display with percentage-based color coding
- Method selection dropdown (newspaper4k/playwright)
- Reset failures button with confirmation

**Testing:**
- 8 comprehensive integration tests covering all scenarios
- Validation for threshold ranges (1-20)
- Method validation (reject "auto", "httpx")
- Reset functionality testing

**Documentation:**
- ADR-013: Newspaper4k Integration Architecture Decision
- Updated API documentation for both services
- Performance benchmarks and comparison tables
- Migration guide and troubleshooting

**Breaking Changes:**
- ⚠️ `scrape_method` values "auto" and "httpx" no longer valid (migrated to "newspaper4k")
- ⚠️ Frontend components require updated TypeScript types

**Migration Path:**
```bash
# 1. Apply database migration
docker exec news-feed-service alembic upgrade head

# 2. Restart services
docker compose restart feed-service scraping-service

# 3. Existing feeds automatically migrated to newspaper4k
```

**Impact:**
- All existing feeds with "auto"/"httpx" automatically use newspaper4k
- Playwright-configured feeds unchanged
- No user action required for migration

**Related:**
- Architecture Decision: `docs/decisions/ADR-013-newspaper4k-scraping-integration.md`
- API Updates: `docs/api/feed-service-api.md`, `docs/api/scraping-service-api.md`
- Integration Tests: `services/feed-service/tests/test_scraping_api.py`

---

## [1.1.0] - 2025-10-21

### Added - Feed Quality Score System

**Feature:** Multi-dimensional automated quality scoring for RSS feeds (0-100 scale)

**Components:**
- Database function `calculate_feed_quality_score()` with automatic trigger
- `quality_score` column in `feeds` table
- API endpoint updates to include quality scores
- Frontend `QualityScoreBadge` component
- Comprehensive documentation

**Scoring Methodology:**
- **Credibility Foundation** (40 points) - Based on tier_1/tier_2/tier_3 classification
- **Editorial Quality** (25 points) - Fact-checking level, corrections policy, source attribution
- **External Trust Ratings** (20 points) - NewsGuard, AllSides, Media Bias/Fact Check
- **Operational Health** (15 points) - Health score and failure penalty

**Quality Categories:**
- 🏆 Premium (85-100): Highest quality tier 1 sources
- ✅ Trusted (70-84): Reliable sources with good practices
- ⚠️ Moderate (50-69): Acceptable quality, use with awareness
- ❌ Limited (<50): Use with caution

**Documentation:**
- Feature Guide: `docs/features/feed-quality-score.md`
- Architecture Decision: `docs/decisions/ADR-007-feed-quality-scoring.md`
- API Reference: `docs/api/feed-service-api.md` (updated)
- Service Docs: `docs/services/feed-service.md` (updated)

**Migration:**
```bash
# Applied automatically via trigger on feed updates
# Manual recalculation:
UPDATE feeds SET quality_score = calculate_feed_quality_score(
  credibility_tier, reputation_score, editorial_standards,
  trust_ratings, health_score, consecutive_failures
);
```

**Impact:**
- Current scores: BBC (88), DW English (85), Der Standard (67), Middle East Eye (52), AllAfrica (52)
- Users can now sort/filter feeds by quality
- Visual quality indicators in Feed List view

---

## Previous Versions

### [1.0.0] - 2025-01-19
- Initial microservices architecture
- Feed Service, Research Service, Content Analysis Service
- Feed Source Assessment integration
- Health monitoring and tracking

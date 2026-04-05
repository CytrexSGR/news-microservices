# Search Service Documentation

**Service Name:** search-service
**Port:** 8106
**Version:** 1.0.0
**Technology Stack:** FastAPI, PostgreSQL Full-Text Search, Redis, RabbitMQ, Celery
**Status:** Production-Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Search Technology](#search-technology)
6. [Data Models](#data-models)
7. [API Endpoints](#api-endpoints)
8. [Event-Driven Indexing](#event-driven-indexing)
9. [Performance Characteristics](#performance-characteristics)
10. [Caching Strategy](#caching-strategy)
11. [Search Features](#search-features)
12. [Configuration](#configuration)
13. [Monitoring & Metrics](#monitoring--metrics)
14. [Troubleshooting](#troubleshooting)
15. [Integration Guide](#integration-guide)

---

## Executive Summary

The Search Service is a high-performance full-text search microservice built on PostgreSQL Full-Text Search (FTS) capabilities. It provides real-time article indexing, advanced search capabilities, autocomplete suggestions, and user search history tracking. The service integrates with the Feed Service for article data and Content Analysis Service for sentiment/entity metadata.

### Key Capabilities

- **Full-Text Search**: PostgreSQL tsvector-based FTS with relevance ranking
- **Advanced Query Support**: Boolean operators, phrase search, field-specific search, fuzzy matching
- **Real-Time Indexing**: Event-driven indexing via RabbitMQ for sub-second search freshness
- **Autocomplete**: Redis-cached suggestions based on popular queries and article titles
- **User Search History**: Per-user search tracking with analytics
- **Faceted Search**: Dynamic facets for sources, sentiment, and date ranges
- **Search Highlighting**: PostgreSQL ts_headline for context snippets
- **Analytics**: Popular queries, click tracking, result distribution analysis

### Performance Profile

- **Search Latency**: ~40-45ms p50 for typical queries (with cache hits ~2-5ms)
- **Index Throughput**: 100+ articles/sec (batch indexing)
- **Cache Hit Rate**: 45-60% for common queries (depends on query distribution)
- **Index Size**: ~187 MB per 100k articles (with GIN index overhead)

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│                      (Port 8106)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Search     │  │   Saved      │  │   History    │          │
│  │   Router     │  │   Search     │  │   Router     │          │
│  │   (/search)  │  │   Router     │  │ (/history)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│                    ┌──────▼───────┐                              │
│                    │ Search       │                              │
│                    │ Service      │                              │
│                    │ (DB Queries) │                              │
│                    └──────┬───────┘                              │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                   │
│         │                 │                 │                   │
│    ┌────▼────┐   ┌────────▼────────┐  ┌────▼────┐              │
│    │ Indexing│   │  Suggestion     │  │  Admin  │              │
│    │ Service │   │  Service        │  │ Service │              │
│    └────┬────┘   └────────┬────────┘  └────┬────┘              │
│         │                 │                │                    │
└─────────┼─────────────────┼────────────────┼────────────────────┘
          │                 │                │
          │        ┌────────┴────────┐      │
          │        │                 │      │
    ┌─────▼──────────────────┐   ┌───▼──────────────┐
    │   PostgreSQL           │   │     Redis        │
    │   + FTS Indexes        │   │     Cache        │
    │   (GIN tsvector)       │   │  (TTL: 3600s)    │
    └─────────┬──────────────┘   └──────────────────┘
              │
              │ (Unified analysis table)
              │
    ┌─────────▼──────────────┐
    │  article_analysis      │
    │  (sentiment, entities) │
    └────────────────────────┘


┌──────────────────────────────────────────────────────┐
│         Event-Driven Indexing Layer                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   RabbitMQ  │  │   RabbitMQ  │  │   RabbitMQ  │ │
│  │  Consumer   │  │  Consumer   │  │  Consumer   │ │
│  │(article.*)  │  │(analysis.*) │  │(feed.fetch) │ │
│  └─────────┬───┘  └─────────┬───┘  └─────────┬───┘ │
│            │                │                 │      │
│            └────────────────┼─────────────────┘      │
│                             │                       │
│                    ┌────────▼────────┐              │
│                    │ Async Indexing  │              │
│                    │ (Real-time)     │              │
│                    └────────┬────────┘              │
│                             │                       │
│                    ┌────────▼────────┐              │
│                    │ PostgreSQL FTS   │              │
│                    │ Vector Update    │              │
│                    │ (tsvector)       │              │
│                    └──────────────────┘              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
1. Article Creation (Feed Service)
   └─> RabbitMQ event (article.created)
       └─> Search Consumer
           └─> Fetch from Feed Service
               └─> Fetch analysis from DB
                   └─> Index with tsvector
                       └─> Commit to PostgreSQL

2. User Search Query
   ├─> Check Redis cache
   │   └─> Return if hit (2-5ms)
   └─> Cache miss
       └─> PostgreSQL FTS query (@@)
           └─> ts_rank() for relevance
               └─> ts_headline() for highlights
                   └─> Cache result (3600s TTL)
                       └─> Return to user (40-45ms)

3. Autocomplete Request
   ├─> Check Redis suggestions cache
   │   └─> Return if hit (1-2ms)
   └─> Cache miss
       └─> Popular queries (similarity)
           ├─> Article titles (trigram)
           └─> Merge + dedupe
               └─> Cache (3600s TTL)
                   └─> Return suggestions (5-10ms)
```

---

## Technology Stack

### Core Dependencies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | 0.115.0 | REST API framework |
| **Server** | Uvicorn | 0.30.0 | ASGI application server |
| **Database** | PostgreSQL | 15+ | Full-text search, ACID transactions |
| **Database Driver** | asyncpg | 0.29.0 | Async PostgreSQL driver |
| **ORM** | SQLAlchemy | 2.0.35 | Database abstraction, async support |
| **Cache** | Redis | 5+ | Result caching, suggestions |
| **Cache Client** | redis-py | 5.0.1 | Async Redis client |
| **Message Queue** | RabbitMQ | 3.12+ | Event-driven architecture |
| **Message Driver** | aio-pika | 9.4.0 | Async RabbitMQ client |
| **Background Jobs** | Celery | 5.3.4 | Async task processing |
| **Validation** | Pydantic | 2.8.0 | Data validation, serialization |
| **Auth** | python-jose | 3.3.0 | JWT token validation |
| **HTTP Client** | httpx | 0.27.0 | Async HTTP requests |

### PostgreSQL Extensions

```sql
-- Required for full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- Trigram similarity
CREATE EXTENSION IF NOT EXISTS unaccent;    -- Accent removal
```

---

## Core Components

### 1. SearchService

**Location:** `/app/services/search_service.py`

Handles all search query execution and result ranking.

#### Key Methods

##### `search(request: SearchRequest, user_id: Optional[str]) -> SearchResponse`
- Performs basic full-text search with caching
- Executes PostgreSQL FTS query using tsvector
- Applies filters: source, sentiment, date range, entities
- Caches results with TTL
- Tracks search history if user authenticated

**Query Flow:**
```sql
SELECT article_index, ts_rank(search_vector, query) as rank
FROM article_indexes
WHERE search_vector @@ to_tsquery('english', ?)
AND (source = ? AND sentiment = ? AND published_at >= ?)
ORDER BY rank DESC
LIMIT ? OFFSET ?
```

**Performance:** 40-45ms typical (cache hit: 2-5ms)

##### `advanced_search(request: AdvancedSearchRequest, user_id: Optional[str]) -> SearchResponse`
- Supports fuzzy matching with trigram similarity
- Generates search term highlighting
- Computes dynamic facets (source, sentiment, date)
- Returns relevance scores and result distribution

**Fuzzy Query Union:**
```python
# Base FTS query UNION fuzzy matches
query = base_fts_query.union(
    fuzzy_query where similarity(title, query) > threshold
)
```

##### `_build_search_query(query: Optional[str], filters: SearchFilters)`
- Parses PostgreSQL tsquery format
- Applies filter predicates
- Handles empty queries (returns all articles ordered by date)
- Supports phrase search and exclusions

##### `_parse_query(query: str) -> str`
- Converts user query to PostgreSQL tsquery syntax
- Supports operators: AND, OR, -keyword
- Simple tokenization (no advanced parsing)

**Example Conversions:**
```
User Input: "tesla earnings"
Output: "tesla & earnings"

User Input: "tesla -bankruptcy"
Output: "tesla & !bankruptcy"

User Input: "tesla OR spacex"
Output: "tesla | spacex"
```

##### `_generate_highlights(article, query) -> Dict[str, List[str]]`
- Uses PostgreSQL `ts_headline()` function
- Generates 3 fragments max per field
- Returns highlighted snippets with `<em>` tags

##### `_compute_facets(query, facet_fields, filters) -> Dict[str, Any]`
- Returns aggregated counts by source, sentiment, date
- Used for UI filter dropdowns
- Groups by facet_fields parameter

#### Caching Strategy
- Cache key: `search:{query}:{page}:{page_size}:{filters_hash}`
- TTL: Configurable (default 3600s)
- Cache hit rate: 45-60% for typical workloads
- Invalidation: Automatic TTL expiration

---

### 2. IndexingService

**Location:** `/app/services/indexing_service.py`

Manages article indexing and tsvector generation.

#### Key Methods

##### `sync_articles(batch_size: int = 100) -> Dict[str, Any]`
- Fetches articles from Feed Service since last sync
- Batch processes articles for indexing
- Returns: `{indexed, updated, errors, total}`

**Process:**
1. Get last indexed timestamp
2. Fetch articles from Feed Service (all feeds)
3. For each article:
   - Fetch sentiment/entities from analysis database
   - Create/update ArticleIndex record
   - Update search_vector via raw SQL
4. Commit batch

##### `reindex_all() -> Dict[str, Any]`
- Full reindex operation (destructive)
- Deletes all existing indexes
- Refetches all articles from Feed Service
- Useful for schema changes or corruption recovery

##### `index_article(article_data: Dict[str, Any]) -> ArticleIndex`
- Single article indexing
- Fetches analysis from unified table (article_analysis)
- Updates search_vector via SQL:

```sql
UPDATE article_indexes
SET search_vector = to_tsvector('english',
    coalesce(title, '') || ' ' || coalesce(content, '')
)
WHERE article_id = ?
```

##### `_fetch_articles(since, limit, page) -> List[Dict[str, Any]]`
- HTTP calls to Feed Service
- Fetches all feeds first, then items per feed
- Filters by date if `since` provided
- Returns paginated results

##### `_fetch_analysis_from_db(article_id) -> Tuple[Optional[str], Optional[list]]`
- Reads from unified `article_analysis` table (not API)
- Direct database reads for performance (40x faster than HTTP)
- Maps: triage_decision → sentiment, entities (list)
- Returns: (sentiment, entities) tuple

#### Performance
- **Indexing Rate:** 100+ articles/sec (batch mode)
- **Single Article:** 5-10ms (includes DB fetch)
- **Reindex Full Index:** ~2-3 min for 100k articles

---

### 3. SuggestionService

**Location:** `/app/services/suggestion_service.py`

Generates autocomplete suggestions and related searches.

#### Key Methods

##### `get_suggestions(query: str, limit: int = 10) -> List[str]`
- Returns autocomplete suggestions
- Combines popular queries + article titles
- Deduplicates results
- Caches with 3600s TTL

**Sources (priority order):**
1. Popular queries starting with user input
2. Article titles with trigram similarity > threshold

##### `get_related_searches(query: str, limit: int = 5) -> List[str]`
- Returns semantically related queries
- Uses trigram similarity (similarity > 0.3)
- Falls back to ILIKE pattern matching
- Caches 1 hour

##### `get_popular_queries(limit: int = 10) -> List[dict]`
- Returns top queries by hit count
- Format: `[{query, hits}, ...]`
- Caches 30 minutes (shorter TTL for freshness)

#### Caching
- Popular queries: 30m TTL
- Suggestions/related: 60m TTL
- Cache keys: `suggestions:{query}:{limit}`, `popular_queries:{limit}`

---

### 4. RabbitMQ Consumer

**Location:** `/app/events/consumer.py`

Real-time event-driven indexing via RabbitMQ.

#### Routing Keys Bound

| Key | Source | Action | Latency |
|-----|--------|--------|---------|
| `article.created` | Feed Service | Index new article | <500ms |
| `article.updated` | Feed Service | Re-index article | <500ms |
| `analysis.completed` | Content Analysis | Update analysis data | <500ms |
| `feed.fetch_completed` | Feed Service | Log batch info | <100ms |

#### Event Processing

**Message Format:**
```json
{
  "event_type": "article.created",
  "service": "feed-service",
  "timestamp": "2025-01-15T10:30:00Z",
  "payload": {
    "item_id": 123,
    "feed_id": 456
  }
}
```

**Processing Flow (article.created):**
1. Receive RabbitMQ message
2. Extract item_id from payload
3. Fetch article from Feed Service endpoint
4. Create database session
5. Call `indexing_service.index_article()`
6. Commit transaction
7. Acknowledge message

**Performance:**
- Prefetch count: 10 (concurrent processing)
- Queue TTL: 1 hour
- Queue max length: 10k messages
- Typical latency: <500ms per article

---

### 5. Admin Service

**Location:** `/app/api/admin.py`

Administrative endpoints for maintenance and monitoring.

#### Statistics Endpoints

##### `/admin/stats/index` - Index Statistics
Returns:
```json
{
  "total_indexed": 125340,
  "by_source": [
    {"source": "Reuters", "count": 45230},
    {"source": "Bloomberg", "count": 38100}
  ],
  "by_sentiment": [
    {"sentiment": "positive", "count": 52000},
    {"sentiment": "neutral", "count": 50000},
    {"sentiment": "negative", "count": 23340}
  ],
  "recent_24h": 3450,
  "index_size": "187 MB"
}
```

##### `/admin/stats/queries` - Query Statistics
Returns:
```json
{
  "top_queries": [
    {"query": "tesla", "hits": 1523},
    {"query": "bitcoin", "hits": 987}
  ],
  "total_searches": 45678,
  "recent_24h": 2345,
  "avg_results_per_query": 23.45
}
```

##### `/admin/stats/cache` - Cache Statistics
Returns Redis metrics:
```json
{
  "total_keys": 1234,
  "memory_used": "45 MB",
  "hit_rate_percent": 52.3,
  "total_hits": 67890,
  "total_misses": 61234
}
```

##### `/admin/stats/performance` - Performance Metrics
Returns query latency distribution and slow queries.

#### Maintenance Endpoints

##### `POST /admin/reindex`
- Full index rebuild
- Deletes all existing indexes
- Refetches all articles from Feed Service
- Useful for corruption recovery or schema changes
- Requires authentication
- Duration: ~2-3 min for 100k articles

##### `POST /admin/sync`
- Incremental sync
- Fetches new articles since last sync
- Updates existing articles
- Non-destructive (no deletion)
- Default batch size: 100 articles

---

## Search Technology

### PostgreSQL Full-Text Search (FTS)

The service uses PostgreSQL's native full-text search with tsvector and tsquery operators.

#### tsvector - Text Search Vector

**Definition:** Normalized, indexed representation of document text.

**Creation:**
```sql
to_tsvector('english', title || ' ' || content)
```

**Format Example:**
```
Input: "Tesla Inc. reported earnings today"
Output: 'earn':3 'inc':1 'report':2 'tesla':1 'today':4
```

Features:
- Stemming (reported → report)
- Stop word removal (a, the, is)
- Case/accent normalization
- Language-aware tokenization

#### Index Strategy

**GIN Index (Generalized Inverted Index):**
```sql
CREATE INDEX idx_article_search_vector ON article_indexes
USING GIN(search_vector);
```

**Characteristics:**
- Optimized for full-text search queries
- Fast search (O(log n) time complexity)
- Slower updates (index maintenance overhead)
- Memory overhead: ~187 MB per 100k articles

**Query Performance:**
- GIN index scan: ~3-5ms
- Results ranking: ~35-40ms
- Total FTS query: ~40-45ms

#### tsquery - Text Search Query

**PostgreSQL Operator:**
```sql
WHERE search_vector @@ to_tsquery('english', 'tesla & earnings')
```

**Supported Operators:**
- `&` (AND) - Both terms required
- `|` (OR) - Either term required
- `!` (NOT) - Exclude term
- No parentheses (left-to-right precedence)

**Examples:**
```sql
to_tsquery('english', 'tesla & earnings')
  -- Matches: "tesla reported earnings"

to_tsquery('english', 'tesla | spacex')
  -- Matches: "tesla news" OR "spacex mission"

to_tsquery('english', 'tesla & !bankruptcy')
  -- Matches: "tesla earnings" but NOT "tesla bankruptcy"
```

#### Relevance Ranking

**ts_rank() Function:**
```sql
SELECT article_id, ts_rank(search_vector, query) as rank
FROM article_indexes
WHERE search_vector @@ query
ORDER BY rank DESC
```

**Ranking Algorithm with Tuned Weights:**

PostgreSQL's `ts_rank()` uses positional weights to control field importance:

```python
# Tuned weights in search_service.py
tuned_weights = '{0.8, 0.6, 0.4, 0.2}'  # D, C, B, A positions
# D (0.8): Title field - highest priority
# C (0.6): Subtitle/heading fields
# B (0.4): Body content
# A (0.2): Metadata (author, source)
```

**Note:** These are `ts_rank()` positional weights, NOT classic TF-IDF term weights. PostgreSQL FTS uses frequency + position + document length normalization.

**Example Scores:**
- Multiple matches in title: 0.95
- Single match in title: 0.85
- Multiple matches in content: 0.65
- Single match in content: 0.45

#### Trigram Similarity (Fuzzy Search)

**Extension:** pg_trgm

```sql
SELECT similarity(title, 'tesla') as score
FROM article_indexes
WHERE similarity(title, 'tesla') > 0.3
ORDER BY score DESC
```

**How It Works:**
- Breaks text into 3-character trigrams
- Compares trigrams between strings
- Score = matching trigrams / total trigrams
- Threshold: 0.3 (configurable)

**Examples:**
- "Tesla" vs "tesla" = 0.95 (near match)
- "Tesla" vs "Teslaa" = 0.75 (typo tolerance)
- "Tesla" vs "test" = 0.40 (partial)

**Performance:**
- Non-indexed similarity: O(n) scan
- With GiST/BRIN index: O(log n) scan
- Useful for autocomplete/typo tolerance

#### Highlighting

**ts_headline() Function:**
```sql
SELECT ts_headline('english', content,
    to_tsquery('english', 'tesla'),
    'MaxFragments=3, MaxWords=20, MinWords=10'
)
```

**Output Example:**
```
"... <b>Tesla</b> Inc reported record Q4 earnings with <b>Tesla</b>
Gigafactory production..."
```

**Parameters:**
- `MaxFragments`: Max snippets (3)
- `MaxWords`: Words per snippet (20)
- `MinWords`: Minimum context (10)

---

### Query Optimization

#### Index Usage Analysis

**EXPLAIN Output (Good Query):**
```sql
EXPLAIN ANALYZE
SELECT * FROM article_indexes
WHERE search_vector @@ to_tsquery('english', 'tesla & earnings')
ORDER BY ts_rank(search_vector, to_tsquery('english', 'tesla & earnings')) DESC;

-- Bitmap Index Scan using idx_article_search_vector (2.3ms)
-- Heap Scan (filter matches): 42.1ms
```

#### Common Query Patterns

| Pattern | Query | Latency | Index Used |
|---------|-------|---------|-----------|
| Keyword search | FTS only | 40-45ms | GIN ✓ |
| Filtered search | FTS + source | 50-60ms | GIN + btree |
| Date range | Source + date | 35-50ms | Composite |
| Fuzzy search | Similarity | 100-150ms | No index |
| No query (browse) | Sort by date | 80-120ms | btree |

#### Optimization Techniques

**1. Composite Indexes**
```sql
CREATE INDEX idx_source_sentiment_date ON article_indexes
  (source, sentiment, published_at DESC);
```
Useful for: Filtered searches without FTS

**2. Partial Indexes**
```sql
CREATE INDEX idx_recent_articles ON article_indexes(search_vector)
  WHERE published_at > now() - interval '90 days';
```
Useful for: Recent articles (smaller index)

**3. Query Result Caching**
- Cache key includes all filter parameters
- TTL: 3600s (1 hour)
- Hit rate: 45-60%
- Saves: 40-45ms per cache hit

**4. Connection Pooling**
- Pool size: 20 connections
- Max overflow: 10
- Prevents connection exhaustion

---

## Data Models

### ArticleIndex

**Table:** `article_indexes`

**Purpose:** Full-text searchable index of all articles.

**Schema:**
```python
class ArticleIndex(Base):
    id: Integer (PK)
    article_id: String (unique, indexed)

    # Content
    title: String
    content: Text
    author: String
    source: String (indexed)
    url: String
    published_at: DateTime (indexed)

    # Analysis
    sentiment: String (indexed) -- positive|neutral|negative|unknown
    entities: Text -- JSON array of entity names

    # Full-Text Search
    search_vector: TSVector (GIN indexed)

    # Metadata
    indexed_at: DateTime
    updated_at: DateTime (updated on re-index)
```

**Indexes:**
```sql
CREATE INDEX idx_article_search_vector ON article_indexes USING GIN(search_vector);
CREATE INDEX idx_article_published_at ON article_indexes(published_at);
CREATE INDEX idx_article_source ON article_indexes(source);
CREATE INDEX idx_article_sentiment ON article_indexes(sentiment);
```

**Storage:**
- Per-article: ~1.5-2.0 KB (content + metadata)
- Per-article (index): ~1.5 KB (tsvector overhead)
- Total: ~3.5 KB per article indexed
- 100k articles: ~350 MB disk + 187 MB index

**Update Latency:**
- Insert + search_vector: 10-15ms
- Update (article change): 5-10ms
- Update (analysis only): <1ms

---

### SearchHistory

**Table:** `search_history`

**Purpose:** Track user search activity for analytics and suggestions.

**Schema:**
```python
class SearchHistory(Base):
    id: Integer (PK)
    user_id: String (indexed)

    query: String
    filters: Text -- JSON of applied filters
    results_count: Integer

    created_at: DateTime (indexed)
```

**Indexes:**
```sql
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_created_at ON search_history(created_at);
```

**Retention:** Indefinite (for analytics)

**Usage:**
- Per-user search history endpoint
- Popular query generation
- Search analytics dashboard

**Insert Latency:** <1ms (no complex indexes)

---

### SavedSearch

**Table:** `saved_searches`

**Purpose:** User-defined saved searches with notification support.

**Schema:**
```python
class SavedSearch(Base):
    id: Integer (PK)
    user_id: String (indexed)

    name: String (user-provided label)
    query: String
    filters: Text -- JSON of filters

    notifications_enabled: Boolean
    last_notified_at: DateTime

    created_at: DateTime
    updated_at: DateTime
```

**Features:**
- Create multiple saved searches per user
- Enable/disable notifications
- Track last notification sent

**Future Enhancement:** Email alerts when new results match

---

### SearchAnalytics

**Table:** `search_analytics`

**Purpose:** Track popular queries for suggestions and analytics.

**Schema:**
```python
class SearchAnalytics(Base):
    id: Integer (PK)
    query: String (indexed)

    hits: Integer -- total times searched
    avg_position: Float -- average click position (optional)

    created_at: DateTime
    updated_at: DateTime
```

**Indexes:**
```sql
CREATE INDEX idx_search_analytics_query ON search_analytics(query);
CREATE INDEX idx_search_analytics_hits ON search_analytics(hits);
```

**Update Strategy:**
- Increment hits on each search
- Update timestamp
- Used for: Popular query suggestions, trending analysis

**Insert Latency:** <1ms (upsert: check + update/insert)

---

## API Endpoints

### Search Endpoints

#### `GET /api/v1/search`
Basic full-text search with optional filtering.

**Parameters:**
```
query: str (optional, max 500 chars)
page: int (default 1, min 1)
page_size: int (default 20, max 100)
source: str (optional, comma-separated)
sentiment: str (optional, comma-separated)
date_from: str (optional, ISO format)
date_to: str (optional, ISO format)
```

**Response:**
```json
{
  "query": "tesla earnings",
  "total": 1523,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "article_id": "uuid",
      "title": "Tesla Q4 Earnings...",
      "content": "...",
      "author": "Jane Doe",
      "source": "Reuters",
      "url": "https://...",
      "published_at": "2025-01-15T10:30:00Z",
      "sentiment": "positive",
      "entities": ["Tesla", "Elon Musk"],
      "relevance_score": 0.95,
      "highlight": null
    }
  ],
  "facets": null,
  "execution_time_ms": 42.3
}
```

**Performance:**
- Cache hit: 2-5ms
- Cache miss: 40-45ms
- Empty query (browse all): 80-120ms

**Caching:**
- Key: `search:{query}:{page}:{page_size}:{filters_hash}`
- TTL: 3600s
- Hit rate: 45-60%

---

#### `POST /api/v1/search/advanced`
Advanced search with fuzzy matching, highlighting, and facets.

**Request:**
```json
{
  "query": "tesla earnings",
  "page": 1,
  "page_size": 20,
  "use_fuzzy": true,
  "highlight": true,
  "facets": ["source", "sentiment", "date"],
  "filters": {
    "source": ["Reuters", "Bloomberg"],
    "sentiment": ["positive"],
    "date_from": "2025-01-01T00:00:00Z"
  }
}
```

**Response:**
```json
{
  "query": "tesla earnings",
  "total": 342,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "article_id": "uuid",
      "title": "Tesla Q4 Earnings...",
      "content": "...",
      "author": "Jane Doe",
      "source": "Reuters",
      "url": "https://...",
      "published_at": "2025-01-15T10:30:00Z",
      "sentiment": "positive",
      "entities": ["Tesla"],
      "relevance_score": 0.95,
      "highlight": {
        "title": ["<em>Tesla</em> Q4 <em>Earnings</em> Report"],
        "content": ["... reported <em>earnings</em> of $7.2B ..."]
      }
    }
  ],
  "facets": {
    "source": [
      {"value": "Reuters", "count": 156},
      {"value": "Bloomberg", "count": 124}
    ],
    "sentiment": [
      {"value": "positive", "count": 280},
      {"value": "neutral", "count": 62}
    ],
    "date": [
      {"value": "2025-01-15", "count": 45},
      {"value": "2025-01-14", "count": 38}
    ]
  },
  "execution_time_ms": 78.5
}
```

**Performance:**
- With fuzzy union: 80-120ms
- Facet computation: +30-40ms
- Highlighting: +15-20ms

---

#### `GET /api/v1/search/suggest`
Autocomplete suggestions.

**Parameters:**
```
query: str (required, 1-100 chars)
limit: int (default 10, max 20)
```

**Response:**
```json
{
  "query": "tes",
  "suggestions": [
    "tesla",
    "tesla earnings",
    "tesla stock",
    "testing",
    "testimony"
  ]
}
```

**Sources (priority order):**
1. Popular queries with prefix match
2. Article titles with trigram similarity

**Caching:**
- Key: `suggestions:{query}:{limit}`
- TTL: 3600s
- Latency: 1-2ms (cache hit), 5-10ms (miss)

---

#### `GET /api/v1/search/popular`
Most popular search queries.

**Parameters:**
```
limit: int (default 10, max 50)
```

**Response:**
```json
{
  "popular_queries": [
    {"query": "tesla", "hits": 1523},
    {"query": "bitcoin", "hits": 987},
    {"query": "apple earnings", "hits": 756}
  ],
  "total": 3
}
```

**Caching:**
- Key: `popular_queries:{limit}`
- TTL: 1800s (30 minutes, shorter for freshness)

---

#### `GET /api/v1/search/related`
Related search queries based on similarity.

**Parameters:**
```
query: str (required, 1-500 chars)
limit: int (default 5, max 20)
```

**Response:**
```json
{
  "query": "tesla earnings",
  "related": [
    "tesla q4 earnings",
    "tesla financial results",
    "tesla stock price",
    "elon musk earnings",
    "tesla revenue"
  ]
}
```

**Algorithm:**
1. Trigram similarity > 0.3
2. OR ILIKE pattern match
3. Ranked by hit count (popularity)

---

#### `GET /api/v1/search/facets`
Available filter options.

**Parameters:** None

**Response:**
```json
{
  "sources": [
    "Reuters",
    "Bloomberg",
    "CNBC",
    "Associated Press"
  ],
  "categories": [
    "positive",
    "neutral",
    "negative"
  ]
}
```

---

### History Endpoints

#### `GET /api/v1/search/history`
User search history (requires auth).

**Parameters:**
```
page: int (default 1)
page_size: int (default 20, max 100)
```

**Response:**
```json
{
  "total": 234,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 123,
      "query": "tesla",
      "filters": null,
      "results_count": 1523,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

#### `DELETE /api/v1/search/history`
Clear all search history for user (requires auth).

**Response:** 204 No Content

---

### Admin Endpoints

All admin endpoints require authentication.

#### `POST /api/v1/admin/reindex`
Full index rebuild.

**Response:**
```json
{
  "status": "success",
  "message": "Reindex completed successfully",
  "stats": {
    "indexed": 125340,
    "errors": 0
  }
}
```

**Duration:** ~2-3 minutes for 100k articles

---

#### `POST /api/v1/admin/sync`
Incremental sync of new articles.

**Parameters:**
```
batch_size: int (default 100)
```

**Response:**
```json
{
  "status": "success",
  "message": "Sync completed successfully",
  "stats": {
    "indexed": 145,
    "updated": 32,
    "errors": 2,
    "total": 179
  }
}
```

---

#### `GET /api/v1/admin/stats/index`
Index statistics.

**Response:**
```json
{
  "total_indexed": 125340,
  "by_source": [
    {"source": "Reuters", "count": 45230}
  ],
  "by_sentiment": [
    {"sentiment": "positive", "count": 52000}
  ],
  "recent_24h": 3450,
  "index_size": "187 MB",
  "last_updated": "2025-01-15T10:30:00Z"
}
```

---

#### `GET /api/v1/admin/stats/queries`
Query statistics.

**Response:**
```json
{
  "top_queries": [
    {"query": "tesla", "hits": 1523}
  ],
  "total_searches": 45678,
  "recent_24h": 2345,
  "avg_results_per_query": 23.45,
  "last_updated": "2025-01-15T10:30:00Z"
}
```

---

#### `GET /api/v1/admin/stats/cache`
Redis cache statistics.

**Response:**
```json
{
  "total_keys": 1234,
  "memory_used": "45 MB",
  "memory_peak": "52 MB",
  "hit_rate_percent": 52.3,
  "total_hits": 67890,
  "total_misses": 61234,
  "evicted_keys": 0,
  "expired_keys": 2345,
  "last_updated": "2025-01-15T10:30:00Z"
}
```

---

#### `GET /api/v1/admin/stats/performance`
Performance metrics.

**Response:**
```json
{
  "avg_execution_time_ms": 42.3,
  "slowest_queries": [
    {"query": "tesla", "hits": 1523}
  ],
  "result_distribution": [
    {"range": "0 results", "count": 234},
    {"range": "1-10 results", "count": 567},
    {"range": "100+ results", "count": 1245}
  ],
  "last_updated": "2025-01-15T10:30:00Z"
}
```

---

## Event-Driven Indexing

### RabbitMQ Integration

The search service listens for events from other microservices to maintain real-time index freshness.

### Event Types

#### 1. article.created
**Source:** Feed Service
**Routing Key:** `article.created`
**Payload:**
```json
{
  "event_type": "article.created",
  "service": "feed-service",
  "timestamp": "2025-01-15T10:30:00Z",
  "payload": {
    "item_id": 123,
    "feed_id": 456
  }
}
```

**Handler Action:**
1. Fetch article details from Feed Service
2. Create ArticleIndex entry
3. Generate tsvector
4. Commit to PostgreSQL

**Latency:** <500ms

---

#### 2. article.updated
**Source:** Feed Service
**Routing Key:** `article.updated`
**Payload:**
```json
{
  "event_type": "article.updated",
  "service": "feed-service",
  "timestamp": "2025-01-15T10:30:00Z",
  "payload": {
    "item_id": 123,
    "feed_id": 456,
    "updated_fields": ["title", "content"]
  }
}
```

**Handler Action:**
1. Fetch updated article data
2. Update existing ArticleIndex
3. Regenerate tsvector
4. Commit changes

**Latency:** <500ms

---

#### 3. analysis.completed
**Source:** Content Analysis Service
**Routing Key:** `analysis.completed`
**Payload:**
```json
{
  "event_type": "analysis.completed",
  "service": "content-analysis-service",
  "timestamp": "2025-01-15T10:30:00Z",
  "payload": {
    "article_id": "uuid-123",
    "sentiment": "positive",
    "entities": ["Tesla", "Elon Musk"]
  }
}
```

**Handler Action:**
1. Fetch analysis from unified database table (not API)
2. Update ArticleIndex with sentiment/entities
3. Commit changes

**Latency:** <500ms

---

#### 4. feed.fetch_completed
**Source:** Feed Service
**Routing Key:** `feed.fetch_completed`
**Payload:**
```json
{
  "event_type": "feed.fetch_completed",
  "service": "feed-service",
  "timestamp": "2025-01-15T10:30:00Z",
  "payload": {
    "feed_id": 456,
    "items_found": 10,
    "items_new": 5,
    "item_ids": [123, 124, 125, 126, 127]
  }
}
```

**Handler Action:** Log batch metrics (individual articles indexed via article.created events)

---

### Queue Configuration

```
Queue Name: search_indexing_events
Durable: true
Max Retries: 3
Message TTL: 1 hour
Max Length: 10k messages
Prefetch Count: 10 (concurrent processing)
```

### Consumer Connection

```python
connection = await aio_pika.connect_robust(
    settings.RABBITMQ_URL,
    client_properties={"service": "search-service"}
)
channel = await connection.channel()
await channel.set_qos(prefetch_count=10)
```

---

## Performance Characteristics

### Query Performance

#### Search Latency Breakdown

**Typical FTS Query (Cache Miss):**
```
PostgreSQL planning:        2-3ms
Index scan (GIN):           3-5ms
Results filtering:          8-10ms
Ranking computation:        15-20ms
Result serialization:       5-10ms
Network + serialization:    5-10ms
─────────────────────────────────
Total:                      40-45ms
```

**Cache Hit:** 2-5ms

**Percentiles (production data, n=10k queries):**
- p50: 42ms
- p95: 85ms
- p99: 150ms
- max: 300ms (worst case)

#### Query Patterns Impact

| Pattern | Latency | Notes |
|---------|---------|-------|
| Simple keyword | 40-45ms | GIN index used |
| Boolean operators | 45-50ms | Union complexity |
| Fuzzy search | 100-150ms | No index, O(n) scan |
| Filtered search | 50-60ms | Composite index |
| Date range | 35-50ms | B-tree index |
| Empty query (browse) | 80-120ms | Full sort by date |
| Autocomplete | 5-10ms | Cache/simple query |

### Index Performance

#### Indexing Throughput

**Batch Indexing:**
- Rate: 100+ articles/sec
- Single article: 10-15ms (includes HTTP fetch)
- Network fetch (Feed Service): 5-10ms
- Database operations: 5-8ms

**Capacity:**
- 100k articles indexed: ~15 minutes (cold start)
- Incremental sync (100 articles): ~2-3 seconds
- Full reindex (100k): 2-3 minutes

### Memory Profile

#### PostgreSQL Memory Usage
```
Shared buffers (default 256MB):
  - Index cache (GIN): ~100-150MB
  - Page cache: ~80-100MB
  - Work memory: ~20-30MB
```

#### Redis Memory Usage
- Cache: ~50-100MB (depends on hit rate)
- Suggestions: ~5-10MB
- Popular queries: <1MB

#### Application Memory
- SQLAlchemy connection pool: ~50MB
- Query object instances: ~20-30MB
- Cache client: ~5-10MB
- Total: ~80-100MB

### Scalability

#### Horizontal Scaling

**Search Queries:**
- Stateless, fully horizontally scalable
- Multiple instances behind load balancer
- Share same PostgreSQL + Redis

**Indexing:**
- RabbitMQ consumer is singleton per instance
- Multiple instances safe (prefetch_count = 10)
- No race conditions (DB-level locking)

#### Vertical Scaling

**PostgreSQL Tuning:**
```
shared_buffers: 25% of RAM
effective_cache_size: 50-75% of RAM
work_mem: RAM / (max_connections * 2)
maintenance_work_mem: RAM / 4
```

**Connection Pool:**
- Current: 20 connections
- Can increase to 50+ for high concurrency
- Max overflow: 10 (temporary overflow)

---

## Caching Strategy

### Cache Architecture

```
┌─────────────┐
│  User Query │
│   Request   │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  Check Redis Cache   │
│  Key: search:{q}:{p} │
└──────┬───────────────┘
       │
       ├─ Hit (2-5ms)
       │  └─> Return cached response
       │
       └─ Miss
          └─> Execute PostgreSQL query (40-45ms)
              └─> Cache result (TTL: 3600s)
                  └─> Return response
```

### Cache Types

#### 1. Search Results Cache
- **Key:** `search:{query}:{page}:{page_size}:{filters_hash}`
- **Value:** Serialized SearchResponse (JSON)
- **TTL:** 3600s (1 hour, configurable)
- **Hit Rate:** 45-60% (typical workloads)
- **Memory:** ~500 bytes per cached result
- **Invalidation:** TTL expiration only

**Example:**
```
Key: search:tesla:1:20:abc123def456
Value: {
  "query": "tesla",
  "total": 1523,
  "page": 1,
  "page_size": 20,
  "results": [...],
  "execution_time_ms": 42.3
}
```

#### 2. Suggestions Cache
- **Key:** `suggestions:{query}:{limit}`
- **Value:** List of suggestion strings
- **TTL:** 3600s
- **Hit Rate:** 70-80% (many repeated prefixes)
- **Memory:** ~100 bytes per cached query
- **Computation:** Popular queries + title similarity

**Example:**
```
Key: suggestions:tes:10
Value: ["tesla", "tesla earnings", "tesla stock", ...]
```

#### 3. Popular Queries Cache
- **Key:** `popular_queries:{limit}`
- **Value:** List of {query, hits} objects
- **TTL:** 1800s (30 minutes, shorter for freshness)
- **Hit Rate:** 95%+ (single key)
- **Memory:** ~5KB

---

#### 4. Related Searches Cache
- **Key:** `related:{query}:{limit}`
- **Value:** List of related query strings
- **TTL:** 3600s
- **Recomputation:** Every hour

### Cache Operations

#### Cache Get
```python
async def cache_get(key: str) -> Optional[Any]:
    client = await get_redis_client()
    value = await client.get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None
```

**Latency:** 1-2ms (network + Redis operation)

#### Cache Set
```python
async def cache_set(key: str, value: Any, ttl: Optional[int] = None):
    client = await get_redis_client()
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    if ttl:
        await client.setex(key, ttl, value)
    else:
        await client.set(key, value)
```

**Latency:** 1-2ms

### Cache Invalidation

**TTL-Based (Primary):**
- Search results: Expire after 3600s
- Suggestions: Expire after 3600s
- Popular queries: Expire after 1800s

**Event-Based (Optional):**
Could implement invalidation on:
- New article published (invalidate all search caches)
- Sentiment analysis updated (invalidate specific query)

Currently not implemented (TTL sufficient).

### Cache Hit Rate Analysis

**Typical Distribution:**
```
Popular queries (top 20):     80-90% hit rate
Common prefixes:               70-80% hit rate
New/rare queries:             10-20% hit rate
Overall:                      45-60% hit rate
```

**Factors Affecting Hit Rate:**
- Query cardinality (fewer unique queries = higher hits)
- Result size (larger pages = longer cache)
- User base (more users = more variety)
- TTL length (longer TTL = higher hits)

**Optimization Opportunities:**
- Increase TTL to 7200s (trade: freshness)
- Pre-populate cache for top 100 queries
- Implement query clustering (cache related queries together)

---

## Search Features

### 1. Full-Text Search

Indexes article title and content with PostgreSQL tsvector.

**Features:**
- Stemming (report, reports, reported → report)
- Stop word removal (the, a, is)
- Phrase search ("exact phrase")
- Boolean operators (AND, OR, NOT)
- Relevance ranking

**Example Queries:**
```
tesla              -> Simple keyword
tesla earnings     -> Multiple keywords (AND)
"tesla earnings"   -> Exact phrase
tesla OR spacex    -> Boolean OR
tesla -bankruptcy  -> Exclusion (NOT)
```

---

### 2. Advanced Search

Extends basic search with fuzzy matching, highlighting, and facets.

**Features:**
- Fuzzy/typo tolerance (trigram similarity)
- Relevance-ranked results
- Search term highlighting
- Dynamic facets (source, sentiment, date)
- Result distribution analysis

**Request Example:**
```json
{
  "query": "tesla earnings",
  "use_fuzzy": true,
  "highlight": true,
  "facets": ["source", "sentiment", "date"],
  "filters": {
    "source": ["Reuters"],
    "sentiment": ["positive"]
  }
}
```

---

### 3. Filtered Search

Multiple filter dimensions:

| Filter | Type | Values | Example |
|--------|------|--------|---------|
| Source | List | Free text | Reuters, Bloomberg |
| Sentiment | List | positive, neutral, negative | positive |
| Date Range | Range | ISO datetime | 2025-01-01 to 2025-01-31 |
| Entities | List | Free text | Tesla, Elon Musk |

**Performance Impact:**
- Single filter: +5-10ms
- Multiple filters: +10-20ms
- Filter + FTS: +50-60ms total

---

### 4. Autocomplete

Real-time search suggestions.

**Sources:**
1. Popular queries (frequency)
2. Article titles (trigram similarity)

**Features:**
- Case-insensitive matching
- Deduplication
- Ranked by relevance
- Redis caching

**Example:**
```
User types: "tes"
Suggestions:
  - tesla
  - tesla earnings
  - tesla stock
  - testing
  - testimony
```

---

### 5. Search History

Per-user search history with analytics.

**Features:**
- Track all searches (optional auth)
- View search history
- Clear history
- Analytics (popular queries)

**Example History Entry:**
```json
{
  "id": 123,
  "query": "tesla",
  "filters": null,
  "results_count": 1523,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### 6. Search Analytics

Track and analyze search patterns.

**Metrics:**
- Total searches
- Popular queries (by frequency)
- Query distribution
- Performance statistics

**Admin Endpoint:** `/api/v1/admin/stats/queries`

---

### 7. Result Highlighting

Display matched terms in context.

**Features:**
- Highlights matched terms with `<em>` tags
- Shows context around matches
- Multiple fragments per document
- PostgreSQL ts_headline

**Example:**
```
"... reported <em>earnings</em> of $7.2B in Q4 2024,
with <em>earnings</em> beating expectations..."
```

---

### 8. Faceted Search

Dynamic filter options for UI.

**Facets:**
- Source (unique values with count)
- Sentiment (unique values with count)
- Date (daily histogram)

**Example Response:**
```json
"facets": {
  "source": [
    {"value": "Reuters", "count": 156},
    {"value": "Bloomberg", "count": 124}
  ],
  "sentiment": [
    {"value": "positive", "count": 280},
    {"value": "neutral", "count": 62}
  ],
  "date": [
    {"value": "2025-01-15", "count": 45},
    {"value": "2025-01-14", "count": 38}
  ]
}
```

---

### Saved Search Endpoints (5 endpoints)

User-defined saved searches with notification support (requires authentication).

#### `POST /api/v1/search/saved`
Create a saved search.

**Request:**
```json
{
  "name": "Tesla News",
  "query": "tesla earnings",
  "filters": {
    "source": ["Reuters", "Bloomberg"],
    "sentiment": ["positive"]
  },
  "notifications_enabled": true
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "name": "Tesla News",
  "query": "tesla earnings",
  "filters": {...},
  "notifications_enabled": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

#### `GET /api/v1/search/saved`
List all saved searches for current user.

**Response:**
```json
{
  "total": 3,
  "items": [
    {"id": 123, "name": "Tesla News", "query": "tesla earnings", ...}
  ]
}
```

---

#### `GET /api/v1/search/saved/{search_id}`
Get a saved search by ID.

**Errors:** 404 Not Found if search doesn't exist or doesn't belong to user.

---

#### `PUT /api/v1/search/saved/{search_id}`
Update a saved search.

**Request:**
```json
{"name": "Tesla Financial News", "notifications_enabled": false}
```

---

#### `DELETE /api/v1/search/saved/{search_id}`
Delete a saved search.

**Response:** 204 No Content

---

**Note:** All saved search endpoints require JWT authentication via `Authorization: Bearer <token>` header.

---

## Configuration

### Environment Variables

```env
# Service Configuration
SERVICE_NAME=search-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8000
ENVIRONMENT=development|production
DEBUG=true|false
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
LOG_FORMAT=json|plain

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600

# Celery
CELERY_BROKER_URL=redis://redis:6379/7
CELERY_RESULT_BACKEND=redis://redis:6379/7

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_EXCHANGE=news.events

# Service URLs
FEED_SERVICE_URL=http://feed-service:8001
CONTENT_ANALYSIS_SERVICE_URL=http://content-analysis-service:8002
AUTH_SERVICE_URL=http://auth-service:8000

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
JWT_ALGORITHM=HS256

# Search Configuration
MAX_SEARCH_RESULTS=100
DEFAULT_PAGE_SIZE=20
ENABLE_FUZZY_SEARCH=true
FUZZY_SIMILARITY_THRESHOLD=0.3

# Indexing
INDEXING_ENABLED=true
INDEXING_INTERVAL=300       # seconds
BATCH_SIZE=100

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]
```

### Tuning Parameters

#### PostgreSQL Optimization

```sql
-- In postgresql.conf
shared_buffers = 256MB         # 25% of RAM
effective_cache_size = 2GB     # 50% of RAM
work_mem = 4MB                 # RAM / (max_connections * 2)
maintenance_work_mem = 256MB   # RAM / 4
wal_buffers = 16MB
random_page_cost = 1.1         # SSD tuning

-- Connection pooling
max_connections = 100
```

#### Redis Configuration

```
maxmemory 512mb                # Max cache size
maxmemory-policy allkeys-lru   # LRU eviction
```

#### Application Parameters

```python
# Cache TTL (seconds)
CACHE_TTL = 3600              # 1 hour

# Search limits
MAX_SEARCH_RESULTS = 100       # Hard limit
DEFAULT_PAGE_SIZE = 20         # Default page size
MAX_PAGE_SIZE = 100            # Max allowed

# Fuzzy search
ENABLE_FUZZY_SEARCH = true
FUZZY_SIMILARITY_THRESHOLD = 0.3

# Indexing
BATCH_SIZE = 100               # Articles per batch
INDEXING_INTERVAL = 300        # Seconds (optional)

# Connection pools
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```

---

## Monitoring & Metrics

### Health Check Endpoint

**`GET /health`**

Response:
```json
{
  "status": "healthy",
  "service": "search-service",
  "version": "1.0.0",
  "environment": "production",
  "indexing": {
    "enabled": true,
    "interval": 300
  },
  "search": {
    "fuzzy_enabled": true,
    "max_results": 100
  }
}
```

### Key Metrics to Monitor

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| Query Latency p50 | Median search time | <50ms | >100ms |
| Query Latency p95 | 95th percentile | <100ms | >200ms |
| Query Latency p99 | 99th percentile | <150ms | >300ms |
| Cache Hit Rate | % of cached requests | >50% | <30% |
| Index Size | Total disk usage | <200MB/100k | Monitor growth |
| Database Connections | Active connections | <20 | >50 |
| Redis Memory | Cache memory used | <100MB | >200MB |
| Indexing Latency | Time to index article | <15ms | >50ms |
| Search Index Count | Total indexed articles | | Trends |

### Admin Statistics Endpoints

#### Index Statistics
```
GET /api/v1/admin/stats/index
```
Returns: total indexed, by_source, by_sentiment, recent_24h, index_size

#### Query Statistics
```
GET /api/v1/admin/stats/queries
```
Returns: top_queries, total_searches, recent_24h, avg_results_per_query

#### Cache Statistics
```
GET /api/v1/admin/stats/cache
```
Returns: total_keys, memory_used, hit_rate, evicted_keys

#### Performance Statistics
```
GET /api/v1/admin/stats/performance
```
Returns: avg_execution_time, slowest_queries, result_distribution

### Logging

**Log Format (JSON):**
```json
{
  "time": "2025-01-15T10:30:00.123456",
  "name": "app.services.search_service",
  "level": "INFO",
  "message": "Search executed",
  "query": "tesla",
  "results": 1523,
  "execution_time_ms": 42.3
}
```

**Log Levels:**
- **DEBUG:** Query plans, intermediate states
- **INFO:** API requests, search queries, index updates
- **WARNING:** Slow queries, connection issues
- **ERROR:** Failed queries, exception traces

---

## Troubleshooting

### Common Issues

#### 1. Slow Search Queries (>100ms)

**Symptoms:** User-visible search latency increase

**Diagnosis:**
```bash
# Check query plan
EXPLAIN ANALYZE SELECT ...

# Check index usage
SELECT * FROM pg_stat_user_indexes
WHERE relname = 'article_indexes'

# Check cache hit rate
GET /api/v1/admin/stats/cache
```

**Solutions:**
1. Verify GIN index exists and is being used
2. Run VACUUM ANALYZE to update statistics
3. Check for slow queries in logs
4. Clear cache and monitor hit rate recovery
5. Increase connection pool if contention detected

---

#### 2. Missing Articles in Search Results

**Symptoms:** Recently published article not findable

**Diagnosis:**
```sql
-- Check if article is indexed
SELECT * FROM article_indexes
WHERE article_id = '?'

-- Check search_vector is populated
SELECT search_vector FROM article_indexes
WHERE article_id = '?'

-- Verify RabbitMQ consumer is running
```

**Solutions:**
1. Verify article exists in Feed Service
2. Check RabbitMQ consumer logs for errors
3. Manually trigger indexing: `POST /api/v1/admin/sync`
4. Reindex if search_vector is NULL: `POST /api/v1/admin/reindex`

---

#### 3. High Memory Usage

**Symptoms:** Cache memory exceeding 200MB or DB connections growing

**Diagnosis:**
```bash
# Check Redis memory
redis-cli INFO memory

# Check PostgreSQL connections
SELECT count(*) FROM pg_stat_activity

# Check cache key count
redis-cli DBSIZE
```

**Solutions:**
1. Reduce CACHE_TTL (default 3600s)
2. Implement cache eviction policy (LRU)
3. Increase max_connections if needed
4. Clear expired cache entries
5. Monitor query cardinality (too many unique queries)

---

#### 4. RabbitMQ Consumer Not Processing Events

**Symptoms:** New articles not being indexed despite RabbitMQ messages

**Diagnosis:**
```bash
# Check consumer connection
curl http://localhost:8106/health

# Check RabbitMQ queue
rabbitmq-plugins enable rabbitmq_management
# Visit http://localhost:15672

# Check logs for errors
docker logs search-service
```

**Solutions:**
1. Verify RabbitMQ is running and accessible
2. Check service can connect to RabbitMQ
3. Verify routing keys match (article.created, etc.)
4. Restart consumer if stuck
5. Check Feed Service is publishing events

---

#### 5. Cache Not Working (Hit Rate <10%)

**Symptoms:** Every search takes 40-45ms (no cache hits)

**Diagnosis:**
```bash
# Check Redis connection
redis-cli ping

# Monitor cache operations
GET /api/v1/admin/stats/cache

# Check query cardinality
# If every query is unique, cache won't help
```

**Solutions:**
1. Verify Redis is running and accessible
2. Check REDIS_URL is correct
3. Increase TTL if changing frequently
4. Monitor if queries are highly unique
5. Pre-populate cache with top queries

---

#### 6. Database Connection Pool Exhaustion

**Symptoms:** "too many connections" errors, query failures

**Diagnosis:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity

-- Check long-running queries
SELECT * FROM pg_stat_activity
WHERE state != 'idle'
```

**Solutions:**
1. Increase DATABASE_POOL_SIZE
2. Increase max_connections in PostgreSQL
3. Kill long-running queries (if safe)
4. Implement query timeouts
5. Profile for connection leaks

---

### Performance Optimization Checklist

```
□ GIN index on search_vector exists
  EXPLAIN shows "Index Scan" not "Seq Scan"

□ Statistics are up to date
  VACUUM ANALYZE article_indexes

□ Redis is operational
  redis-cli ping returns PONG

□ Cache hit rate > 45%
  GET /api/v1/admin/stats/cache

□ Query latency p95 < 200ms
  Monitor query execution times

□ Connection pool not exhausted
  SELECT count(*) FROM pg_stat_activity < 50

□ RabbitMQ consumer running
  Check service logs for "consuming"

□ Indexing latency < 50ms
  Monitor admin/stats endpoint

□ Disk space adequate
  Monitoring alert for > 80% usage
```

---

## Integration Guide

### Integrating Search Service into Frontend

#### Example: React Component

```typescript
import { useEffect, useState } from 'react';
import axios from 'axios';

interface SearchResult {
  article_id: string;
  title: string;
  content: string;
  source: string;
  relevance_score: number;
  highlight: Record<string, string[]>;
}

interface SearchResponse {
  query: string;
  total: number;
  page: number;
  results: SearchResult[];
  execution_time_ms: number;
  facets: Record<string, any>;
}

function SearchComponent() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const performSearch = async (q: string, page = 1) => {
    setLoading(true);
    try {
      const response = await axios.get<SearchResponse>(
        'http://localhost:8106/api/v1/search',
        {
          params: {
            query: q,
            page,
            page_size: 20,
            source: 'Reuters,Bloomberg'
          }
        }
      );
      setResults(response.data);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  return (
    <div>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search articles..."
        />
        <button type="submit">Search</button>
      </form>

      {loading && <p>Loading...</p>}

      {results && (
        <div>
          <p>Found {results.total} results in {results.execution_time_ms}ms</p>
          {results.results.map((result) => (
            <div key={result.article_id}>
              <h3>{result.title}</h3>
              <p>{result.content.substring(0, 200)}...</p>
              <p>Source: {result.source}</p>
              <p>Score: {result.relevance_score.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Integrating with Backend Services

#### Example: Feed Service Publishing Events

```python
# feed-service/app/services/feed_service.py
import pika
import json

async def publish_article_created(item_id: int, feed_id: int):
    """Publish article creation event"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('rabbitmq', 5672)
    )
    channel = connection.channel()

    # Declare exchange
    channel.exchange_declare(
        exchange='news.events',
        exchange_type='topic',
        durable=True
    )

    # Publish event
    event = {
        "event_type": "article.created",
        "service": "feed-service",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "item_id": item_id,
            "feed_id": feed_id
        }
    }

    channel.basic_publish(
        exchange='news.events',
        routing_key='article.created',
        body=json.dumps(event),
        properties=pika.BasicProperties(delivery_mode=2)  # Persistent
    )

    connection.close()
```

### Using Search Service API Programmatically

#### Python Example

```python
import httpx
import json

async def search_articles(query: str, filters: dict = None):
    """Search articles using Search Service API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'http://search-service:8106/api/v1/search',
            params={
                'query': query,
                'page': 1,
                'page_size': 20,
                'source': 'Reuters,Bloomberg' if filters else None,
                'sentiment': 'positive' if filters else None
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
results = await search_articles('tesla earnings')
print(f"Found {results['total']} articles")
```

#### JavaScript/Node.js Example

```javascript
async function searchArticles(query, filters = {}) {
  const response = await fetch(
    `http://localhost:8106/api/v1/search?query=${query}&page=1&page_size=20`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`  // If needed
      }
    }
  );

  const data = await response.json();
  return data;
}

// Usage
const results = await searchArticles('tesla');
console.log(`Found ${results.total} articles in ${results.execution_time_ms}ms`);
results.results.forEach(result => {
  console.log(`${result.title} (${result.source})`);
});
```

---

## Summary

The Search Service provides a production-ready, high-performance full-text search solution with:

- **Real-time indexing** via RabbitMQ events
- **Sub-50ms search latency** with intelligent caching
- **Advanced query support** including fuzzy matching and filtering
- **Comprehensive analytics** for monitoring and optimization
- **Horizontal scalability** through stateless design

For questions or issues, refer to the admin endpoints and troubleshooting section above.


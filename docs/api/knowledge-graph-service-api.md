# Knowledge Graph Service API

**Version:** 1.1
**Last Updated:** 2025-11-06
**Service Port:** 8111
**Database:** Neo4j (Graph Database)

---

## Overview

The Knowledge Graph Service provides a semantic graph database for entities and their relationships. It powers entity-based analytics, relationship discovery, and knowledge exploration across the news corpus.

**Key Features:**
- **Entity Relationship Graph** - Stores entities and relationships in Neo4j
- **Analytics Endpoints** - Graph statistics, top entities, relationship analysis
- **Manual Enrichment** - Admin tools for improving NOT_APPLICABLE relationships
- **Cross-Article Coverage** - Track entity mentions across articles (data model incomplete)
- **Real-time Updates** - Consumes RabbitMQ events for automatic graph updates

**Business Value:**
- **Knowledge Discovery** - Uncover hidden relationships between entities
- **Entity Analytics** - Understand entity importance and connectivity
- **Data Quality Insights** - Identify enrichment opportunities
- **Semantic Search Foundation** - Enable graph-based search queries

---

## Base URL

```
http://localhost:8111
```

For production or remote access:
```
http://{HOST_IP}:8111
```

---

## Authentication

**Method:** None (Internal service)

This service is designed for internal microservice communication and admin dashboards. If exposed externally, implement API gateway authentication.

**Note:** Enrichment endpoints (`/admin/enrichment/*`) should be admin-only in production.

---

## Endpoints

### 1. Analytics Endpoints

#### 1.1 Get Top Entities

Get the most connected entities in the knowledge graph.

```
GET /api/v1/graph/analytics/top-entities?limit={limit}&entity_type={type}
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Number of top entities (1-100) |
| `entity_type` | string | No | null | Filter by entity type (PERSON, ORGANIZATION, etc.) |

**Response:** `200 OK`
```json
[
  {
    "name": "United States",
    "type": "LOCATION",
    "connection_count": 342,
    "sample_connections": [
      {
        "name": "NATO",
        "type": "ORGANIZATION",
        "relationship_type": "MEMBER_OF"
      },
      {
        "name": "Joe Biden",
        "type": "PERSON",
        "relationship_type": "LOCATED_IN"
      }
    ]
  },
  {
    "name": "Tesla",
    "type": "ORGANIZATION",
    "connection_count": 287,
    "sample_connections": [
      {
        "name": "Elon Musk",
        "type": "PERSON",
        "relationship_type": "WORKS_FOR"
      }
    ]
  }
]
```

**Features:**
- Returns entities sorted by connection count (descending)
- Includes sample connections (up to 5) for context
- Filters by entity type if specified
- Shows relationship types for understanding entity context

**Use Case:** Identify most important entities in the graph

**Example:**
```bash
# Top 10 entities (all types)
curl "http://localhost:8111/api/v1/graph/analytics/top-entities?limit=10"

# Top 20 organizations
curl "http://localhost:8111/api/v1/graph/analytics/top-entities?entity_type=ORGANIZATION&limit=20"
```

---

#### 1.2 Get Growth History

Get graph growth history over time (daily node and relationship counts).

```
GET /api/v1/graph/analytics/growth-history?days={days}
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Number of days of history (1-365) |

**Response:** `200 OK`
```json
[
  {
    "date": "2025-10-24",
    "new_nodes": 87,
    "new_relationships": 156,
    "total_nodes": 3867,
    "total_relationships": 7234
  },
  {
    "date": "2025-10-23",
    "new_nodes": 42,
    "new_relationships": 89,
    "total_nodes": 3780,
    "total_relationships": 7078
  }
]
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Date in YYYY-MM-DD format |
| `new_nodes` | integer | Nodes created on this date |
| `new_relationships` | integer | Relationships created on this date |
| `total_nodes` | integer | Cumulative node count |
| `total_relationships` | integer | Cumulative relationship count |

**Features:**
- Returns daily statistics sorted by date (ascending)
- Calculates cumulative totals for visualization
- Uses `created_at` timestamps on nodes/relationships
- Missing dates filled with zeros for continuous timeline

**Use Case:** Visualize knowledge graph growth trends in admin dashboard

**Example:**
```bash
# Last 7 days
curl "http://localhost:8111/api/v1/graph/analytics/growth-history?days=7"

# Last year
curl "http://localhost:8111/api/v1/graph/analytics/growth-history?days=365"
```

---

#### 1.3 Get Relationship Statistics

Get comprehensive statistics about relationship types in the graph.

```
GET /api/v1/graph/analytics/relationship-stats
```

**Response:** `200 OK`
```json
{
  "total_relationships": 7234,
  "relationship_types": [
    {
      "type": "WORKS_FOR",
      "count": 1245,
      "percentage": 17.2,
      "avg_confidence": 0.87,
      "total_mentions": 3421,
      "quality": "high",
      "examples": [
        {
          "source": "Elon Musk",
          "source_type": "PERSON",
          "target": "Tesla",
          "target_type": "ORGANIZATION",
          "confidence": 0.95,
          "mentions": 47
        }
      ]
    },
    {
      "type": "NOT_APPLICABLE",
      "count": 892,
      "percentage": 12.3,
      "avg_confidence": 0.45,
      "total_mentions": 1203,
      "quality": "low",
      "examples": []
    }
  ],
  "patterns": [
    {
      "source_type": "PERSON",
      "relationship_type": "WORKS_FOR",
      "target_type": "ORGANIZATION",
      "count": 1189
    }
  ],
  "quality_insights": {
    "high_quality_count": 5,
    "needs_review_count": 2,
    "avg_confidence_overall": 0.73
  },
  "warnings": [
    {
      "type": "high_not_applicable",
      "message": "NOT_APPLICABLE relationships are 12.3% of total. Consider improving entity extraction.",
      "severity": "warning"
    }
  ]
}
```

**Response Fields:**
| Section | Description |
|---------|-------------|
| `total_relationships` | Total relationship count in graph |
| `relationship_types` | Distribution with confidence, mentions, examples |
| `patterns` | Most common entity-type → relationship → entity-type combinations |
| `quality_insights` | High-quality vs. needs-review counts |
| `warnings` | Automated quality warnings (e.g., high NOT_APPLICABLE %) |

**Quality Classification:**
- **High:** avg_confidence >= 0.8
- **Medium:** avg_confidence >= 0.6
- **Low:** avg_confidence < 0.6

**Features:**
- Includes top 3 concrete examples per relationship type (sorted by mentions)
- Shows entity-type patterns (e.g., PERSON→ORGANIZATION is common for WORKS_FOR)
- Automated quality warnings for data quality issues
- Calculates overall confidence as weighted average

**Use Case:** Understand relationship distribution and identify quality issues

**Example:**
```bash
curl http://localhost:8111/api/v1/graph/analytics/relationship-stats | jq
```

---

#### 1.4 Get Cross-Article Coverage

Get statistics about entities appearing across multiple articles.

```
GET /api/v1/graph/analytics/cross-article-coverage?top_limit={limit}
```

**⚠️ Data Model Incomplete:** This endpoint is implemented but returns empty data because Article nodes don't exist in Neo4j yet.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `top_limit` | integer | No | 10 | Number of top entities (1-50) |

**Response:** `200 OK`
```json
{
  "total_articles": 0,
  "total_unique_entities": 0,
  "entities_per_article_avg": 0.0,
  "articles_per_entity_avg": 0.0,
  "top_entities": []
}
```

**Expected Response (when data model is complete):**
```json
{
  "total_articles": 543,
  "total_unique_entities": 265,
  "entities_per_article_avg": 8.7,
  "articles_per_entity_avg": 2.3,
  "top_entities": [
    {
      "entity_name": "United States",
      "entity_type": "LOCATION",
      "wikidata_id": "Q30",
      "article_count": 127,
      "coverage_percentage": 23.4,
      "recent_articles": [
        {
          "title": "US Economy Shows Growth",
          "published_at": "2025-10-24"
        }
      ]
    }
  ]
}
```

**Missing Data Model:**
- **Article nodes** - Not created in Neo4j
- **EXTRACTED_FROM relationship** - Entity → Article relationship not tracked

**Implementation Required:**
1. Modify `knowledge-graph-service` to create Article nodes
2. Create `EXTRACTED_FROM` relationships when entities are extracted
3. Store article metadata (title, published_at, etc.)

**Status:** Frontend shows mock data with warning banner

**Example:**
```bash
curl "http://localhost:8111/api/v1/graph/analytics/cross-article-coverage?top_limit=10"
```

---

#### 1.5 Get NOT_APPLICABLE Trends

Get historical trends of NOT_APPLICABLE relationship ratio over time.

```
GET /api/v1/graph/analytics/not-applicable-trends?days={days}
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Number of days of history (1-365) |

**Response:** `200 OK`
```json
[
  {
    "date": "2025-11-06",
    "not_applicable_count": 2,
    "total_relationships": 18006,
    "not_applicable_ratio": 0.0001,
    "not_applicable_percentage": 0.01
  },
  {
    "date": "2025-11-05",
    "not_applicable_count": 3,
    "total_relationships": 17854,
    "not_applicable_ratio": 0.0002,
    "not_applicable_percentage": 0.02
  }
]
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Date in YYYY-MM-DD format |
| `not_applicable_count` | integer | NOT_APPLICABLE relationships created on this date |
| `total_relationships` | integer | Total relationships created on this date |
| `not_applicable_ratio` | float | Ratio of NOT_APPLICABLE to total (0.0-1.0) |
| `not_applicable_percentage` | float | Percentage of NOT_APPLICABLE (0-100) |

**Features:**
- Returns daily statistics sorted by date (ascending)
- Filters by `created_at` timestamps on relationships
- Calculates NOT_APPLICABLE ratio for quality tracking
- Uses CASE WHEN aggregation for efficient counting

**Quality Thresholds:**
- **Excellent:** < 5% NOT_APPLICABLE
- **Good:** 5-15% NOT_APPLICABLE
- **Fair:** 15-25% NOT_APPLICABLE
- **Needs Review:** ≥ 25% NOT_APPLICABLE

**Use Case:** Monitor extraction quality over time. Low NOT_APPLICABLE ratio indicates high-quality entity relationship extraction.

**Cypher Query:**
```cypher
MATCH ()-[r]->()
WHERE r.created_at IS NOT NULL
  AND r.created_at >= datetime($start_date)
  AND r.created_at <= datetime($end_date)
WITH date(r.created_at) AS creation_date,
     type(r) AS rel_type
RETURN
    toString(creation_date) AS date,
    sum(CASE WHEN rel_type = 'NOT_APPLICABLE' THEN 1 ELSE 0 END) AS not_applicable_count,
    count(*) AS total_relationships
ORDER BY date ASC
```

**Example:**
```bash
# Last 30 days (default)
curl "http://localhost:8111/api/v1/graph/analytics/not-applicable-trends"

# Last 7 days
curl "http://localhost:8111/api/v1/graph/analytics/not-applicable-trends?days=7"

# Last year
curl "http://localhost:8111/api/v1/graph/analytics/not-applicable-trends?days=365"
```

---

#### 1.6 Get Relationship Quality Trends

Get historical trends of relationship confidence levels (high/medium/low) over time.

```
GET /api/v1/graph/analytics/relationship-quality-trends?days={days}
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Number of days of history (1-365) |

**Response:** `200 OK`
```json
[
  {
    "date": "2025-11-06",
    "high_confidence_count": 17460,
    "medium_confidence_count": 546,
    "low_confidence_count": 0,
    "total_relationships": 18006,
    "high_confidence_ratio": 0.9696,
    "medium_confidence_ratio": 0.0303,
    "low_confidence_ratio": 0.0001,
    "high_confidence_percentage": 96.96,
    "medium_confidence_percentage": 3.03,
    "low_confidence_percentage": 0.01
  },
  {
    "date": "2025-11-05",
    "high_confidence_count": 17254,
    "medium_confidence_count": 598,
    "low_confidence_count": 2,
    "total_relationships": 17854,
    "high_confidence_ratio": 0.9664,
    "medium_confidence_ratio": 0.0335,
    "low_confidence_ratio": 0.0001,
    "high_confidence_percentage": 96.64,
    "medium_confidence_percentage": 3.35,
    "low_confidence_percentage": 0.01
  }
]
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Date in YYYY-MM-DD format |
| `high_confidence_count` | integer | Relationships with confidence > 0.8 |
| `medium_confidence_count` | integer | Relationships with confidence 0.5-0.8 |
| `low_confidence_count` | integer | Relationships with confidence < 0.5 |
| `total_relationships` | integer | Total relationships created on this date |
| `high_confidence_ratio` | float | Ratio of high confidence (0.0-1.0) |
| `medium_confidence_ratio` | float | Ratio of medium confidence (0.0-1.0) |
| `low_confidence_ratio` | float | Ratio of low confidence (0.0-1.0) |
| `high_confidence_percentage` | float | Percentage of high confidence (0-100) |
| `medium_confidence_percentage` | float | Percentage of medium confidence (0-100) |
| `low_confidence_percentage` | float | Percentage of low confidence (0-100) |

**Features:**
- Returns daily statistics sorted by date (ascending)
- Three confidence levels based on relationship confidence score
- Uses CASE WHEN aggregation for efficient counting
- Filters by `created_at` timestamps on relationships
- All ratios sum to 1.0, all percentages sum to 100

**Confidence Level Definitions:**
- **High Confidence (>0.8):** Strong, reliable relationships
- **Medium Confidence (0.5-0.8):** Moderate reliability, may need review
- **Low Confidence (<0.5):** Weak relationships, requires investigation

**Quality Status (based on high confidence %):**
- **Excellent:** ≥ 95%
- **Good:** 85-95%
- **Fair:** 70-85%
- **Needs Review:** < 70%

**Use Case:** Monitor relationship extraction quality over time. Track improvement in confidence scores after model updates or data quality improvements.

**Cypher Query:**
```cypher
MATCH ()-[r]->()
WHERE r.created_at IS NOT NULL
  AND r.created_at >= datetime($start_date)
  AND r.created_at <= datetime($end_date)
WITH date(r.created_at) AS creation_date,
     r.confidence AS conf
RETURN
    toString(creation_date) AS date,
    sum(CASE WHEN conf > 0.8 THEN 1 ELSE 0 END) AS high_confidence_count,
    sum(CASE WHEN conf >= 0.5 AND conf <= 0.8 THEN 1 ELSE 0 END) AS medium_confidence_count,
    sum(CASE WHEN conf < 0.5 THEN 1 ELSE 0 END) AS low_confidence_count,
    count(*) AS total_relationships
ORDER BY date ASC
```

**Example:**
```bash
# Last 30 days (default)
curl "http://localhost:8111/api/v1/graph/analytics/relationship-quality-trends"

# Last 7 days
curl "http://localhost:8111/api/v1/graph/analytics/relationship-quality-trends?days=7"

# Last year
curl "http://localhost:8111/api/v1/graph/analytics/relationship-quality-trends?days=365"

# Pretty print with jq
curl "http://localhost:8111/api/v1/graph/analytics/relationship-quality-trends?days=30" | jq
```

---

### 2. Graph Query Endpoints

#### 2.1 Get Entity Connections

Get all connections for a specific entity.

```
GET /api/v1/graph/entity/{entity_name}/connections?relationship_type={type}&limit={limit}
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_name` | string | Yes | Entity name to query (URL-encoded) |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `relationship_type` | string | No | null | Filter by relationship type |
| `limit` | integer | No | 100 | Maximum connections (1-1000) |

**Response:** `200 OK`
```json
{
  "nodes": [
    {
      "name": "Tesla",
      "type": "ORGANIZATION",
      "connection_count": 47
    },
    {
      "name": "Elon Musk",
      "type": "PERSON",
      "connection_count": 23
    }
  ],
  "edges": [
    {
      "source": "Elon Musk",
      "target": "Tesla",
      "relationship_type": "WORKS_FOR",
      "confidence": 0.95,
      "mention_count": 47,
      "evidence": "Elon Musk is the CEO of Tesla"
    }
  ],
  "total_nodes": 2,
  "total_edges": 1,
  "query_time_ms": 45
}
```

**Response Schema:**
```typescript
{
  nodes: Array<{
    name: string
    type: string
    connection_count: number
  }>
  edges: Array<{
    source: string
    target: string
    relationship_type: string
    confidence: number
    mention_count: number
    evidence: string | null
  }>
  total_nodes: number
  total_edges: number
  query_time_ms: number
}
```

**Features:**
- Returns both outgoing and incoming connections
- Filters by confidence >= 0.5 (minimum quality threshold)
- Sorts by confidence and mention_count (descending)
- Deduplicates nodes (same node may appear in multiple edges)
- Includes evidence text for relationship context

**Use Case:** Visualize entity network in graph UI

**Example:**
```bash
# All connections for Tesla
curl "http://localhost:8111/api/v1/graph/entity/Tesla/connections"

# Only WORKS_FOR relationships
curl "http://localhost:8111/api/v1/graph/entity/Tesla/connections?relationship_type=WORKS_FOR"

# First 50 connections
curl "http://localhost:8111/api/v1/graph/entity/Tesla/connections?limit=50"
```

---

#### 2.2 Get Graph Statistics

Get overall graph statistics.

```
GET /api/v1/graph/stats
```

**Response:** `200 OK`
```json
{
  "total_nodes": 3867,
  "total_relationships": 7234,
  "entity_types": {
    "PERSON": 1432,
    "ORGANIZATION": 987,
    "LOCATION": 765,
    "EVENT": 432,
    "PRODUCT": 187,
    "OTHER": 54,
    "MISC": 8,
    "NOT_APPLICABLE": 2
  }
}
```

**Features:**
- Real-time counts from Neo4j
- Entity types sorted by count (descending)
- Updates Prometheus metrics gauges
- Fast query (~50ms)

**Use Case:** Dashboard overview statistics

**Example:**
```bash
curl http://localhost:8111/api/v1/graph/stats | jq
```

---

### 3. Manual Enrichment Endpoints (Admin)

Manual enrichment tools for improving NOT_APPLICABLE relationships.

#### 3.1 Analyze for Enrichment

Identify entity pairs with NOT_APPLICABLE relationships that need enrichment.

```
POST /api/v1/graph/admin/enrichment/analyze
```

**Request Body:**
```json
{
  "analysis_type": "not_applicable_relationships",
  "limit": 50,
  "min_occurrence": 10
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `analysis_type` | string | No | "not_applicable_relationships" | Analysis type (only one supported) |
| `limit` | integer | No | 100 | Maximum candidates (1-500) |
| `min_occurrence` | integer | No | 5 | Minimum occurrence count (1-100) |

**Response:** `200 OK`
```json
{
  "candidates": [
    {
      "entity1": "Elon Musk",
      "entity1_type": "PERSON",
      "entity2": "Tesla",
      "entity2_type": "ORGANIZATION",
      "current_relationship": "NOT_APPLICABLE",
      "occurrence_count": 47,
      "suggested_tools": ["wikipedia", "research_perplexity"],
      "context_samples": [
        "Elon Musk is the CEO of Tesla",
        "Tesla was founded by Elon Musk"
      ]
    }
  ],
  "summary": {
    "total_candidates": 156,
    "by_entity_type": {
      "PERSON→ORGANIZATION": 89,
      "ORGANIZATION→LOCATION": 34,
      "PERSON→PERSON": 23
    },
    "high_priority_count": 47
  }
}
```

**Features:**
- Identifies high-frequency NOT_APPLICABLE relationships
- Suggests appropriate tools (Wikipedia, Perplexity, Google Deep Research)
- Provides context samples from actual article text
- Prioritizes by occurrence count (high frequency = high priority)

**Use Case:** Bulk identify enrichment opportunities for admin workflow

**Example:**
```bash
curl -X POST http://localhost:8111/api/v1/graph/admin/enrichment/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 50,
    "min_occurrence": 10
  }'
```

---

#### 3.2 Execute Enrichment Tool

Execute a tool to research a relationship between two entities.

```
POST /api/v1/graph/admin/enrichment/execute-tool
```

**Request Body:**
```json
{
  "tool": "wikipedia",
  "entity1": "Elon Musk",
  "entity2": "Tesla",
  "language": "de"
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tool` | string | Yes | - | Tool to execute: `wikipedia`, `research_perplexity`, `google_deep_research` |
| `entity1` | string | Yes | - | First entity name |
| `entity2` | string | Yes | - | Second entity name |
| `language` | string | No | "de" | Language for Wikipedia (de, en) |

**Response:** `200 OK`
```json
{
  "tool": "wikipedia",
  "entity1": "Elon Musk",
  "entity2": "Tesla",
  "result": {
    "relationship_found": true,
    "relationship_type": "WORKS_FOR",
    "confidence": 0.95,
    "evidence": "Elon Musk is the CEO and largest shareholder of Tesla, Inc.",
    "source": "Wikipedia: Elon Musk",
    "wikipedia_url": "https://en.wikipedia.org/wiki/Elon_Musk"
  }
}
```

**Supported Tools:**

**1. Wikipedia Tool**
- Searches Wikipedia for both entities
- Extracts relationship mentions from article text
- Returns evidence and Wikipedia URLs

**2. Perplexity Research Tool**
- Uses Perplexity AI for deep research
- Asks: "What is the relationship between {entity1} and {entity2}?"
- Returns detailed analysis with sources

**3. Google Deep Research Tool**
- Uses Google Deep Research API
- Comprehensive multi-source research
- Returns synthesized relationship analysis

**Use Case:** Research specific entity pair to determine correct relationship

**Example:**
```bash
curl -X POST http://localhost:8111/api/v1/graph/admin/enrichment/execute-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "wikipedia",
    "entity1": "Elon Musk",
    "entity2": "Tesla",
    "language": "en"
  }'
```

---

#### 3.3 Apply Enrichment

Apply enrichment by updating a relationship with new type and evidence.

```
POST /api/v1/graph/admin/enrichment/apply
```

**Request Body:**
```json
{
  "entity1": "Elon Musk",
  "entity2": "Tesla",
  "new_relationship_type": "WORKS_FOR",
  "confidence": 0.95,
  "evidence": "Elon Musk is the CEO of Tesla",
  "source": "manual_enrichment"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity1` | string | Yes | First entity name |
| `entity2` | string | Yes | Second entity name |
| `new_relationship_type` | string | Yes | New relationship type |
| `confidence` | float | Yes | Confidence score (0.0-1.0) |
| `evidence` | string | Yes | Evidence/context for relationship |
| `source` | string | No | Source (default: "manual_enrichment") |

**Response:** `200 OK`
```json
{
  "success": true,
  "entity1": "Elon Musk",
  "entity2": "Tesla",
  "old_relationship": "NOT_APPLICABLE",
  "new_relationship": "WORKS_FOR",
  "confidence": 0.95,
  "updated_at": "2025-10-24T10:30:00Z"
}
```

**Behavior:**
- Updates existing relationship in Neo4j graph
- Overwrites `type`, `confidence`, `evidence`, `source` properties
- Preserves `mention_count` (increments if re-applied)
- Adds `updated_at` timestamp

**Use Case:** Apply enrichment decision after tool research

**Example:**
```bash
curl -X POST http://localhost:8111/api/v1/graph/admin/enrichment/apply \
  -H "Content-Type: application/json" \
  -d '{
    "entity1": "Elon Musk",
    "entity2": "Tesla",
    "new_relationship_type": "WORKS_FOR",
    "confidence": 0.95,
    "evidence": "Elon Musk is the CEO of Tesla"
  }'
```

---

#### 3.4 Get Enrichment Status

Get status of ongoing enrichment operations (if async).

```
GET /api/v1/graph/admin/enrichment/status
```

**Response:** `200 OK`
```json
{
  "status": "idle",
  "total_candidates": 156,
  "processed": 0,
  "enriched": 0,
  "failed": 0
}
```

**Note:** Currently enrichment is synchronous. This endpoint is reserved for future async enrichment workflows.

---

### 4. Health & Monitoring Endpoints

#### 4.1 Basic Health Check

Simple health check to verify service is running.

```
GET /health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "knowledge-graph-service",
  "version": "1.0.0",
  "timestamp": "2025-10-24T10:30:00Z"
}
```

**Use Case:** Load balancer health check

---

#### 4.2 Liveness Probe

Kubernetes liveness probe - checks if service process is alive.

```
GET /health/live
```

**Response:** `200 OK`
```json
{
  "status": "alive",
  "service": "knowledge-graph-service"
}
```

**Behavior:**
- Returns 200 if service process is running
- Kubernetes restarts container if this fails

---

#### 4.3 Readiness Probe

Kubernetes readiness probe - checks if service is ready to accept traffic.

```
GET /health/ready
```

**Response (Ready):** `200 OK`
```json
{
  "status": "ready",
  "checks": {
    "neo4j": "healthy",
    "rabbitmq_consumer": "healthy"
  },
  "service": "knowledge-graph-service"
}
```

**Response (Not Ready):** `503 Service Unavailable`
```json
{
  "status": "not_ready",
  "checks": {
    "neo4j": "unhealthy",
    "rabbitmq_consumer": "not_connected"
  },
  "message": "Service dependencies are not healthy"
}
```

**Checks:**
- **neo4j** - Neo4j database connection
- **rabbitmq_consumer** - RabbitMQ consumer connection

**Behavior:**
- Returns 200 if all checks pass
- Returns 503 if any check fails
- Kubernetes removes pod from load balancer if not ready

---

#### 4.4 Neo4j Health Check

Detailed Neo4j connection health check.

```
GET /health/neo4j
```

**Response (Healthy):** `200 OK`
```json
{
  "status": "healthy",
  "connected": true,
  "version": "5.13.0",
  "edition": "community",
  "host": "bolt://neo4j:7687"
}
```

**Response (Unhealthy):** `503 Service Unavailable`
```json
{
  "status": "unhealthy",
  "message": "Neo4j connection failed"
}
```

**Features:**
- Executes test query: `CALL dbms.components()`
- Returns Neo4j version and edition
- Shows connection host

---

#### 4.5 RabbitMQ Health Check

Detailed RabbitMQ consumer health check.

```
GET /health/rabbitmq
```

**Response (Healthy):** `200 OK`
```json
{
  "status": "healthy",
  "connection": "open",
  "channel": "open",
  "exchange": "news.events",
  "queue": {
    "name": "knowledge_graph.entity_canonicalized",
    "message_count": 5,
    "consumer_count": 1
  },
  "routing_key": "entity.canonicalized"
}
```

**Response (Unhealthy):** `503 Service Unavailable`
```json
{
  "status": "unhealthy",
  "connection": "closed",
  "channel": "closed",
  "message": "RabbitMQ consumer not connected"
}
```

**Features:**
- Checks connection and channel status
- Shows queue message count and consumer count
- Displays exchange, queue, and routing key configuration

---

## Request Schemas

### AnalyzeRequest
```typescript
{
  analysis_type?: string  // "not_applicable_relationships"
  limit?: number          // 1-500, default 100
  min_occurrence?: number // 1-100, default 5
}
```

### ExecuteToolRequest
```typescript
{
  tool: string           // "wikipedia" | "research_perplexity" | "google_deep_research"
  entity1: string        // First entity name
  entity2: string        // Second entity name
  language?: string      // "de" | "en", default "de"
}
```

### ApplyEnrichmentRequest
```typescript
{
  entity1: string              // First entity name
  entity2: string              // Second entity name
  new_relationship_type: string // New relationship type
  confidence: number           // 0.0-1.0
  evidence: string             // Evidence/context
  source?: string              // Default: "manual_enrichment"
}
```

---

## Response Schemas

### GraphResponse
```typescript
{
  nodes: Array<{
    name: string
    type: string
    connection_count: number
  }>
  edges: Array<{
    source: string
    target: string
    relationship_type: string
    confidence: number
    mention_count: number
    evidence: string | null
  }>
  total_nodes: number
  total_edges: number
  query_time_ms: number
}
```

### RelationshipStats
```typescript
{
  total_relationships: number
  relationship_types: Array<{
    type: string
    count: number
    percentage: number
    avg_confidence: number
    total_mentions: number
    quality: "high" | "medium" | "low"
    examples: Array<{
      source: string
      source_type: string
      target: string
      target_type: string
      confidence: number
      mentions: number
    }>
  }>
  patterns: Array<{
    source_type: string
    relationship_type: string
    target_type: string
    count: number
  }>
  quality_insights: {
    high_quality_count: number
    needs_review_count: number
    avg_confidence_overall: number
  }
  warnings: Array<{
    type: string
    message: string
    severity: string
  }>
}
```

---

## Neo4j Data Model

### Current Schema

**Nodes:**
- `Entity` - All canonical entities from entity-canonicalization-service
  - Properties: `name`, `type`, `wikidata_id`, `created_at`
  - Count: 3867 nodes

**Relationships:**
- `WORKS_FOR` - Person → Organization
- `LOCATED_IN` - Entity → Location
- `OWNS` - Organization → Entity
- `MEMBER_OF` - Person/Organization → Organization
- `PARTNER_OF` - Organization → Organization
- `RELATED_TO` - Generic relationship
- `NOT_APPLICABLE` - Fallback for unclear relationships

**Relationship Properties:**
- `confidence` (float) - Confidence score (0.0-1.0)
- `mention_count` (integer) - Times mentioned in articles
- `evidence` (string) - Context/evidence text
- `created_at` (datetime) - Creation timestamp
- `source` (string) - Source of relationship

### Missing Schema Elements

**⚠️ Article Nodes Not Implemented:**
```cypher
// Expected but NOT implemented:
(Article {
  id: string,
  title: string,
  published_at: datetime,
  feed_id: string
})

// Expected but NOT implemented:
(Entity)-[:EXTRACTED_FROM]->(Article)
```

**Impact:**
- `cross-article-coverage` endpoint returns empty data
- Cannot track which articles mention which entities
- Frontend shows mock data with warning banner

---

## Cypher Query Examples

### Get Top Entities by Connection Count
```cypher
MATCH (e:Entity)
OPTIONAL MATCH (e)-[r]-(connected:Entity)
WITH e, count(DISTINCT r) AS connection_count
WHERE connection_count > 0
ORDER BY connection_count DESC
LIMIT 10
RETURN e.name AS name, e.type AS type, connection_count
```

### Get Relationship Distribution
```cypher
MATCH (source:Entity)-[r]->(target:Entity)
WITH type(r) AS relationship_type, count(*) AS count
RETURN relationship_type, count
ORDER BY count DESC
```

### Find NOT_APPLICABLE Relationships
```cypher
MATCH (e1:Entity)-[r:NOT_APPLICABLE]->(e2:Entity)
WHERE r.mention_count >= 5
RETURN e1.name AS entity1, e2.name AS entity2, r.mention_count
ORDER BY r.mention_count DESC
LIMIT 100
```

### Update Relationship Type
```cypher
MATCH (e1:Entity {name: $entity1})-[r:NOT_APPLICABLE]->(e2:Entity {name: $entity2})
SET r.type = $new_type,
    r.confidence = $confidence,
    r.evidence = $evidence,
    r.updated_at = datetime()
RETURN r
```

---

## Error Codes

| HTTP Code | Meaning | When It Occurs |
|-----------|---------|----------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid parameters, missing required fields |
| 404 | Not Found | Entity not found in graph |
| 500 | Internal Server Error | Neo4j connection error, query failure |
| 503 | Service Unavailable | Dependencies not healthy (Neo4j, RabbitMQ) |

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Performance Considerations

### Neo4j Query Performance

| Query Type | Avg. Time | Optimization |
|------------|-----------|--------------|
| Entity connections | 50-100ms | Index on `Entity.name` |
| Top entities | 200-500ms | Pre-computed counts (future) |
| Relationship stats | 500-1000ms | Materialized view (future) |
| Graph stats | 50ms | Cached with 5min TTL |

### Indexes

**Current Indexes:**
- `CREATE INDEX entity_name_index FOR (e:Entity) ON (e.name)`
- `CREATE INDEX entity_type_index FOR (e:Entity) ON (e.type)`
- `CREATE INDEX entity_wikidata_index FOR (e:Entity) ON (e.wikidata_id)`

**Recommended (Future):**
- Full-text index on `Entity.name` for fuzzy search
- Composite index on `(type, name)` for filtered queries

### Caching

**Not Implemented Yet:**
- Consider Redis cache for frequently accessed entities
- Cache graph stats for 5 minutes
- Cache top entities for 1 hour

---

## Integration Examples

### Python
```python
import requests

# Get top entities
response = requests.get(
    "http://localhost:8111/api/v1/graph/analytics/top-entities",
    params={"limit": 10, "entity_type": "ORGANIZATION"}
)
top_entities = response.json()

# Get entity connections
response = requests.get(
    "http://localhost:8111/api/v1/graph/entity/Tesla/connections",
    params={"limit": 50}
)
graph = response.json()
print(f"Nodes: {graph['total_nodes']}, Edges: {graph['total_edges']}")

# Apply enrichment
response = requests.post(
    "http://localhost:8111/api/v1/graph/admin/enrichment/apply",
    json={
        "entity1": "Elon Musk",
        "entity2": "Tesla",
        "new_relationship_type": "WORKS_FOR",
        "confidence": 0.95,
        "evidence": "Elon Musk is the CEO of Tesla"
    }
)
result = response.json()
```

### TypeScript/JavaScript
```typescript
// Fetch relationship stats
const response = await fetch(
  'http://localhost:8111/api/v1/graph/analytics/relationship-stats'
)
const stats = await response.json()
console.log(`Total relationships: ${stats.total_relationships}`)

// Execute enrichment tool
const toolResponse = await fetch(
  'http://localhost:8111/api/v1/graph/admin/enrichment/execute-tool',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tool: 'wikipedia',
      entity1: 'Elon Musk',
      entity2: 'Tesla',
      language: 'en'
    })
  }
)
const toolResult = await toolResponse.json()
```

### Curl
```bash
# Get graph statistics
curl http://localhost:8111/api/v1/graph/stats | jq

# Analyze enrichment opportunities
curl -X POST http://localhost:8111/api/v1/graph/admin/enrichment/analyze \
  -H "Content-Type: application/json" \
  -d '{"limit": 50, "min_occurrence": 10}' | jq

# Health check with details
curl http://localhost:8111/health/neo4j | jq
```

---

## Troubleshooting

### Common Issues

**Neo4j connection timeout**
```bash
# Check Neo4j status
docker logs neo4j | tail -50

# Test connection
docker exec neo4j cypher-shell -u neo4j -p password "RETURN 1"

# Restart Neo4j
docker compose restart neo4j
```

**Empty analytics data**
```bash
# Check if entities exist in graph
curl http://localhost:8111/api/v1/graph/stats

# If total_nodes=0, check RabbitMQ consumer
curl http://localhost:8111/health/rabbitmq
```

**Cross-article coverage returns empty**
- Expected behavior - Article nodes not implemented yet
- See data model section for missing schema
- Frontend shows mock data with warning banner

**High query latency**
```bash
# Check Neo4j query performance
docker exec neo4j cypher-shell -u neo4j -p password "
  CALL dbms.listQueries()
  YIELD query, elapsedTimeMillis
  RETURN query, elapsedTimeMillis
"

# Create missing indexes
docker exec neo4j cypher-shell -u neo4j -p password "
  CREATE INDEX entity_name_index IF NOT EXISTS
  FOR (e:Entity) ON (e.name)
"
```

---

## Related Documentation

- **[Service Architecture](../services/knowledge-graph-service.md)** - Service implementation details
- **[Entity Canonicalization API](./entity-canonicalization-service-api.md)** - Upstream service
- **[Frontend Dashboard](../frontend/knowledge-graph-admin-dashboard.md)** - Admin UI
- **[Mock Data Status](../../frontend/MOCK_DATA_STATUS.md)** - Frontend mock tracking
- **[Event-Driven Architecture](../architecture/EVENT_DRIVEN_ARCHITECTURE.md)** - System-wide events

---

**Last Updated:** 2025-11-06
**Authors:** Development Team
**Maintainer:** Knowledge Graph Service Team
**Version:** 1.1 - Added NOT_APPLICABLE trends and relationship quality trends endpoints

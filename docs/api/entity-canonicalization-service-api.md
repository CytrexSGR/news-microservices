# Entity Canonicalization Service API

**Version:** 1.0
**Last Updated:** 2025-10-24
**Service Port:** 8112
**Database:** PostgreSQL (news_mcp)

---

## Overview

The Entity Canonicalization Service provides entity deduplication, alias resolution, and Wikidata enrichment. It uses a multi-stage pipeline to canonicalize entity names into their standard forms.

**Key Features:**
- Multi-stage canonicalization (Exact → Fuzzy → Semantic → Wikidata → Create New)
- Batch processing for high-throughput scenarios
- Wikidata Q-ID enrichment
- Batch reprocessing for retroactive improvements
- Real-time statistics and trends analytics

---

## Base URL

```
http://localhost:8112
```

For production or remote access:
```
http://{HOST_IP}:8112
```

---

## Authentication

**Method:** None (Internal service)

This service is designed for internal microservice communication. If exposed externally, implement API gateway authentication.

**Note:** Other services in the ecosystem use JWT authentication. This service is accessed internally only.

---

## Endpoints

### 1. Core Canonicalization

#### 1.1 Canonicalize Single Entity

Canonicalize a single entity name into its canonical form.

```
POST /api/v1/canonicalization/canonicalize
```

**Multi-stage Pipeline:**
1. **Exact Match** - Check alias store for known variations
2. **Fuzzy Matching** - Levenshtein distance similarity
3. **Semantic Matching** - Embedding-based similarity
4. **Wikidata Lookup** - Query Wikidata for Q-ID enrichment
5. **Create New** - Register as new canonical entity

**Request Body:**
```json
{
  "entity_name": "USA",
  "entity_type": "LOCATION",
  "language": "en"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_name` | string | Yes | Entity name to canonicalize |
| `entity_type` | string | Yes | Entity type: `PERSON`, `ORGANIZATION`, `LOCATION`, `EVENT`, `PRODUCT`, `OTHER`, `MISC`, `NOT_APPLICABLE` |
| `language` | string | No | Language code (default: `en`) |

**Response:** `200 OK`
```json
{
  "canonical_name": "United States",
  "canonical_id": "Q30",
  "aliases": ["USA", "US", "United States of America", "U.S.", "U.S.A."],
  "confidence": 0.98,
  "source": "wikidata",
  "entity_type": "LOCATION",
  "processing_time_ms": 145.2
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `canonical_name` | string | Standardized entity name |
| `canonical_id` | string \| null | Wikidata Q-ID (e.g., "Q30") |
| `aliases` | array[string] | Known variations of this entity |
| `confidence` | float | Confidence score (0.0-1.0) |
| `source` | string | Match source: `exact`, `fuzzy`, `semantic`, `wikidata`, `new` |
| `entity_type` | string | Entity type |
| `processing_time_ms` | float | Processing time in milliseconds |

**Example:**
```bash
curl -X POST http://localhost:8112/api/v1/canonicalization/canonicalize \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "Barack Obama",
    "entity_type": "PERSON",
    "language": "en"
  }'
```

**Error Responses:**
- `400 Bad Request` - Invalid entity_type or missing required fields
- `500 Internal Server Error` - Canonicalization pipeline failure

---

#### 1.2 Canonicalize Batch

Process multiple entities in a single request. More efficient than individual calls for large batches.

```
POST /api/v1/canonicalization/canonicalize/batch
```

**Request Body:**
```json
{
  "entities": [
    {
      "entity_name": "USA",
      "entity_type": "LOCATION",
      "language": "en"
    },
    {
      "entity_name": "Barack Obama",
      "entity_type": "PERSON",
      "language": "en"
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "canonical_name": "United States",
      "canonical_id": "Q30",
      "aliases": ["USA", "US", "United States of America"],
      "confidence": 0.98,
      "source": "wikidata",
      "entity_type": "LOCATION"
    },
    {
      "canonical_name": "Barack Obama",
      "canonical_id": "Q76",
      "aliases": ["Barack Hussein Obama", "Obama"],
      "confidence": 0.99,
      "source": "wikidata",
      "entity_type": "PERSON"
    }
  ],
  "total_processed": 2,
  "total_time_ms": 287.5
}
```

**Performance:**
- Batch processing uses connection pooling and parallel Wikidata lookups
- Recommended batch size: 50-100 entities
- Maximum batch size: 1000 entities (adjust based on timeout settings)

**Example:**
```bash
curl -X POST http://localhost:8112/api/v1/canonicalization/canonicalize/batch \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {"entity_name": "USA", "entity_type": "LOCATION"},
      {"entity_name": "NASA", "entity_type": "ORGANIZATION"}
    ]
  }'
```

---

#### 1.3 Get Entity Aliases

Retrieve all known aliases for a canonical entity.

```
GET /api/v1/canonicalization/aliases/{canonical_name}?entity_type={type}
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `canonical_name` | string | Yes | Canonical entity name |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | Entity type (e.g., "LOCATION") |

**Response:** `200 OK`
```json
["USA", "US", "United States of America", "U.S.", "U.S.A."]
```

**Example:**
```bash
curl "http://localhost:8112/api/v1/canonicalization/aliases/United%20States?entity_type=LOCATION"
```

**Error Responses:**
- `404 Not Found` - Canonical entity does not exist
- `400 Bad Request` - Missing entity_type parameter

---

### 2. Statistics & Analytics

#### 2.1 Get Basic Statistics

Get high-level canonicalization statistics.

```
GET /api/v1/canonicalization/stats
```

**Response:** `200 OK`
```json
{
  "total_canonical_entities": 392,
  "total_aliases": 721,
  "wikidata_linked": 287,
  "coverage_percentage": 184.0,
  "cache_hit_rate": 0.89
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `total_canonical_entities` | integer | Total unique canonical entities |
| `total_aliases` | integer | Total alias mappings |
| `wikidata_linked` | integer | Entities with Wikidata Q-IDs |
| `coverage_percentage` | float | Aliases per entity ratio × 100 |
| `cache_hit_rate` | float | Cache hit rate (0.0-1.0) |

**Example:**
```bash
curl http://localhost:8112/api/v1/canonicalization/stats
```

---

#### 2.2 Get Detailed Statistics

Get comprehensive statistics for admin dashboard.

```
GET /api/v1/canonicalization/stats/detailed
```

**Response:** `200 OK`
```json
{
  "total_canonical_entities": 392,
  "total_aliases": 721,
  "wikidata_linked": 287,
  "wikidata_coverage_percent": 73.2,
  "deduplication_ratio": 1.84,
  "source_breakdown": {
    "exact": 0,
    "fuzzy": 0,
    "semantic": 0,
    "wikidata": 287,
    "new": 105
  },
  "entity_type_distribution": {
    "PERSON": 142,
    "ORGANIZATION": 98,
    "LOCATION": 87,
    "EVENT": 34,
    "PRODUCT": 12,
    "OTHER": 11,
    "MISC": 5,
    "NOT_APPLICABLE": 3
  },
  "top_entities_by_aliases": [
    {
      "canonical_name": "United States",
      "canonical_id": "Q30",
      "entity_type": "LOCATION",
      "alias_count": 8,
      "wikidata_linked": true
    }
  ],
  "entities_without_qid": 105,
  "avg_cache_hit_time_ms": 2.1,
  "cache_hit_rate": 89.0,
  "total_api_calls_saved": 1247,
  "estimated_cost_savings_monthly": 2.49
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `deduplication_ratio` | float | Average aliases per canonical entity |
| `source_breakdown` | object | Count by canonicalization method |
| `entity_type_distribution` | object | Count by entity type |
| `top_entities_by_aliases` | array | Top 10 entities by alias count |
| `entities_without_qid` | integer | Entities missing Wikidata Q-IDs |
| `avg_cache_hit_time_ms` | float | Average cache lookup time |
| `total_api_calls_saved` | integer | API calls avoided via caching |
| `estimated_cost_savings_monthly` | float | Estimated monthly savings in USD |

**Use Case:** Admin dashboard statistics card

**Example:**
```bash
curl http://localhost:8112/api/v1/canonicalization/stats/detailed
```

---

#### 2.3 Get Entity Type Trends

Get time-series data showing entity growth by type over time.

```
GET /api/v1/canonicalization/trends/entity-types?days={days}
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Number of days (1-365) |

**Response:** `200 OK`
```json
{
  "trends": [
    {
      "date": "2025-10-24",
      "PERSON": 87,
      "ORGANIZATION": 54,
      "LOCATION": 32,
      "EVENT": 18,
      "PRODUCT": 3,
      "OTHER": 2,
      "MISC": 1,
      "NOT_APPLICABLE": 0
    },
    {
      "date": "2025-10-23",
      "PERSON": 12,
      "ORGANIZATION": 8,
      "LOCATION": 5,
      "EVENT": 2,
      "PRODUCT": 0,
      "OTHER": 0,
      "MISC": 0,
      "NOT_APPLICABLE": 0
    }
  ],
  "days": 30,
  "total_entities": 392
}
```

**Features:**
- Daily entity counts by type
- Fills missing dates with zeros
- Ordered chronologically (oldest to newest)
- Useful for visualizing entity growth trends

**Use Case:** Frontend line chart showing entity type growth over time

**Example:**
```bash
# Get last 7 days
curl "http://localhost:8112/api/v1/canonicalization/trends/entity-types?days=7"

# Get last year
curl "http://localhost:8112/api/v1/canonicalization/trends/entity-types?days=365"
```

---

### 3. Batch Reprocessing

**Purpose:** Retroactively improve data quality by:
- Finding and merging duplicate entities
- Adding missing Wikidata Q-IDs
- Applying fuzzy and semantic matching to existing entities

**Use Case:** Run after system improvements or to fix data quality issues.

---

#### 3.1 Start Batch Reprocessing

Start a batch reprocessing job for all entities.

```
POST /api/v1/canonicalization/reprocess/start
```

**Request Body:**
```json
{
  "dry_run": false
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `dry_run` | boolean | No | false | If true, simulate without making changes |

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Batch reprocessing started",
  "dry_run": false
}
```

**6-Phase Pipeline:**
1. **Analyzing** - Count entities, calculate progress estimates
2. **Fuzzy Matching** - Find similar names (Levenshtein distance < 0.8)
3. **Semantic Matching** - Find semantically similar entities (cosine similarity > 0.9)
4. **Wikidata Lookup** - Enrich entities with missing Q-IDs
5. **Merging** - Execute merge operations (handle unique constraints)
6. **Updating** - Update Neo4j graph, aliases, cleanup

**Behavior:**
- Only one reprocessing job can run at a time
- Job runs asynchronously in background
- Use `/reprocess/status` to monitor progress

**Example:**
```bash
# Production run
curl -X POST http://localhost:8112/api/v1/canonicalization/reprocess/start \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'

# Test run (no changes)
curl -X POST http://localhost:8112/api/v1/canonicalization/reprocess/start \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
```

**Error Responses:**
- `409 Conflict` - Batch reprocessing already running
- `500 Internal Server Error` - Failed to start job

---

#### 3.2 Get Reprocessing Status

Get real-time status of the currently running batch reprocessing job.

```
GET /api/v1/canonicalization/reprocess/status
```

**Response:** `200 OK`

**When idle (no job):**
```json
{
  "status": "idle",
  "progress_percent": 0,
  "current_phase": null,
  "entities_processed": 0,
  "total_entities": 0,
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "dry_run": false,
  "stats": {
    "entities_merged": 0,
    "duplicates_found": 0,
    "qids_added": 0
  }
}
```

**When running:**
```json
{
  "status": "running",
  "progress_percent": 45.2,
  "current_phase": "semantic_matching",
  "entities_processed": 177,
  "total_entities": 392,
  "started_at": "2025-10-24T10:15:30Z",
  "completed_at": null,
  "error_message": null,
  "dry_run": false,
  "stats": {
    "entities_merged": 12,
    "duplicates_found": 12,
    "qids_added": 5
  }
}
```

**When completed:**
```json
{
  "status": "completed",
  "progress_percent": 100,
  "current_phase": "updating",
  "entities_processed": 392,
  "total_entities": 392,
  "started_at": "2025-10-24T10:15:30Z",
  "completed_at": "2025-10-24T10:18:45Z",
  "error_message": null,
  "dry_run": false,
  "stats": {
    "entities_merged": 23,
    "duplicates_found": 23,
    "qids_added": 47
  }
}
```

**Status Values:**
- `idle` - No job running
- `running` - Job in progress
- `completed` - Job finished successfully
- `failed` - Job encountered error

**Phase Values:**
- `analyzing` - Counting entities
- `fuzzy_matching` - Finding similar names
- `semantic_matching` - Finding semantic similarities
- `wikidata_lookup` - Enriching with Q-IDs
- `merging` - Merging duplicates
- `updating` - Updating database and graph

**Polling Recommendation:**
- Poll every 5 seconds during active job
- Use frontend force polling pattern (30s @ 1s intervals after start)

**Example:**
```bash
curl http://localhost:8112/api/v1/canonicalization/reprocess/status
```

---

#### 3.3 Stop Batch Reprocessing

Stop the currently running batch reprocessing job gracefully.

```
POST /api/v1/canonicalization/reprocess/stop
```

**Behavior:**
- Job finishes current operation before stopping
- Partial progress is saved
- Statistics reflect work completed before stop

**Response:** `200 OK`
```json
{
  "message": "Batch reprocessing stopped",
  "entities_processed": 177,
  "stats": {
    "entities_merged": 12,
    "duplicates_found": 12,
    "qids_added": 5
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8112/api/v1/canonicalization/reprocess/stop
```

**Error Responses:**
- `404 Not Found` - No reprocessing job is currently running
- `500 Internal Server Error` - Failed to stop job

---

### 4. Health Check

#### 4.1 Service Health

Check if service is running and healthy.

```
GET /api/v1/canonicalization/health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "entity-canonicalization-service"
}
```

**Example:**
```bash
curl http://localhost:8112/api/v1/canonicalization/health
```

---

## Request Schemas

### CanonicalizeRequest
```typescript
{
  entity_name: string      // Entity name to canonicalize
  entity_type: EntityType  // Entity type enum
  language?: string        // Language code (default: "en")
}
```

### CanonicalizeBatchRequest
```typescript
{
  entities: Array<{
    entity_name: string
    entity_type: EntityType
    language?: string
  }>
}
```

### StartReprocessingRequest
```typescript
{
  dry_run?: boolean  // Test mode without changes (default: false)
}
```

---

## Response Schemas

### CanonicalizeResponse
```typescript
{
  canonical_name: string      // Standardized name
  canonical_id: string | null // Wikidata Q-ID (e.g., "Q30")
  aliases: string[]           // Known variations
  confidence: number          // 0.0-1.0
  source: string              // "exact" | "fuzzy" | "semantic" | "wikidata" | "new"
  entity_type: string         // Entity type
  processing_time_ms?: number // Processing time
}
```

### ReprocessingStatus
```typescript
{
  status: "idle" | "running" | "completed" | "failed"
  progress_percent: number    // 0-100
  current_phase: string | null
  entities_processed: number
  total_entities: number
  started_at: string | null   // ISO 8601 timestamp
  completed_at: string | null // ISO 8601 timestamp
  error_message: string | null
  dry_run: boolean
  stats: {
    entities_merged: number
    duplicates_found: number
    qids_added: number
  }
}
```

---

## Entity Types

Valid values for `entity_type` parameter:

| Type | Description | Examples |
|------|-------------|----------|
| `PERSON` | People, individuals | "Barack Obama", "Angela Merkel" |
| `ORGANIZATION` | Companies, institutions | "NASA", "European Union" |
| `LOCATION` | Places, regions | "United States", "Paris" |
| `EVENT` | Events, occurrences | "World War II", "Olympics 2024" |
| `PRODUCT` | Products, brands | "iPhone", "Windows" |
| `OTHER` | Other entities | Miscellaneous entities |
| `MISC` | Miscellaneous | Uncategorized |
| `NOT_APPLICABLE` | Not an entity | Used when entity extraction fails |

---

## Database Schema

### Primary Tables

#### canonical_entities
Stores canonical entity forms with Wikidata enrichment.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `name` | VARCHAR(500) | Canonical entity name |
| `type` | EntityType | Entity type enum |
| `wikidata_id` | VARCHAR(50) | Wikidata Q-ID (nullable) |
| `language` | VARCHAR(10) | Language code |
| `confidence` | FLOAT | Canonicalization confidence |
| `source` | VARCHAR(50) | Match source |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `(name, type, language)`
- Index on `wikidata_id`
- Index on `type`
- Index on `created_at` (for trends queries)

#### entity_aliases
Maps alias variations to canonical entities.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `canonical_entity_id` | UUID | Foreign key to canonical_entities |
| `alias` | VARCHAR(500) | Alias variation |
| `confidence` | FLOAT | Alias match confidence |
| `created_at` | TIMESTAMP | Creation timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key on `canonical_entity_id`
- Unique index on `(alias, canonical_entity_id)`
- Index on `alias` (for fast alias lookups)

---

## Error Codes

| HTTP Code | Meaning | When It Occurs |
|-----------|---------|----------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created (not used in this service) |
| 400 | Bad Request | Invalid entity_type, missing required fields, invalid parameters |
| 404 | Not Found | Canonical entity not found, no reprocessing job running |
| 409 | Conflict | Batch reprocessing already running |
| 500 | Internal Server Error | Pipeline failure, database error, Wikidata API failure |

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example:**
```json
{
  "detail": "Batch reprocessing is already running"
}
```

---

## Performance Considerations

### Caching
- Alias lookups are cached in-memory for fast repeated queries
- Cache hit rate typically 89%+
- Average cache hit time: ~2ms
- Cache automatically invalidated on entity updates

### Batch Processing
- Use `/canonicalize/batch` for > 5 entities
- Recommended batch size: 50-100 entities
- Maximum batch size: 1000 entities
- Batch processing is ~3-5x faster than individual calls

### Wikidata API
- Rate limited: 200 requests/second (Wikidata public API limit)
- Implements exponential backoff on 429 errors
- Connection pooling for concurrent requests
- Typical response time: 100-200ms per entity

### Database Queries
- Entity type trends query optimized with date casting and grouping
- Indexes on created_at, type, and alias fields
- Detailed stats query uses multiple aggregations (~50ms)

---

## Rate Limits

**Current Status:** No rate limits implemented (internal service)

**Recommendations for Production:**
- Implement rate limiting at API gateway level if exposed externally
- Suggested limits:
  - `/canonicalize`: 100 requests/minute per client
  - `/canonicalize/batch`: 10 requests/minute per client
  - `/stats`: 20 requests/minute per client
  - `/reprocess/*`: Admin-only endpoints

---

## Versioning & Change Management

**Current Version:** v1

**API Versioning:**
- Prefix: `/api/v1/`
- Breaking changes will increment version (v2, v3, etc.)
- Old versions maintained for 6 months after deprecation

**Deprecation Policy:**
- 6-month notice before removing endpoints
- Deprecation warnings in response headers
- Migration guide provided

**Change Log:**
- See `docs/CHANGELOG.md` for version history
- Recent changes: 2025-10-24 - Added trends endpoint, batch reprocessing

---

## Integration Examples

### Python
```python
import requests

# Canonicalize single entity
response = requests.post(
    "http://localhost:8112/api/v1/canonicalization/canonicalize",
    json={
        "entity_name": "USA",
        "entity_type": "LOCATION"
    }
)
result = response.json()
print(f"Canonical: {result['canonical_name']} ({result['canonical_id']})")

# Get statistics
stats = requests.get(
    "http://localhost:8112/api/v1/canonicalization/stats/detailed"
).json()
print(f"Total entities: {stats['total_canonical_entities']}")
```

### TypeScript/JavaScript
```typescript
// Fetch entity type trends
const response = await fetch(
  'http://localhost:8112/api/v1/canonicalization/trends/entity-types?days=30'
)
const data = await response.json()
console.log(`Total entities: ${data.total_entities}`)

// Start batch reprocessing
const startResponse = await fetch(
  'http://localhost:8112/api/v1/canonicalization/reprocess/start',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dry_run: false })
  }
)
const job = await startResponse.json()
console.log(`Job started: ${job.job_id}`)
```

### Curl
```bash
# Canonicalize batch
curl -X POST http://localhost:8112/api/v1/canonicalization/canonicalize/batch \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {"entity_name": "USA", "entity_type": "LOCATION"},
      {"entity_name": "NASA", "entity_type": "ORGANIZATION"}
    ]
  }' | jq

# Monitor reprocessing
watch -n 5 'curl -s http://localhost:8112/api/v1/canonicalization/reprocess/status | jq'
```

---

## Troubleshooting

### Common Issues

**Issue:** Canonicalization returns low confidence scores
- **Cause:** Entity name spelling errors, unusual formatting
- **Solution:** Use fuzzy matching threshold, verify entity_type is correct

**Issue:** Batch reprocessing stuck at 0%
- **Cause:** Database lock, large entity count
- **Solution:** Check service logs, ensure no long-running queries

**Issue:** Wikidata Q-IDs not being added
- **Cause:** Wikidata API rate limit, network issues
- **Solution:** Check Wikidata API status, retry after cooldown period

**Issue:** 409 Conflict when starting reprocessing
- **Cause:** Previous job still running
- **Solution:** Check `/reprocess/status`, use `/reprocess/stop` if needed

**Issue:** High memory usage during batch processing
- **Cause:** Large batch size, many aliases per entity
- **Solution:** Reduce batch size, restart service if needed

### Debug Logs

Enable debug logging:
```bash
docker logs -f entity-canonicalization-service --tail 100
```

Look for:
- `INFO - Started batch reprocessing (job_id=...)`
- `INFO - Phase: semantic_matching (progress: 45.2%)`
- `WARNING - Low confidence match: ...`
- `ERROR - Failed to canonicalize entity: ...`

### Health Checks

```bash
# Service health
curl http://localhost:8112/api/v1/canonicalization/health

# Database connectivity (check service logs)
docker logs entity-canonicalization-service | grep "Database connection"

# Reprocessing status
curl http://localhost:8112/api/v1/canonicalization/reprocess/status
```

---

## Related Documentation

- **Service Architecture:** `docs/services/entity-canonicalization-service.md`
- **Knowledge Graph API:** `docs/api/knowledge-graph-service-api.md`
- **Frontend Dashboard:** `docs/frontend/knowledge-graph-admin-dashboard.md`
- **Batch Reprocessing ADR:** `docs/decisions/ADR-020-batch-reprocessing.md`
- **Changelog:** `docs/CHANGELOG.md`

---

**Last Updated:** 2025-10-24
**Authors:** Development Team
**Maintainer:** Entity Canonicalization Service Team

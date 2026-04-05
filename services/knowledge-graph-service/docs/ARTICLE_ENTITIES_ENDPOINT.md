# Article Entities Endpoint

## Overview

The Article Entities endpoint provides access to entities extracted from specific articles in the knowledge graph. It retrieves all entities that have an `EXTRACTED_FROM` relationship to a given article.

## Endpoint

```
GET /api/v1/graph/articles/{article_id}/entities
```

## Use Cases

1. **Article Entity Visualization**: Display all entities mentioned in an article
2. **Entity Filtering**: Filter entities by type (PERSON, ORGANIZATION, etc.)
3. **Entity Analysis**: Analyze extraction confidence and mention frequency
4. **Named Entity Recognition (NER) Review**: Review NER pipeline output
5. **Knowledge Graph Exploration**: Navigate from articles to their entities

## Request Parameters

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `article_id` | string | Yes | Article identifier (UUID or custom ID) |

### Query Parameters

| Parameter | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `entity_type` | string | No | None | - | Filter by entity type (PERSON, ORGANIZATION, LOCATION, etc.) |
| `limit` | integer | No | 50 | 1-200 | Maximum number of entities to return |

## Response Model

```json
{
  "article_id": "string",
  "article_title": "string | null",
  "article_url": "string | null",
  "total_entities": 0,
  "entities": [
    {
      "name": "string",
      "type": "string",
      "wikidata_id": "string | null",
      "confidence": 0.0,
      "mention_count": 0,
      "first_mention_index": 0
    }
  ],
  "query_time_ms": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `article_id` | string | Article identifier (same as request) |
| `article_title` | string \| null | Article title if Article node exists in graph |
| `article_url` | string \| null | Article URL if available |
| `total_entities` | integer | Total number of entities returned (respects filters) |
| `entities` | array | List of entities extracted from article |
| `query_time_ms` | integer | Query execution time in milliseconds |

### Entity Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Entity name |
| `type` | string | Entity type (PERSON, ORGANIZATION, LOCATION, etc.) |
| `wikidata_id` | string \| null | Wikidata identifier if entity enriched |
| `confidence` | float | Extraction confidence score (0.0-1.0) |
| `mention_count` | integer | Number of times entity mentioned in article |
| `first_mention_index` | integer \| null | Character index of first mention in article text |

## Ordering

Entities are ordered by:
1. **Confidence** (descending): Higher confidence entities first
2. **Mention count** (descending): More frequently mentioned entities first (if confidence equal)

This ensures the most relevant and reliable entities appear first.

## Examples

### Basic Request

Fetch entities from an article:

```bash
curl http://localhost:8111/api/v1/graph/articles/abc123/entities
```

**Response:**
```json
{
  "article_id": "abc123",
  "article_title": "Tesla Announces New Factory in Germany",
  "article_url": "https://example.com/articles/abc123",
  "total_entities": 3,
  "entities": [
    {
      "name": "Tesla",
      "type": "ORGANIZATION",
      "wikidata_id": "Q478214",
      "confidence": 0.98,
      "mention_count": 5,
      "first_mention_index": 42
    },
    {
      "name": "Germany",
      "type": "LOCATION",
      "wikidata_id": "Q183",
      "confidence": 0.95,
      "mention_count": 3,
      "first_mention_index": 128
    },
    {
      "name": "Elon Musk",
      "type": "PERSON",
      "wikidata_id": "Q317521",
      "confidence": 0.92,
      "mention_count": 2,
      "first_mention_index": 215
    }
  ],
  "query_time_ms": 45
}
```

### Filter by Entity Type

Fetch only PERSON entities:

```bash
curl "http://localhost:8111/api/v1/graph/articles/abc123/entities?entity_type=PERSON"
```

**Response:**
```json
{
  "article_id": "abc123",
  "article_title": "Tesla Announces New Factory in Germany",
  "article_url": "https://example.com/articles/abc123",
  "total_entities": 1,
  "entities": [
    {
      "name": "Elon Musk",
      "type": "PERSON",
      "wikidata_id": "Q317521",
      "confidence": 0.92,
      "mention_count": 2,
      "first_mention_index": 215
    }
  ],
  "query_time_ms": 38
}
```

### Limit Results

Fetch maximum 10 entities:

```bash
curl "http://localhost:8111/api/v1/graph/articles/abc123/entities?limit=10"
```

### Combined Filters

Fetch top 5 ORGANIZATION entities:

```bash
curl "http://localhost:8111/api/v1/graph/articles/abc123/entities?entity_type=ORGANIZATION&limit=5"
```

## Empty Results

The endpoint returns an empty list in the following cases:

1. **Article has no entities extracted**: Processing not yet complete
2. **Article doesn't exist**: Invalid article_id
3. **All entities filtered out**: No entities match entity_type filter

**Example (no entities):**
```json
{
  "article_id": "nonexistent",
  "article_title": null,
  "article_url": null,
  "total_entities": 0,
  "entities": [],
  "query_time_ms": 12
}
```

**Note**: `article_title` and `article_url` will be `null` if the Article node doesn't exist in Neo4j yet.

## Error Responses

### 422 Validation Error

Invalid query parameters (e.g., limit > 200):

```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 200",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### 500 Internal Server Error

Neo4j connection failure or query error:

```json
{
  "detail": "Failed to fetch article entities: Neo4j connection timeout"
}
```

## Related Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/graph/articles/{article_id}/info` | Get article metadata and entity count |
| `GET /api/v1/graph/entity/{entity_name}/connections` | Get entity connections/relationships |
| `GET /api/v1/graph/stats` | Get overall graph statistics |

## Implementation Details

### Neo4j Cypher Query

The endpoint uses the following Cypher pattern:

```cypher
// Try to find Article node (may not exist yet)
OPTIONAL MATCH (a:Article {id: $article_id})

// Find entities with EXTRACTED_FROM relationship
MATCH (e:Entity)-[r:EXTRACTED_FROM]->(article)
WHERE article.id = $article_id OR article = a
  AND ($entity_type IS NULL OR e.type = $entity_type)

// Return article info and entities
RETURN
    e.name AS name,
    e.type AS type,
    e.wikidata_id AS wikidata_id,
    r.confidence AS confidence,
    r.mention_count AS mention_count,
    r.first_mention_index AS first_mention_index,
    a.id AS article_id,
    a.title AS article_title,
    a.url AS article_url,
    a.published_date AS published_date
ORDER BY r.confidence DESC, r.mention_count DESC
LIMIT $limit
```

### Graceful Degradation

The endpoint gracefully handles cases where:
- **Article node doesn't exist**: Returns entities with `article_title=null`
- **No EXTRACTED_FROM relationships**: Returns empty entity list
- **Neo4j connection issues**: Returns 500 error with details

### Performance

- **Query time**: < 100ms for typical articles (< 50 entities)
- **Index usage**: Uses `Entity.name` index and relationship traversal
- **Pagination**: Built-in via `limit` parameter (max 200)

## Metrics

The endpoint records Prometheus metrics:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `kg_queries_total` | Counter | `endpoint=article_entities`, `status` | Total queries (success/error) |
| `kg_query_duration_seconds` | Histogram | `endpoint=article_entities` | Query response time |
| `kg_query_results_size` | Histogram | `endpoint=article_entities` | Number of entities returned |

## Testing

Run endpoint tests:

```bash
# Unit tests
pytest tests/test_article_entities.py -v

# Integration tests (requires Neo4j)
pytest tests/test_article_entities.py -v -m integration
```

## Future Enhancements

1. **Pagination**: Add cursor-based pagination for large entity sets
2. **Aggregation**: Add entity type counts in response
3. **Sentiment**: Include entity sentiment scores if available
4. **Caching**: Cache frequently accessed article entities
5. **Batch API**: Fetch entities for multiple articles in one request

## Files

| File | Purpose |
|------|---------|
| `app/api/routes/articles.py` | API endpoint definition |
| `app/services/article_service.py` | Business logic for article queries |
| `app/models/articles.py` | Pydantic models for requests/responses |
| `tests/test_article_entities.py` | Endpoint tests |

## Support

For issues or questions:
- Check API docs: `http://localhost:8111/docs`
- Review logs: `docker logs news-knowledge-graph-service`
- Check Neo4j: `http://localhost:7474` (Neo4j Browser)

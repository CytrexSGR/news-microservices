# Article Entities Endpoint - Quick Reference

## Endpoints

### Get Article Entities
```
GET /api/v1/graph/articles/{article_id}/entities
```

**Parameters:**
- `entity_type` (optional): Filter by type (PERSON, ORGANIZATION, LOCATION, etc.)
- `limit` (optional): Max results (1-200, default: 50)

**Response:**
```json
{
  "article_id": "string",
  "article_title": "string | null",
  "total_entities": 0,
  "entities": [...],
  "query_time_ms": 0
}
```

### Get Article Info
```
GET /api/v1/graph/articles/{article_id}/info
```

**Response:**
```json
{
  "article_id": "string",
  "title": "string",
  "entity_count": 0,
  "query_time_ms": 0
}
```

## Quick Examples

```bash
# All entities
curl http://localhost:8111/api/v1/graph/articles/ABC123/entities

# Filter by type
curl "http://localhost:8111/api/v1/graph/articles/ABC123/entities?entity_type=PERSON"

# Limit results
curl "http://localhost:8111/api/v1/graph/articles/ABC123/entities?limit=10"

# Combined
curl "http://localhost:8111/api/v1/graph/articles/ABC123/entities?entity_type=ORGANIZATION&limit=5"
```

## Entity Types

Common entity types:
- `PERSON` - People
- `ORGANIZATION` - Companies, institutions
- `LOCATION` - Places, cities, countries
- `PRODUCT` - Products, brands
- `EVENT` - Events, conferences
- `DATE` - Dates, time references
- `MONEY` - Monetary amounts

## Response Fields

### Entity Object
```json
{
  "name": "Entity Name",
  "type": "PERSON",
  "wikidata_id": "Q12345",
  "confidence": 0.95,
  "mention_count": 3,
  "first_mention_index": 42
}
```

| Field | Type | Description |
|-------|------|-------------|
| name | string | Entity name |
| type | string | Entity type |
| wikidata_id | string? | Wikidata ID (if enriched) |
| confidence | float | Confidence (0.0-1.0) |
| mention_count | int | # mentions in article |
| first_mention_index | int? | First mention position |

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (may have empty entities list) |
| 404 | Article not found (info endpoint only) |
| 422 | Validation error (invalid params) |
| 500 | Server error |

## Python Usage

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8111/api/v1/graph/articles/ABC123/entities",
        params={"entity_type": "PERSON", "limit": 10}
    )
    data = response.json()

    for entity in data['entities']:
        print(f"{entity['name']} ({entity['type']}): {entity['confidence']:.2%}")
```

## Metrics

View at `http://localhost:8111/metrics`:
- `kg_queries_total{endpoint="article_entities"}`
- `kg_query_duration_seconds{endpoint="article_entities"}`
- `kg_query_results_size{endpoint="article_entities"}`

## API Docs

Interactive documentation:
- **Swagger UI:** http://localhost:8111/docs
- **ReDoc:** http://localhost:8111/redoc
- **OpenAPI JSON:** http://localhost:8111/openapi.json

## Files

| File | Purpose |
|------|---------|
| `app/api/routes/articles.py` | API endpoints |
| `app/services/article_service.py` | Business logic |
| `app/models/articles.py` | Data models |
| `tests/test_article_entities.py` | Tests |
| `docs/ARTICLE_ENTITIES_ENDPOINT.md` | Full documentation |
| `examples/article_entities_example.py` | Usage examples |

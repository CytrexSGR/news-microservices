# Admin Query Endpoint - Custom Cypher Queries

## Overview

The Knowledge Graph Service provides an **admin-only endpoint** for executing custom read-only Cypher queries against the Neo4j database.

**Location:** `/api/v1/graph/admin/query/cypher`

## Security Features

### 1. Read-Only Enforcement

All write operations are **strictly prohibited**:

- ❌ `CREATE` - Creating nodes/relationships
- ❌ `DELETE` - Deleting nodes/relationships
- ❌ `SET` - Modifying properties
- ❌ `MERGE` - Upserting nodes/relationships
- ❌ `DROP` - Dropping indexes/constraints
- ❌ `DETACH DELETE` - Detaching relationships
- ❌ `REMOVE` - Removing properties/labels
- ❌ `CALL dbms.*` - Database management procedures

### 2. Query Validation

Before execution, all queries are validated:

- **Syntax check**: Must contain `MATCH` or `RETURN`
- **Security check**: Forbidden keywords blocked
- **Pattern detection**: Dangerous patterns rejected (SQL injection-like)
- **Length limit**: Max 10,000 characters

### 3. Execution Safety

- **Timeout protection**: Max 30 seconds (default: 10s)
- **Result limiting**: Max 1,000 results (default: 100)
- **Auto-LIMIT**: Automatically adds `LIMIT` if missing
- **Query hashing**: SHA256 hash for logging/caching

### 4. Monitoring & Logging

- **WARNING logs**: All admin queries logged at WARNING level
- **Metrics**: Prometheus metrics for execution time, result size
- **Query hash**: Every query has unique hash for audit trail

## API Endpoints

### 1. Execute Custom Query

**POST** `/api/v1/graph/admin/query/cypher`

Execute a custom read-only Cypher query.

**Request Body:**
```json
{
  "query": "MATCH (e:Entity) WHERE e.type = $entity_type RETURN e.name LIMIT 10",
  "parameters": {
    "entity_type": "PERSON"
  },
  "limit": 10,
  "timeout_seconds": 10
}
```

**Response:**
```json
{
  "results": [
    {"e.name": "Elon Musk"},
    {"e.name": "Jeff Bezos"}
  ],
  "total_results": 2,
  "query_time_ms": 45,
  "query_hash": "a3f5d2e1b4c6f9e8..."
}
```

**Errors:**
- `400`: Query validation failed (write operations, forbidden patterns)
- `408`: Query timeout
- `500`: Execution error

### 2. Validate Query (Pre-flight)

**POST** `/api/v1/graph/admin/query/validate`

Validate a query without executing it.

**Request Body:**
```json
{
  "query": "MATCH (e:Entity) RETURN e.name LIMIT 10",
  "parameters": {}
}
```

**Response:**
```json
{
  "query_hash": "a3f5d2e1...",
  "query_length": 47,
  "is_valid": true,
  "validation_error": null,
  "has_limit": true,
  "parameter_count": 0
}
```

### 3. Get Allowed/Forbidden Clauses

**GET** `/api/v1/graph/admin/query/clauses`

Get lists of allowed and forbidden Cypher keywords.

**Response:**
```json
{
  "allowed_clauses": [
    "MATCH", "RETURN", "WHERE", "ORDER BY", "LIMIT"
  ],
  "forbidden_clauses": [
    "CREATE", "DELETE", "SET", "MERGE", "DROP"
  ],
  "max_query_length": 10000,
  "max_timeout_seconds": 30
}
```

### 4. Get Query Examples

**GET** `/api/v1/graph/admin/query/examples`

Get example queries for common use cases.

**Response:**
```json
{
  "examples": [
    {
      "title": "List All Entities",
      "description": "Get all entities with their types",
      "query": "MATCH (e:Entity) RETURN e.name, e.type LIMIT 10",
      "parameters": {}
    }
  ],
  "total_examples": 6
}
```

## Example Queries

### 1. List All Entities

```cypher
MATCH (e:Entity)
RETURN e.name, e.type
LIMIT 10
```

### 2. Find Entities by Type

```cypher
MATCH (e:Entity)
WHERE e.type = $entity_type
RETURN e.name, e.type
LIMIT 10
```

**Parameters:**
```json
{"entity_type": "PERSON"}
```

### 3. Get Entity Connections

```cypher
MATCH (source:Entity {name: $entity_name})-[r]->(target:Entity)
RETURN source.name, type(r) AS relationship, target.name, r.confidence
ORDER BY r.confidence DESC
LIMIT 10
```

**Parameters:**
```json
{"entity_name": "Tesla"}
```

### 4. Relationship Type Distribution

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY count DESC
LIMIT 10
```

### 5. High-Confidence Relationships

```cypher
MATCH (source:Entity)-[r]->(target:Entity)
WHERE r.confidence >= $min_confidence
RETURN source.name, type(r), target.name, r.confidence
ORDER BY r.confidence DESC
LIMIT 10
```

**Parameters:**
```json
{"min_confidence": 0.8}
```

### 6. Most Connected Entities

```cypher
MATCH (e:Entity)
OPTIONAL MATCH (e)-[r]-()
WITH e, count(r) AS connection_count
WHERE connection_count > 0
RETURN e.name, e.type, connection_count
ORDER BY connection_count DESC
LIMIT 10
```

## Usage Examples

### cURL

```bash
# Execute query
curl -X POST http://localhost:8111/api/v1/graph/admin/query/cypher \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (e:Entity) RETURN e.name LIMIT 5",
    "parameters": {},
    "limit": 5,
    "timeout_seconds": 10
  }'

# Validate query
curl -X POST http://localhost:8111/api/v1/graph/admin/query/validate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (e:Entity) RETURN e.name LIMIT 10",
    "parameters": {}
  }'

# Get allowed clauses
curl http://localhost:8111/api/v1/graph/admin/query/clauses

# Get examples
curl http://localhost:8111/api/v1/graph/admin/query/examples
```

### Python

```python
import requests

# Execute query
response = requests.post(
    "http://localhost:8111/api/v1/graph/admin/query/cypher",
    json={
        "query": "MATCH (e:Entity) WHERE e.type = $entity_type RETURN e.name LIMIT 10",
        "parameters": {"entity_type": "PERSON"},
        "limit": 10,
        "timeout_seconds": 10
    }
)

result = response.json()
print(f"Found {result['total_results']} entities in {result['query_time_ms']}ms")
for record in result['results']:
    print(record)
```

### JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:8111/api/v1/graph/admin/query/cypher', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'MATCH (e:Entity) RETURN e.name LIMIT 5',
    parameters: {},
    limit: 5,
    timeout_seconds: 10
  })
});

const result = await response.json();
console.log(`Found ${result.total_results} entities`);
```

## Testing

### Run Tests

```bash
cd /home/cytrex/news-microservices/services/knowledge-graph-service
docker compose exec knowledge-graph-service pytest tests/test_admin_query.py -v
```

### Test Coverage

- ✅ **Security validation**: All write operations blocked
- ✅ **Query validation**: Invalid queries rejected
- ✅ **Parameterized queries**: Parameters properly handled
- ✅ **Auto-LIMIT**: Automatically adds LIMIT if missing
- ✅ **Max limit enforcement**: Prevents excessive results
- ✅ **Allowed/forbidden clauses**: Documentation endpoint
- ✅ **Query examples**: Example queries provided
- ✅ **Security logging**: Admin queries logged at WARNING level

## Monitoring

### Prometheus Metrics

```
# Query execution count
kg_queries_total{endpoint="admin_cypher",status="success"} 42
kg_queries_total{endpoint="admin_cypher",status="error"} 2

# Query duration
kg_query_duration_seconds{endpoint="admin_cypher"} 0.045

# Result size
kg_query_results_size{endpoint="admin_cypher"} 10
```

### Log Examples

```
WARNING - ⚠️  ADMIN QUERY EXECUTION: query_length=208, parameters=[], limit=5, timeout=10s
INFO - Executing admin query (hash: af8279a1..., timeout: 10s)
INFO - Query completed (hash: af8279a1..., results: 5, time: 111ms)
INFO - ✓ Admin query completed: hash=af8279a1..., results=5, time=111ms
```

## Security Best Practices

### 1. Access Control

⚠️ **TODO**: Implement JWT-based authentication with admin role check.

**Current state**: Endpoint is accessible without authentication.

**Future implementation**:
```python
from app.api.dependencies import require_admin

@router.post("/query/cypher")
async def execute_custom_cypher_query(
    request: CypherQueryRequest,
    user: User = Depends(require_admin)  # JWT + role check
):
    ...
```

### 2. Rate Limiting

⚠️ **TODO**: Implement rate limiting to prevent abuse.

**Recommended**: Use FastAPI-Limiter or similar.

### 3. Audit Trail

✅ **Implemented**: All queries logged with:
- Query hash (SHA256)
- Query length
- Parameters (keys only, not values)
- Execution time
- Result count

### 4. Query Review

**Best practice**: Review admin query logs regularly:

```bash
# View recent admin queries
docker compose logs knowledge-graph-service | grep "ADMIN QUERY"

# Count queries per hour
docker compose logs knowledge-graph-service --since=1h | grep "ADMIN QUERY" | wc -l
```

## Limitations

### Current Limitations

1. **No authentication**: Endpoint accessible without JWT (TODO)
2. **No rate limiting**: No protection against query spam (TODO)
3. **No query caching**: Repeated queries not cached (future enhancement)
4. **No query history**: No persistent storage of executed queries (future enhancement)

### Query Limitations

1. **Max query length**: 10,000 characters
2. **Max timeout**: 30 seconds
3. **Max results**: 1,000 records
4. **Read-only**: No write operations allowed

## Troubleshooting

### Query Validation Fails

**Error**: `Write operations not allowed: CREATE`

**Solution**: Remove write operations (`CREATE`, `DELETE`, `SET`, etc.)

### Query Timeout

**Error**: `Query timeout after 10s`

**Solutions**:
1. Increase `timeout_seconds` (max: 30s)
2. Add more selective `WHERE` clauses
3. Reduce result set with `LIMIT`
4. Check for missing indexes

### Query Returns No Results

**Solutions**:
1. Check if entities exist: `MATCH (e:Entity) RETURN count(e)`
2. Verify property names: `MATCH (e:Entity) RETURN keys(e) LIMIT 1`
3. Test simpler queries first

### Neo4j Connection Error

**Error**: `Neo4j driver not initialized`

**Solutions**:
1. Check service health: `curl http://localhost:8111/health`
2. Verify Neo4j is running: `docker compose ps neo4j`
3. Check logs: `docker compose logs knowledge-graph-service`

## Implementation Files

- **Endpoint**: `/app/api/routes/admin_query.py`
- **Query Service**: `/app/services/query_service.py`
- **Validator**: `/app/services/query_validator.py`
- **Models**: `/app/models/admin_query.py`
- **Tests**: `/tests/test_admin_query.py`

## References

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Knowledge Graph Service Documentation](../README.md)
- [API Documentation](http://localhost:8111/docs) (Swagger UI)

---

**Last Updated**: 2025-11-02
**Version**: 1.0.0
**Status**: ✅ Production-ready (pending authentication implementation)

# Pathfinding Endpoint Documentation

## Overview

The pathfinding endpoint finds shortest paths between two entities in the knowledge graph using Neo4j's `allShortestPaths()` algorithm.

## Endpoint

```
GET /api/v1/graph/path/{entity1}/{entity2}
```

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `entity1` | string | required | - | Source entity name (case-sensitive) |
| `entity2` | string | required | - | Target entity name (case-sensitive) |
| `max_depth` | int | 3 | 1-5 | Maximum path length (hops) |
| `limit` | int | 3 | 1-10 | Maximum number of paths to return |
| `min_confidence` | float | 0.5 | 0.0-1.0 | Minimum relationship confidence score |

## Response Model

```json
{
  "paths": [
    {
      "length": 2,
      "nodes": [
        {"name": "Trump", "type": "PERSON"},
        {"name": "Musk", "type": "UNKNOWN"},
        {"name": "Tesla", "type": "ORGANIZATION"}
      ],
      "relationships": [
        {
          "type": "RELATED_TO",
          "confidence": 0.85,
          "evidence": "Trump äußerte sich nach Streit wieder positiv über Musk"
        },
        {
          "type": "WORKS_FOR",
          "confidence": 0.95,
          "evidence": "Musk could leave Tesla"
        }
      ]
    }
  ],
  "shortest_path_length": 2,
  "query_time_ms": 183,
  "entity1": "Trump",
  "entity2": "Tesla",
  "max_depth": 3,
  "total_paths_found": 3
}
```

## Examples

### Basic Usage

Find paths between two entities:

```bash
curl 'http://localhost:8111/api/v1/graph/path/Trump/Tesla'
```

### With Parameters

Find up to 5 paths with max depth of 4:

```bash
curl 'http://localhost:8111/api/v1/graph/path/Trump/Tesla?max_depth=4&limit=5'
```

### Higher Confidence Filter

Only include relationships with confidence >= 0.8:

```bash
curl 'http://localhost:8111/api/v1/graph/path/Trump/Tesla?min_confidence=0.8'
```

## Use Cases

1. **Connection Discovery**: Find how two entities are connected
2. **Network Analysis**: Analyze relationship chains and influence paths
3. **Investigation**: Discover hidden connections between people/organizations
4. **Influence Mapping**: Map paths of influence between entities

## Performance

- **Query Time**: Typically 50-200ms for depth 3
- **Scalability**: Higher max_depth values increase query time exponentially
- **Optimization**: Uses Neo4j indexes on entity names for fast lookups

### Performance Examples

| Depth | Entities | Query Time | Paths Found |
|-------|----------|------------|-------------|
| 2 | Trump → Tesla | ~100ms | 3 paths |
| 3 | Trump → Tesla | ~180ms | 3 paths |
| 4 | Trump → Biden | ~135ms | 1 path |

## Neo4j Cypher Query

The endpoint uses the following Cypher query pattern:

```cypher
MATCH path = allShortestPaths(
    (e1:Entity {name: $entity1})-[*1..{max_depth}]-(e2:Entity {name: $entity2})
)
WHERE all(r in relationships(path) WHERE r.confidence >= $min_confidence)
WITH path, length(path) AS path_length
ORDER BY path_length
LIMIT $limit
RETURN
    [node IN nodes(path) | {name: node.name, type: node.type}] AS nodes,
    [rel IN relationships(path) | {
        type: type(rel),
        confidence: rel.confidence,
        evidence: rel.evidence
    }] AS relationships,
    path_length
```

## Error Handling

### 404 Not Found

Returned when one or both entities don't exist in the graph:

```json
{
  "detail": "One or both entities not found in graph: 'NonExistent', 'Tesla'"
}
```

### Empty Result

When no paths are found, returns empty list:

```json
{
  "paths": [],
  "shortest_path_length": 0,
  "total_paths_found": 0
}
```

## Metrics

The endpoint records the following Prometheus metrics:

- `kg_queries_total{endpoint="pathfinding", status="success|error"}` - Total queries
- `kg_query_duration_seconds{endpoint="pathfinding"}` - Query duration histogram
- `kg_query_results_size{endpoint="pathfinding"}` - Number of paths returned

## Implementation Files

- **Route**: `/app/api/routes/pathfinding.py`
- **Service**: `/app/services/pathfinding_service.py`
- **Models**: `/app/models/pathfinding.py`

## Future Enhancements

1. **Weighted Pathfinding**: Use confidence scores as edge weights
2. **Filtered Paths**: Allow filtering by relationship types
3. **Path Scoring**: Calculate overall path confidence scores
4. **Temporal Paths**: Consider time-based constraints
5. **Bidirectional Search**: Optimize for very long paths

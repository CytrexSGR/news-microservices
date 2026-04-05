# Knowledge Graph Service

Graph database service for entity relationships and connections using Neo4j.

## Features

- **Entity Graph**: Neo4j-based knowledge graph for entities and relationships
- **Relationship Tracking**: Entity connections with confidence scores and evidence
- **Pathfinding**: Find shortest paths between entities
- **Graph Analytics**: Centrality, clustering, and network analysis
- **Entity Search**: Full-text search on entity names
- **Graph Enrichment**: Wikidata integration for entity enrichment
- **History Tracking**: Query history and popular connections
- **Quality Metrics**: Connection quality scores and validation

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Dependencies

```bash
# Neo4j
docker run -d --name kg-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5

# PostgreSQL (for metadata)
docker run -d --name kg-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=kg_db \
  -p 5432:5432 postgres:15

# RabbitMQ (for events)
docker run -d --name kg-rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management
```

### 4. Initialize Database

```bash
# Neo4j constraints and indexes will be created automatically
python -m app.main
```

### 5. Start API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8111 --reload
```

## API Endpoints

### Entity Queries

#### Get Entity Connections
```bash
GET /api/v1/graph/entity/Tesla/connections?limit=100
Authorization: Bearer <jwt-token> (optional)

# With relationship type filter
GET /api/v1/graph/entity/Tesla/connections?relationship_type=WORKS_FOR&limit=50
```

**Response:**
```json
{
  "nodes": [
    {
      "name": "Tesla",
      "type": "ORGANIZATION",
      "wikidata_id": "Q478214",
      "connection_count": 45
    },
    {
      "name": "Elon Musk",
      "type": "PERSON",
      "wikidata_id": "Q317521",
      "connection_count": 89
    }
  ],
  "edges": [
    {
      "source": "Elon Musk",
      "target": "Tesla",
      "relationship_type": "WORKS_FOR",
      "confidence": 0.95,
      "mention_count": 234,
      "evidence": ["article-uuid-1", "article-uuid-2"]
    }
  ],
  "total_nodes": 45,
  "total_edges": 67
}
```

#### Get Entity Details
```bash
GET /api/v1/graph/entity/Tesla
Authorization: Bearer <jwt-token> (optional)
```

### Search

#### Search Entities
```bash
GET /api/v1/graph/search?query=Tesla&limit=10

# With entity type filter
GET /api/v1/graph/search?query=Elon&entity_type=PERSON
```

**Response:**
```json
{
  "results": [
    {
      "name": "Tesla",
      "type": "ORGANIZATION",
      "last_seen": "2025-01-15T10:30:00Z",
      "connection_count": 45,
      "wikidata_id": "Q478214"
    }
  ],
  "total_results": 1,
  "query_time_ms": 12.5
}
```

#### Autocomplete Suggestions
```bash
GET /api/v1/graph/search/autocomplete?query=Tes&limit=5
```

### Pathfinding

#### Find Paths Between Entities
```bash
GET /api/v1/graph/path/{entity1}/{entity2}

# Example: Find paths between Trump and Israel
GET /api/v1/graph/path/Trump/Israel
```

**Response:**
```json
{
  "paths": [
    {
      "length": 2,
      "nodes": ["Trump", "United States", "Israel"],
      "relationships": [
        {"type": "LOCATED_IN", "confidence": 0.92},
        {"type": "RELATED_TO", "confidence": 0.88}
      ]
    },
    {
      "length": 3,
      "nodes": ["Trump", "Biden", "White House", "Israel"],
      "relationships": [
        {"type": "MENTIONED_WITH", "confidence": 0.95},
        {"type": "WORKS_FOR", "confidence": 0.91},
        {"type": "RELATED_TO", "confidence": 0.87}
      ]
    }
  ],
  "total_paths": 15,
  "shortest_path_length": 2
}
```

### Analytics

#### Get Basic Graph Statistics
```bash
GET /api/v1/graph/stats

# Response (simple stats)
{
  "total_nodes": 46177,
  "total_relationships": 69437,
  "entity_types": {
    "UNKNOWN": 9560,
    "MISC": 8650,
    "PERSON": 7101,
    "ORGANIZATION": 6551,
    "ARTICLE": 5395,
    "PRODUCT": 3420,
    "LOCATION": 3284,
    "EVENT": 1636,
    "DATE": 579
  }
}
```

#### Get Detailed Graph Statistics
```bash
GET /api/v1/graph/stats/detailed

# Response (comprehensive stats with quality metrics)
{
  "graph_size": {
    "total_nodes": 46177,
    "total_relationships": 69437,
    "entity_type_distribution": {...}
  },
  "relationship_quality": {
    "high_confidence_count": 61386,
    "medium_confidence_count": 8051,
    "low_confidence_count": 0,
    "high_confidence_ratio": 0.884,
    "medium_confidence_ratio": 0.116,
    "low_confidence_ratio": 0.0
  },
  "data_completeness": {
    "not_applicable_count": 23,
    "not_applicable_ratio": 0.0003,
    "orphaned_entities_count": 11090,
    "entities_with_wikidata": 4088,
    "wikidata_coverage_ratio": 0.089
  },
  "quality_score": 75.96,
  "top_entities": [
    {
      "name": "Trump",
      "type": "PERSON",
      "connection_count": 728
    }
  ],
  "query_time_ms": 335
}
```

#### Get Top Connected Entities
```bash
GET /api/v1/graph/analytics/top-entities?limit=10&entity_type=PERSON

# Response
[
  {
    "name": "Trump",
    "type": "PERSON",
    "connection_count": 728,
    "sample_connections": [
      {
        "name": "Israel",
        "type": "LOCATION",
        "relationship_type": "MENTIONED_WITH"
      }
    ]
  }
]
```

#### Get Relationship Statistics
```bash
GET /api/v1/graph/analytics/relationship-stats

# Response
{
  "total_relationships": 69437,
  "relationship_types": [
    {
      "type": "MENTIONED_IN",
      "count": 28941,
      "percentage": 41.7,
      "avg_confidence": 0.95,
      "quality": "high",
      "examples": [...]
    }
  ],
  "patterns": [
    {
      "source_type": "PERSON",
      "relationship_type": "WORKS_FOR",
      "target_type": "ORGANIZATION",
      "count": 3486
    }
  ],
  "quality_insights": {
    "high_quality_count": 8,
    "needs_review_count": 0,
    "avg_confidence_overall": 0.884
  }
}
```

#### Get Growth History
```bash
GET /api/v1/graph/analytics/growth-history?days=30

# Response
[
  {
    "date": "2025-11-01",
    "new_nodes": 450,
    "new_relationships": 1200,
    "total_nodes": 45000,
    "total_relationships": 68000
  }
]
```

#### Get Cross-Article Coverage
```bash
GET /api/v1/graph/analytics/cross-article-coverage?top_limit=10

# Response
{
  "total_articles": 5395,
  "total_unique_entities": 40782,
  "entities_per_article_avg": 12.5,
  "articles_per_entity_avg": 1.65,
  "top_entities": [
    {
      "entity_name": "Trump",
      "entity_type": "PERSON",
      "article_count": 234,
      "coverage_percentage": 4.3,
      "recent_articles": [...]
    }
  ]
}
```

#### Get Quality Trends
```bash
# NOT_APPLICABLE ratio over time
GET /api/v1/graph/analytics/not-applicable-trends?days=30

# Confidence distribution over time
GET /api/v1/graph/analytics/relationship-quality-trends?days=30
```

### Enrichment

#### Enrich Entity with Wikidata
```bash
POST /api/v1/graph/enrichment/wikidata
Authorization: Bearer <admin-jwt-token>

{
  "entity_name": "Tesla",
  "wikidata_id": "Q478214"
}

# Response
{
  "entity_name": "Tesla",
  "enrichment_status": "success",
  "data_added": {
    "description": "American electric vehicle manufacturer",
    "aliases": ["Tesla Motors", "Tesla Inc."],
    "founded": "2003",
    "headquarters": "Austin, Texas"
  }
}
```

### History

#### Get Enrichment History
```bash
GET /api/v1/graph/history/enrichments?limit=20

# Response
[
  {
    "entity_name": "Tesla",
    "enrichment_type": "wikidata",
    "timestamp": "2025-11-15T10:30:00Z",
    "data_added": {...}
  }
]
```

#### Get History Statistics
```bash
GET /api/v1/graph/history/stats

# Response
{
  "total_events": 1245,
  "event_counts_by_type": {
    "wikidata_enrichment": 450,
    "entity_merge": 120,
    "relationship_update": 675
  },
  "enrichment_sources": {
    "wikidata": 450,
    "manual": 95
  },
  "unique_users": 12,
  "query_time_ms": 3
}
```

### Quality

#### Get Disambiguation Quality
```bash
GET /api/v1/graph/quality/disambiguation?limit=10

# Response
{
  "total_ambiguous_names": 50,
  "total_disambiguation_cases": 192,
  "success_rate": 1.0,
  "well_disambiguated_count": 10,
  "top_ambiguous_entities": [
    {
      "name": "Russian",
      "type_variations": ["LOCATION", "MISC", "ORGANIZATION", "UNKNOWN", "PERSON"],
      "occurrence_count": 5,
      "variations_detail": [
        {
          "type": "LOCATION",
          "avg_confidence": 0.987,
          "relationship_count": 384
        }
      ]
    }
  ]
}
```

#### Get Graph Integrity Check
```bash
GET /api/v1/graph/quality/integrity

# Response
{
  "integrity_percentage": -15.16,
  "total_issues": 53200,
  "total_entities": 46197,
  "issues_by_type": {
    "orphaned_entities": {
      "count": 11090,
      "sample": ["Australian Competition...", "Kids", "Marshalsea"]
    },
    "weak_relationships": {
      "count": 0,
      "sample": []
    },
    "missing_wikidata_id": {
      "count": 42109,
      "sample": ["Bitcoin", "foreign minister", ...]
    }
  }
}
```

### Articles

#### Get Article Information
```bash
GET /api/v1/graph/articles/{article_id}/info

# Example
GET /api/v1/graph/articles/abc123-def456/info

# Response
{
  "article_id": "abc123-def456",
  "article_title": "Tesla Announces New Model",
  "article_url": "https://example.com/article",
  "total_entities": 15,
  "published_at": "2025-11-15T10:00:00Z"
}
```

#### Get Article Entities
```bash
GET /api/v1/graph/articles/{article_id}/entities?limit=20

# Response
{
  "article_id": "abc123-def456",
  "total_entities": 15,
  "entities": [
    {
      "name": "Tesla",
      "type": "ORGANIZATION",
      "confidence": 0.95,
      "relationship_type": "EXTRACTED_FROM"
    },
    {
      "name": "Elon Musk",
      "type": "PERSON",
      "confidence": 0.92,
      "relationship_type": "EXTRACTED_FROM"
    }
  ],
  "query_time_ms": 25
}
```

### Findings (Symbolic Intelligence)

#### Ingest Symbolic Findings
```bash
POST /api/v1/graph/findings

# Request Body
{
  "article_id": "abc123-def456",
  "findings": [
    {
      "type": "sentiment_shift",
      "entity": "Tesla",
      "confidence": 0.87,
      "evidence": "Stock price sentiment changed from negative to positive"
    },
    {
      "type": "anomaly_detected",
      "entity": "Elon Musk",
      "confidence": 0.92,
      "evidence": "Unusual mention frequency spike"
    }
  ]
}

# Response
{
  "status": "success",
  "findings_ingested": 2,
  "article_id": "abc123-def456"
}
```

### Admin

#### Execute Custom Cypher Query
```bash
POST /api/v1/graph/admin/query/cypher
Authorization: Bearer <admin-jwt-token>

# Request
{
  "cypher": "MATCH (n:Entity {name: $name}) RETURN n",
  "parameters": {
    "name": "Tesla"
  }
}

# Response
{
  "results": [...],
  "execution_time_ms": 12
}
```

#### Validate Cypher Query
```bash
POST /api/v1/graph/admin/query/validate
Authorization: Bearer <admin-jwt-token>

# Request
{
  "cypher": "MATCH (n:Entity) WHERE n.name = 'Tesla' RETURN n"
}

# Response
{
  "is_valid": true,
  "allowed": true,
  "warnings": [],
  "syntax_errors": []
}
```

#### Get Query Examples
```bash
GET /api/v1/graph/admin/query/examples
Authorization: Bearer <admin-jwt-token>

# Response
{
  "examples": [
    {
      "name": "Find top entities",
      "cypher": "MATCH (e:Entity) RETURN e.name, e.type ORDER BY e.connection_count DESC LIMIT 10",
      "description": "Get most connected entities"
    }
  ]
}
```

#### Get Allowed Cypher Clauses
```bash
GET /api/v1/graph/admin/query/clauses
Authorization: Bearer <admin-jwt-token>

# Response
{
  "allowed_clauses": ["MATCH", "WHERE", "RETURN", "ORDER BY", "LIMIT"],
  "forbidden_clauses": ["DELETE", "DETACH DELETE", "CREATE", "SET", "REMOVE"]
}
```

#### Analyze Entities for Enrichment
```bash
POST /api/v1/graph/admin/enrichment/analyze
Authorization: Bearer <admin-jwt-token>

# Request
{
  "entity_filter": {
    "type": "ORGANIZATION",
    "missing_wikidata": true
  },
  "limit": 100
}

# Response
{
  "total_candidates": 450,
  "enrichment_suggestions": [
    {
      "entity_name": "Tesla",
      "current_data": {...},
      "suggested_wikidata_id": "Q478214",
      "confidence": 0.95
    }
  ]
}
```

#### Apply Enrichment
```bash
POST /api/v1/graph/admin/enrichment/apply
Authorization: Bearer <admin-jwt-token>

# Request
{
  "entity_name": "Tesla",
  "wikidata_id": "Q478214",
  "enrichment_data": {
    "description": "American EV manufacturer",
    "founded": "2003"
  }
}

# Response
{
  "status": "success",
  "entity_updated": "Tesla",
  "fields_added": ["description", "founded"]
}
```

#### Execute Enrichment Tool
```bash
POST /api/v1/graph/admin/enrichment/execute-tool
Authorization: Bearer <admin-jwt-token>

# Request
{
  "tool": "wikidata_bulk_enrichment",
  "parameters": {
    "entity_type": "ORGANIZATION",
    "batch_size": 50
  }
}

# Response
{
  "job_id": "enrich-job-123",
  "status": "started",
  "estimated_entities": 450
}
```

#### Get Enrichment Statistics
```bash
GET /api/v1/graph/admin/enrichment/stats
Authorization: Bearer <admin-jwt-token>

# Response
{
  "total_entities": 46177,
  "enriched_entities": 4088,
  "enrichment_coverage": 0.089,
  "sources": {
    "wikidata": 4088,
    "manual": 250
  },
  "pending_enrichments": 120
}
```

## RabbitMQ Integration

The service listens for relationship events:

- `entity.relationship.created` - Create new relationship
- `entity.relationship.updated` - Update relationship confidence
- `entity.created` - Create new entity node
- `entity.enriched` - Update entity with enrichment data

### Publishing Relationship Event

```python
import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='events', exchange_type='topic', durable=True)

# Publish relationship event
event = {
    "event_type": "entity.relationship.created",
    "data": {
        "source_entity": "Elon Musk",
        "target_entity": "Tesla",
        "relationship_type": "WORKS_FOR",
        "confidence": 0.95,
        "evidence": {
            "article_id": "uuid-123",
            "mention_count": 5
        }
    }
}

channel.basic_publish(
    exchange='events',
    routing_key='entity.relationship.created',
    body=json.dumps(event)
)

connection.close()
```

## Neo4j Schema

### Node Types

#### Entity Node
```cypher
CREATE (e:Entity {
  name: "Tesla",
  type: "ORGANIZATION",
  wikidata_id: "Q478214",
  first_seen: datetime("2024-10-15T10:00:00Z"),
  last_seen: datetime("2025-01-15T14:30:00Z"),
  connection_count: 45,
  enrichment_data: {
    description: "American electric vehicle manufacturer",
    aliases: ["Tesla Motors", "Tesla Inc."]
  }
})
```

### Relationship Types

- **WORKS_FOR**: Person → Organization
- **FOUNDED**: Person → Organization
- **LOCATED_IN**: Organization → Location
- **MENTIONED_WITH**: Entity → Entity (co-occurrence)
- **ACQUIRED**: Organization → Organization
- **PARTNER_OF**: Organization → Organization

#### Relationship Properties
```cypher
CREATE (source)-[:WORKS_FOR {
  confidence: 0.95,
  mention_count: 234,
  first_seen: datetime(),
  last_seen: datetime(),
  evidence: ["article-uuid-1", "article-uuid-2"],
  quality_score: 0.92
}]->(target)
```

### Constraints and Indexes

```cypher
-- Uniqueness constraint
CREATE CONSTRAINT entity_name_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.name IS UNIQUE;

-- Indexes
CREATE INDEX entity_type_idx IF NOT EXISTS
FOR (e:Entity) ON (e.type);

CREATE INDEX entity_wikidata_idx IF NOT EXISTS
FOR (e:Entity) ON (e.wikidata_id);

CREATE INDEX relationship_confidence_idx IF NOT EXISTS
FOR ()-[r:WORKS_FOR]-() ON (r.confidence);
```

## Architecture

```
┌─────────────────┐
│  FastAPI API    │
│  (Port 8111)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────────┐
│Neo4j │  │ PostgreSQL│
│Graph │  │ (Metadata)│
└──────┘  └───────────┘
    │
┌───▼────────────┐
│RabbitMQ Consumer│
│(Relationships)  │
└─────────────────┘
```

## PostgreSQL Schema (Metadata)

### query_history
- `id` - Unique identifier
- `user_id` - User performing query
- `query_type` - Type of query (search, pathfinding, etc.)
- `parameters` - Query parameters (JSON)
- `execution_time_ms` - Query execution time
- `result_count` - Number of results
- `created_at` - Query timestamp

### popular_connections
- `source_entity` - Source entity name
- `target_entity` - Target entity name
- `relationship_type` - Type of relationship
- `query_count` - Number of times queried
- `last_queried_at` - Most recent query

## Performance Optimization

### Critical Performance Improvements (Week 4 Analysis)

**Current Status:** 5-6x performance improvement available through optimization

#### 1. Index Optimization (IMPLEMENT FIRST)

Current indexes: 2 / 7 recommended (29% coverage)

**Critical missing indexes:**
```cypher
-- 1. Entity type filtering (16x improvement)
CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type);

-- 2. Relationship confidence filtering (15x improvement)
CREATE INDEX relationship_confidence_idx IF NOT EXISTS FOR ()-[r]->() ON (r.confidence);

-- 3. Wikidata enrichment lookups (20x improvement)
CREATE INDEX entity_wikidata_idx IF NOT EXISTS FOR (e:Entity) ON (e.wikidata_id);

-- 4. Time-based analytics (10x improvement)
CREATE INDEX entity_last_seen_idx IF NOT EXISTS FOR (e:Entity) ON (e.last_seen);
```

**Impact:** 8-16x faster queries for type filtering and relationship filtering

#### 2. Query Optimization

**Problem:** Unfiltered relationship traversals
```cypher
-- SLOW: No type hints, evaluates all ~69K relationships
MATCH (source:Entity {name: $name})-[r]->(target:Entity)
WHERE r.confidence >= 0.5
RETURN target.name, type(r), r.confidence

-- FAST: Filter relationships early
MATCH (source:Entity {name: $name})-[r:WORKS_FOR|MENTIONED_WITH|LOCATED_IN]->(target:Entity)
WHERE r.confidence >= 0.5
RETURN target.name, type(r), r.confidence
```

**Impact:** 5-15x faster connection queries

**Files affected:**
- `/app/api/routes/graph.py` - Entity connections endpoint
- `/app/api/routes/analytics.py` - Top entities query
- `/app/services/search_service.py` - Entity search
- `/app/services/pathfinding_service.py` - Pathfinding queries

#### 3. Entity Canonicalization Improvements

**Issues identified:**
1. Case-sensitive entity names cause duplicates (5-10% entity count inflation)
2. Type conflicts for ambiguous entities (same name, different types)
3. Confidence scores unreliable (85% marked high-confidence)

**Solutions:**
1. Normalize entity names to title case on insert
2. Implement type reconciliation for duplicate entities
3. Refine confidence scoring based on evidence type

**Impact:** 10% data quality improvement, cleaner graph structure

#### 4. Schema Optimization

**Cardinality Analysis:**
- Total nodes: 46K+ entities
- Total relationships: 69K+
- Orphaned entities: 11K (24% of graph)
- High-degree nodes: ~800 connections (Trump, US, China)

**Recommendations:**
1. Remove orphaned entities (daily cleanup)
2. Pre-compute connection_count on entities
3. Use relationship type constraints to reduce traversal cost
4. Partition high-degree nodes by relationship type

**Impact:** 5-10% storage reduction, faster analytics

### Neo4j Configuration
```conf
# neo4j.conf
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G

# Performance tuning (for optimized queries)
dbms.cypher_compiler.cypher_planner=cost
```

### Cypher Query Optimization

**Use EXPLAIN to analyze query plans:**
```cypher
-- Analyze execution plan
EXPLAIN MATCH (e:Entity {name: $name})-[r]->(target)
WHERE r.confidence > 0.5
RETURN target;

-- Profile actual execution
PROFILE MATCH (e:Entity {name: $name})-[r]->(target)
WHERE r.confidence > 0.5
RETURN target;
```

**Best Practices:**
```cypher
-- 1. Filter relationships early with type hints
MATCH (e:Entity {name: $name})-[r:WORKS_FOR|MENTIONED_WITH]->(target)
WHERE r.confidence >= 0.5
RETURN target

-- 2. Use indexed properties in WHERE clauses
WHERE e.type = $type AND r.confidence >= 0.5

-- 3. Limit results early
ORDER BY r.confidence DESC
LIMIT 100

-- 4. Avoid expensive OPTIONAL MATCH without filters
-- SLOW:
OPTIONAL MATCH (e)-[r]->()
-- FAST:
OPTIONAL MATCH (e)-[r]->()
WHERE r.confidence >= 0.5
```

### Caching Strategy
- **Redis**: Cache frequently accessed entity connections (TTL: 1 hour)
- **Application-level**: Cache graph statistics and centrality scores (TTL: 30 min)
- **Query-level**: Pre-compute connection_count on Entity nodes

### Performance Targets

**Current state:**
- Entity lookup: ~50ms
- Connection query: ~400ms
- Type filtering: ~800ms
- Analytics: ~500ms

**Target state (after optimization):**
- Entity lookup: ~5ms (10x)
- Connection query: ~80ms (5x)
- Type filtering: ~50ms (16x)
- Analytics: ~100ms (5x)

**Roadmap:**
1. **Day 1:** Create critical indexes (30 min)
2. **Days 2-3:** Optimize queries (4 hours)
3. **Days 4-5:** Entity canonicalization (6 hours)
4. **Days 6+:** Schema optimization (ongoing)

See `/reports/performance/KNOWLEDGE_GRAPH_OPTIMIZATION_WEEK4.md` for complete analysis.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Test graph queries
pytest tests/test_graph.py -v

# Test pathfinding
pytest tests/test_pathfinding.py -v
```

## Monitoring

### Health Check
```bash
curl http://localhost:8111/health

# Response
{
  "status": "healthy",
  "neo4j": "connected",
  "postgres": "connected",
  "rabbitmq": "connected",
  "consumer": "running"
}
```

### Prometheus Metrics
- `kg_queries_total` - Total graph queries
- `kg_query_duration_seconds` - Query execution time
- `kg_graph_nodes_total` - Total nodes in graph
- `kg_graph_relationships_total` - Total relationships
- `kg_query_results_size` - Result size distribution

### Metrics Endpoint
```bash
curl http://localhost:8111/metrics
```

## Production Deployment

### Docker Build
```bash
docker build -t knowledge-graph-service:latest .
```

### Docker Run
```bash
docker run -d \
  --name knowledge-graph-service \
  -p 8111:8111 \
  -e NEO4J_URI=bolt://neo4j:7687 \
  -e NEO4J_USERNAME=neo4j \
  -e NEO4J_PASSWORD=password \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e RABBITMQ_URL=amqp://... \
  knowledge-graph-service:latest
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | Required |
| `NEO4J_USERNAME` | Neo4j username | neo4j |
| `NEO4J_PASSWORD` | Neo4j password | Required |
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `RABBITMQ_URL` | RabbitMQ connection URL | Required |
| `SERVICE_PORT` | API server port | 8111 |
| `LOG_LEVEL` | Logging level | INFO |
| `MAX_PATH_DEPTH` | Maximum pathfinding depth | 5 |

## Troubleshooting

### Neo4j Connection Issues
1. Verify Neo4j is running: `docker ps | grep neo4j`
2. Check connection URI format: `bolt://host:7687`
3. Verify credentials are correct
4. Check Neo4j logs: `docker logs kg-neo4j`

### Slow Graph Queries
1. Check if indexes exist: `SHOW INDEXES`
2. Analyze query plan: `EXPLAIN <query>`
3. Consider adding missing indexes
4. Review relationship cardinality
5. Increase Neo4j heap size if needed

### Missing Relationships
1. Check RabbitMQ consumer is running: `GET /health`
2. Verify relationship events in RabbitMQ UI
3. Check consumer logs for errors
4. Verify relationship confidence threshold (>= 0.5)

### High Memory Usage
1. Reduce Neo4j heap size
2. Limit query result sizes
3. Enable query pagination
4. Clear old query history
5. Monitor with Prometheus metrics

## Recent Changes

### 2025-11-17: Schema Validation Improvements

**Context:** Content-analysis-v2 Tier3 module schema conformity fixes

**Impact on Knowledge Graph Service:**
- ✅ **Improved data quality:** Financial findings now include correct `instruments` field
- ✅ **Reduced validation errors:** consistency_check findings no longer sent (meta-analysis only)
- ✅ **100% ingestion success rate:** All symbolic findings schema-compliant

**Schema Compliance:**
- All 7 symbolic schemas validated: EventTypeSymbolic, IHLConcernSymbolic, RegionalImpactSymbolic, FinancialImpactSymbolic, PoliticalDevelopmentSymbolic, SecurityThreatSymbolic, HumanitarianCrisisSymbolic
- Pydantic validation working correctly (extra fields ignored, required fields validated)
- No 422 validation errors after content-analysis-v2 fixes deployed

**Monitoring:**
```bash
# Monitor for validation errors (should be 0)
docker compose logs -f knowledge-graph-service | grep -i "422\|validation"

# Monitor successful ingestions
docker compose logs -f knowledge-graph-service | grep "200 OK"
```

**Related Documentation:**
- Content-analysis-v2 deployment report: `/tmp/deployment_completion_report.md`
- Schema gap analysis: `/tmp/tier3_graph_schema_gap_analysis.md`

### 2025-11-20: Retry Storm Incident - Cypher Syntax Error

**Severity:** CRITICAL (Incident #18 in POSTMORTEMS.md)

**What Happened:**
- Neo4j Cypher syntax error in `finance_intelligence_consumer.py` caused retry storm
- 2528+ messages stuck in retry loop for 15+ hours
- 32.6 GB network traffic upload, 27.2 GB download
- 257% CPU on RabbitMQ, massive traffic across Neo4j (25.6 GB) and Postgres (22.1 GB)

**Root Cause:**
`ON CREATE SET` clause placed AFTER `SET` block instead of directly after `MERGE`:

```cypher
# ❌ WRONG: ON CREATE SET after SET block
MERGE (n:Node {id: $id})
SET n.property = $value, n.updated_at = datetime()
ON CREATE SET n.created_at = datetime()  # Parser error!

# ✅ CORRECT: ON CREATE SET immediately after MERGE
MERGE (n:Node {id: $id})
ON CREATE SET n.created_at = datetime()
SET n.property = $value, n.updated_at = datetime()
```

**Fixed Locations:**
- Line 236: `_handle_company_update()` - Company node creation
- Line 282-290: `_handle_executives_update()` - Executive node + WORKS_FOR relationship
- Line 485: `_handle_insider_trade()` - Executive (insider) node creation
- Line 856: `_handle_regime_change()` - MarketRegime node creation

**Resolution:**
1. ✅ Purged 2528 stuck messages from `knowledge_graph_finance_intelligence` queue
2. ✅ Fixed all 5 Cypher syntax errors
3. ✅ Service restarted cleanly
4. ✅ Network traffic normalized (77.7 kB / 88 kB, down 99.8%)

**Prevention Measures Planned:**
1. **Cypher Query Validation:**
   - Add unit tests for all Cypher queries
   - Use Neo4j's `EXPLAIN` to validate syntax before execution
   - Pre-commit hook for Cypher syntax validation

2. **Dead Letter Queue (DLQ):**
   - Configure DLQ for all knowledge graph queues
   - Move failed messages to DLQ after 3 retry attempts

3. **Circuit Breaker Pattern:**
   - Stop processing after 10 consecutive failures
   - Exponential backoff for retries

4. **Error Monitoring:**
   - Prometheus metrics for Neo4j query errors
   - Alert on repeated CypherSyntaxError (threshold: 10 in 5 minutes)

**Full Details:** See [POSTMORTEMS.md - Incident #18](../../POSTMORTEMS.md#incident-18-knowledge-graph-service-retry-storm---neo4j-cypher-syntax-error-2025-11-20)

## Neo4j Cypher Best Practices

### MERGE + ON CREATE SET Pattern

**Critical Rule:** `ON CREATE SET` and `ON MATCH SET` must come **immediately after** `MERGE`, **before** any standalone `SET` clause.

**Correct Syntax:**
```cypher
MERGE (n:Node {id: $id})
ON CREATE SET n.created_at = datetime()      # 1. After MERGE
ON MATCH SET n.matched_at = datetime()       # 2. After MERGE
SET n.property = $value, n.updated_at = datetime()  # 3. Last
RETURN n
```

**Why This Matters:**
- Neo4j parser treats `ON CREATE SET` as a sub-clause of `MERGE`
- When placed after a standalone `SET`, parser sees it as invalid standalone statement
- Results in: `Invalid input 'ON': expected MERGE, MATCH, CREATE, etc.`

**Common Patterns:**

**1. Simple Node Creation:**
```cypher
MERGE (c:Company {symbol: $symbol})
ON CREATE SET c.created_at = datetime()
SET c.name = $name,
    c.sector = $sector,
    c.updated_at = datetime()
RETURN c
```

**2. Relationship Creation:**
```cypher
MERGE (e:Executive {name: $name})-[r:WORKS_FOR]->(c:Company {symbol: $symbol})
ON CREATE SET r.created_at = datetime(), r.initial_title = $title
ON MATCH SET r.last_verified = datetime()
SET r.title = $title,
    r.pay_usd = $pay_usd,
    r.updated_at = datetime()
RETURN r
```

**3. Conditional Properties:**
```cypher
MERGE (e:Entity {name: $name})
ON CREATE SET
    e.created_at = datetime(),
    e.confidence = $initial_confidence,
    e.first_seen = datetime()
ON MATCH SET
    e.match_count = coalesce(e.match_count, 0) + 1,
    e.last_seen = datetime()
SET
    e.type = $type,
    e.updated_at = datetime()
RETURN e
```

### Query Validation

**Before Deployment:**
```bash
# Test query syntax with EXPLAIN
echo "EXPLAIN MERGE (n:Node {id: 1}) ON CREATE SET n.created = datetime() SET n.updated = datetime()" | \
  docker exec -i neo4j cypher-shell -u neo4j -p password

# Run unit tests
pytest tests/test_cypher_queries.py -v
```

**Pre-commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit
grep -r "ON CREATE SET\|ON MATCH SET" services/knowledge-graph-service/app/ | \
  grep -v "MERGE.*ON CREATE" && echo "❌ Found ON CREATE SET not after MERGE" && exit 1
```

### Error Handling

**Circuit Breaker Pattern:**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=10, recovery_timeout=60)
async def execute_cypher_with_circuit_breaker(query: str, params: dict):
    """Execute Neo4j query with circuit breaker protection."""
    try:
        result = await neo4j_service.execute_write(query, params)
        return result
    except CypherSyntaxError as e:
        logger.error(f"Cypher syntax error: {e}")
        # Don't retry syntax errors - they'll never succeed
        raise
    except Exception as e:
        logger.error(f"Neo4j error: {e}")
        raise
```

**Dead Letter Queue:**
```python
# RabbitMQ consumer configuration
channel.queue_declare(
    queue='knowledge_graph_finance_intelligence',
    durable=True,
    arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'knowledge_graph_finance_intelligence.dlq',
        'x-message-ttl': 3600000,  # 1 hour
    }
)
```

### Post-Incident #18: Safety Features (2025-11-25)

The following safety features were implemented to prevent retry storms:

#### 1. Cypher Syntax Validation

All write queries are validated BEFORE execution to catch syntax errors early:

```python
# app/services/cypher_validator.py
from app.services.cypher_validator import validate_cypher_syntax, CypherSyntaxError

# Validates MERGE + ON CREATE SET pattern
result = validate_cypher_syntax("""
    MERGE (c:Company {symbol: $symbol})
    ON CREATE SET c.created_at = datetime()
    SET c.name = $name
""")

if not result.is_valid:
    print(f"Errors: {result.errors}")
    # Errors would include: "ON CREATE SET found AFTER standalone SET"
```

**Key validations:**
- MERGE + ON CREATE SET ordering (must come immediately after MERGE)
- ON MATCH SET ordering (before standalone SET)
- Balanced parentheses, brackets, braces
- Empty query detection

#### 2. Dead Letter Queue (DLQ)

Non-retriable errors are sent to DLQ instead of infinite requeue:

```python
# In consumers: relationships_consumer.py, finance_intelligence_consumer.py

# Non-retriable errors go to DLQ immediately
NON_RETRIABLE_ERRORS = (
    CypherSyntaxError,      # Syntax errors will always fail
    json.JSONDecodeError,   # Malformed messages
    KeyError,               # Missing required fields
    ValueError,             # Invalid data format
)

# Queue configuration with DLQ
self.queue = await self.channel.declare_queue(
    settings.RABBITMQ_QUEUE,
    durable=True,
    arguments={
        'x-dead-letter-exchange': f'{exchange_name}.dlx',
        'x-message-ttl': 86400000,  # 24 hours
    }
)
```

#### 3. Query Timeout Protection

All Neo4j queries have enforced timeouts:

```python
# app/services/neo4j_service.py
async def execute_write(self, query, parameters=None, timeout_seconds=None):
    # Default: settings.MAX_QUERY_TIMEOUT_SECONDS (30s)
    timeout = timeout_seconds or settings.MAX_QUERY_TIMEOUT_SECONDS

    # Execute with timeout
    return await asyncio.wait_for(_run_query(), timeout=timeout)
```

#### 4. Rate Limiting

API endpoints are rate-limited to prevent abuse:

```python
# app/core/rate_limiting.py
class RateLimits:
    DEFAULT = "100/minute"  # Standard read endpoints
    SEARCH = "60/minute"    # Search endpoints (heavier)
    WRITE = "30/minute"     # Write endpoints
    ADMIN = "10/minute"     # Admin endpoints (most restrictive)

# Usage in routes:
from app.core.rate_limiting import limiter, RateLimits

@router.post("/query/cypher")
@limiter.limit(RateLimits.ADMIN)
async def execute_custom_cypher_query(request: Request, ...):
    ...
```

#### 5. Standardized Error Handling

Consistent error format across all consumers:

```python
# app/core/errors.py
from app.core.errors import format_consumer_error, ErrorContext

try:
    await process_message(msg)
except Exception as e:
    err = format_consumer_error(
        error=e,
        context=ErrorContext(
            article_id=msg.article_id,
            event_type="finance.company.updated",
            symbol="AAPL"
        ),
        retriable=is_retriable_error(e)
    )
    err.log()
```

**Error log format:**
```json
{
    "error_type": "CypherSyntaxError",
    "message": "ON CREATE SET found AFTER standalone SET",
    "context": {
        "article_id": "12345",
        "event_type": "finance.company.updated",
        "symbol": "AAPL"
    },
    "retriable": false,
    "timestamp": "2025-11-25T10:30:00Z"
}
```

### Monitoring & Alerting

**Prometheus Metrics:**
```python
# Track Cypher errors
cypher_error_counter = Counter(
    'neo4j_cypher_errors_total',
    'Total Neo4j Cypher errors',
    ['error_type']
)

# Track query performance
cypher_query_duration = Histogram(
    'neo4j_query_duration_seconds',
    'Neo4j query duration',
    ['query_type']
)
```

**Alert Rules:**
```yaml
# prometheus/alerts.yml
- alert: HighCypherErrorRate
  expr: rate(neo4j_cypher_errors_total[5m]) > 10
  for: 5m
  annotations:
    summary: "High Neo4j Cypher error rate"
    description: "{{ $value }} errors/sec in last 5 minutes"

- alert: StuckRabbitMQQueue
  expr: rabbitmq_queue_messages{queue="knowledge_graph_finance_intelligence"} > 100
  for: 10m
  annotations:
    summary: "RabbitMQ queue stuck"
    description: "{{ $value }} messages stuck for 10+ minutes"
```

## License

MIT License

## Documentation

- [Service Documentation](../../docs/services/knowledge-graph-service.md)
- [API Documentation](../../docs/api/knowledge-graph-service-api.md)
- [Neo4j Best Practices](../../docs/guides/neo4j-best-practices.md)
- [Incident History](../../POSTMORTEMS.md)

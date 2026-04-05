# MCP Knowledge Graph Server

Model Context Protocol (MCP) server exposing Neo4j Knowledge Graph operations to Claude Desktop and other MCP clients.

## Overview

This server provides 17 high-value tools for querying and analyzing the Neo4j Knowledge Graph, including:
- Entity relationships and connections
- Graph analytics and statistics
- Article-entity relationships
- Market data integration
- Data quality monitoring

## Architecture

```
Claude Desktop (Windows)
    ↓ JSON-RPC 2.0
mcp-knowledge-graph-proxy.js (Node.js)
    ↓ HTTP REST
mcp-knowledge-graph-server (FastAPI - Port 9004)
    ↓ HTTP with Circuit Breaker
knowledge-graph-service (Port 8111)
    ↓
Neo4j Graph Database
```

## Phase 1 Tools (17 Total)

### Core Entity Operations (3)
1. **get_entity_connections** - Get all connections for an entity
2. **find_entity_path** - Find paths between two entities
3. **search_entities** - Search entities by name or properties

### Analytics (4)
4. **get_top_entities** - Get top entities by connections/mentions
5. **get_relationship_stats** - Relationship type statistics
6. **get_growth_history** - Graph growth over time
7. **get_cross_article_coverage** - Entity coverage across articles

### Article Integration (2)
8. **get_article_entities** - Entities extracted from article
9. **get_article_info** - Article node information

### Market Data (4)
10. **query_markets** - Search/filter market nodes
11. **get_market_details** - Full market node with connections
12. **get_market_history** - Historical price data
13. **get_market_stats** - Market overview statistics

### Quality Monitoring (2)
14. **get_quality_integrity** - Graph integrity check
15. **get_quality_disambiguation** - Disambiguation quality

### Statistics (2)
16. **get_graph_stats** - Basic graph statistics
17. **get_detailed_stats** - Comprehensive statistics

## Configuration

Environment variables (`.env`):
```bash
# Service
SERVICE_NAME=mcp-knowledge-graph-server
SERVICE_VERSION=1.0.0
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=9004

# Backend Services
KNOWLEDGE_GRAPH_URL=http://knowledge-graph-service:8111

# HTTP Client
HTTP_TIMEOUT=30
MAX_CONNECTIONS=100

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Redis Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=7  # DB 7 for knowledge-graph-server

# Cache TTLs (seconds)
CACHE_TTL_ENTITY=300      # 5 min
CACHE_TTL_STATS=60        # 1 min
CACHE_TTL_SEARCH=300      # 5 min
CACHE_TTL_ANALYTICS=600   # 10 min
CACHE_TTL_MARKET=60       # 1 min (volatile)
```

## API Endpoints

### MCP Protocol
- `GET /mcp/tools/list` - List all tools
- `POST /mcp/tools/execute` - Execute tool
- `GET /mcp/info` - Server information

### Health
- `GET /health` - Health check
- `GET /debug/circuit-breakers` - Circuit breaker status

## Usage Examples

### List Available Tools
```bash
curl http://localhost:9004/mcp/tools/list | jq '.[].name'
```

### Execute Tool
```bash
curl -X POST http://localhost:9004/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_entity_connections",
    "arguments": {
      "entity_name": "Bitcoin",
      "limit": 10
    }
  }'
```

### Get Server Info
```bash
curl http://localhost:9004/mcp/info
```

## Circuit Breaker Protection

All HTTP calls to knowledge-graph-service are protected by circuit breakers:
- **Failure Threshold:** 5 consecutive failures
- **Recovery Timeout:** 60 seconds
- **Success Threshold:** 2 successful requests to close

Monitor circuit breaker status:
```bash
curl http://localhost:9004/debug/circuit-breakers
```

## Caching Strategy

3-tier Redis caching (DB 7):
- **Entity Operations:** 5 minutes (semi-stable)
- **Statistics:** 1 minute (frequent changes)
- **Analytics:** 10 minutes (slower changing)
- **Market Data:** 1 minute (volatile)

## Development

### Start Container
```bash
docker compose up -d mcp-knowledge-graph-server
```

### View Logs
```bash
docker logs -f mcp-knowledge-graph-server
```

### Hot Reload
Code changes auto-reload via Uvicorn (volume mount in development).

## Integration with Claude Desktop

See `mcp-knowledge-graph-proxy.js` for Node.js JSON-RPC proxy configuration.

## Phase 2 Roadmap

Additional 15-20 tools planned:
- Cypher query execution
- Graph enrichment tools
- History queries
- Relationship quality trends
- Advanced analytics

---

**Port:** 9004
**Service:** knowledge-graph-service (Port 8111)
**Database:** Neo4j (via knowledge-graph-service)
**Cache:** Redis DB 7

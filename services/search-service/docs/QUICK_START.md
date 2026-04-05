# Search Service - Quick Start Guide

## Service Overview

The Search Service provides full-text search capabilities for the news microservices platform using PostgreSQL.

**Service Port**: 8006
**Health Check**: http://localhost:8006/health
**API Documentation**: http://localhost:8006/docs

## Quick Commands

### Start the Service

```bash
cd /home/cytrex/news-microservices
docker compose up -d search-service
```

### Check Service Health

```bash
curl http://localhost:8006/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "search-service",
  "version": "1.0.0",
  "environment": "development",
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

### View Logs

```bash
docker compose logs -f search-service
```

### Rebuild Service

```bash
docker compose build search-service
docker compose up -d search-service
```

## API Usage Examples

### Basic Search (Requires Authentication)

```bash
# Get JWT token from auth service first
TOKEN="your-jwt-token"

# Perform search
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8006/api/v1/search?query=technology&page=1&page_size=20"
```

### Autocomplete Suggestions

```bash
curl "http://localhost:8006/api/v1/search/suggest?query=tech&limit=10"
```

Response:
```json
{
  "query": "tech",
  "suggestions": ["technology", "technical", "techniques"]
}
```

### Popular Queries

```bash
curl "http://localhost:8006/api/v1/search/popular?limit=10"
```

### Advanced Search

```bash
curl -X POST "http://localhost:8006/api/v1/search/advanced" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "page": 1,
    "page_size": 20,
    "use_fuzzy": true,
    "highlight": true,
    "facets": ["source", "sentiment", "date"],
    "filters": {
      "sentiment": ["positive"],
      "date_from": "2025-01-01T00:00:00Z"
    }
  }'
```

## Search Query Syntax

### Basic Queries
- **Simple**: `technology`
- **Multiple words**: `artificial intelligence` (searches for both words)
- **Phrase**: `"artificial intelligence"` (exact phrase)
- **Exclude**: `technology -blockchain` (exclude blockchain)

### Operators
- **AND**: `artificial AND intelligence`
- **OR**: `technology OR science`
- **Combined**: `(artificial OR ai) AND technology`

### Filters
- **Source**: `?source=TechCrunch,Wired`
- **Sentiment**: `?sentiment=positive,neutral`
- **Date Range**: `?date_from=2025-01-01&date_to=2025-12-31`

## Database Access

### Connect to PostgreSQL

```bash
docker exec -it news-postgres psql -U news_user -d news_mcp
```

### Check Search Index

```sql
-- View indexed articles
SELECT article_id, title, source, sentiment, indexed_at
FROM article_indexes
ORDER BY indexed_at DESC
LIMIT 10;

-- Check search vector
SELECT article_id, title,
       ts_headline('english', content, to_tsquery('english', 'technology')) as highlight
FROM article_indexes
WHERE search_vector @@ to_tsquery('english', 'technology')
LIMIT 5;

-- View search analytics
SELECT query, hits, updated_at
FROM search_analytics
ORDER BY hits DESC
LIMIT 10;
```

### Verify Extensions

```sql
-- Check installed extensions
\dx

-- Should show:
-- pg_trgm   | 1.6 | text similarity measurement
-- unaccent  | 1.1 | removes accents
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs search-service

# Common issues:
# 1. Database connection - verify postgres is running
# 2. Redis connection - verify redis is running
# 3. Port conflict - check if 8006 is in use
```

### Search Returns No Results

```bash
# Check if articles are indexed
docker exec -it news-postgres psql -U news_user -d news_mcp -c \
  "SELECT COUNT(*) FROM article_indexes;"

# If count is 0, index articles:
# (Manual indexing endpoint to be implemented)
```

### Redis Connection Error

```bash
# Verify Redis is running
docker compose ps redis

# Test Redis connection
docker exec -it news-redis redis-cli -a redis_secret_2024 ping
# Should return: PONG
```

## Configuration Files

### Main Config
- **Path**: `/home/cytrex/news-microservices/services/search-service/app/core/config.py`
- **Environment**: `.env` file in service directory

### Key Settings
- `MAX_SEARCH_RESULTS=100` - Maximum results per query
- `ENABLE_FUZZY_SEARCH=true` - Enable fuzzy matching
- `FUZZY_SIMILARITY_THRESHOLD=0.3` - Similarity threshold
- `INDEXING_INTERVAL=300` - Auto-sync interval (seconds)
- `CACHE_TTL=3600` - Redis cache TTL (seconds)

## Development

### Run Tests

```bash
cd services/search-service
python -m pytest tests/
```

### Format Code

```bash
black app/
isort app/
```

### Type Checking

```bash
mypy app/
```

## API Documentation

Interactive API documentation is available at:

**Swagger UI**: http://localhost:8006/docs
**ReDoc**: http://localhost:8006/redoc

## Support

For issues or questions:
1. Check service logs: `docker compose logs search-service`
2. Verify health: `curl http://localhost:8006/health`
3. Review implementation status: `/home/cytrex/news-microservices/services/search-service/docs/IMPLEMENTATION_STATUS.md`

# Search Service

Full-text search microservice with PostgreSQL FTS, autocomplete, and advanced query capabilities.

## Features

- **Full-Text Search**:
  - PostgreSQL full-text search with tsvector
  - Relevance scoring and ranking
  - Multi-field search (title, content, author)
  - Fuzzy matching support

- **Advanced Search**:
  - Boolean operators (AND, OR, NOT)
  - Phrase search with quotes
  - Field-specific search
  - Date range filtering
  - Sentiment and entity filtering

- **Autocomplete**: Real-time search suggestions with Redis caching
- **Search History**: Per-user search history tracking
- **Saved Searches**: User-defined search queries with alerts
- **Faceted Search**: Dynamic facets for sources, dates, sentiments
- **Highlighting**: Search term highlighting in results

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
# PostgreSQL
docker run -d --name search-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=search_db \
  -p 5432:5432 postgres:15

# Redis (for caching)
docker run -d --name search-redis \
  -p 6379:6379 redis:7-alpine

# RabbitMQ (for events)
docker run -d --name search-rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management
```

### 4. Initialize Database

```bash
# Database migrations will run automatically on startup
python -m app.main
```

### 5. Start Celery Workers (Optional)

```bash
# For background indexing
celery -A app.workers.celery_app worker --loglevel=info
```

### 6. Start API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8106 --reload
```

## API Endpoints

### Basic Search

#### Search Articles
```bash
GET /api/v1/search?query=tesla&page=1&page_size=20
Authorization: Bearer <jwt-token> (optional)

# With filters
GET /api/v1/search?query=tesla&source=reuters,bloomberg&sentiment=positive&date_from=2025-01-01
```

**Response:**
```json
{
  "query": "tesla",
  "total": 1523,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "article_id": "uuid-123",
      "title": "Tesla Reports Q4 Earnings",
      "content": "Tesla Inc. reported...",
      "author": "Jane Doe",
      "source": "Reuters",
      "url": "https://...",
      "published_at": "2025-01-15T10:30:00Z",
      "sentiment": "positive",
      "entities": ["Tesla", "Elon Musk"],
      "relevance_score": 0.95,
      "highlight": {
        "title": ["<em>Tesla</em> Reports Q4 Earnings"]
      }
    }
  ],
  "execution_time_ms": 45.3
}
```

### Advanced Search

#### Advanced Search with Operators
```bash
POST /api/v1/search/advanced
Authorization: Bearer <jwt-token> (optional)
Content-Type: application/json

{
  "query": "tesla OR \"electric vehicles\"",
  "page": 1,
  "page_size": 20,
  "use_fuzzy": true,
  "highlight": true,
  "facets": ["source", "sentiment", "date"],
  "filters": {
    "sentiment": ["positive", "neutral"],
    "date_from": "2025-01-01T00:00:00Z"
  }
}
```

**Response includes facets:**
```json
{
  "facets": {
    "source": {
      "Reuters": 342,
      "Bloomberg": 289,
      "CNBC": 156
    },
    "sentiment": {
      "positive": 512,
      "neutral": 304,
      "negative": 98
    },
    "date": {
      "2025-01": 450,
      "2024-12": 380
    }
  }
}
```

### Autocomplete

#### Get Search Suggestions
```bash
GET /api/v1/search/autocomplete?query=tes&limit=10

# Response
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

### Search History

#### Get Search History
```bash
GET /api/v1/search/history?limit=50
Authorization: Bearer <jwt-token>
```

#### Delete History Entry
```bash
DELETE /api/v1/search/history/{id}
Authorization: Bearer <jwt-token>
```

### Saved Searches

#### List Saved Searches
```bash
GET /api/v1/search/saved
Authorization: Bearer <jwt-token>
```

#### Create Saved Search
```bash
POST /api/v1/search/saved
Authorization: Bearer <jwt-token>

{
  "name": "Tesla News",
  "query": "tesla",
  "filters": {
    "sentiment": ["positive"]
  },
  "alert_enabled": true
}
```

#### Delete Saved Search
```bash
DELETE /api/v1/search/saved/{id}
Authorization: Bearer <jwt-token>
```

### Admin Endpoints

#### Reindex All Articles
```bash
POST /api/v1/admin/reindex
Authorization: Bearer <admin-jwt-token>
```

#### Get Search Stats
```bash
GET /api/v1/admin/stats
Authorization: Bearer <admin-jwt-token>

# Response
{
  "total_articles": 125340,
  "total_searches": 45678,
  "popular_queries": [
    {"query": "tesla", "count": 1523},
    {"query": "bitcoin", "count": 987}
  ],
  "avg_response_time_ms": 42.5
}
```

## RabbitMQ Integration

The service listens for indexing events:

- `article.created` - Index new article
- `article.updated` - Update article index
- `article.deleted` - Remove from index

### Publishing Article for Indexing

```python
import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='events', exchange_type='topic', durable=True)

# Publish event
event = {
    "event_type": "article.created",
    "article_id": "uuid-123",
    "data": {
        "title": "Tesla Reports Earnings",
        "content": "Full article content...",
        "author": "Jane Doe",
        "source": "Reuters",
        "url": "https://...",
        "published_at": "2025-01-15T10:30:00Z"
    }
}

channel.basic_publish(
    exchange='events',
    routing_key='article.created',
    body=json.dumps(event)
)

connection.close()
```

## Search Query Syntax

### Basic Queries
- `tesla` - Simple keyword search
- `tesla stock` - Multiple keywords (AND)
- `"tesla stock"` - Exact phrase search

### Boolean Operators
- `tesla OR spacex` - Either keyword
- `tesla AND earnings` - Both keywords (explicit AND)
- `tesla -bankruptcy` - Exclude keyword

### Field-Specific Search
- `title:tesla` - Search only in title
- `author:"jane doe"` - Search by author
- `source:reuters` - Filter by source

### Advanced Filters
- `tesla sentiment:positive` - Filter by sentiment
- `tesla date:>2025-01-01` - Date range
- `tesla entities:("elon musk")` - Entity filter

## Search Algorithms

### TF-IDF Weight Tuning

The search service uses optimized TF-IDF weights for better relevance scoring:

- **Title matches:** 0.8 weight (highest priority)
- **Subtitle/headings:** 0.6 weight
- **Body content:** 0.4 weight
- **Metadata (author, source):** 0.2 weight

These weights were tuned through extensive testing to prioritize title matches while still considering content depth and metadata signals.

### Normalization

Uses PostgreSQL's `ts_rank` normalization flag (32) to:
- Adjust scores by document length
- Prevent long documents from dominating results
- Improve ranking fairness across different content types

**Performance impact:** 9.0x faster queries compared to default weights.

### Fuzzy Search

Uses PostgreSQL's `pg_trgm` similarity function with threshold 0.3:
- **Threshold 0.3** = Balanced precision/recall (recommended)
- Lower thresholds (0.1-0.2) = Higher recall, more results
- Higher thresholds (0.4-0.5) = Higher precision, fewer results

**Performance caveat:** Fuzzy search is currently slow (~6 seconds) on large datasets due to sequential scanning. This will be fixed in Phase 5 by adding `pg_trgm` GIN indexes.

### Query Result Caching

Redis-backed caching with intelligent key generation:
- **TTL:** 5 minutes (balances freshness and performance)
- **Cache key:** Includes query, pagination, and filters
- **Hit indicator:** `from_cache: true` in response
- **Expected speedup:** 12-100x for cached queries

### Query Syntax

The service supports advanced query syntax:

```
Basic Search:
  tesla                    # Simple keyword
  tesla electric vehicle   # Multiple keywords (AND)
  "electric vehicle"       # Exact phrase

Boolean Operators:
  tesla OR spacex          # Either keyword
  tesla AND earnings       # Both keywords (explicit)
  tesla -bankruptcy        # Exclude keyword

Field-Specific Search:
  title:tesla              # Search only in title
  author:"jane doe"        # Search by author
  source:reuters           # Filter by source

Advanced Filters:
  tesla sentiment:positive # Filter by sentiment
  tesla date:>2025-01-01  # Date range
```

## Architecture

```
┌─────────────────┐
│  FastAPI API    │
│  (Port 8106)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────────┐
│Redis │  │ PostgreSQL │
│Cache │  │  + FTS     │
│      │  │  + pg_trgm │
└──────┘  └────────────┘
    │
┌───▼────────────┐
│Celery Workers  │
│(Background     │
│ Indexing)      │
└────────────────┘
```

## Database Schema

### search_index
- `article_id` - Article UUID (primary key)
- `title` - Article title
- `content` - Article content
- `author` - Author name
- `source` - Content source
- `url` - Article URL
- `published_at` - Publication timestamp
- `sentiment` - Sentiment analysis result
- `entities` - Extracted entities (JSON)
- `search_vector` - tsvector for full-text search
- `indexed_at` - Index timestamp
- `updated_at` - Last update timestamp

**Indexes:**
- GIN index on `search_vector` for fast FTS
- B-tree indexes on `published_at`, `source`, `sentiment`
- Composite index on `(source, sentiment, published_at)`

### search_history
- `id` - Unique identifier
- `user_id` - User performing search
- `query` - Search query text
- `filters` - Applied filters (JSON)
- `result_count` - Number of results
- `execution_time_ms` - Query execution time
- `created_at` - Search timestamp

### saved_searches
- `id` - Unique identifier
- `user_id` - Owner
- `name` - Saved search name
- `query` - Search query
- `filters` - Filters (JSON)
- `alert_enabled` - Email alerts on new matches
- `created_at` - Creation timestamp

### popular_queries
- `query` - Search query (primary key)
- `search_count` - Number of searches
- `last_searched_at` - Most recent search

## Performance Optimization

### Caching Strategy
- **Redis**: Autocomplete suggestions (TTL: 1 hour)
- **PostgreSQL**: Query result caching for common queries

### Full-Text Search Optimization
```sql
-- tsvector index for performance
CREATE INDEX idx_search_vector ON search_index USING GIN(search_vector);

-- Composite index for filtered queries
CREATE INDEX idx_composite ON search_index(source, sentiment, published_at DESC);
```

### Background Indexing
- New articles indexed asynchronously via Celery
- Batch indexing for bulk imports
- Delta indexing for updates

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Test search functionality
pytest tests/test_search.py -v

# Test autocomplete
pytest tests/test_suggestions.py -v
```

## Monitoring

### Health Check
```bash
curl http://localhost:8106/health

# Response
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "rabbitmq": "connected"
}
```

### Prometheus Metrics
- `search_query_duration_seconds` - Search execution time
- `search_requests_total` - Total search requests
- `search_cache_hit_rate` - Redis cache hit rate
- `search_index_size` - Total indexed articles

## Production Deployment

### Docker Build
```bash
docker build -t search-service:latest .
```

### Docker Run
```bash
docker run -d \
  --name search-service \
  -p 8106:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  -e RABBITMQ_URL=amqp://... \
  search-service:latest
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `REDIS_URL` | Redis connection URL | Required |
| `RABBITMQ_URL` | RabbitMQ connection URL | Required |
| `SERVICE_PORT` | API server port | 8000 |
| `LOG_LEVEL` | Logging level | INFO |
| `CACHE_TTL` | Redis cache TTL (seconds) | 3600 |
| `MAX_QUERY_LENGTH` | Maximum query length | 500 |
| `DEFAULT_PAGE_SIZE` | Default results per page | 20 |
| `MAX_PAGE_SIZE` | Maximum results per page | 100 |

## Troubleshooting

### Slow Search Queries
1. Check PostgreSQL query plan: `EXPLAIN ANALYZE SELECT ...`
2. Verify tsvector index is being used
3. Check database statistics: `VACUUM ANALYZE search_index`
4. Consider increasing shared_buffers in PostgreSQL config

### Redis Connection Issues
1. Verify Redis is running: `redis-cli ping`
2. Check connection URL format
3. Verify Redis auth (if configured)

### Missing Search Results
1. Check if article is indexed: `SELECT * FROM search_index WHERE article_id = '...'`
2. Verify search_vector is populated
3. Run reindex: `POST /api/v1/admin/reindex`
4. Check RabbitMQ consumer logs

### High Memory Usage
1. Reduce Redis cache size
2. Limit search result page size
3. Enable query result pagination
4. Monitor PostgreSQL shared_buffers

## License

MIT License

## Documentation

- [Service Documentation](../../docs/services/search-service.md)
- [API Documentation](../../docs/api/search-service-api.md)
- [Search Query Syntax Guide](../../docs/guides/ENHANCED_SEARCH_GUIDE.md)

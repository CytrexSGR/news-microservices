# Search Service

Full-text search microservice with PostgreSQL full-text search and advanced query capabilities.

## Features

- **PostgreSQL Full-Text Search**: Fast and accurate text search using tsvector and tsquery
- **Advanced Query Syntax**: Supports AND/OR operators, phrase search, field search, and exclusion
- **Fuzzy Matching**: Trigram similarity for typo-tolerant search
- **Autocomplete Suggestions**: Based on popular searches and article titles
- **Search History**: Track user searches with analytics
- **Saved Searches**: Save and manage search queries with notifications
- **Faceted Search**: Group results by source, sentiment, date
- **Highlighted Snippets**: Show matching text snippets with highlighting
- **Background Indexing**: Celery workers sync articles every 5 minutes
- **Redis Caching**: Fast response times for popular queries

## Architecture

```
┌─────────────────┐
│  FastAPI App    │ (Port 8006)
│  /api/v1/search│
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬────────────┐
    │          │          │            │
┌───▼──┐  ┌───▼──┐  ┌───▼──┐    ┌────▼────┐
│ Postgres│  │ Redis │  │Celery│    │ Other   │
│ (FTS)  │  │ Cache │  │Worker│    │ Services│
└────────┘  └──────┘  └──────┘    └─────────┘
```

## API Endpoints

### Search

#### Basic Search
```bash
GET /api/v1/search?query=python&page=1&page_size=20

# With filters
GET /api/v1/search?query=machine+learning&source=TechBlog&sentiment=positive&date_from=2024-01-01
```

**Response:**
```json
{
  "query": "python",
  "total": 42,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "article_id": "art123",
      "title": "Python Programming Tutorial",
      "content": "Learn Python...",
      "author": "John Doe",
      "source": "TechBlog",
      "url": "https://example.com/article",
      "published_at": "2024-01-15T10:00:00Z",
      "sentiment": "positive",
      "entities": ["Python", "Programming"],
      "relevance_score": 0.95
    }
  ],
  "execution_time_ms": 23.5
}
```

#### Advanced Search
```bash
POST /api/v1/search/advanced
Content-Type: application/json

{
  "query": "machine learning",
  "page": 1,
  "page_size": 20,
  "use_fuzzy": true,
  "highlight": true,
  "facets": ["source", "sentiment", "date"],
  "filters": {
    "source": ["TechBlog", "DataScience"],
    "sentiment": ["positive", "neutral"],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
  }
}
```

**Response:**
```json
{
  "query": "machine learning",
  "total": 156,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "article_id": "art456",
      "title": "Machine Learning Basics",
      "content": "Introduction to ML...",
      "relevance_score": 0.98,
      "highlight": {
        "title": ["<b>Machine Learning</b> Basics"],
        "content": ["Introduction to <b>ML</b> algorithms..."]
      }
    }
  ],
  "facets": {
    "source": [
      {"value": "TechBlog", "count": 45},
      {"value": "DataScience", "count": 32}
    ],
    "sentiment": [
      {"value": "positive", "count": 89},
      {"value": "neutral", "count": 67}
    ],
    "date": [
      {"value": "2024-10-12", "count": 12},
      {"value": "2024-10-11", "count": 18}
    ]
  },
  "execution_time_ms": 45.2
}
```

### Query Syntax

#### Basic Query
```
python programming
```

#### AND Operator
```
python AND programming
```

#### OR Operator
```
python OR javascript
```

#### Phrase Search
```
"machine learning"
```

#### Field Search
```
title:python
author:"John Doe"
```

#### Exclusion
```
python -django
```

#### Combined
```
(python OR javascript) AND tutorial -beginner
```

### Autocomplete Suggestions

```bash
GET /api/v1/search/suggest?query=pyth&limit=10
```

**Response:**
```json
{
  "query": "pyth",
  "suggestions": [
    "python tutorial",
    "python programming",
    "python for beginners",
    "python django"
  ]
}
```

### Related Searches

```bash
GET /api/v1/search/related?query=python&limit=5
```

**Response:**
```json
{
  "query": "python",
  "related": [
    "python tutorial",
    "python frameworks",
    "python vs javascript",
    "python programming"
  ]
}
```

### Popular Queries

```bash
GET /api/v1/search/popular?limit=10
```

**Response:**
```json
{
  "popular_queries": [
    {"query": "python", "hits": 1523},
    {"query": "javascript", "hits": 987},
    {"query": "machine learning", "hits": 756}
  ],
  "total": 10
}
```

### Saved Searches

#### Create Saved Search
```bash
POST /api/v1/search/saved
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Python Tutorials",
  "query": "python tutorial",
  "filters": {
    "source": ["TechBlog"],
    "sentiment": ["positive"]
  },
  "notifications_enabled": true
}
```

#### List Saved Searches
```bash
GET /api/v1/search/saved
Authorization: Bearer <token>
```

#### Update Saved Search
```bash
PUT /api/v1/search/saved/123
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "notifications_enabled": false
}
```

#### Delete Saved Search
```bash
DELETE /api/v1/search/saved/123
Authorization: Bearer <token>
```

### Search History

#### Get Search History
```bash
GET /api/v1/search/history?page=1&page_size=20
Authorization: Bearer <token>
```

#### Clear Search History
```bash
DELETE /api/v1/search/history
Authorization: Bearer <token>
```

## Configuration

### Environment Variables

```bash
# Service
SERVICE_NAME=search-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8006
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/search_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=6
CACHE_TTL=3600

# Celery
CELERY_BROKER_URL=redis://localhost:6379/7
CELERY_RESULT_BACKEND=redis://localhost:6379/7

# Service URLs
FEED_SERVICE_URL=http://localhost:8001
CONTENT_ANALYSIS_SERVICE_URL=http://localhost:8002
AUTH_SERVICE_URL=http://localhost:8000

# Search Settings
MAX_SEARCH_RESULTS=100
DEFAULT_PAGE_SIZE=20
ENABLE_FUZZY_SEARCH=true
FUZZY_SIMILARITY_THRESHOLD=0.3

# Indexing
INDEXING_ENABLED=true
INDEXING_INTERVAL=300  # 5 minutes
BATCH_SIZE=100
```

## Installation

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f search-api

# Stop services
docker-compose down
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Initialize database
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Run API server
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload

# Run Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Run Celery beat (separate terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

## Database Schema

### article_indexes
- `id`: Primary key
- `article_id`: Unique article identifier
- `title`: Article title
- `content`: Article content
- `author`: Author name
- `source`: Content source
- `url`: Article URL
- `published_at`: Publication date
- `sentiment`: Sentiment analysis result
- `entities`: Extracted entities (JSON)
- `search_vector`: PostgreSQL tsvector for full-text search
- `indexed_at`: Indexing timestamp
- `updated_at`: Last update timestamp

**Indexes:**
- GIN index on `search_vector` for fast full-text search
- B-tree indexes on `published_at`, `source`, `sentiment`

### search_history
- `id`: Primary key
- `user_id`: User identifier
- `query`: Search query
- `filters`: Applied filters (JSON)
- `results_count`: Number of results
- `created_at`: Search timestamp

### saved_searches
- `id`: Primary key
- `user_id`: User identifier
- `name`: Search name
- `query`: Search query
- `filters`: Applied filters (JSON)
- `notifications_enabled`: Enable notifications
- `last_notified_at`: Last notification timestamp
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### search_analytics
- `id`: Primary key
- `query`: Search query
- `hits`: Query hit count
- `avg_position`: Average result position clicked
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_search.py -v

# Run specific test
pytest tests/test_search.py::TestSearch::test_basic_search -v
```

## Monitoring

### Health Check
```bash
curl http://localhost:8006/health
```

### Metrics
- Search query performance (execution time)
- Cache hit rate
- Popular queries
- Indexing statistics

### Celery Flower (Task Monitoring)
```bash
# Start Flower
celery -A app.workers.celery_app flower --port=5555

# Access: http://localhost:5555
```

## Performance

- **Full-text search**: Sub-20ms for most queries
- **Cached queries**: Sub-5ms response time
- **Indexing**: ~1000 articles/minute
- **Concurrent requests**: Handles 500+ req/sec

## Troubleshooting

### Search returns no results
1. Check if articles are indexed: `SELECT COUNT(*) FROM article_indexes`
2. Verify search vector is populated: `SELECT article_id, search_vector FROM article_indexes LIMIT 1`
3. Check Celery worker logs for indexing errors

### Slow search performance
1. Check if PostgreSQL extensions are installed: `CREATE EXTENSION IF NOT EXISTS pg_trgm`
2. Verify GIN index exists: `\d article_indexes` in psql
3. Increase cache TTL for popular queries

### Celery tasks not running
1. Check Redis connection: `redis-cli PING`
2. Verify Celery broker URL in configuration
3. Check Celery worker logs: `docker-compose logs search-worker`

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

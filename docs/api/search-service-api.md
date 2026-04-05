# Search Service API

**Version:** 1.0.0
**Base URL:** `http://localhost:8106/api/v1`
**OpenAPI Docs:** `http://localhost:8106/docs`

---

## Authentication

Most endpoints support **optional authentication** via JWT tokens:

```http
Authorization: Bearer <jwt_token>
```

- **Optional endpoints:** Return public results without auth, personalized with auth
- **Required endpoints:** Return 403 Forbidden without valid token

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check service health and configuration.

**Authentication:** None

**Response:**
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

---

### 2. Basic Search

**GET** `/api/v1/search`

Perform basic full-text search with filters.

**Authentication:** Optional (enables history tracking)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query (1-500 chars) |
| `page` | integer | No | Page number (default: 1, min: 1) |
| `page_size` | integer | No | Results per page (default: 20, max: 100) |
| `source` | string | No | Filter by source (comma-separated) |
| `sentiment` | string | No | Filter by sentiment (positive, negative, neutral) |
| `date_from` | string | No | Filter by date from (ISO 8601) |
| `date_to` | string | No | Filter by date to (ISO 8601) |

**Example Request:**
```http
GET /api/v1/search?query=python&page=1&page_size=20&source=TechBlog&sentiment=positive
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
      "content": "Learn Python programming basics...",
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

**Query Syntax:**

| Syntax | Example | Description |
|--------|---------|-------------|
| Basic | `python programming` | Words with AND logic |
| AND | `python AND tutorial` | Explicit AND operator |
| OR | `python OR javascript` | Either term |
| Phrase | `"machine learning"` | Exact phrase |
| Exclusion | `python -django` | Exclude term |
| Combined | `(python OR javascript) AND tutorial -beginner` | Complex query |

---

### 3. Advanced Search

**POST** `/api/v1/search/advanced`

Advanced search with fuzzy matching, highlighting, and facets.

**Authentication:** Optional

**Request Body:**
```json
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
    "date_to": "2024-12-31",
    "entities": ["AI", "Machine Learning"]
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
      "content": "Introduction to ML algorithms...",
      "relevance_score": 0.98,
      "highlight": {
        "title": ["<b>Machine Learning</b> Basics"],
        "content": ["Introduction to <b>ML</b> algorithms and <b>machine learning</b> concepts..."]
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

---

### 4. Autocomplete Suggestions

**GET** `/api/v1/search/suggest`

Get autocomplete suggestions based on popular searches and article titles.

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Partial query (1-100 chars) |
| `limit` | integer | No | Max suggestions (default: 10, max: 20) |

**Example Request:**
```http
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
    "python django",
    "python machine learning"
  ]
}
```

---

### 5. Related Searches

**GET** `/api/v1/search/related`

Get related search queries based on similarity.

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Current query (1-500 chars) |
| `limit` | integer | No | Max related queries (default: 5, max: 20) |

**Example Request:**
```http
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

---

### 6. Popular Queries

**GET** `/api/v1/search/popular`

Get most popular search queries by hit count.

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Max queries (default: 10, max: 50) |

**Example Request:**
```http
GET /api/v1/search/popular?limit=10
```

**Response:**
```json
{
  "popular_queries": [
    {"query": "python", "hits": 1523},
    {"query": "javascript", "hits": 987},
    {"query": "machine learning", "hits": 756},
    {"query": "docker", "hits": 543}
  ],
  "total": 10
}
```

---

## Authenticated Endpoints

### 7. Get Search History

**GET** `/api/v1/search/history`

Get user's search history.

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Results per page (default: 20, max: 100) |

**Response:**
```json
{
  "history": [
    {
      "id": 123,
      "query": "python tutorial",
      "filters": {
        "source": ["TechBlog"],
        "sentiment": ["positive"]
      },
      "results_count": 42,
      "created_at": "2024-10-12T14:30:00Z"
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20
}
```

---

### 8. Delete History Item

**DELETE** `/api/v1/search/history/{id}`

Delete specific search history item.

**Authentication:** Required

**Response:**
```json
{
  "message": "History item deleted",
  "id": 123
}
```

---

### 9. List Saved Searches

**GET** `/api/v1/search/saved`

Get user's saved searches.

**Authentication:** Required

**Response:**
```json
{
  "saved_searches": [
    {
      "id": 456,
      "name": "Python Tutorials",
      "query": "python tutorial",
      "filters": {
        "source": ["TechBlog"],
        "sentiment": ["positive"]
      },
      "notifications_enabled": true,
      "last_notified_at": "2024-10-11T12:00:00Z",
      "created_at": "2024-10-01T10:00:00Z",
      "updated_at": "2024-10-11T12:00:00Z"
    }
  ],
  "total": 5
}
```

---

### 10. Create Saved Search

**POST** `/api/v1/search/saved`

Save a search query with notifications.

**Authentication:** Required

**Request Body:**
```json
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

**Response:**
```json
{
  "id": 456,
  "name": "Python Tutorials",
  "query": "python tutorial",
  "filters": {
    "source": ["TechBlog"],
    "sentiment": ["positive"]
  },
  "notifications_enabled": true,
  "created_at": "2024-10-12T15:00:00Z"
}
```

---

### 11. Get Saved Search

**GET** `/api/v1/search/saved/{id}`

Get specific saved search.

**Authentication:** Required

**Response:**
```json
{
  "id": 456,
  "name": "Python Tutorials",
  "query": "python tutorial",
  "filters": {
    "source": ["TechBlog"],
    "sentiment": ["positive"]
  },
  "notifications_enabled": true,
  "last_notified_at": "2024-10-11T12:00:00Z",
  "created_at": "2024-10-01T10:00:00Z",
  "updated_at": "2024-10-11T12:00:00Z"
}
```

---

### 12. Update Saved Search

**PUT** `/api/v1/search/saved/{id}`

Update saved search.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "Updated Name",
  "notifications_enabled": false
}
```

**Response:**
```json
{
  "id": 456,
  "name": "Updated Name",
  "query": "python tutorial",
  "notifications_enabled": false,
  "updated_at": "2024-10-12T15:30:00Z"
}
```

---

### 13. Delete Saved Search

**DELETE** `/api/v1/search/saved/{id}`

Delete saved search.

**Authentication:** Required

**Response:**
```json
{
  "message": "Saved search deleted",
  "id": 456
}
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid query parameter: query must be between 1 and 500 characters"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Authentication required"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Saved search with id 456 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred. Please try again later."
}
```

---

## Rate Limiting

**Not currently implemented.** Future versions will include:
- 100 requests/minute for unauthenticated users
- 1000 requests/minute for authenticated users

---

## Caching

Search results are cached in Redis:
- **Cache TTL:** 1 hour (configurable via `CACHE_TTL`)
- **Cache Key:** Based on query, filters, page, page_size
- **Cache Invalidation:** Automatic on article updates

---

## Performance Tips

1. **Use pagination:** Limit results to 20-50 per page
2. **Enable caching:** Popular queries cached for 1 hour
3. **Use filters:** Narrow results with source/sentiment filters
4. **Avoid wildcard searches:** Specific queries perform better
5. **Use fuzzy search sparingly:** Adds overhead (~2x slower)

---

## Examples

### cURL Examples

```bash
# Basic search
curl "http://localhost:8106/api/v1/search?query=python&page=1&page_size=20"

# With authentication
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8106/api/v1/search?query=python"

# Advanced search with filters
curl -X POST "http://localhost:8106/api/v1/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "use_fuzzy": true,
    "highlight": true,
    "facets": ["source", "sentiment"],
    "filters": {
      "source": ["TechBlog"],
      "sentiment": ["positive"]
    }
  }'

# Autocomplete
curl "http://localhost:8106/api/v1/search/suggest?query=pyth&limit=5"

# Popular queries
curl "http://localhost:8106/api/v1/search/popular?limit=10"
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8106/api/v1"

# Basic search
response = requests.get(f"{BASE_URL}/search", params={
    "query": "python",
    "page": 1,
    "page_size": 20,
    "source": "TechBlog",
    "sentiment": "positive"
})
results = response.json()

# Advanced search
response = requests.post(f"{BASE_URL}/search/advanced", json={
    "query": "machine learning",
    "use_fuzzy": True,
    "highlight": True,
    "facets": ["source", "sentiment"],
    "filters": {
        "source": ["TechBlog"],
        "sentiment": ["positive"]
    }
})
results = response.json()

# Authenticated request
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/search/history", headers=headers)
history = response.json()
```

---

## OpenAPI Specification

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8106/docs
- **ReDoc:** http://localhost:8106/redoc
- **OpenAPI JSON:** http://localhost:8106/openapi.json

---

**Last Updated:** 2025-11-02
**Maintainer:** Andreas

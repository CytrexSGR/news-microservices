# Intelligence Service API Documentation

Base URL: `http://localhost:8118/api/v1/intelligence`

## Overview

The Intelligence Service provides event clustering, risk scoring, and entity detection capabilities for news intelligence analysis.

---

## Endpoints

### Dashboard & Overview

#### GET `/overview`

Returns dashboard overview with top clusters and risk metrics.

**Response:**
```json
{
  "global_risk_index": 45.2,
  "top_clusters": [
    {
      "cluster_id": "uuid",
      "title": "US Election Updates",
      "risk_score": 72.5,
      "event_count": 15,
      "category": "geo"
    }
  ],
  "geo_risk": 48.3,
  "finance_risk": 42.1,
  "top_regions": ["United States", "Europe", "China"],
  "total_clusters": 127,
  "total_events": 1543,
  "timestamp": "2024-12-28T10:00:00Z"
}
```

---

#### GET `/subcategories`

Returns dynamic subcategories per main category.

**Response:**
```json
{
  "geo": ["United States", "Middle East"],
  "finance": ["Banking", "Crypto"],
  "tech": ["AI", "Cybersecurity"],
  "timestamp": "2024-12-28T10:00:00Z"
}
```

---

#### GET `/risk-history`

Returns historical risk scores for trend visualization.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 7 | Days to look back (1-30) |

**Response:**
```json
{
  "history": [
    {
      "date": "2024-12-27",
      "global_risk": 44.2,
      "geo_risk": 46.1,
      "finance_risk": 41.8
    }
  ],
  "days": 7,
  "timestamp": "2024-12-28T10:00:00Z"
}
```

---

### Clusters

#### GET `/clusters`

Returns list of clusters with filtering and pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_events` | int | - | Minimum events in cluster |
| `time_range` | int | 7 | Time range in days |
| `time_window` | string | - | Filter: `1h`, `6h`, `12h`, `24h`, `week`, `month` |
| `sort_by` | string | - | Sort: `risk_score`, `event_count`, `last_updated` |
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response:**
```json
{
  "clusters": [
    {
      "cluster_id": "uuid",
      "title": "Economic Policy Changes",
      "description": "Federal Reserve announces...",
      "category": "finance",
      "subcategory": "Banking",
      "risk_score": 65.3,
      "event_count": 8,
      "entities": {
        "persons": ["Jerome Powell"],
        "organizations": ["Federal Reserve"],
        "locations": ["Washington DC"]
      },
      "created_at": "2024-12-27T08:00:00Z",
      "updated_at": "2024-12-28T09:30:00Z"
    }
  ],
  "total": 127,
  "page": 1,
  "per_page": 20,
  "pages": 7
}
```

---

#### GET `/clusters/{cluster_id}`

Returns detailed information for a specific cluster.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cluster_id` | UUID | Cluster identifier |

**Response:**
```json
{
  "cluster_id": "uuid",
  "title": "Economic Policy Changes",
  "description": "Detailed description...",
  "category": "finance",
  "subcategory": "Banking",
  "risk_score": 65.3,
  "risk_level": "high",
  "event_count": 8,
  "entities": {
    "persons": ["Jerome Powell", "Janet Yellen"],
    "organizations": ["Federal Reserve", "Treasury"],
    "locations": ["Washington DC", "New York"]
  },
  "keywords": ["interest rates", "monetary policy", "inflation"],
  "timeline": [
    {"date": "2024-12-27", "event_count": 3},
    {"date": "2024-12-28", "event_count": 5}
  ],
  "created_at": "2024-12-27T08:00:00Z",
  "updated_at": "2024-12-28T09:30:00Z"
}
```

---

#### GET `/clusters/{cluster_id}/events`

Returns events belonging to a cluster.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cluster_id` | UUID | Cluster identifier |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |

**Response:**
```json
{
  "events": [
    {
      "event_id": "uuid",
      "title": "Fed Announces Rate Decision",
      "source": "reuters",
      "url": "https://...",
      "published_at": "2024-12-28T09:00:00Z",
      "entities": {
        "persons": ["Jerome Powell"],
        "organizations": ["Federal Reserve"],
        "locations": ["Washington DC"]
      }
    }
  ],
  "total": 8,
  "page": 1,
  "per_page": 20
}
```

---

### Events

#### GET `/events/latest`

Returns latest events across all clusters.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hours` | int | 4 | Hours to look back (1-48) |
| `limit` | int | 20 | Max events (1-100) |

**Response:**
```json
{
  "events": [
    {
      "event_id": "uuid",
      "title": "Breaking: Major Development...",
      "cluster_id": "uuid",
      "cluster_title": "Related Cluster",
      "risk_score": 58.2,
      "source": "bbc",
      "published_at": "2024-12-28T09:45:00Z"
    }
  ],
  "count": 15,
  "hours": 4,
  "timestamp": "2024-12-28T10:00:00Z"
}
```

---

#### POST `/events/detect`

Analyzes text to extract entities and keywords.

**Request Body:**
```json
{
  "text": "Goldman Sachs announced major restructuring in New York...",
  "include_keywords": true,
  "max_keywords": 10
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to analyze (10-50000 chars) |
| `include_keywords` | bool | No | Extract keywords (default: true) |
| `max_keywords` | int | No | Max keywords (1-50, default: 10) |

**Response:**
```json
{
  "entities": {
    "persons": ["John Smith"],
    "organizations": ["Goldman Sachs"],
    "locations": ["New York"]
  },
  "keywords": ["restructuring", "layoffs", "banking"],
  "entity_count": 3,
  "text_length": 156,
  "processing_time_ms": 45
}
```

---

### Risk Analysis

#### POST `/risk/calculate`

Calculates risk score for a cluster, entities, or text.

**Request Body (one of three modes):**

```json
// Mode 1: By cluster ID
{
  "cluster_id": "uuid",
  "include_factors": true
}

// Mode 2: By entity names
{
  "entities": ["Goldman Sachs", "Federal Reserve"],
  "include_factors": true
}

// Mode 3: By text content
{
  "text": "Breaking news about cyberattack...",
  "include_factors": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cluster_id` | UUID | No* | Cluster to calculate risk for |
| `entities` | string[] | No* | Entity names to analyze |
| `text` | string | No* | Text content (max 50000 chars) |
| `include_factors` | bool | No | Include factor breakdown (default: true) |

*At least one of `cluster_id`, `entities`, or `text` required.

**Response:**
```json
{
  "risk_score": 67.5,
  "risk_level": "high",
  "risk_delta": 3.2,
  "factors": [
    {
      "name": "Event Frequency",
      "value": 0.8,
      "weight": 0.3,
      "contribution": 24.0
    },
    {
      "name": "Entity Prominence",
      "value": 0.6,
      "weight": 0.25,
      "contribution": 15.0
    }
  ],
  "cluster_id": "uuid",
  "timestamp": "2024-12-28T10:00:00Z"
}
```

**Risk Levels:**
| Score | Level |
|-------|-------|
| 0-24 | `low` |
| 25-49 | `medium` |
| 50-74 | `high` |
| 75-100 | `critical` |

---

### Admin Endpoints

#### GET `/clustering/status`

Returns clustering pipeline status.

**Response:**
```json
{
  "status": "idle",
  "last_run": "2024-12-28T06:00:00Z",
  "next_scheduled": "2024-12-28T12:00:00Z",
  "clusters_created": 127,
  "events_processed": 1543
}
```

---

#### POST `/clustering/trigger`

Manually triggers clustering pipeline.

**Response:**
```json
{
  "task_id": "uuid",
  "status": "started",
  "message": "Clustering task initiated"
}
```

---

#### GET `/clustering/task/{task_id}`

Returns status of a clustering task.

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {
    "clusters_created": 15,
    "events_processed": 234
  }
}
```

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Error message describing the issue"
}
```

**Status Codes:**
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 404 | Resource not found |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## Rate Limits

- Standard endpoints: 100 requests/minute
- POST endpoints: 30 requests/minute
- Admin endpoints: 10 requests/minute

---

## Related

- [Intelligence Service README](../../services/intelligence-service/README.md)
- [Swagger UI](http://localhost:8118/docs)
- [OpenAPI JSON](http://localhost:8118/openapi.json)

# Clustering Service

**Version:** 2.0.0
**Port:** 8122 (HTTP), /metrics (Prometheus)
**Language:** Python 3.11
**Framework:** FastAPI + Celery

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Batch Clustering (Topic Discovery)](#batch-clustering-topic-discovery)
4. [API Endpoints](#api-endpoints)
5. [Event Flow (RabbitMQ)](#event-flow-rabbitmq)
6. [Configuration](#configuration)
7. [Database Schema](#database-schema)
8. [Dependencies](#dependencies)
9. [Development](#development)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Clustering Service provides **dual-mode clustering** for news articles:

1. **Single-Pass Clustering** (Real-time): O(n) algorithm for immediate burst detection
2. **Batch Clustering** (Topic Discovery): UMAP + HDBSCAN for high-quality semantic topic clusters

Both modes run in parallel, serving different use cases while sharing the same article embeddings.

### Key Features

**Real-Time (Single-Pass):**
- **O(n) Clustering:** Real-time article assignment as events arrive
- **Burst Detection:** Automatic breaking news detection based on growth rate
- **Incremental Centroid Updates:** Memory-efficient running average (Welford's algorithm)

**Batch (Topic Discovery):**
- **UMAP + HDBSCAN:** High-quality semantic clustering via dimensionality reduction
- **pgvector Integration:** Efficient centroid similarity search
- **Keyword Extraction:** TF-IDF based topic keywords
- **Incremental Assignment:** New articles auto-assigned to existing topics
- **Celery Scheduling:** Automatic recomputation every 2 hours

**Shared:**
- **Event-Driven Architecture:** Consumes analysis events, emits cluster events
- **Circuit Breaker Protection:** Fault-tolerant RabbitMQ publishing
- **Cosine Similarity Matching:** Semantic similarity using 1536-dim embeddings

### Use Cases

| Mode | Use Cases |
|------|-----------|
| **Single-Pass** | Breaking news alerts, real-time dashboards, velocity tracking |
| **Batch** | Topic browsing, semantic search, trend analysis, content organization |

### Quick Comparison

| Feature | Single-Pass | Batch |
|---------|-------------|-------|
| Latency | Real-time (<100ms) | Periodic (every 2h) |
| Quality | Good (greedy matching) | High (UMAP+HDBSCAN) |
| API | `/api/v1/clusters` | `/api/v1/topics` |
| Storage | `article_clusters` | `batch_clusters` |
| Algorithm | Cosine similarity threshold | UMAP dimensionality reduction + HDBSCAN density clustering |

---

## Architecture

### Single-Pass Clustering Algorithm

```
                         ┌─────────────────────────────────────────┐
                         │         Analysis Consumer               │
                         │    (analysis.v3.completed events)       │
                         └─────────────────┬───────────────────────┘
                                           │
                                           ▼
                         ┌─────────────────────────────────────────┐
                         │         Extract Embedding               │
                         │      (384-dim sentence vector)          │
                         └─────────────────┬───────────────────────┘
                                           │
                                           ▼
                         ┌─────────────────────────────────────────┐
                         │      Load Active Clusters               │
                         │   (last 72 hours, up to 1000)           │
                         └─────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────┴──────────────────────┐
                    │           For each cluster:                  │
                    │    Calculate cosine_similarity(embedding,    │
                    │                cluster.centroid)             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │    Best Match >= Threshold (0.75)?           │
                    └───────────────┬─────────────┬────────────────┘
                                    │             │
                            YES     │             │     NO
                                    ▼             ▼
               ┌────────────────────────┐   ┌────────────────────────┐
               │   Update Cluster       │   │   Create New Cluster   │
               │   - Increment count    │   │   - Article as seed    │
               │   - Update centroid    │   │   - Embedding as       │
               │   - Merge entities     │   │     centroid           │
               │   - Check burst        │   │                        │
               └───────────┬────────────┘   └───────────┬────────────┘
                           │                            │
                           ▼                            ▼
               ┌────────────────────────┐   ┌────────────────────────┐
               │ Emit cluster.updated   │   │ Emit cluster.created   │
               │ (+ burst_detected      │   │                        │
               │   if threshold met)    │   │                        │
               └────────────────────────┘   └────────────────────────┘
```

### Incremental Centroid Update (Welford's Algorithm)

The service uses Welford's online algorithm for numerically stable centroid updates:

```
new_centroid = old_centroid + (new_vector - old_centroid) / n
```

Benefits:
- O(1) space complexity (no need to store all vectors)
- Numerically stable for large n
- Real-time updates without recomputation

### Components

1. **FastAPI Application** (`app/main.py`)
   - REST API endpoints (Port 8122)
   - Prometheus metrics endpoint
   - Health/readiness checks

2. **Analysis Consumer** (`app/workers/analysis_consumer.py`)
   - Consumes `analysis.v3.completed` events
   - Coordinates clustering logic
   - Triggers event publishing

3. **Clustering Service** (`app/services/clustering.py`)
   - Cosine similarity calculation
   - Cluster matching logic
   - Centroid update algorithm

4. **Cluster Repository** (`app/services/cluster_repository.py`)
   - PostgreSQL database operations
   - CRUD for clusters

5. **Event Publisher** (`app/services/event_publisher.py`)
   - Circuit breaker protected publishing
   - EventEnvelope wrapper
   - Cluster event emission

---

## Batch Clustering (Topic Discovery)

The batch clustering system provides high-quality semantic topic clusters using UMAP dimensionality reduction and HDBSCAN density-based clustering.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Batch Clustering Pipeline                             │
│                    (Celery Beat: Every 2 Hours)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Load Embeddings from article_analysis (pgvector, max 30k articles)  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. UMAP Dimensionality Reduction (1536D → 10D)                         │
│     - n_neighbors=15, min_dist=0.1, metric=cosine                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. HDBSCAN Density Clustering                                          │
│     - min_cluster_size=15, min_samples=5                                │
│     - Automatic cluster count discovery                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. Post-Processing                                                     │
│     - Compute cluster centroids (mean of embeddings)                    │
│     - Generate labels (first article title)                             │
│     - Extract keywords (TF-IDF top 5 terms)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  5. Store to Database                                                   │
│     - cluster_batches (batch metadata)                                  │
│     - batch_clusters (clusters with pgvector centroids)                 │
│     - batch_article_clusters (article assignments)                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Incremental Assignment

New articles arriving between batch runs are automatically assigned to existing topic clusters:

```
┌──────────────────────┐     ┌──────────────────────┐
│  analysis.v3.completed│────▶│  Extract Embedding   │
│  (new article event)  │     │  (1536-dim vector)   │
└──────────────────────┘     └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │  pgvector Similarity │
                             │  Search (top 5)      │
                             │  centroid_vec <=>    │
                             └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │  Best Match > 0.5?   │
                             └─────────┬────────────┘
                                       │
                         YES ──────────┴────────── NO
                          │                        │
                          ▼                        ▼
                 ┌────────────────┐      ┌────────────────┐
                 │ Assign to      │      │ Skip (handled  │
                 │ batch cluster  │      │ in next batch) │
                 └────────────────┘      └────────────────┘
```

### Celery Workers

The batch clustering uses dedicated Celery workers:

```yaml
# docker-compose.yml
clustering-celery-worker:
  command: celery -A app.workers.batch_clustering_worker worker -Q batch-clustering -c 1
  mem_limit: 6g

clustering-celery-beat:
  command: celery -A app.workers.batch_clustering_worker beat
```

### Performance Metrics

Based on production runs with 30,000 articles:

| Metric | Value |
|--------|-------|
| Total processing time | ~130 seconds |
| UMAP reduction | ~45 seconds |
| HDBSCAN clustering | ~10 seconds |
| Post-processing | ~60 seconds |
| Typical cluster count | 500-600 |
| Noise ratio | 20-25% |
| Memory usage (peak) | ~5 GB |

### Manual Trigger

```bash
# Trigger batch clustering manually via Celery
docker exec news-clustering-celery-worker celery -A app.workers.batch_clustering_worker call app.workers.batch_clustering_worker.recompute_clusters

# Check task status
docker exec news-clustering-celery-worker celery -A app.workers.batch_clustering_worker inspect active
```

---

## API Endpoints

### Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "service": "clustering-service"
}
```

### Readiness Check

**GET** `/ready`

```json
{
  "status": "ready"
}
```

### Assign Article to Cluster

**POST** `/api/v1/clusters/articles`

Assigns an article to an existing cluster or creates a new one.

**Request:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "embedding": [0.123, -0.456, 0.789, ...],
  "title": "Breaking: Major Tech Company Announces Merger",
  "published_at": "2025-01-04T12:00:00Z",
  "entities": [
    {"id": "Q312", "name": "Apple Inc.", "type": "ORGANIZATION"},
    {"id": "Q42", "name": "Tim Cook", "type": "PERSON"}
  ],
  "simhash_fingerprint": 12345678901234567890
}
```

**Response:**
```json
{
  "cluster_id": "660e8400-e29b-41d4-a716-446655440000",
  "is_new_cluster": false,
  "similarity_score": 0.87,
  "cluster_article_count": 5
}
```

### List Clusters

**GET** `/api/v1/clusters`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | `active` | Filter: `active`, `archived`, `all` |
| `min_articles` | int | `2` | Minimum article count |
| `hours` | int | `24` | Time window (1-168) |
| `limit` | int | `50` | Page size (1-100) |
| `offset` | int | `0` | Pagination offset |

**Response:**
```json
{
  "clusters": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "title": "Tech Industry Merger Developments",
      "article_count": 12,
      "status": "active",
      "tension_score": 7.5,
      "is_breaking": true,
      "first_seen_at": "2025-01-04T08:00:00Z",
      "last_updated_at": "2025-01-04T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 156,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

### Get Cluster Details

**GET** `/api/v1/clusters/{cluster_id}`

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "title": "Tech Industry Merger Developments",
  "article_count": 12,
  "status": "active",
  "tension_score": 7.5,
  "is_breaking": true,
  "first_seen_at": "2025-01-04T08:00:00Z",
  "last_updated_at": "2025-01-04T14:30:00Z",
  "summary": null,
  "centroid_vector": [0.123, -0.456, ...],
  "primary_entities": [
    {"id": "Q312", "name": "Apple Inc.", "type": "ORGANIZATION"},
    {"id": "Q42", "name": "Tim Cook", "type": "PERSON"}
  ],
  "burst_detected_at": "2025-01-04T10:15:00Z"
}
```

### Prometheus Metrics

**GET** `/metrics`

Returns Prometheus-formatted metrics for monitoring.

---

## Topics API (Batch Clustering)

The Topics API provides access to high-quality semantic topic clusters computed via UMAP+HDBSCAN.

### List Topics

**GET** `/api/v1/topics`

Returns paginated list of topic clusters from the latest completed batch.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_size` | int | `10` | Minimum article count |
| `limit` | int | `50` | Page size (1-100) |
| `offset` | int | `0` | Pagination offset |
| `batch_id` | UUID | (latest) | Specific batch to query |

**Response:**
```json
{
  "topics": [
    {
      "id": 80,
      "label": "Trump tariffs and trade war concerns",
      "article_count": 156,
      "keywords": ["tariffs", "trade", "trump", "china", "imports"],
      "created_at": "2026-01-05T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 578,
    "limit": 50,
    "offset": 0,
    "has_more": true
  },
  "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Search Topics by Keyword

**GET** `/api/v1/topics/search`

Searches for topics containing articles with matching keywords.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Comma-separated keywords |
| `limit` | int | No | Max results (default 20) |

**Example:**
```bash
curl "http://localhost:8122/api/v1/topics/search?q=ukraine,russia"
```

**Response:**
```json
{
  "results": [
    {
      "cluster_id": 45,
      "label": "Ukraine-Russia conflict updates",
      "article_count": 89,
      "keywords": ["ukraine", "russia", "war", "military"],
      "match_count": 45
    }
  ],
  "query": ["ukraine", "russia"]
}
```

### Get Topic Details

**GET** `/api/v1/topics/{topic_id}`

Returns detailed information about a specific topic cluster including sample articles.

**Response:**
```json
{
  "id": 80,
  "label": "Trump tariffs and trade war concerns",
  "article_count": 156,
  "keywords": ["tariffs", "trade", "trump", "china"],
  "label_confidence": 0.85,
  "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-01-05T10:30:00Z",
  "articles": [
    {
      "article_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Trump announces new tariffs on Chinese imports",
      "url": "https://example.com/article/123",
      "distance": 0.12,
      "assigned_at": "2026-01-05T10:35:00Z"
    }
  ]
}
```

### List Batch History

**GET** `/api/v1/topics/batches`

Returns history of batch clustering runs.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | (all) | Filter: `running`, `completed`, `failed` |
| `limit` | int | `10` | Max results |

**Response:**
```json
{
  "batches": [
    {
      "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "completed",
      "article_count": 28453,
      "cluster_count": 578,
      "noise_count": 5234,
      "csai_score": 0.72,
      "started_at": "2026-01-05T10:00:00Z",
      "completed_at": "2026-01-05T10:02:10Z"
    }
  ]
}
```

### Submit Feedback

**POST** `/api/v1/topics/{topic_id}/feedback`

Submit user feedback for cluster improvement (label corrections, merge/split suggestions).

**Request:**
```json
{
  "feedback_type": "label_correction",
  "new_value": {
    "label": "US-China trade tensions"
  },
  "created_by": "andreas"
}
```

**Response:**
```json
{
  "feedback_id": 42,
  "message": "Feedback recorded successfully"
}
```

**Feedback Types:**
| Type | Description |
|------|-------------|
| `label_correction` | Correct the cluster label |
| `merge` | Suggest merging with another cluster |
| `split` | Suggest splitting the cluster |
| `quality_rating` | Rate cluster quality (1-5) |

---

## Event Flow (RabbitMQ)

### Consumed Events

**Event:** `analysis.v3.completed`

Triggered when article analysis (LLM/embedding generation) completes.

**Queue:** `clustering.analysis`
**Exchange:** `news.events` (topic)

**Payload Schema:**
```json
{
  "article_id": "UUID",
  "title": "string",
  "embedding": [float, ...],
  "entities": [
    {"name": "string", "type": "string", ...}
  ],
  "sentiment": {"score": 0.5, ...},
  "topics": ["technology", "business"],
  "tension_level": 7.0,
  "published_at": "ISO8601",
  "simhash_fingerprint": 12345678901234567890
}
```

### Emitted Events

#### 1. `cluster.created`

Emitted when a new cluster is created from a seed article.

```json
{
  "event_type": "cluster.created",
  "event_id": "UUID",
  "timestamp": "ISO8601",
  "service": "clustering-service",
  "correlation_id": "UUID",
  "payload": {
    "cluster_id": "UUID",
    "title": "Article Title",
    "article_id": "UUID",
    "article_count": 1
  }
}
```

#### 2. `cluster.updated`

Emitted when an article is added to an existing cluster.

```json
{
  "event_type": "cluster.updated",
  "event_id": "UUID",
  "timestamp": "ISO8601",
  "service": "clustering-service",
  "correlation_id": "UUID",
  "payload": {
    "cluster_id": "UUID",
    "article_id": "UUID",
    "article_count": 5,
    "similarity_score": 0.87,
    "tension_score": 7.5,
    "is_breaking": false,
    "primary_entities": [
      {"name": "Apple Inc.", "type": "ORGANIZATION"}
    ]
  }
}
```

#### 3. `cluster.burst_detected`

Emitted when a cluster reaches the burst threshold (breaking news).

```json
{
  "event_type": "cluster.burst_detected",
  "event_id": "UUID",
  "timestamp": "ISO8601",
  "service": "clustering-service",
  "correlation_id": "UUID",
  "payload": {
    "cluster_id": "UUID",
    "title": "Major Breaking Story",
    "article_count": 10,
    "growth_rate": 2.0,
    "tension_score": 8.5,
    "detection_method": "frequency_spike",
    "top_entities": ["Apple Inc.", "Tim Cook", "Microsoft"],
    "recommended_action": "immediate_alert"
  }
}
```

### Event Flow Diagram

```
┌─────────────────┐     analysis.v3.completed     ┌─────────────────────┐
│ LLM Orchestrator│ ──────────────────────────────▶│  Clustering Service │
│   / Analyzer    │                                │                     │
└─────────────────┘                                └──────────┬──────────┘
                                                              │
                    ┌─────────────────────────────────────────┼──────────────────────────────────────┐
                    │                                         │                                      │
                    ▼                                         ▼                                      ▼
        ┌────────────────────┐               ┌────────────────────────┐              ┌───────────────────────┐
        │  cluster.created   │               │    cluster.updated     │              │ cluster.burst_detected│
        │                    │               │                        │              │                       │
        │ - New story started│               │ - Story growing        │              │ - Breaking news alert │
        │ - First article    │               │ - Entities updated     │              │ - Immediate attention │
        └────────┬───────────┘               └───────────┬────────────┘              └───────────┬───────────┘
                 │                                       │                                       │
                 ▼                                       ▼                                       ▼
        ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
        │                                    Downstream Consumers                                          │
        │  - Dashboard (live cluster display)                                                              │
        │  - Notification Service (n8n workflows)                                                          │
        │  - Analytics Service (trend tracking)                                                            │
        │  - Knowledge Graph (entity relationships)                                                        │
        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Service
SERVICE_NAME=clustering-service
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/news_intelligence

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=news.events

# Single-Pass Clustering Parameters
SIMILARITY_THRESHOLD=0.75          # Cosine similarity threshold for cluster matching
CLUSTER_MAX_AGE_HOURS=72           # Archive clusters older than this
BURST_DETECTION_WINDOW_MINUTES=60  # Time window for burst detection
BURST_ARTICLE_THRESHOLD=5          # Articles to trigger burst alert

# Batch Clustering Parameters (UMAP + HDBSCAN)
BATCH_ENABLED=true                 # Enable batch clustering
BATCH_MAX_ARTICLES=30000           # Maximum articles per batch
BATCH_MIN_CLUSTER_SIZE=15          # HDBSCAN min_cluster_size
BATCH_MIN_SAMPLES=5                # HDBSCAN min_samples
BATCH_UMAP_N_NEIGHBORS=15          # UMAP n_neighbors
BATCH_UMAP_MIN_DIST=0.1            # UMAP min_dist
BATCH_UMAP_N_COMPONENTS=10         # UMAP output dimensions
BATCH_SIMILARITY_THRESHOLD=0.5    # Incremental assignment threshold
BATCH_SCHEDULE_HOURS=2             # Recompute interval (Celery beat)
```

### Settings Class

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "clustering-service"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/news_intelligence"

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_EXCHANGE: str = "news.events"

    # Single-Pass Clustering parameters
    SIMILARITY_THRESHOLD: float = 0.75
    CLUSTER_MAX_AGE_HOURS: int = 72
    BURST_DETECTION_WINDOW_MINUTES: int = 60
    BURST_ARTICLE_THRESHOLD: int = 5

    # Batch Clustering parameters
    BATCH_ENABLED: bool = True
    BATCH_MAX_ARTICLES: int = 30000
    BATCH_MIN_CLUSTER_SIZE: int = 15
    BATCH_MIN_SAMPLES: int = 5
    BATCH_UMAP_N_NEIGHBORS: int = 15
    BATCH_UMAP_MIN_DIST: float = 0.1
    BATCH_UMAP_N_COMPONENTS: int = 10
    BATCH_SIMILARITY_THRESHOLD: float = 0.5
    BATCH_SCHEDULE_HOURS: int = 2

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
```

### Tuning Recommendations

**Single-Pass Clustering:**

| Parameter | Low Value | High Value | Effect |
|-----------|-----------|------------|--------|
| `SIMILARITY_THRESHOLD` | 0.6 | 0.9 | Lower = more articles per cluster, higher = stricter matching |
| `CLUSTER_MAX_AGE_HOURS` | 24 | 168 | Shorter = more new clusters, longer = larger clusters |
| `BURST_ARTICLE_THRESHOLD` | 3 | 10 | Lower = more burst alerts, higher = fewer false positives |

**Batch Clustering:**

| Parameter | Low Value | High Value | Effect |
|-----------|-----------|------------|--------|
| `BATCH_MIN_CLUSTER_SIZE` | 5 | 30 | Lower = more small clusters, higher = fewer, denser clusters |
| `BATCH_UMAP_N_NEIGHBORS` | 5 | 50 | Lower = local structure, higher = global structure preservation |
| `BATCH_UMAP_MIN_DIST` | 0.0 | 0.5 | Lower = tighter clusters, higher = more spread out |
| `BATCH_SIMILARITY_THRESHOLD` | 0.3 | 0.7 | Lower = more incremental assignments, higher = stricter matching |

---

## Database Schema

### Single-Pass Clustering Tables

#### Table: `article_clusters`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique cluster identifier |
| `title` | VARCHAR(500) | Cluster title (from first article) |
| `summary` | TEXT | Optional cluster summary |
| `status` | VARCHAR(20) | `active`, `archived` |
| `article_count` | INTEGER | Number of articles in cluster |
| `first_seen_at` | TIMESTAMP (TZ) | When cluster was created |
| `last_updated_at` | TIMESTAMP (TZ) | Last article addition |
| `centroid_vector` | JSONB | Current centroid embedding |
| `tension_score` | FLOAT | Average tension score (0-10) |
| `is_breaking` | BOOLEAN | Whether burst was detected |
| `burst_detected_at` | TIMESTAMP (TZ) | When burst was detected |
| `primary_entities` | JSONB | Top entities in cluster |
| `created_at` | TIMESTAMP (TZ) | Row creation timestamp |

**Indexes:**
- Primary key on `id`
- Index on `status` for active cluster queries
- Index on `last_updated_at` for time-based filtering

### Batch Clustering Tables (pgvector)

#### Table: `cluster_batches`

Tracks batch clustering runs and their statistics.

| Column | Type | Description |
|--------|------|-------------|
| `batch_id` | UUID (PK) | Unique batch identifier |
| `status` | VARCHAR(20) | `running`, `completed`, `failed` |
| `article_count` | INTEGER | Total articles processed |
| `cluster_count` | INTEGER | Number of clusters created |
| `noise_count` | INTEGER | Articles marked as noise (-1) |
| `csai_score` | FLOAT | Cluster Silhouette Average Index |
| `started_at` | TIMESTAMP (TZ) | When batch started |
| `completed_at` | TIMESTAMP (TZ) | When batch completed |
| `error_message` | TEXT | Error details (if failed) |

#### Table: `batch_clusters`

Stores topic clusters with pgvector centroids.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL (PK) | Auto-increment cluster ID |
| `batch_id` | UUID (FK) | Reference to cluster_batches |
| `hdbscan_label` | INTEGER | Original HDBSCAN label |
| `label` | VARCHAR(255) | Human-readable topic label |
| `label_confidence` | FLOAT | Confidence score (0-1) |
| `article_count` | INTEGER | Articles in this cluster |
| `keywords` | VARCHAR[] | TF-IDF extracted keywords |
| `centroid_vec` | VECTOR(1536) | pgvector centroid embedding |
| `created_at` | TIMESTAMP (TZ) | Row creation timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key on `batch_id` → `cluster_batches.batch_id`
- **HNSW index** on `centroid_vec` for fast similarity search:
  ```sql
  CREATE INDEX idx_batch_clusters_centroid_hnsw
  ON batch_clusters USING hnsw (centroid_vec vector_cosine_ops);
  ```

#### Table: `batch_article_clusters`

Maps articles to their batch cluster assignments.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL (PK) | Auto-increment ID |
| `batch_id` | UUID (FK) | Reference to cluster_batches |
| `article_id` | UUID | Reference to feed_items |
| `cluster_id` | INTEGER (FK) | Reference to batch_clusters |
| `distance_to_centroid` | FLOAT | Distance from article to centroid |
| `assigned_at` | TIMESTAMP (TZ) | When assignment was made |

**Indexes:**
- Composite index on `(batch_id, article_id)` for lookup
- Index on `cluster_id` for cluster article listing

#### Table: `cluster_feedback`

Stores user feedback for cluster improvement.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL (PK) | Auto-increment ID |
| `cluster_id` | INTEGER (FK) | Reference to batch_clusters |
| `feedback_type` | VARCHAR(50) | `label_correction`, `merge`, `split`, `quality_rating` |
| `old_value` | JSONB | Previous value |
| `new_value` | JSONB | Corrected value |
| `created_by` | VARCHAR(100) | User identifier |
| `created_at` | TIMESTAMP (TZ) | When feedback was submitted |

---

## Dependencies

### Python Packages

```
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy>=2.0.0
asyncpg>=0.29.0
pgvector>=0.2.0              # pgvector support for SQLAlchemy

# Message Queue
aio_pika>=9.3.0
celery>=5.3.0                # Batch clustering task queue
redis>=5.0.0                 # Celery broker

# Machine Learning (Batch Clustering)
numpy>=1.26.0
scikit-learn>=1.4.0          # TF-IDF, metrics
umap-learn>=0.5.5            # Dimensionality reduction
hdbscan>=0.8.33              # Density-based clustering

# Utilities
httpx>=0.25.0
prometheus-client>=0.19.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### Shared Libraries

**news-intelligence-common**
- `create_event()` - EventEnvelope creation
- Standardized event format

**news-mcp-common**
- `ResilientRabbitMQPublisher` - Circuit breaker protected publishing
- `CircuitBreakerConfig` - Fault tolerance configuration

### Infrastructure Dependencies

| Service | Purpose |
|---------|---------|
| PostgreSQL | Cluster storage |
| RabbitMQ | Event consumption and publishing |
| Prometheus | Metrics collection |

---

## Development

### Local Setup

```bash
# 1. Navigate to service directory
cd /home/cytrex/news-microservices/services/clustering-service

# 2. Create virtual environment (optional for local development)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Start via Docker Compose (recommended)
cd /home/cytrex/news-microservices
docker compose up -d clustering-service

# 4. Verify service is running
curl http://localhost:8122/health
# Expected: {"status":"healthy","service":"clustering-service"}
```

### Code Structure

```
services/clustering-service/
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── config.py                     # Settings and configuration
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── clusters.py           # Single-Pass API endpoints
│   │       └── topics.py             # Batch/Topics API endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py                # Database session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cluster.py                # Single-Pass cluster models
│   │   └── batch_cluster.py          # Batch cluster models (pgvector)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── cluster.py                # Single-Pass API schemas
│   │   ├── batch_cluster.py          # Batch/Topics API schemas
│   │   └── events.py                 # Event payload schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── clustering.py             # Single-Pass clustering algorithm
│   │   ├── cluster_repository.py     # Single-Pass database operations
│   │   ├── batch_clustering.py       # UMAP+HDBSCAN batch clustering
│   │   ├── batch_cluster_repository.py # Batch cluster database operations
│   │   └── event_publisher.py        # RabbitMQ event publishing
│   └── workers/
│       ├── __init__.py
│       ├── analysis_consumer.py      # RabbitMQ event consumer + incremental assignment
│       └── batch_clustering_worker.py # Celery worker for batch clustering
├── tests/
│   ├── __init__.py
│   ├── test_clustering.py            # Single-Pass unit tests
│   └── test_batch_clustering.py      # Batch clustering tests
├── scripts/                          # Utility scripts
├── Dockerfile
├── requirements.txt
└── README.md
```

### API Documentation

- **Swagger UI:** http://localhost:8122/docs
- **ReDoc:** http://localhost:8122/redoc
- **OpenAPI JSON:** http://localhost:8122/openapi.json

---

## Testing

### Run Unit Tests

```bash
# From service directory
cd /home/cytrex/news-microservices/services/clustering-service

# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_clustering.py::TestCosineSimialrity -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8122/health

# List clusters (last 24 hours, min 2 articles)
curl "http://localhost:8122/api/v1/clusters?hours=24&min_articles=2"

# Get specific cluster
curl http://localhost:8122/api/v1/clusters/660e8400-e29b-41d4-a716-446655440000

# Assign article to cluster (POST)
curl -X POST http://localhost:8122/api/v1/clusters/articles \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "embedding": [0.1, 0.2, 0.3, 0.4],
    "title": "Test Article",
    "entities": [{"id": "Q1", "name": "Test Entity", "type": "ORGANIZATION"}]
  }'
```

### Test Coverage Summary

| Module | Coverage |
|--------|----------|
| `services/clustering.py` | ~95% |
| `services/cluster_repository.py` | ~80% |
| `api/v1/clusters.py` | ~75% |

---

## Troubleshooting

### Issue 1: Service Not Starting

**Symptoms:**
```
ERROR: Failed to connect to PostgreSQL
ERROR: Failed to connect to RabbitMQ
```

**Solution:**
```bash
# Check PostgreSQL
docker ps | grep postgres
docker logs news-postgres-1

# Check RabbitMQ
docker ps | grep rabbitmq
docker logs news-rabbitmq-1

# Verify network connectivity
docker exec news-clustering-service-1 ping postgres
docker exec news-clustering-service-1 ping rabbitmq
```

### Issue 2: No Clusters Being Created

**Symptoms:**
- Articles analyzed but no clusters appearing
- No `cluster.created` events

**Diagnosis:**
```bash
# Check if consumer is receiving events
docker logs news-clustering-service-1 | grep "Processing article"

# Check RabbitMQ queue
curl -u guest:guest http://localhost:15672/api/queues/%2F/clustering.analysis
```

**Common Causes:**
1. Missing embeddings in analysis events
2. Consumer not bound to exchange
3. Exchange routing key mismatch

### Issue 3: Too Many Clusters (Low Merge Rate)

**Symptoms:**
- Many single-article clusters
- Similar stories not being grouped

**Diagnosis:**
```sql
-- Check cluster statistics
SELECT
  status,
  COUNT(*) as cluster_count,
  AVG(article_count) as avg_articles
FROM article_clusters
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;
```

**Solution:**
- Lower `SIMILARITY_THRESHOLD` from 0.75 to 0.65
- Increase `CLUSTER_MAX_AGE_HOURS` for longer matching window
- Check embedding quality from analysis service

### Issue 4: Circuit Breaker Open

**Symptoms:**
```
ERROR: Circuit breaker OPEN - refusing to publish cluster.updated
```

**Solution:**
```bash
# Check RabbitMQ health
docker logs news-rabbitmq-1

# Restart clustering service to reset circuit breaker
docker restart news-clustering-service-1

# Check metrics for failure patterns
curl http://localhost:8122/metrics | grep circuit
```

### Issue 5: High Memory Usage

**Symptoms:**
- Service consuming > 1GB memory
- Slow response times

**Diagnosis:**
```bash
# Check memory usage
docker stats news-clustering-service-1

# Check active cluster count
docker exec news-postgres-1 psql -U postgres -d news_intelligence -c \
  "SELECT COUNT(*) FROM article_clusters WHERE status = 'active';"
```

**Solution:**
- Reduce `CLUSTER_MAX_AGE_HOURS` to limit active clusters
- Add index on frequently queried columns
- Consider archiving old clusters more aggressively

---

## Enhanced Burst Detection (Epic 1.3)

The service includes sophisticated burst detection for breaking news identification.

### Features (v1 - Velocity-Based)

- **Time-Windowed Velocity Tracking:** Counts articles within sliding window (default 15 min)
- **Severity Levels:**
  - `low`: 3+ articles/window
  - `medium`: 5+ articles/window
  - `high`: 10+ articles/window
  - `critical`: 20+ articles/window
- **Cooldown Period:** Prevents alert spam (default 30 min)
- **Webhook Integration:** Sends alerts to n8n for notification routing
- **Database Persistence:** Full audit trail of all burst detections
- **Alert Acknowledgment:** Track which alerts have been reviewed

### Multi-Signal Analysis (v2 - Enhanced)

> **Added 2026-01-18** - See [POSTMORTEMS.md Incident #35](../../POSTMORTEMS.md)

The v2 algorithm uses multiple signals to reduce false positives and improve detection accuracy:

| Signal | Calculation | Threshold | Purpose |
|--------|-------------|-----------|---------|
| **Velocity** | Articles in window | ≥3 | Base requirement |
| **Growth Rate** | current / previous window | ≥2.0x | Detect acceleration |
| **Concentration** | window_articles / total_cluster | ≥50% | Detect sudden spikes |
| **Source Diversity** | Unique sources in window | ≥2 | Filter single-source spam |

**Detection Rule:** Burst requires velocity threshold + at least one other signal.

**Example:**
- ❌ 5 articles in window, but growth rate 1.0x → No burst (steady, not accelerating)
- ✅ 4 articles in window, growth rate 3.0x → Burst detected (rapid acceleration)
- ✅ 3 articles in window, concentration 80% → Burst detected (sudden spike)

**Enable/Disable:**
```bash
USE_ENHANCED_BURST_DETECTION=true   # Use v2 multi-signal (default)
USE_ENHANCED_BURST_DETECTION=false  # Use v1 velocity-only
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/bursts` | GET | List all burst alerts with pagination |
| `/api/v1/bursts/active` | GET | List active (recent) burst alerts |
| `/api/v1/bursts/{burst_id}` | GET | Get specific burst alert details |
| `/api/v1/bursts/{burst_id}/acknowledge` | POST | Acknowledge a burst alert |
| `/api/v1/bursts/stats` | GET | Get burst detection statistics |
| `/api/v1/bursts/cluster/{cluster_id}` | GET | Get burst history for a cluster |

### Configuration

**Basic Settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `BURST_WINDOW_MINUTES` | 15 | Velocity detection window |
| `BURST_VELOCITY_LOW` | 3 | Threshold for low severity |
| `BURST_VELOCITY_MEDIUM` | 5 | Threshold for medium severity |
| `BURST_VELOCITY_HIGH` | 10 | Threshold for high severity |
| `BURST_VELOCITY_CRITICAL` | 20 | Threshold for critical severity |
| `BURST_COOLDOWN_MINUTES` | 30 | Cooldown between alerts |
| `BURST_WEBHOOK_URL` | `http://n8n:5678/webhook/burst-alert` | n8n webhook URL |
| `BURST_WEBHOOK_ENABLED` | true | Enable/disable webhook alerts |

**v2 Multi-Signal Settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_ENHANCED_BURST_DETECTION` | true | Enable v2 multi-signal detection |
| `BURST_GROWTH_RATE_THRESHOLD` | 2.0 | Min growth rate to trigger (2.0 = doubled) |
| `BURST_CONCENTRATION_THRESHOLD` | 0.5 | Min % of articles in window (0.5 = 50%) |
| `BURST_MIN_SOURCES` | 2 | Min unique sources required |
| `BURST_REQUIRE_MULTI_SIGNAL` | true | Require velocity + 1 other signal |

### Prometheus Metrics

**v1 Metrics:**
- `clustering_burst_detected_total{severity}` - Total bursts by severity
- `clustering_burst_velocity` - Histogram of burst velocities
- `clustering_webhook_sent_total{severity,success}` - Webhook delivery stats
- `clustering_webhook_latency_seconds` - Webhook request latency

**v2 Metrics:**
- `clustering_burst_v2_detected_total{severity,signal}` - Total v2 bursts by severity and primary signal
- `clustering_burst_v2_growth_rate` - Histogram of growth rates (buckets: 1.5, 2.0, 3.0, 5.0, 10.0, 20.0)

### Database Tables

**Table: `burst_alerts`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique alert identifier |
| `cluster_id` | UUID | Reference to cluster |
| `severity` | VARCHAR(20) | low, medium, high, critical |
| `velocity` | INTEGER | Articles per window when detected |
| `window_minutes` | INTEGER | Detection window size |
| `alert_sent` | BOOLEAN | Whether webhook was sent |
| `alert_sent_at` | TIMESTAMP (TZ) | When alert was sent |
| `acknowledged` | BOOLEAN | Whether alert was acknowledged |
| `acknowledged_at` | TIMESTAMP (TZ) | When alert was acknowledged |
| `acknowledged_by` | VARCHAR(100) | User who acknowledged |
| `detected_at` | TIMESTAMP (TZ) | When burst was detected |

---

## Frontend Integration

The clustering-service provides the backend for the **Topic Browser** UI in the frontend.

### Topic Browser

- **Route:** `/intelligence/topics`
- **Documentation:** [docs/features/topic-browser.md](../../docs/features/topic-browser.md)

**Features:**
- Browse 500+ semantic topic clusters
- Search topics by keyword
- Filter by minimum article count
- View topic details with sample articles
- Distance scores showing article similarity to cluster centroid

### CORS Configuration

The service includes CORS middleware for browser access from the frontend:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

**Allowed Origins:**
- `http://localhost:3000` (local development)
- `http://192.168.x.x:3000` (remote access from LAN)

### Frontend API Client

The frontend uses dynamic hostname detection for remote access:

```typescript
// frontend/src/features/intelligence/topics/api/topicApi.ts
const getBaseUrl = () => {
  if (import.meta.env.VITE_TOPICS_API_URL) {
    return import.meta.env.VITE_TOPICS_API_URL;
  }
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${hostname}:8122/api/v1`;
};
```

---

## Related Documentation

- **Architecture Overview:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
- **Backend Development Guide:** [CLAUDE.backend.md](../../CLAUDE.backend.md)
- **Circuit Breaker Pattern:** [ADR-035](../../docs/decisions/ADR-035-circuit-breaker-pattern.md)
- **news-intelligence-common:** [libs/news-intelligence-common/](../../libs/news-intelligence-common/)
- **news-mcp-common (Resilience):** [libs/news-mcp-common/](../../libs/news-mcp-common/)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-01-04 | 1.0.0 | Initial release with Single-Pass Clustering | Development Team |
| 2026-01-04 | 1.1.0 | Epic 1.3: Enhanced Burst Detection with time-windowed velocity tracking, severity levels, webhook integration, and REST API | Development Team |
| 2026-01-05 | 2.0.0 | **Epic 1.4: Batch Clustering** - UMAP+HDBSCAN topic discovery, pgvector centroid storage, Topics API, incremental assignment, Celery workers, keyword extraction | Development Team |

---

**Questions or Issues?**

- Documentation: `/home/cytrex/news-microservices/docs/`
- Service: `clustering-service` (Port 8122)
- Swagger UI: http://localhost:8122/docs

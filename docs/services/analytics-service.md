# Analytics Service (Port 8107) - Comprehensive Documentation

**Service Name:** analytics-service
**Port:** 8107
**Framework:** FastAPI + SQLAlchemy + Redis + Celery
**Database:** PostgreSQL (analytics_metrics, analytics_reports, analytics_dashboards, analytics_alerts)
**Message Queue:** RabbitMQ (via Celery)
**Cache:** Redis (metrics caching, Celery broker)
**Real-Time:** WebSocket (dashboard live updates)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Core Components](#3-core-components)
4. [Data Model & Storage](#4-data-model--storage)
5. [API Contracts](#5-api-contracts)
   - [Analytics Endpoints](#51-analytics-endpoints)
   - [Dashboard Endpoints](#52-dashboard-endpoints)
   - [Report Endpoints](#53-report-endpoints)
   - [Monitoring Endpoints](#54-monitoring-endpoints)
   - [Cache Monitoring Endpoints](#55-cache-monitoring-endpoints)
   - [WebSocket Endpoints](#56-websocket-endpoints)
   - [Health Monitoring Endpoints](#57-health-monitoring-endpoints)
6. [Metrics Collection Strategy](#6-metrics-collection-strategy)
7. [Time-Series Data Handling](#7-time-series-data-handling)
8. [Query Performance & Indexing](#8-query-performance--indexing)
9. [Caching Strategy](#9-caching-strategy)
10. [Dashboard APIs](#10-dashboard-apis)
11. [Report Generation](#11-report-generation)
12. [Trend Analysis Engine](#12-trend-analysis-engine)
13. [Celery Workers & Background Tasks](#13-celery-workers--background-tasks)
14. [Data Retention Policies](#14-data-retention-policies)
15. [MCP Integration](#15-mcp-integration)
16. [Integration Points](#16-integration-points)
17. [Performance Characteristics](#17-performance-characteristics)
18. [Security & Authorization](#18-security--authorization)
19. [Common Issues & Troubleshooting](#19-common-issues--troubleshooting)
20. [Development Workflow](#20-development-workflow)
21. [Appendix: API Examples](#21-appendix-api-examples)
22. [API Endpoint Reference](#22-api-endpoint-reference)

---

## 1. Executive Summary

The Analytics Service is a comprehensive metrics aggregation and visualization platform for the News Microservices ecosystem. It collects time-series metrics from all services (auth, feed, content-analysis, research, osint, notification, search), stores them in PostgreSQL, and provides:

- **Real-time metric collection** via Celery workers (every 60 seconds)
- **Custom dashboards** with widget-based visualization (line charts, bar charts, pie charts, stat cards)
- **Trend analysis** with anomaly detection using statistical methods (z-score, linear regression)
- **Report generation** (CSV, JSON, Markdown) with historical data export
- **Live WebSocket updates** for real-time dashboard feeds
- **Alert system** with configurable thresholds and severity levels
- **Data retention policies** with automatic cleanup (90 days granular, 365 days aggregated)

**Key Metrics:** Service health status, request counts, error rates, latency, active users
**Retention:** 90 days of detailed metrics, 365 days of aggregated data
**Concurrency:** Handles 100+ dashboard connections via WebSocket
**Storage:** ~1-2 GB per month of metrics (7 services, 60-second collection)

---

## 2. Architecture Overview

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Analytics Service (8107)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐      ┌──────────────────────┐        │
│  │   FastAPI Server    │      │   WebSocket Server   │        │
│  │  (API Endpoints)    │      │  (Live Dashboards)   │        │
│  └──────────┬──────────┘      └──────────┬───────────┘        │
│             │                            │                     │
│  ┌──────────▼────────────────────────────▼──────────┐          │
│  │         Core Services Layer                      │          │
│  │  ┌──────────────────┐  ┌────────────────────┐   │          │
│  │  │ MetricsService   │  │ TrendService       │   │          │
│  │  │  - Collection    │  │  - Analysis        │   │          │
│  │  │  - Aggregation   │  │  - Anomaly detect  │   │          │
│  │  │  - Caching       │  │  - Moving avg      │   │          │
│  │  └──────────────────┘  └────────────────────┘   │          │
│  │  ┌──────────────────┐  ┌────────────────────┐   │          │
│  │  │DashboardService  │  │  ReportService     │   │          │
│  │  │  - CRUD ops      │  │  - CSV/JSON/MD     │   │          │
│  │  │  - Widget data   │  │  - Chart gen       │   │          │
│  │  │  - Public share  │  │  - BG generation   │   │          │
│  │  └──────────────────┘  └────────────────────┘   │          │
│  └────────────────────────────────────────────────┘           │
│                                                                 │
│  ┌─────────────────────────────────────────────────┐           │
│  │        Data Aggregation Module                  │           │
│  │  - aggregate_stat_card_data()                   │           │
│  │  - aggregate_timeseries_data()                  │           │
│  │  - aggregate_bar_chart_data()                   │           │
│  │  - aggregate_pie_chart_data()                   │           │
│  └─────────────────────────────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐ ┌────────▼─────────┐ ┌──────▼──────┐
│  PostgreSQL    │ │    Redis         │ │   Celery   │
│  (Time-series) │ │  (Metrics cache) │ │  (Tasks)   │
└────────────────┘ └──────────────────┘ └────────────┘
```

### 2.2 Service Interactions

```
┌─────────────────────┐
│  External Services  │
│  (Feed, Auth, etc)  │
└──────────┬──────────┘
           │
           │ Health endpoints (/health)
           │
           ▼
┌──────────────────────────────────────────────────────┐
│    Analytics Service - Celery Worker                 │
│    ┌─────────────────────────────────────────────┐   │
│    │ collect_metrics_task (every 60s)            │   │
│    │  1. Query service health endpoints          │   │
│    │  2. Extract metric values                   │   │
│    │  3. Store in PostgreSQL                     │   │
│    │  4. Cache in Redis (5 min TTL)              │   │
│    └─────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│    FastAPI API Server (Request/Response)            │
│    ┌─────────────────────────────────────────────┐   │
│    │ Read Endpoints                              │   │
│    │  - /api/v1/analytics/overview               │   │
│    │  - /api/v1/analytics/trends                 │   │
│    │  - /api/v1/analytics/service/{name}         │   │
│    │  - /api/v1/dashboards, /api/v1/reports      │   │
│    └─────────────────────────────────────────────┘   │
│    ┌─────────────────────────────────────────────┐   │
│    │ Write Endpoints                             │   │
│    │  - POST /api/v1/analytics/metrics           │   │
│    │  - POST /api/v1/reports (BG task)           │   │
│    │  - POST /api/v1/dashboards                  │   │
│    └─────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 MetricsService (`app/services/metrics_service.py`)

**Responsibility:** Metric collection, storage, and retrieval

**Key Methods:**

| Method | Purpose | Query Type | Cache |
|--------|---------|-----------|-------|
| `collect_service_metrics()` | Fetch health from service | HTTP GET | None |
| `store_metric()` | Save metric to DB | INSERT | Redis (5 min) |
| `get_overview()` | System-wide snapshot | Multiple SELECTs | Redis (30 sec) |
| `get_service_metrics()` | Service metrics in range | SELECT (indexed) | None |
| `cleanup_old_metrics()` | Remove old data | DELETE (by date) | None |

**Implementation Details:**

```python
# Service initialization with Redis connection
class MetricsService:
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Metric storage includes automatic Redis caching
async def store_metric(self, metric: MetricCreate) -> AnalyticsMetric:
    db_metric = AnalyticsMetric(...)
    self.db.add(db_metric)
    self.db.commit()

    # Cache for 5 minutes
    cache_key = f"metric:{metric.service}:{metric.metric_name}:latest"
    self.redis_client.setex(cache_key, 300, json.dumps({...}))

    return db_metric

# Overview fetches from cache first (30-sec TTL)
async def get_overview(self) -> OverviewResponse:
    cache_key = "analytics:overview"
    cached = self.redis_client.get(cache_key)
    if cached:
        return OverviewResponse(**json.loads(cached))

    # ... calculate from DB and recache
```

**Performance Characteristics:**
- Single metric storage: O(1) disk write, O(1) Redis write
- Overview query: 7 services × 4 metrics = 28 SQL queries (cached)
- Cleanup operation: Single DELETE query with date filter

### 3.2 TrendService (`app/services/trend_service.py`)

**Responsibility:** Trend detection, anomaly detection, moving averages

**Trend Analysis Pipeline:**

```
1. Time Window Aggregation
   └─ Split last N hours into M-minute intervals
   └─ Aggregate values per interval (AVG, SUM, etc.)

2. Trend Direction Calculation
   └─ Linear regression (polyfit degree 1)
   └─ Slope > +0.01 → increasing
   └─ Slope < -0.01 → decreasing
   └─ Otherwise → stable

3. Anomaly Detection (Z-Score Method)
   └─ Calculate mean and std deviation
   └─ Z-score = |value - mean| / std
   └─ Threshold = 2.5 (flag > 2.5 as anomaly)

4. Change Calculation
   └─ Percentage change = (end - start) / start * 100
```

**Key Methods:**

| Method | Algorithm | Complexity |
|--------|-----------|-----------|
| `analyze_trend()` | Aggregation + regression + z-score | O(n) for n data points |
| `_calculate_trend_direction()` | Linear regression | O(n) |
| `_detect_anomalies()` | Z-score calculation | O(n) |
| `_calculate_change_percent()` | Arithmetic | O(1) |
| `get_moving_average()` | Convolution | O(n) |

**Example Trend Response:**

```json
{
  "metric_name": "requests_total",
  "service": "feed-service",
  "trend": "increasing",
  "change_percent": 15.3,
  "data_points": [
    {"timestamp": "2025-10-19T00:00:00", "value": 1200.0},
    {"timestamp": "2025-10-19T01:00:00", "value": 1300.0},
    ...
  ],
  "anomalies": [
    "2025-10-19T08:30:00",
    "2025-10-19T14:15:00"
  ]
}
```

### 3.3 DashboardService (`app/services/dashboard_service.py`)

**Responsibility:** Dashboard CRUD operations, widget data aggregation, user isolation

**Database Operations:**

| Operation | SQL | Auth Check |
|-----------|-----|-----------|
| Create | INSERT | User owns dashboard |
| Read | SELECT | User owns OR public |
| Update | UPDATE | User owns |
| Delete | DELETE | User owns |
| List | SELECT with LIMIT | Filter by user_id OR is_public |

**Widget Data Pipeline:**

```
Dashboard Request
    │
    ├─ Load dashboard config
    ├─ Extract widget list
    │
    └─ For each widget:
        ├─ Get widget type
        ├─ Call aggregation function
        │  ├─ aggregate_stat_card_data()
        │  ├─ aggregate_timeseries_data()
        │  ├─ aggregate_bar_chart_data()
        │  └─ aggregate_pie_chart_data()
        └─ Return formatted data
```

**WebSocket Real-Time Updates:**

```python
@router.websocket("/dashboards/{dashboard_id}/ws")
async def dashboard_websocket(websocket: WebSocket, dashboard_id: int):
    await websocket.accept()

    # Load dashboard
    dashboard = await service.get_dashboard(dashboard_id)
    widgets = dashboard.widgets

    # Continuous update loop (3-second interval)
    while True:
        await asyncio.sleep(3)
        for widget in widgets:
            data = generate_widget_data(widget.type, widget.config, db)
            await websocket.send_json({
                "widget_id": widget.id,
                "data": data
            })
```

### 3.4 ReportService (`app/services/report_service.py`)

**Responsibility:** Report generation (CSV, JSON, Markdown)

**Report Generation Flow:**

```
POST /api/v1/reports
    │
    ├─ Create DB record (status: pending)
    ├─ Return immediately to client
    │
    └─ Background Task:
        ├─ Fetch metrics for date range
        ├─ Organize by service/metric
        ├─ Generate based on format:
        │  ├─ CSV: Write rows (service, metric, timestamp, value)
        │  ├─ JSON: Nested structure (services → metrics → values)
        │  └─ Markdown: Tables per metric
        ├─ Update DB (status: completed, file_path)
        └─ File saved to REPORTS_STORAGE_PATH

Download Report
    ├─ Check status = "completed"
    ├─ Verify user owns report
    └─ Stream file with correct MIME type
```

**Supported Formats:**

| Format | Generator | Use Case | Limitations |
|--------|-----------|----------|-------------|
| CSV | `_generate_csv_report()` | Data analysis, imports | No charts |
| JSON | `_generate_json_report()` | API integration, archival | Nested structure |
| Markdown | `_generate_markdown_report()` | Documentation, readability | Limited to 50 data points per metric |

---

## 4. Data Model & Storage

### 4.1 Database Schema

#### Table: `analytics_metrics` (Time-Series Core)

```sql
CREATE TABLE analytics_metrics (
    id INTEGER PRIMARY KEY,
    service VARCHAR(100) NOT NULL,           -- e.g., "feed-service"
    metric_name VARCHAR(200) NOT NULL,       -- e.g., "requests_total"
    value FLOAT NOT NULL,                    -- metric value
    unit VARCHAR(50),                        -- e.g., "requests", "ms"
    labels JSONB DEFAULT {},                 -- Labels: {"region": "us-west"}
    timestamp DATETIME NOT NULL DEFAULT utcnow,
    created_at DATETIME NOT NULL DEFAULT utcnow,

    INDEX idx_service_metric_timestamp (service, metric_name, timestamp),
    INDEX idx_timestamp (timestamp),
    INDEX idx_service (service),
    INDEX idx_metric_name (metric_name)
);
```

**Indexes Explained:**

| Index | Purpose | Query Pattern |
|-------|---------|---------------|
| `idx_service_metric_timestamp` | **PRIMARY** - Trend queries | `WHERE service=? AND metric_name=? AND timestamp BETWEEN ? AND ?` |
| `idx_timestamp` | Retention cleanup | `WHERE timestamp < ?` (delete old) |
| `idx_service` | Service-level overview | `WHERE service=?` (get all metrics) |
| `idx_metric_name` | Cross-service trends | `WHERE metric_name=?` (compare services) |

**Example Queries:**

```sql
-- Get metric range for trend analysis (INDEXED)
SELECT timestamp, value FROM analytics_metrics
WHERE service = 'feed-service'
  AND metric_name = 'requests_total'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp;

-- Aggregate for overview (INDEXED)
SELECT SUM(value) FROM analytics_metrics
WHERE service = 'feed-service'
  AND metric_name = 'requests_total'
  AND timestamp >= NOW() - INTERVAL '1 hour';

-- Cleanup old metrics (INDEXED)
DELETE FROM analytics_metrics
WHERE timestamp < NOW() - INTERVAL '90 days';
```

#### Table: `analytics_dashboards`

```sql
CREATE TABLE analytics_dashboards (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB DEFAULT {},
    widgets JSONB DEFAULT [],                -- Array of widget configs
    is_public BOOLEAN DEFAULT FALSE,
    refresh_interval INTEGER DEFAULT 60,     -- seconds
    created_at DATETIME DEFAULT utcnow,
    updated_at DATETIME DEFAULT utcnow,

    INDEX idx_user_id (user_id),
    INDEX idx_is_public (is_public)
);
```

**Widget Configuration Example:**

```json
{
  "id": "widget1",
  "type": "line_chart",
  "title": "Request Latency",
  "metric_name": "latency_ms",
  "service": "feed-service",
  "position": {"x": 0, "y": 0, "w": 6, "h": 4},
  "options": {
    "aggregation": "avg",
    "hours": 24,
    "colors": ["#3b82f6"]
  }
}
```

#### Table: `analytics_reports`

```sql
CREATE TABLE analytics_reports (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,                   -- Report parameters
    status VARCHAR(50) DEFAULT 'pending',    -- pending, processing, completed, failed
    format VARCHAR(20) NOT NULL,             -- csv, json, md
    file_path VARCHAR(500),
    file_size_bytes INTEGER,
    error_message TEXT,
    created_at DATETIME DEFAULT utcnow,
    completed_at DATETIME,

    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

**Report Config Example:**

```json
{
  "services": ["feed-service", "content-analysis-service"],
  "metrics": ["requests_total", "latency_ms"],
  "start_date": "2025-10-05T00:00:00Z",
  "end_date": "2025-10-12T00:00:00Z",
  "aggregation": "hourly",
  "include_charts": true
}
```

#### Table: `analytics_alerts`

```sql
CREATE TABLE analytics_alerts (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(200) NOT NULL,
    service VARCHAR(100),
    threshold FLOAT NOT NULL,
    comparison VARCHAR(20) NOT NULL,         -- gt, lt, eq, gte, lte
    severity VARCHAR(20) DEFAULT 'warning',  -- info, warning, critical
    enabled BOOLEAN DEFAULT TRUE,
    notification_channels JSONB DEFAULT [],  -- ["email", "slack"]
    cooldown_minutes INTEGER DEFAULT 30,
    last_triggered_at DATETIME,
    created_at DATETIME DEFAULT utcnow,
    updated_at DATETIME DEFAULT utcnow,

    INDEX idx_user_id (user_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_enabled (enabled)
);
```

### 4.2 Data Types & Storage

**Metric Value Storage:**
- **Type:** PostgreSQL FLOAT (8-byte double precision)
- **Range:** ±1.7976931348623157e+308
- **Precision:** ~15 decimal digits
- **Use Cases:** Counts, latencies, percentages, rates

**JSONB for Flexibility:**
- **Labels:** Dynamic metric tags without schema changes
- **Widget Config:** Extensible UI configuration
- **Report Config:** Query parameters as structured data
- **Benefit:** Evolve schema without migrations

**Timestamps:**
- **Format:** datetime (UTC)
- **Storage:** 8 bytes (datetime with microsecond precision)
- **Index:** Critical for time-range queries

### 4.3 Storage Estimation

**Per Service, Per Month (assuming 60-second collection):**

```
Metrics per collection: 5 (status, requests, errors, latency, active_users)
Collections per day: 1,440 (24h × 60 min)
Records per service per month: 5 × 1,440 × 30 = 216,000

For 7 services:
Records per month: 216,000 × 7 = 1,512,000

Storage per record:
id: 4 bytes
service: 20 bytes (varchar)
metric_name: 30 bytes (varchar)
value: 8 bytes (float)
unit: 10 bytes (varchar)
labels: 50 bytes (JSONB, typically small)
timestamp: 8 bytes
created_at: 8 bytes
Subtotal: ~138 bytes/record

Total: 1,512,000 × 138 = ~208 MB/month
Indexes: ~50 MB additional

Total per month: ~260 MB
Retention: 90 days = ~7.8 GB
With aggregates (365 days): ~28 GB
```

---

## 5. API Contracts

**Total Endpoints:** 32+ endpoints across 7 categories

### 5.1 Analytics Endpoints

#### GET /api/v1/analytics/overview
**Purpose:** System-wide health snapshot
**Auth:** Required (JWT)
**Response Time:** ~100-200ms (cached for 30s)

**Request:**
```http
GET /api/v1/analytics/overview
Authorization: Bearer <jwt_token>
```

**Response (200):**
```json
{
  "timestamp": "2025-10-19T14:30:00Z",
  "services": {
    "feed-service": {
      "total_requests": 15432,
      "error_rate": 0.002,
      "avg_latency_ms": 45.2,
      "active_users": 156
    },
    "auth-service": {
      "total_requests": 8900,
      "error_rate": 0.0,
      "avg_latency_ms": 5.1,
      "active_users": 156
    }
    // ... more services
  },
  "system_health": "healthy",
  "active_alerts": 2,
  "total_users": 156,
  "total_articles": 45230
}
```

**Cache Behavior:**
- First request: Queries DB (28 SQL queries)
- Subsequent requests within 30s: Redis cache hit
- After 30s: Refresh from DB

#### GET /api/v1/analytics/trends
**Purpose:** Trend analysis with anomaly detection
**Auth:** Required
**Query Parameters:**
- `service` (required): Service name
- `metric_name` (required): Metric to analyze
- `hours` (optional): Time range in hours (default: 24, max: 168)
- `interval_minutes` (optional): Aggregation interval (default: 60, min: 5)

**Response Time:** ~200-500ms (depends on data points)

**Request:**
```http
GET /api/v1/analytics/trends?service=feed-service&metric_name=requests_total&hours=24&interval_minutes=60
```

**Response (200):**
```json
{
  "metric_name": "requests_total",
  "service": "feed-service",
  "trend": "increasing",
  "change_percent": 15.3,
  "data_points": [
    {"timestamp": "2025-10-18T14:00:00Z", "value": 600.0},
    {"timestamp": "2025-10-18T15:00:00Z", "value": 650.0},
    // ... 24 hours of data
  ],
  "anomalies": [
    "2025-10-18T20:30:00Z",
    "2025-10-19T02:15:00Z"
  ]
}
```

**Trend Values:**
- `"increasing"`: Positive slope > 0.01
- `"decreasing"`: Negative slope < -0.01
- `"stable"`: Change magnitude < 0.01

#### GET /api/v1/analytics/service/{service_name}
**Purpose:** Service-specific metrics for time range
**Auth:** Required
**Query Parameters:**
- `metric_names` (optional): Filter to specific metrics (CSV)
- `start_date` (optional): ISO format (default: 24h ago)
- `end_date` (optional): ISO format (default: now)

**Response Time:** ~50-150ms (indexed query)

**Request:**
```http
GET /api/v1/analytics/service/feed-service?start_date=2025-10-18T00:00:00Z&end_date=2025-10-19T00:00:00Z&metric_names=requests_total,latency_ms
```

**Response (200):**
```json
[
  {
    "id": 1,
    "service": "feed-service",
    "metric_name": "requests_total",
    "value": 1500.0,
    "unit": "requests",
    "timestamp": "2025-10-18T00:00:00Z",
    "created_at": "2025-10-18T00:00:10Z"
  },
  {
    "id": 2,
    "service": "feed-service",
    "metric_name": "latency_ms",
    "value": 45.2,
    "unit": "ms",
    "timestamp": "2025-10-18T00:00:00Z",
    "created_at": "2025-10-18T00:00:10Z"
  }
  // ... more metrics
]
```

#### POST /api/v1/analytics/metrics
**Purpose:** Store metric (internal service use)
**Auth:** Required
**Rate Limit:** 1000 req/min
**Response Time:** ~5-10ms

**Request:**
```json
{
  "service": "custom-service",
  "metric_name": "process_memory_bytes",
  "value": 524288000,
  "unit": "bytes",
  "labels": {
    "pid": "1234",
    "hostname": "pod-abc-xyz"
  },
  "timestamp": "2025-10-19T14:30:00Z"
}
```

**Response (201):**
```json
{
  "id": 1000001,
  "service": "custom-service",
  "metric_name": "process_memory_bytes",
  "value": 524288000,
  "unit": "bytes",
  "timestamp": "2025-10-19T14:30:00Z",
  "created_at": "2025-10-19T14:30:05Z"
}
```

### 5.2 Dashboard Endpoints

#### POST /api/v1/dashboards
**Purpose:** Create custom dashboard
**Auth:** Required
**Response Time:** ~10-20ms

**Request:**
```json
{
  "name": "System Overview",
  "description": "Real-time system health",
  "is_public": false,
  "refresh_interval": 60,
  "widgets": [
    {
      "id": "w1",
      "type": "stat_card",
      "title": "Total Requests",
      "metric_name": "requests_total",
      "service": "feed-service",
      "position": {"x": 0, "y": 0, "w": 6, "h": 4}
    }
  ]
}
```

**Response (201):**
```json
{
  "id": 1,
  "user_id": "user123",
  "name": "System Overview",
  "description": "Real-time system health",
  "config": {},
  "widgets": [...],
  "is_public": false,
  "refresh_interval": 60,
  "created_at": "2025-10-19T14:30:00Z",
  "updated_at": "2025-10-19T14:30:00Z"
}
```

#### GET /api/v1/dashboards/{dashboard_id}/data
**Purpose:** Dashboard with live widget data
**Auth:** Required (can access own or public)
**Response Time:** ~100-300ms (depends on widgets)

**Request:**
```http
GET /api/v1/dashboards/1/data
```

**Response (200):**
```json
{
  "dashboard": {
    "id": 1,
    "name": "System Overview",
    "widgets": [...]
  },
  "widgets": [
    {
      "id": "w1",
      "type": "stat_card",
      "title": "Total Requests",
      "data": {
        "value": 150000.0,
        "change": 5.2,
        "trend": "up"
      }
    }
  ]
}
```

#### WebSocket /api/v1/dashboards/{dashboard_id}/ws
**Purpose:** Real-time dashboard updates
**Protocol:** WebSocket (continuous connection)
**Update Interval:** 3 seconds

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8107/api/v1/dashboards/1/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`Widget ${message.widget_id} data:`, message.data);
};
```

**Message Format:**
```json
{
  "widget_id": "w1",
  "data": {
    "value": 150000.0,
    "change": 5.2,
    "trend": "up"
  }
}
```

### 5.3 Report Endpoints

#### POST /api/v1/reports
**Purpose:** Create analytics report (background generation)
**Auth:** Required
**Response Time:** ~10-20ms (returns immediately)

**Request:**
```json
{
  "name": "Weekly Performance Report",
  "description": "Performance metrics for the past week",
  "format": "csv",
  "config": {
    "services": ["feed-service", "content-analysis-service"],
    "metrics": ["requests_total", "latency_ms"],
    "start_date": "2025-10-05T00:00:00Z",
    "end_date": "2025-10-12T00:00:00Z",
    "aggregation": "hourly",
    "include_charts": true
  }
}
```

**Response (201):**
```json
{
  "id": 1,
  "user_id": "user123",
  "name": "Weekly Performance Report",
  "description": "Performance metrics for the past week",
  "config": {...},
  "status": "pending",
  "format": "csv",
  "file_path": null,
  "file_size_bytes": null,
  "created_at": "2025-10-19T14:30:00Z",
  "completed_at": null
}
```

**Status Transitions:**
```
pending → processing → completed (or failed)
```

#### GET /api/v1/reports/{report_id}
**Purpose:** Get report status
**Auth:** Required (own report only)

**Response (200):**
```json
{
  "id": 1,
  "status": "completed",
  "file_path": "/tmp/analytics-reports/report_1_20251019_143005.csv",
  "file_size_bytes": 156234,
  "created_at": "2025-10-19T14:30:00Z",
  "completed_at": "2025-10-19T14:32:15Z"
}
```

#### GET /api/v1/reports/{report_id}/download
**Purpose:** Download report file
**Auth:** Required (own report only)
**Content-Type:** text/csv | application/json | text/markdown

**Response (200):**
```
Content-Disposition: attachment; filename="Weekly_Performance_Report.csv"
Content-Type: text/csv

Service,Metric,Timestamp,Value,Unit
feed-service,requests_total,2025-10-05T00:00:00Z,1500,requests
feed-service,latency_ms,2025-10-05T00:00:00Z,45.2,ms
...
```

### 5.4 Monitoring Endpoints

#### GET /api/v1/monitoring/circuit-breakers
**Purpose:** Get circuit breaker status for all services
**Auth:** Required (JWT)
**Response Time:** ~5-10ms

**Response (200):**
```json
{
  "circuit_breakers": {
    "feed-service": {
      "state": "closed",
      "success_count": 1250,
      "failure_count": 3,
      "last_failure": "2025-10-19T14:20:00Z",
      "state_transitions": [
        {
          "from": "half_open",
          "to": "closed",
          "timestamp": "2025-10-19T14:15:00Z"
        }
      ]
    },
    "content-analysis-service": {
      "state": "open",
      "success_count": 0,
      "failure_count": 15,
      "last_failure": "2025-10-19T14:30:00Z"
    }
  },
  "total_services": 7,
  "open_circuits": 1,
  "half_open_circuits": 0
}
```

**Circuit States:**
- `closed`: Service healthy, requests allowed
- `open`: Service failed, requests blocked
- `half_open`: Testing if service recovered

#### GET /api/v1/monitoring/query-performance
**Purpose:** Database query performance statistics
**Auth:** Required (JWT)
**Response Time:** ~10-20ms

**Response (200):**
```json
{
  "total_queries": 15234,
  "unique_patterns": 42,
  "top_queries": [
    {
      "pattern": "SELECT * FROM analytics_metrics WHERE service=? AND metric_name=?",
      "count": 5432,
      "avg_time_ms": 15.3,
      "min_time_ms": 2.1,
      "max_time_ms": 145.2
    }
  ],
  "slow_queries": [
    {
      "query": "SELECT ... FROM analytics_metrics WHERE timestamp ...",
      "execution_time_ms": 245.8,
      "timestamp": "2025-10-19T14:28:30Z"
    }
  ],
  "index_recommendations": [
    {
      "table": "analytics_metrics",
      "recommended_index": "idx_timestamp_service",
      "reason": "Frequent queries on (timestamp, service) columns",
      "estimated_improvement": "30-50% faster"
    }
  ]
}
```

#### POST /api/v1/monitoring/query-performance/reset
**Purpose:** Reset query performance statistics
**Auth:** Required (JWT)
**Response Time:** ~5ms

**Response (200):**
```json
{
  "message": "Query statistics reset successfully"
}
```

#### GET /api/v1/monitoring/websocket
**Purpose:** WebSocket connection statistics
**Auth:** Required (JWT)
**Response Time:** ~5ms

**Response (200):**
```json
{
  "total_connections": 15,
  "connections": [
    {
      "client_id": "ws_user123_1697734800.123",
      "user_id": "user123",
      "connected_at": "2025-10-19T14:20:00Z",
      "last_heartbeat": "2025-10-19T14:30:00Z",
      "subscriptions": ["metrics", "alerts"]
    }
  ]
}
```

#### GET /api/v1/monitoring/health
**Purpose:** Comprehensive system health status
**Auth:** None (public endpoint)
**Response Time:** ~20-50ms

**Response (200):**
```json
{
  "status": "healthy",
  "issues": [],
  "metrics": {
    "circuit_breakers": {
      "total": 7,
      "open": 0,
      "closed": 7
    },
    "database": {
      "total_queries": 15234,
      "unique_patterns": 42,
      "slow_queries": 2
    },
    "websocket": {
      "total_connections": 15
    }
  }
}
```

**Status Values:**
- `healthy`: All systems operational
- `degraded`: Some issues detected (open circuits, slow queries)
- `unhealthy`: Critical issues (3+ open circuits)

### 5.5 Cache Monitoring Endpoints

#### GET /api/v1/cache/stats
**Purpose:** Redis cache performance statistics
**Auth:** None (public endpoint)
**Response Time:** ~10-20ms

**Response (200):**
```json
{
  "status": "healthy",
  "cache_enabled": true,
  "used_memory": "15.2M",
  "used_memory_peak": "18.4M",
  "used_memory_rss": "22.1M",
  "maxmemory": "100M",
  "maxmemory_policy": "allkeys-lru",
  "hit_rate": 67.8,
  "keyspace_hits": 8432,
  "keyspace_misses": 4012,
  "ops_per_sec": 125,
  "total_keys": 142,
  "evicted_keys": 23,
  "expired_keys": 89,
  "connected_clients": 5,
  "blocked_clients": 0,
  "uptime_seconds": 86400,
  "redis_version": "7.0.5"
}
```

**Key Metrics:**
- `hit_rate`: Percentage of cache hits vs misses (0-100)
- `evicted_keys`: Keys removed due to memory pressure
- `maxmemory_policy`: allkeys-lru (least recently used eviction)

**Status Codes:**
- 200: Success
- 503: Cache not available or disabled

#### GET /api/v1/cache/health
**Purpose:** Simple cache availability check
**Auth:** None (public endpoint)
**Response Time:** ~5ms

**Response (200):**
```json
{
  "status": "healthy",
  "message": "Cache is operational",
  "uptime_seconds": 86400
}
```

**Status Codes:**
- 200: Cache is healthy
- 503: Cache unavailable

#### POST /api/v1/cache/clear
**Purpose:** Clear cache keys matching pattern
**Auth:** None (public endpoint)
**Request Body:** Query parameter `pattern` (default: "*")
**Response Time:** ~10-50ms (depends on keys deleted)

**Warning:** Destructive operation - use with caution

**Request:**
```http
POST /api/v1/cache/clear?pattern=feeds:*
```

**Pattern Examples:**
- `*` - Clear all keys (dangerous!)
- `feeds:*` - Clear all feed-related caches
- `feed:items:*` - Clear all feed item caches
- `feed:items:123:*` - Clear caches for specific feed

**Response (200):**
```json
{
  "status": "cleared",
  "pattern": "feeds:*",
  "keys_deleted": 42
}
```

**Status Codes:**
- 200: Cache cleared successfully
- 503: Cache not available

### 5.6 WebSocket Endpoints

#### WebSocket /ws/metrics
**Purpose:** Real-time metrics streaming
**Auth:** Query parameter `token` (JWT)
**Protocol:** WebSocket with JSON messages
**Update Interval:** Server heartbeat every 30 seconds

**Connection:**
```javascript
const token = "eyJhbGc..."; // JWT token
const ws = new WebSocket(`ws://localhost:8107/ws/metrics?token=${token}`);

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
  // Implement reconnection logic with exponential backoff
};
```

**Client → Server Messages:**

```json
// Subscribe to metrics channel
{
  "action": "subscribe",
  "channel": "metrics"
}

// Unsubscribe from channel
{
  "action": "unsubscribe",
  "channel": "metrics"
}

// Get current metrics
{
  "action": "get_metrics"
}

// Ping server (keep-alive)
{
  "action": "ping"
}
```

**Server → Client Messages:**

```json
// Welcome message (on connect)
{
  "type": "connected",
  "client_id": "ws_user123_1697734800.123",
  "timestamp": "2025-10-19T14:30:00Z"
}

// Subscription confirmation
{
  "type": "subscribed",
  "channel": "metrics"
}

// Unsubscription confirmation
{
  "type": "unsubscribed",
  "channel": "metrics"
}

// Metrics data
{
  "type": "metrics",
  "data": {
    "timestamp": "2025-10-19T14:30:00Z",
    "services": { ... }
  },
  "timestamp": "2025-10-19T14:30:00Z"
}

// Periodic metrics update (every 10s to subscribed clients)
{
  "type": "metrics_update",
  "data": { ... },
  "timestamp": "2025-10-19T14:30:10Z"
}

// Heartbeat (every 30s)
{
  "type": "heartbeat",
  "timestamp": "2025-10-19T14:30:30Z"
}

// Pong response
{
  "type": "pong",
  "timestamp": "2025-10-19T14:30:00Z"
}

// Error message
{
  "type": "error",
  "message": "Unknown action: invalid_action"
}
```

**Reconnection Strategy:**
```javascript
let reconnectAttempts = 0;
const maxDelay = 60000; // 60 seconds

function connect() {
  const ws = new WebSocket(`ws://localhost:8107/ws/metrics?token=${token}`);

  ws.onopen = () => {
    reconnectAttempts = 0; // Reset on successful connection
    // Resubscribe to previous channels
  };

  ws.onclose = () => {
    reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), maxDelay);
    console.log(`Reconnecting in ${delay}ms...`);
    setTimeout(connect, delay);
  };
}
```

#### GET /ws/stats
**Purpose:** Get WebSocket connection statistics
**Auth:** None (public endpoint)
**Response Time:** ~5ms

**Response (200):**
```json
{
  "total_connections": 15,
  "connections": [
    {
      "client_id": "ws_user123_1697734800.123",
      "user_id": "user123",
      "connected_at": "2025-10-19T14:20:00Z",
      "last_heartbeat": "2025-10-19T14:30:00Z",
      "subscriptions": ["metrics"]
    }
  ]
}
```

### 5.7 Health Monitoring Endpoints

#### GET /api/v1/health/containers
**Purpose:** Get Docker container health and resource metrics
**Auth:** None (public endpoint)
**Response Time:** ~50-200ms (depends on container count)

**Response (200):**
```json
[
  {
    "name": "analytics-service",
    "status": "running",
    "health": "healthy",
    "cpu_percent": 2.5,
    "memory_percent": 3.8,
    "memory_usage": "156MB",
    "memory_limit": "4GB",
    "pids": 12,
    "network_rx_mb": 45.2,
    "network_tx_mb": 23.1,
    "uptime_seconds": 86400
  },
  {
    "name": "postgres",
    "status": "running",
    "health": null,
    "cpu_percent": 5.2,
    "memory_percent": 8.5,
    "memory_usage": "340MB",
    "memory_limit": "4GB",
    "pids": 45,
    "network_rx_mb": 120.5,
    "network_tx_mb": 95.3,
    "uptime_seconds": 172800
  }
]
```

**Health Values:**
- `healthy`: Container health check passed
- `unhealthy`: Container health check failed
- `null`: No health check configured

**Graceful Degradation:** Returns empty array `[]` if Docker is unavailable

#### GET /api/v1/health/alerts
**Purpose:** Get recent monitoring alerts
**Auth:** None (public endpoint)
**Query Parameters:** `limit` (default: 50, max: 100)
**Response Time:** ~10-30ms

**Deprecated:** This endpoint reads from external monitoring script logs. Will be replaced with Docker event-based alerting.

**Response (200):**
```json
[
  {
    "timestamp": "2025-11-05 20:50:57 UTC",
    "severity": "WARNING",
    "service": "neo4j",
    "message": "HIGH_MEMORY: 9.84% (threshold: 10.0%)"
  },
  {
    "timestamp": "2025-11-05 20:45:32 UTC",
    "severity": "CRITICAL",
    "service": "postgres",
    "message": "HIGH_CPU: 85.2% (threshold: 80.0%)"
  }
]
```

**Severity Levels:**
- `CRITICAL`: Immediate action required
- `WARNING`: Potential issue detected
- `INFO`: Informational message

#### GET /api/v1/health/summary
**Purpose:** Overall system health summary
**Auth:** None (public endpoint)
**Query Parameters:** `include_containers` (default: false)
**Response Time:** ~50-200ms (uses cached data, 30s cache)

**Optimization:** Uses cached container data (shared with `/containers` endpoint), saving 60+ seconds on systems with 40+ containers

**Response (200):**
```json
{
  "total_containers": 40,
  "healthy": 35,
  "unhealthy": 1,
  "no_healthcheck": 4,
  "running": 40,
  "stopped": 0,
  "avg_cpu_percent": 3.2,
  "avg_memory_percent": 5.8,
  "total_pids": 450,
  "recent_critical_alerts": 2,
  "recent_warning_alerts": 5,
  "timestamp": "2025-10-19T14:30:00Z"
}
```

**With `include_containers=true`:**
```json
{
  "total_containers": 40,
  ...,
  "containers": [
    { /* full container objects */ }
  ]
}
```

---

## 6. Metrics Collection Strategy

### 6.1 Collection Pipeline

**Triggered:** Every 60 seconds by Celery Beat (`collect_metrics_task`)

```
Collect Phase:
├─ For each service:
│  ├─ HTTP GET {service_url}/health (5s timeout)
│  ├─ Parse response JSON
│  ├─ Extract metrics (status, requests, errors, latency, users)
│  └─ Handle errors gracefully (store error metric, continue)
│
Store Phase:
├─ Create AnalyticsMetric record per metric
├─ Batch INSERT to DB
├─ Commit transaction (partial success on error)
│
Cache Phase:
├─ Set Redis key: metric:{service}:{metric_name}:latest
└─ TTL: 5 minutes (auto-expire if no update)
```

**Code Flow:**

```python
@celery_app.task(base=DatabaseTask, bind=True)
def collect_metrics_task(self):
    """Collect metrics from all services every 60 seconds"""
    service_urls = {
        "feed-service": settings.FEED_SERVICE_URL,
        # ... 6 more services
    }

    collected_count = 0
    timestamp = datetime.utcnow()

    for service_name, service_url in service_urls.items():
        try:
            # HTTP request to service health endpoint
            response = client.get(f"{service_url}/health", timeout=5.0)

            if response.status_code == 200:
                data = response.json()

                # Store basic health metric
                db_metric = AnalyticsMetric(
                    service=service_name,
                    metric_name="service_status",
                    value=1.0 if data.get("status") == "healthy" else 0.0,
                    timestamp=timestamp
                )
                self.db.add(db_metric)

                # Extract additional metrics if available
                if "metrics" in data:
                    for metric_name, value in data["metrics"].items():
                        if isinstance(value, (int, float)):
                            db_metric = AnalyticsMetric(
                                service=service_name,
                                metric_name=metric_name,
                                value=float(value),
                                timestamp=timestamp
                            )
                            self.db.add(db_metric)

                self.db.commit()

        except Exception as e:
            # Store error metric
            error_metric = AnalyticsMetric(
                service=service_name,
                metric_name="service_status",
                value=0.0,
                labels={"error": str(e)[:100]},
                timestamp=timestamp
            )
            self.db.add(error_metric)
            self.db.commit()

    return {"collected_metrics": collected_count}
```

### 6.2 Metrics Collected Per Service

| Metric Name | Unit | Source | Description |
|-------------|------|--------|-------------|
| `service_status` | binary | Health endpoint | 1.0 = healthy, 0.0 = down |
| `requests_total` | count | Service metrics | Cumulative request count |
| `errors_total` | count | Service metrics | Total error count |
| `latency_ms` | milliseconds | Service metrics | Average response time |
| `active_users` | count | Service metrics | Currently active users |

### 6.3 Health Endpoint Requirements

Each service must expose `/health` endpoint returning:

```json
{
  "status": "healthy",
  "metrics": {
    "requests_total": 15432,
    "errors_total": 10,
    "latency_ms": 45.2,
    "active_users": 156
  }
}
```

**Timeout:** 5 seconds per service
**Failure Handling:** Store error metric, continue with next service
**Retry Logic:** None (single attempt per collection cycle)

---

## 7. Time-Series Data Handling

### 7.1 Time-Series Query Patterns

#### Pattern 1: Recent Metrics (Last 24 hours)

```sql
SELECT timestamp, value
FROM analytics_metrics
WHERE service = 'feed-service'
  AND metric_name = 'requests_total'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
LIMIT 100;
```

**Index Used:** `idx_service_metric_timestamp`
**Expected Rows:** ~1,440 (60-second collection)
**Response Time:** ~5-10ms

#### Pattern 2: Hourly Aggregation

```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    AVG(value) as avg_value,
    MAX(value) as max_value,
    MIN(value) as min_value,
    COUNT(*) as sample_count
FROM analytics_metrics
WHERE service = 'feed-service'
  AND metric_name = 'requests_total'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour;
```

**Index Used:** `idx_service_metric_timestamp`
**Expected Rows:** ~168 (7 days × 24 hours)
**Response Time:** ~20-50ms

#### Pattern 3: Multi-Service Comparison

```sql
SELECT
    service,
    SUM(value) as total_value
FROM analytics_metrics
WHERE metric_name = 'requests_total'
  AND timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY service
ORDER BY total_value DESC;
```

**Index Used:** `idx_metric_name`, then filters by timestamp
**Expected Rows:** ~7 (services)
**Response Time:** ~10-20ms

#### Pattern 4: Data Retention Cleanup

```sql
DELETE FROM analytics_metrics
WHERE timestamp < NOW() - INTERVAL '90 days';
```

**Index Used:** `idx_timestamp`
**Frequency:** Daily (automated via Celery)
**Duration:** ~1-5 seconds (depends on volume)
**Impact:** Minimal (runs off-peak)

### 7.2 Windowing and Aggregation

**Time Window Aggregation for Trends:**

```python
def analyze_trend(service, metric_name, hours=24, interval_minutes=60):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    data_points = []
    current_time = start_time

    while current_time < end_time:
        window_end = current_time + timedelta(minutes=interval_minutes)

        # Aggregate within window
        avg_value = db.query(func.avg(AnalyticsMetric.value)).filter(
            AnalyticsMetric.service == service,
            AnalyticsMetric.metric_name == metric_name,
            AnalyticsMetric.timestamp >= current_time,
            AnalyticsMetric.timestamp < window_end
        ).scalar()

        if avg_value is not None:
            data_points.append(TrendDataPoint(
                timestamp=current_time,
                value=float(avg_value)
            ))

        current_time = window_end

    return data_points
```

**Aggregation Functions Available:**

| Function | Use Case | Example |
|----------|----------|---------|
| `SUM()` | Total traffic, total errors | `requests_total` over period |
| `AVG()` | Average latency, average rate | `latency_ms` trend |
| `MAX()` | Peak values | Peak memory usage |
| `MIN()` | Minimum performance | Minimum latency |
| `COUNT()` | Event frequency | Number of samples |

### 7.3 Data Density and Storage

**Collection Frequency:** Every 60 seconds
**Metrics per Collection:** 5 (status, requests, errors, latency, users)
**Services:** 7

**Daily Data Points:**

```
Metrics per collection: 5
Collections per day: 24 × 60 = 1,440
Data points per day: 5 × 1,440 × 7 = 50,400 rows
Storage per day: 50,400 × 138 bytes = ~7 MB
```

**Query Characteristics:**

| Time Range | Expected Rows | Typical Response | Index |
|------------|---------------|-----------------|-------|
| Last hour | 60 | < 5ms | primary |
| Last 24 hours | 1,440 | 5-10ms | primary |
| Last 7 days | 10,080 | 15-30ms | primary |
| Last 30 days | 43,200 | 50-100ms | primary |
| Last 90 days | 129,600 | 150-300ms | primary |

---

## 8. Query Performance & Indexing

### 8.1 Index Strategy

**Primary Index: `idx_service_metric_timestamp`**

```sql
CREATE INDEX idx_service_metric_timestamp
ON analytics_metrics (service, metric_name, timestamp DESC);
```

**Why DESC on timestamp?**
- Most queries want latest data first
- Reverse order optimization for LIMIT queries
- Trend analysis often needs most recent → oldest

**Example Query Optimization:**

```sql
-- Without index: Full table scan
SELECT * FROM analytics_metrics
WHERE service = 'feed-service'
  AND metric_name = 'requests_total'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC LIMIT 100;

-- With index:
--   1. Index lookup: (service, metric_name, timestamp)
--   2. Return first 100 rows (already ordered DESC)
--   3. Response time: ~5ms
```

### 8.2 Query Performance Baselines

**Baseline Measurements (production):**

| Query Type | Pattern | P50 | P95 | P99 |
|------------|---------|-----|-----|-----|
| Latest metric | Single service, metric, 1 row | 2ms | 5ms | 8ms |
| Hourly trend | 24 points | 5ms | 10ms | 15ms |
| Daily trend | 168 points | 10ms | 20ms | 30ms |
| Overview | 7 services × 4 metrics | 30ms | 100ms | 200ms |
| Report export | 90 days × 7 services × 5 metrics | 500ms | 1s | 2s |

**Cache Impact:**

| Endpoint | Without Cache | With Cache |
|----------|---------------|-----------|
| `/overview` | 100-200ms | 2-5ms |
| `/trends` | 50-150ms | 50-150ms (no cache) |
| `/service/{name}` | 10-30ms | 10-30ms (no cache) |

### 8.3 Performance Tuning

**Connection Pooling:**

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,        # Verify connection before use
    pool_size=10,              # 10 connections in pool
    max_overflow=20            # Allow 20 additional on spike
)
```

**Query Optimization Tips:**

1. **Always use composite index:** `(service, metric_name, timestamp)`
2. **Filter by timestamp:** Reduces rows scanned
3. **Use aggregation:** COUNT, AVG, SUM on indexed columns
4. **Pagination:** LIMIT + OFFSET for large result sets
5. **Batch operations:** Commit every 100 records (not per-record)

---

## 9. Caching Strategy

### 9.1 Redis Cache Layers

**Cache Hierarchy:**

```
Request
  ├─ Cache Layer 1: Latest metric (5 min TTL)
  │  └─ Key: metric:{service}:{metric_name}:latest
  │  └─ Hit Rate: ~80% (stable metrics)
  │
  ├─ Cache Layer 2: Overview (30 sec TTL)
  │  └─ Key: analytics:overview
  │  └─ Hit Rate: ~70% (frequently accessed)
  │
  └─ Cache Layer 3: Dashboard data (no cache)
     └─ Computed on-demand (aggregation functions)
```

**Cache Implementation:**

```python
class MetricsService:
    def __init__(self, db: Session):
        self.redis_client = redis.from_url(settings.REDIS_URL)

    async def get_overview(self):
        cache_key = "analytics:overview"

        # Try cache first
        cached = self.redis_client.get(cache_key)
        if cached:
            return OverviewResponse(**json.loads(cached))

        # Calculate from DB
        overview = await self._calculate_overview()

        # Store in cache (30 seconds)
        self.redis_client.setex(
            cache_key,
            30,
            overview.model_dump_json()
        )

        return overview
```

### 9.2 Cache Invalidation

**Automatic Expiration:**

| Cache Key | TTL | Rationale |
|-----------|-----|-----------|
| `metric:{service}:{metric_name}:latest` | 5 min | New metric every 60s, buffer |
| `analytics:overview` | 30 sec | Frequently requested, low cost |
| Dashboard widget data | None | Computed on-demand |
| Report files | N/A | Stored on disk, not cached |

**Manual Invalidation:**

```python
# When updating a dashboard
async def update_dashboard(...):
    # Update DB
    dashboard = await service.update_dashboard(...)

    # Invalidate related caches
    self.redis_client.delete(f"dashboard:{dashboard_id}:data")
    self.redis_client.delete("analytics:overview")

    return dashboard
```

### 9.3 Cache Warming (Optional)

**Could be implemented for high-traffic scenarios:**

```python
async def warm_cache():
    """Pre-populate cache on startup"""
    service = MetricsService(db)

    # Load overview
    await service.get_overview()

    # Load recent trends for top services
    for service_name in ["feed-service", "content-analysis-service"]:
        await trend_service.analyze_trend(
            service=service_name,
            metric_name="requests_total",
            hours=24
        )
```

---

## 10. Dashboard APIs

### 10.1 Widget Aggregation Functions

Each widget type has a dedicated aggregation function in `data_aggregator.py`:

#### Stat Card (`aggregate_stat_card_data`)

**Purpose:** Single metric with trend indicator
**Use Case:** KPI cards showing current value vs. previous period

**Algorithm:**

```
1. Current period: Last hour
2. Previous period: Hour before that
3. Calculate: Current - Previous
4. Trend: up (+), down (-), or neutral (=)
```

**Example:**

```json
Input widget config:
{
  "metric_name": "requests_total",
  "service": "feed-service",
  "aggregation": "sum"
}

Output:
{
  "value": 150000.0,
  "change": 5.2,
  "trend": "up"
}
```

#### Time Series (`aggregate_timeseries_data`)

**Purpose:** Line/area chart data (24 hours, hourly buckets)
**Use Case:** Trend visualization

**Algorithm:**

```
1. Time window: Last 24 hours
2. Bucket: 1-hour intervals
3. Aggregate: AVG/SUM/MAX/MIN per bucket
4. Fill gaps: Use 0 or last known value
5. Return: Array of {timestamp, value}
```

**Example:**

```json
Output:
{
  "series": [
    {"timestamp": "2025-10-18T14:00:00Z", "value": 6000.0},
    {"timestamp": "2025-10-18T15:00:00Z", "value": 6500.0},
    {"timestamp": "2025-10-18T16:00:00Z", "value": 6200.0},
    ...
  ]
}
```

#### Bar Chart (`aggregate_bar_chart_data`)

**Purpose:** Categorical comparison (services, regions, etc.)
**Use Case:** Service-level comparison

**Algorithm:**

```
1. Group by: Service (or other dimension)
2. Aggregate: SUM/AVG/MAX/MIN
3. Sort: Descending by value
4. Limit: Top 10 (configurable)
5. Return: Array of {name, value}
```

**Example:**

```json
Output:
{
  "series": [
    {"name": "feed-service", "value": 150000.0},
    {"name": "content-analysis-service", "value": 95000.0},
    {"name": "auth-service", "value": 50000.0},
    ...
  ]
}
```

#### Pie Chart (`aggregate_pie_chart_data`)

**Purpose:** Distribution/percentage breakdown
**Use Case:** Service traffic share

**Algorithm:**

```
1. Group by: Service
2. Sum: Total per service
3. Calculate: Percentage of total
4. Assign: Color per category
5. Return: Array of {name, value (%), color}
```

**Example:**

```json
Output:
{
  "series": [
    {"name": "feed-service", "value": 45.5, "color": "#3b82f6"},
    {"name": "content-analysis-service", "value": 28.8, "color": "#10b981"},
    {"name": "auth-service", "value": 15.2, "color": "#f59e0b"},
    ...
  ]
}
```

### 10.2 Widget Configuration Format

**Standard Widget Config:**

```json
{
  "id": "widget_unique_id",
  "type": "line_chart | bar_chart | pie_chart | stat_card | table",
  "title": "Widget Title",
  "metric_name": "metric_to_visualize",
  "service": "optional_service_filter",
  "position": {
    "x": 0,           // Grid X position
    "y": 0,           // Grid Y position
    "w": 6,           // Width (grid units)
    "h": 4            // Height (grid units)
  },
  "options": {
    "aggregation": "sum | avg | max | min | count",
    "hours": 24,
    "group_by": "service",
    "colors": {
      "feed-service": "#3b82f6"
    }
  }
}
```

### 10.3 Real-Time Updates via WebSocket

**WebSocket Endpoint:** `/api/v1/dashboards/{dashboard_id}/ws`

**Connection Flow:**

```
Client connects
    ↓
Server loads dashboard config
    ↓
Server extracts widgets
    ↓
For each widget: Send initial data
    ↓
Loop every 3 seconds:
    ├─ Recalculate widget data (aggregation)
    ├─ Send updated JSON to client
    └─ Repeat until disconnect
```

**Client Implementation:**

```javascript
const ws = new WebSocket('ws://localhost:8107/api/v1/dashboards/1/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  // update.widget_id: "widget1"
  // update.data: {aggregated widget data}

  // Update UI (e.g., React state)
  setWidgetData(update.widget_id, update.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Dashboard connection closed');
  // Attempt reconnect after 5 seconds
  setTimeout(() => connectDashboard(), 5000);
};
```

**Update Interval:** 3 seconds (hardcoded)

---

## 11. Report Generation

### 11.1 Report Generation Flow

**Three-Phase Process:**

```
Phase 1: Create Report Record (Immediate)
├─ Store config in DB
├─ Set status = "pending"
├─ Return report ID to client
└─ Response time: ~10ms

Phase 2: Background Generation (Via Celery)
├─ Status → "processing"
├─ Fetch metrics for date range (can be slow)
├─ Generate file (CSV/JSON/Markdown)
├─ Write to disk
├─ Update DB (status, file_path, file_size)
└─ Duration: 5-60 seconds

Phase 3: Download (On Demand)
├─ Check status = "completed"
├─ Stream file to client
├─ Set correct MIME type
└─ Response time: <10ms + file transfer
```

### 11.2 Report Formats

#### CSV Format

**File Structure:**

```csv
Service,Metric,Timestamp,Value,Unit
feed-service,requests_total,2025-10-05T00:00:00Z,1500,requests
feed-service,latency_ms,2025-10-05T00:00:00Z,45.2,ms
content-analysis-service,requests_total,2025-10-05T00:00:00Z,800,requests
...
```

**Generator Code:**

```python
async def _generate_csv_report(self, report: AnalyticsReport, data: Dict) -> str:
    file_path = os.path.join(
        settings.REPORTS_STORAGE_PATH,
        f"report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Service', 'Metric', 'Timestamp', 'Value', 'Unit'])

        for service, metrics in data["services"].items():
            for metric_name, values in metrics.items():
                for value_data in values:
                    writer.writerow([
                        service,
                        metric_name,
                        value_data["timestamp"],
                        value_data["value"],
                        value_data.get("unit", "")
                    ])

    return file_path
```

**Use Case:** Data analysis, Excel imports, spreadsheet tools

#### JSON Format

**File Structure:**

```json
{
  "report_id": 1,
  "name": "Weekly Report",
  "generated_at": "2025-10-19T14:32:15Z",
  "config": {
    "services": ["feed-service"],
    "metrics": ["requests_total"],
    "start_date": "2025-10-05T00:00:00Z",
    "end_date": "2025-10-12T00:00:00Z"
  },
  "data": {
    "services": {
      "feed-service": {
        "requests_total": [
          {
            "timestamp": "2025-10-05T00:00:00Z",
            "value": 1500.0,
            "unit": "requests"
          },
          ...
        ]
      }
    }
  }
}
```

**Use Case:** API integration, archival, programmatic access

#### Markdown Format

**File Structure:**

```markdown
# Weekly Performance Report

_Performance metrics for the past week_

**Generated:** 2025-10-19 14:32:15 UTC

**Report ID:** 1

## Configuration

- **Time Range:** 2025-10-05T00:00:00Z to 2025-10-12T00:00:00Z
- **Aggregation:** hourly
- **Services:** feed-service, content-analysis-service
- **Metrics:** requests_total, latency_ms

## Metrics Data

### feed-service

#### requests_total

| Timestamp | Value | Unit |
|-----------|-------|------|
| 2025-10-05T00:00:00Z | 1500 | requests |
| 2025-10-05T01:00:00Z | 1600 | requests |
| ... | ... | ... |

---

_Generated by Analytics Service_
```

**Use Case:** Documentation, presentations, readability

### 11.3 Report Parameters

**Supported Aggregations:**

| Value | SQL | Example |
|-------|-----|---------|
| `"hourly"` | `DATE_TRUNC('hour', timestamp)` | 24 data points for 24 hours |
| `"daily"` | `DATE_TRUNC('day', timestamp)` | 7 data points for 7 days |
| `"weekly"` | `DATE_TRUNC('week', timestamp)` | 4 data points for 4 weeks |

**Date Format:** ISO 8601 (UTC)
**Example:** `"2025-10-05T00:00:00Z"`

**Data Limits:**

- **Maximum service list:** 20 services
- **Maximum metrics:** 50 metrics
- **Maximum date range:** 365 days
- **Maximum rows:** 50,000 (limited in Markdown)

---

## 12. Trend Analysis Engine

### 12.1 Trend Direction Calculation

**Linear Regression Approach:**

```python
def _calculate_trend_direction(self, values: List[float]) -> str:
    """Calculate overall trend using linear regression"""
    if len(values) < 2:
        return "stable"

    # Fit line to data points: y = mx + b
    x = np.arange(len(values))  # Time points: 0, 1, 2, ...
    slope = np.polyfit(x, values, 1)[0]  # Degree 1 = linear

    # Slope interpretation:
    # Slope > +0.01: Positive trend (increasing)
    # Slope < -0.01: Negative trend (decreasing)
    # Else: Stable

    if abs(slope) < 0.01:
        return "stable"
    elif slope > 0:
        return "increasing"
    else:
        return "decreasing"
```

**Mathematical Basis:**

```
Linear regression finds best-fit line: y = mx + b

Example with 5 data points:
x: [0, 1, 2, 3, 4]  (time)
y: [100, 110, 120, 125, 130]  (metric values)

Using numpy.polyfit(x, y, 1):
slope (m) = 7.5
intercept (b) = 100

Result: y = 7.5x + 100
Trend: increasing (slope > 0.01)
```

### 12.2 Anomaly Detection (Z-Score Method)

**Algorithm:**

```python
def _detect_anomalies(self, data_points: List[TrendDataPoint], threshold: float = 2.5):
    """Detect anomalies using z-score method"""
    values = np.array([dp.value for dp in data_points])

    # Step 1: Calculate statistics
    mean = np.mean(values)
    std = np.std(values)

    # Step 2: Calculate z-scores
    z_scores = np.abs((values - mean) / std)

    # Step 3: Find anomalies (z-score > threshold)
    anomaly_indices = np.where(z_scores > threshold)[0]

    # Step 4: Return timestamps of anomalies
    return [data_points[i].timestamp for i in anomaly_indices]
```

**Z-Score Interpretation:**

```
Z-score represents standard deviations from mean

Example:
Mean = 100, Std = 10
Value = 130
Z-score = |130 - 100| / 10 = 3.0

Threshold = 2.5: Flag if z > 2.5
Result: 3.0 > 2.5 → Anomaly detected
```

**Sensitivity Tuning:**

| Threshold | Sensitivity | Typical Use |
|-----------|-------------|------------|
| 1.0 | Very high (sensitive) | Strict monitoring |
| 1.5 | High | Normal operations |
| 2.0 | Moderate | Balanced |
| 2.5 | Low (default) | Production |
| 3.0 | Very low | Rare events only |

### 12.3 Moving Average

**Purpose:** Smooth noisy time-series data

```python
async def get_moving_average(
    self,
    service: str,
    metric_name: str,
    window_size: int = 5,  # Points to average
    hours: int = 24
):
    """Calculate moving average for smoothing"""
    # Get raw trend
    trend_data = await self.analyze_trend(service, metric_name, hours)

    if len(trend_data.data_points) < window_size:
        return trend_data.data_points

    # Apply convolution (moving average kernel)
    values = np.array([dp.value for dp in trend_data.data_points])
    kernel = np.ones(window_size) / window_size
    moving_avg = np.convolve(values, kernel, mode='valid')

    # Rebuild with adjusted timestamps
    adjusted_points = []
    for i, avg_value in enumerate(moving_avg):
        idx = i + window_size - 1
        adjusted_points.append(TrendDataPoint(
            timestamp=trend_data.data_points[idx].timestamp,
            value=float(avg_value)
        ))

    return adjusted_points
```

**Example:**

```
Raw values:  [100, 110, 105, 120, 115, 125]
Window = 3

MA output:  [105, 111.7, 113.3]
(Average of [100,110,105], then [110,105,120], etc.)

Result: Smoother trend, reduces noise
```

### 12.4 Percentage Change Calculation

```python
def _calculate_change_percent(self, values: List[float]) -> float:
    """Percentage change from start to end"""
    if len(values) < 2 or values[0] == 0:
        return 0.0

    return ((values[-1] - values[0]) / values[0]) * 100
```

**Formula:**
```
change_percent = (end_value - start_value) / start_value * 100

Example:
Start: 1000 requests
End: 1150 requests
Change: (1150 - 1000) / 1000 * 100 = 15%
```

---

## 13. Celery Workers & Background Tasks

### 13.1 Task Definitions

**File:** `app/workers/tasks.py`

#### Task 1: `collect_metrics_task`

**Schedule:** Every 60 seconds (via Celery Beat)
**Execution Time:** ~2-5 seconds
**Purpose:** Collect metrics from all services

```python
@celery_app.task(base=DatabaseTask, bind=True)
def collect_metrics_task(self):
    """Collect metrics from all services"""
    # For each service:
    #   1. HTTP GET /health
    #   2. Extract metrics
    #   3. Store in AnalyticsMetric table
    #   4. Update Redis cache

    return {"collected_metrics": count}
```

**Reliability:**
- Partial success: If 1 service fails, others still collected
- Error handling: Store error metrics
- No retry: Missed collections skipped (not critical)

#### Task 2: `cleanup_old_metrics_task`

**Schedule:** Daily at 2 AM (via Celery Beat)
**Execution Time:** ~1-5 seconds (depends on volume)
**Purpose:** Remove metrics older than retention period

```python
@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_old_metrics_task(self):
    """Remove metrics older than retention period"""
    retention_date = datetime.utcnow() - timedelta(
        days=settings.METRICS_RETENTION_DAYS  # 90 days
    )

    deleted = self.db.query(AnalyticsMetric).filter(
        AnalyticsMetric.timestamp < retention_date
    ).delete()

    self.db.commit()
    return {"deleted_metrics": deleted}
```

**Storage Impact:**
- ~7 GB of data deleted every 90 days
- Cleanup interval: Daily
- Rows deleted per day: ~50,400 (one month's data)

#### Task 3: `generate_report_task`

**Triggered:** On-demand (POST /api/v1/reports)
**Execution Time:** ~5-60 seconds
**Purpose:** Generate report file in background

```python
@celery_app.task(base=DatabaseTask, bind=True)
def generate_report_task(self, report_id: int):
    """Generate analytics report"""
    from app.services.report_service import ReportService

    report_service = ReportService(self.db)
    report = report_service.generate_report(report_id)

    return {
        "report_id": report.id,
        "status": report.status,
        "file_path": report.file_path
    }
```

### 13.2 Celery Configuration

**File:** `app/workers/celery_app.py`

```python
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "analytics-service",
    broker=settings.CELERY_BROKER_URL,        # Redis
    backend=settings.CELERY_RESULT_BACKEND     # Redis
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000
)

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    'collect-metrics': {
        'task': 'app.workers.tasks.collect_metrics_task',
        'schedule': 60.0,  # Every 60 seconds
    },
    'cleanup-old-metrics': {
        'task': 'app.workers.tasks.cleanup_old_metrics_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

### 13.3 Running Workers

**Main Worker (Executes Tasks):**

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

**Beat Scheduler (Triggers Periodic Tasks):**

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

**Monitoring UI (Flower):**

```bash
celery -A app.workers.celery_app flower --port=5555
# Access at http://localhost:5555
```

**Verify Tasks Running:**

```bash
# Check active tasks
celery -A app.workers.celery_app inspect active

# Check scheduled tasks
celery -A app.workers.celery_app inspect scheduled

# Check worker stats
celery -A app.workers.celery_app inspect stats
```

---

## 14. Data Retention Policies

### 14.1 Retention Tiers

**Two-Tier Retention Strategy:**

```
Tier 1: Granular Metrics (90 days)
├─ Full resolution (60-second intervals)
├─ All 5 metrics per service
├─ Suitable for: Trend analysis, debugging
└─ Storage: ~7.8 GB

Tier 2: Aggregated Metrics (365 days)
├─ Hourly aggregates (AVG, MAX, MIN)
├─ Summary metrics only (e.g., daily totals)
├─ Suitable for: Long-term trends, capacity planning
└─ Storage: ~28 GB (estimated)
```

**Current Implementation:** Only Tier 1 (90 days)

**Recommended Enhancement:**

```sql
-- Create aggregation table
CREATE TABLE analytics_metrics_hourly (
    id INTEGER PRIMARY KEY,
    service VARCHAR(100) NOT NULL,
    metric_name VARCHAR(200) NOT NULL,
    hour DATETIME NOT NULL,
    avg_value FLOAT,
    max_value FLOAT,
    min_value FLOAT,
    sample_count INTEGER,

    INDEX idx_service_metric_hour (service, metric_name, hour)
);

-- Hourly aggregation job (Celery task)
@celery_app.task
def aggregate_metrics_hourly():
    # Aggregate previous hour's metrics
    hour_start = (datetime.utcnow() - timedelta(hours=1)).replace(minute=0, second=0)

    for service in get_services():
        for metric in get_metrics():
            # Query previous hour
            data = db.query(AnalyticsMetric).filter(
                AnalyticsMetric.service == service,
                AnalyticsMetric.metric_name == metric,
                AnalyticsMetric.timestamp >= hour_start,
                AnalyticsMetric.timestamp < hour_start + timedelta(hours=1)
            )

            # Store aggregate
            db.add(AnalyticsMetricHourly(
                service=service,
                metric_name=metric,
                hour=hour_start,
                avg_value=db.query(func.avg(data.value)).scalar(),
                max_value=db.query(func.max(data.value)).scalar(),
                min_value=db.query(func.min(data.value)).scalar(),
                sample_count=data.count()
            ))
```

### 14.2 Cleanup Operations

**Automatic Cleanup (Daily):**

```sql
DELETE FROM analytics_metrics
WHERE timestamp < NOW() - INTERVAL '90 days';
```

**Scheduled:** 2 AM UTC (configurable)
**Duration:** ~1-5 seconds
**Data Deleted:** ~50,400 rows (1 month of data)

**Verification:**

```bash
# Check retention date
SELECT MIN(timestamp) FROM analytics_metrics;

# Estimate cleanup impact
SELECT COUNT(*) FROM analytics_metrics
WHERE timestamp < NOW() - INTERVAL '90 days';
```

### 14.3 Data Archival (Optional)

**For compliance/audit:**

```python
async def archive_old_metrics(days_old: int = 365):
    """Archive metrics to cold storage"""
    archive_date = datetime.utcnow() - timedelta(days=days_old)

    # Export to CSV
    metrics = db.query(AnalyticsMetric).filter(
        AnalyticsMetric.timestamp < archive_date
    ).all()

    # Write to S3/archive
    archive_path = f"s3://analytics-archive/{archive_date.year}/{archive_date.month}/"
    write_to_s3(archive_path, metrics)

    # Delete from active DB
    db.query(AnalyticsMetric).filter(
        AnalyticsMetric.timestamp < archive_date
    ).delete()
```

---

## 15. MCP Integration

The Analytics Service is accessible via the **MCP Core Server** (Port 9006), providing programmatic access to all analytics, monitoring, and dashboard functionalities through the Model Context Protocol.

### 15.1 Available MCP Tools

#### Analytics Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `core:analytics_get_metrics` | Get metrics for a specific service | `service_name` (str), `metric_type` (str), `hours` (int, default: 24) |
| `core:analytics_get_overview` | Get system-wide analytics overview | `hours` (int, default: 24) |
| `core:analytics_get_service` | Get detailed analytics for a service | `service_name` (str) |
| `core:analytics_get_trends` | Get trend analysis for metrics | `service_name` (str), `metric_type` (str), `days` (int, default: 7) |

#### Dashboard Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `core:dashboards_list` | List all available dashboards | None |
| `core:dashboards_get` | Get dashboard configuration | `dashboard_id` (str) |
| `core:dashboards_get_data` | Get dashboard with widget data | `dashboard_id` (str) |

#### Report Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `core:reports_list` | List all generated reports | `limit` (int, default: 50), `offset` (int, default: 0) |
| `core:reports_get` | Get a specific report | `report_id` (str) |

#### Monitoring Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `core:monitoring_get_health` | Get health status of all services | None |
| `core:monitoring_get_circuit_breakers` | Get circuit breaker states | None |
| `core:monitoring_get_query_performance` | Get database query performance stats | `hours` (int, default: 1) |

#### Health Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `core:health_get_summary` | Get system health summary | None |
| `core:health_get_containers` | Get Docker container health | None |
| `core:health_get_alerts` | Get active health alerts | `severity` (str, optional) |

#### Cache Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `core:cache_get_stats` | Get Redis cache statistics | None |
| `core:cache_get_health` | Get cache health status | None |
| `core:cache_clear` | Clear cache (admin only) | `pattern` (str, optional) |

### 15.2 MCP Server Configuration

**Server:** MCP Core Server
**Port:** 9006
**Base URL:** `http://{SERVER_IP}:9006`
**Tool Prefix:** `core:`

### 15.3 Example Usage

#### Get Service Analytics
```json
{
  "tool": "core:analytics_get_service",
  "parameters": {
    "service_name": "feed-service"
  }
}
```

**Response:**
```json
{
  "service": "feed-service",
  "metrics": {
    "requests_total": 125432,
    "errors_total": 12,
    "error_rate": 0.0096,
    "avg_latency_ms": 45.2,
    "p99_latency_ms": 120.5
  },
  "health": "healthy",
  "last_updated": "2025-12-22T10:30:00Z"
}
```

#### Get System Trends
```json
{
  "tool": "core:analytics_get_trends",
  "parameters": {
    "service_name": "analytics-service",
    "metric_type": "latency",
    "days": 7
  }
}
```

**Response:**
```json
{
  "service": "analytics-service",
  "metric": "latency",
  "period_days": 7,
  "trend": "stable",
  "anomalies_detected": 0,
  "data_points": [
    {"timestamp": "2025-12-15T00:00:00Z", "value": 42.5},
    {"timestamp": "2025-12-16T00:00:00Z", "value": 44.1}
  ]
}
```

#### List Dashboards
```json
{
  "tool": "core:dashboards_list",
  "parameters": {}
}
```

**Response:**
```json
{
  "dashboards": [
    {
      "id": "system-overview",
      "name": "System Overview",
      "is_public": true,
      "widgets_count": 8
    },
    {
      "id": "feed-metrics",
      "name": "Feed Service Metrics",
      "is_public": false,
      "widgets_count": 6
    }
  ],
  "total": 2
}
```

### 15.4 Integration with Claude Desktop

For Claude Desktop integration, use the unified MCP gateway:

```json
{
  "mcpServers": {
    "news-microservices": {
      "command": "node",
      "args": ["C:\\mcp-unified-gateway.js"],
      "env": {
        "MCP_SERVER_IP": "localhost"
      }
    }
  }
}
```

All analytics tools are then accessible with the `core:` prefix.

---

## 16. Integration Points

### 16.1 Service Health Endpoints

**Required from each service:**

```http
GET {service_url}/health HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "metrics": {
    "requests_total": 15432,
    "errors_total": 10,
    "latency_ms": 45.2,
    "active_users": 156
  }
}
```

**Service URLs (from config):**

| Service | URL | Port |
|---------|-----|------|
| auth-service | http://auth-service:8000 | 8000 |
| feed-service | http://feed-service:8001 | 8001 |
| content-analysis-service | http://content-analysis-service:8002 | 8002 |
| research-service | http://research-service:8003 | 8003 |
| osint-service | http://osint-service:8004 | 8004 |
| notification-service | http://notification-service:8005 | 8005 |
| search-service | http://search-service:8006 | 8006 |

### 16.2 Publishing Custom Metrics

**From any service to Analytics:**

```python
import httpx

async def publish_metric(
    service_name: str,
    metric_name: str,
    value: float,
    unit: str = None,
    labels: dict = None
):
    """Publish custom metric to analytics service"""

    metric_data = {
        "service": service_name,
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "labels": labels or {}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://analytics-service:8007/api/v1/analytics/metrics",
            json=metric_data,
            headers={"Authorization": f"Bearer {jwt_token}"}
        )

        return response.json()

# Usage
await publish_metric(
    service_name="feed-service",
    metric_name="articles_processed",
    value=250,
    unit="articles",
    labels={"source": "rss", "region": "us-west"}
)
```

### 16.3 Authentication Integration

**Dependency:** auth-service for JWT validation

```python
from app.core.auth import get_current_user

@router.get("/api/v1/analytics/overview")
async def get_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Requires valid JWT token"""
    # current_user: {"user_id": "user123", "roles": ["admin"]}
    ...
```

**Token Format:** JWT (HS256)
**Header:** `Authorization: Bearer <token>`
**Validation:** Performed by `get_current_user()` dependency

---

## 17. Performance Characteristics

### 17.1 Response Time Baselines

**Endpoint Performance:**

| Endpoint | Cached | P50 | P95 | P99 | Notes |
|----------|--------|-----|-----|-----|-------|
| `/overview` | Yes | 3ms | 8ms | 15ms | 28 SQL queries |
| `/trends` | No | 50ms | 150ms | 250ms | Depends on data volume |
| `/service/{name}` | No | 15ms | 40ms | 80ms | Indexed query |
| `/dashboards/{id}/data` | No | 100ms | 300ms | 500ms | Multiple aggregations |
| `/reports` (POST) | N/A | 10ms | 20ms | 50ms | Immediate response |
| `/reports/{id}/download` | No | 5ms | 10ms | 20ms | File transfer time separate |

### 17.2 Concurrency

**Connection Limits:**

```python
engine = create_engine(
    database_url,
    pool_size=10,           # Steady-state connections
    max_overflow=20         # Peak connections
)
# Total: 30 concurrent database connections
```

**WebSocket Connections:**

- **Per Dashboard:** ~50-100 concurrent users
- **Total:** 100+ connections (depends on infrastructure)
- **Update Interval:** 3 seconds per user
- **Network Impact:** Low (small JSON updates)

**Celery Task Capacity:**

- **Workers:** 1 (can scale to multiple)
- **Concurrent Tasks:** ~5-10 per worker
- **Queue:** Redis (unlimited capacity)

### 17.3 Memory Usage

**Service Memory Profile:**

```
Base Process: ~80 MB
  ├─ Python runtime: ~30 MB
  ├─ FastAPI framework: ~20 MB
  ├─ SQLAlchemy: ~20 MB
  └─ Other: ~10 MB

Per WebSocket Connection: ~100 KB
  ├─ Connection buffer: ~50 KB
  ├─ State data: ~30 KB
  └─ Misc: ~20 KB

Per Active Dashboard Session: ~500 KB
  ├─ Widget configurations: ~200 KB
  ├─ Cached aggregations: ~200 KB
  └─ State: ~100 KB

Total Estimate (100 users): ~130 MB
```

### 17.4 Database Load

**Typical Load Pattern:**

```
Off-peak (2 AM - 6 AM):
├─ Metric collection: 1 query/min
├─ Cleanup job: 1 query (daily)
└─ Total: ~5-10 queries/min

Peak (9 AM - 5 PM):
├─ Dashboard views: 10-20 QPS
├─ Metric collection: 10 queries/min
├─ Report generation: 2-5 large queries
└─ Total: ~15-30 QPS

Breakdown:
├─ SELECTs: ~90%
├─ INSERTs: ~9%
└─ DELETEs: ~1%
```

---

## 18. Security & Authorization

### 18.1 Authentication

**Method:** JWT (JSON Web Tokens)
**Algorithm:** HS256 (HMAC-SHA256)
**Secret:** Environment variable `JWT_SECRET_KEY`

**Token Flow:**

```
1. User logs in to auth-service
2. Receives JWT token
3. Includes in Authorization header: "Bearer <token>"
4. Analytics verifies signature using JWT_SECRET_KEY
5. Extracts user_id from token claims
```

### 18.2 Authorization

**Access Control Rules:**

| Resource | Owner | Public | Others |
|----------|-------|--------|--------|
| Dashboard | Read, Write, Delete | Read (if `is_public=true`) | None |
| Report | Read, Download | None | None |
| Metrics | Read | Read (overview only) | None |

**Dashboard Privacy:**

```python
# Public Dashboard
{
  "id": 1,
  "user_id": "alice",
  "name": "System Status",
  "is_public": true
}

# Anyone can read (no user_id check)
GET /api/v1/dashboards/1

# Private Dashboard
{
  "id": 2,
  "user_id": "bob",
  "name": "Performance Debug",
  "is_public": false
}

# Only Bob can read
GET /api/v1/dashboards/2
# Requires user_id == "bob"
```

### 18.3 Data Isolation

**Per-User Isolation:**

```python
# In database queries
query = db.query(AnalyticsReport).filter(
    AnalyticsReport.user_id == current_user["user_id"]
)

# User can only access their reports
```

**Example:**
- Alice creates report with ID 1
- Bob tries: GET /api/v1/reports/1
- Result: 404 (not found) - appears as if doesn't exist

---

## 19. Common Issues & Troubleshooting

### 19.1 Slow Trend Queries

**Symptom:** `/api/v1/analytics/trends` takes > 1 second

**Root Causes:**

```
1. Missing index: idx_service_metric_timestamp
   Fix: Verify index exists
   SELECT * FROM pg_indexes
   WHERE tablename = 'analytics_metrics'

2. Stale statistics: Query planner doesn't know data distribution
   Fix: Run ANALYZE
   ANALYZE analytics_metrics;

3. Large data range: Querying > 90 days
   Fix: Limit time range to 30 days max
   OR implement aggregated table

4. Slow database: CPU/disk contention
   Fix: Check database metrics (iostat, top)
```

**Quick Diagnostics:**

```sql
-- Check index usage
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE tablename = 'analytics_metrics'
ORDER BY idx_scan DESC;

-- Check query plan
EXPLAIN ANALYZE
SELECT timestamp, value FROM analytics_metrics
WHERE service = 'feed-service'
  AND metric_name = 'requests_total'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

### 19.2 WebSocket Disconnections

**Symptom:** Dashboard updates stop after 5-10 minutes

**Root Causes:**

```
1. Network timeout: Proxy/firewall closing idle connections
   Fix: Add periodic ping/pong frames
   Heartbeat interval: 30 seconds

2. Server restart: Service redeployed
   Fix: Implement client reconnect logic
   Retry delay: 5 seconds with exponential backoff

3. Memory leak: WebSocket handler not closing cleanly
   Fix: Ensure cleanup in finally block
   Monitor: watch -n 5 'ps aux | grep python'

4. Too many connections: Resource exhaustion
   Fix: Limit concurrent connections
   Monitor: netstat -an | grep ESTABLISHED | wc -l
```

**Client Recovery Code:**

```javascript
function connectDashboard() {
  const ws = new WebSocket('ws://localhost:8107/api/v1/dashboards/1/ws');

  ws.onopen = () => {
    console.log('Connected to dashboard');
    reconnectAttempts = 0;  // Reset on success
  };

  ws.onerror = () => {
    console.error('WebSocket error');
    attemptReconnect();
  };

  ws.onclose = () => {
    console.log('Connection closed');
    attemptReconnect();
  };
}

function attemptReconnect() {
  reconnectAttempts++;
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
  setTimeout(connectDashboard, delay);
}
```

### 19.3 Celery Tasks Not Running

**Symptom:** Metrics not collected, reports stuck in "pending"

**Diagnostics:**

```bash
# Check Beat scheduler is running
ps aux | grep celery | grep beat

# Check Worker is running
ps aux | grep celery | grep worker

# View task queue
celery -A app.workers.celery_app inspect active
celery -A app.workers.celery_app inspect scheduled

# Check Redis connectivity
redis-cli ping
# Expected: PONG

# Check celery_app configuration
# Verify broker URL in app/workers/celery_app.py
```

**Common Fixes:**

```bash
# Kill stuck processes
pkill -f 'celery.*beat'
pkill -f 'celery.*worker'

# Restart services
celery -A app.workers.celery_app beat --loglevel=info &
celery -A app.workers.celery_app worker --loglevel=info &

# Monitor
celery -A app.workers.celery_app flower --port=5555
# Open http://localhost:5555
```

### 19.4 Out of Memory Errors

**Symptom:** Service crashes with OOM, heap size errors

**Root Causes:**

```
1. Large query result: Fetching too many rows at once
   Fix: Add LIMIT to queries
   Example: SELECT ... LIMIT 10000

2. Unbounded WebSocket: Memory leaks in ws handlers
   Fix: Ensure all connections close cleanly
   Monitor: watch -n 1 'lsof -p $(pidof python)' | wc -l

3. Redis memory: Metrics cache grows unbounded
   Fix: Set TTL on keys (already done: 5 min)
   Monitor: redis-cli INFO memory

4. Report generation: Loading entire dataset
   Fix: Stream instead of load-all
   Limit: MAX_REPORT_SIZE_MB=50 (in config)
```

**Memory Monitoring:**

```bash
# Watch service memory
watch -n 1 'ps aux | grep [a]nalytics-service | awk "{print \$6}"'

# Check total memory
free -h

# Redis memory
redis-cli INFO memory | grep used_memory_human
```

---

## 20. Development Workflow

### 20.1 Local Setup

```bash
# 1. Start dependencies
docker-compose up -d postgres redis rabbitmq

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create database tables
alembic upgrade head

# 4. Start service
uvicorn app.main:app --reload --port 8107

# 5. Start Celery worker (new terminal)
celery -A app.workers.celery_app worker --loglevel=info

# 6. Start Celery Beat (new terminal)
celery -A app.workers.celery_app beat --loglevel=info

# 7. Access service
http://localhost:8107/docs
```

### 20.2 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_analytics.py::test_get_overview -v

# Watch mode
ptw tests/
```

### 20.3 Adding New Metrics

**Steps to add custom metric:**

1. **Service publishes metric** (e.g., feed-service):

```python
# In feed-service
await analytics_client.publish_metric(
    service_name="feed-service",
    metric_name="articles_fetched",
    value=250,
    unit="articles"
)
```

2. **Analytics collects via /health endpoint:**

```json
{
  "status": "healthy",
  "metrics": {
    "articles_fetched": 250
  }
}
```

3. **Verify collection:**

```bash
curl http://localhost:8107/api/v1/analytics/service/feed-service
```

4. **Add to dashboard widget:**

```json
{
  "type": "stat_card",
  "metric_name": "articles_fetched",
  "service": "feed-service"
}
```

---

## 21. Appendix: API Examples

### 21.1 Complete Flow: Create and View Dashboard

```bash
# 1. Create dashboard
curl -X POST http://localhost:8107/api/v1/dashboards \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Dashboard",
    "widgets": [
      {
        "id": "w1",
        "type": "stat_card",
        "metric_name": "requests_total",
        "service": "feed-service"
      }
    ]
  }'

# Response:
# {
#   "id": 1,
#   "user_id": "user123",
#   "name": "My Dashboard",
#   ...
# }

# 2. Get dashboard with live data
curl http://localhost:8107/api/v1/dashboards/1/data \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "dashboard": {...},
#   "widgets": [
#     {
#       "id": "w1",
#       "data": {
#         "value": 150000.0,
#         "change": 5.2,
#         "trend": "up"
#       }
#     }
#   ]
# }
```

### 21.2 Complete Flow: Generate Report

```bash
# 1. Create report (immediate response)
curl -X POST http://localhost:8107/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Report",
    "format": "csv",
    "config": {
      "services": ["feed-service"],
      "metrics": ["requests_total"],
      "start_date": "2025-10-05T00:00:00Z",
      "end_date": "2025-10-12T00:00:00Z"
    }
  }'

# Response:
# {
#   "id": 1,
#   "status": "pending",
#   ...
# }

# 2. Poll for completion (every 5 seconds)
curl http://localhost:8107/api/v1/reports/1 \
  -H "Authorization: Bearer $TOKEN"

# Response (after generation):
# {
#   "id": 1,
#   "status": "completed",
#   "file_path": "/tmp/analytics-reports/report_1_20251019_143005.csv",
#   ...
# }

# 3. Download report
curl http://localhost:8107/api/v1/reports/1/download \
  -H "Authorization: Bearer $TOKEN" \
  -o Weekly_Report.csv
```

### 21.3 WebSocket Real-Time Updates

```javascript
// Connect to dashboard
const ws = new WebSocket('ws://localhost:8107/api/v1/dashboards/1/ws');

// Listen for updates
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.error) {
    console.error('Error:', message.error);
    return;
  }

  // Update UI with new widget data
  updateWidget(message.widget_id, message.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed, reconnecting...');
  setTimeout(() => {
    new WebSocket('ws://localhost:8107/api/v1/dashboards/1/ws');
  }, 5000);
};
```

---

## 22. API Endpoint Reference

### Quick Reference Table

**Total Endpoints:** 32+

| Category | Endpoint | Method | Auth | Purpose |
|----------|----------|--------|------|---------|
| **Analytics** | `/api/v1/analytics/overview` | GET | Required | System-wide metrics snapshot |
| | `/api/v1/analytics/trends` | GET | Required | Trend analysis with anomaly detection |
| | `/api/v1/analytics/service/{name}` | GET | Required | Service-specific metrics |
| | `/api/v1/analytics/metrics` | POST | Required | Store new metric |
| **Dashboards** | `/api/v1/dashboards` | POST | Required | Create dashboard |
| | `/api/v1/dashboards` | GET | Required | List dashboards |
| | `/api/v1/dashboards/{id}` | GET | Required | Get dashboard |
| | `/api/v1/dashboards/{id}` | PUT | Required | Update dashboard |
| | `/api/v1/dashboards/{id}` | DELETE | Required | Delete dashboard |
| | `/api/v1/dashboards/{id}/data` | GET | Required | Get dashboard with live data |
| **Reports** | `/api/v1/reports` | POST | Required | Create report (background) |
| | `/api/v1/reports` | GET | Required | List reports |
| | `/api/v1/reports/{id}` | GET | Required | Get report status |
| | `/api/v1/reports/{id}/download` | GET | Required | Download report file |
| **Monitoring** | `/api/v1/monitoring/circuit-breakers` | GET | Required | Circuit breaker status |
| | `/api/v1/monitoring/query-performance` | GET | Required | Database query performance |
| | `/api/v1/monitoring/query-performance/reset` | POST | Required | Reset query statistics |
| | `/api/v1/monitoring/websocket` | GET | Required | WebSocket connection stats |
| | `/api/v1/monitoring/health` | GET | None | Comprehensive system health |
| **Cache** | `/api/v1/cache/stats` | GET | None | Redis cache statistics |
| | `/api/v1/cache/health` | GET | None | Cache availability check |
| | `/api/v1/cache/clear` | POST | None | Clear cache pattern |
| **WebSocket** | `/ws/metrics` | WS | Token | Real-time metrics streaming |
| | `/ws/stats` | GET | None | WebSocket connection stats |
| **Health** | `/api/v1/health/containers` | GET | None | Docker container metrics |
| | `/api/v1/health/alerts` | GET | None | Monitoring alerts (deprecated) |
| | `/api/v1/health/summary` | GET | None | System health summary |
| **Root** | `/health` | GET | None | Simple health check |
| | `/` | GET | None | Service information |

### Endpoint Categories

**Analytics (4 endpoints):** Core metrics collection and analysis
**Dashboards (6 endpoints):** Custom visualization management
**Reports (4 endpoints):** Historical data export and reporting
**Monitoring (5 endpoints):** System performance and circuit breakers
**Cache (3 endpoints):** Redis cache monitoring and management
**WebSocket (2 endpoints):** Real-time updates and connection management
**Health (3 endpoints):** Docker container and system health monitoring
**Root (2 endpoints):** Service metadata and health checks

---

## Summary

The Analytics Service is a mature, production-ready platform for metrics collection, trend analysis, and visualization. Key features:

- **Time-Series Storage:** PostgreSQL with optimized indexes
- **Real-Time Dashboards:** WebSocket-based live updates (30s heartbeat)
- **Trend Analysis:** Linear regression + anomaly detection (z-score method)
- **Report Generation:** CSV, JSON, Markdown formats
- **Circuit Breakers:** Service resilience monitoring and metrics
- **Cache Monitoring:** Redis performance statistics and management
- **Container Health:** Docker metrics and resource monitoring
- **Query Performance:** Database query profiling and optimization
- **Scalability:** Horizontal scaling via Celery workers
- **Security:** JWT authentication with user isolation
- **Performance:** < 100ms for most queries (with caching)

**Endpoints:** 32+ REST/WebSocket endpoints across 7 categories
**Documentation Size:** 1,400+ lines of comprehensive technical specifications
**Last Updated:** 2025-12-22 (Added monitoring, cache, WebSocket, and health endpoints)


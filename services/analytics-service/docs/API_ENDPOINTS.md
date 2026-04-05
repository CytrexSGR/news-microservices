# Analytics Service - API Endpoints

## Base URL

```
http://localhost:8007
```

## Authentication

All endpoints (except `/health` and `/`) require JWT authentication:

```
Authorization: Bearer <jwt_token>
```

Get token from Auth Service:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "andreas@test.com", "password": "Aug2012#"}'
```

---

## Health & Status

### GET /health

Basic health check (no authentication required).

**Response:**

```json
{
  "status": "healthy",
  "service": "analytics-service",
  "version": "1.0.0"
}
```

### GET /

Service information (no authentication required).

**Response:**

```json
{
  "service": "analytics-service",
  "message": "Analytics service is running",
  "endpoints": {
    "health": "/health",
    "docs": "/docs",
    "api": {
      "analytics": "/api/v1/analytics",
      "dashboards": "/api/v1/dashboards",
      "reports": "/api/v1/reports"
    }
  }
}
```

---

## Analytics Endpoints

### GET /api/v1/analytics/overview

Get system-wide analytics overview.

**Authentication:** Required

**Response:**

```json
{
  "timestamp": "2025-11-24T10:00:00Z",
  "services": {
    "auth-service": {
      "total_requests": 1234,
      "error_rate": 0.005,
      "avg_latency_ms": 45.2,
      "active_users": 150
    },
    "feed-service": {
      "total_requests": 5678,
      "error_rate": 0.001,
      "avg_latency_ms": 120.5,
      "active_users": 200
    }
  },
  "system_health": "healthy",
  "active_alerts": 0,
  "total_users": 350,
  "total_articles": 12500
}
```

**Performance:**
- Cache TTL: 30 seconds
- Target latency: < 100ms

### GET /api/v1/analytics/trends

Get trend analysis for specific metric.

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | Yes | Service name |
| metric_name | string | Yes | Metric to analyze |
| hours | integer | No | Time range (1-168), default: 24 |
| interval_minutes | integer | No | Aggregation interval (5-1440), default: 60 |

**Example:**

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8007/api/v1/analytics/trends?service=auth-service&metric_name=requests_total&hours=24&interval_minutes=60"
```

**Response:**

```json
{
  "service": "auth-service",
  "metric_name": "requests_total",
  "time_range_hours": 24,
  "interval_minutes": 60,
  "data_points": [
    {
      "timestamp": "2025-11-24T09:00:00Z",
      "value": 123.5,
      "trend": "up"
    }
  ],
  "summary": {
    "min": 50.2,
    "max": 200.1,
    "avg": 125.3,
    "trend": "increasing"
  }
}
```

### GET /api/v1/analytics/service/{service_name}

Get metrics for specific service.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| service_name | string | Service identifier |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| metric_names | string[] | No | Specific metrics to fetch |
| start_date | datetime | No | Start of time range |
| end_date | datetime | No | End of time range |

**Example:**

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8007/api/v1/analytics/service/auth-service?start_date=2025-11-24T00:00:00Z"
```

### POST /api/v1/analytics/metrics

Store new metric (for internal service use).

**Authentication:** Required

**Request Body:**

```json
{
  "service": "auth-service",
  "metric_name": "requests_total",
  "value": 123.0,
  "unit": "count",
  "labels": {
    "endpoint": "/api/v1/auth/login",
    "status": "200"
  },
  "timestamp": "2025-11-24T10:00:00Z"
}
```

**Response:** Created metric object

---

## Monitoring Endpoints

### GET /api/v1/monitoring/health

Comprehensive system health check.

**Authentication:** Required

**Response:**

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
      "total_queries": 10000,
      "unique_patterns": 15,
      "slow_queries": 2
    },
    "websocket": {
      "total_connections": 25
    }
  }
}
```

**Status values:**
- `healthy` - All systems operational
- `degraded` - Some issues detected
- `unhealthy` - Critical issues

### GET /api/v1/monitoring/circuit-breakers

Get circuit breaker status for all services.

**Authentication:** Required

**Response:**

```json
{
  "circuit_breakers": {
    "feed-service_circuit": {
      "state": "closed",
      "total_calls": 1000,
      "successful_calls": 995,
      "failed_calls": 5,
      "rejected_calls": 0,
      "failure_count": 0,
      "success_count": 0,
      "last_failure_time": null,
      "opened_at": null,
      "state_transitions": []
    }
  },
  "total_services": 7,
  "open_circuits": 0,
  "half_open_circuits": 0
}
```

**Circuit states:**
- `closed` - Normal operation
- `open` - Blocking requests (service failed)
- `half_open` - Testing recovery

### GET /api/v1/monitoring/query-performance

Get database query performance statistics.

**Authentication:** Required

**Response:**

```json
{
  "total_queries": 10000,
  "unique_patterns": 15,
  "slow_query_threshold_ms": 100,
  "top_queries": [
    {
      "query": "SELECT * FROM analytics_metrics WHERE service = '?' AND timestamp >= '?'",
      "executions": 1000,
      "total_time_ms": 150500.0,
      "avg_time_ms": 150.5,
      "min_time_ms": 50.2,
      "max_time_ms": 300.1,
      "slow_query_count": 300
    }
  ],
  "slow_queries": [
    {
      "statement": "SELECT * FROM analytics_metrics WHERE service = 'auth-service'",
      "duration_ms": 250.5,
      "timestamp": "2025-11-24T10:00:00Z",
      "pattern": "SELECT * FROM analytics_metrics WHERE service = '?'"
    }
  ],
  "index_recommendations": [
    {
      "type": "index",
      "table": "analytics_metrics",
      "column": "service",
      "reason": "Frequent WHERE clause on analytics_metrics.service",
      "sql": "CREATE INDEX idx_analytics_metrics_service ON analytics_metrics(service);",
      "impact": "high"
    }
  ]
}
```

### POST /api/v1/monitoring/query-performance/reset

Reset query performance statistics.

**Authentication:** Required

**Response:**

```json
{
  "message": "Query statistics reset successfully"
}
```

### GET /api/v1/monitoring/websocket

Get WebSocket connection statistics.

**Authentication:** Required

**Response:**

```json
{
  "total_connections": 25,
  "connections": [
    {
      "client_id": "ws_andreas_1700000000.123",
      "user_id": "andreas",
      "connected_at": "2025-11-24T10:00:00Z",
      "last_heartbeat": "2025-11-24T10:05:30Z",
      "subscriptions": ["metrics", "alerts"]
    }
  ]
}
```

---

## WebSocket Endpoints

### WS /ws/metrics?token={jwt_token}

Real-time metrics WebSocket connection.

**Authentication:** JWT token via query parameter

**Protocol:** See [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md)

**Client → Server Messages:**

| Action | Description |
|--------|-------------|
| `subscribe` | Subscribe to channel |
| `unsubscribe` | Unsubscribe from channel |
| `get_metrics` | Request current metrics |
| `ping` | Connection test |

**Server → Client Messages:**

| Type | Description |
|------|-------------|
| `connected` | Connection established |
| `heartbeat` | Keep-alive (every 30s) |
| `metrics` | Metrics snapshot |
| `metrics_update` | Broadcast update (every 10s) |
| `subscribed` | Subscription confirmed |
| `unsubscribed` | Unsubscription confirmed |
| `pong` | Ping response |
| `error` | Error message |

**Example:**

```javascript
const ws = new WebSocket(`ws://localhost:8007/ws/metrics?token=${token}`);

ws.onopen = () => {
  // Subscribe to metrics
  ws.send(JSON.stringify({
    action: "subscribe",
    channel: "metrics"
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

### GET /api/v1/ws/stats

Get WebSocket statistics (alternative to monitoring endpoint).

**Authentication:** Not required (returns public stats only)

**Response:**

```json
{
  "total_connections": 25
}
```

---

## Dashboard Endpoints

### GET /api/v1/dashboards

List all dashboards.

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Max results (default: 20) |
| offset | integer | Skip results (default: 0) |

### POST /api/v1/dashboards

Create new dashboard.

**Authentication:** Required

**Request Body:**

```json
{
  "name": "System Overview",
  "description": "Main system metrics",
  "layout": "grid",
  "widgets": [
    {
      "type": "stat-card",
      "title": "Total Users",
      "options": {
        "metric_name": "active_users",
        "aggregation": "sum"
      }
    }
  ]
}
```

### GET /api/v1/dashboards/{id}

Get specific dashboard.

### PUT /api/v1/dashboards/{id}

Update dashboard.

### DELETE /api/v1/dashboards/{id}

Delete dashboard.

---

## Widget Endpoints

### GET /api/v1/widgets

List all widgets.

### POST /api/v1/widgets

Create new widget.

### GET /api/v1/widgets/{id}

Get specific widget.

### PUT /api/v1/widgets/{id}

Update widget.

### DELETE /api/v1/widgets/{id}

Delete widget.

### GET /api/v1/widgets/{id}/data

Get widget data (aggregated metrics).

**Response format depends on widget type:**

**Stat Card:**

```json
{
  "value": 1234,
  "change": 5.2,
  "trend": "up"
}
```

**Time Series:**

```json
{
  "series": [
    {"timestamp": "2025-11-24T09:00:00Z", "value": 123},
    {"timestamp": "2025-11-24T10:00:00Z", "value": 150}
  ]
}
```

---

## Report Endpoints

### GET /api/v1/reports

List all reports.

### POST /api/v1/reports

Generate new report.

**Request Body:**

```json
{
  "name": "Weekly Summary",
  "type": "pdf",
  "start_date": "2025-11-17T00:00:00Z",
  "end_date": "2025-11-24T00:00:00Z",
  "metrics": ["requests_total", "error_rate"],
  "services": ["auth-service", "feed-service"]
}
```

### GET /api/v1/reports/{id}

Get report metadata.

### GET /api/v1/reports/{id}/download

Download report file.

---

## Error Responses

All endpoints return standard error responses:

**400 Bad Request:**

```json
{
  "detail": "Invalid parameter: hours must be between 1 and 168"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden:**

```json
{
  "detail": "Insufficient permissions"
}
```

**404 Not Found:**

```json
{
  "detail": "Dashboard not found"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Internal server error",
  "error_id": "abc123"
}
```

---

## Rate Limiting

All endpoints are rate-limited:

- **Default:** 60 requests per minute per user
- **Header:** `X-RateLimit-Remaining` shows remaining requests
- **Response:** 429 Too Many Requests when exceeded

---

## OpenAPI Documentation

Interactive API documentation available at:

- **Swagger UI:** http://localhost:8007/docs
- **ReDoc:** http://localhost:8007/redoc
- **OpenAPI JSON:** http://localhost:8007/openapi.json

---

**Last Updated:** 2025-11-24
**Version:** 1.0.0

# Analytics Service API

**Base URL:** `http://localhost:8107`

**Authentication:** Required - Bearer token (JWT) via `/api/v1/auth/login`

**API Prefix:** `/api/v1`

## Overview

Comprehensive analytics API providing real-time monitoring, trend analysis, custom dashboards, and automated report generation for the News Microservices platform.

**Key Features:**
- System-wide metrics aggregation from all 7 microservices
- Time-series trend analysis with anomaly detection
- Custom widget-based dashboards (line charts, bar charts, stats)
- Multi-format report generation (PDF, CSV, JSON)
- Real-time WebSocket updates for dashboards
- Prometheus metrics export for Grafana

---

## Analytics Endpoints

### GET /api/v1/analytics/overview

Get system-wide analytics overview.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "total_services": 7,
  "healthy_services": 7,
  "total_requests": 1234567,
  "total_errors": 123,
  "error_rate": 0.0001,
  "average_latency_ms": 45.2,
  "active_users": 523,
  "services": {
    "auth-service": {
      "status": "healthy",
      "requests_total": 45678,
      "errors_total": 12,
      "latency_ms": 23.5
    },
    "feed-service": {
      "status": "healthy",
      "requests_total": 123456,
      "errors_total": 45,
      "latency_ms": 67.8
    }
  },
  "timestamp": "2025-01-19T10:00:00Z"
}
```

**Usage:**
```bash
curl http://localhost:8107/api/v1/analytics/overview \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/analytics/trends

Get trend analysis for a specific metric.

**Authentication:** Required

**Query Parameters:**
- `service` (string, required): Service name (e.g., "feed-service")
- `metric_name` (string, required): Metric to analyze (e.g., "requests_total")
- `hours` (int, optional): Time range in hours (default: 24, max: 168)
- `interval_minutes` (int, optional): Aggregation interval (default: 60, range: 5-1440)

**Response:** `200 OK`
```json
{
  "service": "feed-service",
  "metric_name": "requests_total",
  "time_range_hours": 24,
  "interval_minutes": 60,
  "data_points": [
    {
      "timestamp": "2025-01-19T09:00:00Z",
      "value": 1234,
      "moving_average": 1250
    },
    {
      "timestamp": "2025-01-19T10:00:00Z",
      "value": 1345,
      "moving_average": 1278
    }
  ],
  "trend": "increasing",
  "change_percent": 15.3,
  "slope": 0.45,
  "anomalies": [
    {
      "timestamp": "2025-01-19T08:30:00Z",
      "value": 2500,
      "z_score": 3.2,
      "severity": "high"
    }
  ],
  "statistics": {
    "mean": 1234.5,
    "median": 1200,
    "std_dev": 150.2,
    "min": 980,
    "max": 2500
  }
}
```

**Trend Values:**
- `increasing` - Metric trending upward
- `decreasing` - Metric trending downward
- `stable` - No significant trend
- `volatile` - High variance, unclear trend

**Usage:**
```bash
curl "http://localhost:8107/api/v1/analytics/trends?service=feed-service&metric_name=requests_total&hours=48" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/analytics/service/{service_name}

Get metrics for a specific service.

**Authentication:** Required

**Path Parameters:**
- `service_name` (string): Service name (auth-service, feed-service, etc.)

**Query Parameters:**
- `metric_names` (array[string], optional): Filter specific metrics
- `start_date` (datetime, optional): Start date (ISO 8601, default: 24h ago)
- `end_date` (datetime, optional): End date (ISO 8601, default: now)

**Response:** `200 OK`
```json
[
  {
    "id": 12345,
    "service": "feed-service",
    "metric_name": "requests_total",
    "value": 1234,
    "unit": "requests",
    "labels": {
      "endpoint": "/api/v1/feeds",
      "method": "GET"
    },
    "timestamp": "2025-01-19T10:00:00Z"
  },
  {
    "id": 12346,
    "service": "feed-service",
    "metric_name": "latency_ms",
    "value": 67.8,
    "unit": "milliseconds",
    "timestamp": "2025-01-19T10:00:00Z"
  }
]
```

**Available Metrics:**
- `service_status` - Service health (1.0 = healthy, 0.0 = unhealthy)
- `requests_total` - Total request count
- `errors_total` - Total error count
- `latency_ms` - Average request latency
- `active_users` - Number of active users

**Usage:**
```bash
curl "http://localhost:8107/api/v1/analytics/service/feed-service?metric_names=requests_total,latency_ms" \
  -H "Authorization: Bearer $TOKEN"
```

---

### POST /api/v1/analytics/metrics

Store a new metric (internal service use).

**Authentication:** Required

**Request Body:**
```json
{
  "service": "my-service",
  "metric_name": "custom_metric",
  "value": 123.45,
  "unit": "requests",
  "labels": {
    "region": "us-west",
    "tier": "premium"
  }
}
```

**Parameters:**
- `service` (string, required): Service identifier
- `metric_name` (string, required): Metric name
- `value` (number, required): Metric value
- `unit` (string, optional): Measurement unit
- `labels` (object, optional): Additional key-value labels

**Response:** `201 Created`
```json
{
  "id": 12347,
  "service": "my-service",
  "metric_name": "custom_metric",
  "value": 123.45,
  "unit": "requests",
  "labels": {
    "region": "us-west",
    "tier": "premium"
  },
  "timestamp": "2025-01-19T10:00:00Z"
}
```

---

## Dashboard Endpoints

### POST /api/v1/dashboards

Create a new custom dashboard.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "System Overview",
  "description": "Main system monitoring dashboard",
  "is_public": false,
  "layout": "grid",
  "widgets": [
    {
      "id": "widget1",
      "type": "stat_card",
      "title": "Total Requests",
      "config": {
        "service": "feed-service",
        "metric_name": "requests_total",
        "aggregation": "sum"
      },
      "position": {
        "x": 0,
        "y": 0,
        "w": 6,
        "h": 4
      }
    },
    {
      "id": "widget2",
      "type": "line_chart",
      "title": "Error Rate Trend",
      "config": {
        "service": "feed-service",
        "metric_name": "errors_total",
        "time_range_hours": 24
      },
      "position": {
        "x": 6,
        "y": 0,
        "w": 6,
        "h": 4
      }
    }
  ]
}
```

**Widget Types:**
- `stat_card` - Single metric display
- `line_chart` - Time-series line chart
- `bar_chart` - Bar chart for comparisons
- `pie_chart` - Distribution visualization
- `table` - Tabular data display

**Response:** `201 Created`
```json
{
  "id": 42,
  "name": "System Overview",
  "description": "Main system monitoring dashboard",
  "is_public": false,
  "layout": "grid",
  "widgets": [...],
  "owner_id": "user-uuid",
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T10:00:00Z"
}
```

---

### GET /api/v1/dashboards

List dashboards.

**Authentication:** Optional (returns public dashboards only without auth)

**Query Parameters:**
- `include_public` (boolean, optional): Include public dashboards (default: true)
- `skip` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Max results (default: 20, max: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 42,
    "name": "System Overview",
    "description": "Main system monitoring dashboard",
    "is_public": false,
    "widget_count": 6,
    "owner_id": "user-uuid",
    "created_at": "2025-01-19T10:00:00Z"
  }
]
```

---

### GET /api/v1/dashboards/{dashboard_id}

Get dashboard configuration.

**Authentication:** Optional (public dashboards only without auth)

**Response:** `200 OK`
```json
{
  "id": 42,
  "name": "System Overview",
  "description": "Main system monitoring dashboard",
  "is_public": false,
  "layout": "grid",
  "widgets": [...],
  "owner_id": "user-uuid",
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T10:00:00Z"
}
```

---

### GET /api/v1/dashboards/{dashboard_id}/data

Get dashboard with live widget data.

**Authentication:** Optional (public dashboards only without auth)

**Response:** `200 OK`
```json
{
  "dashboard": {
    "id": 42,
    "name": "System Overview",
    "widgets": [...]
  },
  "data": {
    "widget1": {
      "value": 123456,
      "change_24h": "+15.3%",
      "trend": "increasing"
    },
    "widget2": {
      "data_points": [
        {"timestamp": "2025-01-19T09:00:00Z", "value": 12},
        {"timestamp": "2025-01-19T10:00:00Z", "value": 15}
      ]
    }
  },
  "last_updated": "2025-01-19T10:00:00Z"
}
```

---

### PUT /api/v1/dashboards/{dashboard_id}

Update dashboard.

**Authentication:** Required (owner only)

**Request Body:**
```json
{
  "name": "Updated Dashboard Name",
  "description": "New description",
  "is_public": true,
  "widgets": [...]
}
```

**Response:** `200 OK` (updated dashboard)

---

### DELETE /api/v1/dashboards/{dashboard_id}

Delete dashboard.

**Authentication:** Required (owner only)

**Response:** `204 No Content`

---

## Report Endpoints

### POST /api/v1/reports

Create a new analytics report.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "Weekly Performance Report",
  "description": "Performance metrics for the past week",
  "format": "pdf",
  "config": {
    "services": ["feed-service", "content-analysis-service"],
    "metrics": ["requests_total", "latency_ms", "errors_total"],
    "start_date": "2025-01-12T00:00:00Z",
    "end_date": "2025-01-19T00:00:00Z",
    "include_charts": true,
    "aggregation": "hourly",
    "chart_types": ["line", "bar"]
  }
}
```

**Report Formats:**
- `pdf` - Visual report with charts (uses WeasyPrint)
- `csv` - Raw data export for analysis
- `json` - Structured data export

**Aggregation Options:**
- `raw` - No aggregation
- `hourly` - Hourly aggregates
- `daily` - Daily aggregates
- `weekly` - Weekly aggregates

**Response:** `201 Created`
```json
{
  "id": 123,
  "name": "Weekly Performance Report",
  "description": "Performance metrics for the past week",
  "format": "pdf",
  "status": "pending",
  "progress": 0,
  "file_path": null,
  "file_size_bytes": null,
  "created_at": "2025-01-19T10:00:00Z",
  "completed_at": null
}
```

**Status Values:**
- `pending` - Report queued for generation
- `processing` - Report being generated
- `completed` - Report ready for download
- `failed` - Generation failed (see error_message)

---

### GET /api/v1/reports

List user reports.

**Authentication:** Required

**Query Parameters:**
- `skip` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Max results (default: 20, max: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "name": "Weekly Performance Report",
    "format": "pdf",
    "status": "completed",
    "file_size_bytes": 1234567,
    "created_at": "2025-01-19T10:00:00Z",
    "completed_at": "2025-01-19T10:02:45Z"
  }
]
```

---

### GET /api/v1/reports/{report_id}

Get report details.

**Authentication:** Required (owner only)

**Response:** `200 OK`
```json
{
  "id": 123,
  "name": "Weekly Performance Report",
  "description": "Performance metrics for the past week",
  "format": "pdf",
  "status": "completed",
  "progress": 100,
  "file_path": "/tmp/analytics-reports/report_123.pdf",
  "file_size_bytes": 1234567,
  "config": {...},
  "error_message": null,
  "created_at": "2025-01-19T10:00:00Z",
  "completed_at": "2025-01-19T10:02:45Z"
}
```

---

### GET /api/v1/reports/{report_id}/download

Download report file.

**Authentication:** Required (owner only)

**Response:** `200 OK` (file download)

**Headers:**
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="Weekly Performance Report.pdf"
```

**Error Responses:**
- `400 Bad Request` - Report not ready (status != completed)
- `404 Not Found` - Report or file not found

**Usage:**
```bash
curl http://localhost:8107/api/v1/reports/123/download \
  -H "Authorization: Bearer $TOKEN" \
  -o report.pdf
```

---

## Health & Monitoring

### GET /health

Basic health check.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "analytics-service",
  "version": "1.0.0"
}
```

---

### GET /

Service information.

**Response:** `200 OK`
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

### GET /metrics

Prometheus metrics export.

**Response:** `200 OK` (Prometheus text format)
```
# HELP analytics_service_requests_total Total requests
# TYPE analytics_service_requests_total counter
analytics_service_requests_total 12345

# HELP analytics_service_request_latency_seconds Request latency
# TYPE analytics_service_request_latency_seconds histogram
analytics_service_request_latency_seconds_bucket{le="0.1"} 8234
analytics_service_request_latency_seconds_bucket{le="0.5"} 11456
analytics_service_request_latency_seconds_sum 567.8
analytics_service_request_latency_seconds_count 12345

# HELP analytics_service_active_connections Active WebSocket connections
# TYPE analytics_service_active_connections gauge
analytics_service_active_connections 23
```

---

## Error Handling

All endpoints return standard HTTP status codes and error responses:

**400 Bad Request:**
```json
{
  "detail": "Invalid date range: end_date must be after start_date"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to access this dashboard"
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
  "detail": "Failed to generate report: WeasyPrint error"
}
```

---

## WebSocket Support

Real-time dashboard updates via WebSocket.

**Connection:** `ws://localhost:8107/ws/dashboards/{dashboard_id}`

**Authentication:** Send JWT token in first message
```json
{
  "type": "auth",
  "token": "Bearer eyJ..."
}
```

**Update Messages:**
```json
{
  "type": "data_update",
  "widget_id": "widget1",
  "data": {
    "value": 123456,
    "change_24h": "+15.3%"
  },
  "timestamp": "2025-01-19T10:00:00Z"
}
```

**Heartbeat:** Sent every 30 seconds
```json
{
  "type": "heartbeat",
  "timestamp": "2025-01-19T10:00:00Z"
}
```

---

## Related Documentation

- [Service Documentation](../services/analytics-service.md)
- [Configuration Reference](./analytics-service-config.md)
- [Deployment Guide](../guides/DEPLOYMENT_GUIDE.md)

# Analytics Service

**Port**: 8107 | **Status**: Production | **Version**: 1.1.0

Comprehensive analytics and metrics aggregation service for the News Microservices platform.

## Features

- **Real-time Metrics Collection**: Aggregates metrics from all 7 microservices
- **Trend Analysis**: Time-series analysis with anomaly detection
- **Custom Dashboards**: Drag-and-drop widget-based dashboards
- **Report Generation**: PDF, CSV, and JSON reports with charts
- **Prometheus Integration**: Exports metrics for Grafana visualization
- **WebSocket Support**: Real-time dashboard updates
- **Alert System**: Configurable thresholds with notifications

## Architecture

### Components

1. **Metrics Service**: Collects and stores time-series metrics
2. **Trend Service**: Analyzes trends and detects anomalies
3. **Report Service**: Generates formatted analytics reports
4. **Dashboard Service**: Manages custom user dashboards
5. **Celery Workers**: Background metric collection and report generation

### Database Models

- `analytics_metrics`: Time-series metric storage
- `analytics_reports`: Generated report metadata
- `analytics_dashboards`: User dashboard configurations
- `analytics_alerts`: Alert thresholds and rules

## API Endpoints

### Analytics

- `GET /api/v1/analytics/overview` - System-wide metrics overview
- `GET /api/v1/analytics/trends` - Trend analysis for specific metrics
- `GET /api/v1/analytics/service/{service_name}` - Service-specific metrics
- `POST /api/v1/analytics/metrics` - Store new metric (internal)

### Reports

- `POST /api/v1/analytics/reports` - Create new report
- `GET /api/v1/analytics/reports` - List user reports
- `GET /api/v1/analytics/reports/{id}` - Get report details
- `GET /api/v1/analytics/reports/{id}/download` - Download report file

### Dashboards

- `POST /api/v1/analytics/dashboards` - Create dashboard
- `GET /api/v1/analytics/dashboards` - List dashboards
- `GET /api/v1/analytics/dashboards/{id}` - Get dashboard
- `GET /api/v1/analytics/dashboards/{id}/data` - Get dashboard with live data
- `PUT /api/v1/analytics/dashboards/{id}` - Update dashboard
- `DELETE /api/v1/analytics/dashboards/{id}` - Delete dashboard

## Metrics Collected

### Per Service

- `service_status`: Service health (1.0 = healthy, 0.0 = unhealthy)
- `requests_total`: Total request count
- `errors_total`: Total error count
- `latency_ms`: Average request latency
- `active_users`: Number of active users

### System-Wide

- Total users across all services
- Overall error rate
- Service availability percentage
- Resource utilization

## Configuration

Key environment variables:

```bash
SERVICE_NAME=analytics-service
PORT=8107  # Note: Internal port is 8000, external is 8107
DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp
REDIS_URL=redis://:redis_secret_2024@redis:6379/0
CELERY_BROKER_URL=redis://:redis_secret_2024@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis_secret_2024@redis:6379/2

# Service URLs for metric collection
AUTH_SERVICE_URL=http://auth-service:8000
FEED_SERVICE_URL=http://feed-service:8001
ANALYSIS_SERVICE_URL=http://content-analysis-service:8002
RESEARCH_SERVICE_URL=http://research-service:8003
OSINT_SERVICE_URL=http://osint-service:8004
NOTIFICATION_SERVICE_URL=http://notification-service:8005
SEARCH_SERVICE_URL=http://search-service:8006

# Metrics configuration
METRICS_COLLECTION_INTERVAL=60
METRICS_RETENTION_DAYS=90
```

## Dashboard Widgets

Supported widget types:

1. **line_chart**: Time-series line chart
2. **bar_chart**: Bar chart for comparisons
3. **pie_chart**: Distribution visualization
4. **stat_card**: Single metric display
5. **table**: Tabular data display

### Example Dashboard

```json
{
  "name": "System Overview",
  "widgets": [
    {
      "id": "widget1",
      "type": "stat_card",
      "title": "Total Requests",
      "metric_name": "requests_total",
      "service": "feed-service",
      "position": {"x": 0, "y": 0, "w": 6, "h": 4}
    },
    {
      "id": "widget2",
      "type": "line_chart",
      "title": "Error Rate Trend",
      "metric_name": "errors_total",
      "position": {"x": 6, "y": 0, "w": 6, "h": 4}
    }
  ]
}
```

## Report Generation

### Formats

- **PDF**: Visual reports with charts (using WeasyPrint)
- **CSV**: Raw data export for analysis
- **JSON**: Structured data export

### Example Report Request

```json
{
  "name": "Weekly Performance Report",
  "description": "Performance metrics for the past week",
  "format": "pdf",
  "config": {
    "services": ["feed-service", "content-analysis-service"],
    "metrics": ["requests_total", "latency_ms"],
    "start_date": "2025-10-05T00:00:00Z",
    "end_date": "2025-10-12T00:00:00Z",
    "include_charts": true,
    "aggregation": "hourly"
  }
}
```

## Celery Workers

### Tasks

1. **collect_metrics_task**: Runs every 60 seconds
   - Fetches health data from all services
   - Stores metrics in database
   - Caches recent values in Redis

2. **cleanup_old_metrics_task**: Runs daily
   - Removes metrics older than retention period
   - Keeps aggregated data longer

3. **generate_report_task**: On-demand
   - Generates reports in background
   - Updates report status

### Running Workers

```bash
# Main worker
celery -A app.workers.celery_app worker --loglevel=info

# Beat scheduler for periodic tasks
celery -A app.workers.celery_app beat --loglevel=info

# Flower monitoring UI
celery -A app.workers.celery_app flower --port=5555
```

## Prometheus Metrics

Exported at `/metrics`:

- `analytics_service_requests_total`: Request counter
- `analytics_service_request_latency_seconds`: Request latency histogram
- `analytics_service_active_connections`: Active WebSocket connections

### Grafana Dashboard

Import `grafana/dashboard.json` to get:

- Service health overview
- Request rate graphs
- Latency percentiles (p95, p99)
- Error rate tracking
- Active connections

## Trend Analysis

The service uses statistical methods for trend detection:

- **Linear Regression**: Determines trend direction
- **Z-Score Anomaly Detection**: Identifies outliers
- **Moving Average**: Smooths noisy data
- **Percentage Change**: Quantifies trend magnitude

### Example Trend Response

```json
{
  "metric_name": "requests_total",
  "service": "feed-service",
  "data_points": [...],
  "trend": "increasing",
  "change_percent": 15.3,
  "anomalies": [
    "2025-10-12T08:30:00Z",
    "2025-10-12T14:15:00Z"
  ]
}
```

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start service
uvicorn app.main:app --reload --port 8007

# Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Docker

```bash
# Build
docker build -t analytics-service .

# Run
docker run -p 8007:8007 --env-file .env analytics-service
```

## Integration

### Collecting Custom Metrics

```python
import httpx

# Store a metric
metric_data = {
    "service": "my-service",
    "metric_name": "custom_metric",
    "value": 123.45,
    "unit": "requests",
    "labels": {"region": "us-west"}
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://analytics-service:8007/api/v1/analytics/metrics",
        json=metric_data,
        headers={"Authorization": f"Bearer {token}"}
    )
```

## Performance Considerations

- **Redis Caching**: Recent metrics cached for 5 minutes
- **Database Indexing**: Indexes on service, metric_name, timestamp
- **Batch Processing**: Metrics collected in bulk every minute
- **Retention Policy**: Automatic cleanup of old data

## Security

- JWT authentication required for all endpoints
- User isolation for reports and dashboards
- Public dashboards opt-in only
- File size limits for generated reports

## Documentation

- [Service Documentation](../../docs/services/analytics-service.md)
- [API Documentation](../../docs/api/analytics-service-api.md)

## License

Part of the News Microservices platform.

---

## Changelog

### 2026-01-05: Redis Authentication Fix

**Issue:** `analytics-celery-worker` container marked as unhealthy, failing to connect to Redis.

**Error:**
```
NOAUTH Authentication required
```

**Root Cause:** Redis has password protection enabled (`redis_secret_2024`), but `.env` file had unauthenticated URLs.

**Resolution:** Updated `.env` file with Redis password in connection URLs:

```bash
# Before (broken):
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# After (working):
CELERY_BROKER_URL=redis://:redis_secret_2024@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis_secret_2024@redis:6379/2
```

**Note:** Redis password format is `redis://:{password}@{host}:{port}/{db}` - the username is empty, hence the colon before the password.

---

**Version**: 1.1.0
**Last Updated**: 2026-01-05
**Authors**: Claude Code, Andreas

# Notification Service Documentation

## Overview

The Notification Service is a multi-channel notification delivery system that handles email, webhook, RabbitMQ, and push notifications for the News Microservices platform. It provides template-based messaging, user preference management, async delivery via Celery workers, and event-driven integration with other microservices.

**Key Responsibilities:**
- Multi-channel notification delivery (email, webhook, RabbitMQ, push)
- Template-based message rendering with Jinja2
- User notification preferences management
- Event-driven notification triggering via RabbitMQ
- Retry logic with exponential backoff for failed deliveries
- Delivery tracking and audit logs
- Rate limiting per user (hourly and daily)
- Circuit breaker pattern for webhook resilience

**Service Port:** 8105
**Technology Stack:** FastAPI, Celery, aiosmtplib, aio-pika
**Status:** Production-ready

---

## MCP Integration

**MCP Server**: `mcp-integration-server`
**Port**: `9005`
**Prefix**: `integration:`

The Notification Service is accessible via the **mcp-integration-server** for AI/LLM integration.

### Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `send_notification` | Send notification using a template | `user_id` (required), `template_id` (required), `channel`, `data` |
| `send_adhoc_notification` | Send ad-hoc notification without template | `user_id` (required), `subject` (required), `body` (required), `channel` |
| `get_notification_history` | Get notification history for a user | `user_id`, `limit` |
| `list_notification_templates` | List available notification templates | - |
| `get_notification_preferences` | Get notification preferences for user | `user_id` |
| `get_notification_queue_stats` | Get notification queue statistics (admin) | - |

### Example Usage (Claude Desktop)

```
# Send a notification
integration:send_notification user_id=11 template_id="alert" channel="email"

# Get notification history
integration:get_notification_history user_id=11 limit=20

# List templates
integration:list_notification_templates
```

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Notification Service Architecture             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────────────────────────────┐
│ FastAPI API  │◄────────│  Incoming Requests (JWT Protected)   │
│  (Port 8105) │         │  - POST /send                         │
│              │         │  - GET /history                        │
│              │         │  - POST /templates                     │
│              │         │  - GET/POST /preferences               │
└──────┬───────┘         └──────────────────────────────────────┘
       │
       │ ┌─────────────────────────────────────────────────┐
       ├─┤  Database Layer (PostgreSQL - Shared news_mcp)  │
       │ │  - notification_logs                            │
       │ │  - notification_preferences                     │
       │ │  - notification_templates                       │
       │ │  - delivery_attempts                            │
       │ └─────────────────────────────────────────────────┘
       │
       │ ┌─────────────────────────────────────────────────┐
       ├─┤  Celery Task Queue (Redis Broker)              │
       │ │  - deliver_email_task                           │
       │ │  - deliver_webhook_task                         │
       │ │  - retry_failed_deliveries_task (periodic)      │
       │ └─────────────────────────────────────────────────┘
       │
       │ ┌─────────────────────────────────────────────────┐
       └─┤  RabbitMQ Event Consumer                        │
         │  Listens to:                                    │
         │  - osint.alert.triggered                        │
         │  - research.completed                           │
         │  - analysis.completed                           │
         │  - feed.new_article                             │
         └─────────────────────────────────────────────────┘
              │
              ├──► Email Delivery (SMTP)
              ├──► Webhook Delivery (HTTP POST + Circuit Breaker)
              ├──► RabbitMQ Publishing
              └──► Push Notifications (FCM - not yet implemented)
```

### Data Flow

**1. API-Triggered Notification:**
```
User Request → JWT Auth → Create NotificationLog → Queue Celery Task →
Deliver via Channel (Email/Webhook) → Update Status → Return Response
```

**2. Event-Driven Notification:**
```
RabbitMQ Event → Consumer → Get User Preferences → Filter by Event Type →
Create NotificationLog → Queue Celery Task → Deliver → Update Status
```

**3. Failed Delivery Retry:**
```
Periodic Task (30 min) → Find Failed Notifications (last 24h) →
Re-queue for Delivery → Exponential Backoff → Max 3 Retries
```

### Integration Points

**Upstream Services (Event Producers):**
- `osint-service` → `osint.alert.triggered`
- `research-service` → `research.completed`
- `content-analysis-v3` → `analysis.completed`
- `feed-service` → `feed.new_article`

**Downstream Services:**
- `auth-service` → JWT token validation
- External SMTP servers (Gmail, SendGrid, Mailgun, SES)
- External webhook endpoints (user-configured)

**Infrastructure Dependencies:**
- PostgreSQL (shared `news_mcp` database)
- Redis (Celery broker and result backend)
- RabbitMQ (event bus)

---

## Database Schema

### Tables

#### notification_logs
Primary notification tracking table.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | VARCHAR(50) | User receiving notification (indexed) |
| `channel` | VARCHAR(20) | Delivery channel: email, webhook, rabbitmq, push |
| `status` | VARCHAR(20) | Status: pending, sent, failed, retrying (indexed) |
| `subject` | VARCHAR(200) | Email subject or notification title |
| `content` | TEXT | Notification body (HTML/JSON/plaintext) |
| `notification_metadata` | JSON | Channel-specific metadata (email address, webhook URL, payload) |
| `error_message` | TEXT | Error details if delivery failed |
| `created_at` | TIMESTAMP | Creation time (indexed) |
| `sent_at` | TIMESTAMP | Successful delivery time |

**Indexes:**
- `user_id` (query user history)
- `status` (retry failed notifications)
- `created_at` (time-based queries)

#### notification_preferences
User notification settings and filters.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | VARCHAR(50) | User ID (unique, indexed) |
| `email_enabled` | BOOLEAN | Enable email notifications (default: true) |
| `webhook_enabled` | BOOLEAN | Enable webhook notifications (default: false) |
| `push_enabled` | BOOLEAN | Enable push notifications (default: false) |
| `webhook_url` | VARCHAR(500) | User's webhook endpoint |
| `fcm_token` | VARCHAR(200) | Firebase Cloud Messaging token |
| `filters` | JSON | Event type filters (e.g., excluded_events: []) |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### notification_templates
Jinja2 templates for notification rendering.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `name` | VARCHAR(100) | Template identifier (unique, indexed) |
| `channel` | VARCHAR(20) | Target channel: email, webhook, push |
| `subject` | VARCHAR(200) | Email subject template (Jinja2) |
| `body` | TEXT | Template body (Jinja2) |
| `variables` | JSON | Required variable list |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last update time |

**Default Templates:**
- `osint_alert_email` - OSINT alert notifications
- `research_complete_email` - Research completion notifications
- `feed_digest_email` - Daily feed digest
- `analysis_complete_email` - Content analysis completion

#### delivery_attempts
Delivery retry audit log.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `notification_id` | INTEGER | Foreign key to notification_logs |
| `attempt_number` | INTEGER | Retry attempt number (1-based) |
| `status` | VARCHAR(20) | Attempt status: success, failed |
| `error_message` | TEXT | Error details if failed |
| `attempted_at` | TIMESTAMP | Attempt timestamp |

**Indexes:**
- `notification_id` (track retry history)

---

## API Endpoints

### Endpoint Summary

| Method | Endpoint | Description | Auth | Admin |
|--------|----------|-------------|------|-------|
| **Notifications** |
| POST | `/api/v1/notifications/send` | Send notification via channel | ✅ | ❌ |
| POST | `/api/v1/notifications/send/secure` | Send with production hardening | ✅ | ❌ |
| POST | `/api/v1/notifications/send/adhoc` | Send ad-hoc notification (Agent Service) | ✅ | ❌ |
| POST | `/api/v1/notifications/test` | Send test notification | ✅ | ❌ |
| GET | `/api/v1/notifications/{notification_id}` | Get notification by ID | ✅ | ❌ |
| GET | `/api/v1/notifications/history` | Get user notification history | ✅ | ❌ |
| GET | `/api/v1/notifications/delivery/status/{notification_id}` | Get delivery status with retry history | ✅ | ❌ |
| **Templates** |
| GET | `/api/v1/notifications/templates` | List all templates | ✅ | ❌ |
| POST | `/api/v1/notifications/templates` | Create new template | ✅ | ❌ |
| **Preferences** |
| GET | `/api/v1/notifications/preferences` | Get user preferences | ✅ | ❌ |
| POST | `/api/v1/notifications/preferences` | Update user preferences | ✅ | ❌ |
| **Admin - JWT Rotation** |
| GET | `/api/v1/admin/jwt/info` | Get JWT rotation status | ✅ | ✅ |
| POST | `/api/v1/admin/jwt/rotate` | Manually rotate JWT keys | ✅ | ✅ |
| **Admin - Rate Limiting** |
| GET | `/api/v1/admin/rate-limit/user/{user_id}` | Get user rate limit stats | ✅ | ✅ |
| POST | `/api/v1/admin/rate-limit/user/{user_id}/reset` | Reset user rate limits | ✅ | ✅ |
| **Admin - Delivery Queue** |
| GET | `/api/v1/admin/queue/stats` | Get queue statistics | ✅ | ✅ |
| GET | `/api/v1/admin/dlq/list` | List Dead Letter Queue items | ✅ | ✅ |
| POST | `/api/v1/admin/dlq/retry/{notification_id}` | Retry DLQ item | ✅ | ✅ |
| **Admin - Health** |
| GET | `/api/v1/admin/health/detailed` | Get detailed health info | ✅ | ✅ |
| **Health & Metrics** |
| GET | `/health` | Service health check | ❌ | ❌ |
| GET | `/metrics` | Prometheus metrics | ❌ | ❌ |
| GET | `/` | Service info | ❌ | ❌ |

**Legend:**
- ✅ Required
- ❌ Not required

### Notifications

#### `POST /api/v1/notifications/send`
Send a notification through specified channel.

**Authentication:** Bearer token (JWT) required

**Request Body:**
```json
{
  "user_id": "user123",
  "channel": "email",
  "subject": "Alert Triggered",
  "content": "<h1>Important Alert</h1>",
  "metadata": {
    "email": "user@example.com"
  },
  "template_name": "osint_alert_email",
  "template_variables": {
    "alert": {
      "title": "High Severity Event",
      "severity": "high",
      "message": "Security incident detected"
    }
  }
}
```

**Response:** `201 Created`
```json
{
  "id": 1234,
  "user_id": "user123",
  "channel": "email",
  "status": "pending",
  "subject": "Alert Triggered",
  "content": "<h1>Important Alert</h1>",
  "metadata": {
    "email": "user@example.com",
    "to": "user@example.com"
  },
  "error_message": null,
  "created_at": "2025-11-24T10:30:00Z",
  "sent_at": null
}
```

#### `GET /api/v1/notifications/{notification_id}`
Get notification status by ID.

**Authentication:** Bearer token (JWT) required

**Response:** `200 OK`
```json
{
  "id": 1234,
  "user_id": "user123",
  "channel": "email",
  "status": "sent",
  "subject": "Alert Triggered",
  "content": "<h1>Important Alert</h1>",
  "metadata": {...},
  "error_message": null,
  "created_at": "2025-11-24T10:30:00Z",
  "sent_at": "2025-11-24T10:30:05Z"
}
```

**Authorization:** Users can only view their own notifications (403 if `user_id` mismatch).

#### `GET /api/v1/notifications/history`
Get notification history for current user.

**Authentication:** Bearer token (JWT) required

**Query Parameters:**
- `channel` (optional): Filter by channel (email, webhook, push)
- `status` (optional): Filter by status (pending, sent, failed)
- `limit` (default: 50, max: 200): Results per page
- `offset` (default: 0): Pagination offset

**Response:** `200 OK`
```json
[
  {
    "id": 1234,
    "user_id": "user123",
    "channel": "email",
    "status": "sent",
    ...
  },
  ...
]
```

#### `POST /api/v1/notifications/send/adhoc`
Send ad-hoc notification without template (used by Agent Service).

**Authentication:** Bearer token (JWT) required

**Request Body:**
```json
{
  "recipient": "andreas@test.com",
  "subject": "Geopolitical Analysis Report",
  "body": "# Executive Summary\n\nTensions in the South China Sea...",
  "body_format": "markdown"
}
```

**Security:** Users can only send to their own email address (validated against JWT `email` claim).

**Response:** `201 Created` (same as `/send`)

### Templates

#### `GET /api/v1/notifications/templates`
List all available notification templates.

**Authentication:** Bearer token (JWT) required

**Query Parameters:**
- `channel` (optional): Filter by channel

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "osint_alert_email",
    "channel": "email",
    "subject": "OSINT Alert: {{ alert.title }}",
    "body": "Alert: {{ alert.title }}\n\nSeverity: {{ alert.severity }}...",
    "variables": ["alert"],
    "created_at": "2025-10-14T09:00:00Z",
    "updated_at": null
  },
  ...
]
```

#### `POST /api/v1/notifications/templates`
Create a new notification template.

**Authentication:** Bearer token (JWT) required

**Request Body:**
```json
{
  "name": "custom_alert",
  "channel": "email",
  "subject": "Custom Alert: {{ title }}",
  "body": "<h2>{{ title }}</h2><p>{{ message }}</p>",
  "variables": ["title", "message"]
}
```

**Response:** `201 Created`

### Preferences

#### `GET /api/v1/notifications/preferences`
Get notification preferences for current user.

**Authentication:** Bearer token (JWT) required

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": "user123",
  "email_enabled": true,
  "webhook_enabled": false,
  "push_enabled": false,
  "webhook_url": null,
  "fcm_token": null,
  "filters": {
    "excluded_events": ["feed.new_article"]
  },
  "created_at": "2025-11-20T08:00:00Z",
  "updated_at": "2025-11-24T10:00:00Z"
}
```

#### `POST /api/v1/notifications/preferences`
Update notification preferences.

**Authentication:** Bearer token (JWT) required

**Request Body:**
```json
{
  "email_enabled": true,
  "webhook_enabled": true,
  "webhook_url": "https://example.com/webhook",
  "filters": {
    "excluded_events": ["feed.new_article"]
  }
}
```

**Response:** `200 OK` (updated preferences)

### Testing

#### `POST /api/v1/notifications/test`
Send a test notification (for development/debugging).

**Authentication:** Bearer token (JWT) required

**Request Body:**
```json
{
  "channel": "email",
  "recipient": "test@example.com",
  "template_name": "osint_alert_email",
  "test_data": {
    "alert": {
      "title": "Test Alert",
      "severity": "low",
      "message": "This is a test"
    }
  }
}
```

**Response:** `200 OK`
```json
{
  "status": "sent",
  "message": "Test email sent to test@example.com"
}
```

#### `POST /api/v1/notifications/send/secure`
Send notification with full production hardening.

**Authentication:** Bearer token (JWT) required

**Features:**
- Input validation (webhooks, emails, payloads)
- Channel-specific rate limiting
- Delivery retry logic with exponential backoff
- Dead Letter Queue for failed deliveries
- HTML sanitization (XSS prevention)
- SSRF attack prevention
- RFC 5322 email validation

**Request Body:**
```json
{
  "user_id": "user123",
  "channel": "email",
  "subject": "Security Alert",
  "content": "<h1>Important Alert</h1>",
  "metadata": {
    "email": "user@example.com",
    "priority": "high"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": 1234,
  "user_id": "user123",
  "channel": "email",
  "status": "pending",
  "subject": "Security Alert",
  "content": "<h1>Important Alert</h1>",
  "metadata": {
    "email": "user@example.com",
    "priority": "high"
  },
  "error_message": null,
  "created_at": "2025-11-24T10:30:00Z",
  "sent_at": null
}
```

**Error Response (Rate Limit Exceeded):** `429 Too Many Requests`
```json
{
  "detail": {
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded for email",
    "limits": {
      "user_remaining": 0,
      "user_limit": 100,
      "channel_remaining": 5,
      "channel_limit": 50
    }
  }
}
```

#### `GET /api/v1/notifications/delivery/status/{notification_id}`
Get delivery status with retry history.

**Authentication:** Bearer token (JWT) required

**Response:** `200 OK`
```json
{
  "notification_id": 1234,
  "status": "retrying",
  "channel": "webhook",
  "created_at": "2025-11-24T10:30:00Z",
  "sent_at": null,
  "delivery_attempts": [
    {
      "attempt_number": 1,
      "timestamp": "2025-11-24T10:30:05Z",
      "status": "failed",
      "error": "Connection timeout",
      "next_retry": "2025-11-24T10:32:05Z"
    },
    {
      "attempt_number": 2,
      "timestamp": "2025-11-24T10:32:05Z",
      "status": "failed",
      "error": "Connection timeout",
      "next_retry": "2025-11-24T10:36:05Z"
    }
  ],
  "total_attempts": 2,
  "error_message": "Connection timeout"
}
```

**Authorization:** Users can only view their own notifications (403 if `user_id` mismatch).

### Admin Endpoints

All admin endpoints require `admin` role in JWT token. Unauthorized access attempts are logged.

#### `GET /api/v1/admin/jwt/info`
Get JWT rotation status and metadata.

**Authentication:** Bearer token (JWT) with admin role required

**Response:** `200 OK`
```json
{
  "status": "success",
  "rotation_info": {
    "last_rotation": "2025-11-24T08:00:00Z",
    "key_age_hours": 16,
    "next_rotation": "2025-11-25T08:00:00Z",
    "grace_period_active": false,
    "grace_period_expires": null
  }
}
```

#### `POST /api/v1/admin/jwt/rotate`
Manually rotate JWT signing keys.

**Authentication:** Bearer token (JWT) with admin role required

**Query Parameters:**
- `reason` (optional): Rotation reason (logged)

**Request Example:**
```bash
POST /api/v1/admin/jwt/rotate?reason=security_incident
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "JWT keys rotated successfully",
  "rotation_info": {
    "rotation_time": "2025-11-24T10:45:00Z",
    "reason": "security_incident",
    "old_key_expires": "2025-11-24T11:45:00Z",
    "grace_period_hours": 1
  }
}
```

**Security:** All rotation operations are logged with admin user ID and reason.

#### `GET /api/v1/admin/rate-limit/user/{user_id}`
Get rate limit statistics for a specific user.

**Authentication:** Bearer token (JWT) with admin role required

**Response:** `200 OK`
```json
{
  "status": "success",
  "user_id": "user123",
  "rate_limits": {
    "email": {
      "hourly": {
        "current": 45,
        "limit": 100,
        "remaining": 55,
        "reset_at": "2025-11-24T11:00:00Z"
      },
      "daily": {
        "current": 234,
        "limit": 1000,
        "remaining": 766,
        "reset_at": "2025-11-25T00:00:00Z"
      }
    },
    "webhook": {
      "hourly": {
        "current": 12,
        "limit": 50,
        "remaining": 38,
        "reset_at": "2025-11-24T11:00:00Z"
      }
    }
  }
}
```

#### `POST /api/v1/admin/rate-limit/user/{user_id}/reset`
Reset rate limits for a specific user.

**Authentication:** Bearer token (JWT) with admin role required

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Rate limits reset for user user123",
  "reset_info": {
    "user_id": "user123",
    "channels_reset": ["email", "webhook", "push"],
    "reset_at": "2025-11-24T10:50:00Z",
    "reset_by": "admin_user"
  }
}
```

**Security:** All reset operations are logged with admin user ID.

#### `GET /api/v1/admin/queue/stats`
Get delivery queue statistics.

**Authentication:** Bearer token (JWT) with admin role required

**Response:** `200 OK`
```json
{
  "status": "success",
  "queue_stats": {
    "pending_deliveries": 45,
    "retrying_deliveries": 12,
    "dlq_items": 3,
    "active_workers": 5,
    "average_wait_time_seconds": 2.3,
    "queues": {
      "email": {
        "pending": 30,
        "retrying": 8
      },
      "webhook": {
        "pending": 15,
        "retrying": 4
      }
    }
  }
}
```

#### `GET /api/v1/admin/dlq/list`
List items in Dead Letter Queue.

**Authentication:** Bearer token (JWT) with admin role required

**Query Parameters:**
- `limit` (default: 100, max: 1000): Max items to return

**Response:** `200 OK`
```json
{
  "status": "success",
  "count": 3,
  "dlq_items": [
    {
      "notification_id": 5678,
      "user_id": "user456",
      "channel": "webhook",
      "failed_at": "2025-11-24T09:30:00Z",
      "attempts": 3,
      "last_error": "Connection timeout after 30s",
      "payload": {
        "webhook_url": "https://example.com/webhook",
        "subject": "Alert"
      }
    }
  ]
}
```

#### `POST /api/v1/admin/dlq/retry/{notification_id}`
Retry a notification from Dead Letter Queue.

**Authentication:** Bearer token (JWT) with admin role required

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Notification 5678 requeued for delivery",
  "retry_info": {
    "notification_id": 5678,
    "requeued_at": "2025-11-24T10:55:00Z",
    "priority": "normal",
    "estimated_delivery": "2025-11-24T10:55:30Z"
  }
}
```

**Error Response (Not Found):** `404 Not Found`
```json
{
  "detail": "Notification 5678 not found in DLQ"
}
```

**Security:** All retry operations are logged with admin user ID.

#### `GET /api/v1/admin/health/detailed`
Get detailed system health information.

**Authentication:** Bearer token (JWT) with admin role required

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "notification-service",
  "version": "1.0.0",
  "jwt_rotation": {
    "last_rotation": "2025-11-24T08:00:00Z",
    "key_age_hours": 16,
    "next_rotation": "2025-11-25T08:00:00Z",
    "grace_period_active": false
  },
  "delivery_queue": {
    "pending_deliveries": 45,
    "retrying_deliveries": 12,
    "dlq_items": 3
  },
  "features": {
    "jwt_rotation": true,
    "rate_limiting": true,
    "input_validation": true,
    "delivery_retry": true,
    "dead_letter_queue": true
  }
}
```

**Degraded Response:** `200 OK`
```json
{
  "status": "degraded",
  "error": "Redis connection lost"
}
```

### Health & Metrics

#### `GET /health`
Service health check.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "notification-service",
  "version": "1.0.0"
}
```

#### `GET /metrics`
Prometheus metrics endpoint for monitoring.

**Response:** `200 OK` (Prometheus format)
```
# HELP notification_delivery_total Total notification deliveries
# TYPE notification_delivery_total counter
notification_delivery_total{channel="email",status="sent"} 1234
notification_delivery_total{channel="email",status="failed"} 45
notification_delivery_total{channel="webhook",status="sent"} 567
notification_delivery_total{channel="webhook",status="failed"} 12

# HELP email_delivery_attempts Email delivery attempts
# TYPE email_delivery_attempts counter
email_delivery_attempts{status="success"} 1200
email_delivery_attempts{status="failed"} 45

# HELP webhook_delivery_attempts Webhook delivery attempts
# TYPE webhook_delivery_attempts counter
webhook_delivery_attempts{status="success"} 550
webhook_delivery_attempts{status="failed"} 12
webhook_delivery_attempts{status="circuit_open"} 5
```

#### `GET /`
Service information.

**Response:** `200 OK`
```json
{
  "service": "notification-service",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp` |
| `REDIS_URL` | Redis connection URL (Celery broker) | `redis://redis:6379/0` |
| `RABBITMQ_URL` | RabbitMQ connection URL | `amqp://news_user:news_rabbitmq_2024@rabbitmq:5672/` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | `notifications@example.com` |
| `SMTP_PASSWORD` | SMTP password or app password | `your-app-password` |
| `SMTP_FROM` | Sender email address | `notifications@newsplatform.com` |
| `JWT_SECRET_KEY` | JWT signing secret (min 32 chars) | `<auto-generated or set explicitly>` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_PORT` | 8005 | HTTP server port |
| `DEBUG` | false | Enable debug mode |
| `ENVIRONMENT` | development | Environment name |
| `LOG_LEVEL` | INFO | Logging level |
| `SMTP_FROM_NAME` | News Platform | Sender display name |
| `SMTP_USE_TLS` | true | Use TLS for SMTP |
| `SMTP_USE_SSL` | false | Use SSL for SMTP |
| `SMTP_TIMEOUT` | 30 | SMTP connection timeout (seconds) |
| `MAX_RETRY_ATTEMPTS` | 3 | Max retry attempts for delivery |
| `RETRY_BACKOFF_BASE` | 2 | Exponential backoff base |
| `RETRY_BACKOFF_MAX` | 300 | Max backoff time (seconds) |
| `RATE_LIMIT_ENABLED` | true | Enable rate limiting |
| `RATE_LIMIT_PER_USER_HOUR` | 100 | Max notifications per user per hour |
| `RATE_LIMIT_PER_USER_DAY` | 1000 | Max notifications per user per day |
| `WEBHOOK_TIMEOUT` | 30 | Webhook HTTP timeout (seconds) |
| `WEBHOOK_MAX_RETRIES` | 3 | Webhook max retries |
| `FCM_ENABLED` | false | Enable Firebase Cloud Messaging |
| `FCM_SERVER_KEY` | null | FCM server key (if FCM enabled) |

### Production Hardening Features

The notification service includes comprehensive production hardening features for security, reliability, and observability.

#### JWT Key Rotation

Automatic and manual JWT signing key rotation with grace period support.

**Configuration:**
```env
JWT_SECRET_KEY=<auto-generated or set explicitly>
JWT_ROTATION_ENABLED=true
JWT_ROTATION_INTERVAL_HOURS=24
JWT_GRACE_PERIOD_HOURS=1
```

**Features:**
- **Automatic rotation**: Keys rotate every 24 hours by default
- **Grace period**: Old keys remain valid for 1 hour after rotation
- **Manual rotation**: Admin endpoint for emergency rotation
- **Redis-backed**: Key metadata stored in Redis for distributed systems
- **Audit logging**: All rotation events logged with reason and timestamp

**Use Cases:**
- Security incident response (manual rotation)
- Scheduled key rotation (automatic)
- Zero-downtime key updates (grace period)

#### Rate Limiting

Channel-specific rate limiting with per-user and global limits.

**Configuration:**
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_USER_HOUR=100
RATE_LIMIT_PER_USER_DAY=1000
RATE_LIMIT_EMAIL_CHANNEL_HOUR=5000
RATE_LIMIT_WEBHOOK_CHANNEL_HOUR=2000
```

**Features:**
- **Per-user limits**: Hourly and daily limits per user
- **Channel-specific limits**: Different limits for email, webhook, push
- **Global limits**: System-wide rate limiting per channel
- **Redis-backed**: Distributed rate limiting across multiple instances
- **Admin controls**: View and reset user rate limits

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 2025-11-24T11:00:00Z
```

#### Input Validation & Sanitization

Comprehensive input validation to prevent security vulnerabilities.

**Features:**
- **Email validation**: RFC 5322 compliant email address validation
- **Webhook validation**:
  - URL format validation
  - SSRF attack prevention (blocks private IP ranges)
  - Protocol validation (HTTPS only in production)
- **Payload validation**:
  - Size limits (max 1MB per notification)
  - Structure validation
  - Type checking
- **HTML sanitization**: XSS prevention for HTML email content

**Protected Against:**
- Cross-Site Scripting (XSS)
- Server-Side Request Forgery (SSRF)
- Email injection attacks
- Payload injection

**Example Validation:**
```python
# Email validation
is_valid, error = validator.validate_email_address("user@example.com")
# Returns: (True, None)

# Webhook validation (blocks SSRF)
is_valid, error = validator.validate_webhook("http://localhost/admin")
# Returns: (False, "Private IP addresses not allowed")

# HTML sanitization
sanitized = validator.sanitize("<script>alert('xss')</script><p>Hello</p>")
# Returns: "<p>Hello</p>"
```

#### Delivery Queue & Retry Logic

Reliable delivery with exponential backoff and Dead Letter Queue.

**Configuration:**
```env
DELIVERY_QUEUE_ENABLED=true
DELIVERY_RETRY_ATTEMPTS=3
DELIVERY_BACKOFF_BASE=2
DELIVERY_BACKOFF_MAX=300
DLQ_ENABLED=true
DLQ_MAX_AGE_DAYS=7
```

**Features:**
- **Priority queues**: High and normal priority
- **Exponential backoff**:
  - Attempt 1: Immediate
  - Attempt 2: 2 seconds
  - Attempt 3: 4 seconds
  - Attempt 4: 8 seconds (capped at 300 seconds)
- **Dead Letter Queue**: Failed notifications after max retries
- **Retry history**: Full audit trail of delivery attempts
- **Admin controls**: View DLQ, manually retry failed notifications

**Retry Schedule Example:**
```
Notification created: 10:00:00
Attempt 1 (failed):   10:00:01
Attempt 2 (failed):   10:00:03  (+2s)
Attempt 3 (failed):   10:00:07  (+4s)
Attempt 4 (failed):   10:00:15  (+8s)
→ Moved to DLQ:      10:00:15
```

#### Circuit Breaker Pattern

Webhook delivery includes circuit breaker for failing endpoints.

**Configuration:**
```env
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_THRESHOLD=3
CIRCUIT_BREAKER_TIMEOUT=300
CIRCUIT_BREAKER_RESET_TIMEOUT=60
```

**States:**
- **Closed**: Normal operation, requests pass through
- **Open**: Endpoint failing, requests blocked for 5 minutes
- **Half-Open**: Testing if endpoint recovered

**Metrics:**
```
webhook_delivery_attempts{status="circuit_open"} 5
```

**Benefits:**
- Prevents cascading failures
- Reduces load on failing endpoints
- Automatic recovery detection
- Improved system stability

### SMTP Provider Configuration

**Gmail:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

**SendGrid:**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
```

**Mailgun:**
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-smtp-password
SMTP_USE_TLS=true
```

**Amazon SES:**
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
SMTP_USE_TLS=true
```

---

## Event Integration

### Events Consumed

The service listens to RabbitMQ events on exchange `events` (topic type):

| Event | Routing Key | Description |
|-------|-------------|-------------|
| **OSINT Alert** | `osint.alert.triggered` | OSINT service detected a matching alert |
| **Research Complete** | `research.completed` | Research service finished a task |
| **Analysis Complete** | `analysis.completed` | Content analysis service finished analyzing an article |
| **New Article** | `feed.new_article` | Feed service ingested a new RSS article |

**Event Format:**
```json
{
  "event_type": "osint.alert.triggered",
  "user_id": "user123",
  "data": {
    "alert_name": "High Severity Event",
    "severity": "high",
    "message": "Security incident detected",
    "email": "user@example.com"
  }
}
```

**Event Processing Logic:**
1. Receive event from RabbitMQ
2. Get user's notification preferences
3. Check if event type is excluded in filters
4. Create notification log(s) for enabled channels
5. Queue Celery task(s) for delivery
6. Return acknowledgment to RabbitMQ

### Events Published

None - the service only consumes events, does not publish any.

---

## Deployment

### Docker Compose (Development)

```yaml
notification-service:
  build:
    context: .
    dockerfile: services/notification-service/Dockerfile.dev
  ports:
    - "8105:8000"
  environment:
    - DATABASE_URL=postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp
    - REDIS_URL=redis://:redis_secret_2024@redis:6379/0
    - RABBITMQ_URL=amqp://news_user:news_rabbitmq_2024@rabbitmq:5672/
    - SMTP_HOST=smtp.gmail.com
    - SMTP_PORT=587
    - SMTP_USER=${SMTP_USER}
    - SMTP_PASSWORD=${SMTP_PASSWORD}
    - SMTP_FROM=notifications@newsplatform.com
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  volumes:
    - ./services/notification-service/app:/app/app:ro
  depends_on:
    - postgres
    - redis
    - rabbitmq
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "/usr/local/bin/healthcheck.sh"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### Celery Worker (Required)

The service requires a Celery worker to process background tasks:

```bash
# Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Start Celery Beat for periodic tasks (retry failed deliveries)
celery -A app.workers.celery_app beat --loglevel=info
```

**Docker Compose Worker:**
```yaml
notification-worker:
  build:
    context: .
    dockerfile: services/notification-service/Dockerfile.dev
  command: celery -A app.workers.celery_app worker --loglevel=info
  environment:
    # Same as notification-service
  depends_on:
    - postgres
    - redis
    - rabbitmq

notification-beat:
  build:
    context: .
    dockerfile: services/notification-service/Dockerfile.dev
  command: celery -A app.workers.celery_app beat --loglevel=info
  environment:
    # Same as notification-service
  depends_on:
    - redis
```

### Health Check

The service implements a multi-stage health check:
1. Validate critical imports (`from app.main import app`)
2. Check HTTP endpoint (`/health`)

**Health Check Script:**
```bash
#!/bin/sh
# Step 1: Validate imports
python3 -c "from app.main import app" 2>/dev/null || exit 1

# Step 2: Check HTTP endpoint
curl -f http://localhost:8000/health || exit 1

exit 0
```

### Scaling Considerations

**Horizontal Scaling:**
- Multiple API instances can run behind a load balancer
- Each instance connects to shared PostgreSQL, Redis, RabbitMQ
- No sticky sessions required (stateless)

**Celery Worker Scaling:**
- Scale workers independently: `celery -A app.workers.celery_app worker --concurrency=10`
- Recommended: 1 worker per CPU core
- Monitor queue depth and adjust accordingly

**Database Connection Pool:**
- Current: `NullPool` (no pooling)
- **Recommendation:** Use connection pooling for production (see Issues report)

---

## Usage Examples

### Send Email Notification (Curl)

```bash
# Get JWT token first
TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"andreas","password":"Aug2012#"}' | jq -r .access_token)

# Send notification
curl -X POST http://localhost:8105/api/v1/notifications/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "andreas",
    "channel": "email",
    "subject": "Test Notification",
    "content": "<h1>Test</h1><p>This is a test notification</p>",
    "metadata": {
      "email": "andreas@test.com"
    }
  }'
```

### Send Hardened Notification (Curl)

```bash
# Send notification with production hardening
curl -X POST http://localhost:8105/api/v1/notifications/send/secure \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "andreas",
    "channel": "email",
    "subject": "Security Alert",
    "content": "<h1>Important Alert</h1><p>Suspicious activity detected</p>",
    "metadata": {
      "email": "andreas@test.com",
      "priority": "high"
    }
  }'
```

### Send Notification with Template (Python)

```python
import httpx
import asyncio

async def send_notification():
    # Get token
    auth_response = await httpx.AsyncClient().post(
        "http://localhost:8100/api/v1/auth/login",
        json={"username": "andreas", "password": "Aug2012#"}
    )
    token = auth_response.json()["access_token"]

    # Send notification
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8105/api/v1/notifications/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": "andreas",
                "channel": "email",
                "template_name": "osint_alert_email",
                "template_variables": {
                    "alert": {
                        "title": "Security Incident",
                        "severity": "high",
                        "message": "Unauthorized access detected",
                        "triggered_at": "2025-11-24T10:30:00Z"
                    }
                },
                "metadata": {
                    "email": "andreas@test.com"
                }
            }
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

asyncio.run(send_notification())
```

### Publish Event to Trigger Notification (Python)

```python
import pika
import json

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=pika.PlainCredentials('news_user', 'news_rabbitmq_2024')
    )
)
channel = connection.channel()

# Declare exchange
channel.exchange_declare(
    exchange='events',
    exchange_type='topic',
    durable=True
)

# Publish event
event = {
    "event_type": "osint.alert.triggered",
    "user_id": "andreas",
    "data": {
        "alert_name": "High Severity Alert",
        "severity": "high",
        "message": "Security incident detected in region XYZ",
        "email": "andreas@test.com"
    }
}

channel.basic_publish(
    exchange='events',
    routing_key='osint.alert.triggered',
    body=json.dumps(event),
    properties=pika.BasicProperties(
        delivery_mode=2  # persistent
    )
)

print(f"Published event: {event['event_type']}")
connection.close()
```

### Update User Preferences (Curl)

```bash
# Update preferences to enable webhooks
curl -X POST http://localhost:8105/api/v1/notifications/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email_enabled": true,
    "webhook_enabled": true,
    "webhook_url": "https://myapp.example.com/webhook",
    "filters": {
      "excluded_events": ["feed.new_article"]
    }
  }'
```

### Admin - Check JWT Rotation Status (Curl)

```bash
# Get admin token (requires admin role)
ADMIN_TOKEN=$(curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"andreas","password":"Aug2012#"}' | jq -r .access_token)

# Get JWT rotation info
curl -X GET http://localhost:8105/api/v1/admin/jwt/info \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Admin - Manually Rotate JWT Keys (Curl)

```bash
# Rotate JWT keys (emergency rotation)
curl -X POST "http://localhost:8105/api/v1/admin/jwt/rotate?reason=security_incident" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Admin - Check User Rate Limits (Curl)

```bash
# Get rate limit stats for user
curl -X GET http://localhost:8105/api/v1/admin/rate-limit/user/andreas \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Reset user rate limits
curl -X POST http://localhost:8105/api/v1/admin/rate-limit/user/andreas/reset \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Admin - Manage Delivery Queue (Curl)

```bash
# Get queue statistics
curl -X GET http://localhost:8105/api/v1/admin/queue/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# List Dead Letter Queue items
curl -X GET "http://localhost:8105/api/v1/admin/dlq/list?limit=50" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Retry failed notification
curl -X POST http://localhost:8105/api/v1/admin/dlq/retry/5678 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Admin - Get Detailed Health (Curl)

```bash
# Get detailed system health
curl -X GET http://localhost:8105/api/v1/admin/health/detailed \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Admin - Complete Monitoring Workflow (Python)

```python
import httpx
import asyncio

async def monitor_notification_service():
    """Admin monitoring workflow"""

    # Login as admin
    async with httpx.AsyncClient() as client:
        # Get admin token
        auth_response = await client.post(
            "http://localhost:8100/api/v1/auth/login",
            json={"username": "andreas", "password": "Aug2012#"}
        )
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check system health
        health = await client.get(
            "http://localhost:8105/api/v1/admin/health/detailed",
            headers=headers
        )
        print(f"Health: {health.json()}")

        # Check queue stats
        queue_stats = await client.get(
            "http://localhost:8105/api/v1/admin/queue/stats",
            headers=headers
        )
        print(f"Queue Stats: {queue_stats.json()}")

        # Check JWT rotation status
        jwt_info = await client.get(
            "http://localhost:8105/api/v1/admin/jwt/info",
            headers=headers
        )
        print(f"JWT Rotation: {jwt_info.json()}")

        # Check DLQ items
        dlq = await client.get(
            "http://localhost:8105/api/v1/admin/dlq/list?limit=10",
            headers=headers
        )
        dlq_data = dlq.json()
        print(f"DLQ Items: {dlq_data['count']}")

        # Retry DLQ items if any
        if dlq_data['count'] > 0:
            for item in dlq_data['dlq_items']:
                retry = await client.post(
                    f"http://localhost:8105/api/v1/admin/dlq/retry/{item['notification_id']}",
                    headers=headers
                )
                print(f"Retried notification {item['notification_id']}: {retry.json()}")

asyncio.run(monitor_notification_service())
```

---

## Troubleshooting

### Common Issues

#### Service won't start

**Symptoms:** Container fails to start or exits immediately

**Causes & Solutions:**
1. **Database connection failure**
   ```bash
   # Check DATABASE_URL format
   echo $DATABASE_URL
   # Should be: postgresql+asyncpg://user:pass@host:port/db

   # Test connection
   docker exec -it news-postgres psql -U news_user -d news_mcp -c "SELECT 1"
   ```

2. **Redis connection failure**
   ```bash
   # Check Redis URL
   echo $REDIS_URL
   # Should be: redis://redis:6379/0

   # Test connection
   docker exec -it news-redis redis-cli ping
   ```

3. **RabbitMQ connection failure**
   ```bash
   # Check RabbitMQ URL
   echo $RABBITMQ_URL
   # Should be: amqp://user:pass@rabbitmq:5672/

   # Check RabbitMQ status
   docker exec -it news-rabbitmq rabbitmqctl status
   ```

#### Email notifications not sending

**Symptoms:** Notifications show status "pending" or "failed"

**Causes & Solutions:**
1. **SMTP credentials incorrect**
   ```bash
   # Check SMTP configuration
   docker exec -it notification-service env | grep SMTP

   # For Gmail: Ensure using app password (not account password)
   # Generate app password: https://myaccount.google.com/apppasswords
   ```

2. **Firewall blocking SMTP port**
   ```bash
   # Test SMTP connection
   telnet smtp.gmail.com 587
   # Should connect successfully
   ```

3. **Celery worker not running**
   ```bash
   # Check Celery worker logs
   docker logs notification-worker

   # Verify worker is processing tasks
   docker exec -it notification-worker celery -A app.workers.celery_app inspect active
   ```

4. **Rate limit exceeded**
   ```bash
   # Check notification logs
   docker exec -it news-postgres psql -U news_user -d news_mcp -c \
     "SELECT COUNT(*) FROM notification_logs WHERE user_id='andreas' AND created_at > NOW() - INTERVAL '1 hour';"

   # If count >= 100, user hit hourly rate limit
   # Solution: Adjust RATE_LIMIT_PER_USER_HOUR or wait
   ```

#### Webhook deliveries failing

**Symptoms:** Webhook notifications show status "failed"

**Causes & Solutions:**
1. **Webhook URL unreachable**
   ```bash
   # Test webhook URL manually
   curl -X POST https://myapp.example.com/webhook \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

2. **Circuit breaker open (Task 406)**
   ```bash
   # Check circuit breaker status in logs
   docker logs notification-service | grep "circuit breaker is OPEN"

   # Circuit breaker opens after 3 consecutive failures
   # Waits 5 minutes before retry
   # Solution: Fix webhook endpoint, wait for circuit to close
   ```

3. **Webhook timeout**
   ```bash
   # Increase timeout in environment
   WEBHOOK_TIMEOUT=60  # default: 30 seconds
   ```

#### RabbitMQ consumer not receiving events

**Symptoms:** Events published but notifications not created

**Causes & Solutions:**
1. **Consumer not started**
   ```bash
   # Check service logs for "Started consuming RabbitMQ events"
   docker logs notification-service | grep "RabbitMQ"

   # If not found, consumer failed to start
   # Check for connection errors
   ```

2. **Routing key mismatch**
   ```bash
   # Verify routing key in published event matches consumer bindings
   # Consumer listens to:
   # - osint.alert.triggered
   # - research.completed
   # - analysis.completed
   # - feed.new_article
   ```

3. **Event format incorrect**
   ```json
   // Expected format:
   {
     "event_type": "osint.alert.triggered",
     "user_id": "user123",
     "data": {
       "alert_name": "...",
       "severity": "...",
       "message": "...",
       "email": "user@example.com"
     }
   }
   ```

#### High memory usage

**Symptoms:** Container memory exceeds 1GB

**Current Issue:** Database connection pooling disabled (`NullPool`)

**Solutions:**
1. **Short-term:** Restart service periodically
   ```bash
   docker restart notification-service
   ```

2. **Long-term:** Enable connection pooling (see Issues report, P1-004)
   ```python
   # In app/core/database.py
   engine = create_async_engine(
       settings.DATABASE_URL,
       pool_size=5,
       max_overflow=10,
       pool_pre_ping=True
   )
   ```

#### Celery tasks stuck in pending

**Symptoms:** Notifications created but never delivered

**Causes & Solutions:**
1. **Redis connection lost**
   ```bash
   # Restart worker to reconnect
   docker restart notification-worker
   ```

2. **Worker crashed**
   ```bash
   # Check worker logs
   docker logs notification-worker --tail 100

   # Restart worker
   docker restart notification-worker
   ```

3. **Task timeout**
   ```bash
   # Check Celery configuration
   # Default task_time_limit: 300 seconds (5 minutes)
   # Increase if needed:
   CELERY_TASK_TIME_LIMIT=600
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Set environment variable
DEBUG=true
LOG_LEVEL=DEBUG

# Restart service
docker restart notification-service

# View detailed logs
docker logs -f notification-service
```

### Monitoring

**Prometheus Metrics:**
- `notification_delivery_total` - Total deliveries by channel and status
- `email_delivery_attempts` - Email delivery attempts by status
- `webhook_delivery_attempts` - Webhook delivery attempts by status (includes circuit_open)

**Celery Monitoring (Flower):**
```bash
# Install Flower
pip install flower

# Start Flower
celery -A app.workers.celery_app flower --port=5555

# Access: http://localhost:5555
```

---

## Code Structure

```
notification-service/
├── app/
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API endpoint handlers
│   │   ├── notifications.py      # Notification CRUD operations
│   │   ├── notifications_enhanced.py  # Production hardened endpoints
│   │   ├── preferences.py        # User preference management
│   │   ├── admin.py             # Admin endpoints (JWT, rate limits, DLQ)
│   │   ├── health.py            # Health check endpoints
│   │   └── metrics.py           # Prometheus metrics endpoints
│   ├── core/                     # Core infrastructure
│   │   ├── config.py            # Configuration management (Settings)
│   │   ├── database.py          # SQLAlchemy async engine and session
│   │   ├── auth.py              # JWT authentication dependency
│   │   ├── metrics.py           # Prometheus metrics definitions
│   │   ├── rate_limiter.py      # Rate limiting logic (shared)
│   │   ├── jwt_rotation.py      # JWT key rotation manager
│   │   ├── notification_rate_limiter.py  # Channel-specific rate limiting
│   │   ├── delivery_queue.py    # Delivery queue & retry logic
│   │   └── input_validation.py  # Input validation & sanitization
│   ├── models/                   # SQLAlchemy ORM models
│   │   └── notification.py      # NotificationLog, NotificationPreference, etc.
│   ├── schemas/                  # Pydantic request/response schemas
│   │   └── notification.py      # Request/response DTOs
│   ├── services/                 # Business logic services
│   │   ├── notification_service.py  # Core notification logic
│   │   ├── email_service.py         # SMTP email delivery
│   │   ├── webhook_service.py       # Webhook HTTP delivery (+ circuit breaker)
│   │   ├── template_service.py      # Jinja2 template rendering
│   │   ├── template_defaults.py     # Default template initialization
│   │   ├── preference_service.py    # User preferences management
│   │   └── delivery_tracker.py      # Delivery attempt tracking
│   ├── events/                   # RabbitMQ event consumers
│   │   ├── rabbitmq_consumer.py  # Main event consumer
│   │   ├── base_consumer.py      # Base consumer class
│   │   ├── osint_consumer.py     # OSINT event handler
│   │   ├── research_consumer.py  # Research event handler
│   │   ├── analysis_consumer.py  # Analysis event handler
│   │   └── feed_consumer.py      # Feed event handler
│   └── workers/                  # Celery tasks
│       ├── celery_app.py         # Celery application setup
│       └── tasks.py              # Async delivery tasks
├── alembic/                      # Database migrations
│   ├── versions/
│   │   └── 001_initial_notification_schema.py
│   └── env.py
├── tests/                        # Test suite (3,410 LOC)
│   ├── conftest.py
│   ├── test_api_notifications.py
│   ├── test_api_preferences.py
│   ├── test_api_admin.py        # Admin endpoint tests
│   ├── test_email_service.py
│   ├── test_webhook_service.py
│   ├── test_template_service.py
│   ├── test_celery_tasks.py
│   ├── test_rabbitmq_consumer.py
│   ├── test_e2e_notification_flow.py
│   ├── test_jwt_rotation.py     # JWT rotation tests
│   ├── test_rate_limiting.py    # Rate limiting tests
│   ├── test_input_validation.py # Validation tests
│   ├── test_models.py
│   ├── test_health.py
│   └── test_performance.py
├── templates/                    # Notification templates
│   ├── email_alert.html
│   └── webhook_payload.json
├── scripts/                      # Utility scripts
│   ├── healthcheck.sh
│   ├── startup.sh
│   └── verify-docker-setup.sh
├── docs/                         # Service documentation
│   ├── API.md
│   ├── ARCHITECTURE_SUMMARY.md
│   ├── CONFIGURATION.md
│   ├── DEPLOYMENT.md
│   ├── EVENTS.md
│   ├── EXAMPLES.md
│   ├── TEMPLATES.md
│   ├── TROUBLESHOOTING.md
│   ├── architecture/
│   ├── api/
│   ├── schemas/
│   └── diagrams/
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── Dockerfile.dev                # Development Docker image
├── pytest.ini                    # Pytest configuration
├── alembic.ini                   # Alembic configuration
└── README.md                     # Quick start guide
```

**Key Production Hardening Modules:**

| Module | Purpose | Features |
|--------|---------|----------|
| `core/jwt_rotation.py` | JWT key rotation | Automatic rotation, grace period, manual rotation |
| `core/notification_rate_limiter.py` | Rate limiting | Per-user, per-channel, Redis-backed |
| `core/delivery_queue.py` | Delivery queue | Priority queues, retry logic, DLQ |
| `core/input_validation.py` | Input validation | Email/webhook/payload validation, sanitization |
| `api/admin.py` | Admin endpoints | JWT rotation, rate limits, queue management |
| `api/notifications_enhanced.py` | Hardened notifications | Validation, rate limiting, retry logic |

---

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.115.0 | REST API framework |
| ASGI Server | Uvicorn | 0.30.0 | Production ASGI server |
| Database | PostgreSQL | 14+ | Data persistence (shared `news_mcp`) |
| ORM | SQLAlchemy | 2.0.35 | Async database ORM |
| Migration Tool | Alembic | 1.13.0 | Database schema versioning |
| Task Queue | Celery | 5.3.6 | Async task processing |
| Message Broker | Redis | 7+ | Celery broker and result backend |
| Event Bus | RabbitMQ | 3.12+ | Inter-service event communication |
| AMQP Client | aio-pika | 9.4.0 | Async RabbitMQ client |
| SMTP Client | aiosmtplib | 3.0.1 | Async email sending |
| Template Engine | Jinja2 | 3.1.2 | Template rendering |
| HTTP Client | httpx | 0.27.0 | Webhook delivery |
| Validation | Pydantic | 2.8.0 | Request/response validation |
| Auth | python-jose | 3.3.0 | JWT token validation |
| Rate Limiting | slowapi | 0.1.9 | API rate limiting |
| Monitoring | prometheus-client | 0.20.0 | Metrics collection |
| Logging | structlog | 24.4.0 | Structured logging |
| Circuit Breaker | news-mcp-common | 1.0.0 | Resilience patterns (Task 406) |

---

## Testing

The service has comprehensive test coverage (3,410 LOC):

**Test Categories:**
- **Unit Tests:** Individual service methods
- **Integration Tests:** Database, RabbitMQ, Celery integration
- **E2E Tests:** Full notification flow from event to delivery
- **Performance Tests:** Load testing, concurrency testing

**Running Tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_email_service.py -v

# Run performance tests
pytest tests/test_performance.py -v
```

**Test Configuration:**
- Test database: Separate from production
- Mock SMTP server: Prevents actual email sending
- Mock webhook endpoints: Local test server
- RabbitMQ test exchange: Isolated from production events

---

## Related Documentation

- **API Specification:** [notification-service.yaml](../openapi-specs/notification-service.yaml)
- **Code Quality Report:** [notification-service-issues.md](../issues/notification-service-issues.md)
- **Architecture Overview:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
- **Backend Development Guide:** [CLAUDE.backend.md](../../CLAUDE.backend.md)
- **Event-Driven Architecture:** [Event Integration Patterns](../../docs/architecture/EVENT_DRIVEN_ARCHITECTURE.md)
- **Circuit Breaker Pattern:** [ADR-035: Circuit Breaker Pattern](../../docs/decisions/ADR-035-circuit-breaker-pattern.md)
- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](../../docs/guides/DEPLOYMENT_GUIDE.md)
- **Troubleshooting Guide:** [notification-service-troubleshooting.md](./notification-service-troubleshooting.md)

---

**Service Version:** 1.0.0
**Default Port:** 8105
**Last Updated:** 2025-12-22
**Status:** Production-ready with comprehensive hardening features
**Maintainer:** News Microservices Team

**Production Hardening Status:**
- ✅ JWT Key Rotation (automatic + manual)
- ✅ Rate Limiting (per-user, per-channel)
- ✅ Input Validation & Sanitization (XSS, SSRF prevention)
- ✅ Delivery Queue with Retry Logic (exponential backoff)
- ✅ Dead Letter Queue (DLQ)
- ✅ Circuit Breaker Pattern (webhook resilience)
- ✅ Admin Endpoints (10 endpoints for monitoring and management)
- ✅ Prometheus Metrics
- ✅ Comprehensive Audit Logging

# Research Service API

Base path: `/api/v1` | Default port: `8103` (internal 8003)

Authentication: All endpoints except `/api/v1/health` and `GET /api/v1/templates/functions` require a JWT access token (`Authorization: Bearer <token>`). Service-to-service calls reuse the same JWT validation.

---

## Research Tasks (`/api/v1/research`)

### POST /api/v1/research
Create a research task or execute a specialised function.

**Request Body — ResearchTaskCreate**
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `query` | string | Yes | 10–2000 characters |
| `model_name` | string | No | `sonar` \| `sonar-pro` \| `sonar-reasoning-pro` (default `sonar`) |
| `depth` | string | No | `quick` \| `standard` \| `deep` (default `standard`) |
| `feed_id`, `article_id` | UUID | No | Optional cross-service references |
| `legacy_feed_id`, `legacy_article_id` | integer | No | Migration compatibility |
| `research_function` | string | No | e.g. `feed_source_assessment`, `fact_check`, `trend_analysis` |
| `function_parameters` | object | No | Parameters passed to specialised function |

**Response — 201** → `ResearchTaskResponse` (initial status `pending` unless a function returns immediately).  
Errors: `400` invalid payload, `401` unauthorized.

---

### GET /api/v1/research/{task_id}
Return a single task owned by the caller.  
**Response:** `ResearchTaskResponse` (`200`).  
Errors: `404` task not found.

---

### GET /api/v1/research
List tasks with pagination.

**Query Parameters**
| Name | Type | Notes |
| --- | --- | --- |
| `status` | string | `pending`\|`processing`\|`completed`\|`failed` |
| `feed_id` | UUID | Filter by feed |
| `page`, `page_size` | integer | Defaults 1, 50 (max 100) |

**Response:** `ResearchTaskList` (`tasks`, `total`, `page`, `page_size`, `has_more`).

---

### POST /api/v1/research/batch
Create multiple tasks (max 10 queries).

**Request Body — ResearchTaskBatchCreate**
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `queries` | array[string] | Yes | 1–10 queries |
| `model_name`, `depth` | string | No | Override defaults |
| `feed_id`, `legacy_feed_id` | UUID/int | No | Optional scope |

**Response:** `list[ResearchTaskResponse]` (`200`).

---

### GET /api/v1/research/feed/{feed_id}
Latest tasks for a feed. Optional `limit` (default 10).  
**Response:** `list[ResearchTaskResponse]`.

---

### GET /api/v1/research/history
Historical tasks (supports `days`, `page`, `page_size`).  
**Response:** `ResearchTaskList`.

---

### GET /api/v1/research/stats
Usage statistics covering cost and tokens.  
**Response:** `UsageStats` (`total_requests`, `total_tokens`, `total_cost`, per-model aggregates).

---

## Templates (`/api/v1/templates`)

### POST /api/v1/templates
Create a reusable template.

**Body — TemplateCreate**
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | Yes | 3–100 chars |
| `query_template` | string | Yes | Supports `{{variable}}` syntax |
| `parameters` | object | No | Variable metadata |
| `default_model` | string | No | `sonar`/`sonar-pro`/`sonar-reasoning-pro` |
| `default_depth` | string | No | `quick`/`standard`/`deep` |
| `is_public` | bool | No | Share template with others |
| `research_function` | string | No | Attach specialised function |
| `function_parameters` | object | No | Default parameters |

**Response:** `TemplateResponse` (`201`).

---

### GET /api/v1/templates
List caller templates and optional public templates (`include_public=true`).  
**Response:** `list[TemplateResponse]`.

---

### GET /api/v1/templates/{template_id}
Fetch single template.  
**Response:** `TemplateResponse`.  
`404` if missing or no access.

---

### GET /api/v1/templates/functions
List specialised research functions (no auth required).  
Example:
```json
{
  "functions": [
    {"name": "feed_source_assessment", "description": "Assess credibility...", "default_model": "sonar", "default_depth": "standard"},
    {"name": "fact_check", "description": "Fact-check claims", "default_model": "sonar-reasoning-pro", "default_depth": "deep"}
  ]
}
```

---

### PUT /api/v1/templates/{template_id}
Update template fields (owner only).  
**Body:** `TemplateUpdate`.  
**Response:** `TemplateResponse`.

---

### DELETE /api/v1/templates/{template_id}
Soft-delete template.  
**Response:** `204 No Content`.

---

### POST /api/v1/templates/{template_id}/preview
Render and estimate cost without creating a task.

**Body — TemplateApply** (variables, optional model/depth/feed/article).  
**Response:** `TemplatePreview` (`rendered_query`, `estimated_cost`).

---

### POST /api/v1/templates/{template_id}/apply
Apply template, optionally execute attached function, and create a task.

**Response:** `ResearchTaskResponse` (`200`).

---

## Research Runs (`/api/v1/runs`)

### POST /api/v1/runs
Create a run from a template with optional scheduling/recurrence.

**Body — ResearchRunCreate**
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `template_id` | integer | Yes | Template must belong to user or be public |
| `parameters` | object | No | Variable substitutions |
| `model_name`, `depth` | string | No | Override defaults |
| `scheduled_at` | datetime | No | ISO 8601 timestamp (UTC) |
| `is_recurring` | bool | No | When true, requires `recurrence_pattern` |
| `recurrence_pattern` | string | No | `daily` \| `weekly` \| `monthly` |
| `metadata` | object | No | Arbitrary context |

**Response:** `ResearchRunResponse` (`201`).

---

### GET /api/v1/runs/{run_id}
Return run details.  
**Response:** `ResearchRunResponse`.  
`404` if missing.

---

### GET /api/v1/runs/{run_id}/status
Lightweight progress update (percent complete, tokens, cost).  
**Response:** `ResearchRunStatus`.

---

### GET /api/v1/runs
Paginated run listing. Accepts `status`, `template_id`, `page`, `page_size`.  
**Response:** `ResearchRunList`.

---

### POST /api/v1/runs/{run_id}/cancel
Cancel a pending or running run.  
**Response:** `204 No Content`.  
Errors: `400` invalid state, `404` not found.

---

### GET /api/v1/runs/template/{template_id}
Fetch latest runs for a template (`limit` default 10).  
**Response:** `list[ResearchRunResponse]`.

---

## Health

### GET /api/v1/health
Versioned health summary including Perplexity API availability.

### GET /health
Extended health (database, Redis, Celery, Perplexity) at service root.

---

## Perplexity Integration
- Uses `POST https://api.perplexity.ai/chat/completions` with retry/backoff (`PERPLEXITY_MAX_RETRIES`).
- Calculates cost from `usage.total_tokens` via `settings.calculate_cost` and records in `cost_tracking`.
- Structured output validation via Pydantic models for specialised functions; JSON extraction handles fenced code blocks.
- Redis caching (`CACHE_RESEARCH_RESULTS_TTL`, default 7 days) reduces duplicate queries.

---

## Error Codes

| Status | Meaning | Typical Causes |
| --- | --- | --- |
| 400 | Bad Request | Template variable mismatch, invalid status filters |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Template ownership conflict |
| 404 | Not Found | Unknown task/run/template |
| 429 | Too Many Requests | Per-user rate limit or Perplexity throttle |
| 500 | Internal Error | Celery dispatch failure, Perplexity outage |

---

**Generated:** 2025-01-19  
**Maintainer:** Research Service Team

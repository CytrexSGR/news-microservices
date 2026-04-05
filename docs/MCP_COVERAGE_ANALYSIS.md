# MCP Coverage Analysis Report

**Generated:** 2025-12-22
**Total MCP Tools:** 198

---

## Summary

This report compares documented REST API endpoints with available MCP tools to identify coverage gaps.

---

## 1. Auth Service

### Documented APIs (auth-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `POST /api/v1/auth/register` | - | **MISSING** |
| `POST /api/v1/auth/login` | `core:auth_login` | Covered |
| `POST /api/v1/auth/refresh` | `core:auth_refresh_token` | Covered |
| `POST /api/v1/auth/logout` | `core:auth_logout` | Covered |
| `GET /api/v1/auth/me` | `core:auth_get_current_user` | Covered |
| `GET /api/v1/users` | `core:auth_list_users` | Covered |
| `GET /api/v1/users/{id}` | `core:auth_get_user` | Covered |
| `PUT /api/v1/users/{id}` | - | **MISSING** |
| `DELETE /api/v1/users/{id}` | - | **MISSING** |
| `POST /api/v1/api-keys` | `core:auth_create_api_key` | Covered |
| `GET /api/v1/api-keys` | `core:auth_list_api_keys` | Covered |
| `DELETE /api/v1/api-keys/{id}` | `core:auth_delete_api_key` | Covered |
| `GET /api/v1/auth/stats` | `core:auth_get_stats` | Covered |

**Coverage: 10/13 (77%)**

### Missing MCP Tools for Auth:
- `auth_register` - User registration
- `auth_update_user` - Update user profile
- `auth_delete_user` - Delete user account

---

## 2. Feed Service

### Documented APIs (feed-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `GET /api/v1/feeds` | `content:feeds_list` | Covered |
| `GET /api/v1/feeds/{id}` | `content:feeds_get` | Covered |
| `POST /api/v1/feeds` | `content:feeds_create` | Covered |
| `PUT /api/v1/feeds/{id}` | `content:feeds_update` | Covered |
| `DELETE /api/v1/feeds/{id}` | `content:feeds_delete` | Covered |
| `GET /api/v1/feeds/stats` | `content:feeds_stats` | Covered |
| `GET /api/v1/feeds/{id}/health` | `content:feeds_health` | Covered |
| `POST /api/v1/feeds/{id}/fetch` | `content:feeds_fetch` | Covered |
| `POST /api/v1/feeds/bulk-fetch` | `content:feeds_bulk_fetch` | Covered |
| `POST /api/v1/feeds/{id}/reset-error` | `content:feeds_reset_error` | Covered |
| `GET /api/v1/feeds/{id}/items` | `content:items_list` | Covered |
| `GET /api/v1/feeds/{id}/items/{item_id}` | `content:items_get` | Covered |
| `POST /api/v1/feeds/{id}/assess` | `content:quality_assess` | Covered |
| `GET /api/v1/feeds/{id}/quality` | `content:quality_get` | Covered |
| `GET /api/v1/feeds/{id}/quality-v2` | `content:quality_get_v2` | Covered |
| `GET /api/v1/feeds/{id}/assessment-history` | `content:quality_history` | Covered |
| `GET /api/v1/feeds/quality-v2/overview` | `content:quality_overview` | Covered |
| `POST /api/v1/feeds/pre-assess` | `content:quality_pre_assess` | Covered |
| `GET /api/v1/admiralty-codes/status` | `content:admiralty_status` | Covered |
| `GET /api/v1/admiralty-codes/thresholds` | `content:admiralty_thresholds` | Covered |
| `GET /api/v1/admiralty-codes/weights` | `content:admiralty_weights` | Covered |
| `GET /api/v1/scheduling/timeline` | `content:scheduling_timeline` | Covered |
| `GET /api/v1/scheduling/distribution` | `content:scheduling_distribution` | Covered |
| `POST /api/v1/scheduling/optimize` | `content:scheduling_optimize` | Covered |
| `GET /api/v1/scheduling/conflicts` | `content:scheduling_conflicts` | Covered |
| `GET /api/v1/scheduling/stats` | `content:scheduling_stats` | Covered |
| `GET /api/v1/scheduling/feeds/{id}` | `content:scheduling_get_feed` | Covered |
| `GET /api/v1/feeds/{id}/threshold` | - | **MISSING** |
| `POST /api/v1/feeds/{id}/scraping/reset` | - | **MISSING** |
| `PUT /api/v1/admiralty-codes/thresholds/{code}` | - | **MISSING** (read-only) |
| `POST /api/v1/admiralty-codes/thresholds/reset` | - | **MISSING** |
| `PUT /api/v1/admiralty-codes/weights/{category}` | - | **MISSING** (read-only) |
| `POST /api/v1/admiralty-codes/weights/reset` | - | **MISSING** |

**Coverage: 27/33 (82%)**

### Missing MCP Tools for Feed Service:
- `feeds_get_threshold` - Get feed scraping threshold
- `feeds_reset_scraping` - Reset scraping state
- `admiralty_thresholds_update` - Update threshold config
- `admiralty_thresholds_reset` - Reset to defaults
- `admiralty_weights_update` - Update weight config
- `admiralty_weights_reset` - Reset to defaults

---

## 3. Notification Service

### Documented APIs (notification-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `POST /api/v1/notifications/send` | `integration:send_notification` | Covered |
| `GET /api/v1/notifications/{id}` | - | **MISSING** |
| `GET /api/v1/notifications/history` | `integration:get_notification_history` | Covered |
| `POST /api/v1/notifications/send/adhoc` | `integration:send_adhoc_notification` | Covered |
| `GET /api/v1/notifications/templates` | `integration:list_notification_templates` | Covered |
| `POST /api/v1/notifications/templates` | - | **MISSING** |
| `GET /api/v1/notifications/preferences` | `integration:get_notification_preferences` | Covered |
| `POST /api/v1/notifications/preferences` | - | **MISSING** |
| `POST /api/v1/notifications/test` | - | **MISSING** |
| `POST /api/v1/notifications/send/secure` | - | **MISSING** |
| `GET /api/v1/notifications/delivery/status/{id}` | - | **MISSING** |
| `GET /api/v1/admin/jwt/info` | - | **MISSING** (Admin only) |
| `POST /api/v1/admin/jwt/rotate` | - | **MISSING** (Admin only) |
| `GET /api/v1/admin/rate-limit/user/{id}` | - | **MISSING** (Admin only) |
| `POST /api/v1/admin/rate-limit/user/{id}/reset` | - | **MISSING** (Admin only) |
| `GET /api/v1/admin/queue/stats` | `integration:get_notification_queue_stats` | Covered |
| `GET /api/v1/admin/dlq/list` | - | **MISSING** (Admin only) |
| `POST /api/v1/admin/dlq/retry/{id}` | - | **MISSING** (Admin only) |

**Coverage: 6/18 (33%)**

### Missing MCP Tools for Notification Service:
- `notification_get` - Get single notification
- `notification_templates_create` - Create template
- `notification_preferences_update` - Update preferences
- `notification_test` - Send test notification
- `notification_send_secure` - Send encrypted notification
- `notification_delivery_status` - Get delivery status
- Admin endpoints (jwt, rate-limit, dlq) intentionally excluded

---

## 4. Analytics Service

### Documented APIs (analytics-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `GET /api/v1/analytics/overview` | `core:analytics_get_overview` | Covered |
| `GET /api/v1/analytics/service/{name}` | `core:analytics_get_service` | Covered |
| `GET /api/v1/analytics/metrics` | `core:analytics_get_metrics` | Covered |
| `GET /api/v1/analytics/trends` | `core:analytics_get_trends` | Covered |
| `GET /api/v1/dashboards` | `core:dashboards_list` | Covered |
| `GET /api/v1/dashboards/{id}` | `core:dashboards_get` | Covered |
| `GET /api/v1/dashboards/{id}/data` | `core:dashboards_get_data` | Covered |
| `POST /api/v1/dashboards` | - | **MISSING** |
| `PUT /api/v1/dashboards/{id}` | - | **MISSING** |
| `DELETE /api/v1/dashboards/{id}` | - | **MISSING** |
| `GET /api/v1/reports` | `core:reports_list` | Covered |
| `GET /api/v1/reports/{id}` | `core:reports_get` | Covered |
| `POST /api/v1/reports` | - | **MISSING** |
| `DELETE /api/v1/reports/{id}` | - | **MISSING** |
| `GET /health` | `core:monitoring_get_health` | Covered |
| `GET /api/v1/monitoring/circuit-breakers` | `core:monitoring_get_circuit_breakers` | Covered |
| `GET /api/v1/monitoring/query-performance` | `core:monitoring_get_query_performance` | Covered |
| `GET /api/v1/health/summary` | `core:health_get_summary` | Covered |
| `GET /api/v1/health/containers` | `core:health_get_containers` | Covered |
| `GET /api/v1/health/alerts` | `core:health_get_alerts` | Covered |
| `GET /api/v1/cache/stats` | `core:cache_get_stats` | Covered |
| `GET /api/v1/cache/health` | `core:cache_get_health` | Covered |
| `POST /api/v1/cache/clear` | `core:cache_clear` | Covered |
| WebSocket `/api/v1/dashboards/{id}/ws` | - | **MISSING** (WebSocket) |

**Coverage: 18/24 (75%)**

### Missing MCP Tools for Analytics Service:
- `dashboards_create` - Create dashboard
- `dashboards_update` - Update dashboard
- `dashboards_delete` - Delete dashboard
- `reports_create` - Generate report
- `reports_delete` - Delete report
- WebSocket connections (not applicable to MCP)

---

## 5. Scheduler Service

### Documented APIs (scheduler-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `GET /api/v1/scheduler/status` | `orch:scheduler_status` | Covered |
| `GET /api/v1/scheduler/jobs/stats` | `orch:jobs_stats` | Covered |
| `GET /api/v1/scheduler/jobs` | `orch:jobs_list` | Covered |
| `POST /api/v1/scheduler/jobs/{id}/retry` | `orch:jobs_retry` | Covered |
| `POST /api/v1/scheduler/jobs/{id}/cancel` | `orch:jobs_cancel` | Covered |
| `POST /api/v1/scheduler/feeds/{id}/check` | `orch:feed_schedule_check` | Covered |
| `GET /api/v1/scheduler/cron/jobs` | `orch:cron_list` | Covered |
| `GET /health` | `orch:scheduler_health` | Covered |
| `POST /api/v1/scheduler/internal/health/service` | - | **MISSING** (Internal only) |

**Coverage: 8/9 (89%)**

### Missing MCP Tools for Scheduler Service:
- Internal service health endpoint (intentionally excluded)

---

## 6. Search Service

### Documented APIs (search-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `GET /api/v1/search` | `search:search_articles` | Covered |
| `POST /api/v1/search/advanced` | `search:advanced_search` | Covered |
| `GET /api/v1/search/suggest` | `search:get_search_suggestions` | Covered |
| `GET /api/v1/search/popular` | `search:get_popular_searches` | Covered |
| `GET /api/v1/search/related` | `search:get_related_searches` | Covered |
| `GET /api/v1/search/facets` | `search:get_search_facets` | Covered |
| `GET /api/v1/search/history` | - | **MISSING** |
| `DELETE /api/v1/search/history` | - | **MISSING** |
| `POST /api/v1/search/saved` | `search:create_saved_search` | Covered |
| `GET /api/v1/search/saved` | `search:list_saved_searches` | Covered |
| `GET /api/v1/search/saved/{id}` | - | **MISSING** |
| `PUT /api/v1/search/saved/{id}` | - | **MISSING** |
| `DELETE /api/v1/search/saved/{id}` | `search:delete_saved_search` | Covered |
| `POST /api/v1/admin/reindex` | - | **MISSING** (Admin only) |
| `POST /api/v1/admin/sync` | - | **MISSING** (Admin only) |
| `GET /api/v1/admin/stats/index` | - | **MISSING** (Admin only) |
| `GET /api/v1/admin/stats/queries` | - | **MISSING** (Admin only) |
| `GET /api/v1/admin/stats/cache` | - | **MISSING** (Admin only) |
| `GET /api/v1/admin/stats/performance` | - | **MISSING** (Admin only) |

**Coverage: 10/19 (53%)**

### Missing MCP Tools for Search Service:
- `search_history_get` - Get search history
- `search_history_clear` - Clear search history
- `saved_search_get` - Get single saved search
- `saved_search_update` - Update saved search
- Admin endpoints (reindex, sync, stats) intentionally excluded

---

## 7. FMP Service

### Documented APIs (fmp-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `GET /api/v1/quote/{symbol}` | `integration:get_market_quote` | Covered |
| `GET /api/v1/quotes/batch` | `integration:get_market_quotes_batch` | Covered |
| `GET /api/v1/candles/{symbol}` | `integration:get_ohlcv_candles` | Covered |
| `GET /api/v1/candles/{symbol}/timerange` | `integration:get_ohlcv_timerange` | Covered |
| `GET /api/v1/market/status` | `integration:get_market_status` | Covered |
| `GET /api/v1/assets/list` | `integration:list_symbols` | Covered |
| `GET /api/v1/assets/search` | `integration:search_symbols` | Covered |
| `GET /api/v1/news` | `integration:get_financial_news` | Covered |
| `GET /api/v1/news/sentiment` | `integration:get_news_by_sentiment` | Covered |
| `GET /api/v1/earnings/calendar` | `integration:get_earnings_calendar` | Covered |
| `GET /api/v1/earnings/{symbol}` | `integration:get_earnings_history` | Covered |
| `GET /api/v1/macro/indicators` | `integration:get_macro_indicators` | Covered |
| `GET /api/v1/macro/{indicator}` | `integration:get_macro_indicator_data` | Covered |
| `GET /api/v1/macro/latest` | `integration:get_latest_macro_data` | Covered |
| `GET /api/v1/metadata/{symbol}` | `integration:get_asset_metadata` | Covered |

**Coverage: 15/15 (100%)**

---

## 8. Research Service

### Documented APIs (research-service.md)

| Endpoint | MCP Tool | Status |
|----------|----------|--------|
| `POST /api/v1/research/query` | `integration:research_query` | Covered |
| `POST /api/v1/research/batch` | `integration:research_batch` | Covered |
| `GET /api/v1/research/{id}` | `integration:get_research_result` | Covered |
| `GET /api/v1/research/history` | `integration:get_research_history` | Covered |
| `GET /api/v1/research/templates` | `integration:list_research_templates` | Covered |
| `POST /api/v1/research/templates/apply` | `integration:apply_research_template` | Covered |

**Coverage: 6/6 (100%)**

---

## Overall Coverage Summary

| Service | Documented APIs | MCP Tools | Coverage |
|---------|----------------|-----------|----------|
| Auth Service | 13 | 10 | 77% |
| Feed Service | 33 | 27 | 82% |
| Notification Service | 18 | 6 | 33% |
| Analytics Service | 24 | 18 | 75% |
| Scheduler Service | 9 | 8 | 89% |
| Search Service | 19 | 10 | 53% |
| FMP Service | 15 | 15 | **100%** |
| Research Service | 6 | 6 | **100%** |
| **Total** | **137** | **100** | **73%** |

---

## Priority Recommendations

### High Priority (Critical Functionality Missing)

1. **Notification Service** - 33% coverage
   - Add: `notification_get`, `notification_test`, `notification_delivery_status`
   - Add: `notification_templates_create`, `notification_preferences_update`

2. **Search Service** - 53% coverage
   - Add: `search_history_get`, `search_history_clear`
   - Add: `saved_search_get`, `saved_search_update`

### Medium Priority (Write Operations Missing)

3. **Analytics Service** - 75% coverage
   - Add: `dashboards_create`, `dashboards_update`, `dashboards_delete`
   - Add: `reports_create`, `reports_delete`

4. **Auth Service** - 77% coverage
   - Add: `auth_register`, `auth_update_user`, `auth_delete_user`

### Low Priority (Configuration/Admin)

5. **Feed Service** - 82% coverage
   - Add: `admiralty_thresholds_update`, `admiralty_weights_update`
   - These are admin-level configuration endpoints

---

## Excluded from Analysis

The following were intentionally excluded:
- **Admin-only endpoints** - High privilege operations not suitable for MCP
- **Internal service endpoints** - Service-to-service communication only
- **WebSocket endpoints** - Not applicable to MCP protocol
- **Health/metrics endpoints** - Already covered by monitoring tools

---

## Conclusion

**Current State:** MCP tools cover 73% of documented REST API functionality.

**Well Covered Services:**
- FMP Service: 100%
- Research Service: 100%
- Scheduler Service: 89%
- Feed Service: 82%

**Need Improvement:**
- Notification Service: 33% (missing critical user-facing features)
- Search Service: 53% (missing history and saved search management)

**Recommendation:** Prioritize adding MCP tools for Notification and Search services to improve overall coverage to 85%+.

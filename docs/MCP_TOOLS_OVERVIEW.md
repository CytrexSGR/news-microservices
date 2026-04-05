# MCP Tools Overview

**Generated:** 2025-12-22
**Last Updated:** 2025-12-24
**Total MCP Servers:** 8
**Total Tools:** 217

---

## Quick Reference

| Server | Port | Tools | Primary Functions |
|--------|------|-------|-------------------|
| [Intelligence](#1-mcp-intelligence-server-port-9001) | 9001 | 32 | OSINT, Entity Resolution, Narrative Analysis |
| [Search](#2-mcp-search-server-port-9002) | 9002 | 31 | Article Search, Feed Management, Research |
| [Analytics](#3-mcp-analytics-server-port-9003) | 9003 | 32 | Metrics, Predictions, Execution |
| [Knowledge Graph](#4-mcp-knowledge-graph-server-port-9004) | 9004 | 17 | Neo4j Entity/Relationship Queries |
| [Integration](#5-mcp-integration-server-port-9005) | 9005 | 30 | FMP Market Data, Notifications, Research |
| [Core](#6-mcp-core-server-port-9006) | 9006 | 40 | Auth, Analytics, Dashboards, Reports |
| [Content](#7-mcp-content-server-port-9007) | 9007 | 27 | Feeds CRUD, Quality Assessment, Scheduling |
| [Orchestration](#8-mcp-orchestration-server-port-9008) | 9008 | 8 | Scheduler, Jobs, Cron |

---

## 1. MCP-Intelligence-Server (Port 9001)

**32 Tools** - Intelligence, OSINT, Entity Resolution, Narrative Analysis

### Analysis (3 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `analyze_article` | AI-powered article analysis | content-analysis-v3 |
| `extract_entities` | Extract named entities from text | content-analysis-v3 |
| `get_analysis_status` | Get analysis job status | content-analysis-v3 |

### Entity Resolution (8 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `canonicalize_entity` | Resolve entity to canonical form | entity-canonicalization |
| `batch_canonicalize_entities` | Batch entity resolution | entity-canonicalization |
| `get_entity_aliases` | Get known aliases for entity | entity-canonicalization |
| `get_entity_clusters` | Get entity clusters | entity-canonicalization |
| `get_canonicalization_stats` | Get resolution statistics | entity-canonicalization |
| `get_async_job_status` | Get async job status | entity-canonicalization |
| `get_async_job_result` | Get async job result | entity-canonicalization |

### Intelligence (9 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_intelligence_overview` | System-wide intelligence summary | intelligence-service |
| `get_latest_events` | Get recent intelligence events | intelligence-service |
| `get_event_clusters` | Get clustered events | intelligence-service |
| `get_cluster_details` | Get cluster details | intelligence-service |
| `get_cluster_events` | Get events in cluster | intelligence-service |
| `get_risk_history` | Get risk score history | intelligence-service |
| `get_subcategories` | Get intelligence subcategories | intelligence-service |
| `analyze_graph_quality` | Analyze knowledge graph quality | osint-service |
| `detect_intelligence_patterns` | Detect patterns in intelligence | osint-service |

### OSINT (8 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `list_osint_templates` | List OSINT collection templates | osint-service |
| `get_osint_template` | Get template details | osint-service |
| `create_osint_instance` | Create OSINT collection instance | osint-service |
| `list_osint_instances` | List active instances | osint-service |
| `execute_osint_instance` | Execute OSINT collection | osint-service |
| `get_osint_execution` | Get execution status | osint-service |
| `list_osint_alerts` | List OSINT alerts | osint-service |
| `get_osint_alert_stats` | Get alert statistics | osint-service |

### Narrative Analysis (5 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_narrative_overview` | Narrative landscape overview | narrative-service |
| `list_narrative_clusters` | List narrative clusters | narrative-service |
| `get_narrative_frames` | Get framing analysis | narrative-service |
| `get_bias_analysis` | Get bias detection results | narrative-service |
| `analyze_text_narrative` | Analyze text for narratives | narrative-service |

---

## 2. MCP-Search-Server (Port 9002)

**31 Tools** - Search, Feed Management, Research Tasks

### Search (12 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `search_articles` | Full-text article search | search-service |
| `advanced_search` | Advanced search with facets | search-service |
| `get_search_suggestions` | Autocomplete suggestions | search-service |
| `get_search_facets` | Get available filters | search-service |
| `get_popular_searches` | Trending searches | search-service |
| `get_related_searches` | Related query suggestions | search-service |
| `get_search_history` | User search history | search-service |
| `clear_search_history` | Clear search history | search-service |
| `list_saved_searches` | List saved searches | search-service |
| `get_saved_search` | Get saved search details | search-service |
| `create_saved_search` | Save a search query | search-service |
| `update_saved_search` | Update saved search | search-service |
| `delete_saved_search` | Delete saved search | search-service |

### Feed Management (9 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `list_feeds` | List all feeds | feed-service |
| `get_feed` | Get feed details | feed-service |
| `create_feed` | Add new feed | feed-service |
| `fetch_feed` | Trigger feed fetch | feed-service |
| `get_feed_items` | Get feed articles | feed-service |
| `get_feed_health` | Get feed health metrics | feed-service |
| `assess_feed` | AI credibility assessment | feed-service |
| `pre_assess_feed` | Preview feed before adding | feed-service |
| `get_assessment_history` | Historical assessments | feed-service |

### Research (10 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `create_research_task` | Create Perplexity research | research-service |
| `get_research_task` | Get research results | research-service |
| `list_research_tasks` | List research tasks | research-service |
| `create_batch_research` | Batch research queries | research-service |
| `get_research_history` | Research history | research-service |
| `list_research_templates` | List research templates | research-service |
| `get_research_template` | Get template details | research-service |
| `apply_research_template` | Execute research template | research-service |
| `list_research_functions` | List available functions | research-service |

---

## 3. MCP-Analytics-Server (Port 9003)

**32 Tools** - Analytics, Predictions, Trading Execution

### Analytics (6 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_analytics_overview` | System-wide metrics | analytics-service |
| `get_analytics_metrics` | Specific metrics | analytics-service |
| `get_analytics_trends` | Trend analysis | analytics-service |
| `get_service_analytics` | Per-service analytics | analytics-service |
| `list_dashboards` | List dashboards | analytics-service |
| `get_dashboard_data` | Get dashboard data | analytics-service |

### Monitoring (5 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_health_summary` | System health summary | analytics-service |
| `get_health_containers` | Container health | analytics-service |
| `get_circuit_breaker_status` | Circuit breaker states | analytics-service |
| `get_query_performance` | DB query performance | analytics-service |
| `get_cache_stats` | Cache statistics | analytics-service |

### Prediction (14 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_predictions` | Get price predictions | prediction-service |
| `create_prediction` | Create new prediction | prediction-service |
| `get_signals` | Get trading signals | prediction-service |
| `get_indicators` | Get technical indicators | prediction-service |
| `get_features` | Get ML features | prediction-service |
| `list_strategies` | List trading strategies | prediction-service |
| `validate_strategy` | Validate strategy | prediction-service |
| `get_backtest_results` | Backtest results | prediction-service |
| `get_model_performance` | Model metrics | prediction-service |
| `get_model_drift` | Model drift detection | prediction-service |
| `get_regime_analysis` | Market regime analysis | prediction-service |
| `get_order_flow_data` | Order flow data | prediction-service |
| `get_consensus_alerts` | Consensus alerts | prediction-service |
| `optimize_portfolio` | Portfolio optimization | prediction-service |

### Execution (7 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_execution_status` | Execution system status | execution-service |
| `get_portfolio` | Get portfolio | execution-service |
| `get_positions` | Get open positions | execution-service |
| `get_portfolio_performance` | Portfolio performance | execution-service |
| `get_strategy_analytics` | Strategy analytics | execution-service |
| `close_position` | Close a position | execution-service |
| `control_autotrade` | Control auto-trading | execution-service |

---

## 4. MCP-Knowledge-Graph-Server (Port 9004)

**0 Tools** - Direct Neo4j access via Cypher queries

> Note: Knowledge graph queries are executed directly via Neo4j.
> Use the knowledge-graph-service REST API at port 8111.

---

## 5. MCP-Integration-Server (Port 9005)

**30 Tools** - Financial Data, Notifications, Research

### Market Data (13 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_market_quote` | Real-time quote | fmp-service |
| `get_market_quotes_batch` | Batch quotes | fmp-service |
| `get_ohlcv_candles` | OHLCV candlestick data | fmp-service |
| `get_ohlcv_timerange` | OHLCV by time range | fmp-service |
| `get_market_status` | Market open/close status | fmp-service |
| `list_symbols` | List available symbols | fmp-service |
| `search_symbols` | Search for symbols | fmp-service |
| `get_asset_metadata` | Asset metadata | fmp-service |
| `get_financial_news` | Financial news | fmp-service |
| `get_news_by_sentiment` | News by sentiment | fmp-service |
| `get_earnings_calendar` | Earnings calendar | fmp-service |
| `get_earnings_history` | Historical earnings | fmp-service |

### Macro Economics (3 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `get_macro_indicators` | List macro indicators | fmp-service |
| `get_macro_indicator_data` | Get indicator data | fmp-service |
| `get_latest_macro_data` | Latest macro data | fmp-service |

### Notifications (9 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `send_notification` | Send notification | notification-service |
| `send_adhoc_notification` | Send ad-hoc notification | notification-service |
| `get_notification` | Get notification by ID | notification-service |
| `get_notification_history` | Notification history | notification-service |
| `list_notification_templates` | List templates | notification-service |
| `get_notification_preferences` | Get preferences | notification-service |
| `update_notification_preferences` | Update preferences | notification-service |
| `test_notification` | Send test notification | notification-service |
| `get_notification_queue_stats` | Queue statistics | notification-service |

### Research (6 Tools)
| Tool | Description | Service |
|------|-------------|---------|
| `research_query` | Execute research query | research-service |
| `research_batch` | Batch research | research-service |
| `get_research_result` | Get research result | research-service |
| `get_research_history` | Research history | research-service |
| `list_research_templates` | List templates | research-service |
| `apply_research_template` | Apply template | research-service |

---

## 6. MCP-Core-Server (Port 9006)

**36 Tools** - Authentication, Analytics, Dashboards, Reports

### Authentication (13 Tools)
| Tool | Description |
|------|-------------|
| `auth_login` | User login, get JWT tokens |
| `auth_logout` | Logout, invalidate tokens |
| `auth_refresh_token` | Refresh access token |
| `auth_get_current_user` | Get current user profile |
| `auth_register` | Register new user |
| `auth_update_user` | Update user (admin) |
| `auth_delete_user` | Delete user (admin) |
| `auth_list_users` | List all users (admin) |
| `auth_get_user` | Get user by ID (admin) |
| `auth_get_stats` | Auth statistics (admin) |
| `auth_list_api_keys` | List API keys |
| `auth_create_api_key` | Create API key |
| `auth_delete_api_key` | Delete API key |

### Analytics (4 Tools)
| Tool | Description |
|------|-------------|
| `analytics_get_overview` | System-wide overview |
| `analytics_get_metrics` | Specific metrics |
| `analytics_get_service` | Service analytics |
| `analytics_get_trends` | Trend data |

### Dashboards (6 Tools)
| Tool | Description |
|------|-------------|
| `dashboards_list` | List dashboards |
| `dashboards_get` | Get dashboard config |
| `dashboards_get_data` | Get dashboard data |
| `dashboards_create` | Create dashboard |
| `dashboards_update` | Update dashboard |
| `dashboards_delete` | Delete dashboard |

### Reports (4 Tools)
| Tool | Description |
|------|-------------|
| `reports_list` | List reports |
| `reports_get` | Get report details |
| `reports_create` | Create/generate report |
| `reports_delete` | Delete report |

### Health Monitoring (3 Tools)
| Tool | Description |
|------|-------------|
| `health_get_summary` | System health summary |
| `health_get_containers` | Container health |
| `health_get_alerts` | Active health alerts |

### Cache Management (3 Tools)
| Tool | Description |
|------|-------------|
| `cache_get_stats` | Cache statistics |
| `cache_get_health` | Cache health |
| `cache_clear` | Clear cache |

### Monitoring (3 Tools)
| Tool | Description |
|------|-------------|
| `monitoring_get_health` | Monitoring health |
| `monitoring_get_circuit_breakers` | Circuit breaker status |
| `monitoring_get_query_performance` | Query performance |

---

## 7. MCP-Content-Server (Port 9007)

**27 Tools** - Feed CRUD, Quality Assessment, Scheduling

### Feed Management (10 Tools)
| Tool | Description |
|------|-------------|
| `feeds_list` | List all feeds |
| `feeds_get` | Get feed details |
| `feeds_create` | Create new feed |
| `feeds_update` | Update feed |
| `feeds_delete` | Delete feed |
| `feeds_fetch` | Trigger fetch |
| `feeds_bulk_fetch` | Bulk fetch feeds |
| `feeds_stats` | Feed statistics |
| `feeds_health` | Feed health |
| `feeds_reset_error` | Reset error state |

### Feed Items (2 Tools)
| Tool | Description |
|------|-------------|
| `items_list` | List feed items |
| `items_get` | Get item details |

### Quality Assessment (7 Tools)
| Tool | Description |
|------|-------------|
| `quality_get` | Get quality score |
| `quality_get_v2` | Get quality v2 |
| `quality_overview` | Quality overview |
| `quality_assess` | Assess feed quality |
| `quality_pre_assess` | Pre-assessment |
| `quality_history` | Assessment history |

### Admiralty Rating (3 Tools)
| Tool | Description |
|------|-------------|
| `admiralty_status` | Admiralty code status |
| `admiralty_weights` | Rating weights |
| `admiralty_thresholds` | Rating thresholds |

### Scheduling (6 Tools)
| Tool | Description |
|------|-------------|
| `scheduling_stats` | Scheduling statistics |
| `scheduling_timeline` | Feed timeline |
| `scheduling_distribution` | Fetch distribution |
| `scheduling_conflicts` | Scheduling conflicts |
| `scheduling_optimize` | Optimize schedule |
| `scheduling_get_feed` | Get feed schedule |

---

## 8. MCP-Orchestration-Server (Port 9008)

**8 Tools** - Scheduler Management, Jobs, Cron

### Scheduler Status (2 Tools)
| Tool | Description |
|------|-------------|
| `scheduler_status` | Scheduler status |
| `scheduler_health` | Scheduler health |

### Job Management (4 Tools)
| Tool | Description |
|------|-------------|
| `jobs_list` | List jobs |
| `jobs_stats` | Job statistics |
| `jobs_cancel` | Cancel job |
| `jobs_retry` | Retry job |

### Cron & Feeds (2 Tools)
| Tool | Description |
|------|-------------|
| `cron_list` | List cron jobs |
| `feed_schedule_check` | Check feed schedule |

---

## Tools by Category Summary

| Category | Count | Primary Server |
|----------|-------|----------------|
| Authentication | 13 | Core |
| Search | 13 | Search |
| Feed Management | 19 | Content, Search |
| Research | 16 | Search, Integration |
| Market Data | 13 | Integration |
| Predictions | 14 | Analytics |
| Execution | 7 | Analytics |
| OSINT | 8 | Intelligence |
| Entity Resolution | 8 | Intelligence |
| Intelligence | 9 | Intelligence |
| Narrative | 5 | Intelligence |
| Analytics | 10 | Analytics, Core |
| Notifications | 9 | Integration |
| Dashboards | 6 | Core |
| Reports | 4 | Core |
| Scheduling | 8 | Content, Orchestration |
| Quality | 7 | Content |
| Monitoring | 8 | Analytics, Core |
| Cache | 3 | Core |
| Content Analysis | 3 | Intelligence |

---

## Claude Desktop Configuration

All 8 MCP servers are configured in the unified gateway:

```json
{
  "mcpServers": {
    "news-mcp-gateway": {
      "command": "node",
      "args": ["/path/to/mcp-gateway/index.js"],
      "env": {
        "MCP_INTELLIGENCE_URL": "http://localhost:9001",
        "MCP_SEARCH_URL": "http://localhost:9002",
        "MCP_ANALYTICS_URL": "http://localhost:9003",
        "MCP_KG_URL": "http://localhost:9004",
        "MCP_INTEGRATION_URL": "http://localhost:9005",
        "MCP_CORE_URL": "http://localhost:9006",
        "MCP_CONTENT_URL": "http://localhost:9007",
        "MCP_ORCHESTRATION_URL": "http://localhost:9008"
      }
    }
  }
}
```

---

**Last Updated:** 2025-12-22

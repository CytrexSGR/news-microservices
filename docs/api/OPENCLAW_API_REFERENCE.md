# OpenClaw Agent — News Intelligence API Reference

**Server:** `localhost`
**Agent Host:** `localhost`
**Generated:** 2026-02-09
**Base URL Pattern:** `http://localhost:{PORT}`

---

## Authentication

**Auth Service:** `http://localhost:8100`

```
Credentials:
  username: andreas
  password: Aug2012#
```

### Login → Get JWT Token

```http
POST http://localhost:8100/api/v1/auth/login
Content-Type: application/json

{"username": "andreas", "password": "Aug2012#"}
```

Response:
```json
{"access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer"}
```

### Using the Token

All auth-required endpoints:
```
Authorization: Bearer {access_token}
```

### Refresh (when token expires)

```http
POST http://localhost:8100/api/v1/auth/refresh
Content-Type: application/json

{"refresh_token": "eyJ..."}
```

---

## Service Registry

### Public Services (no auth needed)

| Service | Base URL | Purpose |
|---------|----------|---------|
| intelligence | `http://localhost:8118` | Risk scoring, events, cluster overview |
| feed | `http://localhost:8101` | Articles, feeds (read-only) |
| search | `http://localhost:8106` | Full-text + semantic search |
| geolocation | `http://localhost:8115` | Security events, threat monitoring, hotspots |
| narrative-gateway | `http://localhost:8114` | Narrative frames, entity framing, tension |
| knowledge-graph | `http://localhost:8111` | Entity connections, paths, analytics |
| fmp | `http://localhost:8113` | Financial market data, quotes, news |
| entity-canonicalization | `http://localhost:8112` | Entity lookup, deduplication |

### Auth-Required Services (Bearer token)

| Service | Base URL | Purpose |
|---------|----------|---------|
| sitrep | `http://localhost:8123` | SITREPs / intelligence briefings |
| clustering | `http://localhost:8122` | Burst detection, topic clusters |
| analytics | `http://localhost:8107` | Intelligence signals, top stories, dashboards |
| narrative | `http://localhost:8119` | Frame/bias analysis (LLM-powered) |
| research | `http://localhost:8103` | Perplexity AI deep research |
| prediction | `http://localhost:8116` | Trading signals (CURRENTLY DISABLED) |

---

## API Reference — Public Services

---

### 1. intelligence-service (Port 8118)

Risk scoring, event detection, intelligence cluster analytics.

#### GET /api/v1/intelligence/overview
Dashboard statistics: global risk index, top clusters, geo/finance risk, top regions.

#### GET /api/v1/intelligence/clusters
List intelligence clusters with filtering.
```
?min_events=2          # Minimum events in cluster
&time_range=7          # Days to look back
&time_window=24h       # 1h|6h|12h|24h|week|month
&sort_by=risk_score    # risk_score|event_count|last_updated
&page=1&per_page=20
```

#### GET /api/v1/intelligence/clusters/{cluster_id}
Detailed cluster info with all events.

#### GET /api/v1/intelligence/clusters/{cluster_id}/events
Events for specific cluster.
```
?page=1&per_page=20
```

#### GET /api/v1/intelligence/events/latest
Latest events across all clusters.
```
?hours=4     # 4-48, default 4
&limit=20    # 1-100
```

#### POST /api/v1/intelligence/events/detect
Detect events and extract entities from text.
```json
{"text": "...", "include_keywords": true, "max_keywords": 10}
```

#### POST /api/v1/intelligence/risk/calculate
Calculate risk score (0-100).
```json
{"cluster_id": "uuid"}
// OR
{"entities": ["entity1", "entity2"]}
// OR
{"text": "...", "include_factors": true}
```

#### GET /api/v1/intelligence/subcategories
Top 2 sub-topics per category (geo, finance, tech).

#### GET /api/v1/intelligence/risk-history
Historical risk scores for trend visualization.
```
?days=7    # 1-30
```

---

### 2. feed-service (Port 8101)

Articles, feeds, sources. Read operations are public, write operations require auth.

#### GET /api/v1/feeds
List all feeds.
```
?skip=0&limit=100
&is_active=true
&status=ACTIVE          # ACTIVE|PAUSED|ERROR|INACTIVE
&category=...
&health_score_min=0&health_score_max=100
```

#### GET /api/v1/feeds/{feed_id}
Feed details by UUID.

#### GET /api/v1/feeds/{feed_id}/health
Feed health metrics.

#### GET /api/v1/feeds/items
List articles across all feeds.
```
?skip=0&limit=100       # max 100
&feed_ids=uuid1,uuid2   # comma-separated
&source_type=...
&date_from=2026-01-01&date_to=2026-02-09
&has_content=true
&sentiment=positive     # positive|negative|neutral
&category=...
&sort_by=published_at   # published_at|relevance_score|title
&order=desc             # asc|desc
```

#### GET /api/v1/feeds/{feed_id}/items
Articles for specific feed.
```
?skip=0&limit=50
```

#### GET /api/v1/feeds/items/{item_id}
Single article with full details.

#### GET /api/v1/sources
List news sources.
```
?skip=0&limit=100
&is_active=true
&category=...&country=...&language=...
&credibility_tier=...
&search=keyword
&include_feeds=true
```

#### GET /api/v1/sources/{source_id}
Source details.

#### GET /api/v1/sources/by-domain/{domain}
Source lookup by domain name.

#### GET /api/v1/feeds/{feed_id}/quality
Feed quality score.

#### GET /api/v1/feeds/quality-v2/overview
Overall quality metrics.

#### GET /api/v1/admiralty-codes/thresholds
All Admiralty code thresholds (NATO intelligence credibility standard).

#### GET /api/v1/scheduling/timeline
Feed schedule timeline.
```
?hours=24    # 1-168
```

#### GET /api/v1/duplicates/stats
Duplicate detection statistics.

---

### 3. search-service (Port 8106)

Full-text and semantic search with entity graph integration.

#### GET /api/v1/search
Basic full-text search.
```
?query=keyword
&page=1&page_size=50    # max 100
&source=...
&sentiment=positive
&date_from=2026-01-01&date_to=2026-02-09
```

#### POST /api/v1/search/advanced
Advanced search with complex queries.
```json
{
  "query": "search terms",
  "filters": {"sentiment": "negative", "source": "reuters"},
  "fuzzy": true,
  "highlighting": true,
  "faceted": true
}
```

#### GET /api/v1/search/suggest
Autocomplete suggestions.
```
?query=key&limit=10     # 1-20
```

#### POST /api/v1/search/semantic
Semantic similarity search.
```json
{
  "query": "geopolitical tension in Middle East",
  "page": 1,
  "page_size": 20,
  "threshold": 0.5
}
```

#### POST /api/v1/search/entities/enrich
Entity enrichment and analysis.
```json
{"entities": ["entity1", "entity2"], "article_id": "uuid"}
```

#### GET /api/v1/search/entities/{entity_id}/connections
Entity relationships from Neo4j knowledge graph.
```
?max_depth=2
```

#### GET /api/v1/search/entities/{entity_id}/paths
Find connection paths between entities.
```
?target_entity_id=uuid
```

#### GET /api/v1/search/articles/{article_id}/entities
All entities extracted from an article.

#### GET /api/v1/admin/stats/index
Article index statistics.

#### GET /api/v1/admin/stats/analytics
Search analytics.

---

### 4. geolocation-service (Port 8115)

Geographic visualization, security events, threat monitoring, watchlists.

#### Countries & Map

##### GET /api/v1/geo/countries
Countries with article statistics.
```
?region=Europe
```

##### GET /api/v1/geo/countries/{iso_code}
Country details (e.g. `DE`, `US`, `RU`).

##### GET /api/v1/geo/countries/{iso_code}/articles
Articles for a country.
```
?limit=50&offset=0
```

##### GET /api/v1/geo/map/countries
GeoJSON FeatureCollection for map rendering.
```
?from_date=2026-01-01&to_date=2026-02-09
```

##### GET /api/v1/geo/map/markers
Article markers for map.
```
?time_range=24h&region=...&categories=...&limit=100
```

##### GET /api/v1/geo/map/heatmap
Heatmap intensity data.

##### GET /api/v1/geo/filters/regions
Available regions for filtering.

##### GET /api/v1/geo/filters/categories
V3 categories with article counts.

#### Security View

##### GET /api/v1/geo/security/overview
Global security overview.
```
?days=7&min_priority=3
```

##### GET /api/v1/geo/security/events
Paginated security events.
```
?days=7&min_priority=3
&category=...&country=DE&region=Europe
&threat_level=high
&page=1&per_page=50
```

##### GET /api/v1/geo/security/countries
Aggregated threat data per country.
```
?days=7&min_priority=3&region=Europe&min_events=5&limit=20
```

##### GET /api/v1/geo/security/country/{iso_code}
Country threat profile.
```
?days=30
```

##### GET /api/v1/geo/security/markers
Security markers for map visualization.
```
?days=7&min_priority=3&categories=conflict,security&region=...&limit=100
```

##### GET /api/v1/geo/security/anomalies
Anomaly detection in security events.
```
?period=7&baseline_days=30&min_deviation=2.0&min_events=5
```

##### GET /api/v1/geo/security/entity-graph
Entity relationship graph from security events.
```
?entity=Putin&country=RU&limit=50&min_mentions=3
```

#### Watchlist

##### GET /api/v1/geo/watchlist
Get watchlist items.
```
?item_type=country|entity|region
```

##### POST /api/v1/geo/watchlist
Add watchlist item.
```json
{
  "item_type": "entity",
  "item_value": "Putin",
  "display_name": "Vladimir Putin",
  "notes": "Monitor activity",
  "priority": 8
}
```

##### DELETE /api/v1/geo/watchlist/{item_id}
Remove watchlist item.

##### GET /api/v1/geo/watchlist/alerts
Watchlist alerts.
```
?unread_only=true&page=1&per_page=20
```

##### POST /api/v1/geo/watchlist/alerts/read
Mark alerts as read.
```json
{"alert_ids": ["uuid1", "uuid2"]}
```

##### GET /api/v1/geo/watchlist/stats
Alert statistics.

---

### 5. narrative-intelligence-gateway (Port 8114)

Unified API for narrative analysis. Proxies to knowledge-graph-service.

#### GET /api/v1/narratives/stats
Overall narrative statistics.

#### GET /api/v1/narratives/distribution
Frame type distribution.

#### GET /api/v1/narratives/high-tension
High tension narratives.
```
?min_tension=0.7&limit=50
```

#### GET /api/v1/narratives/top-entities
Top entities with narrative mentions.
```
?limit=20
```

#### GET /api/v1/entity/{entity_name}
All narratives for an entity.
```
?limit=50
```

#### GET /api/v1/entity/{entity_name}/framing
Comprehensive framing analysis for entity.

#### GET /api/v1/entity/{entity_name}/history
Entity tension history over time.
```
?days=30
```

#### GET /api/v1/cooccurrence
Entities frequently appearing together in narratives.
```
?min_shared=3&limit=50
```

#### GET /api/v1/dashboard/overview
Aggregated dashboard data (narratives + entities + tension).

#### Webhooks

##### POST /api/v1/webhooks/subscribe
Register webhook for events.
```json
{"url": "http://localhost:PORT/webhook", "events": ["tension.high"], "secret": "..."}
```

##### GET /api/v1/webhooks
List registered webhooks.

##### DELETE /api/v1/webhooks/{webhook_id}
Remove webhook.

---

### 6. knowledge-graph-service (Port 8111)

Neo4j knowledge graph — entity connections, paths, analytics, narratives, markets.

#### Core

##### GET /api/v1/graph/entity/{entity_name}/connections
All connections for an entity.
```
?relationship_type=...&limit=100    # max 1000
```

##### GET /api/v1/graph/stats
Overall graph statistics (nodes, relationships, entity types).

##### GET /api/v1/graph/search
Full-text entity search.
```
?query=keyword&limit=20&entity_type=PERSON|ORGANIZATION|LOCATION
```

##### GET /api/v1/graph/path/{entity1}/{entity2}
Shortest paths between two entities.
```
?max_depth=3&limit=3&min_confidence=0.5
```

#### Analytics

##### GET /api/v1/graph/analytics/top-entities
Top entities by connection count.
```
?limit=20&entity_type=PERSON
```

##### GET /api/v1/graph/analytics/growth-history
Graph growth over time.
```
?days=30
```

##### GET /api/v1/graph/analytics/relationship-stats
Relationship type statistics.

##### GET /api/v1/graph/analytics/cross-article-coverage
Entity coverage across articles.
```
?limit=50
```

##### GET /api/v1/graph/stats/detailed
Comprehensive stats with metadata.

#### Articles

##### GET /api/v1/graph/articles/{article_id}/entities
All entities extracted from an article.
```
?entity_type=PERSON&limit=50
```

##### GET /api/v1/graph/articles/{article_id}/info
Article info (title, URL, entity count).

#### Markets

##### GET /api/v1/graph/markets
Query MARKET nodes.
```
?asset_type=...&sector=...&exchange=...&is_active=true
&search=keyword&page=0&page_size=50
```

##### GET /api/v1/graph/markets/{symbol}
Market details with relationships.

##### GET /api/v1/graph/markets/{symbol}/history
Historical price data.
```
?from_date=2025-01-01&to_date=2026-02-09&limit=100
```

##### GET /api/v1/graph/markets/stats
Market statistics.

#### Narratives

##### GET /api/v1/graph/narratives/frames/{entity_name}
Narrative frames for entity.
```
?frame_type=conflict|responsibility|morality|security|human_interest|economic_consequences
&min_confidence=0.5&limit=100
```

##### GET /api/v1/graph/narratives/distribution
Frame type distribution.

##### GET /api/v1/graph/narratives/entity-framing/{entity_name}
Comprehensive framing analysis.

##### GET /api/v1/graph/narratives/cooccurrence
Entity co-occurrence in narratives.
```
?entity_name=...&frame_type=...&min_shared=3&limit=50
```

##### GET /api/v1/graph/narratives/high-tension
Narratives with high emotional tension.
```
?min_tension=0.7&frame_type=...&limit=50&include_details=true
```

##### GET /api/v1/graph/narratives/stats
Overall narrative statistics.

##### GET /api/v1/graph/narratives/top-entities
Entities with most narrative mentions.

#### Quality

##### GET /api/v1/graph/quality/disambiguation
Entity disambiguation quality analysis.

##### GET /api/v1/graph/quality/integrity
Knowledge graph integrity checks.

---

### 7. fmp-service (Port 8113)

Financial market data — quotes, candles, earnings, news, macro indicators.

#### Quotes

##### GET /api/v1/market/quotes
Quotes by asset type.
```
?asset_type=indices|forex|commodities|crypto
```

##### GET /api/v1/market/quotes/{symbol}
Quote for specific symbol (e.g. `AAPL`, `EURUSD`, `GCUSD`).

##### GET /api/v1/market/quotes/{symbol}/history
Historical quotes.
```
?limit=100&from_timestamp=...&to_timestamp=...
```

##### GET /api/v1/market/status
Current market hours for all asset types.

#### OHLCV Candles

##### GET /api/v1/market/candles/{symbol}
Candlestick data.
```
?interval=1hour     # 1min|5min|15min|30min|1hour|4hour
&limit=100
&from_timestamp=...&to_timestamp=...
```

##### GET /api/v1/market/candles/{symbol}/latest
Most recent candle.
```
?interval=1hour
```

##### GET /api/v1/market/candles/asset-type/{asset_type}
Latest candles for all symbols in asset type.
```
?interval=1hour&limit=50
```

##### GET /api/v1/market/candles/{symbol}/timerange
Candles in time window.
```
?interval=1hour&hours=24
```

#### Symbol Search

##### GET /api/v1/market/symbols/search
Search symbols.
```
?query=gold&asset_type=commodities&limit=20
```

##### GET /api/v1/market/symbols/list
All available symbols.
```
?asset_type=indices
```

#### Historical Data

##### GET /api/v1/history/{symbol}
Historical EOD data.
```
?from_date=2025-01-01&to_date=2026-02-09&limit=365
```

#### Earnings

##### GET /api/v1/earnings/calendar
Earnings calendar.
```
?from_date=2026-02-01&to_date=2026-02-28&symbol=AAPL&limit=50
```

##### GET /api/v1/earnings/{symbol}/history
Earnings history.
```
?limit=20
```

#### Financial News

##### GET /api/v1/news
Latest financial news from database.
```
?page=1&limit=50&symbol=AAPL
```

##### GET /api/v1/news/stock
Latest stock market news.

##### GET /api/v1/news/by-symbol/{symbol}
News for specific symbol.
```
?days=30&limit=50
```

##### GET /api/v1/news/sentiment/{sentiment}
News by sentiment (positive|negative|neutral).

##### GET /api/v1/news/live/general
Live general news (direct from FMP API).

##### GET /api/v1/news/live/stock
Live stock news.

##### GET /api/v1/news/live/forex
Live forex news.

##### GET /api/v1/news/live/crypto
Live crypto news.

##### GET /api/v1/news/live/mergers-acquisitions
Live M&A news.

---

### 8. entity-canonicalization-service (Port 8112)

Entity deduplication, fuzzy matching, Wikidata lookup.

#### POST /api/v1/canonicalization/canonicalize
Canonicalize a single entity.
```json
{"entity_name": "Vladimir Putin", "entity_type": "PERSON"}
```

#### POST /api/v1/canonicalization/canonicalize/batch
Batch canonicalization (synchronous).
```json
{"entities": [{"name": "Putin", "type": "PERSON"}, {"name": "NATO", "type": "ORGANIZATION"}]}
```

#### POST /api/v1/canonicalization/canonicalize/batch/async
Async batch job.
```json
{"entities": [...], "webhook_url": "http://localhost:PORT/callback"}
```

#### GET /api/v1/canonicalization/jobs/{job_id}/status
Poll async job status.

#### GET /api/v1/canonicalization/jobs/{job_id}/result
Get async job results.

#### GET /api/v1/canonicalization/aliases/{canonical_name}
All aliases for a canonical entity.

#### GET /api/v1/canonicalization/stats
High-level statistics.

#### GET /api/v1/canonicalization/stats/detailed
Detailed statistics by entity type.

#### GET /api/v1/canonicalization/trends/entity-types
Entity type distribution trends.

#### GET /api/v1/canonicalization/fragmentation/report
Entity fragmentation analysis.

#### GET /api/v1/canonicalization/fragmentation/duplicates
Potential duplicate entities.

---

## API Reference — Auth-Required Services

All endpoints below require:
```
Authorization: Bearer {access_token}
```

---

### 9. sitrep-service (Port 8123)

Intelligence briefings (daily/weekly/breaking) generated from news clusters.

#### GET /api/v1/sitreps
List SITREPs.
```
?limit=20&offset=0
&report_type=daily|weekly|breaking
&category=conflict|finance|politics|humanitarian|security|technology|crypto
```

#### GET /api/v1/sitreps/latest
Latest SITREP of specified type.
```
?report_type=daily
```

#### GET /api/v1/sitreps/{sitrep_id}
Full SITREP with content, entities, metadata.

#### POST /api/v1/sitreps/generate
Trigger manual SITREP generation.
```json
{
  "report_type": "daily",
  "category": "security",
  "top_stories_count": 10,
  "min_cluster_size": 3
}
```

#### PATCH /api/v1/sitreps/{sitrep_id}/review
Mark as human-reviewed.
```json
{"reviewed": true}
```

#### DELETE /api/v1/sitreps/{sitrep_id}
Delete SITREP.

---

### 10. clustering-service (Port 8122)

Real-time article clustering, burst detection, topic discovery, semantic profiles.

#### Clusters

##### GET /api/v1/clusters
List clusters.
```
?status=active|archived|all
&min_articles=2
&hours=24         # 1-168
&limit=50&offset=0
```

##### GET /api/v1/clusters/{cluster_id}
Cluster details.

##### GET /api/v1/clusters/{cluster_id}/articles
Articles in cluster.
```
?limit=20&offset=0
```

#### Burst Detection

##### GET /api/v1/bursts
Recent burst alerts.
```
?hours=24
&severity=high
&category=conflict|finance|politics|humanitarian|security|technology|crypto
&deduplicate=true
&limit=50&offset=0
```

##### GET /api/v1/bursts/active
Currently active (unacknowledged) bursts.

##### GET /api/v1/bursts/stats
Burst detection statistics (24h, 7d, by severity).

##### GET /api/v1/bursts/{burst_id}
Burst details.

##### POST /api/v1/bursts/{burst_id}/acknowledge
Acknowledge burst alert.

##### GET /api/v1/bursts/cluster/{cluster_id}
Burst history for cluster.
```
?hours=168     # 1-720
```

#### Topics (Batch UMAP+HDBSCAN)

##### GET /api/v1/topics
Topic clusters from latest batch.
```
?min_size=10&limit=50&offset=0&batch_id=uuid
```

##### GET /api/v1/topics/search
Search topics.
```
?q=geopolitical tension
&mode=semantic|keyword
&limit=20&min_similarity=0.3
```

##### GET /api/v1/topics/batches
List batch clustering runs.
```
?status=running|completed|failed&limit=10
```

##### GET /api/v1/topics/similar/{article_id}
Topic clusters similar to an article.

##### GET /api/v1/topics/article/{article_id}
Topic cluster for specific article.

##### GET /api/v1/topics/{cluster_id}
Topic cluster details.
```
?sample_limit=10
```

#### Profiles (Semantic Categories)

##### GET /api/v1/profiles
All topic profiles.
```
?active_only=true
```

##### GET /api/v1/profiles/{name}
Profile details.

##### GET /api/v1/profiles/{name}/matches
Clusters matching a profile.
```
?limit=20&hours=24
```

##### GET /api/v1/profiles/matches/all
Matching clusters for ALL active profiles.
```
?limit_per_profile=10&hours=24
```

#### Escalation

##### GET /api/v1/escalation/summary (NO AUTH)
Aggregated escalation summary (geopolitical, military, economic domains).
```
?hours=24
```

##### GET /api/v1/escalation/clusters/{cluster_id} (NO AUTH)
Cluster escalation data with signal breakdown.
```
?recalculate=false
```

---

### 11. analytics-service (Port 8107)

Dashboards, reports, intelligence signals, RAG-powered Q&A.

#### Intelligence Signals

##### GET /api/v1/intelligence/top-stories
Top stories with signal decay scoring.
```
?limit=10&hours=24&apply_decay=true&min_priority=0
```

##### GET /api/v1/intelligence/bursts
Entity mention bursts (Kleinberg algorithm).
```
?entity=Putin&hours=24&min_level=1&limit=50
```

##### GET /api/v1/intelligence/momentum
Sentiment momentum (rate of change).
```
?entity=NATO&days=7&direction=improving|deteriorating&limit=20
```

##### GET /api/v1/intelligence/contrarian-alerts
Extreme sentiment detection (euphoria/panic).
```
?entity=...&history_days=90&limit=20
```

##### POST /api/v1/intelligence/novelty
Article novelty score.
```json
{
  "article_id": "uuid",
  "entities": ["entity1"],
  "event_type": "conflict",
  "primary_topic": "Ukraine",
  "published_at": "2026-02-09T12:00:00Z"
}
```

##### GET /api/v1/intelligence/summary
Combined intelligence summary.
```
?hours=24
```

##### GET /api/v1/intelligence/entity-sentiment-history (NO AUTH)
Sentiment timeseries for entity.
```
?entity=Putin&days=30
```

##### GET /api/v1/intelligence/ask (NO AUTH)
RAG-powered intelligence Q&A.
```
?question=What is the current risk level in the Middle East?
&depth=brief|detailed
```

##### GET /api/v1/intelligence/context (NO AUTH)
Raw intelligence context (no LLM).
```
?question=Ukraine conflict&limit=20&min_similarity=0.5
&entity=...&sector=...&days=30
```

#### Dashboards

##### GET /api/v1/dashboards (OPTIONAL AUTH)
List dashboards.
```
?include_public=true&skip=0&limit=50
```

##### GET /api/v1/dashboards/{id}/data (OPTIONAL AUTH)
Dashboard with live widget data.

#### Analytics Core

##### GET /api/v1/analytics/overview
System-wide analytics overview.

##### GET /api/v1/analytics/trends
Metric trend analysis.
```
?service=feed-service&metric_name=articles_processed
&hours=24&interval_minutes=60
```

##### GET /api/v1/analytics/service/{service_name}
Service-specific metrics.

#### Cache

##### GET /api/v1/cache/stats (NO AUTH)
Redis cache statistics.

---

### 12. narrative-service (Port 8119)

LLM-powered narrative frame detection, bias analysis, propaganda detection.

#### POST /api/v1/narrative/analyze/text
Analyze text for narrative frames and bias.
```json
{"text": "Full article text...", "source": "reuters.com"}
```
Response: frames detected, bias indicators, propaganda markers.
Performance: 150ms cold, 3-5ms cached.

#### GET /api/v1/narrative/overview
Overview statistics.
```
?days=30
```

#### GET /api/v1/narrative/frames
List narrative frames.
```
?page=1&per_page=50
&frame_type=conflict|responsibility|morality|security|human_interest|economic_consequences
&event_id=uuid
&min_confidence=0.5
```

#### POST /api/v1/narrative/frames
Create narrative frame.
```json
{
  "event_id": "uuid",
  "frame_type": "conflict",
  "confidence": 0.85,
  "text_excerpt": "...",
  "entities": ["entity1", "entity2"]
}
```

#### GET /api/v1/narrative/clusters
Narrative clusters.
```
?active_only=true&min_frame_count=3&limit=50
```

#### POST /api/v1/narrative/clusters/update
Update clusters from recent frames.

#### GET /api/v1/narrative/bias
Bias comparison across sources.
```
?event_id=uuid&days=7
```

---

### 13. research-service (Port 8103)

Deep research via Perplexity AI. Cost-tracked.

**Rate Limits:** 60 req/min, 500/hour, 5000/day
**Cost Limits:** $0.50/request, $50/day, $500/month

#### POST /api/v1/research/
Create research task.
```json
{
  "query": "Current state of EU sanctions against Russia",
  "model_name": "sonar-pro",
  "depth": "standard",
  "feed_id": "uuid",
  "article_id": "uuid"
}
```
Models: `sonar` | `sonar-pro` | `sonar-reasoning-pro`
Depth: `quick` | `standard` | `deep`

#### GET /api/v1/research/{task_id}
Get research result.

#### GET /api/v1/research/
List tasks.
```
?status=pending|processing|completed|failed
&feed_id=uuid&page=1&page_size=50
```

#### POST /api/v1/research/batch
Batch research.
```json
{"queries": ["query1", "query2"], "model_name": "sonar", "depth": "quick"}
```

#### GET /api/v1/research/stats
Usage and cost statistics.
```
?days=30
```

#### Templates

##### GET /api/v1/templates/
List research templates.

##### GET /api/v1/templates/functions
Specialized functions (feed_source_assessment, fact_check, trend_analysis).

##### POST /api/v1/templates/{template_id}/apply
Apply template to create research task.
```json
{"variables": {"entity": "NATO", "timeframe": "30d"}}
```

#### Runs

##### POST /api/v1/runs/
Create research run from template.
```json
{
  "template_id": "uuid",
  "parameters": {"entity": "Putin"},
  "model_name": "sonar-pro",
  "depth": "standard"
}
```

##### GET /api/v1/runs/{run_id}/status
Research run status.

---

## Common Workflows

### 1. Daily Intelligence Briefing

```
1. GET  :8118/api/v1/intelligence/overview
2. GET  :8122/api/v1/bursts/active                    (AUTH)
3. GET  :8107/api/v1/intelligence/top-stories          (AUTH)
4. GET  :8123/api/v1/sitreps/latest?report_type=daily  (AUTH)
5. GET  :8115/api/v1/geo/security/overview
```

### 2. Entity Deep Dive

```
1. POST :8112/api/v1/canonicalization/canonicalize  → canonical name
2. GET  :8111/api/v1/graph/entity/{name}/connections
3. GET  :8114/api/v1/entity/{name}/framing
4. GET  :8107/api/v1/intelligence/entity-sentiment-history?entity={name}
5. GET  :8111/api/v1/graph/narratives/frames/{name}
6. GET  :8106/api/v1/search?query={name}
```

### 3. Threat Assessment for Region

```
1. GET  :8115/api/v1/geo/security/countries?region=Middle East
2. GET  :8115/api/v1/geo/security/country/{iso_code}
3. GET  :8118/api/v1/intelligence/risk-history?days=30
4. GET  :8122/api/v1/bursts?category=security&hours=168  (AUTH)
5. POST :8118/api/v1/intelligence/risk/calculate  → risk score
```

### 4. Market Intelligence

```
1. GET  :8113/api/v1/market/quotes?asset_type=indices
2. GET  :8113/api/v1/market/candles/{symbol}?interval=1hour&hours=24
3. GET  :8113/api/v1/news/live/stock
4. GET  :8111/api/v1/graph/markets/{symbol}
5. GET  :8113/api/v1/earnings/calendar
```

### 5. Breaking Story Investigation

```
1. GET  :8122/api/v1/bursts/active                    (AUTH)
2. GET  :8122/api/v1/clusters/{cluster_id}/articles    (AUTH)
3. POST :8106/api/v1/search/semantic  → related articles
4. GET  :8114/api/v1/entity/{entity}/framing
5. POST :8103/api/v1/research/  → Perplexity deep research  (AUTH)
6. POST :8123/api/v1/sitreps/generate  → generate SITREP    (AUTH)
```

---

## Health Check (verify all services)

```
GET http://localhost:8118/health  → intelligence
GET http://localhost:8101/health  → feed
GET http://localhost:8106/health  → search
GET http://localhost:8115/health  → geolocation
GET http://localhost:8114/health  → narrative-gateway
GET http://localhost:8111/health  → knowledge-graph
GET http://localhost:8113/health  → fmp
GET http://localhost:8112/health  → entity-canonicalization
GET http://localhost:8123/health  → sitrep
GET http://localhost:8122/health  → clustering
GET http://localhost:8107/health  → analytics
GET http://localhost:8119/health  → narrative
GET http://localhost:8103/health  → research
```

---

## Swagger UI (interactive docs)

Each service has interactive API docs at:
```
http://localhost:{PORT}/docs
```

---

## Notes

- All responses are JSON
- Pagination: `skip`/`limit` (offset-based) or `page`/`page_size` (page-based)
- UUIDs are used for all entity IDs
- Timestamps are ISO 8601 format
- prediction-service (8116) is currently DISABLED
- scraping-service is internal (port 8009), not intended for agent access
- fmp-service runs in host network mode (port 8113 direct)

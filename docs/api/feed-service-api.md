# Feed Service API

Base path: `/api/v1/feeds`
Authentication: Bearer JWT required for all endpoints (except `/` and `/health`).

## Content Analysis Configuration

**IMPORTANT:** As of 2025-10-27, the Content Analysis system has been migrated from V1 to V2:

### V1 (DEPRECATED)
- 7 individual boolean flags per feed (enable_categorization, enable_finance_sentiment, etc.)
- Manual configuration required for each analysis type
- Used by legacy `content-analysis-service`
- **Status:** Deprecated, kept for backward compatibility only

### V2 (RECOMMENDED)
- Single `enable_analysis_v2` boolean flag per feed
- Intelligent AI pipeline automatically determines relevant analysis
- Used by new `content-analysis-v2` service
- **Features:**
  - TRIAGE agent scores article relevance (0-100)
  - 10 specialized agents across 4 tiers
  - Automatic entity extraction, sentiment analysis, categorization, summarization
  - Cost-efficient (only processes high-relevance articles)
- **Status:** Active, recommended for all new feeds

**Migration:** All feeds can use V2 by setting `enable_analysis_v2: true`. V1 flags are ignored when V2 is enabled.

See [ADR-027](../decisions/ADR-027-content-analysis-v2-feed-configuration.md) for migration details.

---

## GET /api/v1/feeds
**Summary:** List feeds
Get list of all feeds with pagination and advanced filtering.

Supports filtering by:
- Active status
- Feed status (ACTIVE, PAUSED, ERROR, INACTIVE)
- Category
- Health score range


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| skip | query | integer | No | Number of records to skip (pagination offset) |
| limit | query | integer | No | Maximum number of records to return |
| is_active | query | boolean | No | Filter by active status |
| status | query | string | No | Filter by feed status |
| category | query | string | No | Filter by category name |
| health_score_min | query | integer | No | Minimum health score (0-100) |
| health_score_max | query | integer | No | Maximum health score (0-100) |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | List of feeds | array[Feed] |
| 401 |  |  |

#### Response Schemas
**array[Feed]**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string (uuid) | Yes | Feed UUID |
| name | string | Yes | Feed display name |
| url | string (uri) | Yes | RSS/Atom feed URL |
| description | string | No | Feed description |
| fetch_interval | integer | Yes | Fetch interval in minutes (5 min to 24 hours) |
| is_active | boolean | Yes | Whether feed is active and should be fetched |
| status | string | Yes | Feed status |
| last_fetched_at | string (date-time) | No | Timestamp of last successful fetch |
| health_score | integer | Yes | Feed health score (0-100) |
| consecutive_failures | integer | Yes | Number of consecutive fetch failures |
| quality_score | integer | No | Feed quality score (0-100, auto-calculated from assessment) |
| total_items | integer | Yes | Total number of items in feed |
| items_last_24h | integer | Yes | Number of new items in last 24 hours |
| scrape_full_content | boolean | Yes | Whether to scrape full article content |
| scrape_method | string | Yes | Scraping method: `newspaper4k` (NLP-based extraction, default) or `playwright` (headless browser) |
| scrape_failure_threshold | integer | Yes | Auto-disable scraping after X consecutive failures (1-20, default: 5) |
| scrape_failure_count | integer | Yes | Current consecutive failure count |
| scrape_last_failure_at | string (date-time) | No | Timestamp of last scraping failure |
| scrape_disabled_reason | string | No | Reason for scraping being disabled: `manual`, `auto_threshold`, or null |
| enable_categorization | boolean | No | **[DEPRECATED]** Enable automatic article categorization (V1 - use enable_analysis_v2 instead) |
| enable_finance_sentiment | boolean | No | **[DEPRECATED]** Enable finance-specific sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_geopolitical_sentiment | boolean | No | **[DEPRECATED]** Enable geopolitical sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_osint_analysis | boolean | No | **[DEPRECATED]** Enable OSINT event analysis (V1 - use enable_analysis_v2 instead) |
| enable_summary | boolean | No | **[DEPRECATED]** Enable summary generation (V1 - use enable_analysis_v2 instead) |
| enable_entity_extraction | boolean | No | **[DEPRECATED]** Enable entity extraction (V1 - use enable_analysis_v2 instead) |
| enable_topic_classification | boolean | No | **[DEPRECATED]** Enable topic classification (V1 - use enable_analysis_v2 instead) |
| enable_analysis_v2 | boolean | No | Enable Content Analysis V2 pipeline (intelligent AI-powered analysis, recommended) |
| created_at | string (date-time) | Yes | Feed creation timestamp |
| updated_at | string (date-time) | Yes | Feed last update timestamp |
| categories | array | No | Feed categories for organization |
| legacy_id | integer | No | Legacy integer ID for backward compatibility |

---
## POST /api/v1/feeds/pre-assess
**Summary:** Pre-assess feed source
Run a credibility assessment of a feed source BEFORE creating the feed.

This endpoint:
- Calls the research service to analyze the feed source
- Returns assessment data (credibility tier, reputation score, political bias, etc.)
- Suggests values for feed creation (name, description, categories)
- Does NOT create or persist a feed record
- Supports polling for async task completion (max 30 seconds)

Use this to gather information about a feed source before committing to create it.

### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| url | query | string (uri) | Yes | RSS/Atom feed URL to assess |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Assessment completed successfully | PreAssessmentResponse |
| 400 | Invalid URL provided | Error |
| 403 | Not authenticated (JWT required) | Error |
| 500 | Assessment failed or timed out | Error |

#### Response Schemas
**PreAssessmentResponse**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| success | boolean | Yes | Whether assessment completed successfully |
| assessment | object | Yes | Assessment data from research service |
| suggested_values | object | Yes | Suggested values for feed creation |

**assessment object**
| Field | Type | Description |
| --- | --- | --- |
| credibility_tier | string | Credibility tier: `tier_1`, `tier_2`, or `tier_3` |
| reputation_score | integer | Reputation score (0-100) |
| founded_year | integer | Year the source was founded |
| organization_type | string | Type of organization (e.g., `major_news`, `independent_media`) |
| political_bias | string | Political bias assessment |
| editorial_standards | object | Editorial standards details |
| trust_ratings | object | Trust ratings from various sources |
| recommendation | object | Recommendations for feed configuration |
| assessment_summary | string | Human-readable summary of assessment |

**suggested_values object**
| Field | Type | Description |
| --- | --- | --- |
| name | string | Suggested feed name |
| description | string | Suggested feed description (truncated to 200 chars) |
| categories | array[string] | Suggested categories based on source type and bias |

### Example Request
```bash
curl -X POST "http://localhost:8101/api/v1/feeds/pre-assess?url=https://www.techcrunch.com/feed/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Example Response
```json
{
  "success": true,
  "assessment": {
    "credibility_tier": "tier_1",
    "reputation_score": 85,
    "founded_year": 2005,
    "organization_type": "major_tech_news",
    "political_bias": "center",
    "editorial_standards": {
      "fact_checking_level": "high",
      "corrections_policy": "standard",
      "source_attribution": "consistent"
    },
    "trust_ratings": {
      "media_bias_fact_check": "High",
      "allsides_rating": "center",
      "newsguard_score": 85
    },
    "recommendation": {
      "skip_waiting_period": true,
      "initial_quality_boost": 10,
      "bot_detection_threshold": 0.7
    },
    "assessment_summary": "TechCrunch is a well-established technology news platform..."
  },
  "suggested_values": {
    "name": "Techcrunch",
    "description": "TechCrunch is a well-established technology news platform with high credibility...",
    "categories": ["Technology", "News"]
  }
}
```

---
## POST /api/v1/feeds
**Summary:** Create feed
Add a new RSS/Atom feed to the system.

After creation:
- Initial health record is created
- Feed is automatically fetched in background
- `feed.created` event is published to RabbitMQ


### Request Body
**application/json**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| name | string | Yes | Feed display name |
| url | string (uri) | Yes | RSS/Atom feed URL |
| description | string | No | Feed description |
| fetch_interval | integer | No | Fetch interval in minutes (5-1440, default: 60) |
| scrape_full_content | boolean | No | Whether to scrape full article content (default: false) |
| scrape_method | string | No | Scraping method: `newspaper4k` (default) or `playwright`. Must match pattern: `^(newspaper4k|playwright)$` |
| scrape_failure_threshold | integer | No | Auto-disable threshold for consecutive failures (1-20, default: 5) |
| enable_categorization | boolean | No | **[DEPRECATED]** Enable automatic categorization (V1 - use enable_analysis_v2 instead) |
| enable_finance_sentiment | boolean | No | **[DEPRECATED]** Enable finance sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_geopolitical_sentiment | boolean | No | **[DEPRECATED]** Enable geopolitical sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_osint_analysis | boolean | No | **[DEPRECATED]** Enable OSINT analysis (V1 - use enable_analysis_v2 instead) |
| enable_summary | boolean | No | **[DEPRECATED]** Enable summary generation (V1 - use enable_analysis_v2 instead) |
| enable_entity_extraction | boolean | No | **[DEPRECATED]** Enable entity extraction (V1 - use enable_analysis_v2 instead) |
| enable_topic_classification | boolean | No | **[DEPRECATED]** Enable topic classification (V1 - use enable_analysis_v2 instead) |
| enable_analysis_v2 | boolean | No | Enable Content Analysis V2 pipeline (default: false, recommended to enable) |
| categories | array | No | Initial feed categories |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 201 | Feed created successfully | Feed |
| 400 | Invalid request (validation error) | Error |
| 409 | Feed with this URL already exists | Error |
| 401 |  |  |

#### Response Schemas
**Feed**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string (uuid) | Yes | Feed UUID |
| name | string | Yes | Feed display name |
| url | string (uri) | Yes | RSS/Atom feed URL |
| description | string | No | Feed description |
| fetch_interval | integer | Yes | Fetch interval in minutes (5 min to 24 hours) |
| is_active | boolean | Yes | Whether feed is active and should be fetched |
| status | string | Yes | Feed status |
| last_fetched_at | string (date-time) | No | Timestamp of last successful fetch |
| health_score | integer | Yes | Feed health score (0-100) |
| consecutive_failures | integer | Yes | Number of consecutive fetch failures |
| quality_score | integer | No | Feed quality score (0-100, auto-calculated from assessment) |
| total_items | integer | Yes | Total number of items in feed |
| items_last_24h | integer | Yes | Number of new items in last 24 hours |
| scrape_full_content | boolean | Yes | Whether to scrape full article content |
| scrape_method | string | Yes | Scraping method: `newspaper4k` (NLP-based extraction, default) or `playwright` (headless browser) |
| scrape_failure_threshold | integer | Yes | Auto-disable scraping after X consecutive failures (1-20, default: 5) |
| scrape_failure_count | integer | Yes | Current consecutive failure count |
| scrape_last_failure_at | string (date-time) | No | Timestamp of last scraping failure |
| scrape_disabled_reason | string | No | Reason for scraping being disabled: `manual`, `auto_threshold`, or null |
| enable_categorization | boolean | No | **[DEPRECATED]** Enable automatic article categorization (V1 - use enable_analysis_v2 instead) |
| enable_finance_sentiment | boolean | No | **[DEPRECATED]** Enable finance-specific sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_geopolitical_sentiment | boolean | No | **[DEPRECATED]** Enable geopolitical sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_osint_analysis | boolean | No | **[DEPRECATED]** Enable OSINT event analysis (V1 - use enable_analysis_v2 instead) |
| enable_summary | boolean | No | **[DEPRECATED]** Enable summary generation (V1 - use enable_analysis_v2 instead) |
| enable_entity_extraction | boolean | No | **[DEPRECATED]** Enable entity extraction (V1 - use enable_analysis_v2 instead) |
| enable_topic_classification | boolean | No | **[DEPRECATED]** Enable topic classification (V1 - use enable_analysis_v2 instead) |
| enable_analysis_v2 | boolean | No | Enable Content Analysis V2 pipeline (intelligent AI-powered analysis, recommended) |
| created_at | string (date-time) | Yes | Feed creation timestamp |
| updated_at | string (date-time) | Yes | Feed last update timestamp |
| categories | array | No | Feed categories for organization |
| legacy_id | integer | No | Legacy integer ID for backward compatibility |

**Error**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| detail | string | Yes | Error message |
| type | string | No | Error type/code |

---
## POST /api/v1/feeds/bulk-fetch
**Summary:** Bulk fetch feeds
Trigger fetch for multiple feeds or all active feeds.

If `feed_ids` is empty or null, all active feeds will be fetched.
Use `force: true` to fetch even recently fetched feeds (ignore rate limiting).

All fetches are performed asynchronously in background.


### Request Body
**application/json**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| feed_ids | array | No | Feed UUIDs to fetch (empty/null = all active feeds) |
| force | boolean | No | Force fetch even if recently fetched |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Bulk fetch scheduled | BulkFetchResponse |

#### Response Schemas
**BulkFetchResponse**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| total_feeds | integer | Yes | Total number of feeds scheduled |
| successful_fetches | integer | Yes | Number of successful fetches (updated by background tasks) |
| failed_fetches | integer | Yes | Number of failed fetches (updated by background tasks) |
| total_new_items | integer | Yes | Total new items fetched (updated by background tasks) |
| details | array | Yes | Per-feed details |

---
## GET /api/v1/feeds/items
**Summary:** List articles across all feeds
Retrieve articles from all feeds with advanced filtering and pagination.

This endpoint aggregates articles from multiple feeds, making it ideal for:
- Creating a unified article listing page
- Filtering articles by feed, date range, or content availability
- Building cross-feed search and discovery features

Articles include associated sentiment analysis data when available:
- Standard sentiment (overall_sentiment, confidence)
- Financial sentiment (market_sentiment, volatility, economic_impact)
- Geopolitical sentiment (stability_score, security_relevance)
- Category classification

Items are returned sorted by ingestion date (newest first by default).
**Note:** As of 2025-10-25, default sorting changed from `published_at` to `created_at` to show recently-added articles first. See ADR-021.


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| skip | query | integer | No | Number of records to skip (pagination offset). Default: 0 |
| limit | query | integer | No | Maximum number of records to return (1-100). Default: 20 |
| feed_ids | query | string | No | Comma-separated list of feed UUIDs to filter by. If omitted, includes all feeds |
| date_from | query | string (date-time) | No | Filter items published after this datetime (ISO 8601 format) |
| date_to | query | string (date-time) | No | Filter items published before this datetime (ISO 8601 format) |
| has_content | query | boolean | No | Filter by scraped content availability. True = only items with scraped content, False = only items without |
| sentiment | query | string | No | **[NEW 2025-11-08]** Filter by sentiment from V2 analysis: `positive`, `negative`, `neutral`, `mixed`. Case-insensitive. Uses SQL-level JSONB filtering on `tier2_results.SENTIMENT_ANALYST.overall_sentiment` |
| category | query | string | No | **[NEW 2025-11-08]** Filter by category from V2 analysis: `Geopolitics Security`, `Politics Society`, `Economy Markets`, `Climate Environment Health`, `Panorama`, `Technology Science`. Uses SQL-level JSONB filtering on `triage_results.category` |
| sort_by | query | string | No | Sort field: 'created_at' or 'published_at'. Default: 'created_at' (changed 2025-10-25) |
| order | query | string | No | Sort order: 'asc' or 'desc'. Default: 'desc' |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | List of articles with feed context | array[FeedItemWithFeed] |
| 401 | Unauthorized (JWT required) |  |

#### Response Schemas
**array[FeedItemWithFeed]**
Each item includes all FeedItem fields plus feed context:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string (uuid) | Yes | Item UUID |
| feed_id | string (uuid) | Yes | Parent feed UUID |
| feed_name | string | Yes | Name of the feed this item belongs to |
| title | string | Yes | Item title |
| link | string (uri) | Yes | Link to original article |
| description | string | No | Item description or summary |
| content | string | No | Full content (RSS content or scraped) |
| author | string | No | Article author |
| published_at | string (date-time) | No | Publication timestamp |
| guid | string | No | RSS GUID (unique identifier from feed) |
| content_hash | string | Yes | SHA-256 hash for deduplication |
| scraped_at | string (date-time) | No | Timestamp when content was scraped |
| scrape_status | string | No | Scraping status (pending, success, failed) |
| scrape_word_count | integer | No | Word count of scraped content |
| created_at | string (date-time) | Yes | Item creation timestamp in database |
| legacy_id | integer | No | Legacy integer ID for backward compatibility |
| legacy_feed_id | integer | No | Legacy feed integer ID |
| sentiment_analysis | object | No | Standard sentiment analysis results |
| finance_sentiment | object | No | Financial sentiment analysis results |
| geopolitical_sentiment | object | No | Geopolitical sentiment analysis results |
| category_analysis | object | No | Article category classification |

**sentiment_analysis object:**
| Field | Type | Description |
| --- | --- | --- |
| overall_sentiment | string | Sentiment: positive, negative, neutral, mixed |
| confidence | number (float) | Confidence score (0.0-1.0) |
| subjectivity | number (float) | Subjectivity score (0.0-1.0) |
| reasoning | string | AI reasoning for sentiment classification |

**finance_sentiment object:**
| Field | Type | Description |
| --- | --- | --- |
| market_sentiment | string | Market sentiment: bullish, bearish, neutral |
| market_confidence | number (float) | Confidence score (0.0-1.0) |
| volatility | number (float) | Market volatility indicator (0.0-1.0) |
| economic_impact | number (float) | Economic impact score (0.0-1.0) |
| affected_sectors | array[string] | Financial sectors affected |

**geopolitical_sentiment object:**
| Field | Type | Description |
| --- | --- | --- |
| stability_score | number (float) | Political stability score (-1.0 to 1.0) |
| security_relevance | number (float) | Security relevance score (0.0-1.0) |
| escalation_potential | number (float) | Conflict escalation potential (0.0-1.0) |
| regions_affected | array[string] | Regions/countries affected |

**category_analysis object:**
| Field | Type | Description |
| --- | --- | --- |
| category | string | Primary category classification |
| confidence | number (float) | Classification confidence (0.0-1.0) |

### Filter Implementation Notes (Added 2025-11-08)

The `sentiment` and `category` filters use **SQL-level JSONB filtering** for optimal performance and proper pagination support.

**Technical Details:**
- Filters are applied directly in PostgreSQL using JSONB operators before pagination
- LEFT JOIN with `public.article_analysis` table when filters are active
- Supports case-insensitive sentiment matching (e.g., "negative" matches "NEGATIVE")
- Category values are normalized from UI format to database format (e.g., "Geopolitics Security" → "GEOPOLITICS_SECURITY")

**Available Filter Values:**
- **Sentiment:** `positive`, `negative`, `neutral`, `mixed` (case-insensitive)
- **Category:**
  - `Geopolitics Security` (DB: `GEOPOLITICS_SECURITY`)
  - `Politics Society` (DB: `POLITICS_SOCIETY`)
  - `Economy Markets` (DB: `ECONOMY_MARKETS`)
  - `Climate Environment Health` (DB: `CLIMATE_ENVIRONMENT_HEALTH`)
  - `Panorama` (DB: `PANORAMA`)
  - `Technology Science` (DB: `TECHNOLOGY_SCIENCE`)

**Performance:**
- Pagination works correctly with filters active (no post-query filtering)
- Filters can be combined (e.g., `?category=PANORAMA&sentiment=negative`)
- Only items with V2 analysis data will match filter criteria

**See also:** ADR-041 for the decision to use SQL-level filtering instead of post-query filtering.

---
## GET /api/v1/feeds/{feed_id}
**Summary:** Get feed details
Retrieve detailed information about a specific feed by UUID

### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Feed details | Feed |
| 404 |  |  |
| 401 |  |  |

#### Response Schemas
**Feed**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string (uuid) | Yes | Feed UUID |
| name | string | Yes | Feed display name |
| url | string (uri) | Yes | RSS/Atom feed URL |
| description | string | No | Feed description |
| fetch_interval | integer | Yes | Fetch interval in minutes (5 min to 24 hours) |
| is_active | boolean | Yes | Whether feed is active and should be fetched |
| status | string | Yes | Feed status |
| last_fetched_at | string (date-time) | No | Timestamp of last successful fetch |
| health_score | integer | Yes | Feed health score (0-100) |
| consecutive_failures | integer | Yes | Number of consecutive fetch failures |
| quality_score | integer | No | Feed quality score (0-100, auto-calculated from assessment) |
| total_items | integer | Yes | Total number of items in feed |
| items_last_24h | integer | Yes | Number of new items in last 24 hours |
| scrape_full_content | boolean | Yes | Whether to scrape full article content |
| scrape_method | string | Yes | Scraping method: `newspaper4k` (NLP-based extraction, default) or `playwright` (headless browser) |
| scrape_failure_threshold | integer | Yes | Auto-disable scraping after X consecutive failures (1-20, default: 5) |
| scrape_failure_count | integer | Yes | Current consecutive failure count |
| scrape_last_failure_at | string (date-time) | No | Timestamp of last scraping failure |
| scrape_disabled_reason | string | No | Reason for scraping being disabled: `manual`, `auto_threshold`, or null |
| enable_categorization | boolean | No | **[DEPRECATED]** Enable automatic article categorization (V1 - use enable_analysis_v2 instead) |
| enable_finance_sentiment | boolean | No | **[DEPRECATED]** Enable finance-specific sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_geopolitical_sentiment | boolean | No | **[DEPRECATED]** Enable geopolitical sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_osint_analysis | boolean | No | **[DEPRECATED]** Enable OSINT event analysis (V1 - use enable_analysis_v2 instead) |
| enable_summary | boolean | No | **[DEPRECATED]** Enable summary generation (V1 - use enable_analysis_v2 instead) |
| enable_entity_extraction | boolean | No | **[DEPRECATED]** Enable entity extraction (V1 - use enable_analysis_v2 instead) |
| enable_topic_classification | boolean | No | **[DEPRECATED]** Enable topic classification (V1 - use enable_analysis_v2 instead) |
| enable_analysis_v2 | boolean | No | Enable Content Analysis V2 pipeline (intelligent AI-powered analysis, recommended) |
| created_at | string (date-time) | Yes | Feed creation timestamp |
| updated_at | string (date-time) | Yes | Feed last update timestamp |
| categories | array | No | Feed categories for organization |
| legacy_id | integer | No | Legacy integer ID for backward compatibility |

---
## PUT /api/v1/feeds/{feed_id}
**Summary:** Update feed
Update feed configuration.

Note: The feed URL cannot be changed after creation.

Publishes `feed.updated` event with changed fields.


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |

### Request Body
**application/json**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| name | string | No | Feed display name (1-200 characters) |
| description | string | No | Feed description |
| fetch_interval | integer | No | Fetch interval in minutes (min: 5, max: 1440 = 24 hours) |
| is_active | boolean | No | Whether feed is active |
| scrape_full_content | boolean | No | Whether to scrape full content |
| scrape_method | string | No | Scraping method |
| enable_categorization | boolean | No | **[DEPRECATED]** Enable categorization (V1 - use enable_analysis_v2 instead) |
| enable_finance_sentiment | boolean | No | **[DEPRECATED]** Enable finance sentiment (V1 - use enable_analysis_v2 instead) |
| enable_geopolitical_sentiment | boolean | No | **[DEPRECATED]** Enable geopolitical sentiment (V1 - use enable_analysis_v2 instead) |
| enable_osint_analysis | boolean | No | **[DEPRECATED]** Enable OSINT analysis (V1 - use enable_analysis_v2 instead) |
| enable_summary | boolean | No | **[DEPRECATED]** Enable summary generation (V1 - use enable_analysis_v2 instead) |
| enable_entity_extraction | boolean | No | **[DEPRECATED]** Enable entity extraction (V1 - use enable_analysis_v2 instead) |
| enable_topic_classification | boolean | No | **[DEPRECATED]** Enable topic classification (V1 - use enable_analysis_v2 instead) |
| enable_analysis_v2 | boolean | No | Enable Content Analysis V2 pipeline (intelligent AI-powered analysis, recommended) |
| categories | array | No | Updated categories (replaces existing) |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Feed updated successfully | Feed |
| 400 | Invalid request | Error |
| 404 |  |  |
| 401 |  |  |

#### Response Schemas
**Feed**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string (uuid) | Yes | Feed UUID |
| name | string | Yes | Feed display name |
| url | string (uri) | Yes | RSS/Atom feed URL |
| description | string | No | Feed description |
| fetch_interval | integer | Yes | Fetch interval in minutes (5 min to 24 hours) |
| is_active | boolean | Yes | Whether feed is active and should be fetched |
| status | string | Yes | Feed status |
| last_fetched_at | string (date-time) | No | Timestamp of last successful fetch |
| health_score | integer | Yes | Feed health score (0-100) |
| consecutive_failures | integer | Yes | Number of consecutive fetch failures |
| quality_score | integer | No | Feed quality score (0-100, auto-calculated from assessment) |
| total_items | integer | Yes | Total number of items in feed |
| items_last_24h | integer | Yes | Number of new items in last 24 hours |
| scrape_full_content | boolean | Yes | Whether to scrape full article content |
| scrape_method | string | Yes | Scraping method: `newspaper4k` (NLP-based extraction, default) or `playwright` (headless browser) |
| scrape_failure_threshold | integer | Yes | Auto-disable scraping after X consecutive failures (1-20, default: 5) |
| scrape_failure_count | integer | Yes | Current consecutive failure count |
| scrape_last_failure_at | string (date-time) | No | Timestamp of last scraping failure |
| scrape_disabled_reason | string | No | Reason for scraping being disabled: `manual`, `auto_threshold`, or null |
| enable_categorization | boolean | No | **[DEPRECATED]** Enable automatic article categorization (V1 - use enable_analysis_v2 instead) |
| enable_finance_sentiment | boolean | No | **[DEPRECATED]** Enable finance-specific sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_geopolitical_sentiment | boolean | No | **[DEPRECATED]** Enable geopolitical sentiment analysis (V1 - use enable_analysis_v2 instead) |
| enable_osint_analysis | boolean | No | **[DEPRECATED]** Enable OSINT event analysis (V1 - use enable_analysis_v2 instead) |
| enable_summary | boolean | No | **[DEPRECATED]** Enable summary generation (V1 - use enable_analysis_v2 instead) |
| enable_entity_extraction | boolean | No | **[DEPRECATED]** Enable entity extraction (V1 - use enable_analysis_v2 instead) |
| enable_topic_classification | boolean | No | **[DEPRECATED]** Enable topic classification (V1 - use enable_analysis_v2 instead) |
| enable_analysis_v2 | boolean | No | Enable Content Analysis V2 pipeline (intelligent AI-powered analysis, recommended) |
| created_at | string (date-time) | Yes | Feed creation timestamp |
| updated_at | string (date-time) | Yes | Feed last update timestamp |
| categories | array | No | Feed categories for organization |
| legacy_id | integer | No | Legacy integer ID for backward compatibility |

**Error**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| detail | string | Yes | Error message |
| type | string | No | Error type/code |

### Example Request: Update Fetch Interval
```bash
curl -X PUT "http://localhost:8101/api/v1/feeds/03f44c8e-687d-444c-8e6b-59131b547db1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fetch_interval": 60
  }'
```

### Example Request: Update Multiple Settings
```bash
curl -X PUT "http://localhost:8101/api/v1/feeds/03f44c8e-687d-444c-8e6b-59131b547db1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechCrunch RSS",
    "fetch_interval": 30,
    "is_active": true,
    "enable_categorization": true,
    "enable_finance_sentiment": true
  }'
```

### Validation Rules
- `fetch_interval`: Must be between 5 and 1440 minutes
  - 5-15 min: Suitable for breaking news sources
  - 15-60 min: Standard interval for active news feeds
  - 60-360 min: Moderate interval for low-priority feeds
  - 360-1440 min: Infrequent updates for archives
- `name`: Must be 1-200 characters if provided
- `scrape_method`: Must be either `newspaper4k` or `playwright` if provided
- `scrape_failure_threshold`: Must be between 1 and 20 if provided

---
## DELETE /api/v1/feeds/{feed_id}
**Summary:** Delete feed
Remove feed and all associated data (cascade delete).

Deletes:
- Feed configuration
- All feed items
- Fetch logs
- Health records
- Categories
- Schedules

Publishes `feed.deleted` event.


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 204 | Feed deleted successfully (no content) |  |
| 404 |  |  |
| 401 |  |  |

---
## POST /api/v1/feeds/{feed_id}/fetch
**Summary:** Manually trigger feed fetch
Trigger immediate feed fetch and parsing.

The fetch operation runs asynchronously in background.
Use GET /api/v1/feeds/{feed_id} to check last_fetched_at timestamp.

**Smart Auto-Reset (New in v1.1.0):** If feed is in ERROR status, automatically resets to ACTIVE before fetching:
- Status: ERROR → ACTIVE
- Consecutive failures: Reset to 0
- Error message: Cleared
- Health score: +10 bonus

Publishes `feed.fetched` or `feed.fetch_failed` event.


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Fetch triggered successfully | FetchResponse |
| 400 | Feed is not active | Error |
| 404 |  |  |
| 401 |  |  |

#### Response Schemas
**FetchResponse**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| success | boolean | Yes | Whether fetch was triggered |
| message | string | Yes | Human-readable status message |
| feed_id | string (uuid) | Yes | Feed UUID |
| auto_reset | boolean | No | True if ERROR status was auto-reset to ACTIVE |

**Error**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| detail | string | Yes | Error message |
| type | string | No | Error type/code |

---
## POST /api/v1/feeds/{feed_id}/reset-error
**Summary:** Reset feed ERROR status
**New in v1.1.0**

Manually reset a feed's ERROR status back to ACTIVE.

**Use Cases:**
- Feed had temporary network issue (HTTP 522, timeouts)
- Source server was down but is now back online
- Want to clear error before changing feed URL
- Manual recovery after investigating the error

**Actions Performed:**
- Status: ERROR → ACTIVE
- Consecutive failures: Reset to 0
- Error message & timestamp: Cleared
- Health score: +20 bonus (higher than auto-reset)

Publishes `feed.error_reset` monitoring event.

### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Error reset successfully | ResetErrorResponse |
| 400 | Feed is not in ERROR status | ResetErrorResponse |
| 404 |  |  |
| 401 |  |  |

#### Response Schemas
**ResetErrorResponse**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| success | boolean | Yes | Whether reset was successful |
| message | string | Yes | Human-readable status message |
| feed_id | string (uuid) | Yes | Feed UUID |
| current_status | string | Yes | Current feed status after reset |
| previous_error | string | No | Error message before reset (if any) |
| error_duration_hours | number (float) | No | How long feed was in ERROR state |

---
## GET /api/v1/feeds/{feed_id}/health
**Summary:** Get feed health metrics
Get detailed health metrics for a specific feed.

Health metrics include:
- Overall health score (0-100)
- Success rate and uptime (24h, 7d, 30d)
- Average response time
- Consecutive failures count
- Last success/failure timestamps


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Feed health metrics | FeedHealth |
| 404 | Feed not found | Error |

#### Response Schemas
**FeedHealth**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| feed_id | string (uuid) | Yes |  |
| health_score | integer | Yes | Overall health score (0-100) |
| consecutive_failures | integer | Yes | Number of consecutive failures |
| is_healthy | boolean | Yes | Whether feed is healthy (score > 70) |
| avg_response_time_ms | number (float) | No | Average response time in milliseconds |
| success_rate | number (float) | Yes | Success rate (0.0-1.0) |
| uptime_24h | number (float) | Yes | Uptime in last 24 hours (0.0-1.0) |
| uptime_7d | number (float) | Yes | Uptime in last 7 days (0.0-1.0) |
| uptime_30d | number (float) | Yes | Uptime in last 30 days (0.0-1.0) |
| last_success_at | string (date-time) | No | Last successful fetch timestamp |
| last_failure_at | string (date-time) | No | Last failed fetch timestamp |

**Error**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| detail | string | Yes | Error message |
| type | string | No | Error type/code |

---
## GET /api/v1/feeds/{feed_id}/items
**Summary:** Get feed items
Retrieve items (articles/entries) from a specific feed.

Items are returned in reverse chronological order (newest first).
Use `since` parameter to get only recent items.


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |
| skip | query | integer | No | Number of items to skip |
| limit | query | integer | No | Maximum number of items to return |
| since | query | string (date-time) | No | Only return items published after this datetime (ISO 8601) |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | List of feed items | array[FeedItem] |
| 404 | Feed not found | Error |
| 401 |  |  |

#### Response Schemas
**array[FeedItem]**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string (uuid) | Yes | Item UUID |
| feed_id | string (uuid) | Yes | Parent feed UUID |
| title | string | Yes | Item title |
| link | string (uri) | Yes | Link to original article |
| description | string | No | Item description or summary |
| content | string | No | Full content (RSS content or scraped) |
| author | string | No | Article author |
| published_at | string (date-time) | No | Publication timestamp |
| guid | string | No | RSS GUID (unique identifier from feed) |
| content_hash | string | Yes | SHA-256 hash for deduplication |
| scraped_at | string (date-time) | No | Timestamp when content was scraped |
| scrape_status | string | No | Scraping status |
| scrape_word_count | integer | No | Word count of scraped content |
| created_at | string (date-time) | Yes | Item creation timestamp in database |
| legacy_id | integer | No | Legacy integer ID for backward compatibility |
| legacy_feed_id | integer | No | Legacy feed integer ID |

**Error**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| detail | string | Yes | Error message |
| type | string | No | Error type/code |

---
## PATCH /api/v1/feeds/{feed_id}/items/{item_id}
**Summary:** Update feed item
Update a feed item (used by scraping service to store scraped content).

Note: This endpoint does NOT require JWT authentication.
It's designed for service-to-service communication and should use
X-Service-Key header for authentication (implementation pending).

Items are append-only, so only scraping-related fields can be updated.


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |
| item_id | path | string (uuid) | Yes | Feed item UUID |

### Request Body
**application/json**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| content | string | No | Full scraped content |
| scraped_at | string (date-time) | No | Scraping timestamp |
| scrape_status | string | No | Scraping status |
| scrape_word_count | integer | No | Word count |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Item updated successfully | FeedItem |
| 404 | Feed or item not found | Error |

#### Response Schemas
**FeedItem**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| id | string (uuid) | Yes | Item UUID |
| feed_id | string (uuid) | Yes | Parent feed UUID |
| title | string | Yes | Item title |
| link | string (uri) | Yes | Link to original article |
| description | string | No | Item description or summary |
| content | string | No | Full content (RSS content or scraped) |
| author | string | No | Article author |
| published_at | string (date-time) | No | Publication timestamp |
| guid | string | No | RSS GUID (unique identifier from feed) |
| content_hash | string | Yes | SHA-256 hash for deduplication |
| scraped_at | string (date-time) | No | Timestamp when content was scraped |
| scrape_status | string | No | Scraping status |
| scrape_word_count | integer | No | Word count of scraped content |
| created_at | string (date-time) | Yes | Item creation timestamp in database |
| legacy_id | integer | No | Legacy integer ID for backward compatibility |
| legacy_feed_id | integer | No | Legacy feed integer ID |

**Error**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| detail | string | Yes | Error message |
| type | string | No | Error type/code |

---

## Events Published

The feed service publishes events to RabbitMQ for downstream processing.

### `article.created`

Published when a new article is successfully scraped and stored.

**Exchange:** `news.events`
**Routing Key:** `article.created`

**Event Schema:**
```json
{
  "event_type": "article.created",
  "payload": {
    "item_id": "uuid",
    "feed_id": "uuid",
    "title": "string",
    "link": "string (uri)",
    "content": "string",
    "description": "string",
    "author": "string",
    "published_at": "datetime (ISO 8601)",
    "word_count": "integer",
    "analysis_config": {
      "enable_summary": "boolean",              // DEPRECATED - V1 only
      "enable_entity_extraction": "boolean",    // DEPRECATED - V1 only
      "enable_topic_classification": "boolean", // DEPRECATED - V1 only
      "enable_categorization": "boolean",       // DEPRECATED - V1 only
      "enable_finance_sentiment": "boolean",    // DEPRECATED - V1 only
      "enable_geopolitical_sentiment": "boolean", // DEPRECATED - V1 only
      "enable_osint": "boolean",                // DEPRECATED - V1 only
      "enable_analysis_v2": "boolean"           // V2 - Recommended (intelligent pipeline)
    }
  }
}
```

**Event-Carried State Transfer Pattern:**
The `analysis_config` object contains the feed's analysis configuration at the time of article creation. This eliminates the need for consuming services (like content-analysis) to query the feed-service database for configuration, reducing coupling between microservices.

**Configuration Source:**
- **V1 (DEPRECATED):** Derived from individual feed settings (`enable_summary`, `enable_entity_extraction`, etc.) in `feeds` table
- **V2 (RECOMMENDED):** Derived from `enable_analysis_v2` flag in `feeds` table. When enabled, the content-analysis-v2 service intelligently determines what analysis to perform based on article content.

**Published by:** `services/feed-service/app/services/feed_fetcher.py:404-423`

**Consumed by:**
- `content-analysis-service` - Creates analysis jobs based on config

**When Published:**
- After successful article scraping (word_count >= 100)
- After database commit (transactional guarantee)
- Includes complete analysis configuration from feed settings

### `feed.created`

Published when a new feed is added to the system.

**Exchange:** `news.events`
**Routing Key:** `feed.created`

### `feed.updated`

Published when feed configuration is modified.

**Exchange:** `news.events`
**Routing Key:** `feed.updated`

### `feed.deleted`

Published when a feed is removed from the system.

**Exchange:** `news.events`
**Routing Key:** `feed.deleted`

---
## GET /api/v1/feeds/{feed_id}/quality
**Summary:** Get feed quality score
Get quality score and metrics for a specific feed.

Quality score (0-100) is calculated based on:
- **Freshness score**: How often new content is published
- **Consistency score**: Publishing regularity
- **Content score**: Content quality and length
- **Reliability score**: Feed uptime and response time

Includes actionable recommendations for improvement.


### Parameters
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| feed_id | path | string (uuid) | Yes | Feed UUID |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Feed quality metrics | FeedQuality |
| 404 | Feed not found | Error |

#### Response Schemas
**FeedQuality**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| feed_id | string (uuid) | Yes |  |
| quality_score | number (float) | Yes | Overall quality score (0-100) |
| freshness_score | number (float) | Yes | Content freshness score |
| consistency_score | number (float) | Yes | Publishing consistency score |
| content_score | number (float) | Yes | Content quality score |
| reliability_score | number (float) | Yes | Feed reliability score |
| recommendations | array | Yes | Actionable recommendations |
| calculated_at | string (date-time) | Yes | Calculation timestamp |

**Error**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| detail | string | Yes | Error message |
| type | string | No | Error type/code |

---

## GET /api/v1/feeds/{feed_id}/threshold
**Summary:** Get scraping threshold for feed

Get the configured scraping failure threshold for a specific feed.

### Path Parameters
| Name | Type | Required | Description |
| --- | --- | --- | --- |
| feed_id | string (uuid) | Yes | Feed UUID |

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Threshold retrieved successfully | ThresholdResponse |
| 404 | Feed not found | Error |
| 401 | Unauthorized | Error |

#### Response Schema
**ThresholdResponse**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| feed_id | string (uuid) | Yes | Feed UUID |
| scrape_failure_threshold | integer | Yes | Current threshold value (1-20) |

**Example Response:**
```json
{
  "feed_id": "123e4567-e89b-12d3-a456-426614174000",
  "scrape_failure_threshold": 7
}
```

---

## POST /api/v1/feeds/{feed_id}/scraping/reset
**Summary:** Reset scraping failures

Reset the scraping failure counter and re-enable scraping for a feed that was auto-disabled due to reaching the failure threshold.

### Path Parameters
| Name | Type | Required | Description |
| --- | --- | --- | --- |
| feed_id | string (uuid) | Yes | Feed UUID |

### Behavior
- Resets `scrape_failure_count` to 0
- Clears `scrape_last_failure_at` timestamp
- Clears `scrape_disabled_reason`
- Re-enables `scrape_full_content` if it was disabled

### Responses
| Status | Description | Schema |
| --- | --- | --- |
| 200 | Scraping reset successfully | ResetResponse |
| 404 | Feed not found | Error |
| 401 | Unauthorized | Error |

#### Response Schema
**ResetResponse**
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| message | string | Yes | Success message |
| feed_id | string (uuid) | Yes | Feed UUID |

**Example Response:**
```json
{
  "message": "Scraping failures reset successfully",
  "feed_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

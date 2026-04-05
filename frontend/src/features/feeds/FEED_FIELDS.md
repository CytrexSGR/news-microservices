# Feed Fields Documentation

This document describes all fields available in the Feed data structure.

## Feed Object

### Basic Feed Information

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique identifier for the feed |
| `name` | string | Yes | Display name of the feed |
| `url` | string (HttpUrl) | Yes | RSS/Atom feed URL |
| `description` | string | No | Optional description of the feed content |
| `categories` | string[] | No | Array of category tags |
| `fetch_interval` | number | Yes | Fetch interval in minutes (5-1440) |
| `is_active` | boolean | Yes | Whether the feed is currently active |
| `status` | string (FeedStatus) | Yes | Current status of the feed |
| `created_at` | string (ISO 8601) | Yes | Timestamp of feed creation |
| `updated_at` | string (ISO 8601) | Yes | Timestamp of last update |
| `last_fetched_at` | string (ISO 8601) | No | Timestamp of last successful fetch |
| `health_score` | number (0-100) | Yes | Health score based on fetch success rate |
| `consecutive_failures` | number | Yes | Number of consecutive failed fetch attempts |
| `total_items` | number | Yes | Total number of items in this feed |
| `items_last_24h` | number | Yes | Number of items added in the last 24 hours |
| `scrape_full_content` | boolean | No | Whether to scrape full article content |
| `scrape_method` | string | No | Scraping method: auto, httpx, or playwright |

### Feed Source Assessment

Assessment data from Perplexity analysis about the reliability and credibility of the news source.

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `assessment_status` | string | No | Assessment status of the feed source |
| `assessment_date` | string (ISO 8601) | No | Date of last assessment |
| `credibility_tier` | string | No | Credibility tier: tier_1, tier_2, tier_3 |
| `reputation_score` | number (0-100) | No | Reputation score |
| `founded_year` | number | No | Year the source was founded |
| `organization_type` | string | No | Type of organization |
| `political_bias` | string | No | Political bias: left, center_left, center, center_right, right, unknown |
| `editorial_standards` | object | No | fact_checking_level, corrections_policy, source_attribution |
| `trust_ratings` | object | No | media_bias_fact_check, allsides_rating, newsguard_score |
| `recommendation` | object | No | skip_waiting_period, initial_quality_boost, bot_detection_threshold |
| `assessment_summary` | string | No | Summary of the assessment |

### Auto-Analysis Configuration

These flags control which automatic analyses are performed on articles from this feed.

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `enable_categorization` | boolean | No | Enable automatic article categorization (6 categories) |
| `enable_finance_sentiment` | boolean | No | Enable finance-specific sentiment analysis |
| `enable_geopolitical_sentiment` | boolean | No | Enable geopolitical sentiment analysis |
| `enable_osint_analysis` | boolean | No | Enable OSINT Event Analysis |
| `enable_summary` | boolean | No | Enable automatic article summarization and key facts extraction |
| `enable_entity_extraction` | boolean | No | Enable entity extraction (persons, organizations, locations) |
| `enable_topic_classification` | boolean | No | Enable topic classification and keyword extraction |

---

## Feed Health Object

Health metrics and statistics about feed fetch performance.

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `feed_id` | string (UUID) | Yes | Reference to the feed |
| `health_score` | number (0-100) | Yes | Overall health score |
| `success_rate` | number (0-100) | Yes | Success rate percentage |
| `consecutive_failures` | number | Yes | Number of consecutive failures |
| `avg_fetch_duration` | number | Yes | Average fetch duration in milliseconds |
| `last_success_at` | string (ISO 8601) | No | Timestamp of last successful fetch |
| `last_failure_at` | string (ISO 8601) | No | Timestamp of last failed fetch |
| `total_fetches` | number | Yes | Total number of fetch attempts |
| `successful_fetches` | number | Yes | Number of successful fetches |
| `failed_fetches` | number | Yes | Number of failed fetches |
| `history` | HealthHistoryPoint[] | Yes | Array of historical health data points |

### Health History Point Object

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | Timestamp of the fetch attempt |
| `health_score` | number (0-100) | Yes | Health score at this point in time |
| `success` | boolean | Yes | Whether the fetch was successful |
| `duration` | number | No | Fetch duration in milliseconds |
| `error` | string | No | Error message if fetch failed |

---

## API Endpoints

### Feed Management
- **GET** `/api/v1/feeds` - Returns array of Feed objects
- **GET** `/api/v1/feeds/{id}` - Returns single Feed object
- **POST** `/api/v1/feeds` - Create new feed
- **PUT** `/api/v1/feeds/{id}` - Update feed
- **DELETE** `/api/v1/feeds/{id}` - Delete feed

### Feed Health
- **GET** `/api/v1/feeds/{id}/health` - Returns FeedHealth object

### Feed Items
- **GET** `/api/v1/feeds/{id}/items` - Returns array of FeedItem objects
- **GET** `/api/v1/items/{id}` - Returns single FeedItem with all analysis data

---

## Type Definitions

See `/src/features/feeds/types/index.ts` for TypeScript type definitions.

## Notes

1. **Feed Source Assessment**: Populated via Perplexity API analysis of the news source's reputation and credibility

2. **Auto-Analysis Configuration**: Controls which AI analyses are automatically run on new articles from this feed

3. **Health Score**: Calculated based on fetch success rate, response times, and uptime

4. **Analysis Results**: Individual article analyses (sentiment, categories, etc.) are stored on Feed Items, not on the Feed itself

5. **Scraping**: Full content scraping can be enabled per-feed with `scrape_full_content: true`

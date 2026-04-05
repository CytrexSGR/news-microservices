# Analysis Fields Reference

Complete field reference for all Content Analysis Service functions.

Last updated: 2025-10-25

---

## Table of Contents

1. [SENTIMENT](#1-sentiment)
2. [ENTITIES](#2-entities)
3. [TOPICS](#3-topics)
4. [SUMMARY](#4-summary)
5. [CATEGORY](#5-category)
6. [FINANCE_SENTIMENT](#6-finance_sentiment)
7. [GEOPOLITICAL_SENTIMENT](#7-geopolitical_sentiment)
8. [EVENT_ANALYSIS](#8-event_analysis)

---

## 1. SENTIMENT

**Endpoint:** `POST /api/v1/analysis/sentiment`
**Database Table:** `sentiment_analysis`

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ | - | Text to analyze (1-50,000 chars) |
| `article_id` | UUID | ❌ | null | Article ID from Feed Service |
| `detect_bias` | boolean | ❌ | true | Detect political/social bias |
| `detect_emotion` | boolean | ❌ | true | Detect emotion scores |
| `use_cache` | boolean | ❌ | true | Use cached results if available |

### Response Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | UUID | - | Unique analysis ID |
| `overall_sentiment` | enum | - | Overall sentiment: `positive`, `negative`, `neutral`, `mixed`, `not_applicable` |
| `confidence` | float | 0.0-1.0 | Confidence in sentiment classification |
| `positive_score` | float | 0.0-1.0 | Positive sentiment strength |
| `negative_score` | float | 0.0-1.0 | Negative sentiment strength |
| `neutral_score` | float | 0.0-1.0 | Neutral sentiment strength |
| `bias_detected` | boolean | - | Whether political/social bias was detected |
| `bias_direction` | enum | - | Bias direction: `left`, `right`, `center`, `unknown` (null if no bias) |
| `bias_confidence` | float | 0.0-1.0 | Confidence in bias detection (null if no bias) |
| `subjectivity_score` | float | 0.0-1.0 | Subjectivity (0.0 = objective, 1.0 = subjective) |
| `emotion_scores` | object | - | Emotion breakdown: `{"joy": 0.8, "fear": 0.2, ...}` |
| `reasoning` | string | - | Explanation of sentiment classification |
| `key_phrases` | array | - | Text phrases that influenced sentiment |
| `cached` | boolean | - | Whether result came from cache |
| `processing_time_ms` | integer | - | Processing duration in milliseconds |

---

## 2. ENTITIES

**Endpoint:** `POST /api/v1/analysis/entities`
**Database Tables:** `extracted_entities`, `entity_relationships`

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ | - | Text to analyze (1-50,000 chars) |
| `article_id` | UUID | ❌ | null | Article ID from Feed Service |
| `entity_types` | array | ❌ | all | Filter by entity types (see Entity Types below) |
| `extract_relationships` | boolean | ❌ | true | Extract relationships between entities |
| `use_cache` | boolean | ❌ | true | Use cached results if available |

### Entity Response Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | UUID | - | Unique entity ID |
| `text` | string | - | Entity text as it appears in content |
| `type` | enum | - | Entity type (see Entity Types below) |
| `confidence` | float | 0.0-1.0 | Confidence in entity classification |
| `mention_count` | integer | ≥1 | Number of times entity appears |
| `canonical_id` | string | - | Wikidata ID (e.g., "Q317521" for Elon Musk) |

### Relationship Response Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `entity1` | string | - | First entity text |
| `entity2` | string | - | Second entity text |
| `type` | enum | - | Relationship type (see Relationship Types below) |
| `confidence` | float | 0.0-1.0 | Confidence in relationship |
| `sentiment_score` | float | -1.0 to +1.0 | Sentiment of relationship (-1 = very negative, +1 = very positive) |
| `sentiment_category` | enum | - | Sentiment: `positive`, `negative`, `neutral` |
| `sentiment_confidence` | float | 0.0-1.0 | Confidence in sentiment analysis |

### Entity Types

```
PERSON               - People (e.g., "Elon Musk")
ORGANIZATION         - Companies, institutions (e.g., "Tesla", "UN")
LOCATION             - Places, countries (e.g., "New York", "Germany")
DATE                 - Dates, time periods (e.g., "Q4 2024")
EVENT                - Named events (e.g., "World War II")
PRODUCT              - Products, goods (e.g., "iPhone 15")
MONEY                - Monetary amounts (e.g., "$10 million")
PERCENT              - Percentages (e.g., "25%")
QUANTITY             - Numerical quantities (e.g., "30 workers")
MOVIE                - Film titles
LEGISLATION          - Laws, regulations
NATIONALITY          - Nationalities, ethnic groups
PLATFORM             - Software platforms, services
LEGAL_CASE           - Court cases, legal proceedings
NOT_APPLICABLE       - No entities found
```

### Relationship Types

```
works_for                     - Employment relationship
located_in                    - Geographic location
owns                          - Ownership
owned_by                      - Inverse ownership
related_to                    - General relationship
member_of                     - Membership
partner_of                    - Partnership
reports_to                    - Reporting hierarchy
produces                      - Manufacturing/creation
founded_in                    - Geographic founding
founded_by                    - Founding relationship
advised                       - Advisory relationship
worked_with                   - Professional collaboration
created                       - Creation/authorship
collaborated_with             - Collaboration
invested_in                   - Investment
brand_ambassador_for          - Brand representation
spokesperson_for              - Official representation
ran                           - Campaign/initiative leadership
oversaw                       - Oversight/management
initially_agreed_to_acquire   - Acquisition intent
acquired                      - Completed acquisition
supports                      - Political/ideological support
opposes                       - Political/ideological opposition
studied_at                    - Educational relationship
competes_with                 - Competition
regulates                     - Regulatory authority
ruled_against                 - Legal/judicial decisions
abused_monopoly_in            - Antitrust violations
announced                     - Official announcements
not_applicable                - No relationships found
```

---

## 3. TOPICS

**Endpoint:** `POST /api/v1/analysis/topics`
**Database Table:** `topic_classifications`

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ | - | Text to analyze (1-50,000 chars) |
| `article_id` | UUID | ❌ | null | Article ID from Feed Service |
| `max_topics` | integer | ❌ | 5 | Maximum topics to extract (1-10) |
| `extract_keywords` | boolean | ❌ | true | Extract keywords for each topic |
| `use_cache` | boolean | ❌ | true | Use cached results if available |

### Response Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | UUID | - | Unique topic ID |
| `topic` | string | - | Topic name |
| `relevance_score` | float | 0.0-1.0 | Topic relevance to content |
| `confidence` | float | 0.0-1.0 | Confidence in topic classification |
| `is_primary` | boolean | - | Whether this is the primary topic |
| `parent_topic` | string | - | Parent topic in hierarchy |
| `topic_hierarchy` | array | - | Full hierarchy: `["Technology", "AI", "Machine Learning"]` |
| `keywords` | array | - | Relevant keywords for this topic |
| `keyword_scores` | object | - | Keyword relevance scores: `{"AI": 0.9, "learning": 0.8}` |
| `reasoning` | string | - | Explanation of topic classification |

### Aggregated Response

| Field | Type | Description |
|-------|------|-------------|
| `topics` | array | List of topics (see Response Fields above) |
| `primary_topic` | string | Name of primary topic |
| `keywords` | array | All extracted keywords across topics |
| `cached` | boolean | Whether result came from cache |
| `processing_time_ms` | integer | Processing duration |

---

## 4. SUMMARY

**Endpoint:** `POST /api/v1/analysis/summary`
**Database Table:** `summaries`

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ | - | Text to summarize (1-50,000 chars) |
| `article_id` | UUID | ❌ | null | Article ID from Feed Service |
| `summary_types` | array | ❌ | `[short, medium]` | Summary lengths to generate |
| `extract_key_points` | boolean | ❌ | true | Extract bullet-point key points |
| `use_cache` | boolean | ❌ | true | Use cached results if available |

### Summary Types

```
short   - 1 sentence summary
medium  - 3 sentences summary
long    - 1 paragraph summary
```

### Response Fields (per summary)

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | UUID | - | Unique summary ID |
| `summary_type` | enum | - | Summary type: `short`, `medium`, `long` |
| `summary_text` | string | - | The summary text |
| `compression_ratio` | float | ≥1.0 | Original length / summary length |
| `original_length` | integer | - | Character count of original text |
| `summary_length` | integer | - | Character count of summary |
| `coherence_score` | float | 0.0-1.0 | Summary coherence quality |
| `coverage_score` | float | 0.0-1.0 | How well key points are covered |
| `bullet_points` | array | - | Key points as bullet list |
| `key_sentences` | array | - | Original sentences used in summary |

### Aggregated Response

| Field | Type | Description |
|-------|------|-------------|
| `summaries` | array | List of summaries (see Response Fields above) |
| `key_points` | array | Extracted key points |
| `compression_ratio` | float | Average compression ratio |
| `cached` | boolean | Whether result came from cache |
| `processing_time_ms` | integer | Processing duration |

---

## 5. CATEGORY

**Endpoint:** `POST /api/v1/analysis/category`
**Database Table:** `category_classification`

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ | - | Text to categorize (1-50,000 chars) |
| `article_id` | UUID | ❌ | null | Article ID from Feed Service |
| `use_cache` | boolean | ❌ | true | Use cached results if available |

### Response Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | UUID | - | Unique classification ID |
| `category` | enum | - | Primary category (see Categories below) |
| `confidence` | float | 0.0-1.0 | Confidence in primary category |
| `alternative_categories` | array | - | Second/third best matches: `[{"category": "...", "confidence": 0.x}]` |
| `reasoning` | string | - | Explanation of category choice |
| `key_indicators` | array | - | Keywords/phrases that influenced decision |
| `cached` | boolean | - | Whether result came from cache |
| `processing_time_ms` | integer | - | Processing duration |

### Categories

```
Geopolitics Security            - Geopolitical events, security, conflicts
Politics Society                - Politics, social issues, governance
Economy Markets                 - Economics, markets, business
Climate Environment Health      - Climate, environment, health
Panorama                        - Culture, lifestyle, entertainment
Technology Science              - Technology, science, innovation
```

---

## 6. FINANCE_SENTIMENT

**Endpoint:** `POST /api/v1/analysis/finance-sentiment`
**Database Table:** `finance_sentiment`

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ | - | Text to analyze (1-50,000 chars) |
| `article_id` | UUID | ❌ | null | Article ID from Feed Service |
| `use_cache` | boolean | ❌ | true | Use cached results if available |

### Response Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | UUID | - | Unique analysis ID |
| `market_sentiment` | enum | - | Market direction: `bearish`, `neutral`, `bullish`, `not_applicable` |
| `market_confidence` | float | 0.0-1.0 | Confidence in market direction |
| `time_horizon` | enum | - | Time frame: `short` (days-weeks), `medium` (weeks-months), `long` (months-years), `not_applicable` |
| `uncertainty` | float | 0.0-1.0 | Market uncertainty level |
| `volatility` | float | 0.0-1.0 | Expected market volatility |
| `economic_impact` | float | 0.0-1.0 | Economic impact score |
| `reasoning` | string | - | Explanation of analysis |
| `key_indicators` | array | - | Economic indicators mentioned |
| `affected_sectors` | array | - | Market sectors affected: `["technology", "finance", ...]` |
| `affected_assets` | array | - | Asset classes affected: `["stocks", "bonds", "crypto", ...]` |
| `cached` | boolean | - | Whether result came from cache |
| `processing_time_ms` | integer | - | Processing duration |

---

## 7. GEOPOLITICAL_SENTIMENT

**Endpoint:** `POST /api/v1/analysis/geopolitical-sentiment`
**Database Table:** `geopolitical_sentiment`

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ | - | Text to analyze (1-50,000 chars) |
| `article_id` | UUID | ❌ | null | Article ID from Feed Service |
| `use_cache` | boolean | ❌ | true | Use cached results if available |

### Response Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `id` | UUID | - | Unique analysis ID |
| `stability_score` | float | -1.0 to +1.0 | Stability assessment (-1 = highly unstable, +1 = very stable) |
| `security_relevance` | float | 0.0-1.0 | Security relevance score |
| `escalation_potential` | float | 0.0-1.0 | Potential for escalation |
| `conflict_type` | enum | - | Conflict classification: `diplomatic`, `economic`, `hybrid`, `interstate_war`, `nuclear_threat`, `not_applicable`, `unknown` |
| `time_horizon` | enum | - | Impact timeframe: `short`, `medium`, `long`, `not_applicable` |
| `confidence` | float | 0.0-1.0 | Confidence in assessment |
| `regions_affected` | array | - | Affected regions/countries |
| `impact_beneficiaries` | array | - | Countries/entities that benefit |
| `impact_affected` | array | - | Countries/entities negatively affected |
| `alliance_activation` | array | - | Alliances that may activate (e.g., NATO) |
| `diplomatic_impact_global` | float | -1.0 to +1.0 | Global diplomatic impact |
| `diplomatic_impact_western` | float | -1.0 to +1.0 | Western perspective impact |
| `diplomatic_impact_regional` | float | -1.0 to +1.0 | Regional impact |
| `reasoning` | string | - | Explanation of analysis |
| `key_factors` | array | - | Key geopolitical factors identified |
| `cached` | boolean | - | Whether result came from cache |
| `processing_time_ms` | integer | - | Processing duration |

---

## 8. EVENT_ANALYSIS

**Endpoint:** Triggered automatically for articles ≥500 words
**Database Table:** `event_analyses`

### Response Fields

#### Basic Information

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique event analysis ID |
| `article_id` | UUID | Article ID from Feed Service |
| `headline` | string | Event headline |
| `source` | string | News source name |
| `publisher_url` | string | Publisher website URL |

#### Event Details

| Field | Type | Description |
|-------|------|-------------|
| `primary_event` | string | Main event description |
| `location` | string | Event location |
| `event_date` | datetime | Date event occurred |

#### Actors (JSONB Object)

```json
{
  "alleged_attacker": "Russian forces",
  "victim": "Ukrainian civilian infrastructure",
  "reporting_party": "Kyiv regional administration"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `actors` | object | Actor roles and identities |

#### Means/Methods (Array)

```json
["drones", "artillery", "missiles"]
```

| Field | Type | Description |
|-------|------|-------------|
| `means` | array | Methods/tools used in event |

#### Impact (JSONB Object)

```json
{
  "trucks_destroyed": 5,
  "fatalities": 2,
  "injured": 7,
  "affected_civilians": 1000,
  "infrastructure_damage": "severe"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `impact` | object | Quantified event impacts |

#### Claims (JSONB Array)

```json
[
  {
    "statement": "15 trucks were destroyed",
    "confidence": "high",
    "evidence_ref": "UN official statement",
    "attribution": "UN spokesperson"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `claims` | array | Verifiable claims from article |

#### Status/Comments (JSONB Object)

```json
{
  "un_comment": "investigating reports",
  "russian_comment": "denies attack occurred",
  "ukrainian_comment": "confirms attack, provides casualty count"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | object | Official statements and responses |

#### Risk Assessment

| Field | Type | Description |
|-------|------|-------------|
| `risk_tags` | array | Risk classifications (see Risk Tags below) |
| `confidence_overall` | enum | Overall confidence: `low`, `medium`, `high` |
| `confidence_dimensions` | object | Detailed confidence breakdown |

##### Risk Tags

**Critical Tags** (always require analyst review):
- `ihl_sensitive` - International Humanitarian Law sensitive
- `high_casualty` - High casualty count
- `war_crime_allegation` - Alleged war crime
- `chemical_use` - Chemical weapons involved
- `nuclear_facility` - Nuclear facility involved

**High-Priority Tags** (require review if confidence is low):
- `needs_corroboration` - Requires additional verification
- `mass_displacement` - Large-scale displacement
- `infrastructure_collapse` - Critical infrastructure failure

**Thematic Tags** (informational only):
- `drone_strike` - Drone attack
- `missile_attack` - Missile attack
- Various other event-specific tags

**Compliance Tags** (procedural):
- `un_statement_required` - UN statement needed
- Various other compliance requirements

#### Confidence Dimensions (JSONB Object)

```json
{
  "source_credibility": "high",
  "specificity": "medium",
  "counter_statements": "medium",
  "corroboration": "high",
  "weighted_score": 0.825
}
```

#### Publisher Context (JSONB Object)

```json
{
  "publisher_bias": "center",
  "source_type": "independent_media",
  "reliability_score": 0.85
}
```

#### Evidence (JSONB Array)

```json
[
  {
    "type": "quote",
    "text": "We confirm 15 casualties",
    "source": "Regional governor",
    "position": 1234
  },
  {
    "type": "photo",
    "url": "https://example.com/image.jpg",
    "description": "Damaged infrastructure"
  }
]
```

#### Summary and Metadata

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string | Event summary |
| `claim_count` | integer | Number of claims |
| `evidence_count` | integer | Number of evidence items |
| `needs_analyst_review` | boolean | Whether event requires human review |
| `created_at` | datetime | Analysis timestamp |
| `updated_at` | datetime | Last update timestamp |

---

## Common Fields (All Analysis Types)

These fields appear in the parent `analysis_results` table for all analysis types:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique analysis ID |
| `article_id` | UUID | Article ID from Feed Service |
| `analysis_type` | enum | Type of analysis performed |
| `model_used` | string | LLM model name |
| `model_provider` | enum | Provider: `OPENAI`, `ANTHROPIC`, `OLLAMA`, `HUGGINGFACE` |
| `status` | enum | Status: `pending`, `in_progress`, `completed`, `failed`, `cancelled` |
| `total_cost` | decimal | Cost in USD |
| `total_tokens` | integer | Total tokens used |
| `input_tokens` | integer | Input tokens |
| `output_tokens` | integer | Output tokens |
| `processing_time_ms` | integer | Processing duration |
| `cached` | boolean | Whether from cache |
| `cache_key` | string | SHA256 cache key |
| `error_message` | string | Error message if failed |
| `retry_count` | integer | Number of retries |
| `started_at` | datetime | Analysis start time |
| `completed_at` | datetime | Analysis completion time |
| `created_at` | datetime | Record creation time |
| `updated_at` | datetime | Last update time |

### Uncertainty Quantification (UQ) Fields

Available for all analysis types:

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `uq_confidence_score` | float | 0.0-1.0 | UQ confidence score (0.0 = low, 1.0 = high) |
| `uncertainty_factors` | array | - | List of identified uncertainty factors |
| `requires_verification` | boolean | - | Flag to trigger DIA verification workflow |
| `uq_metadata` | object | - | Detailed UQ metrics (mean_logprob, entropy, etc.) |

---

## Notes

1. **Enums**: All enum values are case-sensitive and must match exactly
2. **UUIDs**: Must be valid UUID v4 format
3. **Ranges**: Float fields have specified ranges (e.g., 0.0-1.0, -1.0 to +1.0)
4. **Caching**: Set `use_cache: false` to force fresh analysis
5. **Not Applicable**: Many enums have `not_applicable` value for irrelevant content
6. **JSONB Fields**: Stored as JSON objects in PostgreSQL, flexible schema
7. **Arrays**: ARRAY fields store PostgreSQL arrays (for simple lists)

---

**See Also:**
- [Content Analysis API Documentation](content-analysis-api.md)
- [Analysis Service Architecture](../services/content-analysis-service.md)
- [Database Schema](../database/schema.md)

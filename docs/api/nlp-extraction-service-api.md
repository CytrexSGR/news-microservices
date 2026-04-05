# NLP Extraction Service API Documentation

> 🗄️ **ARCHIVED (2025-12-27)** - This service has been decommissioned.
> Archive location: `services/_archived/nlp-extraction-service-20251227/`
> Entity extraction is now handled by content-analysis-v3-consumer.

## Overview

**Version:** 1.0.0
**Base URL:** `http://localhost:8115/api/v1` (no longer active)
**Status:** ARCHIVED

The NLP Extraction Service provided high-speed natural language processing for news articles using spaCy. It was **143x faster** and **100% cheaper** than traditional LLM-based analysis.

## Quick Start

```bash
# Get single article extraction
curl http://localhost:8115/api/v1/extractions/0b121edf-2691-4745-b282-f3b73b2cf494

# Get batch extractions
curl -X POST http://localhost:8115/api/v1/extractions/batch \
  -H "Content-Type: application/json" \
  -d '{"article_ids": ["uuid1", "uuid2", "uuid3"]}'
```

## Features

### Phase 2B Features (In Production)

1. **Entity Extraction** - Named entities with types (PERSON, ORG, GPE, etc.)
2. **Entity-Level Sentiment** (Phase 2B.4) - Sentiment per entity with controversy detection
3. **Entity Centrality** (Phase 2B.5) - Importance scoring (0.0-1.0)
4. **Quote-Sentiment Attribution** (Phase 2B.6) - Quotes with speakers and sentiment

### Additional Features

- Overall article sentiment
- Keyword extraction
- Dependency parsing
- Sentence segmentation

## Endpoints

### GET /extractions/{article_id}

Get NLP extraction for a single article.

**Parameters:**
- `article_id` (path, required): UUID of the article

**Response (200):**
```json
{
  "article_id": "0b121edf-2691-4745-b282-f3b73b2cf494",
  "language": "en",
  "extractor_version": "base_v1",
  "model_version": "en_core_web_lg",
  "created_at": "2025-11-07T14:30:00Z",
  "processing_time_ms": 56,
  "content_length": 1250,
  "entity_count": 35,
  "entity_density": 0.028,
  "entities": [...],
  "entity_sentiments": [...],
  "entity_centrality": [...],
  "quote_sentiments": [...],
  "sentiment_overall": {...},
  "keywords": [...]
}
```

**Errors:**
- **400**: Invalid UUID format
- **404**: Article not found or not yet processed
- **500**: Internal server error

**Performance Target:** < 50ms

---

### POST /extractions/batch

Get NLP extractions for multiple articles (batch).

**Request Body:**
```json
{
  "article_ids": [
    "0b121edf-2691-4745-b282-f3b73b2cf494",
    "b8f45c20-3ba0-4cd9-8d7b-be2471fb3e5c",
    "..."
  ]
}
```

**Limits:**
- Minimum: 1 article
- Maximum: 100 articles per request

**Response (200):**
```json
{
  "total_requested": 3,
  "total_found": 3,
  "total_not_found": 0,
  "not_found_ids": [],
  "extractions": [...]
}
```

**Behavior:**
- Missing articles are skipped (no error)
- Returns only found articles
- Order is not guaranteed
- Uses single optimized database query

**Errors:**
- **400**: Invalid request (empty array, > 100 articles, bad UUID)
- **500**: Internal server error

**Performance Target:** < 200ms for 100 articles

---

## Data Models

### ExtractionResponse

| Field | Type | Description |
|-------|------|-------------|
| `article_id` | UUID | Article identifier |
| `language` | string | Language code ("en", "de") |
| `extractor_version` | string | NLP extractor version |
| `model_version` | string | spaCy model version |
| `created_at` | datetime | Extraction timestamp |
| `processing_time_ms` | integer | Processing time in milliseconds |
| `content_length` | integer | Content length (characters) |
| `entity_count` | integer | Total entities extracted |
| `entity_density` | float | Entities per 1000 chars |
| `entities` | Entity[] | Named entities |
| `entity_sentiments` | EntitySentiment[] | Per-entity sentiment (Phase 2B.4) |
| `entity_centrality` | EntityCentrality[] | Entity importance (Phase 2B.5) |
| `quote_sentiments` | QuoteSentiment[] | Quotes with speakers (Phase 2B.6) |
| `sentiment_overall` | Sentiment | Overall article sentiment |
| `keywords` | Keyword[] | Extracted keywords |

### Entity

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Entity text |
| `label` | string | Entity type (PERSON, ORG, GPE, etc.) |
| `start_char` | integer | Character offset start |
| `end_char` | integer | Character offset end |

**Entity Types:**
- `PERSON` - People (e.g., "Elon Musk")
- `ORG` - Organizations (e.g., "Tesla", "NASA")
- `GPE` - Geopolitical entities (e.g., "United States", "Berlin")
- `LOC` - Locations (e.g., "Mount Everest")
- `DATE`, `TIME` - Temporal expressions
- `MONEY`, `PERCENT` - Numerical values
- `PRODUCT` - Products and services
- `EVENT` - Named events
- Plus 8 more types (see OpenAPI spec)

### EntitySentiment (Phase 2B.4)

| Field | Type | Description |
|-------|------|-------------|
| `entity` | string | Entity text |
| `entity_type` | string | Entity type |
| `sentiment` | Sentiment | Sentiment object |
| `mention_count` | integer | Number of mentions |
| `sentence_indices` | integer[] | Sentences containing entity |
| `sentiment_variance` | float | Controversy indicator (0.0-1.0) |

**Use Cases:**
- "How is sentiment towards Tesla in this article?"
- "Which entities have controversial sentiment?" (high variance)
- "Show only articles where X is mentioned positively"

**Example:**
```json
{
  "entity": "Elon Musk",
  "entity_type": "PERSON",
  "sentiment": {
    "label": "positive",
    "score": 0.78,
    "confidence": 0.85
  },
  "mention_count": 5,
  "sentence_indices": [0, 3, 7, 12],
  "sentiment_variance": 0.12
}
```

### EntityCentrality (Phase 2B.5)

| Field | Type | Description |
|-------|------|-------------|
| `entity` | string | Entity text |
| `entity_type` | string | Entity type |
| `centrality` | Centrality | Centrality metrics |

**Centrality Object:**
| Field | Type | Description |
|-------|------|-------------|
| `score` | float | Centrality score (0.0-1.0) |
| `rank` | integer | Rank among all entities |
| `in_title` | boolean | Appears in title? |
| `in_first_sentence` | boolean | Appears in first sentence? |
| `mention_count` | integer | Number of mentions |
| `agent_count` | integer | Times entity is subject/agent |
| `position_first_mention` | float | Relative position (0.0-1.0) |

**Scoring Algorithm:**
- Title presence: +0.30 (30% weight)
- First sentence: +0.20 (20% weight)
- Mention count: up to +0.25 (diminishing returns)
- Agent count: up to +0.15 (diminishing returns)
- Early position: up to +0.10

**Use Cases:**
- "Show only articles where X is central (score > 0.7)"
- "Rank articles by how prominent Tesla is"
- "In 80% of articles, Musk is highly central"

**Example:**
```json
{
  "entity": "Elon Musk",
  "entity_type": "PERSON",
  "centrality": {
    "score": 0.87,
    "rank": 1,
    "in_title": true,
    "in_first_sentence": true,
    "mention_count": 5,
    "agent_count": 3,
    "position_first_mention": 0.05
  }
}
```

### QuoteSentiment (Phase 2B.6)

| Field | Type | Description |
|-------|------|-------------|
| `quote` | string | Extracted quote text |
| `speaker` | string? | Attributed speaker (null if unknown) |
| `speaker_type` | string? | Speaker entity type |
| `sentiment` | Sentiment? | Quote sentiment (null if failed) |
| `context_before` | string | Context before quote (max 80 chars) |
| `context_after` | string | Context after quote (max 80 chars) |
| `position_in_text` | float | Relative position (0.0-1.0) |

**Use Cases:**
- "What does Elon Musk say about Tesla?"
- "How positive/negative are quotes from Biden?"
- "Which persons are most frequently quoted?"
- Separate article tone from speaker tone

**Example:**
```json
{
  "quote": "The market is very bullish right now",
  "speaker": "Elon Musk",
  "speaker_type": "PERSON",
  "sentiment": {
    "label": "positive",
    "score": 0.82,
    "confidence": 0.90
  },
  "context_before": "Tesla CEO said: ",
  "context_after": " during the earnings call.",
  "position_in_text": 0.35
}
```

### Sentiment

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | "positive", "neutral", "negative" |
| `score` | float | Score (-1.0 to 1.0) |
| `confidence` | float | Confidence (0.0-1.0) |

**Sentiment Analyzers:**
- **English**: VADER (rule-based, fast, good for social media)
- **German**: TextBlob German (dictionary-based)

### Keyword

| Field | Type | Description |
|-------|------|-------------|
| `keyword` | string | Keyword text |
| `score` | float | Relevance score (0.0-1.0) |

---

## Error Responses

All errors follow this structure:

```json
{
  "error": "NotFound",
  "message": "NLP extraction not found for article",
  "details": {
    "article_id": "0b121edf-2691-4745-b282-f3b73b2cf494"
  },
  "timestamp": "2025-11-07T14:30:00Z",
  "path": "/api/v1/extractions/0b121edf-2691-4745-b282-f3b73b2cf494"
}
```

**Error Types:**
- `ValidationError` (400): Invalid input
- `NotFound` (404): Resource not found
- `InternalError` (500): Server error

---

## Performance

### Targets
- Single article: **< 50ms**
- Batch (100 articles): **< 200ms**

### Optimization
- Single database query for batch requests
- Database indexes on `article_id`, `created_at`, and all JSONB columns
- Connection pooling
- No network calls (pure spaCy)

### Monitoring
- Response time metrics in Grafana
- Alert if > 200ms for batch
- Track cache hit rate

---

## Integration Examples

### JavaScript/TypeScript (React Query)

```typescript
import { useQuery } from '@tanstack/react-query';

// Single article
export const useNLPExtraction = (articleId: string) => {
  return useQuery({
    queryKey: ['nlp-extraction', articleId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/extractions/${articleId}`);
      if (!res.ok) throw new Error('Failed to fetch extraction');
      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5 min cache
  });
};

// Batch
export const useNLPExtractionsBatch = (articleIds: string[]) => {
  return useQuery({
    queryKey: ['nlp-extractions-batch', articleIds],
    queryFn: async () => {
      const res = await fetch('/api/v1/extractions/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_ids: articleIds }),
      });
      if (!res.ok) throw new Error('Failed to fetch batch');
      return res.json();
    },
    enabled: articleIds.length > 0,
  });
};
```

### Python (requests)

```python
import requests

# Single article
def get_extraction(article_id: str):
    res = requests.get(f"http://localhost:8115/api/v1/extractions/{article_id}")
    res.raise_for_status()
    return res.json()

# Batch
def get_extractions_batch(article_ids: list[str]):
    res = requests.post(
        "http://localhost:8115/api/v1/extractions/batch",
        json={"article_ids": article_ids}
    )
    res.raise_for_status()
    return res.json()
```

### cURL

```bash
# Single article
curl http://localhost:8115/api/v1/extractions/0b121edf-2691-4745-b282-f3b73b2cf494

# Batch
curl -X POST http://localhost:8115/api/v1/extractions/batch \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [
      "0b121edf-2691-4745-b282-f3b73b2cf494",
      "b8f45c20-3ba0-4cd9-8d7b-be2471fb3e5c"
    ]
  }'
```

---

## Migration from Content-Analysis

### Format Differences

| Feature | Content-Analysis Format | NLP Extraction Format |
|---------|------------------------|----------------------|
| Entities | `{"name": "X", "type": "Y"}` | `{"text": "X", "label": "Y"}` |
| Sentiment | `{"sentiment": "positive"}` | `{"label": "positive", "score": 0.8}` |
| Quotes | Not available | New feature! |

### Adapter Pattern (Frontend)

```typescript
// Normalize NLP format to Content-Analysis format
function normalizeEntities(nlpEntities: NLPEntity[]): ContentAnalysisEntity[] {
  return nlpEntities.map(e => ({
    name: e.text,
    type: e.label,
    start: e.start_char,
    end: e.end_char,
  }));
}

// Use in component
const entities = extraction.entities
  ? normalizeEntities(extraction.entities)
  : contentAnalysis.entities; // Fallback
```

---

## FAQ

**Q: What happens if an article hasn't been processed yet?**
A: You'll get a 404 error. Articles are processed by workers listening to RabbitMQ queues. Processing typically takes < 1 second after article creation.

**Q: Can I request more than 100 articles in batch?**
A: No, the limit is 100 to maintain < 200ms response time. Split large requests into multiple batches.

**Q: Are results cached?**
A: Database results are not cached in the API (PostgreSQL is fast enough). Frontend should use React Query's built-in caching (5 min staleTime recommended).

**Q: How accurate is sentiment analysis?**
A: VADER (English) is 80-85% accurate on social media text. For news articles, expect similar accuracy. German TextBlob is 70-75% accurate.

**Q: What's the difference between entity sentiment and overall sentiment?**
A: Overall sentiment analyzes the entire article. Entity sentiment analyzes only sentences mentioning that specific entity. This separates article tone from entity-specific tone.

**Q: How is entity centrality calculated?**
A: Weighted scoring: title (30%), first sentence (20%), mention count (25%), agent count (15%), early position (10%). See data model docs for details.

**Q: Why are some quotes missing speakers?**
A: Speaker attribution uses dependency parsing. If no reporting verb is found (said, stated, etc.), the speaker is null. This is expected for about 20-30% of quotes.

---

## See Also

- [OpenAPI 3.1 Specification](nlp-extraction-api.yaml)
- [Service Architecture](/home/cytrex/news-microservices/docs/services/nlp-extraction-service.md)
- [Phase 2B Test Report](/home/cytrex/userdocs/nlp-migration/reports/phase2b_test_report.md)
- [NLP Migration Plan](/home/cytrex/userdocs/nlp-migration/IMPLEMENTATION_PLAN.md)

---

**Last Updated:** 2025-11-07
**API Version:** 1.0.0
**Status:** Phase 1 Implementation

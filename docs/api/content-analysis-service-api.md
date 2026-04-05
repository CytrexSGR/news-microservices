# Content Analysis Service API

**Base URL:** `http://localhost:8102`

**Authentication:** Required - Bearer token (JWT) via `/api/v1/auth/login`

**API Prefix:** `/api/v1`

## Overview

AI-powered content analysis API providing multi-LLM analysis capabilities (OpenAI, Anthropic, Ollama, Gemini) for sentiment analysis, entity extraction, topic classification, summarization, and fact-checking.

**Key Features:**
- Multi-provider LLM support with automatic fallback
- Comprehensive analysis (sentiment, entities, topics, summaries, facts)
- **Category classification** (6 fixed categories: Geopolitics Security, Politics Society, Economy Markets, Climate Environment Health, Panorama, Technology Science)
- Specialized analysis (finance, geopolitical sentiment)
- Event-driven processing via RabbitMQ
- Redis caching for cost optimization
- OSINT intelligence event extraction

---

## Core Analysis Operations

### POST /api/v1/analyze

Perform comprehensive content analysis.

**Authentication:** Required

**Request Body:**
```json
{
  "content": "Article text to analyze...",
  "article_id": "uuid (optional)",
  "analysis_type": "comprehensive",
  "model_provider": "openai",
  "model_name": "gpt-4o-mini",
  "use_cache": true,
  "metadata": {
    "source": "feed",
    "language": "en"
  }
}
```

**Parameters:**
- `content` (string, required): Text to analyze (max 50,000 chars)
- `article_id` (UUID, optional): Associated article ID
- `analysis_type` (enum): `comprehensive`, `sentiment_only`, `entities_only`, `topics_only`
- `model_provider` (enum): `openai`, `anthropic`, `ollama`, `gemini`
- `model_name` (string, optional): Specific model (defaults to provider default)
- `use_cache` (boolean): Enable result caching (default: true)
- `metadata` (object, optional): Additional metadata for analysis

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "article_id": "uuid",
  "analysis_type": "comprehensive",
  "status": "pending",
  "model_used": "gpt-4o-mini",
  "model_provider": "openai",
  "cost": 0,
  "tokens_used": 0,
  "cached": false,
  "created_at": "2025-01-19T10:00:00Z"
}
```

**Status Values:**
- `pending` - Analysis queued
- `processing` - Analysis in progress
- `completed` - Analysis successful
- `failed` - Analysis failed (see error_message)

**Usage:**
```bash
curl -X POST http://localhost:8102/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "content": "Breaking news: Market surge...",
    "analysis_type": "comprehensive",
    "model_provider": "openai"
  }'
```

---

### POST /api/v1/analyze/batch

Queue batch content analysis for multiple articles.

**Authentication:** Required

**Request Body:**
```json
{
  "article_ids": ["uuid1", "uuid2", "uuid3"],
  "analysis_type": "comprehensive",
  "model_provider": "openai",
  "use_cache": true,
  "priority": "normal"
}
```

**Parameters:**
- `article_ids` (array[UUID], required): Article IDs to analyze
- `analysis_type` (enum): Analysis type to perform
- `model_provider` (enum): LLM provider
- `use_cache` (boolean): Enable caching
- `priority` (enum): `low`, `normal`, `high`

**Response:** `202 Accepted`
```json
{
  "job_id": "uuid",
  "status": "queued",
  "queued_count": 3,
  "estimated_time_seconds": 6,
  "message": "Batch analysis queued for 3 articles"
}
```

---

### GET /api/v1/analyze/{analysis_id}

Get analysis result by ID.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "article_id": "uuid",
  "analysis_type": "comprehensive",
  "status": "completed",
  "model_used": "gpt-4o-mini",
  "model_provider": "openai",
  "cost": 0.003,
  "tokens_used": 1500,
  "cached": false,
  "processing_time_ms": 2345,
  "created_at": "2025-01-19T10:00:00Z",
  "completed_at": "2025-01-19T10:00:03Z",
  "sentiment": {
    "overall_sentiment": "positive",
    "confidence": 0.92,
    "bias_detected": false,
    "subjectivity_score": 0.35
  },
  "entities": [
    {
      "text": "Federal Reserve",
      "type": "organization",
      "confidence": 0.98,
      "mention_count": 3
    }
  ],
  "topics": [
    {
      "topic": "Economics",
      "relevance_score": 0.95,
      "keywords": ["market", "inflation", "interest rates"],
      "is_primary": true
    }
  ],
  "summaries": [
    {
      "type": "short",
      "text": "Federal Reserve announces rate decision...",
      "compression_ratio": 0.15
    }
  ],
  "facts": [
    {
      "text": "Interest rates increased by 0.25%",
      "type": "statistic",
      "confidence": 0.99,
      "verification_status": "verified"
    }
  ]
}
```

---

### GET /api/v1/analysis/article/{item_id}

**NEW** - Get comprehensive analysis aggregation for an article.

Returns all available analysis data for a single article, combining category, sentiment, finance sentiment, geopolitical sentiment, entities, topics, summaries, facts, and keywords.

**Authentication:** Required

**Path Parameters:**
- `item_id` (UUID, required): Article/item ID from feed-service

**Response:** `200 OK`
```json
{
  "item_id": "uuid",
  "item_title": "Article headline",
  "item_link": "https://...",
  "item_author": "Author name",
  "item_published_at": "2025-01-19T10:00:00Z",
  "item_content": "Full article text...",
  "item_word_count": 850,

  "feed_id": "uuid",
  "feed_name": "Der Standard",
  "feed_config": {
    "enable_categorization": true,
    "enable_finance_sentiment": true,
    "enable_geopolitical_sentiment": true,
    "enable_osint_analysis": true
  },

  "category": {
    "id": "uuid",
    "category": "Politics Society",
    "confidence": 0.85,
    "alternative_categories": [
      {"category": "Geopolitics Security", "confidence": 0.15}
    ],
    "reasoning": "The article discusses...",
    "key_indicators": ["Bundespräsident", "Gesetz", "Nationalrat"],
    "cached": false,
    "processing_time_ms": 4027
  },

  "sentiment": {
    "id": "uuid",
    "overall_sentiment": "neutral",
    "confidence": 0.85,
    "positive_score": 0.2,
    "negative_score": 0.1,
    "neutral_score": 0.7,
    "bias_detected": false,
    "subjectivity_score": 0.4,
    "emotion_scores": {"joy": 0.1, "fear": 0.0},
    "reasoning": "The content discusses...",
    "key_phrases": ["Bundespräsident hat ein Gesetz nicht unterschrieben"],
    "cached": false,
    "processing_time_ms": 4945
  },

  "finance_sentiment": {
    "id": "uuid",
    "market_sentiment": "neutral",
    "market_confidence": 0.6,
    "time_horizon": "medium",
    "uncertainty": 0.4,
    "volatility": 0.3,
    "economic_impact": 0.2,
    "reasoning": "The content discusses...",
    "key_indicators": ["EU legal compliance"],
    "affected_sectors": ["government", "legal"],
    "affected_assets": ["bonds"],
    "cached": false,
    "processing_time_ms": 3719
  },

  "geopolitical_sentiment": {
    "id": "uuid",
    "stability_score": 0.2,
    "security_relevance": 0.1,
    "escalation_potential": 0.2,
    "conflict_type": "diplomatic",
    "time_horizon": "short",
    "confidence": 0.7,
    "regions_affected": ["Austria", "European Union"],
    "impact_beneficiaries": ["European Union"],
    "impact_affected": [],
    "alliance_activation": ["EU"],
    "diplomatic_impact_global": 0.1,
    "diplomatic_impact_western": 0.2,
    "diplomatic_impact_regional": 0.3,
    "reasoning": "The refusal of the Austrian President...",
    "key_factors": ["EU integration", "national sovereignty"],
    "cached": false,
    "processing_time_ms": 7631
  },

  "osint_events": [],
  "entities": [],
  "topics": [
    {
      "topic": "Legislative Process",
      "relevance_score": 0.9,
      "keywords": ["Bundespräsident", "Gesetz"],
      "is_primary": true
    }
  ],
  "summary": null,
  "facts": [],
  "keywords": [],

  "total_analyses": 14,
  "last_analyzed_at": "2025-01-19T20:14:08.885025"
}
```

**Usage:**
```bash
curl -X GET http://localhost:8102/api/v1/analysis/article/e92384b7-899b-4bd9-ab01-09cbaafcf868 \
  -H "Authorization: Bearer $TOKEN"
```

**Notes:**
- Cards are shown in frontend based on `feed_config`, not data availability
- Empty/null analysis fields indicate analysis not yet performed
- Category is only included if `feed_config.enable_categorization` is true

---

### GET /api/v1/analyze/feed/{feed_id}

Get all analyses for a specific feed.

**Authentication:** Required

**Query Parameters:**
- `limit` (int): Max results (default: 100, max: 1000)
- `offset` (int): Pagination offset (default: 0)
- `analysis_type` (enum, optional): Filter by analysis type

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "article_id": "uuid",
    "analysis_type": "comprehensive",
    "status": "completed",
    "created_at": "2025-01-19T10:00:00Z"
  }
]
```

---

## Specialized Analysis Endpoints

### POST /api/v1/analyze/sentiment

Perform sentiment analysis only.

**Request Body:**
```json
{
  "content": "Text to analyze...",
  "article_id": "uuid (optional)",
  "detect_bias": true,
  "detect_emotion": true,
  "use_cache": true
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "overall_sentiment": "positive",
  "confidence": 0.92,
  "bias_detected": false,
  "subjectivity_score": 0.35,
  "emotions": ["hopeful", "confident"],
  "cost": 0.001,
  "tokens_used": 500
}
```

---

### POST /api/v1/analyze/entities

Extract named entities from content.

**Request Body:**
```json
{
  "content": "Text to analyze...",
  "article_id": "uuid (optional)",
  "entity_types": ["person", "organization", "location"],
  "extract_relationships": true,
  "use_cache": true
}
```

**Entity Types:**
- `person` - People names
- `organization` - Companies, institutions
- `location` - Places, regions
- `date` - Temporal expressions
- `event` - Named events
- `product` - Products, services

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "entities": [
    {
      "text": "Elon Musk",
      "type": "person",
      "confidence": 0.99,
      "mention_count": 5,
      "relationships": [
        {
          "entity": "Tesla",
          "type": "organization",
          "relation": "CEO_of"
        }
      ]
    }
  ],
  "cost": 0.002,
  "tokens_used": 800
}
```

---

### POST /api/v1/analyze/topics

Classify content into topics.

**Request Body:**
```json
{
  "content": "Text to analyze...",
  "article_id": "uuid (optional)",
  "max_topics": 5,
  "extract_keywords": true,
  "use_cache": true
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "topics": [
    {
      "topic": "Technology",
      "relevance_score": 0.95,
      "keywords": ["AI", "machine learning", "automation"],
      "is_primary": true
    }
  ],
  "cost": 0.001,
  "tokens_used": 600
}
```

---

### POST /api/v1/analyze/summary

Generate content summaries.

**Request Body:**
```json
{
  "content": "Text to summarize...",
  "article_id": "uuid (optional)",
  "summary_types": ["short", "medium", "long"],
  "extract_key_points": true,
  "use_cache": true
}
```

**Summary Types:**
- `short` - 1-2 sentences (Twitter-length)
- `medium` - 3-5 sentences (abstract)
- `long` - 1-2 paragraphs (executive summary)

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "summaries": [
    {
      "type": "short",
      "text": "Federal Reserve raises interest rates by 0.25% to combat inflation.",
      "compression_ratio": 0.05
    },
    {
      "type": "medium",
      "text": "The Federal Reserve announced a 0.25% interest rate increase...",
      "compression_ratio": 0.15
    }
  ],
  "key_points": [
    "Interest rate increased by 0.25%",
    "Decision driven by inflation concerns",
    "Market reactions mostly positive"
  ],
  "cost": 0.002,
  "tokens_used": 1200
}
```

---

### POST /api/v1/analyze/facts

Extract facts from content.

**Request Body:**
```json
{
  "content": "Text to analyze...",
  "article_id": "uuid (optional)",
  "fact_types": ["claim", "statistic", "quote", "event"],
  "verify_facts": true,
  "use_cache": true
}
```

**Fact Types:**
- `claim` - Factual assertions
- `statistic` - Numerical data
- `quote` - Direct quotations
- `event` - Described occurrences

**Verification Status:**
- `verified` - Fact confirmed
- `disputed` - Contradictory evidence
- `unverified` - Insufficient evidence
- `pending` - Verification in progress

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "facts": [
    {
      "text": "GDP grew by 3.2% in Q4 2024",
      "type": "statistic",
      "confidence": 0.99,
      "verification_status": "verified",
      "source_reference": "Bureau of Economic Analysis"
    }
  ],
  "cost": 0.003,
  "tokens_used": 1500
}
```

---

### POST /api/v1/analyze/keywords

Extract keywords and key phrases.

**Request Body:**
```json
{
  "content": "Text to analyze...",
  "article_id": "uuid (optional)",
  "max_keywords": 10,
  "include_phrases": true,
  "use_cache": true
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "keywords": [
    {
      "text": "artificial intelligence",
      "relevance_score": 0.95,
      "frequency": 8,
      "is_phrase": true
    }
  ],
  "cost": 0.001,
  "tokens_used": 400
}
```

---

### POST /api/v1/analyze/category

**NEW** - Classify article into one of 6 fixed categories.

**Request Body:**
```json
{
  "content": "Article text to categorize...",
  "article_id": "uuid (optional)",
  "use_cache": true
}
```

**Categories:**
1. **Geopolitics Security** - International relations, conflicts, wars, military, terrorism, intelligence, cybersecurity
2. **Politics Society** - Domestic politics, government, elections, legislation, social movements, civil rights
3. **Economy Markets** - Finance, business, markets, economics, trade, corporate news, banking, investments
4. **Climate Environment Health** - Climate change, environment, sustainability, public health, pandemics, medical research
5. **Panorama** - Culture, arts, entertainment, lifestyle, human interest, sports, celebrities, travel
6. **Technology Science** - Technology, science, innovation, research, AI, space, biotechnology, engineering

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "category": "Politics Society",
  "confidence": 0.85,
  "alternative_categories": [
    {
      "category": "Geopolitics Security",
      "confidence": 0.15
    }
  ],
  "reasoning": "The article discusses a specific legislative action...",
  "key_indicators": [
    "Bundespräsident",
    "Gesetz",
    "Nationalrat",
    "EU-Anpassungsgesetz"
  ],
  "cached": false,
  "processing_time_ms": 4027
}
```

**Usage:**
```bash
curl -X POST http://localhost:8102/api/v1/analyze/category \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "content": "Breaking news: President rejects law...",
    "use_cache": true
  }'
```

---

### POST /api/v1/analyze/finance-sentiment

Finance-specific sentiment analysis.

**Request Body:**
```json
{
  "content": "Financial news text...",
  "article_id": "uuid (optional)",
  "use_cache": true
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "market_sentiment": "bullish",
  "economic_impact": "positive",
  "volatility_indicator": "low",
  "affected_sectors": ["technology", "finance"],
  "asset_classes": ["stocks", "bonds"],
  "risk_level": "medium",
  "confidence": 0.88,
  "cost": 0.002,
  "tokens_used": 900
}
```

---

### POST /api/v1/analyze/geopolitical-sentiment

Geopolitical sentiment analysis.

**Request Body:**
```json
{
  "content": "Geopolitical news text...",
  "article_id": "uuid (optional)",
  "use_cache": true
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "uuid",
  "stability_assessment": "stable",
  "conflict_indicators": ["diplomatic_tension"],
  "affected_regions": ["Eastern Europe"],
  "actors": ["NATO", "Russia"],
  "risk_level": "moderate",
  "confidence": 0.85,
  "cost": 0.002,
  "tokens_used": 1000
}
```

---

## Event Analysis (OSINT)

### GET /api/v1/event-analysis/stats

Get event analysis statistics.

**Authentication:** Required

**Query Parameters:**
- `period` (enum): `day`, `week`, `month` (default: week)

**Response:** `200 OK`
```json
{
  "period": "week",
  "total_events": 145,
  "by_confidence": {
    "high": 92,
    "medium": 41,
    "low": 12
  },
  "by_risk_tag": {
    "ihl_sensitive": 8,
    "civilian_impact": 23,
    "infrastructure": 15
  },
  "needs_review": 8,
  "by_day": [
    {
      "date": "2025-01-19",
      "count": 21
    }
  ]
}
```

---

### GET /api/v1/event-analysis/events/review-queue

Get events needing analyst review.

**Authentication:** Required

**Query Parameters:**
- `limit` (int): Max results (default: 50, max: 100)

**Response:** `200 OK`
```json
{
  "count": 8,
  "events": [
    {
      "id": "uuid",
      "headline": "Alleged attack on civilian infrastructure",
      "primary_event": "Infrastructure attack",
      "confidence_overall": "medium",
      "risk_tags": ["ihl_sensitive", "civilian_impact"],
      "event_date": "2025-01-18T14:30:00Z",
      "location": "Eastern Ukraine"
    }
  ]
}
```

**Review Triggers:**
- Critical risk tags: `ihl_sensitive`, `war_crime_allegation`, `chemical_use`, `nuclear_facility`
- Low confidence with any risk tags

---

### GET /api/v1/event-analysis/events/{event_id}

Get single event analysis by ID.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "article_id": "uuid",
  "headline": "Event headline",
  "primary_event": "Attack on infrastructure",
  "summary": "Event summary...",
  "event_date": "2025-01-18T14:30:00Z",
  "location": "City, Region",
  "actors": {
    "alleged_attacker": "Group A",
    "victim": "Civilians",
    "reporting_party": "Local authorities"
  },
  "claims": [
    {
      "claim": "Infrastructure damaged",
      "evidence_reference": "Satellite imagery",
      "confidence": "high"
    }
  ],
  "impact": {
    "fatalities": 0,
    "injuries": 3,
    "damage_assessment": "moderate"
  },
  "confidence_dimensions": {
    "source_reliability": 0.85,
    "corroboration": 0.75,
    "evidence_quality": 0.90
  },
  "confidence_overall": "high",
  "risk_tags": ["civilian_impact", "infrastructure"],
  "created_at": "2025-01-18T15:00:00Z"
}
```

---

## Health & Monitoring

### GET /health

Basic health check.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "content-analysis-service",
  "version": "0.1.0"
}
```

---

### GET /health/live

Kubernetes liveness probe.

**Response:** `200 OK` (service is alive)

---

### GET /health/ready

Kubernetes readiness probe.

Checks:
- Database connectivity
- Redis connectivity
- RabbitMQ connectivity
- LLM provider availability

**Response:** `200 OK` (service is ready) or `503 Service Unavailable`

---

### GET /health/rabbitmq

RabbitMQ consumer status.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "consumers": {
    "article_created": "active",
    "item_scraped": "active"
  },
  "messages_processed": 1234,
  "last_message_at": "2025-01-19T10:05:00Z"
}
```

---

### GET /metrics

Prometheus metrics endpoint.

**Metrics Available:**
- `analysis_jobs_total{status}` - Total analysis jobs by status
- `analysis_duration_seconds{type,provider}` - Analysis duration
- `llm_api_calls_total{provider}` - LLM API calls
- `llm_tokens_used_total{provider}` - Total tokens consumed
- `llm_cost_total{provider}` - Total API costs (USD)
- `cache_hits_total` - Cache hit count
- `cache_misses_total` - Cache miss count

---

## Error Handling

All endpoints return standard HTTP status codes and error responses:

**400 Bad Request:**
```json
{
  "detail": "Content exceeds maximum length of 50,000 characters"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

**404 Not Found:**
```json
{
  "detail": "Analysis uuid not found"
}
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded: 60 requests per minute"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Analysis failed: LLM API timeout"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "Service temporarily unavailable: Daily cost limit exceeded"
}
```

---

## Cost Management

### Daily Cost Limits

The service enforces daily cost limits to prevent excessive LLM API charges:

- Default: $100.00 per day (`MAX_DAILY_COST=100.0`)
- When limit reached: Returns `503 Service Unavailable`
- Reset: Midnight UTC

### Cost Optimization

1. **Enable Caching:** Set `use_cache: true` in requests
2. **Use Cheaper Models:** `gpt-4o-mini` instead of `gpt-4`
3. **Batch Processing:** Use `/analyze/batch` for multiple articles
4. **Local Models:** Configure Ollama for free local inference

---

## Related Documentation

- [Service Documentation](../services/content-analysis-service.md)
- [Configuration Reference](./content-analysis-service-config.md)
- [Event Architecture](../architecture/EVENT_DRIVEN_ARCHITECTURE.md)

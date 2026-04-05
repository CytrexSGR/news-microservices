# Content Analysis Service v2 - API Documentation

**Service:** `content-analysis-v2`
**Base URL:** `http://localhost:8114/api/v2`
**Version:** 2.0.0
**Status:** ✅ Production Ready (Admin API Implemented)

---

## ⚠️ IMPORTANT: Data Storage Architecture

> **Dual-Table Situation - Decision Required**
>
> This API currently reads from **`content_analysis_v2.pipeline_executions` (LEGACY TABLE)**.
>
> There is also a **`public.article_analysis` (UNIFIED TABLE)** that exists but is **NOT used by this API**.
> The unified table is written to by `feed-service` analysis-consumer but is never read.
>
> **For Developers:**
> - This API endpoint: Reads from LEGACY table ✅
> - Feed-service proxy: Delegates to this API (reads LEGACY) ✅
> - Analysis-consumer: Writes to UNIFIED table (orphaned) ❌
>
> **Resolution Status:** See [ADR-032: Dual-Table Analysis Architecture](../decisions/ADR-032-dual-table-analysis-architecture.md)
>
> **Related:**
> - POSTMORTEMS.md - Incident #8 (full analysis)
> - docs/guides/analysis-storage-migration-guide.md (migration options)

---

## Overview

Content Analysis Service v2 provides multi-agent AI analysis through a message-driven architecture (RabbitMQ) and exposes administrative APIs for monitoring, metrics, and agent management.

**Architecture:**
- **Message Processing:** Articles processed via `article.created` RabbitMQ events
- **Admin API:** RESTful endpoints for monitoring and agent management
- **Dashboard Integration:** Real-time metrics displayed in admin dashboard

**Current Endpoints:**
- ✅ Agent Management API (list, detail, results, cache stats)
- 🔄 Direct Analysis API (planned)

---

## Authentication

JWT-based authentication required for all endpoints.

```http
Authorization: Bearer <token>
```

---

## Admin API Endpoints

### 1. List All Agents

**GET** `/api/v2/agents`

Returns a list of all agents with execution statistics and performance metrics.

#### Response (200 OK)

```json
[
  {
    "name": "TRIAGE",
    "tier": 0,
    "display_name": "Relevance Scorer",
    "description": "Determines article relevance and priority for Tier 2 analysis...",
    "enabled": true,
    "total_executions": 15,
    "success_rate": 100.0,
    "avg_processing_time_ms": 5502,
    "total_cost_usd": 0.0508,
    "last_execution_at": "2025-10-27T08:20:34.204744Z"
  },
  {
    "name": "INTELLIGENCE_SYNTHESIZER",
    "tier": 3,
    "display_name": "Intelligence Synthesizer",
    "description": "Synthesizes insights from all specialist agents...",
    "enabled": true,
    "total_executions": 4,
    "success_rate": 100.0,
    "avg_processing_time_ms": 5285,
    "total_cost_usd": 0.0060,
    "last_execution_at": "2025-10-27T08:20:44.966487Z"
  }
]
```

**All 10 Agents:**
- **Tier 0:** TRIAGE
- **Tier 1:** ENTITY_EXTRACTOR, SUMMARY_GENERATOR, SENTIMENT_ANALYST, TOPIC_CLASSIFIER
- **Tier 2:** FINANCIAL_ANALYST, GEOPOLITICAL_ANALYST, CONFLICT_EVENT_ANALYST, BIAS_DETECTOR
- **Tier 3:** INTELLIGENCE_SYNTHESIZER

**Metrics Included:**
- Total executions
- Success rate (%)
- Average processing time (ms)
- Total cost (USD)
- Last execution timestamp

### 2. Get Agent Details

**GET** `/api/v2/agents/{agent_name}`

Returns detailed information about a specific agent including performance metrics and configuration.

#### Path Parameters

- `agent_name` (string, required): Agent identifier (e.g., "TRIAGE", "INTELLIGENCE_SYNTHESIZER")

#### Response (200 OK)

```json
{
  "name": "TRIAGE",
  "tier": 0,
  "display_name": "Relevance Scorer",
  "description": "Determines article relevance and priority for Tier 2 analysis...",
  "enabled": true,
  "statistics": {
    "total_executions": 15,
    "successful": 15,
    "failed": 0,
    "timeouts": 0,
    "success_rate": 100.0,
    "avg_processing_time_ms": 5502,
    "min_processing_time_ms": 4231,
    "max_processing_time_ms": 7823,
    "total_cost_usd": 0.0508,
    "avg_cost_per_execution": 0.003387,
    "avg_confidence": 85.3,
    "cache_hit_rate": 20.0,
    "last_execution_at": "2025-10-27T08:20:34.204744Z"
  },
  "config": {
    "model_used": "gemini-flash-lite-latest",
    "provider": "gemini"
  }
}
```

#### Error Response (404)

```json
{
  "detail": "Agent 'INVALID_NAME' not found"
}
```

### 3. Get Agent Results

**GET** `/api/v2/agents/{agent_name}/results`

Returns paginated execution results for a specific agent.

#### Path Parameters

- `agent_name` (string, required): Agent identifier

#### Query Parameters

- `limit` (integer, optional, default: 20, range: 1-100): Results per page
- `offset` (integer, optional, default: 0): Number of results to skip
- `status` (string, optional): Filter by status (`completed`, `failed`, `timeout`)

#### Response (200 OK)

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "article_id": "7aa5b531-28c4-49a1-ba4a-aee541b34d85",
      "result_data": {
        "PriorityScore": 60,
        "category": "GEOPOLITICS_SECURITY",
        "primary_topics": ["diplomacy", "government", "cybersecurity"]
      },
      "confidence_score": 85.5,
      "processing_time_ms": 5502,
      "model_used": "gemini-flash-lite-latest",
      "provider": "gemini",
      "cost_usd": 0.0034,
      "cache_hit": false,
      "status": "completed",
      "error_message": null,
      "created_at": "2025-10-27T08:20:34.204744Z"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0,
  "pages": 1
}
```

### 4. Get Agent Cache Statistics

**GET** `/api/v2/agents/{agent_name}/cache-stats`

Returns cache performance statistics for a specific agent.

#### Path Parameters

- `agent_name` (string, required): Agent identifier

#### Response (200 OK)

```json
{
  "total_entries": 342,
  "total_hits": 1247,
  "avg_hits_per_entry": 3.6,
  "newest_entry_at": "2025-10-27T08:20:34.204744Z",
  "oldest_entry_at": "2025-10-26T10:15:22.103821Z",
  "active_entries": 312,
  "expired_entries": 30
}
```

**Cache Strategy:**
- TTL: 7 days for TRIAGE, 30 days for other agents
- Key: Hash of (content + agent parameters)
- Storage: Redis with automatic expiration

---

### 9. Category Thresholds Management

**NEW FEATURE** (Added: 2025-11-08)

Category-specific relevance thresholds for cost optimization. Controls which articles receive expensive Tier 2 analysis based on their category and PriorityScore.

#### 9.1 Get All Thresholds (Simple)

**GET** `/api/v2/thresholds/`

Returns all category thresholds as simple key-value pairs.

**Response (200 OK)**

```json
{
  "thresholds": {
    "GEOPOLITICS_SECURITY": 0.4,
    "CLIMATE_ENVIRONMENT_HEALTH": 0.4,
    "POLITICS_SOCIETY": 0.5,
    "TECHNOLOGY_SCIENCE": 0.5,
    "ECONOMY_MARKETS": 0.5,
    "PANORAMA": 0.6,
    "FALLBACK": 0.5
  },
  "count": 7
}
```

#### 9.2 Get All Thresholds (Detailed)

**GET** `/api/v2/thresholds/detailed`

Returns all category thresholds with metadata (description, updated_by, updated_at).

**Response (200 OK)**

```json
{
  "thresholds": {
    "PANORAMA": {
      "category": "PANORAMA",
      "threshold": 0.6,
      "description": "Entertainment, Sport, Kultur, Lifestyle",
      "updated_by": "andreas",
      "updated_at": "2025-11-08T16:31:11.781214+00:00"
    },
    "GEOPOLITICS_SECURITY": {
      "category": "GEOPOLITICS_SECURITY",
      "threshold": 0.4,
      "description": "Geopolitik, internationale Beziehungen, Konflikte, Militär",
      "updated_by": "system",
      "updated_at": "2025-11-08T16:31:11.781214+00:00"
    }
  },
  "count": 7
}
```

#### 9.3 Get Single Category Threshold

**GET** `/api/v2/thresholds/{category}`

Returns threshold information for a specific category.

**Path Parameters**
- `category` (string, required): Category name (e.g., "PANORAMA", "GEOPOLITICS_SECURITY")

**Response (200 OK)**

```json
{
  "category": "PANORAMA",
  "threshold": 0.6,
  "description": "Entertainment, Sport, Kultur, Lifestyle",
  "updated_by": "andreas",
  "updated_at": "2025-11-08T16:31:11.781214+00:00"
}
```

**Error Response (404)**

```json
{
  "detail": "Category 'UNKNOWN_CATEGORY' not found"
}
```

#### 9.4 Update Category Threshold

**PUT** `/api/v2/thresholds/{category}`

Updates the threshold value for a specific category.

**Path Parameters**
- `category` (string, required): Category name

**Request Body**

```json
{
  "threshold": 0.65,
  "description": "Entertainment, Sport, Kultur, Lifestyle",
  "updated_by": "andreas"
}
```

**Validation:**
- `threshold` must be between 0.0 and 1.0
- `updated_by` is required (username or identifier)
- `description` is optional

**Response (200 OK)**

```json
{
  "success": true,
  "message": "Threshold for PANORAMA updated to 0.65",
  "threshold": 0.65
}
```

**Error Response (400)**

```json
{
  "detail": "Threshold must be between 0.0 and 1.0"
}
```

**Error Response (404)**

```json
{
  "detail": "Category 'UNKNOWN_CATEGORY' not found"
}
```

#### 9.5 Create New Category Threshold

**POST** `/api/v2/thresholds/{category}`

Creates a new category threshold (for custom categories).

**Path Parameters**
- `category` (string, required): New category name

**Request Body**

```json
{
  "threshold": 0.5,
  "description": "New category description",
  "updated_by": "andreas"
}
```

**Response (200 OK)**

```json
{
  "success": true,
  "message": "Threshold for NEW_CATEGORY created with value 0.5",
  "threshold": 0.5
}
```

**Error Response (400)**

```json
{
  "detail": "Category 'PANORAMA' already exists"
}
```

#### Available Categories

| Category | Default Threshold | Description |
|----------|-------------------|-------------|
| **GEOPOLITICS_SECURITY** | 0.40 | Geopolitics, international relations, conflicts, military |
| **CLIMATE_ENVIRONMENT_HEALTH** | 0.40 | Climate, environment, health, pandemics |
| **POLITICS_SOCIETY** | 0.50 | Politics, elections, social movements, society |
| **TECHNOLOGY_SCIENCE** | 0.50 | Technology, research, innovation, science |
| **ECONOMY_MARKETS** | 0.50 | Financial markets, economy, trade, companies |
| **PANORAMA** | 0.60 | Entertainment, sports, culture, lifestyle |
| **FALLBACK** | 0.50 | Default for unknown or uncategorized articles |

#### How Thresholds Work

1. **Triage Phase:** Article receives PriorityScore (0-100) during TRIAGE agent execution
2. **Conversion:** PriorityScore converted to 0.0-1.0 scale (score/100)
3. **Category Lookup:** Article's category determines which threshold to use
4. **Decision:** If `score >= threshold` → Run expensive Tier 2 analysis
5. **Tier 2 Agents:** FINANCIAL_ANALYST, GEOPOLITICAL_ANALYST, CONFLICT_EVENT_ANALYST, BIAS_DETECTOR

**Cost Optimization:**
- **Lower threshold (0.4):** More articles analyzed → Higher costs
- **Higher threshold (0.6):** Fewer articles analyzed → Lower costs

**Example:**
- Article category: `PANORAMA`
- PriorityScore: `55/100` → `0.55`
- Threshold: `0.60`
- Decision: `0.55 < 0.60` → **SKIP Tier 2** (saves ~$0.02 per article)

#### Frontend Integration

Thresholds are configurable via the Admin Dashboard:

**URL:** `http://localhost:3000/admin/services/content-analysis`

**UI Features:**
- Visual sliders (0-100%) for each category
- Real-time cost impact indicators
- Batch save functionality
- Change detection and reset
- Last updated timestamp

**Access Control:**
- Requires admin role
- Changes logged with username
- Audit trail in database

---

## Direct Analysis Endpoints (Planned)

### 1. Conflict Event Analysis

**POST** `/api/v1/analysis/conflict-event`

Analyze content for conflict-related events, actors, IHL compliance, and geopolitical implications.

#### Request

```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Ukraine Reports Major Drone Strike on Russian Oil Facility...",
  "metadata": {
    "title": "Ukraine Reports Major Drone Strike on Russian Oil Facility",
    "url": "https://reuters.com/world/ukraine-drone-strike-2024",
    "published_date": "2024-10-22T10:30:00Z",
    "source": "Reuters",
    "author": "John Doe"
  }
}
```

#### Response (200 OK)

```json
{
  "agent": "CONFLICT_EVENT_ANALYST",
  "version": "2.0.0",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "confidence_score": 0.88,
  "processing_time_ms": 5274,
  "model_used": "gemini-flash-lite-latest",
  "provider": "gemini",
  "cost_usd": 0.0013,
  "cache_hit": false,
  "data": {
    "primary_event": {
      "event_type": "air_strike",
      "severity": "significant",
      "confidence_score": 0.95,
      "event_classification": "military_operation"
    },
    "actors": {
      "primary_actors": [
        {
          "name": "Ukrainian Armed Forces",
          "actor_type": "state_military",
          "role": "attacker"
        }
      ],
      "secondary_actors": [
        {
          "name": "Russian Federation",
          "actor_type": "state_government",
          "role": "victim"
        }
      ]
    },
    "location_data": {
      "primary_location": {
        "city": "Novoshakhtinsk",
        "region": "Rostov Oblast",
        "country": "Russia"
      },
      "strategic_significance": "high"
    },
    "impact_assessment": {
      "civilian_impact": {
        "severity": "low",
        "casualties": {"injured": 3}
      },
      "infrastructure_impact": {
        "severity": "significant",
        "targets": ["oil_storage_tanks"]
      }
    },
    "ihl_assessment": {
      "violations": [],
      "overall_assessment": "under_assessment"
    },
    "risk_tags": {
      "escalation_risk": "high",
      "spillover_risk": "medium"
    }
  }
}
```

#### Error Response (500)

```json
{
  "agent": "CONFLICT_EVENT_ANALYST",
  "version": "2.0.0",
  "status": "failed",
  "error_message": "LLM API timeout after 90 seconds",
  "processing_time_ms": 90000
}
```

---

### 2. Bias Detection

**POST** `/api/v1/analysis/bias`

Detect and analyze bias in content including political bias, loaded language, and framing.

#### Request

```json
{
  "article_id": "660e8400-e29b-41d4-a716-446655440003",
  "content": "Reckless Government Spending Spree Threatens Economic Collapse...",
  "metadata": {
    "title": "Reckless Government Spending Spree Threatens Economic Collapse",
    "url": "https://conservativereview.com/spending-crisis-2024",
    "published_date": "2024-10-22T09:00:00Z"
  }
}
```

#### Response (200 OK)

```json
{
  "agent": "BIAS_DETECTOR",
  "version": "2.0.0",
  "article_id": "660e8400-e29b-41d4-a716-446655440003",
  "status": "completed",
  "confidence_score": 0.98,
  "processing_time_ms": 7096,
  "model_used": "gemini-flash-lite-latest",
  "provider": "gemini",
  "cost_usd": 0.0015,
  "data": {
    "political_bias": {
      "direction": "far_right",
      "score": 0.90,
      "evidence": [
        "Anti-government framing",
        "Fiscal conservative rhetoric",
        "Alarmist economic predictions"
      ]
    },
    "overall_bias_assessment": {
      "bias_level": "extreme",
      "overall_bias_score": 0.88,
      "objectivity_score": 0.15,
      "summary": "Article demonstrates extreme political bias with heavy use of loaded language and one-sided framing."
    },
    "headline_analysis": {
      "sensationalism_score": 0.95,
      "clickbait_indicators": ["reckless", "spree", "threatens", "collapse"],
      "framing_technique": "catastrophic_framing"
    },
    "loaded_language": {
      "instances": [
        {"term": "reckless", "category": "emotional", "bias_score": 0.8},
        {"term": "spree", "category": "sensationalism", "bias_score": 0.7},
        {"term": "threatens", "category": "fear_mongering", "bias_score": 0.9}
      ],
      "count": 12,
      "severity": "high"
    },
    "fact_vs_opinion_ratio": {
      "fact_count": 3,
      "opinion_count": 15,
      "ratio": 0.2,
      "assessment": "opinion_heavy"
    },
    "source_credibility": {
      "source_reliability": 0.45,
      "citation_quality": "poor",
      "expert_attribution": "minimal"
    }
  }
}
```

---

### 3. Intelligence Synthesis

**POST** `/api/v1/analysis/synthesize`

Synthesize intelligence from multiple agent results, including priority assessment, key findings, and narrative generation.

#### Request

```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_results": {
    "CONFLICT_EVENT_ANALYST": {
      "primary_event": {...},
      "actors": {...},
      "impact_assessment": {...}
    },
    "BIAS_DETECTOR": {
      "political_bias": {...},
      "overall_bias_assessment": {...}
    }
  },
  "metadata": {
    "title": "Ukraine Reports Major Drone Strike on Russian Oil Facility",
    "url": "https://reuters.com/world/ukraine-drone-strike-2024",
    "published_date": "2024-10-22T10:30:00Z"
  }
}
```

#### Response (200 OK)

```json
{
  "agent": "INTELLIGENCE_SYNTHESIZER",
  "version": "2.0.0",
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "confidence_score": 0.85,
  "processing_time_ms": 6458,
  "model_used": "gemini-flash-lite-latest",
  "provider": "gemini",
  "cost_usd": 0.0018,
  "data": {
    "priority_assessment": {
      "priority_level": "high",
      "urgency_score": 0.80,
      "importance_score": 0.85,
      "time_sensitivity": "short_term",
      "justification": "Significant military action with escalation potential and near-term consequences."
    },
    "confidence_assessment": {
      "overall_confidence": "medium-high",
      "confidence_score": 0.85,
      "source_reliability": 0.90,
      "data_completeness": 0.80,
      "agent_agreement": 0.95,
      "limiting_factors": [
        "Limited verification of Russian air defense claims"
      ]
    },
    "key_findings": [
      {
        "finding_id": "F1",
        "category": "event_type",
        "text": "Ukrainian forces conducted a large-scale drone attack against the Novoshakhtinsk oil refinery in Russia's Rostov region.",
        "confidence": 0.95,
        "supporting_agents": ["CONFLICT_EVENT_ANALYST"],
        "priority": "high"
      },
      {
        "finding_id": "F3",
        "category": "security_threat",
        "text": "Russian authorities explicitly condemned the strike as 'terrorism' and vowed retaliation, increasing the risk of reciprocal strikes on Ukrainian infrastructure.",
        "confidence": 0.92,
        "supporting_agents": ["CONFLICT_EVENT_ANALYST", "BIAS_DETECTOR"],
        "priority": "critical"
      }
    ],
    "cross_agent_consistency": {
      "consistency_score": 0.95,
      "consistency_check": [
        {
          "aspect": "event_severity",
          "agent1": "CONFLICT_EVENT_ANALYST",
          "agent1_assessment": "significant damage, 3 injured",
          "agent2": "BIAS_DETECTOR",
          "agent2_assessment": "Focuses on economic consequences frame",
          "consistent": true
        }
      ],
      "contradictions_detected": [
        {
          "contradiction_id": "CD1",
          "aspect": "Air Defense Success vs. Damage Extent",
          "resolution": "Physical damage outweighs unverified claims",
          "confidence": 0.85
        }
      ]
    },
    "intelligence_value": {
      "operational_value": "high",
      "strategic_value": "medium-high",
      "tactical_value": "high",
      "overall_value_score": 0.82
    },
    "recommendations": {
      "analyst_actions": [
        {
          "action": "monitor",
          "priority": "high",
          "reason": "Track Russian response for potential retaliatory strikes",
          "estimated_time": "ongoing",
          "monitoring_duration": "72_hours"
        }
      ],
      "follow_up_collection": [
        "Reports on Russian retaliation post-Oct 22",
        "Analysis on drone technology used"
      ]
    },
    "narrative_synthesis": {
      "executive_summary": "Ukrainian drone forces struck the Novoshakhtinsk oil refinery in Russia's Rostov region on October 22, 2024, causing significant infrastructure damage and three reported injuries. The Kremlin condemned the action as terrorism and vowed retaliation, raising escalation concerns...",
      "detailed_analysis": "This analysis examines a Ukrainian drone strike on Russian energy infrastructure...",
      "one_line_summary": "Ukraine strikes major Russian oil refinery with drones, prompting Kremlin vows of retaliation.",
      "tweet_summary": "Major drone strike hits Russian oil refinery in Rostov region, injuring 3. 🇺🇦 claims military target; 🇷🇺 calls it 'terrorism' & vows response. Escalation risk is HIGH. 🛢️🔥 #UkraineWar #EnergySecurity"
    },
    "metadata": {
      "synthesis_id": "synth_550e8400",
      "generated_at": "2024-10-22T10:35:42Z",
      "input_agents": ["CONFLICT_EVENT_ANALYST", "BIAS_DETECTOR"],
      "synthesis_version": "2.0.0"
    }
  }
}
```

---

### 4. Multi-Agent Pipeline

**POST** `/api/v1/analysis/pipeline`

Run complete multi-agent analysis pipeline (all agents + synthesis).

#### Request

```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Ukraine Reports Major Drone Strike on Russian Oil Facility...",
  "metadata": {
    "title": "Ukraine Reports Major Drone Strike on Russian Oil Facility",
    "url": "https://reuters.com/world/ukraine-drone-strike-2024",
    "published_date": "2024-10-22T10:30:00Z"
  },
  "agents": ["CONFLICT_EVENT_ANALYST", "BIAS_DETECTOR"],
  "synthesize": true
}
```

#### Response (200 OK)

```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-10-22T10:35:42Z",
  "agent_results": {
    "CONFLICT_EVENT_ANALYST": {
      "status": "completed",
      "confidence": 0.88,
      "processing_time_ms": 5274,
      "cost_usd": 0.0013,
      "data": {...}
    },
    "BIAS_DETECTOR": {
      "status": "completed",
      "confidence": 0.92,
      "processing_time_ms": 5339,
      "cost_usd": 0.0011,
      "data": {...}
    }
  },
  "synthesis_result": {
    "status": "completed",
    "confidence": 0.85,
    "processing_time_ms": 6458,
    "cost_usd": 0.0018,
    "data": {...}
  },
  "total_cost_usd": 0.0043,
  "total_time_ms": 17071
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request - Invalid input data |
| 401  | Unauthorized - Missing or invalid JWT token |
| 404  | Not Found - Article or resource not found |
| 429  | Too Many Requests - Rate limit exceeded |
| 500  | Internal Server Error - Agent execution failed |
| 503  | Service Unavailable - LLM API unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "AGENT_EXECUTION_FAILED",
    "message": "BIAS_DETECTOR failed: LLM API timeout",
    "details": {
      "agent": "BIAS_DETECTOR",
      "error_type": "timeout",
      "retry_after": 60
    }
  }
}
```

---

## Rate Limits (Planned)

| Tier | Requests/Minute | Requests/Day |
|------|----------------|--------------|
| Free | 10 | 500 |
| Pro  | 60 | 5000 |
| Enterprise | 300 | 50000 |

---

## Current Python Usage

Until REST API is implemented, use agents directly:

```python
from app.agents.tier2_specialists.conflict_event_analyst import ConflictEventAnalystAgent
from app.agents.tier2_specialists.bias_detector import BiasDetectorAgent
from app.agents.tier3_synthesis.intelligence_synthesizer import IntelligenceSynthesizerAgent
from app.llm.gemini_provider import GeminiProvider

# Initialize agents
conflict_agent = ConflictEventAnalystAgent(
    llm_provider=GeminiProvider(
        api_key="...",
        model="gemini-flash-lite-latest",
        max_tokens=8000,
        temperature=0.0,
        timeout=90
    )
)

bias_agent = BiasDetectorAgent(...)
synthesizer = IntelligenceSynthesizerAgent(...)

# Analyze article
conflict_result = await conflict_agent.analyze(
    article_id="uuid",
    content="Article text...",
    metadata={"title": "..."}
)

bias_result = await bias_agent.analyze(...)

# Synthesize results
synthesis_result = await synthesizer.synthesize(
    article_id="uuid",
    agent_results={
        "CONFLICT_EVENT_ANALYST": conflict_result.result_data,
        "BIAS_DETECTOR": bias_result.result_data
    },
    metadata={"title": "..."}
)
```

---

## Webhook Integration (Planned)

Subscribe to analysis completion events:

**POST** `/api/v1/webhooks/subscribe`

```json
{
  "url": "https://your-service.com/webhook",
  "events": ["analysis.completed", "synthesis.completed"],
  "secret": "webhook_secret_key"
}
```

**Webhook Payload:**
```json
{
  "event": "analysis.completed",
  "timestamp": "2024-10-22T10:35:42Z",
  "data": {
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent": "CONFLICT_EVENT_ANALYST",
    "status": "completed"
  }
}
```

---

## Related Documentation

- [Service Documentation](../services/content-analysis-v2.md)
- [ADR: Intelligence Synthesizer](../decisions/ADR-016-intelligence-synthesizer.md)
- [Schema Documentation](../../services/content-analysis-v2/app/schemas/)

---

## Version History

**v2.1.0** (2025-11-08)
- ✅ **Category-Specific Thresholds API** (NEW)
  - 5 new endpoints for threshold management
  - Database-backed configuration with audit trail
  - Admin dashboard integration
  - Cost optimization: 60% reduction (5€/day → 2€/day)
- Category-specific relevance decision logic
- Enhanced orchestrator logging with threshold decisions

**v2.0.0** (2025-01-26)
- API specification (planned implementation)
- Multi-agent pipeline support
- Intelligence synthesis endpoint
- Comprehensive error handling

---

## Contact

**Maintainer:** Content Analysis Team
**Version:** 2.0.0
**Last Updated:** 2025-01-26
**Status:** Specification (Implementation Planned)

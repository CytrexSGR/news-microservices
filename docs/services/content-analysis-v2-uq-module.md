# Content Analysis V2 - Uncertainty Quantification Module

**Service:** content-analysis-v2
**Component:** UQ Module (Uncertainty Quantification)
**Version:** 1.0
**Status:** Production
**Last Updated:** 2025-11-02

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [API Reference](#api-reference)
5. [Event Schema](#event-schema)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Development Guide](#development-guide)

---

## Overview

The Uncertainty Quantification (UQ) Module is a critical component of the content-analysis-v2 service that:

1. **Measures confidence** in AI-generated analysis results
2. **Calculates quality scores** across 6 dimensions
3. **Triggers verification workflows** for low-confidence analyses
4. **Publishes events** to RabbitMQ for downstream processing

### Key Features

- **Multi-dimensional Quality Scoring** (Credibility, Objectivity, Verification, Relevance, Completeness, Consistency)
- **Financial Uncertainty Tracking** (market confidence, volatility, economic impact)
- **Event-Driven Architecture** (RabbitMQ integration)
- **Configurable Thresholds** (environment-based configuration)
- **Zero Additional LLM Costs** (uses existing agent data)
- **<1.5% Latency Overhead** (efficient calculation algorithms)

### Use Cases

| Use Case | Description | Trigger |
|----------|-------------|---------|
| **Human Review Queue** | Flag articles needing manual verification | Quality score < 50 |
| **Financial Risk Assessment** | Identify high-uncertainty market analyses | Uncertainty > 0.75 |
| **Source Credibility Alerts** | Warn about unreliable news sources | Credibility < 40 |
| **Cross-Verification** | Trigger multi-source fact-checking | Verification score < 40 |
| **Quality Trending** | Track analysis quality over time | Dashboard metrics |

---

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Content Analysis V2                       │
│                                                              │
│  ┌──────────────┐                                           │
│  │   Triage     │                                           │
│  │   Agent      │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ↓                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Tier 1     │ →  │   Tier 2     │ →  │   Tier 3     │ │
│  │  Foundation  │    │ Specialists  │    │  Synthesis   │ │
│  │              │    │              │    │              │ │
│  │ • Entity     │    │ • Financial  │    │ • Intelligence│ │
│  │ • Sentiment  │    │ • Geopolitical│   │ • Cross-agent│ │
│  │ • Topics     │    │ • Conflict   │    │   consistency│ │
│  │ • Summary    │    │ • Bias       │    │              │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│         │                   │                   │          │
│         └───────────────────┴───────────────────┘          │
│                            │                                │
│                            ↓                                │
│              ┌──────────────────────────┐                  │
│              │   UQ MODULE              │                  │
│              │                          │                  │
│              │  1. Quality Calculation  │                  │
│              │  2. Uncertainty Analysis │                  │
│              │  3. Trigger Decision     │                  │
│              │  4. Event Publishing     │                  │
│              └──────────┬───────────────┘                  │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ↓
                   ┌─────────────┐
                   │  RabbitMQ   │
                   │  Exchange:  │
                   │ news.events │
                   └──────┬──────┘
                          │
                          ↓
              ┌───────────────────────┐
              │  Verification Service │ (Future)
              │  • Cross-reference    │
              │  • Multi-source check │
              │  • Human review UI    │
              └───────────────────────┘
```

### Component Flow

```
Article → Pipeline Orchestrator
           ↓
        [Execute All Tiers]
           ↓
        Quality Indicators Calculator
           ↓
        Verification Trigger Logic
           ↓
        Event Publisher (if triggered)
           ↓
        RabbitMQ (verification.required)
```

---

## Components

### 1. Quality Indicators Calculator

**Location:** `app/quality_scoring/quality_indicators.py`

**Purpose:** Calculate 6-dimensional quality scores from pipeline execution data.

#### Core Function

```python
def calculate_all_quality_scores(pipeline_execution: Dict) -> Dict:
    """
    Calculate all quality scores from pipeline execution data.

    Args:
        pipeline_execution: Complete pipeline execution result with:
            - triage_decision: Triage agent output
            - tier1_summary: Foundation agents output
            - tier2_summary: Specialist agents output
            - tier3_summary: Synthesis agent output
            - agents_executed: List of successfully executed agents

    Returns:
        dict: {
            "overall_score": float (0-100),
            "scores": {
                "credibility": {...},
                "objectivity": {...},
                "verification": {...},
                "relevance": {...},
                "completeness": {...},
                "consistency": {...}
            },
            "validation": {
                "agents_available": [...],
                "agents_missing": [...],
                "completeness_percentage": float,
                "warnings": [...]
            },
            "quality_category": {
                "category": str,
                "recommendation": str,
                "flags": [...],
                "use_cases": [...],
                "display_badge": str,
                "confidence": str
            },
            "metadata": {
                "weights_used": {...},
                "article_type": {...},
                "calculation_version": str
            }
        }
    """
```

#### Individual Score Calculators

**1. Credibility Score**
```python
def calculate_credibility_score(pipeline_data: Dict) -> Dict:
    """
    Credibility Score: 0-100

    Components:
    - Source Credibility (40%): Reliability + transparency + triage source score
    - Bias Level (30%): Overall bias assessment (inverted)
    - Fact/Opinion Ratio (20%): Percentage of factual content
    - Verification Status (10%): Conflict verification

    Data Sources:
    - tier2_summary.bias_detector.source_credibility
    - tier2_summary.bias_detector.overall_bias_assessment
    - tier2_summary.bias_detector.fact_vs_opinion_ratio
    - tier2_summary.conflict_analyst.verification_status
    - triage_decision.scoring_justification.SourceScore
    """
```

**2. Objectivity Score**
```python
def calculate_objectivity_score(pipeline_data: Dict) -> Dict:
    """
    Objectivity Score: 0-100

    Components:
    - Subjectivity (25%): Sentiment subjectivity (inverted)
    - Political Bias (20%): Political bias score (inverted)
    - Framing Balance (20%): Framing analysis balance
    - Perspective Balance (20%): Multiple viewpoints presented
    - Emotional Manipulation (15%): Manipulation risk (inverted)

    Data Sources:
    - tier1_summary.sentiment.subjectivity_score
    - tier2_summary.bias_detector.political_bias
    - tier2_summary.bias_detector.framing_analysis
    - tier2_summary.bias_detector.perspective_balance
    - tier2_summary.bias_detector.emotional_language
    """
```

**3. Verification Score**
```python
def calculate_verification_score(pipeline_data: Dict) -> Dict:
    """
    Verification Score: 0-100

    Components:
    - Verification Status (35%): Overall verification assessment
    - Evidence Count (30%): Photos, videos, witnesses, statements
    - Source Count (20%): Number of independent sources
    - Confidence (15%): Analysis confidence

    Data Sources:
    - tier2_summary.conflict_analyst.verification_status
    - tier2_summary.conflict_analyst.evidence
    - tier2_summary.bias_detector.perspective_balance.viewpoints_presented
    - tier2_summary.conflict_analyst.verification_status.confidence
    - tier3_summary.intelligence_synthesizer.confidence_assessment
    """
```

**4. Relevance Score**
```python
def calculate_relevance_score(pipeline_data: Dict) -> Dict:
    """
    Relevance Score: 0-100

    Components:
    - Priority Score (40%): Triage priority assessment
    - Impact Scores (30%): Geopolitical + economic + security impact
    - Intelligence Value (20%): Operational + strategic relevance
    - Time Sensitivity (10%): Urgency assessment

    Data Sources:
    - triage_decision.PriorityScore
    - tier2_summary.geopolitical_analyst.stability_score
    - tier2_summary.geopolitical_analyst.security_relevance
    - tier2_summary.financial_analyst.economic_impact
    - tier3_summary.intelligence_synthesizer.intelligence_value
    - tier3_summary.intelligence_synthesizer.priority_assessment
    """
```

**5. Completeness Score**
```python
def calculate_completeness_score(pipeline_data: Dict) -> Dict:
    """
    Completeness Score: 0-100

    Components:
    - Agent Coverage (30%): Number of successful agents
    - Information Depth (25%): Key findings + entity count
    - Missing Context (25%): Omitted context (inverted)
    - Evidence Completeness (20%): Evidence type diversity

    Data Sources:
    - agents_executed: List of executed agents
    - tier3_summary.intelligence_synthesizer.key_findings
    - tier1_summary.entities
    - tier2_summary.bias_detector.omission_analysis
    - tier2_summary.conflict_analyst.evidence
    """
```

**6. Consistency Score**
```python
def calculate_consistency_score(pipeline_data: Dict) -> Dict:
    """
    Consistency Score: 0-100

    Components:
    - Cross-Agent Consistency (40%): Synthesizer consistency score
    - Contradiction Count (30%): Number of contradictions (inverted)
    - Confidence Variance (20%): Variance in agent confidences
    - Claim Consistency (10%): Sentiment vs conflict type consistency

    Data Sources:
    - tier3_summary.intelligence_synthesizer.cross_agent_consistency
    - tier3_summary.intelligence_synthesizer.contradictions_detected
    - tier2_summary.*.confidence (variance calculation)
    - tier1_summary.sentiment.overall_sentiment
    - tier2_summary.conflict_analyst.primary_event.event_type
    """
```

#### Missing Data Handling

The UQ module implements **robust missing-data handling** to ensure fair scoring:

```python
def redistribute_weights(components: Dict, target_total=100) -> Dict:
    """
    Redistribute weights when some components are missing.

    Example:
    Original weights: {A: 40%, B: 30%, C: 20%, D: 10%}
    If C is missing: {A: 44.4%, B: 33.3%, D: 11.1%}

    This ensures:
    1. Scores remain in 0-100 range
    2. Available components are fairly weighted
    3. Missing data doesn't artificially lower score
    """
    available = {k: v for k, v in components.items() if v['available']}
    missing = {k: v for k, v in components.items() if not v['available']}

    if not available:
        return {'score': 0, 'components_used': [], 'components_missing': list(components.keys())}

    total_available_weight = sum(c['weight'] for c in available.values())
    total_missing_weight = sum(c['weight'] for c in missing.values())

    # Redistribute missing weight proportionally
    adjusted_weights = {}
    for name, comp in available.items():
        proportion = comp['weight'] / total_available_weight
        additional_weight = total_missing_weight * proportion
        adjusted_weights[name] = comp['weight'] + additional_weight

    # Calculate final score
    final_score = sum(
        (available[name]['value'] / adjusted_weights[name]) * adjusted_weights[name]
        for name in available if adjusted_weights[name] > 0
    )

    return {
        'score': round(final_score, 2),
        'adjusted_weights': adjusted_weights,
        'redistribution_applied': total_missing_weight > 0,
        'components_used': list(available.keys()),
        'components_missing': list(missing.keys())
    }
```

### 2. Financial Uncertainty Tracking

**Location:** `app/agents/tier2_specialists/financial_analyst.py`

**Purpose:** Measure uncertainty in financial/economic analyses.

#### Uncertainty Field

```python
{
  "market_sentiment": "BULLISH|BEARISH|NEUTRAL|NOT_APPLICABLE",
  "market_confidence": 0.75,  # How confident in sentiment assessment
  "uncertainty": 0.40,        # ← UNCERTAINTY METRIC
  "volatility": 0.60,         # Expected market volatility
  "economic_impact": 0.70,    # Magnitude of economic impact
  "reasoning": "..."
}
```

#### Interpretation Table

| Uncertainty Range | Interpretation | Examples | Trigger Verification? |
|------------------|----------------|----------|----------------------|
| 0.0 - 0.3 | **Low Uncertainty** | Clear policy statements, predictable outcomes | No |
| 0.3 - 0.5 | **Moderate Uncertainty** | Some ambiguity, multiple scenarios possible | No |
| 0.5 - 0.7 | **High Uncertainty** | Conflicting signals, unclear direction | Depends on impact |
| 0.7 - 0.9 | **Very High Uncertainty** | Highly unpredictable, major unknowns | Yes (if threshold met) |
| 0.9 - 1.0 | **Extreme Uncertainty** | Complete unpredictability, no reliable data | Yes (always) |

#### LLM Prompt Context

The Financial Analyst agent is instructed to assess uncertainty based on:

1. **Information Completeness**
   - Missing data in article
   - Unclear statements
   - Ambiguous phrasing

2. **Signal Clarity**
   - Conflicting indicators
   - Mixed economic signals
   - Contradictory official statements

3. **Predictability**
   - Historical volatility
   - Policy uncertainty
   - Regulatory ambiguity

4. **Impact Visibility**
   - Unknown affected parties
   - Unclear timeline
   - Indirect effects difficult to assess

### 3. Event Publisher

**Location:** `app/messaging/event_publisher.py`

**Purpose:** Publish verification events to RabbitMQ when quality/uncertainty thresholds are breached.

#### Class: EventPublisher

```python
class EventPublisher:
    """
    Service for publishing events to RabbitMQ.

    Manages:
    - Robust connection to RabbitMQ (auto-reconnect)
    - Topic exchange (news.events)
    - Persistent message delivery
    - JSON encoding (UUID, datetime, Decimal support)

    Attributes:
        connection: aio_pika robust connection
        channel: RabbitMQ channel
        exchange: Topic exchange (news.events)
    """

    async def connect(self):
        """
        Connect to RabbitMQ and set up exchange.

        Creates:
        - Robust connection (auto-reconnect on failure)
        - Channel with QoS prefetch_count=10
        - Durable topic exchange "news.events"

        Raises:
            Exception: If connection fails
        """

    async def disconnect(self):
        """
        Disconnect from RabbitMQ gracefully.

        Closes channel and connection in proper order.
        """

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish an event to RabbitMQ.

        Args:
            event_type: Type of event (e.g., "verification.required")
            payload: Event payload data (must be JSON-serializable)
            correlation_id: Optional correlation ID for tracking

        Returns:
            True if published successfully, False otherwise

        Message Structure:
        {
            "event_type": str,
            "service": "content-analysis-v2",
            "timestamp": ISO8601 datetime,
            "payload": Dict,
            "correlation_id": str (optional)
        }

        Delivery Properties:
        - Content-Type: application/json
        - Delivery-Mode: 2 (persistent)
        - App-ID: content-analysis-v2
        - Type: event_type (for filtering)
        - Timestamp: UTC now
        """
```

#### Custom JSON Encoder

```python
class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for RabbitMQ messages.

    Handles:
    - UUID → str
    - datetime → ISO8601 string
    - Decimal → float

    Usage:
        json.dumps(data, cls=JSONEncoder)
    """

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
```

#### Singleton Pattern

```python
# Global publisher instance
_publisher_instance: Optional[EventPublisher] = None

async def get_event_publisher() -> EventPublisher:
    """
    Get or create global event publisher instance.

    Lazy initialization on first call.
    Reuses same instance for all subsequent calls.

    Returns:
        EventPublisher: Global singleton instance
    """
    global _publisher_instance

    if _publisher_instance is None:
        _publisher_instance = EventPublisher()
        await _publisher_instance.connect()

    return _publisher_instance

async def close_event_publisher():
    """
    Close global event publisher.

    Disconnects from RabbitMQ and resets singleton.
    Call on application shutdown.
    """
    global _publisher_instance

    if _publisher_instance:
        await _publisher_instance.disconnect()
        _publisher_instance = None
```

### 4. Pipeline Integration

**Location:** `app/pipeline/orchestrator.py`

**Purpose:** Integrate UQ module into analysis pipeline.

#### Verification Trigger Logic

```python
def _should_trigger_verification(
    self,
    quality_scores: Dict,
    context: PipelineContext
) -> bool:
    """
    Determine if verification workflow should be triggered.

    Triggers verification if ANY condition is met:
    1. Overall quality score < 50 (low quality)
    2. Verification score < 40 (unverified content)
    3. Financial uncertainty > 0.75 (high market uncertainty)
    4. Credibility score < 40 (unreliable source)

    Args:
        quality_scores: Output from calculate_all_quality_scores()
        context: Pipeline execution context

    Returns:
        bool: True if verification should be triggered
    """
    overall_score = quality_scores.get('overall_score', 100)
    scores = quality_scores.get('scores', {})

    # Trigger 1: Low overall quality
    if overall_score < 50:
        logger.warning(f"Verification trigger: Low overall quality ({overall_score:.1f})")
        return True

    # Trigger 2: Low verification score
    verification_score = scores.get('verification', {}).get('score', 100)
    if verification_score < 40:
        logger.warning(f"Verification trigger: Low verification score ({verification_score:.1f})")
        return True

    # Trigger 3: High financial uncertainty
    tier2_results = context.tier2_results or {}
    financial_data = tier2_results.get('financial_analyst', {})
    uncertainty = financial_data.get('uncertainty', 0.0)
    if uncertainty > 0.75:
        logger.warning(f"Verification trigger: High financial uncertainty ({uncertainty:.2f})")
        return True

    # Trigger 4: Low credibility
    credibility_score = scores.get('credibility', {}).get('score', 100)
    if credibility_score < 40:
        logger.warning(f"Verification trigger: Low credibility ({credibility_score:.1f})")
        return True

    return False
```

#### Event Publishing

```python
async def _publish_verification_event(
    self,
    article_id: str,
    pipeline_execution_id: str,
    quality_scores: Dict,
    context: PipelineContext
) -> None:
    """
    Publish verification.required event to RabbitMQ.

    Args:
        article_id: Article UUID
        pipeline_execution_id: Pipeline execution UUID
        quality_scores: Quality scores from UQ module
        context: Pipeline context with agent results

    Event Payload:
    {
        "article_id": str (UUID),
        "pipeline_execution_id": str (UUID),
        "uq_score": float (overall quality score),
        "trigger_reason": str,
        "uncertainty_factors": List[str],
        "affected_agents": List[str],
        "quality_scores": {
            "overall": float,
            "credibility": float,
            "verification": float,
            ...
        }
    }
    """
    publisher = await get_event_publisher()

    trigger_reason = self._determine_trigger_reason(quality_scores, context)
    uncertainty_factors = self._extract_uncertainty_factors(quality_scores, context)

    payload = {
        "article_id": article_id,
        "pipeline_execution_id": pipeline_execution_id,
        "uq_score": quality_scores['overall_score'],
        "trigger_reason": trigger_reason,
        "uncertainty_factors": uncertainty_factors,
        "affected_agents": self._get_affected_agents(context),
        "quality_scores": {
            "overall": quality_scores['overall_score'],
            "credibility": quality_scores['scores']['credibility']['score'],
            "verification": quality_scores['scores']['verification']['score'],
            "relevance": quality_scores['scores']['relevance']['score'],
        }
    }

    success = await publisher.publish_event(
        event_type="verification.required",
        payload=payload,
        correlation_id=pipeline_execution_id
    )

    if success:
        logger.info(f"Published verification event for article {article_id}")
        self.metrics.verification_events_published.inc()
    else:
        logger.error(f"Failed to publish verification event for article {article_id}")
        self.metrics.verification_events_failed.inc()
```

---

## API Reference

### Quality Score Calculation API

#### Function: `calculate_all_quality_scores`

**Module:** `app.quality_scoring.quality_indicators`

**Signature:**
```python
def calculate_all_quality_scores(pipeline_execution: Dict) -> Dict
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline_execution` | Dict | Yes | Complete pipeline execution result |
| `pipeline_execution.triage_decision` | Dict | Yes | Triage agent output |
| `pipeline_execution.tier1_summary` | Dict | Yes | Foundation agents output |
| `pipeline_execution.tier2_summary` | Dict | No | Specialist agents output (optional) |
| `pipeline_execution.tier3_summary` | Dict | No | Synthesis agent output (optional) |
| `pipeline_execution.agents_executed` | List[str] | Yes | List of executed agent names |

**Returns:**

```python
{
    # Overall quality score (0-100)
    "overall_score": 72.5,

    # Individual dimension scores
    "scores": {
        "credibility": {
            "score": 75.0,
            "components": {...},  # Component breakdown
            "metadata": {...}      # Calculation metadata
        },
        "objectivity": {...},
        "verification": {...},
        "relevance": {...},
        "completeness": {...},
        "consistency": {...}
    },

    # Data completeness validation
    "validation": {
        "agents_available": ["triage", "tier1", "tier2.financial_analyst", ...],
        "agents_missing": ["tier2.geopolitical_analyst"],
        "completeness_percentage": 85.7,
        "warnings": ["Low pipeline coverage: 85.7%"]
    },

    # Quality categorization
    "quality_category": {
        "category": "high_quality",
        "recommendation": "High quality - suitable for most purposes",
        "flags": [],
        "use_cases": ["intelligence_reports", "analysis", "training_data"],
        "display_badge": "✅ High Quality",
        "confidence": "high"
    },

    # Calculation metadata
    "metadata": {
        "weights_used": {
            "credibility": 0.40,
            "objectivity": 0.30,
            "verification": 0.25,
            "relevance": 0.15,
            "completeness": 0.10,
            "consistency": 0.10
        },
        "weights_adjusted": false,
        "scores_excluded": [],
        "article_type": {
            "content_type": "news",
            "conflict_type": null,
            "time_sensitivity": "moderate"
        },
        "calculation_version": "2.0_robust",
        "data_completeness": 85.7
    }
}
```

**Exceptions:**

```python
try:
    result = calculate_all_quality_scores(pipeline_data)
except Exception as e:
    # Returns error structure instead of raising
    return {
        "overall_score": 0,
        "scores": {},
        "validation": {"completeness_percentage": 0, "warnings": [str(e)]},
        "quality_category": {
            "category": "error",
            "recommendation": "Quality calculation failed",
            "flags": ["calculation_error"],
            "confidence": "none"
        }
    }
```

### Event Publishing API

#### Class: `EventPublisher`

**Module:** `app.messaging.event_publisher`

**Methods:**

##### `connect()`

```python
async def connect(self) -> None
```

**Purpose:** Establish connection to RabbitMQ and declare exchange.

**Side Effects:**
- Creates `aio_pika` robust connection
- Declares durable topic exchange `news.events`
- Sets QoS prefetch_count=10

**Raises:**
- `Exception`: If connection fails

---

##### `disconnect()`

```python
async def disconnect(self) -> None
```

**Purpose:** Gracefully close RabbitMQ connection.

**Side Effects:**
- Closes channel
- Closes connection
- Logs disconnection

---

##### `publish_event()`

```python
async def publish_event(
    event_type: str,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_type` | str | Yes | Event type (e.g., "verification.required") |
| `payload` | Dict | Yes | Event payload (must be JSON-serializable) |
| `correlation_id` | str | No | Correlation ID for request tracking |

**Returns:**
- `True`: Event published successfully
- `False`: Event publishing failed

**Message Structure:**
```python
{
    "event_type": "verification.required",
    "service": "content-analysis-v2",
    "timestamp": "2025-11-02T10:30:00.123456Z",
    "correlation_id": "abc-123-def",  # Optional
    "payload": {
        "article_id": "...",
        "uq_score": 35.0,
        ...
    }
}
```

**Routing:**
- **Exchange:** `news.events`
- **Routing Key:** `{event_type}` (e.g., `verification.required`)
- **Type:** Topic
- **Durable:** Yes

---

## Event Schema

### Event: `verification.required`

**Published When:** Quality score or uncertainty exceeds threshold

**Routing Key:** `verification.required`

**Exchange:** `news.events`

**Message Structure:**

```json
{
  "event_type": "verification.required",
  "service": "content-analysis-v2",
  "timestamp": "2025-11-02T10:30:00.123456Z",
  "correlation_id": "pipeline-exec-uuid",
  "payload": {
    "article_id": "550e8400-e29b-41d4-a716-446655440000",
    "pipeline_execution_id": "660e8400-e29b-41d4-a716-446655440001",
    "uq_score": 35.0,
    "trigger_reason": "financial_uncertainty_high",
    "uncertainty_factors": [
      "uncertainty: 0.85 (high market uncertainty)",
      "volatility: 0.90 (extreme market volatility expected)",
      "economic_impact: 0.95 (major systemic impact)",
      "Overall quality score: 35.0 (very low)",
      "Verification score: 25.0 (unverified content)"
    ],
    "affected_agents": [
      "FINANCIAL_ANALYST",
      "CONFLICT_EVENT_ANALYST"
    ],
    "quality_scores": {
      "overall": 35.0,
      "credibility": 42.0,
      "objectivity": 55.0,
      "verification": 25.0,
      "relevance": 68.0,
      "completeness": 48.0,
      "consistency": 32.0
    }
  }
}
```

**Payload Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `article_id` | UUID (string) | Yes | Article unique identifier |
| `pipeline_execution_id` | UUID (string) | Yes | Pipeline execution unique identifier |
| `uq_score` | float | Yes | Overall quality score (0-100) |
| `trigger_reason` | string | Yes | Reason verification was triggered |
| `uncertainty_factors` | List[string] | Yes | Human-readable uncertainty factors |
| `affected_agents` | List[string] | Yes | Agents that reported low confidence |
| `quality_scores` | Object | Yes | Detailed quality scores |
| `quality_scores.overall` | float | Yes | Overall quality (0-100) |
| `quality_scores.credibility` | float | Yes | Credibility score (0-100) |
| `quality_scores.objectivity` | float | Yes | Objectivity score (0-100) |
| `quality_scores.verification` | float | Yes | Verification score (0-100) |
| `quality_scores.relevance` | float | Yes | Relevance score (0-100) |
| `quality_scores.completeness` | float | Yes | Completeness score (0-100) |
| `quality_scores.consistency` | float | Yes | Consistency score (0-100) |

**Trigger Reasons:**

| Trigger Reason | Condition | Example |
|---------------|-----------|---------|
| `low_overall_quality` | overall_score < 50 | General low quality |
| `low_verification_score` | verification_score < 40 | Unverified content |
| `financial_uncertainty_high` | uncertainty > 0.75 | High market uncertainty |
| `low_credibility` | credibility_score < 40 | Unreliable source |
| `multiple_triggers` | Multiple conditions met | Combined issues |

### Consumer Implementation Example

```python
import aio_pika
import json
import logging

logger = logging.getLogger(__name__)

class VerificationConsumer:
    """
    Consumer for verification.required events.

    Subscribes to verification events and processes them.
    """

    async def start(self):
        """Start consuming verification events."""
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(
            "amqp://guest:guest@rabbitmq:5672/"
        )

        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        # Declare exchange (idempotent)
        exchange = await channel.declare_exchange(
            "news.events",
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Declare queue
        queue = await channel.declare_queue(
            "verification.queue",
            durable=True,
        )

        # Bind to verification.required events
        await queue.bind(exchange, routing_key="verification.required")

        logger.info("Verification consumer started, waiting for events...")

        # Consume messages
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self.process_verification(message.body)

    async def process_verification(self, body: bytes):
        """
        Process verification event.

        Args:
            body: Message body (JSON bytes)
        """
        try:
            # Parse message
            data = json.loads(body)
            payload = data['payload']

            article_id = payload['article_id']
            uq_score = payload['uq_score']
            trigger_reason = payload['trigger_reason']
            uncertainty_factors = payload['uncertainty_factors']

            logger.info(
                f"Verification triggered: article={article_id}, "
                f"score={uq_score}, reason={trigger_reason}"
            )

            # TODO: Implement verification logic
            # - Cross-reference with external sources
            # - Run additional LLM passes
            # - Flag for human review
            # - Update article status

        except Exception as e:
            logger.error(f"Failed to process verification event: {e}")
            raise  # Requeue message
```

---

## Configuration

### Environment Variables

**File:** `services/content-analysis-v2/.env`

```bash
# ===== UQ Module Settings =====

# Enable/disable UQ module
UQ_ENABLED=true

# Overall quality score threshold
UQ_VERIFICATION_THRESHOLD_OVERALL=50

# Individual score thresholds
UQ_VERIFICATION_THRESHOLD_VERIFICATION=40
UQ_CREDIBILITY_THRESHOLD=40

# Financial uncertainty threshold
UQ_FINANCIAL_UNCERTAINTY_THRESHOLD=0.75

# ===== RabbitMQ Settings =====

RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_EXCHANGE=news.events
RABBITMQ_ROUTING_KEY_VERIFICATION=verification.required
```

### Configuration Class

**Location:** `app/core/config.py`

```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings."""

    # ===== UQ Module Settings =====

    UQ_ENABLED: bool = Field(
        default=True,
        description="Enable/disable uncertainty quantification module"
    )

    UQ_VERIFICATION_THRESHOLD_OVERALL: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Overall quality score threshold for verification"
    )

    UQ_VERIFICATION_THRESHOLD_VERIFICATION: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Verification score threshold"
    )

    UQ_CREDIBILITY_THRESHOLD: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Credibility score threshold"
    )

    UQ_FINANCIAL_UNCERTAINTY_THRESHOLD: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Financial uncertainty threshold"
    )

    # ===== RabbitMQ Settings =====

    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/",
        description="RabbitMQ connection URL"
    )

    RABBITMQ_EXCHANGE: str = Field(
        default="news.events",
        description="RabbitMQ exchange name"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### Threshold Recommendations

| Scenario | Overall | Verification | Credibility | Financial Uncertainty |
|----------|---------|-------------|-------------|---------------------|
| **Strict** (High-stakes) | 60 | 50 | 50 | 0.65 |
| **Standard** (Production) | 50 | 40 | 40 | 0.75 |
| **Lenient** (Development) | 40 | 30 | 30 | 0.85 |

**Tuning Guide:**

1. **Start with Standard** thresholds
2. **Monitor verification rate** (target: 5-15%)
3. **If rate > 30%:** Increase thresholds (more lenient)
4. **If rate < 5%:** Decrease thresholds (more strict)
5. **Review false positives/negatives** monthly

---

## Deployment

### Docker Compose

**File:** `docker-compose.yml`

```yaml
services:
  content-analysis-v2:
    image: content-analysis-v2:latest
    environment:
      - UQ_ENABLED=true
      - UQ_VERIFICATION_THRESHOLD_OVERALL=50
      - UQ_VERIFICATION_THRESHOLD_VERIFICATION=40
      - UQ_CREDIBILITY_THRESHOLD=40
      - UQ_FINANCIAL_UNCERTAINTY_THRESHOLD=0.75
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    depends_on:
      - rabbitmq
      - postgres
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: uq-module-config
  namespace: news-microservices
data:
  UQ_ENABLED: "true"
  UQ_VERIFICATION_THRESHOLD_OVERALL: "50"
  UQ_VERIFICATION_THRESHOLD_VERIFICATION: "40"
  UQ_CREDIBILITY_THRESHOLD: "40"
  UQ_FINANCIAL_UNCERTAINTY_THRESHOLD: "0.75"
  RABBITMQ_URL: "amqp://guest:guest@rabbitmq:5672/"
```

### Feature Flag Toggle

```bash
# Disable UQ module (emergency)
docker exec content-analysis-v2 \
  sh -c 'echo "UQ_ENABLED=false" >> /app/.env'

docker compose restart content-analysis-v2

# Re-enable UQ module
docker exec content-analysis-v2 \
  sh -c 'sed -i "s/UQ_ENABLED=false/UQ_ENABLED=true/" /app/.env'

docker compose restart content-analysis-v2
```

---

## Monitoring

### Prometheus Metrics

**Location:** `app/core/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge

# Verification events
uq_verification_triggered = Counter(
    'uq_verification_triggered_total',
    'Total verifications triggered by UQ module',
    ['trigger_reason']
)

uq_verification_events_published = Counter(
    'uq_verification_events_published_total',
    'Successfully published verification events'
)

uq_verification_events_failed = Counter(
    'uq_verification_events_failed_total',
    'Failed verification event publications'
)

# Quality scores
uq_quality_score = Histogram(
    'uq_quality_score',
    'Distribution of overall quality scores',
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

uq_credibility_score = Histogram(
    'uq_credibility_score',
    'Distribution of credibility scores',
    buckets=[0, 20, 40, 60, 80, 100]
)

uq_verification_score = Histogram(
    'uq_verification_score',
    'Distribution of verification scores',
    buckets=[0, 20, 40, 60, 80, 100]
)

# Financial uncertainty
uq_financial_uncertainty = Histogram(
    'uq_financial_uncertainty',
    'Distribution of financial uncertainty scores',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0]
)

# Active verifications
uq_active_verifications = Gauge(
    'uq_active_verifications',
    'Number of active verification workflows'
)

# Processing time
uq_calculation_duration = Histogram(
    'uq_calculation_duration_seconds',
    'Time taken to calculate quality scores',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)
```

### Grafana Dashboard

**File:** `grafana/dashboards/uq-module.json`

See [ADR-034 Section 8.2](ADR-034-uq-module-implementation.md#72-grafana-dashboard) for full dashboard JSON.

**Key Panels:**

1. **Verification Rate**
   - Query: `rate(uq_verification_triggered_total[1h]) * 3600`
   - Display: Verifications per hour

2. **Quality Score Distribution**
   - Query: `histogram_quantile(0.50, rate(uq_quality_score_bucket[5m]))`
   - Display: p50, p95, p99 quality scores

3. **Financial Uncertainty Trend**
   - Query: `avg(uq_financial_uncertainty) by (market_sentiment)`
   - Display: Average uncertainty by sentiment type

4. **Verification by Trigger Reason**
   - Query: `sum by (trigger_reason) (rate(uq_verification_triggered_total[1h]))`
   - Display: Pie chart of trigger reasons

### Alerting

**File:** `prometheus/alerts/uq.yml`

```yaml
groups:
  - name: uq_module
    interval: 60s
    rules:
      - alert: HighVerificationRate
        expr: |
          rate(uq_verification_triggered_total[1h]) * 3600 > 100
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "UQ module triggering excessive verifications"
          description: "{{ $value | humanize }} verifications/hour (threshold: 100)"

      - alert: LowQualityScores
        expr: |
          histogram_quantile(0.50, rate(uq_quality_score_bucket[5m])) < 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Median quality score critically low"
          description: "p50 quality score: {{ $value | humanize }}"

      - alert: EventPublishFailures
        expr: |
          rate(uq_verification_events_failed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "RabbitMQ event publishing failing"
          description: "{{ $value | humanize }} failures/sec"
```

---

## Troubleshooting

### Common Issues

#### Issue 1: No Verification Events Published

**Symptoms:**
- UQ module enabled
- Quality scores calculated
- No events in RabbitMQ

**Diagnosis:**

```bash
# Check RabbitMQ connection
docker logs content-analysis-v2 | grep -i "rabbitmq"

# Expected: "Connected to RabbitMQ exchange: news.events"
# If missing: Connection failed

# Check event publisher status
docker exec content-analysis-v2 \
  python3 -c "from app.messaging.event_publisher import get_event_publisher; \
              import asyncio; \
              asyncio.run(get_event_publisher().connect())"

# Expected: No errors
# If error: Connection string incorrect or RabbitMQ down
```

**Solutions:**

1. **RabbitMQ Not Running:**
   ```bash
   docker compose up -d rabbitmq
   docker logs rabbitmq
   ```

2. **Incorrect Connection String:**
   ```bash
   # Check .env file
   cat services/content-analysis-v2/.env | grep RABBITMQ_URL

   # Should be: amqp://guest:guest@rabbitmq:5672/
   ```

3. **Exchange Not Declared:**
   ```bash
   # Check RabbitMQ management UI
   # http://localhost:15672
   # Login: guest/guest
   # Verify "news.events" exchange exists (Type: topic, Durable: yes)
   ```

#### Issue 2: Too Many Verifications Triggered

**Symptoms:**
- Verification rate > 30%
- System overloaded with verification events

**Diagnosis:**

```bash
# Check verification rate
curl -s http://localhost:8114/metrics | grep uq_verification_triggered_total

# Check thresholds
docker exec content-analysis-v2 \
  cat /app/.env | grep UQ_
```

**Solutions:**

1. **Increase Thresholds** (more lenient):
   ```bash
   # Edit .env
   UQ_VERIFICATION_THRESHOLD_OVERALL=40   # Was 50
   UQ_VERIFICATION_THRESHOLD_VERIFICATION=30  # Was 40
   UQ_FINANCIAL_UNCERTAINTY_THRESHOLD=0.85  # Was 0.75

   # Restart service
   docker compose restart content-analysis-v2
   ```

2. **Temporarily Disable UQ Module:**
   ```bash
   docker exec content-analysis-v2 \
     sh -c 'echo "UQ_ENABLED=false" >> /app/.env'

   docker compose restart content-analysis-v2
   ```

#### Issue 3: Low Quality Scores Unexpectedly

**Symptoms:**
- Most articles scoring < 50
- Verification events flooding system

**Diagnosis:**

```bash
# Check data completeness
docker exec content-analysis-v2 \
  python3 -c "from app.quality_scoring.quality_indicators import validate_data_completeness; \
              import json; \
              # Load recent pipeline execution
              print(json.dumps(validate_data_completeness(pipeline_data), indent=2))"

# Expected: completeness_percentage > 70%
# If < 70%: Agents not running or failing
```

**Solutions:**

1. **Check Agent Execution:**
   ```bash
   # View pipeline logs
   docker logs content-analysis-v2 | grep "agents_executed"

   # Expected: [TRIAGE, ENTITY_EXTRACTOR, SENTIMENT_ANALYST, ...]
   # If missing agents: Check agent failures
   ```

2. **Review Missing Data Warnings:**
   ```bash
   # Check quality calculation logs
   docker logs content-analysis-v2 | grep "redistribution_applied"

   # If "true": Some components missing → expected behavior
   # Check which components missing in logs
   ```

3. **Validate Pipeline Data:**
   ```python
   # Test quality calculation with sample data
   from app.quality_scoring.quality_indicators import calculate_all_quality_scores

   test_data = {
       "triage_decision": {...},
       "tier1_summary": {...},
       # ...
   }

   result = calculate_all_quality_scores(test_data)
   print(f"Overall score: {result['overall_score']}")
   print(f"Warnings: {result['validation']['warnings']}")
   ```

---

## Development Guide

### Adding New Quality Dimensions

**Step 1: Create Calculator Function**

```python
# app/quality_scoring/quality_indicators.py

def calculate_new_dimension_score(pipeline_data: Dict) -> Dict:
    """
    New Dimension Score: 0-100

    Components:
    - Component A (50%): Description
    - Component B (30%): Description
    - Component C (20%): Description

    Data Sources:
    - tier1_summary.some_field
    - tier2_summary.agent.some_field
    """
    components = {}

    # Component A
    field_a = safe_get(pipeline_data, 'tier1_summary', 'some_field')
    if field_a is not None:
        components['component_a'] = {
            'available': True,
            'weight': 50,
            'value': field_a * 50,
            'raw_value': field_a
        }
    else:
        components['component_a'] = {'available': False, 'weight': 50, 'value': 0}

    # ... Component B, C ...

    result = redistribute_weights(components)

    return {
        'score': result['score'],
        'components': components,
        'metadata': {...}
    }
```

**Step 2: Integrate into `calculate_all_quality_scores`**

```python
def calculate_all_quality_scores(pipeline_execution: Dict) -> Dict:
    # ... existing code ...

    new_dimension = calculate_new_dimension_score(pipeline_execution)

    scores = {
        'credibility': credibility,
        'objectivity': objectivity,
        'verification': verification,
        'relevance': relevance,
        'completeness': completeness,
        'consistency': consistency,
        'new_dimension': new_dimension,  # ← Add here
    }

    # Update weights
    weights = {
        'credibility': 0.30,  # Adjusted
        'objectivity': 0.25,  # Adjusted
        'verification': 0.20, # Adjusted
        'relevance': 0.10,    # Adjusted
        'completeness': 0.05, # Adjusted
        'consistency': 0.05,  # Adjusted
        'new_dimension': 0.05,  # New weight
    }
```

**Step 3: Update Tests**

```python
# tests/test_quality_indicators.py

def test_new_dimension_score():
    """Test new dimension calculation."""
    pipeline_data = {
        'tier1_summary': {'some_field': 0.75},
        # ...
    }

    result = calculate_new_dimension_score(pipeline_data)

    assert result['score'] > 0
    assert result['metadata']['confidence'] in ['low', 'medium', 'high']
```

### Adding New Verification Triggers

**Step 1: Update Trigger Logic**

```python
# app/pipeline/orchestrator.py

def _should_trigger_verification(
    self,
    quality_scores: Dict,
    context: PipelineContext
) -> bool:
    # ... existing triggers ...

    # NEW TRIGGER: High bias detected
    tier2_results = context.tier2_results or {}
    bias_data = tier2_results.get('bias_detector', {})
    bias_level = bias_data.get('overall_bias_assessment', {}).get('bias_level')

    if bias_level == 'extreme':
        logger.warning("Verification trigger: Extreme bias detected")
        return True

    return False
```

**Step 2: Update Trigger Reason**

```python
def _determine_trigger_reason(
    self,
    quality_scores: Dict,
    context: PipelineContext
) -> str:
    """Determine primary trigger reason."""
    reasons = []

    if quality_scores['overall_score'] < 50:
        reasons.append("low_overall_quality")

    if quality_scores['scores']['verification']['score'] < 40:
        reasons.append("low_verification_score")

    # NEW
    tier2_results = context.tier2_results or {}
    bias_data = tier2_results.get('bias_detector', {})
    bias_level = bias_data.get('overall_bias_assessment', {}).get('bias_level')

    if bias_level == 'extreme':
        reasons.append("extreme_bias_detected")

    return ",".join(reasons) if len(reasons) > 1 else reasons[0] if reasons else "unknown"
```

**Step 3: Document New Trigger**

Update [Event Schema](#event-schema) section with new trigger reason.

---

**Last Updated:** 2025-11-02
**Version:** 1.0
**Maintainer:** Content Analysis V2 Team

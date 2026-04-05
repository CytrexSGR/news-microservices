# Content Analysis v2 - Pipeline Logic & Agent Selection

**Last Updated:** 2025-10-27
**Status:** Production
**Version:** 2.0

## Overview

This document explains the decision logic for agent selection in the Content Analysis v2 pipeline. The system uses a multi-tier architecture with conditional agent execution based on article relevance and content type.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ARTICLE INGESTION                         │
│                  (article.created event)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   STAGE 0: TRIAGE                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ TRIAGE Agent (Relevance Scorer)                       │  │
│  │ • Calculates PriorityScore (0-100)                    │  │
│  │ • Identifies primary topics                           │  │
│  │ • Recommends specialist agents                        │  │
│  │ • Categorizes article (GEOPOLITICS, ECONOMY, etc.)   │  │
│  └───────────────────────────────────────────────────────┘  │
│  Output: PriorityScore, Category, Topics                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │  Score >= 60?         │
                └───────────┬───────────┘
                   YES │         │ NO
                       │         └──────► SKIP Tier 2 & 3
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 1: FOUNDATION (Tier 1)                    │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │ ENTITY_EXTRACTOR    │  │ SUMMARY_GENERATOR           │  │
│  │ • Extract entities  │  │ • Generate article summary  │  │
│  │ • Locations, orgs   │  │ • Key points                │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
│  Output: Entities, Summary                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           STAGE 2: SPECIALISTS (Tier 2)                      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ALWAYS-RUN AGENTS (Universal)                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ • SENTIMENT_ANALYST                                   │  │
│  │   - Sentiment score, emotional tone                   │  │
│  │   - Runs on ALL articles (Score >= 60)               │  │
│  │                                                        │  │
│  │ • BIAS_DETECTOR                                       │  │
│  │   - Political bias, objectivity score                │  │
│  │   - Runs on ALL articles (Score >= 60)               │  │
│  │                                                        │  │
│  │ • TOPIC_CLASSIFIER                                    │  │
│  │   - Detailed multi-label topic classification        │  │
│  │   - Hierarchical topics with keywords                │  │
│  │   - Runs on ALL articles (Score >= 60)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TOPIC-BASED AGENTS (Conditional)                      │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ • CONFLICT_EVENT_ANALYST                              │  │
│  │   Triggers: ["conflict", "war", "military"]          │  │
│  │   - Conflict analysis, parties involved              │  │
│  │                                                        │  │
│  │ • GEOPOLITICAL_ANALYST                                │  │
│  │   Triggers: ["conflict", "war", "military",          │  │
│  │              "politics", "government"]                │  │
│  │   - Geopolitical implications, regional impact       │  │
│  │                                                        │  │
│  │ • FINANCIAL_ANALYST                                   │  │
│  │   Triggers: ["finance", "economy", "markets"]        │  │
│  │   - Economic analysis, market impact                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  Output: Sentiment, Bias, Topics, Specialist Analysis        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 3: SYNTHESIS (Tier 3)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ INTELLIGENCE_SYNTHESIZER                               │  │
│  │ • Combines all agent outputs                           │  │
│  │ • Creates intelligence summary                         │  │
│  │ • Strategic relevance assessment                       │  │
│  └───────────────────────────────────────────────────────┘  │
│  Output: Intelligence Summary, Key Findings                  │
└─────────────────────────────────────────────────────────────┘
```

## Triage Stage - Score Calculation

### Formula

```python
# Component Scores (0-100)
ImpactScore    = Geopolitical/economic significance
EntityScore    = Importance of mentioned entities
SourceScore    = Source credibility

# Base Calculation
BaseScore = ImpactScore + EntityScore + SourceScore

# Urgency Multiplier (0.5-3.0)
UrgencyMultiplier = Time sensitivity factor

# Final Score
FinalScore = BaseScore × UrgencyMultiplier
PriorityScore = min(100, int((FinalScore / 400) * 100))
```

### Score Ranges

| Priority Score | Action | Example |
|----------------|--------|---------|
| 85-100 | Run Tier 2 | Wars, terrorism, central bank decisions, bank collapses |
| 70-84 | Run Tier 2 | Regional conflicts, OPEC policy, government shutdowns |
| 60-69 | Run Tier 2 | National politics, sector-wide trends |
| 50-59 | **Skip Tier 2** | Large company announcements, tech breakthroughs |
| 0-49 | **Skip Tier 2** | Entertainment, sports, lifestyle |

**Threshold:** `PriorityScore >= 60` triggers Tier 2 execution

### Example Calculation (Sudan Article)

```python
Article: "Sudan's RSF storms el-Fasher after UAE shuts down talks"

ImpactScore:         80  # War event, high systemic significance
EntityScore:         85  # RSF, SAF, UAE - major geopolitical actors
SourceScore:         20  # Unknown source
BaseScore:          185  # 80 + 85 + 20
UrgencyMultiplier:  3.0  # Breaking news, developing crisis
FinalScore:       555.0  # 185 × 3.0
PriorityScore:      100  # min(100, (555/400) × 100) = capped at 100
```

**Decision:** ✅ Run Tier 2 (Score = 100)

## Agent Selection Logic

### 1. All Agents Run (Current Strategy)

**ALL Tier 2 agents execute on every article that passes triage (Score >= 60):**

```python
always_run_tier2_agents = [
    "SENTIMENT_ANALYST",        # Emotional tone, sentiment score
    "BIAS_DETECTOR",            # Political bias, objectivity
    "TOPIC_CLASSIFIER",         # Multi-label topic classification
    "FINANCIAL_ANALYST",        # Economic/financial analysis
    "GEOPOLITICAL_ANALYST",     # Geopolitical implications
    "CONFLICT_EVENT_ANALYST",   # Conflict/security analysis
]
```

**Rationale:**
- **Cross-Domain Relevance:** Articles often span multiple domains (finance + geopolitics)
- **No False Negatives:** Topic mapping can miss nuanced connections
- **Knowledge Graph Feeding:** Complete data collection for graph enrichment
- **Data-Driven Future:** Use actual results to optimize later
- **Cost Acceptable:** ~$0.0047/article for complete analysis spectrum

### 2. Selection Algorithm (Simplified)

```python
if should_run_tier2:
    # Run all enabled agents - no topic filtering
    recommended_agents = list(always_run_tier2_agents)
```

**Topic mapping disabled** - Was too restrictive and missed cross-domain relevance.

## Example: Sudan Article Analysis

### Input

```json
{
  "title": "Sudan's RSF storms el-Fasher after UAE shuts down talks",
  "content": "Sudan's paramilitary Rapid Support Forces (RSF) has stormed...",
  "source": "Middle East Eye"
}
```

### Triage Output

```json
{
  "PriorityScore": 100,
  "category": "GEOPOLITICS_SECURITY",
  "primary_topics": ["conflict", "war", "diplomacy"],
  "scoring_justification": {
    "ImpactScore": 80,
    "EntityScore": 85,
    "SourceScore": 20,
    "BaseScore": 185,
    "UrgencyMultiplier": 3.0,
    "FinalScore": 555.0
  }
}
```

### Agent Selection

**All agents run (no topic filtering):**
```
✅ SENTIMENT_ANALYST
✅ BIAS_DETECTOR
✅ TOPIC_CLASSIFIER
✅ FINANCIAL_ANALYST
✅ GEOPOLITICAL_ANALYST
✅ CONFLICT_EVENT_ANALYST
```

**Rationale:** Article has geopolitical, conflict, and diplomatic dimensions. All agents provide valuable analysis regardless of primary topics.

### Execution Flow

```
TRIAGE (100ms, $0.0005)
  ↓
TIER 1 - Parallel
  → ENTITY_EXTRACTOR (2500ms, $0.0008)
  → SUMMARY_GENERATOR (2200ms, $0.0007)
  ↓
TIER 2 - Parallel (max 5 concurrent)
  → SENTIMENT_ANALYST (1800ms, $0.0004)
  → BIAS_DETECTOR (1900ms, $0.0005)
  → TOPIC_CLASSIFIER (2100ms, $0.0006)
  → FINANCIAL_ANALYST (2500ms, $0.0010)
  → CONFLICT_EVENT_ANALYST (3200ms, $0.0012)
  → GEOPOLITICAL_ANALYST (2800ms, $0.0010)
  ↓
TIER 3
  → INTELLIGENCE_SYNTHESIZER (4500ms, $0.0015)

Total: 20.8s, $0.0082
```

## Configuration

### Worker Configuration

Location: `services/content-analysis-v2/app/workers/pipeline_worker.py`

```python
config = PipelineConfig(
    relevance_threshold=0.6,  # PriorityScore >= 60 to run Tier 2

    enabled_tier1_agents=[
        "ENTITY_EXTRACTOR",
        "SUMMARY_GENERATOR",
    ],

    enabled_tier2_agents=[
        "SENTIMENT_ANALYST",
        "TOPIC_CLASSIFIER",
        "FINANCIAL_ANALYST",
        "GEOPOLITICAL_ANALYST",
        "CONFLICT_EVENT_ANALYST",
        "BIAS_DETECTOR",
    ],

    # ALL Tier 2 agents run when Triage passes (Score >= 60)
    # Topic mapping disabled for complete data collection
    always_run_tier2_agents=[
        "SENTIMENT_ANALYST",
        "BIAS_DETECTOR",
        "TOPIC_CLASSIFIER",
        "FINANCIAL_ANALYST",
        "GEOPOLITICAL_ANALYST",
        "CONFLICT_EVENT_ANALYST",
    ],

    parallel_tier2=True,
    max_concurrent_agents=5,
    skip_tier2_on_low_relevance=True,
)
```

## Cost Analysis

### Per-Article Costs (Typical)

| Agent | Cost (USD) | When Runs |
|-------|------------|-----------|
| TRIAGE | $0.0005 | Always |
| ENTITY_EXTRACTOR | $0.0008 | Score >= 60 |
| SUMMARY_GENERATOR | $0.0007 | Score >= 60 |
| SENTIMENT_ANALYST | $0.0004 | Score >= 60 |
| BIAS_DETECTOR | $0.0005 | Score >= 60 |
| TOPIC_CLASSIFIER | $0.0006 | Score >= 60 |
| CONFLICT_EVENT_ANALYST | $0.0012 | Topics: conflict/war/military |
| GEOPOLITICAL_ANALYST | $0.0010 | Topics: conflict/war/politics |
| FINANCIAL_ANALYST | $0.0010 | Topics: finance/economy |
| INTELLIGENCE_SYNTHESIZER | $0.0015 | Score >= 60 |

### Cost Scenarios

**Low Priority Article (Score < 60):**
```
TRIAGE only: $0.0005
Estimated savings: $0.0040 (Tier 2 skipped)
```

**High Priority Article (Score >= 60, No Specialists):**
```
TRIAGE + TIER1 + Always-Run Agents + SYNTHESIS
$0.0005 + $0.0015 + $0.0015 + $0.0015 = $0.0050
```

**High Priority Article (Score >= 60, All Agents):**
```
TRIAGE + TIER1 + All Agents + SYNTHESIS
$0.0005 + $0.0015 + $0.0047 + $0.0015 = $0.0082
```

**Daily Estimates (100 articles):**
- 40% low priority (skip Tier 2): $0.02
- 60% high priority (run specialists): $0.48
- **Total: ~$0.50/day = $15/month**

## Performance Characteristics

### Execution Times (Typical)

| Stage | Time (ms) | Parallelization |
|-------|-----------|-----------------|
| TRIAGE | 100-300 | Sequential |
| TIER 1 | 2000-3000 | Parallel (2 agents) |
| TIER 2 | 1500-3500 | Parallel (max 5 concurrent) |
| TIER 3 | 3000-5000 | Sequential |
| **Total** | **8-15 seconds** | Mixed |

### Bottlenecks

1. **LLM API Latency:** Primary bottleneck (80% of time)
2. **Tier 3 Synthesis:** Sequential, waits for all Tier 2 results
3. **Database Writes:** Minimal impact (<5%)

### Optimization Strategies

- ✅ Parallel execution of independent agents
- ✅ Conditional execution based on relevance
- ✅ Caching of agent results (24h TTL)
- ✅ Topic-based agent selection (avoid unnecessary analysis)
- 🔄 Future: Consider streaming synthesis (incremental results)

## Decision Log

### 2025-10-27: Always-Run Agents Expansion (Phase 1)

**Decision:** Move SENTIMENT_ANALYST, BIAS_DETECTOR, and TOPIC_CLASSIFIER to always-run category

**Rationale:**
1. **Topic Mapping Too Restrictive:** Original logic skipped these agents on many high-value articles
2. **Frontend Dependency:** UI requires consistent sentiment/bias data
3. **Universal Relevance:** All important articles (Score >= 60) have sentiment and bias
4. **Low Cost Impact:** +$0.0015/article is justified by data completeness
5. **User Request:** Explicit requirement to analyze sentiment/bias consistency

**Impact:**
- Before: 2 agents on conflict articles (CONFLICT, GEOPOLITICAL)
- After: 5 agents on conflict articles (+SENTIMENT, +BIAS, +TOPIC_CLASSIFIER)
- Cost increase: ~$0.0015/article
- Data completeness: 100% (no missing sentiment/bias)

**Example:**
```
Sudan article (Score=100, Topics=[conflict, war])
Before: CONFLICT_EVENT_ANALYST, GEOPOLITICAL_ANALYST
After:  SENTIMENT_ANALYST, BIAS_DETECTOR, TOPIC_CLASSIFIER,
        CONFLICT_EVENT_ANALYST, GEOPOLITICAL_ANALYST
```

### 2025-10-27: All Agents Always-Run (Phase 2 - Data Feeding)

**Decision:** Disable topic-based agent selection - ALL Tier 2 agents run when Score >= 60

**Rationale:**
1. **Cross-Domain Relevance:** Many articles have multiple dimensions
   - Example: US-China trade deal = Financial + Geopolitical + Conflict implications
   - Topic mapping missed geopolitical analysis on financial articles
2. **Knowledge Graph Feeding:** Need complete data for graph enrichment
3. **Data-Driven Optimization:** Will use actual analysis results to determine optimal agent selection later
4. **Eliminate False Negatives:** Topic classifier can miss nuanced connections

**Impact:**
- **Cost:** ~$0.0047/article for all 6 Tier 2 agents
- **Total per article (Score >= 60):** ~$0.0082 (TRIAGE + TIER1 + TIER2 + TIER3)
- **Daily estimate (100 articles, 60% high priority):** ~$0.50/day = $15/month
- **Data completeness:** 100% - every important article gets full analysis spectrum

**Example:**
```
ASEAN Summit article (Score=85, Topics=[finance, economy, markets])

Before (Topic Mapping):
✅ SENTIMENT_ANALYST
✅ BIAS_DETECTOR
✅ TOPIC_CLASSIFIER
✅ FINANCIAL_ANALYST
❌ GEOPOLITICAL_ANALYST (skipped - no politics topic)
❌ CONFLICT_EVENT_ANALYST (skipped - no conflict topic)

After (All Agents):
✅ SENTIMENT_ANALYST
✅ BIAS_DETECTOR
✅ TOPIC_CLASSIFIER
✅ FINANCIAL_ANALYST
✅ GEOPOLITICAL_ANALYST (NOW RUNS - captures US-China dynamics)
✅ CONFLICT_EVENT_ANALYST (NOW RUNS - may identify trade tensions)
```

**Strategy:**
- **Phase 1 (Current):** Feed knowledge graph with complete analysis data
- **Phase 2 (Future):** Use graph + historical data to optimize agent selection
- **Phase 3 (Future):** Implement ML-based agent recommendation (graph-informed)

## Troubleshooting

### Agent Not Running

**Symptom:** Expected agent didn't execute

**Check:**
1. Verify PriorityScore >= 60 (check triage_decision in logs)
2. Check if agent in `always_run_tier2_agents` or topic matches `topic_agent_mapping`
3. Verify agent enabled in `enabled_tier2_agents`
4. Check agent initialization in worker logs

### All Agents Running (Unexpected)

**Symptom:** All agents execute even for irrelevant articles

**Check:**
1. Verify triage threshold (should be 0.6)
2. Check if fallback triggered (no topic mapping matched → runs all agents)
3. Review triage scoring logic

### Missing Sentiment/Bias Data

**Symptom:** Frontend shows missing sentiment or bias

**Check:**
1. Verify PriorityScore >= 60 (below 60 skips Tier 2)
2. Check SENTIMENT_ANALYST and BIAS_DETECTOR in `always_run_tier2_agents`
3. Review agent execution logs for errors

## Related Documentation

- [Content Analysis v2 Service](./content-analysis-v2.md) - Overall service architecture
- [Content Analysis v2 API](../api/content-analysis-v2-api.md) - API reference
- [Agent Configuration](../../services/content-analysis-v2/README.md) - Agent-specific settings
- [Triage Agent Prompt](../../services/content-analysis-v2/app/agents/tier0_triage/relevance_scorer.py) - Scoring logic details

## Appendix: Agent Descriptions

### TRIAGE
- **Purpose:** Calculate article relevance and recommend specialists
- **Output:** PriorityScore, category, topics, recommended agents
- **Cost:** ~$0.0005

### ENTITY_EXTRACTOR
- **Purpose:** Extract persons, organizations, locations
- **Output:** Structured entity list with types
- **Cost:** ~$0.0008

### SUMMARY_GENERATOR
- **Purpose:** Generate concise article summary
- **Output:** 2-3 sentence summary
- **Cost:** ~$0.0007

### SENTIMENT_ANALYST
- **Purpose:** Analyze emotional tone and sentiment
- **Output:** Sentiment score (-1 to +1), emotional classification
- **Cost:** ~$0.0004
- **Triggers:** Always (Score >= 60)

### BIAS_DETECTOR
- **Purpose:** Detect political bias and assess objectivity
- **Output:** Bias score, bias direction, objectivity assessment
- **Cost:** ~$0.0005
- **Triggers:** Always (Score >= 60)

### TOPIC_CLASSIFIER
- **Purpose:** Multi-label topic classification with hierarchy
- **Output:** 2-6 topics with relevance scores, keywords, parent-child relationships
- **Cost:** ~$0.0006
- **Triggers:** Always (Score >= 60)

### CONFLICT_EVENT_ANALYST
- **Purpose:** Analyze conflicts, military events, security incidents
- **Output:** Conflict type, parties, impact assessment, escalation risk
- **Cost:** ~$0.0012
- **Triggers:** Topics: conflict, war, military

### GEOPOLITICAL_ANALYST
- **Purpose:** Analyze geopolitical implications and regional impact
- **Output:** Regional impact, diplomatic implications, power dynamics
- **Cost:** ~$0.0010
- **Triggers:** Topics: conflict, war, military, politics, government

### FINANCIAL_ANALYST
- **Purpose:** Analyze economic and financial implications
- **Output:** Market impact, economic indicators, financial risk
- **Cost:** ~$0.0010
- **Triggers:** Topics: finance, economy, markets

### INTELLIGENCE_SYNTHESIZER
- **Purpose:** Synthesize all agent outputs into intelligence summary
- **Output:** Key findings, strategic relevance, intelligence value assessment
- **Cost:** ~$0.0015
- **Triggers:** Always when Tier 2 executed

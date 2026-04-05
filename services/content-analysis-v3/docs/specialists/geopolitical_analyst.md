# GEOPOLITICAL_ANALYST Specialist

## Overview

The `GeopoliticalAnalyst` specialist provides comprehensive analysis of articles with geopolitical significance, including international conflicts, diplomatic relations, security alliances, and regional stability assessments.

**Specialist Type:** `SpecialistType.GEOPOLITICAL_ANALYST`

**Token Budget:** ~1700 tokens
- Quick Check: ~200 tokens
- Deep Dive: ~1500 tokens

**Cost:** ~$0.00005/article (Gemini Flash)

---

## When This Specialist Runs

The GeopoliticalAnalyst is triggered for articles containing:

### Tier1 Topics
- `CONFLICT` - Wars, military operations, armed conflicts
- `POLITICS` - International politics, diplomatic negotiations
- `DIPLOMACY` - Treaties, international agreements
- `SECURITY` - Defense, intelligence, counterterrorism

### Content Indicators
- Countries involved in international disputes
- International organizations (NATO, UN, EU)
- Military operations and defense matters
- Sanctions and international law
- Regional stability concerns

---

## Two-Stage Analysis

### Stage 1: Quick Check (~200 tokens)

**Purpose:** Fast relevance determination to avoid wasting tokens on non-geopolitical content.

**Input:**
- Article title
- Tier1 topics
- Tier1 entities

**Output:**
```python
QuickCheckResult(
    is_relevant=True,
    confidence=0.85,
    reasoning="Article discusses NATO-Ukraine relations with military implications",
    tokens_used=150
)
```

**Logic:**
1. Check Tier1 topics for geopolitical keywords
2. Check Tier1 entities for countries/international organizations
3. Apply confidence boost if geopolitical topics detected
4. Return fast decision with reasoning

**Fallback:** If LLM fails, uses topic-based heuristic (conservative approach).

---

### Stage 2: Deep Dive (~1500 tokens)

**Purpose:** Extract comprehensive geopolitical metrics and relations.

**Input:**
- Full article content (truncated to 3000 chars)
- Tier1 entities (top 15)
- Tier1 relations (top 10)
- Tier1 topics

**Output:**
```python
SpecialistFindings(
    specialist_type=SpecialistType.GEOPOLITICAL_ANALYST,
    geopolitical_metrics=GeopoliticalMetrics(
        metrics={
            "conflict_severity": 8.5,
            "diplomatic_impact": 7.0,
            "regional_stability_risk": 9.0,
            "international_attention": 9.5,
            "economic_implications": 7.5
        },
        countries_involved=["Ukraine", "Russia", "NATO members"],
        relations=[
            {
                "subject": "NATO",
                "predicate": "OPPOSES",
                "object": "Russia",
                "confidence": 0.95
            },
            {
                "subject": "NATO",
                "predicate": "SUPPORTS",
                "object": "Ukraine",
                "confidence": 0.90
            }
        ]
    ),
    tokens_used=1200,
    cost_usd=0.00004,
    model="gemini-2.0-flash-exp"
)
```

---

## Geopolitical Metrics

### 1. Conflict Severity (0.0-10.0)

Measures the intensity of military conflict or potential for escalation.

| Score | Description | Examples |
|-------|-------------|----------|
| 0-2 | Diplomatic tensions, verbal disputes | Trade disagreements, diplomatic statements |
| 3-5 | Sanctions, trade restrictions, military posturing | Economic sanctions, troop movements near border |
| 6-8 | Limited military engagement, proxy conflicts | Airstrikes, proxy war support, naval blockades |
| 9-10 | Full-scale war, existential threats | Total war, nuclear escalation risk |

**Use Cases:**
- Alert systems for conflict escalation
- Portfolio risk assessment for defense companies
- Intelligence monitoring for security threats

---

### 2. Diplomatic Impact (0.0-10.0)

Assesses the significance of diplomatic events and their long-term implications.

| Score | Description | Examples |
|-------|-------------|----------|
| 0-2 | Routine diplomatic activity | Routine meetings, standard protocols |
| 3-5 | Significant bilateral negotiations | Trade agreements, bilateral summits |
| 6-8 | Major international summits, treaty discussions | G7/G20 summits, arms control talks |
| 9-10 | Historic agreements, major alliance shifts | Peace treaties, NATO expansion |

**Use Cases:**
- Strategic planning for international operations
- Policy analysis and forecasting
- Diplomatic timeline tracking

---

### 3. Regional Stability Risk (0.0-10.0)

Evaluates the threat to regional peace and stability.

| Score | Description | Examples |
|-------|-------------|----------|
| 0-2 | Stable situation, minimal disruption | Routine regional cooperation |
| 3-5 | Localized tensions, potential spillover | Border disputes, minority conflicts |
| 6-8 | Regional crisis, multiple nations affected | Refugee crisis, multi-nation tensions |
| 9-10 | Systemic collapse risk, mass migration | Regional war, state collapse |

**Use Cases:**
- Humanitarian organization planning
- Investment risk assessment for emerging markets
- Migration trend forecasting

---

### 4. International Attention (0.0-10.0)

Measures global focus and media coverage intensity.

| Score | Description | Examples |
|-------|-------------|----------|
| 0-2 | Local/regional interest only | Minor border incidents |
| 3-5 | Some international media coverage | Regional conflict with limited coverage |
| 6-8 | Major international focus, UN involvement | UN Security Council meetings |
| 9-10 | Global crisis, emergency security council meetings | 9/11, Ukraine invasion 2022 |

**Use Cases:**
- Media monitoring and analysis
- Public relations strategy
- Intelligence prioritization

---

### 5. Economic Implications (0.0-10.0)

Assesses economic impact on global markets and trade.

| Score | Description | Examples |
|-------|-------------|----------|
| 0-2 | Minimal economic impact | Minor diplomatic spat |
| 3-5 | Trade disruptions, specific sectors affected | Tariffs on specific goods |
| 6-8 | Regional economic consequences, market volatility | Sanctions on major economy |
| 9-10 | Global economic shock, major sanctions regime | Oil crisis, global financial contagion |

**Use Cases:**
- Market risk modeling
- Supply chain risk assessment
- Investment strategy adjustment

---

## Geopolitical Relations

Extracted relations focus on **international relationships** between states, organizations, and alliances.

### Relation Predicates

| Predicate | Meaning | Example |
|-----------|---------|---------|
| `OPPOSES` | Active opposition or hostility | Russia OPPOSES NATO |
| `SUPPORTS` | Active support or assistance | NATO SUPPORTS Ukraine |
| `ALLIES` | Formal alliance or partnership | UK ALLIES USA |
| `NEGOTIATES` | Active negotiations | Iran NEGOTIATES Nuclear Deal |
| `CONDEMNS` | Official condemnation | UN CONDEMNS Invasion |
| `SANCTIONS` | Economic sanctions applied | EU SANCTIONS Russia |

### Relation Confidence Scores

- **0.9-1.0:** Explicit statement in article ("NATO announced support for...")
- **0.7-0.8:** Strong implication ("NATO's actions demonstrate...")
- **0.5-0.6:** Weak/uncertain ("Some suggest NATO may...")

---

## Implementation Details

### Class Structure

```python
class GeopoliticalAnalyst(BaseSpecialist):
    """GEOPOLITICAL_ANALYST specialist for Tier2."""

    def __init__(self):
        super().__init__(specialist_type=SpecialistType.GEOPOLITICAL_ANALYST)

    async def quick_check(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Tier1Results
    ) -> QuickCheckResult:
        """Stage 1: Fast relevance determination."""
        # Implementation

    async def deep_dive(
        self,
        article_id: UUID,
        title: str,
        content: str,
        tier1_results: Tier1Results,
        max_tokens: int
    ) -> SpecialistFindings:
        """Stage 2: Detailed geopolitical analysis."""
        # Implementation
```

---

## Usage Example

```python
from app.pipeline.tier2.specialists import GeopoliticalAnalyst
from app.models.schemas import Tier1Results

# Initialize specialist
analyst = GeopoliticalAnalyst()

# Stage 1: Quick check
quick_result = await analyst.quick_check(
    article_id=article_id,
    title="NATO Summit: Enhanced Support for Ukraine",
    content=content,
    tier1_results=tier1_results
)

if quick_result.is_relevant:
    # Stage 2: Deep dive
    findings = await analyst.deep_dive(
        article_id=article_id,
        title=title,
        content=content,
        tier1_results=tier1_results,
        max_tokens=1500
    )

    # Access metrics
    conflict_severity = findings.geopolitical_metrics.metrics["conflict_severity"]
    countries = findings.geopolitical_metrics.countries_involved
    relations = findings.geopolitical_metrics.relations
```

**Full example:** See `examples/geopolitical_analyst_example.py`

---

## Database Storage

Geopolitical findings are stored in the `tier2_geopolitical_metrics` table:

```sql
CREATE TABLE tier2_geopolitical_metrics (
    id SERIAL PRIMARY KEY,
    article_id UUID REFERENCES articles(id),
    conflict_severity FLOAT,
    diplomatic_impact FLOAT,
    regional_stability_risk FLOAT,
    international_attention FLOAT,
    economic_implications FLOAT,
    countries_involved JSONB,  -- Array of country names
    relations JSONB,            -- Array of relation objects
    tokens_used INTEGER,
    cost_usd FLOAT,
    model VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Testing

Comprehensive test suite in `tests/test_geopolitical_analyst.py`:

- ✅ Quick check identifies geopolitical content
- ✅ Quick check rejects non-geopolitical content
- ✅ Deep dive extracts full metrics
- ✅ Handles JSON parse errors gracefully
- ✅ Fallback logic on LLM failures
- ✅ Correct specialist type assignment

**Run tests:**
```bash
source venv/bin/activate
pytest tests/test_geopolitical_analyst.py -v
```

---

## Performance Characteristics

### Token Usage

| Stage | Expected | Max |
|-------|----------|-----|
| Quick Check | 100-200 | 200 |
| Deep Dive | 1000-1500 | 1500 |
| **Total** | **1100-1700** | **1700** |

### Cost (Gemini Flash @ $0.00003/1K tokens)

- Quick Check: ~$0.000006
- Deep Dive: ~$0.000045
- **Total: ~$0.000051/article**

### Latency

- Quick Check: 0.5-1.0s
- Deep Dive: 2.0-3.0s
- **Total: 2.5-4.0s**

---

## Error Handling

### JSON Parse Failures

**Quick Check Fallback:**
- Uses topic-based heuristic
- Checks for geopolitical keywords in Tier1 topics
- Returns conservative confidence (0.6 if relevant, 0.3 if not)

**Deep Dive Fallback:**
- Returns empty `GeopoliticalMetrics`
- Preserves token/cost metadata
- Logs error for monitoring

### Provider Failures

Handled by `BaseSpecialist.analyze()`:
- Logs error with article_id context
- Returns `None` (specialist skipped)
- Does not block other specialists

---

## Integration Points

### Tier1 Foundation
- **Consumes:** Topics, entities, relations
- **Avoids:** Re-extracting basic facts already in Tier1
- **Focus:** Geopolitical interpretation and metrics

### Intelligence Router (Tier3)
- **Triggers:** GEOPOLITICAL_INTELLIGENCE module
- **Provides:** Conflict severity, regional risks
- **Enables:** Advanced graph analysis of geopolitical networks

### Feed Service
- **Consumed by:** Article filtering and prioritization
- **Used for:** Alert generation for high-severity conflicts
- **Indexed:** Metrics stored for historical analysis

---

## Monitoring & Observability

### Key Metrics to Track

1. **Relevance Rate:** % of articles marked relevant
2. **Average Token Usage:** Should stay within budget
3. **Parse Error Rate:** Should be < 1%
4. **Fallback Usage:** Monitor frequency of fallback logic
5. **Cost per Article:** Track actual vs expected cost

### Logging

```python
logger.info(f"[{article_id}] GEOPOLITICAL_ANALYST: Quick check - relevant={result.is_relevant}")
logger.info(f"[{article_id}] GEOPOLITICAL_ANALYST: Deep dive complete - conflict_severity={severity}")
logger.error(f"[{article_id}] GEOPOLITICAL_ANALYST: Failed to parse response - {error}")
```

---

## Future Enhancements

### Planned (Phase 5)
- [ ] Historical comparison of conflict severity over time
- [ ] Geopolitical entity disambiguation (NATO vs NATO summit)
- [ ] Temporal tracking of diplomatic relations
- [ ] Integration with external geopolitical APIs

### Under Consideration
- [ ] Predictive conflict escalation modeling
- [ ] Alliance network graph construction
- [ ] Sentiment analysis of diplomatic statements
- [ ] Economic impact forecasting

---

## References

- **Design Document:** `/home/cytrex/userdocs/content-analysis-v3/design/tier2-specialists.md`
- **Data Model:** `/home/cytrex/userdocs/content-analysis-v3/design/data-model.md`
- **Examples:** `examples/geopolitical_analyst_example.py`
- **Tests:** `tests/test_geopolitical_analyst.py`

---

**Last Updated:** 2025-11-19
**Version:** 1.0.0
**Status:** ✅ Production Ready

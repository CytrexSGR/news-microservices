# Security View for Geo-Map - Complete System Analysis

## Executive Summary

Analysis of existing system capabilities for implementing a military/intelligence perspective security view on the geo-map.

---

## 1. Content Analysis Pipeline - Complete Tier Documentation

### 1.1 Tier 0: Triage (Fast Keep/Discard Decision)

**Location:** `content-analysis-v3/app/pipeline/tier0/triage.py`

**Purpose:** Fast relevance assessment (< 100 tokens per article)

**Output Schema:**
```python
class TriageDecision:
    PriorityScore: int  # 0-10 urgency score
    category: Literal[
        "CONFLICT",      # Wars, military operations, armed conflicts
        "FINANCE",       # Markets, economy, trading
        "POLITICS",      # Government, diplomacy, elections
        "HUMANITARIAN",  # Disasters, refugees, aid crises
        "SECURITY",      # Cyber, terrorism, threats, espionage
        "TECHNOLOGY",    # Tech innovations, AI, science
        "HEALTH",        # Pandemics, medical breakthroughs
        "OTHER"          # Catch-all
    ]
    keep: bool  # True = process further, False = discard
```

**Priority Score Interpretation:**
| Score | Level | Examples |
|-------|-------|----------|
| 9-10 | CRITICAL | Wars, market crashes, assassinations, major terror attacks |
| 7-8 | HIGH | National elections, central bank decisions, military escalations |
| 5-6 | MEDIUM | G20 policy changes, regional conflicts, major corporate events |
| 3-4 | LOW | Minor political news, routine announcements |
| 0-2 | NOISE | Irrelevant, low-quality content (discarded) |

**Security-Relevant Categories:**
- `CONFLICT` - Score 6-10: Primary source for military intelligence
- `SECURITY` - Score 5-9: Cyber, terrorism, espionage
- `HUMANITARIAN` - Score 4-8: Disasters, refugee movements, aid crises
- `POLITICS` - Score 5-8: Diplomatic shifts, government decisions affecting security

---

### 1.2 Tier 1: Foundation Extraction

**Location:** `content-analysis-v3/app/pipeline/tier1/foundation.py`

**Purpose:** Structured extraction of entities, relations, and topics

**Output Schema:**
```python
class Tier1Results:
    entities: list[Entity]       # Named entities with types
    relations: list[Relation]    # Subject-predicate-object triples
    topics: list[Topic]          # Categorical classifications

    # Numerical scores (0-10)
    impact_score: float      # How significant is this event?
    credibility_score: float # How reliable is the source?
    urgency_score: float     # How time-sensitive?
```

**Entity Types (14 types):**
```python
ENTITY_TYPES = [
    "PERSON",              # Named individuals
    "ORGANIZATION",        # Companies, governments, NGOs, military
    "LOCATION",            # Countries, cities, regions, bases
    "EVENT",               # Named events, operations, summits
    "CONCEPT",             # Abstract ideas, doctrines
    "TECHNOLOGY",          # Weapons systems, platforms
    "PRODUCT",             # Specific products, equipment
    "CURRENCY",            # Monetary units
    "FINANCIAL_INSTRUMENT", # Stocks, bonds, derivatives
    "LAW",                 # Legislation, treaties
    "POLICY",              # Government policies, strategies
    "TIME",                # Dates, periods
    "OTHER"                # Catch-all
]
```

**Relation Structure:**
```python
class Relation:
    subject: str     # Entity name (e.g., "Russia")
    predicate: str   # Relation type (e.g., "ATTACKS", "NEGOTIATES")
    object: str      # Target entity (e.g., "Ukraine")
    confidence: float
```

**Common Predicates for Security:**
- `ATTACKS`, `DEFENDS`, `OCCUPIES`, `WITHDRAWS`
- `NEGOTIATES`, `ALLIES_WITH`, `OPPOSES`, `CONDEMNS`
- `SUPPLIES`, `SANCTIONS`, `SUPPORTS`

---

### 1.3 Tier 2: Specialist Analysis (7 Specialists)

**Location:** `content-analysis-v3/app/pipeline/tier2/`

**Orchestration:** Two-stage approach (quick_check → deep_dive)
- Stage 1: Quick relevance check (~100 tokens)
- Stage 2: Deep analysis only if relevant (~1000-2000 tokens)

**Budget Management:**
- Total budget: 8000 tokens across 7 specialists
- Weighted redistribution from skipped specialists to active ones

#### 1.3.1 GeopoliticalAnalyst ⭐ (Security-Critical)

**File:** `specialists/geopolitical_analyst.py`

**Metrics (0-10 scale):**
```python
METRICS = {
    "conflict_severity": "Intensity of conflict or tension",
    "diplomatic_impact": "Effect on international relations",
    "regional_stability_risk": "Threat to regional stability",
    "international_attention": "Global significance level",
    "economic_implications": "Economic consequences"
}
```

**Countries & Relations:**
```python
class GeopoliticalMetrics:
    metrics: Dict[str, float]           # Above metrics
    countries_involved: List[str]       # ISO codes or names
    relations: List[Dict[str, Any]]     # Inter-country relations
```

**Relation Types:**
- `OPPOSES` - Direct opposition/conflict
- `SUPPORTS` - Alliance or backing
- `NEGOTIATES` - Diplomatic engagement
- `CONDEMNS` - Official criticism
- `ALLIES` - Formal alliance

#### 1.3.2 NarrativeAnalyst ⭐ (Propaganda Detection)

**File:** `specialists/narrative_analyst.py`

**Frame Types:**
```python
FRAME_TYPES = {
    "victim": "Entity portrayed as suffering, harmed, or oppressed",
    "hero": "Entity portrayed as savior, helper, or positive force",
    "threat": "Entity portrayed as dangerous, harmful, or problematic",
    "solution": "Action/entity portrayed as the answer to a problem",
    "conflict": "Framing emphasizing opposition, struggle, or tension",
    "economic": "Framing focused on financial/economic impacts",
    "moral": "Framing with ethical/moral implications",
    "attribution": "Framing that assigns blame or responsibility"
}
```

**Propaganda Indicators:**
```python
PROPAGANDA_INDICATORS = [
    "loaded_language",
    "appeal_to_fear",
    "bandwagon",
    "false_dilemma",
    "ad_hominem",
    "straw_man",
    "cherry_picking",
    "appeal_to_authority",
    "emotional_appeal",
    "oversimplification"
]
```

**Output:**
```python
class NarrativeFrameMetrics:
    frames: List[NarrativeFrame]           # Detected frames
    dominant_frame: Optional[str]          # Most prominent frame
    entity_portrayals: Dict[str, List[str]] # How entities are portrayed
    narrative_tension: float               # 0-1, emotional intensity
    propaganda_indicators: List[str]       # Detected techniques
```

#### 1.3.3 FinancialAnalyst

**File:** `specialists/financial_analyst.py`

**Metrics:**
```python
{
    "market_impact": 0.0-10.0,        # Effect on markets
    "volatility_expected": 0.0-10.0,  # Price movement expected
    "sector_affected": "TECHNOLOGY|FINANCE|ENERGY|HEALTHCARE|COMMODITIES|CRYPTO|OTHER",
    "price_direction": "BULLISH|BEARISH|NEUTRAL"
}
```

**Affected Symbols:**
- Stock tickers: "TSLA", "AAPL", "LMT" (defense contractors)
- Crypto: "BTC-USD", "ETH-USD"
- Indices: "SPY", "^VIX" (volatility)
- Commodities: "GLD", "CL=F" (oil)

#### 1.3.4 SentimentAnalyzerSpecialist

**File:** `specialists/sentiment_analyzer.py`

**Metrics:**
```python
class SentimentMetrics:
    metrics: {
        "bullish_ratio": 0.0-1.0,   # Positive/optimistic
        "bearish_ratio": 0.0-1.0,   # Negative/pessimistic
        "confidence": 0.0-1.0,       # Certainty level
        "is_financial": bool         # Financial vs general content
    }
```

#### 1.3.5 BiasScorer

**File:** `specialists/bias_scorer.py`

**Political Direction (7-level scale):**
```python
POLITICAL_SCALE = {
    "far_left": (-1.0, -0.7),
    "left": (-0.7, -0.4),
    "center_left": (-0.4, -0.15),
    "center": (-0.15, +0.15),
    "center_right": (+0.15, +0.4),
    "right": (+0.4, +0.7),
    "far_right": (+0.7, +1.0)
}
```

**Bias Strength:**
- `minimal`: |score| < 0.15
- `weak`: 0.15-0.4
- `moderate`: 0.4-0.7
- `strong`: 0.7-0.85
- `extreme`: ≥ 0.85

#### 1.3.6 EntityExtractorSpecialist

**File:** `specialists/entity_extractor.py`

**Enrichment Fields:**
```python
# For ORGANIZATION:
{"industry": "Defense", "stock_symbol": "LMT"}

# For PERSON:
{"role": "President", "affiliation": "Russia"}

# For LOCATION:
{"country": "Ukraine", "region": "Eastern Europe"}

# For EVENT:
{"date": "2024-01-15", "location": "Kyiv", "participants": [...]}
```

#### 1.3.7 TopicClassifierSpecialist

**File:** `specialists/topic_classifier.py`

**Hierarchical Topics:**
```python
PARENT_TOPICS = [
    "Economics and Finance",
    "Geopolitics and Defense",
    "Technology and Innovation",
    "Social and Cultural Issues",
    "Environmental and Climate",
    "Legal and Regulatory",
    "Healthcare and Biosciences",
    "Energy and Resources"
]
```

**Example Output:**
```json
{
  "topics": [
    {"topic": "NATO Military Strategy", "parent_topic": "Geopolitics and Defense", "confidence": 0.95},
    {"topic": "Defense Spending", "parent_topic": "Economics and Finance", "confidence": 0.85}
  ]
}
```

---

### 1.4 Tier 3: Intelligence Modules (Designed, Not Implemented)

**Location:** `content-analysis-v3/app/models/schemas.py` (schema only)

**Status:** ⚠️ Schema defined, implementation pending

**Available Modules (6 total):**
```python
INTELLIGENCE_MODULES = [
    "EVENT_INTELLIGENCE",        # Event tracking and correlation
    "SECURITY_INTELLIGENCE",     # Threat assessment ⭐
    "HUMANITARIAN_INTELLIGENCE", # Crisis monitoring ⭐
    "GEOPOLITICAL_INTELLIGENCE", # Strategic analysis ⭐
    "FINANCIAL_INTELLIGENCE",    # Market impact analysis
    "REGIONAL_INTELLIGENCE"      # Geographic focus ⭐
]
```

**SymbolicFinding Types (for Neo4j ingestion):**
```python
FINDING_TYPES = [
    "ENTITY_CLUSTER",      # Related entities grouped
    "CAUSAL_CHAIN",        # Cause-effect relationships
    "TEMPORAL_SEQUENCE",   # Event timeline
    "CONFLICT_PATTERN",    # Recurring conflict dynamics ⭐
    "INFLUENCE_NETWORK"    # Power/influence relationships ⭐
]
```

**Output Structure:**
```python
class IntelligenceModuleOutput:
    module_name: str
    symbolic_findings: List[SymbolicFinding]  # Graph-ready data
    metrics: Dict[str, float]                  # Numerical metrics
```

**Router Decision:**
```python
class RouterDecision:
    modules_to_run: List[str]    # Which modules to execute
    skipped_modules: List[str]   # Modules not relevant
```

---

## 2. SITREP Service (Situation Reports)

**Location:** `sitrep-service/app/services/sitrep_generator.py`

**Purpose:** Generate intelligence briefings from news clusters

### 2.1 Risk Assessment

**Risk Levels:**
```python
RISK_LEVELS = ["critical", "high", "medium", "low"]
```

**Risk Categories:**
```python
RISK_CATEGORIES = [
    "geopolitical",  # International relations, sovereignty
    "economic",      # Market, trade, sanctions
    "security",      # Physical/cyber threats
    "operational"    # Infrastructure, logistics
]
```

### 2.2 Key Developments Structure

```python
class KeyDevelopment:
    title: str
    summary: str
    significance: str
    risk_level: str        # critical|high|medium|low
    risk_category: str     # geopolitical|economic|security|operational
    related_entities: List[str]
```

### 2.3 Emerging Signals

```python
SIGNAL_TYPES = [
    "trend",    # Gradual change
    "pattern",  # Recurring behavior
    "anomaly",  # Unusual deviation
    "risk"      # Emerging threat ⭐
]
```

**Output:**
```python
{
    "signal_type": "risk",
    "description": "Increased military activity near border",
    "confidence": 0.85,
    "related_entities": ["Russia", "Ukraine", "NATO"]
}
```

---

## 3. Database Schema

### 3.1 article_analysis Table (Primary Source)

**Location:** `public.article_analysis` (PostgreSQL)

| Column | Type | Content |
|--------|------|---------|
| `article_id` | UUID | Foreign key to feed_items |
| `triage_results` | JSONB | Tier0: category, PriorityScore, keep |
| `tier1_results` | JSONB | Entities, relations, topics, scores |
| `tier2_results` | JSONB | All 7 specialists output |
| `tier3_results` | JSONB | Intelligence modules (when implemented) |
| `relevance_score` | INTEGER | 0-100 overall relevance |
| `created_at` | TIMESTAMP | Analysis timestamp |

### 3.2 article_locations Table (Geo Data)

**Location:** `public.article_locations`

| Column | Type | Content |
|--------|------|---------|
| `article_id` | UUID | Foreign key to feed_items |
| `country_code` | VARCHAR(3) | ISO 3166-1 alpha-3 |
| `confidence` | FLOAT | Extraction confidence |
| `created_at` | TIMESTAMP | Extraction timestamp |

### 3.3 Knowledge Graph (Neo4j)

**Entity Types:**
- `PERSON`, `ORGANIZATION`, `LOCATION`, `EVENT`

**Relationship Types:**
- `MENTIONED_IN` - Entity appears in article
- `IMPACTS` - Entity A affects Entity B
- `CAUSED_BY` - Event caused by Entity
- `RELATED_TO` - General relationship
- `OPERATES_IN` - Organization in Location
- `OPPOSES`, `SUPPORTS`, `ALLIES_WITH`

---

## 4. Security View Data Points

### 4.1 Per-Article Security Data

```typescript
interface SecurityArticleData {
  // From Tier0
  category: 'CONFLICT' | 'SECURITY' | 'HUMANITARIAN' | 'POLITICS';
  priority_score: number;  // 0-10

  // From Tier1
  entities: Array<{
    name: string;
    type: 'PERSON' | 'ORGANIZATION' | 'LOCATION' | 'EVENT';
    role?: string;
  }>;
  relations: Array<{
    subject: string;
    predicate: string;
    object: string;
  }>;
  impact_score: number;    // 0-10
  urgency_score: number;   // 0-10

  // From Tier2 (GeopoliticalAnalyst)
  conflict_severity?: number;         // 0-10
  diplomatic_impact?: number;         // 0-10
  regional_stability_risk?: number;   // 0-10
  countries_involved?: string[];
  geopolitical_relations?: Array<{
    source: string;
    target: string;
    type: 'OPPOSES' | 'SUPPORTS' | 'NEGOTIATES' | 'CONDEMNS' | 'ALLIES';
  }>;

  // From Tier2 (NarrativeAnalyst)
  dominant_frame?: string;
  narrative_tension?: number;  // 0-1
  propaganda_indicators?: string[];

  // From Tier2 (BiasScorer)
  political_direction?: string;
  bias_score?: number;  // -1 to +1
}
```

### 4.2 Aggregated Country View

```typescript
interface CountrySecurityProfile {
  iso_code: string;
  country_name: string;

  threat_summary: {
    conflict_count: number;
    security_count: number;
    humanitarian_count: number;
    max_priority_score: number;
    avg_conflict_severity: number;
    avg_regional_stability_risk: number;
  };

  active_situations: Array<{
    title: string;
    category: string;
    priority_score: number;
    article_count: number;
  }>;

  key_entities: Array<{
    name: string;
    type: string;
    role: string;
    mentions: number;
  }>;

  geopolitical_relations: Array<{
    target_country: string;
    relation_type: string;
    article_count: number;
  }>;

  trend: 'escalating' | 'stable' | 'de-escalating';
}
```

### 4.3 Security Marker for Map

```typescript
interface SecurityMarker {
  id: string;
  lat: number;
  lon: number;
  country_code: string;

  // Threat classification
  threat_level: 'critical' | 'high' | 'medium' | 'low';
  category: 'CONFLICT' | 'SECURITY' | 'HUMANITARIAN' | 'POLITICS';

  // Content
  title: string;
  summary?: string;

  // Metrics
  priority_score: number;      // 0-10
  conflict_severity?: number;  // 0-10
  impact_score: number;        // 0-10

  // Context
  entities: string[];
  countries_involved: string[];
  article_count: number;

  // Temporal
  first_seen: string;   // ISO timestamp
  last_update: string;  // ISO timestamp

  // Analysis
  dominant_frame?: string;
  propaganda_detected: boolean;
}
```

---

## 5. SQL Queries for Security View

### 5.1 High-Priority Security Events (Last 7 Days)

```sql
SELECT
    aa.article_id,
    fi.title,
    fi.published_at,
    al.country_code,
    c.name as country_name,
    aa.triage_results->>'category' as category,
    (aa.triage_results->>'PriorityScore')::int as priority_score,
    aa.tier1_results->'entities' as entities,
    (aa.tier1_results->>'impact_score')::float as impact_score,
    aa.tier2_results->'geopolitical_metrics'->'metrics' as geo_metrics,
    aa.tier2_results->'narrative_frame_metrics'->>'dominant_frame' as dominant_frame,
    aa.tier2_results->'narrative_frame_metrics'->'propaganda_indicators' as propaganda
FROM article_analysis aa
JOIN feed_items fi ON aa.article_id = fi.id
JOIN article_locations al ON aa.article_id = al.article_id
JOIN countries c ON al.country_code = c.iso_code
WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN')
  AND (aa.triage_results->>'PriorityScore')::int >= 6
  AND fi.published_at >= NOW() - INTERVAL '7 days'
ORDER BY priority_score DESC, fi.published_at DESC
LIMIT 100;
```

### 5.2 Country Threat Aggregation

```sql
SELECT
    al.country_code,
    c.name as country_name,
    COUNT(*) as total_articles,
    COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'CONFLICT') as conflict_count,
    COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'SECURITY') as security_count,
    COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'HUMANITARIAN') as humanitarian_count,
    MAX((aa.triage_results->>'PriorityScore')::int) as max_priority,
    AVG((aa.triage_results->>'PriorityScore')::int)::numeric(3,1) as avg_priority,
    AVG((aa.tier2_results->'geopolitical_metrics'->'metrics'->>'conflict_severity')::float)::numeric(3,1) as avg_conflict_severity,
    AVG((aa.tier2_results->'geopolitical_metrics'->'metrics'->>'regional_stability_risk')::float)::numeric(3,1) as avg_stability_risk
FROM article_locations al
JOIN article_analysis aa ON al.article_id = aa.article_id
JOIN countries c ON al.country_code = c.iso_code
JOIN feed_items fi ON aa.article_id = fi.id
WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
  AND (aa.triage_results->>'PriorityScore')::int >= 5
  AND fi.published_at >= NOW() - INTERVAL '7 days'
GROUP BY al.country_code, c.name
ORDER BY max_priority DESC, total_articles DESC;
```

### 5.3 Propaganda Detection Query

```sql
SELECT
    aa.article_id,
    fi.title,
    fi.source_url,
    aa.triage_results->>'category' as category,
    aa.tier2_results->'narrative_frame_metrics'->>'dominant_frame' as dominant_frame,
    (aa.tier2_results->'narrative_frame_metrics'->>'narrative_tension')::float as tension,
    aa.tier2_results->'narrative_frame_metrics'->'propaganda_indicators' as propaganda_indicators,
    aa.tier2_results->'political_bias'->>'political_direction' as political_direction,
    (aa.tier2_results->'political_bias'->>'bias_score')::float as bias_score
FROM article_analysis aa
JOIN feed_items fi ON aa.article_id = fi.id
WHERE jsonb_array_length(aa.tier2_results->'narrative_frame_metrics'->'propaganda_indicators') > 0
  AND fi.published_at >= NOW() - INTERVAL '7 days'
ORDER BY tension DESC;
```

---

## 6. Integration Recommendation

### 6.1 Option A: Extend geolocation-service (Recommended)

**New Endpoints:**
```
GET /api/v1/geo/security/overview        # Country-level threat aggregation
GET /api/v1/geo/security/events          # Individual security events
GET /api/v1/geo/security/timeline        # Temporal threat evolution
GET /api/v1/geo/security/relations       # Geopolitical relation network
WS  /ws/security-live                    # Real-time security updates
```

**Pros:**
- Already has geo data and map API
- Direct access to article_locations
- WebSocket infrastructure for real-time updates
- Minimal new infrastructure

### 6.2 Database Indexes (Recommended)

```sql
-- Fast security category filtering
CREATE INDEX idx_article_analysis_security_category
ON article_analysis ((triage_results->>'category'))
WHERE triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN');

-- Fast priority score filtering
CREATE INDEX idx_article_analysis_priority
ON article_analysis (((triage_results->>'PriorityScore')::int))
WHERE (triage_results->>'PriorityScore')::int >= 5;

-- Composite index for security queries
CREATE INDEX idx_article_analysis_security_composite
ON article_analysis (
    (triage_results->>'category'),
    ((triage_results->>'PriorityScore')::int)
)
WHERE triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN');
```

---

## 7. Frontend Components (Proposed)

### 7.1 View Mode Toggle
```typescript
// In MapControls.tsx
type ViewMode = 'default' | 'security' | 'economic';
```

### 7.2 Security Layer
```typescript
// New SecurityLayer.tsx
interface SecurityLayerProps {
  markers: SecurityMarker[];
  selectedCategory?: string;
  minThreatLevel?: string;
  showRelations?: boolean;
}
```

### 7.3 Threat Categories Color Coding

| Category | Icon | Color | Marker Style |
|----------|------|-------|--------------|
| CONFLICT | ⚔️ | Red #dc2626 | Pulsing (critical) / Solid (high) |
| SECURITY | 🛡️ | Orange #ea580c | Solid |
| HUMANITARIAN | 🆘 | Yellow #eab308 | Solid |
| POLITICS | 🏛️ | Blue #2563eb | Solid |

### 7.4 Threat Level Visualization

| Level | Priority Score | Marker Style |
|-------|---------------|--------------|
| CRITICAL | 9-10 | Pulsing red, large (24px) |
| HIGH | 7-8 | Solid red, medium (18px) |
| MEDIUM | 5-6 | Orange, medium (16px) |
| LOW | 3-4 | Yellow, small (12px) |

---

## 8. Implementation Phases

### Phase 1: Backend API (geolocation-service)
1. Add security endpoints to geolocation-service
2. Create database indexes for performance
3. Implement aggregation queries
4. Add WebSocket security event channel

### Phase 2: Frontend Components
1. Add SecurityLayer to map
2. Create ThreatSidebar component
3. Implement threat category filters
4. Add timeline visualization

### Phase 3: Real-time & Intelligence
1. Extend WebSocket with threat updates
2. Integrate SITREP emerging signals
3. Add Tier3 intelligence modules when implemented
4. Create threat network visualization (Neo4j relations)

---

## 9. Open Questions

1. **Tier3 Implementation:** When will intelligence modules be implemented?
2. **Historical Depth:** How far back should security view display (7d/30d/90d)?
3. **Clustering:** Should nearby security events be clustered or shown individually?
4. **Relation Network:** Visualize geopolitical relations on map (Neo4j)?
5. **SITREP Integration:** Auto-generate SITREP for selected region/timeframe?
6. **Access Control:** Security view restricted to certain user roles?

---

*Generated: 2026-01-13*
*System: news-microservices*
*Analyst: Claude Opus 4.5*

# Intelligence Service - Comprehensive Technical Documentation

**Service Name:** Intelligence Service
**Port:** 8103 (in docker-compose)
**Language:** Python 3.11
**Framework:** FastAPI
**Database:** PostgreSQL with async support
**Task Queue:** Celery (Redis backend)
**NLP Engine:** spaCy (Named Entity Recognition)
**ML Framework:** scikit-learn (DBSCAN clustering)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [System Design & Principles](#system-design--principles)
4. [Core Components](#core-components)
5. [Intelligence Processing Pipeline](#intelligence-processing-pipeline)
6. [Data Models & Schema](#data-models--schema)
7. [API Endpoints](#api-endpoints)
   - [Overview Endpoint](#overview-endpoint)
   - [Clusters Endpoint](#clusters-endpoint)
   - [Cluster Detail Endpoint](#cluster-detail-endpoint)
   - [Cluster Events Endpoint](#cluster-events-endpoint)
   - [Latest Events Endpoint](#latest-events-endpoint)
   - [Subcategories Endpoint](#subcategories-endpoint)
   - [Risk History Endpoint](#risk-history-endpoint)
   - [Health Check](#health-check)
   - [Root Endpoint](#root-endpoint)
   - [Clustering Admin Endpoints](#clustering-admin-endpoints)
8. [Event Detection Engine](#event-detection-engine)
9. [Clustering Algorithm](#clustering-algorithm)
10. [Risk Scoring System](#risk-scoring-system)
11. [Category Mapping](#category-mapping)
12. [Data Ingestion Pipeline](#data-ingestion-pipeline)
13. [Integration Points](#integration-points)
14. [Performance Characteristics](#performance-characteristics)
15. [Deployment & Configuration](#deployment--configuration)
16. [Monitoring & Debugging](#monitoring--debugging)
17. [Known Issues & Limitations](#known-issues--limitations)
18. [Code Examples](#code-examples)

---

## Executive Summary

The Intelligence Service is a real-time news intelligence and threat analysis platform that transforms raw RSS feeds into structured, correlated intelligence briefings. It ingests articles from the Feed Service, detects related events, clusters them into coherent narratives, calculates risk scores, and exposes findings through RESTful APIs.

**Key Capabilities:**

- **Real-time Event Ingestion**: Pulls recent articles from Feed Service every hour
- **Entity & Keyword Extraction**: Uses spaCy for NER (Named Entity Recognition)
- **Intelligent Clustering**: DBSCAN algorithm groups related events into coherent clusters
- **Risk Quantification**: Multi-factor risk scoring with temporal delta analysis
- **Category Intelligence**: Maps content analysis tiers to dashboard categories (geo, finance, tech, security)
- **Narrative Detection**: Identifies propaganda patterns and narrative frames across events
- **REST API**: Exposes intelligence dashboard data to frontend consumers
- **Async Architecture**: Fully async with FastAPI + asyncpg + SQLAlchemy

**Use Cases:**

1. **News Desk Intelligence**: Real-time monitoring of emerging geopolitical, financial, and security threats
2. **Risk Assessment**: Automated calculation of global risk indices from event clusters
3. **Narrative Analysis**: Detection of coordinated disinformation campaigns
4. **Briefing Generation**: Daily automated intelligence briefings ("Lagebild")

---

## Architecture Overview

### System Boundaries

The Intelligence Service operates in a microservices ecosystem:

```
┌─────────────────────────────────────────────────────────────┐
│                    Intelligence Service                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Ingestion Layer                         │    │
│  │  (Fetches articles from Feed Service)               │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │          Event Detection & Enrichment               │    │
│  │  - Entity Extraction (spaCy)                        │    │
│  │  - Keyword Extraction (TF-IDF)                      │    │
│  │  - Duplicate Detection                             │    │
│  │  - Category Mapping                                │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │           Clustering & Correlation                  │    │
│  │  - DBSCAN Algorithm                                 │    │
│  │  - TF-IDF Vectorization                             │    │
│  │  - Metadata Generation                             │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │         Risk Calculation & Analysis                 │    │
│  │  - Multi-factor Risk Scoring                        │    │
│  │  - Week-over-week Delta Analysis                    │    │
│  │  - Regional Risk Attribution                        │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │         REST API & Presentation                     │    │
│  │  - Intelligence Overview                            │    │
│  │  - Cluster Details & Timeline                       │    │
│  │  - Regional Risk Analysis                           │    │
│  │  - Risk History & Trends                            │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │
                ┌─────────┴──────────┐
                │                    │
         ┌──────▼────────┐   ┌────────▼──────┐
         │  PostgreSQL   │   │  Feed Service │
         │  (Data Store) │   │  (Articles)   │
         └───────────────┘   └───────────────┘
```

### Data Flow

**Ingestion → Detection → Clustering → Risk → API**

1. **Ingestion Phase**
   - Celery task: `ingest_recent_articles` runs hourly
   - Connects to Feed Service database
   - Retrieves recent articles with analysis metadata

2. **Event Detection Phase**
   - Cleans HTML/text
   - Extracts entities (persons, orgs, locations)
   - Extracts keywords using noun chunks
   - Detects duplicates (title similarity + temporal proximity)

3. **Clustering Phase**
   - TF-IDF vectorization of event titles + keywords
   - DBSCAN with cosine distance
   - Groups similar events into clusters
   - Generates cluster metadata

4. **Risk Scoring Phase**
   - Calculates metrics: article count, sentiment, unique sources
   - Compares to previous week for delta analysis
   - Risk Score = (article_factor * 40 + sentiment_factor * 40 + source_factor * 20) * 100

5. **API Phase**
   - REST endpoints serve cluster data, risk indices, timeline
   - Normalized risk scores (raw 0-3000 → display 0-100)
   - Aggregations by category, region, time range

### Key Design Decisions

**Decision 1: DBSCAN for Clustering**
- Why: Works with text similarity without pre-specifying cluster count
- Trade-off: May produce noise points that don't cluster; requires parameter tuning
- Alternative rejected: K-means (requires known k), hierarchical (slow for large N)

**Decision 2: Async FastAPI**
- Why: High-concurrency API with long-running tasks (ingestion, clustering)
- Trade-off: More complex (async/await, connection pooling)
- Performance: Handles 100+ concurrent requests without blocking

**Decision 3: Risk Score Multi-factor Model**
- Why: Captures multiple dimensions: volume (article count), sentiment, credibility (sources)
- Trade-off: Calibration required; weights are tuned empirically
- Normalization: Raw scores ~2500-3000 normalized to 0-100 for UX

**Decision 4: PostgreSQL JSONB for Metadata**
- Why: Flexible schema for entity/keyword storage, JSONB GIN indexes for fast queries
- Trade-off: Schema validation at application layer
- Benefit: Supports complex queries like entity extraction without migrations

---

## System Design & Principles

### Intelligence Analysis Framework

The service implements a tiered intelligence analysis model:

```
┌─────────────────────────────────────────────┐
│        TIER 0: Raw Articles                 │
│  (Title, Description, Source, Published)    │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│       TIER 1: Enriched Events                │
│  (Entities, Keywords, Category, Sentiment)   │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│       TIER 2: Clustered Intelligence         │
│  (Event Groups, Risk Scores, Keywords)       │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│       TIER 3: Analyzed Intelligence          │
│  (Risk Deltas, Regional Attribution,         │
│   Narrative Frames, Propaganda Patterns)     │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│       TIER 4: Intelligence Briefing          │
│  (Lagebild - Daily Automated Briefing)       │
│  (Dashboard Visualizations)                  │
└─────────────────────────────────────────────┘
```

### Event Correlation Strategy

Events are correlated through multiple mechanisms:

1. **Content Similarity Correlation**
   - TF-IDF vectorization of title + keywords
   - Cosine distance metric
   - Threshold: eps=0.3 (DBSCAN parameter)

2. **Entity-Based Correlation**
   - Same persons, organizations, locations
   - Extracted via spaCy NER
   - Fuzzy matching for entity normalization

3. **Temporal Correlation**
   - Published within same day
   - Clusters tracked with first_seen / last_updated
   - Risk delta calculated week-over-week

4. **Category Correlation**
   - V3 analysis categories mapped to dashboard categories
   - Geopolitics → "geo", Economy → "finance", etc.
   - Regional tags extracted from location entities

### Risk Quantification Model

Risk scores combine three factors with weighted importance:

```
Risk Score = (Article Factor × 40 + Sentiment Factor × 40 + Source Factor × 20) × 100

Where:
  Article Factor = min(article_count / 100, 1.0)
    [Higher volume = higher risk]

  Sentiment Factor = (1 - avg_sentiment) / 2
    [Negative sentiment = higher risk]
    [-1 (very negative) → 1.0, +1 (very positive) → 0.0]

  Source Factor = min(unique_sources / 10, 1.0)
    [More credible sources = higher risk/attention]

Risk Delta = ((current_risk - last_week_risk) / last_week_risk) × 100
    [Percentage change week-over-week]
```

**Calibration Notes:**
- Article count normalized to 100 (assume 100+ articles indicates significant event)
- Unique sources normalized to 10 (assume 10+ sources indicates major story)
- Raw scores typically range 0-3000; normalized to 0-100 for display
- Risk delta can be negative (decreasing risk) or positive (increasing risk)

---

## Core Components

### 1. Ingestion Service (`app/services/ingestion.py`)

**Purpose:** Bridge between Feed Service and Intelligence database

**Key Methods:**

```python
class IngestionService:
    async def ingest_rss_articles(db, hours=24, limit=500) -> Dict:
        """
        Fetches articles from Feed Service and normalizes to Intelligence Events

        Returns:
            {
                "fetched": int,     # Articles retrieved
                "created": int,     # New events created
                "duplicates": int,  # Duplicate articles skipped
                "errors": int       # Processing errors
            }
        """

    async def _process_article(db, article, stats):
        """
        Process single article:
        1. Clean HTML/text
        2. Extract metadata (title, description, source)
        3. Check for duplicates
        4. Create IntelligenceEvent record
        """

    @staticmethod
    def clean_html(text: str) -> str:
        """Remove HTML tags using BeautifulSoup"""

    @staticmethod
    def normalize_source(source_url: str) -> str:
        """Extract domain name from URL (e.g., 'https://www.reuters.com' → 'Reuters')"""
```

**Data Integration:**
- Queries Feed Service database (postgresql) directly
- Extracts from `feed_items` and `article_analysis` tables
- Uses JSON extraction from `tier1_results` (topics, entities)
- Handles missing analysis data gracefully

**Duplicate Detection:**
- Title similarity check (30-char prefix + suffix matching)
- Temporal proximity: within 24 hours
- Database query filters using ILIKE

### 2. Event Detection Service (`app/services/event_detection.py`)

**Purpose:** Extract entities and keywords from event text

**Key Methods:**

```python
class EventDetectionService:
    def extract_entities(text: str) -> Dict[str, List[str]]:
        """
        NER using spaCy (en_core_web_sm)

        Returns:
            {
                "persons": ["John Doe", "Jane Smith"],
                "organizations": ["Reuters", "UN"],
                "locations": ["Ukraine", "Moscow"]
            }
        """

    def extract_keywords(text: str, max_keywords=10) -> List[str]:
        """
        Extract keywords using noun chunks + entity recognition

        Algorithm:
        1. Parse with spaCy
        2. Extract noun chunks
        3. Extract named entities
        4. Count frequency
        5. Return top 10
        """

    def calculate_similarity(text1: str, text2: str) -> float:
        """
        Jaccard similarity between word sets

        Result: 0.0 (completely different) to 1.0 (identical)
        """

    def is_duplicate(event1, event2, similarity_threshold=0.8) -> bool:
        """
        Check if two events are duplicates:
        1. Title similarity >= threshold
        2. Published within 1 hour
        """
```

**NLP Pipeline:**
- Uses spaCy model: `en_core_web_sm` (small, fast)
- Entity types mapped:
  - PERSON → persons
  - ORG, NORP → organizations
  - GPE, LOC → locations
- Lazy loading: model loaded on first use

**Performance:**
- Processes ~100 articles/second on single CPU
- Text limited to 10,000 chars (truncated for safety)

### 3. Clustering Service (`app/services/clustering.py`)

**Purpose:** Group related events using DBSCAN algorithm

**Key Methods:**

```python
class ClusteringService:
    def __init__(self, eps=0.3, min_samples=10):
        """
        Initialize DBSCAN with parameters

        eps: Maximum distance between samples in same cluster (0-1 range)
        min_samples: Minimum samples in neighborhood to form core point
        """

    def vectorize_events(events: List[Dict]) -> np.ndarray:
        """
        Convert events to TF-IDF vectors

        Process:
        1. Combine title + keywords for each event
        2. Build TF-IDF matrix (max 1000 features, 1-2 grams)
        3. Stop words: English corpus

        Output:
            (n_events × n_features) matrix
        """

    def cluster_events(events: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Run DBSCAN clustering

        Process:
        1. Vectorize events
        2. Fit DBSCAN (cosine metric)
        3. Group events by cluster label (ignore -1 noise)

        Returns:
            {
                0: [event1, event2, ...],
                1: [event3, event4, ...],
                ...
            }
        """

    def create_cluster_metadata(cluster_events: List[Dict]) -> Dict:
        """
        Generate cluster name and metadata

        Process:
        1. Extract all keywords from events
        2. Count frequency
        3. Top 3 keywords → cluster name
        4. Extract top sources
        5. Calculate average sentiment

        Returns:
            {
                "name": "Ukraine Defense War",
                "keywords": ["Ukraine", "Defense", "Russia"],
                "top_sources": [{"name": "Reuters", "count": 45}],
                "event_count": 45,
                "avg_sentiment": -0.3
            }
        """
```

**DBSCAN Algorithm Details:**

- **Metric**: Cosine distance (good for text similarity)
- **eps**: 0.3 (30% distance threshold)
- **min_samples**: 10 (need 10+ events to form cluster)
- **Noise Handling**: Events with label -1 are discarded
- **Complexity**: O(n²) for n events (acceptable for 0-10k events/day)

**Example:**
```python
# 5 events about Ukraine
events = [
    {"title": "Ukraine Wins Battle", "keywords": ["Ukraine", "War"]},
    {"title": "Ukraine Military Advances", "keywords": ["Ukraine", "Army"]},
    {"title": "Russian Losses Mount", "keywords": ["Russia", "Losses"]},
    ...
]

# After clustering:
clusters = {
    0: [event1, event2],  # Ukraine-related
    1: [event3, event4],  # Russia-related
}
```

### 4. Risk Scoring Service (`app/services/risk_scoring.py`)

**Purpose:** Calculate multi-factor risk scores and trends

**Key Methods:**

```python
class RiskScoringService:
    async def calculate_current_metrics(db, cluster_id, days=7) -> Dict:
        """
        Get this week's metrics

        Returns:
            {
                "article_count": 45,
                "avg_sentiment": -0.3,
                "unique_sources": 8
            }
        """

    async def get_last_week_metrics(db, cluster_id) -> Optional[Dict]:
        """
        Query intelligence_risk_history for previous week
        """

    def calculate_risk_score(current_metrics, last_metrics=None) -> Dict:
        """
        Compute risk score and delta

        Returns:
            {
                "risk_score": 2450.5,
                "risk_delta": 15.3  # +15.3% vs last week
            }
        """

    async def update_cluster_risk(db, cluster_id) -> IntelligenceCluster:
        """
        Persist risk metrics to cluster record
        """
```

**Scoring Formula:**

```
Risk Score = (AF × 40 + SF × 40 + SourceF × 20) × 100

Where:
  AF (Article Factor) = min(count / 100, 1.0)
    • 0 articles = 0 risk
    • 100+ articles = max risk

  SF (Sentiment Factor) = (1 - sentiment) / 2
    • Sentiment -1 (very negative) = max risk
    • Sentiment +1 (very positive) = 0 risk
    • Sentiment 0 (neutral) = 0.5 risk

  SourceF (Source Factor) = min(sources / 10, 1.0)
    • 1 source = 0.1 risk factor (less credible)
    • 10+ sources = max risk factor (highly credible)
```

**Example Calculation:**
```
Current week:
  article_count = 45
  avg_sentiment = -0.5
  unique_sources = 6

AF = min(45/100, 1.0) = 0.45
SF = (1 - (-0.5)) / 2 = 0.75
SourceF = min(6/10, 1.0) = 0.6

Risk = (0.45 × 40 + 0.75 × 40 + 0.6 × 20) × 100
     = (18 + 30 + 12) × 100
     = 6000

Normalized (÷ 60) = 100 / 100 = 100 points
```

### 5. Category Mapper (`app/services/category_mapper.py`)

**Purpose:** Map Content Analysis V3 categories to dashboard categories

**Category Mapping:**

```python
CATEGORY_MAP = {
    # Geopolitical
    "GEOPOLITICS_SECURITY": "geo",
    "POLITICS_SOCIETY": "geo",
    "CONFLICT": "geo",

    # Finance
    "ECONOMY_MARKETS": "finance",
    "FINANCE": "finance",

    # Technology
    "TECHNOLOGY_SCIENCE": "tech",
    "TECHNOLOGY": "tech",

    # Security/Humanitarian
    "HUMANITARIAN": "security",
    "CLIMATE_ENVIRONMENT_HEALTH": "security",

    # Default
    "OTHER": "other"
}
```

**Key Methods:**

```python
def map_category(v3_category: str) -> Optional[str]:
    """Map single V3 category to dashboard category"""

def map_categories_bulk(v3_categories: List[str]) -> str:
    """
    Map multiple V3 categories using majority voting

    Process:
    1. Map all categories
    2. Filter out None and 'other'
    3. Count frequencies
    4. Return most common
    """
```

---

## Intelligence Processing Pipeline

### Full Pipeline Execution

**Trigger:** Celery task runs hourly via `ingest_recent_articles`

**Pipeline Stages:**

```
Stage 1: Article Fetching (Feed Service)
  ├─ Query: feed_items + article_analysis (last 1-24 hours)
  ├─ Processing: Parse JSON, extract topics/entities
  └─ Output: List of article dicts with metadata

Stage 2: Ingestion (Ingestion Service)
  ├─ For each article:
  │   ├─ Clean HTML (BeautifulSoup)
  │   ├─ Normalize source (domain extraction)
  │   ├─ Check duplicates (title similarity + time window)
  │   └─ Create IntelligenceEvent if new
  └─ Output: Created event count, duplicate count, error count

Stage 3: Event Enrichment (Event Detection Service)
  ├─ For each event:
  │   ├─ Extract entities (spaCy NER)
  │   ├─ Extract keywords (TF-IDF + noun chunks)
  │   └─ Update event record
  └─ Output: Enriched events with entities/keywords

Stage 4: Clustering (Clustering Service)
  ├─ Collect unclustered events (from last 7 days)
  ├─ Vectorize with TF-IDF
  ├─ Run DBSCAN
  ├─ For each cluster:
  │   ├─ Generate metadata (name, keywords, sources)
  │   └─ Create or update IntelligenceCluster record
  └─ Output: Cluster assignments, cluster records

Stage 5: Risk Calculation (Risk Scoring Service)
  ├─ For each cluster:
  │   ├─ Calculate current week metrics
  │   ├─ Query previous week metrics (risk_history)
  │   ├─ Calculate risk score and delta
  │   └─ Update cluster risk_score, risk_delta
  └─ Output: Updated risk scores

Stage 6: Narrative Analysis (Future)
  ├─ Detect narrative frames
  ├─ Extract propaganda patterns
  └─ Calculate frame prevalence

Stage 7: Briefing Generation (Future)
  └─ Aggregate daily intelligence
```

### Celery Tasks

**Task 1: `ingest_recent_articles`**
```python
@celery_app.task(name="app.tasks.ingestion.ingest_recent_articles")
def ingest_recent_articles(hours=1, limit=500) -> Dict:
    """
    Hourly ingestion task

    Process:
    1. Fetch articles from last N hours
    2. Process each article (clean, check duplicates, create event)
    3. Return statistics

    Schedule: Every hour via Celery Beat
    Timeout: 5 minutes
    Retries: 3 attempts with exponential backoff
    """
```

**Task 2: `backfill_articles`**
```python
@celery_app.task(name="app.tasks.ingestion.backfill_articles")
def backfill_articles(hours=24, limit=1000) -> Dict:
    """
    One-time historical backfill

    Use Cases:
    - Initial data load from Feed Service
    - Recovering from downtime
    - Data corrections

    Manual Trigger: Required (not scheduled)
    """
```

**Task 3: `enrich_events_with_analysis`**
```python
@celery_app.task(name="app.tasks.ingestion.enrich_events_with_analysis")
def enrich_events_with_analysis(hours=24) -> Dict:
    """
    Enrich existing events with analysis data

    Process:
    1. Find events missing keywords
    2. Query article_analysis table for matching articles
    3. Extract entities, topics from tier1_results
    4. Update event keywords + entities

    Schedule: Every 6 hours (configurable)
    """
```

---

## Data Models & Schema

### Core Tables

#### 1. `intelligence_events`

**Purpose:** Normalized RSS articles for analysis

```sql
CREATE TABLE intelligence_events (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT NOT NULL,        -- "Reuters", "Bloomberg", etc.
    source_url TEXT,             -- Full URL to original article
    published_at TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),

    -- Clustering
    cluster_id UUID REFERENCES intelligence_clusters(id),

    -- AI Analysis
    confidence FLOAT CHECK (0 <= confidence <= 1),
    bias_score FLOAT CHECK (-1 <= bias_score <= 1),
    sentiment FLOAT CHECK (-1 <= sentiment <= 1),

    -- Metadata
    entities JSONB,              -- {"persons": [...], "organizations": [...], "locations": [...]}
    keywords TEXT[],
    language VARCHAR(10),        -- "en", "de", "fr", etc.
    category VARCHAR(50)         -- "geo", "finance", "tech", "security"
);

CREATE INDEX idx_events_cluster ON intelligence_events(cluster_id);
CREATE INDEX idx_events_published ON intelligence_events(published_at DESC);
CREATE INDEX idx_events_source ON intelligence_events(source);
CREATE INDEX idx_events_keywords ON intelligence_events USING GIN(keywords);
CREATE INDEX idx_events_entities ON intelligence_events USING GIN(entities);
CREATE INDEX idx_events_title ON intelligence_events USING GIN(to_tsvector('english', title));
```

**Data Flow:**
1. Created by `IngestionService.ingest_rss_articles()`
2. Enriched by `EventDetectionService` (entities, keywords)
3. Assigned to cluster by `ClusteringService`
4. Updated with category by `CategoryMapper`

**Constraints:**
- Confidence, bias_score, sentiment: valid ranges enforced at DB level
- Entities: JSONB with expected structure (persons, organizations, locations)
- Keywords: Array of strings, can be NULL or empty

#### 2. `intelligence_clusters`

**Purpose:** Groups of related events representing ongoing stories/threats

```sql
CREATE TABLE intelligence_clusters (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,          -- "Ukraine Defense", "Fed Interest Rates", etc.
    description TEXT,

    -- Metrics
    event_count INT DEFAULT 0,   -- Updated via trigger
    risk_score FLOAT,            -- 0-3000 (normalized 0-100 for display)
    risk_delta FLOAT,            -- % change week-over-week
    confidence FLOAT,

    -- Metadata
    keywords TEXT[],             -- ["Ukraine", "War", "Defense"]
    top_sources JSONB,           -- [{"name": "Reuters", "count": 45, "bias": 0.1}]

    -- Lifecycle
    first_seen TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,

    -- Categories
    category VARCHAR(50),        -- "geo", "finance", "tech", "security"
    region TEXT[]               -- ["Europe", "Middle East"]
);

CREATE INDEX idx_clusters_active ON intelligence_clusters(is_active, risk_score DESC);
CREATE INDEX idx_clusters_category ON intelligence_clusters(category);
CREATE INDEX idx_clusters_region ON intelligence_clusters USING GIN(region);
```

**Lifecycle:**
1. Created by `ClusteringService.cluster_events()` after DBSCAN
2. Metadata generated: `create_cluster_metadata()`
3. Risk scores updated: `RiskScoringService.update_cluster_risk()`
4. Marked inactive when: No new events for 30+ days

**Event Count Updates:**
- Automatically maintained via trigger: `update_cluster_event_count()`
- Incremented on INSERT, decremented on DELETE
- Updated on event cluster reassignment

#### 3. `intelligence_risk_history`

**Purpose:** Weekly risk trend tracking for delta analysis

```sql
CREATE TABLE intelligence_risk_history (
    id UUID PRIMARY KEY,
    cluster_id UUID REFERENCES intelligence_clusters(id) ON DELETE CASCADE,

    -- Time window
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,

    -- Metrics
    risk_score FLOAT,
    article_count INT,
    avg_sentiment FLOAT,
    unique_sources INT,

    -- Deltas
    risk_delta FLOAT,
    article_delta FLOAT,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(cluster_id, week_start)
);

CREATE INDEX idx_risk_history_cluster ON intelligence_risk_history(cluster_id, week_start DESC);
```

**Purpose:** Enables risk trend visualization

**Data Entry:**
- Populated after cluster risk calculation
- One record per cluster per week
- Used for: Delta calculation, trend graphs, anomaly detection

#### 4. `intelligence_briefings`

**Purpose:** Daily automated intelligence briefing (Lagebild)

```sql
CREATE TABLE intelligence_briefings (
    id UUID PRIMARY KEY,
    date DATE UNIQUE NOT NULL,

    -- Content
    summary TEXT,
    global_risk_index FLOAT,
    risk_delta FLOAT,

    -- Structured Data
    top_clusters JSONB,              -- Array of cluster summaries
    regional_highlights JSONB,       -- Regional analysis
    market_implications JSONB,       -- Financial implications

    -- Metadata
    generated_at TIMESTAMP DEFAULT NOW(),
    version INT DEFAULT 1
);

CREATE INDEX idx_briefings_date ON intelligence_briefings(date DESC);
```

**Content:**
- Generated once per day (UTC midnight)
- Contains top 5-10 clusters by risk
- Regional breakdowns (Europe, Americas, Asia-Pacific, etc.)
- Category breakdown (geo, finance, tech risk indices)

#### 5. Supporting Narrative Tables

**`narrative_frames`** - Detected narrative frames
```sql
CREATE TABLE narrative_frames (
    id UUID PRIMARY KEY,
    frame TEXT,                      -- "Western defense support", "Market instability"
    description TEXT,
    prevalence FLOAT,                -- 0-1: how common is this frame
    confidence FLOAT,
    sentiment FLOAT,
    clusters UUID[],                 -- Array of cluster IDs
    keywords TEXT[],
    sources JSONB,
    first_detected TIMESTAMP,
    last_updated TIMESTAMP,
    is_active BOOLEAN
);
```

**`narrative_propaganda_patterns`** - Detected propaganda techniques
```sql
CREATE TABLE narrative_propaganda_patterns (
    id UUID PRIMARY KEY,
    technique TEXT,                  -- "Loaded Language", "Appeal to Fear"
    event_id UUID REFERENCES intelligence_events(id),
    text_snippet TEXT,
    confidence FLOAT,
    source TEXT,
    cluster_id UUID
);
```

**`narrative_source_bias`** - Source credibility/bias ratings
```sql
CREATE TABLE narrative_source_bias (
    id UUID PRIMARY KEY,
    source TEXT UNIQUE,
    avg_bias FLOAT,                  -- -1 (left) to +1 (right)
    confidence FLOAT,
    article_count INT,
    manual_bias FLOAT,               -- Human override
    manual_rating_date TIMESTAMP
);
```

### Schema Constraints & Triggers

**Trigger: `update_cluster_event_count`**
```sql
CREATE TRIGGER trigger_update_cluster_event_count
AFTER INSERT OR UPDATE OR DELETE ON intelligence_events
FOR EACH ROW
EXECUTE FUNCTION update_cluster_event_count();
```

**Purpose:** Keep cluster.event_count in sync with actual event count
- On INSERT: event_count += 1
- On DELETE: event_count -= 1
- On UPDATE (cluster change): decrement old cluster, increment new cluster

---

## API Endpoints

### Base URL
```
http://localhost:8103/api/v1/intelligence
```

### Overview Endpoint

**GET `/overview`**

Returns high-level intelligence dashboard data.

```
Request:
  GET /api/v1/intelligence/overview

Response: 200 OK
{
  "global_risk_index": 45.3,
  "top_clusters": [
    {
      "id": "uuid",
      "name": "Ukraine Defense",
      "risk_score": 67.5,
      "risk_delta": 12.3,
      "event_count": 145,
      "keywords": ["Ukraine", "War", "Defense"],
      "category": "geo",
      "last_updated": "2025-11-24T10:30:00Z"
    },
    ...
  ],
  "geo_risk": 52.1,
  "finance_risk": 38.5,
  "top_regions": [
    {
      "name": "Ukraine",
      "event_count": 85,
      "risk_score": 65.0
    },
    ...
  ],
  "total_clusters": 34,
  "total_events": 2847,
  "timestamp": "2025-11-24T10:35:00Z"
}

Error Cases:
  500: Database query failure
```

**Logic:**
1. Get top 5 clusters by risk_score
2. Calculate global_risk_index = average risk of top 5
3. Calculate category-specific risk (geo, finance)
4. Extract top regions from event.entities.locations
5. Count total active clusters and 7-day events

### Clusters Endpoint

**GET `/clusters`**

Get paginated list of clusters with filtering.

```
Request:
  GET /api/v1/intelligence/clusters?min_events=10&time_range=7&sort_by=risk_score&page=1&per_page=20

Query Parameters:
  min_events: int          - Minimum event count filter
  time_range: int          - Only clusters updated in last N days (default: 7)
  sort_by: str             - "risk_score" | "event_count" | "last_updated"
  page: int                - Page number (1-indexed)
  per_page: int            - Items per page (max 100)

Response: 200 OK
{
  "clusters": [
    {
      "id": "uuid",
      "name": "Cluster Name",
      "risk_score": 67.5,
      "risk_delta": 12.3,
      "event_count": 145,
      "keywords": ["keyword1", "keyword2"],
      "category": "geo",
      "avg_sentiment": -0.3,
      "unique_sources": 12,
      "is_active": true,
      "created_at": "2025-11-20T00:00:00Z",
      "last_updated": "2025-11-24T10:30:00Z",
      "timeline": [
        {
          "date": "2025-11-24T00:00:00Z",
          "event_count": 15,
          "avg_sentiment": -0.4
        },
        ...
      ]
    },
    ...
  ],
  "total": 34,
  "page": 1,
  "per_page": 20,
  "timestamp": "2025-11-24T10:35:00Z"
}
```

### Cluster Detail Endpoint

**GET `/clusters/{cluster_id}`**

Get detailed information for single cluster.

```
Request:
  GET /api/v1/intelligence/clusters/550e8400-e29b-41d4-a716-446655440000

Response: 200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Ukraine Defense War",
  "risk_score": 67.5,
  "risk_delta": 12.3,
  "event_count": 145,
  "keywords": ["Ukraine", "Defense", "War"],
  "category": "geo",
  "avg_sentiment": -0.35,
  "unique_sources": 14,
  "is_active": true,
  "created_at": "2025-11-20T00:00:00Z",
  "last_updated": "2025-11-24T10:30:00Z",
  "timeline": [
    {
      "date": "2025-11-20T00:00:00Z",
      "event_count": 12,
      "avg_sentiment": -0.3
    },
    ...
  ]
}

Error Cases:
  404: Cluster not found
```

### Cluster Events Endpoint

**GET `/clusters/{cluster_id}/events`**

Get paginated events for cluster.

```
Request:
  GET /api/v1/intelligence/clusters/550e8400-e29b-41d4-a716-446655440000/events?page=1&per_page=20

Response: 200 OK
{
  "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
  "cluster_name": "Ukraine Defense War",
  "events": [
    {
      "id": "uuid",
      "title": "Ukraine Reports Major Victory",
      "description": "...",
      "source": "Reuters",
      "source_url": "https://...",
      "published_at": "2025-11-24T08:00:00Z",
      "entities": {
        "persons": ["Zelensky"],
        "organizations": ["Ukraine Army"],
        "locations": ["Donetsk"]
      },
      "keywords": ["Ukraine", "War", "Victory"],
      "sentiment": -0.2,
      "bias_score": 0.1,
      "confidence": 0.95
    },
    ...
  ],
  "total": 145,
  "page": 1,
  "per_page": 20,
  "total_pages": 8
}
```

### Latest Events Endpoint

**GET `/events/latest`**

Get most recent events across all clusters.

```
Request:
  GET /api/v1/intelligence/events/latest?hours=4&limit=20

Query Parameters:
  hours: int               - Look back N hours (default: 4, max: 48)
  limit: int               - Max events to return (default: 20, max: 100)

Response: 200 OK
{
  "events": [
    {
      "id": "uuid",
      "title": "Recent Event",
      "description": "...",
      "source": "Reuters",
      "source_url": "https://...",
      "published_at": "2025-11-24T10:00:00Z",
      "entities": {...},
      "keywords": ["key1", "key2"],
      "sentiment": -0.3,
      "bias_score": 0.0,
      "confidence": 0.9,
      "cluster": {
        "id": "uuid",
        "name": "Cluster Name",
        "risk_score": 67.5
      }
    },
    ...
  ],
  "total": 5,
  "hours": 4,
  "timestamp": "2025-11-24T10:35:00Z"
}
```

### Subcategories Endpoint

**GET `/subcategories`**

Get top 2 sub-topics per category (dynamic from current data).

```
Request:
  GET /api/v1/intelligence/subcategories

Response: 200 OK
{
  "geo": [
    {
      "name": "Ukraine",
      "risk_score": 65.0,
      "event_count": 85,
      "clusters": ["uuid1", "uuid2", "uuid3"]
    },
    {
      "name": "Middle East",
      "risk_score": 42.0,
      "event_count": 45,
      "clusters": ["uuid4", "uuid5"]
    }
  ],
  "finance": [
    {
      "name": "Fed Policy",
      "risk_score": 38.0,
      "event_count": 32,
      "clusters": ["uuid6"]
    },
    {
      "name": "Crypto Markets",
      "risk_score": 35.0,
      "event_count": 28,
      "clusters": ["uuid7", "uuid8"]
    }
  ],
  "tech": [
    {
      "name": "AI Regulation",
      "risk_score": 45.0,
      "event_count": 52,
      "clusters": ["uuid9"]
    },
    {
      "name": "Semiconductor",
      "risk_score": 30.0,
      "event_count": 18,
      "clusters": ["uuid10"]
    }
  ]
}
```

**Logic:**
1. Get all active clusters
2. For each category, extract top keywords
3. Count by keyword, sort by risk_score
4. Return top 2 per category

### Risk History Endpoint

**GET `/risk-history`**

Get daily risk trends for visualization.

```
Request:
  GET /api/v1/intelligence/risk-history?days=7

Query Parameters:
  days: int                - Historical days (default: 7, max: 30)

Response: 200 OK
{
  "history": [
    {
      "date": "2025-11-17",
      "global_risk": 42.3,
      "geo_risk": 55.0,
      "finance_risk": 35.5,
      "event_count": 125
    },
    {
      "date": "2025-11-18",
      "global_risk": 44.1,
      "geo_risk": 56.2,
      "finance_risk": 36.0,
      "event_count": 132
    },
    ...
  ],
  "days": 7,
  "total_points": 7
}
```

### Health Check

**GET `/health`**

Service health status.

```
Response: 200 OK
{
  "status": "healthy",
  "service": "intelligence",
  "version": "1.0.0"
}
```

### Root Endpoint

**GET `/`**

Service information and welcome message.

```
Response: 200 OK
{
  "service": "intelligence-service",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "api": "/api/v1/intelligence",
    "docs": "/docs",
    "redoc": "/redoc"
  }
}
```

---

## Clustering Admin Endpoints

### Manual Clustering Trigger

**POST `/api/v1/intelligence/clustering/trigger`**

Manually trigger clustering pipeline with custom parameters. Requires admin role.

```
Request:
  POST /api/v1/intelligence/clustering/trigger
  Headers:
    Authorization: Bearer <jwt_token>
  Body:
  {
    "hours": 24,           // Process events from last N hours (1-168)
    "min_samples": 3,      // Minimum events for cluster formation (2-50)
    "eps": 0.55            // DBSCAN epsilon parameter (0.1-1.0)
  }

Response: 200 OK
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "Clustering pipeline started with custom parameters",
  "parameters": {
    "hours": 24,
    "min_samples": 3,
    "eps": 0.55
  }
}

Error Cases:
  403: Admin access required (user lacks admin role)
  422: Validation error (invalid parameters)
```

**Parameter Details:**
- **hours**: Process events from last N hours
  - Min: 1 (last hour)
  - Max: 168 (last week)
  - Default: 24 (last day)

- **min_samples**: Minimum events required to form a cluster
  - Min: 2 (very aggressive clustering)
  - Max: 50 (very conservative clustering)
  - Default: 3 (balanced)

- **eps**: DBSCAN epsilon parameter for cosine distance
  - Min: 0.1 (very strict - high similarity required)
  - Max: 1.0 (very loose - low similarity required)
  - Default: 0.55 (balanced)
  - Lower values = stricter clustering, fewer/smaller clusters
  - Higher values = looser clustering, more/larger clusters

### Clustering Status

**GET `/api/v1/intelligence/clustering/status`**

Get current clustering configuration and parameter constraints.

```
Request:
  GET /api/v1/intelligence/clustering/status
  Headers:
    Authorization: Bearer <jwt_token>

Response: 200 OK
{
  "current_config": {
    "default_hours": 24,
    "default_min_samples": 3,
    "default_eps": 0.55,
    "metric": "cosine",
    "algorithm": "DBSCAN"
  },
  "last_run": null,
  "scheduled_interval": "Every 15 minutes (Celery Beat)",
  "available_parameters": {
    "hours": {
      "min": 1,
      "max": 168,
      "default": 24,
      "description": "Process events from last N hours (1-168)"
    },
    "min_samples": {
      "min": 2,
      "max": 50,
      "default": 3,
      "description": "Minimum events required to form a cluster (2-50)"
    },
    "eps": {
      "min": 0.1,
      "max": 1.0,
      "default": 0.55,
      "description": "DBSCAN epsilon parameter for cosine distance (0.1-1.0). Lower = stricter clustering."
    }
  }
}

Error Cases:
  401: Authentication required
```

### Clustering Task Status

**GET `/api/v1/intelligence/clustering/task/{task_id}`**

Get status of a specific clustering task.

```
Request:
  GET /api/v1/intelligence/clustering/task/550e8400-e29b-41d4-a716-446655440000
  Headers:
    Authorization: Bearer <jwt_token>

Response: 200 OK (Task Running)
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "result": null
}

Response: 200 OK (Task Complete)
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "result": {
    "clusters_created": 12,
    "clusters_updated": 8,
    "events_clustered": 145,
    "events_noise": 23,
    "processing_time_seconds": 4.5
  }
}

Response: 200 OK (Task Failed)
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FAILURE",
  "result": {
    "error": "Database connection failed",
    "traceback": "..."
  }
}

Task Status Values:
  - PENDING: Task waiting to be executed
  - STARTED: Task execution started
  - SUCCESS: Task completed successfully
  - FAILURE: Task failed with error
  - RETRY: Task being retried after failure
  - REVOKED: Task was cancelled

Error Cases:
  401: Authentication required
  404: Task ID not found
```

---

## Event Detection Engine

### Named Entity Recognition (NER)

**Tool:** spaCy `en_core_web_sm`

**Entity Types Extracted:**
```python
{
    "PERSON": ["John Doe", "Volodymyr Zelensky"],
    "ORG": ["Reuters", "United Nations"],
    "NORP": ["European Union"],
    "GPE": ["Ukraine", "Russia"],
    "LOC": ["Donetsk", "Moscow"]
}
```

**Code Flow:**
```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp(text)

entities = {
    "persons": [],
    "organizations": [],
    "locations": []
}

for ent in doc.ents:
    if ent.label_ == "PERSON":
        entities["persons"].append(ent.text)
    elif ent.label_ in ("ORG", "NORP"):
        entities["organizations"].append(ent.text)
    elif ent.label_ in ("GPE", "LOC"):
        entities["locations"].append(ent.text)
```

### Keyword Extraction

**Method 1: TF-IDF Vectorization** (used in clustering)
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=1000,      # Limit features
    stop_words='english',   # Remove common words
    ngram_range=(1, 2)     # Unigrams + bigrams
)
vectors = vectorizer.fit_transform(texts)
```

**Method 2: Noun Chunks** (used for keyword extraction)
```python
doc = nlp(text)
keywords = []

for chunk in doc.noun_chunks:
    if len(chunk.text) > 3:  # Filter short phrases
        keywords.append(chunk.text.lower())

for ent in doc.ents:
    keywords.append(ent.text.lower())

# Count and return top 10
from collections import Counter
counter = Counter(keywords)
top_keywords = [w for w, _ in counter.most_common(10)]
```

### Duplicate Detection

**Algorithm:**
1. Title similarity check (Jaccard similarity)
2. Temporal proximity check (same day)
3. Both conditions required

**Implementation:**
```python
def is_duplicate(event1, event2, similarity_threshold=0.8):
    # Jaccard similarity on title words
    title_sim = calculate_similarity(
        event1["title"],
        event2["title"]
    )

    if title_sim >= similarity_threshold:
        # Check temporal proximity
        time_diff = abs((event1["published_at"] - event2["published_at"]).total_seconds())
        if time_diff < 3600:  # Within 1 hour
            return True

    return False

def calculate_similarity(text1, text2):
    t1 = set(text1.lower().split())
    t2 = set(text2.lower().split())

    intersection = len(t1.intersection(t2))
    union = len(t1.union(t2))

    return intersection / union if union > 0 else 0.0
```

**Example:**
```
Event 1: "Ukraine Wins Major Battle" (2025-11-24 08:00)
Event 2: "Ukraine Victory in War" (2025-11-24 08:45)

Title similarity:
  t1 = {"ukraine", "wins", "major", "battle"}
  t2 = {"ukraine", "victory", "in", "war"}
  intersection = {"ukraine"} → 1
  union = {"ukraine", "wins", "major", "battle", "victory", "in", "war"} → 7
  similarity = 1/7 = 0.14 (NOT duplicate)

Event 1: "Fed Raises Interest Rates" (2025-11-24 08:00)
Event 3: "Fed Raises Interest Rates 0.25%" (2025-11-24 08:30)

Title similarity:
  t1 = {"fed", "raises", "interest", "rates"}
  t3 = {"fed", "raises", "interest", "rates", "0.25%"}
  intersection = {"fed", "raises", "interest", "rates"} → 4
  union = {"fed", "raises", "interest", "rates", "0.25%"} → 5
  similarity = 4/5 = 0.8 (DUPLICATE!)
```

---

## Clustering Algorithm

### DBSCAN Overview

**Purpose:** Group similar events without predefined cluster count

**Algorithm:**
```
For each unvisited point p:
  1. If p has >= min_samples neighbors within eps distance:
     - Create new cluster
     - Add all reachable neighbors recursively
  2. Else:
     - Mark p as noise (label = -1)
```

**Parameters:**
- **eps** (0.3): Maximum distance for neighbors (0-1 range for cosine)
- **min_samples** (10): Minimum neighbors to form core point
- **metric** (cosine): Distance measure for text vectors

### Text Vectorization

**Method:** TF-IDF (Term Frequency-Inverse Document Frequency)

**Process:**
```python
from sklearn.feature_extraction.text import TfidfVectorizer

# Prepare texts: title + keywords
texts = [
    "Ukraine War Defense " + " ".join(event["keywords"])
    for event in events
]

# Vectorize
vectorizer = TfidfVectorizer(
    max_features=1000,        # Top 1000 terms
    stop_words='english',     # Remove "the", "a", "is", etc.
    ngram_range=(1, 2)        # Single words + 2-word phrases
)

tfidf_matrix = vectorizer.fit_transform(texts)
# Output: (n_events × 1000) sparse matrix
```

**Example:**
```
Event 1: "Ukraine War Defense" + keywords ["war", "defense", "army"]
  → "Ukraine War Defense war defense army"

Event 2: "Ukraine Military Advances" + keywords ["ukraine", "military", "advance"]
  → "Ukraine Military Advances ukraine military advance"

TF-IDF vectorization creates 1000-dimensional vectors
Cosine similarity between vectors: 0.65 (related)

Event 3: "Stock Market Decline" + keywords ["market", "decline", "stocks"]
  → "Stock Market Decline market decline stocks"

Cosine similarity (Event 1 vs Event 3): 0.05 (unrelated)
```

### Clustering Execution

```python
from sklearn.cluster import DBSCAN
import numpy as np

# Vectorize
vectors = vectorizer.fit_transform(texts).toarray()

# Run DBSCAN
dbscan = DBSCAN(eps=0.3, min_samples=10, metric='cosine')
labels = dbscan.fit_predict(vectors)

# Group events
clusters = {}
for idx, label in enumerate(labels):
    if label == -1:      # Skip noise
        continue

    if label not in clusters:
        clusters[label] = []

    clusters[label].append(events[idx])

# Result:
# clusters[0] = [event1, event2, event5, ...]  # Ukraine-related
# clusters[1] = [event3, event4, ...]           # Finance-related
# (events with label=-1 are not included)
```

### Cluster Metadata Generation

**Process:**
```python
def create_cluster_metadata(cluster_events):
    # Extract all keywords
    all_keywords = []
    for event in cluster_events:
        all_keywords.extend(event.get("keywords", []))

    # Top keywords → cluster name
    from collections import Counter
    keyword_counts = Counter(all_keywords)
    top_keywords = [kw for kw, _ in keyword_counts.most_common(10)]
    cluster_name = ", ".join(top_keywords[:3]).title()

    # Extract sources
    sources = {}
    for event in cluster_events:
        source = event.get("source", "Unknown")
        sources[source] = sources.get(source, 0) + 1

    top_sources = [
        {"name": s, "count": c}
        for s, c in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Average sentiment
    sentiments = [e.get("sentiment", 0) for e in cluster_events if e.get("sentiment")]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

    return {
        "name": cluster_name,
        "event_count": len(cluster_events),
        "keywords": top_keywords,
        "top_sources": top_sources,
        "avg_sentiment": avg_sentiment
    }
```

**Example Output:**
```python
{
    "name": "Ukraine War Defense",
    "event_count": 87,
    "keywords": ["Ukraine", "War", "Defense", "Army", "Russia", "Military"],
    "top_sources": [
        {"name": "Reuters", "count": 35},
        {"name": "Bloomberg", "count": 28},
        {"name": "BBC", "count": 12}
    ],
    "avg_sentiment": -0.35
}
```

---

## Risk Scoring System

### Multi-Factor Risk Model

**Formula:**
```
Risk Score = (AF × 40 + SF × 40 + SourceF × 20) × 100

Where:
  AF = Article Factor = min(count / 100, 1.0)
  SF = Sentiment Factor = (1 - sentiment) / 2
  SourceF = Source Factor = min(sources / 10, 1.0)
```

### Factor Explanation

**1. Article Factor (40% weight)**
- Rationale: High volume indicates significant event
- Formula: `min(article_count / 100, 1.0)`
- Range: 0 → 1.0
- Examples:
  - 0 articles → AF = 0.0
  - 50 articles → AF = 0.5
  - 100+ articles → AF = 1.0 (maxed out)

**2. Sentiment Factor (40% weight)**
- Rationale: Negative sentiment indicates threats/crises
- Formula: `(1 - avg_sentiment) / 2`
- Range: 0 → 1.0
- Examples:
  - Sentiment -1.0 (very negative) → SF = (1 - (-1)) / 2 = 1.0
  - Sentiment 0.0 (neutral) → SF = (1 - 0) / 2 = 0.5
  - Sentiment +1.0 (very positive) → SF = (1 - 1) / 2 = 0.0

**3. Source Factor (20% weight)**
- Rationale: Multiple credible sources verify story importance
- Formula: `min(unique_sources / 10, 1.0)`
- Range: 0 → 1.0
- Examples:
  - 1 source → SF = 0.1 (lower credibility)
  - 5 sources → SF = 0.5
  - 10+ sources → SF = 1.0 (high credibility)

### Risk Delta Calculation

**Week-over-Week Change:**
```
Risk Delta = ((current_risk - last_week_risk) / last_week_risk) × 100

Interpretation:
  Delta > 0: Risk increasing (threat escalating)
  Delta < 0: Risk decreasing (threat de-escalating)
  Delta = 0: Risk stable
```

**Examples:**
```
Scenario 1: Risk increasing
  Last week risk: 1000
  Current risk: 1200
  Delta = ((1200 - 1000) / 1000) × 100 = 20%
  Interpretation: Risk up 20% (concerning)

Scenario 2: Risk decreasing
  Last week risk: 2000
  Current risk: 1700
  Delta = ((1700 - 2000) / 2000) × 100 = -15%
  Interpretation: Risk down 15% (improving)
```

### Normalization for Display

**Raw vs Display:**
- Database stores: 0-3000 (raw multi-factor scores)
- Display shows: 0-100 (normalized for UX)

**Normalization Function:**
```python
def normalize_risk_score(raw_score: float) -> float:
    MAX_OBSERVED_SCORE = 3000.0
    normalized = min(100.0, (raw_score / MAX_OBSERVED_SCORE) * 100.0)
    return round(normalized, 1)
```

**Why?**
- Raw scores (0-3000) are hard for humans to interpret
- Normalized (0-100) maps to intuitive risk levels
- Example: 67.5 / 100 = "moderate-high risk"

### Sentiment Analysis

**Source:** Feed Service (content-analysis-v3 tier1_results)

**Scale:** -1.0 (very negative) to +1.0 (very positive)

**Examples:**
```
Event: "Ukraine Wins Battle"
  Sentiment: -0.2 (slightly negative due to war context)

Event: "Stock Market Reaches Record High"
  Sentiment: +0.7 (positive economic news)

Event: "Economic Uncertainty Persists"
  Sentiment: -0.5 (moderate negative)

Event: "Central Bank Holds Rates Steady"
  Sentiment: 0.0 (neutral, no judgment)
```

### Source Credibility

**What counts as a source:**
- Distinct domain/news outlet
- Examples: "Reuters", "Bloomberg", "BBC", "AP", etc.

**Why multiple sources matter:**
- 1 source: Potentially unreliable, low corroboration
- 5 sources: Moderate corroboration, story verified
- 10+ sources: Major story, widely reported

---

## Category Mapping

### V3 Analysis Categories (14 types)

From content-analysis-v3 service (tier0.category):

```
1. GEOPOLITICS_SECURITY → "geo"
2. POLITICS_SOCIETY    → "geo"
3. ECONOMY_MARKETS     → "finance"
4. TECHNOLOGY_SCIENCE  → "tech"
5. CLIMATE_ENVIRONMENT_HEALTH → "security"
6. FINANCE             → "finance"
7. HUMANITARIAN        → "security"
8. SECURITY            → "security"
9. CONFLICT            → "geo"
10. POLITICS           → "geo"
11. TECHNOLOGY         → "tech"
12. HEALTH             → "security"
13. PANORAMA           → "other"
14. OTHER              → "other"
```

### Dashboard Categories (4 types)

**Geo:** Geopolitical & conflict events
- Includes: Wars, sanctions, diplomacy, elections
- Example clusters: Ukraine war, Middle East tensions, Taiwan straits

**Finance:** Economic & market events
- Includes: Interest rates, stock markets, currency, commodities
- Example clusters: Fed policy, crypto markets, supply chain disruptions

**Tech:** Technology & innovation events
- Includes: AI, semiconductors, cybersecurity, breakthroughs
- Example clusters: AI regulation, chip shortages, quantum computing

**Security:** Humanitarian, health, and climate events
- Includes: Pandemics, natural disasters, climate crises, humanitarian crises
- Example clusters: Earthquake aftermath, drought impact, supply crisis

### Bulk Category Mapping

**Use Case:** Cluster has multiple V3 categories (from multiple events)

**Algorithm:** Majority voting
```python
def map_categories_bulk(v3_categories):
    # Map all categories
    mapped = [map_category(cat) for cat in v3_categories if cat]

    # Filter None and 'other'
    valid = [cat for cat in mapped if cat and cat != 'other']

    if not valid:
        return "other"

    # Count and return most common
    from collections import Counter
    counts = Counter(valid)
    return counts.most_common(1)[0][0]
```

**Example:**
```
Cluster events have categories:
  Event 1: CONFLICT → "geo"
  Event 2: POLITICS → "geo"
  Event 3: HUMANITARIAN → "security"
  Event 4: CONFLICT → "geo"

Bulk mapping:
  valid = ["geo", "geo", "security", "geo"]
  Counter: {"geo": 3, "security": 1}
  Result: "geo" (most common)
```

---

## Data Ingestion Pipeline

### Full Ingestion Flow

```
1. Schedule Trigger
   ↓
2. Celery Task: ingest_recent_articles(hours=1, limit=500)
   ├─ Feed Service DB Query (async)
   │  └─ Get articles from last N hours
   │     + article_analysis.tier1_results (topics, entities)
   ├─ Process each article
   │  ├─ Clean HTML
   │  ├─ Check duplicates
   │  └─ Create IntelligenceEvent if new
   ├─ Enrich with analysis data
   │  ├─ Extract keywords from tier1_results
   │  ├─ Extract entities from tier1_results
   │  └─ Map V3 category to dashboard category
   └─ Return statistics (created, duplicates, errors)
   ↓
3. Clustering Task (next run)
   ├─ Collect unclustered events (from last 7 days)
   ├─ Run DBSCAN
   └─ Assign to clusters
   ↓
4. Risk Calculation (next run)
   ├─ For each cluster:
   │  ├─ Calculate metrics
   │  └─ Update risk_score, risk_delta
   └─ Save to intelligence_risk_history
   ↓
5. API Ready
   └─ Frontend calls /api/v1/intelligence/overview
      → Returns latest risk data
```

### Article Processing Details

**Step 1: Article Fetching**

From Feed Service database:
```sql
SELECT
    fi.id,
    fi.title,
    fi.description,
    fi.link,
    fi.published_at,
    aa.tier1_results->>'topics' as topics_json,
    aa.tier1_results->>'entities' as entities_json
FROM feed_items fi
LEFT JOIN article_analysis aa ON fi.id = aa.article_id AND aa.success = true
WHERE fi.published_at >= :time_threshold
ORDER BY fi.published_at DESC
LIMIT :limit
```

**Step 2: HTML Cleaning**

```python
from bs4 import BeautifulSoup
import re

def clean_html(text):
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Before: "<p>Ukraine <b>wins</b> battle</p>"
# After: "Ukraine wins battle"
```

**Step 3: Duplicate Detection**

```python
# Check if similar article already exists
duplicates = await find_duplicate_events(
    db,
    title=title,
    published_at=published_at,
    time_window_hours=24
)

# Uses title ILIKE match + time window
# Query:
# SELECT * FROM intelligence_events
# WHERE published_at >= now - 24h
#   AND published_at <= now
#   AND (title ILIKE '%first_30_chars%' OR title ILIKE '%last_30_chars%')
```

**Step 4: Event Creation**

```python
event = IntelligenceEvent(
    title=clean_title,
    description=clean_description,
    source=normalize_source(source_url),
    source_url=source_url,
    published_at=published_at,
    language=language,
    category=mapped_category,
    keywords=extracted_keywords,
    entities=extracted_entities
)
db.add(event)
await db.commit()
```

### Enrichment Task

**Purpose:** Enrich events missing keywords with analysis data

```python
@celery_app.task(name="enrich_events_with_analysis")
def enrich_events_with_analysis(hours=24):
    """Find events without keywords, extract from article_analysis"""

    # Get events from last 24h without keywords
    events = db.query(IntelligenceEvent).filter(
        IntelligenceEvent.published_at >= now - 24h,
        IntelligenceEvent.keywords == None
    ).all()

    for event in events:
        # Find corresponding analysis
        analysis = db.execute("""
            SELECT tier1_results
            FROM article_analysis
            WHERE article_id IN (
                SELECT id FROM feed_items
                WHERE title = :title
                AND published_at BETWEEN :start AND :end
            )
            LIMIT 1
        """)

        if analysis:
            # Extract keywords from entities
            entities = analysis.tier1_results['entities']
            keywords = [e['name'] for e in entities if e['type'] in [...]]

            # Update event
            event.keywords = keywords
            db.commit()
```

---

## Integration Points

### Feed Service Integration

**Connection:** PostgreSQL database access

**Data Source:** `feed_items` + `article_analysis` tables

**Query Pattern:**
```sql
SELECT fi.*, aa.tier1_results
FROM feed_items fi
LEFT JOIN article_analysis aa ON fi.id = aa.article_id
WHERE fi.published_at >= :start
AND aa.success = true
```

**Data Extracted:**
- Title, description, link (article metadata)
- Topics, entities (from tier1_results)
- Category (from v3_analysis, if available)

**Schedule:** Hourly pull via Celery

### Content Analysis Integration

**Data Structure:** V3 Analysis results stored in `article_analysis.tier1_results`

**Fields Used:**
```json
{
  "topics": [...],           // Topic extraction
  "entities": [              // Entity recognition
    {
      "type": "ORGANIZATION",
      "normalized_text": "Reuters",
      "text": "Reuters"
    }
  ],
  "summary": "...",          // Summary text
  "category": "CONFLICT"     // V3 category (mapped to dashboard)
}
```

### RabbitMQ Events (Future)

**Planned Integration:**
- Publish cluster updates as events
- Subscribe to feed updates for real-time ingestion
- Event types:
  - `intelligence.cluster.created`
  - `intelligence.cluster.risk_updated`
  - `intelligence.event.new`

### External API Consumers

**Frontend Dashboard:**
- Calls: `/overview`, `/clusters`, `/risk-history`
- Updates: Every 30-60 seconds (configurable)
- Data refresh: Auto-updates on cluster changes

**Downstream Services (Future):**
- Narrative Service: Consumes cluster data for frame detection
- Briefing Service: Consumes daily cluster snapshots
- Alerting Service: Triggered on risk_delta threshold

---

## Performance Characteristics

### Throughput

**Article Ingestion:**
- Rate: ~100 articles/hour (average)
- Peak: ~500 articles/hour (high news day)
- Processing time per article: 50-200ms

**Clustering:**
- Time for 1000 events: 2-5 seconds (DBSCAN)
- Vectorization bottleneck: sklearn TfidfVectorizer
- Cluster creation: Negligible

**Risk Calculation:**
- Time per cluster: 10-50ms (database queries)
- Total for 50 clusters: 0.5-2.5 seconds

**API Response Times:**
- `/overview`: 200-500ms (aggregates 50+ clusters)
- `/clusters`: 100-300ms (paginated query)
- `/events/latest`: 50-150ms (simple query)

### Memory Usage

**Model Initialization:**
- spaCy model (en_core_web_sm): ~40MB
- sklearn TfidfVectorizer: ~5MB
- Total baseline: ~100MB

**Peak Memory (during processing):**
- 1000 events vectorization: +200MB
- Full clustering: +300MB
- Total during ingestion task: ~400-500MB

### Database Performance

**Indexes:**
- `idx_clusters_active`: (is_active, risk_score DESC) - fast overview
- `idx_events_cluster`: (cluster_id) - fast event lookup
- `idx_events_published`: (published_at DESC) - fast recent query
- `idx_events_title`: GIN full-text index - fast search
- `idx_events_keywords`: GIN array index - fast keyword filter

**Query Performance:**
- Get top 5 clusters: <50ms
- Get 20 events: <100ms
- Count by category: <30ms

### Scalability Limits

**Current Limits:**
- Max events in database: 10M+ (PostgreSQL)
- Clustering max: ~10k events per run (DBSCAN)
- Concurrent API requests: 100+ (async I/O)

**Bottlenecks:**
1. DBSCAN vectorization: O(n²) for n events
2. Entity extraction: CPU-bound (spaCy)
3. Database connection pool: 10 max (configurable)

**Solutions for scale:**
- Batch clustering by category (partition problem)
- Use cached embeddings instead of vectorizing daily
- Increase DB connection pool (trade CPU/memory)
- Implement pagination for large result sets

---

## Deployment & Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/news_mcp

# Feed Service
FEED_SERVICE_URL=http://feed-service:8000

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Service
SERVICE_PORT=8103
SERVICE_HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO
```

### Docker Compose Entry

```yaml
intelligence-service:
  build:
    context: ./services/intelligence-service
    dockerfile: Dockerfile.dev
  ports:
    - "8103:8000"
  environment:
    - DATABASE_URL=postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp
    - FEED_SERVICE_URL=http://feed-service:8000
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - postgres
    - redis
    - feed-service
  volumes:
    - ./services/intelligence-service/app:/app/app
  networks:
    - default
```

### Database Initialization

**Migrations:**
```bash
# Apply migrations
python app/migrations/apply_migrations.py

# Verify tables
psql -h postgres -U news_user -d news_mcp -c "\dt intelligence*"
```

**Manual Setup:**
```bash
# Run SQL directly
psql -h postgres -U news_user -d news_mcp < migrations/001_initial_schema.sql
```

### Celery Configuration

**Broker:** Redis (pub/sub)

**Scheduled Tasks:**
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'ingest-articles-hourly': {
        'task': 'app.tasks.ingestion.ingest_recent_articles',
        'schedule': crontab(minute=0),  # Every hour
        'args': (1, 500),  # hours=1, limit=500
    },
    'enrich-events-6h': {
        'task': 'app.tasks.ingestion.enrich_events_with_analysis',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'args': (24,),  # hours=24
    },
}
```

### Health Check

```bash
# Service health
curl http://localhost:8103/health
# Response: {"status": "healthy", "service": "intelligence", "version": "1.0.0"}

# Database connectivity
curl http://localhost:8103/api/v1/intelligence/overview
# Should return cluster data (200 OK)
```

---

## Monitoring & Debugging

### Logging

**Log Levels:**
- ERROR: Failed operations (DB errors, network errors)
- WARN: Unusual conditions (no events, empty clusters)
- INFO: Normal operations (task start/complete, counts)
- DEBUG: Detailed processing (entity extraction, clustering steps)

**Log Format:**
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
Example: 2025-11-24 10:30:45,123 - app.services.ingestion - INFO - Ingestion complete: created=45, duplicates=3, errors=0
```

**Configuration:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligence.log'),
        logging.StreamHandler()
    ]
)
```

### Debugging Clustering

**Enable verbose logging:**
```python
# In clustering.py
logger.debug(f"Vectorizing {len(events)} events...")
logger.debug(f"Clustered into {len(clusters)} clusters")
logger.debug(f"Top keywords: {top_keywords}")
```

**Manual clustering test:**
```python
from app.services.clustering import ClusteringService
from app.crud.events import get_events

# Get events
events = await get_events(db, limit=100)

# Create clusterer
clusterer = ClusteringService(eps=0.3, min_samples=10)

# Cluster
event_dicts = [
    {
        "title": e.title,
        "keywords": e.keywords or []
    }
    for e in events
]

clusters = clusterer.cluster_events(event_dicts)
print(f"Created {len(clusters)} clusters")

for cluster_id, cluster_events in clusters.items():
    metadata = clusterer.create_cluster_metadata(cluster_events)
    print(f"Cluster {cluster_id}: {metadata['name']} ({metadata['event_count']} events)")
```

### Debugging Risk Scoring

**Get cluster metrics:**
```python
from app.services.risk_scoring import RiskScoringService

scorer = RiskScoringService()

# Get current metrics
current = await scorer.calculate_current_metrics(db, cluster_id, days=7)
print(f"Current: {current}")

# Get last week
last_week = await scorer.get_last_week_metrics(db, cluster_id)
print(f"Last week: {last_week}")

# Calculate risk
risk = scorer.calculate_risk_score(current, last_week)
print(f"Risk: {risk}")
```

### API Testing

**Get overview:**
```bash
curl http://localhost:8103/api/v1/intelligence/overview | jq
```

**Get clusters:**
```bash
curl 'http://localhost:8103/api/v1/intelligence/clusters?page=1&per_page=10' | jq
```

**Get specific cluster:**
```bash
curl http://localhost:8103/api/v1/intelligence/clusters/{cluster_id} | jq
```

### Database Queries

**Check cluster stats:**
```sql
SELECT
    COUNT(*) as total_clusters,
    AVG(risk_score) as avg_risk,
    MAX(risk_score) as max_risk,
    SUM(event_count) as total_events
FROM intelligence_clusters
WHERE is_active = true;
```

**Check event ingestion:**
```sql
SELECT
    DATE(published_at) as date,
    COUNT(*) as event_count,
    COUNT(DISTINCT source) as unique_sources
FROM intelligence_events
WHERE published_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(published_at)
ORDER BY date DESC;
```

**Check clustering:**
```sql
SELECT
    c.id,
    c.name,
    c.event_count,
    c.risk_score,
    COUNT(DISTINCT e.source) as unique_sources
FROM intelligence_clusters c
LEFT JOIN intelligence_events e ON c.id = e.cluster_id
WHERE c.is_active = true
GROUP BY c.id
ORDER BY c.risk_score DESC
LIMIT 10;
```

---

## Known Issues & Limitations

### Issue 1: DBSCAN Sensitivity

**Problem:** DBSCAN parameters (eps, min_samples) are dataset-dependent

**Impact:**
- If eps too small: Most events become noise (no clustering)
- If eps too large: All events cluster together (over-clustering)

**Current:** eps=0.3, min_samples=10 (tuned empirically)

**Workaround:** Monitor clustering output, adjust if >20% events are noise

### Issue 2: Entity Extraction Accuracy

**Problem:** spaCy NER not 100% accurate for domain-specific entities

**Examples:**
- "Ukraine" correctly identified as GPE
- "Fed" sometimes missed (acronym)
- Product names may not be recognized

**Impact:** Incomplete entity coverage

**Workaround:** Use keyword extraction as fallback; fuzzy entity matching

### Issue 3: Sentiment Analysis Dependency

**Problem:** Sentiment scores come from Feed Service (content-analysis-v3)

**Impact:**
- Delayed enrichment (analysis may not be ready when article ingested)
- Accuracy depends on upstream service
- Missing sentiment = risk score less accurate

**Workaround:** Use default sentiment (0.0) if missing; backfill later

### Issue 4: Duplicate Detection False Negatives

**Problem:** Similar articles with different titles (e.g., different languages) not detected as duplicates

**Examples:**
- English: "Ukraine Wins Battle"
- Russian translation: "Украина выигрывает битву"
  → Not detected as duplicate (different words)

**Impact:** Slight over-counting of events (inflate risk)

**Workaround:** Accept minor duplication; could use translation API for multilingual detection

### Issue 5: Risk Score Calibration

**Problem:** Risk score weights (40/40/20) are tuned empirically, not theoretically

**Impact:**
- May not align with actual threat levels
- Weights may need adjustment as news patterns change

**Workaround:** Monitor risk_delta trends; validate against actual events

### Issue 6: Clustering Instability

**Problem:** DBSCAN results can change with slight data variations

**Impact:** Same cluster might be split/merged between runs

**Workaround:** Use cluster IDs as primary key; update cluster metadata, don't recreate

### Issue 7: Category Mapping Incompleteness

**Problem:** V3 has 14 categories, but dashboard only shows 4 (loses detail)

**Impact:** "Other" category captures events that don't fit 4 categories

**Workaround:** Could expand to 6-8 categories; requires frontend redesign

---

## Code Examples

### Example 1: Complete Ingestion Task

```python
from app.tasks.ingestion import ingest_recent_articles
from app.database import AsyncSessionLocal

# Run ingestion task (normally via Celery)
async def test_ingestion():
    async with AsyncSessionLocal() as db:
        result = await ingest_recent_articles(db, hours=1, limit=500)

        print(f"Ingestion complete:")
        print(f"  Fetched: {result['fetched']}")
        print(f"  Created: {result['created']}")
        print(f"  Duplicates: {result['duplicates']}")
        print(f"  Errors: {result['errors']}")

# Output:
# Ingestion complete:
#   Fetched: 145
#   Created: 128
#   Duplicates: 12
#   Errors: 5
```

### Example 2: Entity Extraction

```python
from app.services.event_detection import EventDetectionService

service = EventDetectionService()

text = """
Ukraine reported a major military victory today as forces advanced
into Russian-held territories near Donetsk. President Zelensky
confirmed the operation to Reuters and announced new sanctions
against Moscow.
"""

entities = service.extract_entities(text)
keywords = service.extract_keywords(text)

print("Entities:")
print(f"  Persons: {entities['persons']}")
print(f"  Organizations: {entities['organizations']}")
print(f"  Locations: {entities['locations']}")

print("Keywords:")
print(f"  {keywords}")

# Output:
# Entities:
#   Persons: ['Zelensky']
#   Organizations: ['Reuters', 'Ukraine']
#   Locations: ['Ukraine', 'Donetsk', 'Moscow']
# Keywords:
#   ['ukraine', 'military', 'victory', 'forces', 'russian', 'territories', 'donetsk', 'zelensky', 'sanctions', 'moscow']
```

### Example 3: Clustering Events

```python
from app.services.clustering import ClusteringService

service = ClusteringService()

events = [
    {"title": "Ukraine Wins Battle", "keywords": ["Ukraine", "War", "Defense"]},
    {"title": "Ukraine Military Advances", "keywords": ["Ukraine", "Army", "Russian"]},
    {"title": "Fed Raises Rates", "keywords": ["Fed", "Interest", "Rates"]},
    {"title": "ECB Monetary Policy", "keywords": ["ECB", "Rates", "Inflation"]},
    {"title": "Stock Market Surge", "keywords": ["Market", "Stocks", "Economy"]},
]

clusters = service.cluster_events(events)

for cluster_id, cluster_events in clusters.items():
    metadata = service.create_cluster_metadata(cluster_events)
    print(f"\nCluster {cluster_id}: {metadata['name']}")
    print(f"  Events: {metadata['event_count']}")
    print(f"  Keywords: {metadata['keywords'][:3]}")
    print(f"  Top sources: {[s['name'] for s in metadata['top_sources'][:2]]}")

# Output:
# Cluster 0: Ukraine War Defense
#   Events: 2
#   Keywords: ['Ukraine', 'War', 'Defense']
#   Top sources: ['Unknown', 'Unknown']
#
# Cluster 1: Fed Rates Monetary
#   Events: 2
#   Keywords: ['Fed', 'Rates', 'Interest']
#   Top sources: ['Unknown', 'Unknown']
#
# Cluster 2: Stock Market Economy
#   Events: 1
#   Keywords: ['Market', 'Stocks', 'Economy']
#   Top sources: ['Unknown', 'Unknown']
```

### Example 4: Risk Calculation

```python
from app.services.risk_scoring import RiskScoringService

scorer = RiskScoringService()

# Current metrics
current = {
    "article_count": 87,
    "avg_sentiment": -0.35,
    "unique_sources": 12
}

# Last week's metrics
last_week = {
    "risk_score": 1800,
    "article_count": 65,
    "avg_sentiment": -0.2,
    "unique_sources": 8
}

# Calculate risk
risk = scorer.calculate_risk_score(current, last_week)

print(f"Risk Score: {risk['risk_score']}")
print(f"Risk Delta: {risk['risk_delta']}%")

# Normalized display
def normalize(score):
    return min(100.0, (score / 3000.0) * 100.0)

print(f"Display Score: {normalize(risk['risk_score']):.1f}/100")

# Output:
# Risk Score: 2340.5
# Risk Delta: 30.0%
# Display Score: 78.0/100
```

### Example 5: API Response Building

```python
from app.routers.intelligence import normalize_risk_score
from datetime import datetime, timedelta
from sqlalchemy import select

async def get_cluster_overview(db, cluster_id):
    """Build detailed cluster response"""

    # Get cluster
    cluster = await db.execute(
        select(IntelligenceCluster).where(IntelligenceCluster.id == cluster_id)
    )
    cluster = cluster.scalar_one_or_none()

    if not cluster:
        return None

    # Get recent events for timeline
    cutoff = datetime.utcnow() - timedelta(days=7)
    events = await db.execute(
        select(IntelligenceEvent)
        .where(IntelligenceEvent.cluster_id == cluster_id)
        .where(IntelligenceEvent.published_at >= cutoff)
        .order_by(IntelligenceEvent.published_at.asc())
    )
    events = events.scalars().all()

    # Build timeline
    daily_data = {}
    for event in events:
        day = event.published_at.date()
        if day not in daily_data:
            daily_data[day] = {"count": 0, "sentiments": []}
        daily_data[day]["count"] += 1
        if event.sentiment:
            daily_data[day]["sentiments"].append(event.sentiment)

    timeline = []
    for day in sorted(daily_data.keys()):
        data = daily_data[day]
        avg_sentiment = sum(data["sentiments"]) / len(data["sentiments"]) if data["sentiments"] else 0.0
        timeline.append({
            "date": day.isoformat(),
            "event_count": data["count"],
            "avg_sentiment": round(avg_sentiment, 2)
        })

    # Build response
    return {
        "id": str(cluster.id),
        "name": cluster.name,
        "risk_score": normalize_risk_score(cluster.risk_score or 0),
        "risk_delta": cluster.risk_delta or 0,
        "event_count": cluster.event_count or 0,
        "keywords": cluster.keywords or [],
        "category": cluster.category,
        "timeline": timeline,
        "last_updated": cluster.last_updated.isoformat() if cluster.last_updated else None
    }

# Usage
response = await get_cluster_overview(db, cluster_id)
# Returns formatted response for API
```

---

## Appendix: Implementation Roadmap

### Phase 1: Core (Complete)
- [x] Event ingestion from Feed Service
- [x] Entity & keyword extraction
- [x] DBSCAN clustering
- [x] Risk scoring with deltas
- [x] REST API endpoints

### Phase 2: Analytics (Planned)
- [ ] Narrative frame detection
- [ ] Propaganda pattern extraction
- [ ] Source bias tracking
- [ ] Daily briefing generation

### Phase 3: Intelligence (Planned)
- [ ] Anomaly detection (unusual risk spikes)
- [ ] Predictive risk modeling
- [ ] Disinformation campaign detection
- [ ] Geopolitical early warning signals

### Phase 4: Integration (Planned)
- [ ] RabbitMQ event publishing
- [ ] Real-time ingestion (vs hourly)
- [ ] Narrative Service integration
- [ ] Alerting system

---

## Summary

The Intelligence Service is a sophisticated event correlation and risk analysis platform that transforms raw news into actionable intelligence. Its multi-layered architecture—from entity extraction through clustering to risk quantification—enables real-time threat awareness for geopolitical, financial, and security domains.

**Key Strengths:**
- Async architecture supports high concurrency
- DBSCAN avoids k-means limitations
- Multi-factor risk model captures nuance
- PostgreSQL JSONB enables flexible storage

**Key Challenges:**
- DBSCAN parameter tuning
- Entity extraction accuracy
- Sentiment analysis dependency
- Risk score calibration

The service is production-ready for the core intelligence pipeline and extensible for future narrative and propaganda analysis features.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-24
**Maintained By:** Engineering Team

# NLP Extraction Service Documentation

**Version:** 1.0.0
**Port:** 8115 (no longer active)
**Status:** 🗄️ ARCHIVED (2025-12-27) - Service decommissioned
**Archive Location:** `services/_archived/nlp-extraction-service-20251227/`
**Last Updated:** 2025-12-27

> ⚠️ **This service has been archived.** The NLP extraction functionality was deprecated
> as part of the content-analysis-v3 migration. Entity extraction is now handled by
> the content-analysis-v3-consumer. See the archived code for historical reference.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Service Overview](#2-service-overview)
3. [Architecture](#3-architecture)
4. [Core Components](#4-core-components)
5. [NLP Pipeline](#5-nlp-pipeline)
6. [API Endpoints](#6-api-endpoints)
7. [Database Schema](#7-database-schema)
8. [Performance Characteristics](#8-performance-characteristics)
9. [Configuration](#9-configuration)
10. [Deployment](#10-deployment)
11. [Security](#11-security)
12. [Monitoring & Observability](#12-monitoring--observability)
13. [Known Issues & Limitations](#13-known-issues--limitations)
14. [Development Guide](#14-development-guide)
15. [Appendices](#15-appendices)

---

## 1. Executive Summary

### 1.1 Purpose

The **nlp-extraction-service** provides high-performance, deterministic Natural Language Processing (NLP) capabilities for news article analysis using **spaCy** and **transformers**. It replaces expensive LLM-based analysis with **143x faster and 100% cheaper** rule-based and ML-based NLP.

**Key Value Proposition:**
- **Speed:** < 50ms per article (single query), < 200ms for 100 articles (batch)
- **Cost:** $0 per article (vs. $0.002-0.01 per LLM call)
- **Determinism:** Consistent, reproducible results (no LLM hallucinations)
- **Multilingual:** German (de_core_news_lg) and English (en_core_web_lg) support

### 1.2 Current Status

⚠️ **DEPRECATED SERVICE** - Not in production use as of 2025-11-09.

**Reason:** Service was planned as a split from `content-analysis-v2` but was never activated in production. The content-analysis-v2 service continues to handle NLP extraction in production.

**Action Items:**
- **Review Date:** 2025-12-09 (30 days)
- **Decision Pending:** Archive or reactivate
- **Codebase Status:** Complete and functional, but not deployed

### 1.3 Features

#### Phase 1 (Baseline - Implemented)
- ✅ **Named Entity Recognition (NER):** 18 entity types (PERSON, ORG, LOC, DATE, etc.)
- ✅ **Dependency Parsing:** Subject-Verb-Object (SVO) triples
- ✅ **Noun Chunks:** Multi-word entity extraction
- ✅ **POS Tagging:** Part-of-speech distribution analysis
- ✅ **Keyword Extraction:** Lemmatized important terms
- ✅ **Sentence Segmentation:** Sentence boundary detection
- ✅ **Quote Detection:** Direct speech extraction with speaker attribution

#### Phase 2A (Advanced NLP - Implemented)
- ✅ **Improved Quote Detection:** HTML-stripped, minimum length filter
- ✅ **Context Extraction:** Sentence before/after quotes
- ✅ **Speaker Attribution:** Dependency parsing-based speaker identification

#### Phase 2B (Sentiment & Relations - Implemented)
- ✅ **Sentiment Analysis (2B.2):** BERT-based (German) + VADER/TextBlob (English)
- ✅ **Entity Relations (2B.3):** Co-occurrence, temporal, affiliation
- ✅ **Entity Sentiments (2B.4):** Entity-level sentiment scores
- ✅ **Entity Centrality (2B.5):** Importance scoring (mentions, title, first sentence)
- ✅ **Quote Sentiments (2B.6):** Quote-speaker-sentiment attribution

### 1.4 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | 0.115.5 | REST API |
| **NLP Engine** | spaCy | 3.7.6 | Entity extraction, parsing |
| **German Model** | de_core_news_lg | 3.7.x | German NLP (500MB) |
| **English Model** | en_core_web_lg | 3.7.x | English NLP (500MB) |
| **Sentiment (German)** | transformers (BERT) | 4.36.2 | German sentiment analysis |
| **Sentiment (English)** | VADER + TextBlob | - | English sentiment analysis |
| **Database** | PostgreSQL | - | Extraction storage |
| **Cache** | Redis | - | Result caching |
| **Message Queue** | RabbitMQ | - | Event-driven processing |
| **Language Detection** | langdetect | 1.0.9 | Auto-detect article language |

---

## 2. Service Overview

### 2.1 Service Role in Ecosystem

The NLP Extraction Service acts as a **deterministic linguistic analysis layer** that processes articles in real-time as they are ingested by the feed-service.

```
┌─────────────────────────────────────────────────────────────┐
│                    Article Processing Pipeline               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Feed Service │────→│   RabbitMQ      │────→│ NLP Extract  │
│   (8101)     │     │ article.created │     │   Service    │
└──────────────┘     └─────────────────┘     │   (8115)     │
                                              └──────────────┘
                                                     ↓
                                              ┌──────────────┐
                                              │  PostgreSQL  │
                                              │ nlp_extractions│
                                              └──────────────┘
```

**Event Flow:**
1. **feed-service** publishes `article.created` event to RabbitMQ
2. **nlp-extraction-service** consumes event from queue
3. Fetches article content from feed-service API
4. Processes article with spaCy (entities, sentiment, relations)
5. Stores extraction results in PostgreSQL
6. Provides REST API for frontend/services to query results

### 2.2 Key Responsibilities

| Responsibility | Description | Performance Target |
|---------------|-------------|-------------------|
| **Entity Extraction** | Identify PERSON, ORG, LOC, DATE, etc. | < 50ms per article |
| **Sentiment Analysis** | Article + sentence-level sentiment | Included in 50ms |
| **Relation Extraction** | Entity co-occurrence, temporal, affiliation | Included in 50ms |
| **Quote Attribution** | Extract quotes with speaker identification | Included in 50ms |
| **Batch Processing** | Process multiple articles in single query | < 200ms for 100 |
| **Result Caching** | Redis-based result caching | 24h TTL |
| **Quality Filtering** | Remove noise entities (dates, numbers, etc.) | 4-stage pipeline |

### 2.3 Deployment Status

**Current State (as of 2025-11-24):**
- ✅ **Code Complete:** All Phase 1, 2A, 2B features implemented
- ✅ **Tests Present:** Unit tests in `tests/` directory
- ❌ **Not Deployed:** Service stopped by design in docker-compose
- ❌ **No Production Data:** Database schema exists but unpopulated
- ⚠️ **Pending Review:** Decision needed by 2025-12-09

**Why Deprecated:**
The service was originally planned to extract NLP extraction functionality from `content-analysis-v2` (which was handling both LLM analysis and spaCy extraction). However, the split was never activated in production, and content-analysis-v2 continues to handle both responsibilities.

**Options for Future:**
1. **Archive:** Remove service if content-analysis-v2 performs adequately
2. **Activate:** Deploy service to offload NLP from content-analysis-v2 (reduces load)
3. **Merge:** Integrate codebase back into content-analysis-v2

---

## 3. Architecture

### 3.1 Service Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                   NLP Extraction Service                       │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────┐          ┌─────────────────┐            │
│  │   FastAPI App   │          │ Realtime Worker │            │
│  │   (Port 8115)   │          │  (Background)   │            │
│  └────────┬────────┘          └────────┬────────┘            │
│           │                             │                      │
│           │                             │                      │
│  ┌────────▼─────────────────────────────▼────────┐           │
│  │          Core Business Logic Layer             │           │
│  ├────────────────────────────────────────────────┤           │
│  │  - BaseSpacyExtractor (NLP Processing)        │           │
│  │  - ExtractionService (DB Queries)             │           │
│  │  - Quality Filters (Entity Filtering)         │           │
│  │  - Sentiment Analyzers (BERT, VADER)          │           │
│  │  - Relation Extractors (Co-occurrence)        │           │
│  └────────┬────────────────────────┬──────────────┘           │
│           │                        │                          │
│  ┌────────▼────────┐      ┌───────▼──────────┐              │
│  │  spaCy Models   │      │  Transformers    │              │
│  │  - de_core_lg   │      │  - BERT German   │              │
│  │  - en_core_lg   │      │  - VADER English │              │
│  └─────────────────┘      └──────────────────┘              │
│                                                                │
├───────────────────────────────────────────────────────────────┤
│                    Data & Integration Layer                    │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │ PostgreSQL  │  │   Redis     │  │  RabbitMQ    │         │
│  │ (Extracts)  │  │  (Cache)    │  │  (Events)    │         │
│  └─────────────┘  └─────────────┘  └──────────────┘         │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 Component Interaction

```mermaid
sequenceDiagram
    participant FS as Feed Service
    participant RMQ as RabbitMQ
    participant NLP as NLP Worker
    participant Extractor as BaseSpacyExtractor
    participant DB as PostgreSQL
    participant API as NLP API

    Note over FS,RMQ: 1. Article Created Event
    FS->>RMQ: Publish article.created event

    Note over RMQ,NLP: 2. Event Consumption
    NLP->>RMQ: Consume event (article_id)

    Note over NLP,FS: 3. Fetch Article Content
    NLP->>FS: GET /api/v1/feeds/items/{id}
    FS-->>NLP: Article data (content, title, language)

    Note over NLP,Extractor: 4. NLP Processing
    NLP->>Extractor: extract(text, language, title)

    Note over Extractor: 5. Multi-Stage Processing
    Note over Extractor: - Detect language (if auto)
    Note over Extractor: - Strip HTML tags
    Note over Extractor: - spaCy NER extraction
    Note over Extractor: - Dependency parsing (SVO)
    Note over Extractor: - Sentiment analysis (BERT/VADER)
    Note over Extractor: - Entity relations (co-occurrence)
    Note over Extractor: - Entity centrality scoring
    Note over Extractor: - Quote attribution
    Note over Extractor: - Quality filtering (4 stages)

    Extractor-->>NLP: Extraction result (entities + metadata)

    Note over NLP,DB: 6. Store Results
    NLP->>DB: INSERT INTO extractions (...)

    Note over API,DB: 7. API Query (Later)
    API->>DB: SELECT * FROM extractions WHERE article_id=?
    DB-->>API: Extraction data
```

### 3.3 Processing Modes

The service supports two processing modes:

#### 1. Realtime Worker (Primary Mode)
- **Purpose:** Process articles as they arrive (event-driven)
- **Trigger:** `article.created` event from RabbitMQ
- **Latency:** < 50ms per article
- **Command:** `python -m app.workers.realtime_worker`
- **Scaling:** Multiple workers (prefetch count: 10)

#### 2. Batch Worker (Historical Processing)
- **Purpose:** Process large batches of historical articles
- **Trigger:** Manual invocation or scheduled job
- **Latency:** < 200ms per 100 articles
- **Command:** `python -m app.workers.batch_worker`
- **Rate Limit:** 100 articles/minute (configurable)

#### 3. REST API (Query Mode)
- **Purpose:** Serve extraction results to frontends/services
- **Endpoints:** Single article, batch query, statistics
- **Port:** 8115
- **Performance:** < 10ms database query (indexed)

---

## 4. Core Components

### 4.1 BaseSpacyExtractor

**Location:** `/app/nlp/extractors/base_extractor.py`
**Lines of Code:** ~919 lines
**Purpose:** Core NLP processing engine using spaCy

#### Key Features

1. **Singleton Pattern for Models**
   - spaCy models are loaded once per language (500MB each)
   - Models shared across all extractor instances
   - Memory-efficient: 2 models total (German + English)

2. **Language Auto-Detection**
   ```python
   def detect_language(text: str) -> str:
       # Uses langdetect on first 1000 chars
       # Returns: "de" | "en" (defaults to "en" on error)
   ```

3. **HTML Sanitization**
   - **Critical Fix (Phase 2B.1):** Strip HTML before NLP processing
   - **Reason:** Phase 2A quote detection extracted HTML attributes as quotes (`border="0"` → quote: "border=")
   - **Implementation:** BeautifulSoup4 text extraction + whitespace normalization

4. **Multi-Stage Quality Filtering**
   ```python
   # Stage 1: Basic quality (pattern matching, length, stopwords)
   entities = self.entity_filter.filter_entities(entities)

   # Stage 2: Temporal/Quantitative noise removal
   entities = [e for e in entities if e["label"] not in IGNORED_LABELS]
   # Filters: TIME, DATE, ORDINAL, CARDINAL, QUANTITY, PERCENT

   # Stage 3: Frequency filtering (remove single-mention false positives)
   entities = self._filter_by_frequency(entities, min_mentions=2)

   # Stage 4: Centrality-based Top-N filtering (keep most important)
   entities = self._apply_centrality_filtering(entities, max_entities=30)
   ```

#### Performance Characteristics

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| **Model Loading** | 2-3 seconds | Once per service start |
| **Language Detection** | < 1ms | First 1000 chars only |
| **HTML Stripping** | 5-10ms | Only if HTML detected |
| **spaCy Processing** | 20-40ms | Depends on article length |
| **Sentiment Analysis** | 10-20ms | BERT (German), VADER (English) |
| **Relation Extraction** | 5-10ms | Co-occurrence analysis |
| **Total Processing** | **40-80ms** | Target: < 50ms median |

#### Extracted Features

```python
result = {
    # Core Extraction (Phase 1)
    "entities": [...],              # 18 entity types
    "dependency_triples": [...],    # SVO relations
    "noun_chunks": [...],           # Multi-word entities
    "keywords": [...],              # Important terms (lemmatized)
    "sentences": [...],             # Sentence boundaries
    "quotes": [...],                # Direct speech + speakers

    # Sentiment Analysis (Phase 2B.2)
    "sentiment_overall": {...},     # Article-level sentiment
    "sentiment_sentences": [...],   # Per-sentence sentiment

    # Relations (Phase 2B.3)
    "entity_relations": {...},      # Co-occurrence, temporal, affiliation

    # Entity-Level Analysis (Phase 2B.4, 2B.5)
    "entity_sentiments": [...],     # Entity-specific sentiment
    "entity_centrality": [...],     # Importance scores

    # Quotes (Phase 2B.6)
    "quote_sentiments": [...],      # Quote + speaker + sentiment

    # Metadata
    "language": "de",
    "processing_time_ms": 45,
    "entity_count": 12,
    "entity_density": 2.3,          # Entities per 100 words
}
```

### 4.2 Sentiment Analysis System

**Location:** `/app/nlp/sentiment/`

#### German Sentiment (BERT-based)

```python
# Model: oliverguhr/german-sentiment-bert
# Approach: Transformers pipeline
# Performance: 15-20ms per article
# Accuracy: State-of-the-art for German news

from transformers import pipeline

sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="oliverguhr/german-sentiment-bert"
)

result = sentiment_analyzer(text)
# Returns: {"label": "positive", "score": 0.95}
```

**Output Format:**
```json
{
  "score": 0.65,          // -1.0 (negative) to +1.0 (positive)
  "label": "positive",    // "positive", "neutral", "negative"
  "confidence": 0.87,     // 0.0 to 1.0
  "model": "oliverguhr/german-sentiment-bert"
}
```

#### English Sentiment (VADER + TextBlob)

```python
# Approach: VADER (rule-based) + TextBlob (ML-based)
# Performance: 5-10ms per article
# Accuracy: Good for news, handles negation well

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

# VADER: Rule-based (fast, handles slang/emoticons)
vader = SentimentIntensityAnalyzer()
vader_scores = vader.polarity_scores(text)

# TextBlob: Pattern-based (handles subjectivity)
blob = TextBlob(text)
textblob_score = blob.sentiment.polarity

# Combine scores (weighted average)
final_score = 0.6 * vader_scores["compound"] + 0.4 * textblob_score
```

#### Sentence-Level Sentiment

```python
# Process first 20 sentences (performance optimization)
# Full article sentiment already captures overall tone

MAX_SENTENCES = 20
sentences_to_analyze = sentences[:MAX_SENTENCES]

sentence_sentiments = [
    {
        "sentence_idx": 0,
        "text": "Die Wirtschaft wächst stark.",
        "score": 0.82,
        "label": "positive",
        "confidence": 0.91
    },
    # ...
]
```

### 4.3 Entity Relation Extraction

**Location:** `/app/nlp/relations/`

#### Co-occurrence Relations

**Principle:** Entities mentioned in the same sentence/paragraph are likely related.

```python
# Example: "Merkel und Scholz diskutieren über die Wirtschaft."
# Entities: [Merkel (PERSON), Scholz (PERSON), Wirtschaft (ORG)]

relations = [
    {
        "entity1": "Merkel",
        "entity2": "Scholz",
        "relation_type": "co-occurrence",
        "confidence": 0.8,
        "context": "same_sentence",
        "sentence_idx": 3
    },
    {
        "entity1": "Merkel",
        "entity2": "Wirtschaft",
        "relation_type": "co-occurrence",
        "confidence": 0.6,
        "context": "verb_link",  # Connected via verb "diskutieren"
        "verb": "diskutieren"
    }
]
```

#### Temporal Relations

**Principle:** Date/time entities linked to events/entities in temporal context.

```python
# Example: "Am 15. März kündigte Merkel neue Maßnahmen an."

relations = [
    {
        "entity": "Merkel",
        "temporal_marker": "15. März",
        "relation_type": "temporal",
        "event": "kündigte ... an",
        "confidence": 0.9
    }
]
```

#### Affiliation Relations

**Principle:** Detect organizational membership (PERSON → ORG).

```python
# Example: "Bundeskanzlerin Merkel von der CDU..."

relations = [
    {
        "person": "Merkel",
        "organization": "CDU",
        "relation_type": "affiliation",
        "title": "Bundeskanzlerin",
        "confidence": 0.95
    }
]
```

### 4.4 Entity Centrality Scoring

**Location:** `/app/nlp/analysis/entity_centrality.py`

**Purpose:** Rank entities by importance in article using multiple signals.

#### Scoring Algorithm

```python
def calculate_entity_centrality(doc, entities, title, dependency_triples):
    """
    Multi-factor centrality scoring:

    1. Title Presence Boost (+30 points)
       - Entity appears in article title

    2. First Sentence Boost (+20 points)
       - Entity in first sentence (lede)

    3. Mention Frequency (variable)
       - Base: Count of entity mentions
       - Normalized to 0-50 range

    4. Syntactic Role Bonus (+10 per SVO role)
       - Subject in dependency triple
       - Object in dependency triple
       - Part of verb phrase

    Total Score = Title + FirstSent + Frequency + Syntax
    Max Possible Score = 30 + 20 + 50 + 30 = 130 points
    """
```

**Example Output:**
```json
[
    {
        "entity": "Angela Merkel",
        "centrality": {
            "score": 95,
            "in_title": true,
            "in_first_sentence": true,
            "mention_count": 8,
            "syntactic_roles": ["subject", "object"]
        }
    },
    {
        "entity": "CDU",
        "centrality": {
            "score": 42,
            "in_title": false,
            "in_first_sentence": true,
            "mention_count": 3,
            "syntactic_roles": ["object"]
        }
    }
]
```

**Usage in Filtering:**
- Stage 4 of entity filtering uses centrality scores
- Keep top-N entities by centrality (default: 30)
- Ensures most important entities are retained

### 4.5 Quote Attribution System

**Location:** `/app/nlp/quotes/quote_sentiment.py`

#### Multi-Strategy Speaker Detection

```python
# Strategy 1: Dependency Parsing (Highest Confidence: 0.9)
# Find subject of speech verbs (say, tell, ask, etc.)
SPEECH_VERBS = {"say", "tell", "ask", "sagen", "erzählen", ...}

for token in sentence:
    if token.lemma in SPEECH_VERBS:
        subject = find_subject(token)
        if subject in entities:
            return (subject, 0.9)

# Strategy 2: Proximity Before Quote (Medium Confidence: 0.7)
# Find closest PERSON/ORG entity before the quote
entities_before_quote = [e for e in entities if e.end < quote_start]
closest = max(entities_before_quote, key=lambda e: e.end)
return (closest, 0.7)

# Strategy 3: Proximity After Quote (Low Confidence: 0.5)
# Find closest entity after the quote (less reliable)
entities_after_quote = [e for e in entities if e.start > quote_end]
closest = min(entities_after_quote, key=lambda e: e.start)
return (closest, 0.5)
```

#### Quote Sentiment Analysis

```python
# Combine quote extraction with sentiment analysis
quote_sentiments = [
    {
        "quote": "Wir schaffen das",
        "speaker": "Merkel",
        "speaker_confidence": 0.9,
        "sentiment": {
            "score": 0.75,
            "label": "positive",
            "confidence": 0.88
        },
        "context_before": "Merkel sagte:",
        "context_after": "Das ist unser Ziel.",
        "sentence_idx": 3
    }
]
```

---

## 5. NLP Pipeline

### 5.1 Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Article Input                              │
│  - Text content (full article or RSS description)          │
│  - Language (de/en or auto-detect)                         │
│  - Title (for centrality scoring)                          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Pre-Processing Stage                          │
│  1. Language Detection (if auto)                           │
│  2. Content Length Validation (100-50,000 chars)           │
│  3. HTML Tag Detection & Stripping (if present)            │
│  4. Whitespace Normalization                               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            spaCy NLP Processing (Core)                      │
│  - Tokenization                                            │
│  - POS Tagging                                             │
│  - Dependency Parsing                                      │
│  - Named Entity Recognition (NER)                          │
│  - Sentence Segmentation                                   │
│  - Noun Chunk Extraction                                   │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Feature Extraction Stage                           │
│  - Entities (18 types)                                     │
│  - Dependency Triples (SVO)                                │
│  - Noun Chunks                                             │
│  - Keywords (lemmatized)                                   │
│  - Sentences                                               │
│  - Quotes (with regex pattern matching)                    │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Advanced Analysis Stage (Phase 2B)                 │
│  1. Sentiment Analysis                                     │
│     - Article-level (BERT/VADER)                           │
│     - Sentence-level (first 20 sentences)                  │
│  2. Entity Relations                                       │
│     - Co-occurrence (same sentence)                        │
│     - Temporal (date linkage)                              │
│     - Affiliation (PERSON → ORG)                           │
│  3. Entity Sentiments                                      │
│     - Link entities to sentence sentiments                 │
│  4. Entity Centrality                                      │
│     - Title presence, first sentence, frequency, syntax    │
│  5. Quote Sentiments                                       │
│     - Speaker attribution + sentiment                      │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Quality Filtering Stage (4 Stages)                 │
│  Stage 1: Basic Quality Filter                             │
│   - Remove patterns (URLs, emails, phone numbers)          │
│   - Length constraints (2-100 chars)                       │
│   - Stopword filtering                                     │
│                                                             │
│  Stage 2: Temporal/Quantitative Noise                      │
│   - Remove: TIME, DATE, ORDINAL, CARDINAL, QUANTITY        │
│                                                             │
│  Stage 3: Frequency Filtering                              │
│   - Minimum mentions: 2 (configurable)                     │
│   - Removes single-mention false positives                 │
│                                                             │
│  Stage 4: Centrality-Based Top-N                           │
│   - Keep top 30 entities by centrality score               │
│   - Ensures most important entities retained               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 Result Assembly                             │
│  - Combine all extracted features                          │
│  - Calculate metadata (entity_count, density)              │
│  - Add performance metrics (processing_time_ms)            │
│  - Format for database storage                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Database Storage (PostgreSQL)                    │
│  Schema: nlp_extractions.extractions                       │
│  - Indexed by article_id                                   │
│  - JSONB columns for flexibility                           │
│  - Unique constraint: (article_id, extractor_version)      │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Processing Time Breakdown

**Target Article:** 500 words, German language

| Stage | Time | Percentage | Notes |
|-------|------|------------|-------|
| **Language Detection** | 0.5ms | 1% | First 1000 chars only |
| **HTML Stripping** | 8ms | 16% | Only if HTML detected |
| **spaCy Processing** | 25ms | 50% | Tokenization, NER, parsing |
| **Sentiment Analysis** | 12ms | 24% | BERT (German) |
| **Relation Extraction** | 3ms | 6% | Co-occurrence analysis |
| **Centrality Scoring** | 1ms | 2% | Simple counting + lookup |
| **Quote Sentiments** | 0.5ms | 1% | Regex + dependency parsing |
| **Total** | **50ms** | **100%** | Within target |

**Scaling Characteristics:**
- **Linear with article length** (up to 50,000 chars)
- **Independent of entity count** (filtering is fast)
- **Parallelizable:** Multiple workers can process concurrently

---

## 6. API Endpoints

### 6.1 Endpoint Overview

| Endpoint | Method | Purpose | Rate Limit | Target Latency |
|----------|--------|---------|------------|----------------|
| `/` | GET | Service info | - | < 1ms |
| `/health` | GET | Health check | - | < 5ms |
| `/ready` | GET | Readiness probe | - | < 10ms |
| `/api/v1/extractions/stats` | GET | Statistics | 100/min | < 50ms |
| `/api/v1/extractions/{article_id}` | GET | Single extraction | 60/min | < 50ms |
| `/api/v1/extractions/batch` | POST | Batch extraction | 10/min | < 200ms |

### 6.2 GET /api/v1/extractions/{article_id}

**Purpose:** Retrieve NLP extraction for a single article.

**Path Parameters:**
- `article_id` (string, required): Article UUID

**Response 200 (Success):**
```json
{
  "article_id": "123e4567-e89b-12d3-a456-426614174000",
  "language": "de",
  "extractor_version": "base_v1",
  "model_version": "de_core_news_lg-3.7.0",
  "created_at": "2025-11-24T10:30:00Z",
  "processing_time_ms": 45,
  "content_length": 1234,
  "entity_count": 12,
  "entity_density": 2.3,
  "entities": [
    {
      "text": "Angela Merkel",
      "label": "PER",
      "start": 0,
      "end": 13,
      "start_char": 0,
      "end_char": 13
    }
  ],
  "entity_sentiments": [
    {
      "entity": "Angela Merkel",
      "sentiment": {
        "score": 0.65,
        "label": "positive",
        "confidence": 0.87
      },
      "mention_count": 8
    }
  ],
  "entity_centrality": [
    {
      "entity": "Angela Merkel",
      "centrality": {
        "score": 95,
        "in_title": true,
        "in_first_sentence": true,
        "mention_count": 8,
        "syntactic_roles": ["subject", "object"]
      }
    }
  ],
  "quote_sentiments": [
    {
      "quote": "Wir schaffen das",
      "speaker": "Merkel",
      "speaker_confidence": 0.9,
      "sentiment": {
        "score": 0.75,
        "label": "positive",
        "confidence": 0.88
      },
      "sentence_idx": 3
    }
  ],
  "sentiment_overall": {
    "score": 0.65,
    "label": "positive",
    "confidence": 0.87,
    "model": "oliverguhr/german-sentiment-bert"
  },
  "keywords": [
    {"text": "Merkel", "lemma": "merkel", "pos": "PROPN"},
    {"text": "Politik", "lemma": "politik", "pos": "NOUN"}
  ]
}
```

**Response 404 (Not Found):**
```json
{
  "error": "NOT_FOUND",
  "message": "NLP extraction not found for article",
  "details": {
    "article_id": "123e4567-e89b-12d3-a456-426614174000",
    "note": "Article may not have been processed yet"
  },
  "path": "/api/v1/extractions/123e4567-e89b-12d3-a456-426614174000"
}
```

**Response 400 (Invalid UUID):**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid UUID format: not-a-uuid",
  "details": {"article_id": "not-a-uuid"},
  "path": "/api/v1/extractions/not-a-uuid"
}
```

**Response 503 (Query Timeout):**
```json
{
  "error": "SERVICE_UNAVAILABLE",
  "message": "Database query exceeded timeout - please try again later",
  "details": {"article_id": "..."},
  "query_info": {
    "article_id": "...",
    "operation": "single_fetch"
  }
}
```

**Performance Headers:**
```
X-Processing-Time: 45.32ms
```

### 6.3 POST /api/v1/extractions/batch

**Purpose:** Retrieve NLP extractions for multiple articles in a single query.

**Request Body:**
```json
{
  "article_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
  ]
}
```

**Constraints:**
- Minimum: 1 article
- Maximum: 100 articles per request
- All IDs must be valid UUIDs

**Response 200 (Success):**
```json
{
  "total_requested": 3,
  "total_found": 2,
  "total_not_found": 1,
  "not_found_ids": [
    "323e4567-e89b-12d3-a456-426614174002"
  ],
  "extractions": [
    {
      "article_id": "123e4567-e89b-12d3-a456-426614174000",
      "entities": [...],
      // ... full extraction data
    },
    {
      "article_id": "223e4567-e89b-12d3-a456-426614174001",
      "entities": [...],
      // ... full extraction data
    }
  ]
}
```

**Response 400 (Invalid Request):**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Maximum 100 article IDs allowed per request, got 150",
  "details": {
    "requested_count": 150,
    "max_allowed": 100
  },
  "path": "/api/v1/extractions/batch"
}
```

**Performance:**
- **Database Query:** Single query with `IN` clause
- **Target Latency:** < 200ms for 100 articles
- **Typical Latency:** 100-150ms for 100 articles

### 6.4 GET /api/v1/extractions/stats

**Purpose:** Get extraction statistics for monitoring and health checks.

**Response 200:**
```json
{
  "total_extractions": 22021,
  "with_phase2b_sentiments": 15430,
  "with_phase2b_centrality": 15430,
  "with_phase2b_quotes": 8200,
  "phase2b_coverage_pct": 70.05
}
```

**Use Cases:**
- **Monitoring:** Track processing progress
- **Health Checks:** Verify service is processing articles
- **Analytics:** Measure Phase 2B feature adoption

---

## 7. Database Schema

### 7.1 Schema Overview

**Schema Name:** `nlp_extractions`
**Primary Table:** `extractions`
**Supporting Tables:** `batch_progress`, `failed_extractions`

### 7.2 Table: extractions

**Purpose:** Store spaCy entity extraction results with Phase 2B features.

```sql
CREATE TABLE nlp_extractions.extractions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    article_id UUID NOT NULL,

    -- Version Control (for A/B testing)
    extractor_version VARCHAR(50) NOT NULL,  -- "base_v1", "refined_v1", "custom_v1"
    model_version VARCHAR(50) NOT NULL,      -- "de_core_news_lg-3.7.0"

    -- Core Extracted Data (JSONB for flexibility)
    entities JSONB NOT NULL,                 -- [{text, label, start, end, ...}]
    dependency_triples JSONB,                -- [{subject, verb, object, ...}]
    noun_chunks JSONB,                       -- [{text, root_text, ...}]

    -- Linguistic Features
    language VARCHAR(10),                    -- "de" | "en"
    pos_distribution JSONB,                  -- {"NOUN": 120, "VERB": 45, ...}

    -- Content Metadata
    content_length INTEGER,                  -- Character count
    content_type VARCHAR(20),                -- "full" | "rss_only"
    entity_count INTEGER,                    -- Total entities extracted
    entity_density FLOAT,                    -- Entities per 100 words

    -- Performance Metrics
    processing_time_ms INTEGER,              -- Processing time in milliseconds
    cache_hit BOOLEAN DEFAULT FALSE,

    -- Phase 2A: Advanced NLP Features
    keywords JSONB,                          -- [{text, lemma, pos}]
    sentence_count INTEGER,                  -- Number of sentences
    sentences JSONB,                         -- [{text, start, end, ...}]
    quotes JSONB,                            -- [{quote, speaker, sentence_idx, ...}]

    -- Phase 2B: Advanced Analysis Features
    sentiment_overall JSONB,                 -- {score, label, confidence, model}
    sentiment_sentences JSONB,               -- [{sentence_idx, score, label, ...}]
    entity_relations JSONB,                  -- {co-occurrence, temporal, affiliation}
    entity_sentiments JSONB,                 -- [{entity, sentiment, mention_count}]
    entity_centrality JSONB,                 -- [{entity, centrality: {score, ...}}]
    quote_sentiments JSONB,                  -- [{quote, speaker, sentiment, ...}]

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_extractions_article_version UNIQUE (article_id, extractor_version)
);

-- Indexes for Performance
CREATE INDEX idx_extractions_article ON nlp_extractions.extractions(article_id);
CREATE INDEX idx_extractions_created ON nlp_extractions.extractions(created_at);
CREATE INDEX idx_extractions_version ON nlp_extractions.extractions(extractor_version);

-- GIN indexes for JSONB queries (full-text search on entities)
CREATE INDEX idx_extractions_entities ON nlp_extractions.extractions USING GIN(entities);
CREATE INDEX idx_extractions_keywords ON nlp_extractions.extractions USING GIN(keywords);
CREATE INDEX idx_extractions_quotes ON nlp_extractions.extractions USING GIN(quotes);
```

**Storage Estimates:**
- **Average Row Size:** 15-20 KB (JSONB compression)
- **100,000 articles:** ~1.5-2 GB
- **1,000,000 articles:** ~15-20 GB

### 7.3 Table: batch_progress

**Purpose:** Track progress of batch processing jobs (historical article processing).

```sql
CREATE TABLE nlp_extractions.batch_progress (
    id SERIAL PRIMARY KEY,

    -- Batch Information
    batch_name VARCHAR(100),                 -- "historical_batch_001"
    total_articles INTEGER,                  -- Total articles in batch
    processed_articles INTEGER,              -- Successfully processed
    failed_articles INTEGER,                 -- Failed processing

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Status
    status VARCHAR(20),                      -- "running" | "completed" | "failed"
    extractor_version VARCHAR(50)            -- Version used for this batch
);
```

**Use Cases:**
- Monitor progress of historical backfill jobs
- Generate progress reports
- Track processing failures

### 7.4 Table: failed_extractions

**Purpose:** Track failed extraction attempts for retry and debugging.

```sql
CREATE TABLE nlp_extractions.failed_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    article_id UUID NOT NULL,

    -- Error Information
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_failed_extractions_article ON nlp_extractions.failed_extractions(article_id);
```

**Common Error Types:**
- `content_too_short`: < 100 characters
- `content_too_long`: > 50,000 characters (truncated)
- `spacy_error`: spaCy processing failure
- `unsupported_language`: Language not supported (only de/en)
- `failed_to_fetch_article`: feed-service API error

---

## 8. Performance Characteristics

### 8.1 API Latency

**Measured Performance (PostgreSQL, indexed queries):**

| Operation | Target | Typical | p95 | p99 | Notes |
|-----------|--------|---------|-----|-----|-------|
| **Single Article** | < 50ms | 10-20ms | 30ms | 45ms | Database query only |
| **Batch (10 articles)** | < 100ms | 40-60ms | 80ms | 95ms | Single query with IN |
| **Batch (100 articles)** | < 200ms | 120-150ms | 180ms | 195ms | Single query with IN |
| **Stats Endpoint** | < 50ms | 15-25ms | 40ms | 48ms | Aggregation query |

**HTTP Response Headers:**
```
X-Processing-Time: 12.45ms  # Database query + serialization
```

### 8.2 NLP Processing Performance

**Baseline Article:** 500 words, German language

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Processing Time** | 45-50ms | Median |
| **p95 Processing Time** | 75ms | 95th percentile |
| **p99 Processing Time** | 100ms | 99th percentile |
| **Throughput** | 20 articles/sec | Per worker |
| **Parallel Workers** | 2-10 | Configurable (REALTIME_WORKERS) |
| **Total Throughput** | 40-200 articles/sec | 2-10 workers |

**Processing Time by Article Length:**

| Article Length | Processing Time | Throughput |
|----------------|----------------|------------|
| **100-200 words** | 20-30ms | 40 articles/sec |
| **200-500 words** | 30-50ms | 25 articles/sec |
| **500-1000 words** | 50-80ms | 15 articles/sec |
| **1000-2000 words** | 80-120ms | 10 articles/sec |
| **2000+ words** | 120-200ms | 6 articles/sec |

### 8.3 Memory Usage

**spaCy Model Memory (Per Worker):**

| Component | Memory | Notes |
|-----------|--------|-------|
| **de_core_news_lg** | 500 MB | German model (loaded once) |
| **en_core_web_lg** | 500 MB | English model (loaded once) |
| **BERT Sentiment** | 400 MB | German sentiment model |
| **Base Python Process** | 100 MB | FastAPI + dependencies |
| **Total Per Worker** | **1.5 GB** | Peak usage |

**Scaling Considerations:**
- **Singleton Pattern:** Models loaded once per service, shared across requests
- **Worker Memory:** 1.5 GB × number of workers
- **Recommended:** 4 GB RAM per worker (includes OS + overhead)
- **Max Workers:** 2-4 on 8 GB server, 4-8 on 16 GB server

### 8.4 Database Performance

**Query Patterns:**

| Query Type | Index Used | Typical Time | Notes |
|------------|-----------|--------------|-------|
| **Single Article** | `idx_extractions_article` | 5-10ms | B-tree index on UUID |
| **Batch (100)** | `idx_extractions_article` | 80-120ms | IN clause, single query |
| **Entity Search** | `idx_extractions_entities` | 50-100ms | GIN index on JSONB |
| **Stats Query** | Table scan | 15-25ms | Aggregation, no filter |

**Index Sizes (100,000 articles):**

| Index | Size | Type | Purpose |
|-------|------|------|---------|
| `idx_extractions_article` | 20 MB | B-tree | Article lookup |
| `idx_extractions_entities` | 150 MB | GIN | JSONB full-text search |
| `idx_extractions_keywords` | 80 MB | GIN | Keyword search |
| `idx_extractions_quotes` | 40 MB | GIN | Quote search |

### 8.5 Cost Comparison: spaCy vs. LLM

**Scenario:** Process 1 million articles

| Approach | Cost per Article | Total Cost | Processing Time | Notes |
|----------|-----------------|------------|-----------------|-------|
| **spaCy (this service)** | $0.00 | **$0** | 50ms | Free, deterministic |
| **OpenAI GPT-4 Turbo** | $0.01 | $10,000 | 500-1000ms | Expensive, variable |
| **OpenAI GPT-3.5 Turbo** | $0.002 | $2,000 | 300-500ms | Cheaper, less accurate |
| **Anthropic Claude 3** | $0.004 | $4,000 | 400-800ms | Good quality |

**Cost Savings:**
- **vs. GPT-4 Turbo:** $10,000 saved (100% cheaper)
- **vs. GPT-3.5 Turbo:** $2,000 saved (100% cheaper)
- **vs. Claude 3:** $4,000 saved (100% cheaper)

**Performance Advantage:**
- **10-20x faster** than LLM-based analysis
- **Deterministic:** Same input = same output (no hallucinations)
- **Offline:** No API rate limits or downtime

---

## 9. Configuration

### 9.1 Environment Variables

**Configuration File:** `.env` (copy from `.env.example`)

#### Required Variables

```bash
# PostgreSQL connection string
DATABASE_URL=postgresql://news_user:your_db_password@postgres:5432/news_mcp

# Redis connection string (for caching)
REDIS_URL=redis://redis:6379/3

# RabbitMQ connection string (for event processing)
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

#### Service Configuration

```bash
# Service identity
SERVICE_NAME=nlp-extraction-service
SERVICE_PORT=8115
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# spaCy Models
SPACY_MODEL_DE=de_core_news_lg      # German model (500MB)
SPACY_MODEL_EN=en_core_web_lg        # English model (500MB)
EXTRACTOR_VERSION=base_v1            # base_v1, refined_v1, custom_v1
```

#### Database Configuration

```bash
# Schema and connection pooling
DATABASE_SCHEMA=nlp_extractions
DATABASE_POOL_SIZE=10                # Connection pool size
DATABASE_MAX_OVERFLOW=20             # Max overflow connections

# Query Timeout Protection (H.H2 - Production Hardening)
QUERY_TIMEOUT_SECONDS=30             # 5-300 seconds, default: 30
```

#### Circuit Breaker Configuration (H.H3)

```bash
# Circuit breaker protection (prevents connection pool exhaustion)
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5   # Open after N failures (2-20, default: 5)
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2   # Close after N successes (1-10, default: 2)
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60    # Wait N seconds before retry (10-300s, default: 60s)
```

#### Redis Configuration

```bash
# Caching (extraction results)
ENABLE_CACHE=true
CACHE_TTL=86400                      # 24 hours (in seconds)
```

#### RabbitMQ Configuration

```bash
# Queue names
RABBITMQ_REALTIME_QUEUE=nlp_extraction_realtime_queue
RABBITMQ_BATCH_QUEUE=nlp_extraction_batch_queue

# TLS Configuration (disabled for development)
RABBITMQ_TLS_ENABLED=false
RABBITMQ_TLS_CA_CERT=/etc/rabbitmq/certs/ca-cert.pem
RABBITMQ_TLS_VERIFY_HOSTNAME=true
```

#### Worker Configuration

```bash
# Worker modes and scaling
WORKER_MODE=realtime                 # "realtime" | "batch"
WORKER_PREFETCH_COUNT=10             # Messages to prefetch per worker
REALTIME_WORKERS=2                   # Number of realtime workers
BATCH_WORKERS=1                      # Number of batch workers
```

#### Processing Configuration

```bash
# Rate limiting and batch sizes
BATCH_RATE_LIMIT=100                 # Articles per minute (batch mode)
BATCH_SIZE=500                       # Articles per batch iteration
MAX_CONTENT_LENGTH=50000             # Max chars to process
MIN_CONTENT_LENGTH=100               # Min chars to process
PROCESSING_TIMEOUT=30                # Processing timeout (seconds)
```

#### Entity Quality Filtering

```bash
# Quality filters (4-stage pipeline)
ENABLE_ENTITY_FILTER=true
MIN_ENTITY_LENGTH=2                  # Minimum entity text length
MAX_ENTITY_LENGTH=100                # Maximum entity text length
MIN_ENTITY_MENTIONS=2                # Min mentions to keep (1-10, default: 2)
MAX_ENTITIES_PER_ARTICLE=30          # Max entities per article (10-100, default: 30)
```

#### Monitoring & Metrics

```bash
# Prometheus metrics
ENABLE_METRICS=true
METRICS_PORT=9115

# Tracing and error tracking
ENABLE_TRACING=false
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

#### Phase Control

```bash
# Feature flags (gradual rollout)
CURRENT_PHASE=phase1                 # phase1, phase2, phase3
ENABLE_DEPENDENCY_PARSING=true       # SVO triple extraction
ENABLE_NOUN_CHUNKS=true              # Noun chunk extraction
ENABLE_CUSTOM_PATTERNS=false         # EntityRuler patterns (Phase 2+)
```

### 9.2 Configuration Validation

All configuration is validated on startup using Pydantic:

```python
# Example: Port validation
@field_validator('SERVICE_PORT', 'METRICS_PORT')
def validate_port(cls, v: int) -> int:
    if not 1024 <= v <= 65535:
        raise ValueError(f"Port must be between 1024 and 65535, got {v}")
    return v

# Example: Batch rate limit validation
@field_validator('BATCH_RATE_LIMIT')
def validate_batch_rate(cls, v: int) -> int:
    if v < 1 or v > 100:
        raise ValueError("BATCH_RATE_LIMIT must be between 1 and 100")
    return v
```

**Startup Behavior:**
- Invalid configuration → Service fails to start
- Missing required variables → Clear error message
- Out-of-range values → Clear error message with constraints

---

## 10. Deployment

### 10.1 Docker Deployment (Development)

**Current Status:** ⚠️ Service is NOT deployed in production (stopped by design)

#### Docker Compose Configuration

```yaml
# ⚠️ DEPRECATED: nlp-extraction-service (2025-11-09)
# Status: Not in production use, stopped by design
# Review Date: 2025-12-09 (30 days)

nlp-extraction-realtime-1:
  build:
    context: .
    dockerfile: services/nlp-extraction-service/Dockerfile.dev
  container_name: news-nlp-extraction-realtime-1
  restart: no  # Stopped by design
  command: python -m app.workers.realtime_worker
  environment:
    SERVICE_NAME: nlp-extraction-service
    SERVICE_PORT: 8115
    LOG_LEVEL: INFO
    DATABASE_URL: postgresql://news_user:your_db_password@postgres:5432/news_mcp
    REDIS_URL: redis://redis:6379/3
    RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/
    WORKER_MODE: realtime
    WORKER_PREFETCH_COUNT: 10
  depends_on:
    - postgres
    - redis
    - rabbitmq
  volumes:
    - ./services/nlp-extraction-service/app:/app/app  # Hot-reload
  networks:
    - news-network

nlp-extraction-api:
  build:
    context: .
    dockerfile: services/nlp-extraction-service/Dockerfile.dev
  container_name: news-nlp-extraction-api
  restart: no  # Stopped by design
  command: uvicorn app.main:app --host 0.0.0.0 --port 8115 --reload
  ports:
    - "8115:8115"  # API endpoint
  environment:
    # Same as worker
  depends_on:
    - postgres
    - redis
  volumes:
    - ./services/nlp-extraction-service/app:/app/app  # Hot-reload
  networks:
    - news-network
```

#### Dockerfile (Development)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl build-essential gcc g++ postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY services/nlp-extraction-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models (500MB-1GB each)
RUN python -m spacy download de_core_news_lg && \
    python -m spacy download en_core_web_lg

# Copy Alembic configuration and migrations
COPY services/nlp-extraction-service/alembic.ini ./
COPY services/nlp-extraction-service/alembic ./alembic

# Copy application code
COPY services/nlp-extraction-service/app ./app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Default command (realtime worker)
CMD ["python", "-m", "app.workers.realtime_worker"]
```

**Build Time:** 5-8 minutes (spaCy model downloads)
**Image Size:** ~2.5 GB (Python + spaCy models)

### 10.2 Deployment Checklist

**If reactivating service:**

#### Prerequisites
- [ ] PostgreSQL database available
- [ ] Redis cache available
- [ ] RabbitMQ message broker available
- [ ] 4-8 GB RAM per worker
- [ ] CPU: 2+ cores recommended

#### Database Setup
```bash
# Run Alembic migrations
docker exec -it news-nlp-extraction-api alembic upgrade head

# Verify schema created
docker exec -it postgres psql -U news_user -d news_mcp \
  -c "\dt nlp_extractions.*"
```

#### Configuration
- [ ] Set all required environment variables
- [ ] Configure circuit breaker thresholds
- [ ] Set query timeout protection
- [ ] Configure worker count (REALTIME_WORKERS)
- [ ] Set rate limits (BATCH_RATE_LIMIT)

#### Smoke Tests
```bash
# 1. Health check
curl http://localhost:8115/health

# 2. Readiness check
curl http://localhost:8115/ready

# 3. Stats endpoint
curl http://localhost:8115/api/v1/extractions/stats

# 4. Single article (requires article_id)
curl http://localhost:8115/api/v1/extractions/{article_id}
```

#### Monitoring Setup
- [ ] Configure Prometheus metrics (port 9115)
- [ ] Set up Grafana dashboards
- [ ] Configure Sentry error tracking (optional)
- [ ] Set up log aggregation (ELK/Loki)

### 10.3 Scaling Strategy

**Horizontal Scaling:**

```yaml
# Scale realtime workers (docker-compose)
nlp-extraction-realtime-1:
  deploy:
    replicas: 4  # 4 workers
```

**Recommended Scaling:**

| Load | Workers | RAM | CPU | Throughput |
|------|---------|-----|-----|------------|
| **Light** (< 10 articles/sec) | 2 | 8 GB | 2 cores | 40 articles/sec |
| **Medium** (10-50 articles/sec) | 4 | 16 GB | 4 cores | 80 articles/sec |
| **Heavy** (50-100 articles/sec) | 8 | 32 GB | 8 cores | 160 articles/sec |

**Bottlenecks:**
1. **spaCy Processing:** CPU-bound (parallelize with workers)
2. **BERT Sentiment:** CPU/GPU-bound (use GPU for 3-5x speedup)
3. **Database Writes:** I/O-bound (connection pooling helps)

---

## 11. Security

### 11.1 Security Hardening (H.H10)

#### Security Headers (All Responses)

```python
# Middleware: add_security_headers
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
response.headers["Referrer-Policy"] = "no-referrer"
response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
```

#### Query Timeout Protection (H.H2)

**Purpose:** Prevent indefinite database blocking from slow queries.

```python
# Configuration
QUERY_TIMEOUT_SECONDS=30  # Cancel queries exceeding 30 seconds

# Implementation
DATABASE_URL += f"?options=-c%20statement_timeout%3D{timeout_ms}"
```

**Error Handling:**
```python
try:
    result = db.execute(query)
except OperationalError as e:
    if "canceling statement due to statement timeout" in str(e):
        raise QueryTimeoutError(message="Query timeout exceeded")
```

#### Circuit Breaker Pattern (H.H3)

**Purpose:** Prevent connection pool exhaustion during database outages.

```python
# Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5   # Open after 5 failures
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=2   # Close after 2 successes
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60    # Wait 60s before retry

# States: CLOSED → OPEN → HALF_OPEN → CLOSED
```

**Behavior:**
- **CLOSED:** Normal operation, all queries execute
- **OPEN:** Fail-fast, reject queries immediately (prevent backlog)
- **HALF_OPEN:** Test with 1 query, close if successful

#### Rate Limiting

```python
# API rate limits (slowapi)
@limiter.limit("60/minute")  # Single article endpoint
@limiter.limit("10/minute")  # Batch endpoint
@limiter.limit("100/minute") # Stats endpoint
```

**Response:**
```json
{
  "error": "Rate limit exceeded: 60 per 1 minute",
  "retry_after": 42  // seconds
}
```

#### Secure Logging (CVE-2025-001 Mitigation)

**Problem:** Logs may contain sensitive data (passwords, tokens, PII)

**Solution:** Sensitive data filter

```python
# Configuration
configure_logging(
    log_level=settings.LOG_LEVEL,
    enable_sensitive_filter=True  # Mask passwords, tokens, emails
)

# Behavior
logger.info("User login: password=secret123")
# Output: User login: password=***MASKED***
```

### 11.2 TLS/HTTPS Configuration (Production)

**Development:** HTTP only (localhost)
**Production:** HTTPS via reverse proxy (nginx/traefik)

```bash
# Enable HSTS (uncomment in production)
# response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

# TLS Configuration (production only)
ENABLE_HTTPS=true
TLS_CERT_PATH=/etc/ssl/certs/nlp-extraction.crt
TLS_KEY_PATH=/etc/ssl/private/nlp-extraction.key
```

### 11.3 Authentication (Future)

**Current Status:** ⚠️ No authentication (internal service only)

**Future Options:**
1. **JWT Authentication:**
   ```bash
   ENABLE_JWT_AUTH=true
   JWT_SECRET_KEY=your-secret-key
   JWT_ALGORITHM=HS256
   JWT_ISSUER=auth-service
   ```

2. **API Key Authentication:**
   ```python
   X-API-Key: service-specific-api-key
   ```

3. **mTLS (Mutual TLS):**
   - Client certificates for service-to-service communication

**Recommendation:** JWT authentication when exposing to external clients.

---

## 12. Monitoring & Observability

### 12.1 Prometheus Metrics

**Metrics Port:** 9115
**Endpoint:** `http://localhost:9115/metrics`

#### Standard Metrics

```prometheus
# HTTP Request Duration
http_request_duration_seconds{method="GET", handler="/api/v1/extractions/{id}"}

# HTTP Request Count
http_requests_total{method="GET", handler="/api/v1/extractions/{id}", status="200"}

# Processing Time
nlp_processing_duration_seconds{language="de", extractor_version="base_v1"}

# Entity Count
nlp_entities_extracted_total{language="de", entity_type="PERSON"}

# Circuit Breaker State
circuit_breaker_state{resource="database"} # 0=CLOSED, 1=OPEN, 2=HALF_OPEN
circuit_breaker_failures_total{resource="database"}
circuit_breaker_successes_total{resource="database"}

# Database Query Duration
db_query_duration_seconds{operation="single_fetch"}

# Cache Hit Rate
cache_hit_rate{cache_type="redis"}
```

### 12.2 Logging

**Log Format:** JSON (structured logging)

```json
{
  "timestamp": "2025-11-24T10:30:00.123Z",
  "level": "INFO",
  "service": "nlp-extraction-service",
  "message": "Extracted 12 entities from article 123e4567",
  "article_id": "123e4567-e89b-12d3-a456-426614174000",
  "entity_count": 12,
  "processing_time_ms": 45,
  "language": "de",
  "extractor_version": "base_v1"
}
```

**Log Levels:**
- **DEBUG:** Detailed processing information (per-entity)
- **INFO:** Processing summaries, API requests
- **WARNING:** Slow requests (> 500ms), content issues
- **ERROR:** Processing failures, database errors
- **CRITICAL:** Service startup failures, fatal errors

### 12.3 Health Checks

#### Liveness Probe (Kubernetes)

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8115
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

**Response:**
```json
{
  "status": "healthy",
  "service": "nlp-extraction-service",
  "database": "connected",
  "timestamp": 1732442400.0
}
```

#### Readiness Probe (Kubernetes)

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8115
  initialDelaySeconds: 40
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

**Response:**
```json
{
  "status": "ready",
  "extractions_count": 22021,
  "timestamp": 1732442400.0
}
```

### 12.4 Alerting Rules (Prometheus)

```yaml
groups:
  - name: nlp-extraction-alerts
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in NLP extraction service"

      # Slow Processing
      - alert: SlowProcessing
        expr: |
          histogram_quantile(0.95, nlp_processing_duration_seconds) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "p95 NLP processing time > 100ms"

      # Circuit Breaker Open
      - alert: CircuitBreakerOpen
        expr: |
          circuit_breaker_state{resource="database"} == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database circuit breaker is OPEN"

      # High Memory Usage
      - alert: HighMemoryUsage
        expr: |
          process_resident_memory_bytes > 2147483648  # 2 GB
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "NLP extraction service using > 2 GB RAM"
```

---

## 13. Known Issues & Limitations

### 13.1 Current Limitations

| Issue | Impact | Workaround | Status |
|-------|--------|------------|--------|
| **Service Not Deployed** | No production data | Use content-analysis-v2 | ⚠️ Pending review (2025-12-09) |
| **German Sentiment Slow** | 15-20ms per article | Use GPU acceleration | Accepted |
| **Max Article Length** | 50,000 chars limit | Truncate long articles | By design |
| **Language Support** | Only German/English | Add more spaCy models | Low priority |
| **Quote Detection** | Regex-based (brittle) | Use ML-based quote detection | Future |
| **Entity Disambiguation** | No entity linking | Integrate entity-canonicalization-service | Future |

### 13.2 Known Bugs

**None reported** (service not in production use).

### 13.3 Performance Bottlenecks

1. **BERT Sentiment Analysis (German)**
   - **Impact:** 15-20ms per article (40% of processing time)
   - **Mitigation:** Use GPU acceleration (3-5x speedup)
   - **Alternative:** Switch to faster model (e.g., distilbert)

2. **spaCy Model Loading**
   - **Impact:** 2-3 seconds per worker startup
   - **Mitigation:** Singleton pattern (models loaded once)
   - **Status:** Already implemented

3. **Large Article Processing**
   - **Impact:** 200ms+ for 2000+ word articles
   - **Mitigation:** Truncate to 50,000 chars, process in chunks
   - **Status:** Truncation implemented

### 13.4 Future Improvements

#### Phase 3 Features (Not Yet Implemented)

1. **Custom EntityRuler Patterns**
   - Add domain-specific entities (company names, products)
   - Improve entity extraction accuracy

2. **Entity Linking (Disambiguation)**
   - Link entities to knowledge graphs (DBpedia, Wikidata)
   - Integrate with entity-canonicalization-service

3. **Coreference Resolution**
   - Resolve pronouns to entities ("he" → "Merkel")
   - Improve quote attribution accuracy

4. **Event Extraction**
   - Extract structured events (who, what, when, where, why)
   - Build event knowledge graph

5. **Multi-Document Summarization**
   - Extract key entities/events across multiple articles
   - Generate timelines

#### Performance Optimizations

1. **GPU Acceleration**
   - Use CUDA for BERT sentiment analysis (3-5x speedup)
   - Add GPU support to Docker image

2. **Model Quantization**
   - Reduce model size (500MB → 200MB per model)
   - Faster loading, lower memory usage

3. **Batch Processing**
   - Process multiple articles in single spaCy call
   - 20-30% throughput improvement

---

## 14. Development Guide

### 14.1 Local Development Setup

#### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL (via Docker)
- Redis (via Docker)
- RabbitMQ (via Docker)

#### Quick Start

```bash
# 1. Clone repository
cd /home/cytrex/news-microservices/services/nlp-extraction-service

# 2. Install dependencies (local development)
pip install -r requirements.txt

# 3. Download spaCy models
python -m spacy download de_core_news_lg
python -m spacy download en_core_web_lg

# 4. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 5. Run database migrations
alembic upgrade head

# 6. Start service (Docker Compose - if reactivating)
docker compose up nlp-extraction-api

# 7. Or run locally (hot-reload)
uvicorn app.main:app --reload --port 8115
```

#### Running Tests

```bash
# Unit tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=app --cov-report=html

# Specific test
pytest tests/test_api_extractions.py -v
```

#### Code Quality

```bash
# Type checking
mypy app/

# Linting
flake8 app/
pylint app/

# Code formatting
black app/
isort app/
```

### 14.2 Project Structure

```
nlp-extraction-service/
├── app/
│   ├── main.py                      # FastAPI application
│   ├── core/                        # Core configuration
│   │   ├── config.py               # Pydantic settings
│   │   ├── logging_config.py       # Secure logging
│   │   ├── rate_limit.py           # Rate limiter
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── circuit_breaker.py      # Circuit breaker
│   ├── api/
│   │   └── routes/
│   │       └── extractions.py      # API endpoints
│   ├── database/
│   │   ├── models.py               # SQLAlchemy models
│   │   └── session.py              # Database session
│   ├── models/
│   │   └── extraction.py           # Pydantic response models
│   ├── services/
│   │   └── extraction_service.py   # Business logic
│   ├── nlp/
│   │   ├── extractors/
│   │   │   └── base_extractor.py   # spaCy extraction (919 lines)
│   │   ├── sentiment/
│   │   │   ├── base_sentiment.py   # Sentiment analysis
│   │   │   └── entity_sentiment.py # Entity-level sentiment
│   │   ├── relations/
│   │   │   ├── cooccurrence.py     # Co-occurrence relations
│   │   │   ├── temporal.py         # Temporal relations
│   │   │   └── affiliation.py      # Affiliation relations
│   │   ├── analysis/
│   │   │   └── entity_centrality.py # Centrality scoring
│   │   ├── quotes/
│   │   │   └── quote_sentiment.py  # Quote attribution
│   │   └── filters/
│   │       └── entity_filter.py    # Quality filtering
│   ├── workers/
│   │   ├── realtime_worker.py      # RabbitMQ consumer (realtime)
│   │   └── batch_worker.py         # Batch processor
│   ├── messaging/
│   │   └── rabbitmq_client.py      # RabbitMQ client
│   └── utils/
│       └── html_utils.py           # HTML sanitization
├── alembic/
│   ├── versions/                   # Database migrations
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_phase2a_features.py
│   │   ├── 003_add_phase2b2_sentiment.py
│   │   ├── 004_add_phase2b3_relations.py
│   │   ├── 005_add_phase2b4_entity_sentiments.py
│   │   ├── 006_add_phase2b5_entity_centrality.py
│   │   └── 007_add_phase2b6_quote_sentiments.py
│   └── env.py
├── tests/
│   ├── test_api_extractions.py     # API tests
│   ├── test_nlp_extraction.py      # NLP tests
│   └── conftest.py                 # Pytest fixtures
├── scripts/
│   └── download_sentiment_models.py # Download BERT models
├── requirements.txt                # Python dependencies
├── .env.example                    # Configuration template
├── Dockerfile.dev                  # Development Dockerfile
├── alembic.ini                     # Alembic configuration
└── README.md                       # Service README
```

**Total Lines of Code:** ~3,095 lines

### 14.3 Testing Strategy

#### Unit Tests

```python
# Test entity extraction
def test_entity_extraction():
    extractor = BaseSpacyExtractor()
    result = extractor.extract(
        text="Angela Merkel ist Bundeskanzlerin von Deutschland.",
        language="de"
    )

    assert result["entity_count"] >= 2
    assert any(e["text"] == "Angela Merkel" for e in result["entities"])
    assert any(e["label"] == "PER" for e in result["entities"])
```

#### API Tests

```python
# Test single article endpoint
def test_get_extraction_by_id(client, db_session):
    # Insert test extraction
    extraction = Extraction(
        article_id=uuid4(),
        entities=[{"text": "Test", "label": "PER"}],
        # ...
    )
    db_session.add(extraction)
    db_session.commit()

    # Query API
    response = client.get(f"/api/v1/extractions/{extraction.article_id}")
    assert response.status_code == 200
    assert response.json()["entity_count"] == 1
```

#### Integration Tests

```python
# Test full pipeline (RabbitMQ → Processing → Database)
@pytest.mark.integration
def test_realtime_worker_pipeline():
    # Publish article.created event
    publish_event({"article_id": article_id})

    # Wait for processing
    time.sleep(2)

    # Verify extraction stored
    extraction = db.query(Extraction).filter_by(article_id=article_id).first()
    assert extraction is not None
    assert extraction.entity_count > 0
```

#### Performance Tests

```python
# Test processing time
def test_processing_time():
    extractor = BaseSpacyExtractor()

    start = time.time()
    result = extractor.extract(text=sample_article, language="de")
    duration = (time.time() - start) * 1000

    assert duration < 100  # < 100ms
    assert result["processing_time_ms"] < 100
```

### 14.4 Adding New Features

#### Example: Add New Entity Type

1. **Update EntityRuler patterns** (if custom patterns enabled):
```python
# app/nlp/extractors/custom_patterns.py
CUSTOM_PATTERNS = [
    {"label": "PRODUCT", "pattern": "iPhone"},
    {"label": "PRODUCT", "pattern": [{"LOWER": "iphone"}, {"IS_DIGIT": True}]},
]
```

2. **Update quality filter** (if needed):
```python
# app/nlp/filters/entity_filter.py
IGNORED_LABELS = {"TIME", "DATE", "ORDINAL", ...}  # Don't ignore PRODUCT
```

3. **Add tests**:
```python
def test_product_extraction():
    result = extractor.extract("Apple verkauft das iPhone 15.")
    products = [e for e in result["entities"] if e["label"] == "PRODUCT"]
    assert len(products) > 0
```

4. **Update documentation** (this file).

---

## 15. Appendices

### 15.1 Glossary

| Term | Definition |
|------|------------|
| **NER (Named Entity Recognition)** | Identification of entities (PERSON, ORG, LOC) in text |
| **POS (Part-of-Speech)** | Grammatical category of words (NOUN, VERB, ADJ) |
| **SVO Triples** | Subject-Verb-Object relationships (dependency parsing) |
| **Noun Chunks** | Multi-word expressions (e.g., "die ehemalige Bundeskanzlerin") |
| **Lemmatization** | Reducing words to base form ("running" → "run") |
| **Co-occurrence** | Entities mentioned together (likely related) |
| **Entity Centrality** | Importance ranking of entities in article |
| **Circuit Breaker** | Fault-tolerance pattern (fail-fast during outages) |
| **spaCy** | Open-source NLP library (Python) |
| **BERT** | Transformer-based ML model for NLP |
| **VADER** | Rule-based sentiment analysis (English) |

### 15.2 Entity Label Reference

**spaCy Standard Labels (18 types):**

| Label | Description | Example |
|-------|-------------|---------|
| **PER / PERSON** | Person names | "Angela Merkel", "Joe Biden" |
| **ORG** | Organizations | "CDU", "Apple Inc." |
| **LOC** | Locations (non-GPE) | "Europa", "der Rhein" |
| **GPE** | Geopolitical entities | "Deutschland", "Berlin" |
| **DATE** | Dates | "15. März 2024", "yesterday" |
| **TIME** | Times | "10:30 Uhr", "morning" |
| **MONEY** | Monetary values | "100 Euro", "$50" |
| **PERCENT** | Percentages | "50%", "zehn Prozent" |
| **CARDINAL** | Numerals (not ordinal) | "drei", "100" |
| **ORDINAL** | Ordinal numbers | "erste", "10th" |
| **QUANTITY** | Quantities with units | "5 Kilometer", "10kg" |
| **EVENT** | Named events | "Olympische Spiele", "Weltkrieg" |
| **PRODUCT** | Products | "iPhone", "Mercedes" |
| **WORK_OF_ART** | Titles of works | "Faust", "Mona Lisa" |
| **LAW** | Legal documents | "Grundgesetz", "GDPR" |
| **LANGUAGE** | Language names | "Deutsch", "English" |
| **FACILITY** | Buildings, infrastructure | "Reichstag", "Brandenburger Tor" |
| **MISC** | Miscellaneous | Catch-all for other entities |

**Filtered Out (Stage 2):**
- TIME, DATE, ORDINAL, CARDINAL, QUANTITY, PERCENT

**Reason:** High noise, low information value for news analysis.

### 15.3 Performance Benchmarks

**Baseline System:**
- CPU: AMD Ryzen 7 (8 cores)
- RAM: 16 GB
- Storage: SSD
- OS: Ubuntu 22.04

**Processing Performance:**

| Article Length | Processing Time | Throughput |
|----------------|----------------|------------|
| 100 words | 25ms | 40 articles/sec |
| 250 words | 35ms | 28 articles/sec |
| 500 words | 50ms | 20 articles/sec |
| 1000 words | 80ms | 12 articles/sec |
| 2000 words | 150ms | 6 articles/sec |

**Database Query Performance (100,000 extractions):**

| Query Type | Time (p50) | Time (p95) | Time (p99) |
|------------|-----------|-----------|-----------|
| Single article | 8ms | 15ms | 25ms |
| Batch (10) | 45ms | 70ms | 90ms |
| Batch (100) | 130ms | 180ms | 195ms |
| Stats query | 18ms | 30ms | 45ms |

### 15.4 References

**External Documentation:**
- [spaCy Documentation](https://spacy.io/usage)
- [spaCy Models](https://spacy.io/models)
- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [VADER Sentiment](https://github.com/cjhutto/vaderSentiment)
- [German BERT Sentiment](https://huggingface.co/oliverguhr/german-sentiment-bert)

**Internal Documentation:**
- [CLAUDE.backend.md](/home/cytrex/news-microservices/CLAUDE.backend.md)
- [ARCHITECTURE.md](/home/cytrex/news-microservices/ARCHITECTURE.md)
- [feed-service Documentation](/home/cytrex/userdocs/doku-update241125/docs/feed-service.md)

**Related Services:**
- feed-service (8101): Source of articles
- content-analysis-v3 (8110): LLM-based analysis (alternative approach)
- entity-canonicalization-service (8112): Entity deduplication

### 15.5 Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-09 | 1.0.0 | Service marked as DEPRECATED, not in production use |
| 2025-10-15 | 0.9.0 | Phase 2B complete (sentiment, relations, centrality, quotes) |
| 2025-09-20 | 0.8.0 | Phase 2A complete (improved quote detection, HTML stripping) |
| 2025-08-10 | 0.7.0 | Phase 1 complete (baseline NER, dependency parsing) |

---

**END OF DOCUMENTATION**

This documentation is part of the news-microservices project documentation consolidation (Phase 2c).

**Last Updated:** 2025-11-24
**Maintained By:** Development Team
**Review Schedule:** Quarterly or after major changes

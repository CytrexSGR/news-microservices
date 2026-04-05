# FMP-Service ↔ Knowledge-Graph Integration Analysis

**Date:** 2025-01-16
**Status:** Planning Phase
**Services:**
- FMP Service (Port 8113) - Financial market data aggregation
- Knowledge-Graph Service (Port 8111) - Neo4j-based relationship management

---

## Executive Summary

The **FMP Service** provides rich financial market data (quotes, history, news, events) that can dramatically enhance the **Knowledge-Graph Service**'s ability to model financial relationships and market impacts. This document outlines a comprehensive integration strategy.

### Key Integration Opportunities

1. **Market Entity Modeling** - Create MARKET nodes in Neo4j from FMP asset metadata
2. **Company-Ticker Relationships** - Link ORGANIZATION entities to financial markets
3. **News Correlation** - Connect FMP financial news to knowledge graph articles
4. **Historical Context** - Provide price history for market impact analysis
5. **Event-Driven Updates** - Real-time market data via RabbitMQ events
6. **Sentiment-Price Correlation** - Link news sentiment to market movements

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         FMP Service (8113)                        │
├──────────────────────────────────────────────────────────────────┤
│ • Asset Metadata (40 assets)                                     │
│ • Real-time Quotes (indices, forex, commodities, crypto)         │
│ • Historical EOD Prices (2024-2025)                              │
│ • Financial News (pre-tagged with symbols)                       │
│ • Earnings Calendar, Macro Indicators                            │
└─────────────────┬────────────────────────────────────────────────┘
                  │
                  │ Integration Paths:
                  │
                  ├─────────────────────────────────────┐
                  │                                     │
                  ▼                                     ▼
         ┌────────────────┐                  ┌──────────────────┐
         │  HTTP/REST API  │                  │  RabbitMQ Events │
         │  Polling/Sync   │                  │  (market.*)      │
         └────────┬────────┘                  └────────┬─────────┘
                  │                                     │
                  └──────────────┬──────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Knowledge-Graph Service (8111)                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐      │
│  │              FMP Integration Layer (NEW)               │      │
│  ├────────────────────────────────────────────────────────┤      │
│  │ • MarketDataIngestion → MARKET nodes                  │      │
│  │ • AssetMetadataEnrichment → Entity properties         │      │
│  │ • NewsCorrelation → Article-Market links              │      │
│  │ • PriceHistoryStorage → Temporal relationships        │      │
│  │ • EventConsumer (market.price.updated)                │      │
│  └────────────────────────────────────────────────────────┘      │
│                           │                                       │
│                           ▼                                       │
│              ┌────────────────────────┐                          │
│              │   Neo4j Graph Store    │                          │
│              ├────────────────────────┤                          │
│              │ Nodes:                 │                          │
│              │ • :MARKET              │ ← NEW                    │
│              │ • :TICKER              │ ← NEW                    │
│              │ • :SECTOR              │ ← NEW                    │
│              │ • :FINANCIAL_EVENT     │ ← Existing               │
│              │ • :ORGANIZATION        │ ← Enhanced               │
│              │                        │                          │
│              │ Relationships:         │                          │
│              │ • TRADED_AS            │ ← NEW                    │
│              │ • IMPACTS_MARKET       │ ← Enhanced               │
│              │ • BELONGS_TO_SECTOR    │ ← NEW                    │
│              │ • PRICE_MOVEMENT_AT    │ ← NEW (temporal)         │
│              │ • CORRELATED_WITH      │ ← NEW                    │
│              └────────────────────────┘                          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Integration Points

### 2.1 Market Entity Modeling

**Source:** FMP `/metadata/assets` (40 assets)

**Neo4j Schema:**

```cypher
CREATE (:MARKET {
  symbol: "^GSPC",                    # FMP symbol
  name: "S&P 500",                    # Display name
  asset_type: "indices",              # indices/forex/commodities/crypto
  category: "major_indices",          # From FMP metadata
  currency: "USD",
  exchange: "NYSE",
  is_active: true,
  icon_url: "...",
  created_at: datetime(),
  last_updated: datetime()
})

CREATE (:SECTOR {
  name: "Technology",
  description: "Information Technology Sector",
  market_classification: "S&P_SECTOR"
})
```

**Implementation:**
```python
# services/knowledge-graph-service/app/services/fmp_integration_service.py
async def sync_market_entities():
    """Fetch FMP asset metadata and create MARKET nodes"""
    fmp_assets = await fmp_client.get(
        "http://fmp-service:8113/api/v1/metadata/assets"
    )

    for asset in fmp_assets:
        cypher = """
        MERGE (m:MARKET {symbol: $symbol})
        SET m.name = $name,
            m.asset_type = $asset_type,
            m.category = $category,
            m.currency = $currency,
            m.is_active = $is_active,
            m.last_updated = datetime()
        RETURN m
        """
        await neo4j_service.execute_query(cypher, params=asset)
```

**Endpoints:**
- **New:** POST `/api/v1/graph/markets/sync` - Manual sync trigger
- **New:** GET `/api/v1/graph/markets` - List all MARKET nodes
- **New:** GET `/api/v1/graph/markets/{symbol}` - Get market details

---

### 2.2 Company-Ticker Relationships

**Goal:** Link ORGANIZATION entities in knowledge graph to financial markets

**Example:**
```
Apple Inc. (ORGANIZATION) -[:TRADED_AS {ticker: "AAPL", exchange: "NASDAQ"}]-> S&P 500 (MARKET)
```

**Neo4j Pattern:**

```cypher
MATCH (org:ORGANIZATION {name: "Apple Inc."})
MATCH (market:MARKET {symbol: "AAPL"})
MERGE (org)-[r:TRADED_AS]->(market)
SET r.ticker = "AAPL",
    r.exchange = "NASDAQ",
    r.sector = "Technology",
    r.market_cap_category = "mega_cap",
    r.created_at = datetime()
```

**Enrichment Flow:**
1. Extract company names from articles (existing)
2. Query FMP for ticker match via fuzzy search
3. Create TRADED_AS relationship if confidence > 0.8
4. Store in enrichment_events table for audit

**Implementation:**
```python
async def enrich_organization_with_ticker(org_name: str):
    """Find ticker for company and create relationship"""
    # Search FMP for company
    search_results = await fmp_client.get(
        f"http://fmp-service:8113/api/v1/metadata/search?q={org_name}"
    )

    if not search_results:
        return None

    best_match = search_results[0]  # Highest similarity
    if best_match.confidence < 0.8:
        return None

    # Create relationship in Neo4j
    cypher = """
    MATCH (org:ORGANIZATION {name: $org_name})
    MATCH (market:MARKET {symbol: $ticker})
    MERGE (org)-[r:TRADED_AS]->(market)
    SET r.ticker = $ticker,
        r.exchange = $exchange,
        r.confidence = $confidence
    RETURN r
    """

    return await neo4j_service.execute_query(cypher, params={
        "org_name": org_name,
        "ticker": best_match.symbol,
        "exchange": best_match.exchange,
        "confidence": best_match.confidence
    })
```

---

### 2.3 News Correlation

**Source:** FMP `/news` endpoints (pre-tagged with symbols)

**Advantage:** FMP news articles are already tagged with stock symbols

**Integration Pattern:**

```cypher
MATCH (article:ARTICLE {url: $fmp_news_url})
MATCH (market:MARKET {symbol: $symbol})
MERGE (article)-[r:MENTIONS_MARKET]->(market)
SET r.sentiment = $sentiment,
    r.sentiment_confidence = $confidence,
    r.created_at = datetime()
```

**Use Case:**
1. FMP Service pulls financial news (every 10 minutes)
2. For each news article, extract mentioned symbols
3. Publish event to RabbitMQ: `market.news.published`
4. Knowledge-Graph consumes and creates MENTIONS_MARKET relationships

**Event Schema:**
```python
class MarketNewsPublishedEvent(BaseModel):
    article_id: str              # Knowledge-graph article ID (if exists)
    fmp_news_id: str            # FMP news table ID
    title: str
    url: str
    published_at: datetime
    symbols: List[str]          # ["AAPL", "MSFT"]
    sentiment: Optional[str]    # "positive"/"negative"/"neutral"
    source: str
```

**RabbitMQ Routing:**
```python
# FMP Service publishes:
exchange = "news.events"
routing_key = "market.news.published"

# Knowledge-Graph consumes:
queue = "knowledge_graph_market_news"
binding_key = "market.news.#"
```

---

### 2.4 Historical Price Context

**Source:** FMP `/history/{symbol}` (2024-2025 coverage)

**Goal:** Provide temporal price context for market impact analysis

**Neo4j Temporal Pattern:**

**Option A: Dated Relationships (Recommended for queries)**
```cypher
(article:ARTICLE)-[:PUBLISHED_AT {date: date("2025-01-15")}]->
(event:FINANCIAL_EVENT)-[:IMPACTED_MARKET {
    change_percentage: -2.5,
    price_before: 5891.34,
    price_after: 5743.81,
    date: date("2025-01-15")
}]->(market:MARKET {symbol: "^GSPC"})
```

**Option B: Separate Price Nodes (Recommended for time-series)**
```cypher
(market:MARKET {symbol: "^GSPC"})<-[:PRICE_OF]-(price:PRICE_POINT {
    date: date("2025-01-15"),
    open: 5880.0,
    high: 5910.0,
    low: 5840.0,
    close: 5891.34,
    volume: 3200000000
})
```

**Query Example:**
```cypher
// Find articles correlated with price movements > 2%
MATCH (article:ARTICLE)-[:PUBLISHED_AT {date: $date}]->(:FINANCIAL_EVENT)
      -[impact:IMPACTED_MARKET]->(market:MARKET)
WHERE abs(impact.change_percentage) > 2.0
RETURN article.title, market.name, impact.change_percentage
ORDER BY abs(impact.change_percentage) DESC
```

**Implementation:**
```python
async def sync_historical_prices(symbol: str, from_date: str, to_date: str):
    """Fetch FMP historical data and create price nodes"""
    history = await fmp_client.get(
        f"http://fmp-service:8113/api/v1/history/{symbol}",
        params={"from_date": from_date, "to_date": to_date}
    )

    for price_data in history:
        cypher = """
        MATCH (m:MARKET {symbol: $symbol})
        MERGE (p:PRICE_POINT {market_symbol: $symbol, date: date($date)})
        SET p.open = $open,
            p.high = $high,
            p.low = $low,
            p.close = $close,
            p.volume = $volume
        MERGE (m)<-[:PRICE_OF]-(p)
        """
        await neo4j_service.execute_query(cypher, params=price_data)
```

---

### 2.5 Event-Driven Real-Time Updates

**RabbitMQ Event Types:**

```python
class MarketPriceUpdatedEvent(BaseModel):
    """Published by FMP scheduler jobs"""
    symbol: str                    # "^GSPC"
    asset_type: str               # "indices"
    price: float
    change: float
    change_percent: float
    timestamp: datetime
    volume: Optional[int]

class EarningsAnnouncedEvent(BaseModel):
    """Published from FMP earnings calendar sync"""
    symbol: str
    company_name: str
    report_date: date
    eps_actual: Optional[float]
    eps_estimate: Optional[float]
    eps_surprise_percent: Optional[float]
    revenue_actual: Optional[float]
    revenue_estimate: Optional[float]

class MacroIndicatorReleasedEvent(BaseModel):
    """Published from FMP macro indicator sync"""
    indicator_name: str           # "CPI", "GDP Growth", etc.
    value: float
    period: str
    release_date: date
    impact_level: str            # "HIGH", "MEDIUM", "LOW"
```

**Consumer Implementation:**
```python
# services/knowledge-graph-service/app/consumers/market_events_consumer.py
async def handle_market_price_updated(event: MarketPriceUpdatedEvent):
    """Update MARKET node with latest price"""
    cypher = """
    MATCH (m:MARKET {symbol: $symbol})
    SET m.current_price = $price,
        m.last_change_percent = $change_percent,
        m.last_updated = datetime()

    // If significant price movement (>2%), create event
    WITH m
    WHERE abs($change_percent) > 2.0
    CREATE (e:PRICE_EVENT {
        market_symbol: $symbol,
        change_percent: $change_percent,
        timestamp: datetime($timestamp),
        event_type: CASE
            WHEN $change_percent > 0 THEN 'surge'
            ELSE 'drop'
        END
    })
    CREATE (m)<-[:AFFECTED]-(e)
    """
    await neo4j_service.execute_query(cypher, params=event.dict())
```

**Routing Configuration:**
```python
# FMP Service (publisher)
EXCHANGES = {
    "market.events": {
        "type": "topic",
        "durable": True
    }
}

ROUTING_KEYS = {
    "market.price.updated.indices.*",
    "market.price.updated.forex.*",
    "market.price.updated.commodities.*",
    "market.price.updated.crypto.*",
    "market.earnings.announced",
    "market.macro.released"
}

# Knowledge-Graph Service (consumer)
QUEUES = {
    "knowledge_graph_market_updates": {
        "bindings": [
            ("market.events", "market.price.updated.#"),
            ("market.events", "market.earnings.#"),
            ("market.events", "market.macro.#")
        ]
    }
}
```

---

### 2.6 Sentiment-Price Correlation Analysis

**Goal:** Analyze relationship between news sentiment and market movements

**Graph Pattern:**

```cypher
(article:ARTICLE {sentiment_score: 0.85, published_at: datetime("2025-01-15T10:00:00")})
  -[:MENTIONS_MARKET {sentiment: "positive"}]->
(market:MARKET {symbol: "AAPL"})
  <-[:PRICE_OF]-
(price_before:PRICE_POINT {date: date("2025-01-14"), close: 185.50})

(market)
  <-[:PRICE_OF]-
(price_after:PRICE_POINT {date: date("2025-01-15"), close: 189.20})
```

**Query: Find Sentiment-Price Correlations**

```cypher
// Articles with positive sentiment followed by price increase
MATCH (article:ARTICLE)-[mention:MENTIONS_MARKET]->(market:MARKET)
WHERE mention.sentiment = "positive"
  AND article.published_at >= datetime() - duration({days: 7})

MATCH (market)<-[:PRICE_OF]-(price_before:PRICE_POINT)
WHERE price_before.date = date(article.published_at) - duration({days: 1})

MATCH (market)<-[:PRICE_OF]-(price_after:PRICE_POINT)
WHERE price_after.date = date(article.published_at)

WITH article, market,
     ((price_after.close - price_before.close) / price_before.close * 100) AS price_change,
     mention.sentiment_confidence AS sentiment_confidence

WHERE price_change > 0  // Positive correlation

RETURN
  article.title,
  market.name,
  price_change,
  sentiment_confidence,
  article.published_at
ORDER BY price_change DESC
LIMIT 20
```

**Analytics Endpoint:**
```python
@router.get("/analytics/sentiment-price-correlation")
async def analyze_sentiment_correlation(
    symbol: Optional[str] = None,
    days: int = 7,
    min_correlation: float = 0.5
):
    """
    Analyze correlation between article sentiment and price movements

    Returns:
    - Articles with sentiment scores
    - Corresponding price changes
    - Correlation coefficient
    - Predictive accuracy metrics
    """
    # Implementation uses Cypher query above
    pass
```

---

## 3. New Endpoints (Knowledge-Graph Service)

### Market Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/graph/markets/sync` | POST | Sync FMP asset metadata to MARKET nodes |
| `/api/v1/graph/markets` | GET | List all MARKET nodes |
| `/api/v1/graph/markets/{symbol}` | GET | Get market details + relationships |
| `/api/v1/graph/markets/{symbol}/news` | GET | Get articles mentioning market |
| `/api/v1/graph/markets/{symbol}/price-history` | GET | Get historical price nodes |
| `/api/v1/graph/markets/{symbol}/organizations` | GET | Get companies traded as this symbol |

### Analytics

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/graph/analytics/sentiment-price-correlation` | GET | Sentiment vs. price movement analysis |
| `/api/v1/graph/analytics/market-impact-timeline` | GET | Timeline of market impacts from articles |
| `/api/v1/graph/analytics/sector-exposure` | GET | Distribution of articles by sector |
| `/api/v1/graph/analytics/price-event-clusters` | GET | Identify concurrent price movements |

### Enrichment

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/graph/enrichment/ticker-lookup` | POST | Find ticker for company name |
| `/api/v1/graph/enrichment/bulk-ticker-match` | POST | Batch ticker matching for ORGANIZATIONs |

---

## 4. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create FMP integration service module
- [ ] Define new Neo4j node types (MARKET, SECTOR, TICKER)
- [ ] Implement asset metadata sync endpoint
- [ ] Add MARKET node creation logic
- [ ] Test basic MARKET queries

**Deliverables:**
- `services/knowledge-graph-service/app/services/fmp_integration_service.py`
- `services/knowledge-graph-service/app/models/markets.py`
- Endpoint: POST `/api/v1/graph/markets/sync`

### Phase 2: Relationships (Week 3-4)
- [ ] Implement company-ticker enrichment
- [ ] Create TRADED_AS relationship logic
- [ ] Add news correlation (MENTIONS_MARKET)
- [ ] Implement historical price sync
- [ ] Create PRICE_POINT nodes

**Deliverables:**
- Enrichment endpoint: POST `/api/v1/graph/enrichment/ticker-lookup`
- Price sync endpoint: POST `/api/v1/graph/markets/{symbol}/sync-history`

### Phase 3: Event Integration (Week 5-6)
- [ ] Define RabbitMQ event schemas
- [ ] Implement FMP event publishers (in fmp-service)
- [ ] Create knowledge-graph event consumers
- [ ] Add real-time price update handling
- [ ] Implement earnings/macro event ingestion

**Deliverables:**
- `services/fmp-service/app/services/event_publisher.py` (enhanced)
- `services/knowledge-graph-service/app/consumers/market_events_consumer.py`

### Phase 4: Analytics (Week 7-8)
- [ ] Build sentiment-price correlation queries
- [ ] Implement market impact timeline
- [ ] Add sector exposure analysis
- [ ] Create price event clustering
- [ ] Build analytics dashboard endpoints

**Deliverables:**
- Endpoint: GET `/api/v1/graph/analytics/sentiment-price-correlation`
- Endpoint: GET `/api/v1/graph/analytics/market-impact-timeline`

### Phase 5: Optimization (Week 9-10)
- [ ] Add Neo4j indexes for market queries
- [ ] Implement caching for frequently accessed data
- [ ] Optimize bulk enrichment operations
- [ ] Add monitoring and metrics
- [ ] Performance testing

**Deliverables:**
- Migration scripts for indexes
- Performance benchmarks
- Monitoring dashboard

---

## 5. Data Flow Examples

### Example 1: Financial News Article Processing

```
1. FMP Scheduler → Fetch news from FMP API
2. FMP Service → Store in fmp_news table
3. FMP Service → Publish MarketNewsPublishedEvent to RabbitMQ
4. Knowledge-Graph Consumer → Receive event
5. Knowledge-Graph → Check if article exists in graph
6. Knowledge-Graph → For each symbol in article:
   a. MATCH (market:MARKET {symbol: $symbol})
   b. MERGE (article)-[:MENTIONS_MARKET {
        sentiment: $sentiment,
        confidence: $confidence
      }]->(market)
7. Knowledge-Graph → Create FINANCIAL_EVENT if significant impact
8. Knowledge-Graph → Query FMP for price at publish time
9. Knowledge-Graph → Create PRICE_MOVEMENT_AT relationship
```

### Example 2: Earnings Announcement Impact

```
1. FMP Scheduler → Fetch earnings calendar
2. FMP Service → Detect new earnings event
3. FMP Service → Publish EarningsAnnouncedEvent
4. Knowledge-Graph → Receive event
5. Knowledge-Graph → Create :EARNINGS_EVENT node
6. Knowledge-Graph → Link to company (ORGANIZATION)
7. Knowledge-Graph → Link to market (MARKET)
8. Knowledge-Graph → Query price before/after announcement
9. Knowledge-Graph → Calculate impact:
   - EPS surprise → Price movement correlation
   - Revenue surprise → Sector impact
10. Knowledge-Graph → Create IMPACTS_MARKET relationship
```

### Example 3: Macro Indicator Release

```
1. FMP Service → Fetch economic calendar (daily 06:00 UTC)
2. FMP Service → Detect GDP/CPI/Unemployment release
3. FMP Service → Publish MacroIndicatorReleasedEvent
4. Knowledge-Graph → Create :MACRO_EVENT node
5. Knowledge-Graph → Link to affected markets:
   - CPI → Inflation-sensitive sectors
   - GDP → Broad market indices
   - Unemployment → Consumer stocks
6. Knowledge-Graph → Query price movements across affected markets
7. Knowledge-Graph → Create IMPACTS_SECTOR relationships
8. Knowledge-Graph → Enable queries: "Show market reaction to CPI surprises"
```

---

## 6. Query Examples

### Query 1: Find Companies Mentioned in Articles with Price Impact

```cypher
MATCH (article:ARTICLE)-[:MENTIONS_MARKET]->(market:MARKET)
WHERE article.published_at >= datetime() - duration({days: 7})

MATCH (market)<-[:TRADED_AS]-(org:ORGANIZATION)

OPTIONAL MATCH (market)<-[:PRICE_OF]-(price_before:PRICE_POINT)
WHERE price_before.date = date(article.published_at) - duration({days: 1})

OPTIONAL MATCH (market)<-[:PRICE_OF]-(price_after:PRICE_POINT)
WHERE price_after.date = date(article.published_at)

WITH org, article, market,
     ((price_after.close - price_before.close) / price_before.close * 100) AS price_change

RETURN
  org.name AS company,
  market.symbol AS ticker,
  article.title,
  article.published_at,
  price_change,
  article.sentiment_score
ORDER BY abs(price_change) DESC
LIMIT 20
```

### Query 2: Sector Exposure in News Coverage

```cypher
MATCH (article:ARTICLE)-[:MENTIONS_MARKET]->(market:MARKET)
      <-[:TRADED_AS]-(org:ORGANIZATION)
WHERE article.published_at >= datetime() - duration({days: 30})

MATCH (org)-[:BELONGS_TO_SECTOR]->(sector:SECTOR)

RETURN
  sector.name,
  count(DISTINCT article) AS article_count,
  count(DISTINCT org) AS companies_mentioned,
  avg(article.sentiment_score) AS avg_sentiment
ORDER BY article_count DESC
```

### Query 3: Identify Market Shocks

```cypher
MATCH (event:PRICE_EVENT)
WHERE event.timestamp >= datetime() - duration({days: 7})
  AND abs(event.change_percent) > 5.0

MATCH (event)-[:AFFECTED]->(market:MARKET)

OPTIONAL MATCH (article:ARTICLE)-[:MENTIONS_MARKET]->(market)
WHERE article.published_at >= event.timestamp - duration({hours: 24})
  AND article.published_at <= event.timestamp + duration({hours: 2})

RETURN
  market.name,
  event.timestamp,
  event.change_percent,
  event.event_type,
  collect(article.title) AS related_articles
ORDER BY abs(event.change_percent) DESC
```

### Query 4: Earnings Surprise Impact Network

```cypher
MATCH (earnings:EARNINGS_EVENT)
WHERE earnings.eps_surprise_percent IS NOT NULL
  AND abs(earnings.eps_surprise_percent) > 10.0
  AND earnings.report_date >= date() - duration({months: 3})

MATCH (earnings)-[:FOR_COMPANY]->(org:ORGANIZATION)
      -[:TRADED_AS]->(market:MARKET)

MATCH (market)<-[impact:IMPACTS_MARKET]-(financial_event:FINANCIAL_EVENT)
WHERE financial_event.timestamp >= datetime(earnings.report_date)
  AND financial_event.timestamp <= datetime(earnings.report_date) + duration({days: 1})

RETURN
  org.name,
  market.symbol,
  earnings.eps_surprise_percent,
  impact.change_percentage AS market_reaction,
  (earnings.eps_surprise_percent / impact.change_percentage) AS impact_multiplier
ORDER BY abs(earnings.eps_surprise_percent) DESC
```

---

## 7. Benefits of Integration

### For Intelligence Analysis

1. **Enhanced Context**
   - Link geopolitical events to market impacts
   - Correlate sanctions with commodity prices
   - Track conflict impact on energy markets

2. **Predictive Insights**
   - Identify patterns: "Articles mentioning X tend to move Y market by Z%"
   - Early warning: Unusual sentiment spikes correlated with price movements
   - Sector contagion: Regional conflicts → energy → transport → consumer

3. **Network Effects**
   - Discover hidden relationships: "Company A impacts Company B through shared market exposure"
   - Supply chain implications: Commodity price changes → manufacturer stocks

### For Financial Analysis

1. **News-Driven Trading Signals**
   - High-confidence sentiment + historical correlation = actionable signal
   - Track institutional moves via company announcement analysis

2. **Risk Assessment**
   - Identify companies with high geopolitical exposure
   - Monitor sentiment shifts across correlated assets
   - Detect sector-wide sentiment trends

3. **Event Impact Measurement**
   - Quantify exact price impact of specific article types
   - Build historical database of event-price relationships
   - Enable backtesting of NLP-based trading strategies

### For System Architecture

1. **Unified Data Model**
   - Single source of truth for entity relationships
   - No duplicate company/market data across services
   - Consistent entity resolution via knowledge graph

2. **Scalable Event Processing**
   - RabbitMQ enables async, decoupled processing
   - Can handle high-frequency price updates without blocking
   - Easy to add new consumers for additional analysis

3. **Flexible Querying**
   - Cypher enables complex multi-hop queries
   - Graph structure naturally represents market relationships
   - Can discover unexpected connections via path queries

---

## 8. Technical Considerations

### Neo4j Performance

**Indexes Required:**
```cypher
CREATE INDEX market_symbol FOR (m:MARKET) ON (m.symbol);
CREATE INDEX price_point_date FOR (p:PRICE_POINT) ON (p.date);
CREATE INDEX organization_ticker FOR (o:ORGANIZATION) ON (o.ticker);
CREATE INDEX article_published FOR (a:ARTICLE) ON (a.published_at);
CREATE INDEX sector_name FOR (s:SECTOR) ON (s.name);
```

**Constraints:**
```cypher
CREATE CONSTRAINT market_symbol_unique FOR (m:MARKET) REQUIRE m.symbol IS UNIQUE;
CREATE CONSTRAINT price_point_unique FOR (p:PRICE_POINT) REQUIRE (p.market_symbol, p.date) IS UNIQUE;
```

### Data Volume Estimates

**MARKET Nodes:**
- Initial: 40 (FMP asset metadata)
- Growth: +5-10/month (new listings, asset expansions)

**PRICE_POINT Nodes:**
- Per market: 365 days/year = 365 nodes
- For 40 markets: 14,600 nodes/year
- 2-year history: ~30,000 nodes

**MENTIONS_MARKET Relationships:**
- Assuming 100 articles/day mentioning markets
- Average 2 symbols/article = 200 relationships/day
- Per year: 73,000 relationships

**Storage:**
- Neo4j: ~50 MB for 30K price nodes + 73K relationships
- PostgreSQL: Historical data remains in FMP service (1.6 MB currently)
- Total: < 100 MB additional graph storage/year

### Rate Limiting

**FMP API Limits:**
- Current usage: ~240 calls/day
- Available: 300 calls/day (free tier)
- Buffer: 60 calls/day for enrichment requests

**Recommendation:**
- Batch enrichment operations (e.g., 10 companies/request)
- Cache ticker lookups in PostgreSQL
- Use Redis for rate limit state across service instances

### RabbitMQ Configuration

**Message Volume:**
- Price updates: 4 asset types × 15-60 min intervals = ~100 messages/day
- News: ~400 messages/day (100 articles × 4 endpoints)
- Earnings/Macro: ~20 messages/day
- **Total: ~520 messages/day** (well within capacity)

**Queue Durability:**
- All queues: `durable=True`
- Messages: `persistent=True` for price/earnings events
- TTL: 7 days for unprocessed messages

---

## 9. Risk Mitigation

### Risk 1: Data Inconsistency

**Scenario:** FMP price data and Neo4j graph get out of sync

**Mitigation:**
- Implement reconciliation job (daily)
- Add version timestamps to MARKET nodes
- Use FMP as source of truth, graph as enrichment layer
- Monitoring: Alert if Neo4j last_updated > 2 hours behind FMP

### Risk 2: Symbol Ambiguity

**Scenario:** Company name doesn't match ticker unambiguously

**Mitigation:**
- Require confidence > 0.8 for automatic linking
- Manual review queue for 0.5-0.8 confidence matches
- Store all candidates in enrichment_events table
- Admin endpoint for manual confirmation/rejection

### Risk 3: Historical Data Bloat

**Scenario:** PRICE_POINT nodes grow unbounded

**Mitigation:**
- Archive nodes older than 2 years to PostgreSQL
- Keep only monthly snapshots for >2 years old data
- Implement Neo4j TTL for very old nodes
- Alternative: Keep full history in FMP service, query via API

### Risk 4: Rate Limit Exhaustion

**Scenario:** Enrichment operations exhaust FMP API quota

**Mitigation:**
- Implement request queue with rate limiting
- Cache all FMP responses in Redis (1-hour TTL)
- Batch ticker lookups (10+ companies per request)
- Fallback: Use Wikipedia/Wikidata for basic company info

---

## 10. Monitoring & Observability

### Metrics to Track

**Integration Health:**
- `fmp_kg_sync_duration_seconds` - Time to sync market metadata
- `fmp_kg_enrichment_success_rate` - Ticker match success %
- `fmp_kg_events_processed_total` - RabbitMQ messages consumed
- `fmp_kg_events_failed_total` - Failed event processing

**Data Quality:**
- `kg_market_nodes_total` - Current MARKET node count
- `kg_price_points_total` - Historical price nodes
- `kg_mentions_market_total` - Article-market relationships
- `kg_enrichment_confidence_avg` - Average ticker match confidence

**Performance:**
- `kg_cypher_query_duration_seconds{query_type="market_sync"}`
- `kg_cypher_query_duration_seconds{query_type="price_history"}`
- `fmp_api_latency_seconds{endpoint="/metadata/assets"}`

### Dashboards

**Dashboard 1: Integration Status**
- Last sync timestamp for each asset type
- Event processing rate (messages/sec)
- Error rate by event type
- Current queue depths

**Dashboard 2: Data Quality**
- MARKET nodes without price history
- ORGANIZATIONs without ticker relationships
- Confidence score distribution for enrichments
- Missing data alerts

**Dashboard 3: Performance**
- Query latency percentiles (p50, p95, p99)
- FMP API response times
- Neo4j connection pool usage
- RabbitMQ consumer lag

---

## 11. Next Steps

### Immediate Actions

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/fmp-knowledge-graph-integration
   ```

2. **Set Up Development Environment**
   - Ensure Neo4j container is running
   - Verify RabbitMQ connectivity
   - Test FMP service API availability

3. **Scaffold New Module**
   ```bash
   # In knowledge-graph-service
   mkdir -p app/services/fmp_integration
   mkdir -p app/consumers/market_events
   mkdir -p app/models/markets
   mkdir -p app/api/v1/markets
   ```

4. **Define Event Schemas**
   - Create `services/fmp-service/app/schemas/market_events.py`
   - Add to RabbitMQ message types

5. **Implement Phase 1**
   - Market metadata sync endpoint
   - Basic MARKET node creation
   - Test with FMP asset catalog

### Decision Points

**Before Phase 2:**
- [ ] Decide: Store full price history in Neo4j or just reference FMP?
- [ ] Decide: Use dated relationships or separate PRICE_POINT nodes?
- [ ] Decide: Automatic vs. manual ticker matching threshold?

**Before Phase 3:**
- [ ] Decide: Event retention policy (how long to keep in RabbitMQ?)
- [ ] Decide: Real-time vs. batch processing for price updates?
- [ ] Decide: Which FMP endpoints to publish events for?

**Before Phase 4:**
- [ ] Define analytics KPIs and metrics
- [ ] Design frontend visualization requirements
- [ ] Determine query performance SLAs

---

## 12. References

### Service Documentation
- [FMP Service README](../../../services/fmp-service/README.md)
- [Knowledge-Graph Service README](../../../services/knowledge-graph-service/README.md)
- [FMP API Documentation](https://site.financialmodelingprep.com/developer/docs)

### Architecture Patterns
- [Event-Driven Microservices](../guides/event-driven-architecture.md)
- [Neo4j Best Practices](../guides/neo4j-modeling-guide.md)
- [RabbitMQ Message Patterns](../guides/rabbitmq-patterns.md)

### Neo4j Resources
- [Temporal Data in Graphs](https://neo4j.com/developer/modeling-time/)
- [Financial Data Modeling](https://neo4j.com/use-cases/financial-services/)
- [Graph Algorithms](https://neo4j.com/docs/graph-data-science/)

---

**Document Version:** 1.0
**Last Updated:** 2025-01-16
**Author:** Integration Planning Analysis
**Status:** ✅ Ready for Implementation

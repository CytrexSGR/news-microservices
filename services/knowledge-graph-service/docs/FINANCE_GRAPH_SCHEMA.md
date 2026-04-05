# Finance Intelligence Knowledge Graph Schema

**Version**: 1.0
**Date**: 2025-11-16
**Purpose**: Graph schema for Financial Intelligence + Intermarket Analytics integration

---

## 🎯 Overview

This graph schema integrates data from **8 FMP Background Jobs** into Neo4j to enable:
- Company network analysis (M&A, insider trading, executive connections)
- Event timeline tracking (earnings, filings, trades)
- Market regime correlation analysis
- Cross-asset relationship discovery

---

## 📊 Node Types

### 1. Company (:Company)

**Description**: Public companies tracked by FMP Service

**Properties**:
```cypher
{
  symbol: String! (unique),
  name: String!,
  cik: String,
  sector: String,
  industry: String,
  market_cap: Float,
  employee_count: Integer,
  country: String,
  exchange: String,
  ipo_date: Date,
  created_at: DateTime,
  updated_at: DateTime
}
```

**Source Events**:
- `finance.company.updated`
- `finance.marketcap.updated`
- `finance.employees.updated`

**Indexes**:
```cypher
CREATE INDEX company_symbol IF NOT EXISTS FOR (c:Company) ON (c.symbol);
CREATE INDEX company_cik IF NOT EXISTS FOR (c:Company) ON (c.cik);
CREATE INDEX company_sector IF NOT EXISTS FOR (c:Company) ON (c.sector);
```

---

### 2. Executive (:Executive)

**Description**: Key executives and directors

**Properties**:
```cypher
{
  name: String!,
  title: String,
  age: Integer,
  since_year: Integer,
  pay_usd: Float,
  created_at: DateTime,
  updated_at: DateTime
}
```

**Source Events**:
- `finance.executives.updated`

**Indexes**:
```cypher
CREATE INDEX executive_name IF NOT EXISTS FOR (e:Executive) ON (e.name);
```

---

### 3. Event Nodes (Polymorphic)

#### 3a. EarningsEvent (:Event:EarningsEvent)

**Properties**:
```cypher
{
  event_id: String! (unique),
  symbol: String!,
  date: Date!,
  eps_actual: Float,
  eps_estimate: Float,
  revenue_actual: Float,
  revenue_estimate: Float,
  fiscal_period: String,
  created_at: DateTime
}
```

**Source Events**: (Future - not yet implemented)

---

#### 3b. SECFiling (:Event:SECFiling)

**Description**: SEC filings (10-K, 10-Q, 8-K, etc.)

**Properties**:
```cypher
{
  filing_id: String! (unique),
  symbol: String!,
  filing_type: String!,
  filing_date: Date!,
  report_date: Date,
  accepted_date: DateTime,
  filing_url: String,
  created_at: DateTime
}
```

**Source Events**:
- `finance.sec.filing.new`

**Indexes**:
```cypher
CREATE INDEX sec_filing_id IF NOT EXISTS FOR (f:SECFiling) ON (f.filing_id);
CREATE INDEX sec_filing_type IF NOT EXISTS FOR (f:SECFiling) ON (f.filing_type);
CREATE INDEX sec_filing_date IF NOT EXISTS FOR (f:SECFiling) ON (f.filing_date);
```

---

#### 3c. InsiderTrade (:Event:InsiderTrade)

**Description**: Insider trading transactions

**Properties**:
```cypher
{
  trade_id: String! (unique),
  symbol: String!,
  filing_date: Date!,
  transaction_date: Date,
  insider_name: String!,
  insider_title: String,
  transaction_type: String!,
  shares: Integer,
  price_per_share: Float,
  total_value: Float,
  shares_owned_after: Integer,
  created_at: DateTime
}
```

**Source Events**:
- `finance.insider.trade.new`

**Indexes**:
```cypher
CREATE INDEX insider_trade_id IF NOT EXISTS FOR (t:InsiderTrade) ON (t.trade_id);
CREATE INDEX insider_trade_date IF NOT EXISTS FOR (t:InsiderTrade) ON (t.filing_date);
CREATE INDEX insider_name IF NOT EXISTS FOR (t:InsiderTrade) ON (t.insider_name);
```

---

#### 3d. MergerAcquisition (:Event:MergerAcquisition)

**Description**: M&A transactions

**Properties**:
```cypher
{
  ma_id: String! (unique),
  acquiring_symbol: String!,
  target_symbol: String!,
  target_name: String!,
  announcement_date: Date!,
  completion_date: Date,
  deal_value_usd: Float,
  deal_type: String,
  status: String,
  created_at: DateTime
}
```

**Source Events**:
- `finance.ma.new`

**Indexes**:
```cypher
CREATE INDEX ma_id IF NOT EXISTS FOR (m:MergerAcquisition) ON (m.ma_id);
CREATE INDEX ma_date IF NOT EXISTS FOR (m:MergerAcquisition) ON (m.announcement_date);
```

---

### 4. MarketIndicator (:MarketIndicator)

**Description**: Market indicators and economic data

**Properties**:
```cypher
{
  indicator_id: String! (unique),
  indicator_type: String!, // 'VIX', 'DXY', 'TREASURY_10Y', 'T10YIE', etc.
  date: Date!,
  value: Float!,
  metadata: Map, // Additional indicator-specific data
  created_at: DateTime
}
```

**Source Events**:
- `finance.volatility.updated` → VIX, VVIX, MOVE
- `finance.indices.dxy.updated` → DXY
- `finance.carry_trade.updated` → AUD/JPY
- `finance.treasury.yields.updated` → 3M, 2Y, 10Y, Spreads
- `finance.inflation.breakeven.updated` → T5YIE, T10YIE
- `finance.real_rates.updated` → TIPS 10Y

**Indexes**:
```cypher
CREATE INDEX indicator_type_date IF NOT EXISTS FOR (i:MarketIndicator) ON (i.indicator_type, i.date);
```

---

### 5. MarketRegime (:MarketRegime)

**Description**: Market regime state (Risk-On/Off/Transitional)

**Properties**:
```cypher
{
  date: Date! (unique),
  regime_type: String!, // 'RISK_ON', 'RISK_OFF', 'TRANSITIONAL'
  regime_score: Float!, // -1.0 to +1.0
  vix_signal: Float,
  correlation_signal: Float,
  yield_curve_signal: Float,
  dxy_signal: Float,
  carry_trade_signal: Float,
  transition_probability: Float,
  created_at: DateTime
}
```

**Source Events**:
- `finance.regime.changed`

**Indexes**:
```cypher
CREATE INDEX regime_date IF NOT EXISTS FOR (r:MarketRegime) ON (r.date);
CREATE INDEX regime_type IF NOT EXISTS FOR (r:MarketRegime) ON (r.regime_type);
```

---

## 🔗 Relationship Types

### 1. WORKS_FOR

**Description**: Executive works for Company

**Pattern**: `(e:Executive)-[:WORKS_FOR]->(c:Company)`

**Properties**:
```cypher
{
  title: String,
  since_year: Integer,
  pay_usd: Float,
  created_at: DateTime
}
```

**Source**: `finance.executives.updated`

---

### 2. ACQUIRED

**Description**: Company acquired another company (M&A)

**Pattern**: `(acquirer:Company)-[:ACQUIRED]->(target:Company)`

**Properties**:
```cypher
{
  announcement_date: Date!,
  completion_date: Date,
  deal_value_usd: Float,
  deal_type: String,
  status: String,
  created_at: DateTime
}
```

**Source**: `finance.ma.new`

---

### 3. FILED

**Description**: Company filed SEC document

**Pattern**: `(c:Company)-[:FILED]->(f:SECFiling)`

**Properties**:
```cypher
{
  filing_type: String!,
  filing_date: Date!,
  created_at: DateTime
}
```

**Source**: `finance.sec.filing.new`

---

### 4. TRADES_IN

**Description**: Executive trades in company stock (insider trading)

**Pattern**: `(e:Executive)-[:TRADES_IN]->(t:InsiderTrade)-[:OF_COMPANY]->(c:Company)`

**Properties (on TRADES_IN)**:
```cypher
{
  transaction_type: String!, // 'BUY', 'SELL'
  transaction_date: Date!,
  shares: Integer,
  price_per_share: Float,
  total_value: Float,
  created_at: DateTime
}
```

**Source**: `finance.insider.trade.new`

---

### 5. HAS_FINANCIALS

**Description**: Company has financial statement for fiscal period

**Pattern**: `(c:Company)-[:HAS_FINANCIALS {fiscal_period, fiscal_year}]->(fs:FinancialStatement)`

**Properties**:
```cypher
{
  fiscal_period: String!, // 'Q1', 'Q2', 'Q3', 'Q4', 'FY'
  fiscal_year: Integer!,
  statement_type: String!, // 'INCOME', 'BALANCE', 'CASHFLOW', 'RATIOS', 'GROWTH'
  created_at: DateTime
}
```

**Source**: `finance.financials.*`

---

### 6. CORRELATED_WITH

**Description**: Asset/Indicator correlation (from DCC-GARCH)

**Pattern**: `(a:Company|MarketIndicator)-[:CORRELATED_WITH]->(b:Company|MarketIndicator)`

**Properties**:
```cypher
{
  correlation: Float!, // -1.0 to +1.0
  window_days: Integer!, // 30, 90, 180
  calculation_date: Date!,
  method: String!, // 'DCC-GARCH', 'Pearson'
  created_at: DateTime
}
```

**Source**: `finance.correlation.updated`

**Constraint**: Undirected relationship (create only a→b where a.symbol < b.symbol alphabetically)

---

### 7. IN_REGIME

**Description**: Date has specific market regime

**Pattern**: `(r:MarketRegime {date: Date})`

**Note**: This is stored as node properties, not relationship

**Source**: `finance.regime.changed`

---

## 📈 Graph Patterns & Queries

### Pattern 1: Executive Network Analysis

```cypher
// Find all executives who worked together at multiple companies
MATCH (e1:Executive)-[:WORKS_FOR]->(c1:Company)<-[:WORKS_FOR]-(e2:Executive)
WHERE e1 <> e2
WITH e1, e2, count(DISTINCT c1) as companies_together
WHERE companies_together > 1
RETURN e1.name, e2.name, companies_together
ORDER BY companies_together DESC
```

### Pattern 2: M&A Network (Company Acquisition Tree)

```cypher
// Find acquisition chains (A acquired B, B acquired C)
MATCH path=(acquirer:Company)-[:ACQUIRED*1..3]->(target:Company)
RETURN path
```

### Pattern 3: Insider Trading Patterns

```cypher
// Find executives with significant recent sales
MATCH (e:Executive)-[t:TRADES_IN]->(trade:InsiderTrade)-[:OF_COMPANY]->(c:Company)
WHERE trade.transaction_type = 'SELL'
  AND trade.transaction_date > date('2024-01-01')
  AND trade.total_value > 1000000
RETURN e.name, c.symbol, trade.transaction_date, trade.total_value
ORDER BY trade.total_value DESC
```

### Pattern 4: Regime Correlation Analysis

```cypher
// Find companies highly correlated during RISK_OFF regimes
MATCH (c1:Company)-[corr:CORRELATED_WITH]->(c2:Company)
WHERE corr.correlation > 0.8
WITH c1, c2, corr
MATCH (r:MarketRegime)
WHERE r.regime_type = 'RISK_OFF'
  AND r.date = corr.calculation_date
RETURN c1.symbol, c2.symbol, corr.correlation, r.regime_score
ORDER BY corr.correlation DESC
```

### Pattern 5: Company Event Timeline

```cypher
// Get all events for a company in chronological order
MATCH (c:Company {symbol: 'AAPL'})
OPTIONAL MATCH (c)-[:FILED]->(filing:SECFiling)
OPTIONAL MATCH (c)<-[:OF_COMPANY]-(trade:InsiderTrade)
OPTIONAL MATCH (c)-[:ACQUIRED]->(target:Company)
WITH c,
     collect({type: 'SEC_FILING', date: filing.filing_date, data: filing}) as filings,
     collect({type: 'INSIDER_TRADE', date: trade.transaction_date, data: trade}) as trades,
     collect({type: 'ACQUISITION', date: target.announcement_date, data: target}) as acquisitions
UNWIND filings + trades + acquisitions as event
RETURN event.type, event.date, event.data
ORDER BY event.date DESC
```

---

## 🔄 Event Processing Flow

```
FMP Service Background Jobs
         ↓
   RabbitMQ (finance.* events)
         ↓
Knowledge-Graph Service
    (Finance Intelligence Consumer)
         ↓
   Transform Event → Cypher Queries
         ↓
   Neo4j (Create Nodes + Relationships)
```

### Event → Node/Relationship Mapping

| Event | Action |
|-------|--------|
| `finance.company.updated` | MERGE Company node |
| `finance.executives.updated` | MERGE Executive + WORKS_FOR relationship |
| `finance.ma.new` | MERGE MergerAcquisition + ACQUIRED relationship |
| `finance.sec.filing.new` | CREATE SECFiling + FILED relationship |
| `finance.insider.trade.new` | CREATE InsiderTrade + TRADES_IN + OF_COMPANY |
| `finance.financials.*` | CREATE FinancialStatement + HAS_FINANCIALS |
| `finance.key_metrics.updated` | UPDATE Company properties (P/E, ROE, etc.) |
| `finance.volatility.updated` | CREATE MarketIndicator (VIX, VVIX, MOVE) |
| `finance.treasury.yields.updated` | CREATE MarketIndicator (3M, 2Y, 10Y, Spreads) |
| `finance.correlation.updated` | CREATE CORRELATED_WITH relationships |
| `finance.regime.changed` | MERGE MarketRegime node |

---

## 📊 Performance Considerations

### Indexing Strategy

**Required Indexes** (already listed above):
- Company: symbol, cik, sector
- Executive: name
- SECFiling: filing_id, filing_type, filing_date
- InsiderTrade: trade_id, filing_date, insider_name
- MergerAcquisition: ma_id, announcement_date
- MarketIndicator: (indicator_type, date) composite
- MarketRegime: date, regime_type

### Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT company_symbol_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.symbol IS UNIQUE;
CREATE CONSTRAINT sec_filing_id_unique IF NOT EXISTS FOR (f:SECFiling) REQUIRE f.filing_id IS UNIQUE;
CREATE CONSTRAINT insider_trade_id_unique IF NOT EXISTS FOR (t:InsiderTrade) REQUIRE t.trade_id IS UNIQUE;
CREATE CONSTRAINT ma_id_unique IF NOT EXISTS FOR (m:MergerAcquisition) REQUIRE m.ma_id IS UNIQUE;
CREATE CONSTRAINT regime_date_unique IF NOT EXISTS FOR (r:MarketRegime) REQUIRE r.date IS UNIQUE;
```

### Batch Processing

- **Correlations**: Bulk insert using `UNWIND` for 50+ pairs per event
- **Market Indicators**: Group by date, insert all indicators for same date together
- **SEC Filings**: Batch process filings for same company

---

## 🎯 Next Steps

1. ✅ **Schema Design** - This document
2. **Create Finance Intelligence Consumer** - Listen to all finance.* events
3. **Implement Node Creation Logic** - Cypher query builders for each node type
4. **Implement Relationship Creation** - Link nodes based on events
5. **Create Graph Query API** - Endpoints for graph analytics
6. **Testing** - Verify graph integrity, query performance

---

**Author**: Claude Code
**Last Updated**: 2025-11-16

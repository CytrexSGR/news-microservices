# Financial Impact Knowledge Extraction

## Markets to Track

### Indices
- ^GSPC (S&P 500)
- ^DJI (Dow Jones)
- ^IXIC (NASDAQ)
- ^FTSE (FTSE 100)

### Crypto
- BTC (Bitcoin)
- ETH (Ethereum)
- XRP (Ripple)
- SOL (Solana)
- ADA (Cardano)

### Currencies
- USD (US Dollar)
- EUR (Euro)
- JPY (Yen)
- GBP (Pound)

### Commodities
- GOLD (Gold)
- CRUDE (Oil)
- SILVER (Silver)

## News Events/Topics

### Monetary Policy
1. **Interest Rate Hike**
   - Affected Markets:
     * S&P 500: DOWN (strength: 0.85, lag: 1 day)
       - Mechanism: Higher discount rates reduce stock valuations
       - Historical: 2022-2023 Fed hikes → -20% SPY

     * USD: UP (strength: 0.75, immediate)
       - Mechanism: Higher yields attract foreign capital

     * Bitcoin: DOWN (strength: 0.70, immediate)
       - Mechanism: Risk-off sentiment, opportunity cost vs bonds

     * Gold: DOWN (strength: 0.60, 1-3 days)
       - Mechanism: Stronger USD, higher opportunity cost

2. **Interest Rate Cut**
   - Affected Markets:
     * S&P 500: UP (strength: 0.80, 1 day)
     * USD: DOWN (strength: 0.70, immediate)
     * Bitcoin: UP (strength: 0.65, immediate)
     * Gold: UP (strength: 0.55, 1-3 days)

### Crypto-Specific Events

3. **Bitcoin ETF News**
   - Affected Markets:
     * BTC: UP (strength: 0.90, immediate)
     * ETH: UP (strength: 0.75, lag: 2 hours) - correlation
     * XRP: UP (strength: 0.60, lag: 4 hours)
     * SOL: UP (strength: 0.65, lag: 4 hours)

4. **Crypto Regulation (Negative)**
   - Affected Markets:
     * All Crypto: DOWN (strength: 0.80, immediate)
     * Compliance Coins (XRP): DOWN (strength: 0.90, immediate)

### Geopolitical

5. **War/Major Conflict**
   - Affected Markets:
     * Gold: UP (strength: 0.85, immediate) - safe haven
     * Oil: UP (strength: 0.75, immediate) - supply concerns
     * S&P 500: DOWN (strength: 0.60, 1 day) - risk-off
     * Bitcoin: MIXED (strength: 0.40) - unclear direction

### Economic Data

6. **High Inflation Report (CPI)**
   - Affected Markets:
     * Bonds: DOWN (strength: 0.80, immediate)
     * Gold: UP (strength: 0.70, 1 day) - inflation hedge
     * S&P 500: DOWN (strength: 0.60, 1 day) - rate hike expectations

## Correlation Relationships

### Crypto Market
- BTC leads all altcoins (0.85-0.95 correlation, 1-4 hour lag)
- ETH follows BTC (0.92 correlation, 1 hour lag)
- Altcoins follow BTC stronger in downturns

### Traditional Markets
- Tech stocks more sensitive to rates (1.2x S&P reaction)
- USD inverse to commodities (0.70 correlation)
- Bonds inverse to stocks in risk-off (0.80 correlation)

## Implementation Notes

Convert this to Cypher CREATE statements:
- Nodes: Market entities, Event types, Institutions
- Relationships: IMPACTS, LEADS, CORRELATES_WITH
- Properties: direction, strength, lag_time, mechanism


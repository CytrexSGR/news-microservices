# Live Indicators API Discovery

**Erstellt:** 2025-12-07
**Status:** Discovery abgeschlossen
**Zweck:** Dokumentation der bestehenden API-Struktur für Live Indicators Feature

---

## 1. Executive Summary

**Wichtigste Erkenntnisse:**

1. ✅ **Prediction Service API existiert bereits** und liefert Indicator-Daten
2. ✅ **React Query Hooks existieren** (`useIndicators`, `useHistoricalIndicators`)
3. ⚠️ **Type-Definitionen sind veraltet** (zeigen nur 4 statt 14 Indikatoren)
4. ⚠️ **Kein Timeframe-Parameter** bei Indicators API (nur bei OHLCV)
5. ✅ **Auto-Refresh implementiert** (60s Interval, 30s Stale Time)

---

## 2. API-Struktur

### 2.1 Prediction Service Endpoints

**Base URL:** `/api/prediction/v1` (via Vite Proxy → `localhost:8116`)

| Endpoint | Methode | Parameter | Response Type |
|----------|---------|-----------|---------------|
| `/indicators/{symbol}/current` | GET | `symbol` (Bybit format) | `IndicatorsSnapshot` |
| `/indicators/{symbol}/historical` | GET | `symbol`, `hours` (default: 24) | `HistoricalIndicator[]` |
| `/market-data/ohlcv` | GET | `symbol`, `timeframe`, `limit`, `since?` | `OHLCV[]` |
| `/indicators/symbols` | GET | - | `string[]` |

**Symbol-Konvertierung:**
- Frontend nutzt: `BTCUSDT`, `ETHUSDT`
- API erwartet: `BTC/USDT:USDT`, `ETH/USDT:USDT` (Bybit-Format)
- Konvertierung: `toBybitSymbol()` Utility-Funktion

### 2.2 Indicators API Response

**Laut Type-Definitionen** (`/frontend/src/types/indicators.ts`):

```typescript
interface IndicatorsSnapshot {
  symbol: string
  timestamp: string
  rsi: RSIIndicator
  macd: MACDIndicator
  ema: EMAIndicator
  volume: VolumeIndicator
  consensus: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number // 0-1
}
```

**Tatsächlich verwendet in TradingIndicatorsPage** (14 Indikatoren):

```typescript
interface ActualIndicatorsSnapshot {
  // TREND (5 Indikatoren)
  rsi: RSIIndicator                    // ✅ In Types
  macd: MACDIndicator                  // ✅ In Types
  ema: EMAIndicator                    // ✅ In Types (nur EMA200)
  adx: ADXIndicator                    // ❌ FEHLT in Types
  stochastic_rsi: StochasticRSI        // ❌ FEHLT in Types

  // VOLUME/VOLATILITY (5 Indikatoren)
  volume: VolumeIndicator              // ✅ In Types
  obv: OBVIndicator                    // ❌ FEHLT in Types
  volume_profile: VolumeProfile        // ❌ FEHLT in Types
  bollinger_bands: BollingerBands      // ❌ FEHLT in Types
  atr: ATRIndicator                    // ❌ FEHLT in Types

  // MARKET STRUCTURE (4 Indikatoren)
  fair_value_gaps: FairValueGaps       // ❌ FEHLT in Types
  liquidity_sweeps: LiquiditySweeps    // ❌ FEHLT in Types
  funding_rate: FundingRate            // ❌ FEHLT in Types
  open_interest: OpenInterest          // ❌ FEHLT in Types

  // Consensus
  consensus: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number
}
```

**⚠️ Problem:** Type-Definitionen sind unvollständig (nur 4/14 Indikatoren definiert)

---

## 3. React Query Hooks

### 3.1 useIndicators Hook

**Location:** `/frontend/src/features/trading/hooks/useIndicators.ts`

```typescript
export function useIndicators(
  symbol: string,
  options?: UseQueryOptions<IndicatorsSnapshot, Error>
) {
  return useQuery<IndicatorsSnapshot, Error>({
    queryKey: indicatorKeys.current(symbol),
    queryFn: () => predictionService.getIndicators(symbol),
    refetchInterval: 60_000,    // 60 Sekunden
    staleTime: 30_000,          // 30 Sekunden
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...options,
  })
}
```

**Features:**
- ✅ Auto-Refresh alle 60 Sekunden
- ✅ Stale Time 30 Sekunden (reduziert unnötige Requests)
- ✅ Retry Logic (exponential backoff)
- ✅ Query Key Invalidierung unterstützt

### 3.2 useHistoricalIndicators Hook

```typescript
export function useHistoricalIndicators(
  symbol: string,
  options?: UseQueryOptions<HistoricalIndicator[], Error>
) {
  return useQuery<HistoricalIndicator[], Error>({
    queryKey: indicatorKeys.historical(symbol),
    queryFn: () => predictionService.getHistoricalIndicators(symbol),
    refetchInterval: 300_000,   // 5 Minuten
    staleTime: 120_000,         // 2 Minuten
    retry: 3,
    ...options,
  })
}
```

**Verwendung:** Für Charts/Trends (weniger frequent als live data)

---

## 4. Prediction Service Client

**Location:** `/frontend/src/lib/api/prediction-service.ts`

```typescript
class PredictionServiceClient {
  async getIndicators(symbol: string): Promise<IndicatorsSnapshot> {
    const bybitSymbol = toBybitSymbol(symbol)
    const encodedSymbol = encodeURIComponent(bybitSymbol)
    const response = await this.client.get<IndicatorsSnapshot>(
      `/indicators/${encodedSymbol}/current`
    )
    return response.data
  }
}

export const predictionService = new PredictionServiceClient()
```

**Pattern:**
- Singleton Instance (`predictionService`)
- Symbol-Konvertierung vor Request
- URL Encoding für Sonderzeichen
- Type-Safety mit TypeScript Generics

---

## 5. Kritische Erkenntnisse für Implementation

### 5.1 Timeframe-Problem

**Aktuell:**
- Indicators API: **Kein Timeframe-Parameter**
- OHLCV API: **Hat Timeframe-Parameter** (1m, 5m, 15m, 1h, 4h, 1d)

**Implikation:**
- Indicators werden **immer** für denselben Timeframe berechnet (vermutlich 1h)
- Für Regime Detection mit Multi-Timeframe: **API-Erweiterung nötig**

**Optionen:**
1. **Kurzfristig:** Nur 1h Timeframe nutzen (wie aktuell)
2. **Mittelfristig:** Backend-API erweitern für Timeframe-Parameter
3. **Langfristig:** Multi-Timeframe Regime Detection mit separaten Requests

**Empfehlung für Phase 1:** Option 1 (1h Timeframe) - schnellste Umsetzung

### 5.2 Fehlende Type-Definitionen

**Problem:** Types zeigen nur 4 Indikatoren, API liefert aber 14

**Lösung:**
1. Type-Definitionen vervollständigen (`indicators.ts`)
2. Alle 10 fehlenden Indikatoren typisieren
3. Sicherstellen, dass `IndicatorsSnapshot` vollständig ist

**Priorität:** HOCH - Sonst kein Type-Safety!

### 5.3 Regime Detection Daten

**Gebraucht für Regime Detection:**

| Regime | Benötigte Indikatoren | Verfügbar? | Status |
|--------|----------------------|------------|---------|
| **TREND** | ADX, +DI, -DI | ADX ✅, +DI/-DI ❓ | ADX vorhanden, +DI/-DI in ADX-Objekt? |
| **TREND** | EMA 10, 20 | ❌ | Nur EMA200 verfügbar |
| **TREND** | Volume Ratio | ✅ | Volume Indicator hat `ratio` |
| **CONSOLIDATION** | ADX | ✅ | Vorhanden |
| **CONSOLIDATION** | BBW | ✅ | Bollinger Bands vorhanden |
| **CONSOLIDATION** | RSI | ✅ | Vorhanden |
| **HIGH_VOLATILITY** | ATR | ✅ | Vorhanden |
| **HIGH_VOLATILITY** | BBW | ✅ | Bollinger Bands vorhanden |

**Fehlende Daten:**
- ❌ EMA 10, EMA 20 (nur EMA200 verfügbar)
- ❓ +DI, -DI (möglicherweise in ADX-Objekt enthalten?)

**Action Items:**
1. Backend API prüfen: Enthält ADX-Response +DI/-DI?
2. Falls nein: Backend erweitern für +DI/-DI
3. EMA 10/20: Backend erweitern ODER Client-seitig aus OHLCV berechnen

---

## 6. Datenfluss

### 6.1 Current Data Flow (TradingIndicatorsPage)

```
┌─────────────────┐
│ TradingIndicators│
│     Page.tsx     │
└────────┬─────────┘
         │
         ├─ useIndicators(symbol)
         │  └─ React Query (60s auto-refresh)
         │     └─ predictionService.getIndicators(symbol)
         │        └─ GET /api/prediction/v1/indicators/{symbol}/current
         │           └─ Prediction Service Backend (Port 8116)
         │
         ├─ useHistoricalIndicators(symbol)
         │  └─ React Query (5min auto-refresh)
         │     └─ predictionService.getHistoricalIndicators(symbol)
         │        └─ GET /api/prediction/v1/indicators/{symbol}/historical
         │
         └─ useOHLCV(symbol, timeframe)
            └─ React Query
               └─ predictionService.getOHLCV(symbol, timeframe)
                  └─ GET /api/prediction/v1/market-data/ohlcv?...
```

### 6.2 Planned Data Flow (Strategy Overview mit Live Indicators)

```
┌─────────────────┐
│ Strategy Overview│
│      Page        │
└────────┬─────────┘
         │
         ├─ useState(selectedSymbol)  ← User wählt Pair
         ├─ useState(selectedTimeframe)  ← User wählt Timeframe
         │
         ├─ useStrategy(strategyId)  ← Bestehend
         │  └─ GET /api/prediction/v1/strategies/{id}
         │
         └─ useIndicators(selectedSymbol)  ← NEU
            └─ React Query (60s auto-refresh)
               └─ GET /api/prediction/v1/indicators/{symbol}/current
                  └─ Indicators für Regime Detection

┌──────────────────────────────────────────────┐
│ Komponenten-Struktur (geplant):              │
│                                               │
│ StrategyOverview                             │
│  ├─ StrategyControls                         │
│  │   ├─ PairSelector (selectedSymbol)        │
│  │   ├─ TimeframeSelector (selectedTimeframe)│
│  │   └─ RefreshButton                        │
│  │                                            │
│  ├─ RegimeStatus                             │
│  │   └─ Current Regime + Confidence          │
│  │                                            │
│  └─ Tabs (Overview, Indicators, Logic, ...)  │
│      └─ TREND Tab                            │
│          └─ RegimeIndicators                 │
│              ├─ IndicatorValue (ADX)         │
│              ├─ IndicatorValue (+DI/-DI)     │
│              ├─ IndicatorValue (Volume)      │
│              └─ ...                           │
└──────────────────────────────────────────────┘
```

---

## 7. Gap Analysis: Was fehlt?

### 7.1 API-Ebene

| Feature | Status | Bemerkung |
|---------|--------|-----------|
| Indicators für Symbol | ✅ Vorhanden | `/indicators/{symbol}/current` |
| Timeframe-Parameter | ❌ Fehlt | Nur bei OHLCV, nicht bei Indicators |
| +DI/-DI Indikatoren | ❓ Unklar | Möglicherweise in ADX enthalten? |
| EMA 10/20 | ❌ Fehlt | Nur EMA200 verfügbar |
| Regime Detection Logic | ❌ Fehlt | Aktuell nur in Strategy, nicht als Endpoint |

### 7.2 Frontend-Ebene

| Feature | Status | Bemerkung |
|---------|--------|-----------|
| Type-Definitionen | ⚠️ Unvollständig | Nur 4/14 Indikatoren typisiert |
| useIndicators Hook | ✅ Vorhanden | Kann direkt genutzt werden |
| Pair Selector UI | ❌ Fehlt | Muss erstellt werden |
| Timeframe Selector UI | ❌ Fehlt | Muss erstellt werden |
| Regime Status Display | ❌ Fehlt | Muss erstellt werden |
| Live Indicator Cards | ⚠️ Teilweise | In TradingIndicatorsPage vorhanden, für Strategy anpassen |

### 7.3 Regime Detection

| Komponente | Status | Bemerkung |
|-----------|--------|-----------|
| ADX Berechnung | ✅ Vorhanden | Teil der Indicators |
| ATR Berechnung | ✅ Vorhanden | Teil der Indicators |
| BBW Berechnung | ✅ Vorhanden | Bollinger Bands verfügbar |
| RSI Berechnung | ✅ Vorhanden | Teil der Indicators |
| Volume Ratio | ✅ Vorhanden | Teil des Volume Indicators |
| EMA 10/20 Kreuzung | ❌ Fehlt | Nur EMA200 verfügbar |
| +DI/-DI Comparison | ❓ Unklar | Muss geprüft werden |
| Regime Classification Logic | ⚠️ Backend | Existiert in Strategy Engine, nicht als Endpoint |

---

## 8. Empfehlungen für Implementation

### Phase 1: Quick Win (Bestehende API nutzen)

**Scope:** Live Indicators mit 1h Timeframe (fest), ohne Multi-TF

**Änderungen:**
1. ✅ Type-Definitionen vervollständigen (`indicators.ts`)
2. ✅ `StrategyControls` Komponente erstellen (nur Pair Selector)
3. ✅ `RegimeStatus` Komponente erstellen (Regime anzeigen)
4. ✅ `RegimeIndicators` Komponente erstellen (Indicators pro Regime)
5. ✅ `useIndicators` Hook in Strategy Overview integrieren

**Zeitaufwand:** ~8-10 Stunden

**Einschränkungen:**
- Kein Timeframe-Wechsel (fest 1h)
- Möglicherweise fehlende +DI/-DI (falls nicht in ADX enthalten)
- Keine EMA 10/20 (nur EMA200)

### Phase 2: API-Erweiterung (Backend Changes)

**Scope:** Timeframe-Support, fehlende Indikatoren

**Backend-Änderungen:**
1. Indicators Endpoint um `timeframe` Parameter erweitern
2. +DI/-DI in ADX-Response aufnehmen (falls noch nicht)
3. EMA 10/20 berechnen und zurückgeben
4. Regime Detection als separater Endpoint (`/regime/{symbol}?timeframe={tf}`)

**Frontend-Änderungen:**
1. `getIndicators()` um Timeframe-Parameter erweitern
2. Timeframe Selector UI implementieren
3. Multi-Timeframe Support in Hooks

**Zeitaufwand:** ~15-20 Stunden (Backend + Frontend)

### Phase 3: Regime Detection Endpoint (Optional)

**Scope:** Dedizierter Endpoint für Regime Detection

**Vorteil:**
- Backend berechnet Regime (Single Source of Truth)
- Konsistenz zwischen Strategy und UI
- Weniger Client-seitige Logik

**Endpoint Design:**
```
GET /api/prediction/v1/regime/{symbol}?timeframe=1h

Response:
{
  "regime": "TREND" | "CONSOLIDATION" | "HIGH_VOLATILITY",
  "confidence": 0.85,
  "indicators_used": {
    "adx": 28.5,
    "atr": 125.3,
    "bbw": 0.045,
    ...
  },
  "thresholds_met": {
    "adx_gt_25": true,
    "plus_di_gt_minus_di": true,
    ...
  }
}
```

**Zeitaufwand:** ~10 Stunden (Backend + Frontend Integration)

---

## 9. Nächste Schritte

**Sofort:**
1. ✅ Discovery abgeschlossen - Dieses Dokument erstellt
2. 🔄 Implementation Plan aktualisieren basierend auf Findings
3. 🔄 Entscheiden: Phase 1 (Quick Win) oder Phase 2 (Full Support)?

**Phase 1 Umsetzung (Quick Win):**
1. Type-Definitionen vervollständigen
2. UI-Komponenten erstellen (StrategyControls, RegimeStatus, RegimeIndicators)
3. Integration in Strategy Overview
4. Testing

**Danach:**
- Backend API prüfen: +DI/-DI enthalten?
- Backend API prüfen: Regime Detection Logic vorhanden?
- Entscheiden ob Phase 2 nötig

---

## 10. Appendix: Vollständige Indicator Types (Extrapoliert)

**Basierend auf TradingIndicatorsPage Verwendung:**

```typescript
// Fehlende Type-Definitionen (müssen hinzugefügt werden)

export interface ADXIndicator {
  adx: number                              // 0-100
  plus_di?: number                         // +DI (Directional Indicator)
  minus_di?: number                        // -DI (Directional Indicator)
  trend_strength: 'WEAK' | 'MODERATE' | 'STRONG'
  market_phase: 'TRENDING' | 'RANGING'
}

export interface StochasticRSIIndicator {
  k: number                                // 0-100
  d?: number                               // 0-100
  signal: 'OVERSOLD' | 'NEUTRAL' | 'OVERBOUGHT'
  interpretation: string
}

export interface OBVIndicator {
  value: number
  trend: 'RISING' | 'FALLING' | 'NEUTRAL'
  divergence?: 'BULLISH' | 'BEARISH' | null
}

export interface VolumeProfileIndicator {
  poc: number                              // Point of Control
  value_area_high?: number
  value_area_low?: number
  signal: 'SUPPORT' | 'RESISTANCE' | 'NEUTRAL'
  interpretation: string
}

export interface BollingerBandsIndicator {
  upper: number
  middle: number
  lower: number
  bandwidth: number                        // BBW (Bollinger Band Width)
  position: 'ABOVE_UPPER' | 'BETWEEN' | 'BELOW_LOWER'
  interpretation: string
}

export interface ATRIndicator {
  value: number
  percentage: number                       // ATR as % of price
  volatility: 'LOW' | 'NORMAL' | 'HIGH'
}

export interface FairValueGapsIndicator {
  recent_unfilled_bullish: number
  recent_unfilled_bearish: number
  signal: 'BULLISH_GAPS' | 'BEARISH_GAPS' | 'NEUTRAL'
  interpretation: string
}

export interface LiquiditySweepsIndicator {
  recent_bullish_sweeps: number
  recent_bearish_sweeps: number
  signal: 'BULLISH_SWEEP' | 'BEARISH_SWEEP' | 'NEUTRAL'
  interpretation: string
}

export interface FundingRateIndicator {
  rate_percent: number
  signal: 'LONG_PRESSURE' | 'SHORT_PRESSURE' | 'NEUTRAL'
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
}

export interface OpenInterestIndicator {
  value_usd: number
  change_percent?: number
  signal: 'RISING' | 'FALLING' | 'NEUTRAL'
  interpretation: string
}

// Vollständige IndicatorsSnapshot (erweitert)
export interface CompleteIndicatorsSnapshot {
  symbol: string
  timestamp: string

  // TREND
  rsi: RSIIndicator
  macd: MACDIndicator
  ema: EMAIndicator
  adx: ADXIndicator
  stochastic_rsi: StochasticRSIIndicator

  // VOLUME/VOLATILITY
  volume: VolumeIndicator
  obv: OBVIndicator
  volume_profile: VolumeProfileIndicator
  bollinger_bands: BollingerBandsIndicator
  atr: ATRIndicator

  // MARKET STRUCTURE
  fair_value_gaps: FairValueGapsIndicator
  liquidity_sweeps: LiquiditySweepsIndicator
  funding_rate: FundingRateIndicator
  open_interest: OpenInterestIndicator

  // Consensus
  consensus: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number // 0-1
}
```

---

**Ende der Discovery-Dokumentation**

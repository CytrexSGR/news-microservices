# Live Indicators Integration: Umsetzungsplan

**Erstellt:** 2025-12-07
**Aktualisiert:** 2025-12-07 (nach API Discovery)
**Ziel:** Strategy Overview mit Live-Indikator-Daten erweitern
**Status:** Discovery abgeschlossen → Bereit für Implementierung

**📋 Related Documents:**
- [API Discovery Results](./LIVE_INDICATORS_API_DISCOVERY.md) - Vollständige API-Analyse

---

## 1. Executive Summary

**Anforderung:**
Erweitere `/trading/strategy/:strategyId` um Live-Indikator-Anzeige pro Regime mit Pair-Auswahl.

**Kern-Features:**
- ✅ 14 vorhandene Indikatoren live anzeigen
- ✅ Pro Regime-Tab: Relevante Indikatoren gruppiert
- ✅ Pair-Selector (BTCUSDT, ETHUSDT, etc.)
- ✅ Timeframe-Selector (15m, 1h, 4h, 1d)
- ✅ Auto-Refresh optional

**Geschätzte Dauer:** 1-2 Tage
**Anpassung nach Discovery:** ~10-12 Stunden (viele Komponenten bereits vorhanden)

---

## 2. Anforderungsanalyse

### 2.1 Funktionale Anforderungen

| ID | Anforderung | Priorität | Aufwand |
|----|-------------|-----------|---------|
| FR-1 | Pair-Auswahl oben (Dropdown) | Hoch | 1h |
| FR-2 | Timeframe-Auswahl (15m, 1h, 4h, 1d) | Hoch | 0.5h |
| FR-3 | Live-Daten per API abrufen | Hoch | 2h |
| FR-4 | TREND-Tab: ADX, +DI/-DI, EMA, Volumen, ATR anzeigen | Hoch | 2h |
| FR-5 | CONSOLIDATION-Tab: ADX, BBW, RSI, EMA anzeigen | Hoch | 1h |
| FR-6 | HIGH_VOLATILITY-Tab: ATR, BBW, ADX anzeigen | Hoch | 1h |
| FR-7 | Aktuelles Regime hervorheben | Mittel | 1h |
| FR-8 | Auto-Refresh (30s/60s) | Niedrig | 1h |
| FR-9 | Loading States | Mittel | 0.5h |
| FR-10 | Error Handling | Mittel | 1h |

### 2.2 Nicht-funktionale Anforderungen

| ID | Anforderung | Kriterium |
|----|-------------|-----------|
| NFR-1 | Performance | API-Call < 500ms |
| NFR-2 | Usability | Intuitive Bedienung |
| NFR-3 | Responsiveness | Mobile-friendly |
| NFR-4 | Accessibility | WCAG 2.1 AA |

---

## 3. Technische Analyse

### 3.1 Bestehende Komponenten

#### A) `/trading/indicators` Seite ✅ ANALYSIERT

**Ergebnisse der Discovery:**
- ✅ Nutzt `predictionService.getIndicators(symbol)`
- ✅ Nutzt `useIndicators()` React Query Hook (60s auto-refresh)
- ✅ Zeigt 14 Indikatoren: RSI, MACD, EMA, ADX, Stochastic RSI, Volume, OBV, Volume Profile, Bollinger Bands, ATR, Fair Value Gaps, Liquidity Sweeps, Funding Rate, Open Interest
- ⚠️ Type-Definitionen sind unvollständig (nur 4/14 typisiert)
- ⚠️ Kein Timeframe-Selector (nur Symbol-Auswahl)

**Files:**
- `frontend/src/features/trading/pages/TradingIndicatorsPage.tsx` (468 Zeilen)
- `frontend/src/features/trading/hooks/useIndicators.ts` (78 Zeilen)
- `frontend/src/lib/api/prediction-service.ts` (138 Zeilen)
- `frontend/src/types/indicators.ts` (51 Zeilen) - ⚠️ **MUSS ERWEITERT WERDEN**

#### B) `/trading/strategy/:strategyId` Seite

**Aktueller Stand:**
- 5 Tabs: Overview, Indicators, Logic, Risk Management, Execution
- Statische Anzeige der Strategy-Konfiguration
- Keine Live-Daten

**Zu erweitern:**
- Controls oben (Pair, Timeframe)
- Live-Daten in allen Tabs
- Regime-Status-Indikator

### 3.2 API-Struktur ✅ VERIFIZIERT

**Tatsächlicher Endpoint:**
```
GET /api/prediction/v1/indicators/{symbol}/current
```

**⚠️ KRITISCH: Kein Timeframe-Parameter!**
- API liefert Indicators für festen Timeframe (vermutlich 1h)
- Timeframe-Support benötigt Backend-Erweiterung

**Tatsächliche Response** (basierend auf Types + Code-Analyse):
```typescript
interface IndicatorsSnapshot {
  symbol: string                        // "BTCUSDT"
  timestamp: string                     // ISO8601

  // TREND Indicators (5)
  rsi: RSIIndicator                     // ✅ Vorhanden
  macd: MACDIndicator                   // ✅ Vorhanden
  ema: EMAIndicator                     // ✅ Nur EMA200, NICHT EMA10/20!
  adx: ADXIndicator                     // ✅ Vorhanden (ADX value, trend_strength, market_phase)
  stochastic_rsi: StochasticRSI         // ✅ Vorhanden

  // VOLUME/VOLATILITY Indicators (5)
  volume: VolumeIndicator               // ✅ Vorhanden (mit ratio!)
  obv: OBVIndicator                     // ✅ Vorhanden
  volume_profile: VolumeProfile         // ✅ Vorhanden
  bollinger_bands: BollingerBands       // ✅ Vorhanden (hat bandwidth = BBW!)
  atr: ATRIndicator                     // ✅ Vorhanden

  // MARKET STRUCTURE Indicators (4)
  fair_value_gaps: FairValueGaps        // ✅ Vorhanden
  liquidity_sweeps: LiquiditySweeps     // ✅ Vorhanden
  funding_rate: FundingRate             // ✅ Vorhanden
  open_interest: OpenInterest           // ✅ Vorhanden

  // Consensus
  consensus: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number                    // 0-1
}
```

**❌ NICHT in Response (laut Discovery):**
- `regime` Objekt (Regime Detection findet in Strategy Engine statt, nicht als separater Endpoint)
- Multi-Timeframe Daten (nur ein Timeframe pro Request)
- EMA 10/20 (nur EMA200 verfügbar)
- +DI/-DI als separate Werte (möglicherweise in `adx` Objekt?)

---

## 4. UI/UX Design

### 4.1 Layout-Struktur

```
┌─────────────────────────────────────────────────────────┐
│  Strategy Overview: Multi-Regime RSI Strategy           │
├─────────────────────────────────────────────────────────┤
│  Controls:                                              │
│  [Pair: BTCUSDT ▼]  [Timeframe: 1h ▼]  [🔄 Refresh]   │
│  Last Update: 2025-12-07 10:15:23                       │
├─────────────────────────────────────────────────────────┤
│  Current Regime: 🟢 TREND (Confidence: 85%)            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │ [Overview] [TREND] [CONSOLIDATION] [HIGH_VOL]  │   │
│  ├─────────────────────────────────────────────────┤   │
│  │                                                  │   │
│  │  TREND Indicators (Live)                        │   │
│  │  ────────────────────────────                   │   │
│  │  ADX (14):           28.5  ✅ > 25 (Strong)     │   │
│  │  +DI (14):           25.3                       │   │
│  │  -DI (14):           18.7  ✅ +DI > -DI         │   │
│  │  EMA 10:          43,250.5                      │   │
│  │  EMA 20:          43,100.2  ✅ 10 > 20          │   │
│  │  Price > EMA10:      ✅ Yes                     │   │
│  │  Volume Ratio:        1.35  ✅ > 1.2            │   │
│  │  ATR (14):           245.8                      │   │
│  │                                                  │   │
│  │  Trend Confirmation: 5/5 ✅                     │   │
│  │                                                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Regime-Tab Inhalte

#### TREND Tab

**Indikatoren:**
- ADX (14) mit Schwellenwert-Check (> 25)
- +DI / -DI mit Richtungs-Check (+DI > -DI für Aufwärts)
- EMA 10 / EMA 20 mit Hierarchie-Check (Price > EMA10 > EMA20)
- Volume Ratio mit Schwellenwert-Check (> 1.2)
- ATR (14) für Volatilität

**Visuelles Feedback:**
- ✅ Grün: Kriterium erfüllt
- ❌ Rot: Kriterium nicht erfüllt
- ⚠️ Gelb: Grenzwertig

#### CONSOLIDATION Tab

**Indikatoren:**
- ADX (14) mit Schwellenwert-Check (< 20)
- BBW (20) mit Squeeze-Indikation
- RSI (14) mit Neutral-Zone-Check (40-60)
- EMA Konvergenz (Abstand < 0.5%)
- Volume Ratio mit Low-Check (< 1.0)

#### HIGH_VOLATILITY Tab

**Indikatoren:**
- ATR (14) mit Durchschnitts-Vergleich
- ATR Percentile (80. Perzentil)
- BBW (20) mit High-Check
- ADX für Richtungsbestimmung

---

## 5. Implementierungsschritte

### Phase 1: API-Integration (2 Stunden) ✅ STARK REDUZIERT

> **Discovery-Ergebnis:** Viele Komponenten existieren bereits! Phase 1 fokussiert auf Type-Vervollständigung statt Neuentwicklung.

#### Step 1.1: Bestehende API analysieren ✅ ABGESCHLOSSEN

**Tasks:**
- [x] `/trading/indicators` Seite Code lesen → `TradingIndicatorsPage.tsx` (468 Zeilen)
- [x] API-Endpoint identifizieren → `/api/prediction/v1/indicators/{symbol}/current`
- [x] Datenstruktur dokumentieren → `LIVE_INDICATORS_API_DISCOVERY.md`
- [x] Bestehende Hooks gefunden → `useIndicators()`, `useHistoricalIndicators()`

**Ergebnis:** API und Hooks existieren bereits, können direkt genutzt werden!

#### Step 1.2: Type-Definitionen vervollständigen (1h) ⚠️ KRITISCH

**Problem:** `frontend/src/types/indicators.ts` zeigt nur 4 Indikatoren, API liefert aber 14!

**Location:** `frontend/src/types/indicators.ts`

**Zu hinzufügen:**
```typescript
// ADX Indicator (FEHLT komplett!)
export interface ADXIndicator {
  adx: number                              // 0-100
  plus_di?: number                         // +DI (falls vorhanden)
  minus_di?: number                        // -DI (falls vorhanden)
  trend_strength: 'WEAK' | 'MODERATE' | 'STRONG'
  market_phase: 'TRENDING' | 'RANGING'
}

// Stochastic RSI (FEHLT komplett!)
export interface StochasticRSIIndicator {
  k: number                                // 0-100
  d?: number
  signal: 'OVERSOLD' | 'NEUTRAL' | 'OVERBOUGHT'
  interpretation: string
}

// OBV (FEHLT komplett!)
export interface OBVIndicator {
  value: number
  trend: 'RISING' | 'FALLING' | 'NEUTRAL'
  divergence?: 'BULLISH' | 'BEARISH' | null
}

// Bollinger Bands (FEHLT komplett!)
export interface BollingerBandsIndicator {
  upper: number
  middle: number
  lower: number
  bandwidth: number                        // BBW (Bollinger Band Width)!
  position: 'ABOVE_UPPER' | 'BETWEEN' | 'BELOW_LOWER'
  interpretation: string
}

// ATR (FEHLT komplett!)
export interface ATRIndicator {
  value: number
  percentage: number                       // ATR as % of price
  volatility: 'LOW' | 'NORMAL' | 'HIGH'
}

// + 5 weitere: VolumeProfile, FairValueGaps, LiquiditySweeps, FundingRate, OpenInterest
// (Siehe LIVE_INDICATORS_API_DISCOVERY.md Appendix A für vollständige Definitionen)
```

**Dann `IndicatorsSnapshot` erweitern:**
```typescript
export interface IndicatorsSnapshot {
  symbol: string
  timestamp: string

  // TREND
  rsi: RSIIndicator
  macd: MACDIndicator
  ema: EMAIndicator
  adx: ADXIndicator                    // ← NEU
  stochastic_rsi: StochasticRSIIndicator // ← NEU

  // VOLUME/VOLATILITY
  volume: VolumeIndicator
  obv: OBVIndicator                    // ← NEU
  volume_profile: VolumeProfileIndicator // ← NEU
  bollinger_bands: BollingerBandsIndicator // ← NEU
  atr: ATRIndicator                    // ← NEU

  // MARKET STRUCTURE
  fair_value_gaps: FairValueGapsIndicator // ← NEU
  liquidity_sweeps: LiquiditySweepsIndicator // ← NEU
  funding_rate: FundingRateIndicator   // ← NEU
  open_interest: OpenInterestIndicator // ← NEU

  // Consensus
  consensus: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number
}
```

**Vollständige Type-Definitionen:** Siehe `LIVE_INDICATORS_API_DISCOVERY.md` Appendix A

#### Step 1.3: Bestehenden Hook anpassen (0.5h) ✅ VEREINFACHT

**Bestehendes:** `useIndicators()` Hook existiert bereits in `frontend/src/features/trading/hooks/useIndicators.ts`

**Änderungen:**
```typescript
// KEIN neuer Hook nötig! Bestehenden nutzen:
import { useIndicators } from '@/features/trading/hooks/useIndicators'

// Verwendung in StrategyOverview:
const { data: indicators, isLoading, error, refetch } = useIndicators(selectedSymbol)

// ✅ Auto-Refresh bereits implementiert (60s)
// ✅ React Query Caching bereits implementiert
// ✅ Error Handling bereits implementiert
```

**Optional:** Wrapper-Hook für Regime-spezifische Logik
```typescript
// frontend/src/hooks/useRegimeIndicators.ts
export const useRegimeIndicators = (symbol: string) => {
  const { data, ...rest } = useIndicators(symbol)

  // Regime-spezifische Berechnungen (falls nötig)
  const regimeData = useMemo(() => {
    if (!data) return null
    return {
      trend: extractTrendIndicators(data),
      consolidation: extractConsolidationIndicators(data),
      highVolatility: extractVolatilityIndicators(data)
    }
  }, [data])

  return { data: regimeData, ...rest }
}
```

#### Step 1.4: Testing Type-Definitionen (0.5h)

**Tasks:**
- [ ] TypeScript Compilation Check (keine Errors nach Type-Erweiterung)
- [ ] Type Coverage prüfen (alle 14 Indikatoren erfasst?)
- [ ] Mock-Daten mit vollständiger Response testen

### Phase 2: UI-Komponenten (5-6 Stunden)

#### Step 2.1: Controls Component (1.5h)

**Location:** `frontend/src/components/trading/StrategyControls.tsx`

```typescript
// frontend/src/components/trading/StrategyControls.tsx
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { RefreshCw } from 'lucide-react';

interface StrategyControlsProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
  timeframe: string;
  onTimeframeChange: (timeframe: string) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  lastUpdate?: string;
}

export const StrategyControls: React.FC<StrategyControlsProps> = ({
  symbol,
  onSymbolChange,
  timeframe,
  onTimeframeChange,
  onRefresh,
  isRefreshing,
  lastUpdate
}) => {
  const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'];
  const timeframes = [
    { value: '15m', label: '15 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' }
  ];

  return (
    <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Pair:</label>
        <Select value={symbol} onValueChange={onSymbolChange}>
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {symbols.map(s => (
              <SelectItem key={s} value={s}>{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Timeframe:</label>
        <Select value={timeframe} onValueChange={onTimeframeChange}>
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {timeframes.map(tf => (
              <SelectItem key={tf.value} value={tf.value}>
                {tf.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Button
        onClick={onRefresh}
        disabled={isRefreshing}
        variant="outline"
        size="sm"
      >
        <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
        Refresh
      </Button>

      {lastUpdate && (
        <div className="ml-auto text-sm text-muted-foreground">
          Last Update: {new Date(lastUpdate).toLocaleString()}
        </div>
      )}
    </div>
  );
};
```

#### Step 2.2: Regime Status Component (1h)

**Location:** `frontend/src/components/trading/RegimeStatus.tsx`

```typescript
// frontend/src/components/trading/RegimeStatus.tsx
import { Card, CardContent } from '@/components/ui/Card';
import { TrendingUp, BarChart3, Activity } from 'lucide-react';

interface RegimeStatusProps {
  regime: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY';
  confidence: number;
  scores: {
    trend_score: number;
    consolidation_score: number;
    high_volatility_score: number;
  };
}

export const RegimeStatus: React.FC<RegimeStatusProps> = ({
  regime,
  confidence,
  scores
}) => {
  const regimeConfig = {
    TREND: {
      icon: TrendingUp,
      color: 'text-green-500',
      bg: 'bg-green-500/10',
      label: 'Trend'
    },
    CONSOLIDATION: {
      icon: BarChart3,
      color: 'text-blue-500',
      bg: 'bg-blue-500/10',
      label: 'Consolidation'
    },
    HIGH_VOLATILITY: {
      icon: Activity,
      color: 'text-orange-500',
      bg: 'bg-orange-500/10',
      label: 'High Volatility'
    }
  };

  const config = regimeConfig[regime];
  const Icon = config.icon;

  return (
    <Card className={config.bg}>
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-full ${config.bg}`}>
            <Icon className={`h-6 w-6 ${config.color}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold">Current Regime:</span>
              <span className={`text-lg font-bold ${config.color}`}>
                {config.label}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              Confidence: {(confidence * 100).toFixed(1)}%
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Trend</div>
              <div className="font-medium">{(scores.trend_score * 100).toFixed(0)}%</div>
            </div>
            <div>
              <div className="text-muted-foreground">Consolidation</div>
              <div className="font-medium">{(scores.consolidation_score * 100).toFixed(0)}%</div>
            </div>
            <div>
              <div className="text-muted-foreground">Volatility</div>
              <div className="font-medium">{(scores.high_volatility_score * 100).toFixed(0)}%</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

#### Step 2.3: Indicator Display Components (2h)

**Location:** `frontend/src/components/trading/IndicatorValue.tsx`

```typescript
// frontend/src/components/trading/IndicatorValue.tsx
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

interface IndicatorValueProps {
  label: string;
  value: number;
  threshold?: {
    type: '>' | '<' | 'range';
    value: number | [number, number];
  };
  formatValue?: (val: number) => string;
  unit?: string;
}

export const IndicatorValue: React.FC<IndicatorValueProps> = ({
  label,
  value,
  threshold,
  formatValue = (v) => v.toFixed(2),
  unit = ''
}) => {
  const checkThreshold = (): boolean | null => {
    if (!threshold) return null;

    if (threshold.type === '>') {
      return value > (threshold.value as number);
    } else if (threshold.type === '<') {
      return value < (threshold.value as number);
    } else if (threshold.type === 'range') {
      const [min, max] = threshold.value as [number, number];
      return value >= min && value <= max;
    }
    return null;
  };

  const passed = checkThreshold();
  const StatusIcon = passed === true ? CheckCircle2 : passed === false ? XCircle : AlertCircle;
  const statusColor = passed === true ? 'text-green-500' : passed === false ? 'text-red-500' : 'text-gray-500';

  return (
    <div className="flex items-center justify-between py-2 border-b last:border-b-0">
      <span className="text-sm font-medium">{label}:</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-mono">{formatValue(value)}{unit}</span>
        {passed !== null && (
          <StatusIcon className={`h-4 w-4 ${statusColor}`} />
        )}
      </div>
    </div>
  );
};
```

**Location:** `frontend/src/components/trading/RegimeIndicators.tsx`

```typescript
// frontend/src/components/trading/RegimeIndicators.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { IndicatorValue } from './IndicatorValue';

interface RegimeIndicatorsProps {
  regime: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY';
  indicators: Record<string, number>;
  price?: number;
}

export const RegimeIndicators: React.FC<RegimeIndicatorsProps> = ({
  regime,
  indicators,
  price
}) => {
  if (regime === 'TREND') {
    const ema10 = indicators['1h_EMA_10'];
    const ema20 = indicators['1h_EMA_20'];
    const priceAboveEMA10 = price && ema10 ? price > ema10 : null;
    const ema10AboveEMA20 = ema10 && ema20 ? ema10 > ema20 : null;

    return (
      <Card>
        <CardHeader>
          <CardTitle>TREND Indicators (Live)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          <IndicatorValue
            label="ADX (14)"
            value={indicators['1h_ADX_14'] || 0}
            threshold={{ type: '>', value: 25 }}
          />
          <IndicatorValue
            label="+DI (14)"
            value={indicators['1h_PLUS_DI_14'] || 0}
          />
          <IndicatorValue
            label="-DI (14)"
            value={indicators['1h_MINUS_DI_14'] || 0}
          />
          <IndicatorValue
            label="EMA 10"
            value={ema10 || 0}
            formatValue={(v) => v.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          />
          <IndicatorValue
            label="EMA 20"
            value={ema20 || 0}
            formatValue={(v) => v.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          />
          <div className="py-2 border-b">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Price {'>'} EMA10:</span>
              <span className={`text-sm ${priceAboveEMA10 ? 'text-green-500' : 'text-red-500'}`}>
                {priceAboveEMA10 ? '✅ Yes' : '❌ No'}
              </span>
            </div>
          </div>
          <div className="py-2 border-b">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">EMA10 {'>'} EMA20:</span>
              <span className={`text-sm ${ema10AboveEMA20 ? 'text-green-500' : 'text-red-500'}`}>
                {ema10AboveEMA20 ? '✅ Yes' : '❌ No'}
              </span>
            </div>
          </div>
          <IndicatorValue
            label="Volume Ratio"
            value={indicators['1h_VOLUME_RATIO_20'] || 0}
            threshold={{ type: '>', value: 1.2 }}
          />
          <IndicatorValue
            label="ATR (14)"
            value={indicators['1h_ATR_14'] || 0}
            formatValue={(v) => v.toFixed(2)}
          />
        </CardContent>
      </Card>
    );
  }

  // Similar for CONSOLIDATION and HIGH_VOLATILITY
  // ...

  return null;
};
```

#### Step 2.4: StrategyOverview Integration (1.5h)

**Location:** `frontend/src/pages/StrategyOverview.tsx`

**Änderungen:**
1. Import neuer Komponenten
2. State für Symbol, Timeframe
3. useLiveIndicators Hook
4. Controls oben einfügen
5. RegimeStatus einfügen
6. RegimeIndicators in Tabs einfügen

**Pseudocode:**
```typescript
// Imports
import { StrategyControls } from '@/components/trading/StrategyControls';
import { RegimeStatus } from '@/components/trading/RegimeStatus';
import { RegimeIndicators } from '@/components/trading/RegimeIndicators';
import { useLiveIndicators } from '@/hooks/useLiveIndicators';

// State
const [symbol, setSymbol] = useState('BTCUSDT');
const [timeframe, setTimeframe] = useState('1h');

// Hook
const { data: liveData, loading, error, refetch } = useLiveIndicators(symbol, timeframe);

// Render
return (
  <div className="container mx-auto p-6 space-y-6">
    {/* Header */}
    {/* ... */}

    {/* Controls */}
    <StrategyControls
      symbol={symbol}
      onSymbolChange={setSymbol}
      timeframe={timeframe}
      onTimeframeChange={setTimeframe}
      onRefresh={refetch}
      isRefreshing={loading}
      lastUpdate={liveData?.timestamp}
    />

    {/* Regime Status */}
    {liveData?.regime && (
      <RegimeStatus
        regime={liveData.regime.current}
        confidence={liveData.regime.confidence}
        scores={liveData.regime.details}
      />
    )}

    {/* Tabs */}
    <Tabs defaultValue="overview">
      {/* ... */}
      <TabsContent value="trend">
        <RegimeIndicators
          regime="TREND"
          indicators={liveData?.indicators || {}}
          price={currentPrice}
        />
      </TabsContent>
      {/* ... */}
    </Tabs>
  </div>
);
```

### Phase 3: Testing & Refinement (2-3 Stunden)

#### Step 3.1: Component Testing (1h)

**Tasks:**
- [ ] Test StrategyControls (Pair/Timeframe Selection)
- [ ] Test RegimeStatus (Visual Display)
- [ ] Test IndicatorValue (Threshold Checks)
- [ ] Test RegimeIndicators (Data Mapping)

#### Step 3.2: Integration Testing (1h)

**Tasks:**
- [ ] Test Full Flow (Pair Selection → API Call → Display)
- [ ] Test Error States (API Failure)
- [ ] Test Loading States
- [ ] Test Auto-Refresh

#### Step 3.3: UI/UX Polish (1h)

**Tasks:**
- [ ] Responsive Design Check
- [ ] Loading Skeletons
- [ ] Error Messages
- [ ] Empty States
- [ ] Animations/Transitions

---

## 6. Testing-Strategie

### 6.1 Unit Tests

```typescript
// frontend/src/services/__tests__/indicatorService.test.ts
describe('indicatorService', () => {
  it('should fetch live indicators successfully', async () => {
    // Mock fetch
    // Test fetchLiveIndicators
  });

  it('should handle API errors gracefully', async () => {
    // Mock failed fetch
    // Test error handling
  });
});
```

### 6.2 Component Tests

```typescript
// frontend/src/components/trading/__tests__/StrategyControls.test.tsx
describe('StrategyControls', () => {
  it('should render pair selector', () => {
    // Test rendering
  });

  it('should call onSymbolChange when pair is selected', () => {
    // Test callback
  });
});
```

### 6.3 E2E Tests (Optional)

**Playwright/Cypress:**
```typescript
test('Strategy Overview with Live Data', async ({ page }) => {
  await page.goto('http://localhost:3000/trading/strategy/...');

  // Select ETHUSDT
  await page.click('[data-testid="pair-selector"]');
  await page.click('text=ETHUSDT');

  // Wait for data
  await page.waitForSelector('[data-testid="regime-status"]');

  // Verify indicators displayed
  expect(await page.textContent('[data-testid="adx-value"]')).toBeTruthy();
});
```

---

## 7. Deployment-Plan

### 7.1 Development

```bash
# 1. Create feature branch
git checkout -b feature/live-indicators-integration

# 2. Implement changes
# ... (siehe Implementierungsschritte)

# 3. Run tests
npm test

# 4. Run dev server
npm run dev

# 5. Manual testing
# http://localhost:3000/trading/strategy/9675ccea-f520-4557-b54c-a98e1972cc1f
```

### 7.2 Staging

```bash
# 1. Build production bundle
npm run build

# 2. Deploy to staging
# docker compose -f docker-compose.staging.yml up -d

# 3. Smoke tests
# curl http://staging:3000/trading/strategy/...
```

### 7.3 Production

```bash
# 1. Create PR
# 2. Code Review
# 3. Merge to master
# 4. Deploy
docker compose -f docker-compose.prod.yml up -d frontend
```

---

## 8. Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| API-Endpoint existiert nicht | Hoch | Hoch | Fallback: Debug API nutzen oder neuen Endpoint erstellen |
| Performance-Issues | Mittel | Mittel | Caching, Debouncing, Lazy Loading |
| Dateninkonsistenzen | Niedrig | Hoch | Validation Layer, Error Boundaries |
| Mobile Responsive | Niedrig | Mittel | Responsive Design Testing |

---

## 9. Timeline

### Woche 1 (Tag 1-2)

| Tag | Phase | Aufwand | Tasks |
|-----|-------|---------|-------|
| Tag 1 (AM) | Phase 1: API | 4h | API-Analyse, Service, Hook, Tests |
| Tag 1 (PM) | Phase 2: UI Start | 2h | Controls Component |
| Tag 2 (AM) | Phase 2: UI | 4h | RegimeStatus, IndicatorValue, RegimeIndicators |
| Tag 2 (PM) | Phase 2: Integration | 2h | StrategyOverview Integration |

### Woche 1 (Tag 3)

| Tag | Phase | Aufwand | Tasks |
|-----|-------|---------|-------|
| Tag 3 (AM) | Phase 3: Testing | 2h | Component Tests, Integration Tests |
| Tag 3 (PM) | Phase 3: Polish | 1h | UI/UX Refinement, Documentation |

**Total: ~15 Stunden = 2 Tage**

---

## 10. Success Criteria

- [ ] User kann Pair aus Dropdown auswählen
- [ ] User kann Timeframe auswählen
- [ ] Live-Indikatoren werden korrekt angezeigt
- [ ] Aktuelles Regime wird hervorgehoben
- [ ] Threshold-Checks funktionieren (✅/❌)
- [ ] Refresh funktioniert (Manual + Optional Auto)
- [ ] Loading States korrekt
- [ ] Error Handling vorhanden
- [ ] Responsive auf Mobile
- [ ] Unit Tests > 80% Coverage
- [ ] Keine Console Errors

---

## 11. Nächste Schritte

### Sofort

1. [ ] Umsetzungsplan reviewen
2. [ ] `/trading/indicators` Code analysieren
3. [ ] API-Struktur verifizieren

### Heute

1. [ ] Phase 1 starten (API-Integration)
2. [ ] Mock-Daten vorbereiten (falls API nicht verfügbar)

### Diese Woche

1. [ ] Phase 2 implementieren (UI-Komponenten)
2. [ ] Phase 3 Testing
3. [ ] Deployment

---

## Anhang A: File-Struktur

```
frontend/src/
├── components/
│   └── trading/
│       ├── StrategyControls.tsx       # 🆕 Neu
│       ├── RegimeStatus.tsx           # 🆕 Neu
│       ├── IndicatorValue.tsx         # 🆕 Neu
│       └── RegimeIndicators.tsx       # 🆕 Neu
├── hooks/
│   └── useLiveIndicators.ts           # 🆕 Neu
├── services/
│   └── indicatorService.ts            # 🆕 Neu
├── pages/
│   └── StrategyOverview.tsx           # ⚠️ Erweitern
└── __tests__/
    ├── components/
    │   └── trading/
    │       ├── StrategyControls.test.tsx
    │       ├── RegimeStatus.test.tsx
    │       └── IndicatorValue.test.tsx
    ├── hooks/
    │   └── useLiveIndicators.test.ts
    └── services/
        └── indicatorService.test.ts
```

---

## 12. Discovery-Zusammenfassung (2025-12-07)

### Wichtigste Erkenntnisse

**✅ Positive Überraschungen:**
1. **API existiert bereits** - `/api/prediction/v1/indicators/{symbol}/current`
2. **React Query Hooks vorhanden** - `useIndicators()` mit Auto-Refresh (60s)
3. **14 Indikatoren verfügbar** - Alle für Regime Detection benötigten Daten sind da
4. **predictionService implementiert** - Singleton Client mit Symbol-Konvertierung
5. **TradingIndicatorsPage als Referenz** - Vollständiges Beispiel für Indicator Display

**⚠️ Kritische Findings:**
1. **Type-Definitionen unvollständig** - Nur 4/14 Indikatoren typisiert (MUSS korrigiert werden!)
2. **Kein Timeframe-Parameter** - API liefert nur einen festen Timeframe (vermutlich 1h)
3. **Kein Regime Endpoint** - Regime Detection ist Teil der Strategy Engine, nicht als separater Endpoint
4. **EMA 10/20 fehlen** - Nur EMA200 verfügbar, EMA 10/20 für TREND-Detection nicht vorhanden
5. **+DI/-DI unklar** - Möglicherweise in ADX-Objekt enthalten, muss geprüft werden

### Anpassungen am Plan

**Phase 1: Von 4-5h auf 2h reduziert**
- Step 1.1: ✅ Abgeschlossen (Discovery)
- Step 1.2: Type-Definitionen vervollständigen (NEU, 1h)
- Step 1.3: Bestehenden Hook nutzen statt neuen erstellen (0.5h)
- Step 1.4: Type-Testing statt Service-Testing (0.5h)

**Phase 2: Unverändert (5-6h)**
- UI-Komponenten wie geplant

**Phase 3: Unverändert (2-3h)**
- Testing & Refinement

**Neue Gesamtzeit: ~10-12h statt 15h**

### Scope-Entscheidung: Phase 1 vs. Full Implementation

**Option A: Phase 1 - Quick Win (10-12h)**
- ✅ Nutzt bestehende API (kein Timeframe-Support)
- ✅ Zeigt 14 Live-Indikatoren
- ✅ Pair Selector (funktional)
- ❌ Timeframe Selector (nur Display, kein Backend-Support)
- ❌ Keine EMA 10/20 (nur EMA200)
- ❌ Möglicherweise keine +DI/-DI

**Empfehlung:** Phase 1 starten, Backend-Erweiterung für Phase 2 planen

**Option B: Full Implementation mit Backend (25-30h)**
- Backend: Timeframe-Parameter hinzufügen (5-8h)
- Backend: EMA 10/20 berechnen (2-3h)
- Backend: +DI/-DI in Response aufnehmen (1-2h)
- Backend: Regime Detection Endpoint (optional, 5-8h)
- Frontend: Wie Phase 1 (10-12h)

**Empfehlung:** Nur bei expliziter Anforderung für Multi-Timeframe Support

### Nächste Actions (Priorisiert)

**Sofort (heute):**
1. [ ] Type-Definitionen in `indicators.ts` vervollständigen (1h)
2. [ ] TypeScript Compilation prüfen (5min)
3. [ ] Entscheidung: Phase 1 oder warten auf Backend-Erweiterung?

**Morgen (Tag 1):**
1. [ ] UI-Komponenten implementieren (Step 2.1-2.4)
2. [ ] Integration in StrategyOverview

**Übermorgen (Tag 2):**
1. [ ] Testing & Polish
2. [ ] Dokumentation
3. [ ] Deployment

---

**Erstellt:** 2025-12-07
**Aktualisiert:** 2025-12-07 (nach Discovery - Plan um 30% verkürzt)
**Nächstes Review:** Nach Phase 1 Implementierung oder Backend-Erweiterungs-Entscheidung

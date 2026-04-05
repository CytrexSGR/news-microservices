# Regime Detection: Gap-Analyse & Implementierungsplan

**Erstellt:** 2025-12-07
**Status:** Analyse abgeschlossen
**Zweck:** Detaillierte Analyse zwischen aktueller Implementierung und Best Practices

---

## Executive Summary

**Aktueller Stand:**
- 3 Indikatoren für Regime Detection implementiert (ADX, ATR, BBW auf 1h)
- Basis-Funktionalität vorhanden, aber **nicht vollständig** gemäß Best Practices

**Hauptlücken:**
- ❌ **Volumen-Indikatoren** fehlen komplett
- ❌ **EMA/MA-Kreuzungen** für Trendbestätigung fehlen
- ❌ **RSI** wird nicht für Consolidation-Erkennung genutzt
- ❌ **+DI/-DI** (Directional Indicators) fehlen

**Empfehlung:**
- Phase 1: Volumen + EMA hinzufügen (niedrige Komplexität, hoher Impact)
- Phase 2: RSI-Integration für Consolidation (bereits vorhanden für Entries)
- Phase 3: Multi-Timeframe Validierung

---

## 1. Aktueller Stand: Was haben wir?

### 1.1 Implementierte Regime Detection

**Quelle:** Strategy JSON in Database `prediction_service.strategies`
**Strategy ID:** `9675ccea-f520-4557-b54c-a98e1972cc1f`

```json
"regime_detection": {
  "enabled": true,
  "indicators": ["1h_ADX_14", "1h_ATR_14", "1h_BBW_20"],
  "timeframe": "1h"
}
```

### 1.2 Verfügbare Indikatoren (14 total)

**Aktuell in Strategy definiert:**

| Indikator | Timeframe | Parameter | Wird genutzt für |
|-----------|-----------|-----------|------------------|
| **1h_ADX_14** | 1h | 14 | ✅ Regime Detection (Trendstärke) |
| **1h_ATR_14** | 1h | 14 | ✅ Regime Detection (Volatilität) |
| **1h_BBW_20** | 1h | 20 | ✅ Regime Detection (Squeeze) |
| 1h_RSI_14 | 1h | 14 | ❌ Nur Entry Conditions |
| 1h_EMA_10 | 1h | 10 | ❌ Nur Entry Conditions |
| 1h_EMA_20 | 1h | 20 | ❌ Nur Entry Conditions |
| 4h_RSI_14 | 4h | 14 | ❌ Nur Entry Conditions |
| 4h_EMA_10 | 4h | 10 | ❌ Nur Entry Conditions |
| 4h_EMA_20 | 4h | 20 | ❌ Nur Entry Conditions |
| 4h_MACD_12_26_9 | 4h | 12,26,9 | ❌ Nur Entry Conditions |
| 1d_RSI_14 | 1d | 14 | ❌ Nur Entry Conditions |
| 1d_EMA_50 | 1d | 50 | ❌ Nur Entry Conditions |
| 1d_EMA_200 | 1d | 200 | ❌ Nur Entry Conditions |
| 1d_MACD_12_26_9 | 1d | 12,26,9 | ❌ Nur Entry Conditions |

**Wichtig:** EMA und RSI sind bereits vorhanden, werden aber NICHT für Regime Detection genutzt!

### 1.3 Datenquellen

**Marktdaten-Quelle:** FMP Service (Financial Modeling Prep API)

**Verfügbare Daten pro Candle:**
```python
{
  "open": float,
  "high": float,
  "low": float,
  "close": float,
  "volume": int,        # ✅ Vorhanden!
  "timestamp": datetime
}
```

**Wichtig:** Volumen ist in den Rohdaten vorhanden, wird aber nicht als Indikator berechnet!

### 1.4 Berechnungs-Engine

**Location:** `/services/prediction-service/app/core/strategy_engine.py`

**Aktuell implementierte Berechnungen:**
- ✅ ADX (Average Directional Index)
- ✅ ATR (Average True Range)
- ✅ BBW (Bollinger Band Width)
- ✅ RSI (Relative Strength Index)
- ✅ EMA (Exponential Moving Average)
- ✅ MACD (Moving Average Convergence Divergence)

**Fehlende Berechnungen:**
- ❌ +DI / -DI (Directional Indicators)
- ❌ Volumen-Indikatoren (Volume Ratio, Volume MA)
- ❌ MA-Konvergenz-Detection
- ❌ Historical Volatility

---

## 2. Anforderungen: Was brauchen wir?

### 2.1 TREND-Regime (Sollzustand)

| Indikator | Status | Datenquelle | Berechnungskomplexität |
|-----------|--------|-------------|------------------------|
| ADX > 25/30 | ✅ Vorhanden | OHLC | - |
| **+DI / -DI** | ❌ **FEHLT** | OHLC | Niedrig (Teil von ADX-Berechnung) |
| **EMA 10/20** | ⚠️ Vorhanden aber ungenutzt | OHLC | - |
| **EMA-Kreuzungen** | ❌ **FEHLT** | EMA-Werte | Trivial (Vergleich) |
| **Volumen** | ❌ **FEHLT** | OHLCV | Niedrig (Simple Average) |

### 2.2 CONSOLIDATION-Regime (Sollzustand)

| Indikator | Status | Datenquelle | Berechnungskomplexität |
|-----------|--------|-------------|------------------------|
| ADX < 20/25 | ✅ Vorhanden | OHLC | - |
| BBW niedrig | ✅ Vorhanden | OHLC | - |
| **RSI um 50** | ⚠️ Vorhanden aber ungenutzt | OHLC | - |
| **MA-Konvergenz** | ❌ **FEHLT** | EMA-Werte | Niedrig (Abstand berechnen) |
| **Volumen niedrig** | ❌ **FEHLT** | OHLCV | Niedrig (Vergleich mit Average) |

### 2.3 HIGH_VOLATILITY-Regime (Sollzustand)

| Indikator | Status | Datenquelle | Berechnungskomplexität |
|-----------|--------|-------------|------------------------|
| ATR > Durchschnitt | ✅ Vorhanden | OHLC | - |
| BBW hoch | ✅ Vorhanden | OHLC | - |
| ADX (Richtung) | ✅ Vorhanden | OHLC | - |
| **Historical Volatility** | ❌ **FEHLT** | Close Prices | Mittel (Std. Dev. Log Returns) |

---

## 3. Gap-Analyse: Was fehlt und wie bekommen wir es?

### 3.1 Fehlende Indikatoren (Priorität: HOCH)

#### A) Volumen-Indikatoren

**Was fehlt:**
- Volume Ratio (aktuelles Volumen / Durchschnittsvolumen)
- Volume Moving Average (SMA/EMA über Volumen)

**Woher bekommen:**
- ✅ **Daten bereits vorhanden** in OHLCV-Daten von FMP Service
- Keine zusätzliche API-Anbindung nötig

**Wie berechnen:**
```python
# Pseudocode
def calculate_volume_ratio(volumes: List[float], period: int = 20) -> float:
    current_volume = volumes[-1]
    avg_volume = sum(volumes[-period:]) / period
    return current_volume / avg_volume

def volume_ma(volumes: List[float], period: int = 20) -> float:
    return sum(volumes[-period:]) / period
```

**Implementierung:**
- Location: `/services/prediction-service/app/indicators/volume.py` (neu)
- Aufwand: **1-2 Stunden**
- Dependencies: Keine neuen Libraries nötig

#### B) +DI / -DI (Directional Indicators)

**Was fehlt:**
- Positive Directional Indicator (+DI)
- Negative Directional Indicator (-DI)

**Woher bekommen:**
- ✅ **Teil der ADX-Berechnung** (bereits implementiert, nur nicht exposed)
- Bereits in TA-Lib verfügbar (wenn verwendet)

**Wie berechnen:**
```python
# Falls TA-Lib verwendet wird:
import talib
plus_di = talib.PLUS_DI(high, low, close, timeperiod=14)
minus_di = talib.MINUS_DI(high, low, close, timeperiod=14)

# Falls eigene Implementierung:
# +DI und -DI sind Zwischenschritte der ADX-Berechnung
# Müssen nur zurückgegeben werden
```

**Implementierung:**
- Location: Erweitern der bestehenden ADX-Berechnung
- Aufwand: **30-60 Minuten**
- Dependencies: Keine (bereits Teil von ADX)

#### C) EMA-Kreuzungen Detection

**Was fehlt:**
- Golden Cross Detection (EMA10 kreuzt EMA20 von unten)
- Death Cross Detection (EMA10 kreuzt EMA20 von oben)
- Price-EMA-Relationship (Preis > EMA10 > EMA20)

**Woher bekommen:**
- ✅ **EMAs bereits berechnet** (1h_EMA_10, 1h_EMA_20 vorhanden)
- Nur Vergleichslogik fehlt

**Wie berechnen:**
```python
# Pseudocode
def detect_ema_cross(ema_short: List[float], ema_long: List[float]) -> str:
    if ema_short[-1] > ema_long[-1] and ema_short[-2] <= ema_long[-2]:
        return "golden_cross"  # Bullish
    elif ema_short[-1] < ema_long[-1] and ema_short[-2] >= ema_long[-2]:
        return "death_cross"   # Bearish
    return "no_cross"

def price_ema_hierarchy(price: float, ema10: float, ema20: float) -> bool:
    return price > ema10 > ema20  # Bullish hierarchy
```

**Implementierung:**
- Location: `/services/prediction-service/app/indicators/ma_cross.py` (neu)
- Aufwand: **1 Stunde**
- Dependencies: Keine (nur Vergleiche)

### 3.2 Ungenutzte vorhandene Indikatoren (Priorität: MITTEL)

#### D) RSI für Consolidation

**Was fehlt:**
- RSI-Wert wird nicht für Regime Detection geprüft

**Woher bekommen:**
- ✅ **Bereits berechnet** (1h_RSI_14 vorhanden)
- Nur Integration in Regime Detection fehlt

**Wie nutzen:**
```python
# Pseudocode
def check_consolidation_rsi(rsi: float) -> bool:
    return 40 < rsi < 60  # Neutral Zone
```

**Implementierung:**
- Location: Erweitern der Regime Detection Logic
- Aufwand: **30 Minuten**
- Dependencies: Keine

#### E) MA-Konvergenz Detection

**Was fehlt:**
- Messung des Abstands zwischen EMAs
- Konvergenz-Kriterium

**Woher bekommen:**
- ✅ **EMAs bereits berechnet**
- Abstand-Berechnung fehlt

**Wie berechnen:**
```python
# Pseudocode
def ema_convergence(ema10: float, ema20: float, threshold: float = 0.005) -> bool:
    distance = abs(ema10 - ema20) / ema20  # Prozentuale Distanz
    return distance < threshold  # Konvergierend wenn < 0.5%
```

**Implementierung:**
- Location: `/services/prediction-service/app/indicators/ma_cross.py`
- Aufwand: **30 Minuten**
- Dependencies: Keine

### 3.3 Optionale Erweiterungen (Priorität: NIEDRIG)

#### F) Historical Volatility

**Was fehlt:**
- Standardabweichung der Log-Returns
- Rolling Window Berechnung

**Woher bekommen:**
- ✅ **Close Prices vorhanden**
- Berechnung nötig

**Wie berechnen:**
```python
import numpy as np

def historical_volatility(closes: List[float], period: int = 20) -> float:
    log_returns = np.log(np.array(closes[1:]) / np.array(closes[:-1]))
    return np.std(log_returns[-period:])
```

**Implementierung:**
- Location: `/services/prediction-service/app/indicators/volatility.py` (neu)
- Aufwand: **1-2 Stunden**
- Dependencies: numpy (bereits vorhanden)

---

## 4. Datenquellen-Mapping

### 4.1 Externe APIs

| Datenquelle | Zweck | Status | Kosten |
|-------------|-------|--------|--------|
| **FMP Service** | OHLCV Market Data | ✅ Aktiv | Vorhanden |
| Additional Sources | - | ❌ Nicht nötig | - |

**Wichtig:** Alle benötigten Rohdaten sind bereits vorhanden! Keine neuen API-Integrationen erforderlich.

### 4.2 Interne Datenflüsse

```
FMP Service (Port 8109)
    ↓
[OHLCV Data]
    ↓
Prediction Service (Port 8116)
    ↓
Strategy Engine
    ↓
Indicator Calculator
    ↓
Regime Detection
```

**Aktueller Flow:**
1. FMP Service holt Marktdaten von FMP API
2. Prediction Service ruft FMP Service ab
3. Strategy Engine berechnet 14 Indikatoren
4. Regime Detection nutzt nur 3 davon

**Benötigter Flow:**
- ✅ Keine Änderungen am Datenfluss nötig
- ✅ Nur Indicator Calculator erweitern
- ✅ Regime Detection Logic anpassen

---

## 5. Implementierungsplan

### Phase 1: Quick Wins (1-2 Tage)

**Ziel:** Minimale Änderungen, maximaler Impact

| Task | Aufwand | Files | Dependencies |
|------|---------|-------|--------------|
| **1. Volumen-Indikator** | 2h | `indicators/volume.py` (neu) | Keine |
| **2. +DI/-DI Integration** | 1h | `indicators/adx.py` | Keine |
| **3. EMA-Kreuzungen** | 1h | `indicators/ma_cross.py` (neu) | Keine |
| **4. RSI für Consolidation** | 0.5h | `core/regime_detection.py` | Keine |
| **5. Strategy JSON Update** | 0.5h | Database Migration | Keine |
| **Testing** | 2h | `tests/test_indicators.py` | pytest |
| **Dokumentation** | 1h | API Docs, README | - |

**Total:** ~8 Stunden (1 Tag)

### Phase 2: Verfeinerung (2-3 Tage)

| Task | Aufwand | Files | Dependencies |
|------|---------|-------|--------------|
| **1. MA-Konvergenz** | 1h | `indicators/ma_cross.py` | Keine |
| **2. Historical Volatility** | 2h | `indicators/volatility.py` (neu) | numpy |
| **3. Multi-TF Validierung** | 4h | `core/regime_detection.py` | Keine |
| **4. Regime Confidence Score** | 3h | `core/regime_detection.py` | Keine |
| **5. Testing** | 3h | `tests/` | pytest |
| **Dokumentation** | 2h | Docs | - |

**Total:** ~15 Stunden (2 Tage)

### Phase 3: Backtesting & Validation (3-5 Tage)

| Task | Aufwand | Files | Dependencies |
|------|---------|-------|--------------|
| **1. Backtest Framework** | 8h | `backtesting/` | Backtrader/Vectorbt |
| **2. Historical Data Import** | 4h | Scripts | FMP API |
| **3. Regime Detection Test** | 6h | Tests | - |
| **4. Performance Comparison** | 4h | Analysis | Pandas |
| **5. Frontend Integration** | 4h | `frontend/src/` | React |
| **Dokumentation** | 2h | Reports | - |

**Total:** ~28 Stunden (3-4 Tage)

---

## 6. Risiken & Mitigationen

### 6.1 Technische Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **Performance-Degradation** | Mittel | Hoch | Caching, Batch Processing |
| **Falsche Berechnungen** | Niedrig | Sehr Hoch | Unit Tests, Cross-Validation |
| **Breaking Changes** | Niedrig | Hoch | Backward Compatibility, Feature Flags |

### 6.2 Daten-Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **FMP API Rate Limits** | Niedrig | Mittel | Bereits implementiertes Caching |
| **Fehlende Daten** | Niedrig | Mittel | Fallback auf vorherige Werte |
| **Datenqualität** | Mittel | Mittel | Validation Checks |

---

## 7. Nächste Schritte

### Sofort (heute)

1. ✅ **Gap-Analyse dokumentiert**
2. [ ] Review mit Team
3. [ ] Prioritäten bestätigen

### Diese Woche

1. [ ] Phase 1 implementieren (Volumen, +DI/-DI, EMA-Kreuzungen)
2. [ ] Unit Tests schreiben
3. [ ] Strategy JSON aktualisieren

### Nächste Woche

1. [ ] Phase 2 implementieren (MA-Konvergenz, HV)
2. [ ] Integration Tests
3. [ ] Frontend-Anpassungen

### Nächster Sprint

1. [ ] Backtesting Framework aufsetzen
2. [ ] Performance-Vergleich
3. [ ] Production Deployment

---

## 8. Offene Fragen

- [ ] Welche ADX-Schwellenwerte bevorzugt? (20 vs. 25 für Consolidation)
- [ ] Soll Historical Volatility implementiert werden oder reicht ATR + BBW?
- [ ] Multi-Timeframe: 1h + 4h oder nur 1h?
- [ ] Regime Confidence Score: Gewichtung der Indikatoren?

---

## Anhang A: Code-Locations

```
services/prediction-service/
├── app/
│   ├── core/
│   │   ├── strategy_engine.py      # ⚠️ Erweitern: Neue Indikatoren registrieren
│   │   └── regime_detection.py     # ⚠️ Erweitern: Logic anpassen
│   ├── indicators/
│   │   ├── adx.py                  # ⚠️ Erweitern: +DI/-DI exposieren
│   │   ├── atr.py                  # ✅ Keine Änderung
│   │   ├── bbw.py                  # ✅ Keine Änderung
│   │   ├── rsi.py                  # ✅ Keine Änderung
│   │   ├── ema.py                  # ✅ Keine Änderung
│   │   ├── volume.py               # 🆕 Neu erstellen
│   │   ├── ma_cross.py             # 🆕 Neu erstellen
│   │   └── volatility.py           # 🆕 Neu erstellen (Phase 2)
│   └── models/
│       └── strategy.py             # ⚠️ Erweitern: Schema anpassen
└── tests/
    └── indicators/
        ├── test_volume.py          # 🆕 Neu erstellen
        ├── test_ma_cross.py        # 🆕 Neu erstellen
        └── test_regime_detection.py # ⚠️ Erweitern
```

---

## Anhang B: Beispiel Strategy JSON (Sollzustand)

```json
{
  "regime_detection": {
    "enabled": true,
    "indicators": [
      "1h_ADX_14",
      "1h_PLUS_DI_14",
      "1h_MINUS_DI_14",
      "1h_ATR_14",
      "1h_BBW_20",
      "1h_RSI_14",
      "1h_EMA_10",
      "1h_EMA_20",
      "1h_VOLUME_RATIO_20"
    ],
    "timeframe": "1h",
    "multi_tf_validation": {
      "enabled": true,
      "higher_tf": "4h"
    },
    "thresholds": {
      "trend": {
        "adx_min": 25,
        "adx_strong": 30,
        "volume_ratio_min": 1.2,
        "ema_hierarchy_required": true
      },
      "consolidation": {
        "adx_max": 20,
        "rsi_min": 40,
        "rsi_max": 60,
        "ema_convergence_threshold": 0.005
      },
      "high_volatility": {
        "atr_percentile": 80,
        "bbw_threshold_high": 0.05
      }
    }
  }
}
```

---

**Letzte Aktualisierung:** 2025-12-07
**Nächstes Review:** Nach Phase 1 Implementierung

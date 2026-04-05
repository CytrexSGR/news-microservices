# Strategy Refactoring: Regime Detection

**Status:** In Arbeit
**Erstellt:** 2025-12-07
**Letzte Aktualisierung:** 2025-12-07

---

## 1. Übersicht

Refactoring der Regime Detection für adaptive Trading-Strategien basierend auf Best Practices aus Trading Notebook.

**Ziel:** Robustere Marktphasen-Erkennung durch Kombination mehrerer Indikatoren zur Reduzierung von Fehlsignalen.

---

## 2. Aktueller Stand (Implementierung)

### Verwendete Indikatoren für Regime Detection

| Indikator | Timeframe | Parameter | Zweck |
|-----------|-----------|-----------|-------|
| ADX | 1h | 14 | Trendstärke |
| ATR | 1h | 14 | Volatilität (absolut) |
| BBW | 1h | 20 | Volatilität/Squeeze |

### Erkannte Regimes

1. **TREND** - Klare Auf-/Abwärtsbewegung
2. **CONSOLIDATION** - Seitwärtsmarkt (Range)
3. **HIGH_VOLATILITY** - Stark schwankend

**Limitierung:** Nur 3 Indikatoren, alle auf 1h-Timeframe

---

## 3. Zielzustand (Best Practice aus Notebook)

### 3.1 TREND (Klare Auf-/Abwärtsbewegung)

**Anforderung:** Messung von **Stärke** und **Richtung** der Preisbewegung

| Indikator | Messgröße | Erkennungskriterium | Status |
|-----------|-----------|---------------------|--------|
| **ADX** | Trendstärke | ADX > 25 (stark: > 30) | ✅ Vorhanden |
| **MA/EMA** | Trendrichtung und -dynamik | EMA für schnelle Märkte | ❌ Fehlt |
| **MA-Kreuzungen** | Bestätigung/Richtung | Golden Cross (kurzfristig × langfristig) | ❌ Fehlt |
| **Volumen** | Trendstärke-Bestätigung | Volumen in Trendrichtung > Gegenrichtung | ❌ Fehlt |

**Beispiel starker Bullenmarkt (5min-Chart):**
- ADX > 30
- Kurs > 10-EMA > 20-EMA
- Volumen bei Aufwärtsbewegungen merklich höher

#### Detaillierte Standardwerte TREND

| Parameter | Standardwert | Schwellenwert | Anwendung |
|-----------|--------------|---------------|-----------|
| **ADX-Periode** | 14 Perioden | - | Gängige Einstellung für alle Timeframes |
| **ADX-Wert** | - | > 25 (Trend bestätigt)<br>> 30 (Starker Trend) | Über 25 = Trend vorhanden<br>Über 30 = Besonders stark |
| **+DI / -DI** | - | +DI > -DI (Aufwärts)<br>-DI > +DI (Abwärts) | Richtungsbestimmung |
| **EMA Kurzfristig** | 10 Perioden | Kurs > EMA10 | Kurzfristiges Momentum |
| **EMA Mittelfristig** | 20 Perioden | EMA10 > EMA20 | Hierarchie bestätigt Trend |
| **EMA Langfristig** | 50, 100, 200 Perioden | Kurs > EMA200 | Übergeordneter Kontext |
| **Volumen** | - | In Trendrichtung **merklich höher** | Steigendes Volumen bei steigenden Kursen = Kaufdruck |
| **ATR-Periode** | 14 Perioden | - | Für Volatilitätsmessung |
| **ATR-Schwelle** | - | Aktueller ATR > Ø ATR (20 Perioden) | Bestätigt erhöhte Volatilität |
| **ATR-Multiplikator** | 1.5x - 3.0x | - | Für volatilitätsadaptierte Stop-Loss |

### 3.2 CONSOLIDATION (Seitwärtsmarkt / Range)

**Anforderung:** Erkennung von **fehlendem Trend** und **geringer Volatilität**

| Indikator | Messgröße | Erkennungskriterium | Status |
|-----------|-----------|---------------------|--------|
| **ADX** | Abwesenheit von Trendstärke | ADX < 20 oder < 25 | ✅ Vorhanden |
| **BBW** | Volatilität/Range-Breite | Niedrige BBW (Squeeze) | ✅ Vorhanden |
| **MA** | Konvergenz | Konvergierende/flache MAs | ❌ Fehlt |
| **RSI** | Momentum-Neutralität | RSI pendelt um 50 | ❌ Fehlt |

**Hauptkriterien für CONSOLIDATION:**
1. **ADX < 20** (Fehlender Trend)
2. **Bollinger Bänder ziehen sich zusammen** (niedrige BBW = Squeeze)
3. **RSI oszilliert um 50** (keine Extreme)
4. **Preis in definierter Spanne** (klar definiertes Hoch/Tief)

**Geeignete Strategien:** Mean Reversion, Range Trading

#### Detaillierte Standardwerte CONSOLIDATION

##### Trendstärke

| Parameter | Schwellenwert | Funktion |
|-----------|---------------|----------|
| **ADX** | **< 20** (oder **< 25**) | Wert unter 20 = Schwacher/kein Trend<br>Markt ist trendlos/seitwärts |

##### Volatilität und Range-Definition

| Indikator | Schwellenwert | Funktion |
|-----------|---------------|----------|
| **BBW** | **Niedrig** | Geringe Breite = Niedrige Volatilität<br>Kontraktion ("Squeeze") deutet auf Konsolidierung |
| **ATR** | **Relativ stabil und niedrig** | Niedriger ATR = Geringe Volatilität<br>Engere Handelsspannen |
| **Preisbewegung** | **Klar definierte Spanne** | Preis bewegt sich über Zeitraum (z.B. 4h)<br>innerhalb definiertem Hoch/Tief |

##### Momentum und Richtung

| Indikator | Schwellenwert | Funktion |
|-----------|---------------|----------|
| **RSI** | **Pendelt um 50** | Keine Extreme (>70 oder <30)<br>Oszilliert um neutralen Bereich<br>Extreme könnten Mean-Reversion-Signale sein |
| **MA/EMA** | **Konvergierend oder flach** | Kurz- und mittelfristige MAs verlaufen horizontal<br>Nähern sich einander an<br>Kein klarer Richtungstrend |
| **Volumen** | **Niedrig** | Niedriges Volumen = Marktunsicherheit<br>Oder "Verschnaufpause" |

**Hinweis:** ADX-Filterung kann auf längerem Zeitrahmen (1h) für Range-Definition geprüft werden

### 3.3 HIGH_VOLATILITY (Stark schwankend)

**Anforderung:** Messung der **Intensität der Preisbewegung** (nicht Richtung/Bandbreite)

| Indikator | Messgröße | Erkennungskriterium | Status |
|-----------|-----------|---------------------|--------|
| **ATR** | Absolute Volatilität | Aktueller ATR > Durchschnitts-ATR | ✅ Vorhanden |
| **BB** | Visuelle Volatilität | Starke Weitung der Bänder | ✅ Teilweise (BBW) |
| **ADX** | Richtung der Volatilität | Hoch (>25) = gerichtet<br>Niedrig = chaotisch | ✅ Vorhanden |

**Wichtigster Indikator:** ATR (Average True Range)

**Primäre strategische Konsequenz:**
- **Positionsgröße reduzieren** (absolutes Risiko konstant halten)
- **Stop-Loss-Abstände erweitern** (vorzeitiges Ausstoppen vermeiden)

**Geeignete Strategien:**
- **Ausbruchsstrategien** (bei gerichteter Volatilität, hoher ADX)
- **Handel aussetzen** (bei chaotischer, richtungsloser Volatilität, niedriger ADX)

#### Detaillierte Standardwerte HIGH_VOLATILITY

##### 1. Average True Range (ATR) - Hauptindikator

| Parameter | Standardwert | Kriterium | Anwendung |
|-----------|--------------|-----------|-----------|
| **ATR-Periode** | **14 Perioden** | - | Standardberechnung |
| **ATR-Schwelle** | - | Aktueller ATR > Ø ATR (20 Perioden)<br>**ODER**<br>ATR > 80. Perzentil der jüngsten Werte | Signalisiert hochvolatiles Regime |
| **ATRP** | - | ATR als % des Preises | Alternative Betrachtung |
| **Stop-Loss-Multiplikator** | **1.5x - 3.0x ATR** | - | Dynamische Stop-Loss-Distanz |

**ATR-Trend:** Aufwärtstrend in letzten Perioden bestätigt steigende Volatilität

##### 2. Bollinger Bänder (BB)

| Parameter | Standardwert | Kriterium | Signalisiert |
|-----------|--------------|-----------|--------------|
| **BB-Periode** | **20 Perioden** | - | Standard |
| **Standardabweichungen** | **2** | - | Standard |
| **BBW** | - | **Hoch** (starkes Auseinanderlaufen) | Explosives Momentum oder<br>chaotische Bewegungen |

##### 3. ADX - Richtung der Volatilität

| ADX-Wert | Interpretation | Konsequenz |
|----------|----------------|------------|
| **> 25 oder > 30** | Gerichtete Volatilität<br>(begleitet starken Trend) | Ausbruchsstrategien möglich |
| **Niedrig** | Chaotische, richtungslose Volatilität | Handel aussetzen |

**Wichtig:** ADX misst NICHT die Volatilität selbst, sondern die RICHTUNG der Volatilität

##### 4. Risikomanagement-Anpassungen

| Aspekt | Anpassung in HIGH_VOLATILITY | Begründung |
|--------|------------------------------|------------|
| **Positionsgröße** | **Automatisch reduzieren** | Absolutes monetäres Risiko pro Trade konstant halten |
| **Stop-Loss-Abstand** | **Erweitern** (1.5x - 3.0x ATR) | Vorzeitiges Ausstoppen in volatilen Märkten vermeiden |
| **Risiko-Normalisierung** | ATR-basierte Multiplikatoren | Größere Preisbewegungen kompensieren |

---

## 4. Gap-Analyse

### Fehlende Indikatoren

| Regime | Fehlende Indikatoren | Priorität | Begründung |
|--------|---------------------|-----------|------------|
| TREND | Volumen | Hoch | Trendbestätigung kritisch |
| TREND | MA-Kreuzungen | Mittel | Richtungs-Bestätigung |
| CONSOLIDATION | RSI | Mittel | Momentum-Neutralität |
| CONSOLIDATION | MA-Konvergenz | Niedrig | Redundant zu ADX |
| HIGH_VOLATILITY | Historical Volatility | Niedrig | ATR + BBW ausreichend |

### Implementierungs-Komplexität

| Indikator | Aufwand | Datenquellen | Bemerkungen |
|-----------|---------|--------------|-------------|
| Volumen | Niedrig | Bereits in OHLCV-Daten | Einfach hinzufügen |
| MA-Kreuzungen | Niedrig | Berechnung aus Preisdaten | Standard-Implementierung |
| RSI | Niedrig | Bereits vorhanden (für Entries) | Für Regime Detection nutzen |
| Historical Volatility | Mittel | Eigene Berechnung nötig | σ der Log-Returns |

---

## 5. Änderungsvorschläge

### Phase 1: Quick Wins (Niedrige Komplexität)

1. **Volumen-Indikator hinzufügen**
   - Berechne: `volume_ratio = current_volume / avg_volume(20)`
   - TREND-Kriterium: `volume_ratio > 1.2` bei Bewegungen in Trendrichtung

2. **RSI für Consolidation nutzen**
   - Nutze bestehenden RSI-Indikator
   - CONSOLIDATION-Kriterium: `40 < RSI < 60`

3. **MA-Kreuzungen implementieren**
   - EMA 10 / EMA 20 auf 1h
   - TREND-Kriterium: Golden Cross + Price > EMA10 > EMA20

### Phase 2: Verfeinerung (Mittlere Komplexität)

4. **Historical Volatility berechnen**
   - 20-Perioden Rolling Std. Dev. der Log-Returns
   - HIGH_VOLATILITY-Kriterium: `HV > HV_avg * 1.5`

5. **Multi-Timeframe Validierung**
   - Regime auf 1h bestimmen
   - Auf 4h validieren (höhere Zuverlässigkeit)

---

## 6. Offene Fragen

- [ ] Sollen alle Indikatoren gleich gewichtet werden oder gibt es Prioritäten?
- [ ] Welche Schwellenwerte für ADX bevorzugt? (20 vs. 25 für Consolidation)
- [ ] Soll Volumen-Indikator auch für andere Regimes genutzt werden?
- [ ] Timeframe-Strategie: Nur 1h oder Multi-TF (1h + 4h)?

---

## 7. Nächste Schritte

1. **Diskussion:** Weitere Notebook-Hinweise sammeln (Entry/Exit Logic, Risk Management)
2. **Priorisierung:** Welche Änderungen zuerst implementieren?
3. **Testing:** Backtesting-Plan für neue Regime Detection

---

## 8. Changelog

| Datum | Änderung | Quelle |
|-------|----------|--------|
| 2025-12-07 | Initial dokumentiert | Notebook-Hinweis zu Regime Detection |
| 2025-12-07 | Detaillierte Standardwerte für TREND hinzugefügt (ADX, EMA, Volumen, ATR) | Notebook-Hinweis: Standardwerte technische Indikatoren |
| 2025-12-07 | Detaillierte Standardwerte für CONSOLIDATION hinzugefügt (ADX, BBW, ATR, RSI, MA, Volumen) | Notebook-Hinweis: CONSOLIDATION Erkennung |
| 2025-12-07 | Detaillierte Standardwerte für HIGH_VOLATILITY hinzugefügt (ATR, BB, ADX, Risikomanagement) | Notebook-Hinweis: HIGH_VOLATILITY Erkennung |

---

## Referenzen

- **Aktuelle Implementierung:** `/services/prediction-service/app/core/strategy_engine.py`
- **Strategy JSON:** Database `prediction_service.strategies` (ID: `9675ccea-f520-4557-b54c-a98e1972cc1f`)
- **Frontend:** `/frontend/src/pages/StrategyOverview.tsx`

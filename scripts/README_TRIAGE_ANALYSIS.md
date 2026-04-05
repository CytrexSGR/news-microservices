# TRIAGE Quality Analysis Tools

Diese Tools helfen bei der Qualitätsbewertung des TRIAGE-Agenten nach dem Model-Wechsel von `gemini-flash-latest` zu `gemini-flash-lite-latest`.

## 📊 Verfügbare Tools

### 1. SQL-Analyse (Schnell & Einfach)

**Datei:** `scripts/analyze_triage_quality.sql`

Führt eine umfassende SQL-Analyse direkt in der Datenbank aus.

**Verwendung:**

```bash
# Von außerhalb des Containers
docker exec postgres psql -U news_user -d news_mcp -f /home/cytrex/news-microservices/scripts/analyze_triage_quality.sql

# Oder Output in Datei speichern
docker exec postgres psql -U news_user -d news_mcp -f /home/cytrex/news-microservices/scripts/analyze_triage_quality.sql > /tmp/triage_analysis.txt
```

**Was es zeigt:**
- Model-Usage über Zeit
- Priority Score Verteilung
- Scoring-Komponenten (Impact, Entity, Source)
- Kategorie-Verteilung
- Performance-Metriken (Cost, Time)
- Score-Buckets
- Top 10 Artikel pro Model
- Fehlerrate

---

### 2. Python-Analyse (Detailliert & Exportierbar)

**Datei:** `scripts/analyze_triage_quality.py`

Fortgeschrittene Analyse mit Export und optionalen Visualisierungen.

**Installation (falls Visualisierung gewünscht):**

```bash
cd /home/cytrex/news-microservices/services/content-analysis-v2
source venv/bin/activate
pip install pandas matplotlib seaborn
```

**Verwendung:**

```bash
# Basic Analyse (letzte 7 Tage)
python scripts/analyze_triage_quality.py

# Letzte 3 Tage
python scripts/analyze_triage_quality.py --days 3

# Mit JSON Export
python scripts/analyze_triage_quality.py --export json

# Mit CSV Export
python scripts/analyze_triage_quality.py --export csv

# Mit Visualisierungen
python scripts/analyze_triage_quality.py --charts

# Alles zusammen
python scripts/analyze_triage_quality.py --days 7 --export json --charts
```

**Output:**
- Detaillierter Comparison-Report in Console
- Export nach `/tmp/triage_quality_TIMESTAMP.json` oder `.csv`
- Charts nach `/tmp/triage_quality_comparison.png`

---

## 🎯 Was zu prüfen ist

### 1. Score-Qualität

**Akzeptabel:**
- Priority Score Differenz: **< 5 Punkte**
- Component Scores (Impact/Entity/Source): **< 5 Punkte**
- Standard-Abweichung ähnlich zwischen Models

**Beispiel:**
```
gemini-flash-latest:     Avg Priority: 62.5 ± 18.3
gemini-flash-lite-latest: Avg Priority: 61.8 ± 17.9
Differenz: 0.7 → ✅ GOOD
```

### 2. Tier 2 Trigger Rate

**Akzeptabel:**
- Differenz: **< 10%**

**Beispiel:**
```
gemini-flash-latest:     45% Tier 2 triggered
gemini-flash-lite-latest: 43% Tier 2 triggered
Differenz: 2% → ✅ GOOD
```

### 3. Kategorie-Verteilung

**Prüfen:**
- Sind die Kategorien ähnlich verteilt?
- Werden wichtige Artikel (GEOPOLITICS, ECONOMY) noch korrekt erkannt?

### 4. Performance

**Erwartete Verbesserungen:**
- Cost: **~90% günstiger**
- Speed: **3-5x schneller**

---

## 📅 Empfohlener Zeitplan

### Tag 1-2 (Jetzt)
- Baseline-Messung durchführen
- Erste Abweichungen prüfen

```bash
# Quick Check
python scripts/analyze_triage_quality.py --days 2
```

### Tag 3-5 (In 3 Tagen)
- Vollständige Analyse mit mehr Daten
- Export für Dokumentation

```bash
python scripts/analyze_triage_quality.py --days 5 --export json --charts
```

### Tag 7 (Nach 1 Woche)
- Finale Bewertung
- Entscheidung: Model beibehalten oder zurückwechseln?

```bash
python scripts/analyze_triage_quality.py --days 7 --export json --charts
```

---

## 🚨 Warnsignale

**Zurückwechseln zu gemini-flash-latest wenn:**

1. **Priority Score Differenz > 10 Punkte**
   - Lite-Model bewertet systematisch anders

2. **Tier 2 Trigger Rate Differenz > 15%**
   - Wichtige Artikel werden übersprungen ODER
   - Zu viele unwichtige Artikel triggern Tier 2

3. **Kategorisierung fehlerhaft**
   - GEOPOLITICS-Artikel als PANORAMA klassifiziert
   - ECONOMY-News nicht erkannt

4. **Manuelle Review zeigt Probleme**
   - Top-Artikel haben offensichtlich falsche Scores
   - Breaking News wird als unwichtig eingestuft

---

## 📝 Beispiel-Output

```
================================================================================
TRIAGE MODEL QUALITY COMPARISON REPORT
================================================================================

1. MODEL STATISTICS
--------------------------------------------------------------------------------

gemini-flash-latest:
  Articles Analyzed:     1500
  Avg Priority Score:    62.3 ± 18.5
  Score Range:           15-98 (median: 64)
  Tier 2 Triggered:      678 (45.2%)
  Tier 2 Skipped:        822 (54.8%)

  Component Scores:
    Impact Score:        58.4
    Entity Score:        52.1
    Source Score:        61.8
    Urgency Multiplier:  1.35

  Performance:
    Avg Cost:            $0.00350000
    Total Cost:          $5.250000
    Avg Time:            5690ms
    P95 Time:            8200ms
    Failures:            2

gemini-flash-lite-latest:
  Articles Analyzed:     450
  Avg Priority Score:    61.8 ± 17.9
  Score Range:           18-96 (median: 63)
  Tier 2 Triggered:      195 (43.3%)
  Tier 2 Skipped:        255 (56.7%)

  Component Scores:
    Impact Score:        57.9
    Entity Score:        51.8
    Source Score:        62.1
    Urgency Multiplier:  1.33

  Performance:
    Avg Cost:            $0.00031430
    Total Cost:          $0.141435
    Avg Time:            1030ms
    P95 Time:            1500ms
    Failures:            0


2. MODEL COMPARISON
--------------------------------------------------------------------------------

Comparing: gemini-flash-latest vs gemini-flash-lite-latest

  Score Differences:
    Priority Score:      0.50 points
    Impact Score:        0.50 points
    Entity Score:        0.30 points
    Source Score:        0.30 points
    Tier 2 Trigger Rate: 1.90%

  Performance Improvements:
    Cost Reduction:      91.0%
    Speed Improvement:   81.9%
    Total Savings:       $5.108565

  Quality Assessment:
    ✓ Score Similarity: GOOD
    ✓ Tier 2 Trigger Consistency: GOOD
    ✓ Component Scores Consistent: GOOD

================================================================================
RECOMMENDATIONS
================================================================================

✅ QUALITY MAINTAINED
   The lite model produces comparable results to the standard model.
   Cost savings of 91.0% make this an excellent optimization.
```

---

## 🔍 Weitere manuelle Checks

### Admin-Dashboard
http://localhost:3000/admin/services/content-analysis

Prüfen:
- Tier 2 Execution Rate (sollte stabil bleiben)
- Success Rate (sollte bei ~99% bleiben)
- Keine Häufung von "low_relevance_score" Skips für wichtige News

### Sample-Check wichtiger Artikel
```bash
# Top 10 wichtigste Artikel der letzten 3 Tage anschauen
docker exec postgres psql -U news_user -d news_mcp -c "
SELECT
    ar.article_id::text,
    fi.title,
    (ar.result_data->>'PriorityScore')::int as score,
    ar.model_used
FROM content_analysis_v2.agent_results ar
JOIN feed_items fi ON fi.id = ar.article_id
WHERE ar.agent_name = 'TRIAGE'
  AND ar.created_at > NOW() - INTERVAL '3 days'
  AND ar.model_used = 'gemini-flash-lite-latest'
ORDER BY (ar.result_data->>'PriorityScore')::int DESC
LIMIT 10;
"
```

---

## 💡 Tipps

1. **Erste Woche:** Täglich kurz prüfen
2. **Bei Unsicherheit:** Beide Models parallel laufen lassen (A/B Test)
3. **Dokumentation:** Exports aufbewahren für spätere Referenz
4. **Manuelle Reviews:** 10-20 zufällige Artikel überprüfen

---

## 📞 Bei Problemen

1. Logs prüfen:
```bash
docker logs news-microservices-content-analysis-v2-1 | grep TRIAGE
```

2. Zurückwechseln zu flash-latest:
```bash
# In .env Datei ändern
sed -i 's/gemini-flash-lite-latest/gemini-flash-latest/g' services/content-analysis-v2/.env

# Workers neustarten
cd /home/cytrex/news-microservices
docker compose up -d --force-recreate --no-deps content-analysis-v2
```

3. Issue erstellen mit Analysis-Output

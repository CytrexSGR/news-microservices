# Knowledge Graph Validation Plan
## Umfassender Testplan für Relationship Extraction

**Version:** 1.0
**Erstellt:** 2025-10-23
**Status:** In Preparation

---

## 🎯 Ziel

Quantitativ und qualitativ bewerten, wie zuverlässig, genau und robust die neue Beziehungsextraktion unter verschiedenen Bedingungen arbeitet.

---

## 📋 Methodik

Wir führen eine Reihe von manuellen und teil-automatisierten Tests auf **vier verschiedenen Ebenen** durch:

1. **Atomare Validierung** - Präzision & Recall pro Artikel
2. **Konsistenz-Validierung** - Entity Normalization über Artikel hinweg
3. **Robustheits-Tests** - Verhalten bei schwierigen Inputs
4. **Monitoring-Validierung** - Korrektheit der Metriken

---

## 📚 Test-Vorbereitung: Kuratierter Test-Datensatz

### Artikel-Kategorien (15-20 Artikel Total)

#### Kategorie A: "Einfach & Faktisch" (5 Artikel)
**Charakteristik:** Kurze Nachrichtenmeldungen mit sehr klaren, unzweideutigen Fakten

**Beispiele:**
- Personalwechsel ("Firma X ernennt Y zum CEO")
- Unternehmensübernahmen ("A kauft B für $X Millionen")
- Gerichtsentscheidungen ("Gericht X entscheidet gegen Firma Y")
- Produktankündigungen ("Apple stellt iPhone 15 vor")
- Standorteröffnungen ("Tesla eröffnet Gigafactory in Texas")

**Erwartete Performance:**
- Präzision: > 90%
- Recall: > 80%
- Avg Confidence: > 0.85

---

#### Kategorie B: "Komplex & Dicht" (5 Artikel)
**Charakteristik:** Längere Analyse-Artikel mit vielen verschachtelten Sätzen und mehreren, miteinander verbundenen Ereignissen

**Beispiele:**
- Wirtschaftsanalysen mit mehreren Akteuren
- Politische Hintergrundberichte
- Investigative Recherchen
- Merger & Acquisition Analysen
- Geopolitische Konfliktsituationen

**Erwartete Performance:**
- Präzision: > 75%
- Recall: > 60%
- Avg Confidence: > 0.70

---

#### Kategorie C: "Mehrdeutig & Meinungsbasiert" (5 Artikel)
**Charakteristik:** Kommentare oder Interviews, bei denen Beziehungen oft eher impliziert als explizit genannt werden

**Beispiele:**
- Meinungskolumnen
- Interviews mit indirekter Rede
- Spekulative Marktanalysen
- Politische Kommentare
- Zukunftsprognosen

**Erwartete Performance:**
- Präzision: > 60%
- Recall: > 40%
- Avg Confidence: < 0.65
- **Wichtig:** System sollte niedrige Confidence-Scores vergeben!

---

#### Kategorie D: "Negativ-Beispiele" (3 Artikel)
**Charakteristik:** Artikel, die zwar Entitäten, aber absichtlich keine klaren Beziehungen enthalten

**Beispiele:**
- Reine Auflistung von Konferenzteilnehmern
- Wetterberichte mit Orten
- Sportstatistiken ohne narrative Verbindungen
- Terminkalender
- Produktspezifikationen ohne Kontext

**Erwartete Performance:**
- False Positive Rate: < 10%
- Extracted Relationships: < 3 per Artikel
- Avg Confidence: < 0.50

---

## 🧪 Test-Ebene 1: Atomare Validierung (Präzision & Recall)

### Ziel
Wie gut funktioniert die Extraktion bei einem einzelnen Artikel?

### Prozess

1. **Artikel auswählen** aus Test-Set (Start mit Kategorie A)

2. **Ground Truth Erstellung (Manual)**
   - Artikel sorgfältig lesen
   - Alle Fakten-Triplets von Hand aufschreiben
   - Format: `[Subjekt, Beziehung, Objekt, Evidence-Quote]`
   - In `test-data/ground-truth/<article-id>.json` speichern

3. **Analyse durchführen**
   ```bash
   # Via API
   curl -X POST http://localhost:8102/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d @test-data/articles/<article-id>.json
   ```

4. **Ergebnisse extrahieren**
   ```sql
   SELECT extracted_relationships, relationship_metadata
   FROM analysis_results
   WHERE article_id = '<article-id>'
     AND analysis_type = 'entities';
   ```

5. **Vergleich durchführen**
   - System-Triplets (confidence > 0.7) vs. Ground Truth
   - Berechnung von Precision, Recall, F1-Score

### Metriken

**Präzision (Precision)**
```
Precision = Korrekte_System_Funde / Alle_System_Funde
```
- **Bedeutung:** Von den Beziehungen, die das System fand, wie viele sind korrekt?
- **Ziel:** System erfindet wenig Unsinn

**Trefferquote (Recall)**
```
Recall = Korrekte_System_Funde / Alle_Wahren_Beziehungen
```
- **Bedeutung:** Von allen wahren Beziehungen, wie viele fand das System?
- **Ziel:** Dem System entgeht wenig

**F1-Score**
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```
- **Bedeutung:** Harmonisches Mittel aus Precision und Recall
- **Ziel:** Ausgewogene Performance

**Evidence-Qualität**
- Ist der `evidence`-Text wirklich Beweis für die Beziehung?
- Scoring: 0 (irrelevant), 0.5 (teilweise), 1.0 (perfekt)

### Erfolgs-Kriterien

| Kategorie | Precision | Recall | F1-Score | Evidence Quality |
|-----------|-----------|--------|----------|------------------|
| A (Faktisch) | > 90% | > 80% | > 85% | > 0.9 |
| B (Komplex) | > 75% | > 60% | > 67% | > 0.8 |
| C (Meinungsbasiert) | > 60% | > 40% | > 48% | > 0.7 |
| D (Negativ) | N/A | N/A | N/A | False Positives < 10% |

---

## 🔄 Test-Ebene 2: Konsistenz-Validierung (Entity Normalization)

### Ziel
Baut das System über mehrere Artikel hinweg ein sauberes, konsistentes Wissensnetz auf?

### Prozess

1. **Artikel-Paare auswählen**
   - Zwei Artikel über dieselben Kern-Entitäten (z.B. Apple)
   - Aus verschiedenen Zeiträumen oder Quellen

2. **Beide Artikel analysieren**

3. **Triplets aus Datenbank extrahieren**
   ```sql
   SELECT
       article_id,
       extracted_relationships,
       relationship_metadata
   FROM analysis_results
   WHERE article_id IN ('<id1>', '<id2>')
     AND analysis_type = 'entities'
   ORDER BY created_at;
   ```

4. **Konsistenz prüfen**

### Test-Kriterien

#### 1. Entity Normalization
**Frage:** Erkennt das System, dass "Apple", "Apple Inc." und "der iPhone-Hersteller" dieselbe Entität sind?

**Prüfung:**
```python
# Extrahiere alle Entity-Varianten für dieselbe reale Entity
entity_variants = {
    "Apple": ["Apple", "Apple Inc.", "Apple Inc", "der iPhone-Hersteller"],
    "Tim Cook": ["Tim Cook", "Cook", "CEO Tim Cook"]
}

# Prüfe Normalisierung in Triplets
for triplet in extracted_relationships:
    if any_variant_in(triplet, entity_variants["Apple"]):
        assert uses_canonical_name(triplet, "Apple")
```

**Erfolgskriterium:** > 90% der Triplets verwenden konsistente, normalisierte Namen

#### 2. Beziehungs-Konsistenz
**Frage:** Extrahiert das System denselben Fakt aus beiden Artikeln gleich?

**Beispiel:**
- Artikel 1: `[Tim Cook, works_for, Apple]` (confidence: 0.95)
- Artikel 2: `[Tim Cook, works_for, Apple]` (confidence: 0.93)
- ✅ Konsistent!

**Erfolgskriterium:** Identische Fakten sollten in > 85% der Fälle gleich extrahiert werden

#### 3. Fehlen von Widersprüchen
**Frage:** Erzeugt das System offensichtlich widersprüchliche Fakten?

**Anti-Patterns:**
```json
[
  ["Elon Musk", "works_for", "Tesla"],
  ["Elon Musk", "works_for", "SpaceX"]  // ✅ OK - beide korrekt
]

[
  ["Apple", "located_in", "Cupertino"],
  ["Apple", "located_in", "Seattle"]  // ❌ WIDERSPRUCH!
]
```

**Erfolgskriterium:** < 5% Widerspruchsrate

---

## 💪 Test-Ebene 3: Robustheits- & Stress-Tests

### Ziel
Wie verhält sich das System bei schwierigen oder unerwarteten Eingaben?

### Test 3.1: Falsch-Positive-Rate (Kritischster Test!)

**Prozess:**
1. Verwende Kategorie D Artikel (Negativ-Beispiele)
2. Lasse analysieren
3. Zähle extrahierte Beziehungen

**Erwartung:**
```python
assert len(extracted_relationships) < 3
assert all(r['confidence'] < 0.6 for r in extracted_relationships)
```

**Erfolgskriterium:** Falsch-Positive-Rate < 10%

### Test 3.2: Verhalten bei Meinungen

**Test-Input:**
```
"Ich glaube, Firma A könnte bald Firma B übernehmen."
"Es wird spekuliert, dass X für Y arbeitet."
"Möglicherweise hat Z eine Verbindung zu W."
```

**Erwartung:**
- Entweder: Keine Extraktion
- Oder: Sehr niedrige Confidence (< 0.5)

**Erfolgskriterium:** Avg Confidence für spekulative Sätze < 0.5

### Test 3.3: Edge Cases & Error Handling

| Input | Erwartetes Verhalten |
|-------|---------------------|
| Leerer String | `extracted_relationships: []` |
| Nur HTML Tags | `extracted_relationships: []` |
| Nur Zahlen | `extracted_relationships: []` |
| 1-Wort-Input | `extracted_relationships: []` |
| 10,000+ Wörter | Truncation + Warning, aber keine Errors |
| Nicht-englischer Text | Basierend auf LLM-Capability |
| Gemischte Sprachen | Best-Effort Extraktion |

**Erfolgskriterium:** Keine Crashes, graceful degradation

### Test 3.4: Validation Rules Check

**Prozess:** Mock LLM response mit absichtlich fehlerhaften Daten

```python
# Test: Self-Relationship Detection
mock_response = {
    "entities": [{"text": "Apple", "type": "ORGANIZATION", "confidence": 0.9}],
    "relationships": [{
        "entity1": "Apple",
        "entity2": "Apple",  # SAME!
        "relationship_type": "owns",
        "confidence": 0.8,
        "evidence": "Apple owns Apple"
    }]
}
```

**Erwartung:** RelationshipValidator filtert dies als invalid (reason: "Self-relationship detected")

**Erfolgskriterium:** Alle 4 Validierungsregeln funktionieren korrekt

---

## 📊 Test-Ebene 4: Monitoring-Validierung

### Ziel
Funktionieren die von uns eingebauten Messinstrumente korrekt?

### Prozess

1. **Service-Neustart** (Metriken zurücksetzen)
   ```bash
   docker compose restart content-analysis-service
   ```

2. **Test-Set analysieren** (alle 15-20 Artikel)

3. **Metriken abrufen**
   ```bash
   curl http://localhost:8102/metrics | grep relationship
   ```

### Metrik-Validierungen

#### 1. `relationship_extraction_total`
**Check:**
```python
total_valid = metrics['relationship_extraction_total{status="valid"}']
total_invalid = metrics['relationship_extraction_total{status="invalid"}']
total_proposed = total_valid + total_invalid

# Muss mit Summe aller LLM-Vorschläge übereinstimmen
assert total_proposed == sum(len(r['relationships']) for r in llm_responses)
```

#### 2. `relationship_confidence_distribution`
**Check:** Histogramm-Verteilung plausibel?

Erwartete Verteilung für Kategorie A (Faktisch):
```
Bucket 0.5-0.6:  5%
Bucket 0.6-0.7: 10%
Bucket 0.7-0.8: 20%
Bucket 0.8-0.9: 35%
Bucket 0.9-1.0: 30%
```

#### 3. `analysis_acceptance_rate`
**Check:** Gauge-Wert in erwartetem Bereich?

```python
assert 0.70 <= acceptance_rate <= 0.90  # für gemischten Test-Set
```

#### 4. `relationship_validation_failures_total`
**Check:** Breakdown nach Reason korrekt?

```python
failures = {
    'failed_confidence': metrics['...{reason="failed_confidence"}'],
    'failed_evidence': metrics['...{reason="failed_evidence"}'],
    'failed_entity': metrics['...{reason="failed_entity"}'],
    'failed_self_ref': metrics['...{reason="failed_self_ref"}']
}

# Summe muss total_invalid entsprechen
assert sum(failures.values()) == total_invalid
```

### Erfolgs-Kriterien

- ✅ Alle Counter summieren sich korrekt
- ✅ Histogramm zeigt plausible Verteilung
- ✅ Gauges aktualisieren sich in Echtzeit
- ✅ Keine fehlenden oder NaN-Werte

---

## 🗂️ Test-Daten-Struktur

### Verzeichnisstruktur
```
/home/cytrex/news-microservices/tests/knowledge-graph/
├── README.md
├── test-data/
│   ├── articles/
│   │   ├── category-a/
│   │   │   ├── article-001-ceo-appointment.json
│   │   │   ├── article-002-acquisition.json
│   │   │   ├── article-003-court-ruling.json
│   │   │   ├── article-004-product-launch.json
│   │   │   └── article-005-factory-opening.json
│   │   ├── category-b/
│   │   │   └── (5 complex articles)
│   │   ├── category-c/
│   │   │   └── (5 opinion pieces)
│   │   └── category-d/
│   │       └── (3 negative examples)
│   └── ground-truth/
│       ├── article-001-ground-truth.json
│       ├── article-002-ground-truth.json
│       └── ...
├── scripts/
│   ├── run_test_suite.py
│   ├── calculate_metrics.py
│   ├── validate_monitoring.py
│   └── generate_report.py
└── results/
    └── test-run-YYYYMMDD-HHMMSS/
        ├── precision-recall.csv
        ├── consistency-report.md
        ├── robustness-report.md
        └── monitoring-validation.json
```

### Article Format (`articles/*.json`)
```json
{
  "article_id": "article-001",
  "category": "A",
  "title": "Apple Appoints New CFO",
  "content": "Apple Inc. announced today that Jane Smith has been appointed as the new Chief Financial Officer...",
  "source": "TechCrunch",
  "published_at": "2025-10-20",
  "metadata": {
    "word_count": 250,
    "expected_entities": 5,
    "expected_relationships": 3
  }
}
```

### Ground Truth Format (`ground-truth/*.json`)
```json
{
  "article_id": "article-001",
  "ground_truth_relationships": [
    {
      "triplet": ["Jane Smith", "works_for", "Apple Inc."],
      "evidence": "Jane Smith has been appointed as the new Chief Financial Officer at Apple Inc.",
      "confidence_expectation": "high",
      "notes": "Explicitly stated appointment"
    },
    {
      "triplet": ["Jane Smith", "located_in", "Cupertino"],
      "evidence": "She will be based at Apple's headquarters in Cupertino",
      "confidence_expectation": "high",
      "notes": "Clear location statement"
    }
  ],
  "expected_metrics": {
    "total_relationships": 2,
    "avg_confidence_min": 0.85
  }
}
```

---

## 📈 Test-Ausführung & Reporting

### Durchführung
```bash
# 1. Test-Suite ausführen
cd /home/cytrex/news-microservices/tests/knowledge-graph
python scripts/run_test_suite.py --category all

# 2. Ergebnisse analysieren
python scripts/calculate_metrics.py --results results/latest

# 3. Report generieren
python scripts/generate_report.py --output report.html
```

### Report-Struktur

**Executive Summary:**
- Gesamt-Präzision, Recall, F1-Score
- Acceptance Rate
- Falsch-Positive-Rate

**Detaillierte Ergebnisse:**
- Pro Kategorie (A, B, C, D)
- Pro Artikel (mit Drill-Down)
- Häufigste Fehlertypen

**Empfehlungen:**
- Identifizierte Schwachstellen
- Vorschläge zur Prompt-Optimierung
- Threshold-Anpassungen

---

## 🎯 Erfolgs-Definition

### Minimum Viable Quality (MVQ)

| Metrik | Schwellenwert |
|--------|--------------|
| **Overall Precision** | ≥ 75% |
| **Overall Recall** | ≥ 60% |
| **F1-Score** | ≥ 67% |
| **Acceptance Rate** | 70-90% |
| **False Positive Rate** | ≤ 15% |
| **Consistency Score** | ≥ 80% |
| **Evidence Quality** | ≥ 0.75 |

### Stretch Goals

| Metrik | Ziel |
|--------|------|
| **Overall Precision** | ≥ 85% |
| **Overall Recall** | ≥ 70% |
| **F1-Score** | ≥ 77% |
| **Acceptance Rate** | 75-85% |
| **False Positive Rate** | ≤ 10% |
| **Consistency Score** | ≥ 90% |
| **Evidence Quality** | ≥ 0.85 |

---

## 🚀 Nächste Schritte

### Phase 1: Test-Datensatz erstellen (This Week)
- [ ] 5 Artikel Kategorie A sammeln/erstellen
- [ ] 5 Artikel Kategorie B sammeln/erstellen
- [ ] 5 Artikel Kategorie C sammeln/erstellen
- [ ] 3 Artikel Kategorie D sammeln/erstellen
- [ ] Ground Truth für alle Artikel manuell erstellen

### Phase 2: Test-Infrastruktur (Next Week)
- [ ] `run_test_suite.py` implementieren
- [ ] `calculate_metrics.py` implementieren
- [ ] `validate_monitoring.py` implementieren
- [ ] `generate_report.py` implementieren

### Phase 3: Ausführung & Iteration (Week 3)
- [ ] Vollständige Test-Suite durchführen
- [ ] Ergebnisse analysieren
- [ ] Schwachstellen identifizieren
- [ ] Prompt/Threshold Optimierungen
- [ ] Retest

### Phase 4: Dokumentation & Handoff (Week 4)
- [ ] Finaler Test-Report
- [ ] Lessons Learned dokumentieren
- [ ] Best Practices ableiten
- [ ] Production Readiness Assessment

---

**Status:** Ready to Start
**Next Action:** Test-Datensatz zusammenstellen

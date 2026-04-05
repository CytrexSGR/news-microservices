# Knowledge Graph Test Suite - Session Status

**Datum:** 2025-10-23, 21:04 Uhr
**Status:** Test-Suite bereit, aber API-Endpoint fehlt
**Nächster Schritt:** Test-Endpoint implementieren

---

## ✅ Was erfolgreich abgeschlossen wurde

### 1. Implementierung abgeschlossen (Phase 1 der ursprünglichen Planung)

Alle Komponenten der Knowledge Graph Relationship Extraction wurden implementiert:

- **Prompts erweitert** (`app/llm/prompts.py`):
  - ENTITIES Prompt mit detaillierten Relationship Extraction Rules
  - Confidence Score Guidelines (0.9-1.0 = explizit, 0.7-0.9 = stark impliziert, etc.)
  - 3 neue Relationship Types: `ruled_against`, `abused_monopoly_in`, `announced`

- **Pydantic Schemas** (`app/schemas/relationship_extraction.py`):
  - `RelationshipTriplet` mit Validation
  - `EntityExtractionResponse` mit Cross-Validation
  - `RelationshipValidator` Klasse

- **Validation Service** (`app/services/relationship_validator.py`):
  - 4 Validierungsregeln (Confidence, Evidence, Entity, Self-Relationship)
  - Filtering und Metrics Berechnung

- **Database Schema** erweitert (`database/models/analysis.py`):
  - `extracted_relationships` JSONB Feld
  - `relationship_metadata` JSONB Feld
  - GIN Indexes erstellt

- **Prometheus Metrics** (`app/core/metrics.py`):
  - `relationship_extraction_total` Counter
  - `relationship_confidence_distribution` Histogram
  - `relationship_validation_failures` Counter
  - `relationship_acceptance_rate` Gauge

- **LLM Provider Integration** (alle 3):
  - OpenAI, Anthropic, Gemini: Pydantic Validation nach JSON Parsing

- **Analysis Service Integration** (`app/services/analysis_service.py`):
  - Relationship Validation nach LLM Response
  - Metrics Updates
  - Database Storage

### 2. Test-Datensatz komplett erstellt

**18 Artikel + 18 Ground Truth Dateien:**

```
Category A (Simple):     5 Artikel ✓
Category B (Complex):    5 Artikel ✓
Category C (Ambiguous):  5 Artikel ✓
Category D (Negative):   3 Artikel ✓
```

**Beispiele:**
- `article-003-court-ruling.json` - Testet neue `ruled_against` und `abused_monopoly_in` Types
- `article-009-investigative-journalism.json` - FTX Collapse (25 Entities, 19 erwartete Relationships)
- `article-015-future-prediction.json` - Kritischer Test für Speculation Handling
- `article-017-weather-report.json` - Negative Example (0 Relationships erwartet)

### 3. Test-Automatisierung vollständig implementiert

**4 Python Scripts + 1 Master Script:**

1. **`run_test_suite.py`** (277 Zeilen)
   - Iteriert durch alle Kategorien
   - POST Request an API für jeden Artikel
   - Speichert Rohdaten in `test-results/`
   - Rate-Limiting (1 req/sec)

2. **`calculate_metrics.py`** (390 Zeilen)
   - Triplet Normalization (lowercase, relationship type mapping)
   - TP/FP/FN Berechnung
   - Precision/Recall/F1 per Kategorie + Overall
   - Hall of Fame/Shame Identifikation

3. **`generate_report.py`** (380 Zeilen)
   - Visueller HTML Report
   - Overall Performance Dashboard
   - Per-Category Tabelle mit Farbcodierung
   - Confusion Matrix

4. **`validate_monitoring.py`** (297 Zeilen)
   - Prometheus Metrics Scraping
   - Counter/Gauge Validierung
   - 10% Toleranz für Varianz

5. **`run_all_tests.sh`** (Master Script)
   - Sequentielle Ausführung aller 4 Phasen
   - Error Handling zwischen Phasen
   - Quick Summary mit `jq`

### 4. Dokumentation komplett

- **`README.md`** (vollständig, 500+ Zeilen):
  - Quick Start Guide
  - Script-Dokumentation
  - Troubleshooting
  - Best Practices
  - Templates für neue Test-Artikel

---

## ❌ Das Problem beim ersten Testlauf

### Fehlerbeschreibung

**Alle 18 Requests schlugen mit 422 Unprocessable Entity fehl:**

```bash
✗ Analysis failed: 422 Client Error: Unprocessable Entity for url: http://localhost:8102/api/v1/analysis/
```

### Root Cause Analyse

**Der content-analysis-service ist event-driven, nicht request-driven:**

- ✅ **Hat:** Event Handler für RabbitMQ `article.created` Events
- ❌ **Hat NICHT:** HTTP POST Endpoint `/api/v1/analysis`

**Existierende Endpoints:**
- `GET /api/v1/events` - Liste OSINT Event Analyses
- `GET /api/v1/events/{event_id}` - Einzelnes Event
- `GET /api/v1/articles/{article_id}/events` - Events für Artikel
- `POST /api/v1/events/search` - Full-text Search
- `GET /api/v1/events/review-queue` - Review Queue
- `GET /api/v1/stats` - Statistiken

**Wo ist der Analysis Code?**
- Location: `services/content-analysis-service/app/services/analysis_service.py`
- Trigger: RabbitMQ Message Handler in `app/services/message_handler.py`
- Flow: Feed-Service → RabbitMQ → Content-Analysis → Database

### Warum das ein Problem ist

**Test-Suite erwartet synchronen HTTP Endpoint:**
```python
response = requests.post(
    f"{API_URL}/analysis",
    json={
        "article_id": "uuid",
        "content": "text",
        "analysis_type": "entities"
    }
)
```

**Production verwendet asynchronen Event Flow:**
```
Feed-Service → article.created Event → RabbitMQ → Content-Analysis → DB
```

---

## 🔧 Die Lösung (Nächster Schritt)

### Option 1: Event-basiert testen (Production-like)
**Vorteile:**
- Testet echten Production Flow
- Deckt RabbitMQ Integration ab

**Nachteile:**
- Komplexer (RabbitMQ Producer implementieren)
- Asynchron (muss auf Verarbeitung warten)
- Schwieriger zu debuggen

### Option 2: Test-Endpoint erstellen ⚡ **EMPFOHLEN**

**Erstelle:** `app/api/routes/testing.py`

```python
@router.post("/test/analyze")
async def test_analyze_article(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    TEST-ONLY endpoint for Knowledge Graph validation.

    Synchronously analyzes an article and returns relationships.
    NOT for production use - only for test suite.
    """
    # Call analysis_service.analyze_article() directly
    result = await analysis_service.analyze_article(
        db=db,
        article_id=request.article_id,
        content=request.content,
        title=request.title,
        analysis_type=request.analysis_type
    )

    return {
        "article_id": request.article_id,
        "relationships": result.get("relationships", []),
        "entities": result.get("entities", []),
        "metadata": {
            "confidence_avg": ...,
            "extraction_count": ...
        }
    }
```

**Vorteile:**
- Schnell implementierbar (~10 Minuten)
- Sofortige Validierung möglich
- Einfaches Debugging
- Test-Suite kann ohne Änderung laufen

**Nachteile:**
- Testet nicht RabbitMQ Integration
- Zusätzlicher Code nur für Testing

---

## 📋 Konkrete TODOs für Fortsetzung

### Schritt 1: Test-Endpoint implementieren (10 Minuten)

1. **Erstelle:** `services/content-analysis-service/app/api/routes/testing.py`
   ```python
   from fastapi import APIRouter, Depends
   from app.services.analysis_service import AnalysisService
   # ... siehe Vorlage oben
   ```

2. **Registriere Router in:** `app/api/__init__.py` oder `app/main.py`
   ```python
   from app.api.routes import testing
   app.include_router(testing.router, prefix="/api/v1", tags=["testing"])
   ```

3. **Restart Service:**
   ```bash
   docker compose restart content-analysis
   ```

4. **Verify:**
   ```bash
   curl -X POST http://localhost:8102/api/v1/test/analyze \
     -H "Authorization: Bearer $AUTH_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"article_id": "test", "content": "Microsoft CEO Satya Nadella announced...", "analysis_type": "entities"}'
   ```

### Schritt 2: Test-Suite ausführen (20-30 Minuten)

```bash
cd /home/cytrex/news-microservices/tests/knowledge-graph

export AUTH_TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "andreas@test.com", "password": "Aug2012#"}' | jq -r '.access_token')

export CONTENT_ANALYSIS_API_URL="http://localhost:8102/api/v1"

# UPDATE: run_test_suite.py Zeile 88 ändern:
# f"{self.api_url}/test/analyze"  # Statt /analysis

./scripts/run_all_tests.sh
```

### Schritt 3: Ergebnisse analysieren (Phase 2)

**Quantitativ:**
1. HTML Report öffnen: `firefox test-results/test_report.html`
2. Overall Performance prüfen: Precision, Recall, F1
3. Per-Category Vergleich mit Baseline:
   ```
   Category A: Erwartung >90% Precision
   Category B: Erwartung >75% Precision
   Category C: Erwartung >60% Precision
   Category D: Erwartung <2 FP/Artikel
   ```

**Qualitativ:**
1. **Hall of Shame analysieren:**
   - Welche False Positives?
   - Muster erkennen (bestimmte Relationship Types? Satzstrukturen?)
   - Beispiele notieren

2. **Hall of Fame studieren:**
   - Was funktioniert perfekt?
   - Diese Patterns in Prompt verstärken

3. **Category D prüfen:**
   - KRITISCH: Wie viele False Positives bei Negativ-Beispielen?
   - Artikel 016, 017, 018 sollten 0 Relationships haben

---

## 🗂️ Wichtige Dateipfade

### Implementierte Features
```
services/content-analysis-service/app/
├── llm/prompts.py                          # ERWEITERT: ENTITIES Prompt
├── schemas/relationship_extraction.py      # NEU: Pydantic Schemas
├── services/
│   ├── relationship_validator.py           # NEU: Validation Logik
│   └── analysis_service.py                 # ERWEITERT: Metrics + Storage
├── core/metrics.py                         # NEU: Prometheus Metrics
└── database/models/analysis.py             # ERWEITERT: JSONB Felder

database/migrations/
├── add_relationship_fields.sql             # Migration Script
└── rollback_relationship_fields.sql        # Rollback Script
```

### Test Suite
```
tests/knowledge-graph/
├── README.md                                # Vollständige Doku
├── SESSION_STATUS.md                        # Diese Datei
├── test-data/
│   ├── articles/
│   │   ├── category-a/                      # 5 Artikel
│   │   ├── category-b/                      # 5 Artikel
│   │   ├── category-c/                      # 5 Artikel
│   │   └── category-d/                      # 3 Artikel
│   └── ground-truth/                        # 18 Ground Truth Files
├── test-results/                            # Wird generiert
│   ├── category-*/                          # Result JSONs
│   ├── execution_stats.json
│   ├── summary_report.json
│   └── test_report.html
└── scripts/
    ├── run_test_suite.py                    # Phase 1: Execute
    ├── calculate_metrics.py                 # Phase 2: Metrics
    ├── generate_report.py                   # Phase 3: HTML
    ├── validate_monitoring.py               # Phase 4: Prometheus
    └── run_all_tests.sh                     # Master Script
```

### Zu erstellen
```
services/content-analysis-service/app/api/routes/
└── testing.py                               # NEU: Test-Endpoint
```

---

## 🔍 Debug-Informationen

### Auth Token (valid bis ~22:59 Uhr heute)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMSIsInVzZXJuYW1lIjoiYW5kcmVhcyIsInJvbGVzIjpbInVzZXIiLCJhZG1pbiJdLCJleHAiOjE3NjEyNTUxNjksImlhdCI6MTc2MTI1MzM2OSwidHlwZSI6ImFjY2VzcyJ9.2T64ZidCyvqs8D6Vnlfxyba-2gGP3TEELGFN2xaZR7M
```

### Service Status (beim Abbruch)
```bash
docker ps --filter "name=content-analysis"
# Status: Up 33 minutes (healthy)
# Port: 8102:8000
```

### Letzter Test-Run
```bash
# Background Process ID: 2fdef6
# Command: ./scripts/run_all_tests.sh
# Status: Failed (Exit Code 1)
# Failures: 18/18 (422 Errors)
# Grund: POST /api/v1/analysis Endpoint existiert nicht
```

### Test-Run Output (Auszug)
```
Total articles: 18
Successful: 0 (0.0%)
Failed: 18 (100.0%)

By Category:
  category-a: 0/5 (0.0%)
  category-b: 0/5 (0.0%)
  category-c: 0/5 (0.0%)
  category-d: 0/3 (0.0%)
```

---

## 📊 Erwartete Baseline-Performance (zum Vergleich)

Nach erfolgreicher Implementierung des Test-Endpoints erwarten wir:

| Kategorie | Precision | Recall | F1 | FP/Artikel |
|-----------|-----------|--------|----|------------|
| Category A | >90% | >85% | >87% | <1 |
| Category B | >75% | >60% | >67% | <3 |
| Category C | >60% | >50% | >54% | <6 |
| Category D | N/A | N/A | N/A | <2 |
| **Overall** | **>75%** | **>65%** | **>69%** | - |

**Kritische Erfolgskriterien:**
1. ✅ Category A muss >90% Precision erreichen (einfache Fakten)
2. ✅ Category D darf max 2 FP/Artikel haben (keine Halluzinationen)
3. ✅ Overall F1 Score muss >65% sein
4. ✅ Prometheus Metrics müssen mit Actual Results übereinstimmen

---

## 💡 Lessons Learned

1. **Event-driven Architecture:** Service Design prüfen bevor Test-Suite schreiben
2. **API Discovery:** Existierende Endpoints dokumentieren/testen vor Implementierung
3. **Test-Endpoints:** Für ML/LLM Services oft sinnvoll (synchrone Validation)
4. **Ground Truth Naming:** Muss exakt matchen (aktuell funktioniert nicht wegen Suffix)

---

## 🚀 Quick Start für Morgen

```bash
# 1. Status prüfen
cd /home/cytrex/news-microservices
docker compose ps content-analysis

# 2. Diese Datei lesen
cat tests/knowledge-graph/SESSION_STATUS.md

# 3. Test-Endpoint implementieren (siehe Schritt 1 oben)
vim services/content-analysis-service/app/api/routes/testing.py

# 4. Service neu starten
docker compose restart content-analysis

# 5. Token holen
export AUTH_TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "andreas@test.com", "password": "Aug2012#"}' | jq -r '.access_token')

# 6. Test-Suite starten
cd tests/knowledge-graph
./scripts/run_all_tests.sh

# 7. Ergebnisse analysieren
firefox test-results/test_report.html
```

---

**Geschätzte Zeit bis zum ersten vollständigen Testlauf:** ~40 Minuten
**Geschätzte Zeit für Analyse:** ~1-2 Stunden

**Status:** Bereit für Fortsetzung 🚀

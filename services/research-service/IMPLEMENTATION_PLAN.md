# Research Service - Produktionsreife Implementation
**Ziel:** Service vollständig lauffähig machen (UUID, Celery, Perplexity, Health-Checks)
**Geschätzte Zeit:** 2-3 Stunden
**Status:** Bereit zur Ausführung

---

## 🎯 Änderungsübersicht

### 1. **UUID Migration** (KRITISCH)
**Warum:** Feed Service nutzt UUID → Research muss kompatibel sein
**Was:**
- ResearchTask.id: Integer → UUID
- ResearchTemplate.id: Integer → UUID
- ResearchRun.id: Integer → UUID
- ResearchCache.id: Integer → UUID
- CostTracking.id: Integer → UUID

### 2. **Legacy Fields** (KRITISCH)
**Warum:** Migration von altem System, API erwartet diese
**Was:**
- ResearchTask.legacy_feed_id: Integer (nullable)
- ResearchTask.legacy_article_id: Integer (nullable)

### 3. **Celery Aktivierung** (KRITISCH)
**Warum:** API blockiert ohne async Queue
**Was:**
- create_research_task() → Celery Queue statt synchron
- Worker verarbeitet Task
- Event Publishing nach Completion

### 4. **Health-Checks** (WICHTIG)
**Warum:** Production Monitoring
**Was:**
- Database Connection Check
- Redis Connection Check
- RabbitMQ Connection Check
- Celery Worker Status

### 5. **Perplexity Functions** (OPTIONAL MVP)
**Warum:** Kosten-Optimierung + erweiterte Features
**Was:**
- model_selector.py integrieren (75% Cost Reduction)
- quick_threat_lookup.py verfügbar machen

---

## 📋 Detaillierte Schritte

### SCHRITT 1: Alembic Setup (10 min)

```bash
cd /home/cytrex/news-microservices/services/research-service

# Alembic initialisieren
alembic init alembic

# alembic.ini anpassen:
# sqlalchemy.url = postgresql://news_user:your_db_password@localhost:5432/news_mcp

# alembic/env.py anpassen:
# from app.models.research import Base
# target_metadata = Base.metadata
```

**Dateien:**
- `alembic.ini` (erstellen/anpassen)
- `alembic/env.py` (anpassen)

---

### SCHRITT 2: Models auf UUID umstellen (20 min)

**Datei:** `app/models/research.py`

**Änderungen:**
```python
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    # VORHER:
    # id = Column(Integer, primary_key=True, index=True)
    # user_id = Column(Integer, nullable=False, index=True)

    # NACHHER:
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Legacy Fields (NEU):
    legacy_feed_id = Column(Integer, nullable=True, index=True)
    legacy_article_id = Column(Integer, nullable=True, index=True)

    # Existierende UUID Fields behalten:
    feed_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    article_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    run_id = Column(PGUUID(as_uuid=True), ForeignKey("research_runs.id"), nullable=True)

# Gleiche Änderungen für:
# - ResearchTemplate
# - ResearchCache
# - ResearchRun
# - CostTracking
```

**Wichtig:** Alle Foreign Keys auch auf UUID umstellen!

---

### SCHRITT 3: Alembic Migration erstellen (5 min)

```bash
# Migration generieren
alembic revision --autogenerate -m "migrate_to_uuid_and_add_legacy_fields"

# Migration prüfen
cat alembic/versions/XXXX_migrate_to_uuid.py

# Falls Schema-Drop nötig (Development):
# Migration wird Integer → UUID konvertieren
# VORSICHT: Datenverlust bei bestehenden Daten!
```

**Wichtig:** Prüfen dass Migration korrekt ist!

---

### SCHRITT 4: API Layer anpassen (15 min)

**Datei:** `app/api/research.py`

**Änderungen:**
```python
from uuid import UUID

# Alle task_id Parameter sind bereits UUID ✅
# Nur sicherstellen dass legacy_* Parameter optional sind:

@router.post("/", response_model=ResearchTaskResponse)
async def create_research_task(
    task_data: ResearchTaskCreate,
    ...
):
    task = await research_service.create_research_task(
        db=db,
        user_id=current_user.user_id,  # String von JWT → UUID konvertieren
        query=task_data.query,
        ...
        feed_id=task_data.feed_id,
        legacy_feed_id=task_data.legacy_feed_id,  # Optional
        article_id=task_data.article_id,
        legacy_article_id=task_data.legacy_article_id,  # Optional
    )
```

**Wichtig:** `current_user.user_id` ist String aus JWT → zu UUID konvertieren!

---

### SCHRITT 5: Service Layer anpassen (15 min)

**Datei:** `app/services/research.py`

**Änderungen:**
```python
from uuid import UUID

async def create_research_task(
    self,
    db: Session,
    user_id: UUID,  # Parameter-Typ anpassen
    query: str,
    ...
) -> ResearchTask:
    # User ID validieren (String aus JWT → UUID)
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    # ... Rest bleibt gleich
```

**Wichtig:** Alle DB-Queries prüfen ob UUID-kompatibel!

---

### SCHRITT 6: Celery Aktivierung (20 min)

**Datei:** `app/services/research.py`

**Änderungen:**
```python
# VORHER (Zeile 652-680):
async def create_research_task(...):
    # ... Task erstellen
    db.add(task)
    db.commit()
    db.refresh(task)

    # ❌ Synchrone Ausführung:
    try:
        task.status = "processing"
        db.commit()
        result = await perplexity_client.research(...)
        task.status = "completed"
        ...
    except Exception as e:
        task.status = "failed"
        ...

    return task

# NACHHER:
async def create_research_task(...):
    # ... Task erstellen
    db.add(task)
    db.commit()
    db.refresh(task)

    # ✅ Celery Queue:
    from app.workers.tasks import research_task

    # Task in Queue stellen
    celery_result = research_task.delay(str(task.id))
    logger.info(f"Task {task.id} queued with Celery task {celery_result.id}")

    # Task sofort zurückgeben (Status: pending)
    return task
```

**Wichtig:** Worker verarbeitet async, API blockiert nicht!

**Event Publishing (in Celery Worker tasks.py bereits vorhanden):**
```python
# workers/tasks.py:113-129 bereits implementiert ✅
# Publiziert Event nach Completion
```

---

### SCHRITT 7: Health-Checks erweitern (15 min)

**Datei:** `app/main.py`

**Änderungen:**
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    from app.core.database import SessionLocal
    from app.workers.celery_app import celery_app
    import redis

    health_status = {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "checks": {}
    }

    # 1. Database Check
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # 2. Redis Check
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # 3. Celery Check
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            health_status["checks"]["celery"] = f"ok ({len(active_workers)} workers)"
        else:
            health_status["checks"]["celery"] = "no workers"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["celery"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # 4. Perplexity API Check
    perplexity_available = await perplexity_client.check_health()
    health_status["checks"]["perplexity_api"] = "ok" if perplexity_available else "unavailable"

    # TODO: RabbitMQ Check (optional)

    return health_status
```

---

### SCHRITT 8: Perplexity Functions Integration (OPTIONAL, 30 min)

**Option A: Minimale Integration (Quick Win)**
```bash
# Kopiere nur model_selector
cp /path/to/model_selector.py app/services/perplexity/

# In research.py integrieren:
from app.services.perplexity.model_selector import select_optimal_model

async def create_research_task(...):
    # Auto-select model based on query
    if optimize_cost:
        optimal_model = select_optimal_model(
            query=query,
            user_tier=depth,
            function_name=None  # Auto-detect
        )
        model_name = optimal_model
```

**Option B: Vollständige Integration (later)**
- Alle Functions aus /userdocs/perplexity/ kopieren
- Research Functions Registry erstellen
- API Endpoints für specialized research

**Empfehlung:** Option A für MVP, Option B später

---

## 🔧 Ausführungsreihenfolge (SEQUENTIELL!)

```bash
# 1. Alembic Setup
cd /home/cytrex/news-microservices/services/research-service
alembic init alembic
# Edit alembic.ini + alembic/env.py

# 2. Models anpassen
# Edit app/models/research.py (UUID + Legacy Fields)

# 3. Migration erstellen
alembic revision --autogenerate -m "migrate_to_uuid_and_add_legacy_fields"

# 4. Migration PREVIEW (NICHT ausführen bis Code fertig!)
# alembic upgrade head  # SPÄTER!

# 5. API Layer anpassen
# Edit app/api/research.py

# 6. Service Layer anpassen
# Edit app/services/research.py (UUID + Celery)

# 7. Health-Checks erweitern
# Edit app/main.py

# 8. JETZT Migration ausführen
alembic upgrade head

# 9. Service starten
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

# 10. Celery Worker starten (separates Terminal)
celery -A app.workers.celery_app worker --loglevel=info -Q research,research_scheduled,maintenance,health

# 11. Testen
curl http://localhost:8003/health
curl -X POST http://localhost:8003/api/v1/research \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"query": "Test research", "model_name": "sonar", "depth": "quick"}'
```

---

## ⚠️ Kritische Punkte

### 1. User ID Konvertierung
```python
# JWT gibt String, DB braucht UUID
from uuid import UUID

# In auth.py:
class CurrentUser:
    user_id: str  # JWT sub claim

# In Service:
user_uuid = UUID(current_user.user_id)
```

### 2. Migration Datenverlust
```
⚠️ ACHTUNG: Integer → UUID Migration löscht existierende Daten!

Lösung für Production:
1. Backup: pg_dump
2. Dual-Write Phase: Integer + UUID parallel
3. Data Migration Script
4. Switch to UUID
5. Remove Integer

Für Development:
- Einfach neu erstellen (keine Daten)
```

### 3. Celery Worker MUSS laufen
```bash
# Start Worker BEVOR Service genutzt wird!
celery -A app.workers.celery_app worker --loglevel=info

# Ohne Worker:
# - Tasks bleiben in Queue
# - Status bleibt "pending"
# - Keine Completion
```

---

## 🧪 Validierung

### Test 1: Health-Check
```bash
curl http://localhost:8003/health

# Erwartete Response:
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok (1 workers)",
    "perplexity_api": "ok"
  }
}
```

### Test 2: Research Task erstellen
```bash
# 1. JWT Token holen (vom Auth Service)
TOKEN="eyJhbGc..."

# 2. Research Task erstellen
curl -X POST http://localhost:8003/api/v1/research \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest AI developments",
    "model_name": "sonar",
    "depth": "quick"
  }'

# Erwartete Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",  # Wird zu "completed" durch Worker
  "query": "Latest AI developments",
  ...
}

# 3. Task Status prüfen (nach 5-10 Sekunden)
curl http://localhost:8003/api/v1/research/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"

# Erwartete Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",  # Worker hat verarbeitet ✅
  "result": { ... },
  "cost": 0.001,
  ...
}
```

### Test 3: Celery Worker Logs
```bash
# Worker Terminal:
[INFO] Task research.research_task[abc-123] received
[INFO] Starting research task 550e8400-...
[INFO] Research task 550e8400-... completed successfully
[INFO] Task research.research_task[abc-123] succeeded in 3.2s
```

---

## 📊 Erfolgs-Metriken

- ✅ Health-Check zeigt alle "ok"
- ✅ Research Task wird erstellt (Status: pending)
- ✅ Celery Worker verarbeitet Task
- ✅ Task Status wechselt zu "completed"
- ✅ Result enthält Perplexity Response
- ✅ Cost Tracking funktioniert
- ✅ Keine Errors in Logs

---

## 🚀 Nach Implementation

1. **Docker Integration**
   - Dockerfile.dev für hot-reload
   - docker-compose.yml Integration
   - Celery Worker als separater Container

2. **Tests**
   - Integration Tests (API → Celery → Perplexity)
   - Unit Tests (Models, Services)
   - Health-Check Tests

3. **Documentation**
   - API Endpoints dokumentieren
   - Deployment Guide
   - Troubleshooting

4. **Monitoring**
   - Celery Flower Dashboard
   - Cost Tracking Dashboard
   - Error Alerting

---

## 📝 Dateien die geändert werden

```
services/research-service/
├── alembic/                          [NEU]
│   ├── env.py                       [ERSTELLEN]
│   └── versions/
│       └── XXXX_migrate_to_uuid.py  [AUTO-GENERIERT]
├── alembic.ini                      [ERSTELLEN]
├── app/
│   ├── models/
│   │   └── research.py              [UUID + Legacy Fields]
│   ├── api/
│   │   └── research.py              [UUID Handling]
│   ├── services/
│   │   ├── research.py              [Celery Integration]
│   │   └── perplexity/
│   │       └── model_selector.py    [OPTIONAL: KOPIEREN]
│   └── main.py                      [Health-Checks]
└── IMPLEMENTATION_PLAN.md           [DIESES DOKUMENT]
```

---

**Bereit zur Ausführung!** 🎯

Alle Informationen gesammelt, alle Abhängigkeiten geprüft, alle Blocker identifiziert.

**Nächster Schritt:** Ausführung starten mit Schritt 1 (Alembic Setup)

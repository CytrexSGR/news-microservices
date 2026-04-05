# Knowledge Graph - Gap Analysis & Implementation Status

**Date:** 2025-10-24
**Status:** Ready for Implementation Phase 1

---

## Executive Summary

**Situation:** Wir haben vollständige Konzepte und die Daten-Extraktion ist komplett, aber der eigentliche Knowledge Graph Service existiert noch nicht.

**Was läuft:**
- ✅ Content-Analysis extrahiert Relationships (100%)
- ✅ 5.295 Relationships in PostgreSQL gespeichert
- ✅ Test-Suite bereit (100%)

**Was fehlt:**
- ❌ Separater Knowledge Graph Service (0%)
- ❌ Neo4j Integration (0%)
- ❌ Graph Query API (0%)

**Implementierungsaufwand:** 2-3 Wochen (3 Phasen)

---

## 📊 Status Matrix

| Komponente | Konzept | Implementierung | Tests | Doku | Status |
|-----------|---------|----------------|-------|------|--------|
| **Data Extraction** | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** |
| **Knowledge Graph Service** | ✅ 100% | ❌ 0% | ❌ 0% | ✅ 100% | **NOT STARTED** |
| **Neo4j Setup** | ✅ 100% | ❌ 0% | - | ✅ 100% | **NOT STARTED** |
| **Event Consumer** | ✅ 100% | ❌ 0% | ❌ 0% | ✅ 100% | **NOT STARTED** |
| **Query API** | ✅ 100% | ❌ 0% | ❌ 0% | ✅ 100% | **NOT STARTED** |
| **Agent Integration** | ✅ 100% | ❌ 0% | ❌ 0% | ✅ 100% | **NOT STARTED** |

---

## ✅ Was IST implementiert (Content-Analysis Integration)

### 1. Relationship Extraction Pipeline ✅
**Location:** `services/content-analysis-service/`

**Funktionen:**
- Entity Extraction mit 15 Entity-Types
- Relationship Extraction mit 32 Relationship-Types
- Confidence-Scoring (0.0-1.0)
- Evidence-Tracking
- Validation mit Graceful Fallbacks
- JSON Repair (3-Tier Strategy)

**Datenspeicherung:**
- PostgreSQL: `analysis_results` table
- JSONB Felder: `extracted_relationships`, `relationship_metadata`
- 5.295 Relationships aktuell in Datenbank

**Qualität:**
- 100% Test Success Rate (18/18 Artikel)
- Robust gegen LLM-Fehler
- Production-Ready

### 2. Test Suite ✅
**Location:** `tests/knowledge-graph/`

**Komponenten:**
- 18 Test-Artikel mit Ground Truth
- 4 Automatisierungs-Scripts
- HTML Report Generator
- Prometheus Metrics Validator

**Problem:** Blockiert durch fehlenden Test-Endpoint (~10 Min Fix)

### 3. Dokumentation ✅
**Files:**
- `docs/services/knowledge-graph-service-concept.md` - Vollständiges Konzept
- `docs/guides/KNOWLEDGE-GRAPH-IMPLEMENTATION-PLAN.md` - Implementation Guide
- `tests/knowledge-graph/IMPLEMENTATION_SUMMARY.md` - Status-Bericht

---

## ❌ Was NICHT implementiert ist (Knowledge Graph Service)

### 1. Neo4j Database Setup ❌
**Gap:** Keine Neo4j Instanz im Docker-Setup

**Was fehlt:**
```yaml
# docker-compose.yml
neo4j:
  image: neo4j:5.25-community
  ports:
    - "7474:7474"  # Browser
    - "7687:7687"  # Bolt
  environment:
    NEO4J_AUTH: neo4j/password
  volumes:
    - neo4j_data:/data
```

**Aufwand:** 30 Minuten

---

### 2. Knowledge Graph Service (Microservice) ❌
**Gap:** Kein separater Service existiert

**Was fehlt:**
```
services/knowledge-graph-service/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── api/routes/
│   │   ├── graph.py           # Query endpoints
│   │   └── health.py          # Health check
│   ├── consumers/
│   │   └── relationships_consumer.py  # RabbitMQ consumer
│   ├── services/
│   │   ├── neo4j_service.py   # Neo4j connection
│   │   ├── ingestion_service.py  # Triplet ingestion
│   │   └── query_service.py   # Graph queries
│   └── models/
│       ├── graph.py           # Node/Relationship models
│       ├── requests.py        # API requests
│       └── responses.py       # API responses
├── tests/
├── Dockerfile
├── requirements.txt
└── .env
```

**Aufwand:** 1-2 Wochen (Phase 1-2)

---

### 3. Event Integration ❌
**Gap:** Content-Analysis publiziert keine `relationships.extracted` Events

**Was fehlt:**

**A) Event Publishing (Content-Analysis):**
```python
# services/content-analysis-service/app/services/analysis_service.py
# Nach Relationship-Validation:

if valid_rels:
    # Publish to RabbitMQ
    event = {
        "event_type": "relationships.extracted",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "article_id": item_id,
            "source_url": source_url,
            "triplets": [
                {
                    "subject": {"text": r["entity1"], "type": "..."},
                    "relationship": {"type": r["relationship_type"], "confidence": r["confidence"]},
                    "object": {"text": r["entity2"], "type": "..."}
                }
                for r in valid_rels
            ]
        }
    }
    await rabbitmq.publish("news.events", "relationships.extracted", event)
```

**B) Event Consumption (Knowledge-Graph-Service):**
```python
# services/knowledge-graph-service/app/consumers/relationships_consumer.py

class RelationshipsConsumer:
    async def handle_message(self, message):
        event = RelationshipsExtractedEvent.parse_raw(message.body)

        # Ingest to Neo4j
        await self.neo4j_service.ingest_triplets(
            triplets=event.payload.triplets,
            article_id=event.payload.article_id,
            source_url=event.payload.source_url
        )
```

**Aufwand:** 3-4 Stunden

---

### 4. Neo4j Ingestion Logic ❌
**Gap:** Keine MERGE-Queries zum Speichern in Neo4j

**Was fehlt:**
```python
# services/knowledge-graph-service/app/services/ingestion_service.py

class Neo4jIngestionService:
    async def ingest_triplets(self, triplets, article_id, source_url):
        async with self.driver.session() as session:
            for triplet in triplets:
                # Idempotent MERGE query
                await session.run("""
                    MERGE (subject:{label} {name: $subject_name})
                    ON CREATE SET subject.created_at = datetime()
                    ON MATCH SET subject.last_seen = datetime()

                    MERGE (object:{label} {name: $object_name})
                    ON CREATE SET object.created_at = datetime()
                    ON MATCH SET object.last_seen = datetime()

                    MERGE (subject)-[rel:{relationship}]->(object)
                    ON CREATE SET rel.confidence = $confidence, rel.mention_count = 1
                    ON MATCH SET rel.mention_count = rel.mention_count + 1

                    RETURN subject, rel, object
                """, parameters={...})
```

**Aufwand:** 1 Tag

---

### 5. Query API ❌
**Gap:** Keine REST API für Graph-Queries

**Was fehlt:**

**Endpoint 1: Entity Connections**
```python
@router.get("/api/v1/graph/entity/{entity_name}/connections")
async def get_entity_connections(
    entity_name: str,
    relationship_type: Optional[str] = None,
    limit: int = 100,
    user_id: str = Depends(get_current_user_id)
):
    # Query Neo4j
    cypher = """
        MATCH (e {name: $entity_name})-[r]->(connected)
        WHERE r.confidence >= 0.5
        RETURN connected, r
        LIMIT $limit
    """
    results = await neo4j.run(cypher, {"entity_name": entity_name, "limit": limit})

    return {
        "entity": {...},
        "connections": [...]
    }
```

**Endpoint 2: Custom Cypher**
```python
@router.post("/api/v1/graph/query")
async def execute_cypher(
    request: CypherQueryRequest,
    user_id: str = Depends(get_current_user_id)
):
    # Validate query (block DELETE, DROP)
    validate_query_safety(request.query)

    # Execute
    results = await neo4j.run(request.query, request.parameters)

    return {
        "columns": [...],
        "records": [...]
    }
```

**Aufwand:** 2-3 Tage

---

### 6. Agent Integration ❌
**Gap:** LLM-Orchestrator kennt keine Graph-Tools

**Was fehlt:**

**Tool Definition (Agent-Service):**
```python
# services/agent-service/app/core/tool_registry.py

{
    "type": "function",
    "function": {
        "name": "query_knowledge_graph",
        "description": "Query the knowledge graph for entity relationships",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity to query"},
                "relationship_type": {"type": "string", "description": "Optional relationship filter"}
            },
            "required": ["entity_name"]
        }
    }
}
```

**Tool Execution:**
```python
async def _query_knowledge_graph(self, arguments, user_token):
    url = f"{settings.KNOWLEDGE_GRAPH_SERVICE_URL}/api/v1/graph/entity/{arguments['entity_name']}/connections"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {user_token}"},
            params={"relationship_type": arguments.get("relationship_type")}
        )
        return response.json()
```

**Aufwand:** 1 Tag

---

## 📋 Implementierungs-Phasen

### Phase 1: MVP (Woche 1 - 5 Tage)
**Ziel:** Minimales System funktionsfähig

**Tasks:**
1. ✅ Neo4j Container Setup (30 Min)
   - docker-compose.yml erweitern
   - Test-Verbindung

2. ✅ Knowledge Graph Service Grundgerüst (1 Tag)
   - FastAPI App
   - Config & Dependencies
   - Health Check Endpoint
   - Docker Integration

3. ✅ Neo4j Connection Service (3 Std)
   - Driver Setup
   - Connection Pool
   - Basic Cypher Execution

4. ✅ Ingestion Service (1 Tag)
   - MERGE Query Implementation
   - Idempotenz-Tests
   - Error Handling

5. ✅ Basic GET Endpoint (3 Std)
   - `/api/v1/graph/entity/{name}/connections`
   - Simple 1-hop queries
   - JSON Response

**Deliverable:** Service kann Daten in Neo4j schreiben und basic Queries ausführen

---

### Phase 2: Event Integration (Woche 2 - 3 Tage)
**Ziel:** Automatische Synchronisierung via RabbitMQ

**Tasks:**
1. ✅ Event Schema Definition (1 Std)
   - Pydantic Models für `relationships.extracted`

2. ✅ RabbitMQ Consumer (1 Tag)
   - Consume Logic
   - Error Handling & Retries
   - Message ACK/NACK

3. ✅ Event Publisher (Content-Analysis) (3 Std)
   - Publish nach Validation
   - Event Format

4. ✅ End-to-End Test (1 Tag)
   - Artikel analysieren
   - Event publizieren
   - Neo4j Query verifizieren

**Deliverable:** Content-Analysis → Event → Neo4j Pipeline funktioniert

---

### Phase 3: Advanced Features (Woche 3 - 2 Tage)
**Ziel:** Production-Ready & Agent Integration

**Tasks:**
1. ✅ POST /graph/query Endpoint (1 Tag)
   - Custom Cypher Execution
   - Query Validation (Security)
   - Rate Limiting

2. ✅ Agent Integration (1 Tag)
   - Tool Definition
   - Tool Execution
   - Error Handling

3. ✅ Monitoring & Metrics (3 Std)
   - Prometheus Metrics
   - Health Checks
   - Logging

4. ✅ Documentation (2 Std)
   - API Docs
   - Usage Examples
   - Troubleshooting Guide

**Deliverable:** Production-Ready Service mit Agent Integration

---

## 🎯 Empfohlene Reihenfolge

### Schnellster Weg zu funktionierendem System:

**Tag 1-2:** Phase 1 MVP
- Neo4j Setup
- Service Grundgerüst
- Ingestion Logic

**Tag 3-4:** Phase 2 Events
- RabbitMQ Integration
- End-to-End Pipeline

**Tag 5:** Phase 3 Agent
- Graph Query Tool
- Agent Integration

**Total:** 1 Woche intensiv (oder 2 Wochen normal)

---

## 💰 Kosten-Schätzung

### Infrastruktur
- **Neo4j Community:** Kostenlos
- **RabbitMQ:** Bereits vorhanden
- **Docker Resources:** +512MB RAM, +1GB Disk

### Development
- **Phase 1:** 5 Arbeitstage
- **Phase 2:** 3 Arbeitstage
- **Phase 3:** 2 Arbeitstage

**Total:** 10 Arbeitstage (2 Wochen @ 50% capacity)

---

## 🚨 Risiken & Mitigation

### Risiko 1: Neo4j Performance
**Problem:** 5.295 Relationships → Kann Neo4j Community das handeln?

**Mitigation:**
- Community Edition unterstützt Millionen Nodes
- Indexing auf Entity Names (UNIQUE constraints)
- Connection Pooling (max 50 connections)

**Likelihood:** LOW

---

### Risiko 2: Event Ordering
**Problem:** Events können out-of-order ankommen

**Mitigation:**
- MERGE ist idempotent (kann mehrfach ausgeführt werden)
- mention_count tracking für Duplikate
- last_seen Timestamp

**Likelihood:** MEDIUM (aber handled)

---

### Risiko 3: Query Complexity
**Problem:** Unbounded Queries können Neo4j lahmlegen

**Mitigation:**
- Query Timeout (30s default)
- LIMIT clause enforcement
- Block unbounded paths `[*]`
- Rate Limiting (10 queries/minute)

**Likelihood:** MEDIUM (aber preventable)

---

## 📦 Dependencies

### New Python Packages
```toml
# knowledge-graph-service/pyproject.toml

neo4j = "^5.25.0"           # Official Neo4j driver
aio-pika = "^9.4.0"         # Already used in other services
tenacity = "^9.0.0"         # Retry logic
```

### Docker Images
```yaml
neo4j:5.25-community        # ~550MB
```

---

## 🔄 Migration Path

### Existing Data (5.295 Relationships)
**Problem:** Wie kommen die in Neo4j?

**Solution:** One-time Backfill Script
```python
# scripts/backfill_neo4j.py

# 1. Read from PostgreSQL
rows = db.execute("""
    SELECT
        article_id,
        extracted_relationships,
        relationship_metadata
    FROM analysis_results
    WHERE extracted_relationships IS NOT NULL
""")

# 2. Transform to events
for row in rows:
    event = create_event_from_row(row)
    await ingestion_service.ingest_triplets(event)

# 3. Verify
print(f"Migrated {count} articles with {relationship_count} relationships")
```

**Aufwand:** 2-3 Stunden (inkl. Testing)

---

## ✅ Next Steps

**Option A: Full Implementation (2 Wochen)**
1. Setup Neo4j (30 Min)
2. Implement Phase 1 MVP (1 Woche)
3. Implement Phase 2 Events (3 Tage)
4. Implement Phase 3 Agent (2 Tage)

**Option B: Quick Proof-of-Concept (1 Tag)**
1. Setup Neo4j (30 Min)
2. Basic Service + Ingestion (4 Std)
3. Manual Data Insert (2 Std)
4. Simple Query Test (1 Std)

**Option C: Staged Rollout (3 Wochen)**
1. Week 1: MVP ohne Events (manually test)
2. Week 2: Event Integration (auto sync)
3. Week 3: Agent Integration (production)

---

## 🤔 Frage an dich

Welchen Ansatz möchtest du?

**A) Full Implementation starten** → 2 Wochen, Production-Ready
**B) Quick PoC first** → 1 Tag, dann entscheiden
**C) Staged Rollout** → 3 Wochen, risk-averse

Oder soll ich eine andere Priorisierung machen?

---

**Last Updated:** 2025-10-24
**Status:** Bereit für Phase 1 Implementation
**Blocker:** Keine - Alle Dependencies vorhanden

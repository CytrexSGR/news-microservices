# OSS Service (Ontology Suggestion System)

**Service Type:** Analysis & Learning System
**Port:** 8110
**Status:** ✅ Production Ready
**Added:** 2025-11-10
**Last Updated:** 2025-12-27

---

## Purpose

The OSS (Ontology Suggestion System) analyzes the Neo4j knowledge graph to detect patterns and data quality issues, then generates ontology change proposals for human review or automatic implementation.

## Key Responsibilities

### 1. Pattern Detection
- Identifies recurring entity type patterns (PERSON, ORGANIZATION, LOCATION, etc.)
- Finds relationship patterns for semantic connections
- Calculates confidence scores based on frequency and consistency
- Generates NEW_ENTITY_TYPE proposals for well-established patterns

### 2. Inconsistency Detection
- **ISO 3166-1 Violations:** Invalid country codes (not 2-letter uppercase)
- **Duplicate Entities:** Same entity_id across multiple nodes
- **Missing Properties:** Entities lacking required properties (entity_id, entity_type, name)
- **UNKNOWN Entity Types:** Entities with unclassified types
- **Article UUID Garbage:** Metadata artifacts incorrectly stored as entities

### 3. Proposal Generation
- Creates detailed proposals with evidence samples
- Provides impact analysis and effort estimates
- Calculates confidence scores (0.0 - 1.0)
- Submits to Ontology Proposals Service (port 8109)

### 4. Automatic Scheduling
- Runs analysis every hour via APScheduler
- Configurable interval (default: 3600 seconds)
- Non-blocking background execution
- Deduplication prevents duplicate proposals

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      OSS Service (8110)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  APScheduler    │───▶│  Analysis Cycle                 │ │
│  │  (hourly)       │    │  ┌───────────────────────────┐  │ │
│  └─────────────────┘    │  │  Pattern Detector         │  │ │
│                         │  │  - Entity type frequency  │  │ │
│  ┌─────────────────┐    │  │  - Relationship patterns  │  │ │
│  │  Manual Trigger │───▶│  └───────────────────────────┘  │ │
│  │  POST /analyze  │    │  ┌───────────────────────────┐  │ │
│  └─────────────────┘    │  │  Inconsistency Detector   │  │ │
│                         │  │  - ISO violations         │  │ │
│                         │  │  - Duplicates             │  │ │
│                         │  │  - Missing properties     │  │ │
│                         │  │  - UNKNOWN types          │  │ │
│                         │  │  - Article UUID garbage   │  │ │
│                         │  └───────────────────────────┘  │ │
│                         └─────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                │ HTTP POST
                                ▼
                    ┌───────────────────────┐
                    │  Neo4j Knowledge      │◀──── Source Data
                    │  Graph (7687)         │
                    └───────────────────────┘
                                │
                                │ Proposals
                                ▼
                    ┌───────────────────────┐
                    │  Ontology Proposals   │───▶ Manual Review
                    │  Service (8109)       │     OR Auto-Approval
                    └───────────────────────┘
```

---

## Detection Methods

### 1. Entity Type Pattern Detection

Detects frequently occurring entity types in the knowledge graph.

```cypher
MATCH (n:Entity)
WHERE n.entity_type IS NOT NULL
RETURN n.entity_type AS type, count(*) AS count
ORDER BY count DESC
```

**Thresholds:**
- Minimum occurrences: 10 (configurable)
- Confidence: Based on frequency relative to total

### 2. ISO Country Code Violations

Detects Country entities with invalid ISO 3166-1 alpha-2 codes.

```cypher
MATCH (c)
WHERE (c.entity_type = 'COUNTRY' OR 'Country' IN labels(c))
  AND (size(c.entity_id) <> 2 OR c.entity_id =~ '.*[^A-Z].*')
RETURN c.entity_id, c.name
```

**Valid Examples:** `US`, `DE`, `FR`
**Invalid Examples:** `USA`, `germany`, `123`

### 3. Duplicate Entity Detection

Finds entities sharing the same entity_id.

```cypher
MATCH (n)
WHERE n.entity_id IS NOT NULL
WITH n.entity_id AS id, collect(n) AS nodes
WHERE size(nodes) > 1
RETURN id, size(nodes) AS duplicate_count
```

### 4. Missing Required Properties

Detects Entity nodes lacking required properties.

```cypher
MATCH (e:Entity)
WHERE e.entity_id IS NULL OR e.entity_type IS NULL OR e.name IS NULL
  AND NOT 'Article' IN labels(e)  -- Exclude metadata
RETURN id(e), e.name, e.entity_type
```

### 5. UNKNOWN Entity Type Detection

Identifies entities with unclassified types needing reclassification.

```cypher
MATCH (e:Entity)
WHERE e.entity_type = 'UNKNOWN'
RETURN count(e), collect(e.name)[0..10]
```

### 6. Article UUID Garbage Detection

**IMPORTANT:** Excludes legitimate legal document references.

```cypher
MATCH (e:Entity)
WHERE e.entity_type = 'ARTICLE'
   OR (e.name STARTS WITH 'Article '
       AND e.name =~ 'Article [0-9a-f]{8}-[0-9a-f]{4}-.*')  -- UUID pattern only
RETURN count(*), collect(e.name)[0..5]
```

**Correctly Detected (Garbage):**
- `Article a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- Entity with `entity_type = 'ARTICLE'`

**Correctly Excluded (Legitimate):**
- `Article 370` (Indian Constitution)
- `Article 146 of the Fourth Geneva Convention`
- `Article 18 of the Rome Statute`

---

## Proposal Types

### FLAG_INCONSISTENCY

Data quality issues that should be fixed.

| Issue Type | Severity | Confidence | Auto-Approvable |
|------------|----------|------------|-----------------|
| ISO violations | HIGH | 95%+ | ✅ Yes |
| UNKNOWN entities | HIGH | 95%+ | ✅ Yes |
| Article UUID garbage | HIGH | 95%+ | ✅ Yes |
| Missing properties | MEDIUM | 95%+ | ✅ Yes |
| Duplicate entities | HIGH | 95%+ | ✅ Yes |

### NEW_ENTITY_TYPE

Patterns suggesting new entity types should be added to ontology.

| Pattern | Threshold | Confidence | Auto-Approvable |
|---------|-----------|------------|-----------------|
| Entity type frequency | 100+ occurrences | 98%+ | ✅ Yes |

---

## API Endpoints

### POST /api/v1/analysis/run

Triggers a manual analysis cycle.

**Response:**
```json
{
  "cycle_id": "cycle_20251227_150607_0bc8875d",
  "started_at": "2025-12-27T15:06:07.071355",
  "completed_at": "2025-12-27T15:06:07.727456",
  "patterns_detected": 13,
  "inconsistencies_detected": 4,
  "proposals_generated": 17,
  "duplicates_skipped": 0,
  "proposals_submitted": 17,
  "errors": [],
  "warnings": [],
  "proposals": [...]
}
```

### GET /api/v1/analysis/status

Returns service status and last analysis results.

### GET /api/v1/analysis/queue/status

Returns deduplication queue status.

### POST /api/v1/analysis/queue/clear

Clears the deduplication queue (allows re-proposing).

### GET /health

Health check endpoint.

```json
{
  "status": "healthy",
  "service": "OSS Service",
  "version": "1.0.0",
  "timestamp": "2025-12-27T15:06:01.007285",
  "neo4j": "connected",
  "proposals_api": "http://ontology-proposals-service:8109"
}
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_PORT` | 8110 | Service port |
| `ANALYSIS_INTERVAL_SECONDS` | 3600 | Analysis frequency (hourly) |
| `MIN_PATTERN_OCCURRENCES` | 10 | Minimum occurrences for patterns |
| `CONFIDENCE_THRESHOLD` | 0.7 | Minimum confidence for proposals |
| `NEO4J_URI` | bolt://neo4j:7687 | Neo4j connection |
| `NEO4J_USER` | neo4j | Neo4j username |
| `NEO4J_PASSWORD` | - | Neo4j password |
| `PROPOSALS_API_URL` | http://ontology-proposals-service:8109 | Target API |

---

## Integration with Auto-Approval

The Scheduler Service (port 8108) includes a Proposal Auto-Approver that automatically approves and implements high-confidence OSS proposals.

**Auto-Approval Rules:**

| Change Type | Min Confidence | Min Occurrences | Title Patterns |
|-------------|----------------|-----------------|----------------|
| FLAG_INCONSISTENCY | 95% | 1 | ISO, UNKNOWN, Article UUID, missing properties, Duplicate |
| NEW_ENTITY_TYPE | 98% | 100 | Any |

See: [ADR-047: Ontology Auto-Approval Rules](../decisions/ADR-047-ontology-auto-approval-rules.md)

---

## Monitoring

### Key Metrics

- Patterns detected per cycle
- Inconsistencies found per cycle
- Proposals generated per cycle
- Proposals submitted vs duplicates skipped
- Analysis cycle duration
- Neo4j query latency

### Logs to Watch

```bash
# Analysis cycle logs
docker logs -f news-oss-service 2>&1 | grep -E "(cycle|proposal|ERROR)"

# Detection-specific logs
docker logs -f news-oss-service 2>&1 | grep -E "(ISO|UNKNOWN|ARTICLE|duplicate)"
```

### Health Check

```bash
curl http://localhost:8110/health | jq
```

---

## Performance

| Metric | Value |
|--------|-------|
| Analysis Duration | 200-700ms (depends on graph size) |
| Automatic Frequency | Every 60 minutes |
| Memory Usage | 50-150 MB |
| CPU Usage | < 5% average, spikes during analysis |
| Neo4j Queries | 10-15 per cycle |

---

## Known Issues

### Resolved

1. **Article UUID False Positives** (2025-12-27) ✅
   - Detection incorrectly matched legal documents like "Article 370"
   - Fixed: Query now uses UUID pattern matching
   - See: [POSTMORTEMS.md - Incident #30](../../POSTMORTEMS.md)

### Current

None.

---

## Troubleshooting

### OSS Not Generating Proposals

1. Check Neo4j connection:
   ```bash
   curl http://localhost:8110/health | jq '.neo4j'
   ```

2. Check if proposals API is reachable:
   ```bash
   curl http://localhost:8109/health
   ```

3. Trigger manual analysis:
   ```bash
   curl -X POST http://localhost:8110/api/v1/analysis/run | jq
   ```

### Duplicate Proposals Being Skipped

The deduplication queue prevents duplicate proposals. To reset:

```bash
curl -X POST http://localhost:8110/api/v1/analysis/queue/clear
```

### False Positives in Detection

1. Review evidence samples in proposal
2. Check detection query in `inconsistency_detector.py`
3. Add exclusion patterns if needed
4. Reject false-positive proposals via API

---

## File Structure

```
services/oss-service/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration
│   ├── database.py                # Neo4j connection
│   ├── models/
│   │   └── proposal.py            # Proposal models
│   ├── analyzers/
│   │   ├── pattern_detector.py    # Pattern detection
│   │   └── inconsistency_detector.py  # Inconsistency detection
│   └── services/
│       ├── analysis_service.py    # Analysis orchestration
│       └── proposal_submitter.py  # Proposal submission
├── Dockerfile.dev
└── requirements.txt
```

---

## Related Documentation

- **Service README:** `/services/oss-service/README.md`
- **API Documentation:** `/docs/api/oss-service-api.md`
- **OSS Specification:** `/home/cytrex/userdocs/system-ontology/07_OSS_SPECIFICATION.md`
- **Ontology Proposals Service:** `/docs/services/ontology-proposals-service.md`
- **Auto-Approval ADR:** `/docs/decisions/ADR-047-ontology-auto-approval-rules.md`
- **Incident #30:** `/POSTMORTEMS.md` (Article UUID False Positives)

---

**Maintainer:** System
**Last Updated:** 2025-12-27

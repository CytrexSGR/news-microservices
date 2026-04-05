# OSS Service - Ontology Suggestion System

**Version:** 1.0.0
**Port:** 8110
**Status:** ✅ Production Ready

---

## Overview

The **OSS (Ontology Suggestion System)** is a learning system that analyzes the Neo4j knowledge graph to detect patterns and inconsistencies, then generates ontology change proposals for human review.

**Key Features:**
- 🔍 **Pattern Detection** - Identifies recurring patterns suggesting new entity/relationship types
- 🚨 **Inconsistency Detection** - Finds data quality issues (invalid ISO codes, duplicates, missing properties)
- 📝 **Proposal Generation** - Creates detailed proposals with evidence and impact analysis
- 🔄 **API Integration** - Submits proposals to Ontology Proposals Service (Port 8109)
- ⏰ **Automatic Scheduling** - APScheduler runs analysis every hour (configurable)
- 🧠 **Self-Learning** - Improves confidence calculations based on approval patterns

---

## Architecture

```
Neo4j Knowledge Graph
        ↓ (analyzes)
   OSS Service (8110)
   ├── Pattern Detector
   │   ├── Entity patterns
   │   └── Relationship patterns
   ├── Inconsistency Detector
   │   ├── ISO code violations
   │   ├── Duplicate entities
   │   └── Missing properties
   └── Proposal Generator
        ↓ (POST proposals)
Ontology Proposals API (8109)
        ↓ (stores)
    PostgreSQL
        ↓ (reviewed via)
   Dashboard UI
```

---

## API Endpoints

### Analysis Operations

#### `POST /api/v1/analysis/run`
Trigger an analysis cycle manually.

**Response:**
```json
{
  "cycle_id": "cycle_20251110_143022_abc123",
  "started_at": "2025-11-10T14:30:22Z",
  "completed_at": "2025-11-10T14:30:45Z",
  "patterns_detected": 5,
  "inconsistencies_detected": 3,
  "proposals_generated": 8,
  "proposals_submitted": 8,
  "errors": [],
  "warnings": [],
  "proposals": [...]
}
```

#### `GET /api/v1/analysis/status`
Get service status and configuration.

**Response:**
```json
{
  "service": "OSS Service",
  "version": "1.0.0",
  "status": "operational",
  "neo4j_connected": true,
  "proposals_api": "http://ontology-proposals-service:8109",
  "analysis_interval_seconds": 3600,
  "min_pattern_occurrences": 10,
  "confidence_threshold": 0.7
}
```

### Health Check

#### `GET /health`
Service health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "OSS Service",
  "version": "1.0.0",
  "timestamp": "2025-11-10T14:30:22Z",
  "neo4j": "connected",
  "proposals_api": "http://ontology-proposals-service:8109"
}
```

---

## Configuration

Environment variables (all optional with defaults):

```bash
# Application
APP_NAME="OSS Service"
DEBUG=true
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8110

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=news_graph_2024
NEO4J_DATABASE=neo4j

# Ontology Proposals API
PROPOSALS_API_URL=http://ontology-proposals-service:8109

# Analysis Configuration
ANALYSIS_INTERVAL_SECONDS=3600  # 1 hour (3600s)
MIN_PATTERN_OCCURRENCES=10
CONFIDENCE_THRESHOLD=0.7

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
```

---

## Automatic Scheduling

**Status:** ✅ Implemented (2025-11-11)

OSS uses **APScheduler** to run analysis cycles automatically at configured intervals.

### How It Works

1. **Startup:** Scheduler starts when service starts (see `lifespan` in `main.py`)
2. **Interval:** Runs every `ANALYSIS_INTERVAL_SECONDS` (default: 3600s = 1 hour)
3. **Job Function:** `scheduled_analysis_job()` calls `run_analysis_cycle()`
4. **Shutdown:** Scheduler stops gracefully when service stops

### Configuration

Change interval via environment variable:

```yaml
# docker-compose.yml
oss-service:
  environment:
    - ANALYSIS_INTERVAL_SECONDS=1800  # 30 minutes
```

Or for testing (5 minutes):

```yaml
- ANALYSIS_INTERVAL_SECONDS=300  # 5 minutes
```

### Monitoring Scheduled Runs

```bash
# Watch logs for scheduled runs
docker logs -f oss-service 2>&1 | grep "scheduled"

# Example output:
# 2025-11-11 08:21:34 - app.main - INFO - Running scheduled OSS analysis cycle
# 2025-11-11 08:21:45 - app.main - INFO - Scheduled analysis completed: 6 proposals generated, 6 proposals submitted
```

### Manual Trigger (Still Available)

You can still trigger analysis manually via API:

```bash
curl -X POST http://localhost:8110/api/v1/analysis/run
```

This does NOT affect the scheduler - it continues running on schedule.

---

## Pattern Detection

### Entity Type Patterns

Detects when a specific entity pattern occurs frequently:

```cypher
// Example: Find untyped nodes with type property
MATCH (n)
WHERE NOT n:Entity AND n.type IS NOT NULL
WITH n.type AS type, count(*) AS count
WHERE count >= 10
RETURN type, count
```

**Proposal Example:**
- **Title:** "New entity type: CyberActorGroup"
- **Evidence:** 47 nodes with type "CYBER_ACTOR"
- **Confidence:** 0.92
- **Impact:** 47 entities need migration

### Relationship Type Patterns

Detects when nodes frequently co-occur via generic relationships:

```cypher
// Example: Find common MENTIONED_WITH patterns
MATCH (a)-[r:MENTIONED_WITH]->(b)
WITH labels(a) AS source, labels(b) AS target, count(*) AS count
WHERE count >= 5
RETURN source, target, count
```

**Proposal Example:**
- **Title:** "New relationship: CyberAttack_TO_Country"
- **Evidence:** 31 co-occurrences
- **Suggestion:** Replace generic MENTIONED_WITH with semantic relationship

---

## Inconsistency Detection

### ISO Code Violations

Detects Country entities with invalid ISO 3166-1 alpha-2 codes:

```cypher
MATCH (c)
WHERE c.entity_type = 'COUNTRY'
  AND (size(c.entity_id) <> 2 OR c.entity_id =~ '.*[^A-Z].*')
RETURN c
```

**Severity:** CRITICAL
**Confidence:** 1.0 (always a violation)

### Duplicate Entities

Finds entities with duplicate entity_id values:

```cypher
MATCH (n)
WITH n.entity_id AS id, collect(n) AS nodes
WHERE size(nodes) > 1
RETURN id, size(nodes) AS count
```

**Severity:** HIGH
**Action:** Merge or deduplicate

### Missing Required Properties

Detects Entity nodes missing mandatory properties:

```cypher
MATCH (e:Entity)
WHERE e.entity_id IS NULL
   OR e.entity_type IS NULL
   OR e.name IS NULL
RETURN e
```

**Severity:** HIGH
**Impact:** Query reliability issues

---

## Proposal Model

Every proposal includes:

```python
{
  "proposal_id": "OSS_20251110_143022_abc123",
  "change_type": "NEW_ENTITY_TYPE | FLAG_INCONSISTENCY | ...",
  "severity": "CRITICAL | HIGH | MEDIUM | LOW",
  "title": "Short description",
  "description": "Detailed explanation with context",
  "evidence": [
    {
      "example_id": "node_12345",
      "example_type": "NODE",
      "properties": {...},
      "context": "Why this is evidence",
      "frequency": 47
    }
  ],
  "pattern_query": "Cypher query that found the pattern",
  "occurrence_count": 47,
  "confidence": 0.92,
  "confidence_factors": {
    "frequency": 0.9,
    "consistency": 0.95
  },
  "impact_analysis": {
    "affected_entities_count": 47,
    "breaking_change": false,
    "migration_complexity": "MEDIUM",
    "estimated_effort_hours": 4.0,
    "benefits": [...],
    "risks": [...]
  }
}
```

---

## Usage

### Manual Analysis Trigger

```bash
# Trigger analysis cycle
curl -X POST http://localhost:8110/api/v1/analysis/run

# Check status
curl http://localhost:8110/api/v1/analysis/status
```

### Docker Development

```bash
# Start OSS service
cd /home/cytrex/news-microservices
docker compose up -d oss-service

# View logs
docker logs -f oss-service

# Check health
curl http://localhost:8110/health

# Swagger UI
http://localhost:8110/docs
```

---

## Development

### Project Structure

```
oss-service/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings
│   ├── database.py          # Neo4j connection
│   ├── models/
│   │   └── proposal.py      # Pydantic models
│   ├── analyzers/
│   │   ├── pattern_detector.py
│   │   └── inconsistency_detector.py
│   └── api/
│       └── analysis.py      # API routes
├── Dockerfile.dev           # Development dockerfile
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Adding New Analyzers

1. Create analyzer in `app/analyzers/`:

```python
class MyAnalyzer:
    def __init__(self, neo4j: Neo4jConnection):
        self.neo4j = neo4j

    async def detect_issues(self) -> List[OntologyChangeProposal]:
        # Your detection logic
        return proposals
```

2. Add to analysis cycle in `app/api/analysis.py`:

```python
my_analyzer = MyAnalyzer(neo4j)
issues = await my_analyzer.detect_issues()
all_proposals.extend(issues)
```

---

## Testing

### Test Pattern Detection

```bash
# Check Neo4j has data
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (n) RETURN count(n) AS total_nodes"

# Run analysis
curl -X POST http://localhost:8110/api/v1/analysis/run

# Check proposals were created
curl http://localhost:8109/api/v1/ontology/proposals
```

### Test Inconsistency Detection

```bash
# Create test data with ISO violations
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "CREATE (c:Country {entity_id: 'UKR', name: 'Ukraine', entity_type: 'COUNTRY'})"

# Run analysis
curl -X POST http://localhost:8110/api/v1/analysis/run

# Should detect ISO code violation (UKR should be UA)
```

---

## Monitoring

### Key Metrics

- **Patterns detected per cycle**
- **Inconsistencies found per cycle**
- **Proposals generated per cycle**
- **Proposals submitted successfully**
- **Analysis cycle duration**

### Logs

```bash
# Watch OSS logs
docker logs -f oss-service

# Filter for proposals
docker logs oss-service 2>&1 | grep "proposal"

# Filter for errors
docker logs oss-service 2>&1 | grep "ERROR"
```

---

## Integration

### With Ontology Proposals Service

OSS automatically submits proposals to Port 8109:

```
POST http://ontology-proposals-service:8109/api/v1/ontology/proposals
```

### With Dashboard UI (Future)

Dashboard will:
- Display pending proposals
- Allow Accept/Reject
- Show approval history
- Track implementation status

---

## Future Enhancements

### Phase 2 (Completed ✅)
- [x] Scheduled analysis via APScheduler (2025-11-11)
- [x] Frontend navigation integration (2025-11-11)
- [x] ISO code validation and fixes (2025-11-10)
- [ ] Approval rate tracking
- [ ] Confidence calibration based on approvals
- [ ] Validation of content-analysis-v2 output

### Phase 3 (Planned)
- [ ] Machine learning for confidence scoring
- [ ] Auto-approval for high-confidence proposals
- [ ] Trend analysis (weekly/monthly reports)
- [ ] Integration with formal ontology Git repo
- [ ] Slack/Email notifications for critical proposals

---

## Troubleshooting

### Neo4j Connection Failed

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check credentials
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 "RETURN 1"

# Check OSS config
docker exec oss-service env | grep NEO4J
```

### Proposals Not Submitting

```bash
# Check Proposals API is running
curl http://localhost:8109/health

# Check OSS can reach it
docker exec oss-service curl http://ontology-proposals-service:8109/health

# Check logs for errors
docker logs oss-service 2>&1 | grep "submit"
```

### No Proposals Generated

```bash
# Check if Neo4j has data
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (n) RETURN count(n)"

# Lower MIN_PATTERN_OCCURRENCES
# Edit docker-compose.yml: MIN_PATTERN_OCCURRENCES=5

# Restart service
docker compose restart oss-service
```

### Scheduler Not Running

```bash
# Check scheduler logs at startup
docker logs oss-service 2>&1 | grep "scheduler"

# Expected output:
# Starting background scheduler with interval: 3600s
# Scheduler started
# Background scheduler started

# If missing, check for errors:
docker logs oss-service 2>&1 | grep "ERROR"

# Verify APScheduler is installed
docker exec oss-service pip list | grep -i apscheduler
# Expected: APScheduler 3.10.4
```

### Scheduled Analysis Not Running Automatically

```bash
# Check last scheduled run
docker logs oss-service 2>&1 | grep "scheduled" | tail -5

# If no recent runs, check interval setting
curl http://localhost:8110/api/v1/analysis/status | grep analysis_interval

# Force a test run to verify functionality
curl -X POST http://localhost:8110/api/v1/analysis/run

# If manual works but automatic doesn't, check scheduler state
docker logs oss-service 2>&1 | grep "apscheduler" | tail -20
```

### Change Scheduler Interval

```bash
# Stop service
docker compose stop oss-service

# Edit docker-compose.yml
# Add under oss-service environment:
#   - ANALYSIS_INTERVAL_SECONDS=300  # 5 minutes for testing

# Rebuild and restart
docker compose up -d --force-recreate oss-service

# Verify new interval
curl http://localhost:8110/api/v1/analysis/status | grep analysis_interval
```

---

## References

- **OSS Specification:** `/home/cytrex/userdocs/system-ontology/07_OSS_SPECIFICATION.md`
- **MVO Phase 1:** `/home/cytrex/userdocs/system-ontology/06_MVO_PHASE_1.md`
- **Ontology Proposals Service:** `services/ontology-proposals-service/README.md`

---

**Status:** ✅ Production Ready

**Recent Updates:**
- 2025-11-11: APScheduler implementation for automatic analysis
- 2025-11-11: Frontend navigation integration
- 2025-11-10: ISO code validation and fix mechanism
- 2025-11-10: Initial release and testing

**Last Updated:** 2025-11-11

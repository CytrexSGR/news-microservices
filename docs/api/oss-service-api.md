# OSS Service API Documentation

**Base URL:** `http://localhost:8110`
**Version:** 1.0.0
**OpenAPI Docs:** http://localhost:8110/docs

---

## Authentication

Currently no authentication required (internal service).

---

## Endpoints

### Analysis Operations

#### POST /api/v1/analysis/run

Trigger an OSS analysis cycle manually.

**Request:**
```bash
curl -X POST http://localhost:8110/api/v1/analysis/run
```

**Response 200:**
```json
{
  "cycle_id": "cycle_20251111_071418_f9edb1dd",
  "started_at": "2025-11-11T07:14:18.186593",
  "completed_at": "2025-11-11T07:14:18.404187",
  "patterns_detected": 0,
  "inconsistencies_detected": 6,
  "proposals_generated": 6,
  "proposals_submitted": 6,
  "errors": [],
  "warnings": [],
  "proposals": [
    {
      "proposal_id": "OSS_20251111_071418_a8ba3185",
      "change_type": "FLAG_INCONSISTENCY",
      "severity": "CRITICAL",
      "title": "Inconsistent ISO country codes",
      "description": "Detected 15 Country nodes with invalid ISO 3166-1 alpha-2 codes",
      "evidence": [...],
      "occurrence_count": 15,
      "confidence": 1.0
    }
  ]
}
```

**Response Fields:**
- `cycle_id` - Unique identifier for this analysis cycle
- `started_at` - ISO 8601 timestamp
- `completed_at` - ISO 8601 timestamp
- `patterns_detected` - Number of patterns found
- `inconsistencies_detected` - Number of inconsistencies found
- `proposals_generated` - Number of proposals created
- `proposals_submitted` - Number successfully submitted to Proposals API
- `errors` - Array of error messages
- `warnings` - Array of warnings
- `proposals` - Array of generated proposals (full details)

---

#### GET /api/v1/analysis/status

Get service status and configuration.

**Request:**
```bash
curl http://localhost:8110/api/v1/analysis/status
```

**Response 200:**
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

**Response Fields:**
- `service` - Service name
- `version` - Service version
- `status` - Service health status
- `neo4j_connected` - Boolean, true if Neo4j is reachable
- `proposals_api` - URL of Ontology Proposals Service
- `analysis_interval_seconds` - Automatic analysis interval
- `min_pattern_occurrences` - Minimum pattern occurrences to generate proposal
- `confidence_threshold` - Minimum confidence to include proposal

---

### Health Check

#### GET /health

Service health check endpoint.

**Request:**
```bash
curl http://localhost:8110/health
```

**Response 200:**
```json
{
  "status": "healthy",
  "service": "OSS Service",
  "version": "1.0.0",
  "timestamp": "2025-11-11T07:13:52.767954",
  "neo4j": "connected",
  "proposals_api": "http://ontology-proposals-service:8109"
}
```

**Status Values:**
- `healthy` - All dependencies are healthy
- `degraded` - Neo4j connection failed (service still operational)

---

## Data Models

### AnalysisResult

```typescript
{
  cycle_id: string;           // Unique cycle identifier
  started_at: datetime;       // Start timestamp
  completed_at: datetime;     // Completion timestamp
  patterns_detected: number;  // Count of patterns found
  inconsistencies_detected: number;  // Count of inconsistencies
  proposals_generated: number;  // Count of proposals created
  proposals_submitted: number;  // Count successfully submitted
  errors: string[];           // Error messages
  warnings: string[];         // Warning messages
  proposals: Proposal[];      // Array of generated proposals
}
```

### Proposal

```typescript
{
  proposal_id: string;        // Unique identifier (OSS_YYYYMMDD_HHMMSS_hash)
  change_type: string;        // NEW_ENTITY_TYPE | FLAG_INCONSISTENCY | etc
  severity: string;           // CRITICAL | HIGH | MEDIUM | LOW
  title: string;              // Short description
  description: string;        // Detailed explanation
  evidence: Evidence[];       // Array of evidence
  pattern_query: string;      // Cypher query that found pattern
  occurrence_count: number;   // Number of occurrences
  confidence: number;         // 0.0 to 1.0
  confidence_factors: object; // Confidence breakdown
  impact_analysis: object;    // Impact assessment
  oss_version: string;        // OSS service version
  tags: string[];             // Categorization tags
}
```

### Evidence

```typescript
{
  example_id: string;         // Node/relationship ID
  example_type: string;       // NODE | RELATIONSHIP
  properties: object;         // Property values
  context: string;            // Why this is evidence
  frequency: number | null;   // Occurrence frequency
}
```

---

## Error Responses

### 500 Internal Server Error

```json
{
  "detail": "Internal server error",
  "type": "internal_error"
}
```

Occurs when:
- Neo4j connection fails during analysis
- Proposals API is unreachable
- Unexpected error in analysis logic

---

## Automatic Scheduling

OSS runs analysis automatically every `ANALYSIS_INTERVAL_SECONDS` (default: 3600s).

**How to Monitor:**
```bash
# Watch for scheduled runs
docker logs -f oss-service 2>&1 | grep "scheduled"

# Expected output every hour:
# 2025-11-11 08:21:34 - app.main - INFO - Running scheduled OSS analysis cycle
# 2025-11-11 08:21:45 - app.main - INFO - Scheduled analysis completed: 6 proposals generated
```

**Change Interval:**
Set `ANALYSIS_INTERVAL_SECONDS` environment variable in docker-compose.yml.

---

## Examples

### Pattern Detection Example

**Request:**
```bash
curl -X POST http://localhost:8110/api/v1/analysis/run
```

**Response:**
```json
{
  "cycle_id": "cycle_20251111_143000_abc123",
  "patterns_detected": 2,
  "proposals": [
    {
      "proposal_id": "OSS_20251111_143000_def456",
      "change_type": "NEW_ENTITY_TYPE",
      "severity": "MEDIUM",
      "title": "New entity type: CyberActorGroup",
      "description": "Detected 47 nodes with pattern suggesting CyberActorGroup entity type",
      "occurrence_count": 47,
      "confidence": 0.92
    }
  ]
}
```

### Inconsistency Detection Example

**Request:**
```bash
curl -X POST http://localhost:8110/api/v1/analysis/run
```

**Response:**
```json
{
  "cycle_id": "cycle_20251111_143100_xyz789",
  "inconsistencies_detected": 3,
  "proposals": [
    {
      "proposal_id": "OSS_20251111_143100_iso001",
      "change_type": "FLAG_INCONSISTENCY",
      "severity": "CRITICAL",
      "title": "Inconsistent ISO country codes",
      "description": "15 Country entities have invalid ISO codes",
      "occurrence_count": 15,
      "confidence": 1.0,
      "evidence": [
        {
          "example_id": "2",
          "properties": {"entity_id": "USA", "name": "United States"},
          "context": "Invalid ISO code: 'USA' should be 'US'"
        }
      ]
    }
  ]
}
```

---

## Integration

### With Ontology Proposals Service

OSS automatically submits proposals to:

```
POST http://ontology-proposals-service:8109/api/v1/ontology/proposals
```

Each proposal is stored in PostgreSQL and available via Proposals API.

### With Dashboard UI

Dashboard displays proposals at:
```
http://localhost:3000/admin/ontology/proposals
```

---

## Rate Limiting

No rate limiting currently implemented (internal service).

---

## Related Documentation

- Service README: `/services/oss-service/README.md`
- Ontology Proposals API: `/docs/api/ontology-proposals-api.md`
- System Ontology: `/home/cytrex/userdocs/system-ontology/`

---

**Last Updated:** 2025-11-11

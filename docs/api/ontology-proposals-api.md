# Ontology Proposals Service API Documentation

**Base URL:** `http://localhost:8109`
**Version:** 1.0.0
**OpenAPI Docs:** http://localhost:8109/docs

---

## Authentication

Currently no authentication required (internal service).
Future: JWT from auth-service.

---

## Endpoints

### Proposal Management

#### POST /api/v1/ontology/proposals

Create a new ontology change proposal.

**Request:**
```bash
curl -X POST http://localhost:8109/api/v1/ontology/proposals \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": "OSS_20251111_120000_abc123",
    "change_type": "NEW_ENTITY_TYPE",
    "severity": "HIGH",
    "title": "New entity type: TechnologicalInnovation",
    "description": "Detected recurring pattern suggesting new entity type",
    "evidence": [
      {
        "example_id": "node_123",
        "example_type": "NODE",
        "properties": {"name": "AI Development"},
        "context": "Occurs 157 times in graph",
        "frequency": 157
      }
    ],
    "occurrence_count": 157,
    "confidence": 0.89,
    "pattern_query": "MATCH (n) WHERE n.type = \"innovation\" RETURN n"
  }'
```

**Response 201:**
```json
{
  "success": true,
  "proposal_id": "OSS_20251111_120000_abc123",
  "message": "Proposal created successfully"
}
```

**Response 400 (Duplicate):**
```json
{
  "detail": "Proposal with ID OSS_20251111_120000_abc123 already exists"
}
```

**Request Fields:**
- `proposal_id` *(required)* - Unique identifier
- `change_type` *(required)* - Type of change (NEW_ENTITY_TYPE, FLAG_INCONSISTENCY, etc.)
- `severity` *(required)* - CRITICAL | HIGH | MEDIUM | LOW
- `title` *(required)* - Short description
- `description` *(required)* - Detailed explanation
- `evidence` *(optional)* - Array of evidence objects
- `occurrence_count` *(optional)* - Number of occurrences
- `confidence` *(optional)* - 0.0 to 1.0
- `pattern_query` *(optional)* - Cypher query

---

#### GET /api/v1/ontology/proposals

List all proposals with optional filtering.

**Request:**
```bash
# List all proposals
curl http://localhost:8109/api/v1/ontology/proposals

# Filter by status
curl "http://localhost:8109/api/v1/ontology/proposals?status=PENDING"

# Filter by severity
curl "http://localhost:8109/api/v1/ontology/proposals?severity=CRITICAL"

# Pagination
curl "http://localhost:8109/api/v1/ontology/proposals?limit=20&offset=0"

# Multiple filters
curl "http://localhost:8109/api/v1/ontology/proposals?status=ACCEPTED&severity=HIGH&limit=50"
```

**Query Parameters:**
- `status` *(optional)* - Filter by status (PENDING, ACCEPTED, REJECTED, IMPLEMENTED, FAILED)
- `severity` *(optional)* - Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
- `change_type` *(optional)* - Filter by change type
- `limit` *(optional)* - Max results (default: 100, max: 1000)
- `offset` *(optional)* - Pagination offset (default: 0)

**Response 200:**
```json
[
  {
    "id": 1,
    "proposal_id": "OSS_20251111_120000_abc123",
    "change_type": "NEW_ENTITY_TYPE",
    "severity": "HIGH",
    "status": "PENDING",
    "title": "New entity type: TechnologicalInnovation",
    "description": "Detected recurring pattern...",
    "occurrence_count": 157,
    "confidence": 0.89,
    "created_at": "2025-11-11T12:00:00Z",
    "updated_at": "2025-11-11T12:00:00Z",
    "implementation_result": null,
    "implemented_at": null
  }
]
```

---

#### GET /api/v1/ontology/proposals/{proposal_id}

Get a specific proposal by ID.

**Request:**
```bash
curl http://localhost:8109/api/v1/ontology/proposals/OSS_20251111_120000_abc123
```

**Response 200:**
```json
{
  "id": 1,
  "proposal_id": "OSS_20251111_120000_abc123",
  "change_type": "NEW_ENTITY_TYPE",
  "severity": "HIGH",
  "status": "PENDING",
  "title": "New entity type: TechnologicalInnovation",
  "description": "Detected recurring pattern suggesting new entity type",
  "definition": null,
  "evidence": [
    {
      "example_id": "node_123",
      "example_type": "NODE",
      "properties": {"name": "AI Development"},
      "context": "Occurs 157 times",
      "frequency": 157
    }
  ],
  "pattern_query": "MATCH (n) WHERE n.type = \"innovation\" RETURN n",
  "occurrence_count": 157,
  "confidence": 0.89,
  "confidence_factors": {"frequency": 0.9, "consistency": 0.88},
  "validation_checks": ["Verified against existing types"],
  "impact_analysis": {
    "affected_entities_count": 157,
    "breaking_change": false,
    "migration_complexity": "MEDIUM",
    "estimated_effort_hours": 4.0
  },
  "oss_version": "1.0.0",
  "related_proposals": null,
  "tags": ["entity-type", "innovation"],
  "created_at": "2025-11-11T12:00:00Z",
  "updated_at": "2025-11-11T12:00:00Z",
  "reviewed_by": null,
  "reviewed_at": null,
  "review_notes": null,
  "implementation_result": null,
  "implemented_at": null
}
```

**Response 404:**
```json
{
  "detail": "Proposal not found"
}
```

---

### Implementation API

#### POST /api/v1/ontology/proposals/{proposal_id}/implement

Implement an approved proposal by applying changes to Neo4j.

**Prerequisites:**
- Proposal must have `status = "ACCEPTED"`

**Request:**
```bash
curl -X POST http://localhost:8109/api/v1/ontology/proposals/OSS_20251110_214600_ac9ec601/implement
```

**Response 200 (Success):**
```json
{
  "success": true,
  "proposal_id": "OSS_20251110_214600_ac9ec601",
  "status": "IMPLEMENTED",
  "message": "Proposal implemented successfully",
  "changes_applied": {
    "entities_updated": 15,
    "properties_fixed": ["entity_id"],
    "fix_type": "iso_code_correction",
    "details": {
      "United States": "US",
      "Australia": "AU",
      "Japan": "JP",
      "North Korea": "KP",
      "China": "CN",
      "Russia": "RU"
    }
  },
  "implemented_at": "2025-11-10T21:46:30.123456Z"
}
```

**Response 200 (Error):**
```json
{
  "success": false,
  "proposal_id": "OSS_20251110_214600_ac9ec601",
  "status": "FAILED",
  "error": "Neo4j connection failed: Connection timeout",
  "implemented_at": "2025-11-10T21:46:30.123456Z"
}
```

**Response 400 (Invalid Status):**
```json
{
  "detail": "Proposal must be ACCEPTED before implementation. Current status: PENDING"
}
```

**Response 404:**
```json
{
  "detail": "Proposal not found"
}
```

**Status Transitions:**
- `ACCEPTED` → `IMPLEMENTED` (on success)
- `ACCEPTED` → `FAILED` (on error)

**Supported Fix Types:**

1. **ISO Code Corrections**
   - Detects: "ISO country code", "ISO code violation"
   - Action: Updates entity_id to ISO 3166-1 alpha-2 code
   - Example: "United States" → "US"

2. **Missing Properties**
   - Detects: "missing required properties", "missing property"
   - Action: Adds default values for required fields
   - Example: Sets entity_type, entity_id

3. **Property Standardization**
   - Detects: "inconsistent format", "standardize property"
   - Action: Normalizes property values
   - Example: Date format standardization

---

### Health Check

#### GET /health

Service health check endpoint.

**Request:**
```bash
curl http://localhost:8109/health
```

**Response 200:**
```json
{
  "status": "healthy",
  "service": "Ontology Proposals Service",
  "version": "1.0.0",
  "timestamp": "2025-11-11T12:00:00Z",
  "database": "connected",
  "neo4j": "connected"
}
```

**Status Values:**
- `healthy` - All dependencies OK
- `degraded` - Database or Neo4j connection issues

---

## Data Models

### Proposal

```typescript
{
  // System fields
  id: number;                 // Auto-increment PK
  proposal_id: string;        // Unique identifier

  // Proposal details
  change_type: string;        // Type of change
  severity: string;           // CRITICAL | HIGH | MEDIUM | LOW
  status: string;             // PENDING | ACCEPTED | REJECTED | IMPLEMENTED | FAILED
  title: string;              // Short description
  description: string;        // Detailed explanation
  definition: string | null;  // Formal definition

  // Evidence & analysis
  evidence: Evidence[];       // Array of evidence
  pattern_query: string | null;  // Cypher query
  occurrence_count: number | null;  // Count
  confidence: number | null;  // 0.0 to 1.0
  confidence_factors: object | null;  // Breakdown
  validation_checks: string[] | null;  // Validation steps
  impact_analysis: object | null;  // Impact assessment

  // Metadata
  oss_version: string | null;  // OSS version
  related_proposals: string[] | null;  // Related IDs
  tags: string[] | null;       // Tags

  // Timestamps
  created_at: datetime;       // Creation time
  updated_at: datetime;       // Last update

  // Review
  reviewed_by: string | null;  // Reviewer ID
  reviewed_at: datetime | null;  // Review time
  review_notes: string | null;  // Review comments

  // Implementation
  implementation_result: object | null;  // Result details
  implemented_at: datetime | null;  // Implementation time
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

### 400 Bad Request

```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found

```json
{
  "detail": "Proposal not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error",
  "type": "database_error"
}
```

---

## Examples

### Complete Workflow: ISO Code Fix

```bash
# 1. OSS creates proposal
curl -X POST http://localhost:8110/api/v1/analysis/run

# 2. List critical proposals
curl "http://localhost:8109/api/v1/ontology/proposals?severity=CRITICAL"

# 3. Get proposal details
curl http://localhost:8109/api/v1/ontology/proposals/OSS_20251110_214600_ac9ec601

# 4. Review in UI (http://localhost:3000/admin/ontology/proposals)
# User clicks "Accept" → status changes to ACCEPTED

# 5. Implement proposal
curl -X POST http://localhost:8109/api/v1/ontology/proposals/OSS_20251110_214600_ac9ec601/implement

# 6. Verify implementation
curl http://localhost:8109/api/v1/ontology/proposals/OSS_20251110_214600_ac9ec601
# Check: status = "IMPLEMENTED", implemented_at is set

# 7. Verify in Neo4j
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (e:Entity {entity_type: 'COUNTRY'}) RETURN e.name, e.entity_id"
```

### Filtering Examples

```bash
# Get all pending proposals
curl "http://localhost:8109/api/v1/ontology/proposals?status=PENDING"

# Get critical issues only
curl "http://localhost:8109/api/v1/ontology/proposals?severity=CRITICAL"

# Get implemented ISO fixes
curl "http://localhost:8109/api/v1/ontology/proposals?status=IMPLEMENTED&change_type=FLAG_INCONSISTENCY"

# Paginate results (50 per page)
curl "http://localhost:8109/api/v1/ontology/proposals?limit=50&offset=0"
curl "http://localhost:8109/api/v1/ontology/proposals?limit=50&offset=50"
```

---

## Integration

### With OSS Service

OSS submits proposals automatically:

```
POST /api/v1/ontology/proposals
```

### With Dashboard UI

Dashboard displays proposals at:

```
http://localhost:3000/admin/ontology/proposals
```

Provides:
- List view with filters
- Detail view with evidence
- Accept/Reject buttons
- Implementation status

---

## Database Schema

Table: `public.ontology_proposals`

**Columns:** 21 fields including:
- id (PK), proposal_id (unique)
- change_type, severity, status
- title, description, definition
- evidence (JSONB), pattern_query
- confidence, impact_analysis (JSONB)
- timestamps, review fields
- implementation fields

**Indexes:** 8 indexes for efficient queries on:
- proposal_id (unique)
- status
- severity
- change_type
- created_at
- compound indexes

**Trigger:** `update_ontology_proposals_updated_at` for automatic timestamp updates

---

## Rate Limiting

No rate limiting currently implemented (internal service).

---

## Related Documentation

- Service README: `/services/ontology-proposals-service/README.md`
- OSS API: `/docs/api/oss-service-api.md`
- ISO Code Utils: `/services/ontology-proposals-service/app/utils/iso_codes.py`

---

**Last Updated:** 2025-11-11

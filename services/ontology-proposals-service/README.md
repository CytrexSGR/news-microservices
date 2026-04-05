# Ontology Proposals Service

**Version:** 1.0.0
**Port:** 8109
**Status:** ✅ Production Ready

FastAPI microservice for receiving, managing, and implementing ontology change proposals from the OSS (Ontology Suggestion System).

## Overview

This service provides a REST API to:
- ✅ Receive ontology change proposals from OSS
- ✅ Store proposals in PostgreSQL
- ✅ Query and manage proposals
- ✅ **Implement approved proposals** (Neo4j updates)
- ✅ **Fix inconsistencies** (ISO codes, missing properties)
- 🔜 Prepare proposals for review in Dashboard UI

## API Endpoints

### POST /api/v1/ontology/proposals
Create a new ontology proposal.

**Request Body:**
```json
{
  "proposal_id": "OSS_20251110_120000_test001",
  "change_type": "NEW_ENTITY",
  "severity": "HIGH",
  "title": "New entity type: TechnologicalInnovation",
  "description": "Detected recurring pattern...",
  "evidence": {...},
  "occurrence_count": 157,
  "confidence": 0.89
}
```

**Response:**
```json
{
  "success": true,
  "proposal_id": "OSS_20251110_120000_test001",
  "message": "Proposal created successfully"
}
```

### GET /api/v1/ontology/proposals
List all proposals with optional filters.

**Query Parameters:**
- `status` - Filter by status (PENDING, APPROVED, REJECTED)
- `severity` - Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
- `change_type` - Filter by change type
- `limit` - Max results (default: 100)
- `offset` - Pagination offset (default: 0)

### GET /api/v1/ontology/proposals/{proposal_id}
Get a specific proposal by ID.

---

### Implementation API

#### POST /api/v1/ontology/proposals/{proposal_id}/implement
Implement an approved proposal by applying changes to Neo4j.

**Status Transitions:**
- `ACCEPTED` → `IMPLEMENTED` (on success)
- `ACCEPTED` → `FAILED` (on error)

**Request:**
```bash
curl -X POST http://localhost:8109/api/v1/ontology/proposals/OSS_20251110_214600_ac9ec601/implement
```

**Response (Success):**
```json
{
  "success": true,
  "proposal_id": "OSS_20251110_214600_ac9ec601",
  "status": "IMPLEMENTED",
  "message": "Proposal implemented successfully",
  "changes_applied": {
    "entities_updated": 15,
    "properties_fixed": ["entity_id"],
    "fix_type": "iso_code_correction"
  },
  "implemented_at": "2025-11-10T21:46:30.123Z"
}
```

**Response (Error):**
```json
{
  "success": false,
  "proposal_id": "OSS_20251110_214600_ac9ec601",
  "status": "FAILED",
  "error": "Detailed error message",
  "implemented_at": "2025-11-10T21:46:30.123Z"
}
```

**Supported Fix Types:**
1. **ISO Code Corrections** - Fixes invalid country codes (e.g., "United States" → "US")
2. **Missing Properties** - Adds required properties to entities
3. **Property Standardization** - Normalizes property formats

**Implementation Logic:**
- Detects fix type from proposal title/description
- Uses utility functions (e.g., `iso_codes.get_iso_code()`)
- Updates Neo4j entities via `_fix_inconsistency()`
- Records implementation timestamp

---

### GET /health
Health check endpoint.

### GET /docs
Interactive API documentation (Swagger UI).

## Database Schema

Uses table `public.ontology_proposals` (already created via migration):

- 21 columns (id, proposal_id, change_type, severity, title, etc.)
- 8 indexes for efficient queries
- 1 trigger for updated_at timestamp

## Development

### Local Testing

```bash
# Start service (via docker-compose)
docker compose up ontology-proposals -d

# Test API
curl -X POST http://localhost:8109/api/v1/ontology/proposals \
  -H "Content-Type: application/json" \
  -d @/path/to/sample-proposal.json

# View logs
docker compose logs -f ontology-proposals

# Check database
docker exec postgres psql -h localhost -U news_user -d news_mcp -c \
  "SELECT proposal_id, severity, status FROM ontology_proposals;"
```

### Environment Variables

- `POSTGRES_HOST` - Database host (default: postgres)
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_USER` - Database user (default: news_user)
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DB` - Database name (default: news_mcp)

## Architecture

**4-Layer Architecture:**

1. **API Layer** (`app/api/`)
   - `proposals.py` - Proposal CRUD operations
   - `implementation.py` - Proposal implementation endpoints
   - FastAPI routers, request validation, response formatting

2. **Service Layer** (`app/services/`)
   - `implementation.py` - Implementation business logic
   - Neo4j integration for applying changes
   - Fix type detection and execution

3. **Utilities** (`app/utils/`)
   - `iso_codes.py` - ISO 3166-1 alpha-2 mappings (96 countries)
   - Helper functions for data validation

4. **Data Layer** (`app/models/`, `app/schemas/`)
   - SQLAlchemy ORM models (PostgreSQL)
   - Pydantic schemas (validation)

## ISO Code Utilities

**Location:** `app/utils/iso_codes.py`

### Features

- **96 Country Mappings** - ISO 3166-1 alpha-2 codes
- **Fuzzy Matching** - Handles variations ("United States" → "US")
- **Validation** - `validate_iso_code(code)` checks format
- **Lookup** - `get_iso_code(name)` returns code or None

### Example Usage

```python
from app.utils.iso_codes import get_iso_code, validate_iso_code

# Get ISO code
get_iso_code("United States")  # Returns "US"
get_iso_code("North Korea")    # Returns "KP"
get_iso_code("Unknown")        # Returns None

# Validate code
validate_iso_code("US")   # Returns True
validate_iso_code("USA")  # Returns False (must be 2 chars)
validate_iso_code("us")   # Returns False (must be uppercase)
```

### Supported Countries

Full list of 96 countries available in `app/utils/iso_codes.py`.

Examples:
- United States → US
- United Kingdom → GB
- Germany → DE
- Japan → JP
- China → CN
- Russia → RU
- Australia → AU
- ... (91 more)

## Usage Examples

### Complete Workflow: ISO Code Fix

```bash
# 1. OSS detects ISO violations
curl -X POST http://localhost:8110/api/v1/analysis/run

# 2. Check generated proposals
curl http://localhost:8109/api/v1/ontology/proposals?severity=CRITICAL

# 3. Review proposal in UI (http://localhost:3000/admin/ontology/proposals)

# 4. Accept proposal (manual or via UI)
# Status changes to ACCEPTED

# 5. Implement proposal
curl -X POST http://localhost:8109/api/v1/ontology/proposals/OSS_20251110_214600_ac9ec601/implement

# 6. Verify in Neo4j
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (e:Entity {entity_type: 'COUNTRY'}) RETURN e.name, e.entity_id LIMIT 10"
```

### Check Implementation Status

```bash
# Get proposal with implementation details
curl http://localhost:8109/api/v1/ontology/proposals/OSS_20251110_214600_ac9ec601

# Look for:
# - status: "IMPLEMENTED"
# - implementation_result: {...}
# - implemented_at: "2025-11-10T21:46:30Z"
```

---

## Troubleshooting

### Implementation Fails

```bash
# Check Neo4j connection
curl http://localhost:8109/health

# Check logs
docker logs ontology-proposals-service 2>&1 | grep -i "implement"

# Verify proposal is ACCEPTED
curl http://localhost:8109/api/v1/ontology/proposals/{proposal_id}

# Check Neo4j directly
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 "MATCH (n) RETURN count(n)"
```

### ISO Code Not Found

```bash
# Check if country is in mapping
docker exec ontology-proposals-service python3 -c \
  "from app.utils.iso_codes import get_iso_code; print(get_iso_code('YourCountry'))"

# Add missing country to app/utils/iso_codes.py:
# "Your Country": "YC",
```

### Proposal Status Not Updating

```bash
# Check database connection
docker exec postgres psql -U news_user -d news_mcp -c \
  "SELECT proposal_id, status FROM ontology_proposals WHERE proposal_id = 'OSS_...';"

# Check service logs
docker logs ontology-proposals-service --tail 50
```

---

## Future Enhancements

### Phase 2 (Completed ✅)
- [x] Implementation API for approved proposals (2025-11-10)
- [x] ISO code validation and fixes (2025-11-10)
- [x] Frontend navigation integration (2025-11-11)

### Phase 3 (Planned)
- [ ] Add authentication (JWT from auth-service)
- [ ] Add approval workflow (PATCH endpoint for Accept/Reject)
- [ ] Add Slack notifications via webhooks
- [ ] Add metrics/monitoring (Prometheus)
- [ ] Add unit tests (pytest)
- [ ] Auto-implementation for low-risk proposals
- [ ] Batch implementation API

## Dependencies

- FastAPI 0.115.0 - Web framework
- SQLAlchemy 2.0.35 - ORM
- Pydantic 2.8.0 - Validation
- psycopg2-binary 2.9.9 - PostgreSQL driver

## Port

8109

## Status

✅ **Production Ready**

**Recent Updates:**
- 2025-11-11: Frontend navigation integration
- 2025-11-10: Implementation API for proposal execution
- 2025-11-10: ISO code utilities and validation
- 2025-11-10: Initial release with PostgreSQL storage

**Last Updated:** 2025-11-11

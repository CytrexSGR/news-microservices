# Batch Reprocessing API Documentation

## Overview

The Batch Reprocessing API allows administrators to reprocess all existing entities through the canonicalization pipeline to:

1. Find and merge duplicate entities
2. Add missing Wikidata Q-IDs
3. Apply fuzzy and semantic matching retroactively
4. Improve overall data quality

## Endpoints

### 1. Start Batch Reprocessing

**POST** `/api/v1/canonicalization/reprocess/start`

Starts a new batch reprocessing job.

**Request Body:**
```json
{
  "dry_run": false  // If true, only analyzes without making changes
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Batch reprocessing started",
  "dry_run": false
}
```

**Status Codes:**
- `200` - Job started successfully
- `409` - Another reprocessing job is already running
- `500` - Server error

---

### 2. Get Reprocessing Status

**GET** `/api/v1/canonicalization/reprocess/status`

Returns the current status of the reprocessing job.

**Response:**
```json
{
  "status": "running",  // idle | running | completed | failed
  "progress_percent": 45.2,
  "current_phase": "fuzzy_matching",  // analyzing | fuzzy_matching | semantic_matching | wikidata_lookup | merging | updating
  "stats": {
    "total_entities": 265,
    "processed_entities": 120,
    "duplicates_found": 18,
    "entities_merged": 12,
    "qids_added": 34,
    "errors": 0
  },
  "started_at": "2025-01-24T20:30:00Z",
  "completed_at": null,
  "error_message": null,
  "dry_run": false
}
```

**Status Values:**
- `idle` - No job running
- `running` - Job in progress
- `completed` - Job finished successfully
- `failed` - Job failed with errors

**Phase Values:**
1. `analyzing` - Analyzing all entities and planning work
2. `fuzzy_matching` - Finding similar entity names (Levenshtein distance)
3. `semantic_matching` - Finding semantically similar entities (embeddings)
4. `wikidata_lookup` - Fetching missing Wikidata Q-IDs
5. `merging` - Merging duplicate entities
6. `updating` - Updating PostgreSQL and Neo4j databases

**Status Codes:**
- `200` - Status retrieved successfully
- `500` - Server error

---

### 3. Stop Batch Reprocessing

**POST** `/api/v1/canonicalization/reprocess/stop`

Gracefully stops the current reprocessing job.

**Response:**
```json
{
  "message": "Reprocessing stopped",
  "stats": {
    "processed_entities": 120,
    "duplicates_found": 18,
    "entities_merged": 12,
    "qids_added": 34
  }
}
```

**Status Codes:**
- `200` - Job stopped successfully
- `404` - No job running
- `500` - Server error

---

## Implementation Requirements

### Backend Implementation

**File:** `services/entity-canonicalization-service/app/services/batch_reprocessor.py`

```python
class BatchReprocessor:
    """
    Handles batch reprocessing of all entities through canonicalization pipeline.
    """

    def __init__(self, db: AsyncSession, canonicalizer: EntityCanonicalizer):
        self.db = db
        self.canonicalizer = canonicalizer
        self.status = {
            "status": "idle",
            "progress_percent": 0.0,
            "current_phase": None,
            "stats": {
                "total_entities": 0,
                "processed_entities": 0,
                "duplicates_found": 0,
                "entities_merged": 0,
                "qids_added": 0,
                "errors": 0,
            },
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "dry_run": False,
        }

    async def start(self, dry_run: bool = False) -> str:
        """Start batch reprocessing job."""

    async def get_status(self) -> dict:
        """Get current reprocessing status."""

    async def stop(self) -> dict:
        """Stop current reprocessing job."""

    async def _run_reprocessing(self, dry_run: bool):
        """Main reprocessing logic (runs in background)."""
        # Phase 1: Analyze entities
        await self._phase_analyzing()

        # Phase 2: Fuzzy matching
        await self._phase_fuzzy_matching()

        # Phase 3: Semantic matching
        await self._phase_semantic_matching()

        # Phase 4: Wikidata lookup
        await self._phase_wikidata_lookup()

        # Phase 5: Merge duplicates
        await self._phase_merging(dry_run)

        # Phase 6: Update databases
        if not dry_run:
            await self._phase_updating()
```

**File:** `services/entity-canonicalization-service/app/api/routes/canonicalization.py`

```python
# Global reprocessor instance (singleton)
_reprocessor: Optional[BatchReprocessor] = None

@router.post("/reprocess/start")
async def start_batch_reprocessing(
    request: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """Start batch reprocessing job."""
    global _reprocessor

    if _reprocessor and _reprocessor.status["status"] == "running":
        raise HTTPException(status_code=409, detail="Reprocessing already running")

    canonicalizer = await get_canonicalizer(session)
    _reprocessor = BatchReprocessor(session, canonicalizer)

    job_id = await _reprocessor.start(dry_run=request.get("dry_run", False))

    return {
        "job_id": job_id,
        "message": "Batch reprocessing started",
        "dry_run": request.get("dry_run", False)
    }

@router.get("/reprocess/status", response_model=ReprocessingStatus)
async def get_reprocessing_status():
    """Get current reprocessing status."""
    global _reprocessor

    if not _reprocessor:
        return {
            "status": "idle",
            "progress_percent": 0.0,
            "current_phase": None,
            "stats": {
                "total_entities": 0,
                "processed_entities": 0,
                "duplicates_found": 0,
                "entities_merged": 0,
                "qids_added": 0,
                "errors": 0,
            },
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "dry_run": False,
        }

    return _reprocessor.get_status()

@router.post("/reprocess/stop")
async def stop_batch_reprocessing():
    """Stop current reprocessing job."""
    global _reprocessor

    if not _reprocessor or _reprocessor.status["status"] != "running":
        raise HTTPException(status_code=404, detail="No reprocessing job running")

    result = await _reprocessor.stop()
    return result
```

---

## Algorithm Details

### Phase 1: Analyzing
- Load all canonical entities from PostgreSQL
- Count total entities
- Group entities by type
- Estimate processing time

### Phase 2: Fuzzy Matching
- For each entity name, compute Levenshtein distance to other names
- Threshold: distance <= 2 for names > 5 chars
- Create candidate pairs for merging

### Phase 3: Semantic Matching
- Use sentence embeddings (same as current pipeline)
- Cosine similarity > 0.85 threshold
- Add to candidate pairs

### Phase 4: Wikidata Lookup
- For entities without Q-ID, query Wikidata API
- Use entity name + type for search
- Store Q-ID if confidence > 0.8

### Phase 5: Merging Duplicates
- Sort candidate pairs by confidence (highest first)
- Merge duplicates:
  - Keep entity with Q-ID if available
  - Merge aliases from both entities
  - Update relationships in Neo4j
- Mark entities as merged in PostgreSQL

### Phase 6: Updating Databases
- Batch update PostgreSQL (canonical_entities, entity_aliases)
- Batch update Neo4j (MERGE nodes, update relationships)
- Commit transaction
- Update statistics

---

## Frontend Integration

The frontend automatically:
1. Polls `/reprocess/status` every 2 seconds when job is running
2. Displays live progress bar and statistics
3. Stops polling when status becomes `completed` or `failed`
4. Invalidates cached stats after completion

**Frontend Files:**
- `frontend/src/features/admin/knowledge-graph/components/analytics/BatchReprocessing.tsx`
- `frontend/src/features/admin/knowledge-graph/hooks/useReprocessingStatus.ts`
- `frontend/src/lib/api/canonicalizationAdmin.ts`
- `frontend/src/types/knowledgeGraph.ts`

---

## Testing

### Manual Testing Steps

1. **Start Dry Run:**
   ```bash
   curl -X POST http://localhost:8112/api/v1/canonicalization/reprocess/start \
     -H "Content-Type: application/json" \
     -d '{"dry_run": true}'
   ```

2. **Check Status:**
   ```bash
   curl http://localhost:8112/api/v1/canonicalization/reprocess/status
   ```

3. **Stop Job:**
   ```bash
   curl -X POST http://localhost:8112/api/v1/canonicalization/reprocess/stop
   ```

### Expected Results

**Before Reprocessing:**
- Total Entities: 265
- Wikidata Coverage: 73.9%
- Deduplication Ratio: 1.74x

**After Reprocessing:**
- Total Entities: ~180-190 (85-75 merged)
- Wikidata Coverage: ~85%+
- Deduplication Ratio: ~2.3-2.5x

---

## Error Handling

- If job fails during merging, rollback database transaction
- Continue processing remaining entities after error
- Track errors in `stats.errors` counter
- Set `status = "failed"` and populate `error_message`

---

## Performance Considerations

- Process in batches (50 entities at a time)
- Use asyncio for concurrent Wikidata lookups
- Cache embedding calculations
- Estimated time: 5-10 minutes for 265 entities

---

## Security

- Only accessible by admin users (add auth middleware)
- Log all reprocessing activities
- Create database backup before starting (recommended in UI)
- Rate limit API calls (1 job per hour max)

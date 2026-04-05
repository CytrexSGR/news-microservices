# Admiralty Code Quality Rating System

## Overview

The Admiralty Code system provides a standardized A-F rating scale for feed source quality assessment, based on the NATO intelligence evaluation system. It complements the existing 0-100 quality score with easily recognizable letter grades.

**Status:** ✅ Implemented (2025-10-21)
**Version:** 1.0.0
**Services:** Feed Service, Frontend

## Purpose

Transform numeric quality scores (0-100) into intuitive letter grades (A-F) for:
- Quick visual assessment of feed reliability
- Standardized quality communication across the platform
- Administrative configuration of quality thresholds
- Flexible categorization of feed sources

## Admiralty Code Ratings

| Code | Label | Min Score | Description | Color |
|------|-------|-----------|-------------|-------|
| **A** | Completely Reliable | 90+ | Premium sources with exceptional credibility | 🟢 Green |
| **B** | Usually Reliable | 75+ | Trusted sources with strong credibility | 🔵 Blue |
| **C** | Fairly Reliable | 60+ | Acceptable sources with reasonable credibility | 🟡 Yellow |
| **D** | Not Usually Reliable | 40+ | Questionable sources requiring verification | 🟠 Orange |
| **E** | Unreliable | 20+ | Poor credibility, use with extreme caution | 🔴 Red |
| **F** | Cannot Be Judged | 0+ | No assessment available or insufficient data | ⚫ Gray |

## Quality Score Calculation

The underlying quality score (0-100) is calculated using weighted categories:

| Category | Weight | Description |
|----------|--------|-------------|
| **Credibility** | 40% | Tier rating (tier_1/tier_2/tier_3), reputation, longevity |
| **Editorial** | 25% | Fact-checking, corrections policy, source attribution |
| **Trust** | 20% | External ratings (NewsGuard, AllSides, MBFC) |
| **Health** | 15% | Uptime, response time, fetch success rate |

**Formula:**
```
quality_score = (credibility × 0.40) + (editorial × 0.25) + (trust × 0.20) + (health × 0.15)
admiralty_code = map_score_to_threshold(quality_score)
```

## Architecture

### Backend Components

#### 1. Database Schema

**Table: `admiralty_code_thresholds`**
```sql
CREATE TABLE admiralty_code_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(1) UNIQUE NOT NULL,           -- A, B, C, D, E, F
    label VARCHAR(50) NOT NULL,                -- "Completely Reliable"
    min_score INTEGER NOT NULL,                -- Minimum quality score
    description TEXT,                          -- Detailed explanation
    color VARCHAR(20),                         -- "green", "blue", etc.
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_admiralty_thresholds_code ON admiralty_code_thresholds(code);
CREATE INDEX idx_admiralty_thresholds_min_score ON admiralty_code_thresholds(min_score DESC);
```

**Table: `quality_score_weights`**
```sql
CREATE TABLE quality_score_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) UNIQUE NOT NULL,      -- credibility, editorial, trust, health
    weight NUMERIC(5,2) NOT NULL,              -- 0.40, 0.25, 0.20, 0.15
    description TEXT,
    min_value NUMERIC(5,2) DEFAULT 0.00,
    max_value NUMERIC(5,2) DEFAULT 1.00,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Constraint: weights must sum to 1.00
ALTER TABLE quality_score_weights
ADD CONSTRAINT check_weight_range CHECK (weight >= 0.00 AND weight <= 1.00);
```

#### 2. Service Layer

**File:** `services/feed-service/app/services/admiralty_code.py`

```python
class AdmiraltyCodeService:
    """
    Manages Admiralty Code configuration and calculation.

    Features:
    - In-memory caching for performance
    - Fallback to hardcoded defaults
    - Thread-safe operations
    - Validation of weight sums
    """

    async def get_admiralty_code(self, quality_score: int) -> Dict[str, str]:
        """Calculate Admiralty Code for a quality score."""

    async def get_all_thresholds(self) -> List[AdmiraltyCodeThreshold]:
        """Get all thresholds (cached)."""

    async def update_threshold(self, code: str, **kwargs) -> AdmiraltyCodeThreshold:
        """Update a specific threshold."""

    async def get_all_weights(self) -> Dict[str, Decimal]:
        """Get all category weights (cached)."""

    async def update_weight(self, category: str, weight: float) -> QualityScoreWeight:
        """Update a category weight with validation."""

    async def validate_weights_sum(self) -> bool:
        """Ensure weights sum to 1.00 (100%)."""
```

#### 3. API Endpoints

**Base Path:** `/api/v1/admiralty-codes`

**Thresholds:**
- `GET /thresholds` - List all thresholds
- `GET /thresholds/{code}` - Get specific threshold (A-F)
- `PUT /thresholds/{code}` - Update threshold
- `POST /thresholds/reset` - Reset to defaults

**Weights:**
- `GET /weights` - List all category weights
- `GET /weights/{category}` - Get specific weight
- `PUT /weights/{category}` - Update weight (validates sum)
- `POST /weights/reset` - Reset to defaults
- `GET /weights/validate` - Validate weights sum to 1.00

**Status:**
- `GET /status` - Overall configuration status

**Feed Integration:**
- Feeds automatically include `admiralty_code` field in responses
- Calculated on-the-fly from `quality_score`

### Frontend Components

#### 1. Display Components

**AdmiraltyCodeBadge** (`frontend/src/components/shared/AdmiraltyCodeBadge.tsx`)
```typescript
interface AdmiraltyCodeBadgeProps {
  admiraltyCode: AdmiraltyCodeData;
  showLabel?: boolean;  // Show "B: Usually Reliable" vs just "B"
  className?: string;
}

// Usage:
<AdmiraltyCodeBadge admiraltyCode={feed.admiralty_code} />
```

#### 2. Configuration Components

**AdmiraltyCodeConfig** (`frontend/src/features/feeds/components/AdmiraltyCodeConfig.tsx`)
- Manage A-F thresholds
- Edit min_score, label, description, color
- Reset to defaults

**CategoryWeightsConfig** (`frontend/src/features/feeds/components/CategoryWeightsConfig.tsx`)
- Configure category weights
- Real-time validation (sum must equal 1.00)
- Visual progress bar showing total
- Reset to defaults

#### 3. Admin Interface

**Location:** `http://localhost:3000/admin/services/feed-service`

**Configuration Tab:**
- Split into two cards (side-by-side)
- Left: Admiralty Code Thresholds
- Right: Quality Score Weights

## Configuration

### Default Thresholds

```yaml
thresholds:
  A: { min_score: 90, label: "Completely Reliable", color: "green" }
  B: { min_score: 75, label: "Usually Reliable", color: "blue" }
  C: { min_score: 60, label: "Fairly Reliable", color: "yellow" }
  D: { min_score: 40, label: "Not Usually Reliable", color: "orange" }
  E: { min_score: 20, label: "Unreliable", color: "red" }
  F: { min_score: 0,  label: "Cannot Be Judged", color: "gray" }
```

### Default Weights

```yaml
weights:
  credibility: { weight: 0.40, description: "Tier assessment and reputation" }
  editorial:   { weight: 0.25, description: "Fact-checking and standards" }
  trust:       { weight: 0.20, description: "External ratings (NewsGuard, etc.)" }
  health:      { weight: 0.15, description: "Technical reliability" }
```

### Environment Variables

No additional environment variables required. Configuration stored in database.

## Usage Examples

### API Usage

**Get all thresholds:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/admiralty-codes/thresholds
```

**Update threshold:**
```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"min_score": 85, "label": "Very Reliable"}' \
  http://localhost:8101/api/v1/admiralty-codes/thresholds/B
```

**Update weight:**
```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"weight": 0.45, "description": "Updated weight"}' \
  http://localhost:8101/api/v1/admiralty-codes/weights/credibility
```

**Validate weights:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/admiralty-codes/weights/validate

# Response:
# {"is_valid": true, "total": "1.00", "message": "Weights are valid"}
```

**Get feed with Admiralty Code:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/feeds

# Response includes:
# {
#   "id": "...",
#   "name": "DW English",
#   "quality_score": 85,
#   "admiralty_code": {
#     "code": "B",
#     "label": "Usually Reliable",
#     "color": "blue"
#   }
# }
```

### Frontend Usage

**Display badge:**
```typescript
import { AdmiraltyCodeBadge } from '@/components/shared/AdmiraltyCodeBadge';

function FeedCard({ feed }: { feed: Feed }) {
  return (
    <div>
      <h3>{feed.name}</h3>
      <AdmiraltyCodeBadge admiraltyCode={feed.admiralty_code} />
    </div>
  );
}
```

**Use configuration hooks:**
```typescript
import { useAdmiraltyThresholds, useUpdateAdmiraltyThreshold } from '@/features/feeds/api';

function ThresholdEditor() {
  const { data: thresholds } = useAdmiraltyThresholds();
  const updateThreshold = useUpdateAdmiraltyThreshold();

  const handleUpdate = async (code: string) => {
    await updateThreshold.mutateAsync({
      code,
      updates: { min_score: 80 }
    });
  };
}
```

## Validation Rules

1. **Thresholds:**
   - Code must be A, B, C, D, E, or F
   - min_score must be 0-100
   - Codes must be unique
   - Thresholds should be in descending order

2. **Weights:**
   - Category must be credibility, editorial, trust, or health
   - Weight must be 0.00-1.00
   - **All weights must sum to exactly 1.00**
   - Categories must be unique

3. **Quality Score:**
   - Must be 0-100
   - Null scores result in code "F"

## Performance Considerations

### Caching Strategy
- Thresholds cached in-memory after first load
- Weights cached in-memory after first load
- Cache invalidated on updates
- Cache shared across requests (class-level)

### Database Optimization
- Indexed on `code` and `min_score DESC`
- Small tables (6 thresholds, 4 weights)
- Reads >> Writes (configuration changes rare)

### Frontend Optimization
- React Query caching (10s stale time)
- Optimistic updates on mutations
- Automatic cache invalidation

## Monitoring

### Key Metrics
- Threshold/weight update frequency
- Validation failures
- Cache hit rate
- API response times

### Logging
```python
logger.info(f"Updated threshold {code}: {min_score}")
logger.warning(f"Weights validation failed: {total}")
logger.error(f"Failed to update weight {category}: {error}")
```

## Migration

**File:** `services/feed-service/alembic/versions/20251021_007_add_admiralty_code_config.py`

**Applies:**
- Creates `admiralty_code_thresholds` table
- Creates `quality_score_weights` table
- Inserts default thresholds (A-F)
- Inserts default weights (4 categories)

**Rollback:**
- Drops both tables
- No data loss (configuration is restorable from defaults)

## Testing

### Backend Tests
```bash
# Service layer tests
pytest services/feed-service/tests/test_admiralty_code_service.py

# API endpoint tests
pytest services/feed-service/tests/test_admiralty_codes_api.py
```

### Frontend Tests
```bash
# Component tests
npm test -- AdmiraltyCodeBadge
npm test -- AdmiraltyCodeConfig
npm test -- CategoryWeightsConfig
```

### Manual Testing
1. Navigate to `/admin/services/feed-service`
2. Click "Configuration" tab
3. Edit a threshold, verify validation
4. Edit weights, ensure sum = 1.00
5. Check feeds list shows badges correctly

## Security Considerations

- **Authentication:** All endpoints require valid JWT
- **Authorization:** Admin role required for configuration changes
- **Validation:** Strict input validation on all updates
- **SQL Injection:** Protected by SQLAlchemy ORM
- **Rate Limiting:** Inherited from FastAPI middleware

## Future Enhancements

- [ ] Batch threshold updates
- [ ] Historical tracking of configuration changes
- [ ] Per-user custom thresholds
- [ ] Export/import configuration
- [ ] Audit log for administrative changes
- [ ] Webhook notifications on config changes
- [ ] Multi-language threshold labels

## Troubleshooting

### Issue: Weights don't sum to 1.00
**Solution:** Use validation endpoint, adjust weights proportionally
```bash
curl http://localhost:8101/api/v1/admiralty-codes/weights/validate
# Adjust weights and retry
```

### Issue: Badge not showing
**Checklist:**
1. Feed has `quality_score` set
2. Frontend successfully loaded thresholds
3. Check browser console for errors
4. Verify API returns `admiralty_code` field

### Issue: Configuration not persisting
**Checklist:**
1. Check database connection
2. Verify migration applied (`alembic current`)
3. Check transaction commits
4. Review service logs

## References

- [NATO Admiralty Code](https://en.wikipedia.org/wiki/Admiralty_code)
- Feed Service API Documentation
- Quality Score Calculation Documentation
- Admin Interface Guide

## Change Log

### 2025-10-21 - v1.0.0 (Initial Release)
- Implemented Admiralty Code system
- Created database schema and migration
- Added API endpoints for configuration
- Built admin interface components
- Integrated with feed display
- Fixed FastAPI route ordering bug

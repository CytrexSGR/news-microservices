# Feed Quality Score System

**Status:** ✅ Implemented (2025-10-21)
**Version:** 1.0
**Services:** Feed Service, Research Service
**Components:** Database, Backend API, Frontend UI

## Overview

The Feed Quality Score System provides a comprehensive, automated quality assessment for RSS feeds based on multiple dimensions including credibility, editorial standards, external trust ratings, and operational health. Scores range from 0-100 and are automatically calculated whenever feed assessment data changes.

## Motivation

### Problem
- Users need to quickly evaluate feed reliability and quality
- Manual assessment of editorial standards is time-consuming
- No unified metric combining multiple quality dimensions
- Difficult to compare feeds objectively

### Solution
- Automated scoring algorithm combining 4 key dimensions
- Real-time calculation via database triggers
- Visual quality indicators in UI
- Transparent, documented scoring methodology

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Feed Quality Score System                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Research Service│────────▶│  Assessment Data │         │
│  │  (Perplexity AI) │         │  (feeds table)   │         │
│  └──────────────────┘         └────────┬─────────┘         │
│                                         │                     │
│                                         ▼                     │
│                              ┌──────────────────────┐        │
│                              │  PostgreSQL Trigger  │        │
│                              │  calculate_feed_     │        │
│                              │  quality_score()     │        │
│                              └──────────┬───────────┘        │
│                                         │                     │
│                                         ▼                     │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Feed Service API│────────▶│  quality_score   │         │
│  │  GET /feeds      │         │  column          │         │
│  └──────────────────┘         └────────┬─────────┘         │
│                                         │                     │
│                                         ▼                     │
│                              ┌──────────────────────┐        │
│                              │  Frontend UI         │        │
│                              │  QualityScoreBadge   │        │
│                              └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

**New Column:**
```sql
ALTER TABLE feeds ADD COLUMN quality_score INTEGER;
```

**Trigger:**
```sql
CREATE TRIGGER trigger_update_feed_quality_score
    BEFORE INSERT OR UPDATE ON feeds
    FOR EACH ROW
    EXECUTE FUNCTION update_feed_quality_score();
```

**Index:**
```sql
CREATE INDEX idx_feeds_quality_score ON feeds(quality_score DESC);
```

## Scoring Methodology

### Total Score: 0-100 Points

#### 1. Credibility Foundation (40 points)
Base score determined by credibility tier from Feed Source Assessment:

| Tier | Points | Description |
|------|--------|-------------|
| tier_1 | 40 | Premier sources (NYT, BBC, DW, Reuters) |
| tier_2 | 30 | Established regional/specialized sources |
| tier_3 | 20 | Emerging or niche sources |
| unassessed | 10 | Default for feeds without assessment |

**Rationale:** Credibility tier represents institutional reputation and is the strongest predictor of overall quality.

#### 2. Editorial Quality (25 points)

Based on `editorial_standards` JSONB field:

**Fact Checking Level** (10 points):
- `high`: 10 points - Rigorous multi-source verification
- `medium`: 7 points - Standard journalistic fact-checking
- `low`: 3 points - Minimal verification processes

**Corrections Policy** (8 points):
- `transparent`: 8 points - Public corrections with clear attribution
- `adequate`: 5 points - Corrections published but less visible
- `poor`: 2 points - Inconsistent or absent correction policy

**Source Attribution** (7 points):
- `excellent`: 7 points - Comprehensive source citations
- `good`: 5 points - Standard source attribution
- `fair`: 3 points - Limited source information

**Rationale:** Editorial standards directly impact content reliability and trustworthiness.

#### 3. External Trust Ratings (20 points)

Based on `trust_ratings` JSONB field from independent fact-checking organizations:

**NewsGuard Score** (8 points):
- Scaled: `(newsguard_score / 100) * 8`
- Range: 0-8 points
- Source: NewsGuard Technologies journalistic criteria

**AllSides Media Bias Rating** (7 points):
- `center`: 7 points - Minimal partisan bias
- `lean left/lean right`: 5 points - Slight bias
- `left/right`: 3 points - Clear partisan lean

**Media Bias/Fact Check Rating** (5 points):
- `least biased` or `high`: 5 points
- `mostly factual` or `mostly-factual`: 3 points
- `mixed`: 1 point

**Rationale:** Third-party ratings provide independent validation of quality claims.

#### 4. Operational Health (15 points)

**Health Score Component** (10 points):
- Scaled: `(health_score / 100) * 10`
- Based on feed reliability metrics

**Failure Penalty** (up to -5 points):
- `-1 point` per consecutive failure
- Capped at -5 points maximum
- Reflects recent operational issues

**Rationale:** Even high-quality sources lose value if technically unreliable.

### Score Categories

| Category | Range | Badge Color | Description |
|----------|-------|-------------|-------------|
| 🏆 Premium | 85-100 | Purple | Highest quality, tier 1 sources with excellent standards |
| ✅ Trusted | 70-84 | Blue | Reliable sources with good editorial practices |
| ⚠️ Moderate | 50-69 | Yellow | Acceptable quality, use with awareness |
| ❌ Limited | 0-49 | Orange | Use with caution, verify information |

## Implementation Details

### Database Function

**Location:** `/services/feed-service/alembic/versions/add_quality_score_function.sql`

**Function Signature:**
```sql
calculate_feed_quality_score(
    p_credibility_tier VARCHAR,
    p_reputation_score INTEGER,
    p_editorial_standards JSONB,
    p_trust_ratings JSONB,
    p_health_score INTEGER,
    p_consecutive_failures INTEGER
) RETURNS INTEGER
```

**Properties:**
- `IMMUTABLE` - Pure function, same inputs always produce same output
- Null-safe - Handles missing assessment data gracefully
- Score clamped to 0-100 range

### Backend API

**Endpoint:** `GET /api/v1/feeds`

**Response Schema:**
```json
{
  "id": "uuid",
  "name": "Feed Name",
  "quality_score": 85,
  "health_score": 100,
  "assessment": {
    "credibility_tier": "tier_1",
    "reputation_score": 90,
    "quality_score": 85,
    "editorial_standards": {...},
    "trust_ratings": {...}
  }
}
```

**Changes:**
- Added `quality_score` to `FeedResponse` schema
- Added `quality_score` to `FeedAssessmentData` schema
- Updated `_build_assessment_data()` helper function
- Modified feed list endpoint to include `quality_score` in response

### Frontend UI

**Component:** `QualityScoreBadge.tsx`

**Features:**
- Color-coded badges based on score category
- Tooltip with full score and category label
- Graceful handling of unassessed feeds ("Not assessed")
- Optional `showLabel` prop for detailed display

**Integration:**
- Added to `FeedListPage.tsx` as new "Quality" column
- Appears between "Health" and "Last Fetched" columns

## Usage Examples

### Database Query
```sql
-- Get feeds sorted by quality
SELECT name, quality_score, credibility_tier
FROM feeds
WHERE quality_score IS NOT NULL
ORDER BY quality_score DESC;
```

### API Request
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/feeds \
  | jq '.[] | {name, quality_score}'
```

### Frontend Component
```tsx
import { QualityScoreBadge } from '@/features/feeds/components/QualityScoreBadge';

<QualityScoreBadge score={feed.quality_score} showLabel={true} />
```

## Recalculation Triggers

Quality scores are automatically recalculated when:

1. **Feed Assessment Completed** - Research service updates assessment data
2. **Health Score Changes** - Feed fetcher updates operational metrics
3. **Manual Update** - Admin modifies assessment fields
4. **Bulk Updates** - Migration scripts or data imports

### Force Recalculation
```sql
UPDATE feeds
SET quality_score = calculate_feed_quality_score(
    credibility_tier,
    reputation_score,
    editorial_standards,
    trust_ratings,
    health_score,
    consecutive_failures
)
WHERE credibility_tier IS NOT NULL;
```

## Current Scores (2025-10-21)

| Feed | Score | Category | Tier | Reputation |
|------|-------|----------|------|------------|
| BBC News | 88 | 🏆 Premium | tier_1 | 95 |
| DW English | 85 | 🏆 Premium | tier_1 | 90 |
| Der Standard | 67 | ⚠️ Moderate | tier_1 | 90 |
| Middle East Eye | 52 | ⚠️ Moderate | tier_2 | 60 |
| AllAfrica | 52 | ⚠️ Moderate | tier_2 | 75 |

**Note:** Der Standard scores lower despite tier_1 due to missing external trust ratings from NewsGuard/AllSides.

## Limitations & Future Improvements

### Current Limitations

1. **Missing Data Handling**
   - Feeds without assessments default to score 10
   - Missing external ratings reduce total possible score
   - No interpolation for partial data

2. **Static Weights**
   - Component weights are fixed (40/25/20/15)
   - No domain-specific adjustments
   - One-size-fits-all approach

3. **Temporal Aspects**
   - No decay function for outdated assessments
   - Recent changes not weighted more heavily
   - Historical trends not considered

### Planned Improvements

1. **Dynamic Weighting** (v2.0)
   - Machine learning model to optimize weights
   - User feedback integration
   - Domain-specific weight profiles

2. **Temporal Scoring** (v2.0)
   - Assessment freshness factor
   - Trend analysis (improving/declining)
   - Seasonal reliability adjustments

3. **Advanced Metrics** (v3.0)
   - Content quality analysis from articles
   - Reader engagement correlation
   - Fact-check failure rate tracking

4. **User Customization** (v3.0)
   - Personal quality preferences
   - Custom weight configurations
   - Trust network effects

## Testing

### Unit Tests
```bash
# Test scoring function with various inputs
PGPASSWORD=your_db_password psql -h localhost -U news_user -d news_mcp \
  -f services/feed-service/tests/test_quality_score.sql
```

### Integration Tests
```bash
# Test API response includes quality_score
pytest services/feed-service/tests/test_feeds_api.py::test_feed_list_includes_quality_score
```

### Frontend Tests
```bash
# Test QualityScoreBadge rendering
cd frontend && npm test -- QualityScoreBadge.test.tsx
```

## Monitoring

### Key Metrics

1. **Score Distribution**
   ```sql
   SELECT
     CASE
       WHEN quality_score >= 85 THEN 'Premium'
       WHEN quality_score >= 70 THEN 'Trusted'
       WHEN quality_score >= 50 THEN 'Moderate'
       ELSE 'Limited'
     END as category,
     COUNT(*) as count
   FROM feeds
   WHERE quality_score IS NOT NULL
   GROUP BY category;
   ```

2. **Assessment Coverage**
   ```sql
   SELECT
     COUNT(*) FILTER (WHERE quality_score IS NOT NULL) as assessed,
     COUNT(*) FILTER (WHERE quality_score IS NULL) as unassessed,
     ROUND(100.0 * COUNT(*) FILTER (WHERE quality_score IS NOT NULL) / COUNT(*), 1) as coverage_percent
   FROM feeds;
   ```

3. **Score Changes**
   - Track in `feed_assessment_history` table
   - Alert on significant drops (>10 points)
   - Monitor average score trend

## References

- [Feed Source Assessment Documentation](./feed-source-assessment.md)
- [Research Service API](../api/research-service-api.md)
- [Feed Service API](../api/feed-service-api.md)
- [ADR-007: Feed Quality Scoring Methodology](../decisions/ADR-007-feed-quality-scoring.md)

## Changelog

### Version 1.0 (2025-10-21)
- Initial implementation
- 4-component scoring algorithm
- Database triggers for auto-calculation
- Frontend UI integration
- Documentation completed

---

**Maintained by:** Feed Service Team
**Last Updated:** 2025-10-21
**Related ADRs:** ADR-007

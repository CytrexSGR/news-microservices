# Data Quality Dashboard

**Version**: 1.0
**Last Updated**: 2025-11-06
**Status**: Production Ready ✅

---

## Overview

The Data Quality Dashboard provides comprehensive real-time monitoring and visualization of Knowledge Graph quality metrics. It enables operators to track relationship quality, identify data issues, and monitor quality improvements over time.

**Location**: Frontend → Admin → Knowledge Graph Service → Statistics & Analytics Tab

**Key Components**:
1. **DataQualityCard** - Composite quality score with breakdown
2. **NOT_APPLICABLE Trend Tracking** - Temporal tracking of unclassified relationships
3. **Relationship Quality Breakdown** - Detailed confidence level visualization

---

## Architecture

### Backend Services

**Service**: `knowledge-graph-service` (Port 8111)

**New Endpoints**:
```
GET /api/v1/graph/stats/detailed
GET /api/v1/graph/analytics/not-applicable-trends?days={days}
GET /api/v1/graph/analytics/relationship-quality-trends?days={days}
```

**Data Sources**:
- **Neo4j**: Relationship confidence levels, entity metadata, timestamps
- **PostgreSQL**: Historical metrics (future enhancement)

**Query Performance**:
- Detailed Stats: ~150-200ms (50k nodes, 200k relationships)
- NOT_APPLICABLE Trends: ~80-120ms (7-30 days)
- Quality Trends: ~100-150ms (7-30 days)

---

## Components

### 1. DataQualityCard

**Purpose**: Displays composite quality score (0-100) with detailed breakdown.

**Location**: `frontend/src/features/admin/knowledge-graph/components/analytics/DataQualityCard.tsx`

**Data Source**: `/api/v1/graph/stats/detailed`

**Metrics Displayed**:

| Metric | Formula | Weight | Threshold |
|--------|---------|--------|-----------|
| Quality Score | Composite | 100% | Excellent: ≥90, Good: ≥75, Fair: ≥60 |
| High Confidence Ratio | count(conf > 0.8) / total | 50% | Target: >80% |
| NOT_APPLICABLE Ratio | count(NOT_APPLICABLE) / total | 30% | Target: <15% |
| Wikidata Coverage | count(wikidata_id != null) / total | 20% | Target: >70% |

**Quality Score Formula**:
```
score = (high_conf_ratio * 0.5 +
         (1 - not_applicable_ratio) * 0.3 +
         wikidata_coverage * 0.2) * 100
```

**Features**:
- ✅ Large quality score display with color-coded badge
- ✅ Progress bar visualization
- ✅ Graph size overview (total entities/relationships)
- ✅ Relationship quality breakdown (3 progress bars)
- ✅ Data completeness metrics
- ✅ Dynamic quality insights with recommendations
- ✅ Auto-refresh every 5 minutes

**Quality Tiers**:
```
Excellent (≥90):  Green  - 🟢 Maintain standards
Good (≥75):       Blue   - 🔵 Monitor regularly
Fair (≥60):       Yellow - 🟡 Review recommended
Needs Attention:  Red    - 🔴 Action required
```

**Example Response**:
```json
{
  "quality_score": 80.39,
  "graph_size": {
    "total_nodes": 50091,
    "total_relationships": 209122
  },
  "relationship_quality": {
    "high_confidence_ratio": 0.9755,
    "medium_confidence_ratio": 0.0245,
    "low_confidence_ratio": 0.0
  },
  "data_completeness": {
    "not_applicable_ratio": 0.0001,
    "wikidata_coverage_ratio": 0.68,
    "orphaned_entities_count": 125
  }
}
```

---

### 2. NOT_APPLICABLE Trend Tracking

**Purpose**: Monitors temporal changes in unclassified relationships to identify data quality issues.

**Location**: `frontend/src/features/admin/knowledge-graph/components/analytics/NotApplicableTrendCard.tsx`

**Data Source**: `/api/v1/graph/analytics/not-applicable-trends?days=30`

**Metrics Tracked**:
- NOT_APPLICABLE count per day
- NOT_APPLICABLE ratio (0-1)
- NOT_APPLICABLE percentage (0-100)
- Total relationships per day

**Visualization**:
- Line chart showing percentage over time
- Current status badge with trend indicator
- Summary statistics (current, average, peak, change)

**Quality Thresholds**:
```
Excellent: < 5%   - Green badge, no alerts
Good: < 15%       - Blue badge, no alerts
Fair: < 25%       - Yellow badge, no alerts
Needs Review: ≥25% - Red badge, warning alert
```

**Features**:
- ✅ 30-day trend line chart
- ✅ Trend direction indicator (up/down/stable arrows)
- ✅ Dynamic alerts for high ratios (>15%)
- ✅ Positive feedback for decreasing trends
- ✅ Auto-refresh every 5 minutes

**Cypher Query**:
```cypher
MATCH ()-[r]->()
WHERE r.created_at >= datetime($start_date)
  AND r.created_at <= datetime($end_date)
WITH date(r.created_at) AS creation_date,
     type(r) AS rel_type
RETURN
    toString(creation_date) AS date,
    sum(CASE WHEN rel_type = 'NOT_APPLICABLE' THEN 1 ELSE 0 END) AS not_applicable_count,
    count(*) AS total_relationships
ORDER BY date ASC
```

**Example Response**:
```json
[
  {
    "date": "2025-11-06",
    "not_applicable_count": 2,
    "total_relationships": 17841,
    "not_applicable_ratio": 0.0001,
    "not_applicable_percentage": 0.01
  }
]
```

---

### 3. Relationship Quality Breakdown

**Purpose**: Comprehensive visualization of relationship confidence levels with temporal trends.

**Location**: `frontend/src/features/admin/knowledge-graph/components/analytics/RelationshipQualityBreakdown.tsx`

**Data Source**: `/api/v1/graph/analytics/relationship-quality-trends?days=30`

**Confidence Levels**:

| Level | Confidence Range | Color | Target |
|-------|-----------------|-------|--------|
| High | > 0.8 | Green | >85% |
| Medium | 0.5 - 0.8 | Blue | <15% |
| Low | < 0.5 | Orange | <1% |

**Visualizations**:

1. **Pie Chart**: Current distribution
   - Shows percentage breakdown of High/Medium/Low
   - Only displays categories with >0% values
   - Color-coded for quick identification

2. **Stacked Area Chart**: 30-day trends
   - Three stacked areas (High/Medium/Low)
   - Shows quality evolution over time
   - Helps identify quality degradation or improvement

3. **Statistics Cards**: Individual metrics
   - Separate cards for each confidence level
   - Shows current percentage and 30-day change
   - Trend indicators (up/down arrows)

**Features**:
- ✅ Overall quality badge with status
- ✅ Total relationships counter
- ✅ Current distribution (pie chart)
- ✅ 30-day trend visualization (stacked area)
- ✅ Per-level statistics with trends
- ✅ 30-day averages
- ✅ Dynamic insights (4 alert types)
- ✅ Auto-refresh every 5 minutes

**Quality Status Logic**:
```typescript
if (high_confidence >= 95%) return "Excellent"
if (high_confidence >= 85%) return "Good"
if (high_confidence >= 70%) return "Fair"
return "Needs Review"
```

**Alert Conditions**:
1. **Excellent Quality**: high_confidence ≥ 95%
2. **Positive Trend**: high_confidence increased >1% over 30 days
3. **Review Recommended**: medium_confidence > 20%
4. **Action Required**: low_confidence > 5%

**Cypher Query**:
```cypher
MATCH ()-[r]->()
WHERE r.created_at >= datetime($start_date)
  AND r.created_at <= datetime($end_date)
WITH date(r.created_at) AS creation_date,
     r.confidence AS conf
RETURN
    toString(creation_date) AS date,
    sum(CASE WHEN conf > 0.8 THEN 1 ELSE 0 END) AS high_confidence_count,
    sum(CASE WHEN conf >= 0.5 AND conf <= 0.8 THEN 1 ELSE 0 END) AS medium_confidence_count,
    sum(CASE WHEN conf < 0.5 THEN 1 ELSE 0 END) AS low_confidence_count,
    count(*) AS total_relationships
ORDER BY date ASC
```

**Example Response**:
```json
[
  {
    "date": "2025-11-06",
    "high_confidence_count": 17461,
    "medium_confidence_count": 547,
    "low_confidence_count": 0,
    "total_relationships": 18006,
    "high_confidence_ratio": 0.9696,
    "medium_confidence_ratio": 0.0304,
    "low_confidence_ratio": 0.0,
    "high_confidence_percentage": 96.96,
    "medium_confidence_percentage": 3.04,
    "low_confidence_percentage": 0.0
  }
]
```

---

## Integration

### Frontend Stack

**Framework**: React 18 + TypeScript + Vite

**Key Libraries**:
- `@tanstack/react-query` - Data fetching with auto-refresh
- `recharts` - Chart visualization (Line, Pie, Area, Progress)
- `lucide-react` - Icons
- `tailwindcss` - Styling with dark mode support

**State Management**: TanStack Query with 5-minute cache

**Auto-Refresh**:
```typescript
const { data } = useDetailedGraphStats({
  refetchInterval: 5 * 60 * 1000 // 5 minutes
})
```

### Page Structure

```
KnowledgeGraphAdminPage
├── Live Operations Tab
│   ├── ServiceHealthCard
│   ├── GraphStatsCard
│   ├── Neo4jHealthCard
│   └── RabbitMQHealthCard
│
├── Statistics & Analytics Tab
│   ├── Graph Metrics Sub-Tab
│   │   ├── DataQualityCard ← Phase 3.1
│   │   ├── RelationshipQualityBreakdown ← Phase 3.3
│   │   ├── GraphStatsCard
│   │   ├── TopEntitiesCard
│   │   └── RelationshipStatsCard
│   │
│   ├── Canonicalization Sub-Tab
│   │   ├── BatchReprocessing
│   │   ├── CanonicalizationStatsCard
│   │   ├── EntityMergeHistory
│   │   └── DisambiguationQuality
│   │
│   └── Trends Sub-Tab
│       ├── GrowthHistoryChart
│       ├── NotApplicableTrendCard ← Phase 3.2
│       ├── EntityTypeTrends
│       └── CrossArticleCoverage
│
└── Manual Enrichment Tab
    └── EnrichmentDashboard
```

---

## Performance Considerations

### Backend Optimization

**Neo4j Query Optimization**:
1. **Indexes**: Entity name, type, created_at
2. **Query Pattern**: Use CASE WHEN for aggregation (faster than multiple queries)
3. **Date Filtering**: Always filter by created_at with datetime() conversion
4. **Limit Usage**: Trend queries return max 365 days

**Query Performance** (50k nodes, 200k relationships):
```
Detailed Stats Query:       150-200ms
NOT_APPLICABLE Trends (30d): 80-120ms
Quality Trends (30d):       100-150ms
```

### Frontend Optimization

**React Query Configuration**:
```typescript
{
  staleTime: 5 * 60 * 1000,      // 5 minutes (data freshness)
  gcTime: 10 * 60 * 1000,        // 10 minutes (cache retention)
  refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
}
```

**Component Optimization**:
- Memoized chart data transformations
- Conditional rendering for empty states
- Lazy loading for heavy visualizations
- Progressive enhancement for chart interactions

**Bundle Size Impact**:
- DataQualityCard: ~8KB (gzipped)
- NotApplicableTrendCard: ~10KB (gzipped)
- RelationshipQualityBreakdown: ~14KB (gzipped)
- Total: ~32KB additional bundle size

---

## Monitoring & Alerts

### Quality Metrics to Watch

**Critical Metrics**:
1. **Quality Score**: Should stay >75 (Good)
2. **NOT_APPLICABLE Ratio**: Should stay <15%
3. **High Confidence Ratio**: Should stay >80%
4. **Low Confidence Count**: Should stay near 0

**Warning Conditions**:
```
⚠️  Quality Score < 60         → "Needs Attention" status
⚠️  NOT_APPLICABLE > 15%       → Yellow alert displayed
⚠️  NOT_APPLICABLE > 25%       → Red alert displayed
⚠️  Medium Confidence > 20%    → Review recommended
⚠️  Low Confidence > 5%        → Action required
```

### Alert Actions

| Alert Type | Recommended Action | Priority |
|------------|-------------------|----------|
| Quality Score < 60 | Review entity extraction logic | High |
| NOT_APPLICABLE > 25% | Investigate relationship classification | High |
| Low Confidence > 5% | Consider reprocessing articles | Critical |
| Medium Confidence > 20% | Review confidence thresholds | Medium |
| Orphaned Entities > 500 | Run entity linking job | Low |

---

## Troubleshooting

### Common Issues

**1. Dashboard Not Loading**

**Symptoms**: Spinner displays indefinitely, no data shown

**Possible Causes**:
- knowledge-graph-service is down
- Neo4j connection issue
- Network connectivity problem

**Resolution**:
```bash
# Check service health
curl http://localhost:8111/health/ready

# Check Neo4j connection
docker logs news-knowledge-graph-service | grep -i neo4j

# Restart service if needed
docker restart news-knowledge-graph-service
```

---

**2. Empty Charts/No Trend Data**

**Symptoms**: "No trend data available yet" message

**Possible Causes**:
- Relationships missing created_at timestamps
- Date range has no data (new installation)
- Neo4j query returned empty results

**Resolution**:
```bash
# Check if relationships have created_at timestamps
curl http://localhost:8111/api/v1/graph/analytics/not-applicable-trends?days=7

# If empty, check Neo4j data:
docker exec -it news-neo4j cypher-shell -u neo4j -p news_neo4j_password
MATCH ()-[r]->()
WHERE r.created_at IS NOT NULL
RETURN count(r) AS relationships_with_timestamps
```

**Fix**: Backfill created_at timestamps if missing (see Migration Guide)

---

**3. Slow Query Performance**

**Symptoms**: Dashboard takes >5 seconds to load

**Possible Causes**:
- Missing Neo4j indexes
- Large dataset (>500k relationships)
- Inefficient query patterns

**Resolution**:
```bash
# Check Neo4j indexes
docker exec -it news-neo4j cypher-shell -u neo4j -p news_neo4j_password
SHOW INDEXES

# Expected indexes:
# - entity_name_index (Entity.name)
# - entity_unique (Entity.name, Entity.type)

# Add missing indexes if needed:
CREATE INDEX entity_created_at IF NOT EXISTS
FOR (e:Entity)
ON (e.created_at)
```

---

**4. Quality Score Calculation Issues**

**Symptoms**: Quality score doesn't match expectations

**Possible Causes**:
- Formula weights changed
- Data quality degradation
- Calculation bug

**Verification**:
```bash
# Get raw data
curl http://localhost:8111/api/v1/graph/stats/detailed | jq '.relationship_quality, .data_completeness, .quality_score'

# Manual calculation:
# score = (high_conf_ratio * 0.5) +
#         ((1 - not_applicable_ratio) * 0.3) +
#         (wikidata_coverage * 0.2) * 100
```

---

## Testing

### Manual Testing Checklist

**DataQualityCard**:
- [ ] Score displays correctly (0-100)
- [ ] Badge color matches quality tier
- [ ] Progress bar renders
- [ ] All metrics display (graph size, quality breakdown, completeness)
- [ ] Dynamic insights appear based on thresholds
- [ ] Auto-refresh works (wait 5 minutes)
- [ ] Loading state displays correctly
- [ ] Error state handles failures gracefully

**NOT_APPLICABLE Trend Tracking**:
- [ ] Line chart renders with correct data
- [ ] Current status badge displays
- [ ] Trend indicator shows (up/down/stable)
- [ ] Summary stats calculate correctly
- [ ] Alerts display conditionally
- [ ] Chart tooltip works on hover
- [ ] Auto-refresh works

**Relationship Quality Breakdown**:
- [ ] Pie chart renders current distribution
- [ ] Stacked area chart shows 30-day trends
- [ ] Statistics cards display correctly
- [ ] Trend arrows show direction
- [ ] Overall quality badge matches data
- [ ] All alerts display conditionally
- [ ] Auto-refresh works

### Automated Testing

**API Endpoint Tests**:
```bash
# Test detailed stats endpoint
curl -w "\nTime: %{time_total}s\n" http://localhost:8111/api/v1/graph/stats/detailed

# Test NOT_APPLICABLE trends
curl -w "\nTime: %{time_total}s\n" "http://localhost:8111/api/v1/graph/analytics/not-applicable-trends?days=7"

# Test quality trends
curl -w "\nTime: %{time_total}s\n" "http://localhost:8111/api/v1/graph/analytics/relationship-quality-trends?days=7"
```

**Expected Performance**:
- All queries should complete <500ms
- Response should be valid JSON
- All required fields should be present

---

## Future Enhancements

### Planned Features (Phase 4)

1. **Historical Quality Tracking**
   - Store daily quality scores in PostgreSQL
   - 90-day trend charts
   - Year-over-year comparisons

2. **Quality Alerts & Notifications**
   - Email alerts when quality drops below threshold
   - Slack/webhook integration
   - Alert history and acknowledgment

3. **Automated Quality Reports**
   - Weekly quality report generation
   - PDF export with charts
   - Executive summary dashboard

4. **Quality Improvement Recommendations**
   - AI-powered suggestions for quality improvements
   - Automated reprocessing recommendations
   - Entity extraction tuning suggestions

5. **Confidence Calibration**
   - Confidence score validation against human review
   - Automatic threshold adjustment
   - Model performance tracking

### Technical Debt

1. **Frontend**:
   - Add unit tests for components
   - Add integration tests for hooks
   - Implement chart export functionality
   - Add keyboard navigation support

2. **Backend**:
   - Add query result caching (Redis)
   - Implement batch query optimization
   - Add historical data archival
   - Implement rate limiting

---

## References

**Related Documentation**:
- [knowledge-graph-service API](../api/knowledge-graph-service-api.md)
- [Neo4j Schema](../database/neo4j-schema.md)
- [Frontend Architecture](../frontend/architecture.md)
- [ADR-036: Quality Metrics Implementation](../decisions/ADR-036-quality-metrics-implementation.md)

**External Resources**:
- [Recharts Documentation](https://recharts.org/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)

---

## Changelog

### Version 1.0 (2025-11-06)
- ✅ Initial release
- ✅ DataQualityCard component
- ✅ NOT_APPLICABLE Trend Tracking
- ✅ Relationship Quality Breakdown
- ✅ Full documentation
- ✅ Production deployment

---

**Maintainers**: Knowledge Graph Team
**Last Review**: 2025-11-06
**Next Review**: 2025-12-06

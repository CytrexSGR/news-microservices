# Feed Quality V2 - Master-Detail View

**Status:** ✅ Implemented
**Date:** 2025-11-06
**Version:** Phase 1.2
**Related:** [ADR-030: Feed Quality System V2](../decisions/ADR-030-feed-quality-system-v2.md)

---

## Overview

The Feed Quality V2 Master-Detail View provides a comprehensive interface for analyzing feed quality across all feeds. It consists of two sections:

1. **Master View (Section 1):** Scrollable table showing all feeds with key quality metrics
2. **Detail View (Section 2):** Comprehensive quality analysis for the selected feed

---

## Features

### Section 1: Feed Quality Overview Table

**Location:** Always visible at the top of the Quality V2 tab

**Displays:**
- Sortable table of all active feeds (max height: 500px, scrollable)
- 5 key columns:
  1. **Feed Name** - With coverage %, confidence level, trend indicator
  2. **Quality Score** - 0-100 numerical score
  3. **Admiralty Code** - A-F reliability rating with label
  4. **Total Articles** - Total article count
  5. **Last 24h** - Articles added in last 24 hours

**Interactions:**
- ✅ Click any row to view detailed analysis
- ✅ Sort by any column (ascending/descending)
- ✅ Visual selection feedback (blue left border, chevron rotation)
- ✅ Hover effects for better UX

**Features:**
- Null-safe: Shows "N/A" for feeds with insufficient data
- Trend indicators: 📈 (improving) / 📉 (declining) shown in feed name
- Auto-scrollable: Fixed height prevents endless scrolling

### Section 2: Detailed Quality View

**Location:** Appears directly below the table when a feed is selected

**Displays:**
- **QualityOverviewCardV2**: Overall score, Admiralty code, confidence, trend
- **QualityComponentsChart**: Radar chart with 4 component breakdowns
- **QualityDistributionChart**: Article quality distribution
- **QualityRecommendations**: Actionable recommendations based on metrics

**Loading States:**
- Spinner while loading detailed metrics
- Error message if API fails
- Cached for 5 minutes (React Query)

---

## Architecture

### Backend

**New Endpoint:**
```
GET /api/v1/feeds/quality-v2/overview
```

**Response Structure:**
```json
[
  {
    "feed_id": "uuid",
    "feed_name": "Feed Name",
    "quality_score": 78.58,           // null if insufficient data
    "admiralty_code": "B",             // A-F or null
    "admiralty_label": "Usually Reliable",
    "admiralty_color": "blue",         // green, blue, yellow, orange, red, gray
    "confidence": "high",              // high, medium, low, null
    "trend": "improving",              // improving, stable, declining, null
    "trend_direction": 5.2,            // percentage change, null
    "total_articles": 110,
    "articles_24h": 5,
    "articles_analyzed": 108,
    "coverage_percentage": 98.18
  }
]
```

**Performance:**
- Cached for 5 minutes (`@cached(ttl=300)`)
- Uses lightweight 30-day quality calculation
- Handles errors gracefully (returns feed with null metrics)

**Implementation:**
- File: `/services/feed-service/app/api/feeds.py` (lines 1105-1203)
- Uses existing `FeedQualityScorerV2` class
- Parallel calculation for all active feeds

### Frontend

**Component Structure:**
```
FeedServiceAdminPage (Quality V2 Tab)
├── QualityFeedListTable (Section 1)
│   ├── Sortable table headers
│   ├── Feed rows with selection
│   └── Visual feedback (chevron, blue border)
│
└── Detail View (Section 2) [conditional: if selectedFeedId]
    ├── QualityOverviewCardV2
    ├── QualityComponentsChart
    ├── QualityDistributionChart
    └── QualityRecommendations
```

**New Components:**
- `QualityFeedListTable.tsx` (247 lines)
  - Props: `feeds`, `onFeedSelect`, `selectedFeedId`, `isLoading`
  - State: `sortField`, `sortDirection`
  - Features: Sorting, selection, null-safety, visual feedback

**New Hooks:**
- `useFeedQualityOverview()` - Fetches overview data for all feeds
  - Cache: 5 minutes
  - Auto-refresh: No (manual refetch only)

**New Types:**
- `FeedQualityOverview` interface (13 fields)
  - Location: `frontend/src/types/feedServiceAdmin.ts` (lines 459-473)

---

## User Flow

### Accessing the View

1. Navigate to **Admin → Feed Service**
2. Click **Quality V2** tab
3. See table of all feeds with quality metrics

### Viewing Detailed Analysis

1. **Click any row** in the table
   - Row highlights with blue left border
   - Chevron icon rotates from → to ↓
2. **Detail view appears** directly below the table
   - Loading spinner (1-2 seconds)
   - 4 cards with comprehensive metrics
3. **Click another row** to switch feeds
   - Previous selection unhighlights
   - New feed details load

### Sorting the Table

1. **Click column header** to sort
   - First click: Ascending order
   - Second click: Descending order
   - Icon shows current direction (↑/↓)
2. **Null values** are always sorted to the end

---

## Implementation Details

### Phase 1.1: Null-Safety Updates

**Problem:** Backend changes in Phase 1.1 introduced `null` scores for insufficient data, breaking frontend components that expected numeric values.

**Solution:** Updated all Quality V2 components to handle `null` values:
- `QualityComponentsChart.tsx` - Added `hasData` flags, nullish coalescing
- `QualityOverviewCardV2.tsx` - Null checks before `.toFixed()`
- `QualityRecommendations.tsx` - Null checks in comparisons

### Phase 1.2: Article Quality Rewrite

**Problem:** Article Quality always showed `null` despite 108 analyzed articles. Quality V2 code searched for OLD format (relevance_score, score_breakdown) but Content Analysis V2 stores NEW format (triage/tier1/tier2/tier3 pipeline results).

**Solution:** Complete rewrite of `_calculate_article_quality()` method:
- Maps pipeline agent outputs to quality dimensions
- Relevance: `triage.PriorityScore`
- Objectivity: `tier2.BIAS_DETECTOR` scores
- Credibility: tier2 agent confidence averages
- Verification: tier2/tier3 presence scoring
- Completeness: entity count + tier2 agent count
- Consistency: tier2 agent confidence variance

**Result:** Article Quality now works correctly (e.g., Bleeping Computer: 66.75)

### Master-Detail View Implementation

**Challenge:** Table with all feeds was too long, forcing users to scroll endlessly to see detail view.

**Solution:**
- Table: `max-h-[500px]` with `overflow-y-auto`
- Internal scrolling keeps detail view visible
- Detail view appears directly below table (no scrolling needed)

**Visual Feedback:**
- Chevron icon (→) before each feed name, rotates to ↓ when selected
- Row hover: subtle gray background
- Selected row: light blue background + blue left border
- Clear instruction: "Click any row to view detailed analysis"

---

## API Documentation

### Get Feed Quality Overview

```http
GET /api/v1/feeds/quality-v2/overview
Authorization: Bearer <jwt_token>
```

**Query Parameters:** None

**Response:** `200 OK`
```json
[
  {
    "feed_id": "string (uuid)",
    "feed_name": "string",
    "quality_score": "number | null",
    "admiralty_code": "string | null",
    "admiralty_label": "string",
    "admiralty_color": "string",
    "confidence": "string | null",
    "trend": "string | null",
    "trend_direction": "number | null",
    "total_articles": "number",
    "articles_24h": "number",
    "articles_analyzed": "number",
    "coverage_percentage": "number"
  }
]
```

**Cache:** 5 minutes (300 seconds)

**Error Handling:**
- If a feed fails quality calculation, includes feed with null metrics
- Logs error but continues processing other feeds
- Never returns HTTP error (graceful degradation)

---

## Files Changed

### Backend (Feed Service)

**Modified:**
- `/services/feed-service/app/api/feeds.py`
  - Lines 1105-1203: New `/quality-v2/overview` endpoint
  - Imports: Added `datetime`, `timedelta`, `timezone`

- `/services/feed-service/app/services/feed_quality_v2.py`
  - Lines 165-393: Complete rewrite of `_calculate_article_quality()`
  - Lines 493-544: Null-safety in `_calculate_overall_score()`
  - Lines 705-777: Null-safety in `_generate_recommendations()`

### Frontend

**New Files:**
- `/frontend/src/features/admin/feed-service/components/quality-v2/QualityFeedListTable.tsx` (247 lines)
- `/frontend/src/features/admin/feed-service/hooks/useFeedQualityOverview.ts` (22 lines)

**Modified:**
- `/frontend/src/types/feedServiceAdmin.ts`
  - Lines 459-473: New `FeedQualityOverview` interface

- `/frontend/src/lib/api/feedServiceAdmin.ts`
  - Import: Added `FeedQualityOverview`
  - Lines 216-219: New `getFeedQualityOverview()` function

- `/frontend/src/features/admin/feed-service/hooks/index.ts`
  - Export: Added `useFeedQualityOverview`

- `/frontend/src/features/admin/feed-service/components/quality-v2/index.ts`
  - Export: Added `QualityFeedListTable`

- `/frontend/src/pages/admin/FeedServiceAdminPage.tsx`
  - Lines 28: Import `QualityFeedListTable`
  - Lines 41: Import `useFeedQualityOverview`
  - Lines 63-67: Hook for overview data
  - Lines 165-220: Complete rewrite of Quality V2 tab structure

**Null-Safety Fixes:**
- `/frontend/src/features/admin/feed-service/components/quality-v2/QualityComponentsChart.tsx` (5 edits)
- `/frontend/src/features/admin/feed-service/components/quality-v2/QualityOverviewCardV2.tsx` (2 edits)
- `/frontend/src/features/admin/feed-service/components/quality-v2/QualityRecommendations.tsx` (7 edits)

---

## Testing

### Manual Testing Checklist

**Backend:**
- [x] Endpoint returns data for all active feeds
- [x] Handles feeds with insufficient data (null scores)
- [x] Response cached for 5 minutes
- [x] Error handling works (logs error, continues)

**Frontend:**
- [x] Table displays all feeds correctly
- [x] Sorting works for all columns
- [x] Null values display as "N/A"
- [x] Click row selects feed (chevron rotates)
- [x] Detail view loads after selection
- [x] Detail view shows correct feed data
- [x] Switching feeds updates detail view
- [x] Loading states work (spinner)
- [x] Error states work (error message)

**UX:**
- [x] Table scrolls internally (max 500px)
- [x] Detail view visible without scrolling
- [x] Visual feedback on hover/selection
- [x] Trend indicators show correctly
- [x] Confidence badges show correctly
- [x] Admiralty codes colored correctly

### Automated Testing

**Backend Tests Needed:**
- [ ] `/quality-v2/overview` endpoint integration test
- [ ] Null-safety in quality calculations
- [ ] Error handling for failed feed calculations

**Frontend Tests Needed:**
- [ ] QualityFeedListTable component tests
- [ ] Sorting logic tests
- [ ] Selection state management tests
- [ ] Null-safety in rendering

---

## Known Issues

### Fixed Issues

1. ✅ **Frontend null.toFixed() crash** (Phase 1.1)
   - Fixed: Added null checks before all `.toFixed()` calls

2. ✅ **Backend NameError for logger** (Phase 1.1)
   - Fixed: Added `import logging` and logger initialization

3. ✅ **Backend TypeError on None * float** (Phase 1.1)
   - Fixed: Rewrote `_calculate_overall_score()` for null-safety

4. ✅ **Article Quality always null** (Phase 1.2)
   - Fixed: Rewrote `_calculate_article_quality()` for new pipeline format

5. ✅ **Endless scrolling to see detail view** (Phase 1.2)
   - Fixed: Table max-height 500px with internal scrolling

### Current Limitations

1. **Overview endpoint performance**
   - Calculates quality for all active feeds (can be slow with many feeds)
   - Mitigation: 5-minute cache, lightweight 30-day calculation
   - Future: Consider pagination or background job

2. **No real-time updates**
   - Overview data cached for 5 minutes
   - Manual page refresh needed to see latest data
   - Future: Consider WebSocket or polling for real-time updates

3. **Limited mobile responsiveness**
   - Table has 5 columns, may be cramped on mobile
   - Future: Consider mobile-specific layout or hide columns

---

## Future Enhancements

### Short-term (Phase 2)

1. **Search/Filter**
   - Search feeds by name
   - Filter by Admiralty code
   - Filter by confidence level
   - Filter by trend direction

2. **Bulk Actions**
   - Select multiple feeds
   - Export quality reports
   - Bulk quality recalculation

3. **Detail View Enhancements**
   - Historical quality trends chart
   - Compare with other feeds
   - Quality improvement suggestions

### Long-term (Phase 3+)

1. **Performance Optimization**
   - Background job for quality calculation
   - Pagination for large feed lists
   - Virtual scrolling for better performance

2. **Real-time Updates**
   - WebSocket connection for live updates
   - Notification when quality changes significantly
   - Auto-refresh on quality calculation completion

3. **Advanced Analytics**
   - Quality trends over time
   - Feed comparison matrix
   - Quality predictions (ML-based)
   - Anomaly detection

---

## Related Documentation

- [Feed Quality System V2 Architecture](../decisions/ADR-030-feed-quality-system-v2.md)
- [Feed Service API Documentation](../api/feed-service-api.md)
- [Frontend Architecture Guide](../../CLAUDE.frontend.md)
- [Content Analysis V2 Pipeline](../services/content-analysis-v2.md)

---

## Changelog

### 2025-11-06 - Phase 1.2

**Added:**
- Master-Detail View with scrollable table and detail view
- `/quality-v2/overview` endpoint for all feeds
- `QualityFeedListTable` component with sorting
- `useFeedQualityOverview` hook
- `FeedQualityOverview` TypeScript interface

**Fixed:**
- Article Quality calculation for new pipeline format
- Null-safety in all Quality V2 components
- Backend null arithmetic crashes
- Endless scrolling UX issue

**Changed:**
- Table now scrollable (max-height 500px)
- Detail view appears directly below table
- Improved visual feedback for selection

### 2025-10-30 - Phase 1.1

**Added:**
- 4-tier confidence system (insufficient_data, low, medium, high)
- Default scores return `null` instead of false `50.0`
- Triage threshold tuning (48 passing tests)

**Fixed:**
- Multiple frontend null-safety issues
- Backend null arithmetic crashes
- Logger import errors

---

**Maintainer:** Claude Code
**Last Updated:** 2025-11-06
**Next Review:** After Phase 2 implementation

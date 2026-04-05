# Frontend V1 to V2 Migration

**Date:** 2025-10-27
**Status:** Completed

## Summary

The frontend "View Full Analysis" feature has been migrated from V1 (content-analysis-service) to V2 (content-analysis-v2) architecture.

## Changes Made

### 1. New API Hook

**Created:** `src/features/feeds/api/useArticleV2.ts`

Replaces the old `useArticleAnalysis` hook which called the non-existent V1 analysis API.

```typescript
// OLD (V1 - DEPRECATED)
const { data } = useArticleAnalysis(itemId);
// Calls: analysisApi.get(`/analysis/article/${itemId}`)
// → VITE_ANALYSIS_API_URL (content-analysis service - doesn't exist)

// NEW (V2)
const { data } = useArticleV2(itemId);
// Calls: feedApi.get(`/feeds/items/${itemId}`)
// → VITE_FEED_API_URL/feeds/items/{id}
// Returns: article with pipeline_execution field
```

### 2. New Detail Page

**Created:** `src/pages/ArticleDetailPageV2.tsx`

Complete rewrite of the article detail view to display V2 `pipeline_execution` data structure.

**Features:**
- ✅ Triage Assessment (category, priority score, topics)
- ✅ Tier 1 Summary (summary, entities, topics)
- ✅ Tier 2 Deep Analysis (sentiment, topics, financial, geopolitical)
- ✅ Tier 3 Intelligence Synthesis
- ✅ Article Content
- ✅ Analysis Status Badges (pending, success, failed)
- ✅ Cost & Processing Time Display

**Deprecated:** `src/pages/ArticleDetailPage.tsx` → renamed to `.v1-deprecated`

### 3. Route Update

**File:** `src/App.tsx`

```typescript
// OLD
import { ArticleDetailPage } from '@/pages/ArticleDetailPage'

// NEW
import { ArticleDetailPageV2 } from '@/pages/ArticleDetailPageV2'

// Route uses ArticleDetailPageV2 instead
```

### 4. Export Updates

**File:** `src/features/feeds/api/index.ts`

```typescript
export { useArticleAnalysis } from './useArticleAnalysis'; // DEPRECATED: V1
export { useArticleV2 } from './useArticleV2'; // V2 analysis via feed-service
```

### 5. ArticleListPage Update

**File:** `src/pages/ArticleListPage.tsx`

Articles list page updated to use embedded `pipeline_execution` data:

```typescript
// BEFORE (V1 - WRONG)
const { data: articlesRaw } = useArticles({...});
const articleIds = useMemo(() => articlesRaw?.map(a => a.id) || [], [articlesRaw]);
const { data: v2Analysis } = useArticlesV2Analysis({ articleIds });
// Passed separate v2Analysis prop to ArticleCard

// AFTER (V2 - CORRECT)
const { data: articlesRaw } = useArticles({...});
const articles = useMemo(() => articlesRaw || [], [articlesRaw]);
// Articles already include pipeline_execution from feed-service
// ArticleCard uses article.pipeline_execution directly
```

**Why**: Feed-service API returns `pipeline_execution` embedded in each article. No separate fetch needed.

### 6. Date Sorting Feature

**Added:** Multi-field date sorting with UI controls

**Sort Options:**
- `created_at` (Fetched) - When article was fetched from RSS feed
- `published_at` (Published) - Original article publication date

**UI Implementation:**
```typescript
<Button
  variant={sortBy === 'created_at' ? 'default' : 'outline'}
  onClick={() => handleSortChange('created_at')}
>
  Fetched
  {sortBy === 'created_at' && (
    sortOrder === 'desc' ? <ArrowDown /> : <ArrowUp />
  )}
</Button>
```

**Date Display Enhancement:**
- Published date (from original article)
- Fetched date (when RSS feed was retrieved)
- Scraped date (when full content was extracted)
- All dates shown with relative time (e.g., "3 days ago")

## Data Structure Changes

### V1 Structure (DEPRECATED)

```typescript
{
  item_id: string,
  item_title: string,
  category: { category, confidence, ... },
  sentiment: { overall_sentiment, confidence, ... },
  finance_sentiment: { market_sentiment, ... },
  geopolitical_sentiment: { stability_score, ... },
  osint_events: [...],
  summary: { text, ... },
  facts: [...],
  entities: [...],
  topics: [...],
  feed_config: { ... }
}
```

### V2 Structure (NEW)

```typescript
{
  id: string,
  title: string,
  link: string,
  content: string,
  feed_name: string,
  pipeline_execution: {
    id: string,
    article_id: string,
    success: boolean,
    agents_executed: string[],
    total_cost_usd: number,
    total_processing_time_ms: number,
    triage_decision: {
      category: string,
      PriorityScore: number,
      primary_topics: string[],
      reasoning: string,
      should_run_tier2: boolean
    },
    tier1_summary: {
      summary: string,
      entities: [...],
      sentiment: {},
      topics: [],
      topic_scores: {}
    },
    tier2_summary: {
      sentiment: { label, positive, negative, neutral },
      topics: [...],
      financial: {},
      geopolitical: {}
    } | null,
    tier3_summary: {
      // Intelligence synthesis
    } | null
  }
}
```

## API Endpoint Changes

### V1 API (REMOVED)

```bash
GET /api/v1/analysis/article/{item_id}
# Service: content-analysis-service (port 8102)
# Status: Service removed, API no longer exists
```

### V2 API (CURRENT)

```bash
GET /api/v1/feeds/items/{item_id}
# Service: feed-service (port 8101)
# Returns: Article with pipeline_execution from content-analysis-v2
```

## Migration Checklist

- [x] Create new V2 hook (`useArticleV2.ts`)
- [x] Create new V2 detail page (`ArticleDetailPageV2.tsx`)
- [x] Update routes in `App.tsx`
- [x] Export new hook from `index.ts`
- [x] Update ArticleListPage to use embedded pipeline_execution
- [x] Remove redundant useArticlesV2Analysis call
- [x] Add multi-field date sorting (Fetched/Published)
- [x] Display all date fields in article cards
- [x] Deprecate old V1 components
- [ ] Test v2 migration in browser (http://localhost:3000/articles)
- [ ] Remove V1 components completely (after testing)
- [ ] Update types to remove V1 interfaces
- [ ] Clean up unused V1 schemas

## Testing

### Manual Testing

1. Navigate to http://localhost:3000/articles
2. Click "View Full Analysis" on any article
3. Verify detail page shows:
   - ✅ Triage assessment
   - ✅ Summary tab with tier1 data
   - ✅ Deep Analysis tab (if tier2 available)
   - ✅ Intelligence tab (if tier3 available)
   - ✅ Content tab
   - ✅ Analysis status badges
   - ✅ Cost & time metrics

### API Testing

```bash
TOKEN="..."
curl -s "http://localhost:8101/api/v1/feeds/items/{item_id}" \
  -H "Authorization: Bearer $TOKEN" | jq '.pipeline_execution'
```

## Known Issues

- ~~"Processing..." shown for all articles on list page~~ ✅ **FIXED**: ArticleListPage now uses embedded `pipeline_execution`
- V1 `useArticleAnalysis` hook still exists but is deprecated
- V1 types (`ArticleAnalysis`, etc.) still defined but unused
- V1 schemas in `features/feeds/schemas/` still present
- TypeScript compilation errors in some admin pages (unrelated to v2 migration)

## Cleanup Tasks (Future)

1. Remove `useArticleAnalysis.ts` completely
2. Remove V1 types from `features/feeds/types.ts`
3. Remove V1 schemas from `features/feeds/schemas/`
4. Remove deprecated `ArticleDetailPage.tsx.v1-deprecated`
5. Update `analysisApi` in `axios.ts` (currently points to non-existent service)

## Related Documents

- Backend Migration: `/docs/incidents/2025-10-27-v1-to-v2-content-analysis-migration.md`
- ADR: `/docs/decisions/ADR-028-v2-api-proxy-pattern.md`

---

**Version:** 2.0
**Last Updated:** 2025-10-27

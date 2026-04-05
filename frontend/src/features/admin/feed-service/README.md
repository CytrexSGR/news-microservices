# Feed Service Admin Feature

**Status:** Production Ready
**Route:** `/admin/services/feed-service`
**Created:** 2025-10-21

## Quick Start

```typescript
// Import hooks from centralized index
import {
  useServiceHealth,
  useFeedStats,
  useFeedList,
  useTriggerFetch,
} from '@/features/admin/feed-service/hooks'

// Use in component
function MyComponent() {
  const { data: health } = useServiceHealth(10000) // 10s auto-refresh
  const { data: stats } = useFeedStats(10000)
  const { data: feeds } = useFeedList({ status: 'ACTIVE' })
  const triggerFetch = useTriggerFetch()

  return (
    <div>
      <p>Service: {health?.service}</p>
      <p>Active Feeds: {stats?.active_feeds}</p>
      <button onClick={() => triggerFetch.mutate(feedId)}>
        Fetch Feed
      </button>
    </div>
  )
}
```

## Directory Structure

```
feed-service/
├── components/
│   ├── live-operations/      # Tab 1: Real-time monitoring
│   │   ├── ServiceHealthCard.tsx
│   │   ├── SchedulerStatusCard.tsx
│   │   ├── FeedStatsCard.tsx
│   │   └── QualityOverviewCard.tsx
│   ├── feed-explorer/         # Tab 2: Feed management
│   │   ├── FeedListTable.tsx
│   │   ├── FeedHealthChart.tsx
│   │   ├── RecentItemsTable.tsx
│   │   └── AssessmentHistorySection.tsx
│   └── management/            # Tab 3: Bulk operations
│       ├── BulkFetchControl.tsx
│       ├── CategoryManagement.tsx
│       └── AnalysisToggles.tsx
├── hooks/
│   ├── index.ts               # ⚠️ IMPORTANT: Central export point
│   ├── useServiceHealth.ts
│   ├── useFeedStats.ts
│   ├── useFeedList.ts
│   ├── useFeedHealth.ts
│   ├── useFeedQuality.ts
│   ├── useAssessmentHistory.ts
│   ├── useTriggerFetch.ts
│   ├── useTriggerAssessment.ts
│   ├── useBulkFetch.ts
│   └── useRecentItems.ts
└── README.md                  # This file
```

## Available Hooks

### Query Hooks (Read Data)

| Hook | Purpose | Auto-refresh | Query Key |
|------|---------|--------------|-----------|
| `useServiceHealth(interval?)` | Service health status | Optional | `['feed-service', 'health']` |
| `useFeedStats(interval?)` | Dashboard statistics | Optional | `['feed-service', 'stats']` |
| `useFeedList(filters?)` | List all feeds | No | `['feed-service', 'feeds', filters]` |
| `useFeedHealth(feedId)` | Individual feed health | No | `['feed-service', 'feeds', feedId, 'health']` |
| `useFeedQuality(feedId)` | Feed quality metrics | No | `['feed-service', 'feeds', feedId, 'quality']` |
| `useAssessmentHistory(feedId)` | Assessment history | No | `['feed-service', 'feeds', feedId, 'assessments']` |
| `useRecentItems(limit?)` | Recent scraped items | No | `['feed-service', 'items', 'recent', limit]` |

### Mutation Hooks (Actions)

| Hook | Purpose | Toast | Invalidates Queries |
|------|---------|-------|---------------------|
| `useTriggerFetch()` | Trigger feed fetch | ✅ Yes | `['feed-service', 'feeds']` |
| `useTriggerAssessment()` | Trigger assessment | ✅ Yes | `['feed-service', 'feeds']` |
| `useBulkFetch()` | Bulk fetch all feeds | ✅ Yes | `['feed-service', 'feeds']`, `['feed-service', 'stats']` |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health (⚠️ root level, not `/api/v1`) |
| `/api/v1/feeds/stats` | GET | Dashboard statistics |
| `/api/v1/feeds` | GET | List feeds (with filters) |
| `/api/v1/feeds/:id/health` | GET | Individual feed health |
| `/api/v1/feeds/:id/quality` | GET | Feed quality metrics |
| `/api/v1/feeds/items/recent` | GET | Recent scraped items |
| `/api/v1/feeds/:id/fetch` | POST | Trigger feed fetch |
| `/api/v1/feeds/:id/assess` | POST | Trigger assessment |
| `/api/v1/feeds/bulk-fetch` | POST | Bulk fetch operation |

## TypeScript Types

All types are in `src/types/feedServiceAdmin.ts`:

```typescript
import type {
  FeedServiceHealth,
  FeedStats,
  FeedResponse,
  FeedStatus,
  ScrapeStatus,
  AssessmentStatus,
} from '@/types/feedServiceAdmin'
```

## Component Guidelines

### Using Auto-refresh

```typescript
// Refresh every 10 seconds
const { data, isLoading, error } = useServiceHealth(10000)

// Refresh every 30 seconds
const { data } = useFeedStats(30000)

// No auto-refresh
const { data } = useFeedList()
```

### Using Mutations

```typescript
const triggerFetch = useTriggerFetch()

// In event handler
const handleFetch = (feedId: string) => {
  triggerFetch.mutate(feedId)
}

// Check mutation state
if (triggerFetch.isPending) {
  return <Spinner />
}
```

### Filtering Feeds

```typescript
const { data } = useFeedList({
  status: 'ACTIVE',
  health_score_min: 80,
  health_score_max: 100,
  limit: 50,
  skip: 0,
})
```

## Styling

All components use:
- **shadcn/ui:** Card, Badge, Button, Input, Tabs
- **lucide-react:** Icons
- **Tailwind CSS:** Utility classes
- **Native HTML tables:** No shadcn Table components (not available)

## Common Patterns

### Status Badge Variants

```typescript
const getStatusBadgeVariant = (status: FeedStatus) => {
  switch (status) {
    case 'ACTIVE': return 'default'
    case 'PAUSED': return 'secondary'
    case 'ERROR': return 'destructive'
    case 'INACTIVE': return 'outline'
  }
}
```

### Health Score Color Coding

```typescript
const getHealthBadgeVariant = (score: number) => {
  if (score >= 80) return 'default'  // Green
  if (score >= 50) return 'secondary' // Yellow
  return 'destructive'                // Red
}
```

## Important Notes

⚠️ **Health Endpoint:** The `/health` endpoint is at root level, NOT `/api/v1/health`. The API client handles this with a baseURL override.

⚠️ **Central Exports:** ALWAYS import hooks from `@/features/admin/feed-service/hooks`, NOT from individual files.

⚠️ **Toast Notifications:** All mutations automatically show toast notifications. Don't add duplicate toasts.

⚠️ **Query Invalidation:** Mutations automatically invalidate related queries. The UI will refresh automatically.

⚠️ **Native Tables:** Use native HTML `<table>` elements, not shadcn Table components.

## Testing

```bash
# Run Vite dev server
npm run dev

# Access page
open http://localhost:3000/admin/services/feed-service

# Check React Query DevTools
# Look for queries with key: ['feed-service', ...]
```

## Troubleshooting

**Health endpoint 404:**
- Check if baseURL override is working in `lib/api/feedServiceAdmin.ts`
- Verify endpoint is `/health`, not `/api/v1/health`

**Hook import errors:**
- Import from `@/features/admin/feed-service/hooks`, not individual files
- Check `hooks/index.ts` exports all hooks

**Mutation not updating UI:**
- Verify query invalidation in mutation `onSuccess`
- Check React Query DevTools for cache updates

**Type errors:**
- Ensure TypeScript types match actual API responses
- Use browser DevTools to inspect API responses
- Update types in `src/types/feedServiceAdmin.ts`

## Related Files

- **Main Component:** `src/pages/admin/FeedServiceAdminPage.tsx`
- **API Client:** `src/lib/api/feedServiceAdmin.ts`
- **Types:** `src/types/feedServiceAdmin.ts`
- **Routing:** `src/App.tsx` (route `/admin/services/feed-service`)
- **Navigation:** `src/components/layout/MainLayout.tsx`

## Documentation

- [Full Technical Documentation](../../../../docs/frontend/feed-service-admin.md)
- [Frontend Features Inventory](../../../FEATURES.md)
- [Frontend Architecture](../../../ARCHITECTURE.md)

## Changelog

### 2025-10-21 - Initial Release
- Created Feed Service Admin Dashboard
- 11 components across 3 tabs
- 10 React Query hooks
- Complete TypeScript types
- Full documentation

# Search Stats Hooks - Quick Start Guide

⚡ **5-Minute Integration Guide** for Search Service Statistics

## 🎯 Quick Reference

```tsx
// Import what you need
import {
  useIndexStats,      // Article index statistics
  useQueryStats,      // Search query analytics
  useCacheStats,      // Redis cache metrics
  useCeleryStats,     // Worker status
  usePerformanceStats,// Performance metrics
  useAllSearchStats,  // All stats in one hook
  useReindexArticles, // Admin: Full reindex
  useSyncArticles,    // Admin: Incremental sync
} from '@/hooks/useSearchStats';
```

## 📊 Most Common Use Cases

### 1. Display Total Article Count
```tsx
function ArticleCount() {
  const { data, isLoading } = useIndexStats();

  if (isLoading) return <div>Loading...</div>;

  return <div>{data?.total_indexed.toLocaleString()} articles</div>;
}
```

### 2. Show Cache Health
```tsx
function CacheHealth() {
  const { data } = useCacheStats({ refetchInterval: 30000 });

  return (
    <div className={data?.hit_rate_percent > 80 ? 'text-green-600' : 'text-red-600'}>
      Cache Hit Rate: {data?.hit_rate_percent}%
    </div>
  );
}
```

### 3. Admin Sync Button
```tsx
function SyncButton() {
  const sync = useSyncArticles();

  return (
    <button
      onClick={() => sync.mutateAsync()}
      disabled={sync.isPending}
    >
      {sync.isPending ? 'Syncing...' : 'Sync Articles'}
    </button>
  );
}
```

### 4. Complete Dashboard
```tsx
function Dashboard() {
  const {
    indexStats,
    cacheStats,
    isLoading
  } = useAllSearchStats({ refetchInterval: 30000 });

  if (isLoading) return <div>Loading dashboard...</div>;

  return (
    <div>
      <h1>Search Service</h1>
      <p>Articles: {indexStats?.total_indexed}</p>
      <p>Cache Hit Rate: {cacheStats?.hit_rate_percent}%</p>
    </div>
  );
}
```

## 🎨 Copy-Paste Templates

### Metric Card
```tsx
function MetricCard({ title, value, subtitle }: {
  title: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <div className="p-4 bg-white rounded shadow">
      <h3 className="text-sm font-semibold text-gray-600">{title}</h3>
      <p className="text-3xl font-bold">{value}</p>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </div>
  );
}

// Usage
function IndexMetrics() {
  const { data } = useIndexStats();

  return (
    <MetricCard
      title="Total Articles"
      value={data?.total_indexed.toLocaleString() ?? 0}
      subtitle={`${data?.recent_24h} in last 24h`}
    />
  );
}
```

### Stats Grid
```tsx
function StatsGrid() {
  const { data } = useIndexStats();

  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard title="Total" value={data?.total_indexed ?? 0} />
      <MetricCard title="Recent 24h" value={data?.recent_24h ?? 0} />
      <MetricCard title="Index Size" value={data?.index_size ?? 'N/A'} />
      <MetricCard title="Sources" value={data?.by_source.length ?? 0} />
    </div>
  );
}
```

### Reindex with Confirmation
```tsx
function ReindexButton() {
  const reindex = useReindexArticles();

  const handleReindex = () => {
    if (confirm('This will delete all indexes. Continue?')) {
      reindex.mutateAsync()
        .then(() => alert('Reindex completed!'))
        .catch(() => alert('Reindex failed!'));
    }
  };

  return (
    <button
      onClick={handleReindex}
      disabled={reindex.isPending}
      className="px-4 py-2 bg-red-600 text-white rounded"
    >
      {reindex.isPending ? 'Reindexing...' : 'Reindex All'}
    </button>
  );
}
```

## ⚙️ Default Settings

All hooks come with sensible defaults:

```tsx
// Index Stats - Refresh every 1 minute
useIndexStats({ refetchInterval: 60000 })

// Query Stats - Refresh every 1 minute, top 20 queries
useQueryStats(20, { refetchInterval: 60000 })

// Cache Stats - Refresh every 30 seconds (real-time monitoring)
useCacheStats({ refetchInterval: 30000 })

// Celery Stats - Refresh every 30 seconds
useCeleryStats({ refetchInterval: 30000 })

// Performance Stats - Refresh every 1 minute
usePerformanceStats({ refetchInterval: 60000 })
```

## 🚨 Common Mistakes

### ❌ Don't Do This
```tsx
// Multiple individual hooks - causes waterfall loading
const index = useIndexStats();
const cache = useCacheStats();
const query = useQueryStats();
```

### ✅ Do This Instead
```tsx
// Single composite hook - parallel loading
const { indexStats, cacheStats, queryStats } = useAllSearchStats();
```

### ❌ Don't Do This
```tsx
// Missing loading state
const { data } = useIndexStats();
return <div>{data.total_indexed}</div>; // Crashes if data is undefined
```

### ✅ Do This Instead
```tsx
// Proper loading/error handling
const { data, isLoading, error } = useIndexStats();
if (isLoading) return <div>Loading...</div>;
if (error) return <div>Error: {error.message}</div>;
return <div>{data?.total_indexed ?? 0}</div>;
```

## 🎯 Cheat Sheet

| Need | Hook | Example |
|------|------|---------|
| Article count | `useIndexStats()` | `data?.total_indexed` |
| Top searches | `useQueryStats(10)` | `data?.top_queries` |
| Cache health | `useCacheStats()` | `data?.hit_rate_percent` |
| Worker status | `useCeleryStats()` | `data?.status` |
| Full dashboard | `useAllSearchStats()` | Gets everything |
| Sync articles | `useSyncArticles()` | `mutateAsync()` |
| Reindex all | `useReindexArticles()` | `mutateAsync()` |

## 📦 TypeScript Support

All hooks are fully typed. Import types if needed:

```tsx
import type {
  IndexStatistics,
  CacheStatistics,
  QueryStatistics
} from '@/types/search';

function MyComponent() {
  const { data } = useIndexStats();
  // data is IndexStatistics | undefined
}
```

## 🔧 Environment Variables

Make sure `VITE_SEARCH_API_URL` is set in your `.env`:

```bash
VITE_SEARCH_API_URL=http://localhost:8106
```

## 📚 Learn More

- **Full Documentation:** [README.md](./README.md)
- **Complete Examples:** [../components/SearchStatsExample.tsx](../components/SearchStatsExample.tsx)
- **API Reference:** http://localhost:8106/docs

## 🆘 Troubleshooting

### Hook returns no data
1. Check if Search Service is running: `docker ps | grep search-service`
2. Verify API URL: `console.log(import.meta.env.VITE_SEARCH_API_URL)`
3. Check browser console for errors
4. Test API directly: `curl http://localhost:8106/api/v1/admin/stats/index`

### 401 Unauthorized
Make sure authentication token is set in axios config (already configured in `@/api/axios.ts`).

### Stale data
Force refresh with:
```tsx
const { refetch } = useIndexStats();
refetch(); // Manual refresh
```

Or invalidate cache:
```tsx
import { useQueryClient } from '@tanstack/react-query';
const queryClient = useQueryClient();
queryClient.invalidateQueries({ queryKey: ['search-stats'] });
```

---

**That's it!** You're ready to use Search Stats hooks. For advanced usage, see [README.md](./README.md).

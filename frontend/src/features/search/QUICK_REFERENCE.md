# Search Service Hooks - Quick Reference

## Import

```tsx
import {
  useCacheStats,
  useIndexStats,
  useQueryStats,
  usePerformanceStats,
  CacheStatsCard,
  SearchDashboard,
} from '@/features/search';
```

## Hooks

### useCacheStats()

```tsx
const { data, isLoading, error, refetch } = useCacheStats({
  refetchInterval: 5000, // Optional: auto-refresh
});

// data.hit_rate_percent
// data.memory_used
// data.total_keys
// data.evicted_keys
```

### useIndexStats()

```tsx
const { data } = useIndexStats();

// data.total_indexed
// data.index_size
// data.by_source[]
// data.by_sentiment[]
```

### useQueryStats(limit?)

```tsx
const { data } = useQueryStats(10); // Top 10 queries

// data.top_queries[]
// data.total_searches
// data.avg_results_per_query
```

### usePerformanceStats()

```tsx
const { data } = usePerformanceStats();

// data.avg_execution_time_ms
// data.slowest_queries[]
// data.result_distribution[]
```

## Components

### CacheStatsCard

```tsx
<CacheStatsCard
  refreshInterval={5000}
  className="custom-class"
/>
```

### SearchDashboard

```tsx
<SearchDashboard />
```

## Common Patterns

### Auto-refresh

```tsx
useCacheStats({ refetchInterval: 5000 });
```

### Conditional fetch

```tsx
useCacheStats({ enabled: isAdmin });
```

### Manual refresh

```tsx
const { refetch } = useCacheStats();
<button onClick={() => refetch()}>Refresh</button>
```

### Custom stale time

```tsx
useCacheStats({ staleTime: 10000 }); // 10 seconds
```

## API Endpoints

- `/admin/stats/cache` - Cache stats
- `/admin/stats/index` - Index stats
- `/admin/stats/queries?limit=N` - Query stats
- `/admin/stats/performance` - Performance stats

## More Info

- Full docs: `README.md`
- Examples: `examples/BasicUsage.tsx`
- Implementation: `IMPLEMENTATION_SUMMARY.md`

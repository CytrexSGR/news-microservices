# Search Service Frontend Integration

This directory contains React components and hooks for integrating with the Search Service API.

## Features

- **React Query Hooks** - Type-safe data fetching with automatic caching
- **Real-time Statistics** - Auto-refreshing cache, index, query, and performance metrics
- **TypeScript Support** - Full type definitions for all API responses
- **Optimized Performance** - Smart caching with configurable stale times

## Directory Structure

```
features/search/
├── hooks/
│   ├── useCacheStats.ts      # React Query hooks for all statistics endpoints
│   └── index.ts              # Barrel export
├── components/
│   ├── CacheStatsCard.tsx    # Cache statistics card component
│   └── SearchDashboard.tsx   # Complete search dashboard
└── README.md                 # This file
```

## Available Hooks

### `useCacheStats(options?)`

Fetches Redis cache statistics with auto-refresh support.

**Returns:**
- `total_keys` - Total number of keys in cache
- `memory_used` - Current memory usage (human-readable)
- `memory_peak` - Peak memory usage
- `hit_rate_percent` - Cache hit rate percentage
- `total_hits` - Total cache hits
- `total_misses` - Total cache misses
- `evicted_keys` - Number of evicted keys
- `expired_keys` - Number of expired keys

**Example:**
```tsx
import { useCacheStats } from '@/features/search/hooks';

function CacheMonitor() {
  const { data, isLoading, error, refetch } = useCacheStats({
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <p>Hit Rate: {data.hit_rate_percent}%</p>
      <p>Memory: {data.memory_used}</p>
      <button onClick={() => refetch()}>Refresh</button>
    </div>
  );
}
```

### `useIndexStats(options?)`

Fetches article index statistics.

**Returns:**
- `total_indexed` - Total indexed articles
- `by_source` - Articles grouped by source
- `by_sentiment` - Articles grouped by sentiment
- `recent_24h` - Articles indexed in last 24 hours
- `index_size` - Database index size

**Example:**
```tsx
import { useIndexStats } from '@/features/search/hooks';

function IndexStats() {
  const { data } = useIndexStats();

  return (
    <div>
      <h2>Total Articles: {data?.total_indexed.toLocaleString()}</h2>
      <p>Index Size: {data?.index_size}</p>
    </div>
  );
}
```

### `useQueryStats(limit?, options?)`

Fetches search query statistics.

**Parameters:**
- `limit` - Number of top queries to return (default: 20)

**Returns:**
- `top_queries` - Most popular search queries
- `total_searches` - Total number of searches
- `recent_24h` - Searches in last 24 hours
- `avg_results_per_query` - Average results per query

**Example:**
```tsx
import { useQueryStats } from '@/features/search/hooks';

function PopularQueries() {
  const { data } = useQueryStats(10); // Top 10 queries

  return (
    <ul>
      {data?.top_queries.map(q => (
        <li key={q.query}>
          {q.query} - {q.hits} hits
        </li>
      ))}
    </ul>
  );
}
```

### `usePerformanceStats(options?)`

Fetches search performance statistics.

**Returns:**
- `avg_execution_time_ms` - Average query execution time
- `slowest_queries` - Slowest performing queries
- `result_distribution` - Distribution of result counts

**Example:**
```tsx
import { usePerformanceStats } from '@/features/search/hooks';

function PerformanceMonitor() {
  const { data } = usePerformanceStats();

  return (
    <div>
      <p>Avg Time: {data?.avg_execution_time_ms.toFixed(2)}ms</p>
    </div>
  );
}
```

## Components

### `<CacheStatsCard />`

A pre-built card component displaying cache statistics.

**Props:**
- `refreshInterval?` - Auto-refresh interval in milliseconds
- `className?` - Custom CSS classes

**Example:**
```tsx
import { CacheStatsCard } from '@/features/search/components/CacheStatsCard';

function AdminPage() {
  return (
    <div>
      <CacheStatsCard refreshInterval={5000} />
    </div>
  );
}
```

### `<SearchDashboard />`

Complete dashboard displaying all search service statistics.

**Example:**
```tsx
import { SearchDashboard } from '@/features/search/components/SearchDashboard';

function AdminDashboard() {
  return <SearchDashboard />;
}
```

## React Query Configuration

All hooks use the following default configuration:

- **Cache Keys:** Namespaced under `['search', 'admin', ...]`
- **Stale Time:** 30-60 seconds (depending on data type)
- **Refetch on Window Focus:** Disabled
- **Auto-refresh:** Disabled by default (can be enabled via `refetchInterval`)

### Customizing Configuration

You can override any React Query option:

```tsx
const { data } = useCacheStats({
  staleTime: 10000,        // Consider fresh for 10 seconds
  refetchInterval: 3000,   // Auto-refresh every 3 seconds
  enabled: isAdmin,        // Only fetch if user is admin
  retry: 3,                // Retry failed requests 3 times
});
```

## Type Definitions

All TypeScript types are defined in `/types/search.ts`:

```typescript
import type {
  CacheStatistics,
  IndexStatistics,
  QueryStatistics,
  PerformanceStatistics,
} from '@/types/search';
```

## API Endpoints

All hooks connect to the Search Service API:

- **Base URL:** `VITE_SEARCH_API_URL` (configured in `.env`)
- **Cache Stats:** `GET /admin/stats/cache`
- **Index Stats:** `GET /admin/stats/index`
- **Query Stats:** `GET /admin/stats/queries?limit=20`
- **Performance Stats:** `GET /admin/stats/performance`

## Authentication

The Search Service API requires authentication. Auth tokens are automatically added via Axios interceptors in `/api/axios.ts`.

## Performance Optimization Tips

1. **Use Appropriate Stale Times:**
   - Cache stats: 30 seconds (changes frequently)
   - Index stats: 60 seconds (changes less frequently)
   - Query stats: 60 seconds
   - Performance stats: 60 seconds

2. **Enable Auto-refresh Only When Visible:**
   ```tsx
   const [isVisible, setIsVisible] = useState(true);

   const { data } = useCacheStats({
     refetchInterval: isVisible ? 5000 : false,
   });
   ```

3. **Conditional Fetching:**
   ```tsx
   const { data } = useCacheStats({
     enabled: userRole === 'admin', // Only fetch for admins
   });
   ```

4. **Parallel Fetching:**
   ```tsx
   // All hooks fetch in parallel automatically
   const cacheQuery = useCacheStats();
   const indexQuery = useIndexStats();
   const queryQuery = useQueryStats();
   ```

## Testing

Example test with React Testing Library:

```tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCacheStats } from './useCacheStats';

test('fetches cache statistics', async () => {
  const queryClient = new QueryClient();
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  const { result } = renderHook(() => useCacheStats(), { wrapper });

  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  expect(result.current.data).toHaveProperty('hit_rate_percent');
  expect(result.current.data).toHaveProperty('memory_used');
});
```

## Troubleshooting

### Hook returns undefined data

1. Check if Search Service is running: `http://localhost:8106/health`
2. Verify `VITE_SEARCH_API_URL` in `.env`
3. Check browser console for CORS errors
4. Verify authentication token is valid

### Cache stats show 0% hit rate

This is normal if Redis was recently restarted or has no traffic. The hit rate will improve as the cache is used.

### Slow performance

1. Increase `staleTime` to reduce API calls
2. Disable `refetchOnWindowFocus`
3. Reduce `refetchInterval` or disable auto-refresh
4. Use `enabled: false` when data not needed

## Related Documentation

- [Search Service API Documentation](http://localhost:8106/docs)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Search Service Backend Code](/services/search-service/)
- [TypeScript Type Definitions](/frontend/src/types/search.ts)

## Support

For issues or questions:
1. Check [POSTMORTEMS.md](/POSTMORTEMS.md) for known issues
2. Review [Search Service logs](http://localhost:8106/admin/logs)
3. Contact the backend team for API-related issues

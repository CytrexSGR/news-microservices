import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import type {
  CacheStatistics,
  IndexStatistics,
  QueryStatistics,
  PerformanceStatistics,
} from '@/types/search';

/**
 * React Query hook for fetching Redis cache statistics
 *
 * @param options - React Query options
 * @returns Query result with cache statistics
 *
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useCacheStats({
 *   refetchInterval: 5000, // Auto-refresh every 5 seconds
 * });
 *
 * if (isLoading) return <div>Loading cache stats...</div>;
 * if (error) return <div>Error loading cache stats</div>;
 *
 * return (
 *   <div>
 *     <p>Hit Rate: {data.hit_rate_percent}%</p>
 *     <p>Memory: {data.memory_used}</p>
 *     <button onClick={() => refetch()}>Refresh</button>
 *   </div>
 * );
 * ```
 */
export const useCacheStats = (
  options?: Omit<
    UseQueryOptions<CacheStatistics, Error>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery<CacheStatistics, Error>({
    queryKey: ['search', 'admin', 'cache-stats'],
    queryFn: async () => {
      const { data } = await searchApi.get<CacheStatistics>(
        '/admin/stats/cache'
      );
      return data;
    },
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
    ...options,
  });
};

/**
 * React Query hook for fetching index statistics
 *
 * @param options - React Query options
 * @returns Query result with index statistics
 *
 * @example
 * ```tsx
 * const { data } = useIndexStats();
 * console.log(`Total indexed: ${data.total_indexed}`);
 * console.log(`Index size: ${data.index_size}`);
 * ```
 */
export const useIndexStats = (
  options?: Omit<
    UseQueryOptions<IndexStatistics, Error>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery<IndexStatistics, Error>({
    queryKey: ['search', 'admin', 'index-stats'],
    queryFn: async () => {
      const { data } = await searchApi.get<IndexStatistics>(
        '/admin/stats/index'
      );
      return data;
    },
    staleTime: 60000, // Consider data fresh for 60 seconds
    refetchOnWindowFocus: false,
    ...options,
  });
};

/**
 * React Query hook for fetching query statistics
 *
 * @param limit - Number of top queries to return
 * @param options - React Query options
 * @returns Query result with query statistics
 *
 * @example
 * ```tsx
 * const { data } = useQueryStats(10);
 * data.top_queries.map(q => (
 *   <div key={q.query}>{q.query}: {q.hits} hits</div>
 * ));
 * ```
 */
export const useQueryStats = (
  limit: number = 20,
  options?: Omit<
    UseQueryOptions<QueryStatistics, Error>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery<QueryStatistics, Error>({
    queryKey: ['search', 'admin', 'query-stats', limit],
    queryFn: async () => {
      const { data } = await searchApi.get<QueryStatistics>(
        '/admin/stats/queries',
        {
          params: { limit },
        }
      );
      return data;
    },
    staleTime: 60000,
    refetchOnWindowFocus: false,
    ...options,
  });
};

/**
 * React Query hook for fetching performance statistics
 *
 * @param options - React Query options
 * @returns Query result with performance statistics
 *
 * @example
 * ```tsx
 * const { data } = usePerformanceStats();
 * console.log(`Average execution time: ${data.avg_execution_time_ms}ms`);
 * ```
 */
export const usePerformanceStats = (
  options?: Omit<
    UseQueryOptions<PerformanceStatistics, Error>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery<PerformanceStatistics, Error>({
    queryKey: ['search', 'admin', 'performance-stats'],
    queryFn: async () => {
      const { data } = await searchApi.get<PerformanceStatistics>(
        '/admin/stats/performance'
      );
      return data;
    },
    staleTime: 60000,
    refetchOnWindowFocus: false,
    ...options,
  });
};

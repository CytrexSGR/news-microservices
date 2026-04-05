/**
 * React Query hooks for Search Service statistics
 *
 * Provides hooks for fetching and managing search service statistics:
 * - Index statistics (total articles, by source, by sentiment)
 * - Query statistics (top queries, search activity)
 * - Cache statistics (Redis metrics)
 * - Celery worker statistics
 * - Performance statistics
 * - Admin operations (reindex, sync)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getIndexStats,
  getQueryStats,
  getCacheStats,
  getCeleryStats,
  getPerformanceStats,
  reindexArticles,
  syncArticles,
} from '@/api/search';
import type {
  IndexStatistics,
  QueryStatistics,
  CacheStatistics,
  CeleryStatistics,
  PerformanceStatistics,
} from '@/types/search';

/**
 * Query keys for Search Service statistics
 */
export const searchStatsKeys = {
  all: ['search-stats'] as const,
  index: () => [...searchStatsKeys.all, 'index'] as const,
  queries: (limit?: number) => [...searchStatsKeys.all, 'queries', limit] as const,
  cache: () => [...searchStatsKeys.all, 'cache'] as const,
  celery: () => [...searchStatsKeys.all, 'celery'] as const,
  performance: () => [...searchStatsKeys.all, 'performance'] as const,
};

/**
 * Hook to fetch index statistics
 *
 * Returns:
 * - total_indexed: Total number of indexed articles
 * - by_source: Articles grouped by source (top 10)
 * - by_sentiment: Articles grouped by sentiment
 * - recent_24h: Articles indexed in last 24 hours
 * - index_size: Database size estimate
 *
 * @param options - React Query options
 */
export const useIndexStats = (
  options?: {
    refetchInterval?: number;
    enabled?: boolean;
  }
) => {
  return useQuery<IndexStatistics>({
    queryKey: searchStatsKeys.index(),
    queryFn: getIndexStats,
    refetchInterval: options?.refetchInterval ?? 60000, // Default: 1 minute
    staleTime: 30000, // 30 seconds
    enabled: options?.enabled ?? true,
  });
};

/**
 * Hook to fetch query statistics
 *
 * Returns:
 * - top_queries: Most frequently searched queries
 * - total_searches: Total number of searches
 * - recent_24h: Searches in last 24 hours
 * - avg_results_per_query: Average number of results per query
 *
 * @param limit - Number of top queries to fetch (default: 20)
 * @param options - React Query options
 */
export const useQueryStats = (
  limit = 20,
  options?: {
    refetchInterval?: number;
    enabled?: boolean;
  }
) => {
  return useQuery<QueryStatistics>({
    queryKey: searchStatsKeys.queries(limit),
    queryFn: () => getQueryStats(limit),
    refetchInterval: options?.refetchInterval ?? 60000, // Default: 1 minute
    staleTime: 30000,
    enabled: options?.enabled ?? true,
  });
};

/**
 * Hook to fetch cache statistics
 *
 * Returns Redis cache metrics:
 * - total_keys: Number of keys in cache
 * - memory_used/memory_peak: Memory usage
 * - hit_rate_percent: Cache hit rate
 * - evicted_keys/expired_keys: Key lifecycle metrics
 *
 * @param options - React Query options
 */
export const useCacheStats = (
  options?: {
    refetchInterval?: number;
    enabled?: boolean;
  }
) => {
  return useQuery<CacheStatistics>({
    queryKey: searchStatsKeys.cache(),
    queryFn: getCacheStats,
    refetchInterval: options?.refetchInterval ?? 30000, // Default: 30 seconds
    staleTime: 15000, // 15 seconds
    enabled: options?.enabled ?? true,
  });
};

/**
 * Hook to fetch Celery worker statistics
 *
 * Returns:
 * - active_workers: Number of active workers
 * - registered_tasks: Number of registered task types
 * - reserved_tasks: Number of tasks in queue
 * - worker_stats: Per-worker statistics
 * - status: Overall worker health
 *
 * @param options - React Query options
 */
export const useCeleryStats = (
  options?: {
    refetchInterval?: number;
    enabled?: boolean;
  }
) => {
  return useQuery<CeleryStatistics>({
    queryKey: searchStatsKeys.celery(),
    queryFn: getCeleryStats,
    refetchInterval: options?.refetchInterval ?? 30000, // Default: 30 seconds
    staleTime: 15000,
    enabled: options?.enabled ?? true,
  });
};

/**
 * Hook to fetch performance statistics
 *
 * Returns:
 * - avg_execution_time_ms: Average query execution time
 * - slowest_queries: Queries with most hits (proxy for slow queries)
 * - result_distribution: Distribution of results per query
 *
 * @param options - React Query options
 */
export const usePerformanceStats = (
  options?: {
    refetchInterval?: number;
    enabled?: boolean;
  }
) => {
  return useQuery<PerformanceStatistics>({
    queryKey: searchStatsKeys.performance(),
    queryFn: getPerformanceStats,
    refetchInterval: options?.refetchInterval ?? 60000, // Default: 1 minute
    staleTime: 30000,
    enabled: options?.enabled ?? true,
  });
};

/**
 * Hook to trigger full reindex of all articles
 *
 * This is a destructive operation that:
 * 1. Deletes all existing article indexes
 * 2. Fetches all articles from Feed Service
 * 3. Fetches sentiment/entity data from Content Analysis Service
 * 4. Creates full-text search indexes
 *
 * Use with caution - this can take several minutes.
 *
 * @example
 * const reindex = useReindexArticles();
 *
 * const handleReindex = async () => {
 *   try {
 *     const result = await reindex.mutateAsync();
 *     console.log('Reindex completed:', result.stats);
 *   } catch (error) {
 *     console.error('Reindex failed:', error);
 *   }
 * };
 */
export const useReindexArticles = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: reindexArticles,
    onSuccess: () => {
      // Invalidate all search statistics after reindex
      queryClient.invalidateQueries({ queryKey: searchStatsKeys.all });
    },
  });
};

/**
 * Hook to sync new articles from Feed Service
 *
 * This operation:
 * 1. Fetches articles updated since last sync
 * 2. Indexes new articles
 * 3. Updates existing articles
 *
 * Less destructive than full reindex, recommended for regular updates.
 *
 * @example
 * const sync = useSyncArticles();
 *
 * const handleSync = async () => {
 *   try {
 *     const result = await sync.mutateAsync(100); // Batch size 100
 *     console.log('Sync completed:', result.stats);
 *   } catch (error) {
 *     console.error('Sync failed:', error);
 *   }
 * };
 */
export const useSyncArticles = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (batchSize?: number) => syncArticles(batchSize),
    onSuccess: () => {
      // Invalidate index and performance stats after sync
      queryClient.invalidateQueries({ queryKey: searchStatsKeys.index() });
      queryClient.invalidateQueries({ queryKey: searchStatsKeys.performance() });
    },
  });
};

/**
 * Composite hook that fetches all search statistics in parallel
 *
 * Useful for dashboard views that need all statistics at once.
 * Each statistic can be enabled/disabled individually.
 *
 * @param options - Configuration for each statistic
 * @returns Object with all statistics and loading states
 *
 * @example
 * const {
 *   indexStats,
 *   queryStats,
 *   cacheStats,
 *   isLoading,
 *   error
 * } = useAllSearchStats({
 *   enableCache: true,
 *   queryStatsLimit: 10,
 * });
 */
export const useAllSearchStats = (
  options?: {
    enableIndex?: boolean;
    enableQueries?: boolean;
    enableCache?: boolean;
    enableCelery?: boolean;
    enablePerformance?: boolean;
    queryStatsLimit?: number;
    refetchInterval?: number;
  }
) => {
  const {
    enableIndex = true,
    enableQueries = true,
    enableCache = true,
    enableCelery = true,
    enablePerformance = true,
    queryStatsLimit = 20,
    refetchInterval,
  } = options ?? {};

  const indexStats = useIndexStats({
    enabled: enableIndex,
    refetchInterval,
  });

  const queryStats = useQueryStats(queryStatsLimit, {
    enabled: enableQueries,
    refetchInterval,
  });

  const cacheStats = useCacheStats({
    enabled: enableCache,
    refetchInterval,
  });

  const celeryStats = useCeleryStats({
    enabled: enableCelery,
    refetchInterval,
  });

  const performanceStats = usePerformanceStats({
    enabled: enablePerformance,
    refetchInterval,
  });

  const isLoading =
    indexStats.isLoading ||
    queryStats.isLoading ||
    cacheStats.isLoading ||
    celeryStats.isLoading ||
    performanceStats.isLoading;

  const error =
    indexStats.error ||
    queryStats.error ||
    cacheStats.error ||
    celeryStats.error ||
    performanceStats.error;

  return {
    indexStats: indexStats.data,
    queryStats: queryStats.data,
    cacheStats: cacheStats.data,
    celeryStats: celeryStats.data,
    performanceStats: performanceStats.data,
    isLoading,
    error,
    // Individual query states for granular control
    queries: {
      index: indexStats,
      query: queryStats,
      cache: cacheStats,
      celery: celeryStats,
      performance: performanceStats,
    },
  };
};

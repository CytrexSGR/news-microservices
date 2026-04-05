/**
 * useCacheStats Hook
 *
 * Fetches Redis cache statistics with auto-refresh.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { CacheStats } from '../types';

const QUERY_KEY = ['monitoring', 'cache-stats'];

/**
 * Fetch cache stats from MCP orchestration server
 */
async function fetchCacheStats(): Promise<CacheStats> {
  return mcpClient.callTool<CacheStats>('get_cache_stats');
}

export interface UseCacheStatsOptions {
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch Redis cache statistics
 *
 * @example
 * ```tsx
 * const { data: cacheStats, isLoading } = useCacheStats({
 *   autoRefresh: true,
 *   refetchInterval: 30000
 * });
 * ```
 */
export function useCacheStats({
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseCacheStatsOptions = {}) {
  const queryClient = useQueryClient();

  const query = useQuery<CacheStats>({
    queryKey: QUERY_KEY,
    queryFn: fetchCacheStats,
    refetchInterval: autoRefresh ? refetchInterval : false,
    staleTime: 10000, // 10 seconds
    enabled,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEY });
  };

  // Derived data
  const memoryUsagePercent = query.data
    ? (query.data.memory_used_mb / query.data.memory_max_mb) * 100
    : 0;
  const hitRate = query.data?.hit_rate_percent ?? 0;

  return {
    ...query,
    memoryUsagePercent,
    hitRate,
    invalidate,
  };
}

export { QUERY_KEY as CACHE_STATS_QUERY_KEY };

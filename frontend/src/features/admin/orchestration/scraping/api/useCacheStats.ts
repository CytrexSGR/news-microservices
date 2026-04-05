import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { CacheStats } from '../types/scraping.types';

/**
 * Query keys for cache
 */
export const cacheStatsQueryKey = ['scraping', 'cache', 'stats'] as const;
export const cacheEntryQueryKey = (url: string) => ['scraping', 'cache', 'entry', url] as const;

/**
 * Cached content response
 */
interface CachedContent {
  url: string;
  domain: string;
  content: string;
  title?: string;
  author?: string;
  cached_at: string;
  expires_at: string;
  size_bytes: number;
}

/**
 * Fetch cache statistics
 */
async function fetchCacheStats(): Promise<CacheStats> {
  return mcpClient.callTool<CacheStats>('scraping_get_cache_stats');
}

/**
 * Fetch cached content for a URL
 */
async function fetchCachedContent(url: string): Promise<CachedContent | null> {
  return mcpClient.callTool<CachedContent | null>('scraping_get_cached_content', { url });
}

/**
 * Hook to fetch cache statistics
 *
 * @param options - React Query options
 * @returns Query result with cache stats
 *
 * @example
 * ```tsx
 * const { data } = useCacheStats();
 * console.log(`Cache hit rate: ${(data?.hit_rate * 100).toFixed(1)}%`);
 * ```
 */
export function useCacheStats(
  options?: Omit<UseQueryOptions<CacheStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: cacheStatsQueryKey,
    queryFn: fetchCacheStats,
    staleTime: 30000,
    refetchInterval: 60000,
    ...options,
  });
}

/**
 * Hook to fetch cached content for a URL
 */
export function useCachedContent(
  url: string,
  options?: Omit<UseQueryOptions<CachedContent | null>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: cacheEntryQueryKey(url),
    queryFn: () => fetchCachedContent(url),
    enabled: !!url,
    staleTime: 60000,
    ...options,
  });
}

import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { CacheInvalidateParams, CacheActionResponse } from '../types/scraping.types';
import { cacheStatsQueryKey } from './useCacheStats';

/**
 * Invalidate cache entries
 */
async function invalidateCache(params: CacheInvalidateParams): Promise<CacheActionResponse> {
  return mcpClient.callTool<CacheActionResponse>('scraping_invalidate_cache', params);
}

/**
 * Clear all cache
 */
async function clearCache(): Promise<CacheActionResponse> {
  return mcpClient.callTool<CacheActionResponse>('scraping_clear_cache', {});
}

/**
 * Warm cache for a list of URLs
 */
async function warmCache(urls: string[]): Promise<{ success: boolean; warmed: number; failed: number }> {
  return mcpClient.callTool<{ success: boolean; warmed: number; failed: number }>('scraping_warm_cache', { urls });
}

/**
 * Expire old cache entries
 */
async function expireCache(older_than_hours: number): Promise<CacheActionResponse> {
  return mcpClient.callTool<CacheActionResponse>('scraping_expire_cache', { older_than_hours });
}

/**
 * Hook to invalidate cache entries
 *
 * @example
 * ```tsx
 * const invalidate = useInvalidateCache();
 *
 * // Invalidate by URL
 * await invalidate.mutateAsync({ url: 'https://example.com/article' });
 *
 * // Invalidate by domain
 * await invalidate.mutateAsync({ domain: 'example.com' });
 *
 * // Invalidate old entries
 * await invalidate.mutateAsync({ older_than_hours: 24 });
 * ```
 */
export function useInvalidateCache(
  options?: Omit<UseMutationOptions<CacheActionResponse, Error, CacheInvalidateParams>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: invalidateCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheStatsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to clear all cache
 */
export function useClearCache(
  options?: Omit<UseMutationOptions<CacheActionResponse, Error, void>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: ['scraping', 'cache', 'entry'] });
    },
    ...options,
  });
}

/**
 * Hook to warm cache for URLs
 */
export function useWarmCache(
  options?: Omit<UseMutationOptions<{ success: boolean; warmed: number; failed: number }, Error, string[]>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: warmCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheStatsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to expire old cache entries
 */
export function useExpireCache(
  options?: Omit<UseMutationOptions<CacheActionResponse, Error, number>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: expireCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheStatsQueryKey });
    },
    ...options,
  });
}

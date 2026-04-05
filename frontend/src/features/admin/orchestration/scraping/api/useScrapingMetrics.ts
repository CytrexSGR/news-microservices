import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { ScrapingMetrics, ActiveJob, RateLimitInfo, FeedFailure } from '../types/scraping.types';

/**
 * Query keys for scraping metrics
 */
export const scrapingMetricsQueryKey = ['scraping', 'metrics'] as const;
export const activeJobsQueryKey = ['scraping', 'active-jobs'] as const;
export const rateLimitsQueryKey = ['scraping', 'rate-limits'] as const;
export const feedFailuresQueryKey = ['scraping', 'feed-failures'] as const;

/**
 * Fetch scraping metrics using MCP tool
 */
async function fetchScrapingMetrics(): Promise<ScrapingMetrics> {
  return mcpClient.callTool<ScrapingMetrics>('scraping_get_metrics');
}

/**
 * Fetch active scraping jobs
 */
async function fetchActiveJobs(): Promise<{ jobs: ActiveJob[] }> {
  return mcpClient.callTool<{ jobs: ActiveJob[] }>('scraping_get_active_jobs');
}

/**
 * Fetch rate limit information
 */
async function fetchRateLimits(): Promise<{ limits: RateLimitInfo[] }> {
  return mcpClient.callTool<{ limits: RateLimitInfo[] }>('scraping_get_rate_limits');
}

/**
 * Fetch feed failures
 */
async function fetchFeedFailures(params?: { limit?: number }): Promise<{ failures: FeedFailure[] }> {
  return mcpClient.callTool<{ failures: FeedFailure[] }>('scraping_get_feed_failures', params || {});
}

/**
 * Hook to fetch scraping metrics
 *
 * @param options - React Query options
 * @returns Query result with scraping metrics
 */
export function useScrapingMetrics(
  options?: Omit<UseQueryOptions<ScrapingMetrics>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: scrapingMetricsQueryKey,
    queryFn: fetchScrapingMetrics,
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    ...options,
  });
}

/**
 * Hook to fetch active scraping jobs
 */
export function useActiveJobs(
  options?: Omit<UseQueryOptions<{ jobs: ActiveJob[] }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: activeJobsQueryKey,
    queryFn: fetchActiveJobs,
    staleTime: 5000,
    refetchInterval: 10000,
    ...options,
  });
}

/**
 * Hook to fetch rate limit status
 */
export function useRateLimits(
  options?: Omit<UseQueryOptions<{ limits: RateLimitInfo[] }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: rateLimitsQueryKey,
    queryFn: fetchRateLimits,
    staleTime: 10000,
    ...options,
  });
}

/**
 * Hook to fetch feed failures
 */
export function useFeedFailures(
  params?: { limit?: number },
  options?: Omit<UseQueryOptions<{ failures: FeedFailure[] }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...feedFailuresQueryKey, params],
    queryFn: () => fetchFeedFailures(params),
    staleTime: 30000,
    ...options,
  });
}

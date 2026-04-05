import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { RateLimitInfo } from '../types/scraping.types';

/**
 * Query keys
 */
export const rateLimitStatusQueryKey = ['scraping', 'rate-limits'] as const;
export const domainRateLimitQueryKey = (domain: string) => ['scraping', 'rate-limits', domain] as const;

/**
 * Rate limit configuration
 */
interface RateLimitConfig {
  domain: string;
  requests_per_minute: number;
  burst_limit?: number;
  cooldown_seconds?: number;
}

/**
 * Rate limit action response
 */
interface RateLimitActionResponse {
  success: boolean;
  domain: string;
  message: string;
}

/**
 * Fetch rate limit status
 */
async function fetchRateLimitStatus(): Promise<{ limits: RateLimitInfo[] }> {
  return mcpClient.callTool<{ limits: RateLimitInfo[] }>('scraping_get_rate_limit_status');
}

/**
 * Fetch rate limit for a specific domain
 */
async function fetchDomainRateLimit(domain: string): Promise<RateLimitInfo> {
  return mcpClient.callTool<RateLimitInfo>('scraping_get_domain_rate_limit', { domain });
}

/**
 * Set rate limit for a domain
 */
async function setRateLimit(config: RateLimitConfig): Promise<RateLimitActionResponse> {
  return mcpClient.callTool<RateLimitActionResponse>('scraping_set_rate_limit', config);
}

/**
 * Reset rate limit for a domain
 */
async function resetRateLimit(domain: string): Promise<RateLimitActionResponse> {
  return mcpClient.callTool<RateLimitActionResponse>('scraping_reset_rate_limit', { domain });
}

/**
 * Clear all rate limits
 */
async function clearRateLimits(): Promise<{ success: boolean; cleared: number }> {
  return mcpClient.callTool<{ success: boolean; cleared: number }>('scraping_clear_rate_limits', {});
}

/**
 * Hook to fetch rate limit status
 *
 * @example
 * ```tsx
 * const { data } = useRateLimitStatus();
 * const limitedDomains = data?.limits.filter(l => l.is_limited);
 * ```
 */
export function useRateLimitStatus(
  options?: Omit<UseQueryOptions<{ limits: RateLimitInfo[] }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: rateLimitStatusQueryKey,
    queryFn: fetchRateLimitStatus,
    staleTime: 10000,
    refetchInterval: 30000,
    ...options,
  });
}

/**
 * Hook to fetch rate limit for a specific domain
 */
export function useDomainRateLimit(
  domain: string,
  options?: Omit<UseQueryOptions<RateLimitInfo>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: domainRateLimitQueryKey(domain),
    queryFn: () => fetchDomainRateLimit(domain),
    enabled: !!domain,
    staleTime: 10000,
    ...options,
  });
}

/**
 * Hook to set rate limit for a domain
 */
export function useSetRateLimit(
  options?: Omit<UseMutationOptions<RateLimitActionResponse, Error, RateLimitConfig>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: setRateLimit,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: rateLimitStatusQueryKey });
      queryClient.invalidateQueries({ queryKey: domainRateLimitQueryKey(variables.domain) });
    },
    ...options,
  });
}

/**
 * Hook to reset rate limit for a domain
 */
export function useResetRateLimit(
  options?: Omit<UseMutationOptions<RateLimitActionResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resetRateLimit,
    onSuccess: (_, domain) => {
      queryClient.invalidateQueries({ queryKey: rateLimitStatusQueryKey });
      queryClient.invalidateQueries({ queryKey: domainRateLimitQueryKey(domain) });
    },
    ...options,
  });
}

/**
 * Hook to clear all rate limits
 */
export function useClearRateLimits(
  options?: Omit<UseMutationOptions<{ success: boolean; cleared: number }, Error, void>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearRateLimits,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rateLimitStatusQueryKey });
    },
    ...options,
  });
}

import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { ScrapingHealth } from '../types/scraping.types';

/**
 * Query key for scraping health
 */
export const scrapingHealthQueryKey = ['scraping', 'health'] as const;

/**
 * Fetch scraping service health using MCP tool
 */
async function fetchScrapingHealth(): Promise<ScrapingHealth> {
  return mcpClient.callTool<ScrapingHealth>('scraping_get_health');
}

/**
 * Hook to fetch scraping service health status
 *
 * @param options - React Query options
 * @returns Query result with scraping health
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useScrapingHealth();
 *
 * if (data?.status === 'healthy') {
 *   // All components are working
 * }
 * ```
 */
export function useScrapingHealth(
  options?: Omit<UseQueryOptions<ScrapingHealth>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: scrapingHealthQueryKey,
    queryFn: fetchScrapingHealth,
    staleTime: 5000, // 5 seconds
    refetchInterval: 15000, // Auto-refresh every 15 seconds
    ...options,
  });
}

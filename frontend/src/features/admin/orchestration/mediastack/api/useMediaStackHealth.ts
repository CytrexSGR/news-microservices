import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';

/**
 * MediaStack Health Response
 */
export interface MediaStackHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  api_reachable: boolean;
  api_key_valid: boolean;
  latency_ms: number;
  last_check: string;
  error?: string;
}

/**
 * Query key for MediaStack health
 */
export const mediaStackHealthQueryKey = ['mediastack', 'health'] as const;

/**
 * Check MediaStack API health status
 */
async function checkMediaStackHealth(): Promise<MediaStackHealth> {
  return mcpClient.callTool<MediaStackHealth>('mediastack_health');
}

/**
 * Hook to check MediaStack API health status
 *
 * @param options - React Query options
 * @returns Query result with health status
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useMediaStackHealth();
 *
 * if (data?.status === 'healthy') {
 *   // API is working
 * }
 * ```
 */
export function useMediaStackHealth(
  options?: Omit<UseQueryOptions<MediaStackHealth>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: mediaStackHealthQueryKey,
    queryFn: checkMediaStackHealth,
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
    ...options,
  });
}

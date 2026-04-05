import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { ProxyInfo, ProxyStats } from '../types/scraping.types';

/**
 * Query keys for proxies
 */
export const proxyListQueryKey = ['scraping', 'proxies'] as const;
export const proxyStatsQueryKey = ['scraping', 'proxies', 'stats'] as const;
export const proxyQueryKey = (proxyId: string) => ['scraping', 'proxies', proxyId] as const;

/**
 * Fetch proxy list
 */
async function fetchProxyList(): Promise<{ proxies: ProxyInfo[] }> {
  return mcpClient.callTool<{ proxies: ProxyInfo[] }>('scraping_get_proxy_list');
}

/**
 * Fetch proxy statistics
 */
async function fetchProxyStats(): Promise<ProxyStats> {
  return mcpClient.callTool<ProxyStats>('scraping_get_proxy_stats');
}

/**
 * Fetch single proxy info
 */
async function fetchProxy(proxyId: string): Promise<ProxyInfo> {
  return mcpClient.callTool<ProxyInfo>('scraping_get_proxy', { proxy_id: proxyId });
}

/**
 * Hook to fetch proxy list
 *
 * @param options - React Query options
 * @returns Query result with proxy list
 *
 * @example
 * ```tsx
 * const { data } = useProxyList();
 * const healthyProxies = data?.proxies.filter(p => p.status === 'healthy');
 * ```
 */
export function useProxyList(
  options?: Omit<UseQueryOptions<{ proxies: ProxyInfo[] }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: proxyListQueryKey,
    queryFn: fetchProxyList,
    staleTime: 30000,
    refetchInterval: 60000,
    ...options,
  });
}

/**
 * Hook to fetch proxy statistics
 */
export function useProxyStats(
  options?: Omit<UseQueryOptions<ProxyStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: proxyStatsQueryKey,
    queryFn: fetchProxyStats,
    staleTime: 30000,
    refetchInterval: 60000,
    ...options,
  });
}

/**
 * Hook to fetch a single proxy
 */
export function useProxy(
  proxyId: string,
  options?: Omit<UseQueryOptions<ProxyInfo>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: proxyQueryKey(proxyId),
    queryFn: () => fetchProxy(proxyId),
    enabled: !!proxyId,
    staleTime: 30000,
    ...options,
  });
}

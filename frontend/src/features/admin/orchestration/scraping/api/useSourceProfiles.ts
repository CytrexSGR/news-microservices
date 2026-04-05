import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  SourceProfile,
  SourcesListParams,
  SourcesListResponse,
  SourcesStats,
  SourceConfig,
} from '../types/scraping.types';

/**
 * Query keys for source profiles
 */
export const sourceProfilesQueryKey = ['scraping', 'sources'] as const;
export const sourceProfileQueryKey = (domain: string) => ['scraping', 'sources', domain] as const;
export const sourcesStatsQueryKey = ['scraping', 'sources', 'stats'] as const;
export const sourceConfigQueryKey = (url: string) => ['scraping', 'sources', 'config', url] as const;

/**
 * Fetch source profiles list
 */
async function fetchSourceProfiles(params?: SourcesListParams): Promise<SourcesListResponse> {
  return mcpClient.callTool<SourcesListResponse>('scraping_list_source_profiles', params || {});
}

/**
 * Fetch single source profile by domain
 */
async function fetchSourceProfile(domain: string): Promise<SourceProfile> {
  return mcpClient.callTool<SourceProfile>('scraping_get_source_profile', { domain });
}

/**
 * Fetch sources statistics
 */
async function fetchSourcesStats(): Promise<SourcesStats> {
  return mcpClient.callTool<SourcesStats>('scraping_get_sources_stats');
}

/**
 * Analyze URL and get recommended configuration
 */
async function analyzeSourceConfig(url: string): Promise<SourceConfig> {
  return mcpClient.callTool<SourceConfig>('scraping_analyze_source', { url });
}

/**
 * Hook to fetch source profiles list
 *
 * @param params - Filter parameters
 * @param options - React Query options
 * @returns Query result with source profiles
 *
 * @example
 * ```tsx
 * const { data } = useSourceProfiles({ status: 'working', limit: 20 });
 * ```
 */
export function useSourceProfiles(
  params?: SourcesListParams,
  options?: Omit<UseQueryOptions<SourcesListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [...sourceProfilesQueryKey, params],
    queryFn: () => fetchSourceProfiles(params),
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Hook to fetch single source profile
 *
 * @param domain - Domain to fetch
 * @param options - React Query options
 */
export function useSourceProfile(
  domain: string,
  options?: Omit<UseQueryOptions<SourceProfile>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: sourceProfileQueryKey(domain),
    queryFn: () => fetchSourceProfile(domain),
    enabled: !!domain,
    staleTime: 60000, // 1 minute
    ...options,
  });
}

/**
 * Hook to fetch sources statistics
 */
export function useSourcesStats(
  options?: Omit<UseQueryOptions<SourcesStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: sourcesStatsQueryKey,
    queryFn: fetchSourcesStats,
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to analyze a URL and get recommended config
 */
export function useSourceConfig(
  url: string,
  options?: Omit<UseQueryOptions<SourceConfig>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: sourceConfigQueryKey(url),
    queryFn: () => analyzeSourceConfig(url),
    enabled: !!url,
    staleTime: 300000, // 5 minutes
    ...options,
  });
}

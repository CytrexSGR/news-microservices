import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { MediaStackSourcesResponse, MediaStackSourcesParams } from '../types/mediastack.types';

/**
 * Query key for MediaStack sources
 */
export const mediaStackSourcesQueryKey = (params: MediaStackSourcesParams) =>
  ['mediastack', 'sources', params] as const;

/**
 * Fetch available news sources from MediaStack
 */
async function fetchMediaStackSources(params: MediaStackSourcesParams): Promise<MediaStackSourcesResponse> {
  // Convert arrays to comma-separated strings for the API
  const apiParams: Record<string, unknown> = {};

  if (params.countries?.length) apiParams.countries = params.countries.join(',');
  if (params.categories?.length) apiParams.categories = params.categories.join(',');
  if (params.languages?.length) apiParams.languages = params.languages.join(',');
  if (params.search) apiParams.search = params.search;
  if (params.limit) apiParams.limit = params.limit;
  if (params.offset) apiParams.offset = params.offset;

  return mcpClient.callTool<MediaStackSourcesResponse>('mediastack_fetch_sources', apiParams);
}

/**
 * Hook to fetch available news sources from MediaStack
 *
 * @param params - Filter parameters
 * @param options - React Query options
 * @returns Query result with sources list
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useMediaStackSources({
 *   countries: ['de'],
 *   categories: ['technology']
 * });
 * ```
 */
export function useMediaStackSources(
  params: MediaStackSourcesParams = {},
  options?: Omit<UseQueryOptions<MediaStackSourcesResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: mediaStackSourcesQueryKey(params),
    queryFn: () => fetchMediaStackSources(params),
    staleTime: 30 * 60 * 1000, // 30 minutes (sources don't change often)
    ...options,
  });
}

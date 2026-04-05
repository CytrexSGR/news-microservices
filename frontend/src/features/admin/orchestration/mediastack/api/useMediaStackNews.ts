import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { MediaStackNewsResponse, MediaStackNewsParams } from '../types/mediastack.types';

/**
 * Query key for MediaStack news
 */
export const mediaStackNewsQueryKey = (params: MediaStackNewsParams) =>
  ['mediastack', 'news', params] as const;

/**
 * Fetch news articles from MediaStack
 */
async function fetchMediaStackNews(params: MediaStackNewsParams): Promise<MediaStackNewsResponse> {
  // Convert arrays to comma-separated strings for the API
  const apiParams: Record<string, unknown> = {};

  if (params.keywords) apiParams.keywords = params.keywords;
  if (params.sources?.length) apiParams.sources = params.sources.join(',');
  if (params.categories?.length) apiParams.categories = params.categories.join(',');
  if (params.countries?.length) apiParams.countries = params.countries.join(',');
  if (params.languages?.length) apiParams.languages = params.languages.join(',');
  if (params.sort) apiParams.sort = params.sort;
  if (params.limit) apiParams.limit = params.limit;
  if (params.offset) apiParams.offset = params.offset;

  return mcpClient.callTool<MediaStackNewsResponse>('mediastack_fetch_news', apiParams);
}

/**
 * Hook to fetch news articles from MediaStack
 *
 * @param params - Search/filter parameters
 * @param options - React Query options
 * @returns Query result with news articles
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useMediaStackNews({
 *   keywords: 'technology',
 *   countries: ['de', 'us'],
 *   limit: 25
 * });
 * ```
 */
export function useMediaStackNews(
  params: MediaStackNewsParams = {},
  options?: Omit<UseQueryOptions<MediaStackNewsResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: mediaStackNewsQueryKey(params),
    queryFn: () => fetchMediaStackNews(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

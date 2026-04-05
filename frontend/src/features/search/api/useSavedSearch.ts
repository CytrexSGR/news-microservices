/**
 * useSavedSearch Hook
 *
 * Query hook for fetching a single saved search by ID.
 */

import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import type { SavedSearch } from '../types/search.types';
import { savedSearchKeys } from './useSavedSearches';

/**
 * Fetch a single saved search by ID
 */
const fetchSavedSearch = async (id: string): Promise<SavedSearch> => {
  const { data } = await searchApi.get<SavedSearch>(`/search/saved/${id}`);
  return data;
};

/**
 * Hook to fetch a single saved search
 *
 * @param id - Saved search ID
 * @param options - React Query options
 *
 * @example
 * ```tsx
 * const { data: savedSearch, isLoading } = useSavedSearch('123');
 *
 * if (isLoading) return <Loading />;
 *
 * return <div>{savedSearch.name}</div>;
 * ```
 */
export function useSavedSearch(
  id: string | undefined,
  options?: Omit<
    UseQueryOptions<SavedSearch, Error>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<SavedSearch, Error>({
    queryKey: savedSearchKeys.detail(id ? Number(id) : 0),
    queryFn: () => fetchSavedSearch(id!),
    enabled: !!id,
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Hook to fetch saved search with extended details including run history
 *
 * @param id - Saved search ID
 * @param options - React Query options
 */
export function useSavedSearchWithHistory(
  id: string | undefined,
  options?: Omit<
    UseQueryOptions<SavedSearch & { run_history?: Array<{ executed_at: string; result_count: number }> }, Error>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery({
    queryKey: [...savedSearchKeys.detail(id ? Number(id) : 0), 'history'],
    queryFn: async () => {
      const { data } = await searchApi.get<SavedSearch>(`/search/saved/${id}`, {
        params: { include_history: true },
      });
      return data;
    },
    enabled: !!id,
    staleTime: 30000,
    ...options,
  });
}

/**
 * useExecuteSavedSearch Hook
 *
 * Mutation hook for executing saved searches and retrieving results.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { searchApi } from '@/api/axios';
import toast from 'react-hot-toast';
import type { SearchExecuteResponse, QuickSearchRequest } from '../types/search.types';
import { savedSearchKeys } from './useSavedSearches';

// =============================================================================
// Query Keys
// =============================================================================

export const searchExecuteKeys = {
  all: ['search-execute'] as const,
  savedSearch: (id: string) => [...searchExecuteKeys.all, 'saved', id] as const,
  quick: (query: string) => [...searchExecuteKeys.all, 'quick', query] as const,
  suggestions: () => [...searchExecuteKeys.all, 'suggestions'] as const,
};

// =============================================================================
// API Functions
// =============================================================================

interface ExecuteSavedSearchParams {
  id: string;
  page?: number;
  page_size?: number;
}

/**
 * Execute a saved search
 */
const executeSavedSearch = async ({
  id,
  page = 1,
  page_size = 20,
}: ExecuteSavedSearchParams): Promise<SearchExecuteResponse> => {
  const { data } = await searchApi.post<SearchExecuteResponse>(
    `/search/saved/${id}/execute`,
    null,
    { params: { page, page_size } }
  );
  return data;
};

/**
 * Execute a quick search (not saved)
 */
const executeQuickSearch = async (
  params: QuickSearchRequest
): Promise<SearchExecuteResponse> => {
  const { data } = await searchApi.post<SearchExecuteResponse>(
    '/search/execute',
    params
  );
  return data;
};

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to execute a saved search
 *
 * Returns mutation for running saved searches with pagination support.
 *
 * @example
 * ```tsx
 * const { mutate: executeSearch, data: results, isPending } = useExecuteSavedSearch();
 *
 * const handleRun = () => {
 *   executeSearch({
 *     id: '123',
 *     page: 1,
 *     page_size: 20,
 *   });
 * };
 *
 * if (results) {
 *   console.log(`Found ${results.total} results`);
 * }
 * ```
 */
export function useExecuteSavedSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: executeSavedSearch,
    onSuccess: (data, variables) => {
      // Cache the results
      queryClient.setQueryData(
        searchExecuteKeys.savedSearch(variables.id),
        data
      );
      // Invalidate saved search list to update last_run timestamp
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() });
      toast.success(`Found ${data.total} results in ${data.execution_time_ms}ms`);
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to execute search');
    },
  });
}

/**
 * Hook to get cached results from last saved search execution
 *
 * @param id - Saved search ID
 *
 * @example
 * ```tsx
 * const { data: cachedResults } = useSavedSearchResults('123');
 * ```
 */
export function useSavedSearchResults(id: string | undefined) {
  return useQuery<SearchExecuteResponse>({
    queryKey: searchExecuteKeys.savedSearch(id || ''),
    queryFn: () => executeSavedSearch({ id: id! }),
    enabled: false, // Don't auto-fetch, only use cached data
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to execute a quick search (not saved)
 *
 * @example
 * ```tsx
 * const { mutate: search, data: results, isPending } = useQuickSearch();
 *
 * const handleSearch = (query: string) => {
 *   search({
 *     query,
 *     filters: { sentiment: 'positive' },
 *     page: 1,
 *     page_size: 20,
 *   });
 * };
 * ```
 */
export function useQuickSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: executeQuickSearch,
    onSuccess: (data, variables) => {
      // Cache the results
      queryClient.setQueryData(
        searchExecuteKeys.quick(variables.query),
        data
      );
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Search failed');
    },
  });
}

/**
 * Hook for live search with auto-execution on query change
 *
 * @param request - Search request parameters
 * @param enabled - Whether to enable the query
 *
 * @example
 * ```tsx
 * const [query, setQuery] = useState('');
 * const { data, isLoading } = useLiveSearch(
 *   { query, page: 1, page_size: 10 },
 *   query.length >= 3
 * );
 * ```
 */
export function useLiveSearch(
  request: QuickSearchRequest,
  enabled = true
) {
  return useQuery<SearchExecuteResponse>({
    queryKey: [...searchExecuteKeys.quick(request.query), request.filters, request.page],
    queryFn: () => executeQuickSearch(request),
    enabled: enabled && request.query.length >= 2,
    staleTime: 30000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook to fetch search suggestions based on query
 *
 * @param query - Current search query
 *
 * @example
 * ```tsx
 * const { data: suggestions } = useSearchSuggestions('artif');
 * // suggestions.queries = ['artificial intelligence', 'artificial neural networks']
 * ```
 */
export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: [...searchExecuteKeys.suggestions(), query],
    queryFn: async () => {
      const { data } = await searchApi.get('/search/suggestions', {
        params: { query, limit: 10 },
      });
      return data as {
        queries: string[];
        entities: Array<{ name: string; type: string }>;
        recent: Array<{ query: string; timestamp: string }>;
      };
    },
    enabled: query.length >= 2,
    staleTime: 60000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to run a saved search and navigate to results
 *
 * Wrapper that combines execution with navigation callback.
 *
 * @param onNavigate - Callback to navigate to results page
 *
 * @example
 * ```tsx
 * const navigate = useNavigate();
 * const { mutate: runAndNavigate } = useRunSavedSearchWithNavigation(
 *   (id, total) => navigate(`/search/results/${id}?total=${total}`)
 * );
 *
 * runAndNavigate('123');
 * ```
 */
export function useRunSavedSearchWithNavigation(
  onNavigate: (id: string, total: number) => void
) {
  const { mutate: execute, ...rest } = useExecuteSavedSearch();

  const runAndNavigate = (id: string) => {
    execute(
      { id },
      {
        onSuccess: (data) => {
          onNavigate(id, data.total);
        },
      }
    );
  };

  return {
    mutate: runAndNavigate,
    ...rest,
  };
}

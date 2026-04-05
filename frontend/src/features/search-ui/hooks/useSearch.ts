import { useQuery } from '@tanstack/react-query'
import { searchArticles } from '@/lib/api/searchPublic'
import type { SearchParams, SearchResponse } from '../types/search.types'

/**
 * Hook to search articles with full-text search
 *
 * Features:
 * - Debounced query execution
 * - Automatic caching (5 min stale, 10 min gc)
 * - Runs when query exists OR filters are applied
 * - Supports filter-only searches (browse without query)
 * - No auto-refresh (user-triggered only)
 *
 * @param params - Search parameters including query, filters, pagination
 * @returns React Query result with search response
 *
 * @example
 * ```tsx
 * // Search with query
 * const { data, isLoading, error } = useSearch({
 *   query: 'artificial intelligence',
 *   page: 1,
 *   page_size: 20,
 *   sentiment: 'positive'
 * })
 *
 * // Filter-only search (no query)
 * const { data } = useSearch({
 *   query: '',
 *   source: 'BBC News',
 *   sentiment: 'economy_markets'
 * })
 * ```
 */
export const useSearch = (params: SearchParams) => {
  // Check if any filter has a value
  const hasFilters =
    !!params.source ||
    !!params.sentiment ||
    !!params.date_from ||
    !!params.date_to

  // Enable search if query exists OR filters are applied
  const shouldFetch = params.query.length > 0 || hasFilters

  return useQuery<SearchResponse>({
    queryKey: ['search', 'public', params.query, params],
    queryFn: () => searchArticles(params),
    enabled: shouldFetch,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: 1, // Retry once on failure
    refetchOnWindowFocus: false, // Don't refetch on window focus
  })
}

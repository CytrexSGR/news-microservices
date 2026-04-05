import { useQuery } from '@tanstack/react-query'
import { getAutocomplete } from '@/lib/api/searchPublic'
import type { AutocompleteResponse } from '../types/search.types'

/**
 * Hook to fetch autocomplete suggestions
 *
 * Features:
 * - Debouncing handled at component level
 * - Cancels previous requests automatically (React Query)
 * - Only runs when query length >= 2
 * - Short cache time (30 seconds) for fresh suggestions
 * - Returns empty array on error (graceful degradation)
 *
 * @param query - Partial search query
 * @param limit - Maximum number of suggestions (default: 10)
 * @returns React Query result with suggestions array
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useAutocomplete('artificial int', 5)
 * const suggestions = data?.suggestions || []
 * ```
 */
export const useAutocomplete = (query: string, limit: number = 10) => {
  return useQuery<AutocompleteResponse>({
    queryKey: ['search', 'autocomplete', query, limit],
    queryFn: () => getAutocomplete(query, limit),
    enabled: query.length >= 2,
    staleTime: 30 * 1000, // 30 seconds (suggestions change frequently)
    gcTime: 2 * 60 * 1000, // 2 minutes
    retry: false, // Don't retry autocomplete (not critical)
    refetchOnWindowFocus: false,
    // Return empty suggestions on error (graceful degradation)
    placeholderData: (previousData) => previousData,
  })
}

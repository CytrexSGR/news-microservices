import { useQuery } from '@tanstack/react-query'
import { getFacets } from '@/lib/api/searchPublic'
import type { FacetsResponse } from '../types/search.types'

/**
 * Hook to fetch available filter options (facets)
 *
 * Features:
 * - Fetches all unique sources and categories from index
 * - Aggressive caching (30 min stale, 1 hour gc)
 * - Auto-refresh on mount
 * - Used to populate filter dropdowns dynamically
 *
 * @returns React Query result with facets data
 *
 * @example
 * ```tsx
 * const { data: facets, isLoading } = useFacets()
 *
 * // Use in SearchFilters
 * <SearchFilters availableSources={facets?.sources || []} />
 * ```
 */
export const useFacets = () => {
  return useQuery<FacetsResponse>({
    queryKey: ['search', 'facets'],
    queryFn: getFacets,
    staleTime: 30 * 60 * 1000, // 30 minutes (facets don't change often)
    gcTime: 60 * 60 * 1000, // 1 hour
    retry: 2, // Retry twice on failure
    refetchOnWindowFocus: false,
  })
}

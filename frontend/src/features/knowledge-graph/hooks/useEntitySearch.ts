/**
 * useEntitySearch Hook
 *
 * Searches entities in the knowledge graph with debounced input.
 * Useful for autocomplete and search interfaces.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useEntitySearch(searchQuery, {
 *   entityType: 'PERSON',
 *   limit: 10,
 *   debounceMs: 300
 * })
 * ```
 */

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchEntities } from '@/lib/api/knowledgeGraphPublic'
import type { EntitySearchResponse } from '@/types/knowledgeGraphPublic'

export interface UseEntitySearchOptions {
  entityType?: string
  limit?: number
  debounceMs?: number
  enabled?: boolean
}

/**
 * Helper hook for debouncing values
 */
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}

export function useEntitySearch(
  query: string,
  options?: UseEntitySearchOptions
) {
  const debouncedQuery = useDebounce(query, options?.debounceMs ?? 300)

  return useQuery<EntitySearchResponse>({
    queryKey: [
      'knowledge-graph',
      'search',
      debouncedQuery,
      options?.entityType,
      options?.limit,
    ],
    queryFn: () =>
      searchEntities(
        debouncedQuery,
        options?.limit ?? 10,
        options?.entityType
      ),
    enabled: debouncedQuery.length >= 2 && (options?.enabled ?? true),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 60 * 1000, // 1 minute
  })
}

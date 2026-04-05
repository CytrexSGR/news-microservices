/**
 * useSources Hook
 *
 * Fetches list of sources with optional filtering and pagination.
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useSources({
 *   status: 'active',
 *   credibility_tier: 'tier_1',
 *   limit: 20
 * })
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getSourceList } from '@/lib/api/feedServiceAdmin'
import type { SourceFilters, SourceListResponse } from '@/types/source'

export interface UseSourcesOptions extends SourceFilters {
  refetchInterval?: number
  enabled?: boolean
}

export function useSources(options?: UseSourcesOptions) {
  const { refetchInterval, enabled = true, ...filters } = options ?? {}

  return useQuery<SourceListResponse>({
    queryKey: ['sources', filters],
    queryFn: () => getSourceList(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval,
    enabled,
  })
}

export const sourceQueryKeys = {
  all: ['sources'] as const,
  lists: () => [...sourceQueryKeys.all, 'list'] as const,
  list: (filters?: SourceFilters) => [...sourceQueryKeys.lists(), filters] as const,
  details: () => [...sourceQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...sourceQueryKeys.details(), id] as const,
  feeds: (id: string) => [...sourceQueryKeys.detail(id), 'feeds'] as const,
  assessment: (id: string) => [...sourceQueryKeys.detail(id), 'assessment'] as const,
}

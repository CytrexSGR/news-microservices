/**
 * useSource Hook
 *
 * Fetches a single source by ID with full details.
 *
 * @example
 * ```tsx
 * const { data: source, isLoading } = useSource(sourceId)
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { getSource, getSourceByDomain } from '@/lib/api/feedServiceAdmin'
import type { Source } from '@/types/source'
import { sourceQueryKeys } from './useSources'

export interface UseSourceOptions {
  enabled?: boolean
  refetchInterval?: number
}

export function useSource(sourceId: string, options?: UseSourceOptions) {
  return useQuery<Source>({
    queryKey: sourceQueryKeys.detail(sourceId),
    queryFn: () => getSource(sourceId),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled: (options?.enabled ?? true) && !!sourceId,
    refetchInterval: options?.refetchInterval,
  })
}

export function useSourceByDomain(domain: string, options?: UseSourceOptions) {
  return useQuery<Source>({
    queryKey: ['sources', 'by-domain', domain],
    queryFn: () => getSourceByDomain(domain),
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: (options?.enabled ?? true) && !!domain,
    refetchInterval: options?.refetchInterval,
  })
}

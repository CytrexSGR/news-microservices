/**
 * useSourceFeeds Hook
 *
 * Fetches feeds for a specific source.
 *
 * @example
 * ```tsx
 * const { data: feeds, isLoading } = useSourceFeeds(sourceId)
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getSourceFeeds,
  addSourceFeed,
  removeSourceFeed,
} from '@/lib/api/feedServiceAdmin'
import type { SourceFeed, AddSourceFeedRequest } from '@/types/source'
import { sourceQueryKeys } from './useSources'

export interface UseSourceFeedsOptions {
  enabled?: boolean
  refetchInterval?: number
}

export function useSourceFeeds(sourceId: string, options?: UseSourceFeedsOptions) {
  return useQuery<SourceFeed[]>({
    queryKey: sourceQueryKeys.feeds(sourceId),
    queryFn: () => getSourceFeeds(sourceId),
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: (options?.enabled ?? true) && !!sourceId,
    refetchInterval: options?.refetchInterval,
  })
}

export interface AddFeedParams {
  sourceId: string
  data: AddSourceFeedRequest
}

export interface UseAddSourceFeedOptions {
  onSuccess?: (feed: SourceFeed) => void
  onError?: (error: Error) => void
}

export function useAddSourceFeed(options?: UseAddSourceFeedOptions) {
  const queryClient = useQueryClient()

  return useMutation<SourceFeed, Error, AddFeedParams>({
    mutationFn: ({ sourceId, data }) => addSourceFeed(sourceId, data),
    onSuccess: (data, variables) => {
      // Invalidate feeds and source detail
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.feeds(variables.sourceId) })
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.detail(variables.sourceId) })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}

export interface RemoveFeedParams {
  sourceId: string
  feedId: string
}

export interface UseRemoveSourceFeedOptions {
  onSuccess?: () => void
  onError?: (error: Error) => void
}

export function useRemoveSourceFeed(options?: UseRemoveSourceFeedOptions) {
  const queryClient = useQueryClient()

  return useMutation<void, Error, RemoveFeedParams>({
    mutationFn: ({ sourceId, feedId }) => removeSourceFeed(sourceId, feedId),
    onSuccess: (_, variables) => {
      // Invalidate feeds and source detail
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.feeds(variables.sourceId) })
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.detail(variables.sourceId) })
      options?.onSuccess?.()
    },
    onError: options?.onError,
  })
}

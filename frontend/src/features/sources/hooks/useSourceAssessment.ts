/**
 * useSourceAssessment Hook
 *
 * Manages source assessment - fetching history and triggering new assessments.
 *
 * @example
 * ```tsx
 * const { data: history } = useSourceAssessmentHistory(sourceId)
 * const { mutate: triggerAssessment } = useTriggerSourceAssessment()
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getSourceAssessmentHistory,
  triggerSourceAssessment,
} from '@/lib/api/feedServiceAdmin'
import type { SourceAssessmentHistory, TriggerAssessmentResponse } from '@/types/source'
import { sourceQueryKeys } from './useSources'

export interface UseSourceAssessmentHistoryOptions {
  limit?: number
  enabled?: boolean
}

export function useSourceAssessmentHistory(
  sourceId: string,
  options?: UseSourceAssessmentHistoryOptions
) {
  return useQuery<SourceAssessmentHistory[]>({
    queryKey: [...sourceQueryKeys.assessment(sourceId), options?.limit],
    queryFn: () => getSourceAssessmentHistory(sourceId, options?.limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,
    enabled: (options?.enabled ?? true) && !!sourceId,
  })
}

export interface UseTriggerSourceAssessmentOptions {
  onSuccess?: (response: TriggerAssessmentResponse) => void
  onError?: (error: Error) => void
}

export function useTriggerSourceAssessment(options?: UseTriggerSourceAssessmentOptions) {
  const queryClient = useQueryClient()

  return useMutation<TriggerAssessmentResponse, Error, string>({
    mutationFn: triggerSourceAssessment,
    onSuccess: (data, sourceId) => {
      // Invalidate source detail and assessment history
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.detail(sourceId) })
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.assessment(sourceId) })
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.lists() })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}

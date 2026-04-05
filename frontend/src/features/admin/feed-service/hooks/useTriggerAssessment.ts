import { useMutation, useQueryClient } from '@tanstack/react-query'
import { triggerAssessment } from '@/lib/api/feedServiceAdmin'
import type { AssessmentTriggerResponse } from '@/types/feedServiceAdmin'
import toast from 'react-hot-toast'

/**
 * Hook to trigger assessment for a feed
 */
export const useTriggerAssessment = () => {
  const queryClient = useQueryClient()

  return useMutation<AssessmentTriggerResponse, Error, string>({
    mutationFn: triggerAssessment,
    onSuccess: (data) => {
      toast.success(data.message || 'Assessment triggered successfully')

      // Invalidate feed and assessment queries
      queryClient.invalidateQueries({
        queryKey: ['feed-service', 'feeds'],
      })
    },
    onError: (error) => {
      toast.error(`Assessment failed: ${error.message}`)
    },
  })
}

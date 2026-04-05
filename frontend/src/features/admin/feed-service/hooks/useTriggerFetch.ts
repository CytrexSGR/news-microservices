import { useMutation, useQueryClient } from '@tanstack/react-query'
import { triggerFetch } from '@/lib/api/feedServiceAdmin'
import type { FetchTriggerResponse } from '@/types/feedServiceAdmin'
import toast from 'react-hot-toast'

/**
 * Hook to trigger manual fetch for a feed
 */
export const useTriggerFetch = () => {
  const queryClient = useQueryClient()

  return useMutation<FetchTriggerResponse, Error, string>({
    mutationFn: triggerFetch,
    onSuccess: (data) => {
      toast.success(data.message || 'Fetch triggered successfully')

      // Invalidate feed queries to refresh data
      queryClient.invalidateQueries({
        queryKey: ['feed-service', 'feeds'],
      })
    },
    onError: (error) => {
      toast.error(`Fetch failed: ${error.message}`)
    },
  })
}

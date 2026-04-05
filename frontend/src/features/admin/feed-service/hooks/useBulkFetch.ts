import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bulkFetch } from '@/lib/api/feedServiceAdmin'
import type { BulkFetchRequest, BulkFetchResponse } from '@/types/feedServiceAdmin'
import toast from 'react-hot-toast'

/**
 * Hook to trigger bulk fetch operation
 */
export const useBulkFetch = () => {
  const queryClient = useQueryClient()

  return useMutation<BulkFetchResponse, Error, BulkFetchRequest>({
    mutationFn: bulkFetch,
    onSuccess: (data) => {
      toast.success(
        `Bulk fetch triggered: ${data.total_feeds} feeds (${data.successful_fetches} successful)`
      )

      // Invalidate feed queries to refresh data
      queryClient.invalidateQueries({
        queryKey: ['feed-service', 'feeds'],
      })
      queryClient.invalidateQueries({
        queryKey: ['feed-service', 'stats'],
      })
    },
    onError: (error) => {
      toast.error(`Bulk fetch failed: ${error.message}`)
    },
  })
}

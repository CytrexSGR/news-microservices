import { useMutation, useQueryClient } from '@tanstack/react-query'
import { resetFeedError } from '@/lib/api/feedServiceAdmin'
import type { ResetErrorResponse } from '@/types/feedServiceAdmin'
import toast from 'react-hot-toast'

/**
 * Hook to reset ERROR status on a feed
 *
 * Use cases:
 * - Feed had temporary network issue (HTTP 522, timeouts)
 * - Source server was down but is now back online
 * - Want to clear error before changing feed URL
 * - Manual recovery after investigating the error
 */
export const useResetError = () => {
  const queryClient = useQueryClient()

  return useMutation<ResetErrorResponse, Error, string>({
    mutationFn: resetFeedError,
    onSuccess: (data) => {
      if (data.success) {
        const duration = data.error_duration_hours
          ? ` (was in error for ${data.error_duration_hours.toFixed(1)}h)`
          : ''
        toast.success(`Error reset successfully${duration}`)
      } else {
        toast.info(data.message)
      }

      // Invalidate feed queries to refresh data
      queryClient.invalidateQueries({
        queryKey: ['feed-service', 'feeds'],
      })
    },
    onError: (error) => {
      toast.error(`Reset failed: ${error.message}`)
    },
  })
}

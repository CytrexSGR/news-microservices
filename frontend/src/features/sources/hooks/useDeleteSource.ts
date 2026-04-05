/**
 * useDeleteSource Hook
 *
 * Deletes a source by ID.
 *
 * @example
 * ```tsx
 * const { mutate: deleteSource, isPending } = useDeleteSource()
 *
 * deleteSource(sourceId)
 * ```
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteSource } from '@/lib/api/feedServiceAdmin'
import { sourceQueryKeys } from './useSources'

export interface UseDeleteSourceOptions {
  onSuccess?: () => void
  onError?: (error: Error) => void
}

export function useDeleteSource(options?: UseDeleteSourceOptions) {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: deleteSource,
    onSuccess: (_, sourceId) => {
      // Remove from cache and invalidate lists
      queryClient.removeQueries({ queryKey: sourceQueryKeys.detail(sourceId) })
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.lists() })
      options?.onSuccess?.()
    },
    onError: options?.onError,
  })
}

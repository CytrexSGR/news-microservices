/**
 * useUpdateSource Hook
 *
 * Updates an existing source.
 *
 * @example
 * ```tsx
 * const { mutate: updateSource, isPending } = useUpdateSource()
 *
 * updateSource({
 *   sourceId: '123',
 *   data: { canonical_name: 'New Name' }
 * })
 * ```
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateSource } from '@/lib/api/feedServiceAdmin'
import type { UpdateSourceRequest, Source } from '@/types/source'
import { sourceQueryKeys } from './useSources'

export interface UpdateSourceParams {
  sourceId: string
  data: UpdateSourceRequest
}

export interface UseUpdateSourceOptions {
  onSuccess?: (source: Source) => void
  onError?: (error: Error) => void
}

export function useUpdateSource(options?: UseUpdateSourceOptions) {
  const queryClient = useQueryClient()

  return useMutation<Source, Error, UpdateSourceParams>({
    mutationFn: ({ sourceId, data }) => updateSource(sourceId, data),
    onSuccess: (data, variables) => {
      // Invalidate specific source and lists
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.detail(variables.sourceId) })
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.lists() })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}

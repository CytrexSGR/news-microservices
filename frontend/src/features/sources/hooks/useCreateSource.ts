/**
 * useCreateSource Hook
 *
 * Creates a new source with the provided data.
 *
 * @example
 * ```tsx
 * const { mutate: createSource, isPending } = useCreateSource()
 *
 * createSource({
 *   domain: 'example.com',
 *   canonical_name: 'Example News'
 * })
 * ```
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createSource } from '@/lib/api/feedServiceAdmin'
import type { CreateSourceRequest, Source } from '@/types/source'
import { sourceQueryKeys } from './useSources'

export interface UseCreateSourceOptions {
  onSuccess?: (source: Source) => void
  onError?: (error: Error) => void
}

export function useCreateSource(options?: UseCreateSourceOptions) {
  const queryClient = useQueryClient()

  return useMutation<Source, Error, CreateSourceRequest>({
    mutationFn: createSource,
    onSuccess: (data) => {
      // Invalidate source lists to refetch
      queryClient.invalidateQueries({ queryKey: sourceQueryKeys.lists() })
      options?.onSuccess?.(data)
    },
    onError: options?.onError,
  })
}

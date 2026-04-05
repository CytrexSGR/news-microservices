/**
 * useCanonicalizeEntity Hook
 *
 * Mutation hook for canonicalizing a single entity.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { canonicalizeEntity } from './entitiesApi';
import type { CanonicalizeRequest, CanonicalEntity } from '../types/entities.types';

interface UseCanonicalizeEntityOptions {
  onSuccess?: (data: CanonicalEntity) => void;
  onError?: (error: Error) => void;
}

export function useCanonicalizeEntity(options?: UseCanonicalizeEntityOptions) {
  const queryClient = useQueryClient();

  return useMutation<CanonicalEntity, Error, CanonicalizeRequest>({
    mutationFn: canonicalizeEntity,
    onSuccess: (data) => {
      // Invalidate stats queries to reflect new entity
      queryClient.invalidateQueries({ queryKey: ['entities', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['entities', 'clusters'] });
      options?.onSuccess?.(data);
    },
    onError: (error) => {
      options?.onError?.(error);
    },
  });
}

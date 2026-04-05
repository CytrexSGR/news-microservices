/**
 * useBatchCanonicalize Hook
 *
 * Mutation hook for batch entity canonicalization.
 * Supports both sync and async modes.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { batchCanonicalizeEntities, batchCanonicalizeEntitiesAsync } from './entitiesApi';
import type {
  BatchCanonRequest,
  BatchCanonResponse,
  AsyncBatchCanonResponse,
} from '../types/entities.types';

interface UseBatchCanonicalizeOptions {
  async?: boolean;
  onSuccess?: (data: BatchCanonResponse | AsyncBatchCanonResponse) => void;
  onError?: (error: Error) => void;
}

export function useBatchCanonicalize(options?: UseBatchCanonicalizeOptions) {
  const queryClient = useQueryClient();
  const { async: useAsync = false, onSuccess, onError } = options || {};

  return useMutation<BatchCanonResponse | AsyncBatchCanonResponse, Error, BatchCanonRequest>({
    mutationFn: async (request) => {
      if (useAsync || request.entities.length > 10) {
        return batchCanonicalizeEntitiesAsync(request);
      }
      return batchCanonicalizeEntities(request);
    },
    onSuccess: (data) => {
      // Invalidate stats queries to reflect new entities
      queryClient.invalidateQueries({ queryKey: ['entities', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['entities', 'clusters'] });
      onSuccess?.(data);
    },
    onError: (error) => {
      onError?.(error);
    },
  });
}

/**
 * Sync-only batch canonicalization
 */
export function useBatchCanonicalizeSync(options?: Omit<UseBatchCanonicalizeOptions, 'async'>) {
  const queryClient = useQueryClient();
  const { onSuccess, onError } = options || {};

  return useMutation<BatchCanonResponse, Error, BatchCanonRequest>({
    mutationFn: batchCanonicalizeEntities,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['entities', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['entities', 'clusters'] });
      onSuccess?.(data);
    },
    onError: (error) => {
      onError?.(error);
    },
  });
}

/**
 * Async-only batch canonicalization
 */
export function useBatchCanonicalizeAsync(options?: Omit<UseBatchCanonicalizeOptions, 'async'>) {
  const queryClient = useQueryClient();
  const { onSuccess, onError } = options || {};

  return useMutation<AsyncBatchCanonResponse, Error, BatchCanonRequest>({
    mutationFn: batchCanonicalizeEntitiesAsync,
    onSuccess: (data) => {
      // Don't invalidate yet - wait for job to complete
      onSuccess?.(data);
    },
    onError: (error) => {
      onError?.(error);
    },
  });
}

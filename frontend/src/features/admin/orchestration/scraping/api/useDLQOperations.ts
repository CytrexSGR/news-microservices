import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { DLQStatus, DLQFailureReason } from '../types/scraping.types';
import { dlqStatsQueryKey, dlqEntriesQueryKey } from './useDLQStats';
import { queueStatsQueryKey } from './useQueueStats';

/**
 * Requeue DLQ entry response
 */
interface RequeueDLQResponse {
  success: boolean;
  entry_id: number;
  new_job_id: string;
  message: string;
}

/**
 * Bulk requeue response
 */
interface BulkRequeueResponse {
  success: boolean;
  requeued_count: number;
  failed_count: number;
  job_ids: string[];
}

/**
 * Purge DLQ response
 */
interface PurgeDLQResponse {
  success: boolean;
  purged_count: number;
  message: string;
}

/**
 * Update DLQ entry response
 */
interface UpdateDLQEntryResponse {
  success: boolean;
  entry_id: number;
  message: string;
}

/**
 * Requeue a single DLQ entry
 */
async function requeueDLQEntry(id: number): Promise<RequeueDLQResponse> {
  return mcpClient.callTool<RequeueDLQResponse>('scraping_requeue_dlq_entry', { id });
}

/**
 * Bulk requeue DLQ entries by filter
 */
async function bulkRequeueDLQ(params: {
  status?: DLQStatus;
  domain?: string;
  failure_reason?: DLQFailureReason;
  limit?: number;
}): Promise<BulkRequeueResponse> {
  return mcpClient.callTool<BulkRequeueResponse>('scraping_bulk_requeue_dlq', params);
}

/**
 * Purge DLQ entries
 */
async function purgeDLQ(params: {
  status?: DLQStatus;
  domain?: string;
  older_than_days?: number;
}): Promise<PurgeDLQResponse> {
  return mcpClient.callTool<PurgeDLQResponse>('scraping_purge_dlq', params);
}

/**
 * Update DLQ entry status
 */
async function updateDLQEntry(params: {
  id: number;
  status: DLQStatus;
  resolver_notes?: string;
}): Promise<UpdateDLQEntryResponse> {
  return mcpClient.callTool<UpdateDLQEntryResponse>('scraping_update_dlq_entry', params);
}

/**
 * Hook to requeue a single DLQ entry
 *
 * @example
 * ```tsx
 * const requeue = useRequeueDLQEntry();
 *
 * const handleRequeue = async (id: number) => {
 *   const result = await requeue.mutateAsync(id);
 *   toast.success(`Requeued as job ${result.new_job_id}`);
 * };
 * ```
 */
export function useRequeueDLQEntry(
  options?: Omit<UseMutationOptions<RequeueDLQResponse, Error, number>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: requeueDLQEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dlqStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: dlqEntriesQueryKey });
      queryClient.invalidateQueries({ queryKey: queueStatsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to bulk requeue DLQ entries
 */
export function useBulkRequeueDLQ(
  options?: Omit<UseMutationOptions<BulkRequeueResponse, Error, {
    status?: DLQStatus;
    domain?: string;
    failure_reason?: DLQFailureReason;
    limit?: number;
  }>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: bulkRequeueDLQ,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dlqStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: dlqEntriesQueryKey });
      queryClient.invalidateQueries({ queryKey: queueStatsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to purge DLQ entries
 */
export function usePurgeDLQ(
  options?: Omit<UseMutationOptions<PurgeDLQResponse, Error, {
    status?: DLQStatus;
    domain?: string;
    older_than_days?: number;
  }>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: purgeDLQ,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dlqStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: dlqEntriesQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to update a DLQ entry status
 */
export function useUpdateDLQEntry(
  options?: Omit<UseMutationOptions<UpdateDLQEntryResponse, Error, {
    id: number;
    status: DLQStatus;
    resolver_notes?: string;
  }>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateDLQEntry,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: dlqStatsQueryKey });
      queryClient.invalidateQueries({ queryKey: dlqEntriesQueryKey });
      queryClient.invalidateQueries({ queryKey: ['scraping', 'dlq', 'entry', variables.id] });
    },
    ...options,
  });
}

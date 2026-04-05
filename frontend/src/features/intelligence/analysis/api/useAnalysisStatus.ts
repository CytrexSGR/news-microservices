/**
 * useAnalysisStatus Hook
 *
 * Query hook for polling analysis status.
 * Automatically polls while status is 'pending' or 'processing'.
 */
import { useQuery } from '@tanstack/react-query';
import { getAnalysisStatus } from './analysisApi';
import type { AnalysisStatusResponse, AnalysisStatus } from '../types/analysis.types';

interface UseAnalysisStatusOptions {
  /** Article ID to check status for */
  articleId: string;
  /** Whether to enable the query */
  enabled?: boolean;
  /** Polling interval in milliseconds (default: 2 seconds) */
  pollingInterval?: number;
  /** Callback when status changes to completed */
  onCompleted?: (data: AnalysisStatusResponse) => void;
  /** Callback when status changes to failed */
  onFailed?: (data: AnalysisStatusResponse) => void;
}

/**
 * Check if status requires continued polling
 */
function shouldPoll(status: AnalysisStatus | undefined): boolean {
  return status === 'pending' || status === 'processing';
}

export function useAnalysisStatus({
  articleId,
  enabled = true,
  pollingInterval = 2000,
  onCompleted,
  onFailed,
}: UseAnalysisStatusOptions) {
  const query = useQuery<AnalysisStatusResponse, Error>({
    queryKey: ['analysis', 'status', articleId],
    queryFn: () => getAnalysisStatus(articleId),
    enabled: enabled && !!articleId,
    // Only refetch while processing
    refetchInterval: (query) => {
      const data = query.state.data;
      if (shouldPoll(data?.status)) {
        return pollingInterval;
      }
      return false;
    },
    staleTime: 1000, // Short stale time for status checks
  });

  // Trigger callbacks on status changes
  if (query.data?.status === 'completed' && onCompleted) {
    onCompleted(query.data);
  }
  if (query.data?.status === 'failed' && onFailed) {
    onFailed(query.data);
  }

  return {
    ...query,
    status: query.data?.status,
    progressPercent: query.data?.progress_percent,
    errorMessage: query.data?.error_message,
    startedAt: query.data?.started_at,
    completedAt: query.data?.completed_at,
    isPolling: shouldPoll(query.data?.status),
    isPending: query.data?.status === 'pending',
    isProcessing: query.data?.status === 'processing',
    isCompleted: query.data?.status === 'completed',
    isFailed: query.data?.status === 'failed',
  };
}

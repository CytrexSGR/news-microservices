/**
 * useAnalysisResult Hook
 *
 * Query hook for fetching complete analysis results.
 * Only enabled when analysis is completed.
 */
import { useQuery } from '@tanstack/react-query';
import { getAnalysisResult } from './analysisApi';
import type { AnalysisResult } from '../types/analysis.types';

interface UseAnalysisResultOptions {
  /** Article ID to fetch result for */
  articleId: string;
  /** Whether to enable the query */
  enabled?: boolean;
  /** Stale time in milliseconds (default: 10 minutes) */
  staleTime?: number;
}

export function useAnalysisResult({
  articleId,
  enabled = true,
  staleTime = 10 * 60 * 1000,
}: UseAnalysisResultOptions) {
  const query = useQuery<AnalysisResult, Error>({
    queryKey: ['analysis', 'result', articleId],
    queryFn: () => getAnalysisResult(articleId),
    enabled: enabled && !!articleId,
    staleTime,
    retry: 1,
  });

  return {
    ...query,
    result: query.data,
    entities: query.data?.entities || [],
    sentiment: query.data?.sentiment,
    topics: query.data?.topics || [],
    narrativeFrames: query.data?.narrative_frames || [],
    costUsd: query.data?.cost_usd,
    latencyMs: query.data?.latency_ms,
    analysisTimestamp: query.data?.analysis_timestamp,
  };
}

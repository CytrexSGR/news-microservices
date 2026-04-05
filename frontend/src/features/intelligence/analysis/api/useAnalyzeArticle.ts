/**
 * useAnalyzeArticle Hook
 *
 * Mutation hook for triggering article analysis.
 * Invalidates relevant queries on success.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { analyzeArticle } from './analysisApi';
import type { AnalyzeArticleRequest, AnalyzeArticleResponse } from '../types/analysis.types';

interface UseAnalyzeArticleOptions {
  onSuccess?: (data: AnalyzeArticleResponse) => void;
  onError?: (error: Error) => void;
}

export function useAnalyzeArticle(options?: UseAnalyzeArticleOptions) {
  const queryClient = useQueryClient();

  return useMutation<AnalyzeArticleResponse, Error, AnalyzeArticleRequest>({
    mutationFn: analyzeArticle,
    onSuccess: (data, variables) => {
      // Invalidate status query to trigger refetch
      queryClient.invalidateQueries({
        queryKey: ['analysis', 'status', variables.article_id],
      });

      // Invalidate entities query
      queryClient.invalidateQueries({
        queryKey: ['analysis', 'entities', variables.article_id],
      });

      // Invalidate result query
      queryClient.invalidateQueries({
        queryKey: ['analysis', 'result', variables.article_id],
      });

      options?.onSuccess?.(data);
    },
    onError: (error) => {
      options?.onError?.(error);
    },
  });
}

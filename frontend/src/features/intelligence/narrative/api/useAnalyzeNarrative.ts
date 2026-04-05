import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  NarrativeAnalysisRequest,
  NarrativeAnalysisResult,
} from '../types/narrative.types';

/**
 * MCP Tool Response for analyze_text_narrative
 */
interface AnalyzeNarrativeResponse {
  result: NarrativeAnalysisResult;
  metadata: {
    cached: boolean;
    processing_time_ms: number;
  };
}

/**
 * Hook for analyzing text for narrative frames
 *
 * Uses the MCP tool `analyze_text_narrative` which costs ~$0.002 per call.
 *
 * @example
 * ```tsx
 * const { mutate, data, isPending, error } = useAnalyzeNarrative();
 *
 * const handleAnalyze = () => {
 *   mutate({
 *     text: "The government announced new economic sanctions...",
 *     include_bias: true,
 *     include_propaganda: true
 *   });
 * };
 * ```
 */
export function useAnalyzeNarrative() {
  const queryClient = useQueryClient();

  return useMutation<NarrativeAnalysisResult, Error, NarrativeAnalysisRequest>({
    mutationKey: ['narrative', 'analyze'],
    mutationFn: async (request: NarrativeAnalysisRequest) => {
      const response = await mcpClient.callTool<AnalyzeNarrativeResponse>(
        'analyze_text_narrative',
        {
          text: request.text,
          include_bias: request.include_bias ?? true,
          include_propaganda: request.include_propaganda ?? false,
          language: request.language ?? 'en',
        },
        { timeout: 60000 } // 60 seconds for LLM processing
      );

      return response.result;
    },
    onSuccess: () => {
      // Invalidate overview to update statistics
      queryClient.invalidateQueries({ queryKey: ['narrative', 'overview'] });
    },
  });
}

/**
 * Estimated cost per analysis in USD
 */
export const NARRATIVE_ANALYSIS_COST_USD = 0.002;

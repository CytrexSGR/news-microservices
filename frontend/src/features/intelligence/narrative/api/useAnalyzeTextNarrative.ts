import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { RealTimeNarrativeAnalysis } from '../types/narrative.types';

/**
 * Parameters for real-time text narrative analysis
 */
export interface AnalyzeTextNarrativeParams {
  text: string;
  include_bias?: boolean;
  include_propaganda?: boolean;
  language?: string;
}

/**
 * MCP Tool Response for analyze_text_narrative
 */
interface AnalyzeTextNarrativeResponse {
  result: RealTimeNarrativeAnalysis;
  metadata: {
    cached: boolean;
    processing_time_ms: number;
    model_used: string;
  };
}

/**
 * Hook for real-time text narrative analysis
 *
 * Uses the MCP tool `analyze_text_narrative` for immediate text analysis.
 * This provides real-time frame detection, bias scoring, and propaganda detection.
 *
 * @example
 * ```tsx
 * const { mutate, data, isPending, error } = useAnalyzeTextNarrative();
 *
 * const handleAnalyze = () => {
 *   mutate({
 *     text: "The government announced new economic measures today...",
 *     include_bias: true,
 *     include_propaganda: true
 *   });
 * };
 *
 * // Access results
 * if (data) {
 *   console.log('Detected frames:', data.frames);
 *   console.log('Bias direction:', data.bias_direction);
 *   console.log('Propaganda signals:', data.propaganda_signals);
 * }
 * ```
 */
export function useAnalyzeTextNarrative() {
  const queryClient = useQueryClient();

  return useMutation<RealTimeNarrativeAnalysis, Error, AnalyzeTextNarrativeParams>({
    mutationKey: ['narrative', 'analyze', 'text'],
    mutationFn: async (params: AnalyzeTextNarrativeParams) => {
      // Validate text length
      if (!params.text || params.text.trim().length === 0) {
        throw new Error('Text is required for analysis');
      }

      if (params.text.length < 50) {
        throw new Error('Text must be at least 50 characters for meaningful analysis');
      }

      if (params.text.length > 50000) {
        throw new Error('Text exceeds maximum length of 50,000 characters');
      }

      const response = await mcpClient.callTool<AnalyzeTextNarrativeResponse>(
        'analyze_text_narrative',
        {
          text: params.text.trim(),
          include_bias: params.include_bias ?? true,
          include_propaganda: params.include_propaganda ?? true,
          language: params.language ?? 'en',
        },
        { timeout: 90000 } // 90 seconds for LLM processing
      );

      return response.result;
    },
    onSuccess: () => {
      // Invalidate overview and stats to reflect new analysis
      queryClient.invalidateQueries({ queryKey: ['narrative', 'overview'] });
      queryClient.invalidateQueries({ queryKey: ['narrative', 'kg', 'stats'] });
    },
  });
}

/**
 * Estimated cost per real-time analysis in USD
 */
export const REALTIME_ANALYSIS_COST_USD = 0.003;

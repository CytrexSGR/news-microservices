import { useMutation } from '@tanstack/react-query';
import { analyzeText, type TextAnalyzerInput, type TextAnalysisResult, type ApiResponse } from './narrativeApi';

/**
 * Hook for analyzing text for narrative frames and bias
 *
 * Uses mutation pattern since text analysis is a POST endpoint.
 * Results are cached on the backend (~3ms with cache, ~150ms without).
 *
 * @example
 * ```tsx
 * const { mutate, data, isPending, error } = useTextAnalysis();
 *
 * // Analyze article text
 * mutate({
 *   text: 'Breaking news: Major political developments...',
 *   source: 'reuters'
 * });
 *
 * // Access analysis results
 * if (data?.data) {
 *   console.log('Detected frames:', data.data.frames);
 *   console.log('Bias score:', data.data.bias.bias_score);
 *   console.log('Bias label:', data.data.bias.bias_label);
 * }
 * ```
 */
export function useTextAnalysis() {
  return useMutation<ApiResponse<TextAnalysisResult>, Error, TextAnalyzerInput>({
    mutationFn: (input) => analyzeText(input),
  });
}

/**
 * Convenience type exports
 */
export type { TextAnalyzerInput, TextAnalysisResult };

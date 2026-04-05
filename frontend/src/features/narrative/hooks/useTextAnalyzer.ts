import { useMutation } from '@tanstack/react-query';
import { analyzeText } from '../api';
import type { TextAnalyzerInput, TextAnalysisResult } from '../types';

/**
 * Hook for analyzing text for narrative frames, entities, and sentiment
 *
 * Uses the new fetch-based API with { data, error } response wrapper.
 *
 * @example
 * ```tsx
 * const { mutate, data, isPending, error } = useTextAnalyzer();
 *
 * const handleAnalyze = () => {
 *   mutate({
 *     text: "The government announced new sanctions...",
 *     options: {
 *       analyze_entities: true,
 *       analyze_sentiment: true,
 *       analyze_frames: true
 *     }
 *   });
 * };
 *
 * // Access result
 * if (data) {
 *   console.log(`Detected ${data.frames.length} frames`);
 *   console.log(`Bias: ${data.bias.bias_label}`);
 * }
 * ```
 */
export function useTextAnalyzer() {
  return useMutation<TextAnalysisResult, Error, TextAnalyzerInput>({
    mutationFn: async (input: TextAnalyzerInput) => {
      const { data, error } = await analyzeText(input);

      if (error) {
        throw new Error(error);
      }

      if (!data) {
        throw new Error('No data returned from analysis');
      }

      return data;
    },
    mutationKey: ['narrative', 'analyze-text'],
  });
}

export type { TextAnalyzerInput, TextAnalysisResult };

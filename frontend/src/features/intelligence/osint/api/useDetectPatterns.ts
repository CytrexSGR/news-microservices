/**
 * useDetectPatterns - Pattern Detection Mutation Hook
 *
 * Triggers intelligence pattern detection analysis across entities
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  PatternDetectionRequest,
  PatternDetectionResponse,
} from '../types/osint.types';

export function useDetectPatterns() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: PatternDetectionRequest): Promise<PatternDetectionResponse> => {
      return mcpClient.callTool<PatternDetectionResponse>(
        'detect_intelligence_patterns',
        {
          entity_ids: request.entity_ids,
          timeframe_days: request.timeframe_days ?? 30,
          pattern_types: request.pattern_types,
          min_confidence: request.min_confidence ?? 0.5,
        },
        { timeout: 60000 } // Pattern detection may take longer
      );
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['osint', 'patterns'] });
    },
  });
}

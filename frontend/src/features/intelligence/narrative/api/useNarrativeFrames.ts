import { useQuery } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  NarrativeFrame,
  NarrativeFramesResponse,
  NarrativeFilters,
  NarrativeType,
} from '../types/narrative.types';

/**
 * Extended parameters for narrative frames query
 */
export interface NarrativeFramesParams extends NarrativeFilters {
  limit?: number;
  category?: 'all' | 'political' | 'economic' | 'social' | 'crisis';
  include_examples?: boolean;
  language?: string;
}

/**
 * Hook for fetching available narrative frames
 *
 * Uses the MCP tool `get_narrative_frames` to retrieve the list of
 * narrative frames that can be detected in text analysis.
 *
 * @param params - Query parameters including filters, limit, and category
 * @param enabled - Whether to enable the query (default: true)
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useNarrativeFrames();
 *
 * // With full parameters
 * const { data } = useNarrativeFrames({
 *   frame_type: 'conflict',
 *   min_confidence: 0.7,
 *   limit: 50,
 *   category: 'political',
 *   include_examples: true
 * });
 * ```
 */
export function useNarrativeFrames(
  params?: NarrativeFramesParams,
  enabled: boolean = true
) {
  return useQuery<NarrativeFramesResponse, Error>({
    queryKey: ['narrative', 'frames', params],
    queryFn: async () => {
      const response = await mcpClient.callTool<NarrativeFramesResponse>(
        'get_narrative_frames',
        {
          frame_type: params?.frame_type,
          min_confidence: params?.min_confidence ?? 0.5,
          limit: params?.limit ?? 100,
          category: params?.category ?? 'all',
          include_examples: params?.include_examples ?? false,
          language: params?.language ?? 'en',
          date_from: params?.date_from,
          date_to: params?.date_to,
        }
      );

      return response;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes - frames don't change often
    gcTime: 30 * 60 * 1000, // 30 minutes cache
  });
}

/**
 * Get a single frame by ID from the frames list
 */
export function useNarrativeFrame(frameId: string, enabled: boolean = true) {
  const framesQuery = useNarrativeFrames(undefined, enabled);

  const frame = framesQuery.data?.frames.find((f) => f.id === frameId);

  return {
    ...framesQuery,
    data: frame,
  };
}

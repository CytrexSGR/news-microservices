import { useMutation } from '@tanstack/react-query';
import {
  intelligenceEndpoints,
  type EventDetectRequest,
  type EventDetectResponse,
} from './intelligenceApi';

/**
 * Hook for detecting events from text content
 *
 * Uses mutation pattern since event detection is a POST endpoint
 * that analyzes provided content.
 *
 * @example
 * ```tsx
 * const { mutate, data, isPending, error } = useEventDetection();
 *
 * // Detect event from article content
 * mutate({
 *   text: 'Breaking news: Major political developments in...',
 *   include_keywords: true,
 *   max_keywords: 10
 * });
 *
 * // Access detection results
 * if (data) {
 *   console.log('Entity count:', data.entity_count);
 *   console.log('Entities:', data.entities);
 *   console.log('Keywords:', data.keywords);
 *   console.log('Processing time:', data.processing_time_ms, 'ms');
 * }
 * ```
 */
export function useEventDetection() {
  return useMutation<EventDetectResponse, Error, EventDetectRequest>({
    mutationFn: (data) => intelligenceEndpoints.detectEvents(data),
  });
}

/**
 * Convenience type for event detection input
 */
export type { EventDetectRequest, EventDetectResponse };

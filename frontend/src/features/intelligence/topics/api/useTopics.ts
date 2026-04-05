// frontend/src/features/intelligence/topics/api/useTopics.ts

/**
 * React Query hooks for Topic Browser
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTopics,
  searchTopics,
  getTopicById,
  getBatches,
  submitTopicFeedback,
} from './topicApi';
import type {
  TopicListParams,
  TopicSearchParams,
  TopicFeedbackRequest,
} from '../types';

// =============================================================================
// Query Keys
// =============================================================================

export const topicKeys = {
  all: ['topics'] as const,
  lists: () => [...topicKeys.all, 'list'] as const,
  list: (params: TopicListParams) => [...topicKeys.lists(), params] as const,
  search: (params: TopicSearchParams) => [...topicKeys.all, 'search', params] as const,
  details: () => [...topicKeys.all, 'detail'] as const,
  detail: (id: number) => [...topicKeys.details(), id] as const,
  batches: () => [...topicKeys.all, 'batches'] as const,
};

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Fetch paginated topic list
 */
export function useTopics(params: TopicListParams = {}) {
  return useQuery({
    queryKey: topicKeys.list(params),
    queryFn: () => getTopics(params),
    staleTime: 60_000, // 1 minute
  });
}

/**
 * Search topics by keyword
 */
export function useTopicSearch(params: TopicSearchParams, enabled: boolean = true) {
  return useQuery({
    queryKey: topicKeys.search(params),
    queryFn: () => searchTopics(params),
    enabled: enabled && params.q.length > 0,
    staleTime: 60_000,
  });
}

/**
 * Fetch single topic with articles
 */
export function useTopic(id: number, enabled: boolean = true) {
  return useQuery({
    queryKey: topicKeys.detail(id),
    queryFn: () => getTopicById(id),
    enabled,
    staleTime: 60_000,
  });
}

/**
 * Fetch batch list
 */
export function useBatches(status?: string) {
  return useQuery({
    queryKey: topicKeys.batches(),
    queryFn: () => getBatches(status),
    staleTime: 60_000,
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Submit topic label feedback
 */
export function useSubmitFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clusterId, feedback }: { clusterId: number; feedback: TopicFeedbackRequest }) =>
      submitTopicFeedback(clusterId, feedback),
    onSuccess: (_, { clusterId }) => {
      // Invalidate the specific topic and list
      queryClient.invalidateQueries({ queryKey: topicKeys.detail(clusterId) });
      queryClient.invalidateQueries({ queryKey: topicKeys.lists() });
    },
  });
}

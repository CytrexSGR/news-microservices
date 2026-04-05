// frontend/src/features/intelligence/topics/api/topicApi.ts

/**
 * Topic Browser API Client
 * Connects to clustering-service Topics API (Port 8122)
 */

import { createApiClient } from '@/shared/api';
import type {
  TopicDetail,
  TopicListResponse,
  TopicListParams,
  TopicSearchResponse,
  TopicSearchParams,
  BatchListResponse,
  FeedbackResponse,
  TopicFeedbackRequest,
} from '../types';

// =============================================================================
// Configuration
// =============================================================================

const getBaseUrl = () => {
  if (import.meta.env.VITE_TOPICS_API_URL) {
    return import.meta.env.VITE_TOPICS_API_URL;
  }
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${hostname}:8122/api/v1`;
};

const TOPICS_BASE_URL = getBaseUrl();

export const topicApi = createApiClient(TOPICS_BASE_URL);

// =============================================================================
// API Functions
// =============================================================================

/**
 * List topic clusters with pagination
 */
export async function getTopics(params: TopicListParams = {}): Promise<TopicListResponse> {
  const { min_size = 10, limit = 50, offset = 0, batch_id } = params;
  const queryParams = new URLSearchParams();
  queryParams.append('min_size', String(min_size));
  queryParams.append('limit', String(limit));
  queryParams.append('offset', String(offset));
  if (batch_id) {
    queryParams.append('batch_id', batch_id);
  }

  const response = await topicApi.get<TopicListResponse>(`/topics?${queryParams}`);
  return response.data;
}

/**
 * Search topics by semantic similarity or keyword matching
 *
 * @param params.mode - 'semantic' (default): uses OpenAI embeddings for mathematical similarity
 *                     'keyword': falls back to SQL LIKE matching
 * @param params.min_similarity - Minimum similarity threshold for semantic mode (0-1, default: 0.3)
 */
export async function searchTopics(params: TopicSearchParams): Promise<TopicSearchResponse> {
  const { q, mode = 'semantic', limit = 20, min_similarity = 0.3 } = params;
  const queryParams = new URLSearchParams();
  queryParams.append('q', q);
  queryParams.append('mode', mode);
  queryParams.append('limit', String(limit));
  if (mode === 'semantic') {
    queryParams.append('min_similarity', String(min_similarity));
  }

  const response = await topicApi.get<TopicSearchResponse>(`/topics/search?${queryParams}`);
  return response.data;
}

/**
 * Get topic details with sample articles
 */
export async function getTopicById(id: number, sampleLimit: number = 20): Promise<TopicDetail> {
  const response = await topicApi.get<TopicDetail>(`/topics/${id}?sample_limit=${sampleLimit}`);
  return response.data;
}

/**
 * List batch clustering runs
 */
export async function getBatches(status?: string): Promise<BatchListResponse> {
  const queryParams = status ? `?status=${status}` : '';
  const response = await topicApi.get<BatchListResponse>(`/topics/batches${queryParams}`);
  return response.data;
}

/**
 * Submit feedback to correct topic label
 */
export async function submitTopicFeedback(
  clusterId: number,
  feedback: TopicFeedbackRequest
): Promise<FeedbackResponse> {
  const response = await topicApi.post<FeedbackResponse>(`/topics/${clusterId}/feedback`, feedback);
  return response.data;
}

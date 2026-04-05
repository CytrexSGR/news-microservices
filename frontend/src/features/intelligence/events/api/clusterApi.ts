// frontend/src/features/intelligence/events/api/clusterApi.ts

/**
 * Cluster API Client
 * Connects to clustering-service Clusters API (Port 8122)
 */

import { createApiClient } from '@/shared/api';

// =============================================================================
// Types from Backend
// =============================================================================

export type EntityRef = {
  id: string;
  name: string;
  type: string;
};

export type ClusterDetailBackend = {
  id: string;
  title: string;
  article_count: number;
  status: string;
  tension_score: number | null;
  is_breaking: boolean;
  first_seen_at: string;
  last_updated_at: string;
  summary: string | null;
  centroid_vector: number[] | null;
  primary_entities: EntityRef[] | null;
  burst_detected_at: string | null;
}

export type ClusterSummary = {
  id: string;
  title: string;
  article_count: number;
  status: string;
  tension_score: number | null;
  is_breaking: boolean;
  first_seen_at: string;
  last_updated_at: string;
};

export type ClusterListResponse = {
  clusters: ClusterSummary[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

// =============================================================================
// Configuration
// =============================================================================

const getBaseUrl = () => {
  if (import.meta.env.VITE_CLUSTERING_API_URL) {
    return import.meta.env.VITE_CLUSTERING_API_URL;
  }
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${hostname}:8122/api/v1`;
};

const CLUSTERS_BASE_URL = getBaseUrl();

export const clusterApi = createApiClient(CLUSTERS_BASE_URL);

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get cluster details by ID
 */
export async function getClusterById(clusterId: string): Promise<ClusterDetailBackend> {
  const response = await clusterApi.get<ClusterDetailBackend>(`/clusters/${clusterId}`);
  return response.data;
}

/**
 * List clusters with pagination
 */
export async function getClusters(params: {
  status?: 'active' | 'archived' | 'all';
  min_articles?: number;
  hours?: number;
  limit?: number;
  offset?: number;
} = {}): Promise<ClusterListResponse> {
  const { status = 'active', min_articles = 2, hours = 24, limit = 50, offset = 0 } = params;
  const queryParams = new URLSearchParams();
  queryParams.append('status', status);
  queryParams.append('min_articles', String(min_articles));
  queryParams.append('hours', String(hours));
  queryParams.append('limit', String(limit));
  queryParams.append('offset', String(offset));

  const response = await clusterApi.get<ClusterListResponse>(`/clusters?${queryParams}`);
  return response.data;
}

// =============================================================================
// Cluster Articles Types
// =============================================================================

export type ClusterArticle = {
  id: string;
  title: string;
  url: string | null;
  published_at: string | null;
  source_name: string | null;
  joined_at: string | null;
  similarity_score: number | null;
};

export type PaginationMeta = {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
};

export type ClusterArticlesResponse = {
  cluster_id: string;
  articles: ClusterArticle[];
  pagination: PaginationMeta;
};

/**
 * Get articles belonging to a cluster
 */
export async function getClusterArticles(
  clusterId: string,
  params: { limit?: number; offset?: number } = {}
): Promise<ClusterArticlesResponse> {
  const { limit = 20, offset = 0 } = params;
  const queryParams = new URLSearchParams();
  queryParams.append('limit', String(limit));
  queryParams.append('offset', String(offset));

  const response = await clusterApi.get<ClusterArticlesResponse>(
    `/clusters/${clusterId}/articles?${queryParams}`
  );
  return response.data;
}

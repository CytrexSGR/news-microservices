/**
 * Search Service API Client
 *
 * Provides functions to interact with the Search Service API
 * All endpoints are prefixed with /api/v1/admin
 */

import { searchApi } from './axios';
import type {
  IndexStatistics,
  QueryStatistics,
  CacheStatistics,
  CeleryStatistics,
  PerformanceStatistics,
  ReindexResponse,
  SyncResponse,
} from '@/types/search';

/**
 * Get index statistics
 * Endpoint: GET /api/v1/admin/stats/index
 */
export const getIndexStats = async (): Promise<IndexStatistics> => {
  const { data } = await searchApi.get<IndexStatistics>('/api/v1/admin/stats/index');
  return data;
};

/**
 * Get query statistics
 * Endpoint: GET /api/v1/admin/stats/queries
 *
 * @param limit - Number of top queries to return (default: 20)
 */
export const getQueryStats = async (limit = 20): Promise<QueryStatistics> => {
  const { data } = await searchApi.get<QueryStatistics>('/api/v1/admin/stats/queries', {
    params: { limit },
  });
  return data;
};

/**
 * Get cache statistics
 * Endpoint: GET /api/v1/admin/stats/cache
 */
export const getCacheStats = async (): Promise<CacheStatistics> => {
  const { data } = await searchApi.get<CacheStatistics>('/api/v1/admin/stats/cache');
  return data;
};

/**
 * Get Celery worker statistics
 * Endpoint: GET /api/v1/admin/stats/celery
 */
export const getCeleryStats = async (): Promise<CeleryStatistics> => {
  const { data } = await searchApi.get<CeleryStatistics>('/api/v1/admin/stats/celery');
  return data;
};

/**
 * Get performance statistics
 * Endpoint: GET /api/v1/admin/stats/performance
 */
export const getPerformanceStats = async (): Promise<PerformanceStatistics> => {
  const { data } = await searchApi.get<PerformanceStatistics>('/api/v1/admin/stats/performance');
  return data;
};

/**
 * Trigger full reindex of all articles
 * Endpoint: POST /api/v1/admin/reindex
 *
 * Requires authentication. This will:
 * 1. Delete all existing article indexes
 * 2. Fetch all articles from Feed Service
 * 3. Fetch sentiment/entity data from Content Analysis Service
 * 4. Create full-text search indexes
 */
export const reindexArticles = async (): Promise<ReindexResponse> => {
  const { data } = await searchApi.post<ReindexResponse>('/api/v1/admin/reindex');
  return data;
};

/**
 * Sync new articles from Feed Service
 * Endpoint: POST /api/v1/admin/sync
 *
 * @param batchSize - Number of articles to fetch per batch (default: 100)
 */
export const syncArticles = async (batchSize = 100): Promise<SyncResponse> => {
  const { data } = await searchApi.post<SyncResponse>('/api/v1/admin/sync', null, {
    params: { batch_size: batchSize },
  });
  return data;
};

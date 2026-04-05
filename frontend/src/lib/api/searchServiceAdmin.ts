/**
 * API client for Search Service Admin Dashboard
 * Uses JWT authentication via searchApi from @/api/axios
 */

import { searchApi } from '@/api/axios'
import type {
  IndexStatistics,
  CacheStatistics,
  CeleryStatistics,
  QueryStatistics,
  PerformanceStatistics,
} from '@/types/searchServiceAdmin'

// ===========================
// Admin Statistics Endpoints
// ===========================

export const getIndexStats = async (): Promise<IndexStatistics> => {
  const { data } = await searchApi.get<IndexStatistics>('/admin/stats/index')
  return data
}

export const getCacheStats = async (): Promise<CacheStatistics> => {
  const { data } = await searchApi.get<CacheStatistics>('/admin/stats/cache')
  return data
}

export const getCeleryStats = async (): Promise<CeleryStatistics> => {
  const { data } = await searchApi.get<CeleryStatistics>('/admin/stats/celery')
  return data
}

export const getQueryStats = async (): Promise<QueryStatistics> => {
  const { data } = await searchApi.get<QueryStatistics>('/admin/stats/queries')
  return data
}

export const getPerformanceStats = async (): Promise<PerformanceStatistics> => {
  const { data } = await searchApi.get<PerformanceStatistics>('/admin/stats/performance')
  return data
}

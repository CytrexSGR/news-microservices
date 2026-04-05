/**
 * API client for Entity Canonicalization Service
 */

import axios from 'axios'
import type {
  CanonicalizationStats,
  ReprocessingStatus,
  EntityTypeTrendsResponse
} from '@/types/knowledgeGraph'

// Entity Canonicalization Service URL (from docker-compose.yml)
const BASE_URL = import.meta.env.VITE_CANONICALIZATION_API_URL || 'http://localhost:8112'

// Create axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ===========================
// Canonicalization Statistics
// ===========================

export const getCanonicalizationStats = async (): Promise<CanonicalizationStats> => {
  const { data } = await apiClient.get<CanonicalizationStats>(
    '/api/v1/canonicalization/stats/detailed'
  )
  return data
}

// ===========================
// Health Check
// ===========================

export const getCanonicalizationHealth = async (): Promise<{ status: string; service: string }> => {
  const { data } = await apiClient.get('/api/v1/canonicalization/health')
  return data
}

// ===========================
// Batch Reprocessing
// ===========================

export const startBatchReprocessing = async (dryRun: boolean = false): Promise<{ job_id: string }> => {
  const { data } = await apiClient.post('/api/v1/canonicalization/reprocess/start', {
    dry_run: dryRun,
  })
  return data
}

export const getReprocessingStatus = async (): Promise<ReprocessingStatus> => {
  const { data } = await apiClient.get<ReprocessingStatus>('/api/v1/canonicalization/reprocess/status')
  return data
}

export const stopBatchReprocessing = async (): Promise<{ message: string }> => {
  const { data } = await apiClient.post('/api/v1/canonicalization/reprocess/stop')
  return data
}

// ===========================
// Entity Type Trends
// ===========================

export const getEntityTypeTrends = async (days: number = 30): Promise<EntityTypeTrendsResponse> => {
  const { data } = await apiClient.get<EntityTypeTrendsResponse>(
    `/api/v1/canonicalization/trends/entity-types?days=${days}`
  )
  return data
}

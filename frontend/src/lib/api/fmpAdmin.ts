/**
 * FMP Service Admin API Client
 */

import axios from 'axios'

const FMP_API_URL = import.meta.env.VITE_FMP_API_URL || 'http://localhost:8113/api/v1'

const api = axios.create({
  baseURL: `${FMP_API_URL}/admin`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ==================== Scheduler APIs ====================

export const getSchedulerStatus = () =>
  api.get('/scheduler/status')

export const pauseScheduler = () =>
  api.post('/scheduler/pause')

export const resumeScheduler = () =>
  api.post('/scheduler/resume')

export const pauseJob = (jobId: string) =>
  api.post(`/scheduler/jobs/${jobId}/pause`)

export const resumeJob = (jobId: string) =>
  api.post(`/scheduler/jobs/${jobId}/resume`)

// ==================== Statistics APIs ====================

export const getDatabaseStats = () =>
  api.get('/stats/database')

export const getAPIUsage = (days: number = 7) =>
  api.get('/stats/api-usage', { params: { days } })

export const getJobPerformance = () =>
  api.get('/stats/job-performance')

export const getDataQuality = () =>
  api.get('/stats/data-quality')

export const getDataGrowth = (days: number = 30) =>
  api.get('/stats/data-growth', { params: { days } })

// ==================== Management APIs ====================

export interface HistoricalSyncParams {
  asset_type: 'indices' | 'forex' | 'commodities' | 'crypto'
  symbol: string
  from_date: string  // YYYY-MM-DD
  to_date: string    // YYYY-MM-DD
}

export const syncHistoricalData = (params: HistoricalSyncParams) =>
  api.post('/sync/historical', params)

export const clearCache = () =>
  api.delete('/cache')

export const getCacheStats = () =>
  api.get('/cache/stats')

// ==================== Service Health API ====================

export const getServiceHealth = () =>
  api.get('/health')

// ==================== Rate Limit Monitoring ====================

export const getRateLimitStats = () =>
  api.get('/rate-limit/stats')

// ==================== Market Sync APIs ====================

export const triggerMarketSync = () =>
  api.post('/trigger-market-sync')

/**
 * TypeScript types for FMP Service Admin
 */

export interface JobExecutionInfo {
  time: string
  success: boolean
  error?: string
}

export interface SchedulerJob {
  id: string
  name: string
  status: 'running' | 'paused'
  next_run: string | null
  trigger: string
  last_execution?: JobExecutionInfo
  success_rate: number
  avg_duration: number
  total_executions: number
  total_failures: number
}

export interface SchedulerStatus {
  running: boolean
  paused: boolean
  jobs: SchedulerJob[]
  total_jobs: number
}

export interface TableStats {
  table: string
  rows: number
  last_update: string | null
  error?: string
}

export interface DatabaseStats {
  tables: TableStats[]
  total_rows: number
  last_sync: string
}

export interface APICallBreakdown {
  indices: number
  forex: number
  commodities: number
  crypto: number
  news: number
  earnings: number
  macro: number
  backfill: number
}

export interface DailyAPIUsage {
  date: string
  calls: number
  breakdown: APICallBreakdown
}

export interface APIUsageStats {
  limit: number
  today_estimate: number
  remaining_estimate: number
  history: DailyAPIUsage[]
  note?: string
}

export interface DataQualityCheck {
  check: string
  status: 'ok' | 'warning' | 'error'
  count?: number
  expected?: number
  actual?: number
  percentage?: string
  error?: string
}

export interface DataQualityMetrics {
  duplicates_found: number
  missing_data_count: number
  failed_syncs_24h: number
  completeness_score: number
  checks: DataQualityCheck[]
}

export interface DailyGrowthStats {
  date: string
  quotes: number
  news: number
  historical: number
  forex: number
  commodities: number
  crypto: number
  total: number
}

export interface DataGrowthStats {
  days: number
  data: DailyGrowthStats[]
}

export interface JobPerformance {
  job_id: string
  job_name: string
  total_executions: number
  total_failures: number
  success_rate: number
  avg_duration: number
  last_execution?: JobExecutionInfo
}

export interface JobPerformanceStats {
  jobs: JobPerformance[]
  overall_success_rate: number
}

export interface ServiceHealth {
  status: 'healthy' | 'unhealthy'
  database_connected: boolean
  fmp_api_reachable: boolean
  scheduler_running: boolean
  last_check: string
  uptime_seconds?: number
}

export interface CacheStats {
  size_mb: number
  entries: number
  hit_rate: number
  last_cleared: string | null
}

export interface RateLimitStats {
  current_calls: number
  limit: number
  window_seconds: number
  remaining: number
  percentage: number
  status: 'ok' | 'warning' | 'critical'
}

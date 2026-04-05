/**
 * TypeScript types for Search Service Admin Dashboard
 * Backend API: http://localhost:8106/api/v1/admin
 */

// ===========================
// Index Statistics Types
// ===========================

export interface IndexBySource {
  source: string
  count: number
}

export interface IndexBySentiment {
  sentiment: string
  count: number
}

export interface IndexStatistics {
  total_indexed: number
  by_source: IndexBySource[]
  by_sentiment: IndexBySentiment[]
  recent_24h: number
  index_size: string
}

// ===========================
// Cache Statistics Types
// ===========================

export interface CacheStatistics {
  total_keys: number
  memory_used: string
  hit_rate_percent: number
  total_hits: number
  total_misses: number
  evicted_keys: number
  expired_keys: number
}

// ===========================
// Celery Statistics Types
// ===========================

export interface WorkerStats {
  worker: string
  pool: number
  total_tasks: Record<string, unknown>
}

export interface CeleryStatistics {
  active_workers: number
  registered_tasks: number
  reserved_tasks: number
  worker_stats: WorkerStats[]
  status: string
}

// ===========================
// Query Statistics Types
// ===========================

export interface TopQuery {
  query: string
  hits: number
}

export interface QueryStatistics {
  top_queries: TopQuery[]
  total_searches: number
  recent_24h: number
  avg_results_per_query: number
}

// ===========================
// Performance Statistics Types
// ===========================

export interface SlowestQuery {
  query: string
  hits: number
}

export interface ResultDistribution {
  range: string
  count: number
}

export interface PerformanceStatistics {
  avg_execution_time_ms: number
  slowest_queries: SlowestQuery[]
  result_distribution: ResultDistribution[]
}

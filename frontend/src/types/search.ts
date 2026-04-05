/**
 * Type definitions for Search Service API
 */

/**
 * Index Statistics Response
 */
export interface IndexStatistics {
  total_indexed: number;
  by_source: SourceStats[];
  by_sentiment: SentimentStats[];
  recent_24h: number;
  index_size: string;
  last_updated: string;
}

export interface SourceStats {
  source: string;
  count: number;
}

export interface SentimentStats {
  sentiment: string;
  count: number;
}

/**
 * Query Statistics Response
 */
export interface QueryStatistics {
  top_queries: TopQuery[];
  total_searches: number;
  recent_24h: number;
  avg_results_per_query: number;
  last_updated: string;
}

export interface TopQuery {
  query: string;
  hits: number;
}

/**
 * Cache Statistics Response
 */
export interface CacheStatistics {
  total_keys: number;
  memory_used: string;
  memory_peak: string;
  hit_rate_percent: number;
  total_hits: number;
  total_misses: number;
  evicted_keys: number;
  expired_keys: number;
  last_updated: string;
}

/**
 * Celery Worker Statistics Response
 */
export interface CeleryStatistics {
  active_workers: number;
  registered_tasks: number;
  reserved_tasks: number;
  worker_stats: WorkerStats[];
  status: 'healthy' | 'no_workers';
  last_updated: string;
}

export interface WorkerStats {
  worker: string;
  pool: number;
  total_tasks: Record<string, unknown>;
}

/**
 * Performance Statistics Response
 */
export interface PerformanceStatistics {
  avg_execution_time_ms: number;
  slowest_queries: SlowQuery[];
  result_distribution: ResultDistribution[];
  last_updated: string;
}

export interface SlowQuery {
  query: string;
  hits: number;
}

export interface ResultDistribution {
  range: string;
  count: number;
}

/**
 * Reindex Response
 */
export interface ReindexResponse {
  status: 'success' | 'error';
  message: string;
  stats: ReindexStats;
}

export interface ReindexStats {
  total_indexed?: number;
  errors?: number;
  duration_seconds?: number;
}

/**
 * Sync Response
 */
export interface SyncResponse {
  status: 'success' | 'error';
  message: string;
  stats: SyncStats;
}

export interface SyncStats {
  new_articles?: number;
  updated_articles?: number;
  errors?: number;
}

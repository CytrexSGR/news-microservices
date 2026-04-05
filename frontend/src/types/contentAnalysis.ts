/**
 * TypeScript types for Content Analysis Admin Dashboard
 */

// ===========================
// Enums (as const objects for erasableSyntaxOnly compatibility)
// ===========================

export const ServiceStatus = {
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  UNHEALTHY: 'unhealthy',
  UNKNOWN: 'unknown',
} as const

export type ServiceStatus = (typeof ServiceStatus)[keyof typeof ServiceStatus]

export const ConsumerStatus = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  ERROR: 'error',
  UNKNOWN: 'unknown',
} as const

export type ConsumerStatus = (typeof ConsumerStatus)[keyof typeof ConsumerStatus]

export const AnalysisStatus = {
  COMPLETED: 'completed',
  FAILED: 'failed',
  PENDING: 'pending',
  PROCESSING: 'processing',
} as const

export type AnalysisStatus = (typeof AnalysisStatus)[keyof typeof AnalysisStatus]

// ===========================
// Live Operations Types
// ===========================

export interface DependencyHealth {
  name: string
  status: ServiceStatus
  message?: string
  response_time_ms?: number
}

export interface RabbitMQMetrics {
  consumer_status: ConsumerStatus
  queue_depth: number
  messages_per_second: number
  dead_letter_queue_count: number
  total_processed: number
  total_failed: number
}

export interface PerformanceMetrics {
  in_flight_analyses: number
  average_latency_seconds: number
  requests_per_minute: number
  error_rate_percent: number
}

export interface CostMetrics {
  daily_cost_usd: number
  max_daily_cost_usd: number
  cost_percentage: number
  is_near_limit: boolean
}

export interface CacheMetrics {
  hit_rate_percent: number
  total_hits: number
  total_misses: number
  total_requests: number
  cache_size_mb?: number
}

export interface OperationsStatus {
  timestamp: string
  dependencies: DependencyHealth[]
  rabbitmq: RabbitMQMetrics
  performance: PerformanceMetrics
  cost: CostMetrics
  cache: CacheMetrics
}

// ===========================
// Analysis Explorer Types
// ===========================

export interface AnalysisActivityItem {
  id: string
  timestamp: string
  article_id: string
  article_title: string
  status: AnalysisStatus
  sentiment?: string
  cost_usd?: number
  duration_seconds?: number
  error_message?: string
}

export interface RecentActivityResponse {
  activities: AnalysisActivityItem[]
  total_count: number
  failed_count: number
  success_count: number
}

export interface OSINTEvent {
  event_id: string
  article_id: string
  article_title: string
  event_type: string
  severity: string
  created_at: string
}

export interface OSINTReviewSummary {
  queue_count: number
  recent_events: OSINTEvent[]
  high_severity_count: number
  medium_severity_count: number
  low_severity_count: number
}

// ===========================
// Configuration Types
// ===========================

export interface ProviderConfig {
  provider: 'openai' | 'anthropic' | 'ollama' | 'gemini'
  model: string
  temperature?: number
  max_tokens?: number
}

export interface AnalysisOverride {
  analysis_type: string
  provider: 'openai' | 'anthropic' | 'ollama' | 'gemini'
  model: string
}

export interface ModelConfiguration {
  default_provider: string
  default_models: Record<string, string>
  analysis_specific_overrides: Record<string, { provider: string; model: string }>
  available_models?: Record<string, string[]>
}

export interface UpdateModelConfigRequest {
  default_provider?: string
  default_models?: Record<string, string>
  analysis_specific_overrides?: Record<string, { provider: string; model: string }>
}

export interface ServiceControlsConfig {
  max_daily_cost_usd: number
  rate_limit_requests_per_minute: number
  cache_enabled: boolean
  consumer_enabled: boolean
}

export interface UpdateServiceControlsRequest {
  max_daily_cost_usd?: number
  rate_limit_requests_per_minute?: number
  cache_enabled?: boolean
  consumer_enabled?: boolean
}

// ===========================
// Action Response Types
// ===========================

export interface FlushCacheResponse {
  success: boolean
  keys_flushed: number
  message: string
  timestamp: string
}

export interface ConfigUpdateResponse {
  success: boolean
  message: string
  updated_fields: string[]
  timestamp: string
}

/**
 * Scraping Service Types
 *
 * TypeScript type definitions for the Scraping Service MCP tools.
 * Based on: mcp-orchestration-server scraping tools (55 tools)
 */

// ============================================
// Health & Monitoring Types
// ============================================

export interface ScrapingHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  browser: boolean;
  redis: boolean;
  components: {
    cache: boolean;
    queue: boolean;
    dlq: boolean;
    proxy_pool: boolean;
  };
  last_check: string;
}

export interface ScrapingMetrics {
  concurrency: {
    max: number;
    current: number;
    available: number;
  };
  retry_stats: {
    total_retries: number;
    success_rate: number;
    avg_retries_per_success: number;
  };
  browser_status: {
    instances: number;
    healthy: number;
    memory_mb: number;
  };
  throughput: {
    requests_per_minute: number;
    bytes_per_minute: number;
  };
}

export interface ActiveJob {
  job_id: string;
  url: string;
  domain: string;
  method: ScrapingMethod;
  started_at: string;
  duration_seconds: number;
  retries: number;
}

export interface RateLimitInfo {
  key: string;
  domain: string;
  requests_made: number;
  requests_limit: number;
  reset_at: string;
  is_limited: boolean;
}

export interface FeedFailure {
  feed_id: number;
  feed_url: string;
  failure_count: number;
  last_failure_at: string;
  last_error: string;
  consecutive_failures: number;
}

// ============================================
// Source Profile Types
// ============================================

export type SourceStatus = 'working' | 'degraded' | 'blocked' | 'unknown';
export type ScrapingMethod = 'httpx' | 'playwright' | 'newspaper4k' | 'trafilatura' | 'auto';

export interface SourceProfile {
  domain: string;
  status: SourceStatus;
  scraping_method: ScrapingMethod;
  success_rate: number;
  avg_response_time_ms: number;
  last_checked: string;
  last_success?: string;
  failure_count: number;
  requires_js: boolean;
  requires_proxy: boolean;
  rate_limit_rpm?: number;
  custom_selectors?: {
    title?: string;
    content?: string;
    author?: string;
    date?: string;
  };
  notes?: string;
}

export interface SourcesListParams {
  status?: SourceStatus;
  limit?: number;
  offset?: number;
}

export interface SourcesListResponse {
  sources: SourceProfile[];
  total: number;
  limit: number;
  offset: number;
}

export interface SourcesStats {
  total: number;
  by_status: Record<SourceStatus, number>;
  by_method: Record<ScrapingMethod, number>;
  avg_success_rate: number;
  recently_checked: number;
}

export interface SourceConfig {
  url: string;
  domain: string;
  recommended_method: ScrapingMethod;
  requires_js: boolean;
  requires_proxy: boolean;
  rate_limit_rpm: number;
  selectors: {
    title?: string;
    content?: string;
    author?: string;
    date?: string;
  };
  headers?: Record<string, string>;
}

// ============================================
// Dead Letter Queue (DLQ) Types
// ============================================

export type DLQStatus = 'pending' | 'resolved' | 'abandoned' | 'manual';
export type DLQFailureReason =
  | 'timeout'
  | 'rate_limited'
  | 'blocked'
  | 'paywall'
  | 'parse_error'
  | 'network_error'
  | 'captcha'
  | 'unknown';

export interface DLQEntry {
  id: number;
  url: string;
  domain: string;
  status: DLQStatus;
  failure_reason: DLQFailureReason;
  retry_count: number;
  first_failed_at: string;
  last_failed_at: string;
  resolved_at?: string;
  resolver_notes?: string;
  error_details?: string;
}

export interface DLQStats {
  total: number;
  by_status: Record<DLQStatus, number>;
  by_reason: Record<DLQFailureReason, number>;
  by_domain: Array<{ domain: string; count: number }>;
  pending_retry_count: number;
}

export interface DLQListParams {
  status?: DLQStatus;
  domain?: string;
  failure_reason?: DLQFailureReason;
  limit?: number;
  offset?: number;
}

export interface DLQListResponse {
  entries: DLQEntry[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================
// Cache Types
// ============================================

export interface CacheStats {
  total_entries: number;
  total_size_bytes: number;
  total_size_human: string;
  hit_rate: number;
  miss_rate: number;
  avg_age_seconds: number;
  expired_entries: number;
  by_domain: Array<{ domain: string; entries: number; size_bytes: number }>;
}

export interface CacheInvalidateParams {
  url?: string;
  domain?: string;
  older_than_hours?: number;
}

export interface CacheActionResponse {
  success: boolean;
  entries_affected: number;
  message: string;
}

// ============================================
// Proxy Pool Types
// ============================================

export type ProxyType = 'http' | 'https' | 'socks5';
export type ProxyStatus = 'healthy' | 'unhealthy' | 'unknown';

export interface ProxyInfo {
  proxy_id: string;
  host: string;
  port: number;
  type: ProxyType;
  status: ProxyStatus;
  success_rate: number;
  avg_response_time_ms: number;
  last_checked: string;
  last_success?: string;
  failure_count: number;
  total_requests: number;
  auth_required: boolean;
}

export interface ProxyStats {
  total: number;
  healthy: number;
  unhealthy: number;
  avg_response_time_ms: number;
  overall_success_rate: number;
  by_type: Record<ProxyType, number>;
}

export interface AddProxyParams {
  host: string;
  port: number;
  type: ProxyType;
  username?: string;
  password?: string;
}

export interface ProxyActionResponse {
  success: boolean;
  proxy_id?: string;
  message: string;
}

// ============================================
// Priority Queue Types
// ============================================

export type QueuePriority = 'LOW' | 'NORMAL' | 'HIGH' | 'CRITICAL';
export type QueueJobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface QueueStats {
  pending_jobs: number;
  processing_jobs: number;
  completed_last_hour: number;
  failed_last_hour: number;
  avg_wait_time_seconds: number;
  avg_processing_time_seconds: number;
  throughput_per_minute: number;
  priority_distribution: Record<QueuePriority, number>;
}

export interface EnqueueJobParams {
  url: string;
  priority?: QueuePriority;
  method?: ScrapingMethod;
  max_retries?: number;
  delay_seconds?: number;
  callback_url?: string;
  metadata?: Record<string, unknown>;
}

export interface QueueJob {
  job_id: string;
  url: string;
  domain: string;
  priority: QueuePriority;
  status: QueueJobStatus;
  method: ScrapingMethod;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  retries: number;
  max_retries: number;
  result?: {
    success: boolean;
    content_length?: number;
    error?: string;
  };
}

export interface QueueJobStatusResponse {
  job: QueueJob;
  position_in_queue?: number;
  estimated_wait_seconds?: number;
}

export interface PendingJobsResponse {
  jobs: QueueJob[];
  total: number;
  limit: number;
}

// ============================================
// Wikipedia Types
// ============================================

export interface WikipediaSearchParams {
  query: string;
  language?: 'de' | 'en' | 'fr' | 'es' | 'it';
  limit?: number;
}

export interface WikipediaSearchResult {
  title: string;
  pageid: number;
  snippet: string;
  url: string;
}

export interface WikipediaSearchResponse {
  results: WikipediaSearchResult[];
  total: number;
  query: string;
}

export interface WikipediaArticleParams {
  title: string;
  language?: 'de' | 'en';
  include_infobox?: boolean;
  include_categories?: boolean;
  include_links?: boolean;
}

export interface WikipediaArticle {
  title: string;
  pageid: number;
  url: string;
  summary: string;
  content?: string;
  infobox?: Record<string, string | string[]>;
  categories?: string[];
  links?: string[];
  images?: string[];
  last_modified: string;
}

export interface WikipediaRelationship {
  entity: string;
  entity_type: 'person' | 'organization' | 'location' | 'event' | 'concept';
  relation_type: string;
  confidence: number;
  source_sentence?: string;
}

export interface WikipediaRelationshipsResponse {
  title: string;
  relationships: WikipediaRelationship[];
  total: number;
}

// ============================================
// Direct Scraping Types
// ============================================

export interface DirectScrapeParams {
  url: string;
  method?: ScrapingMethod;
  timeout_seconds?: number;
  use_proxy?: boolean;
  custom_headers?: Record<string, string>;
}

export interface DirectScrapeResult {
  success: boolean;
  url: string;
  domain: string;
  method_used: ScrapingMethod;
  title?: string;
  content?: string;
  author?: string;
  published_date?: string;
  content_length: number;
  scrape_time_ms: number;
  error?: string;
}

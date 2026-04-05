/**
 * TypeScript types for Feed Service Admin Dashboard
 * Based on /home/cytrex/userdocs/feed-service-frontend-konzept.md
 */

// ===========================
// Enums
// ===========================

export const FeedStatus = {
  ACTIVE: 'ACTIVE',
  PAUSED: 'PAUSED',
  ERROR: 'ERROR',
  INACTIVE: 'INACTIVE',
} as const

export type FeedStatus = (typeof FeedStatus)[keyof typeof FeedStatus]

export const ScrapeMethod = {
  NEWSPAPER4K: 'newspaper4k',
  PLAYWRIGHT: 'playwright',
} as const

export type ScrapeMethod = (typeof ScrapeMethod)[keyof typeof ScrapeMethod]

export const ScrapeStatus = {
  SUCCESS: 'success',
  PAYWALL: 'paywall',
  ERROR: 'error',
  TIMEOUT: 'timeout',
  PENDING: 'pending',
} as const

export type ScrapeStatus = (typeof ScrapeStatus)[keyof typeof ScrapeStatus]

export const AssessmentStatus = {
  PENDING: 'pending',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const

export type AssessmentStatus = (typeof AssessmentStatus)[keyof typeof AssessmentStatus]

// ===========================
// Service Health Types
// ===========================

export interface FeedServiceHealth {
  status: string
  service: string
  version: string
  environment: string
  scheduler?: {
    is_running: boolean
    check_interval_seconds: number
    fetcher_active: boolean
  }
  // Additional scheduler info (flattened structure used by UI components)
  scheduler_enabled?: boolean
  scheduler_status?: {
    active_jobs?: number
    next_scheduled_fetch?: string
    average_fetch_duration_seconds?: number
  }
}

// ===========================
// Feed Stats Types (Dashboard)
// ===========================

export interface FeedStats {
  active_feeds: number
  total_articles: number
  articles_today: number
  articles_by_day: Array<{
    date: string
    count: number
  }>
  top_sources: Array<{
    source: string
    count: number
  }>
}

// ===========================
// Feed Types
// ===========================

export interface FeedAssessmentData {
  assessment_status: AssessmentStatus
  assessment_date?: string
  credibility_tier?: string
  reputation_score?: number
  founded_year?: number
  organization_type?: string
  political_bias?: string
  editorial_standards?: Record<string, unknown>
  trust_ratings?: Record<string, unknown>
  recommendation?: Record<string, unknown>
  assessment_summary?: string
  quality_score?: number
}

export interface FeedResponse {
  id: string
  name: string
  url: string
  description?: string
  fetch_interval: number
  scrape_full_content: boolean
  scrape_method: ScrapeMethod
  scrape_failure_count: number
  scrape_failure_threshold: number
  scrape_last_failure_at?: string | null
  scrape_disabled_reason?: 'manual' | 'auto_threshold' | null
  is_active: boolean
  status: FeedStatus
  last_fetched_at?: string
  last_error_message?: string | null
  last_error_at?: string | null
  health_score: number
  consecutive_failures: number
  quality_score?: number
  admiralty_code?: AdmiraltyCode  // NATO Admiralty Code rating (A-F)
  total_items: number
  items_last_24h: number

  // Analysis enable flags
  enable_category_analysis: boolean
  enable_finance_sentiment: boolean
  enable_geopolitical_sentiment: boolean
  enable_bias: boolean
  enable_conflict: boolean
  enable_osint_analysis: boolean
  enable_summary: boolean
  enable_entity_extraction: boolean
  enable_topic_classification: boolean

  created_at: string
  updated_at: string
  categories: string[]
  category?: string  // Primary category (singular) - used by UI components
  assessment?: FeedAssessmentData

  // Legacy fields (optional)
  legacy_id?: number
  legacy_feed_id?: number
}

// ===========================
// Feed List & Filters
// ===========================

export interface FeedListFilters {
  skip?: number
  limit?: number
  is_active?: boolean
  status?: FeedStatus
  category?: string
  health_score_min?: number
  health_score_max?: number
}

export interface FeedListResponse {
  feeds: FeedResponse[]
  total: number
  skip: number
  limit: number
}

// ===========================
// Feed Health Types
// ===========================

export interface FeedHealthResponse {
  health_score: number
  consecutive_failures: number
  is_healthy: boolean
  avg_response_time_ms?: number
  success_rate: number
  uptime_24h: number
  uptime_7d: number
  uptime_30d: number
  last_success_at?: string
  last_failure_at?: string
}

// ===========================
// Feed Quality Types
// ===========================

export interface FeedQualityResponse {
  quality_score: number
  freshness_score: number
  consistency_score: number
  content_score: number
  reliability_score: number
  recommendations: string[]
  calculated_at: string
}

// ===========================
// Feed Item Types
// ===========================

export interface FeedItemResponse {
  id: string
  feed_id: string
  title: string
  link: string
  description?: string
  content?: string
  author?: string
  published_at?: string
  guid?: string
  content_hash: string
  scraped_at?: string
  scrape_status?: ScrapeStatus
  scrape_word_count?: number
  scraped_metadata?: Record<string, any>
  created_at: string

  // Analysis data (all optional)
  category_analysis?: Record<string, unknown>
  sentiment_analysis?: Record<string, unknown>
  finance_sentiment?: Record<string, unknown>
  geopolitical_sentiment?: Record<string, unknown>
  event_analysis?: Record<string, unknown>
  summaries?: Array<Record<string, unknown>>
  topics?: Array<Record<string, unknown>>

  // Legacy fields
  legacy_id?: number
  legacy_feed_id?: number
}

export interface FeedItemWithFeedResponse extends FeedItemResponse {
  feed_name: string
}

export interface FeedItemsResponse {
  items: FeedItemResponse[]
  total: number
  skip: number
  limit: number
}

export interface RecentItemsResponse {
  items: FeedItemWithFeedResponse[]
  total: number
}

// ===========================
// Assessment History Types
// ===========================

export interface AssessmentHistoryItem {
  id: number
  assessment_status: AssessmentStatus
  assessment_date?: string
  credibility_tier?: string
  reputation_score?: number
  founded_year?: number
  organization_type?: string
  political_bias?: string
  editorial_standards?: Record<string, unknown>
  trust_ratings?: Record<string, unknown>
  recommendation?: Record<string, unknown>
  assessment_summary?: string
}

export interface AssessmentHistoryResponse {
  history: AssessmentHistoryItem[]
  total: number
}

// ===========================
// Bulk Fetch Types
// ===========================

export interface BulkFetchRequest {
  feed_ids?: string[]
  force?: boolean
}

export interface BulkFetchResponse {
  total_feeds: number
  successful_fetches: number
  failed_fetches: number
  total_new_items: number
  details: Array<{
    feed_id: string
    feed_name: string
    status: string
  }>
}

// ===========================
// Action Response Types
// ===========================

export interface FetchTriggerResponse {
  success: boolean
  message: string
  feed_id: string
  auto_reset?: boolean  // Indicates if ERROR status was auto-reset
}

export interface AssessmentTriggerResponse {
  message: string
  feed_id: string
  status: AssessmentStatus
}

export interface ResetErrorResponse {
  success: boolean
  message: string
  feed_id: string
  current_status: string
  previous_error?: string  // Error message before reset
  error_duration_hours?: number  // How long feed was in ERROR state
}

// ===========================
// Category Management Types
// ===========================

export interface CategoryStats {
  category: string
  feed_count: number
  total_items: number
  items_last_24h: number
}

// ===========================
// Quality Distribution Types
// ===========================

export interface QualityDistribution {
  excellent: number  // 90-100
  good: number       // 70-89
  average: number    // 50-69
  poor: number       // 0-49
}

export interface HealthDistribution {
  healthy: number    // 80-100
  warning: number    // 50-79
  critical: number   // 0-49
}

// ===========================
// Feed Quality V2 Types
// ===========================

export interface AdmiraltyCode {
  code: string          // A-F
  label: string         // e.g., "Completely Reliable", "Fairly Reliable"
  color: string         // green, blue, yellow, orange, red, gray
}

export interface ArticleQualityScore {
  score: number         // 0-100
  weight: number        // 0.5 (50% weight)
  breakdown: {
    credibility: number
    objectivity: number
    verification: number
    relevance: number
    completeness: number
    consistency: number
  }
  distribution: {
    premium: number              // 90-100
    high_quality: number         // 75-89
    moderate_quality: number     // 60-74
    low_quality: number          // 40-59
    very_low_quality: number     // 0-39
  }
  distribution_bonus: number
  red_flags: Record<string, number>
  articles_analyzed: number
}

export interface SourceCredibilityScore {
  score: number         // 0-100
  weight: number        // 0.2 (20% weight)
  reputation_score: number
  credibility_tier: string
  tier_adjustment: number
  trend_adjustment: number
  editorial_bonus: number
}

export interface OperationalScore {
  score: number         // 0-100
  weight: number        // 0.2 (20% weight)
  success_rate: number
  uptime_7d: number
  uptime_30d: number
  consecutive_failures: number
  failure_penalty: number
}

export interface FreshnessConsistencyScore {
  score: number         // 0-100
  weight: number        // 0.1 (10% weight)
  freshness: number
  consistency: number
}

export interface ComponentScores {
  article_quality: ArticleQualityScore
  source_credibility: SourceCredibilityScore
  operational: OperationalScore
  freshness_consistency: FreshnessConsistencyScore
}

export interface QualityTrends {
  trend_label: string   // improving, stable, declining
  trend_value: number
  quality_7d_vs_30d: number
  score_7d?: number
  score_30d?: number
}

export interface QualityDataStats {
  articles_analyzed: number
  total_articles: number
  coverage_percentage: number
  date_range_days: number
}

export interface FeedQualityV2Response {
  feed_id: string
  feed_name: string
  quality_score: number
  admiralty_code: AdmiraltyCode
  confidence: string              // low, medium, high
  confidence_score: number        // 0-100
  trend: string                   // improving, stable, declining
  trend_direction: number
  component_scores: ComponentScores
  quality_distribution: {
    premium: number
    high_quality: number
    moderate_quality: number
    low_quality: number
    very_low_quality: number
  }
  red_flags: Record<string, number>
  trends: QualityTrends
  data_stats: QualityDataStats
  recommendations: string[]
  calculated_at: string
}

// ===========================
// Feed Quality V2 Overview Types
// ===========================

export interface FeedQualityOverview {
  feed_id: string
  feed_name: string
  quality_score: number | null      // Can be null if insufficient data
  admiralty_code: string | null     // A-F, null if insufficient data
  admiralty_label: string           // e.g., "Usually Reliable", "Error"
  admiralty_color: string           // green, blue, yellow, orange, red, gray
  confidence: string | null         // low, medium, high, null if insufficient data
  trend: string | null              // improving, stable, declining, null if insufficient data
  trend_direction: number | null    // Trend change value, null if insufficient data
  total_articles: number            // Total articles in feed
  articles_24h: number              // Articles added in last 24h
  articles_analyzed: number         // Articles with quality analysis
  coverage_percentage: number       // Percentage of articles analyzed
}

// ===========================
// Feed Scheduling Types
// ===========================

export interface ScheduledFeed {
  id: string
  name: string
  fetch_interval: number
  next_fetch_at: string
  priority: number
}

export interface TimelineSlot {
  [timestamp: string]: ScheduledFeed[]
}

export interface ScheduleTimeline {
  start_time: string
  end_time: string
  hours: number
  total_feeds: number
  total_slots: number
  max_concurrent_feeds: number
  avg_feeds_per_slot: number
  timeline: TimelineSlot
}

export interface DistributionStats {
  total_active_feeds: number
  max_concurrent_feeds: number
  avg_feeds_per_slot?: number  // Optional - not returned by backend
  distribution_score: number  // 0-100
  recommendation: string
  intervals?: {  // Optional - not returned by backend
    [interval: string]: {
      count: number
      avg_concurrent: number
    }
  }
  // Additional fields returned by backend
  feeds_in_next_24h?: number
  peak_times?: string[]
}

export interface OptimizationResult {
  feeds_analyzed: number
  feeds_optimized: number
  before: {
    max_concurrent: number
    distribution_score: number
  }
  after: {
    max_concurrent: number
    distribution_score: number
  }
  improvement_percentage: number
  preview?: Array<{
    feed_id: string
    feed_name: string
    old_offset: number
    new_offset: number
    old_next_fetch: string
    new_next_fetch: string
  }>
  message: string
}

export interface SchedulingConflict {
  time_window: string
  feed_count: number
  feeds: Array<{
    id: string
    name: string
    next_fetch_at: string
  }>
}

export interface ConflictAnalysis {
  conflicts_detected: number
  clusters: SchedulingConflict[]
  recommendations: string[]
  total_affected_feeds: number
}

export interface SchedulingStats {
  interval_distribution: {
    [minutes: string]: number
  }
  distribution_score: number
  max_concurrent_feeds: number
  total_active_feeds: number
  clusters_detected: number
  max_cluster_size: number
  recommendation: string
  health_status: 'excellent' | 'good' | 'fair' | 'poor'
}

export interface RescheduleResponse {
  feed_id: string
  feed_name: string
  fetch_interval: number
  schedule_offset_minutes: number
  next_fetch_at: string
  message: string
}

/**
 * API client for Feed Service Admin Dashboard
 * Uses JWT authentication via feedApi from @/api/axios
 */

import { feedApi } from '@/api/axios'
import type {
  FeedServiceHealth,
  FeedStats,
  FeedListResponse,
  FeedListFilters,
  FeedResponse,
  FeedHealthResponse,
  FeedQualityResponse,
  FeedQualityV2Response,
  FeedQualityOverview,
  AssessmentHistoryResponse,
  FetchTriggerResponse,
  AssessmentTriggerResponse,
  BulkFetchRequest,
  BulkFetchResponse,
  RecentItemsResponse,
  ResetErrorResponse,
  ScheduleTimeline,
  DistributionStats,
  OptimizationResult,
  ConflictAnalysis,
  SchedulingStats,
  RescheduleResponse,
} from '@/types/feedServiceAdmin'
import type {
  Source,
  SourceFeed,
  SourceFilters,
  SourceListResponse,
  CreateSourceRequest,
  UpdateSourceRequest,
  AddSourceFeedRequest,
  SourceAssessmentHistory,
  TriggerAssessmentResponse,
  SourceStats,
} from '@/types/source'

// ===========================
// Service Health & Stats
// ===========================

export const getServiceHealth = async (): Promise<FeedServiceHealth> => {
  // Health endpoint is at root level (/health), not under /api/v1
  // We need to override the baseURL to access it
  const baseUrl = import.meta.env.VITE_FEED_API_URL.replace('/api/v1', '')
  const { data } = await feedApi.get<FeedServiceHealth>('/health', {
    baseURL: baseUrl,
  })
  return data
}

export const getFeedStats = async (): Promise<FeedStats> => {
  const { data } = await feedApi.get<FeedStats>('/feeds/stats')
  return data
}

// ===========================
// Feed Management
// ===========================

export const getFeedList = async (filters?: FeedListFilters): Promise<FeedListResponse> => {
  const { data } = await feedApi.get<FeedResponse[]>('/feeds', {
    params: {
      skip: filters?.skip || 0,
      limit: filters?.limit || 100,
      is_active: filters?.is_active,
      status: filters?.status,
      category: filters?.category,
      health_score_min: filters?.health_score_min,
      health_score_max: filters?.health_score_max,
    },
  })

  // Transform array response to list response format
  return {
    feeds: data,
    total: data.length,
    skip: filters?.skip || 0,
    limit: filters?.limit || 100,
  }
}

export const getFeed = async (feedId: string): Promise<FeedResponse> => {
  const { data } = await feedApi.get<FeedResponse>(`/feeds/${feedId}`)
  return data
}

export const getFeedHealth = async (feedId: string): Promise<FeedHealthResponse> => {
  const { data } = await feedApi.get<FeedHealthResponse>(`/feeds/${feedId}/health`)
  return data
}

export const getFeedQuality = async (feedId: string): Promise<FeedQualityResponse> => {
  const { data } = await feedApi.get<FeedQualityResponse>(`/feeds/${feedId}/quality`)
  return data
}

// ===========================
// Assessment Management
// ===========================

export const getAssessmentHistory = async (
  feedId: string,
  limit: number = 10
): Promise<AssessmentHistoryResponse> => {
  const { data } = await feedApi.get<AssessmentHistoryResponse>(
    `/feeds/${feedId}/assessment-history`,
    { params: { limit } }
  )
  return data
}

export const triggerAssessment = async (
  feedId: string
): Promise<AssessmentTriggerResponse> => {
  const { data } = await feedApi.post<AssessmentTriggerResponse>(`/feeds/${feedId}/assess`)
  return data
}

// ===========================
// Feed Operations
// ===========================

export const triggerFetch = async (feedId: string): Promise<FetchTriggerResponse> => {
  const { data } = await feedApi.post<FetchTriggerResponse>(`/feeds/${feedId}/fetch`)
  return data
}

export const resetFeedError = async (feedId: string): Promise<ResetErrorResponse> => {
  const { data } = await feedApi.post<ResetErrorResponse>(`/feeds/${feedId}/reset-error`)
  return data
}

export const bulkFetch = async (request: BulkFetchRequest): Promise<BulkFetchResponse> => {
  const { data } = await feedApi.post<BulkFetchResponse>('/feeds/bulk-fetch', request)
  return data
}

// ===========================
// Feed Items
// ===========================

export const getRecentItems = async (limit: number = 20): Promise<RecentItemsResponse> => {
  const { data } = await feedApi.get('/feeds/items', {
    params: {
      limit,
      sort_by: 'created_at',
      order: 'desc',
    },
  })

  // Transform to expected format
  return {
    items: data,
    total: data.length,
  }
}

// ===========================
// Category Analytics
// ===========================

export const getCategoryStats = async (): Promise<Array<{
  category: string
  feed_count: number
  total_items: number
  items_last_24h: number
}>> => {
  // This would need a dedicated backend endpoint
  // For now, we'll derive it from feed list
  const feedList = await getFeedList({ limit: 1000 })

  const categoryMap = new Map<string, {
    feed_count: number
    total_items: number
    items_last_24h: number
  }>()

  feedList.feeds.forEach(feed => {
    // Now each feed has a single category instead of an array
    if (feed.category) {
      const existing = categoryMap.get(feed.category) || {
        feed_count: 0,
        total_items: 0,
        items_last_24h: 0,
      }

      categoryMap.set(feed.category, {
        feed_count: existing.feed_count + 1,
        total_items: existing.total_items + feed.total_items,
        items_last_24h: existing.items_last_24h + feed.items_last_24h,
      })
    }
  })

  return Array.from(categoryMap.entries()).map(([category, stats]) => ({
    category,
    ...stats,
  }))
}

// ===========================
// Feed Quality V2
// ===========================

/**
 * Get comprehensive Feed Quality V2 metrics for a specific feed
 * @param feedId - Feed UUID
 * @param days - Number of days to analyze (default: 30)
 */
export const getFeedQualityV2 = async (
  feedId: string,
  days: number = 30
): Promise<FeedQualityV2Response> => {
  const { data } = await feedApi.get<FeedQualityV2Response>(
    `/feeds/${feedId}/quality-v2`,
    {
      params: { days },
    }
  )
  return data
}

/**
 * Get Quality V2 overview for all active feeds
 * Returns a list with key metrics for each feed
 */
export const getFeedQualityOverview = async (): Promise<FeedQualityOverview[]> => {
  const { data } = await feedApi.get<FeedQualityOverview[]>('/feeds/quality-v2/overview')
  return data
}

// ===========================
// Feed Scheduling
// ===========================

/**
 * Get feed schedule timeline for visualization
 * @param hours - Number of hours to look ahead (default: 24, max: 168)
 */
export const getScheduleTimeline = async (hours: number = 24): Promise<ScheduleTimeline> => {
  const { data } = await feedApi.get<ScheduleTimeline>('/scheduling/timeline', {
    params: { hours },
  })
  return data
}

/**
 * Get current schedule distribution statistics
 */
export const getDistributionStats = async (): Promise<DistributionStats> => {
  const { data } = await feedApi.get<DistributionStats>('/scheduling/distribution')
  return data
}

/**
 * Calculate and optionally apply schedule optimization
 * @param apply - If true, apply changes to database. If false, return preview only.
 */
export const optimizeSchedule = async (apply: boolean = false): Promise<OptimizationResult> => {
  const { data } = await feedApi.post<OptimizationResult>('/scheduling/optimize', null, {
    params: { apply },
  })
  return data
}

/**
 * Detect scheduling conflicts (clusters of feeds)
 */
export const detectConflicts = async (): Promise<ConflictAnalysis> => {
  const { data } = await feedApi.get<ConflictAnalysis>('/scheduling/conflicts')
  return data
}

/**
 * Get comprehensive scheduling statistics
 */
export const getSchedulingStats = async (): Promise<SchedulingStats> => {
  const { data } = await feedApi.get<SchedulingStats>('/scheduling/stats')
  return data
}

/**
 * Manually reschedule a specific feed
 * @param feedId - Feed UUID
 * @param offsetMinutes - New offset in minutes (0 to fetch_interval)
 */
export const rescheduleFeed = async (
  feedId: string,
  offsetMinutes: number
): Promise<RescheduleResponse> => {
  const { data } = await feedApi.put<RescheduleResponse>(
    `/scheduling/feeds/${feedId}/schedule`,
    null,
    {
      params: { offset_minutes: offsetMinutes },
    }
  )
  return data
}

// ===========================
// Source Management
// ===========================

/**
 * API response structure from backend
 */
interface SourceApiResponse {
  items: SourceApiItem[]
  total: number
  skip: number
  limit: number
}

interface SourceApiItem {
  id: string
  domain: string
  canonical_name: string
  organization_name?: string
  description?: string
  homepage_url?: string
  logo_url?: string
  status: string
  is_active: boolean
  category?: string
  country?: string
  language?: string
  assessment?: {
    assessment_status?: string
    assessment_date?: string
    credibility_tier?: string
    reputation_score?: number
    political_bias?: string
    founded_year?: number
    organization_type?: string
    editorial_standards?: Record<string, unknown>
    trust_ratings?: Record<string, unknown>
    assessment_summary?: string
  }
  scrape_config?: {
    scrape_method: string
    fallback_methods?: string[]
    scrape_status: string
    paywall_type: string
    paywall_bypass_method?: string
    rate_limit_per_minute: number
    requires_stealth: boolean
    requires_proxy: boolean
    custom_headers?: Record<string, string>
  }
  scrape_metrics?: {
    scrape_success_rate: number
    scrape_avg_response_ms: number
    scrape_total_attempts: number
    scrape_avg_word_count: number
    scrape_avg_quality: number
    scrape_last_success?: string
    scrape_last_failure?: string
  }
  feeds_count?: number
  active_feeds_count?: number
  notes?: string
  created_at: string
  updated_at?: string
}

/**
 * Transform API response to frontend Source type
 */
function transformSourceApiItem(item: SourceApiItem): Source {
  return {
    id: item.id,
    domain: item.domain,
    canonical_name: item.canonical_name,
    organization_name: item.organization_name,
    description: item.description,
    homepage_url: item.homepage_url,
    logo_url: item.logo_url,
    status: item.status as Source['status'],
    is_active: item.is_active,
    category: item.category,
    country: item.country,
    language: item.language,
    // Flatten assessment
    assessment_status: item.assessment?.assessment_status as Source['assessment_status'],
    assessment_date: item.assessment?.assessment_date,
    credibility_tier: item.assessment?.credibility_tier as Source['credibility_tier'],
    reputation_score: item.assessment?.reputation_score,
    political_bias: item.assessment?.political_bias,
    founded_year: item.assessment?.founded_year,
    organization_type: item.assessment?.organization_type,
    editorial_standards: item.assessment?.editorial_standards,
    trust_ratings: item.assessment?.trust_ratings,
    assessment_summary: item.assessment?.assessment_summary,
    // Flatten scrape_config
    scrape_method: item.scrape_config?.scrape_method ?? 'newspaper4k',
    fallback_methods: item.scrape_config?.fallback_methods,
    scrape_status: (item.scrape_config?.scrape_status ?? 'unknown') as Source['scrape_status'],
    paywall_type: (item.scrape_config?.paywall_type ?? 'none') as Source['paywall_type'],
    paywall_bypass_method: item.scrape_config?.paywall_bypass_method,
    rate_limit_per_minute: item.scrape_config?.rate_limit_per_minute ?? 10,
    requires_stealth: item.scrape_config?.requires_stealth ?? false,
    requires_proxy: item.scrape_config?.requires_proxy ?? false,
    custom_headers: item.scrape_config?.custom_headers,
    // Flatten scrape_metrics
    scrape_success_rate: item.scrape_metrics?.scrape_success_rate ?? 0,
    scrape_avg_response_ms: item.scrape_metrics?.scrape_avg_response_ms ?? 0,
    scrape_total_attempts: item.scrape_metrics?.scrape_total_attempts ?? 0,
    scrape_avg_word_count: item.scrape_metrics?.scrape_avg_word_count ?? 0,
    scrape_avg_quality: item.scrape_metrics?.scrape_avg_quality ?? 0,
    scrape_last_success: item.scrape_metrics?.scrape_last_success,
    scrape_last_failure: item.scrape_metrics?.scrape_last_failure,
    // Stats
    feeds_count: item.feeds_count,
    active_feeds_count: item.active_feeds_count,
    notes: item.notes,
    created_at: item.created_at,
    updated_at: item.updated_at,
  }
}

/**
 * Get list of sources with optional filtering
 */
export const getSourceList = async (filters?: SourceFilters): Promise<SourceListResponse> => {
  const { data } = await feedApi.get<SourceApiResponse>('/sources', {
    params: {
      skip: filters?.skip || 0,
      limit: filters?.limit || 50,
      status: filters?.status,
      credibility_tier: filters?.credibility_tier,
      scrape_status: filters?.scrape_status,
      country: filters?.country,
      category: filters?.category,
      language: filters?.language,
      search: filters?.search,
      is_active: filters?.is_active,
      has_assessment: filters?.has_assessment,
    },
  })

  return {
    sources: data.items.map(transformSourceApiItem),
    total: data.total,
    skip: data.skip,
    limit: data.limit,
  }
}

/**
 * Get a single source by ID
 */
export const getSource = async (sourceId: string): Promise<Source> => {
  const { data } = await feedApi.get<Source>(`/sources/${sourceId}`)
  return data
}

/**
 * Get a source by domain
 */
export const getSourceByDomain = async (domain: string): Promise<Source> => {
  const { data } = await feedApi.get<Source>(`/sources/by-domain/${encodeURIComponent(domain)}`)
  return data
}

/**
 * Create a new source
 */
export const createSource = async (request: CreateSourceRequest): Promise<Source> => {
  const { data } = await feedApi.post<Source>('/sources', request)
  return data
}

/**
 * Update an existing source
 */
export const updateSource = async (
  sourceId: string,
  request: UpdateSourceRequest
): Promise<Source> => {
  const { data } = await feedApi.put<Source>(`/sources/${sourceId}`, request)
  return data
}

/**
 * Delete a source
 */
export const deleteSource = async (sourceId: string): Promise<void> => {
  await feedApi.delete(`/sources/${sourceId}`)
}

/**
 * Get source statistics
 */
export const getSourceStats = async (): Promise<SourceStats> => {
  const { data } = await feedApi.get<SourceStats>('/sources/stats')
  return data
}

// ===========================
// Source Feeds
// ===========================

/**
 * Get feeds for a specific source
 */
export const getSourceFeeds = async (sourceId: string): Promise<SourceFeed[]> => {
  const { data } = await feedApi.get<SourceFeed[]>(`/sources/${sourceId}/feeds`)
  return data
}

/**
 * Add a feed to a source
 */
export const addSourceFeed = async (
  sourceId: string,
  request: AddSourceFeedRequest
): Promise<SourceFeed> => {
  const { data } = await feedApi.post<SourceFeed>(`/sources/${sourceId}/feeds`, request)
  return data
}

/**
 * Remove a feed from a source
 */
export const removeSourceFeed = async (sourceId: string, feedId: string): Promise<void> => {
  await feedApi.delete(`/sources/${sourceId}/feeds/${feedId}`)
}

// ===========================
// Source Assessment
// ===========================

/**
 * Get assessment history for a source
 */
export const getSourceAssessmentHistory = async (
  sourceId: string,
  limit: number = 10
): Promise<SourceAssessmentHistory[]> => {
  const { data } = await feedApi.get<SourceAssessmentHistory[]>(
    `/sources/${sourceId}/assessment-history`,
    { params: { limit } }
  )
  return data
}

/**
 * Trigger assessment for a source
 */
export const triggerSourceAssessment = async (
  sourceId: string
): Promise<TriggerAssessmentResponse> => {
  const { data } = await feedApi.post<TriggerAssessmentResponse>(`/sources/${sourceId}/assess`)
  return data
}

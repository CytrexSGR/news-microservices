/**
 * TypeScript types for Unified Source Management
 *
 * Source: Master entity per domain with assessment and scraping config
 * SourceFeed: Provider-specific feeds (RSS, MediaStack, etc.)
 */

// ===========================
// Enums
// ===========================

export const SourceStatus = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  BLOCKED: 'blocked',
} as const

export type SourceStatus = (typeof SourceStatus)[keyof typeof SourceStatus]

export const ScrapeStatus = {
  WORKING: 'working',
  DEGRADED: 'degraded',
  BLOCKED: 'blocked',
  UNSUPPORTED: 'unsupported',
  UNKNOWN: 'unknown',
} as const

export type ScrapeStatus = (typeof ScrapeStatus)[keyof typeof ScrapeStatus]

export const PaywallType = {
  NONE: 'none',
  SOFT: 'soft',
  HARD: 'hard',
  METERED: 'metered',
  REGISTRATION: 'registration',
} as const

export type PaywallType = (typeof PaywallType)[keyof typeof PaywallType]

export const ProviderType = {
  RSS: 'rss',
  MEDIASTACK: 'mediastack',
  NEWSAPI: 'newsapi',
  GDELT: 'gdelt',
  MANUAL: 'manual',
} as const

export type ProviderType = (typeof ProviderType)[keyof typeof ProviderType]

export const CredibilityTier = {
  TIER_1: 'tier_1',
  TIER_2: 'tier_2',
  TIER_3: 'tier_3',
  UNKNOWN: 'unknown',
} as const

export type CredibilityTier = (typeof CredibilityTier)[keyof typeof CredibilityTier]

export const AssessmentStatus = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const

export type AssessmentStatus = (typeof AssessmentStatus)[keyof typeof AssessmentStatus]

// ===========================
// Source Types
// ===========================

export interface Source {
  id: string
  domain: string
  canonical_name: string
  organization_name?: string
  description?: string
  homepage_url?: string
  logo_url?: string

  // Status
  status: SourceStatus
  is_active: boolean

  // Categorization
  category?: string
  country?: string
  language?: string

  // Assessment
  assessment_status?: AssessmentStatus
  assessment_date?: string
  credibility_tier?: CredibilityTier
  reputation_score?: number
  political_bias?: string
  founded_year?: number
  organization_type?: string
  editorial_standards?: Record<string, unknown>
  trust_ratings?: Record<string, unknown>
  assessment_summary?: string

  // Scraping Config
  scrape_method: string
  fallback_methods?: string[]
  scrape_status: ScrapeStatus
  paywall_type: PaywallType
  paywall_bypass_method?: string
  rate_limit_per_minute: number
  requires_stealth: boolean
  requires_proxy: boolean
  custom_headers?: Record<string, string>

  // Scraping Metrics
  scrape_success_rate: number
  scrape_avg_response_ms: number
  scrape_total_attempts: number
  scrape_avg_word_count: number
  scrape_avg_quality: number
  scrape_last_success?: string
  scrape_last_failure?: string

  // Meta
  notes?: string
  created_at: string
  updated_at?: string

  // Computed / Relationships
  feeds?: SourceFeed[]
  feeds_count?: number
  active_feeds_count?: number
  articles_count?: number
}

// ===========================
// SourceFeed Types
// ===========================

export interface SourceFeed {
  id: string
  source_id: string
  provider_type: ProviderType
  provider_id?: string
  channel_name?: string

  // RSS-specific
  feed_url?: string
  etag?: string
  last_modified?: string
  fetch_interval: number

  // Status
  is_active: boolean
  health_score: number
  consecutive_failures: number
  last_fetched_at?: string
  last_error?: string

  // Analysis Config
  enable_analysis: boolean

  // Statistics
  total_items: number
  items_last_24h: number

  // Meta
  discovered_at: string
  created_at: string
  updated_at?: string

  // Relationship (when loaded)
  source?: Source
}

// ===========================
// Request/Response Types
// ===========================

export interface SourceFilters {
  status?: SourceStatus
  credibility_tier?: CredibilityTier
  scrape_status?: ScrapeStatus
  country?: string
  category?: string
  language?: string
  search?: string
  is_active?: boolean
  has_assessment?: boolean
  skip?: number
  limit?: number
}

export interface SourceListResponse {
  sources: Source[]
  total: number
  skip: number
  limit: number
}

export interface CreateSourceRequest {
  domain: string
  canonical_name: string
  organization_name?: string
  description?: string
  homepage_url?: string
  category?: string
  country?: string
  language?: string
  scrape_method?: string
  paywall_type?: PaywallType
  rate_limit_per_minute?: number
  requires_stealth?: boolean
  requires_proxy?: boolean
  notes?: string
}

export interface UpdateSourceRequest {
  canonical_name?: string
  organization_name?: string
  description?: string
  homepage_url?: string
  logo_url?: string
  status?: SourceStatus
  is_active?: boolean
  category?: string
  country?: string
  language?: string
  scrape_method?: string
  fallback_methods?: string[]
  paywall_type?: PaywallType
  paywall_bypass_method?: string
  rate_limit_per_minute?: number
  requires_stealth?: boolean
  requires_proxy?: boolean
  custom_headers?: Record<string, string>
  notes?: string
}

export interface AddSourceFeedRequest {
  provider_type: ProviderType
  feed_url?: string
  provider_id?: string
  channel_name?: string
  fetch_interval?: number
  enable_analysis?: boolean
}

export interface SourceFeedFilters {
  provider_type?: ProviderType
  is_active?: boolean
  health_score_min?: number
}

// ===========================
// Assessment Types
// ===========================

export interface SourceAssessmentHistory {
  id: string
  source_id: string
  assessment_status: AssessmentStatus
  assessment_date: string
  credibility_tier?: CredibilityTier
  reputation_score?: number
  political_bias?: string
  founded_year?: number
  organization_type?: string
  editorial_standards?: Record<string, unknown>
  trust_ratings?: Record<string, unknown>
  assessment_summary?: string
  raw_response?: Record<string, unknown>
  created_at: string
}

export interface TriggerAssessmentResponse {
  message: string
  source_id: string
  status: AssessmentStatus
}

// ===========================
// Stats Types
// ===========================

export interface SourceStats {
  total_sources: number
  active_sources: number
  sources_by_tier: {
    tier_1: number
    tier_2: number
    tier_3: number
    unknown: number
  }
  sources_by_status: {
    active: number
    inactive: number
    blocked: number
  }
  total_feeds: number
  active_feeds: number
  total_articles: number
}

// ===========================
// UI Helper Types
// ===========================

export interface SourceCardData {
  source: Source
  isExpanded?: boolean
  showFeeds?: boolean
}

export interface CredibilityBadgeProps {
  tier?: CredibilityTier
  score?: number
  showScore?: boolean
}

export interface PoliticalBiasIndicator {
  bias: string
  label: string
  position: number // -100 to +100 for slider positioning
}

// Helper function to get bias position
export function getBiasPosition(bias?: string): number {
  if (!bias) return 0
  const biasMap: Record<string, number> = {
    'far-left': -80,
    'left': -50,
    'center-left': -25,
    'center': 0,
    'center-right': 25,
    'right': 50,
    'far-right': 80,
  }
  return biasMap[bias.toLowerCase()] ?? 0
}

// Helper function to get tier color
export function getTierColor(tier?: CredibilityTier): string {
  const colorMap: Record<CredibilityTier, string> = {
    tier_1: 'green',
    tier_2: 'yellow',
    tier_3: 'red',
    unknown: 'gray',
  }
  return tier ? colorMap[tier] : 'gray'
}

// Helper function to get tier label
export function getTierLabel(tier?: CredibilityTier): string {
  const labelMap: Record<CredibilityTier, string> = {
    tier_1: 'Highly Credible',
    tier_2: 'Generally Credible',
    tier_3: 'Use with Caution',
    unknown: 'Not Assessed',
  }
  return tier ? labelMap[tier] : 'Not Assessed'
}

// Helper function to get scrape status color
export function getScrapeStatusColor(status?: ScrapeStatus): string {
  const colorMap: Record<ScrapeStatus, string> = {
    working: 'green',
    degraded: 'yellow',
    blocked: 'red',
    unsupported: 'orange',
    unknown: 'gray',
  }
  return status ? colorMap[status] : 'gray'
}

// Helper function to get provider icon
export function getProviderIcon(provider: ProviderType): string {
  const iconMap: Record<ProviderType, string> = {
    rss: '📡',
    mediastack: '📰',
    newsapi: '🗞️',
    gdelt: '🌐',
    manual: '✏️',
  }
  return iconMap[provider]
}

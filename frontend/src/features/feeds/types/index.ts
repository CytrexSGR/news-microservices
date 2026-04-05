export interface FeedAssessment {
  assessment_status?: string;
  assessment_date?: string;
  credibility_tier?: string;
  reputation_score?: number;
  founded_year?: number;
  organization_type?: string;
  political_bias?: string;
  editorial_standards?: {
    fact_checking_level?: string;
    corrections_policy?: string;
    source_attribution?: string;
  };
  trust_ratings?: {
    media_bias_fact_check?: string;
    allsides_rating?: string;
    newsguard_score?: number;
  };
  recommendation?: {
    skip_waiting_period?: boolean;
    initial_quality_boost?: number;
    bot_detection_threshold?: number;
  };
  assessment_summary?: string;
  quality_score?: number; // 0-100, auto-calculated quality score
}

export interface AdmiraltyCodeData {
  code: 'A' | 'B' | 'C' | 'D' | 'E' | 'F';
  label: string;
  color: string;
}

export interface Feed {
  id: string;
  name: string;
  url: string;
  description?: string;
  category?: string;  // Single category from fixed set
  fetch_interval: number;
  is_active: boolean;
  status: string;
  created_at: string;
  updated_at?: string;
  last_fetched_at?: string;
  health_score: number;
  consecutive_failures: number;
  quality_score?: number; // 0-100, calculated feed quality score
  admiralty_code?: AdmiraltyCodeData; // NATO Admiralty Code rating (A-F)
  total_items: number;
  items_last_24h: number;
  scrape_full_content?: boolean;
  scrape_method?: string;
  scrape_failure_count?: number;
  scrape_failure_threshold?: number;
  scrape_last_failure_at?: string | null;
  scrape_disabled_reason?: 'manual' | 'auto_threshold' | null;

  // Auto-analysis configuration (V1 - DEPRECATED, kept for backward compatibility)
  enable_categorization?: boolean;
  enable_finance_sentiment?: boolean;
  enable_geopolitical_sentiment?: boolean;
  enable_osint_analysis?: boolean;
  enable_summary?: boolean;
  enable_entity_extraction?: boolean;
  enable_topic_classification?: boolean;

  // Auto-analysis configuration (V2 - unified analysis via feed-service)
  enable_analysis_v2?: boolean;

  // Feed source assessment
  assessment?: FeedAssessment;
}

export interface FeedHealth {
  feed_id: string;
  health_score: number;
  success_rate: number;
  consecutive_failures: number;
  avg_fetch_duration: number;
  last_success_at?: string;
  last_failure_at?: string;
  total_fetches: number;
  successful_fetches: number;
  failed_fetches: number;
  history: HealthHistoryPoint[];
}

export interface HealthHistoryPoint {
  timestamp: string;
  health_score: number;
  success: boolean;
  duration?: number;
  error?: string;
}

// API returns array directly, not wrapped in object
export type FeedListResponse = Feed[];

// Source types for feed items (matches backend SourceType enum)
export type SourceType =
  | 'rss'
  | 'perplexity_research'
  | 'scraping'
  | 'manual'
  | 'api_twitter'
  | 'api_telegram';

// Source-specific metadata (for Perplexity: model, cost, query, etc.)
export interface SourceMetadata {
  model?: string;
  cost?: number;
  query?: string;
  citations?: string[];
  [key: string]: unknown;
}

export interface FeedItem {
  id: string;
  title: string;
  link: string;
  description?: string;
  author?: string | null;
  published_at?: string;
  created_at: string;
  feed_id: string | null;  // Nullable for non-RSS sources
  guid?: string;
  content?: string;
  scrape_status?: string | null;
  scrape_word_count?: number | null;
  scraped_at?: string | null;
  content_hash?: string;

  // Source type discriminator (rss, perplexity_research, scraping, etc.)
  source_type?: SourceType;
  // Source-specific metadata (model, cost, query for Perplexity, etc.)
  source_metadata?: SourceMetadata;
  // Parent article reference (for research/derived content)
  parent_article_id?: string | null;
  // Research articles linked to this article
  research_articles?: FeedItem[];

  // Analysis fields (V1 - legacy)
  sentiment_analysis?: any;
  finance_sentiment?: any;
  geopolitical_sentiment?: any;
  category_analysis?: any;
  event_analysis?: any;
  summaries?: any;
  topics?: any;
  // V2 Analysis - ARCHIVED (service decommissioned 2025-11-24)
  v2_analysis?: Record<string, unknown>;
  // V3 Analysis (from content-analysis-v3 service) - ACTIVE
  v3_analysis?: import('./analysisV3').V3ArticleAnalysis;
}

// Extended FeedItem with feed context for cross-feed article listings
export interface FeedItemWithFeed extends FeedItem {
  feed_name: string;
}

// Re-export analysis types
export * from './analysis';

// Re-export admiralty code types
export * from './admiraltyCode';

// Re-export feed creation types
export * from './createFeed';

// Re-export quality monitoring types
export * from './quality';

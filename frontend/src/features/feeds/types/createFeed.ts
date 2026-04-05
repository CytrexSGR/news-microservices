/**
 * Types for Feed Creation
 */

export interface PreAssessmentRequest {
  url: string;
}

/**
 * Fixed feed categories
 */
export const FEED_CATEGORIES = [
  'General News',
  'Finance & Markets',
  'Tech & Science',
  'Geopolitics & Security',
  'Energy & Industry',
  'Regional / Local',
  'Think Tanks / Analysis',
  'Special Interest',
] as const;

export type FeedCategory = typeof FEED_CATEGORIES[number];

export interface PreAssessmentResponse {
  success: boolean;
  assessment: {
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
  };
  suggested_values: {
    name?: string;
    description?: string;
    category?: FeedCategory;  // Single category from fixed set
  };
}

export interface FeedCreateInput {
  // Basic Info
  name: string;
  url: string;
  description?: string;
  category?: FeedCategory;  // Single category from fixed set
  fetch_interval: number;

  // Scraping Configuration
  scrape_full_content: boolean;
  scrape_method: 'newspaper4k' | 'playwright';
  scrape_failure_threshold: number;

  // Auto-Analysis Configuration
  enable_categorization: boolean;
  enable_finance_sentiment: boolean;
  enable_geopolitical_sentiment: boolean;
  enable_bias: boolean;
  enable_conflict: boolean;
  enable_osint_analysis: boolean;
  enable_summary: boolean;
  enable_entity_extraction: boolean;
  enable_topic_classification: boolean;

  // Source Assessment (optional)
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
}

export interface CreateFeedFormData extends FeedCreateInput {
  // Additional form-only fields
  _hasRunAssessment?: boolean;
  _assessmentData?: PreAssessmentResponse['assessment'];
}

export const DEFAULT_FEED_VALUES: Partial<CreateFeedFormData> = {
  description: undefined, // Will be filled by assessment
  category: undefined, // Will be filled by assessment
  fetch_interval: 60,
  scrape_full_content: false,
  scrape_method: 'newspaper4k',
  scrape_failure_threshold: 5,
  // All analysis options enabled by default
  enable_categorization: true,
  enable_finance_sentiment: true,
  enable_geopolitical_sentiment: true,
  enable_bias: true,
  enable_conflict: true,
  enable_osint_analysis: true,
  enable_summary: true,
  enable_entity_extraction: true,
  enable_topic_classification: true,
};

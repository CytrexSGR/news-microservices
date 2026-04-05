/**
 * Article Analysis Types
 *
 * TypeScript types for article analysis data from content-analysis-service.
 * Matches backend ArticleAnalysisResponse schema.
 */

// ============================================================================
// Feed Configuration
// ============================================================================

export interface FeedConfig {
  enable_categorization: boolean;
  enable_finance_sentiment: boolean;
  enable_geopolitical_sentiment: boolean;
  enable_osint_analysis: boolean;
}

// ============================================================================
// Category Classification
// ============================================================================

export type ArticleCategory =
  | 'Geopolitics Security'
  | 'Politics Society'
  | 'Economy Markets'
  | 'Climate Environment Health'
  | 'Panorama'
  | 'Technology Science';

export interface CategoryClassification {
  id: string;
  category: ArticleCategory;
  confidence: number;
  alternative_categories: Array<{
    category: ArticleCategory;
    confidence: number;
  }>;
  reasoning: string;
  key_indicators: string[];
  cached: boolean;
  processing_time_ms?: number;
}

// ============================================================================
// Sentiment Analysis
// ============================================================================

export type SentimentLabel = 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | 'MIXED';

export interface SentimentAnalysis {
  id: string;
  overall_sentiment: SentimentLabel;
  confidence: number;
  positive_score: number;
  negative_score: number;
  neutral_score: number;
  bias_detected: boolean;
  bias_direction?: string;
  bias_confidence?: number;
  subjectivity_score: number;
  emotion_scores?: Record<string, number>;
  reasoning?: string;
  key_phrases?: string[];
  cached: boolean;
  processing_time_ms?: number;
}

// ============================================================================
// Finance Sentiment
// ============================================================================

export type MarketSentiment = 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'MIXED';
export type TimeHorizon = 'SHORT_TERM' | 'MEDIUM_TERM' | 'LONG_TERM';

export interface FinanceSentiment {
  id: string;
  market_sentiment: MarketSentiment;
  market_confidence: number;
  time_horizon: TimeHorizon;
  uncertainty: number;
  volatility: number;
  economic_impact: number;
  reasoning: string;
  key_indicators: string[];
  affected_sectors: string[];
  affected_assets: string[];
  cached: boolean;
  processing_time_ms?: number;
}

// ============================================================================
// Geopolitical Sentiment
// ============================================================================

export type ConflictType =
  | 'MILITARY'
  | 'DIPLOMATIC'
  | 'ECONOMIC'
  | 'CYBER'
  | 'HYBRID'
  | 'NONE';

export interface GeopoliticalSentiment {
  id: string;
  stability_score: number; // -1 to +1
  security_relevance: number; // 0 to 1
  escalation_potential: number; // 0 to 1
  conflict_type: ConflictType;
  time_horizon: TimeHorizon;
  confidence: number;
  regions_affected: string[];
  impact_beneficiaries: string[];
  impact_affected: string[];
  alliance_activation: string[];
  diplomatic_impact_global?: number;
  diplomatic_impact_western?: number;
  diplomatic_impact_regional?: number;
  reasoning: string;
  key_factors: string[];
  cached: boolean;
  processing_time_ms?: number;
}

// ============================================================================
// OSINT Events (Event Analysis)
// ============================================================================

export interface OsintEvent {
  id: string;
  article_id: string;
  headline: string;
  source: string;
  publisher_url?: string;
  primary_event: string;
  location?: string;
  event_date?: string;
  actors: Record<string, string>;
  means?: string[];
  impact?: Record<string, any>;
  claims: Array<Record<string, any>>;
  status?: Record<string, any>;
  risk_tags: string[];
  publisher_context?: Record<string, any>;
  summary: string;
  confidence_overall: string; // "low" | "medium" | "high"
  confidence_dimensions?: Record<string, any>;
  evidence?: Array<Record<string, any>>;
  claim_count: number;
  evidence_count: number;
  needs_analyst_review: boolean;
  created_at?: string;
  updated_at?: string;
}

// ============================================================================
// Entities
// ============================================================================

export type EntityType =
  | 'PERSON'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'DATE'
  | 'EVENT'
  | 'PRODUCT';

export interface Entity {
  text: string;
  type: EntityType;
  confidence: number;
  mention_count: number;
}

// ============================================================================
// Topics
// ============================================================================

export interface Topic {
  topic: string;
  relevance_score: number;
  keywords?: string[];
  is_primary: boolean;
}

// ============================================================================
// Summary
// ============================================================================

export type SummaryType = 'SHORT' | 'MEDIUM' | 'LONG';

export interface Summary {
  type: SummaryType;
  text: string;
  compression_ratio?: number;
}

// ============================================================================
// Facts
// ============================================================================

export type FactType = 'CLAIM' | 'STATISTIC' | 'QUOTE' | 'EVENT';
export type VerificationStatus = 'UNVERIFIED' | 'VERIFIED' | 'DISPUTED';

export interface Fact {
  text: string;
  type: FactType;
  confidence: number;
  verification_status: VerificationStatus;
}

// ============================================================================
// Article Analysis Response (Main Type)
// ============================================================================

export interface ArticleAnalysis {
  // Article metadata (from feed-service)
  item_id: string;
  item_title: string;
  item_link: string;
  item_author?: string;
  item_published_at?: string;
  item_content?: string;
  item_word_count?: number;

  // Feed information and configuration
  feed_id: string;
  feed_name: string;
  feed_config: FeedConfig;

  // Analysis data (optional - may be null/empty if not yet analyzed)
  // Cards are shown based on feed_config, not on data availability
  category?: CategoryClassification;
  sentiment?: SentimentAnalysis;
  finance_sentiment?: FinanceSentiment;
  geopolitical_sentiment?: GeopoliticalSentiment;
  osint_events: OsintEvent[];
  entities: Entity[];
  topics: Topic[];
  summary?: Summary;
  facts: Fact[];
  keywords: string[];

  // Analysis metadata
  total_analyses: number;
  last_analyzed_at?: string;
}

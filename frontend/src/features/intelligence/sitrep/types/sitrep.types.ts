/**
 * SITREP (Situation Report) Types
 *
 * Type definitions for the SITREP service API responses.
 */

/**
 * Available SITREP categories for filtering and generation
 * Aligned with Tier-0 Triage Agent from content-analysis-v3
 * Source: services/content-analysis-v3/app/pipeline/tier0/triage.py
 */
export type SitrepCategory =
  | 'conflict'
  | 'finance'
  | 'politics'
  | 'humanitarian'
  | 'security'
  | 'technology'
  | 'other'
  | 'crypto';

/**
 * Display labels for SITREP categories
 */
export const SITREP_CATEGORY_LABELS: Record<SitrepCategory, string> = {
  conflict: 'Conflict',
  finance: 'Finance',
  politics: 'Politics',
  humanitarian: 'Humanitarian',
  security: 'Security',
  technology: 'Technology',
  other: 'Other',
  crypto: 'Crypto',
};

export interface RiskAssessment {
  level: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
}

export interface KeyDevelopment {
  title: string;
  summary: string;
  significance: string;
  risk_assessment?: RiskAssessment;
  related_entities?: string[];
}

export interface TopStory {
  // GPT-generated SITREPs use these fields
  cluster_id?: string;
  title?: string;
  tension_score?: number;
  is_breaking?: boolean;
  category?: string;
  // n8n-generated SITREPs use these fields
  id?: string;      // Cluster ID (alternative to cluster_id)
  label?: string;   // Story title (alternative to title)
  similarity?: number;
  // Common fields
  article_count: number;
}

export interface KeyEntity {
  name: string;
  type: string;
  mention_count: number;
}

export interface SentimentSummary {
  overall: 'positive' | 'negative' | 'neutral' | 'mixed';
  positive_percent: number;
  negative_percent: number;
  neutral_percent: number;
}

export interface EmergingSignal {
  signal_type: string;
  description: string;
  confidence: number;
  related_entities: string[];
}

export interface Sitrep {
  id: string;
  report_date: string;
  report_type: 'daily' | 'weekly' | 'breaking';
  category?: SitrepCategory;
  title: string;
  executive_summary: string;
  content_markdown?: string;
  content_html?: string;
  key_developments?: KeyDevelopment[];
  top_stories?: TopStory[];
  key_entities?: KeyEntity[];
  sentiment_summary?: SentimentSummary;
  emerging_signals?: EmergingSignal[];
  generation_model: string;
  generation_time_ms: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  articles_analyzed: number;
  confidence_score: number;
  human_reviewed: boolean;
  created_at: string;
}

export interface SitrepListResponse {
  sitreps: Sitrep[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface SitrepGenerateRequest {
  report_type: 'daily' | 'weekly' | 'breaking';
  category?: SitrepCategory;
  report_date?: string;
  top_stories_count?: number;
  min_cluster_size?: number;
}

export interface SitrepGenerateResponse {
  success: boolean;
  message: string;
  sitrep_id: string;
  sitrep: Sitrep;
}

export interface SitrepListParams {
  limit?: number;
  offset?: number;
  report_type?: 'daily' | 'weekly' | 'breaking';
  category?: SitrepCategory;
}

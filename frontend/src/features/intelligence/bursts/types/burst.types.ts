/**
 * Burst Detection Types
 *
 * Type definitions for the clustering-service Burst API responses.
 * Aligned with Tier-0 Triage Agent categories.
 */

/**
 * Available categories for filtering (aligned with SITREP categories)
 */
export type BurstCategory =
  | 'conflict'
  | 'finance'
  | 'politics'
  | 'humanitarian'
  | 'security'
  | 'technology'
  | 'other'
  | 'crypto';

/**
 * Category display labels
 */
export const BURST_CATEGORY_LABELS: Record<BurstCategory, string> = {
  conflict: 'Conflict',
  finance: 'Finance',
  politics: 'Politics',
  humanitarian: 'Humanitarian',
  security: 'Security',
  technology: 'Technology',
  other: 'Other',
  crypto: 'Crypto',
};

/**
 * Severity levels for burst alerts
 */
export type BurstSeverity = 'low' | 'medium' | 'high' | 'critical';

/**
 * Severity display colors
 */
export const SEVERITY_COLORS: Record<BurstSeverity, string> = {
  low: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

/**
 * Burst Alert from API response
 */
export interface BurstAlert {
  id: string;
  cluster_id: string;
  severity: BurstSeverity;
  velocity: number;
  window_minutes: number;
  alert_sent: boolean;
  alert_sent_at?: string;
  detected_at: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
  // New fields for category-based filtering
  title?: string;
  category?: BurstCategory;
  tension_score?: number;
  growth_rate?: number;
  top_entities?: string[];
  // Article time range
  first_article_at?: string;
  last_article_at?: string;
}

/**
 * Paginated burst alerts response
 */
export interface BurstListResponse {
  items: BurstAlert[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Burst detection statistics
 */
export interface BurstStats {
  total_bursts_24h: number;
  total_bursts_7d: number;
  by_severity: Record<BurstSeverity, number>;
  avg_velocity: number;
}

/**
 * Acknowledge response
 */
export interface AcknowledgeResponse {
  id: string;
  acknowledged: boolean;
  acknowledged_at: string;
  acknowledged_by: string;
}

/**
 * List params for burst API
 */
export interface BurstListParams {
  hours?: number;
  severity?: BurstSeverity;
  category?: BurstCategory;
  limit?: number;
  offset?: number;
}

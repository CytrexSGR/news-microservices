/**
 * Quality Types for Knowledge Graph
 *
 * TypeScript type definitions for graph quality assessment and monitoring.
 * Includes integrity checks, disambiguation quality, and data validation.
 *
 * @module features/knowledge-graph/types/quality
 */

// ===========================
// Graph Integrity Types
// ===========================

/**
 * Severity level for quality issues
 */
export type IssueSeverity = 'critical' | 'warning' | 'info';

/**
 * Quality issue type
 */
export type IssueType =
  | 'orphaned_node'
  | 'broken_relationship'
  | 'missing_properties'
  | 'duplicate_entity'
  | 'invalid_reference'
  | 'stale_data'
  | 'inconsistent_type';

/**
 * Quality Issue
 *
 * Represents a single data quality issue in the knowledge graph.
 */
export interface QualityIssue {
  /** Issue type category */
  type: IssueType;
  /** Number of occurrences */
  count: number;
  /** Severity level */
  severity: IssueSeverity;
  /** Human-readable description */
  description?: string;
  /** Example node/relationship IDs */
  examples?: string[];
}

/**
 * Graph Integrity Status
 *
 * Overall health metrics for the knowledge graph.
 */
export interface GraphIntegrity {
  /** Number of nodes without any relationships */
  orphaned_nodes: number;
  /** Number of relationships with invalid source/target */
  broken_relationships: number;
  /** Total nodes in the graph */
  total_nodes: number;
  /** Total relationships in the graph */
  total_relationships: number;
  /** Overall data quality score (0-100) */
  data_quality_score: number;
  /** Detailed issues list */
  issues: QualityIssue[];
  /** Last integrity check timestamp (ISO 8601) */
  last_checked?: string;
}

// ===========================
// Disambiguation Quality Types
// ===========================

/**
 * Entity type disambiguation statistics
 */
export interface EntityTypeDisambiguationStats {
  /** Total entities of this type */
  total: number;
  /** Successfully resolved entities */
  resolved: number;
  /** Pending disambiguation */
  pending: number;
  /** Resolution rate (0-1) */
  rate: number;
}

/**
 * Disambiguation Quality Metrics
 *
 * Metrics for entity disambiguation and resolution quality.
 */
export interface DisambiguationQuality {
  /** Overall success rate (0-1) */
  success_rate: number;
  /** Number of entities still ambiguous */
  ambiguous_entities: number;
  /** Number of successfully resolved entities */
  resolved_entities: number;
  /** Statistics by entity type */
  by_entity_type: Record<string, EntityTypeDisambiguationStats>;
  /** Last update timestamp (ISO 8601) */
  last_updated?: string;
}

// ===========================
// Data Freshness Types
// ===========================

/**
 * Data Freshness Status
 *
 * Metrics for data staleness and update frequency.
 */
export interface DataFreshness {
  /** Number of nodes updated in last 24h */
  updated_24h: number;
  /** Number of nodes updated in last 7d */
  updated_7d: number;
  /** Number of stale nodes (not updated in 30d+) */
  stale_nodes: number;
  /** Average age of data in hours */
  avg_data_age_hours: number;
  /** Last full refresh timestamp */
  last_full_refresh?: string;
}

// ===========================
// Quality Trend Types
// ===========================

/**
 * Quality Trend Data Point
 */
export interface QualityTrendPoint {
  /** Timestamp (ISO 8601) */
  timestamp: string;
  /** Quality score at this point */
  quality_score: number;
  /** Orphaned nodes count */
  orphaned_nodes: number;
  /** Disambiguation rate */
  disambiguation_rate: number;
}

/**
 * Quality Trends Response
 */
export interface QualityTrends {
  /** Trend data points */
  data: QualityTrendPoint[];
  /** Time range start */
  start_date: string;
  /** Time range end */
  end_date: string;
  /** Overall trend direction */
  trend: 'improving' | 'stable' | 'declining';
}

// ===========================
// API Request Types
// ===========================

/**
 * Query parameters for quality trends
 */
export interface QualityTrendsQueryParams {
  /** Start date (ISO 8601) */
  start_date?: string;
  /** End date (ISO 8601) */
  end_date?: string;
  /** Granularity (hour, day, week) */
  granularity?: 'hour' | 'day' | 'week';
}

// ===========================
// Quality Thresholds
// ===========================

/**
 * Quality score thresholds for display
 */
export const QUALITY_THRESHOLDS = {
  EXCELLENT: 90,
  GOOD: 75,
  FAIR: 50,
  POOR: 25,
} as const;

/**
 * Get quality level label based on score
 */
export function getQualityLevel(score: number): 'excellent' | 'good' | 'fair' | 'poor' | 'critical' {
  if (score >= QUALITY_THRESHOLDS.EXCELLENT) return 'excellent';
  if (score >= QUALITY_THRESHOLDS.GOOD) return 'good';
  if (score >= QUALITY_THRESHOLDS.FAIR) return 'fair';
  if (score >= QUALITY_THRESHOLDS.POOR) return 'poor';
  return 'critical';
}

/**
 * Quality level color mapping
 */
export const QUALITY_LEVEL_COLORS: Record<string, string> = {
  excellent: '#10B981', // Green-500
  good: '#22C55E',      // Green-400
  fair: '#F59E0B',      // Amber-500
  poor: '#F97316',      // Orange-500
  critical: '#EF4444',  // Red-500
};

/**
 * Severity color mapping
 */
export const SEVERITY_COLORS: Record<IssueSeverity, string> = {
  critical: '#EF4444', // Red-500
  warning: '#F59E0B',  // Amber-500
  info: '#3B82F6',     // Blue-500
};

/**
 * Severity icon mapping
 */
export const SEVERITY_ICONS: Record<IssueSeverity, string> = {
  critical: '🔴',
  warning: '🟡',
  info: '🔵',
};

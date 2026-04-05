/**
 * Feed Quality Monitoring Types
 *
 * Types for combined quality metrics from Knowledge Graph service.
 */

import type { GraphIntegrityResult } from '../api/useGraphIntegrity';
import type { DisambiguationQualityResult } from '../api/useDisambiguationQuality';

/**
 * Combined feed quality metrics from all sources
 */
export interface FeedQualityMetrics {
  /** Graph integrity check results */
  graph_integrity: GraphIntegrityResult;
  /** Entity disambiguation quality results */
  disambiguation: DisambiguationQualityResult;
  /** Combined overall quality score (0-100) */
  overall_score: number;
  /** Timestamp of the last quality check */
  last_checked: string;
}

/**
 * Quality trend data point for historical analysis
 */
export interface QualityTrendPoint {
  timestamp: string;
  graph_quality_score: number;
  disambiguation_rate: number;
  overall_score: number;
}

/**
 * Quality alert threshold configuration
 */
export interface QualityAlertThreshold {
  metric: 'graph_quality' | 'disambiguation_rate' | 'orphaned_nodes' | 'broken_relationships';
  warning_threshold: number;
  error_threshold: number;
  enabled: boolean;
}

/**
 * Quality issue summary for dashboard display
 */
export interface QualityIssueSummary {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  count: number;
  first_detected: string;
  last_seen: string;
  resolved: boolean;
}

/**
 * Helper function to calculate overall quality score
 */
export const calculateOverallQualityScore = (
  graphScore: number,
  disambiguationRate: number
): number => {
  // Weighted average: graph integrity 60%, disambiguation 40%
  const graphWeight = 0.6;
  const disambiguationWeight = 0.4;

  // Disambiguation rate is 0-1, convert to 0-100
  const disambiguationScore = disambiguationRate * 100;

  return Math.round(graphScore * graphWeight + disambiguationScore * disambiguationWeight);
};

/**
 * Get quality status based on score
 */
export const getQualityStatus = (
  score: number
): { status: 'excellent' | 'good' | 'warning' | 'critical'; color: string; label: string } => {
  if (score >= 90) {
    return { status: 'excellent', color: 'green', label: 'Excellent' };
  }
  if (score >= 75) {
    return { status: 'good', color: 'blue', label: 'Good' };
  }
  if (score >= 50) {
    return { status: 'warning', color: 'yellow', label: 'Needs Attention' };
  }
  return { status: 'critical', color: 'red', label: 'Critical' };
};

/**
 * Get severity badge color class
 */
export const getSeverityColor = (severity: 'low' | 'medium' | 'high' | 'critical'): string => {
  const colors: Record<string, string> = {
    low: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };
  return colors[severity] || colors.low;
};

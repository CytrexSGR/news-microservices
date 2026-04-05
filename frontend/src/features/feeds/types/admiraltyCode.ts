/**
 * Admiralty Code Configuration Types
 *
 * Types for managing Admiralty Code thresholds and quality score weights.
 */

export interface AdmiraltyThreshold {
  id: string;
  code: 'A' | 'B' | 'C' | 'D' | 'E' | 'F';
  label: string;
  min_score: number;
  description: string;
  color: string;
  created_at: string;
  updated_at: string;
}

export interface AdmiraltyThresholdUpdate {
  min_score?: number;
  label?: string;
  description?: string;
  color?: string;
}

export interface QualityWeight {
  id: string;
  category: 'credibility' | 'editorial' | 'trust' | 'health';
  weight: string; // Decimal as string (e.g., "0.40")
  description: string;
  min_value: string;
  max_value: string;
  created_at: string;
  updated_at: string;
}

export interface QualityWeightUpdate {
  weight: number;
  description?: string;
}

export interface WeightValidation {
  is_valid: boolean;
  total: string;
  message: string;
}

export interface ConfigurationStatus {
  thresholds_count: number;
  weights_count: number;
  weights_valid: boolean;
  using_defaults: boolean;
}

/**
 * Escalation Types for Intelligence Interpretation Layer
 *
 * TypeScript types matching backend Pydantic schemas in clustering-service.
 * Used for escalation scoring across three domains (geopolitical, military, economic)
 * with FMP market regime correlation.
 *
 * @module features/intelligence/types/escalation
 */

// =============================================================================
// Base Types
// =============================================================================

/**
 * Market regime type from FMP service
 */
export type RegimeType = 'RISK_ON' | 'RISK_OFF' | 'TRANSITIONAL' | 'UNKNOWN';

/**
 * Correlation alert type between market regime and news escalation
 */
export type AlertType = 'CONFIRMATION' | 'DIVERGENCE' | 'EARLY_WARNING';

/**
 * Escalation level (1-5 scale)
 * 1: Routine, 2: Elevated, 3: Significant, 4: High, 5: Critical
 */
export type EscalationLevel = 1 | 2 | 3 | 4 | 5;

/**
 * Domain for escalation scoring
 */
export type EscalationDomain = 'geopolitical' | 'military' | 'economic';

// =============================================================================
// Core Interfaces
// =============================================================================

/**
 * Current market regime status from FMP
 */
export interface RegimeStatus {
  /** Current regime type */
  type: RegimeType;
  /** Regime confidence/strength score (0-1) */
  score: number;
  /** ISO timestamp when this regime started */
  since?: string;
}

/**
 * Financial market indicators from FMP
 */
export interface FinanceIndicators {
  /** VIX volatility index value */
  vix: number | null;
  /** VIX change from previous period */
  vixChange: number | null;
  /** US Dollar Index */
  dxy: number | null;
  /** Yield spread (10Y-2Y) */
  yieldSpread: number | null;
  /** Carry trade indicator */
  carryTrade: number | null;
}

/**
 * Regional escalation heatmap data
 */
export interface RegionHeatmap {
  /** Region name (e.g., "Middle East", "Europe") */
  region: string;
  /** Geopolitical escalation score (0-1) */
  geopolitical: number;
  /** Military escalation score (0-1) */
  military: number;
  /** Economic escalation score (0-1) */
  economic: number;
}

/**
 * Correlation alert between market and news signals
 */
export interface CorrelationAlert {
  /** Alert type */
  type: AlertType;
  /** Human-readable alert message */
  message: string;
  /** ISO timestamp when alert was generated */
  timestamp: string;
  /** Alert confidence (0-1) */
  confidence: number;
  /** Related cluster ID if applicable */
  clusterId?: string;
}

// =============================================================================
// API Response Interfaces
// =============================================================================

/**
 * Escalation summary response from /escalation/summary endpoint
 */
export interface EscalationSummary {
  /** Current market regime status */
  regime: RegimeStatus;
  /** Financial market indicators */
  finance: FinanceIndicators;
  /** Regional escalation heatmap */
  heatmap: RegionHeatmap[];
  /** Active correlation alerts */
  alerts: CorrelationAlert[];
}

/**
 * Signal breakdown by source type
 */
export interface EscalationSignals {
  /** Embedding similarity signals per domain */
  embedding: Record<string, { score: number; level?: number; anchor_id?: string }>;
  /** Content analysis signals per domain */
  content: Record<string, { score: number }>;
  /** Keyword heuristic signals per domain */
  keywords: Record<string, { score: number }>;
}

/**
 * Detailed escalation data for a single cluster
 * Response from /escalation/clusters/{id} endpoint
 */
export interface ClusterEscalation {
  /** Cluster UUID */
  clusterId: string;
  /** Geopolitical escalation score (0-1) */
  geopolitical: number;
  /** Military escalation score (0-1) */
  military: number;
  /** Economic escalation score (0-1) */
  economic: number;
  /** Combined weighted score (0-1) */
  combined: number;
  /** Escalation level (1-5) */
  level: EscalationLevel;
  /** Signal breakdown by source */
  signals: EscalationSignals;
  /** FMP market correlation data */
  fmpCorrelation: {
    alertType: AlertType | null;
    message: string | null;
    regimeAtTime: string | null;
    confidence: number | null;
  } | null;
  /** ISO timestamp when escalation was calculated */
  calculatedAt: string | null;
}

// =============================================================================
// UI Helper Constants
// =============================================================================

/**
 * Escalation level metadata for UI rendering
 */
export const ESCALATION_LEVELS: Record<
  EscalationLevel,
  { label: string; color: string; bgColor: string; description: string }
> = {
  1: {
    label: 'Routine',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    description: 'Normal activity levels',
  },
  2: {
    label: 'Elevated',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    description: 'Increased monitoring recommended',
  },
  3: {
    label: 'Significant',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
    description: 'Notable developments requiring attention',
  },
  4: {
    label: 'High',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    description: 'Critical situation developing',
  },
  5: {
    label: 'Critical',
    color: 'text-gray-100',
    bgColor: 'bg-gray-800',
    description: 'Maximum alert - immediate attention required',
  },
};

/**
 * Regime type colors for UI rendering
 */
export const REGIME_COLORS: Record<RegimeType, string> = {
  RISK_ON: 'bg-green-500',
  RISK_OFF: 'bg-red-500',
  TRANSITIONAL: 'bg-yellow-500',
  UNKNOWN: 'bg-gray-400',
};

/**
 * Alert type colors for UI rendering
 */
export const ALERT_TYPE_COLORS: Record<AlertType, { bg: string; text: string; border: string }> = {
  CONFIRMATION: {
    bg: 'bg-green-50',
    text: 'text-green-700',
    border: 'border-green-200',
  },
  DIVERGENCE: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-200',
  },
  EARLY_WARNING: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
  },
};

// =============================================================================
// UI Helper Functions
// =============================================================================

/**
 * Get escalation level metadata
 *
 * @param level - Escalation level (1-5)
 * @returns Level metadata with label, colors, and description
 */
export function getEscalationLevelInfo(level: EscalationLevel) {
  return ESCALATION_LEVELS[level] || ESCALATION_LEVELS[1];
}

/**
 * Convert score (0-1) to escalation level (1-5)
 *
 * @param score - Combined score from 0 to 1
 * @returns Escalation level from 1 to 5
 */
export function scoreToLevel(score: number): EscalationLevel {
  if (score < 0.2) return 1;
  if (score < 0.4) return 2;
  if (score < 0.6) return 3;
  if (score < 0.8) return 4;
  return 5;
}

/**
 * Get regime display information
 *
 * @param type - Regime type
 * @returns Object with label and color
 */
export function getRegimeInfo(type: RegimeType): { label: string; color: string; description: string } {
  const info: Record<RegimeType, { label: string; color: string; description: string }> = {
    RISK_ON: {
      label: 'Risk On',
      color: REGIME_COLORS.RISK_ON,
      description: 'Markets show appetite for risk assets',
    },
    RISK_OFF: {
      label: 'Risk Off',
      color: REGIME_COLORS.RISK_OFF,
      description: 'Flight to safety - defensive positioning',
    },
    TRANSITIONAL: {
      label: 'Transitional',
      color: REGIME_COLORS.TRANSITIONAL,
      description: 'Market regime uncertain - watch for signals',
    },
    UNKNOWN: {
      label: 'Unknown',
      color: REGIME_COLORS.UNKNOWN,
      description: 'No market data available',
    },
  };
  return info[type] || info.UNKNOWN;
}

/**
 * Get alert type display information
 *
 * @param type - Alert type
 * @returns Object with label, colors, and description
 */
export function getAlertTypeInfo(type: AlertType): {
  label: string;
  colors: { bg: string; text: string; border: string };
  description: string;
} {
  const info: Record<
    AlertType,
    { label: string; colors: { bg: string; text: string; border: string }; description: string }
  > = {
    CONFIRMATION: {
      label: 'Confirmation',
      colors: ALERT_TYPE_COLORS.CONFIRMATION,
      description: 'Market regime aligns with news escalation',
    },
    DIVERGENCE: {
      label: 'Divergence',
      colors: ALERT_TYPE_COLORS.DIVERGENCE,
      description: 'Market and news signals conflict - investigate',
    },
    EARLY_WARNING: {
      label: 'Early Warning',
      colors: ALERT_TYPE_COLORS.EARLY_WARNING,
      description: 'Market may be leading news signals',
    },
  };
  return info[type];
}

/**
 * Format escalation score as percentage string
 *
 * @param score - Score from 0 to 1
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "45.2%")
 */
export function formatEscalationScore(score: number, decimals: number = 1): string {
  return `${(score * 100).toFixed(decimals)}%`;
}

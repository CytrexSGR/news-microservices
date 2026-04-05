/**
 * Types for Data Management feature
 *
 * Unified Market Data Architecture - Frontend Types
 */

// ============================================================================
// Symbol Types
// ============================================================================

export interface SymbolInfo {
  internal: string;
  fmp: string;
  bybit: string;
  name: string;           // API returns 'name' not 'display'
  rank?: number;          // API returns 'rank'
  // Legacy fields (may be present in some responses)
  display?: string;
  base?: string;
  quote?: string;
  asset_class?: 'crypto' | 'stock' | 'forex';
}

// ============================================================================
// Data Inventory Types
// ============================================================================

export type CandleInterval = '1min' | '5min' | '15min' | '30min' | '1hour' | '4hour' | '1day';
export type DataSource = 'fmp' | 'bybit' | 'manual';

export interface TimeframeStats {
  interval: CandleInterval;
  count: number;
  first_timestamp: string | null;
  last_timestamp: string | null;
  sources: DataSource[];
}

export interface SymbolInventory {
  symbol: string;
  display_name: string;
  asset_type: string;
  total_candles: number;
  timeframes: TimeframeStats[];
  first_data: string | null;
  last_data: string | null;
  gaps_detected: number;
  sources: DataSource[];
}

export interface InventoryResponse {
  symbols: SymbolInventory[];
  total_symbols: number;
  total_candles: number;
  last_updated: string;
}

// ============================================================================
// Gap Detection Types
// ============================================================================

export interface DataGap {
  start: string;
  end: string;
  missing_candles?: number;
  missing_candles_estimated?: number;  // Backend may return this instead
  duration_hours: number;
}

export interface GapsResponse {
  symbol: string;
  interval?: CandleInterval;
  timeframe?: string;  // Backend returns 'timeframe' not 'interval'
  gaps: DataGap[];
  total_gaps: number;
  total_missing_candles?: number;
  total_missing_hours?: number;  // Backend returns this
  analyzed_from?: string;
  analyzed_to?: string;
  start_date?: string;  // Backend returns these
  end_date?: string;
}

// ============================================================================
// Backfill Types
// ============================================================================

export type BackfillStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type BackfillSource = 'fmp' | 'bybit' | 'auto';

export interface BackfillRequest {
  symbol: string;
  interval: CandleInterval;
  start_date: string;
  end_date: string;
  source?: BackfillSource;
}

export interface BackfillJob {
  job_id: string;
  symbol: string;
  interval: CandleInterval;
  status: BackfillStatus;
  source: BackfillSource;
  start_date: string;
  end_date: string;
  started_at: string | null;
  completed_at: string | null;
  candles_fetched: number;
  candles_inserted: number;
  progress_percent: number;
  error: string | null;
}

export interface BackfillResponse {
  job_id: string;
  status: BackfillStatus;
  message: string;
}

export interface FillGapsRequest {
  symbol: string;
  interval: CandleInterval;
  start_date: string;
  end_date: string;
}

export interface FillGapsResponse {
  jobs_created: number;
  jobs: BackfillJob[];
  message: string;
}

// ============================================================================
// OHLCV Data Types
// ============================================================================

export interface OHLCVCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: DataSource;
}

export interface OHLCVResponse {
  symbol: string;
  interval: CandleInterval;
  data: OHLCVCandle[];
  count: number;
  from: string;
  to: string;
  source: DataSource | 'mixed';
}

// ============================================================================
// Data Availability Types
// ============================================================================

export interface AvailabilityCheck {
  symbol: string;
  interval: CandleInterval;
  start_date: string;
  end_date: string;
}

export interface AvailabilityResult {
  symbol: string;
  interval: CandleInterval;
  requested_from: string;
  requested_to: string;
  available: boolean;
  available_from: string | null;
  available_to: string | null;
  coverage_percent: number;
  missing_ranges: DataGap[];
  recommendation: 'ready' | 'partial' | 'backfill_required';
}

export interface AvailabilityResponse {
  results: AvailabilityResult[];
  all_available: boolean;
}

// ============================================================================
// Health Types
// ============================================================================

export interface DataManagementHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database_connected: boolean;
  sync_worker_running: boolean;
  last_sync: string | null;
  syncs_completed: number;
  errors_last_hour: number;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface DataManagementFilters {
  symbol?: string;
  interval?: CandleInterval;
  source?: DataSource;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface BackfillFormData {
  symbols: string[];
  interval: CandleInterval;
  startDate: string;
  endDate: string;
  source: BackfillSource;
}

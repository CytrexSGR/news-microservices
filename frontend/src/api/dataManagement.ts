/**
 * Data Management API Client
 *
 * Unified Market Data Architecture - API functions for data inventory,
 * backfilling, and OHLCV data retrieval from FMP service.
 */

import axios from 'axios';
import { useAuthStore } from '@/store/authStore';
import type {
  InventoryResponse,
  SymbolInventory,
  GapsResponse,
  BackfillRequest,
  BackfillResponse,
  BackfillJob,
  FillGapsRequest,
  FillGapsResponse,
  OHLCVResponse,
  AvailabilityCheck,
  AvailabilityResponse,
  DataManagementHealth,
  CandleInterval,
  SymbolInfo,
} from '@/types/data-management';

// Create axios instance for FMP service (data management)
// Note: FMP service runs on port 8113 in host network mode
// VITE_FMP_API_URL already includes /api/v1 suffix, so paths should NOT include it
const fmpApi = axios.create({
  baseURL: import.meta.env.VITE_FMP_API_URL || 'http://localhost:8113/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
fmpApi.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ============================================================================
// Data Inventory API
// ============================================================================

/**
 * Get data inventory for all symbols
 */
export async function getDataInventory(): Promise<InventoryResponse> {
  const response = await fmpApi.get<InventoryResponse>('/data-management/inventory');
  return response.data;
}

/**
 * Get data inventory for a specific symbol
 */
export async function getSymbolInventory(symbol: string): Promise<SymbolInventory> {
  const response = await fmpApi.get<SymbolInventory>(`/data-management/inventory/${symbol}`);
  return response.data;
}

/**
 * Get list of supported symbols
 */
export async function getSupportedSymbols(): Promise<SymbolInfo[]> {
  const response = await fmpApi.get<{ symbols: SymbolInfo[] }>('/data-management/symbols');
  return response.data.symbols;
}

// ============================================================================
// Gap Detection API
// ============================================================================

/**
 * Detect gaps in data for a symbol and interval
 */
export async function detectGaps(
  symbol: string,
  interval: CandleInterval,
  startDate?: string,
  endDate?: string
): Promise<GapsResponse> {
  const params = new URLSearchParams();
  params.append('interval', interval);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await fmpApi.get<GapsResponse>(
    `/data-management/gaps/${symbol}?${params.toString()}`
  );
  return response.data;
}

// ============================================================================
// Backfill API
// ============================================================================

/**
 * Start a backfill job for a symbol
 */
export async function startBackfill(request: BackfillRequest): Promise<BackfillResponse> {
  const response = await fmpApi.post<BackfillResponse>(
    '/data-management/backfill',
    request
  );
  return response.data;
}

/**
 * Auto-fill detected gaps for a symbol
 */
export async function fillGaps(request: FillGapsRequest): Promise<FillGapsResponse> {
  const response = await fmpApi.post<FillGapsResponse>(
    '/data-management/backfill/fill-gaps',
    request
  );
  return response.data;
}

/**
 * Get list of active backfill jobs
 */
export async function getBackfillJobs(): Promise<BackfillJob[]> {
  const response = await fmpApi.get<{ jobs: BackfillJob[] }>(
    '/data-management/backfill/jobs'
  );
  return response.data.jobs;
}

/**
 * Get status of a specific backfill job
 */
export async function getBackfillJobStatus(jobId: string): Promise<BackfillJob> {
  const response = await fmpApi.get<BackfillJob>(
    `/data-management/backfill/jobs/${jobId}`
  );
  return response.data;
}

// ============================================================================
// OHLCV Data API
// ============================================================================

/**
 * Get OHLCV data for a symbol
 */
export async function getOHLCVData(
  symbol: string,
  interval: CandleInterval,
  startDate?: string,
  endDate?: string,
  limit?: number
): Promise<OHLCVResponse> {
  const params = new URLSearchParams();
  params.append('interval', interval);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (limit) params.append('limit', limit.toString());

  const response = await fmpApi.get<OHLCVResponse>(
    `/data-management/ohlcv/${symbol}?${params.toString()}`
  );
  return response.data;
}

// ============================================================================
// Data Availability API
// ============================================================================

/**
 * Check data availability for multiple symbol/interval combinations
 */
export async function checkAvailability(
  checks: AvailabilityCheck[]
): Promise<AvailabilityResponse> {
  const response = await fmpApi.post<AvailabilityResponse>(
    '/data-management/availability',
    { checks }
  );
  return response.data;
}

/**
 * Check data availability for a single symbol
 */
export async function checkSymbolAvailability(
  symbol: string,
  interval: CandleInterval,
  startDate: string,
  endDate: string
): Promise<AvailabilityResponse> {
  return checkAvailability([
    {
      symbol,
      interval,
      start_date: startDate,
      end_date: endDate,
    },
  ]);
}

// ============================================================================
// Health API
// ============================================================================

/**
 * Get data management health status
 */
export async function getDataManagementHealth(): Promise<DataManagementHealth> {
  const response = await fmpApi.get<DataManagementHealth>(
    '/data-management/health'
  );
  return response.data;
}

// ============================================================================
// Export
// ============================================================================

export const dataManagementApi = {
  // Inventory
  getDataInventory,
  getSymbolInventory,
  getSupportedSymbols,
  // Gaps
  detectGaps,
  // Backfill
  startBackfill,
  fillGaps,
  getBackfillJobs,
  getBackfillJobStatus,
  // OHLCV
  getOHLCVData,
  // Availability
  checkAvailability,
  checkSymbolAvailability,
  // Health
  getDataManagementHealth,
};

export default dataManagementApi;

/**
 * React Query Hooks for Data Management
 *
 * Unified Market Data Architecture - hooks for data inventory,
 * backfilling, gap detection, and OHLCV data retrieval.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataManagementApi } from '@/api/dataManagement';
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

// ============================================================================
// Query Keys
// ============================================================================

export const dataManagementKeys = {
  all: ['data-management'] as const,
  inventory: () => [...dataManagementKeys.all, 'inventory'] as const,
  symbolInventory: (symbol: string) => [...dataManagementKeys.inventory(), symbol] as const,
  symbols: () => [...dataManagementKeys.all, 'symbols'] as const,
  gaps: (symbol: string, interval: CandleInterval) =>
    [...dataManagementKeys.all, 'gaps', symbol, interval] as const,
  backfillJobs: () => [...dataManagementKeys.all, 'backfill-jobs'] as const,
  backfillJob: (jobId: string) => [...dataManagementKeys.backfillJobs(), jobId] as const,
  ohlcv: (symbol: string, interval: CandleInterval) =>
    [...dataManagementKeys.all, 'ohlcv', symbol, interval] as const,
  availability: () => [...dataManagementKeys.all, 'availability'] as const,
  health: () => [...dataManagementKeys.all, 'health'] as const,
};

// ============================================================================
// Inventory Hooks
// ============================================================================

/**
 * Hook to fetch data inventory for all symbols
 */
export function useDataInventory() {
  return useQuery<InventoryResponse, Error>({
    queryKey: dataManagementKeys.inventory(),
    queryFn: dataManagementApi.getDataInventory,
    staleTime: 30_000, // 30 seconds
    refetchInterval: 60_000, // Auto-refresh every minute
  });
}

/**
 * Hook to fetch data inventory for a specific symbol
 */
export function useSymbolInventory(symbol: string) {
  return useQuery<SymbolInventory, Error>({
    queryKey: dataManagementKeys.symbolInventory(symbol),
    queryFn: () => dataManagementApi.getSymbolInventory(symbol),
    enabled: !!symbol,
    staleTime: 30_000,
  });
}

/**
 * Hook to fetch supported symbols
 */
export function useSupportedSymbols() {
  return useQuery<SymbolInfo[], Error>({
    queryKey: dataManagementKeys.symbols(),
    queryFn: dataManagementApi.getSupportedSymbols,
    staleTime: 5 * 60_000, // 5 minutes - symbols don't change often
  });
}

// ============================================================================
// Gap Detection Hooks
// ============================================================================

/**
 * Hook to detect data gaps for a symbol
 */
export function useDataGaps(
  symbol: string,
  interval: CandleInterval,
  startDate?: string,
  endDate?: string
) {
  return useQuery<GapsResponse, Error>({
    queryKey: [...dataManagementKeys.gaps(symbol, interval), startDate, endDate],
    queryFn: () => dataManagementApi.detectGaps(symbol, interval, startDate, endDate),
    enabled: !!symbol && !!interval,
    staleTime: 60_000, // 1 minute
  });
}

// ============================================================================
// Backfill Hooks
// ============================================================================

/**
 * Hook to fetch active backfill jobs
 */
export function useBackfillJobs() {
  return useQuery<BackfillJob[], Error>({
    queryKey: dataManagementKeys.backfillJobs(),
    queryFn: dataManagementApi.getBackfillJobs,
    refetchInterval: 5_000, // Poll every 5 seconds for active jobs
  });
}

/**
 * Hook to start a backfill job
 */
export function useStartBackfill() {
  const queryClient = useQueryClient();

  return useMutation<BackfillResponse, Error, BackfillRequest>({
    mutationFn: dataManagementApi.startBackfill,
    onSuccess: () => {
      // Invalidate backfill jobs to show the new job
      queryClient.invalidateQueries({ queryKey: dataManagementKeys.backfillJobs() });
    },
  });
}

/**
 * Hook to auto-fill detected gaps
 */
export function useFillGaps() {
  const queryClient = useQueryClient();

  return useMutation<FillGapsResponse, Error, FillGapsRequest>({
    mutationFn: dataManagementApi.fillGaps,
    onSuccess: (_, variables) => {
      // Invalidate backfill jobs and gaps for the symbol
      queryClient.invalidateQueries({ queryKey: dataManagementKeys.backfillJobs() });
      queryClient.invalidateQueries({
        queryKey: dataManagementKeys.gaps(variables.symbol, variables.interval),
      });
    },
  });
}

// ============================================================================
// OHLCV Data Hooks
// ============================================================================

/**
 * Hook to fetch OHLCV data
 */
export function useOHLCVData(
  symbol: string,
  interval: CandleInterval,
  startDate?: string,
  endDate?: string,
  limit?: number,
  enabled = true
) {
  return useQuery<OHLCVResponse, Error>({
    queryKey: [...dataManagementKeys.ohlcv(symbol, interval), startDate, endDate, limit],
    queryFn: () => dataManagementApi.getOHLCVData(symbol, interval, startDate, endDate, limit),
    enabled: enabled && !!symbol && !!interval,
    staleTime: 60_000, // 1 minute
  });
}

// ============================================================================
// Availability Hooks
// ============================================================================

/**
 * Hook to check data availability
 */
export function useDataAvailability(checks: AvailabilityCheck[], enabled = true) {
  return useQuery<AvailabilityResponse, Error>({
    queryKey: [...dataManagementKeys.availability(), checks],
    queryFn: () => dataManagementApi.checkAvailability(checks),
    enabled: enabled && checks.length > 0,
    staleTime: 30_000,
  });
}

/**
 * Hook to check availability for a single symbol
 */
export function useSymbolAvailability(
  symbol: string,
  interval: CandleInterval,
  startDate: string,
  endDate: string,
  enabled = true
) {
  return useDataAvailability(
    [{ symbol, interval, start_date: startDate, end_date: endDate }],
    enabled && !!symbol && !!interval && !!startDate && !!endDate
  );
}

// ============================================================================
// Health Hooks
// ============================================================================

/**
 * Hook to fetch data management health status
 */
export function useDataManagementHealth() {
  return useQuery<DataManagementHealth, Error>({
    queryKey: dataManagementKeys.health(),
    queryFn: dataManagementApi.getDataManagementHealth,
    refetchInterval: 30_000, // Poll every 30 seconds
  });
}

// ============================================================================
// Export
// ============================================================================

export {
  // Types re-exported for convenience
  type InventoryResponse,
  type SymbolInventory,
  type GapsResponse,
  type BackfillRequest,
  type BackfillResponse,
  type BackfillJob,
  type FillGapsRequest,
  type FillGapsResponse,
  type OHLCVResponse,
  type AvailabilityCheck,
  type AvailabilityResponse,
  type DataManagementHealth,
  type CandleInterval,
  type SymbolInfo,
};

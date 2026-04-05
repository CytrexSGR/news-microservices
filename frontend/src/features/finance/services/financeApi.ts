/**
 * Finance Terminal API Client
 *
 * Handles communication with FMP service for:
 * - Real-time market quotes
 * - Market hours status
 * - System health monitoring
 * - Symbol search
 * - Historical OHLCV data
 */

import type {
  Quote,
  MarketStatusResponse,
  OHLCVCandle,
  CandleInterval,
} from '../types/market.types';
import type { SystemHealth, ErrorLogEntry } from '../types/system.types';

const FMP_SERVICE_URL = import.meta.env.VITE_FMP_API_URL?.replace('/api/v1', '') || 'http://localhost:8113';

/**
 * API Response wrapper
 */
interface ApiResponse<T> {
  data?: T;
  error?: string;
}

/**
 * Fetch helper with error handling
 */
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${FMP_SERVICE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return { error: `HTTP ${response.status}: ${errorText}` };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Get bulk quotes for all symbols or specific asset types
 */
export async function getBulkQuotes(assetType?: string): Promise<ApiResponse<Quote[]>> {
  const params = assetType ? `?asset_type=${assetType}` : '';
  return fetchApi<Quote[]>(`/api/v1/market/quotes${params}`);
}

/**
 * Get quote for a single symbol
 */
export async function getQuote(symbol: string): Promise<ApiResponse<Quote>> {
  return fetchApi<Quote>(`/api/v1/market/quotes/${symbol}`);
}

/**
 * Get market hours status for all asset types
 */
export async function getMarketStatus(): Promise<ApiResponse<MarketStatusResponse>> {
  return fetchApi<MarketStatusResponse>('/api/v1/market/status');
}

/**
 * Get OHLCV candlestick data for a symbol
 */
export async function getOHLCVData(
  symbol: string,
  interval: CandleInterval = '1min',
  limit: number = 100
): Promise<ApiResponse<OHLCVCandle[]>> {
  return fetchApi<OHLCVCandle[]>(
    `/api/v1/market/ohlcv/${symbol}?interval=${interval}&limit=${limit}`
  );
}

/**
 * Search symbols by name or symbol
 */
export async function searchSymbols(query: string): Promise<ApiResponse<Quote[]>> {
  return fetchApi<Quote[]>(`/api/v1/market/symbols/search?q=${encodeURIComponent(query)}`);
}

/**
 * Get system health metrics
 */
export async function getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
  return fetchApi<SystemHealth>('/api/v1/system/health');
}

/**
 * Get API call statistics
 */
export async function getApiCallStats(
  timeframe: '24h' | '7d' | '30d' = '24h'
): Promise<ApiResponse<{ timestamp: string; count: number }[]>> {
  return fetchApi(`/api/v1/system/metrics/api-calls?timeframe=${timeframe}`);
}

/**
 * Get recent error logs
 */
export async function getErrorLogs(limit: number = 50): Promise<ApiResponse<ErrorLogEntry[]>> {
  return fetchApi<ErrorLogEntry[]>(`/api/v1/system/errors?limit=${limit}`);
}

/**
 * Get symbols by tier
 */
export async function getSymbolsByTier(tier: 1 | 2 | 3): Promise<ApiResponse<Quote[]>> {
  return fetchApi<Quote[]>(`/api/v1/market/symbols/tier/${tier}`);
}

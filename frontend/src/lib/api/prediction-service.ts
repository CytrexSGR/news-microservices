/**
 * Prediction Service API Client
 *
 * Provides access to:
 * - Real-time indicators (RSI, MACD, EMA200, Volume)
 * - Historical OHLCV data (via BybitMarketData)
 * - Trading signals and strategies
 */

import axios from 'axios'
import type { AxiosInstance } from 'axios'
import type { OHLCV } from '@/types/market'
import type { IndicatorsSnapshot, HistoricalIndicator } from '@/types/indicators'
import type { StrategyEvaluationResponse } from '@/types/strategy-evaluation'
import { toBybitSymbol } from '@/constants/symbols'

/**
 * API Configuration
 * Uses Vite proxy: /api/prediction -> localhost:8116
 */
const API_CONFIG = {
  baseURL: '/api/prediction/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
}

/**
 * Prediction Service API Client
 */
class PredictionServiceClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create(API_CONFIG)
  }

  /**
   * Get current technical indicators for a symbol
   *
   * @param symbol Frontend symbol (e.g., "BTCUSDT")
   * @param timeframe Indicator timeframe (15m, 1h, 4h, 1d) - defaults to 1h
   * @param comprehensive Include comprehensive regime details (defaults to true)
   * @returns Current indicators snapshot
   */
  async getIndicators(
    symbol: string,
    timeframe: '15m' | '1h' | '4h' | '1d' = '1h',
    comprehensive: boolean = true
  ): Promise<IndicatorsSnapshot> {
    const bybitSymbol = toBybitSymbol(symbol)
    const encodedSymbol = encodeURIComponent(bybitSymbol)
    const response = await this.client.get<IndicatorsSnapshot>(
      `/indicators/${encodedSymbol}/current?timeframe=${timeframe}&comprehensive=${comprehensive}`
    )
    return response.data
  }

  /**
   * Get historical indicators (24h)
   *
   * @param symbol Frontend symbol (e.g., "BTCUSDT")
   * @param hours Number of hours (default: 24)
   * @returns Array of historical indicator data points
   */
  async getHistoricalIndicators(symbol: string, hours: number = 24): Promise<HistoricalIndicator[]> {
    const bybitSymbol = toBybitSymbol(symbol)
    const encodedSymbol = encodeURIComponent(bybitSymbol)
    const response = await this.client.get<HistoricalIndicator[]>(
      `/indicators/${encodedSymbol}/historical?hours=${hours}`
    )
    return response.data
  }

  /**
   * Get available symbols
   *
   * @returns Array of Bybit symbols (e.g., ["BTC/USDT:USDT", "ETH/USDT:USDT"])
   */
  async getAvailableSymbols(): Promise<string[]> {
    const response = await this.client.get<string[]>('/indicators/symbols')
    return response.data
  }

  /**
   * Get OHLCV data (candlesticks)
   *
   * @param symbol Frontend symbol (e.g., "BTCUSDT")
   * @param timeframe Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
   * @param limit Number of candles (default: 300, max: 1000)
   * @param since Optional Unix timestamp in milliseconds to start from
   * @returns OHLCV data
   */
  async getOHLCV(
    symbol: string,
    timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' = '1h',
    limit: number = 300,
    since?: number
  ): Promise<OHLCV[]> {
    const bybitSymbol = toBybitSymbol(symbol)
    const params = new URLSearchParams({
      symbol: bybitSymbol,
      timeframe,
      limit: limit.toString(),
    })

    if (since) {
      params.append('since', since.toString())
    }

    const response = await this.client.get<number[][]>(
      `/market-data/ohlcv?${params.toString()}`
    )

    // Convert CCXT format to our OHLCV type
    return this.convertCCXTtoOHLCV(response.data)
  }

  /**
   * Evaluate strategy entry/exit conditions
   *
   * @param strategyId Strategy UUID
   * @param symbol Frontend symbol (e.g., "BTCUSDT")
   * @param timeframe Evaluation timeframe (default: "1h")
   * @returns Strategy evaluation results with entry/exit analysis
   */
  async evaluateStrategy(
    strategyId: string,
    symbol: string,
    timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' = '1h'
  ): Promise<StrategyEvaluationResponse> {
    const bybitSymbol = toBybitSymbol(symbol)
    const response = await this.client.get<StrategyEvaluationResponse>(
      `/strategies/${strategyId}/evaluate`,
      {
        params: {
          symbol: bybitSymbol,
          timeframe,
        },
      }
    )
    return response.data
  }

  /**
   * Convert CCXT OHLCV format to our OHLCV type
   *
   * CCXT format: [timestamp, open, high, low, close, volume]
   * Our format: { timestamp, open, high, low, close, volume }
   *
   * @param ccxtCandles CCXT format candles
   * @returns Our OHLCV format
   */
  private convertCCXTtoOHLCV(ccxtCandles: number[][]): OHLCV[] {
    return ccxtCandles.map((candle) => ({
      timestamp: new Date(candle[0]).toISOString(),
      open: candle[1],
      high: candle[2],
      low: candle[3],
      close: candle[4],
      volume: candle[5],
    }))
  }
}

/**
 * Singleton instance
 */
export const predictionService = new PredictionServiceClient()

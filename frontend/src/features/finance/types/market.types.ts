/**
 * Market Data Types for Finance Terminal
 */

export type AssetType = 'crypto' | 'forex' | 'indices' | 'commodities';

export type MarketStatus = 'open' | 'closed' | 'pre_market' | 'after_hours';

export interface Quote {
  symbol: string;
  name?: string;
  asset_type: AssetType;
  price: number;
  bid?: number | null;
  ask?: number | null;
  volume?: number | null;
  change?: number | null;
  change_percent?: number | null;
  day_high?: number | null;
  day_low?: number | null;
  day_open?: number | null;
  prev_close?: number | null;
  timestamp: string;
}

export interface MarketHoursStatus {
  status: MarketStatus;
  reason: string;
  next_open?: string;
  next_close?: string;
}

export interface MarketStatusResponse {
  timestamp: string;
  crypto: MarketHoursStatus;
  forex: MarketHoursStatus;
  indices: MarketHoursStatus;
  commodities: MarketHoursStatus;
}

export interface OHLCVCandle {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
}

export interface APIMetrics {
  timestamp: string;
  calls: number;
}

export interface APISavings {
  total_calls: number;
  estimated_calls_without_market_hours: number;
  savings: number;
  savings_percent: number;
}

export type CandleInterval = '1min' | '5min' | '15min' | '1h' | '1d';

export type TechnicalIndicator = 'ma50' | 'ma200' | 'rsi' | 'macd';

export interface ChartConfig {
  symbol: string;
  interval: CandleInterval;
  indicators: Set<TechnicalIndicator>;
  compareSymbols: string[];
}

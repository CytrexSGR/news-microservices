/**
 * Formatting utilities for trading indicators
 *
 * Provides consistent number formatting across the trading dashboard.
 */

/**
 * Format currency with symbol and thousands separators
 *
 * @example formatCurrency(85754.2) // "$85,754.20"
 */
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format percentage with 2 decimal places
 *
 * @example formatPercent(0.5) // "50.00%"
 */
export const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(2)}%`;
};

/**
 * Format decimal number with specified precision
 *
 * @example formatDecimal(1.32277797, 2) // "1.32"
 */
export const formatDecimal = (value: number, decimals: number = 2): string => {
  return value.toFixed(decimals);
};

/**
 * Format large numbers with K/M/B suffixes
 *
 * @example formatCompact(1234567) // "1.23M"
 */
export const formatCompact = (value: number): string => {
  if (Math.abs(value) < 1000) {
    return value.toFixed(2);
  }

  const units = ['', 'K', 'M', 'B', 'T'];
  const order = Math.floor(Math.log10(Math.abs(value)) / 3);
  const unitValue = value / Math.pow(10, order * 3);

  return `${unitValue.toFixed(2)}${units[order]}`;
};

/**
 * Format RSI value with color indication
 *
 * @example formatRSI(29.1) // "29.10"
 */
export const formatRSI = (value: number): string => {
  return value.toFixed(2);
};

/**
 * Format MACD histogram with +/- sign
 *
 * @example formatMACDHistogram(-95.2) // "-95.20"
 */
export const formatMACDHistogram = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
};

/**
 * Get trend direction from MACD histogram
 */
export const getMACDTrend = (histogram: number): 'up' | 'down' | 'neutral' => {
  if (histogram > 0) return 'up';
  if (histogram < 0) return 'down';
  return 'neutral';
};

/**
 * Get trend direction from EMA position
 */
export const getEMATrend = (position: 'ABOVE' | 'BELOW'): 'up' | 'down' => {
  return position === 'ABOVE' ? 'up' : 'down';
};

/**
 * Get trend direction from Volume ratio
 */
export const getVolumeTrend = (ratio: number): 'up' | 'down' | 'neutral' => {
  if (ratio > 1.5) return 'up';
  if (ratio < 0.5) return 'down';
  return 'neutral';
};

/**
 * Format symbol for display (remove exchange suffix)
 *
 * @example formatSymbol("BTC/USDT:USDT") // "BTC/USDT"
 */
export const formatSymbol = (symbol: string): string => {
  return symbol.split(':')[0];
};

/**
 * Format volume with thousands separators (no decimals)
 *
 * @example formatVolume(21687812) // "21,687,812"
 */
export const formatVolume = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

/**
 * Format price with consistent 2 decimal places and $ symbol
 * Used for all price displays in trading UI
 *
 * @example formatPrice(91926.4) // "$91,926.40"
 */
export const formatPrice = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format indicator value based on indicator type
 * Ensures consistent formatting across all strategy displays
 *
 * @param name - Indicator name (e.g., "1H_EMA_50", "1H_RSI_14")
 * @param value - Indicator value
 * @returns Formatted string
 */
export const formatIndicatorValue = (name: string, value: number): string => {
  const upperName = name.toUpperCase();

  // Price indicators: $98,234.50 (always 2 decimals)
  if (upperName.includes('PRICE') || upperName.includes('EMA') || upperName.includes('SMA') ||
      upperName.includes('BB') || upperName.includes('KELTNER') || upperName === 'CLOSE' ||
      upperName === 'OPEN' || upperName === 'HIGH' || upperName === 'LOW') {
    return formatPrice(value);
  }

  // Percentage indicators: 72.40%
  if (upperName.includes('PERCENT') || upperName.includes('PCT') || upperName.includes('CHANGE')) {
    return `${value.toFixed(2)}%`;
  }

  // RSI, ADX, MFI: 72.40 (2 decimals)
  if (upperName.includes('RSI') || upperName.includes('ADX') || upperName.includes('DI') ||
      upperName.includes('MFI') || upperName.includes('STOCH')) {
    return value.toFixed(2);
  }

  // ATR, volatility measures: 123.45 (2 decimals)
  if (upperName.includes('ATR') || upperName.includes('VOLATILITY') || upperName.includes('STDEV')) {
    return value.toFixed(2);
  }

  // BBW (Bollinger Band Width): 0.0414 (4 decimals for small ratios)
  if (upperName.includes('BBW')) {
    return value.toFixed(4);
  }

  // Volume: 21,687,812 (no decimals, with separators)
  if (upperName.includes('VOLUME') && !upperName.includes('SMA')) {
    return formatVolume(value);
  }

  // Volume SMA: formatted as currency (it's a volume average often compared with price context)
  if (upperName.includes('VOLUME_SMA') || upperName.includes('VOLUME SMA')) {
    return formatVolume(value);
  }

  // MACD and signals: 2 decimals
  if (upperName.includes('MACD')) {
    return value.toFixed(2);
  }

  // Default: 4 decimals for ratios and other indicators
  return value.toFixed(4);
};

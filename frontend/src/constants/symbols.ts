/**
 * Bybit Perpetual Futures Trading Pairs
 *
 * Based on Prediction Service tracking:
 * - 16 major crypto pairs
 * - Bybit format: BTC/USDT:USDT (perpetual futures)
 * - Frontend format: BTCUSDT (simplified)
 */

export interface TradingSymbol {
  /** Frontend display name (e.g., "BTCUSDT") */
  symbol: string
  /** Bybit API format (e.g., "BTC/USDT:USDT") */
  bybitSymbol: string
  /** Display name (e.g., "Bitcoin") */
  name: string
  /** Base currency (e.g., "BTC") */
  base: string
  /** Quote currency (always USDT for perpetuals) */
  quote: string
}

/**
 * 16 Bybit perpetual futures pairs tracked by Prediction Service
 */
export const BYBIT_SYMBOLS: TradingSymbol[] = [
  {
    symbol: 'BTCUSDT',
    bybitSymbol: 'BTC/USDT:USDT',
    name: 'Bitcoin',
    base: 'BTC',
    quote: 'USDT',
  },
  {
    symbol: 'ETHUSDT',
    bybitSymbol: 'ETH/USDT:USDT',
    name: 'Ethereum',
    base: 'ETH',
    quote: 'USDT',
  },
  {
    symbol: 'XRPUSDT',
    bybitSymbol: 'XRP/USDT:USDT',
    name: 'Ripple',
    base: 'XRP',
    quote: 'USDT',
  },
  {
    symbol: 'BNBUSDT',
    bybitSymbol: 'BNB/USDT:USDT',
    name: 'BNB',
    base: 'BNB',
    quote: 'USDT',
  },
  {
    symbol: 'SOLUSDT',
    bybitSymbol: 'SOL/USDT:USDT',
    name: 'Solana',
    base: 'SOL',
    quote: 'USDT',
  },
  {
    symbol: 'TRXUSDT',
    bybitSymbol: 'TRX/USDT:USDT',
    name: 'Tron',
    base: 'TRX',
    quote: 'USDT',
  },
  {
    symbol: 'DOGEUSDT',
    bybitSymbol: 'DOGE/USDT:USDT',
    name: 'Dogecoin',
    base: 'DOGE',
    quote: 'USDT',
  },
  {
    symbol: 'ADAUSDT',
    bybitSymbol: 'ADA/USDT:USDT',
    name: 'Cardano',
    base: 'ADA',
    quote: 'USDT',
  },
  {
    symbol: 'AVAXUSDT',
    bybitSymbol: 'AVAX/USDT:USDT',
    name: 'Avalanche',
    base: 'AVAX',
    quote: 'USDT',
  },
  {
    symbol: 'LINKUSDT',
    bybitSymbol: 'LINK/USDT:USDT',
    name: 'Chainlink',
    base: 'LINK',
    quote: 'USDT',
  },
  {
    symbol: 'DOTUSDT',
    bybitSymbol: 'DOT/USDT:USDT',
    name: 'Polkadot',
    base: 'DOT',
    quote: 'USDT',
  },
  {
    symbol: 'XLMUSDT',
    bybitSymbol: 'XLM/USDT:USDT',
    name: 'Stellar',
    base: 'XLM',
    quote: 'USDT',
  },
  {
    symbol: 'LTCUSDT',
    bybitSymbol: 'LTC/USDT:USDT',
    name: 'Litecoin',
    base: 'LTC',
    quote: 'USDT',
  },
  {
    symbol: 'TONUSDT',
    bybitSymbol: 'TON/USDT:USDT',
    name: 'Toncoin',
    base: 'TON',
    quote: 'USDT',
  },
  {
    symbol: 'HBARUSDT',
    bybitSymbol: 'HBAR/USDT:USDT',
    name: 'Hedera',
    base: 'HBAR',
    quote: 'USDT',
  },
  {
    symbol: 'UNIUSDT',
    bybitSymbol: 'UNI/USDT:USDT',
    name: 'Uniswap',
    base: 'UNI',
    quote: 'USDT',
  },
]

/**
 * Get Bybit symbol format from frontend symbol
 * @param symbol Frontend symbol (e.g., "BTCUSDT")
 * @returns Bybit format (e.g., "BTC/USDT:USDT")
 */
export function toBybitSymbol(symbol: string): string {
  const found = BYBIT_SYMBOLS.find((s) => s.symbol === symbol)
  if (!found) {
    throw new Error(`Unknown symbol: ${symbol}`)
  }
  return found.bybitSymbol
}

/**
 * Get frontend symbol from Bybit format
 * @param bybitSymbol Bybit format (e.g., "BTC/USDT:USDT")
 * @returns Frontend symbol (e.g., "BTCUSDT")
 */
export function fromBybitSymbol(bybitSymbol: string): string {
  const found = BYBIT_SYMBOLS.find((s) => s.bybitSymbol === bybitSymbol)
  if (!found) {
    throw new Error(`Unknown Bybit symbol: ${bybitSymbol}`)
  }
  return found.symbol
}

/**
 * Get symbol metadata
 * @param symbol Frontend symbol (e.g., "BTCUSDT")
 * @returns Symbol metadata
 */
export function getSymbolInfo(symbol: string): TradingSymbol {
  const found = BYBIT_SYMBOLS.find((s) => s.symbol === symbol)
  if (!found) {
    throw new Error(`Unknown symbol: ${symbol}`)
  }
  return found
}

export type OHLCV = {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type SymbolInfo = {
  symbol: string
  name: string
  type: 'stock' | 'crypto' | 'forex'
  exchange: string
  currency: string
}

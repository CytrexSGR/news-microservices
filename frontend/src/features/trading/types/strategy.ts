export type StrategyType = 'rsi' | 'bollinger' | 'ma_crossover' | 'vwap' | 'order_flow'

export type RegimeType = 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY' | 'CHOPPY' | 'ANY'

export type IndicatorParameter = {
  name: string
  type: 'int' | 'float' | 'string' | 'categorical'
  value: number | string
  min?: number
  max?: number
  options?: string[]
  description?: string
}

export type Strategy = {
  id: string
  name: string
  type: StrategyType
  description: string
  parameters: IndicatorParameter[]
  enabled: boolean
  created_at: string
  updated_at: string
}

export type StrategyConfig = {
  type: StrategyType
  parameters: Record<string, number | string>
}

/**
 * Strategy Format Converter
 *
 * Converts between backend (nested logic) and frontend (flat) strategy formats.
 *
 * Backend format (execution-optimized):
 * - logic.TREND.entry, logic.TREND.exit, logic.TREND.risk
 *
 * Frontend format (editing-optimized):
 * - entryLogic.TREND, exitLogic.TREND, riskManagement.TREND
 */

// Regime types
export type RegimeType = 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY' | 'CHOPPY' | 'ANY'

/**
 * Backend strategy format (as stored in database)
 */
export interface BackendStrategyDefinition {
  strategyId: string
  name: string
  version: string
  description?: string
  regimeDetection: any
  indicators: any[]
  logic: {
    [regime: string]: {
      entry: any
      exit: any
      risk: any
    }
  }
  execution: any
  metadata: any
}

/**
 * Frontend strategy format (used in editor)
 */
export interface FrontendStrategyDefinition {
  regimeDetection: any
  mtfa?: any
  protections?: any[]
  entryLogic: {
    [regime: string]: any
  }
  exitLogic: {
    [regime: string]: any
  }
  riskManagement: {
    [regime: string]: any
  }
  // Additional frontend-specific fields
  indicators?: any[]
  execution?: any
  metadata?: any
}

/**
 * Convert backend format to frontend format
 *
 * @param backend - Strategy in backend format (from API)
 * @returns Strategy in frontend format (for editor)
 */
export function backendToFrontend(backend: BackendStrategyDefinition): FrontendStrategyDefinition {
  const frontend: FrontendStrategyDefinition = {
    regimeDetection: convertRegimeDetectionToFrontend(backend.regimeDetection),
    entryLogic: {},
    exitLogic: {},
    riskManagement: {},
    indicators: backend.indicators || [],
    execution: backend.execution,
    metadata: backend.metadata
  }

  // Extract protections from execution if present
  if (backend.execution?.protections) {
    frontend.protections = backend.execution.protections
  }

  // Convert nested logic to flat structure
  Object.entries(backend.logic || {}).forEach(([regime, logicData]) => {
    // Entry logic
    frontend.entryLogic[regime] = {
      regime: regime as RegimeType,
      aggregation_mode: mapAggregationMode(logicData.entry.aggregation),
      conditions: logicData.entry.conditions || []
    }

    // Exit logic
    frontend.exitLogic[regime] = {
      regime: regime as RegimeType,
      rules: convertExitRules(logicData.exit.rules || [])
    }

    // Risk management
    frontend.riskManagement[regime] = {
      regime: regime as RegimeType,
      stop_loss: convertStopLoss(logicData.risk.stopLoss),
      position_sizing: convertPositionSizing(logicData.risk.positionSize),
      leverage: convertLeverage(logicData.risk.leverage)
    }
  })

  return frontend
}

/**
 * Convert frontend format to backend format
 *
 * @param frontend - Strategy in frontend format (from editor)
 * @param existingBackend - Existing backend data to preserve required fields
 * @returns Strategy in backend format (for API)
 */
export function frontendToBackend(
  frontend: FrontendStrategyDefinition,
  existingBackend?: Partial<BackendStrategyDefinition>
): BackendStrategyDefinition {
  const backend: BackendStrategyDefinition = {
    strategyId: existingBackend?.strategyId || `strategy_${Date.now()}`,
    name: existingBackend?.name || 'Unnamed Strategy',
    version: existingBackend?.version || '1.0.0',
    description: existingBackend?.description,
    regimeDetection: convertRegimeDetectionToBackend(frontend.regimeDetection),
    indicators: frontend.indicators || existingBackend?.indicators || [],
    logic: {},
    execution: {
      ...existingBackend?.execution,
      ...frontend.execution,
      protections: frontend.protections || existingBackend?.execution?.protections || []
    },
    metadata: frontend.metadata || existingBackend?.metadata || {}
  }

  // Convert flat structure to nested logic
  const regimes = new Set([
    ...Object.keys(frontend.entryLogic || {}),
    ...Object.keys(frontend.exitLogic || {}),
    ...Object.keys(frontend.riskManagement || {})
  ])

  regimes.forEach(regime => {
    const entryData = frontend.entryLogic[regime]
    const exitData = frontend.exitLogic[regime]
    const riskData = frontend.riskManagement[regime]

    backend.logic[regime] = {
      entry: {
        conditions: entryData?.conditions || [],
        aggregation: mapAggregationModeToBackend(entryData?.aggregation_mode),
        threshold: entryData?.threshold || 0.7,
        description: entryData?.description
      },
      exit: {
        rules: exitData?.rules || []
      },
      risk: {
        stopLoss: convertStopLossToBackend(riskData?.stop_loss),
        positionSize: convertPositionSizingToBackend(riskData?.position_sizing),
        leverage: convertLeverageToBackend(riskData?.leverage)
      }
    }
  })

  return backend
}

/**
 * Helper: Map aggregation mode from backend to frontend
 */
function mapAggregationMode(backendMode: string): 'ALL' | 'ANY' | 'WEIGHTED' {
  const mapping: Record<string, 'ALL' | 'ANY' | 'WEIGHTED'> = {
    'all': 'ALL',
    'any': 'ANY',
    'weighted_avg': 'WEIGHTED'
  }
  return mapping[backendMode] || 'ALL'
}

/**
 * Helper: Map aggregation mode from frontend to backend
 */
function mapAggregationModeToBackend(frontendMode?: string): string {
  const mapping: Record<string, string> = {
    'ALL': 'all',
    'ANY': 'any',
    'WEIGHTED': 'weighted_avg'
  }
  return mapping[frontendMode || 'ALL'] || 'all'
}

/**
 * Helper: Convert backend stop loss to frontend format
 */
function convertStopLoss(backendStopLoss: any): any {
  return {
    method: backendStopLoss.dynamic ? 'atr_based' : 'fixed',
    atr_multiplier: extractATRMultiplier(backendStopLoss.formula),
    fixed_ratio: backendStopLoss.fixed_ratio
  }
}

/**
 * Helper: Convert backend position sizing to frontend format
 */
function convertPositionSizing(backendPositionSize: any): any {
  return {
    method: backendPositionSize.method || 'percent_risk',
    percent_risk: backendPositionSize.maxRiskPerTrade
  }
}

/**
 * Helper: Convert backend leverage to frontend format
 */
function convertLeverage(backendLeverage: any): any {
  return {
    max_leverage: backendLeverage.max || 1,
    adaptive: backendLeverage.formula !== backendLeverage.max.toString(),
    formula: backendLeverage.formula
  }
}

/**
 * Helper: Convert frontend stop loss to backend format
 */
function convertStopLossToBackend(frontendStopLoss: any): any {
  if (!frontendStopLoss) {
    return {
      formula: 'entry_price - (2.0 * 1h_ATR_14)',
      dynamic: true,
      description: 'Default ATR-based stop loss'
    }
  }

  if (frontendStopLoss.method === 'atr_based') {
    return {
      formula: `entry_price - (${frontendStopLoss.atr_multiplier || 2.0} * 1h_ATR_14)`,
      dynamic: true,
      description: `ATR-based stop loss (${frontendStopLoss.atr_multiplier}x)`
    }
  }

  return {
    formula: `entry_price * (1 + ${frontendStopLoss.fixed_ratio || -0.02})`,
    dynamic: false,
    description: `Fixed stop loss (${(frontendStopLoss.fixed_ratio || -0.02) * 100}%)`
  }
}

/**
 * Helper: Convert frontend position sizing to backend format
 */
function convertPositionSizingToBackend(frontendPositionSizing: any): any {
  if (!frontendPositionSizing) {
    return {
      formula: '(account_balance * 0.01) / ((2.0 * 1h_ATR_14) / entry_price)',
      method: 'percent_risk',
      maxRiskPerTrade: 0.01,
      description: 'Risk 1% of capital per trade'
    }
  }

  return {
    formula: `(account_balance * ${frontendPositionSizing.percent_risk || 0.01}) / ((2.0 * 1h_ATR_14) / entry_price)`,
    method: frontendPositionSizing.method || 'percent_risk',
    maxRiskPerTrade: frontendPositionSizing.percent_risk || 0.01,
    description: `Risk ${(frontendPositionSizing.percent_risk || 0.01) * 100}% of capital per trade`
  }
}

/**
 * Helper: Convert frontend leverage to backend format
 */
function convertLeverageToBackend(frontendLeverage: any): any {
  if (!frontendLeverage) {
    return {
      formula: '1.0',
      min: 1.0,
      max: 1.0,
      description: 'No leverage (1x)'
    }
  }

  return {
    formula: frontendLeverage.formula || frontendLeverage.max_leverage?.toString() || '1.0',
    min: 1.0,
    max: frontendLeverage.max_leverage || 1,
    description: `Leverage up to ${frontendLeverage.max_leverage}x${frontendLeverage.adaptive ? ' (adaptive)' : ''}`
  }
}

/**
 * Helper: Extract ATR multiplier from formula
 */
function extractATRMultiplier(formula?: string): number {
  if (!formula) return 2.0

  // Extract number before * 1h_ATR
  const match = formula.match(/(\d+\.?\d*)\s*\*\s*1h_ATR/)
  return match ? parseFloat(match[1]) : 2.0
}

/**
 * Helper: Convert backend exit rules to frontend format
 */
function convertExitRules(backendRules: any[]): any[] {
  return backendRules.map((rule, index) => {
    // Generate ID if not present
    const id = rule.id || `exit_rule_${index}`
    const enabled = rule.enabled !== undefined ? rule.enabled : true

    // Convert based on rule type
    let config: any = {}

    switch (rule.type) {
      case 'take_profit':
        config = {
          profit_ratio: rule.value || rule.profit_ratio || 0.03,
          description: rule.description
        }
        break

      case 'trailing_stop':
        config = {
          trailing_offset: rule.offset || rule.trailing_offset || 0.01,
          trailing_only_offset_is_reached: rule.activation !== undefined,
          activation_ratio: rule.activation,
          description: rule.description
        }
        break

      case 'stop_loss':
        config = {
          stop_loss_ratio: rule.value || rule.stop_loss_ratio || -0.02,
          description: rule.description
        }
        break

      case 'time_based':
        config = {
          max_candles_in_trade: rule.max_candles || rule.max_candles_in_trade || 24,
          description: rule.description
        }
        break

      case 'regime_change':
        config = {
          exit_on_regime_change: true,
          action: rule.action || 'exit',
          description: rule.description
        }
        break

      case 'indicator_signal':
        config = {
          expression: rule.expression || '',
          description: rule.description || ''
        }
        break

      default:
        // Unknown type - preserve as-is
        config = rule.config || rule
    }

    return {
      id,
      type: rule.type,
      enabled,
      config
    }
  })
}

/**
 * Helper: Convert backend regime detection to frontend format
 */
function convertRegimeDetectionToFrontend(backendRegimeDetection: any): any {
  if (!backendRegimeDetection) {
    return {
      provider: 'rule_based',
      config: {
        adx_threshold: 25,
        bbw_threshold: 0.02,
        atr_threshold: 0.5
      }
    }
  }

  // Map provider name: "threshold" → "rule_based"
  const provider = backendRegimeDetection.provider === 'threshold' ? 'rule_based' : backendRegimeDetection.provider

  // If already in frontend format, return as-is
  if (provider === 'rule_based' && backendRegimeDetection.config?.adx_threshold !== undefined) {
    return backendRegimeDetection
  }

  // Convert backend format to frontend format
  const backendConfig = backendRegimeDetection.config || {}

  // Extract thresholds from nested structure
  const trendThresholds = backendConfig.thresholds?.TREND || {}
  const highVolThresholds = backendConfig.thresholds?.HIGH_VOLATILITY || {}

  return {
    provider,
    config: {
      adx_threshold: trendThresholds.adx_min || 25,
      bbw_threshold: highVolThresholds.bbw_min || 0.02,
      atr_threshold: 0.5  // Default, not stored in backend nested format
    }
  }
}

/**
 * Helper: Convert frontend regime detection to backend format
 */
function convertRegimeDetectionToBackend(frontendRegimeDetection: any): any {
  if (!frontendRegimeDetection) {
    return {
      provider: 'threshold',
      config: {
        method: 'adx_bbw',
        indicators: {
          adx: '1h_ADX_14',
          bbw: '1h_BBW_20',
          atr: '1h_ATR_14'
        },
        thresholds: {
          TREND: {
            adx_min: 25,
            bbw_max: 0.05,
            description: 'Strong directional movement with controlled volatility'
          },
          CONSOLIDATION: {
            adx_max: 20,
            bbw_max: 0.03,
            description: 'Weak movement, sideways market'
          },
          HIGH_VOLATILITY: {
            bbw_min: 0.06,
            description: 'High volatility regardless of trend'
          }
        }
      }
    }
  }

  // Map provider name: "rule_based" → "threshold"
  const provider = frontendRegimeDetection.provider === 'rule_based' ? 'threshold' : frontendRegimeDetection.provider

  const frontendConfig = frontendRegimeDetection.config || {}
  const adxThreshold = frontendConfig.adx_threshold || 25
  const bbwThreshold = frontendConfig.bbw_threshold || 0.02

  return {
    provider,
    config: {
      method: 'adx_bbw',
      indicators: {
        adx: '1h_ADX_14',
        bbw: '1h_BBW_20',
        atr: '1h_ATR_14'
      },
      thresholds: {
        TREND: {
          adx_min: adxThreshold,
          bbw_max: bbwThreshold * 2.5,  // BBW max is usually higher than min
          description: 'Strong directional movement with controlled volatility'
        },
        CONSOLIDATION: {
          adx_max: Math.max(adxThreshold - 5, 20),
          bbw_max: bbwThreshold * 1.5,
          description: 'Weak movement, sideways market'
        },
        HIGH_VOLATILITY: {
          bbw_min: bbwThreshold * 3,
          description: 'High volatility regardless of trend'
        }
      }
    }
  }
}

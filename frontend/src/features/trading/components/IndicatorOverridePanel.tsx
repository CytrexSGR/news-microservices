/**
 * IndicatorOverridePanel Component
 *
 * Allows users to override indicator parameters during backtest configuration.
 * Part of Phase 2: Backtest Comprehensive Upgrade.
 *
 * Features:
 * - Displays strategy indicators as editable fields
 * - Parameter sliders with min/max validation
 * - Live preview of changes vs original values
 * - Reset individual indicators or all at once
 */

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Settings2,
  RotateCcw,
  ChevronDown,
  ChevronRight,
  Info,
  AlertCircle,
} from 'lucide-react'
import type { IndicatorDefinition } from '@/types/strategy'
import type { IndicatorOverride } from '@/types/backtest'

// Indicator parameter configurations with min/max/step
const INDICATOR_PARAM_CONFIG: Record<string, Record<string, { min: number; max: number; step: number; label: string }>> = {
  RSI: {
    period: { min: 2, max: 50, step: 1, label: 'RSI Period' },
  },
  EMA: {
    period: { min: 5, max: 500, step: 1, label: 'EMA Period' },
  },
  SMA: {
    period: { min: 5, max: 500, step: 1, label: 'SMA Period' },
  },
  MACD: {
    fast_period: { min: 5, max: 50, step: 1, label: 'Fast Period' },
    slow_period: { min: 10, max: 100, step: 1, label: 'Slow Period' },
    signal_period: { min: 3, max: 30, step: 1, label: 'Signal Period' },
  },
  ATR: {
    period: { min: 5, max: 50, step: 1, label: 'ATR Period' },
  },
  BBANDS: {
    period: { min: 5, max: 50, step: 1, label: 'BB Period' },
    std_dev: { min: 1, max: 4, step: 0.5, label: 'Std Deviation' },
  },
  ADX: {
    period: { min: 5, max: 50, step: 1, label: 'ADX Period' },
  },
  STOCH: {
    k_period: { min: 5, max: 30, step: 1, label: 'K Period' },
    d_period: { min: 2, max: 10, step: 1, label: 'D Period' },
  },
  OBV: {
    // OBV has no parameters (cumulative)
  },
  VWAP: {
    // VWAP has no parameters
  },
  AROON: {
    period: { min: 10, max: 50, step: 1, label: 'Aroon Period' },
  },
  VOLUME_RATIO: {
    period: { min: 5, max: 50, step: 1, label: 'Volume Period' },
  },
  BBW: {
    period: { min: 5, max: 50, step: 1, label: 'BBW Period' },
    std_dev: { min: 1, max: 4, step: 0.5, label: 'Std Deviation' },
  },
}

// Parse indicator ID to extract type and params
// e.g., "1h_RSI_14" -> { type: "RSI", timeframe: "1h", originalPeriod: 14 }
function parseIndicatorId(id: string): { type: string; timeframe: string; params: Record<string, number> } | null {
  const parts = id.split('_')
  if (parts.length < 2) return null

  const timeframe = parts[0]
  const type = parts[1].toUpperCase()

  // Extract numeric params from the ID
  const params: Record<string, number> = {}

  // Common patterns:
  // RSI_14 -> period: 14
  // EMA_50 -> period: 50
  // MACD_12_26_9 -> fast_period: 12, slow_period: 26, signal_period: 9
  // BB_UPPER_20 -> period: 20
  // STOCH_K_14 -> k_period: 14

  if (type === 'MACD' && parts.length >= 5) {
    params.fast_period = parseInt(parts[2], 10) || 12
    params.slow_period = parseInt(parts[3], 10) || 26
    params.signal_period = parseInt(parts[4], 10) || 9
  } else if (type === 'BB' || type === 'BBW') {
    // Handle BB_UPPER_20, BB_LOWER_20, BB_MID_20, BBW_20
    const lastPart = parts[parts.length - 1]
    params.period = parseInt(lastPart, 10) || 20
    params.std_dev = 2 // default
  } else if (type === 'STOCH') {
    // Handle STOCH_K_14, STOCH_D_14
    const lastPart = parts[parts.length - 1]
    params.k_period = parseInt(lastPart, 10) || 14
    params.d_period = 3 // default
  } else if (type === 'AROON') {
    // Handle AROON_UP_25, AROON_DOWN_25
    const lastPart = parts[parts.length - 1]
    params.period = parseInt(lastPart, 10) || 25
  } else if (type === 'VOLUME') {
    // Handle VOLUME_SMA_20, VOLUME_RATIO_20
    if (parts.length >= 4) {
      const lastPart = parts[parts.length - 1]
      params.period = parseInt(lastPart, 10) || 20
    }
  } else {
    // Simple pattern: TYPE_PERIOD (RSI_14, EMA_50, etc.)
    const lastPart = parts[parts.length - 1]
    const period = parseInt(lastPart, 10)
    if (!isNaN(period)) {
      params.period = period
    }
  }

  return { type, timeframe, params }
}

interface IndicatorOverridePanelProps {
  /** Strategy indicators from definition */
  indicators: IndicatorDefinition[]
  /** Current overrides */
  overrides: IndicatorOverride[]
  /** Callback when overrides change */
  onOverridesChange: (overrides: IndicatorOverride[]) => void
  /** Whether the panel is expanded */
  isExpanded?: boolean
  /** Callback when expansion state changes */
  onExpandedChange?: (expanded: boolean) => void
}

export function IndicatorOverridePanel({
  indicators,
  overrides,
  onOverridesChange,
  isExpanded = false,
  onExpandedChange,
}: IndicatorOverridePanelProps) {
  const [expanded, setExpanded] = useState(isExpanded)

  useEffect(() => {
    setExpanded(isExpanded)
  }, [isExpanded])

  const handleExpandedChange = (newExpanded: boolean) => {
    setExpanded(newExpanded)
    onExpandedChange?.(newExpanded)
  }

  // Build list of available indicators from strategy
  const availableIndicators = useMemo(() => {
    const result: Array<{
      id: string
      type: string
      timeframe: string
      originalParams: Record<string, number>
      paramConfig: Record<string, { min: number; max: number; step: number; label: string }>
    }> = []

    for (const indicator of indicators) {
      const parsed = parseIndicatorId(indicator.id)
      if (!parsed) continue

      const baseType = parsed.type.replace('_UPPER', '').replace('_LOWER', '').replace('_MID', '')
        .replace('_K', '').replace('_D', '').replace('_UP', '').replace('_DOWN')

      const config = INDICATOR_PARAM_CONFIG[baseType] || INDICATOR_PARAM_CONFIG[parsed.type]
      if (!config || Object.keys(config).length === 0) continue // Skip indicators without configurable params

      result.push({
        id: indicator.id,
        type: parsed.type,
        timeframe: parsed.timeframe,
        originalParams: parsed.params,
        paramConfig: config,
      })
    }

    // Deduplicate by indicator type+timeframe (keep first occurrence)
    const seen = new Set<string>()
    return result.filter((item) => {
      const key = `${item.timeframe}_${item.type}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  }, [indicators])

  // Get current value for an indicator param (override or original)
  const getParamValue = (indicatorId: string, paramName: string, originalValue: number): number => {
    const override = overrides.find((o) => o.indicator_id === indicatorId)
    if (override && override.params[paramName] !== undefined) {
      return override.params[paramName] as number
    }
    return originalValue
  }

  // Check if indicator has any overrides
  const hasOverride = (indicatorId: string): boolean => {
    return overrides.some((o) => o.indicator_id === indicatorId)
  }

  // Update a param override
  const updateParamOverride = (indicatorId: string, paramName: string, value: number) => {
    const existingIndex = overrides.findIndex((o) => o.indicator_id === indicatorId)

    if (existingIndex >= 0) {
      // Update existing override
      const newOverrides = [...overrides]
      newOverrides[existingIndex] = {
        ...newOverrides[existingIndex],
        params: {
          ...newOverrides[existingIndex].params,
          [paramName]: value,
        },
      }
      onOverridesChange(newOverrides)
    } else {
      // Create new override
      onOverridesChange([
        ...overrides,
        {
          indicator_id: indicatorId,
          params: { [paramName]: value },
        },
      ])
    }
  }

  // Reset single indicator
  const resetIndicator = (indicatorId: string) => {
    onOverridesChange(overrides.filter((o) => o.indicator_id !== indicatorId))
  }

  // Reset all overrides
  const resetAllOverrides = () => {
    onOverridesChange([])
  }

  const overrideCount = overrides.length

  return (
    <Card className="border-dashed">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <button
            type="button"
            className="flex items-center gap-2 text-left"
            onClick={() => handleExpandedChange(!expanded)}
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            <CardTitle className="text-base flex items-center gap-2">
              <Settings2 className="h-4 w-4" />
              Advanced: Indicator Overrides
            </CardTitle>
          </button>
          {overrideCount > 0 && (
            <Badge variant="secondary" className="ml-2">
              {overrideCount} override{overrideCount > 1 ? 's' : ''}
            </Badge>
          )}
        </div>
        {!expanded && (
          <CardDescription className="mt-1 ml-6">
            Test different indicator parameters without modifying the strategy
          </CardDescription>
        )}
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-4">
          {/* Info Banner */}
          <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
            <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-blue-900 dark:text-blue-100">
              Override indicator parameters for this backtest only. Original strategy remains unchanged.
              Results will show comparison between original and modified parameters.
            </p>
          </div>

          {availableIndicators.length === 0 ? (
            <div className="text-center py-6 text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No configurable indicators in this strategy</p>
            </div>
          ) : (
            <>
              {/* Reset All Button */}
              {overrideCount > 0 && (
                <div className="flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={resetAllOverrides}
                    className="text-muted-foreground"
                  >
                    <RotateCcw className="h-3.5 w-3.5 mr-1" />
                    Reset All
                  </Button>
                </div>
              )}

              {/* Indicator List */}
              <div className="space-y-4">
                {availableIndicators.map((indicator) => (
                  <div
                    key={indicator.id}
                    className={`border rounded-lg p-4 ${
                      hasOverride(indicator.id)
                        ? 'border-primary/50 bg-primary/5'
                        : 'border-border'
                    }`}
                  >
                    {/* Indicator Header */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          {indicator.timeframe}
                        </Badge>
                        <span className="font-medium">{indicator.type}</span>
                        {hasOverride(indicator.id) && (
                          <Badge variant="default" className="text-xs">
                            Modified
                          </Badge>
                        )}
                      </div>
                      {hasOverride(indicator.id) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => resetIndicator(indicator.id)}
                          className="h-7 px-2"
                        >
                          <RotateCcw className="h-3 w-3" />
                        </Button>
                      )}
                    </div>

                    {/* Parameter Controls */}
                    <div className="space-y-4">
                      {Object.entries(indicator.paramConfig).map(([paramName, config]) => {
                        const originalValue = indicator.originalParams[paramName] || config.min
                        const currentValue = getParamValue(indicator.id, paramName, originalValue)
                        const isModified = currentValue !== originalValue

                        return (
                          <div key={paramName} className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Label className="text-sm">{config.label}</Label>
                              <div className="flex items-center gap-2">
                                {isModified && (
                                  <span className="text-xs text-muted-foreground line-through">
                                    {originalValue}
                                  </span>
                                )}
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Input
                                        type="number"
                                        value={currentValue}
                                        onChange={(e) => {
                                          const val = parseFloat(e.target.value)
                                          if (!isNaN(val) && val >= config.min && val <= config.max) {
                                            updateParamOverride(indicator.id, paramName, val)
                                          }
                                        }}
                                        className={`w-20 h-8 text-center ${
                                          isModified ? 'border-primary' : ''
                                        }`}
                                        min={config.min}
                                        max={config.max}
                                        step={config.step}
                                      />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      Range: {config.min} - {config.max}
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </div>
                            </div>
                            <Slider
                              value={[currentValue]}
                              onValueChange={([val]) => updateParamOverride(indicator.id, paramName, val)}
                              min={config.min}
                              max={config.max}
                              step={config.step}
                              className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>{config.min}</span>
                              <span>{config.max}</span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      )}
    </Card>
  )
}

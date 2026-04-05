/**
 * EntryLogicEditor Component
 *
 * Per-Regime Entry Conditions Configuration
 * - TREND: EMA crossovers, MACD signals
 * - CONSOLIDATION: RSI extremes, BB touches
 * - HIGH_VOLATILITY: Volume spikes + RSI
 *
 * Uses RegimeTabs for uniform UX
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/Textarea'
import { Input } from '@/components/ui/Input'
import { Plus, Trash2, AlertCircle } from 'lucide-react'
import { RegimeTabs } from './shared/RegimeTabs'
import type { Strategy } from '@/types/strategy'
import type { RegimeType } from './shared/RegimeTabs'

interface EntryLogicEditorProps {
  strategy: Strategy
  onChange?: (field: string, value: any) => void
}

type AggregationMode = 'ALL' | 'ANY' | 'WEIGHTED' | 'CONFIDENCE_VOTING'

interface EntryCondition {
  id: string
  expression: string
  description: string
  confidence?: number
}

interface RegimeEntryLogic {
  regime: RegimeType
  aggregation_mode: AggregationMode
  conditions: EntryCondition[]
}

const REGIMES: RegimeType[] = ['TREND', 'CONSOLIDATION', 'HIGH_VOLATILITY']

// Available indicators for autocomplete/reference
const AVAILABLE_INDICATORS = [
  // Momentum Indicators
  '1h_RSI_14',
  '1h_MACD_12_26_9',
  '1h_MACD_signal',
  '1h_MACD_hist',
  '1h_STOCH_K_14',
  '1h_STOCH_D_14',
  // Trend Indicators
  '1h_EMA_20',
  '1h_EMA_50',
  '1h_EMA_200',
  '1h_SMA_20',
  '1h_SMA_50',
  '1h_ADX_14',
  '1h_AROON_UP_25',
  '1h_AROON_DOWN_25',
  // Volatility Indicators
  '1h_ATR_14',
  '1h_BB_UPPER_20',
  '1h_BB_LOWER_20',
  '1h_BB_MID_20',
  '1h_BBW_20',
  // Volume Indicators
  '1h_VOLUME',
  '1h_VOLUME_SMA_20',
  '1h_VOLUME_RATIO_20',
  '1h_OBV',
  '1h_VWAP',
  // Higher Timeframe (4h)
  '4h_EMA_50',
  '4h_EMA_200',
  '4h_RSI_14',
  '4h_ADX_14',
  // Daily Timeframe
  '1d_EMA_50',
  '1d_EMA_200',
]

export function EntryLogicEditor({ strategy, onChange }: EntryLogicEditorProps) {
  const entryLogic: Record<RegimeType, RegimeEntryLogic> = strategy.definition?.entryLogic || {
    TREND: {
      regime: 'TREND',
      aggregation_mode: 'ALL',
      conditions: [],
    },
    CONSOLIDATION: {
      regime: 'CONSOLIDATION',
      aggregation_mode: 'ALL',
      conditions: [],
    },
    HIGH_VOLATILITY: {
      regime: 'HIGH_VOLATILITY',
      aggregation_mode: 'ALL',
      conditions: [],
    },
  }

  const handleAddCondition = (regime: RegimeType) => {
    const newCondition: EntryCondition = {
      id: `condition_${Date.now()}`,
      expression: '',
      description: '',
      confidence: 1.0,
    }
    const updated = {
      ...entryLogic[regime],
      conditions: [...entryLogic[regime].conditions, newCondition],
    }
    onChange?.(`entryLogic.${regime}`, updated)
  }

  const handleRemoveCondition = (regime: RegimeType, conditionId: string) => {
    const updated = {
      ...entryLogic[regime],
      conditions: entryLogic[regime].conditions.filter((c) => c.id !== conditionId),
    }
    onChange?.(`entryLogic.${regime}`, updated)
  }

  const handleConditionChange = (
    regime: RegimeType,
    conditionId: string,
    field: keyof EntryCondition,
    value: any
  ) => {
    const updated = {
      ...entryLogic[regime],
      conditions: entryLogic[regime].conditions.map((c) =>
        c.id === conditionId ? { ...c, [field]: value } : c
      ),
    }
    onChange?.(`entryLogic.${regime}`, updated)
  }

  const handleAggregationChange = (regime: RegimeType, mode: AggregationMode) => {
    const updated = {
      ...entryLogic[regime],
      aggregation_mode: mode,
    }
    onChange?.(`entryLogic.${regime}`, updated)
  }

  const renderRegimeContent = (regime: RegimeType) => {
    const logic = entryLogic[regime]

    return (
      <div className="space-y-6">
        {/* Info Banner */}
        <div className="p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>{regime} Regime:</strong>{' '}
            {regime === 'TREND' && 'EMA crossovers, MACD signals, strong directional movement'}
            {regime === 'CONSOLIDATION' && 'RSI extremes, BB touches, range-bound conditions'}
            {regime === 'HIGH_VOLATILITY' && 'Volume spikes, RSI divergence, volatility breakouts'}
          </p>
        </div>

        {/* Aggregation Mode */}
        <div className="space-y-2">
          <Label htmlFor={`${regime}-aggregation`}>Aggregation Mode</Label>
          <select
            id={`${regime}-aggregation`}
            value={logic.aggregation_mode}
            onChange={(e) => handleAggregationChange(regime, e.target.value as AggregationMode)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="ALL">ALL (AND) - All conditions must be true</option>
            <option value="ANY">ANY (OR) - At least one condition must be true</option>
            <option value="WEIGHTED">WEIGHTED - Weighted sum of conditions</option>
            <option value="CONFIDENCE_VOTING">CONFIDENCE_VOTING - ML-style voting</option>
          </select>
          <p className="text-xs text-muted-foreground">
            How to combine multiple conditions into a final entry signal
          </p>
        </div>

        {/* Conditions List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Entry Conditions</Label>
            <Badge variant="outline">{logic.conditions.length} conditions</Badge>
          </div>

          {logic.conditions.length === 0 ? (
            <div className="text-center py-8 border rounded-lg bg-muted/30">
              <AlertCircle className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">No entry conditions configured</p>
              <p className="text-xs text-muted-foreground mt-1">
                Add conditions to define when to enter trades in {regime} regime
              </p>
            </div>
          ) : (
            logic.conditions.map((condition, index) => (
              <div key={condition.id} className="border rounded-lg p-4 space-y-4">
                {/* Condition Header */}
                <div className="flex items-center justify-between">
                  <Badge variant="secondary">Condition {index + 1}</Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveCondition(regime, condition.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                {/* Expression */}
                <div className="space-y-2">
                  <Label htmlFor={`${regime}-${condition.id}-expression`}>
                    Expression (SymPy-compatible)
                    <span className="text-destructive ml-1">*</span>
                  </Label>
                  <Textarea
                    id={`${regime}-${condition.id}-expression`}
                    value={condition.expression}
                    onChange={(e) =>
                      handleConditionChange(regime, condition.id, 'expression', e.target.value)
                    }
                    placeholder="(1h_EMA_20 > 1h_EMA_50) & (1h_RSI_14 > 50)"
                    rows={3}
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    Use indicator names: {AVAILABLE_INDICATORS.slice(0, 3).join(', ')}...
                  </p>
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor={`${regime}-${condition.id}-description`}>Description</Label>
                  <Input
                    id={`${regime}-${condition.id}-description`}
                    value={condition.description}
                    onChange={(e) =>
                      handleConditionChange(regime, condition.id, 'description', e.target.value)
                    }
                    placeholder="e.g., Bullish EMA crossover with RSI confirmation"
                  />
                </div>

                {/* Confidence (for WEIGHTED/CONFIDENCE_VOTING modes) */}
                {(logic.aggregation_mode === 'WEIGHTED' ||
                  logic.aggregation_mode === 'CONFIDENCE_VOTING') && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor={`${regime}-${condition.id}-confidence`}>
                        Confidence Weight
                      </Label>
                      <span className="text-sm font-medium">
                        {((condition.confidence ?? 1.0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <input
                      id={`${regime}-${condition.id}-confidence`}
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={condition.confidence ?? 1.0}
                      onChange={(e) =>
                        handleConditionChange(regime, condition.id, 'confidence', Number(e.target.value))
                      }
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      Higher confidence = more influence on final decision
                    </p>
                  </div>
                )}
              </div>
            ))
          )}

          {/* Add Condition Button */}
          <Button
            variant="outline"
            onClick={() => handleAddCondition(regime)}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Condition
          </Button>
        </div>

        {/* Available Indicators Reference */}
        <div className="border-t pt-4">
          <details className="space-y-2">
            <summary className="cursor-pointer text-sm font-medium">
              Available Indicators ({AVAILABLE_INDICATORS.length})
            </summary>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {AVAILABLE_INDICATORS.map((indicator) => (
                <code key={indicator} className="text-xs bg-muted px-2 py-1 rounded">
                  {indicator}
                </code>
              ))}
            </div>
          </details>
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Entry Logic Configuration</CardTitle>
        <CardDescription>
          Define entry conditions for each market regime using SymPy-compatible expressions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RegimeTabs regimes={REGIMES} defaultRegime="TREND" renderContent={renderRegimeContent} />
      </CardContent>
    </Card>
  )
}

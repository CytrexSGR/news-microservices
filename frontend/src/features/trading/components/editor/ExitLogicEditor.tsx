/**
 * ExitLogicEditor Component
 *
 * Per-Regime Exit Rules Configuration
 * Exit types:
 * - take_profit: Fixed profit target
 * - trailing_stop: Dynamic trailing stop
 * - stop_loss: Fixed stop loss (overridden by risk management)
 * - time_based: Exit after N candles
 * - regime_change: Exit on regime shift
 * - indicator_signal: Custom indicator-based exit
 *
 * Uses RegimeTabs for uniform UX
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Plus, Trash2, AlertCircle } from 'lucide-react'
import { RegimeTabs } from './shared/RegimeTabs'
import type { Strategy } from '@/types/strategy'
import type { RegimeType } from './shared/RegimeTabs'

interface ExitLogicEditorProps {
  strategy: Strategy
  onChange?: (field: string, value: any) => void
}

type ExitType = 'take_profit' | 'trailing_stop' | 'stop_loss' | 'time_based' | 'regime_change' | 'indicator_signal'

interface ExitRule {
  id: string
  type: ExitType
  enabled: boolean
  config: any
}

interface RegimeExitLogic {
  regime: RegimeType
  rules: ExitRule[]
}

const REGIMES: RegimeType[] = ['TREND', 'CONSOLIDATION', 'HIGH_VOLATILITY']

const exitTypeLabels: Record<ExitType, string> = {
  take_profit: 'Take Profit',
  trailing_stop: 'Trailing Stop',
  stop_loss: 'Stop Loss',
  time_based: 'Time-Based Exit',
  regime_change: 'Regime Change',
  indicator_signal: 'Indicator Signal',
}

const exitTypeTemplates: Record<ExitType, any> = {
  take_profit: { profit_ratio: 0.03 },
  trailing_stop: { trailing_offset: 0.01, trailing_only_offset_is_reached: true },
  stop_loss: { stop_loss_ratio: -0.02 },
  time_based: { max_candles_in_trade: 24 },
  regime_change: { exit_on_regime_change: true },
  indicator_signal: { expression: '', description: '' },
}

export function ExitLogicEditor({ strategy, onChange }: ExitLogicEditorProps) {
  const exitLogic: Record<RegimeType, RegimeExitLogic> = strategy.definition?.exitLogic || {
    TREND: { regime: 'TREND', rules: [] },
    CONSOLIDATION: { regime: 'CONSOLIDATION', rules: [] },
    HIGH_VOLATILITY: { regime: 'HIGH_VOLATILITY', rules: [] },
  }

  const handleAddRule = (regime: RegimeType, type: ExitType) => {
    const newRule: ExitRule = {
      id: `exit_${Date.now()}`,
      type,
      enabled: true,
      config: exitTypeTemplates[type],
    }
    const updated = {
      ...exitLogic[regime],
      rules: [...exitLogic[regime].rules, newRule],
    }
    onChange?.(`exitLogic.${regime}`, updated)
  }

  const handleRemoveRule = (regime: RegimeType, ruleId: string) => {
    const updated = {
      ...exitLogic[regime],
      rules: exitLogic[regime].rules.filter((r) => r.id !== ruleId),
    }
    onChange?.(`exitLogic.${regime}`, updated)
  }

  const handleRuleChange = (regime: RegimeType, ruleId: string, field: keyof ExitRule, value: any) => {
    const updated = {
      ...exitLogic[regime],
      rules: exitLogic[regime].rules.map((r) =>
        r.id === ruleId ? { ...r, [field]: value } : r
      ),
    }
    onChange?.(`exitLogic.${regime}`, updated)
  }

  const handleConfigChange = (regime: RegimeType, ruleId: string, key: string, value: any) => {
    const updated = {
      ...exitLogic[regime],
      rules: exitLogic[regime].rules.map((r) =>
        r.id === ruleId ? { ...r, config: { ...r.config, [key]: value } } : r
      ),
    }
    onChange?.(`exitLogic.${regime}`, updated)
  }

  const renderRegimeContent = (regime: RegimeType) => {
    const logic = exitLogic[regime]

    return (
      <div className="space-y-6">
        {/* Info Banner */}
        <div className="p-4 bg-purple-50 dark:bg-purple-950 border border-purple-200 dark:border-purple-800 rounded-lg">
          <p className="text-sm text-purple-900 dark:text-purple-100">
            <strong>Exit Strategy:</strong> Multiple exit rules can be combined. The first triggered
            rule will close the position.
          </p>
        </div>

        {/* Rules List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Exit Rules</Label>
            <Badge variant="outline">{logic.rules.length} rules</Badge>
          </div>

          {logic.rules.length === 0 ? (
            <div className="text-center py-8 border rounded-lg bg-muted/30">
              <AlertCircle className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">No exit rules configured</p>
              <p className="text-xs text-muted-foreground mt-1">
                Add exit rules to define when to close trades in {regime} regime
              </p>
            </div>
          ) : (
            logic.rules.map((rule, index) => (
              <div key={rule.id} className="border rounded-lg p-4 space-y-4">
                {/* Rule Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={rule.enabled ? 'default' : 'secondary'}>
                      {exitTypeLabels[rule.type]}
                    </Badge>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={rule.enabled}
                        onChange={(e) =>
                          handleRuleChange(regime, rule.id, 'enabled', e.target.checked)
                        }
                        className="w-4 h-4 rounded border-gray-300"
                      />
                      <span className="text-sm">Enabled</span>
                    </label>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveRule(regime, rule.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                {/* Type-Specific Config */}
                {rule.type === 'take_profit' && (
                  <TakeProfitConfig
                    config={rule.config}
                    onChange={(key, value) => handleConfigChange(regime, rule.id, key, value)}
                  />
                )}

                {rule.type === 'trailing_stop' && (
                  <TrailingStopConfig
                    config={rule.config}
                    onChange={(key, value) => handleConfigChange(regime, rule.id, key, value)}
                  />
                )}

                {rule.type === 'stop_loss' && (
                  <StopLossConfig
                    config={rule.config}
                    onChange={(key, value) => handleConfigChange(regime, rule.id, key, value)}
                  />
                )}

                {rule.type === 'time_based' && (
                  <TimeBasedConfig
                    config={rule.config}
                    onChange={(key, value) => handleConfigChange(regime, rule.id, key, value)}
                  />
                )}

                {rule.type === 'regime_change' && (
                  <RegimeChangeConfig
                    config={rule.config}
                    onChange={(key, value) => handleConfigChange(regime, rule.id, key, value)}
                  />
                )}

                {rule.type === 'indicator_signal' && (
                  <IndicatorSignalConfig
                    config={rule.config}
                    onChange={(key, value) => handleConfigChange(regime, rule.id, key, value)}
                  />
                )}
              </div>
            ))
          )}
        </div>

        {/* Add Rule Buttons */}
        <div className="border-t pt-4">
          <h4 className="font-semibold text-sm mb-3">Add Exit Rule</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(exitTypeLabels).map(([type, label]) => (
              <Button
                key={type}
                variant="outline"
                size="sm"
                onClick={() => handleAddRule(regime, type as ExitType)}
                className="justify-start"
              >
                <Plus className="h-4 w-4 mr-2" />
                {label}
              </Button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Exit Logic Configuration</CardTitle>
        <CardDescription>
          Define exit rules for each market regime. Multiple rules can be active simultaneously.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RegimeTabs regimes={REGIMES} defaultRegime="TREND" renderContent={renderRegimeContent} />
      </CardContent>
    </Card>
  )
}

/**
 * Type-Specific Config Components
 */
interface ConfigProps {
  config: any
  onChange: (key: string, value: any) => void
}

function TakeProfitConfig({ config, onChange }: ConfigProps) {
  const profitRatio = config.profit_ratio ?? 0.03

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor="profit-ratio">Profit Target</Label>
        <span className="text-sm font-medium">{(profitRatio * 100).toFixed(1)}%</span>
      </div>
      <input
        id="profit-ratio"
        type="range"
        min="0.01"
        max="0.2"
        step="0.005"
        value={profitRatio}
        onChange={(e) => onChange('profit_ratio', Number(e.target.value))}
        className="w-full"
      />
      <p className="text-xs text-muted-foreground">
        Exit when profit reaches this percentage
      </p>
    </div>
  )
}

function TrailingStopConfig({ config, onChange }: ConfigProps) {
  const offset = config.trailing_offset ?? 0.01
  const onlyOffset = config.trailing_only_offset_is_reached ?? true

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="trailing-offset">Trailing Offset</Label>
          <span className="text-sm font-medium">{(offset * 100).toFixed(1)}%</span>
        </div>
        <input
          id="trailing-offset"
          type="range"
          min="0.005"
          max="0.05"
          step="0.001"
          value={offset}
          onChange={(e) => onChange('trailing_offset', Number(e.target.value))}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          Distance from peak price to trigger exit
        </p>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={onlyOffset}
          onChange={(e) => onChange('trailing_only_offset_is_reached', e.target.checked)}
          className="w-4 h-4 rounded border-gray-300"
        />
        <span className="text-sm">Only activate after offset is reached</span>
      </label>
    </div>
  )
}

function StopLossConfig({ config, onChange }: ConfigProps) {
  const stopLoss = config.stop_loss_ratio ?? -0.02

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor="stop-loss">Stop Loss</Label>
        <span className="text-sm font-medium">{(stopLoss * 100).toFixed(1)}%</span>
      </div>
      <input
        id="stop-loss"
        type="range"
        min="-0.1"
        max="-0.005"
        step="0.001"
        value={stopLoss}
        onChange={(e) => onChange('stop_loss_ratio', Number(e.target.value))}
        className="w-full"
      />
      <p className="text-xs text-muted-foreground">
        Exit when loss reaches this percentage (negative value)
      </p>
    </div>
  )
}

function TimeBasedConfig({ config, onChange }: ConfigProps) {
  const maxCandles = config.max_candles_in_trade ?? 24

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor="max-candles">Max Candles in Trade</Label>
        <span className="text-sm font-medium">{maxCandles}</span>
      </div>
      <input
        id="max-candles"
        type="range"
        min="5"
        max="100"
        step="1"
        value={maxCandles}
        onChange={(e) => onChange('max_candles_in_trade', Number(e.target.value))}
        className="w-full"
      />
      <p className="text-xs text-muted-foreground">
        Force exit after this many candles regardless of profit/loss
      </p>
    </div>
  )
}

function RegimeChangeConfig({ config, onChange }: ConfigProps) {
  const exitOnChange = config.exit_on_regime_change ?? true

  return (
    <div className="space-y-2">
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={exitOnChange}
          onChange={(e) => onChange('exit_on_regime_change', e.target.checked)}
          className="w-4 h-4 rounded border-gray-300"
        />
        <span className="text-sm">Exit immediately when regime changes</span>
      </label>
      <p className="text-xs text-muted-foreground">
        Closes position when market regime shifts (e.g., TREND → CONSOLIDATION)
      </p>
    </div>
  )
}

function IndicatorSignalConfig({ config, onChange }: ConfigProps) {
  const expression = config.expression ?? ''
  const description = config.description ?? ''

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="exit-expression">
          Exit Expression (SymPy-compatible)
          <span className="text-destructive ml-1">*</span>
        </Label>
        <Textarea
          id="exit-expression"
          value={expression}
          onChange={(e) => onChange('expression', e.target.value)}
          placeholder="(1h_RSI_14 < 30) | (1h_EMA_20 < 1h_EMA_50)"
          rows={3}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Custom indicator-based exit condition
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="exit-description">Description</Label>
        <Input
          id="exit-description"
          value={description}
          onChange={(e) => onChange('description', e.target.value)}
          placeholder="e.g., Exit on RSI oversold or bearish crossover"
        />
      </div>
    </div>
  )
}

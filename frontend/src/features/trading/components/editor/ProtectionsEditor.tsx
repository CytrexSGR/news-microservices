/**
 * ProtectionsEditor Component
 *
 * Global safety guards that override all regimes
 * Protection types:
 * - StoplossGuard: Prevent trading after X stoploss in Y minutes
 * - MaxDrawdown: Halt trading if drawdown exceeds threshold
 * - LowProfitPairs: Lock pairs with low profit percentage
 * - CooldownPeriod: Force cooldown after losing streaks
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/Button'
import { Plus, Trash2 } from 'lucide-react'
import type { Strategy } from '@/types/strategy'

interface ProtectionsEditorProps {
  strategy: Strategy
  onChange?: (field: string, value: any) => void
}

type ProtectionType = 'StoplossGuard' | 'MaxDrawdown' | 'LowProfitPairs' | 'CooldownPeriod'

interface Protection {
  id: string
  type: ProtectionType
  enabled: boolean
  config: any
}

const protectionTemplates: Record<ProtectionType, Protection> = {
  StoplossGuard: {
    id: '',
    type: 'StoplossGuard',
    enabled: true,
    config: {
      stop_duration_candles: 5,
      trade_limit: 3,
      required_profit: 0.0,
    },
  },
  MaxDrawdown: {
    id: '',
    type: 'MaxDrawdown',
    enabled: true,
    config: {
      max_allowed_drawdown: 0.2,
      lookback_period_candles: 48,
    },
  },
  LowProfitPairs: {
    id: '',
    type: 'LowProfitPairs',
    enabled: true,
    config: {
      required_profit: 0.02,
      lookback_period_candles: 24,
    },
  },
  CooldownPeriod: {
    id: '',
    type: 'CooldownPeriod',
    enabled: true,
    config: {
      stop_duration_candles: 10,
      trade_limit: 2,
    },
  },
}

export function ProtectionsEditor({ strategy, onChange }: ProtectionsEditorProps) {
  const protections: Protection[] = strategy.definition?.protections || []

  const handleAddProtection = (type: ProtectionType) => {
    const newProtection = {
      ...protectionTemplates[type],
      id: `protection_${Date.now()}`,
    }
    onChange?.('protections', [...protections, newProtection])
  }

  const handleRemoveProtection = (id: string) => {
    onChange?.(
      'protections',
      protections.filter((p) => p.id !== id)
    )
  }

  const handleProtectionChange = (id: string, field: string, value: any) => {
    const updated = protections.map((p) =>
      p.id === id ? { ...p, [field]: value } : p
    )
    onChange?.('protections', updated)
  }

  const handleConfigChange = (id: string, key: string, value: any) => {
    const updated = protections.map((p) =>
      p.id === id ? { ...p, config: { ...p.config, [key]: value } } : p
    )
    onChange?.('protections', updated)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Protection Guards</CardTitle>
        <CardDescription>
          Configure global safety mechanisms that override all regime-specific rules
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Info */}
        <div className="p-4 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg">
          <p className="text-sm text-amber-900 dark:text-amber-100">
            <strong>Purpose:</strong> Protections are emergency brakes. They trigger when market
            conditions become too risky, halting trading regardless of signals.
          </p>
        </div>

        {/* Active Protections */}
        <div className="space-y-4">
          {protections.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No protections configured</p>
              <p className="text-xs mt-1">Add protection guards to improve risk management</p>
            </div>
          ) : (
            protections.map((protection) => (
              <div key={protection.id} className="border rounded-lg p-4 space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={protection.enabled ? 'default' : 'secondary'}>
                      {protection.type}
                    </Badge>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={protection.enabled}
                        onChange={(e) =>
                          handleProtectionChange(protection.id, 'enabled', e.target.checked)
                        }
                        className="w-4 h-4 rounded border-gray-300"
                      />
                      <span className="text-sm">Enabled</span>
                    </label>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveProtection(protection.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                {/* Type-Specific Config */}
                {protection.type === 'StoplossGuard' && (
                  <StoplossGuardConfig
                    config={protection.config}
                    onChange={(key, value) => handleConfigChange(protection.id, key, value)}
                  />
                )}

                {protection.type === 'MaxDrawdown' && (
                  <MaxDrawdownConfig
                    config={protection.config}
                    onChange={(key, value) => handleConfigChange(protection.id, key, value)}
                  />
                )}

                {protection.type === 'LowProfitPairs' && (
                  <LowProfitPairsConfig
                    config={protection.config}
                    onChange={(key, value) => handleConfigChange(protection.id, key, value)}
                  />
                )}

                {protection.type === 'CooldownPeriod' && (
                  <CooldownPeriodConfig
                    config={protection.config}
                    onChange={(key, value) => handleConfigChange(protection.id, key, value)}
                  />
                )}
              </div>
            ))
          )}
        </div>

        {/* Add Protection Buttons */}
        <div className="border-t pt-6">
          <h4 className="font-semibold text-sm mb-3">Add Protection Guard</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.keys(protectionTemplates).map((type) => (
              <Button
                key={type}
                variant="outline"
                size="sm"
                onClick={() => handleAddProtection(type as ProtectionType)}
                className="justify-start"
              >
                <Plus className="h-4 w-4 mr-2" />
                {type}
              </Button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * StoplossGuard Config
 * Prevents trading after X stop losses in Y minutes
 */
interface ConfigProps {
  config: any
  onChange: (key: string, value: any) => void
}

function StoplossGuardConfig({ config, onChange }: ConfigProps) {
  const stopDuration = config.stop_duration_candles ?? 5
  const tradeLimit = config.trade_limit ?? 3
  const requiredProfit = config.required_profit ?? 0.0

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Halts trading for {stopDuration} candles after {tradeLimit} stop losses
      </p>

      {/* Stop Duration */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="stop-duration">Stop Duration (candles)</Label>
          <span className="text-sm font-medium">{stopDuration}</span>
        </div>
        <input
          id="stop-duration"
          type="range"
          min="1"
          max="50"
          step="1"
          value={stopDuration}
          onChange={(e) => onChange('stop_duration_candles', Number(e.target.value))}
          className="w-full"
        />
      </div>

      {/* Trade Limit */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="trade-limit">Trade Limit (stop losses before trigger)</Label>
          <span className="text-sm font-medium">{tradeLimit}</span>
        </div>
        <input
          id="trade-limit"
          type="range"
          min="1"
          max="10"
          step="1"
          value={tradeLimit}
          onChange={(e) => onChange('trade_limit', Number(e.target.value))}
          className="w-full"
        />
      </div>

      {/* Required Profit */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="required-profit">Required Profit (override if profitable)</Label>
          <span className="text-sm font-medium">{(requiredProfit * 100).toFixed(1)}%</span>
        </div>
        <input
          id="required-profit"
          type="range"
          min="0"
          max="0.1"
          step="0.001"
          value={requiredProfit}
          onChange={(e) => onChange('required_profit', Number(e.target.value))}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          If overall profit is above this threshold, ignore stop loss limit
        </p>
      </div>
    </div>
  )
}

/**
 * MaxDrawdown Config
 * Halts trading if drawdown exceeds threshold
 */
function MaxDrawdownConfig({ config, onChange }: ConfigProps) {
  const maxDrawdown = config.max_allowed_drawdown ?? 0.2
  const lookbackPeriod = config.lookback_period_candles ?? 48

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Halts trading if drawdown exceeds {(maxDrawdown * 100).toFixed(0)}% in the last{' '}
        {lookbackPeriod} candles
      </p>

      {/* Max Drawdown */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="max-drawdown">Max Allowed Drawdown</Label>
          <span className="text-sm font-medium">{(maxDrawdown * 100).toFixed(0)}%</span>
        </div>
        <input
          id="max-drawdown"
          type="range"
          min="0.05"
          max="0.5"
          step="0.01"
          value={maxDrawdown}
          onChange={(e) => onChange('max_allowed_drawdown', Number(e.target.value))}
          className="w-full"
        />
      </div>

      {/* Lookback Period */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="lookback">Lookback Period (candles)</Label>
          <span className="text-sm font-medium">{lookbackPeriod}</span>
        </div>
        <input
          id="lookback"
          type="range"
          min="10"
          max="200"
          step="1"
          value={lookbackPeriod}
          onChange={(e) => onChange('lookback_period_candles', Number(e.target.value))}
          className="w-full"
        />
      </div>
    </div>
  )
}

/**
 * LowProfitPairs Config
 * Locks pairs with low profit percentage
 */
function LowProfitPairsConfig({ config, onChange }: ConfigProps) {
  const requiredProfit = config.required_profit ?? 0.02
  const lookbackPeriod = config.lookback_period_candles ?? 24

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Locks pairs with less than {(requiredProfit * 100).toFixed(1)}% profit in the last{' '}
        {lookbackPeriod} candles
      </p>

      {/* Required Profit */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="lpp-profit">Required Profit</Label>
          <span className="text-sm font-medium">{(requiredProfit * 100).toFixed(1)}%</span>
        </div>
        <input
          id="lpp-profit"
          type="range"
          min="0"
          max="0.1"
          step="0.001"
          value={requiredProfit}
          onChange={(e) => onChange('required_profit', Number(e.target.value))}
          className="w-full"
        />
      </div>

      {/* Lookback Period */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="lpp-lookback">Lookback Period (candles)</Label>
          <span className="text-sm font-medium">{lookbackPeriod}</span>
        </div>
        <input
          id="lpp-lookback"
          type="range"
          min="10"
          max="100"
          step="1"
          value={lookbackPeriod}
          onChange={(e) => onChange('lookback_period_candles', Number(e.target.value))}
          className="w-full"
        />
      </div>
    </div>
  )
}

/**
 * CooldownPeriod Config
 * Forces cooldown after losing streaks
 */
function CooldownPeriodConfig({ config, onChange }: ConfigProps) {
  const stopDuration = config.stop_duration_candles ?? 10
  const tradeLimit = config.trade_limit ?? 2

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Enforces {stopDuration} candle cooldown after {tradeLimit} consecutive losing trades
      </p>

      {/* Stop Duration */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="cd-duration">Cooldown Duration (candles)</Label>
          <span className="text-sm font-medium">{stopDuration}</span>
        </div>
        <input
          id="cd-duration"
          type="range"
          min="1"
          max="50"
          step="1"
          value={stopDuration}
          onChange={(e) => onChange('stop_duration_candles', Number(e.target.value))}
          className="w-full"
        />
      </div>

      {/* Trade Limit */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="cd-limit">Trade Limit (losing trades before cooldown)</Label>
          <span className="text-sm font-medium">{tradeLimit}</span>
        </div>
        <input
          id="cd-limit"
          type="range"
          min="1"
          max="10"
          step="1"
          value={tradeLimit}
          onChange={(e) => onChange('trade_limit', Number(e.target.value))}
          className="w-full"
        />
      </div>
    </div>
  )
}

/**
 * RiskManagementEditor Component
 *
 * Per-Regime Risk Configuration
 * 3 Sub-Sections:
 * 1. Stop Loss: Dynamic ATR-based, trailing stops
 * 2. Position Sizing: Percent-risk, Kelly criterion, volatility-adjusted
 * 3. Leverage: Regime-dependent (1x-3x)
 *
 * Uses RegimeTabs for uniform UX
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { RegimeTabs } from './shared/RegimeTabs'
import type { Strategy } from '@/types/strategy'
import type { RegimeType } from './shared/RegimeTabs'

interface RiskManagementEditorProps {
  strategy: Strategy
  onChange?: (field: string, value: any) => void
}

interface StopLossConfig {
  method: 'fixed' | 'atr_based' | 'trailing' | 'formula'
  fixed_ratio?: number
  atr_multiplier?: number
  trailing_offset?: number
  formula?: string
}

interface PositionSizingConfig {
  method: 'percent_risk' | 'kelly' | 'volatility_adjusted' | 'formula'
  percent_risk?: number
  kelly_fraction?: number
  volatility_window?: number
  formula?: string
}

interface LeverageConfig {
  max_leverage: number
  adaptive: boolean
  formula?: string
}

interface RegimeRiskManagement {
  regime: RegimeType
  stop_loss: StopLossConfig
  position_sizing: PositionSizingConfig
  leverage: LeverageConfig
}

const REGIMES: RegimeType[] = ['TREND', 'CONSOLIDATION', 'HIGH_VOLATILITY']

export function RiskManagementEditor({ strategy, onChange }: RiskManagementEditorProps) {
  const riskManagement: Record<RegimeType, RegimeRiskManagement> = strategy.definition
    ?.riskManagement || {
    TREND: {
      regime: 'TREND',
      stop_loss: { method: 'atr_based', atr_multiplier: 2.0 },
      position_sizing: { method: 'percent_risk', percent_risk: 0.02 },
      leverage: { max_leverage: 2, adaptive: true },
    },
    CONSOLIDATION: {
      regime: 'CONSOLIDATION',
      stop_loss: { method: 'fixed', fixed_ratio: -0.015 },
      position_sizing: { method: 'percent_risk', percent_risk: 0.01 },
      leverage: { max_leverage: 1, adaptive: false },
    },
    HIGH_VOLATILITY: {
      regime: 'HIGH_VOLATILITY',
      stop_loss: { method: 'atr_based', atr_multiplier: 3.0 },
      position_sizing: { method: 'volatility_adjusted', volatility_window: 20 },
      leverage: { max_leverage: 1, adaptive: true },
    },
  }

  const handleStopLossChange = (regime: RegimeType, field: string, value: any) => {
    const updated = {
      ...riskManagement[regime],
      stop_loss: { ...riskManagement[regime].stop_loss, [field]: value },
    }
    onChange?.(`riskManagement.${regime}`, updated)
  }

  const handlePositionSizingChange = (regime: RegimeType, field: string, value: any) => {
    const updated = {
      ...riskManagement[regime],
      position_sizing: { ...riskManagement[regime].position_sizing, [field]: value },
    }
    onChange?.(`riskManagement.${regime}`, updated)
  }

  const handleLeverageChange = (regime: RegimeType, field: string, value: any) => {
    const updated = {
      ...riskManagement[regime],
      leverage: { ...riskManagement[regime].leverage, [field]: value },
    }
    onChange?.(`riskManagement.${regime}`, updated)
  }

  const renderRegimeContent = (regime: RegimeType) => {
    const risk = riskManagement[regime]

    return (
      <div className="space-y-8">
        {/* Info Banner */}
        <div className="p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-900 dark:text-red-100">
            <strong>{regime} Regime:</strong>{' '}
            {regime === 'TREND' && 'Higher leverage, wider stops, aggressive sizing'}
            {regime === 'CONSOLIDATION' && 'Lower leverage, tight stops, conservative sizing'}
            {regime === 'HIGH_VOLATILITY' && 'Minimal leverage, dynamic stops, volatility-based sizing'}
          </p>
        </div>

        {/* Section 1: Stop Loss */}
        <div className="space-y-4 border-b pb-6">
          <h4 className="font-semibold text-lg">1. Stop Loss Configuration</h4>

          <div className="space-y-2">
            <Label htmlFor={`${regime}-sl-method`}>Stop Loss Method</Label>
            <select
              id={`${regime}-sl-method`}
              value={risk.stop_loss.method}
              onChange={(e) => handleStopLossChange(regime, 'method', e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="fixed">Fixed Percentage</option>
              <option value="atr_based">ATR-Based Dynamic</option>
              <option value="trailing">Trailing Stop</option>
              <option value="formula">Custom Formula</option>
            </select>
          </div>

          {risk.stop_loss.method === 'fixed' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`${regime}-sl-fixed`}>Fixed Stop Loss</Label>
                <span className="text-sm font-medium">
                  {((risk.stop_loss.fixed_ratio ?? -0.02) * 100).toFixed(1)}%
                </span>
              </div>
              <input
                id={`${regime}-sl-fixed`}
                type="range"
                min="-0.1"
                max="-0.005"
                step="0.001"
                value={risk.stop_loss.fixed_ratio ?? -0.02}
                onChange={(e) => handleStopLossChange(regime, 'fixed_ratio', Number(e.target.value))}
                className="w-full"
              />
            </div>
          )}

          {risk.stop_loss.method === 'atr_based' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`${regime}-sl-atr`}>ATR Multiplier</Label>
                <span className="text-sm font-medium">
                  {(risk.stop_loss.atr_multiplier ?? 2.0).toFixed(1)}x
                </span>
              </div>
              <input
                id={`${regime}-sl-atr`}
                type="range"
                min="0.5"
                max="5"
                step="0.1"
                value={risk.stop_loss.atr_multiplier ?? 2.0}
                onChange={(e) => handleStopLossChange(regime, 'atr_multiplier', Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Stop loss = Entry price - (ATR × Multiplier)
              </p>
            </div>
          )}

          {risk.stop_loss.method === 'trailing' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`${regime}-sl-trailing`}>Trailing Offset</Label>
                <span className="text-sm font-medium">
                  {((risk.stop_loss.trailing_offset ?? 0.01) * 100).toFixed(1)}%
                </span>
              </div>
              <input
                id={`${regime}-sl-trailing`}
                type="range"
                min="0.005"
                max="0.05"
                step="0.001"
                value={risk.stop_loss.trailing_offset ?? 0.01}
                onChange={(e) => handleStopLossChange(regime, 'trailing_offset', Number(e.target.value))}
                className="w-full"
              />
            </div>
          )}

          {risk.stop_loss.method === 'formula' && (
            <div className="space-y-2">
              <Label htmlFor={`${regime}-sl-formula`}>Custom Formula (SymPy)</Label>
              <Textarea
                id={`${regime}-sl-formula`}
                value={risk.stop_loss.formula ?? ''}
                onChange={(e) => handleStopLossChange(regime, 'formula', e.target.value)}
                placeholder="entry_price - (1h_ATR_14 * 2.5)"
                rows={2}
                className="font-mono text-sm"
              />
            </div>
          )}
        </div>

        {/* Section 2: Position Sizing */}
        <div className="space-y-4 border-b pb-6">
          <h4 className="font-semibold text-lg">2. Position Sizing</h4>

          <div className="space-y-2">
            <Label htmlFor={`${regime}-ps-method`}>Position Sizing Method</Label>
            <select
              id={`${regime}-ps-method`}
              value={risk.position_sizing.method}
              onChange={(e) => handlePositionSizingChange(regime, 'method', e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="percent_risk">Percent Risk</option>
              <option value="kelly">Kelly Criterion</option>
              <option value="volatility_adjusted">Volatility Adjusted</option>
              <option value="formula">Custom Formula</option>
            </select>
          </div>

          {risk.position_sizing.method === 'percent_risk' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`${regime}-ps-percent`}>Risk Per Trade</Label>
                <span className="text-sm font-medium">
                  {((risk.position_sizing.percent_risk ?? 0.02) * 100).toFixed(1)}%
                </span>
              </div>
              <input
                id={`${regime}-ps-percent`}
                type="range"
                min="0.005"
                max="0.05"
                step="0.001"
                value={risk.position_sizing.percent_risk ?? 0.02}
                onChange={(e) => handlePositionSizingChange(regime, 'percent_risk', Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Position size = (Account × Risk%) / (Entry - Stop Loss)
              </p>
            </div>
          )}

          {risk.position_sizing.method === 'kelly' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`${regime}-ps-kelly`}>Kelly Fraction</Label>
                <span className="text-sm font-medium">
                  {((risk.position_sizing.kelly_fraction ?? 0.25) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                id={`${regime}-ps-kelly`}
                type="range"
                min="0.1"
                max="1"
                step="0.05"
                value={risk.position_sizing.kelly_fraction ?? 0.25}
                onChange={(e) => handlePositionSizingChange(regime, 'kelly_fraction', Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Uses Kelly Criterion (win_rate, avg_win, avg_loss from backtest)
              </p>
            </div>
          )}

          {risk.position_sizing.method === 'volatility_adjusted' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`${regime}-ps-vol`}>Volatility Window (candles)</Label>
                <span className="text-sm font-medium">
                  {risk.position_sizing.volatility_window ?? 20}
                </span>
              </div>
              <input
                id={`${regime}-ps-vol`}
                type="range"
                min="10"
                max="50"
                step="1"
                value={risk.position_sizing.volatility_window ?? 20}
                onChange={(e) => handlePositionSizingChange(regime, 'volatility_window', Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Size inversely proportional to volatility (reduce size in volatile markets)
              </p>
            </div>
          )}

          {risk.position_sizing.method === 'formula' && (
            <div className="space-y-2">
              <Label htmlFor={`${regime}-ps-formula`}>Custom Formula (SymPy)</Label>
              <Textarea
                id={`${regime}-ps-formula`}
                value={risk.position_sizing.formula ?? ''}
                onChange={(e) => handlePositionSizingChange(regime, 'formula', e.target.value)}
                placeholder="(account_balance * 0.02) / abs(entry_price - stop_loss)"
                rows={2}
                className="font-mono text-sm"
              />
            </div>
          )}
        </div>

        {/* Section 3: Leverage */}
        <div className="space-y-4">
          <h4 className="font-semibold text-lg">3. Leverage Settings</h4>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor={`${regime}-leverage`}>Max Leverage</Label>
              <span className="text-sm font-medium">
                {risk.leverage.max_leverage ?? 1}x
              </span>
            </div>
            <input
              id={`${regime}-leverage`}
              type="range"
              min="1"
              max="5"
              step="0.5"
              value={risk.leverage.max_leverage ?? 1}
              onChange={(e) => handleLeverageChange(regime, 'max_leverage', Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Maximum leverage allowed for this regime (1x = no leverage)
            </p>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={risk.leverage.adaptive ?? false}
              onChange={(e) => handleLeverageChange(regime, 'adaptive', e.target.checked)}
              className="w-4 h-4 rounded border-gray-300"
            />
            <span className="text-sm">Adaptive Leverage (based on confidence/volatility)</span>
          </label>

          {risk.leverage.adaptive && (
            <div className="space-y-2">
              <Label htmlFor={`${regime}-leverage-formula`}>Leverage Formula (optional)</Label>
              <Textarea
                id={`${regime}-leverage-formula`}
                value={risk.leverage.formula ?? ''}
                onChange={(e) => handleLeverageChange(regime, 'formula', e.target.value)}
                placeholder="max_leverage * (1 - (1h_ATR_14 / price))"
                rows={2}
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Dynamic leverage calculation (uses max_leverage as upper bound)
              </p>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Management Configuration</CardTitle>
        <CardDescription>
          Configure stop loss, position sizing, and leverage for each market regime
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RegimeTabs regimes={REGIMES} defaultRegime="TREND" renderContent={renderRegimeContent} />
      </CardContent>
    </Card>
  )
}

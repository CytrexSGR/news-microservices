/**
 * Backtest Dialog
 *
 * Dialog for configuring and starting Strategy Lab backtests with unified market data.
 *
 * The dialog closes immediately when the backtest is started.
 * Progress is shown on the parent page (StrategyOverview - Backtests tab).
 *
 * Features:
 * - Symbol selection (BTCUSDT, ETHUSDT, XRPUSDT, etc.)
 * - Timeframe selection (1h, 4h, 1d)
 * - Date range picker
 * - Data availability indicator (shows if data is in database)
 * - Initial capital input
 * - Buy & Hold comparison toggle
 * - Regime breakdown toggle
 *
 * Part of Unified Market Data Architecture (Phase 5.3)
 */

import { useState, useEffect, useMemo } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  PlayCircle,
  Calendar,
  DollarSign,
  BarChart3,
  TrendingUp,
  Database,
  Cloud,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Info,
  Settings2,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useSymbolAvailability } from '@/hooks/useDataManagement'
import type { Strategy } from '@/types/strategy'
import type {
  StrategyLabBacktestRequest,
  IndicatorOverride,
  ModuleTestMode,
} from '@/types/backtest'
import type { CandleInterval } from '@/types/data-management'
import { IndicatorOverridePanel } from './IndicatorOverridePanel'
import { ModuleTestPanel, type ModuleTestConfig } from './ModuleTestPanel'

// Available symbols for backtesting
const AVAILABLE_SYMBOLS = [
  { value: 'BTCUSDT', label: 'BTC/USDT - Bitcoin' },
  { value: 'ETHUSDT', label: 'ETH/USDT - Ethereum' },
  { value: 'XRPUSDT', label: 'XRP/USDT - Ripple' },
  { value: 'SOLUSDT', label: 'SOL/USDT - Solana' },
  { value: 'ADAUSDT', label: 'ADA/USDT - Cardano' },
  { value: 'DOGEUSDT', label: 'DOGE/USDT - Dogecoin' },
  { value: 'LINKUSDT', label: 'LINK/USDT - Chainlink' },
  { value: 'AVAXUSDT', label: 'AVAX/USDT - Avalanche' },
  { value: 'DOTUSDT', label: 'DOT/USDT - Polkadot' },
  { value: 'MATICUSDT', label: 'MATIC/USDT - Polygon' },
]

// Available timeframes (all Bybit-compatible intervals)
const AVAILABLE_TIMEFRAMES = [
  { value: '1m', label: '1 Minute', dbInterval: '1min' as CandleInterval },
  { value: '5m', label: '5 Minutes', dbInterval: '5min' as CandleInterval },
  { value: '15m', label: '15 Minutes', dbInterval: '15min' as CandleInterval },
  { value: '30m', label: '30 Minutes', dbInterval: '30min' as CandleInterval },
  { value: '1h', label: '1 Hour', dbInterval: '1hour' as CandleInterval },
  { value: '4h', label: '4 Hours', dbInterval: '4hour' as CandleInterval },
  { value: '1d', label: '1 Day', dbInterval: '1day' as CandleInterval },
  { value: '1w', label: '1 Week', dbInterval: '1day' as CandleInterval }, // 1w uses 1day data
]

// Convert backtest timeframe to database interval format
const getDbInterval = (timeframe: string): CandleInterval => {
  const tf = AVAILABLE_TIMEFRAMES.find(t => t.value === timeframe)
  return tf?.dbInterval || '1hour'
}

// Helper function to get higher timeframes based on primary selection
const getHigherTimeframes = (primary: string): string[] => {
  const hierarchy: Record<string, string[]> = {
    '1m': ['5m', '15m', '1h', '4h', '1d'],
    '5m': ['15m', '1h', '4h', '1d'],
    '15m': ['30m', '1h', '4h', '1d'],
    '30m': ['1h', '4h', '1d'],
    '1h': ['4h', '1d'],
    '4h': ['1d', '1w'],
    '1d': ['1w'],
    '1w': [],
  }
  return hierarchy[primary] || []
}

// Default date range (last 30 days)
const getDefaultDates = () => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)

  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  }
}

interface BacktestDialogProps {
  strategy: Strategy
  isOpen: boolean
  onClose: () => void
  /** Callback when backtest is started - receives the request config */
  onStartBacktest: (request: StrategyLabBacktestRequest) => void
  /** Initial symbol to pre-select (e.g., from StrategyOverview) */
  initialSymbol?: string
  /** Initial timeframe to pre-select (e.g., from StrategyOverview) */
  initialTimeframe?: string
}

export function BacktestDialog({
  strategy,
  isOpen,
  onClose,
  onStartBacktest,
  initialSymbol,
  initialTimeframe
}: BacktestDialogProps) {
  const defaultDates = getDefaultDates()

  // Form state - use initial values if provided
  const [symbol, setSymbol] = useState(initialSymbol || 'BTCUSDT')
  const [primaryTimeframe, setPrimaryTimeframe] = useState(initialTimeframe || '1h')
  const [startDate, setStartDate] = useState(defaultDates.start)
  const [endDate, setEndDate] = useState(defaultDates.end)
  const [initialCapital, setInitialCapital] = useState(10000)
  const [includeBuyHold, setIncludeBuyHold] = useState(true)
  const [includeRegimeBreakdown, setIncludeRegimeBreakdown] = useState(true)

  // Advanced Mode: Indicator Overrides (Phase 2)
  const [advancedModeOpen, setAdvancedModeOpen] = useState(false)
  const [indicatorOverrides, setIndicatorOverrides] = useState<IndicatorOverride[]>([])

  // Module Test Mode (Phase 3)
  const [moduleTestPanelOpen, setModuleTestPanelOpen] = useState(false)
  const [moduleTestConfig, setModuleTestConfig] = useState<ModuleTestConfig>({
    mode: 'full',
  })

  // Check data availability in unified database
  const dbInterval = useMemo(() => getDbInterval(primaryTimeframe), [primaryTimeframe])
  const { data: availabilityData, isLoading: isCheckingAvailability } = useSymbolAvailability(
    symbol,
    dbInterval,
    startDate,
    endDate,
    isOpen && !!symbol && !!startDate && !!endDate
  )

  // Extract availability info
  const availability = availabilityData?.results?.[0]
  const coveragePercent = availability?.coverage_percent ?? 0
  const dataSource = coveragePercent >= 95 ? 'database' : 'api'

  // Reset form when dialog opens - apply initial values
  useEffect(() => {
    if (isOpen) {
      const dates = getDefaultDates()
      setStartDate(dates.start)
      setEndDate(dates.end)
      // Apply initial symbol/timeframe if provided
      if (initialSymbol) {
        setSymbol(initialSymbol)
      }
      if (initialTimeframe) {
        setPrimaryTimeframe(initialTimeframe)
      }
      // Reset advanced mode state
      setAdvancedModeOpen(false)
      setIndicatorOverrides([])
      // Reset module test state
      setModuleTestPanelOpen(false)
      setModuleTestConfig({ mode: 'full' })
    }
  }, [isOpen, initialSymbol, initialTimeframe])

  const handleSubmit = () => {
    const request: StrategyLabBacktestRequest = {
      strategy_id: strategy.id,
      symbol,
      start_date: startDate,
      end_date: endDate,
      primary_timeframe: primaryTimeframe,
      higher_timeframes: getHigherTimeframes(primaryTimeframe),
      config: {
        initial_capital: initialCapital,
      },
      include_buy_hold: includeBuyHold,
      include_regime_breakdown: includeRegimeBreakdown,
      // Include indicator overrides if any are configured (Phase 2)
      indicator_overrides: indicatorOverrides.length > 0 ? indicatorOverrides : undefined,
      // Include module test config if not full strategy (Phase 3)
      module_test_mode: moduleTestConfig.mode !== 'full' ? moduleTestConfig.mode : undefined,
      module_test_params: moduleTestConfig.mode !== 'full' ? {
        hold_bars: moduleTestConfig.hold_bars,
        num_random_entries: moduleTestConfig.num_random_entries,
        entry_interval: moduleTestConfig.entry_interval,
      } : undefined,
    }

    // Pass the request to parent and close dialog immediately
    onStartBacktest(request)
    onClose()
  }

  // Validate dates
  const isDateRangeValid = new Date(startDate) < new Date(endDate)
  const daysDiff = Math.ceil(
    (new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24)
  )

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PlayCircle className="h-5 w-5" />
            Run Backtest
          </DialogTitle>
          <DialogDescription>
            Run a historical backtest for <strong>{strategy.name}</strong> using unified market data
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Market Data Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Market Data
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Symbol Selection */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">Trading Pair</Label>
                  <Select value={symbol} onValueChange={setSymbol}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_SYMBOLS.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Timeframe Selection */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">Primary Timeframe</Label>
                  <Select value={primaryTimeframe} onValueChange={setPrimaryTimeframe}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_TIMEFRAMES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <p className="text-xs text-muted-foreground">
                Select the trading pair and candlestick timeframe for backtesting.
                {primaryTimeframe === '1h' && ' Higher timeframes (4h, 1d) will be included for MTF analysis.'}
              </p>

              {/* Data Availability Indicator */}
              <div className="mt-4 p-3 rounded-lg border bg-muted/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {isCheckingAvailability ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Checking data availability...</span>
                      </>
                    ) : dataSource === 'database' ? (
                      <>
                        <Database className="h-4 w-4 text-green-500" />
                        <span className="text-sm">
                          <span className="font-medium text-green-600">Database</span>
                          <span className="text-muted-foreground"> - {coveragePercent.toFixed(0)}% coverage</span>
                        </span>
                      </>
                    ) : (
                      <>
                        <Cloud className="h-4 w-4 text-amber-500" />
                        <span className="text-sm">
                          <span className="font-medium text-amber-600">Bybit API</span>
                          {coveragePercent > 0 && (
                            <span className="text-muted-foreground"> - {coveragePercent.toFixed(0)}% in database</span>
                          )}
                        </span>
                      </>
                    )}
                  </div>

                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-6 w-6">
                          <Info className="h-3.5 w-3.5 text-muted-foreground" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="left" className="max-w-xs">
                        {dataSource === 'database' ? (
                          <p>Data will be loaded from the unified database for faster backtesting.</p>
                        ) : (
                          <div className="space-y-2">
                            <p>Data will be fetched from Bybit API (may be slower).</p>
                            <p className="text-xs">
                              <Link
                                to="/trading/data-management"
                                className="text-primary hover:underline"
                                onClick={onClose}
                              >
                                Backfill data →
                              </Link>
                            </p>
                          </div>
                        )}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>

                {/* Show recommendation for partial coverage */}
                {!isCheckingAvailability && coveragePercent > 0 && coveragePercent < 95 && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-amber-600">
                    <AlertTriangle className="h-3 w-3" />
                    <span>
                      Partial data in database.
                      <Link
                        to="/trading/data-management"
                        className="ml-1 text-primary hover:underline"
                        onClick={onClose}
                      >
                        Backfill to improve speed
                      </Link>
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Date Range */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Date Range
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium mb-2 block">Start Date</Label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium mb-2 block">End Date</Label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>

              {!isDateRangeValid && (
                <p className="text-sm text-destructive">
                  End date must be after start date
                </p>
              )}

              {isDateRangeValid && (
                <p className="text-xs text-muted-foreground">
                  Backtesting period: {daysDiff} days
                  {daysDiff > 90 && ' (longer periods may take more time to fetch data)'}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Backtest Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Backtest Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm font-medium mb-2 block">Initial Capital (USD)</Label>
                <Input
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Number(e.target.value))}
                  min={100}
                  max={10000000}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Starting portfolio value for the backtest
                </p>
              </div>

              <div className="space-y-3 pt-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="buyHold"
                    checked={includeBuyHold}
                    onCheckedChange={(checked) => setIncludeBuyHold(checked === true)}
                  />
                  <Label htmlFor="buyHold" className="text-sm font-medium cursor-pointer">
                    Include Buy & Hold Comparison
                  </Label>
                </div>
                <p className="text-xs text-muted-foreground ml-6">
                  Compare strategy performance against simple buy-and-hold benchmark
                </p>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="regimeBreakdown"
                    checked={includeRegimeBreakdown}
                    onCheckedChange={(checked) => setIncludeRegimeBreakdown(checked === true)}
                  />
                  <Label htmlFor="regimeBreakdown" className="text-sm font-medium cursor-pointer">
                    Include Regime Breakdown
                  </Label>
                </div>
                <p className="text-xs text-muted-foreground ml-6">
                  Analyze performance across different market regimes (TREND, CONSOLIDATION,
                  HIGH_VOLATILITY)
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Advanced Mode: Indicator Overrides (Phase 2) */}
          {strategy.definition?.indicators && strategy.definition.indicators.length > 0 && (
            <IndicatorOverridePanel
              indicators={strategy.definition.indicators}
              overrides={indicatorOverrides}
              onOverridesChange={setIndicatorOverrides}
              isExpanded={advancedModeOpen}
              onExpandedChange={setAdvancedModeOpen}
            />
          )}

          {/* Module Test Mode (Phase 3) */}
          <ModuleTestPanel
            config={moduleTestConfig}
            onConfigChange={setModuleTestConfig}
            isExpanded={moduleTestPanelOpen}
            onExpandedChange={setModuleTestPanelOpen}
          />

          {/* Strategy Info */}
          <Card className="bg-muted/50">
            <CardContent className="pt-4">
              <div className="flex items-start gap-3">
                <BarChart3 className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="flex-1">
                  <div className="font-medium">{strategy.name}</div>
                  <div className="text-sm text-muted-foreground">
                    Version {strategy.version} &bull;{' '}
                    {Object.keys(strategy.definition?.logic || {}).length} regimes &bull;{' '}
                    {strategy.definition?.indicators?.length || 0} indicators
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!isDateRangeValid}
              className="min-w-32"
            >
              <PlayCircle className="mr-2 h-4 w-4" />
              Run Backtest
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

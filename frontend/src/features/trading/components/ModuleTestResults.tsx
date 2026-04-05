/**
 * Module Test Results Component
 *
 * Displays results from module isolation tests with mode-specific metrics,
 * insights, and recommendations.
 *
 * Part of Backtest Comprehensive Upgrade - Phase 3
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Crosshair,
  LogOut,
  Shield,
  TrendingUp,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  Lightbulb,
  BarChart3,
  Target,
  Clock,
  Percent,
} from 'lucide-react'
import type {
  ModuleTestMode,
  ModuleTestResult,
  EntryTestMetrics,
  ExitTestMetrics,
  RiskTestMetrics,
  RegimeTestMetrics,
} from '@/types/backtest'

// Mode info mapping
const MODE_INFO: Record<
  Exclude<ModuleTestMode, 'full'>,
  { label: string; icon: React.ElementType; color: string }
> = {
  entry: { label: 'Entry Logic Test', icon: Crosshair, color: 'bg-green-500' },
  exit: { label: 'Exit Logic Test', icon: LogOut, color: 'bg-amber-500' },
  risk: { label: 'Risk Management Test', icon: Shield, color: 'bg-red-500' },
  regime: { label: 'Regime Detection Test', icon: TrendingUp, color: 'bg-purple-500' },
}

// Metric value formatter
function formatMetricValue(value: number | string | null | undefined, format: 'percent' | 'number' | 'decimal' = 'number'): string {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'string') return value

  switch (format) {
    case 'percent':
      return `${(value * 100).toFixed(1)}%`
    case 'decimal':
      return value.toFixed(2)
    default:
      return value.toLocaleString()
  }
}

// Metric card component
interface MetricCardProps {
  label: string
  value: string
  icon?: React.ElementType
  description?: string
  variant?: 'default' | 'success' | 'warning' | 'danger'
}

function MetricCard({ label, value, icon: Icon, description, variant = 'default' }: MetricCardProps) {
  const variantClasses = {
    default: 'border-border',
    success: 'border-green-500/50 bg-green-50/50 dark:bg-green-950/20',
    warning: 'border-amber-500/50 bg-amber-50/50 dark:bg-amber-950/20',
    danger: 'border-red-500/50 bg-red-50/50 dark:bg-red-950/20',
  }

  return (
    <div className={`p-3 rounded-lg border ${variantClasses[variant]}`}>
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <div className="text-lg font-semibold">{value}</div>
      {description && (
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      )}
    </div>
  )
}

// Entry Test Results
function EntryTestResults({ metrics }: { metrics: EntryTestMetrics }) {
  const winRateVariant =
    metrics.entry_win_rate >= 0.6 ? 'success' : metrics.entry_win_rate >= 0.4 ? 'warning' : 'danger'

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="Total Entries"
          value={metrics.total_entries.toString()}
          icon={Target}
        />
        <MetricCard
          label="Entry Win Rate"
          value={formatMetricValue(metrics.entry_win_rate, 'percent')}
          icon={Percent}
          variant={winRateVariant}
        />
        <MetricCard
          label="Avg Entry Quality"
          value={formatMetricValue(metrics.avg_entry_quality, 'decimal')}
          icon={BarChart3}
          description="1.0 = perfect timing"
        />
        <MetricCard
          label="False Signals"
          value={metrics.false_signals.toString()}
          icon={AlertTriangle}
          variant={metrics.false_signals > metrics.total_entries * 0.3 ? 'danger' : 'default'}
        />
      </div>

      {metrics.avg_bars_to_profit !== null && (
        <MetricCard
          label="Avg Bars to Profit"
          value={metrics.avg_bars_to_profit.toFixed(1)}
          icon={Clock}
          description="Average bars until position becomes profitable"
        />
      )}

      {Object.keys(metrics.entries_by_regime).length > 0 && (
        <div className="p-3 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Entries by Regime</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(metrics.entries_by_regime).map(([regime, count]) => (
              <Badge key={regime} variant="outline">
                {regime}: {count}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Exit Test Results
function ExitTestResults({ metrics }: { metrics: ExitTestMetrics }) {
  const optimalExitVariant =
    metrics.optimal_exit_rate >= 70 ? 'success' : metrics.optimal_exit_rate >= 50 ? 'warning' : 'danger'

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="Total Exits"
          value={metrics.total_exits.toString()}
          icon={LogOut}
        />
        <MetricCard
          label="Optimal Exit Rate"
          value={`${metrics.optimal_exit_rate.toFixed(1)}%`}
          icon={Target}
          variant={optimalExitVariant}
        />
        <MetricCard
          label="Timing Error"
          value={`${metrics.avg_exit_timing_error.toFixed(1)} bars`}
          icon={Clock}
          description="Avg bars from optimal"
        />
        <MetricCard
          label="Premature Exits"
          value={metrics.premature_exits.toString()}
          icon={AlertTriangle}
          variant={metrics.premature_exits > metrics.total_exits * 0.4 ? 'danger' : 'default'}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          label="Late Exits"
          value={metrics.late_exits.toString()}
          icon={Clock}
          description="Exits after price reversal"
        />
        {Object.keys(metrics.exits_by_reason).length > 0 && (
          <div className="p-3 rounded-lg border">
            <div className="flex items-center gap-2 mb-2">
              <Info className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Exits by Reason</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(metrics.exits_by_reason).map(([reason, count]) => (
                <Badge key={reason} variant="outline">
                  {reason}: {count}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Risk Test Results
function RiskTestResults({ metrics }: { metrics: RiskTestMetrics }) {
  const riskRewardVariant =
    metrics.avg_risk_reward_actual >= 2 ? 'success' : metrics.avg_risk_reward_actual >= 1 ? 'warning' : 'danger'

  const totalHits = metrics.stop_loss_hits + metrics.take_profit_hits
  const slHitRate = totalHits > 0 ? (metrics.stop_loss_hits / totalHits) : 0
  const tpHitRate = totalHits > 0 ? (metrics.take_profit_hits / totalHits) : 0

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="Stop-Loss Hits"
          value={metrics.stop_loss_hits.toString()}
          icon={Shield}
          variant={slHitRate > 0.5 ? 'danger' : 'default'}
        />
        <MetricCard
          label="Take-Profit Hits"
          value={metrics.take_profit_hits.toString()}
          icon={CheckCircle}
          variant={tpHitRate >= 0.4 ? 'success' : 'default'}
        />
        <MetricCard
          label="Actual R/R Ratio"
          value={metrics.avg_risk_reward_actual.toFixed(2)}
          icon={BarChart3}
          variant={riskRewardVariant}
        />
        <MetricCard
          label="Max Consecutive SL"
          value={metrics.max_consecutive_stops.toString()}
          icon={AlertTriangle}
          variant={metrics.max_consecutive_stops >= 5 ? 'danger' : 'default'}
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <MetricCard
          label="SL Effectiveness"
          value={`${metrics.stop_loss_effectiveness.toFixed(1)}%`}
          icon={Shield}
          description="SL prevented larger losses"
        />
        <MetricCard
          label="TP Effectiveness"
          value={`${metrics.take_profit_effectiveness.toFixed(1)}%`}
          icon={CheckCircle}
          description="TP captured optimal exit"
        />
        <MetricCard
          label="Position Sizing"
          value={`${metrics.position_sizing_accuracy.toFixed(1)}%`}
          icon={Target}
          description="Matched target risk"
        />
      </div>
    </div>
  )
}

// Regime Test Results
function RegimeTestResults({ metrics }: { metrics: RegimeTestMetrics }) {
  const accuracyVariant =
    metrics.detection_accuracy >= 70 ? 'success' : metrics.detection_accuracy >= 50 ? 'warning' : 'danger'

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <MetricCard
          label="Total Bars"
          value={metrics.total_bars.toString()}
          icon={Clock}
        />
        <MetricCard
          label="Detection Accuracy"
          value={`${metrics.detection_accuracy.toFixed(1)}%`}
          icon={Target}
          variant={accuracyVariant}
        />
        <MetricCard
          label="Regime Changes"
          value={metrics.regime_changes_detected.toString()}
          icon={TrendingUp}
          description="Transitions detected"
        />
      </div>

      {/* Regime distribution */}
      {Object.keys(metrics.regime_distribution).length > 0 && (
        <div className="p-3 rounded-lg border">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Time in Each Regime</span>
          </div>
          <div className="space-y-2">
            {Object.entries(metrics.regime_distribution).map(([regime, pct]) => {
              const percentage = pct as number
              return (
                <div key={regime} className="flex items-center gap-2">
                  <span className="text-sm w-32 truncate">{regime}</span>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-sm w-12 text-right">{percentage.toFixed(0)}%</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Average regime duration */}
      {Object.keys(metrics.avg_regime_duration_bars).length > 0 && (
        <div className="p-3 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Avg Regime Duration (bars)</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(metrics.avg_regime_duration_bars).map(([regime, duration]) => (
              <Badge key={regime} variant="outline">
                {regime}: {(duration as number).toFixed(1)}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Additional metrics */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          label="False Regime Changes"
          value={metrics.false_regime_changes.toString()}
          icon={AlertTriangle}
          variant={metrics.false_regime_changes > metrics.regime_changes_detected * 0.3 ? 'warning' : 'default'}
          description="Quick reversals (noise)"
        />
        <MetricCard
          label="Trend Correlation"
          value={metrics.regime_vs_trend_correlation.toFixed(2)}
          icon={TrendingUp}
          variant={metrics.regime_vs_trend_correlation >= 0.7 ? 'success' : metrics.regime_vs_trend_correlation >= 0.4 ? 'warning' : 'danger'}
          description="TREND vs actual trending"
        />
      </div>
    </div>
  )
}

// Insights and Recommendations Section
function InsightsSection({
  insights,
  recommendations,
}: {
  insights: string[]
  recommendations: string[]
}) {
  if (insights.length === 0 && recommendations.length === 0) return null

  return (
    <div className="space-y-4">
      {/* Insights */}
      {insights.length > 0 && (
        <div className="p-4 rounded-lg border bg-blue-50/50 dark:bg-blue-950/20">
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-blue-700 dark:text-blue-400">Key Insights</span>
          </div>
          <ul className="space-y-2">
            {insights.map((insight, idx) => (
              <li key={idx} className="text-sm flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="p-4 rounded-lg border bg-amber-50/50 dark:bg-amber-950/20">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="h-4 w-4 text-amber-600" />
            <span className="font-medium text-amber-700 dark:text-amber-400">
              Recommendations
            </span>
          </div>
          <ul className="space-y-2">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="text-sm flex items-start gap-2">
                <span className="text-amber-500 mt-1">→</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// Main Component
interface ModuleTestResultsProps {
  result: ModuleTestResult
}

export function ModuleTestResults({ result }: ModuleTestResultsProps) {
  const modeInfo = MODE_INFO[result.test_mode as Exclude<ModuleTestMode, 'full'>]

  if (!modeInfo) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">Unknown test mode: {result.test_mode}</p>
        </CardContent>
      </Card>
    )
  }

  const Icon = modeInfo.icon

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded ${modeInfo.color}`}>
              <Icon className="h-4 w-4 text-white" />
            </div>
            <span>{modeInfo.label} Results</span>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant={result.success ? 'default' : 'destructive'}>
                  {result.success ? 'Completed' : 'Issues Found'}
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                {result.success
                  ? 'Test completed successfully'
                  : 'Test completed with warnings or issues'}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Mode-specific metrics */}
        {result.test_mode === 'entry' && result.entry_metrics && (
          <EntryTestResults metrics={result.entry_metrics} />
        )}
        {result.test_mode === 'exit' && result.exit_metrics && (
          <ExitTestResults metrics={result.exit_metrics} />
        )}
        {result.test_mode === 'risk' && result.risk_metrics && (
          <RiskTestResults metrics={result.risk_metrics} />
        )}
        {result.test_mode === 'regime' && result.regime_metrics && (
          <RegimeTestResults metrics={result.regime_metrics} />
        )}

        {/* Insights and Recommendations */}
        <InsightsSection
          insights={result.insights || []}
          recommendations={result.recommendations || []}
        />
      </CardContent>
    </Card>
  )
}

import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { EntryEvaluation, ConditionEvaluation, RegimeType } from '@/types/strategy-evaluation'
import { AGGREGATION_MODE_LABELS } from '@/types/strategy-evaluation'
import { formatIndicatorValue } from '@/features/trading/utils/formatters'

interface EntryConditionsDisplayProps {
  entry: EntryEvaluation
  regime: RegimeType
  className?: string
}

/**
 * EntryConditionsDisplay Component
 *
 * Displays entry conditions for a single regime with visual indicators:
 * - Green checkmark for met conditions
 * - Red X for unmet conditions
 * - Yellow warning for errors
 * - Confidence badges
 * - Formatted indicator values
 */
export function EntryConditionsDisplay({
  entry,
  regime,
  className
}: EntryConditionsDisplayProps) {
  // Don't render if entry logic is disabled
  if (!entry.enabled) {
    return (
      <div className={cn('p-4 rounded-lg border border-border bg-muted/50', className)}>
        <p className="text-sm text-muted-foreground">Entry logic disabled for {regime} regime</p>
      </div>
    )
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Header with regime name and aggregation mode */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          Entry Conditions ({regime})
        </h3>
        <Badge variant="outline" className="text-xs">
          {AGGREGATION_MODE_LABELS[entry.aggregation]}
        </Badge>
      </div>

      {/* Score display for weighted_avg mode */}
      {entry.aggregation === 'weighted_avg' && (
        <div className="flex items-center justify-between p-2 rounded-lg bg-muted/50 text-xs">
          <span className="text-muted-foreground">Score:</span>
          <span className="font-mono font-semibold">
            {entry.score.toFixed(2)} / {entry.max_score.toFixed(2)}
            {' '}
            <span className={cn(
              'text-xs',
              entry.entry_possible ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            )}>
              ({entry.entry_possible ? '✓ Above' : '✗ Below'} threshold: {entry.threshold.toFixed(2)})
            </span>
          </span>
        </div>
      )}

      {/* Individual condition cards */}
      <div className="space-y-2">
        {entry.conditions.map((condition, index) => (
          <ConditionCard
            key={index}
            condition={condition}
            index={index}
          />
        ))}
      </div>

      {/* Summary indicator */}
      <div className={cn(
        'p-3 rounded-lg border text-sm font-medium',
        entry.entry_possible
          ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
          : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
      )}>
        {entry.entry_possible ? (
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>Entry conditions met - Entry possible</span>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4" />
            <span>Entry conditions not met - No entry signal</span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Individual condition card with status, description, and indicator values
 */
function ConditionCard({ condition, index }: { condition: ConditionEvaluation; index: number }) {
  const status = getConditionStatus(condition)
  const statusClass = getStatusClass(status)
  const StatusIcon = getStatusIcon(status)

  return (
    <div className={cn('p-3 rounded-lg text-xs border', statusClass)}>
      {/* Condition header with status icon and confidence */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <StatusIcon className={cn(
            'h-4 w-4 flex-shrink-0 mt-0.5',
            status === 'met' && 'text-green-500',
            status === 'unmet' && 'text-red-500',
            status === 'error' && 'text-yellow-500'
          )} />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-foreground break-words">
              {condition.description}
            </p>
          </div>
        </div>
        <Badge
          variant="outline"
          className="text-xs whitespace-nowrap flex-shrink-0"
        >
          conf: {condition.confidence.toFixed(1)}
        </Badge>
      </div>

      {/* Indicator values */}
      {Object.keys(condition.indicator_values).length > 0 && (
        <div className="mt-2 space-y-1">
          {Object.entries(condition.indicator_values).map(([name, value]) => (
            <div key={name} className="font-mono text-xs">
              <span className="text-muted-foreground">{formatIndicatorName(name)}:</span>
              {' '}
              <span className={cn(
                'font-medium',
                status === 'met' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              )}>
                {formatIndicatorValue(name, value)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Error message if present */}
      {condition.error && (
        <div className="mt-2 p-2 rounded bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
            <span className="text-xs">{condition.error}</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get condition status: met, unmet, or error
 */
function getConditionStatus(condition: ConditionEvaluation): 'met' | 'unmet' | 'error' {
  if (condition.error) return 'error'
  return condition.met ? 'met' : 'unmet'
}

/**
 * Get background and border classes based on status
 */
function getStatusClass(status: 'met' | 'unmet' | 'error'): string {
  switch (status) {
    case 'met':
      return 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
    case 'unmet':
      return 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
    case 'error':
      return 'bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800'
  }
}

/**
 * Get appropriate icon component for status
 */
function getStatusIcon(status: 'met' | 'unmet' | 'error') {
  switch (status) {
    case 'met':
      return CheckCircle2
    case 'unmet':
      return XCircle
    case 'error':
      return AlertTriangle
  }
}

/**
 * Format indicator name for display (convert snake_case to readable format)
 */
function formatIndicatorName(name: string): string {
  // Remove timeframe prefix (e.g., "1H_EMA_50" -> "EMA_50", "1h_EMA_50" -> "EMA_50")
  const withoutTimeframe = name.replace(/^\d+[hdwmHDWM]_/i, '')

  // Convert to readable format (e.g., "EMA_50" -> "EMA 50")
  return withoutTimeframe.replace(/_/g, ' ')
}

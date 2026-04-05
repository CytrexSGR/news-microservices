/**
 * MacroIndicatorCard Component
 *
 * Displays a single macroeconomic indicator with:
 * - Current value and trend
 * - Previous value comparison
 * - Visual trend indicator
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Minus, Calendar } from 'lucide-react'
import type { MacroIndicator } from '@/features/market/types/market.types'

export interface MacroIndicatorCardProps {
  indicator: MacroIndicator
  onClick?: (indicator: MacroIndicator) => void
  className?: string
}

/**
 * Macro indicator card with trend visualization
 *
 * @example
 * ```tsx
 * <MacroIndicatorCard
 *   indicator={gdpData}
 *   onClick={(indicator) => navigate(`/macro/${indicator.name}`)}
 * />
 * ```
 */
export function MacroIndicatorCard({
  indicator,
  onClick,
  className = '',
}: MacroIndicatorCardProps) {
  // Calculate change
  const change = indicator.value - (indicator.previous || indicator.value)
  const changePercent =
    indicator.previous && indicator.previous !== 0
      ? ((change / indicator.previous) * 100)
      : 0

  const isPositive = change > 0
  const isNegative = change < 0
  const isNeutral = change === 0

  // Determine if positive change is "good" based on indicator type
  // (e.g., rising unemployment is bad, rising GDP is good)
  const isGoodChange = determineGoodChange(indicator.name, isPositive)

  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-lg hover:border-primary/50 ${className}`}
      onClick={() => onClick?.(indicator)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base font-semibold">
              {formatIndicatorName(indicator.name)}
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              {indicator.unit || 'Index'}
            </CardDescription>
          </div>
          <Badge
            variant={
              isGoodChange ? 'default' : !isNeutral ? 'destructive' : 'secondary'
            }
            className="shrink-0"
          >
            {indicator.period || 'Latest'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Current Value */}
        <div className="space-y-3">
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-bold">
              {formatValue(indicator.value, indicator.name)}
            </div>
            {indicator.unit && (
              <div className="text-sm text-muted-foreground">{indicator.unit}</div>
            )}
          </div>

          {/* Change Indicator */}
          {indicator.previous !== undefined && !isNeutral && (
            <div
              className={`flex items-center gap-1 text-sm ${
                isGoodChange
                  ? 'text-green-600'
                  : isNegative
                  ? 'text-red-600'
                  : 'text-gray-600'
              }`}
            >
              {isPositive && <TrendingUp className="h-4 w-4" />}
              {isNegative && <TrendingDown className="h-4 w-4" />}
              {isNeutral && <Minus className="h-4 w-4" />}
              <span className="font-medium">
                {isPositive ? '+' : ''}
                {change.toFixed(2)} ({isPositive ? '+' : ''}
                {changePercent.toFixed(2)}%)
              </span>
            </div>
          )}

          {/* Previous Value */}
          {indicator.previous !== undefined && (
            <div className="text-xs text-muted-foreground">
              Previous: {formatValue(indicator.previous, indicator.name)}
              {indicator.unit && ` ${indicator.unit}`}
            </div>
          )}

          {/* Date */}
          {indicator.date && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground pt-2 border-t">
              <Calendar className="h-3 w-3" />
              {formatDate(indicator.date)}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Format indicator name for display
 */
function formatIndicatorName(name: string): string {
  // Convert snake_case or SCREAMING_SNAKE_CASE to Title Case
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Format indicator value based on type
 */
function formatValue(value: number, indicatorName: string): string {
  const name = indicatorName.toLowerCase()

  // Percentage indicators
  if (name.includes('rate') || name.includes('percent') || name.includes('inflation')) {
    return `${value.toFixed(2)}%`
  }

  // Large numbers (GDP, debt, etc.) - format with K, M, B, T
  if (name.includes('gdp') || name.includes('debt') || name.includes('spending')) {
    if (Math.abs(value) >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
    if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
    if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
    if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(2)}K`
    return `$${value.toFixed(2)}`
  }

  // Default: format with commas
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/**
 * Determine if a positive change is "good" for this indicator
 */
function determineGoodChange(indicatorName: string, isPositive: boolean): boolean {
  const name = indicatorName.toLowerCase()

  // Indicators where LOWER is better
  const lowerIsBetter = [
    'unemployment',
    'inflation',
    'debt',
    'deficit',
    'claims',
    'jobless',
  ]

  if (lowerIsBetter.some((term) => name.includes(term))) {
    return !isPositive // Lower is good, so negative change is good
  }

  // Default: higher is better (GDP, employment, production, etc.)
  return isPositive
}

/**
 * Format date for display
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

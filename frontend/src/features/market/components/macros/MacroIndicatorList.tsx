/**
 * MacroIndicatorList Component
 *
 * Grid list of macroeconomic indicators with:
 * - Responsive grid layout
 * - Loading and error states
 * - Click handling for detail navigation
 */

import { MacroIndicatorCard } from './MacroIndicatorCard'
import { Skeleton } from '@/components/ui/Skeleton'
import { Card } from '@/components/ui/Card'
import type { MacroIndicator } from '@/features/market/types/market.types'

export interface MacroIndicatorListProps {
  indicators: MacroIndicator[]
  isLoading?: boolean
  error?: Error | null
  onIndicatorClick?: (indicator: MacroIndicator) => void
  columns?: 1 | 2 | 3 | 4
  className?: string
}

/**
 * Grid list of macro indicator cards
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useLatestMacroIndicators()
 * <MacroIndicatorList
 *   indicators={data}
 *   isLoading={isLoading}
 *   error={error}
 *   onIndicatorClick={(indicator) => navigate(`/macro/${indicator.name}`)}
 *   columns={3}
 * />
 * ```
 */
export function MacroIndicatorList({
  indicators,
  isLoading = false,
  error = null,
  onIndicatorClick,
  columns = 3,
  className = '',
}: MacroIndicatorListProps) {
  // Column classes mapping
  const columnClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={`grid ${columnClasses[columns]} gap-4 ${className}`}>
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="p-6">
            <div className="space-y-3">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-40" />
              <Skeleton className="h-4 w-24" />
            </div>
          </Card>
        ))}
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className={className}>
        <Card className="p-6">
          <div className="text-center py-8">
            <div className="text-destructive font-semibold mb-2">
              Error loading macro indicators
            </div>
            <div className="text-sm text-muted-foreground">{error.message}</div>
          </div>
        </Card>
      </div>
    )
  }

  // Empty state
  if (!indicators || indicators.length === 0) {
    return (
      <div className={className}>
        <Card className="p-6">
          <div className="text-center py-8">
            <div className="text-muted-foreground">
              No macroeconomic indicators available
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className={`grid ${columnClasses[columns]} gap-4 ${className}`}>
      {indicators.map((indicator) => (
        <MacroIndicatorCard
          key={indicator.name}
          indicator={indicator}
          onClick={onIndicatorClick}
        />
      ))}
    </div>
  )
}

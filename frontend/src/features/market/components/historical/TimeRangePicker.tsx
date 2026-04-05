/**
 * TimeRangePicker Component
 *
 * Preset time range selector for historical data charts
 * Provides quick selection: 1W, 1M, 3M, 6M, 1Y, All
 */

import { Button } from '@/components/ui/Button'

export interface TimeRange {
  label: string
  value: string
  days: number | null // null = all time
}

export const TIME_RANGES: TimeRange[] = [
  { label: '1W', value: '1w', days: 7 },
  { label: '1M', value: '1m', days: 30 },
  { label: '3M', value: '3m', days: 90 },
  { label: '6M', value: '6m', days: 180 },
  { label: '1Y', value: '1y', days: 365 },
  { label: 'All', value: 'all', days: null },
]

export interface TimeRangePickerProps {
  selectedRange: string
  onRangeChange: (range: TimeRange) => void
  disabled?: boolean
  className?: string
}

/**
 * Time range picker with preset buttons
 *
 * @example
 * ```tsx
 * <TimeRangePicker
 *   selectedRange="1m"
 *   onRangeChange={(range) => setTimeRange(range)}
 * />
 * ```
 */
export function TimeRangePicker({
  selectedRange,
  onRangeChange,
  disabled = false,
  className = '',
}: TimeRangePickerProps) {
  return (
    <div className={`flex gap-2 ${className}`}>
      {TIME_RANGES.map((range) => (
        <Button
          key={range.value}
          variant={selectedRange === range.value ? 'default' : 'outline'}
          size="sm"
          onClick={() => onRangeChange(range)}
          disabled={disabled}
          className="min-w-[48px]"
        >
          {range.label}
        </Button>
      ))}
    </div>
  )
}

/**
 * Helper function to calculate date range from TimeRange
 */
export function calculateDateRange(range: TimeRange): {
  fromDate: string
  toDate: string
} {
  const today = new Date()
  const toDate = today.toISOString().split('T')[0] // YYYY-MM-DD

  if (range.days === null) {
    // All time: use a very old date
    return {
      fromDate: '2000-01-01',
      toDate,
    }
  }

  const fromDateObj = new Date(today)
  fromDateObj.setDate(fromDateObj.getDate() - range.days)
  const fromDate = fromDateObj.toISOString().split('T')[0]

  return {
    fromDate,
    toDate,
  }
}

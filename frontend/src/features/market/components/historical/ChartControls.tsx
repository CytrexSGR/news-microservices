/**
 * ChartControls Component
 *
 * Control panel for historical data charts
 * Combines time range picker, custom date range, and chart options
 */

import { useState } from 'react'
import { Calendar } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { TimeRangePicker, calculateDateRange, type TimeRange } from './TimeRangePicker'

export interface DateRange {
  fromDate: string // YYYY-MM-DD
  toDate: string   // YYYY-MM-DD
}

export interface ChartControlsProps {
  selectedRange: string
  onRangeChange: (range: TimeRange) => void
  onCustomDateRange?: (range: DateRange) => void
  showCustomDatePicker?: boolean
  disabled?: boolean
  className?: string
}

/**
 * Chart controls with time range picker and optional custom date range
 *
 * @example
 * ```tsx
 * <ChartControls
 *   selectedRange={timeRange}
 *   onRangeChange={setTimeRange}
 *   onCustomDateRange={handleCustomRange}
 *   showCustomDatePicker
 * />
 * ```
 */
export function ChartControls({
  selectedRange,
  onRangeChange,
  onCustomDateRange,
  showCustomDatePicker = false,
  disabled = false,
  className = '',
}: ChartControlsProps) {
  const [showCustomPicker, setShowCustomPicker] = useState(false)
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const handleCustomDateApply = () => {
    if (fromDate && toDate && onCustomDateRange) {
      onCustomDateRange({ fromDate, toDate })
      setShowCustomPicker(false)
    }
  }

  const handleRangeChange = (range: TimeRange) => {
    onRangeChange(range)
    setShowCustomPicker(false)
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Time Range Buttons */}
      <div className="flex flex-wrap items-center gap-2">
        <TimeRangePicker
          selectedRange={selectedRange}
          onRangeChange={handleRangeChange}
          disabled={disabled}
        />

        {/* Custom Date Range Toggle */}
        {showCustomDatePicker && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCustomPicker(!showCustomPicker)}
            disabled={disabled}
            className="gap-2"
          >
            <Calendar className="h-4 w-4" />
            Custom
          </Button>
        )}
      </div>

      {/* Custom Date Picker */}
      {showCustomPicker && showCustomDatePicker && (
        <Card className="p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-sm font-medium">From Date</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                max={toDate || undefined}
                className="w-full px-3 py-2 border rounded-md text-sm"
                disabled={disabled}
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">To Date</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                min={fromDate || undefined}
                max={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border rounded-md text-sm"
                disabled={disabled}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleCustomDateApply}
              disabled={!fromDate || !toDate || disabled}
            >
              Apply
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowCustomPicker(false)}
            >
              Cancel
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}

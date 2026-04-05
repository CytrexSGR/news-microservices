/**
 * Confidence Slider Component
 *
 * Range slider for filtering by minimum confidence level.
 * Features:
 * - Range slider (0.0 - 1.0)
 * - Live percentage display
 * - Color-coded indicator (High/Medium/Low)
 * - Preset buttons for quick selection
 * - Integration with Zustand store
 *
 * @module features/knowledge-graph/components/filters/ConfidenceSlider
 */

import { memo, useCallback } from 'react'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { getConfidenceColor, getConfidenceLabel } from '../../utils/colorScheme'
import { cn } from '@/lib/utils'

// ===========================
// Props Interface
// ===========================

export interface ConfidenceSliderProps {
  /** Confidence value (0.0 - 1.0) */
  value: number
  /** Callback when value changes */
  onChange: (confidence: number) => void
  /** Optional CSS class */
  className?: string
}

// ===========================
// Constants
// ===========================

/** Preset confidence values */
const PRESETS = {
  LOW: 0.3,
  MEDIUM: 0.5,
  HIGH: 0.7,
} as const

// ===========================
// Component
// ===========================

/**
 * Confidence threshold slider with presets.
 *
 * @example
 * ```tsx
 * const [confidence, setConfidence] = useState(0.5)
 *
 * <ConfidenceSlider
 *   value={confidence}
 *   onChange={setConfidence}
 * />
 * ```
 */
export const ConfidenceSlider = memo<ConfidenceSliderProps>(
  ({ value, onChange, className }) => {
    // Get color and label for current value
    const color = getConfidenceColor(value)
    const label = getConfidenceLabel(value)
    const percentage = Math.round(value * 100)

    // Handle slider change
    const handleSliderChange = useCallback(
      (values: number[]) => {
        onChange(values[0])
      },
      [onChange]
    )

    // Handle preset button click
    const handlePresetClick = useCallback(
      (preset: number) => {
        onChange(preset)
      },
      [onChange]
    )

    return (
      <div className={cn('space-y-4', className)}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Minimum Confidence
          </h3>

          <Badge
            variant="outline"
            className="font-mono font-semibold"
            style={{
              borderColor: color,
              color: color,
            }}
          >
            {percentage}%
          </Badge>
        </div>

        {/* Slider */}
        <div className="px-2">
          <Slider
            value={[value]}
            onValueChange={handleSliderChange}
            min={0}
            max={1}
            step={0.01}
            className="w-full"
            aria-label="Minimum confidence threshold"
          />

          {/* Range labels */}
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
            <span>0%</span>
            <span className="font-medium" style={{ color }}>
              {label} Confidence
            </span>
            <span>100%</span>
          </div>
        </div>

        {/* Preset buttons */}
        <div className="space-y-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">Quick presets:</p>
          <div className="flex items-center gap-2">
            <Button
              variant={value === PRESETS.LOW ? 'default' : 'outline'}
              size="sm"
              onClick={() => handlePresetClick(PRESETS.LOW)}
              className="flex-1"
            >
              Low {Math.round(PRESETS.LOW * 100)}%
            </Button>
            <Button
              variant={value === PRESETS.MEDIUM ? 'default' : 'outline'}
              size="sm"
              onClick={() => handlePresetClick(PRESETS.MEDIUM)}
              className="flex-1"
            >
              Medium {Math.round(PRESETS.MEDIUM * 100)}%
            </Button>
            <Button
              variant={value === PRESETS.HIGH ? 'default' : 'outline'}
              size="sm"
              onClick={() => handlePresetClick(PRESETS.HIGH)}
              className="flex-1"
            >
              High {Math.round(PRESETS.HIGH * 100)}%
            </Button>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Show only relationships with confidence above {percentage}%.
          {value >= 0.7 && ' High-quality connections only.'}
          {value >= 0.5 && value < 0.7 && ' Balanced quality and coverage.'}
          {value < 0.5 && ' Includes lower-confidence connections.'}
        </p>
      </div>
    )
  }
)

ConfidenceSlider.displayName = 'ConfidenceSlider'

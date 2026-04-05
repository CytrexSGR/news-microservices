/**
 * Entity Type Filter Component
 *
 * Multi-select checkboxes for filtering entities by type.
 * Features:
 * - Color-coded badges for each entity type
 * - Select All / Clear All buttons
 * - Count of selected types in header
 * - Integration with Zustand store
 *
 * @module features/knowledge-graph/components/filters/EntityTypeFilter
 */

import { memo, useCallback } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import {
  ENTITY_TYPE_COLORS,
  ENTITY_TYPE_ICONS,
  getEntityTypeDisplayName,
} from '../../utils/colorScheme'
import { cn } from '@/lib/utils'

// ===========================
// Props Interface
// ===========================

export interface EntityTypeFilterProps {
  /** Selected entity types */
  value: string[]
  /** Callback when selection changes */
  onChange: (types: string[]) => void
  /** Optional CSS class */
  className?: string
}

// ===========================
// Component
// ===========================

/**
 * Entity type multi-select filter.
 *
 * @example
 * ```tsx
 * const [selected, setSelected] = useState(['PERSON', 'ORGANIZATION'])
 *
 * <EntityTypeFilter
 *   value={selected}
 *   onChange={setSelected}
 * />
 * ```
 */
export const EntityTypeFilter = memo<EntityTypeFilterProps>(({ value, onChange, className }) => {
  // Get all entity types from color scheme
  const allEntityTypes = Object.keys(ENTITY_TYPE_COLORS).filter(
    (type) => type !== 'DEFAULT' && type !== 'MISC' && type !== 'OTHER'
  )

  // Toggle individual type
  const handleToggle = useCallback(
    (type: string) => {
      const newValue = value.includes(type)
        ? value.filter((t) => t !== type)
        : [...value, type]
      onChange(newValue)
    },
    [value, onChange]
  )

  // Select all types
  const handleSelectAll = useCallback(() => {
    onChange(allEntityTypes)
  }, [allEntityTypes, onChange])

  // Clear all types
  const handleClearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with count */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Entity Types
          {value.length > 0 && (
            <span className="ml-2 text-xs font-normal text-gray-500 dark:text-gray-400">
              ({value.length} selected)
            </span>
          )}
        </h3>
      </div>

      {/* Entity type checkboxes */}
      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
        {allEntityTypes.map((type) => {
          const isChecked = value.includes(type)
          const color = ENTITY_TYPE_COLORS[type]
          const icon = ENTITY_TYPE_ICONS[type]
          const displayName = getEntityTypeDisplayName(type)

          return (
            <label
              key={type}
              className={cn(
                'flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors',
                'hover:bg-gray-50 dark:hover:bg-gray-800',
                isChecked && 'bg-gray-50 dark:bg-gray-800'
              )}
            >
              <Checkbox
                checked={isChecked}
                onCheckedChange={() => handleToggle(type)}
                aria-label={`Filter by ${displayName}`}
              />

              <div className="flex items-center gap-2 flex-1">
                <Badge
                  variant="outline"
                  className="flex items-center gap-1 font-normal"
                  style={{
                    borderColor: color,
                    color: color,
                  }}
                >
                  <span>{icon}</span>
                  <span>{displayName}</span>
                </Badge>
              </div>
            </label>
          )
        })}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
        <Button
          variant="outline"
          size="sm"
          onClick={handleSelectAll}
          disabled={value.length === allEntityTypes.length}
          className="flex-1"
        >
          Select All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleClearAll}
          disabled={value.length === 0}
          className="flex-1"
        >
          Clear All
        </Button>
      </div>
    </div>
  )
})

EntityTypeFilter.displayName = 'EntityTypeFilter'

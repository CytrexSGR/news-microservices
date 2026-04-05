/**
 * Graph Filters Wrapper Component
 *
 * Container for all graph filters (entity types, relationships, confidence).
 * Features:
 * - Slide-in panel from right
 * - Integration with Zustand store
 * - Reset All / Apply Filters buttons
 * - Close button with keyboard support
 *
 * @module features/knowledge-graph/components/filters/GraphFilters
 */

import { memo, useCallback, useEffect } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useGraphStore } from '../../store/graphStore'
import { EntityTypeFilter } from './EntityTypeFilter'
import { RelationshipFilter } from './RelationshipFilter'
import { ConfidenceSlider } from './ConfidenceSlider'
import { cn } from '@/lib/utils'

// ===========================
// Props Interface
// ===========================

export interface GraphFiltersProps {
  /** Whether panel is open */
  isOpen: boolean
  /** Callback to close panel */
  onClose: () => void
  /** Optional CSS class */
  className?: string
}

// ===========================
// Component
// ===========================

/**
 * Graph filters panel with entity types, relationships, and confidence slider.
 *
 * @example
 * ```tsx
 * const [isOpen, setIsOpen] = useState(false)
 *
 * <GraphFilters
 *   isOpen={isOpen}
 *   onClose={() => setIsOpen(false)}
 * />
 * ```
 */
export const GraphFilters = memo<GraphFiltersProps>(({ isOpen, onClose, className }) => {
  // Get filters and actions from store
  const filters = useGraphStore((state) => state.filters)
  const setFilters = useGraphStore((state) => state.setFilters)
  const resetFilters = useGraphStore((state) => state.resetFilters)

  // Handle entity type change
  const handleEntityTypesChange = useCallback(
    (types: string[]) => {
      setFilters({ entityTypes: types })
    },
    [setFilters]
  )

  // Handle relationship type change
  const handleRelationshipTypesChange = useCallback(
    (types: string[]) => {
      setFilters({ relationshipTypes: types })
    },
    [setFilters]
  )

  // Handle confidence change
  const handleConfidenceChange = useCallback(
    (confidence: number) => {
      setFilters({ minConfidence: confidence })
    },
    [setFilters]
  )

  // Handle reset all
  const handleResetAll = useCallback(() => {
    resetFilters()
  }, [resetFilters])

  // Handle Escape key to close
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Don't render if not open
  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={cn(
          'fixed right-0 top-0 bottom-0 w-full sm:w-96 bg-white dark:bg-gray-900',
          'shadow-2xl z-50 overflow-y-auto',
          'animate-in slide-in-from-right duration-300',
          className
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="filters-title"
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <h2
              id="filters-title"
              className="text-lg font-semibold text-gray-900 dark:text-gray-100"
            >
              Graph Filters
            </h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              aria-label="Close filters"
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Filter sections */}
        <div className="p-4 space-y-6">
          {/* Entity Type Filter */}
          <EntityTypeFilter
            value={filters.entityTypes}
            onChange={handleEntityTypesChange}
          />

          {/* Divider */}
          <div className="border-t border-gray-200 dark:border-gray-700" />

          {/* Relationship Filter */}
          <RelationshipFilter
            value={filters.relationshipTypes}
            onChange={handleRelationshipTypesChange}
          />

          {/* Divider */}
          <div className="border-t border-gray-200 dark:border-gray-700" />

          {/* Confidence Slider */}
          <ConfidenceSlider
            value={filters.minConfidence}
            onChange={handleConfidenceChange}
          />
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleResetAll}
              className="flex-1"
            >
              Reset All
            </Button>
            <Button
              onClick={onClose}
              className="flex-1"
            >
              Apply Filters ✓
            </Button>
          </div>
        </div>
      </div>
    </>
  )
})

GraphFilters.displayName = 'GraphFilters'

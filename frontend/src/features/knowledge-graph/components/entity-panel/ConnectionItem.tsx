/**
 * ConnectionItem Component
 *
 * Displays a single relationship/connection in the EntityDetails panel.
 * Shows target entity name, relationship type badge, and confidence indicator.
 *
 * Features:
 * - Clickable to select target entity
 * - Color-coded confidence (green/yellow/red)
 * - Hover effect
 * - Accessible keyboard navigation
 *
 * @module features/knowledge-graph/components/entity-panel/ConnectionItem
 */

import { memo } from 'react'

import { getConfidenceColor, getConfidenceLabel } from '../../utils/colorScheme'
import { cn } from '@/lib/utils'

// ===========================
// Type Definitions
// ===========================

interface ConnectionData {
  relationshipType: string
  confidence: number
  evidence?: string
  targetEntity: string
  targetEntityType: string
}

interface ConnectionItemProps {
  connection: ConnectionData
  onClick: (targetEntity: string) => void
  className?: string
}

// ===========================
// Component
// ===========================

export const ConnectionItem = memo(function ConnectionItem({
  connection,
  onClick,
  className,
}: ConnectionItemProps) {
  const confidenceColor = getConfidenceColor(connection.confidence)
  const confidenceLabel = getConfidenceLabel(connection.confidence)
  const confidencePercentage = Math.round(connection.confidence * 100)

  return (
    <button
      onClick={() => onClick(connection.targetEntity)}
      className={cn(
        'w-full px-4 py-3 text-left hover:bg-muted/50 transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-inset',
        'group',
        className
      )}
      aria-label={`View details for ${connection.targetEntity}`}
    >
      <div className="flex items-center justify-between gap-3">
        {/* Left: Entity Name & Type */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate group-hover:text-primary transition-colors mb-1">
            {connection.targetEntity}
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{connection.targetEntityType}</span>
            {connection.evidence && (
              <>
                <span>•</span>
                <span className="truncate">{connection.evidence}</span>
              </>
            )}
          </div>
        </div>

        {/* Right: Confidence Indicator (subtle dot) */}
        <div
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: confidenceColor }}
          title={`${confidenceLabel} confidence (${confidencePercentage}%)`}
        />
      </div>
    </button>
  )
})

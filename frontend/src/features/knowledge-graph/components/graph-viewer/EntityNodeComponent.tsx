import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { Badge } from '@/components/ui/badge'
import { ENTITY_TYPE_ICONS } from '@/types/knowledgeGraphPublic'
import { cn } from '@/lib/utils'

interface EntityNodeData {
  label: string
  entityType: string
  connectionCount: number
  wikidataId?: string
  color: string
  isSelected?: boolean
  isHovered?: boolean
}

export const EntityNodeComponent = memo<NodeProps<EntityNodeData>>(({ data, selected }) => {
  const { label, entityType, connectionCount, wikidataId, color, isSelected } = data

  // Get icon for entity type
  const icon = ENTITY_TYPE_ICONS[entityType] || ENTITY_TYPE_ICONS.DEFAULT

  // Determine node styling
  const isHighlighted = selected || isSelected

  return (
    <div
      className={cn(
        'px-4 py-2 rounded-lg border-2 bg-white shadow-md transition-all duration-200',
        'hover:shadow-lg hover:scale-105',
        isHighlighted && 'ring-2 ring-blue-500 ring-offset-2 shadow-xl scale-110'
      )}
      style={{
        borderColor: color,
        minWidth: '120px',
        maxWidth: '200px',
      }}
    >
      {/* Handles for edges (invisible, but needed for connections) */}
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
      <Handle type="source" position={Position.Left} className="opacity-0" />
      <Handle type="source" position={Position.Right} className="opacity-0" />

      {/* Node content */}
      <div className="flex items-center gap-2">
        {/* Entity type icon */}
        <span className="text-xl" title={entityType}>
          {icon}
        </span>

        {/* Entity name */}
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm truncate text-gray-900" title={label}>
            {label}
          </div>

          {/* Connection count badge */}
          <div className="flex items-center gap-1 mt-1">
            <Badge
              variant="secondary"
              className="text-xs px-1.5 py-0 text-gray-900"
              style={{ backgroundColor: `${color}20` }}
            >
              {connectionCount} {connectionCount === 1 ? 'link' : 'links'}
            </Badge>

            {/* Wikidata indicator */}
            {wikidataId && (
              <Badge variant="outline" className="text-xs px-1.5 py-0">
                <svg
                  className="w-3 h-3"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h2v2h-2v-2zm0-8h2v6h-2V9z" />
                </svg>
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Entity type label */}
      <div className="text-xs text-gray-500 mt-1 capitalize">
        {entityType.toLowerCase().replace('_', ' ')}
      </div>
    </div>
  )
})

EntityNodeComponent.displayName = 'EntityNodeComponent'

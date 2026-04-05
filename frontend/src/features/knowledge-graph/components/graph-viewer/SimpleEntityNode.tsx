import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import { cn } from '@/lib/utils'

interface SimpleNodeData {
  label: string
  entityType: string
  color: string
  isSelected?: boolean
}

export const SimpleEntityNode = memo<NodeProps<SimpleNodeData>>(({ data, selected }) => {
  const { label, color, isSelected } = data
  const isHighlighted = selected || isSelected

  return (
    <div
      className={cn(
        'px-2 py-1 rounded-md border bg-white text-xs transition-all',
        'hover:shadow-md',
        isHighlighted && 'ring-1 ring-blue-500'
      )}
      style={{
        borderColor: color,
        minWidth: '60px',
        maxWidth: '100px',
      }}
    >
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <Handle type="source" position={Position.Bottom} className="opacity-0" />

      <div className="font-medium truncate text-gray-900" title={label}>
        {label}
      </div>
    </div>
  )
})

SimpleEntityNode.displayName = 'SimpleEntityNode'

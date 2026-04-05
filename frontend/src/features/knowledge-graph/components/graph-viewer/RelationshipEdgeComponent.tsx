/**
 * Relationship Edge Component
 *
 * Custom React Flow edge for visualizing entity relationships with:
 * - Confidence-based styling (color, width, opacity)
 * - Interactive labels (show on selection)
 * - Evidence tooltips
 * - Smooth step path animations
 *
 * @module features/knowledge-graph/components/graph-viewer
 */

import { memo } from 'react'
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from '@xyflow/react'
import type { RelationshipEdge } from '@/types/knowledgeGraphPublic'
import { Badge } from '@/components/ui/badge'
import { getConfidenceColor, getConfidenceLabel } from '@/features/knowledge-graph/utils'

/**
 * Custom edge component for relationship visualization
 *
 * Features:
 * - Smooth step path with configurable border radius
 * - Confidence-based color coding (high/medium/low)
 * - Dynamic stroke width based on confidence
 * - Interactive labels (visible on selection)
 * - Evidence tooltips
 * - Smooth transitions on hover/selection
 *
 * @example
 * ```tsx
 * <ReactFlow
 *   edgeTypes={{
 *     relationship: RelationshipEdgeComponent,
 *   }}
 * />
 * ```
 */
export const RelationshipEdgeComponent = memo(
  ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    markerEnd,
    selected,
  }: EdgeProps<RelationshipEdge['data']>) => {
    const {
      relationshipType = 'RELATED_TO',
      confidence = 0.5,
      evidence,
    } = data ?? {}

    // Calculate smooth step path for better visual flow
    const [edgePath, labelX, labelY] = getSmoothStepPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
      borderRadius: 10,
    })

    // Determine stroke color based on confidence level
    const strokeColor = getConfidenceColor(confidence)
    const confidenceLabel = getConfidenceLabel(confidence)

    // Calculate stroke width based on confidence
    const strokeWidth = 1.5 + confidence * 2

    // Adjust visual properties based on selection state
    const finalOpacity = selected ? 1 : 0.4 + confidence * 0.6
    const finalStrokeWidth = selected ? strokeWidth + 1 : strokeWidth

    return (
      <>
        {/* The edge path with confidence-based styling */}
        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={markerEnd}
          style={{
            stroke: strokeColor,
            strokeWidth: finalStrokeWidth,
            opacity: finalOpacity,
            transition: 'all 0.2s ease',
          }}
        />

        {/* Edge label (relationship type + confidence) */}
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
          >
            {/* Only show label on selection for cleaner visualization */}
            {selected && (
              <div className="flex flex-col gap-1 items-center">
                {/* Relationship type badge */}
                <Badge
                  variant="secondary"
                  className="text-xs px-2 py-0.5 bg-white shadow-md border"
                  style={{
                    borderColor: strokeColor,
                    color: strokeColor,
                  }}
                >
                  {relationshipType.replace(/_/g, ' ')}
                </Badge>

                {/* Confidence badge */}
                <Badge
                  variant="outline"
                  className="text-xs px-1.5 py-0 bg-white"
                  style={{
                    borderColor: strokeColor,
                    color: strokeColor,
                  }}
                >
                  {confidenceLabel} ({(confidence * 100).toFixed(0)}%)
                </Badge>

                {/* Evidence tooltip (if available) */}
                {evidence && (
                  <div className="text-xs text-gray-600 bg-white px-2 py-1 rounded shadow-sm max-w-xs truncate">
                    {evidence}
                  </div>
                )}
              </div>
            )}
          </div>
        </EdgeLabelRenderer>
      </>
    )
  }
)

RelationshipEdgeComponent.displayName = 'RelationshipEdgeComponent'

export default RelationshipEdgeComponent

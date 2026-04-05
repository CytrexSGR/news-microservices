/**
 * Animated Relationship Edge Component
 *
 * Animated variant of relationship edge for high-confidence connections.
 * Features gradient animations with pulse effect to highlight important
 * relationships in the knowledge graph.
 *
 * Recommended usage: confidence > 0.8
 *
 * @module features/knowledge-graph/components/graph-viewer
 */

import { memo } from 'react'
import {
  BaseEdge,
  getSmoothStepPath,
  type EdgeProps,
} from '@xyflow/react'
import type { RelationshipEdge } from '@/types/knowledgeGraphPublic'
import { getConfidenceColor } from '@/features/knowledge-graph/utils'

/**
 * Animated edge component for high-confidence relationships
 *
 * Features:
 * - Gradient animation with pulse effect
 * - Confidence-based animation intensity
 * - Smooth step path with custom border radius
 * - Dynamic stroke width scaling with confidence
 * - SVG gradient definitions with unique IDs
 *
 * Animation Details:
 * - Duration: 2 seconds per cycle
 * - Pattern: Fade in/out (0.2 → 0.8 → 0.2 opacity)
 * - Infinite loop
 * - Three-stop gradient for smooth transitions
 *
 * Performance Notes:
 * - Uses CSS animations (GPU-accelerated)
 * - Memoized to prevent unnecessary re-renders
 * - Unique gradient ID per edge to avoid conflicts
 *
 * @example
 * ```tsx
 * <ReactFlow
 *   edgeTypes={{
 *     animated: AnimatedRelationshipEdge,
 *   }}
 * />
 *
 * // Use for high-confidence edges
 * const edge = {
 *   type: confidence > 0.8 ? 'animated' : 'smoothstep',
 *   data: { relationshipType, confidence }
 * }
 * ```
 */
export const AnimatedRelationshipEdge = memo(
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
  }: EdgeProps<RelationshipEdge['data']>) => {
    const { confidence = 0.9 } = data ?? {}

    // Calculate smooth step path
    const [edgePath] = getSmoothStepPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
      borderRadius: 10,
    })

    // Get base color from confidence level
    const baseColor = getConfidenceColor(confidence)

    // Generate unique gradient ID to avoid conflicts in multi-edge graphs
    const gradientId = `gradient-${id}`

    // Scale stroke width with confidence for visual hierarchy
    const strokeWidth = 2 + confidence * 2

    // Scale opacity with confidence
    const baseOpacity = 0.7 + confidence * 0.3

    return (
      <>
        {/* SVG gradient definition with animation */}
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            {/* Start stop - fades in/out */}
            <stop offset="0%" stopColor={baseColor} stopOpacity="0.2">
              <animate
                attributeName="stop-opacity"
                values="0.2;0.8;0.2"
                dur="2s"
                repeatCount="indefinite"
              />
            </stop>

            {/* Middle stop - pulses opposite to ends */}
            <stop offset="50%" stopColor={baseColor} stopOpacity="0.8">
              <animate
                attributeName="stop-opacity"
                values="0.8;0.2;0.8"
                dur="2s"
                repeatCount="indefinite"
              />
            </stop>

            {/* End stop - fades in/out (synced with start) */}
            <stop offset="100%" stopColor={baseColor} stopOpacity="0.2">
              <animate
                attributeName="stop-opacity"
                values="0.2;0.8;0.2"
                dur="2s"
                repeatCount="indefinite"
              />
            </stop>
          </linearGradient>
        </defs>

        {/* Edge path with animated gradient */}
        <BaseEdge
          id={id}
          path={edgePath}
          markerEnd={markerEnd}
          style={{
            stroke: `url(#${gradientId})`,
            strokeWidth,
            opacity: baseOpacity,
          }}
        />
      </>
    )
  }
)

AnimatedRelationshipEdge.displayName = 'AnimatedRelationshipEdge'

export default AnimatedRelationshipEdge

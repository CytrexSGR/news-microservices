/**
 * Graph Transformer Utility
 *
 * Transforms backend GraphResponse into React Flow format with layout algorithms.
 * Implements three layout strategies: force-directed, hierarchical, and radial.
 *
 * @module features/knowledge-graph/utils/graphTransformer
 */

import type { GraphResponse, GraphNode, GraphEdge } from '../../../types/knowledgeGraph'
import type { EntityNode, RelationshipEdge, FilterState } from '../../../types/knowledgeGraphPublic'
import { ENTITY_TYPE_COLORS } from './colorScheme'
import { RELATIONSHIP_COLORS } from './colorScheme'

// ===========================
// Core Transformation
// ===========================

/**
 * Transform backend GraphResponse to React Flow format with layout applied.
 *
 * @param apiData - Backend graph response
 * @param layoutType - Layout algorithm to use
 * @returns Positioned nodes and edges ready for React Flow
 *
 * @example
 * const { nodes, edges } = transformToReactFlow(apiData, 'force')
 * <ReactFlow nodes={nodes} edges={edges} />
 */
export function transformToReactFlow(
  apiData: GraphResponse,
  layoutType: 'force' | 'hierarchical' | 'radial' = 'force'
): {
  nodes: EntityNode[]
  edges: RelationshipEdge[]
} {
  // Filter out ARTICLE nodes - they're just references, not interesting entities
  const filteredNodes = apiData.nodes.filter((node) => node.type !== 'ARTICLE')

  // Also filter edges that connect to articles
  const articleNames = new Set(
    apiData.nodes.filter((n) => n.type === 'ARTICLE').map((n) => n.name)
  )
  const filteredEdges = apiData.edges.filter(
    (edge) => !articleNames.has(edge.source) && !articleNames.has(edge.target)
  )

  const nodes = transformNodes(filteredNodes)
  const edges = transformEdges(filteredEdges)

  // Apply layout algorithm to position nodes
  const positionedNodes = applyLayout(nodes, edges, layoutType)

  return {
    nodes: positionedNodes,
    edges,
  }
}

// ===========================
// Node Transformation
// ===========================

/**
 * Transform backend nodes to React Flow EntityNode format.
 *
 * Maps GraphNode[] to EntityNode[] with:
 * - Unique IDs (using entity name)
 * - Custom node type for rendering
 * - Initial position (0,0) - layout algorithm positions later
 * - Color coding by entity type
 *
 * @param apiNodes - Backend graph nodes
 * @returns React Flow entity nodes
 */
function transformNodes(apiNodes: GraphNode[]): EntityNode[] {
  return apiNodes.map((node) => ({
    id: node.name, // Use name as ID (should be unique)
    type: 'entity', // Custom node renderer component
    position: { x: 0, y: 0 }, // Will be set by layout algorithm
    data: {
      label: node.name,
      entityType: node.type,
      connectionCount: node.connection_count ?? 0,
      wikidataId: undefined, // Not in GraphNode, would need separate query
      lastSeen: undefined, // Not in GraphNode, would need separate query
      // Visual styling
      color: ENTITY_TYPE_COLORS[node.type] ?? ENTITY_TYPE_COLORS.DEFAULT,
    },
    // React Flow node properties
    draggable: true,
    selectable: true,
    connectable: false, // Don't allow manual edge creation
  }))
}

// ===========================
// Edge Transformation
// ===========================

/**
 * Transform backend edges to React Flow RelationshipEdge format.
 *
 * Maps GraphEdge[] to RelationshipEdge[] with:
 * - Unique IDs (source-target-index to handle multiple relationships)
 * - Smooth curved edges
 * - Animation for high-confidence relationships (>0.8)
 * - Stroke width/opacity based on confidence
 * - Color coding by relationship type
 *
 * @param apiEdges - Backend graph edges
 * @returns React Flow relationship edges
 */
function transformEdges(apiEdges: GraphEdge[]): RelationshipEdge[] {
  return apiEdges.map((edge, index) => ({
    id: `edge-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'smoothstep', // Smooth curved edges
    animated: edge.confidence > 0.8, // Animate high-confidence edges
    data: {
      relationshipType: edge.relationship_type,
      confidence: edge.confidence,
      evidence: edge.evidence,
      mentionCount: edge.mention_count,
      // Visual styling calculations
      strokeWidth: 1 + edge.confidence * 2, // 1-3px based on confidence
      opacity: 0.4 + edge.confidence * 0.6, // 0.4-1.0 based on confidence
    },
    style: {
      stroke: getEdgeColor(edge.relationship_type),
      strokeWidth: 1 + edge.confidence * 2,
      opacity: 0.4 + edge.confidence * 0.6,
    },
    markerEnd: {
      type: 'arrowclosed',
      width: 20,
      height: 20,
    },
  }))
}

// ===========================
// Layout Algorithms
// ===========================

/**
 * Apply layout algorithm to position nodes spatially.
 *
 * Delegates to specific layout implementation based on type.
 * All layouts return nodes with updated position property.
 *
 * @param nodes - Entity nodes to position
 * @param edges - Relationship edges (used for connectivity)
 * @param layoutType - Layout algorithm to use
 * @returns Positioned entity nodes
 */
function applyLayout(
  nodes: EntityNode[],
  edges: RelationshipEdge[],
  layoutType: 'force' | 'hierarchical' | 'radial'
): EntityNode[] {
  switch (layoutType) {
    case 'force':
      return applyForceDirectedLayout(nodes, edges)
    case 'hierarchical':
      return applyHierarchicalLayout(nodes, edges)
    case 'radial':
      return applyRadialLayout(nodes, edges)
    default:
      return applyForceDirectedLayout(nodes, edges)
  }
}

/**
 * Force-Directed Layout (Circular Initial Placement)
 *
 * Simple circular layout as starting point for force simulation.
 * For production: Use d3-force or elkjs for true physics-based layout.
 *
 * Algorithm:
 * 1. Place nodes in a circle around center point
 * 2. Radius scales with node count (more nodes = larger circle)
 * 3. Evenly distribute nodes around circle using angle steps
 *
 * @param nodes - Entity nodes to position
 * @param edges - Relationship edges (unused in simple version)
 * @returns Nodes positioned in circular pattern
 */
function applyForceDirectedLayout(
  nodes: EntityNode[],
  edges: RelationshipEdge[]
): EntityNode[] {
  const centerX = 400
  const centerY = 300

  // Simple circular layout as starting point for force simulation
  const angleStep = (2 * Math.PI) / nodes.length
  const radius = Math.min(200 + nodes.length * 10, 400) // Scale with node count, cap at 400px

  return nodes.map((node, index) => {
    const angle = index * angleStep

    return {
      ...node,
      position: {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      },
    }
  })
}

/**
 * Hierarchical Layout (Tree-Based)
 *
 * Creates a top-down tree structure:
 * 1. Find root nodes (no incoming edges or most connected)
 * 2. Use BFS to assign levels to nodes
 * 3. Position nodes in horizontal layers by level
 * 4. Orphaned nodes (not in tree) placed at bottom
 *
 * Good for: Organization hierarchies, dependency graphs
 *
 * @param nodes - Entity nodes to position
 * @param edges - Relationship edges (defines tree structure)
 * @returns Nodes positioned in hierarchical tree
 */
function applyHierarchicalLayout(
  nodes: EntityNode[],
  edges: RelationshipEdge[]
): EntityNode[] {
  // Find root nodes (nodes with no incoming edges)
  const incomingEdges = new Set(edges.map((e) => e.target))
  const rootNodes = nodes.filter((n) => !incomingEdges.has(n.id))

  if (rootNodes.length === 0) {
    // Fallback: Use node with most connections as root
    const sorted = [...nodes].sort(
      (a, b) => (b.data.connectionCount ?? 0) - (a.data.connectionCount ?? 0)
    )
    if (sorted.length > 0) {
      rootNodes.push(sorted[0])
    }
  }

  // Layout parameters
  const levelSpacing = 150 // Vertical distance between levels
  const nodeSpacing = 120 // Horizontal distance between nodes

  const positioned = new Map<string, EntityNode>()
  const levels: EntityNode[][] = []

  // BFS to assign levels
  const queue = rootNodes.map((n) => ({ node: n, level: 0 }))
  const visited = new Set<string>()

  while (queue.length > 0) {
    const item = queue.shift()
    if (!item) break

    const { node, level } = item

    if (visited.has(node.id)) continue
    visited.add(node.id)

    if (!levels[level]) levels[level] = []
    levels[level].push(node)

    // Add children (nodes this node points to)
    const children = edges
      .filter((e) => e.source === node.id)
      .map((e) => nodes.find((n) => n.id === e.target))
      .filter((n): n is EntityNode => n !== undefined)

    children.forEach((child) => {
      queue.push({ node: child, level: level + 1 })
    })
  }

  // Position nodes based on levels
  levels.forEach((levelNodes, level) => {
    const levelWidth = levelNodes.length * nodeSpacing
    const startX = (800 - levelWidth) / 2 // Center horizontally

    levelNodes.forEach((node, index) => {
      positioned.set(node.id, {
        ...node,
        position: {
          x: startX + index * nodeSpacing,
          y: 100 + level * levelSpacing,
        },
      })
    })
  })

  // Add remaining nodes (not in tree) at bottom
  nodes.forEach((node) => {
    if (!positioned.has(node.id)) {
      const bottomLevel = levels.length
      const index = positioned.size
      positioned.set(node.id, {
        ...node,
        position: {
          x: 100 + (index % 5) * nodeSpacing,
          y: 100 + bottomLevel * levelSpacing,
        },
      })
    }
  })

  return Array.from(positioned.values())
}

/**
 * Radial Layout (Star Pattern)
 *
 * Creates a center-and-spokes pattern:
 * 1. Find center node (most connected entity)
 * 2. Place center at (400, 300)
 * 3. Arrange remaining nodes in circle around center
 *
 * Good for: Network analysis, influence diagrams, hub-and-spoke
 *
 * @param nodes - Entity nodes to position
 * @param edges - Relationship edges (used to find center)
 * @returns Nodes positioned in radial pattern
 */
function applyRadialLayout(
  nodes: EntityNode[],
  edges: RelationshipEdge[]
): EntityNode[] {
  if (nodes.length === 0) return []

  // Center node: Most connected entity
  const centerNode = [...nodes].sort(
    (a, b) => (b.data.connectionCount ?? 0) - (a.data.connectionCount ?? 0)
  )[0]

  const centerX = 400
  const centerY = 300
  const radius = 250

  return nodes.map((node, index) => {
    // Place center node at center
    if (node.id === centerNode.id) {
      return { ...node, position: { x: centerX, y: centerY } }
    }

    // Arrange remaining nodes in circle
    const angleStep = (2 * Math.PI) / (nodes.length - 1)
    const angle = index * angleStep

    return {
      ...node,
      position: {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      },
    }
  })
}

// ===========================
// Filtering
// ===========================

/**
 * Filter nodes and edges based on filter criteria.
 *
 * Applies filters sequentially:
 * 1. Entity type filter (if specified)
 * 2. Relationship type filter (if specified)
 * 3. Confidence threshold filter (if specified)
 * 4. Remove orphaned nodes (nodes with no edges after filtering)
 *
 * @param nodes - Entity nodes to filter
 * @param edges - Relationship edges to filter
 * @param filters - Filter criteria to apply
 * @returns Filtered nodes and edges
 *
 * @example
 * const { nodes, edges } = filterGraph(
 *   allNodes,
 *   allEdges,
 *   {
 *     entityTypes: ['PERSON', 'ORGANIZATION'],
 *     minConfidence: 0.7
 *   }
 * )
 */
export function filterGraph(
  nodes: EntityNode[],
  edges: RelationshipEdge[],
  filters: FilterState
): {
  nodes: EntityNode[]
  edges: RelationshipEdge[]
} {
  let filteredNodes = nodes
  let filteredEdges = edges

  // Filter by entity type
  if (filters.entityTypes && filters.entityTypes.length > 0) {
    filteredNodes = filteredNodes.filter((node) =>
      filters.entityTypes.includes(node.data.entityType)
    )
  }

  // Filter by relationship type
  if (filters.relationshipTypes && filters.relationshipTypes.length > 0) {
    filteredEdges = filteredEdges.filter((edge) =>
      filters.relationshipTypes!.includes(edge.data.relationshipType)
    )
  }

  // Filter by confidence threshold
  if (filters.minConfidence !== undefined) {
    filteredEdges = filteredEdges.filter(
      (edge) => edge.data.confidence >= filters.minConfidence!
    )
  }

  // Remove orphaned nodes (nodes with no edges after filtering)
  const connectedNodeIds = new Set([
    ...filteredEdges.map((e) => e.source),
    ...filteredEdges.map((e) => e.target),
  ])

  filteredNodes = filteredNodes.filter((node) => connectedNodeIds.has(node.id))

  return {
    nodes: filteredNodes,
    edges: filteredEdges,
  }
}

// ===========================
// Utility Functions
// ===========================

/**
 * Get edge color based on relationship type.
 *
 * Uses predefined color scheme from colorScheme.ts.
 * Falls back to default gray for unknown types.
 *
 * @param relationshipType - Relationship type (WORKS_FOR, LOCATED_IN, etc.)
 * @returns Hex color code
 */
function getEdgeColor(relationshipType: string): string {
  return RELATIONSHIP_COLORS[relationshipType] ?? RELATIONSHIP_COLORS.DEFAULT
}

/**
 * Calculate graph statistics after transformation.
 *
 * Useful for debugging and analytics.
 *
 * @param nodes - Entity nodes
 * @param edges - Relationship edges
 * @returns Graph statistics
 */
export function calculateGraphStats(
  nodes: EntityNode[],
  edges: RelationshipEdge[]
): {
  totalNodes: number
  totalEdges: number
  entityTypeCounts: Record<string, number>
  relationshipTypeCounts: Record<string, number>
  avgConfidence: number
  connectedComponents: number
} {
  const entityTypeCounts: Record<string, number> = {}
  const relationshipTypeCounts: Record<string, number> = {}

  // Count entity types
  nodes.forEach((node) => {
    const type = node.data.entityType
    entityTypeCounts[type] = (entityTypeCounts[type] ?? 0) + 1
  })

  // Count relationship types and average confidence
  let totalConfidence = 0
  edges.forEach((edge) => {
    const type = edge.data.relationshipType
    relationshipTypeCounts[type] = (relationshipTypeCounts[type] ?? 0) + 1
    totalConfidence += edge.data.confidence
  })

  const avgConfidence = edges.length > 0 ? totalConfidence / edges.length : 0

  // Simple connected components calculation (BFS)
  const visited = new Set<string>()
  let connectedComponents = 0

  const bfs = (startId: string) => {
    const queue = [startId]
    while (queue.length > 0) {
      const nodeId = queue.shift()!
      if (visited.has(nodeId)) continue
      visited.add(nodeId)

      // Add neighbors
      edges.forEach((edge) => {
        if (edge.source === nodeId && !visited.has(edge.target)) {
          queue.push(edge.target)
        }
        if (edge.target === nodeId && !visited.has(edge.source)) {
          queue.push(edge.source)
        }
      })
    }
  }

  nodes.forEach((node) => {
    if (!visited.has(node.id)) {
      connectedComponents++
      bfs(node.id)
    }
  })

  return {
    totalNodes: nodes.length,
    totalEdges: edges.length,
    entityTypeCounts,
    relationshipTypeCounts,
    avgConfidence,
    connectedComponents,
  }
}

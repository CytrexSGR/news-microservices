/**
 * GraphVisualization Component
 *
 * Main React Flow canvas component for Knowledge Graph visualization.
 * Implements interactive graph rendering with:
 * - Custom node/edge components
 * - Layout algorithms (force, hierarchical, radial)
 * - Filtering (entity types, relationships, confidence)
 * - Selection and hover states
 * - Statistics panel and legend
 * - Read-only mode (no manual connections)
 *
 * @module features/knowledge-graph/components/graph-viewer
 */

import React, { useCallback, useEffect, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
  type Connection,
  type Edge,
  type Node,
  type NodeTypes,
  type EdgeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { useGraphStore } from '@/features/knowledge-graph/store'
import { transformToReactFlow, filterGraph } from '@/features/knowledge-graph/utils'
import type { GraphResponse } from '@/types/knowledgeGraph'
import type { EntityNode } from '@/types/knowledgeGraphPublic'
import { ENTITY_TYPE_COLORS } from '@/features/knowledge-graph/utils/colorScheme'

// Import custom node/edge components
import { EntityNodeComponent } from './EntityNodeComponent'
import { RelationshipEdgeComponent } from './RelationshipEdgeComponent'

// ===========================
// Component Props
// ===========================

export interface GraphVisualizationProps {
  /** Graph data from backend API */
  graphData: GraphResponse
  /** Callback when a node is clicked */
  onNodeClick?: (nodeId: string) => void
  /** Callback when an edge is clicked */
  onEdgeClick?: (edgeId: string) => void
  /** Additional CSS classes */
  className?: string
}

// ===========================
// Custom Node/Edge Types
// ===========================

/**
 * Register custom node and edge types for React Flow.
 * These map to custom component implementations.
 */
const nodeTypes: NodeTypes = {
  entity: EntityNodeComponent, // Custom entity node renderer
}

const edgeTypes: EdgeTypes = {
  custom: RelationshipEdgeComponent, // Custom relationship edge renderer
}

// ===========================
// Main Component
// ===========================

export function GraphVisualization({
  graphData,
  onNodeClick,
  onEdgeClick,
  className = '',
}: GraphVisualizationProps) {
  // ===== Zustand Store State =====
  const layoutType = useGraphStore((state) => state.layoutType)
  const filters = useGraphStore((state) => state.filters)
  const selectedEntity = useGraphStore((state) => state.selectedEntity)
  const setSelectedEntity = useGraphStore((state) => state.setSelectedEntity)
  const setHoveredEntity = useGraphStore((state) => state.setHoveredEntity)
  const showLegend = useGraphStore((state) => state.showLegend)

  // ===== Graph Transformation Pipeline =====

  // Step 1: Transform API data to React Flow format with layout
  const { nodes: transformedNodes, edges: transformedEdges } = useMemo(() => {
    return transformToReactFlow(graphData, layoutType)
  }, [graphData, layoutType])

  // Step 2: Apply filters to transformed graph
  const { nodes: filteredNodes, edges: filteredEdges } = useMemo(() => {
    return filterGraph(transformedNodes, transformedEdges, {
      entityTypes: filters.entityTypes,
      relationshipTypes: filters.relationshipTypes,
      minConfidence: filters.minConfidence,
      minConnectionCount: filters.minConnectionCount,
      dateRange: filters.dateRange,
      searchQuery: filters.searchQuery,
    })
  }, [transformedNodes, transformedEdges, filters])

  // ===== React Flow State =====

  const [nodes, setNodes, onNodesChange] = useNodesState(filteredNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(filteredEdges)

  // Update nodes/edges when filtered data changes
  useEffect(() => {
    setNodes(filteredNodes)
    setEdges(filteredEdges)
  }, [filteredNodes, filteredEdges, setNodes, setEdges])

  // Update selected state on nodes
  useEffect(() => {
    setNodes((prevNodes) =>
      prevNodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          isSelected: node.id === selectedEntity,
        },
      }))
    )
  }, [selectedEntity, setNodes])

  // ===== Event Handlers =====

  /**
   * Handle node click event.
   * Updates store and triggers callback.
   */
  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedEntity(node.id)
      onNodeClick?.(node.id)
    },
    [setSelectedEntity, onNodeClick]
  )

  /**
   * Handle edge click event.
   * Triggers callback (no store update for edges).
   */
  const handleEdgeClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      onEdgeClick?.(edge.id)
    },
    [onEdgeClick]
  )

  /**
   * Handle node hover enter event.
   * Updates store for hover highlighting.
   */
  const handleNodeMouseEnter = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setHoveredEntity(node.id)
    },
    [setHoveredEntity]
  )

  /**
   * Handle node hover leave event.
   * Clears hover state.
   */
  const handleNodeMouseLeave = useCallback(() => {
    setHoveredEntity(null)
  }, [setHoveredEntity])

  /**
   * Block edge connections (read-only graph).
   * Users cannot manually create edges.
   */
  const onConnect = useCallback((params: Connection) => {
    // Do nothing - read-only graph
    console.log('Connection attempt blocked (read-only graph)', params)
  }, [])

  // ===== Empty State =====

  if (nodes.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center">
          <p className="text-lg text-gray-500">No entities to display</p>
          <p className="text-sm text-gray-400 mt-2">
            Try adjusting your filters or searching for an entity
          </p>
        </div>
      </div>
    )
  }

  // ===== Render =====

  return (
    <div className={`w-full h-full ${className}`}>
      <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          onNodeMouseEnter={handleNodeMouseEnter}
          onNodeMouseLeave={handleNodeMouseLeave}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{
            padding: 0.2,
            minZoom: 0.5,
            maxZoom: 1.5,
          }}
          minZoom={0.1}
          maxZoom={2}
          defaultEdgeOptions={{
            animated: false,
            type: 'custom',
          }}
          deleteKeyCode={null} // Disable delete key
          selectionKeyCode={null} // Disable multi-selection
          multiSelectionKeyCode={null}
          nodesDraggable={true}
          nodesConnectable={false} // Read-only: no manual connections
          elementsSelectable={true}
        >
          {/* Background pattern */}
          <Background color="#aaa" gap={16} />

          {/* Built-in controls (zoom, fit view) */}
          <Controls showInteractive={false} />

          {/* Mini map overview */}
          <MiniMap
            nodeColor={(node) => {
              const entityNode = node as unknown as EntityNode
              return (entityNode.data as any)?.color || '#6b7280'
            }}
            nodeStrokeWidth={3}
            zoomable
            pannable
          />

          {/* Graph statistics panel */}
          <Panel position="top-right" className="bg-white p-3 rounded-lg shadow-md">
            <div className="text-xs text-gray-900 space-y-1">
              <div>
                <span className="font-semibold">Nodes:</span> {nodes.length}
              </div>
              <div>
                <span className="font-semibold">Edges:</span> {edges.length}
              </div>
              <div>
                <span className="font-semibold">Layout:</span>{' '}
                <span className="capitalize">{layoutType}</span>
              </div>
            </div>
          </Panel>

          {/* Legend (if enabled) */}
          {showLegend && (
            <Panel position="bottom-left" className="bg-white p-3 rounded-lg shadow-md">
              <GraphLegend />
            </Panel>
          )}
        </ReactFlow>
    </div>
  )
}

// ===========================
// Legend Component
// ===========================

/**
 * Graph Legend Component
 *
 * Displays entity type color coding for reference.
 * Inline component (no separate file needed).
 */
function GraphLegend() {
  return (
    <div className="text-xs text-gray-900">
      <div className="font-semibold mb-2">Entity Types</div>
      <div className="space-y-1">
        {Object.entries(ENTITY_TYPE_COLORS).map(([type, color]) => {
          // Skip internal keys (DEFAULT, etc.)
          if (type === 'DEFAULT') return null

          return (
            <div key={type} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="capitalize">{type.toLowerCase()}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ===========================
// Export
// ===========================

export default GraphVisualization

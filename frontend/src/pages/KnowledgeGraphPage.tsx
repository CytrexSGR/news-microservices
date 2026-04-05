/**
 * Knowledge Graph Page
 *
 * User-facing page for exploring the knowledge graph.
 * Provides entity search, graph visualization, and entity detail panels.
 *
 * Features:
 * - Entity search with autocomplete
 * - Interactive graph visualization
 * - Entity detail panel with connections
 * - Pathfinding between entities
 * - Graph filtering and layout controls
 *
 * @module pages/KnowledgeGraphPage
 */

import React, { useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { Network, AlertCircle, Loader2 } from 'lucide-react'
import { ReactFlowProvider } from '@xyflow/react'

import { EntitySearch } from '@/features/knowledge-graph/components/search'
import { GraphVisualization, GraphControls } from '@/features/knowledge-graph/components/graph-viewer'
import { EntityDetails } from '@/features/knowledge-graph/components/entity-panel'
import { GraphFilters } from '@/features/knowledge-graph/components/filters'

import { getEntityConnections } from '@/lib/api/knowledgeGraphPublic'
import type { GraphResponse } from '@/types/knowledgeGraphPublic'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

/**
 * Main Knowledge Graph Page Component
 */
export function KnowledgeGraphPage() {
  // ===== URL State Management =====
  const [searchParams, setSearchParams] = useSearchParams()
  const entityFromUrl = searchParams.get('entity')

  // ===== Local State =====
  const [graphData, setGraphData] = useState<GraphResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedEntity, setSelectedEntity] = useState<string | null>(entityFromUrl)

  // ===== Entity Loading =====

  /**
   * Load entity connections from API and update graph
   */
  const loadEntity = useCallback(async (entityName: string) => {
    if (!entityName) return

    setIsLoading(true)
    setError(null)

    try {
      // Fetch entity connections from public API
      const response = await getEntityConnections(entityName, undefined, 100)

      setGraphData(response)
      setSelectedEntity(entityName)

      // Update URL with entity parameter
      setSearchParams({ entity: entityName })

      // Calculate filtered counts (excluding ARTICLE nodes)
      const nonArticleNodes = response.nodes.filter((node) => node.type !== 'ARTICLE')
      const articleNames = new Set(
        response.nodes.filter((n) => n.type === 'ARTICLE').map((n) => n.name)
      )
      const nonArticleEdges = response.edges.filter(
        (edge) => !articleNames.has(edge.source) && !articleNames.has(edge.target)
      )

      toast.success(`Loaded ${nonArticleNodes.length} entities with ${nonArticleEdges.length} connections`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load entity'
      setError(errorMessage)
      toast.error(errorMessage)
      console.error('Entity load error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [setSearchParams])

  // ===== Effect: Load entity from URL on mount =====
  React.useEffect(() => {
    if (entityFromUrl && !graphData) {
      loadEntity(entityFromUrl)
    }
  }, [entityFromUrl, graphData, loadEntity])

  // ===== Event Handlers =====

  /**
   * Handle entity selection from search
   */
  const handleEntitySelect = useCallback((entityName: string) => {
    loadEntity(entityName)
  }, [loadEntity])

  /**
   * Handle node click in graph
   */
  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedEntity(nodeId)
    // Optionally: Load clicked entity's connections
    // loadEntity(nodeId)
  }, [])

  /**
   * Clear current graph and selection
   */
  const handleClear = useCallback(() => {
    setGraphData(null)
    setSelectedEntity(null)
    setError(null)
    setSearchParams({})
  }, [setSearchParams])

  // ===== Render Empty State =====
  if (!graphData && !isLoading && !error) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Network className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-3xl font-bold">Knowledge Graph</h1>
              <p className="text-muted-foreground">
                Explore entity relationships and connections
              </p>
            </div>
          </div>
        </div>

        {/* Search */}
        <Card>
          <CardHeader>
            <CardTitle>Search Entities</CardTitle>
          </CardHeader>
          <CardContent>
            <EntitySearch
              onEntitySelect={handleEntitySelect}
              placeholder="Search for people, organizations, locations..."
              autoFocus
            />
          </CardContent>
        </Card>

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">What is the Knowledge Graph?</h3>
              <p className="text-muted-foreground">
                The Knowledge Graph visualizes entities (people, organizations, locations)
                and their relationships extracted from news articles.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">How to Use</h3>
              <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
                <li>Search for an entity using the search bar above</li>
                <li>View the entity's connections in an interactive graph</li>
                <li>Click on nodes to see entity details and explore connections</li>
                <li>Use filters and controls to customize the visualization</li>
              </ol>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Example Entities</h3>
              <div className="flex flex-wrap gap-2 mt-2">
                {['Tesla', 'Elon Musk', 'OpenAI', 'Apple', 'Microsoft'].map((entity) => (
                  <Button
                    key={entity}
                    variant="outline"
                    size="sm"
                    onClick={() => handleEntitySelect(entity)}
                  >
                    {entity}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // ===== Render Error State =====
  if (error && !graphData) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Network className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Knowledge Graph</h1>
          </div>
          <Button onClick={handleClear} variant="outline">
            Start Over
          </Button>
        </div>

        {/* Error */}
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <div>
                <p className="font-semibold">Error Loading Entity</p>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Retry Search */}
        <Card>
          <CardHeader>
            <CardTitle>Search Again</CardTitle>
          </CardHeader>
          <CardContent>
            <EntitySearch
              onEntitySelect={handleEntitySelect}
              placeholder="Try searching for a different entity..."
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  // ===== Render Loading State =====
  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading knowledge graph...</p>
        </div>
      </div>
    )
  }

  // ===== Render Graph View =====
  return (
    <ReactFlowProvider>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-border bg-card px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Network className="h-6 w-6 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Knowledge Graph</h1>
                {graphData && (() => {
                  // Filter out ARTICLE nodes (same as graphTransformer.ts)
                  const nonArticleNodes = graphData.nodes.filter((node) => node.type !== 'ARTICLE')
                  const articleNames = new Set(
                    graphData.nodes.filter((n) => n.type === 'ARTICLE').map((n) => n.name)
                  )
                  const nonArticleEdges = graphData.edges.filter(
                    (edge) => !articleNames.has(edge.source) && !articleNames.has(edge.target)
                  )

                  return (
                    <p className="text-sm text-muted-foreground">
                      {nonArticleNodes.length} entities • {nonArticleEdges.length} connections
                    </p>
                  )
                })()}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <EntitySearch
                onEntitySelect={handleEntitySelect}
                placeholder="Search entities..."
                className="w-80"
              />
              <Button onClick={handleClear} variant="outline" size="sm">
                Clear
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content - Graph + Sidebar */}
        <div className="flex flex-1 overflow-hidden">
          {/* Graph Visualization */}
          <div className="flex-1 relative">
            {graphData && (
              <>
                <GraphVisualization
                  graphData={graphData}
                  onNodeClick={handleNodeClick}
                  className="h-full"
                />

                {/* Overlay Controls */}
                <div className="absolute top-4 left-4 z-10 space-y-2">
                  <GraphFilters />
                  <GraphControls />
                </div>
              </>
            )}
          </div>

          {/* Entity Detail Panel (Right Sidebar) */}
          {selectedEntity && (
            <div className="w-96 border-l border-border bg-card overflow-y-auto">
              <EntityDetails
                entityName={selectedEntity}
                onClose={() => setSelectedEntity(null)}
              />
            </div>
          )}
        </div>
      </div>
    </ReactFlowProvider>
  )
}

export default KnowledgeGraphPage

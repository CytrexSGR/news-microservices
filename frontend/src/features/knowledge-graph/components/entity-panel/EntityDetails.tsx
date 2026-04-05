/**
 * EntityDetails Side Panel Component
 *
 * Displays detailed information about a selected entity including:
 * - Entity header (name, type, Wikidata link, connection count)
 * - Grouped connections by relationship type
 * - Action buttons (Explore Connections, Find Path To, View in Neo4j)
 *
 * Features:
 * - Slide-in animation from right
 * - Responsive design (sidebar on desktop, full-screen on mobile)
 * - Collapsible connection groups
 * - Loading/error states with retry
 * - Keyboard navigation (Esc to close, focus trap)
 *
 * @module features/knowledge-graph/components/entity-panel/EntityDetails
 */

import { memo, useCallback, useEffect, useMemo } from 'react'
import { ExternalLink, X, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { useEntityConnections } from '../../hooks/useEntityConnections'
import { useGraphStore } from '../../store/graphStore'
import { ENTITY_TYPE_COLORS, getEntityTypeDisplayName } from '../../utils/colorScheme'
import { cn } from '@/lib/utils'
import { ConnectionItem } from './ConnectionItem'

// ===========================
// Type Definitions
// ===========================

interface EntityDetailsProps {
  entityName: string | null
  onClose: () => void
  className?: string
}

interface ConnectionData {
  relationshipType: string
  confidence: number
  evidence?: string
  targetEntity: string
  targetEntityType: string
}

interface GroupedConnections {
  [relationshipType: string]: ConnectionData[]
}

// ===========================
// Main Component
// ===========================

export const EntityDetails = memo(function EntityDetails({
  entityName,
  onClose,
  className,
}: EntityDetailsProps) {
  // Store state
  const setSelectedEntity = useGraphStore((state) => state.setSelectedEntity)
  const detailPanelOpen = useGraphStore((state) => state.detailPanelOpen)

  // Fetch entity connections
  const {
    data: graphData,
    isLoading,
    error,
    refetch,
  } = useEntityConnections(entityName, {
    enabled: !!entityName && detailPanelOpen,
  })

  // ===========================
  // Computed Values
  // ===========================

  // Find the selected entity node
  const selectedNode = useMemo(() => {
    if (!graphData || !entityName) return null
    return graphData.nodes.find((node) => node.name === entityName)
  }, [graphData, entityName])

  // Group relationships by type and count article mentions
  const { groupedConnections, articleMentionCount } = useMemo(() => {
    if (!graphData || !entityName) return { groupedConnections: {}, articleMentionCount: 0 }

    const groups: GroupedConnections = {}
    let articleCount = 0

    graphData.edges.forEach((edge) => {
      // Only include edges connected to the selected entity
      if (edge.source !== entityName && edge.target !== entityName) return

      const relationshipType = edge.relationship_type
      if (!groups[relationshipType]) {
        groups[relationshipType] = []
      }

      // Create relationship object
      const targetNodeId = edge.source === entityName ? edge.target : edge.source
      const targetNode = graphData.nodes.find((n) => n.name === targetNodeId)

      if (!targetNode) return

      // Count ARTICLE nodes separately but don't add to groups
      if (targetNode.type === 'ARTICLE') {
        articleCount++
      } else {
        groups[relationshipType].push({
          relationshipType: edge.relationship_type,
          confidence: edge.confidence,
          evidence: edge.evidence,
          targetEntity: targetNode.name,
          targetEntityType: targetNode.type,
        })
      }
    })

    return { groupedConnections: groups, articleMentionCount: articleCount }
  }, [graphData, entityName])

  // Total connection count
  const totalConnections = useMemo(() => {
    return Object.values(groupedConnections).reduce((sum, group) => sum + group.length, 0)
  }, [groupedConnections])

  // Sort relationship types by connection count (descending)
  const sortedRelationshipTypes = useMemo(() => {
    return Object.keys(groupedConnections).sort(
      (a, b) => groupedConnections[b].length - groupedConnections[a].length
    )
  }, [groupedConnections])

  // ===========================
  // Event Handlers
  // ===========================

  // Close panel
  const handleClose = useCallback(() => {
    onClose()
    setSelectedEntity(null)
  }, [onClose, setSelectedEntity])

  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && detailPanelOpen) {
        handleClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [detailPanelOpen, handleClose])

  // Handle connection click (select that entity)
  const handleConnectionClick = useCallback(
    (targetEntity: string) => {
      setSelectedEntity(targetEntity)
    },
    [setSelectedEntity]
  )

  // Handle "Explore Connections" button
  const handleExploreConnections = useCallback(() => {
    // TODO: Phase 4 - Expand graph to show more connections
    console.log('Explore connections for:', entityName)
  }, [entityName])

  // Handle "Find Path To..." button
  const handleFindPath = useCallback(() => {
    // TODO: Phase 4 - Open pathfinding dialog
    console.log('Find path from:', entityName)
  }, [entityName])

  // ===========================
  // Render Helpers
  // ===========================

  // Render empty state
  if (!entityName) {
    return (
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-[400px] bg-background border-l border-border',
          'shadow-lg z-50 flex items-center justify-center text-muted-foreground',
          'max-md:w-full',
          className
        )}
      >
        <div className="text-center">
          <p className="text-sm">No entity selected</p>
          <p className="text-xs mt-2">Click on a node to view details</p>
        </div>
      </div>
    )
  }

  // Render loading state
  if (isLoading) {
    return (
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-[400px] bg-background border-l border-border',
          'shadow-lg z-50 flex items-center justify-center',
          'max-md:w-full animate-in slide-in-from-right duration-300',
          className
        )}
      >
        <div className="text-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-sm text-muted-foreground">Loading entity details...</p>
        </div>
      </div>
    )
  }

  // Render error state
  if (error || !selectedNode) {
    return (
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-[400px] bg-background border-l border-border',
          'shadow-lg z-50 flex flex-col',
          'max-md:w-full animate-in slide-in-from-right duration-300',
          className
        )}
      >
        {/* Header with close button */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold">Entity Details</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClose}
            aria-label="Close panel"
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Error content */}
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center space-y-4">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive" />
            <div>
              <p className="text-sm font-medium">Failed to load entity details</p>
              <p className="text-xs text-muted-foreground mt-1">
                {error?.message || 'Entity not found'}
              </p>
            </div>
            <Button onClick={() => refetch()} variant="outline" size="sm">
              Retry
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // ===========================
  // Main Render
  // ===========================

  const entityType = selectedNode.type
  const entityColor = ENTITY_TYPE_COLORS[entityType] || ENTITY_TYPE_COLORS.DEFAULT
  const wikidataId = selectedNode.properties?.wikidata_id || null

  return (
    <div
      className={cn(
        'fixed right-0 top-0 h-full w-[400px] bg-background border-l border-border',
        'shadow-lg z-50 flex flex-col',
        'max-md:w-full animate-in slide-in-from-right duration-300',
        className
      )}
      role="dialog"
      aria-labelledby="entity-details-title"
      aria-modal="true"
    >
      {/* Header with close button */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h2 id="entity-details-title" className="text-lg font-semibold">
          Entity Details
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleClose}
          aria-label="Close panel"
          className="h-8 w-8"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {/* Entity Header Section */}
        <div className="p-6 border-b border-border space-y-3">
          {/* Entity Name */}
          <h3 className="text-xl font-bold truncate">{selectedNode.name}</h3>

          {/* Entity Type Badge & Wikidata Link */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge
              style={{ backgroundColor: entityColor }}
              className="text-white font-medium"
            >
              {getEntityTypeDisplayName(entityType)}
            </Badge>
            {wikidataId && (
              <a
                href={`https://www.wikidata.org/wiki/${wikidataId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                Wikidata
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>

          {/* Connection Count */}
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">{totalConnections}</span>{' '}
            {totalConnections === 1 ? 'connection' : 'connections'}
          </p>
        </div>

        {/* Connections Section */}
        <div className="p-6 space-y-4">
          <h4 className="text-sm font-semibold uppercase text-muted-foreground">
            Relationships
          </h4>

          {totalConnections === 0 && articleMentionCount === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No connections found
            </p>
          ) : totalConnections === 0 && articleMentionCount > 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Mentioned in {articleMentionCount} article{articleMentionCount !== 1 ? 's' : ''}
              <br />
              <span className="text-xs">(No entity relationships found)</span>
            </p>
          ) : (
            <div className="space-y-3">
              {sortedRelationshipTypes.map((relationshipType) => {
                const connections = groupedConnections[relationshipType]

                // Better relationship labels
                const relationshipLabel = relationshipType
                  .replace(/_/g, ' ')
                  .toLowerCase()
                  .replace(/\b\w/g, (l) => l.toUpperCase())

                return (
                  <div
                    key={relationshipType}
                    className="border border-border rounded-lg overflow-hidden bg-card"
                  >
                    {/* Card Header */}
                    <div className="px-4 py-2.5 bg-muted/30 border-b border-border">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {relationshipLabel}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          • {connections.length}
                        </span>
                      </div>
                    </div>

                    {/* Card Content - List */}
                    <div className="divide-y divide-border">
                      {connections.slice(0, 10).map((connection, index) => (
                        <ConnectionItem
                          key={`${connection.targetEntity}-${index}`}
                          connection={connection}
                          onClick={handleConnectionClick}
                        />
                      ))}
                      {connections.length > 10 && (
                        <div className="px-4 py-3 text-center bg-muted/10">
                          <button className="text-xs text-muted-foreground hover:text-foreground transition-colors font-medium">
                            + {connections.length - 10} more
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Article Mentions Card */}
          {articleMentionCount > 0 && (
            <div className="border border-border rounded-lg overflow-hidden bg-card">
              {/* Card Header */}
              <div className="px-4 py-2.5 bg-muted/30 border-b border-border">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    📰 Article Mentions
                  </span>
                </div>
              </div>
              {/* Card Content */}
              <div className="px-4 py-3">
                <p className="text-sm text-muted-foreground">
                  Mentioned in <span className="font-medium text-foreground">{articleMentionCount}</span>{' '}
                  {articleMentionCount === 1 ? 'article' : 'articles'}
                </p>
                {selectedNode.properties?.last_seen && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Last seen: {new Date(selectedNode.properties.last_seen).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Actions Section */}
        <div className="p-6 border-t border-border space-y-2">
          <h4 className="text-sm font-semibold uppercase text-muted-foreground mb-3">
            Actions
          </h4>
          <Button
            onClick={handleExploreConnections}
            className="w-full"
            variant="default"
            size="sm"
          >
            Explore Connections
          </Button>
          <Button onClick={handleFindPath} className="w-full" variant="outline" size="sm">
            Find Path To...
          </Button>
          <Button className="w-full" variant="outline" size="sm" disabled>
            View in Neo4j
            <span className="text-xs ml-2">(Phase 4)</span>
          </Button>
        </div>
      </div>
    </div>
  )
})

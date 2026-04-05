/**
 * Graph Controls Component
 *
 * Comprehensive toolbar for graph manipulation with controls for:
 * - Layout selection (Force-Directed, Hierarchical, Radial)
 * - Zoom controls (In/Out/Fit View)
 * - View toggles (Labels, Legend)
 * - Filter panel toggle with active indicator
 * - Export options (JSON functional, PNG/SVG stubs)
 *
 * Features:
 * - Toast notifications for user feedback
 * - Disabled states during operations
 * - Active layout indicator badge
 * - Filter reset button (conditional)
 * - Lucide icons for all actions
 *
 * @module features/knowledge-graph/components/graph-viewer/GraphControls
 */

import { useState } from 'react'
import { useReactFlow } from '@xyflow/react'
import { Button } from '@/components/ui/Button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu'
import { Badge } from '@/components/ui/badge'
import {
  Layout,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  Grid,
  Eye,
  EyeOff,
  Filter,
  RotateCcw,
} from 'lucide-react'
import { useGraphStore, useHasActiveFilters } from '@/features/knowledge-graph/store'
import { exportToJSON } from '@/features/knowledge-graph/utils'
import { toast } from 'react-hot-toast'

// ===========================
// Component Props
// ===========================

export interface GraphControlsProps {
  /** Callback when filter toggle button is clicked */
  onFilterToggle?: () => void
  /** Additional CSS classes */
  className?: string
}

// ===========================
// Component
// ===========================

/**
 * Graph Controls Toolbar Component.
 *
 * Provides comprehensive controls for graph manipulation including
 * layout selection, zoom, view toggles, filters, and export.
 *
 * @example
 * <GraphControls
 *   onFilterToggle={() => setFilterPanelOpen(true)}
 *   className="mb-4"
 * />
 */
export function GraphControls({ onFilterToggle, className = '' }: GraphControlsProps) {
  const reactFlowInstance = useReactFlow()

  // ===== Zustand Store State =====
  const layoutType = useGraphStore((state) => state.layoutType)
  const setLayoutType = useGraphStore((state) => state.setLayoutType)
  const showLabels = useGraphStore((state) => state.showLabels)
  const toggleLabels = useGraphStore((state) => state.toggleLabels)
  const showLegend = useGraphStore((state) => state.showLegend)
  const toggleLegend = useGraphStore((state) => state.toggleLegend)
  const resetFilters = useGraphStore((state) => state.resetFilters)

  // Use the utility hook to check if any filters are active
  const hasActiveFilters = useHasActiveFilters()

  // ===== Local State =====
  const [isExporting, setIsExporting] = useState(false)

  // ===========================
  // Zoom Controls
  // ===========================

  const handleZoomIn = () => {
    reactFlowInstance.zoomIn({ duration: 300 })
    toast.success('Zoomed in')
  }

  const handleZoomOut = () => {
    reactFlowInstance.zoomOut({ duration: 300 })
    toast.success('Zoomed out')
  }

  const handleFitView = () => {
    reactFlowInstance.fitView({ padding: 0.2, duration: 300 })
    toast.success('View fit to graph')
  }

  // ===========================
  // Layout Controls
  // ===========================

  const handleLayoutChange = (layout: 'force' | 'hierarchical' | 'radial') => {
    setLayoutType(layout)
    toast.success(`Layout changed to ${layout}`)
  }

  // ===========================
  // Export Controls
  // ===========================

  const handleExport = async (format: 'png' | 'svg' | 'json') => {
    setIsExporting(true)

    try {
      const nodes = reactFlowInstance.getNodes()
      const edges = reactFlowInstance.getEdges()

      // Validate data
      if (nodes.length === 0) {
        toast.error('No graph data to export')
        return
      }

      switch (format) {
        case 'json':
          await exportToJSON(nodes, edges, 'knowledge-graph.json')
          toast.success('Graph exported as JSON')
          break

        case 'png':
          // Stub for Phase 4
          toast.error('PNG export coming in Phase 4', {
            duration: 3000,
            icon: '🚧',
          })
          break

        case 'svg':
          // Stub for Phase 4
          toast.error('SVG export coming in Phase 4', {
            duration: 3000,
            icon: '🚧',
          })
          break
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      toast.error(`Export failed: ${errorMessage}`)
      console.error('Export error:', error)
    } finally {
      setIsExporting(false)
    }
  }

  // ===========================
  // Filter Controls
  // ===========================

  const handleResetFilters = () => {
    resetFilters()
    toast.success('Filters reset')
  }

  // ===========================
  // Render
  // ===========================

  return (
    <div className={`flex items-center gap-2 bg-white rounded-lg shadow-sm p-2 border ${className}`}>
      {/* ===== Layout Selector ===== */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <Layout className="w-4 h-4" />
            <span className="capitalize">{layoutType}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuLabel>Graph Layout</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => handleLayoutChange('force')}>
            <Grid className="w-4 h-4 mr-2" />
            Force-Directed
            {layoutType === 'force' && (
              <Badge variant="default" className="ml-auto text-xs">
                Active
              </Badge>
            )}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleLayoutChange('hierarchical')}>
            <Layout className="w-4 h-4 mr-2" />
            Hierarchical
            {layoutType === 'hierarchical' && (
              <Badge variant="default" className="ml-auto text-xs">
                Active
              </Badge>
            )}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleLayoutChange('radial')}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Radial
            {layoutType === 'radial' && (
              <Badge variant="default" className="ml-auto text-xs">
                Active
              </Badge>
            )}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* ===== Zoom Controls ===== */}
      <div className="flex items-center border rounded-md overflow-hidden">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          className="rounded-none border-r"
          title="Zoom out"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleFitView}
          className="rounded-none border-r"
          title="Fit view to graph"
        >
          <Maximize2 className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          className="rounded-none"
          title="Zoom in"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
      </div>

      {/* ===== View Toggles ===== */}
      <div className="flex items-center gap-1">
        <Button
          variant={showLabels ? 'default' : 'outline'}
          size="sm"
          onClick={toggleLabels}
          title={showLabels ? 'Hide labels' : 'Show labels'}
        >
          {showLabels ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          <span className="ml-2">Labels</span>
        </Button>

        <Button
          variant={showLegend ? 'default' : 'outline'}
          size="sm"
          onClick={toggleLegend}
          title={showLegend ? 'Hide legend' : 'Show legend'}
        >
          Legend
        </Button>
      </div>

      {/* ===== Divider ===== */}
      <div className="h-6 w-px bg-border" />

      {/* ===== Filter Controls ===== */}
      {onFilterToggle && (
        <Button variant="outline" size="sm" onClick={onFilterToggle} className="gap-2" title="Toggle filters panel">
          <Filter className="w-4 h-4" />
          Filters
          {hasActiveFilters && (
            <Badge variant="destructive" className="ml-1 px-1.5 py-0.5 text-xs">
              Active
            </Badge>
          )}
        </Button>
      )}

      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleResetFilters}
          className="text-red-600 hover:text-red-700 hover:bg-red-50"
          title="Reset all filters"
        >
          <RotateCcw className="w-4 h-4 mr-1" />
          Reset
        </Button>
      )}

      {/* ===== Divider ===== */}
      <div className="h-6 w-px bg-border" />

      {/* ===== Export Menu ===== */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" disabled={isExporting} className="gap-2" title="Export graph">
            <Download className="w-4 h-4" />
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Export Graph</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => handleExport('json')} disabled={isExporting}>
            <Download className="w-4 h-4 mr-2" />
            Export as JSON
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleExport('png')} disabled>
            <Download className="w-4 h-4 mr-2" />
            Export as PNG <span className="ml-2 text-xs text-muted-foreground">(Phase 4)</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleExport('svg')} disabled>
            <Download className="w-4 h-4 mr-2" />
            Export as SVG <span className="ml-2 text-xs text-muted-foreground">(Phase 4)</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

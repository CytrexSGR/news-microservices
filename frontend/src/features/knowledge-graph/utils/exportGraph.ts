/**
 * Graph Export Utility
 *
 * Provides functions to export knowledge graph visualizations to various formats.
 * Currently supports PNG/SVG export (stubs for Phase 4 implementation).
 *
 * @module features/knowledge-graph/utils/exportGraph
 */

import type { EntityNode, RelationshipEdge } from '../../../types/knowledgeGraphPublic'

// ===========================
// Export Types
// ===========================

/**
 * Supported export formats.
 */
export type ExportFormat = 'png' | 'svg' | 'json'

/**
 * Export options configuration.
 */
export interface ExportOptions {
  /** Image format (png or svg) */
  format: ExportFormat
  /** Image width in pixels (for png) */
  width?: number
  /** Image height in pixels (for png) */
  height?: number
  /** Background color (default: white) */
  backgroundColor?: string
  /** Include legend in export */
  includeLegend?: boolean
  /** Include metadata (title, date) */
  includeMetadata?: boolean
  /** Export filename (without extension) */
  filename?: string
  /** Image quality (0.0 - 1.0, for png) */
  quality?: number
}

/**
 * Default export options.
 */
export const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  format: 'png',
  width: 1920,
  height: 1080,
  backgroundColor: '#ffffff',
  includeLegend: true,
  includeMetadata: true,
  filename: 'knowledge-graph',
  quality: 0.92,
}

// ===========================
// Export Functions (Stubs)
// ===========================

/**
 * Export graph to PNG image.
 *
 * **STUB for Phase 4 Implementation**
 *
 * Implementation will use html2canvas or similar library to:
 * 1. Capture React Flow canvas as image
 * 2. Add legend/metadata if requested
 * 3. Download as PNG file
 *
 * @param nodes - Entity nodes to export
 * @param edges - Relationship edges to export
 * @param options - Export options
 * @returns Promise resolving to Blob or data URL
 *
 * @example
 * await exportToPNG(nodes, edges, {
 *   width: 1920,
 *   height: 1080,
 *   filename: 'my-graph'
 * })
 */
export async function exportToPNG(
  nodes: EntityNode[],
  edges: RelationshipEdge[],
  options: Partial<ExportOptions> = {}
): Promise<Blob | string> {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options, format: 'png' as const }

  // TODO: Phase 4 Implementation
  // 1. Get React Flow instance ref
  // 2. Use html2canvas or similar to capture canvas
  // 3. Add legend/metadata overlay if requested
  // 4. Convert to Blob
  // 5. Trigger download

  console.warn('exportToPNG: Stub implementation - not yet functional')
  console.log('Export options:', opts)
  console.log('Nodes to export:', nodes.length)
  console.log('Edges to export:', edges.length)

  // Return empty blob for now
  return new Blob([], { type: 'image/png' })
}

/**
 * Export graph to SVG vector image.
 *
 * **STUB for Phase 4 Implementation**
 *
 * Implementation will:
 * 1. Extract SVG from React Flow canvas
 * 2. Add legend/metadata if requested
 * 3. Download as SVG file
 *
 * @param nodes - Entity nodes to export
 * @param edges - Relationship edges to export
 * @param options - Export options
 * @returns Promise resolving to SVG string
 *
 * @example
 * await exportToSVG(nodes, edges, {
 *   filename: 'my-graph',
 *   includeLegend: true
 * })
 */
export async function exportToSVG(
  nodes: EntityNode[],
  edges: RelationshipEdge[],
  options: Partial<ExportOptions> = {}
): Promise<string> {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options, format: 'svg' as const }

  // TODO: Phase 4 Implementation
  // 1. Get React Flow SVG
  // 2. Add legend/metadata elements if requested
  // 3. Serialize to string
  // 4. Trigger download

  console.warn('exportToSVG: Stub implementation - not yet functional')
  console.log('Export options:', opts)
  console.log('Nodes to export:', nodes.length)
  console.log('Edges to export:', edges.length)

  // Return empty SVG for now
  return '<svg></svg>'
}

/**
 * Export graph data to JSON.
 *
 * Exports raw node/edge data as JSON for:
 * - Data backup
 * - External analysis
 * - Import into other tools
 *
 * @param nodes - Entity nodes to export
 * @param edges - Relationship edges to export
 * @param options - Export options
 * @returns Promise resolving to JSON string
 *
 * @example
 * await exportToJSON(nodes, edges, {
 *   filename: 'graph-data'
 * })
 */
export async function exportToJSON(
  nodes: EntityNode[],
  edges: RelationshipEdge[],
  options: Partial<ExportOptions> = {}
): Promise<string> {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options, format: 'json' as const }

  const data = {
    metadata: {
      exportDate: new Date().toISOString(),
      nodeCount: nodes.length,
      edgeCount: edges.length,
      ...(opts.includeMetadata && {
        filename: opts.filename,
        format: opts.format,
      }),
    },
    nodes,
    edges,
  }

  const json = JSON.stringify(data, null, 2)

  // Trigger download
  downloadFile(json, `${opts.filename}.json`, 'application/json')

  return json
}

// ===========================
// Utility Functions
// ===========================

/**
 * Trigger browser download of file.
 *
 * Creates temporary anchor element to trigger download.
 *
 * @param content - File content (string or Blob)
 * @param filename - Download filename
 * @param mimeType - MIME type for file
 */
export function downloadFile(content: string | Blob, filename: string, mimeType: string): void {
  const blob = typeof content === 'string' ? new Blob([content], { type: mimeType }) : content

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()

  // Cleanup
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

/**
 * Get export button props for React component.
 *
 * Helper to generate button props with proper handlers.
 *
 * @param format - Export format
 * @param nodes - Entity nodes
 * @param edges - Relationship edges
 * @param options - Export options
 * @returns Button props object
 *
 * @example
 * const pngButtonProps = getExportButtonProps('png', nodes, edges)
 * <button {...pngButtonProps}>Export as PNG</button>
 */
export function getExportButtonProps(
  format: ExportFormat,
  nodes: EntityNode[],
  edges: RelationshipEdge[],
  options: Partial<ExportOptions> = {}
): {
  onClick: () => Promise<void>
  disabled: boolean
  title: string
} {
  const isDisabled = nodes.length === 0 && edges.length === 0

  const handlers: Record<ExportFormat, () => Promise<void>> = {
    png: () => exportToPNG(nodes, edges, options).then(() => {}),
    svg: () => exportToSVG(nodes, edges, options).then(() => {}),
    json: () => exportToJSON(nodes, edges, options).then(() => {}),
  }

  const titles: Record<ExportFormat, string> = {
    png: 'Export graph as PNG image',
    svg: 'Export graph as SVG vector image',
    json: 'Export graph data as JSON',
  }

  return {
    onClick: handlers[format],
    disabled: isDisabled,
    title: isDisabled ? 'No graph to export' : titles[format],
  }
}

/**
 * Estimate export file size (rough approximation).
 *
 * @param nodes - Entity nodes
 * @param edges - Relationship edges
 * @param format - Export format
 * @returns Estimated file size in bytes
 */
export function estimateExportSize(
  nodes: EntityNode[],
  edges: RelationshipEdge[],
  format: ExportFormat
): number {
  // Rough estimates based on average entity sizes
  const avgNodeSize = 200 // bytes in JSON
  const avgEdgeSize = 150 // bytes in JSON

  const jsonSize = nodes.length * avgNodeSize + edges.length * avgEdgeSize

  switch (format) {
    case 'json':
      return jsonSize

    case 'png':
      // PNG: Rough estimate based on complexity
      // Assume ~1-2KB per node (rendered to bitmap)
      return nodes.length * 1500 + edges.length * 500

    case 'svg':
      // SVG: Text-based, larger than JSON but smaller than PNG
      return jsonSize * 1.5

    default:
      return jsonSize
  }
}

/**
 * Format file size for display.
 *
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "1.2 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ===========================
// Export Validation
// ===========================

/**
 * Validate graph data before export.
 *
 * Checks for:
 * - Empty graph
 * - Disconnected nodes
 * - Invalid node/edge data
 *
 * @param nodes - Entity nodes to validate
 * @param edges - Relationship edges to validate
 * @returns Validation result with warnings
 */
export function validateExportData(
  nodes: EntityNode[],
  edges: RelationshipEdge[]
): {
  valid: boolean
  warnings: string[]
  errors: string[]
} {
  const warnings: string[] = []
  const errors: string[] = []

  // Check for empty graph
  if (nodes.length === 0) {
    errors.push('Graph has no nodes')
  }

  if (edges.length === 0) {
    warnings.push('Graph has no edges')
  }

  // Check for orphaned nodes (nodes with no edges)
  const connectedNodeIds = new Set([...edges.map((e) => e.source), ...edges.map((e) => e.target)])
  const orphanedNodes = nodes.filter((n) => !connectedNodeIds.has(n.id))

  if (orphanedNodes.length > 0) {
    warnings.push(`${orphanedNodes.length} nodes have no connections`)
  }

  // Check for invalid node positions (might not render correctly)
  const nodesWithoutPosition = nodes.filter((n) => !n.position || isNaN(n.position.x))

  if (nodesWithoutPosition.length > 0) {
    warnings.push(`${nodesWithoutPosition.length} nodes have invalid positions`)
  }

  return {
    valid: errors.length === 0,
    warnings,
    errors,
  }
}

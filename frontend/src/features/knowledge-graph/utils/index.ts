/**
 * Knowledge Graph Utilities Index
 *
 * Re-exports all utility functions for knowledge graph feature.
 *
 * @module features/knowledge-graph/utils
 */

// Graph Transformation
export {
  transformToReactFlow,
  filterGraph,
  calculateGraphStats,
} from './graphTransformer'

// Color Scheme
export {
  ENTITY_TYPE_COLORS,
  ENTITY_TYPE_COLORS_LIGHT,
  ENTITY_TYPE_COLORS_DARK,
  RELATIONSHIP_COLORS,
  ENTITY_TYPE_ICONS,
  RELATIONSHIP_TYPE_ICONS,
  CONFIDENCE_COLORS,
  getConfidenceColor,
  getConfidenceLabel,
  getEntityTypeDisplayName,
  getRelationshipTypeDisplayName,
  getUniqueEntityTypes,
  getUniqueRelationshipTypes,
  getEntityTypeBadgeClasses,
  getConfidenceBadgeClasses,
} from './colorScheme'

// Export
export {
  exportToPNG,
  exportToSVG,
  exportToJSON,
  downloadFile,
  getExportButtonProps,
  estimateExportSize,
  formatFileSize,
  validateExportData,
} from './exportGraph'

export type { ExportFormat, ExportOptions } from './exportGraph'

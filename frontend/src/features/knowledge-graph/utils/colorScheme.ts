/**
 * Color Scheme for Knowledge Graph Visualization
 *
 * Defines consistent color mappings for entity types and relationship types
 * across the knowledge graph feature.
 *
 * @module features/knowledge-graph/utils/colorScheme
 */

// ===========================
// Entity Type Colors
// ===========================

/**
 * Color mapping for entity types.
 *
 * Uses Tailwind CSS color palette for consistency with rest of app.
 * Colors are optimized for:
 * - Visual distinction (high contrast)
 * - Semantic meaning (e.g., blue for people, green for organizations)
 * - Accessibility (WCAG AA compliant)
 *
 * @example
 * const nodeColor = ENTITY_TYPE_COLORS[node.type] ?? ENTITY_TYPE_COLORS.DEFAULT
 */
export const ENTITY_TYPE_COLORS: Record<string, string> = {
  // Core Entity Types
  PERSON: '#3B82F6', // Blue-500 - Associated with people
  ORGANIZATION: '#10B981', // Green-500 - Associated with institutions
  LOCATION: '#F59E0B', // Amber-500 - Associated with places
  EVENT: '#EF4444', // Red-500 - Associated with time-bound occurrences
  PRODUCT: '#8B5CF6', // Purple-500 - Associated with products/services

  // Extended Entity Types
  MISC: '#6B7280', // Gray-500 - Miscellaneous
  OTHER: '#6B7280', // Gray-500 - Other/Unknown
  NOT_APPLICABLE: '#9CA3AF', // Gray-400 - Not classified

  // Fallback
  DEFAULT: '#6B7280', // Gray-500 - Default for unknown types
}

/**
 * Light variants for hover/selection states.
 * 200-weight colors from Tailwind palette.
 */
export const ENTITY_TYPE_COLORS_LIGHT: Record<string, string> = {
  PERSON: '#BFDBFE', // Blue-200
  ORGANIZATION: '#A7F3D0', // Green-200
  LOCATION: '#FDE68A', // Amber-200
  EVENT: '#FECACA', // Red-200
  PRODUCT: '#DDD6FE', // Purple-200
  MISC: '#D1D5DB', // Gray-300
  OTHER: '#D1D5DB', // Gray-300
  NOT_APPLICABLE: '#E5E7EB', // Gray-200
  DEFAULT: '#D1D5DB', // Gray-300
}

/**
 * Dark variants for borders/emphasis.
 * 700-weight colors from Tailwind palette.
 */
export const ENTITY_TYPE_COLORS_DARK: Record<string, string> = {
  PERSON: '#1D4ED8', // Blue-700
  ORGANIZATION: '#047857', // Green-700
  LOCATION: '#B45309', // Amber-700
  EVENT: '#B91C1C', // Red-700
  PRODUCT: '#6D28D9', // Purple-700
  MISC: '#374151', // Gray-700
  OTHER: '#374151', // Gray-700
  NOT_APPLICABLE: '#4B5563', // Gray-600
  DEFAULT: '#374151', // Gray-700
}

// ===========================
// Relationship Type Colors
// ===========================

/**
 * Color mapping for relationship types.
 *
 * Uses distinct colors to differentiate relationship types.
 * Colors chosen to avoid confusion with entity type colors.
 *
 * @example
 * const edgeColor = RELATIONSHIP_COLORS[edge.type] ?? RELATIONSHIP_COLORS.DEFAULT
 */
export const RELATIONSHIP_COLORS: Record<string, string> = {
  // Employment & Professional
  WORKS_FOR: '#3B82F6', // Blue-500 - Employment
  MANAGES: '#06B6D4', // Cyan-500 - Management
  FOUNDED_BY: '#14B8A6', // Teal-500 - Founding

  // Partnerships & Collaboration
  PARTNERS_WITH: '#10B981', // Green-500 - Partnership
  AFFILIATED_WITH: '#22C55E', // Green-400 - Affiliation
  COLLABORATES_WITH: '#84CC16', // Lime-500 - Collaboration

  // Geographic & Location
  LOCATED_IN: '#F59E0B', // Amber-500 - Location
  HEADQUARTERED_IN: '#F97316', // Orange-500 - HQ Location
  OPERATES_IN: '#FB923C', // Orange-400 - Operations

  // Ownership & Control
  OWNS: '#8B5CF6', // Purple-500 - Ownership
  ACQUIRED_BY: '#A855F7', // Purple-400 - Acquisition
  PART_OF: '#C084FC', // Purple-300 - Subsidiary

  // Competition & Conflict
  COMPETES_WITH: '#EF4444', // Red-500 - Competition
  OPPOSES: '#DC2626', // Red-600 - Opposition

  // Generic Relations
  RELATED_TO: '#6B7280', // Gray-500 - Generic relation
  MENTIONED_WITH: '#9CA3AF', // Gray-400 - Co-mention
  ASSOCIATED_WITH: '#D1D5DB', // Gray-300 - Association

  // Fallback
  DEFAULT: '#6B7280', // Gray-500 - Default for unknown types
}

// ===========================
// Icon Mappings
// ===========================

/**
 * Emoji icons for entity types.
 * Used in legend, tooltips, and detail panels.
 */
export const ENTITY_TYPE_ICONS: Record<string, string> = {
  PERSON: '👤',
  ORGANIZATION: '🏢',
  LOCATION: '📍',
  EVENT: '📅',
  PRODUCT: '📦',
  MISC: '🔖',
  OTHER: '❓',
  NOT_APPLICABLE: '⚪',
}

/**
 * Emoji icons for relationship types.
 * Used in edge labels and tooltips.
 */
export const RELATIONSHIP_TYPE_ICONS: Record<string, string> = {
  WORKS_FOR: '💼',
  MANAGES: '👔',
  FOUNDED_BY: '🏗️',
  PARTNERS_WITH: '🤝',
  AFFILIATED_WITH: '🔗',
  COLLABORATES_WITH: '🤝',
  LOCATED_IN: '📍',
  HEADQUARTERED_IN: '🏢',
  OPERATES_IN: '🌍',
  OWNS: '🏛️',
  ACQUIRED_BY: '💰',
  PART_OF: '🧩',
  COMPETES_WITH: '⚔️',
  OPPOSES: '🚫',
  RELATED_TO: '↔️',
  MENTIONED_WITH: '💬',
  ASSOCIATED_WITH: '🔗',
  DEFAULT: '→',
}

// ===========================
// Confidence Color Scale
// ===========================

/**
 * Color scale for confidence levels (0.0 - 1.0).
 *
 * Green = High confidence
 * Yellow = Medium confidence
 * Red = Low confidence
 */
export const CONFIDENCE_COLORS = {
  HIGH: '#10B981', // Green-500 (>= 0.8)
  MEDIUM: '#F59E0B', // Amber-500 (>= 0.5)
  LOW: '#EF4444', // Red-500 (< 0.5)
}

/**
 * Get confidence color based on value.
 *
 * @param confidence - Confidence value (0.0 - 1.0)
 * @returns Hex color code
 *
 * @example
 * const color = getConfidenceColor(0.85) // Returns '#10B981' (green)
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return CONFIDENCE_COLORS.HIGH
  if (confidence >= 0.5) return CONFIDENCE_COLORS.MEDIUM
  return CONFIDENCE_COLORS.LOW
}

/**
 * Get confidence label based on value.
 *
 * @param confidence - Confidence value (0.0 - 1.0)
 * @returns Human-readable label
 */
export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return 'High'
  if (confidence >= 0.5) return 'Medium'
  return 'Low'
}

// ===========================
// Utility Functions
// ===========================

/**
 * Get entity type display name.
 *
 * Converts SCREAMING_SNAKE_CASE to Title Case.
 *
 * @param type - Entity type (e.g., "PERSON", "ORGANIZATION")
 * @returns Display name (e.g., "Person", "Organization")
 */
export function getEntityTypeDisplayName(type: string): string {
  return type
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Get relationship type display name.
 *
 * Converts SCREAMING_SNAKE_CASE to Title Case and replaces underscores.
 *
 * @param type - Relationship type (e.g., "WORKS_FOR")
 * @returns Display name (e.g., "Works For")
 */
export function getRelationshipTypeDisplayName(type: string): string {
  return type
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Get all unique entity types from nodes.
 *
 * @param nodes - Entity nodes
 * @returns Sorted array of unique entity types
 */
export function getUniqueEntityTypes(nodes: Array<{ data: { entityType: string } }>): string[] {
  const types = new Set(nodes.map((n) => n.data.entityType))
  return Array.from(types).sort()
}

/**
 * Get all unique relationship types from edges.
 *
 * @param edges - Relationship edges
 * @returns Sorted array of unique relationship types
 */
export function getUniqueRelationshipTypes(
  edges: Array<{ data: { relationshipType: string } }>
): string[] {
  const types = new Set(edges.map((e) => e.data.relationshipType))
  return Array.from(types).sort()
}

// ===========================
// CSS Class Generators
// ===========================

/**
 * Generate Tailwind CSS classes for entity type badge.
 *
 * @param type - Entity type
 * @returns CSS class string
 *
 * @example
 * <span className={getEntityTypeBadgeClasses('PERSON')}>Person</span>
 */
export function getEntityTypeBadgeClasses(type: string): string {
  const baseClasses = 'px-2 py-1 rounded-full text-xs font-medium'

  const typeClasses: Record<string, string> = {
    PERSON: 'bg-blue-100 text-blue-800',
    ORGANIZATION: 'bg-green-100 text-green-800',
    LOCATION: 'bg-amber-100 text-amber-800',
    EVENT: 'bg-red-100 text-red-800',
    PRODUCT: 'bg-purple-100 text-purple-800',
    MISC: 'bg-gray-100 text-gray-800',
    OTHER: 'bg-gray-100 text-gray-800',
    NOT_APPLICABLE: 'bg-gray-50 text-gray-600',
  }

  const specificClasses = typeClasses[type] ?? typeClasses.OTHER

  return `${baseClasses} ${specificClasses}`
}

/**
 * Generate Tailwind CSS classes for confidence badge.
 *
 * @param confidence - Confidence value (0.0 - 1.0)
 * @returns CSS class string
 */
export function getConfidenceBadgeClasses(confidence: number): string {
  const baseClasses = 'px-2 py-1 rounded-full text-xs font-medium'

  if (confidence >= 0.8) {
    return `${baseClasses} bg-green-100 text-green-800`
  }
  if (confidence >= 0.5) {
    return `${baseClasses} bg-amber-100 text-amber-800`
  }
  return `${baseClasses} bg-red-100 text-red-800`
}

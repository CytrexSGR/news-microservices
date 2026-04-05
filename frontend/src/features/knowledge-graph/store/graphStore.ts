/**
 * Zustand Store for Knowledge Graph UI State Management
 *
 * Manages global state for graph visualization including:
 * - Entity selection/hover state
 * - Layout configuration
 * - Filters (entity types, relationships, confidence)
 * - UI state (sidebars, zoom level)
 * - Recent searches (persisted)
 *
 * Features:
 * - Devtools middleware for debugging
 * - Persist middleware for localStorage
 * - Type-safe actions and selectors
 * - Auto-open detail panel on entity selection
 *
 * @see {@link FilterState} for filter configuration
 * @see {@link GraphUIState} for UI state shape
 */

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { FilterState } from '@/types/knowledgeGraphPublic'

// ===========================
// Store State Interface
// ===========================

interface GraphStore {
  // ===== Entity Selection =====
  /** Currently selected entity ID (null if none selected) */
  selectedEntity: string | null
  /** Set selected entity (opens detail panel automatically) */
  setSelectedEntity: (entityId: string | null) => void

  /** Currently hovered entity ID (for hover highlights) */
  hoveredEntity: string | null
  /** Set hovered entity */
  setHoveredEntity: (entityId: string | null) => void

  // ===== Layout Configuration =====
  /** Current graph layout algorithm */
  layoutType: 'force' | 'hierarchical' | 'radial'
  /** Change layout algorithm */
  setLayoutType: (layout: 'force' | 'hierarchical' | 'radial') => void

  // ===== Filters =====
  /** Current filter state (entity types, relationships, confidence) */
  filters: FilterState
  /** Update filters (partial update) */
  setFilters: (filters: Partial<FilterState>) => void
  /** Reset filters to default values */
  resetFilters: () => void

  // ===== Zoom & Pan =====
  /** Current zoom level (1.0 = 100%, 0.1-2.0 range) */
  zoomLevel: number
  /** Set zoom level */
  setZoomLevel: (zoom: number) => void

  // ===== Recent Searches (Persisted) =====
  /** Recent entity search queries (max 10) */
  recentSearches: string[]
  /** Add search query to recent searches */
  addRecentSearch: (query: string) => void
  /** Clear all recent searches */
  clearRecentSearches: () => void

  // ===== UI Visibility =====
  /** Whether sidebar is open */
  sidebarOpen: boolean
  /** Toggle sidebar visibility */
  toggleSidebar: () => void

  /** Whether detail panel is open */
  detailPanelOpen: boolean
  /** Toggle detail panel visibility */
  toggleDetailPanel: () => void

  // ===== Labels & Legend =====
  /** Whether to show edge labels */
  showLabels: boolean
  /** Toggle edge labels visibility */
  toggleLabels: () => void

  /** Whether to show entity type legend */
  showLegend: boolean
  /** Toggle legend visibility */
  toggleLegend: () => void

  // ===== Reset =====
  /** Reset entire store to default state (except persisted values) */
  reset: () => void
}

// ===========================
// Default Values
// ===========================

/** Default filter state (show all entities/relationships) */
const DEFAULT_FILTERS: FilterState = {
  entityTypes: [],
  relationshipTypes: [],
  minConfidence: 0.5,
  minConnectionCount: undefined,
  dateRange: undefined,
  searchQuery: undefined,
}

/** Initial UI state */
const INITIAL_STATE = {
  selectedEntity: null,
  hoveredEntity: null,
  layoutType: 'force' as const,
  filters: DEFAULT_FILTERS,
  zoomLevel: 1.0,
  recentSearches: [],
  sidebarOpen: true,
  detailPanelOpen: false,
  showLabels: true,
  showLegend: true,
}

// ===========================
// Store Implementation
// ===========================

export const useGraphStore = create<GraphStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        ...INITIAL_STATE,

        // ===== Entity Selection Actions =====
        setSelectedEntity: (entityId) => {
          set({ selectedEntity: entityId }, false, 'setSelectedEntity')

          // Auto-open detail panel when selecting entity
          if (entityId && !get().detailPanelOpen) {
            set({ detailPanelOpen: true }, false, 'autoOpenDetailPanel')
          }
        },

        setHoveredEntity: (entityId) => {
          set({ hoveredEntity: entityId }, false, 'setHoveredEntity')
        },

        // ===== Layout Actions =====
        setLayoutType: (layout) => {
          set({ layoutType: layout }, false, 'setLayoutType')
        },

        // ===== Filter Actions =====
        setFilters: (newFilters) => {
          set(
            (state) => ({
              filters: { ...state.filters, ...newFilters },
            }),
            false,
            'setFilters'
          )
        },

        resetFilters: () => {
          set({ filters: DEFAULT_FILTERS }, false, 'resetFilters')
        },

        // ===== Zoom Actions =====
        setZoomLevel: (zoom) => {
          // Clamp zoom level to 0.1 - 2.0 range
          const clampedZoom = Math.max(0.1, Math.min(2.0, zoom))
          set({ zoomLevel: clampedZoom }, false, 'setZoomLevel')
        },

        // ===== Recent Searches Actions =====
        addRecentSearch: (query) => {
          // Trim query
          const trimmedQuery = query.trim()
          if (!trimmedQuery) return

          const currentSearches = get().recentSearches
          const updatedSearches = [
            trimmedQuery,
            // Remove duplicate if exists, keep others
            ...currentSearches.filter((q) => q !== trimmedQuery),
          ].slice(0, 10) // Keep only 10 most recent

          set({ recentSearches: updatedSearches }, false, 'addRecentSearch')
        },

        clearRecentSearches: () => {
          set({ recentSearches: [] }, false, 'clearRecentSearches')
        },

        // ===== UI Visibility Actions =====
        toggleSidebar: () => {
          set((state) => ({ sidebarOpen: !state.sidebarOpen }), false, 'toggleSidebar')
        },

        toggleDetailPanel: () => {
          set((state) => ({ detailPanelOpen: !state.detailPanelOpen }), false, 'toggleDetailPanel')
        },

        toggleLabels: () => {
          set((state) => ({ showLabels: !state.showLabels }), false, 'toggleLabels')
        },

        toggleLegend: () => {
          set((state) => ({ showLegend: !state.showLegend }), false, 'toggleLegend')
        },

        // ===== Reset Action =====
        reset: () => {
          set(
            {
              selectedEntity: null,
              hoveredEntity: null,
              layoutType: 'force',
              filters: DEFAULT_FILTERS,
              zoomLevel: 1.0,
              sidebarOpen: true,
              detailPanelOpen: false,
              showLabels: true,
              showLegend: true,
              // Note: recentSearches is NOT reset (persisted)
            },
            false,
            'reset'
          )
        },
      }),
      {
        name: 'knowledge-graph-store',
        // Only persist these keys to localStorage
        partialize: (state) => ({
          layoutType: state.layoutType,
          filters: state.filters,
          recentSearches: state.recentSearches,
          sidebarOpen: state.sidebarOpen,
          showLabels: state.showLabels,
          showLegend: state.showLegend,
        }),
      }
    ),
    { name: 'KnowledgeGraphStore' }
  )
)

// ===========================
// Selector Hooks (Optimized)
// ===========================

/**
 * Hook to get selected entity ID.
 * Re-renders only when selectedEntity changes.
 */
export const useSelectedEntity = () => useGraphStore((state) => state.selectedEntity)

/**
 * Hook to get hovered entity ID.
 * Re-renders only when hoveredEntity changes.
 */
export const useHoveredEntity = () => useGraphStore((state) => state.hoveredEntity)

/**
 * Hook to get current layout type.
 * Re-renders only when layoutType changes.
 */
export const useLayoutType = () => useGraphStore((state) => state.layoutType)

/**
 * Hook to get current filters.
 * Re-renders only when filters change.
 */
export const useFilters = () => useGraphStore((state) => state.filters)

/**
 * Hook to get recent searches.
 * Re-renders only when recentSearches change.
 */
export const useRecentSearches = () => useGraphStore((state) => state.recentSearches)

/**
 * Hook to get zoom level.
 * Re-renders only when zoomLevel changes.
 */
export const useZoomLevel = () => useGraphStore((state) => state.zoomLevel)

/**
 * Hook to get sidebar open state.
 * Re-renders only when sidebarOpen changes.
 */
export const useSidebarOpen = () => useGraphStore((state) => state.sidebarOpen)

/**
 * Hook to get detail panel open state.
 * Re-renders only when detailPanelOpen changes.
 */
export const useDetailPanelOpen = () => useGraphStore((state) => state.detailPanelOpen)

/**
 * Hook to get label visibility state.
 * Re-renders only when showLabels changes.
 */
export const useShowLabels = () => useGraphStore((state) => state.showLabels)

/**
 * Hook to get legend visibility state.
 * Re-renders only when showLegend changes.
 */
export const useShowLegend = () => useGraphStore((state) => state.showLegend)

// ===========================
// Utility Hooks (Computed)
// ===========================

/**
 * Hook to check if any filters are active.
 * Re-renders only when filters change.
 */
export const useHasActiveFilters = () =>
  useGraphStore((state) => {
    const { filters } = state
    return (
      filters.entityTypes.length > 0 ||
      filters.relationshipTypes.length > 0 ||
      filters.minConfidence !== 0.5 ||
      filters.minConnectionCount !== undefined ||
      filters.dateRange !== undefined ||
      (filters.searchQuery !== undefined && filters.searchQuery.trim() !== '')
    )
  })

/**
 * Hook to check if entity is selected.
 * Re-renders only when selectedEntity changes.
 */
export const useIsEntitySelected = (entityId: string) =>
  useGraphStore((state) => state.selectedEntity === entityId)

/**
 * Hook to check if entity is hovered.
 * Re-renders only when hoveredEntity changes.
 */
export const useIsEntityHovered = (entityId: string) =>
  useGraphStore((state) => state.hoveredEntity === entityId)

/**
 * EntitySearch Component
 *
 * Autocomplete search component for finding entities in the knowledge graph.
 * Features:
 * - Debounced search with React Query integration (300ms)
 * - Keyboard navigation (↑↓ to navigate, Enter to select, Esc to close)
 * - Recent searches from Zustand store (max 5)
 * - Loading states and error handling
 * - Click outside to close dropdown
 * - Entity type badges with color coding
 * - Wikidata indicators
 *
 * @example
 * ```tsx
 * <EntitySearch
 *   onEntitySelect={(name) => console.log('Selected:', name)}
 *   placeholder="Search entities..."
 * />
 * ```
 */

import { useState, useRef, useEffect, memo, useCallback, type KeyboardEvent } from 'react'
import { Search, TrendingUp, Loader2, AlertCircle, Database } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/badge'
import { useEntitySearch } from '../../hooks/useEntitySearch'
import { useGraphStore } from '../../store/graphStore'
import { ENTITY_TYPE_COLORS } from '../../utils/colorScheme'
import { cn } from '@/lib/utils'
import type { EntitySearchResult } from '@/types/knowledgeGraphPublic'

// ===========================
// Props Interface
// ===========================

export interface EntitySearchProps {
  /** Callback when entity is selected */
  onEntitySelect: (entityName: string) => void
  /** Search input placeholder text */
  placeholder?: string
  /** Additional CSS classes */
  className?: string
}

// ===========================
// Constants
// ===========================

const MAX_RESULTS = 10 // Maximum search results to display
const MAX_RECENT_SEARCHES = 5 // Maximum recent searches to show

// ===========================
// Component
// ===========================

export const EntitySearch = memo(function EntitySearch({
  onEntitySelect,
  placeholder = 'Search entities...',
  className,
}: EntitySearchProps) {
  // ===== Local State =====
  const [inputValue, setInputValue] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isOpen, setIsOpen] = useState(false)

  // ===== Refs =====
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // ===== Store State =====
  const recentSearches = useGraphStore((state) => state.recentSearches)
  const addRecentSearch = useGraphStore((state) => state.addRecentSearch)

  // ===== React Query Hook (with built-in debouncing) =====
  const { data: searchData, isLoading, isError, error } = useEntitySearch(inputValue, {
    limit: MAX_RESULTS,
  })

  // ===== Computed Values =====
  const results = searchData?.results ?? []
  const showRecent = inputValue.trim().length === 0 && recentSearches.length > 0
  const displayItems = showRecent ? recentSearches.slice(0, MAX_RECENT_SEARCHES) : results
  const hasResults = displayItems.length > 0

  // ===== Close Dropdown =====
  const closeDropdown = useCallback(() => {
    setIsOpen(false)
    setSelectedIndex(-1)
  }, [])

  // ===== Handle Entity Selection =====
  const selectEntity = useCallback(
    (entityName: string) => {
      // Update input
      setInputValue(entityName)

      // Close dropdown
      closeDropdown()

      // Add to recent searches
      addRecentSearch(entityName)

      // Call parent callback
      onEntitySelect(entityName)

      // Blur input
      inputRef.current?.blur()
    },
    [closeDropdown, addRecentSearch, onEntitySelect]
  )

  // ===== Handle Result Click =====
  const handleResultClick = useCallback(
    (item: EntitySearchResult | string) => {
      const entityName = typeof item === 'string' ? item : item.name
      selectEntity(entityName)
    },
    [selectEntity]
  )

  // ===== Handle Input Change =====
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setInputValue(value)
    setSelectedIndex(-1)
    setIsOpen(true)
  }, [])

  // ===== Handle Input Focus =====
  const handleInputFocus = useCallback(() => {
    setIsOpen(true)
  }, [])

  // ===== Keyboard Navigation =====
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (!isOpen) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          setIsOpen(true)
          return
        }
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex((prev) => (prev < displayItems.length - 1 ? prev + 1 : 0))
          break

        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : displayItems.length - 1))
          break

        case 'Enter':
          e.preventDefault()
          if (selectedIndex >= 0 && displayItems[selectedIndex]) {
            const item = displayItems[selectedIndex]
            handleResultClick(item)
          }
          break

        case 'Escape':
          e.preventDefault()
          closeDropdown()
          inputRef.current?.blur()
          break
      }
    },
    [isOpen, displayItems, selectedIndex, handleResultClick, closeDropdown]
  )

  // ===== Click Outside Handler =====
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        closeDropdown()
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, closeDropdown])

  // ===== Scroll Selected Item Into View =====
  useEffect(() => {
    if (selectedIndex >= 0 && dropdownRef.current) {
      const selectedElement = dropdownRef.current.children[selectedIndex] as HTMLElement
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth',
        })
      }
    }
  }, [selectedIndex])

  // ===========================
  // Render Helpers
  // ===========================

  const renderEmptyState = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          <span className="text-sm">Searching...</span>
        </div>
      )
    }

    if (isError) {
      return (
        <div className="flex items-center justify-center py-8 text-destructive">
          <AlertCircle className="mr-2 h-4 w-4" />
          <span className="text-sm">
            {error instanceof Error ? error.message : 'Search failed'}
          </span>
        </div>
      )
    }

    if (inputValue.trim().length === 0) {
      return (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <Search className="mr-2 h-4 w-4" />
          <span className="text-sm">Start typing to search entities...</span>
        </div>
      )
    }

    if (inputValue.trim().length < 2) {
      return (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <span className="text-sm">Type at least 2 characters...</span>
        </div>
      )
    }

    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        <Database className="mr-2 h-4 w-4" />
        <span className="text-sm">No entities found</span>
      </div>
    )
  }

  const renderRecentSearchItem = (query: string, index: number) => {
    const isSelected = index === selectedIndex

    return (
      <button
        key={`recent-${query}`}
        className={cn(
          'flex w-full items-center gap-3 px-4 py-3 text-left transition-colors',
          'hover:bg-accent focus:outline-none',
          isSelected && 'bg-accent'
        )}
        onClick={() => handleResultClick(query)}
        onMouseEnter={() => setSelectedIndex(index)}
      >
        <TrendingUp className="h-4 w-4 text-muted-foreground" />
        <span className="flex-1 text-sm font-medium">{query}</span>
      </button>
    )
  }

  const renderSearchResultItem = (result: EntitySearchResult, index: number) => {
    const isSelected = index === selectedIndex
    const entityColor = ENTITY_TYPE_COLORS[result.type] ?? ENTITY_TYPE_COLORS.DEFAULT

    return (
      <button
        key={`result-${result.name}-${result.type}`}
        className={cn(
          'flex w-full items-center gap-3 px-4 py-3 text-left transition-colors',
          'hover:bg-accent focus:outline-none',
          isSelected && 'bg-accent'
        )}
        onClick={() => handleResultClick(result)}
        onMouseEnter={() => setSelectedIndex(index)}
      >
        {/* Entity Icon */}
        <div
          className="h-8 w-8 flex-shrink-0 rounded-full flex items-center justify-center text-white text-xs font-bold"
          style={{ backgroundColor: entityColor }}
        >
          {result.name.charAt(0).toUpperCase()}
        </div>

        {/* Entity Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm truncate">{result.name}</span>
            {result.wikidata_id && (
              <span className="text-xs text-blue-600" title="Has Wikidata ID">
                🔗
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 mt-1">
            <Badge
              variant="secondary"
              className="text-xs"
              style={{
                backgroundColor: `${entityColor}20`,
                color: entityColor,
                borderColor: entityColor,
              }}
            >
              {result.type}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {result.connection_count}{' '}
              {result.connection_count === 1 ? 'connection' : 'connections'}
            </span>
          </div>
        </div>
      </button>
    )
  }

  // ===========================
  // Render
  // ===========================

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="pl-10 pr-10"
          autoComplete="off"
          spellCheck={false}
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className={cn(
            'absolute z-50 mt-2 w-full',
            'rounded-lg border bg-popover shadow-lg',
            'max-h-[400px] overflow-y-auto',
            'animate-in fade-in-0 zoom-in-95'
          )}
        >
          {hasResults ? (
            <div className="py-2">
              {/* Recent Searches Header */}
              {showRecent && (
                <div className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  Recent Searches
                </div>
              )}

              {/* Search Results Header */}
              {!showRecent && results.length > 0 && (
                <div className="px-4 py-2 text-xs font-semibold text-muted-foreground">
                  Found {searchData?.total_results ?? 0} entities
                  {searchData?.query_time_ms && ` in ${searchData.query_time_ms}ms`}
                </div>
              )}

              {/* Items */}
              {displayItems.map((item, index) =>
                showRecent
                  ? renderRecentSearchItem(item as string, index)
                  : renderSearchResultItem(item as EntitySearchResult, index)
              )}
            </div>
          ) : (
            renderEmptyState()
          )}
        </div>
      )}
    </div>
  )
})

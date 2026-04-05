import { useState, useCallback, useEffect } from 'react'
import { useSearchParams as useRouterSearchParams } from 'react-router-dom'
import type { SearchParams, SearchFilters } from '../types/search.types'

/**
 * Hook to manage search state (query, filters, pagination)
 *
 * Architecture:
 * - React State for filters (instant updates, no timing issues)
 * - URL for query and pagination (shareable, history)
 * - One-way sync: State → URL for sharing (optional)
 *
 * Why not URL for filters?
 * React Router v7 navigate() is async - causes timing issues
 * where filters are written to URL but read before update completes.
 *
 * @returns Search state and update functions
 */
export const useSearchParams = () => {
  const [searchParams, setSearchParams] = useRouterSearchParams()

  // ===========================
  // State Management
  // ===========================

  // Query and pagination from URL (these work fine)
  const query = searchParams.get('q') || ''
  const page = parseInt(searchParams.get('page') || '1', 10)
  const pageSize = parseInt(searchParams.get('page_size') || '20', 10)

  // Filters in React State (instant, no timing issues)
  const [filters, setFilters] = useState<SearchFilters>({
    source: null,
    sentiment: null,
    date_from: null,
    date_to: null,
    entities: [],
  })

  // ===========================
  // Update Functions
  // ===========================

  /**
   * Update search query
   */
  const setQuery = useCallback(
    (newQuery: string) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        if (newQuery) {
          next.set('q', newQuery)
        } else {
          next.delete('q')
        }
        next.set('page', '1')
        return next
      })
    },
    [setSearchParams]
  )

  /**
   * Update filters (instant React State update)
   */
  const updateFilters = useCallback((newFilters: Partial<SearchFilters>) => {
    setFilters((prev) => ({
      ...prev,
      ...newFilters,
    }))
  }, [])

  /**
   * Update page number
   */
  const setPage = useCallback(
    (newPage: number) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.set('page', String(newPage))
        return next
      })
    },
    [setSearchParams]
  )

  /**
   * Update page size
   */
  const setPageSize = useCallback(
    (newPageSize: number) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.set('page_size', String(newPageSize))
        next.set('page', '1')
        return next
      })
    },
    [setSearchParams]
  )

  /**
   * Clear filters only
   */
  const clearFilters = useCallback(() => {
    setFilters({
      source: null,
      sentiment: null,
      date_from: null,
      date_to: null,
      entities: [],
    })
  }, [])

  /**
   * Clear everything
   */
  const clearAll = useCallback(() => {
    setSearchParams(new URLSearchParams())
    setFilters({
      source: null,
      sentiment: null,
      date_from: null,
      date_to: null,
      entities: [],
    })
  }, [setSearchParams])

  /**
   * Get complete search params for API call
   */
  const getSearchParams = useCallback((): SearchParams => {
    return {
      query,
      page,
      page_size: pageSize,
      source: filters.source,
      sentiment: filters.sentiment,
      date_from: filters.date_from,
      date_to: filters.date_to,
    }
  }, [query, page, pageSize, filters])

  // ===========================
  // Optional: Sync filters to URL for sharing
  // ===========================
  // Disabled by default - enable if you want shareable filter URLs
  // useEffect(() => {
  //   setSearchParams((prev) => {
  //     const next = new URLSearchParams(prev)
  //
  //     // Sync filters to URL
  //     if (filters.source) {
  //       next.set('source', filters.source)
  //     } else {
  //       next.delete('source')
  //     }
  //
  //     if (filters.sentiment) {
  //       next.set('sentiment', filters.sentiment)
  //     } else {
  //       next.delete('sentiment')
  //     }
  //
  //     return next
  //   }, { replace: true }) // Use replace to avoid cluttering history
  // }, [filters, setSearchParams])

  return {
    // State
    query,
    filters,
    page,
    pageSize,

    // Actions
    setQuery,
    setFilters: updateFilters,
    setPage,
    setPageSize,
    clearFilters,
    clearAll,
    getSearchParams,
  }
}

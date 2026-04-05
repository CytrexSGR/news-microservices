/**
 * React Query hooks for Saved Searches CRUD operations
 *
 * Provides hooks for:
 * - Listing saved searches
 * - Creating saved searches
 * - Updating saved searches
 * - Deleting saved searches
 * - Running saved searches
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchApi } from '@/api/axios'
import type {
  SavedSearch,
  SavedSearchCreate,
  SavedSearchUpdate,
  SavedSearchListResponse,
  RunSavedSearchResponse,
} from '../types/savedSearch'

// ===========================
// Query Keys
// ===========================

export const savedSearchKeys = {
  all: ['saved-searches'] as const,
  list: () => [...savedSearchKeys.all, 'list'] as const,
  detail: (id: number) => [...savedSearchKeys.all, 'detail', id] as const,
  run: (id: number) => [...savedSearchKeys.all, 'run', id] as const,
}

// ===========================
// API Functions
// ===========================

/**
 * Fetch all saved searches for current user
 */
const fetchSavedSearches = async (): Promise<SavedSearchListResponse> => {
  const { data } = await searchApi.get<SavedSearchListResponse>('/search/saved')
  return data
}

/**
 * Create a new saved search
 */
const createSavedSearch = async (
  params: SavedSearchCreate
): Promise<SavedSearch> => {
  const { data } = await searchApi.post<SavedSearch>('/search/saved', params)
  return data
}

/**
 * Update an existing saved search
 */
const updateSavedSearch = async ({
  id,
  ...params
}: SavedSearchUpdate & { id: number }): Promise<SavedSearch> => {
  const { data } = await searchApi.put<SavedSearch>(
    `/search/saved/${id}`,
    params
  )
  return data
}

/**
 * Delete a saved search
 */
const deleteSavedSearch = async (id: number): Promise<void> => {
  await searchApi.delete(`/search/saved/${id}`)
}

/**
 * Run a saved search and get results
 */
const runSavedSearch = async ({
  id,
  page = 1,
  page_size = 20,
}: {
  id: number
  page?: number
  page_size?: number
}): Promise<RunSavedSearchResponse> => {
  const { data } = await searchApi.post<RunSavedSearchResponse>(
    `/search/saved/${id}/run`,
    null,
    { params: { page, page_size } }
  )
  return data
}

// ===========================
// React Query Hooks
// ===========================

/**
 * Hook to fetch all saved searches
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useSavedSearches()
 *
 * if (isLoading) return <Loading />
 * if (error) return <Error message={error.message} />
 *
 * return (
 *   <ul>
 *     {data.items.map(search => (
 *       <li key={search.id}>{search.name}</li>
 *     ))}
 *   </ul>
 * )
 * ```
 */
export const useSavedSearches = () => {
  return useQuery({
    queryKey: savedSearchKeys.list(),
    queryFn: fetchSavedSearches,
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to create a new saved search
 *
 * @example
 * ```tsx
 * const { mutate: createSearch, isPending } = useCreateSavedSearch()
 *
 * const handleSave = () => {
 *   createSearch({
 *     name: 'AI News',
 *     query: 'artificial intelligence',
 *     filters: { sentiment: ['positive'] }
 *   }, {
 *     onSuccess: (saved) => {
 *       toast.success(`Saved search "${saved.name}" created`)
 *     }
 *   })
 * }
 * ```
 */
export const useCreateSavedSearch = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createSavedSearch,
    onSuccess: () => {
      // Invalidate the list to refetch
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() })
    },
  })
}

/**
 * Hook to update an existing saved search
 *
 * @example
 * ```tsx
 * const { mutate: updateSearch, isPending } = useUpdateSavedSearch()
 *
 * const handleUpdate = () => {
 *   updateSearch({
 *     id: savedSearch.id,
 *     name: 'Updated Name',
 *   }, {
 *     onSuccess: () => toast.success('Search updated')
 *   })
 * }
 * ```
 */
export const useUpdateSavedSearch = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateSavedSearch,
    onSuccess: (data) => {
      // Invalidate list and update specific item
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() })
      queryClient.setQueryData(savedSearchKeys.detail(data.id), data)
    },
  })
}

/**
 * Hook to delete a saved search
 *
 * @example
 * ```tsx
 * const { mutate: deleteSearch, isPending } = useDeleteSavedSearch()
 *
 * const handleDelete = () => {
 *   deleteSearch(savedSearch.id, {
 *     onSuccess: () => toast.success('Search deleted')
 *   })
 * }
 * ```
 */
export const useDeleteSavedSearch = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteSavedSearch,
    onSuccess: () => {
      // Invalidate the list
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() })
    },
  })
}

/**
 * Hook to run a saved search
 *
 * @example
 * ```tsx
 * const { mutate: runSearch, data: results, isPending } = useRunSavedSearch()
 *
 * const handleRun = () => {
 *   runSearch({
 *     id: savedSearch.id,
 *     page: 1,
 *     page_size: 20
 *   })
 * }
 * ```
 */
export const useRunSavedSearch = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: runSavedSearch,
    onSuccess: (data, variables) => {
      // Cache the run result
      queryClient.setQueryData(savedSearchKeys.run(variables.id), data)
      // Invalidate list to update last_run time
      queryClient.invalidateQueries({ queryKey: savedSearchKeys.list() })
    },
  })
}

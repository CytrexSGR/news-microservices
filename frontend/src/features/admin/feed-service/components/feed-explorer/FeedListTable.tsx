import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { RefreshCw, FileSearch, AlertCircle, Plus, Eye, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import type { FeedResponse, FeedStatus } from '@/types/feedServiceAdmin'
import { useTriggerFetch, useTriggerAssessment, useResetError } from '@/features/admin/feed-service/hooks'
import { AdmiraltyCodeBadge } from '@/components/shared/AdmiraltyCodeBadge'

type SortField = 'name' | 'status' | 'health' | 'rating' | 'quality' | 'items' | 'lastFetch' | 'error'
type SortDirection = 'asc' | 'desc' | null

interface FeedListTableProps {
  feeds: FeedResponse[]
  onFilterChange?: (filters: {
    status?: FeedStatus
    category?: string
    healthMin?: number
    healthMax?: number
  }) => void
}

/**
 * FeedListTable Component
 *
 * Displays a sortable, filterable table of RSS feeds with health metrics and actions.
 *
 * ## Sorting Feature (Added: 2025-12-01)
 * - Click any column header to sort by that field
 * - 3-state cycle: ascending → descending → unsorted (null)
 * - Visual indicators: ArrowUpDown (unsorted), ArrowUp (asc), ArrowDown (desc)
 *
 * ### Sortable Columns:
 * - **name**: Alphabetical sort by feed name
 * - **status**: Sort by feed status (ACTIVE, PAUSED, ERROR, INACTIVE)
 * - **health**: Numeric sort by health score (0-100)
 * - **rating**: Sort by Admiralty Code (A1-F6, null treated as 'ZZ')
 * - **quality**: Numeric sort by quality score (null treated as -1)
 * - **items**: Numeric sort by total items count
 * - **lastFetch**: Chronological sort by last fetch timestamp (null treated as 0)
 * - **error**: Binary sort (ERROR status first, then others)
 *
 * ## Implementation Details:
 * - State managed via `sortField` (SortField | null) and `sortDirection` ('asc' | 'desc' | null)
 * - Sorting applied after filtering in the `.filter().sort()` chain
 * - Click same column cycles through states, click different column starts at 'asc'
 *
 * @example
 * <FeedListTable
 *   feeds={feedsData}
 *   onFilterChange={(filters) => console.log(filters)}
 * />
 */
export function FeedListTable({ feeds }: FeedListTableProps) {
  const navigate = useNavigate()
  const [, setSearchParams] = useSearchParams()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<FeedStatus | ''>('')
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)
  const healthRange: [number, number] = [0, 100]

  const triggerFetch = useTriggerFetch()
  const triggerAssessment = useTriggerAssessment()
  const resetError = useResetError()

  // Handle column header click for sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortField(null)
        setSortDirection(null)
      }
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Get sort icon for column header
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3 w-3 ml-1 opacity-50" />
    }
    if (sortDirection === 'asc') {
      return <ArrowUp className="h-3 w-3 ml-1" />
    }
    return <ArrowDown className="h-3 w-3 ml-1" />
  }

  const getStatusBadgeVariant = (status: FeedStatus) => {
    switch (status) {
      case 'ACTIVE':
        return 'default'
      case 'PAUSED':
        return 'secondary'
      case 'ERROR':
        return 'destructive'
      case 'INACTIVE':
        return 'outline'
      default:
        return 'outline'
    }
  }

  const getHealthBadgeVariant = (score: number) => {
    if (score >= 80) return 'default'
    if (score >= 50) return 'secondary'
    return 'destructive'
  }

  const filteredFeeds = feeds
    .filter((feed) => {
      const matchesSearch =
        feed.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        feed.url.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesStatus = !statusFilter || feed.status === statusFilter
      const matchesHealth =
        feed.health_score >= healthRange[0] && feed.health_score <= healthRange[1]

      return matchesSearch && matchesStatus && matchesHealth
    })
    .sort((a, b) => {
      if (!sortField || !sortDirection) return 0

      let comparison = 0

      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'status':
          comparison = a.status.localeCompare(b.status)
          break
        case 'health':
          comparison = a.health_score - b.health_score
          break
        case 'rating':
          // Admiralty code format: "A1" -> compare as string
          const ratingA = a.admiralty_code || 'ZZ'
          const ratingB = b.admiralty_code || 'ZZ'
          comparison = ratingA.localeCompare(ratingB)
          break
        case 'quality':
          const qualityA = a.quality_score ?? -1
          const qualityB = b.quality_score ?? -1
          comparison = qualityA - qualityB
          break
        case 'items':
          comparison = a.total_items - b.total_items
          break
        case 'lastFetch':
          const dateA = a.last_fetched_at ? new Date(a.last_fetched_at).getTime() : 0
          const dateB = b.last_fetched_at ? new Date(b.last_fetched_at).getTime() : 0
          comparison = dateA - dateB
          break
        case 'error':
          const hasErrorA = a.status === 'ERROR' ? 1 : 0
          const hasErrorB = b.status === 'ERROR' ? 1 : 0
          comparison = hasErrorA - hasErrorB
          break
      }

      return sortDirection === 'asc' ? comparison : -comparison
    })

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Feed List</h3>
        <div className="flex items-center gap-3">
          <Badge variant="outline">{filteredFeeds.length} feeds</Badge>
          <Button onClick={() => setSearchParams({ tab: 'sources' })}>
            <Plus className="h-4 w-4 mr-2" />
            Create Feed (via Sources)
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <div className="flex-1">
          <Input
            placeholder="Search by name or URL..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as FeedStatus | '')}
          className="px-3 py-2 border rounded-md"
        >
          <option value="">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="PAUSED">Paused</option>
          <option value="ERROR">Error</option>
          <option value="INACTIVE">Inactive</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-md border overflow-x-auto">
        <table className="w-full">
          <thead className="border-b bg-muted/50">
            <tr className="text-sm">
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center">
                  Feed Name
                  {getSortIcon('name')}
                </div>
              </th>
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center">
                  Status
                  {getSortIcon('status')}
                </div>
              </th>
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('health')}
              >
                <div className="flex items-center">
                  Health
                  {getSortIcon('health')}
                </div>
              </th>
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('rating')}
              >
                <div className="flex items-center">
                  Rating
                  {getSortIcon('rating')}
                </div>
              </th>
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('quality')}
              >
                <div className="flex items-center">
                  Quality
                  {getSortIcon('quality')}
                </div>
              </th>
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('items')}
              >
                <div className="flex items-center">
                  Items (24h/Total)
                  {getSortIcon('items')}
                </div>
              </th>
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('lastFetch')}
              >
                <div className="flex items-center">
                  Last Fetch
                  {getSortIcon('lastFetch')}
                </div>
              </th>
              <th
                className="text-left p-3 font-medium cursor-pointer hover:bg-muted select-none"
                onClick={() => handleSort('error')}
              >
                <div className="flex items-center">
                  Error
                  {getSortIcon('error')}
                </div>
              </th>
              <th className="text-right p-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredFeeds.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-8 text-muted-foreground">
                  No feeds found
                </td>
              </tr>
            ) : (
              filteredFeeds.map((feed) => (
                <tr key={feed.id} className="border-b hover:bg-muted/50">
                  <td className="p-3">
                    <div>
                      <div className="font-medium">{feed.name}</div>
                      <div className="text-xs text-muted-foreground truncate max-w-xs">
                        {feed.url}
                      </div>
                    </div>
                  </td>
                  <td className="p-3">
                    <Badge variant={getStatusBadgeVariant(feed.status)}>
                      {feed.status}
                    </Badge>
                  </td>
                  <td className="p-3">
                    <Badge variant={getHealthBadgeVariant(feed.health_score)}>
                      {feed.health_score}
                    </Badge>
                  </td>
                  <td className="p-3">
                    <AdmiraltyCodeBadge
                      admiraltyCode={feed.admiralty_code ?? null}
                      showLabel={false}
                    />
                  </td>
                  <td className="p-3">
                    {feed.quality_score !== undefined && feed.quality_score !== null ? (
                      <Badge variant="outline">{feed.quality_score}</Badge>
                    ) : (
                      <span className="text-muted-foreground text-sm">N/A</span>
                    )}
                  </td>
                  <td className="p-3">
                    <div className="text-sm">
                      <span className="font-medium">{feed.items_last_24h}</span>
                      <span className="text-muted-foreground"> / </span>
                      <span>{feed.total_items}</span>
                    </div>
                  </td>
                  <td className="p-3">
                    {feed.last_fetched_at ? (
                      <div className="text-sm">
                        {new Date(feed.last_fetched_at).toLocaleString()}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-sm">Never</span>
                    )}
                  </td>
                  <td className="p-3">
                    {feed.status === 'ERROR' && feed.last_error_message ? (
                      <div className="group relative">
                        <span className="text-sm text-destructive cursor-help">
                          Error
                        </span>
                        {/* Tooltip on hover */}
                        <div className="invisible group-hover:visible absolute z-10 bg-popover text-popover-foreground p-3 rounded-md border shadow-md w-72 -top-2 left-full ml-2">
                          <div className="text-xs font-medium mb-1">Error Details:</div>
                          <div className="text-xs mb-2 break-words">{feed.last_error_message}</div>
                          {feed.last_error_at && (
                            <div className="text-xs text-muted-foreground">
                              At: {new Date(feed.last_error_at).toLocaleString()}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-sm">-</span>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {feed.status === 'ERROR' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => resetError.mutate(feed.id)}
                          disabled={resetError.isPending}
                          title="Reset error status and retry"
                          className="text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                        >
                          <AlertCircle className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/feeds/${feed.id}`)}
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => triggerFetch.mutate(feed.id)}
                        disabled={triggerFetch.isPending}
                        title="Trigger fetch"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => triggerAssessment.mutate(feed.id)}
                        disabled={triggerAssessment.isPending}
                        title="Trigger assessment"
                      >
                        <FileSearch className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

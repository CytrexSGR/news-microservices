import { useState, useMemo } from 'react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/Button'
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  ChevronRight,
} from 'lucide-react'
import type { FeedQualityOverview } from '@/types/feedServiceAdmin'

interface QualityFeedListTableProps {
  feeds: FeedQualityOverview[]
  onFeedSelect: (feedId: string) => void
  selectedFeedId?: string | null
  isLoading?: boolean
}

type SortField =
  | 'feed_name'
  | 'quality_score'
  | 'admiralty_code'
  | 'total_articles'
  | 'articles_24h'
type SortDirection = 'asc' | 'desc'

const admiraltyColors = {
  green: 'bg-green-100 text-green-800 border-green-300',
  blue: 'bg-blue-100 text-blue-800 border-blue-300',
  yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  orange: 'bg-orange-100 text-orange-800 border-orange-300',
  red: 'bg-red-100 text-red-800 border-red-300',
  gray: 'bg-gray-100 text-gray-800 border-gray-300',
}

const confidenceColors = {
  high: 'bg-green-50 text-green-700',
  medium: 'bg-yellow-50 text-yellow-700',
  low: 'bg-orange-50 text-orange-700',
}

const TrendIcon = ({ trend }: { trend: string | null }) => {
  if (trend === 'improving') return <TrendingUp className="h-3.5 w-3.5 text-green-600" />
  if (trend === 'declining') return <TrendingDown className="h-3.5 w-3.5 text-red-600" />
  return <Minus className="h-3.5 w-3.5 text-gray-600" />
}

export function QualityFeedListTable({
  feeds,
  onFeedSelect,
  selectedFeedId,
  isLoading = false,
}: QualityFeedListTableProps) {
  const [sortField, setSortField] = useState<SortField>('feed_name')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const handleFeedSelect = (feedId: string) => {
    console.log('🔵 Feed selected:', feedId)
    onFeedSelect(feedId)
  }

  // Sort feeds
  const sortedFeeds = useMemo(() => {
    const sorted = [...feeds].sort((a, b) => {
      const aValue: any = a[sortField]
      const bValue: any = b[sortField]

      // Handle null values (sort nulls to end)
      if (aValue === null && bValue === null) return 0
      if (aValue === null) return 1
      if (bValue === null) return -1

      // String comparison
      if (typeof aValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }

      // Number comparison
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
    })

    return sorted
  }, [feeds, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      // New field, default to ascending
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => {
    const isActive = sortField === field
    const Icon = isActive
      ? sortDirection === 'asc'
        ? ArrowUp
        : ArrowDown
      : ArrowUpDown

    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleSort(field)}
        className={`h-8 px-2 ${isActive ? 'bg-muted' : ''}`}
      >
        {children}
        <Icon className="ml-1.5 h-3.5 w-3.5" />
      </Button>
    )
  }

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="text-center py-12 text-muted-foreground">
          <div className="text-sm">Loading feed quality data...</div>
        </div>
      </Card>
    )
  }

  if (feeds.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center py-12 text-muted-foreground">
          <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <div className="text-sm font-medium">No feeds found</div>
          <div className="text-xs mt-1">Add feeds to see quality metrics</div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">All Feeds - Quality Overview</h3>
        <p className="text-sm text-muted-foreground mt-0.5">
          {feeds.length} feed{feeds.length !== 1 ? 's' : ''} • {sortedFeeds.filter((f) => f.quality_score !== null).length} with quality data
        </p>
        <div className="mt-2 flex items-center gap-2 text-xs text-blue-600">
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="font-medium">Click any row to view detailed analysis</span>
        </div>
      </div>

      <div className="overflow-x-auto max-h-[500px] overflow-y-auto border rounded-lg">
        <table className="w-full text-sm">
          <thead className="border-b">
            <tr>
              <th className="text-left py-3 px-2">
                <SortButton field="feed_name">Feed Name</SortButton>
              </th>
              <th className="text-center py-3 px-2">
                <SortButton field="quality_score">Quality Score</SortButton>
              </th>
              <th className="text-center py-3 px-2">
                <SortButton field="admiralty_code">Admiralty Code</SortButton>
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="total_articles">Total Articles</SortButton>
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="articles_24h">Last 24h</SortButton>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedFeeds.map((feed) => {
              const isSelected = selectedFeedId === feed.feed_id
              const hasQualityData = feed.quality_score !== null
              const admiraltyColorClass =
                admiraltyColors[feed.admiralty_color as keyof typeof admiraltyColors] ||
                admiraltyColors.gray
              const _confidenceColorClass =
                confidenceColors[feed.confidence as keyof typeof confidenceColors] || ''

              return (
                <tr
                  key={feed.feed_id}
                  onClick={() => handleFeedSelect(feed.feed_id)}
                  className={`
                    border-b cursor-pointer transition-all
                    hover:bg-muted/30
                    ${isSelected ? 'bg-blue-50/50 border-l-4 border-l-blue-600' : ''}
                  `}
                >
                  {/* Feed Name */}
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-2">
                      <ChevronRight className={`h-4 w-4 transition-transform ${isSelected ? 'rotate-90 text-blue-600' : 'text-muted-foreground'}`} />
                      <div>
                        <div className="font-medium">{feed.feed_name}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {feed.coverage_percentage.toFixed(0)}% analyzed •
                          {feed.confidence ? ` ${feed.confidence} confidence` : ' no data'}
                          {feed.trend && feed.trend !== 'stable' && (
                            <span className="ml-1">
                              {feed.trend === 'improving' ? '📈' : '📉'}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Quality Score */}
                  <td className="py-3 px-2 text-center">
                    {hasQualityData ? (
                      <div className="font-semibold text-lg">
                        {feed.quality_score!.toFixed(1)}
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground">N/A</div>
                    )}
                  </td>

                  {/* Admiralty Code */}
                  <td className="py-3 px-2 text-center">
                    {feed.admiralty_code ? (
                      <Badge className={`text-xs border ${admiraltyColorClass}`}>
                        {feed.admiralty_code} • {feed.admiralty_label}
                      </Badge>
                    ) : (
                      <div className="text-xs text-muted-foreground">N/A</div>
                    )}
                  </td>

                  {/* Total Articles */}
                  <td className="py-3 px-2 text-right font-medium">
                    {feed.total_articles.toLocaleString()}
                  </td>

                  {/* Articles 24h */}
                  <td className="py-3 px-2 text-right">
                    <span className="font-medium">{feed.articles_24h}</span>
                    {feed.articles_24h > 0 && (
                      <span className="text-xs text-green-600 ml-1">+</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

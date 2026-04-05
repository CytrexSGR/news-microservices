import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, Play } from 'lucide-react'
import { useBulkFetch } from '@/features/admin/feed-service/hooks/useBulkFetch'
import type { FeedResponse } from '@/types/feedServiceAdmin'

interface BulkFetchControlProps {
  feeds: FeedResponse[]
}

export function BulkFetchControl({ feeds }: BulkFetchControlProps) {
  const [forceRefresh, setForceRefresh] = useState(false)
  const bulkFetch = useBulkFetch()

  const activeFeeds = feeds.filter((f) => f.is_active)

  const handleBulkFetch = () => {
    bulkFetch.mutate({
      feed_ids: undefined, // Fetch all active feeds
      force: forceRefresh,
    })
  }

  const handleFetchSelected = (feedIds: string[]) => {
    bulkFetch.mutate({
      feed_ids: feedIds,
      force: forceRefresh,
    })
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <RefreshCw className="h-5 w-5" />
        Bulk Fetch Control
      </h3>

      <div className="space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 rounded-lg border text-center">
            <div className="text-sm text-muted-foreground mb-1">Total Feeds</div>
            <div className="text-2xl font-bold">{feeds.length}</div>
          </div>
          <div className="p-3 rounded-lg border text-center bg-primary/5">
            <div className="text-sm text-muted-foreground mb-1">Active Feeds</div>
            <div className="text-2xl font-bold">{activeFeeds.length}</div>
          </div>
          <div className="p-3 rounded-lg border text-center">
            <div className="text-sm text-muted-foreground mb-1">Inactive Feeds</div>
            <div className="text-2xl font-bold">{feeds.length - activeFeeds.length}</div>
          </div>
        </div>

        {/* Force Refresh Option */}
        <div className="flex items-center gap-2 p-3 rounded-lg border">
          <input
            type="checkbox"
            id="force-refresh"
            checked={forceRefresh}
            onChange={(e) => setForceRefresh(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300"
          />
          <label htmlFor="force-refresh" className="text-sm font-medium cursor-pointer flex-1">
            Force Refresh
            <span className="block text-xs text-muted-foreground">
              Fetch even if recently updated (ignores fetch_interval)
            </span>
          </label>
        </div>

        {/* Actions */}
        <div className="space-y-2">
          <Button
            onClick={handleBulkFetch}
            disabled={bulkFetch.isPending || activeFeeds.length === 0}
            className="w-full"
          >
            {bulkFetch.isPending ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Fetching...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Fetch All Active Feeds ({activeFeeds.length})
              </>
            )}
          </Button>

          {/* Quick Actions by Status */}
          <div className="grid grid-cols-2 gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleFetchSelected(
                  feeds.filter((f) => f.status === 'ERROR').map((f) => f.id)
                )
              }
              disabled={bulkFetch.isPending}
            >
              Retry Failed ({feeds.filter((f) => f.status === 'ERROR').length})
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleFetchSelected(
                  feeds.filter((f) => f.health_score < 50).map((f) => f.id)
                )
              }
              disabled={bulkFetch.isPending}
            >
              Low Health ({feeds.filter((f) => f.health_score < 50).length})
            </Button>
          </div>
        </div>

        {/* Last Result */}
        {bulkFetch.isSuccess && bulkFetch.data && (
          <div className="p-3 rounded-lg border bg-primary/5">
            <div className="text-sm font-medium mb-2">Last Bulk Fetch Result</div>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Total:</span>{' '}
                <span className="font-medium">{bulkFetch.data.total_feeds}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Success:</span>{' '}
                <Badge variant="default" className="ml-1">
                  {bulkFetch.data.successful_fetches}
                </Badge>
              </div>
              <div>
                <span className="text-muted-foreground">Failed:</span>{' '}
                <Badge variant="destructive" className="ml-1">
                  {bulkFetch.data.failed_fetches}
                </Badge>
              </div>
            </div>
            <div className="mt-2 text-sm">
              <span className="text-muted-foreground">New Items:</span>{' '}
              <span className="font-medium">{bulkFetch.data.total_new_items}</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

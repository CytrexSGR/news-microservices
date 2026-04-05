import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Folder, FileText } from 'lucide-react'
import type { FeedResponse } from '@/types/feedServiceAdmin'

interface CategoryManagementProps {
  feeds: FeedResponse[]
}

export function CategoryManagement({ feeds }: CategoryManagementProps) {
  // Calculate category stats
  const categoryStats = new Map<
    string,
    {
      feedCount: number
      totalItems: number
      items24h: number
    }
  >()

  feeds.forEach((feed) => {
    // Now each feed has a single category instead of an array
    if (feed.category) {
      const existing = categoryStats.get(feed.category) || {
        feedCount: 0,
        totalItems: 0,
        items24h: 0,
      }
      categoryStats.set(feed.category, {
        feedCount: existing.feedCount + 1,
        totalItems: existing.totalItems + feed.total_items,
        items24h: existing.items24h + feed.items_last_24h,
      })
    }
  })

  const categories = Array.from(categoryStats.entries())
    .map(([category, stats]) => ({ category, ...stats }))
    .sort((a, b) => b.feedCount - a.feedCount)

  const feedsWithoutCategory = feeds.filter(
    (f) => !f.categories || f.categories.length === 0
  ).length

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Folder className="h-5 w-5" />
        Category Management
      </h3>

      <div className="space-y-4">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg border text-center">
            <div className="text-sm text-muted-foreground mb-1">Total Categories</div>
            <div className="text-2xl font-bold">{categories.length}</div>
          </div>
          <div className="p-3 rounded-lg border text-center">
            <div className="text-sm text-muted-foreground mb-1">Uncategorized</div>
            <div className="text-2xl font-bold">{feedsWithoutCategory}</div>
          </div>
        </div>

        {/* Category List */}
        {categories.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Folder className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No categories found</p>
            <p className="text-sm mt-1">Add categories to feeds to organize them</p>
          </div>
        ) : (
          <div className="space-y-2">
            {categories.map(({ category, feedCount, totalItems, items24h }) => (
              <div
                key={category}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <Folder className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="font-medium truncate">{category}</div>
                    <div className="text-sm text-muted-foreground">
                      {feedCount} {feedCount === 1 ? 'feed' : 'feeds'}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" title="Total items">
                    <FileText className="h-3 w-3 mr-1" />
                    {totalItems.toLocaleString()}
                  </Badge>
                  <Badge variant="default" title="Items last 24h">
                    +{items24h}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Uncategorized Warning */}
        {feedsWithoutCategory > 0 && (
          <div className="p-3 rounded-lg border bg-yellow-50 dark:bg-yellow-950/20">
            <div className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              {feedsWithoutCategory} {feedsWithoutCategory === 1 ? 'feed has' : 'feeds have'} no
              category
            </div>
            <div className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
              Consider adding categories for better organization
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

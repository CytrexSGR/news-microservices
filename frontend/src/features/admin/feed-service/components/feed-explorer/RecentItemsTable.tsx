import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { FileText, ExternalLink, CheckCircle2, XCircle, Clock } from 'lucide-react'
import type { FeedItemWithFeedResponse, ScrapeStatus } from '@/types/feedServiceAdmin'

interface RecentItemsTableProps {
  items: FeedItemWithFeedResponse[]
}

export function RecentItemsTable({ items }: RecentItemsTableProps) {
  const getScrapeStatusBadge = (status?: ScrapeStatus) => {
    switch (status) {
      case 'success':
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Success
          </Badge>
        )
      case 'error':
      case 'timeout':
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            {status}
          </Badge>
        )
      case 'paywall':
        return (
          <Badge variant="secondary" className="gap-1">
            Paywall
          </Badge>
        )
      case 'pending':
        return (
          <Badge variant="outline" className="gap-1">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        )
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Recent Items
        </h3>
        <Badge variant="outline">{items.length} items</Badge>
      </div>

      <div className="rounded-md border overflow-x-auto">
        <table className="w-full">
          <thead className="border-b">
            <tr className="text-sm">
              <th className="text-left p-3 font-medium">Title</th>
              <th className="text-left p-3 font-medium">Feed</th>
              <th className="text-left p-3 font-medium">Scrape Status</th>
              <th className="text-left p-3 font-medium">Word Count</th>
              <th className="text-left p-3 font-medium">Scraped At</th>
              <th className="text-right p-3 font-medium">Link</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-muted-foreground">
                  No recent items found
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-b hover:bg-muted/50">
                  <td className="p-3">
                    <div className="max-w-md">
                      <div className="font-medium line-clamp-2">{item.title}</div>
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="text-sm text-muted-foreground">{item.feed_name}</div>
                  </td>
                  <td className="p-3">{getScrapeStatusBadge(item.scrape_status)}</td>
                  <td className="p-3">
                    {item.scrape_word_count ? (
                      <Badge variant="outline">{item.scrape_word_count}</Badge>
                    ) : (
                      <span className="text-muted-foreground text-sm">N/A</span>
                    )}
                  </td>
                  <td className="p-3">
                    {item.scraped_at ? (
                      <div className="text-sm">
                        {new Date(item.scraped_at).toLocaleString()}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-sm">N/A</span>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-primary hover:underline"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
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

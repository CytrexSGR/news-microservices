/**
 * SourceCard Component
 *
 * Displays a summary card for a single source.
 */

import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Globe, Rss, FileText, ExternalLink, MoreHorizontal } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu'
import { SourceCredibilityBadge } from './SourceCredibilityBadge'
import { SourceStatusBadge, ScrapeStatusBadge } from './SourceStatusBadge'
import type { Source } from '@/types/source'
import { formatDistanceToNow } from 'date-fns'

interface SourceCardProps {
  source: Source
  onSelect?: (source: Source) => void
  onEdit?: (source: Source) => void
  onAssess?: (source: Source) => void
  onManageFeeds?: (source: Source) => void
}

export function SourceCard({
  source,
  onSelect,
  onEdit,
  onAssess,
  onManageFeeds,
}: SourceCardProps) {
  const lastFetched = source.scrape_last_success
    ? formatDistanceToNow(new Date(source.scrape_last_success), { addSuffix: true })
    : 'Never'

  return (
    <Card
      className="hover:border-primary/50 transition-colors cursor-pointer"
      onClick={() => onSelect?.(source)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {source.logo_url ? (
              <img
                src={source.logo_url}
                alt={source.canonical_name}
                className="w-8 h-8 rounded object-contain"
              />
            ) : (
              <Globe className="w-8 h-8 text-muted-foreground" />
            )}
            <div>
              <h3 className="font-semibold text-base leading-tight">
                {source.canonical_name}
              </h3>
              <p className="text-sm text-muted-foreground">{source.domain}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <SourceCredibilityBadge
              tier={source.credibility_tier}
              score={source.reputation_score}
            />
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit?.(source)}>
                  Edit Source
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onManageFeeds?.(source)}>
                  Manage Feeds
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onAssess?.(source)}>
                  Request Assessment
                </DropdownMenuItem>
                {source.homepage_url && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <a
                        href={source.homepage_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Visit Website
                      </a>
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
          {source.organization_name && (
            <span className="truncate">{source.organization_name}</span>
          )}
          {source.country && (
            <span className="uppercase font-mono text-xs">{source.country}</span>
          )}
          {source.category && <span>{source.category}</span>}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <Rss className="h-4 w-4 text-muted-foreground" />
              <span>{source.active_feeds_count ?? source.feeds_count ?? 0} feeds</span>
            </div>
            <div className="flex items-center gap-1">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span>{source.articles_count?.toLocaleString() ?? 0} articles</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ScrapeStatusBadge status={source.scrape_status} />
            <span className="text-xs text-muted-foreground">{lastFetched}</span>
          </div>
        </div>

        {source.assessment_summary && (
          <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
            {source.assessment_summary}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

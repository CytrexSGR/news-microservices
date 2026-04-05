/**
 * Article Card Component
 *
 * Displays a single search result with:
 * - Title with highlighting
 * - Content preview (truncated)
 * - Metadata (source, date, sentiment)
 * - Relevance score
 * - Click navigation
 * - Responsive design
 */

import * as React from 'react'
import { Calendar, ExternalLink, TrendingUp, User } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { SearchResultItem } from '../../types/search.types'

interface ArticleCardProps {
  /** Article data from search results */
  article: SearchResultItem
  /** Optional: Click handler */
  onClick?: (article: SearchResultItem) => void
  /** Optional: Custom class name */
  className?: string
  /** Optional: Show full content instead of preview */
  showFullContent?: boolean
}

/**
 * Get sentiment badge variant based on sentiment value
 */
function getSentimentVariant(
  sentiment: string
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (sentiment.toLowerCase()) {
    case 'positive':
      return 'default' // Green
    case 'negative':
      return 'destructive' // Red
    case 'neutral':
      return 'secondary' // Gray
    default:
      return 'outline'
  }
}

/**
 * Get sentiment display color
 * @deprecated - Use getSentimentVariant instead
 */
// function getSentimentColor(sentiment: string): string {
//   switch (sentiment.toLowerCase()) {
//     case 'positive':
//       return 'text-green-600 dark:text-green-400'
//     case 'negative':
//       return 'text-red-600 dark:text-red-400'
//     case 'neutral':
//       return 'text-gray-600 dark:text-gray-400'
//     default:
//       return 'text-muted-foreground'
//   }
// }

/**
 * Highlight search terms in text
 */
function HighlightedText({
  text,
  highlights,
}: {
  text: string
  highlights?: string[]
}) {
  if (!highlights || highlights.length === 0) {
    return <>{text}</>
  }

  // Simple highlighting - replace matched terms with marked version
  let highlightedText = text
  highlights.forEach((highlight) => {
    // Remove HTML tags from highlight
    const cleanHighlight = highlight.replace(/<\/?em>/g, '')
    const regex = new RegExp(`(${cleanHighlight})`, 'gi')
    highlightedText = highlightedText.replace(
      regex,
      '<mark class="bg-yellow-200 dark:bg-yellow-800 px-0.5 rounded">$1</mark>'
    )
  })

  return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />
}

/**
 * Format date for display
 */
function formatArticleDate(dateString: string | null | undefined): string {
  if (!dateString) return 'Unknown date'

  try {
    const date = parseISO(dateString)
    return format(date, 'MMM d, yyyy')
  } catch {
    return dateString
  }
}

/**
 * Truncate content to specified length
 */
function truncateContent(content: string, maxLength: number = 200): string {
  if (content.length <= maxLength) return content

  const truncated = content.substring(0, maxLength)
  const lastSpace = truncated.lastIndexOf(' ')

  return lastSpace > 0
    ? truncated.substring(0, lastSpace) + '...'
    : truncated + '...'
}

export function ArticleCard({
  article,
  onClick,
  className,
  showFullContent = false,
}: ArticleCardProps) {
  const handleClick = () => {
    if (onClick) {
      onClick(article)
    } else if (article.url) {
      window.open(article.url, '_blank', 'noopener,noreferrer')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }

  // Extract highlights
  const titleHighlights = article.highlight?.title || []
  const contentHighlights = article.highlight?.content || []

  return (
    <Card
      className={cn(
        'group cursor-pointer transition-all hover:shadow-lg hover:border-primary/50',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        className
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="article"
      aria-label={`Article: ${article.title}`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-lg font-semibold leading-tight group-hover:text-primary transition-colors flex-1">
            <HighlightedText text={article.title} highlights={titleHighlights} />
          </h3>
          {article.url && (
            <ExternalLink className="h-4 w-4 text-muted-foreground shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
          )}
        </div>

        {/* Author (if available) */}
        {article.author && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            <User className="h-3 w-3" />
            <span>{article.author}</span>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Content Preview */}
        <p className="text-sm text-muted-foreground leading-relaxed">
          <HighlightedText
            text={
              showFullContent
                ? article.content
                : truncateContent(article.content, 200)
            }
            highlights={contentHighlights}
          />
        </p>

        {/* Entities (if available) */}
        {article.entities && article.entities.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {article.entities.slice(0, 5).map((entity, idx) => (
              <Badge key={idx} variant="outline" className="text-xs">
                {entity}
              </Badge>
            ))}
            {article.entities.length > 5 && (
              <Badge variant="outline" className="text-xs">
                +{article.entities.length - 5} more
              </Badge>
            )}
          </div>
        )}

        {/* Metadata Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {/* Date */}
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatArticleDate(article.published_at)}</span>
            </div>

            {/* Source */}
            {article.source && (
              <div className="flex items-center gap-1">
                <span className="font-medium">{article.source}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Sentiment Badge */}
            {article.sentiment && (
              <Badge
                variant={getSentimentVariant(article.sentiment)}
                className="text-xs"
              >
                {article.sentiment}
              </Badge>
            )}

            {/* Relevance Score */}
            <div
              className="flex items-center gap-1 text-xs text-muted-foreground"
              title={`Relevance score: ${article.relevance_score.toFixed(3)}`}
            >
              <TrendingUp className="h-3 w-3" />
              <span className="font-mono">
                {article.relevance_score.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Compact variant of ArticleCard for list views
 */
export function ArticleCardCompact({
  article,
  onClick,
  className,
}: Omit<ArticleCardProps, 'showFullContent'>) {
  const handleClick = () => {
    if (onClick) {
      onClick(article)
    } else if (article.url) {
      window.open(article.url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div
      className={cn(
        'group flex items-start gap-4 p-4 rounded-lg border border-border bg-card',
        'cursor-pointer transition-all hover:shadow-md hover:border-primary/50',
        className
      )}
      onClick={handleClick}
      role="article"
    >
      <div className="flex-1 min-w-0 space-y-1">
        <h4 className="font-medium leading-tight group-hover:text-primary transition-colors line-clamp-2">
          {article.title}
        </h4>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {truncateContent(article.content, 150)}
        </p>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>{formatArticleDate(article.published_at)}</span>
          {article.source && <span>•</span>}
          {article.source && <span>{article.source}</span>}
        </div>
      </div>

      <div className="flex flex-col items-end gap-2 shrink-0">
        {article.sentiment && (
          <Badge
            variant={getSentimentVariant(article.sentiment)}
            className="text-xs"
          >
            {article.sentiment}
          </Badge>
        )}
        <div className="text-xs text-muted-foreground font-mono">
          {article.relevance_score.toFixed(2)}
        </div>
      </div>
    </div>
  )
}

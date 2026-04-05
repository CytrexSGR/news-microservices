/**
 * SearchResultCard Component
 *
 * Displays a single search result with title, preview,
 * source, sentiment badge, and entity chips.
 */

import * as React from 'react';
import { format, parseISO } from 'date-fns';
import {
  ExternalLink,
  Calendar,
  User,
  Building2,
  MapPin,
  Tag,
  TrendingUp,
  TrendingDown,
  Minus,
  Globe,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { SearchResult, EntityType } from '../types/search.types';

interface SearchResultCardProps {
  /** Search result data */
  result: SearchResult;
  /** Called when clicking the result */
  onClick?: (result: SearchResult) => void;
  /** Show full content preview */
  expanded?: boolean;
  /** Highlight matched terms */
  highlightTerms?: string[];
  /** Additional CSS classes */
  className?: string;
}

// Entity type to icon mapping
const ENTITY_ICONS: Record<EntityType, React.ComponentType<{ className?: string }>> = {
  PERSON: User,
  ORGANIZATION: Building2,
  LOCATION: MapPin,
  GPE: Globe,
  EVENT: Calendar,
  PRODUCT: Tag,
  MONEY: TrendingUp,
  DATE: Calendar,
  PERCENT: TrendingUp,
};

// Entity type colors
const ENTITY_COLORS: Record<EntityType, string> = {
  PERSON: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  ORGANIZATION: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  LOCATION: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  GPE: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
  EVENT: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  PRODUCT: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  MONEY: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  DATE: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  PERCENT: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
};

/**
 * Sentiment badge component
 */
function SentimentBadge({
  score,
  label,
}: {
  score: number;
  label?: 'positive' | 'negative' | 'neutral';
}) {
  const sentiment = label || (score > 0.2 ? 'positive' : score < -0.2 ? 'negative' : 'neutral');

  const config = {
    positive: {
      icon: TrendingUp,
      className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      label: 'Positive',
    },
    negative: {
      icon: TrendingDown,
      className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      label: 'Negative',
    },
    neutral: {
      icon: Minus,
      className: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
      label: 'Neutral',
    },
  }[sentiment];

  const Icon = config.icon;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={cn('gap-1', config.className)}>
            <Icon className="h-3 w-3" />
            {config.label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          Score: {(score * 100).toFixed(0)}%
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Entity chip component
 */
function EntityChip({
  name,
  type,
}: {
  name: string;
  type: EntityType;
}) {
  const Icon = ENTITY_ICONS[type] || Tag;
  const colorClass = ENTITY_COLORS[type] || 'bg-gray-100 text-gray-800';

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
              colorClass
            )}
          >
            <Icon className="h-3 w-3" />
            <span className="max-w-24 truncate">{name}</span>
          </span>
        </TooltipTrigger>
        <TooltipContent>
          {type}: {name}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Relevance score indicator
 */
function RelevanceIndicator({ score }: { score: number }) {
  const percentage = Math.round(score * 100);
  const width = Math.min(100, Math.max(0, percentage));

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2">
            <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${width}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground tabular-nums">
              {percentage}%
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent>Relevance Score: {percentage}%</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Highlight matched terms in text
 */
function HighlightedText({
  text,
  terms,
  maxLength = 300,
}: {
  text: string;
  terms?: string[];
  maxLength?: number;
}) {
  if (!terms || terms.length === 0) {
    const truncated = text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
    return <span>{truncated}</span>;
  }

  // Create regex for all terms
  const pattern = new RegExp(`(${terms.map(escapeRegex).join('|')})`, 'gi');

  // Truncate first
  const truncated = text.length > maxLength ? text.slice(0, maxLength) + '...' : text;

  // Split by pattern
  const parts = truncated.split(pattern);

  return (
    <span>
      {parts.map((part, i) => {
        const isMatch = terms.some(
          (term) => part.toLowerCase() === term.toLowerCase()
        );
        return isMatch ? (
          <mark key={i} className="bg-yellow-200 dark:bg-yellow-800 px-0.5 rounded">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </span>
  );
}

function escapeRegex(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function SearchResultCard({
  result,
  onClick,
  expanded = false,
  highlightTerms,
  className,
}: SearchResultCardProps) {
  const publishedDate = result.published_at
    ? format(parseISO(result.published_at), 'MMM d, yyyy')
    : null;

  // Limit entities to show
  const visibleEntities = result.entities.slice(0, 5);
  const hiddenEntityCount = result.entities.length - visibleEntities.length;

  return (
    <Card
      className={cn(
        'group transition-all hover:shadow-md hover:border-primary/30',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={() => onClick?.(result)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          {/* Title and metadata */}
          <div className="space-y-1 flex-1 min-w-0">
            <h3 className="font-semibold leading-tight line-clamp-2 group-hover:text-primary transition-colors">
              {result.title}
            </h3>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              {/* Source */}
              <span className="font-medium">{result.source}</span>

              {/* Author */}
              {result.author && (
                <>
                  <span>-</span>
                  <span className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {result.author}
                  </span>
                </>
              )}

              {/* Date */}
              {publishedDate && (
                <>
                  <span>-</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {publishedDate}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            <SentimentBadge
              score={result.sentiment_score}
              label={result.sentiment_label}
            />
            {result.url && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                asChild
                onClick={(e) => e.stopPropagation()}
              >
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span className="sr-only">Open article</span>
                </a>
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Content preview */}
        <p className={cn(
          'text-sm text-muted-foreground',
          expanded ? '' : 'line-clamp-3'
        )}>
          <HighlightedText
            text={result.content_preview}
            terms={highlightTerms}
            maxLength={expanded ? 1000 : 200}
          />
        </p>

        {/* Entities */}
        {result.entities.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {visibleEntities.map((entity, index) => (
              <EntityChip
                key={`${entity.type}-${entity.name}-${index}`}
                name={entity.name}
                type={entity.type}
              />
            ))}
            {hiddenEntityCount > 0 && (
              <span className="text-xs text-muted-foreground">
                +{hiddenEntityCount} more
              </span>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t">
          <RelevanceIndicator score={result.relevance_score} />

          {/* Highlights from search */}
          {result.highlights && Object.keys(result.highlights).length > 0 && (
            <span className="text-xs text-muted-foreground">
              {Object.values(result.highlights).flat().length} matches
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Compact version of search result for list views
 */
export function SearchResultListItem({
  result,
  onClick,
  highlightTerms,
  className,
}: SearchResultCardProps) {
  const publishedDate = result.published_at
    ? format(parseISO(result.published_at), 'MMM d')
    : null;

  return (
    <div
      className={cn(
        'flex items-start gap-4 p-3 rounded-lg transition-colors',
        onClick && 'cursor-pointer hover:bg-muted/50',
        className
      )}
      onClick={() => onClick?.(result)}
    >
      {/* Relevance indicator */}
      <div className="shrink-0 pt-1">
        <div
          className="w-1.5 h-12 rounded-full bg-muted overflow-hidden"
          title={`Relevance: ${Math.round(result.relevance_score * 100)}%`}
        >
          <div
            className="w-full bg-primary transition-all"
            style={{ height: `${result.relevance_score * 100}%` }}
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1">
        <h4 className="font-medium leading-tight line-clamp-1">
          {result.title}
        </h4>
        <p className="text-sm text-muted-foreground line-clamp-2">
          <HighlightedText
            text={result.content_preview}
            terms={highlightTerms}
            maxLength={150}
          />
        </p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{result.source}</span>
          {publishedDate && (
            <>
              <span>-</span>
              <span>{publishedDate}</span>
            </>
          )}
          {result.entities.length > 0 && (
            <>
              <span>-</span>
              <span>{result.entities.length} entities</span>
            </>
          )}
        </div>
      </div>

      {/* Sentiment */}
      <div className="shrink-0">
        <SentimentBadge
          score={result.sentiment_score}
          label={result.sentiment_label}
        />
      </div>
    </div>
  );
}

/**
 * EventCard Component
 *
 * Displays a single intelligence event in card format
 */
import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { ChevronDown, ChevronUp, ExternalLink, Clock, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { RiskBadge } from './RiskBadge';
import type { IntelligenceEvent } from '../types/events.types';
import { getCategoryColor, getCategoryBgColor, formatTimeAgo } from '../types/events.types';

interface EventCardProps {
  event: IntelligenceEvent;
  onClick?: (event: IntelligenceEvent) => void;
  showCluster?: boolean;
  expandable?: boolean;
  className?: string;
}

export function EventCard({
  event,
  onClick,
  showCluster = true,
  expandable = true,
  className,
}: EventCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClick = () => {
    if (onClick) {
      onClick(event);
    }
  };

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  return (
    <Card
      className={cn(
        'transition-all hover:shadow-md cursor-pointer',
        onClick && 'hover:border-primary/50',
        className
      )}
      onClick={handleClick}
    >
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm line-clamp-2">{event.title}</h4>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <RiskBadge level={event.risk_level} score={event.risk_score} size="sm" />
            {expandable && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={toggleExpand}
              >
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </div>

        {/* Meta info */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
          <Badge
            variant="outline"
            className={cn(
              'capitalize text-xs',
              getCategoryBgColor(event.category),
              getCategoryColor(event.category)
            )}
          >
            {event.category}
          </Badge>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatTimeAgo(event.last_updated)}
          </span>
          <span className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {event.article_count} articles
          </span>
        </div>

        {/* Entities preview */}
        {event.entities.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {event.entities.slice(0, isExpanded ? undefined : 3).map((entity) => (
              <Badge key={entity} variant="secondary" className="text-xs">
                {entity}
              </Badge>
            ))}
            {!isExpanded && event.entities.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{event.entities.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Expanded content */}
        {isExpanded && (
          <div className="mt-3 pt-3 border-t space-y-3">
            {event.description && (
              <p className="text-sm text-muted-foreground">{event.description}</p>
            )}

            {/* Sources */}
            {event.sources.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Sources</p>
                <div className="flex flex-wrap gap-1">
                  {event.sources.map((source) => (
                    <Badge key={source} variant="outline" className="text-xs">
                      {source}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamps */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <p className="text-muted-foreground">First seen</p>
                <p className="font-medium">{formatTimeAgo(event.first_seen)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Last updated</p>
                <p className="font-medium">{formatTimeAgo(event.last_updated)}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * EventTimeline - Chronological event view with clustering
 *
 * Displays latest events in a timeline format with cluster context
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  User,
  Building2,
  MapPin,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { useLatestEvents } from '../api/useTrendingEntities';
import { CompactRiskBadge } from './RiskScoreCard';
import type { IntelligenceEvent } from '../types/intelligence.types';

interface EventTimelineProps {
  hours?: number;
  limit?: number;
  onEventClick?: (event: IntelligenceEvent) => void;
}

export function EventTimeline({ hours = 4, limit = 20, onEventClick }: EventTimelineProps) {
  const [selectedHours, setSelectedHours] = useState(hours);
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());

  const { data, isLoading, error, refetch } = useLatestEvents({
    hours: selectedHours,
    limit,
  });

  const toggleEventExpansion = (eventId: string) => {
    const newExpanded = new Set(expandedEvents);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedEvents(newExpanded);
  };

  const formatTimeAgo = (dateStr: string): string => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const getSentimentColor = (sentiment?: number): string => {
    if (sentiment === undefined || sentiment === null) return 'text-muted-foreground';
    if (sentiment > 0.2) return 'text-green-500';
    if (sentiment < -0.2) return 'text-red-500';
    return 'text-yellow-500';
  };

  const getSentimentLabel = (sentiment?: number): string => {
    if (sentiment === undefined || sentiment === null) return 'neutral';
    if (sentiment > 0.2) return 'positive';
    if (sentiment < -0.2) return 'negative';
    return 'neutral';
  };

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Event Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center gap-2 py-8 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            <p>Failed to load events</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Event Timeline
          </CardTitle>
          <CardDescription>
            {data?.total || 0} events in the last {selectedHours} hours
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedHours}
            onChange={(e) => setSelectedHours(Number(e.target.value))}
            className="px-2 py-1 text-sm border rounded bg-background"
          >
            <option value={1}>Last hour</option>
            <option value={4}>Last 4 hours</option>
            <option value={12}>Last 12 hours</option>
            <option value={24}>Last 24 hours</option>
            <option value={48}>Last 48 hours</option>
          </select>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-5 w-3/4 mb-2" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : data?.events.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No events found in the selected time range
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-[23px] top-0 bottom-0 w-0.5 bg-border" />

            <div className="space-y-4">
              {data?.events.map((event) => {
                const isExpanded = expandedEvents.has(event.id);
                return (
                  <div
                    key={event.id}
                    className="relative pl-14 group"
                  >
                    {/* Timeline dot */}
                    <div className="absolute left-[18px] top-2 w-3 h-3 rounded-full bg-primary ring-4 ring-background" />

                    <div
                      className="p-4 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer"
                      onClick={() => onEventClick?.(event)}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h4 className="font-medium line-clamp-2 flex-1">
                          {event.title}
                        </h4>
                        <div className="flex items-center gap-2 shrink-0">
                          {event.cluster && (
                            <CompactRiskBadge score={event.cluster.risk_score} size="sm" />
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleEventExpansion(event.id);
                            }}
                          >
                            {isExpanded ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 text-sm text-muted-foreground">
                        <span>{event.source}</span>
                        <span>|</span>
                        <span>{formatTimeAgo(event.published_at)}</span>
                        {event.sentiment !== undefined && (
                          <>
                            <span>|</span>
                            <span className={getSentimentColor(event.sentiment)}>
                              {getSentimentLabel(event.sentiment)}
                            </span>
                          </>
                        )}
                      </div>

                      {/* Cluster badge */}
                      {event.cluster && (
                        <div className="mt-2">
                          <Badge variant="outline" className="text-xs">
                            Cluster: {event.cluster.name}
                          </Badge>
                        </div>
                      )}

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="mt-4 pt-4 border-t space-y-3">
                          {event.description && (
                            <p className="text-sm text-muted-foreground">
                              {event.description}
                            </p>
                          )}

                          {/* Entities */}
                          {event.entities && (
                            <div className="space-y-2">
                              {event.entities.persons?.length > 0 && (
                                <div className="flex items-start gap-2">
                                  <User className="h-4 w-4 text-blue-500 mt-0.5" />
                                  <div className="flex flex-wrap gap-1">
                                    {event.entities.persons.map((person) => (
                                      <Badge key={person} variant="secondary" className="text-xs">
                                        {person}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {event.entities.organizations?.length > 0 && (
                                <div className="flex items-start gap-2">
                                  <Building2 className="h-4 w-4 text-purple-500 mt-0.5" />
                                  <div className="flex flex-wrap gap-1">
                                    {event.entities.organizations.map((org) => (
                                      <Badge key={org} variant="secondary" className="text-xs">
                                        {org}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {event.entities.locations?.length > 0 && (
                                <div className="flex items-start gap-2">
                                  <MapPin className="h-4 w-4 text-green-500 mt-0.5" />
                                  <div className="flex flex-wrap gap-1">
                                    {event.entities.locations.map((loc) => (
                                      <Badge key={loc} variant="secondary" className="text-xs">
                                        {loc}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Keywords */}
                          {event.keywords?.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {event.keywords.map((keyword) => (
                                <span
                                  key={keyword}
                                  className="px-2 py-0.5 text-xs bg-secondary rounded-full"
                                >
                                  {keyword}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Source link */}
                          {event.source_url && (
                            <a
                              href={event.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <ExternalLink className="h-3 w-3" />
                              View original
                            </a>
                          )}

                          {/* Metadata */}
                          <div className="grid grid-cols-3 gap-4 text-xs text-muted-foreground pt-2">
                            <div>
                              <p className="font-medium">Confidence</p>
                              <p>{event.confidence ? `${(event.confidence * 100).toFixed(0)}%` : 'N/A'}</p>
                            </div>
                            <div>
                              <p className="font-medium">Bias Score</p>
                              <p>{event.bias_score?.toFixed(2) || 'N/A'}</p>
                            </div>
                            <div>
                              <p className="font-medium">Sentiment</p>
                              <p className={getSentimentColor(event.sentiment)}>
                                {event.sentiment?.toFixed(2) || 'N/A'}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * LatestEventsPage
 *
 * Timeline view of latest intelligence events
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Clock,
  RefreshCw,
  AlertTriangle,
  Filter,
} from 'lucide-react';
import { useLatestEvents } from '../api/useLatestEvents';
import { EventCard } from '../components/EventCard';
import type { IntelligenceEvent, EventCategory, RiskLevel } from '../types/events.types';

export function LatestEventsPage() {
  const [categoryFilter, setCategoryFilter] = useState<EventCategory | undefined>();
  const [riskFilter, setRiskFilter] = useState<RiskLevel | undefined>();
  const [limit, setLimit] = useState(50);

  const { data, isLoading, error, refetch } = useLatestEvents({
    category: categoryFilter,
    risk_level: riskFilter,
    limit,
  });

  const categories: EventCategory[] = ['breaking', 'developing', 'trend', 'recurring', 'anomaly'];
  const riskLevels: RiskLevel[] = ['low', 'medium', 'high', 'critical'];

  const handleEventClick = (event: IntelligenceEvent) => {
    // Navigate to event detail or open modal
    console.log('Event clicked:', event.id);
  };

  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center gap-3 text-destructive">
              <AlertTriangle className="h-8 w-8" />
              <p>Failed to load latest events</p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Clock className="h-6 w-6" />
            Latest Events
          </h1>
          <p className="text-muted-foreground">
            Real-time timeline of intelligence events
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-wrap items-center gap-4">
            <Filter className="h-4 w-4 text-muted-foreground" />

            {/* Category filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Category:</span>
              <select
                value={categoryFilter || ''}
                onChange={(e) => setCategoryFilter(e.target.value as EventCategory || undefined)}
                className="px-2 py-1 text-sm border rounded bg-background"
              >
                <option value="">All</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat} className="capitalize">
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Risk filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Risk:</span>
              <select
                value={riskFilter || ''}
                onChange={(e) => setRiskFilter(e.target.value as RiskLevel || undefined)}
                className="px-2 py-1 text-sm border rounded bg-background"
              >
                <option value="">All</option>
                {riskLevels.map((level) => (
                  <option key={level} value={level} className="capitalize">
                    {level}
                  </option>
                ))}
              </select>
            </div>

            {/* Limit */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Show:</span>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="px-2 py-1 text-sm border rounded bg-background"
              >
                <option value={25}>25 events</option>
                <option value={50}>50 events</option>
                <option value={100}>100 events</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Events Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Event Timeline</CardTitle>
          <CardDescription>
            {data?.total || 0} events found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : data?.events.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No events found matching your filters
            </div>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-[11px] top-0 bottom-0 w-0.5 bg-border" />

              <div className="space-y-4">
                {data?.events.map((event) => (
                  <div key={event.id} className="relative pl-8">
                    {/* Timeline dot */}
                    <div className="absolute left-0 top-4 w-6 h-6 rounded-full bg-primary flex items-center justify-center ring-4 ring-background">
                      <Clock className="h-3 w-3 text-primary-foreground" />
                    </div>

                    <EventCard
                      event={event}
                      onClick={handleEventClick}
                      expandable
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Load more */}
          {data && data.events.length < data.total && (
            <div className="text-center mt-6">
              <Button
                variant="outline"
                onClick={() => setLimit((l) => l + 50)}
              >
                Load More Events
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

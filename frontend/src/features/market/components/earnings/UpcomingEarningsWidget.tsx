/**
 * UpcomingEarningsWidget Component
 * Compact widget showing next earnings events with countdown
 */

import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';
import {
  CalendarClock,
  Clock,
  ChevronRight,
  Building2,
  Filter,
} from 'lucide-react';
import { useUpcomingEarnings, useTodayEarnings } from '../../api/useEarningsCalendar';
import type { EarningsEvent } from '../../types/earnings.types';
import { formatEarningsTime, getEarningsTimeColor } from '../../types/earnings.types';

interface UpcomingEarningsWidgetProps {
  limit?: number;
  showFilters?: boolean;
  onEventClick?: (event: EarningsEvent) => void;
  onViewAll?: () => void;
  className?: string;
}

type FilterMode = 'all' | 'today' | 'week';

function getCountdown(dateStr: string): { days: number; hours: number; label: string } {
  const now = new Date();
  const target = new Date(dateStr);
  const diffMs = target.getTime() - now.getTime();

  if (diffMs < 0) {
    return { days: 0, hours: 0, label: 'Reported' };
  }

  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (days === 0 && hours === 0) {
    return { days: 0, hours: 0, label: 'Today' };
  } else if (days === 0) {
    return { days: 0, hours, label: `${hours}h` };
  } else if (days === 1) {
    return { days: 1, hours, label: 'Tomorrow' };
  } else {
    return { days, hours, label: `${days}d` };
  }
}

function formatDateShort(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

export function UpcomingEarningsWidget({
  limit = 5,
  showFilters = true,
  onEventClick,
  onViewAll,
  className,
}: UpcomingEarningsWidgetProps) {
  const [filter, setFilter] = useState<FilterMode>('week');

  const { data: weeklyEvents, isLoading: weeklyLoading } = useUpcomingEarnings(7);
  const { data: todayEvents, isLoading: todayLoading } = useTodayEarnings();

  const isLoading = filter === 'today' ? todayLoading : weeklyLoading;

  const displayEvents = useMemo(() => {
    const events = filter === 'today' ? todayEvents : weeklyEvents;
    if (!events) return [];

    // Sort by date, then by time (bmo before amc)
    const sorted = [...events].sort((a, b) => {
      const dateCompare = a.date.localeCompare(b.date);
      if (dateCompare !== 0) return dateCompare;

      const timeOrder = { bmo: 0, dmh: 1, amc: 2 };
      return timeOrder[a.time] - timeOrder[b.time];
    });

    return sorted.slice(0, limit);
  }, [weeklyEvents, todayEvents, filter, limit]);

  const totalCount = useMemo(() => {
    const events = filter === 'today' ? todayEvents : weeklyEvents;
    return events?.length || 0;
  }, [weeklyEvents, todayEvents, filter]);

  const nextEarnings = displayEvents[0];
  const countdown = nextEarnings ? getCountdown(nextEarnings.date) : null;

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5" />
            Upcoming Earnings
          </CardTitle>

          {showFilters && (
            <div className="flex items-center gap-1">
              <Button
                variant={filter === 'today' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('today')}
                className="h-7 text-xs"
              >
                Today
              </Button>
              <Button
                variant={filter === 'week' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter('week')}
                className="h-7 text-xs"
              >
                This Week
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Countdown to next earnings */}
        {countdown && nextEarnings && (
          <div className="mb-4 p-3 rounded-lg bg-primary/10 border border-primary/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-muted-foreground">Next Earnings</div>
                <div className="font-semibold text-primary">{nextEarnings.symbol}</div>
                <div className="text-xs text-muted-foreground">{nextEarnings.company_name}</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-primary">{countdown.label}</div>
                <Badge variant="outline" className={getEarningsTimeColor(nextEarnings.time)}>
                  {formatEarningsTime(nextEarnings.time)}
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* Events List */}
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : displayEvents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CalendarClock className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <div>No upcoming earnings {filter === 'today' ? 'today' : 'this week'}</div>
          </div>
        ) : (
          <div className="space-y-2">
            {displayEvents.map((event, index) => (
              <EarningsEventRow
                key={`${event.symbol}-${event.date}`}
                event={event}
                isFirst={index === 0}
                onClick={() => onEventClick?.(event)}
              />
            ))}
          </div>
        )}

        {/* View All Link */}
        {totalCount > limit && onViewAll && (
          <Button
            variant="ghost"
            className="w-full mt-4"
            onClick={onViewAll}
          >
            View all {totalCount} earnings
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

interface EarningsEventRowProps {
  event: EarningsEvent;
  isFirst?: boolean;
  onClick?: () => void;
}

function EarningsEventRow({ event, isFirst, onClick }: EarningsEventRowProps) {
  const countdown = getCountdown(event.date);

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg border transition-colors hover:bg-muted/50 ${
        isFirst ? 'border-primary/30 bg-primary/5' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="flex-shrink-0">
            <Building2 className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-primary">{event.symbol}</span>
              <Badge
                variant="outline"
                className={`text-[10px] px-1 py-0 ${getEarningsTimeColor(event.time)}`}
              >
                {event.time.toUpperCase()}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground truncate">
              {event.company_name}
            </div>
          </div>
        </div>

        <div className="flex-shrink-0 text-right">
          <div className="text-sm font-medium">{countdown.label}</div>
          <div className="text-xs text-muted-foreground">{formatDateShort(event.date)}</div>
        </div>
      </div>

      {/* EPS Estimate */}
      {event.eps_estimated !== null && (
        <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
          <span>EPS Estimate:</span>
          <span className="font-mono">${event.eps_estimated.toFixed(2)}</span>
        </div>
      )}
    </button>
  );
}

export default UpcomingEarningsWidget;

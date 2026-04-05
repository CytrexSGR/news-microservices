/**
 * EarningsCalendar Component
 * Weekly calendar view of upcoming earnings events
 */

import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  ChevronLeft,
  ChevronRight,
  Calendar,
  Building2,
  Clock,
} from 'lucide-react';
import { useWeeklyEarnings, groupEarningsByDate } from '../../api/useEarningsCalendar';
import type { EarningsEvent, EarningsByDate } from '../../types/earnings.types';
import {
  formatEarningsTime,
  getEarningsTimeColor,
} from '../../types/earnings.types';

interface EarningsCalendarProps {
  onEventClick?: (event: EarningsEvent) => void;
  className?: string;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getWeekDates(weekOffset: number = 0): Date[] {
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay() + weekOffset * 7);

  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(startOfWeek);
    date.setDate(startOfWeek.getDate() + i);
    return date;
  });
}

function formatDateKey(date: Date): string {
  return date.toISOString().split('T')[0];
}

function formatDateDisplay(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function isToday(date: Date): boolean {
  const today = new Date();
  return formatDateKey(date) === formatDateKey(today);
}

function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

export function EarningsCalendar({ onEventClick, className }: EarningsCalendarProps) {
  const [weekOffset, setWeekOffset] = useState(0);
  const { data: events, isLoading, error } = useWeeklyEarnings();

  const weekDates = useMemo(() => getWeekDates(weekOffset), [weekOffset]);
  const groupedEvents = useMemo(() => {
    if (!events) return new Map<string, EarningsEvent[]>();

    const grouped = groupEarningsByDate(events);
    return new Map(grouped.map((g) => [g.date, g.events]));
  }, [events]);

  const weekLabel = useMemo(() => {
    const start = weekDates[0];
    const end = weekDates[6];
    const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    return `${startStr} - ${endStr}`;
  }, [weekDates]);

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            Failed to load earnings calendar
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Earnings Calendar
          </CardTitle>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setWeekOffset((w) => w - 1)}
              className="p-1 hover:bg-muted rounded transition-colors"
              aria-label="Previous week"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-sm font-medium min-w-[180px] text-center">
              {weekLabel}
            </span>
            <button
              onClick={() => setWeekOffset((w) => w + 1)}
              className="p-1 hover:bg-muted rounded transition-colors"
              aria-label="Next week"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            {weekOffset !== 0 && (
              <button
                onClick={() => setWeekOffset(0)}
                className="ml-2 text-xs text-primary hover:underline"
              >
                Today
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1">
          {/* Header Row */}
          {WEEKDAYS.map((day, i) => (
            <div
              key={day}
              className={`text-center text-xs font-medium p-2 ${
                i === 0 || i === 6 ? 'text-muted-foreground' : ''
              }`}
            >
              {day}
            </div>
          ))}

          {/* Date Cells */}
          {weekDates.map((date) => {
            const dateKey = formatDateKey(date);
            const dayEvents = groupedEvents.get(dateKey) || [];
            const isTodayDate = isToday(date);
            const isWeekendDate = isWeekend(date);

            return (
              <div
                key={dateKey}
                className={`min-h-[120px] border rounded-lg p-2 ${
                  isTodayDate
                    ? 'border-primary bg-primary/5'
                    : isWeekendDate
                      ? 'bg-muted/30 border-border/50'
                      : 'border-border'
                }`}
              >
                <div
                  className={`text-xs font-medium mb-2 ${
                    isTodayDate ? 'text-primary' : 'text-muted-foreground'
                  }`}
                >
                  {formatDateDisplay(date)}
                  {isTodayDate && (
                    <span className="ml-1 text-primary">(Today)</span>
                  )}
                </div>

                {isLoading ? (
                  <div className="space-y-1">
                    <Skeleton className="h-6 w-full" />
                    <Skeleton className="h-6 w-3/4" />
                  </div>
                ) : (
                  <div className="space-y-1">
                    {dayEvents.slice(0, 4).map((event) => (
                      <EarningsEventItem
                        key={`${event.symbol}-${event.date}`}
                        event={event}
                        onClick={() => onEventClick?.(event)}
                      />
                    ))}
                    {dayEvents.length > 4 && (
                      <div className="text-xs text-muted-foreground text-center pt-1">
                        +{dayEvents.length - 4} more
                      </div>
                    )}
                    {dayEvents.length === 0 && !isWeekendDate && (
                      <div className="text-xs text-muted-foreground text-center py-4">
                        No earnings
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 mt-4 pt-4 border-t">
          <div className="text-xs text-muted-foreground">Time:</div>
          <div className="flex items-center gap-1">
            <Badge variant="outline" className="text-xs text-green-600 bg-green-100 dark:bg-green-900/30">
              BMO
            </Badge>
            <span className="text-xs text-muted-foreground">Before Open</span>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="outline" className="text-xs text-blue-600 bg-blue-100 dark:bg-blue-900/30">
              AMC
            </Badge>
            <span className="text-xs text-muted-foreground">After Close</span>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="outline" className="text-xs text-gray-600 bg-gray-100 dark:bg-gray-900/30">
              DMH
            </Badge>
            <span className="text-xs text-muted-foreground">Market Hours</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface EarningsEventItemProps {
  event: EarningsEvent;
  onClick?: () => void;
}

function EarningsEventItem({ event, onClick }: EarningsEventItemProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-1.5 rounded hover:bg-muted/80 transition-colors group"
    >
      <div className="flex items-center justify-between gap-1">
        <span className="font-semibold text-xs truncate group-hover:text-primary">
          {event.symbol}
        </span>
        <Badge
          variant="outline"
          className={`text-[10px] px-1 py-0 ${getEarningsTimeColor(event.time)}`}
        >
          {event.time.toUpperCase()}
        </Badge>
      </div>
      {event.eps_estimated !== null && (
        <div className="text-[10px] text-muted-foreground truncate">
          EPS Est: ${event.eps_estimated.toFixed(2)}
        </div>
      )}
    </button>
  );
}

export default EarningsCalendar;

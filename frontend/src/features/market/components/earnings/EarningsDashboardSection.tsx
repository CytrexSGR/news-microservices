/**
 * EarningsDashboardSection Component
 * Compact section for the main market dashboard
 */

import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  CalendarClock,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Building2,
} from 'lucide-react';
import { useWeeklyEarnings } from '../../api/useEarningsCalendar';
import { useRecentSurprises, getTopSurprises } from '../../api/useEarningsSurprises';
import type { EarningsEvent, EarningsSurprise } from '../../types/earnings.types';
import { getEarningsTimeColor } from '../../types/earnings.types';

interface EarningsDashboardSectionProps {
  className?: string;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function getTimeLabel(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return 'Reported';
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  return `${diffDays}d`;
}

export function EarningsDashboardSection({ className }: EarningsDashboardSectionProps) {
  const navigate = useNavigate();

  const { data: weeklyEvents, isLoading: eventsLoading } = useWeeklyEarnings();
  const { data: recentSurprises, isLoading: surprisesLoading } = useRecentSurprises(10);

  // Upcoming earnings (next 5)
  const upcomingEarnings = useMemo(() => {
    if (!weeklyEvents) return [];
    const now = new Date();
    return weeklyEvents
      .filter((e) => new Date(e.date) >= now)
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(0, 5);
  }, [weeklyEvents]);

  // Today's count
  const todayCount = useMemo(() => {
    if (!weeklyEvents) return 0;
    const today = new Date().toISOString().split('T')[0];
    return weeklyEvents.filter((e) => e.date === today).length;
  }, [weeklyEvents]);

  // This week's count
  const weekCount = weeklyEvents?.length || 0;

  // Top surprises
  const { topBeats, topMisses } = useMemo(() => {
    if (!recentSurprises) return { topBeats: [], topMisses: [] };
    return getTopSurprises(recentSurprises, 3);
  }, [recentSurprises]);

  const handleViewAll = () => {
    navigate('/market/earnings');
  };

  const handleEventClick = (event: EarningsEvent) => {
    navigate(`/market/earnings/${event.symbol}`);
  };

  const handleSymbolClick = (symbol: string) => {
    navigate(`/market/earnings/${symbol}`);
  };

  const isLoading = eventsLoading || surprisesLoading;

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5" />
            Earnings This Week
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={handleViewAll}>
            View All
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-16" />
              <Skeleton className="h-16" />
            </div>
            <Skeleton className="h-32" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                <div className="text-2xl font-bold text-primary">{todayCount}</div>
                <div className="text-xs text-muted-foreground">Reporting Today</div>
              </div>
              <div className="p-3 rounded-lg bg-muted">
                <div className="text-2xl font-bold">{weekCount}</div>
                <div className="text-xs text-muted-foreground">This Week</div>
              </div>
            </div>

            {/* Upcoming Earnings */}
            {upcomingEarnings.length > 0 && (
              <div>
                <div className="text-sm font-medium mb-2">Upcoming</div>
                <div className="space-y-2">
                  {upcomingEarnings.map((event) => (
                    <button
                      key={`${event.symbol}-${event.date}`}
                      onClick={() => handleEventClick(event)}
                      className="w-full text-left p-2 rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          <span className="font-semibold text-primary">{event.symbol}</span>
                          <Badge
                            variant="outline"
                            className={`text-[10px] px-1 py-0 ${getEarningsTimeColor(event.time)}`}
                          >
                            {event.time.toUpperCase()}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {getTimeLabel(event.date)}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Surprises Summary */}
            {(topBeats.length > 0 || topMisses.length > 0) && (
              <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                {/* Recent Beats */}
                <div>
                  <div className="flex items-center gap-1 text-sm font-medium text-green-600 mb-2">
                    <TrendingUp className="h-4 w-4" />
                    Recent Beats
                  </div>
                  <div className="space-y-1">
                    {topBeats.slice(0, 3).map((s) => (
                      <SurpriseRow
                        key={`${s.symbol}-${s.date}`}
                        surprise={s}
                        onClick={() => handleSymbolClick(s.symbol)}
                      />
                    ))}
                  </div>
                </div>

                {/* Recent Misses */}
                <div>
                  <div className="flex items-center gap-1 text-sm font-medium text-red-600 mb-2">
                    <TrendingDown className="h-4 w-4" />
                    Recent Misses
                  </div>
                  <div className="space-y-1">
                    {topMisses.slice(0, 3).map((s) => (
                      <SurpriseRow
                        key={`${s.symbol}-${s.date}`}
                        surprise={s}
                        onClick={() => handleSymbolClick(s.symbol)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Empty State */}
            {upcomingEarnings.length === 0 && topBeats.length === 0 && topMisses.length === 0 && (
              <div className="text-center py-4 text-muted-foreground">
                No earnings data available
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface SurpriseRowProps {
  surprise: EarningsSurprise;
  onClick?: () => void;
}

function SurpriseRow({ surprise, onClick }: SurpriseRowProps) {
  const isBeat = surprise.surprise_percent > 0;

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-1.5 rounded hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-center justify-between">
        <span className="font-medium text-sm">{surprise.symbol}</span>
        <span
          className={`text-xs font-mono ${
            isBeat ? 'text-green-600' : 'text-red-600'
          }`}
        >
          {isBeat ? '+' : ''}
          {surprise.surprise_percent.toFixed(1)}%
        </span>
      </div>
    </button>
  );
}

export default EarningsDashboardSection;

/**
 * EarningsDetailsPage Component
 * Single company earnings history, surprises, and transcripts
 */

import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  Building2,
  TrendingUp,
  TrendingDown,
  Calendar,
  FileText,
  BarChart3,
  Target,
} from 'lucide-react';
import {
  useSymbolEarnings,
  useEarningsSurprises,
  useEarningsSurpriseStats,
  useAvailableTranscripts,
} from '../api';
import {
  EarningsSurprisesChart,
  EarningsTranscriptViewer,
} from '../components/earnings';
import type { EarningsEvent } from '../types/earnings.types';
import { formatEarningsTime, getEarningsTimeColor } from '../types/earnings.types';

export function EarningsDetailsPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const [selectedTranscript, setSelectedTranscript] = useState<{
    quarter: string;
    year: number;
  } | null>(null);

  const { data: events, isLoading: eventsLoading } = useSymbolEarnings(symbol || '');
  const { stats, isLoading: statsLoading } = useEarningsSurpriseStats(symbol || '');
  const { data: transcripts, isLoading: transcriptsLoading } = useAvailableTranscripts(
    symbol || ''
  );

  // Next upcoming earnings
  const nextEarnings = useMemo(() => {
    if (!events) return null;
    const now = new Date();
    return events.find((e) => new Date(e.date) >= now);
  }, [events]);

  // Past earnings
  const pastEarnings = useMemo(() => {
    if (!events) return [];
    const now = new Date();
    return events
      .filter((e) => new Date(e.date) < now)
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, 8);
  }, [events]);

  const handleBack = () => {
    navigate('/market/earnings');
  };

  const handleTranscriptSelect = (value: string) => {
    const [quarter, year] = value.split('-');
    setSelectedTranscript({ quarter, year: parseInt(year) });
  };

  if (!symbol) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center text-muted-foreground">Symbol not provided</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div className="flex items-center gap-3">
            <Building2 className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">{symbol} Earnings</h1>
              <p className="text-muted-foreground">
                Historical earnings data and analysis
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      {statsLoading ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : stats ? (
        <div className="grid gap-4 md:grid-cols-4">
          <StatsCard
            title="Beat Rate"
            value={`${stats.beatRate.toFixed(0)}%`}
            subtitle={`${stats.totalReports} reports`}
            icon={<Target className="h-5 w-5 text-primary" />}
          />
          <StatsCard
            title="Beats"
            value={stats.beats.toString()}
            subtitle="earnings beats"
            icon={<TrendingUp className="h-5 w-5 text-green-600" />}
            valueColor="text-green-600"
          />
          <StatsCard
            title="Misses"
            value={stats.misses.toString()}
            subtitle="earnings misses"
            icon={<TrendingDown className="h-5 w-5 text-red-600" />}
            valueColor="text-red-600"
          />
          <StatsCard
            title="Avg Surprise"
            value={`${stats.avgSurprisePercent >= 0 ? '+' : ''}${stats.avgSurprisePercent.toFixed(1)}%`}
            subtitle={`${stats.streak.count}-quarter ${stats.streak.type} streak`}
            icon={<BarChart3 className="h-5 w-5 text-primary" />}
            valueColor={
              stats.avgSurprisePercent > 0
                ? 'text-green-600'
                : stats.avgSurprisePercent < 0
                  ? 'text-red-600'
                  : ''
            }
          />
        </div>
      ) : null}

      {/* Next Upcoming Earnings */}
      {nextEarnings && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Next Earnings Announcement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="text-lg font-semibold">
                  {new Date(nextEarnings.date).toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <Badge
                    variant="outline"
                    className={getEarningsTimeColor(nextEarnings.time)}
                  >
                    {formatEarningsTime(nextEarnings.time)}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {nextEarnings.fiscal_quarter} {nextEarnings.fiscal_year}
                  </span>
                </div>
              </div>
              <div className="text-right">
                {nextEarnings.eps_estimated !== null && (
                  <div>
                    <span className="text-sm text-muted-foreground">EPS Estimate: </span>
                    <span className="font-mono font-semibold">
                      ${nextEarnings.eps_estimated.toFixed(2)}
                    </span>
                  </div>
                )}
                {nextEarnings.revenue_estimated !== null && (
                  <div>
                    <span className="text-sm text-muted-foreground">Revenue Estimate: </span>
                    <span className="font-mono font-semibold">
                      ${(nextEarnings.revenue_estimated / 1e9).toFixed(2)}B
                    </span>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="chart" className="space-y-4">
        <TabsList>
          <TabsTrigger value="chart" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Earnings Chart
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            History
          </TabsTrigger>
          <TabsTrigger value="transcripts" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Transcripts
          </TabsTrigger>
        </TabsList>

        <TabsContent value="chart">
          <EarningsSurprisesChart symbol={symbol} showStats />
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Earnings History</CardTitle>
            </CardHeader>
            <CardContent>
              {eventsLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : pastEarnings.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No historical earnings data available
                </div>
              ) : (
                <div className="space-y-3">
                  {pastEarnings.map((event) => (
                    <EarningsHistoryItem key={`${event.symbol}-${event.date}`} event={event} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transcripts">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Earnings Transcripts
                </CardTitle>

                {transcripts && transcripts.length > 0 && (
                  <Select
                    value={
                      selectedTranscript
                        ? `${selectedTranscript.quarter}-${selectedTranscript.year}`
                        : undefined
                    }
                    onValueChange={handleTranscriptSelect}
                  >
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select transcript" />
                    </SelectTrigger>
                    <SelectContent>
                      {transcripts.map((t) => (
                        <SelectItem key={`${t.quarter}-${t.year}`} value={`${t.quarter}-${t.year}`}>
                          {t.quarter} {t.year}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {transcriptsLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : !transcripts || transcripts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No transcripts available for {symbol}
                </div>
              ) : selectedTranscript ? (
                <EarningsTranscriptViewer
                  symbol={symbol}
                  quarter={selectedTranscript.quarter}
                  year={selectedTranscript.year}
                />
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Select a transcript to view
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  valueColor?: string;
}

function StatsCard({ title, value, subtitle, icon, valueColor }: StatsCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-muted-foreground">{title}</div>
            <div className={`text-2xl font-bold ${valueColor || ''}`}>{value}</div>
            <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>
          </div>
          <div className="p-3 rounded-lg bg-muted">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

interface EarningsHistoryItemProps {
  event: EarningsEvent;
}

function EarningsHistoryItem({ event }: EarningsHistoryItemProps) {
  const hasSurprise = event.eps_actual !== null && event.eps_estimated !== null;
  const surprise = hasSurprise ? event.eps_actual! - event.eps_estimated! : 0;
  const isBeat = surprise > 0;
  const isMiss = surprise < 0;

  return (
    <div className="p-4 rounded-lg border hover:bg-muted/50 transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-semibold">
              {event.fiscal_quarter} {event.fiscal_year}
            </span>
            <Badge variant="outline" className={getEarningsTimeColor(event.time)}>
              {formatEarningsTime(event.time)}
            </Badge>
            {hasSurprise && (
              <Badge variant={isBeat ? 'default' : isMiss ? 'destructive' : 'secondary'}>
                {isBeat ? 'Beat' : isMiss ? 'Miss' : 'Inline'}
              </Badge>
            )}
          </div>
          <div className="text-sm text-muted-foreground mt-1">
            {new Date(event.date).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-right">
          <div>
            <div className="text-xs text-muted-foreground">EPS</div>
            <div className="font-mono text-sm">
              {event.eps_actual !== null ? (
                <span className={isBeat ? 'text-green-600' : isMiss ? 'text-red-600' : ''}>
                  ${event.eps_actual.toFixed(2)}
                </span>
              ) : (
                '-'
              )}
              {event.eps_estimated !== null && (
                <span className="text-muted-foreground"> / ${event.eps_estimated.toFixed(2)}</span>
              )}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Revenue</div>
            <div className="font-mono text-sm">
              {event.revenue_actual !== null ? (
                <span>${(event.revenue_actual / 1e9).toFixed(2)}B</span>
              ) : (
                '-'
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EarningsDetailsPage;

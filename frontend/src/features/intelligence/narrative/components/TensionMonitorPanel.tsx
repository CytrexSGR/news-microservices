/**
 * TensionMonitorPanel - Monitor high-tension narratives in real-time
 *
 * Provides tension threshold slider, severity badges, and alert list for emotionally charged content.
 */
import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  AlertCircle,
  AlertTriangle,
  Flame,
  RefreshCw,
  ExternalLink,
  TrendingUp,
  Clock,
} from 'lucide-react';
import { useHighTensionNarratives, useTensionAlerts } from '../api/kg';
import type {
  HighTensionNarrative,
  NarrativeType,
} from '../types/narrative.types';
import {
  getTensionSeverity,
  getTensionColor,
  getTensionBgColor,
  getNarrativeColor,
} from '../types/narrative.types';

interface TensionMonitorPanelProps {
  defaultThreshold?: number;
  enableAlerts?: boolean;
  onNarrativeClick?: (narrative: HighTensionNarrative) => void;
  className?: string;
}

export function TensionMonitorPanel({
  defaultThreshold = 0.6,
  enableAlerts = true,
  onNarrativeClick,
  className = '',
}: TensionMonitorPanelProps) {
  const [threshold, setThreshold] = useState(defaultThreshold);
  const [frameTypeFilter, setFrameTypeFilter] = useState<NarrativeType | 'all'>('all');

  // Fetch high tension narratives
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useHighTensionNarratives(
    {
      min_tension: threshold,
      frame_type: frameTypeFilter === 'all' ? undefined : frameTypeFilter,
      limit: 25,
    }
  );

  // Optional: Use tension alerts for real-time monitoring
  const { data: alertsData } = useTensionAlerts(0.8, enableAlerts);

  const criticalCount = useMemo(() => {
    return data?.narratives.filter((n) => n.tension_score >= 0.8).length ?? 0;
  }, [data]);

  const highCount = useMemo(() => {
    return data?.narratives.filter((n) => n.tension_score >= 0.6 && n.tension_score < 0.8).length ?? 0;
  }, [data]);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            <CardTitle>Tension Monitor</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {criticalCount > 0 && (
              <Badge variant="destructive" className="animate-pulse">
                {criticalCount} Critical
              </Badge>
            )}
            {highCount > 0 && (
              <Badge className="bg-orange-500">
                {highCount} High
              </Badge>
            )}
          </div>
        </div>
        <CardDescription>
          Monitor emotionally charged content and high-tension narratives
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Controls */}
        <div className="grid md:grid-cols-2 gap-4">
          {/* Threshold Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Tension Threshold</Label>
              <span className={`text-sm font-medium ${getTensionColor(threshold)}`}>
                {(threshold * 100).toFixed(0)}%
              </span>
            </div>
            <Slider
              value={[threshold]}
              onValueChange={([value]) => setThreshold(value)}
              min={0.3}
              max={1}
              step={0.05}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Low (30%)</span>
              <span>Critical (100%)</span>
            </div>
          </div>

          {/* Frame Type Filter */}
          <div className="space-y-2">
            <Label>Frame Type</Label>
            <Select
              value={frameTypeFilter}
              onValueChange={(value) => setFrameTypeFilter(value as NarrativeType | 'all')}
            >
              <SelectTrigger>
                <SelectValue placeholder="All frame types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="conflict">Conflict</SelectItem>
                <SelectItem value="crisis">Crisis</SelectItem>
                <SelectItem value="decline">Decline</SelectItem>
                <SelectItem value="progress">Progress</SelectItem>
                <SelectItem value="cooperation">Cooperation</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Stats Summary */}
        {data && (
          <div className="grid grid-cols-3 gap-4">
            <StatBox
              icon={<Flame className="h-4 w-4 text-red-500" />}
              label="Avg Tension"
              value={`${(data.avg_tension * 100).toFixed(1)}%`}
              valueClass={getTensionColor(data.avg_tension)}
            />
            <StatBox
              icon={<AlertTriangle className="h-4 w-4 text-orange-500" />}
              label="High Tension"
              value={data.narratives.filter((n) => n.tension_score >= 0.6).length.toString()}
            />
            <StatBox
              icon={<TrendingUp className="h-4 w-4 text-blue-500" />}
              label="Total Found"
              value={data.total.toString()}
            />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex flex-col items-center gap-4 py-6 text-center">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-muted-foreground">{error.message}</p>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && <TensionListSkeleton />}

        {/* Narratives List */}
        {data && !isLoading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">High Tension Narratives</Label>
              <Button variant="ghost" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
            {data.narratives.length > 0 ? (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {data.narratives.map((narrative) => (
                  <TensionNarrativeCard
                    key={narrative.id}
                    narrative={narrative}
                    onClick={() => onNarrativeClick?.(narrative)}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Flame className="h-10 w-10 mx-auto mb-2 opacity-20" />
                <p>No narratives above {(threshold * 100).toFixed(0)}% tension threshold</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Tension Narrative Card
 */
interface TensionNarrativeCardProps {
  narrative: HighTensionNarrative;
  onClick?: () => void;
}

function TensionNarrativeCard({ narrative, onClick }: TensionNarrativeCardProps) {
  const severity = getTensionSeverity(narrative.tension_score);
  const severityIcons = {
    low: null,
    medium: <AlertCircle className="h-4 w-4" />,
    high: <AlertTriangle className="h-4 w-4" />,
    critical: <Flame className="h-4 w-4 animate-pulse" />,
  };

  return (
    <div
      className={`p-3 rounded-lg cursor-pointer transition-colors ${getTensionBgColor(
        narrative.tension_score
      )} hover:opacity-90`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{narrative.headline}</h4>
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {new Date(narrative.created_at).toLocaleDateString()}
            <span>|</span>
            {narrative.source}
          </div>
        </div>
        <SeverityBadge
          severity={severity}
          score={narrative.tension_score}
          icon={severityIcons[severity]}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge variant="outline" className={getNarrativeColor(narrative.frame_type)}>
          {narrative.frame_type}
        </Badge>
        {narrative.entities.slice(0, 3).map((entity) => (
          <Badge key={entity} variant="secondary" className="text-xs">
            {entity}
          </Badge>
        ))}
        {narrative.entities.length > 3 && (
          <Badge variant="secondary" className="text-xs">
            +{narrative.entities.length - 3}
          </Badge>
        )}
      </div>
    </div>
  );
}

/**
 * Severity Badge Component
 */
interface SeverityBadgeProps {
  severity: 'low' | 'medium' | 'high' | 'critical';
  score: number;
  icon?: React.ReactNode;
}

function SeverityBadge({ severity, score, icon }: SeverityBadgeProps) {
  const variants: Record<string, string> = {
    low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };

  return (
    <Badge className={`${variants[severity]} flex items-center gap-1`}>
      {icon}
      {(score * 100).toFixed(0)}%
    </Badge>
  );
}

/**
 * Stat Box Component
 */
interface StatBoxProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueClass?: string;
}

function StatBox({ icon, label, value, valueClass = '' }: StatBoxProps) {
  return (
    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
      {icon}
      <div>
        <div className={`font-bold ${valueClass}`}>{value}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}

/**
 * Loading Skeleton
 */
function TensionListSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(4)].map((_, i) => (
        <Skeleton key={i} className="h-20 w-full" />
      ))}
    </div>
  );
}

/**
 * Compact Tension Widget for Dashboard
 */
export function TensionWidget({
  limit = 5,
  onViewAll,
  className = '',
}: {
  limit?: number;
  onViewAll?: () => void;
  className?: string;
}) {
  const { data, isLoading } = useHighTensionNarratives({ min_tension: 0.7, limit });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Flame className="h-4 w-4 text-orange-500" />
            High Tension
          </CardTitle>
          {data && data.total > limit && (
            <Button variant="ghost" size="sm" onClick={onViewAll}>
              View All
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {data && data.narratives.length > 0 ? (
          <div className="space-y-2">
            {data.narratives.slice(0, limit).map((narrative) => (
              <div
                key={narrative.id}
                className={`p-2 rounded text-sm ${getTensionBgColor(narrative.tension_score)}`}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate flex-1">{narrative.headline}</span>
                  <Badge className={getTensionColor(narrative.tension_score)}>
                    {(narrative.tension_score * 100).toFixed(0)}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">
            No high tension content
          </p>
        )}
      </CardContent>
    </Card>
  );
}

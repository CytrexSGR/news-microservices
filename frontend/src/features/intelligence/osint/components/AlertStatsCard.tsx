/**
 * AlertStatsCard - OSINT Alert Statistics Card
 *
 * Displays aggregated alert statistics
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
} from 'lucide-react';
import { useAlertStats } from '../api';
import type { AlertSeverity } from '../types/osint.types';
import { getSeverityColor, getSeverityBgColor } from '../types/osint.types';

interface AlertStatsCardProps {
  className?: string;
  compact?: boolean;
}

export function AlertStatsCard({ className, compact = false }: AlertStatsCardProps) {
  const { data, isLoading, error } = useAlertStats();

  if (isLoading) {
    return <AlertStatsCardSkeleton compact={compact} />;
  }

  if (error || !data) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load alert stats</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <Card className={className}>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              <span className="font-medium">Alerts</span>
            </div>
            <div className="flex items-center gap-3">
              {data.unacknowledged > 0 ? (
                <Badge variant="destructive">{data.unacknowledged} pending</Badge>
              ) : (
                <Badge variant="outline" className="text-green-500">All clear</Badge>
              )}
              <TrendIndicator trend={data.trend} />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Alert Statistics
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Overview Stats */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatItem
              label="Total Alerts"
              value={data.total}
              icon={<Bell className="h-4 w-4" />}
            />
            <StatItem
              label="Unacknowledged"
              value={data.unacknowledged}
              icon={<AlertTriangle className="h-4 w-4" />}
              highlight={data.unacknowledged > 0}
            />
            <StatItem
              label="Last 24 Hours"
              value={data.last_24h}
              icon={<Clock className="h-4 w-4" />}
            />
            <StatItem
              label="Last 7 Days"
              value={data.last_7d}
              icon={<Clock className="h-4 w-4" />}
              suffix={<TrendIndicator trend={data.trend} />}
            />
          </div>

          {/* Severity Breakdown */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">By Severity</h4>
            <div className="flex flex-wrap gap-2">
              {(['critical', 'high', 'medium', 'low'] as AlertSeverity[]).map((severity) => (
                <Badge
                  key={severity}
                  className={`${getSeverityBgColor(severity)} ${getSeverityColor(severity)} border-0`}
                >
                  <span className="capitalize">{severity}:</span>
                  <span className="ml-1 font-bold">{data.by_severity[severity] || 0}</span>
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface StatItemProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  highlight?: boolean;
  suffix?: React.ReactNode;
}

function StatItem({ label, value, icon, highlight = false, suffix }: StatItemProps) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? 'border-yellow-500/50 bg-yellow-500/5' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-muted-foreground">
          {icon}
          <span className="text-xs uppercase tracking-wider">{label}</span>
        </div>
        {suffix}
      </div>
      <div className={`text-2xl font-bold mt-1 ${highlight ? 'text-yellow-500' : ''}`}>
        {value.toLocaleString()}
      </div>
    </div>
  );
}

interface TrendIndicatorProps {
  trend: 'increasing' | 'decreasing' | 'stable';
}

function TrendIndicator({ trend }: TrendIndicatorProps) {
  switch (trend) {
    case 'increasing':
      return (
        <div className="flex items-center gap-1 text-red-500">
          <TrendingUp className="h-4 w-4" />
          <span className="text-xs">Rising</span>
        </div>
      );
    case 'decreasing':
      return (
        <div className="flex items-center gap-1 text-green-500">
          <TrendingDown className="h-4 w-4" />
          <span className="text-xs">Falling</span>
        </div>
      );
    case 'stable':
    default:
      return (
        <div className="flex items-center gap-1 text-muted-foreground">
          <Minus className="h-4 w-4" />
          <span className="text-xs">Stable</span>
        </div>
      );
  }
}

function AlertStatsCardSkeleton({ compact }: { compact?: boolean }) {
  if (compact) {
    return (
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-20" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-6 w-36" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="rounded-lg border p-3">
                <Skeleton className="h-4 w-20 mb-2" />
                <Skeleton className="h-8 w-12" />
              </div>
            ))}
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <div className="flex gap-2">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-5 w-20" />
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default AlertStatsCard;

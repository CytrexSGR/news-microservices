/**
 * UsageStatsCard Component
 *
 * Displays research usage statistics:
 * - Total requests and tokens
 * - Cost breakdown by model
 * - Period summary
 */

import {
  Coins,
  Zap,
  TrendingUp,
  BarChart3,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useUsageStats } from '../api';

interface UsageStatsCardProps {
  days?: number;
}

export function UsageStatsCard({ days = 30 }: UsageStatsCardProps) {
  const { data: stats, isLoading, isError } = useUsageStats(days);

  if (isLoading) {
    return (
      <div className="p-6 border border-border rounded-lg bg-card">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <div className="p-6 border border-border rounded-lg bg-card">
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <AlertCircle className="h-5 w-5 mr-2" />
          Failed to load statistics
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  const modelColors: Record<string, string> = {
    sonar: 'bg-blue-500',
    'sonar-pro': 'bg-purple-500',
    'sonar-reasoning-pro': 'bg-orange-500',
  };

  return (
    <div className="border border-border rounded-lg bg-card overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-foreground flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Usage Statistics
          </h3>
          <span className="text-xs text-muted-foreground">
            Last {days} days
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4">
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs">Requests</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">
            {formatNumber(stats.total_requests)}
          </p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
            <Zap className="h-4 w-4" />
            <span className="text-xs">Tokens</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">
            {formatNumber(stats.total_tokens)}
          </p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
            <Coins className="h-4 w-4" />
            <span className="text-xs">Total Cost</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">
            {formatCurrency(stats.total_cost)}
          </p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
            <BarChart3 className="h-4 w-4" />
            <span className="text-xs">Avg Tokens</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">
            {Math.round(stats.avg_tokens_per_request)}
          </p>
        </div>
      </div>

      {/* Model Breakdown */}
      {Object.keys(stats.requests_by_model).length > 0 && (
        <div className="p-4 border-t border-border bg-muted/30">
          <h4 className="text-xs font-medium text-muted-foreground mb-3">
            Usage by Model
          </h4>
          <div className="space-y-2">
            {Object.entries(stats.requests_by_model).map(([model, count]) => {
              const cost = stats.cost_by_model[model] || 0;
              const percentage =
                stats.total_requests > 0
                  ? (count / stats.total_requests) * 100
                  : 0;

              return (
                <div key={model} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-foreground capitalize">
                      {model.replace(/-/g, ' ')}
                    </span>
                    <span className="text-muted-foreground">
                      {count} requests ({formatCurrency(cost)})
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${modelColors[model] || 'bg-primary'} rounded-full transition-all`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Period Info */}
      <div className="p-4 border-t border-border text-xs text-muted-foreground">
        Period: {new Date(stats.period_start).toLocaleDateString()} -{' '}
        {new Date(stats.period_end).toLocaleDateString()}
      </div>
    </div>
  );
}

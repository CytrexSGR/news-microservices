/**
 * ResearchStatsPanel Component
 *
 * Comprehensive statistics panel for research usage:
 * - Overview metrics
 * - Model usage breakdown
 * - Cost analysis
 * - Time period comparison
 */

import {
  TrendingUp,
  Zap,
  Coins,
  BarChart3,
  Activity,
  Clock,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useUsageStats } from '../api';

interface ResearchStatsPanelProps {
  days?: number;
}

function StatCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
}: {
  title: string;
  value: string | number;
  icon: typeof TrendingUp;
  description?: string;
  trend?: { value: number; positive: boolean };
}) {
  return (
    <div className="p-4 border border-border rounded-lg bg-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-muted-foreground">{title}</span>
        <Icon className="h-4 w-4 text-primary" />
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-foreground">{value}</span>
        {trend && (
          <span
            className={`text-xs font-medium ${
              trend.positive ? 'text-green-500' : 'text-red-500'
            }`}
          >
            {trend.positive ? '+' : ''}
            {trend.value}%
          </span>
        )}
      </div>
      {description && (
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

function ModelBreakdownChart({
  requestsByModel,
  costByModel,
  totalRequests,
  totalCost,
}: {
  requestsByModel: Record<string, number>;
  costByModel: Record<string, number>;
  totalRequests: number;
  totalCost: number;
}) {
  const modelColors: Record<string, string> = {
    sonar: '#3b82f6',
    'sonar-pro': '#8b5cf6',
    'sonar-reasoning-pro': '#f97316',
  };

  const models = Object.keys(requestsByModel);

  return (
    <div className="p-4 border border-border rounded-lg bg-card">
      <h4 className="text-sm font-medium text-foreground mb-4 flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-primary" />
        Usage by Model
      </h4>

      {models.length === 0 ? (
        <p className="text-sm text-muted-foreground">No data available</p>
      ) : (
        <div className="space-y-4">
          {models.map((model) => {
            const requests = requestsByModel[model] || 0;
            const cost = costByModel[model] || 0;
            const percentage =
              totalRequests > 0 ? (requests / totalRequests) * 100 : 0;

            return (
              <div key={model} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: modelColors[model] || '#6b7280' }}
                    />
                    <span className="text-foreground capitalize">
                      {model.replace(/-/g, ' ')}
                    </span>
                  </div>
                  <span className="text-muted-foreground">
                    {requests} requests
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: modelColors[model] || '#6b7280',
                      }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground w-16 text-right">
                    ${cost.toFixed(2)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function ResearchStatsPanel({ days = 30 }: ResearchStatsPanelProps) {
  const { data: stats, isLoading, isError } = useUsageStats(days);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <div className="flex items-center justify-center py-12 text-destructive">
        <AlertCircle className="h-5 w-5 mr-2" />
        Failed to load statistics
      </div>
    );
  }

  const formatNumber = (n: number) => new Intl.NumberFormat('en-US').format(n);
  const formatCurrency = (n: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(n);

  const avgCostPerRequest =
    stats.total_requests > 0 ? stats.total_cost / stats.total_requests : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-foreground flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          Research Statistics
        </h3>
        <span className="text-sm text-muted-foreground">
          {new Date(stats.period_start).toLocaleDateString()} -{' '}
          {new Date(stats.period_end).toLocaleDateString()}
        </span>
      </div>

      {/* Overview Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Requests"
          value={formatNumber(stats.total_requests)}
          icon={TrendingUp}
          description={`Last ${days} days`}
        />
        <StatCard
          title="Total Tokens"
          value={formatNumber(stats.total_tokens)}
          icon={Zap}
          description="Tokens consumed"
        />
        <StatCard
          title="Total Cost"
          value={formatCurrency(stats.total_cost)}
          icon={Coins}
        />
        <StatCard
          title="Avg Cost/Request"
          value={formatCurrency(avgCostPerRequest)}
          icon={Clock}
        />
      </div>

      {/* Model Breakdown */}
      <div className="grid md:grid-cols-2 gap-6">
        <ModelBreakdownChart
          requestsByModel={stats.requests_by_model}
          costByModel={stats.cost_by_model}
          totalRequests={stats.total_requests}
          totalCost={stats.total_cost}
        />

        {/* Token Stats */}
        <div className="p-4 border border-border rounded-lg bg-card">
          <h4 className="text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            Token Statistics
          </h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Average tokens per request
              </span>
              <span className="text-sm font-medium text-foreground">
                {Math.round(stats.avg_tokens_per_request)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Total tokens used
              </span>
              <span className="text-sm font-medium text-foreground">
                {formatNumber(stats.total_tokens)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Cost per 1K tokens
              </span>
              <span className="text-sm font-medium text-foreground">
                {stats.total_tokens > 0
                  ? formatCurrency((stats.total_cost / stats.total_tokens) * 1000)
                  : '$0.00'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

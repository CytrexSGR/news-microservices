/**
 * Optimization Results View
 *
 * Detailed visualization of optimization results.
 *
 * Features:
 * - Optimization history chart (trial progression)
 * - Walk-forward validation metrics
 * - Best parameters display
 * - Performance metrics cards
 * - Apply optimized parameters to strategy
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, CheckCircle2, AlertTriangle, X, Play, Loader2, Check } from 'lucide-react';

import type { OptimizationResult, ApplyParamsRequest, ApplyParamsResponse } from '../types/optimization';
import { predictionClient } from '@/lib/api-client';

interface OptimizationResultsViewProps {
  result: OptimizationResult;
  jobId?: string;  // Job ID for applying parameters (uses result.id as fallback)
  onClose?: () => void;
}

export function OptimizationResultsView({ result, jobId, onClose }: OptimizationResultsViewProps) {
  const [applySuccess, setApplySuccess] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  // Use jobId prop or fall back to result.id
  const effectiveJobId = jobId || result.id;

  // Mutation for applying optimized parameters
  const applyParamsMutation = useMutation({
    mutationFn: async (createNewVersion: boolean) => {
      const response = await predictionClient.post<ApplyParamsResponse>(
        `/optimization/jobs/${effectiveJobId}/apply`,
        { create_new_version: createNewVersion } as ApplyParamsRequest
      );
      return response.data;
    },
    onSuccess: (data) => {
      setApplySuccess(true);
      setApplyError(null);
      console.log('Parameters applied successfully:', data);
    },
    onError: (error: Error) => {
      setApplyError(error.message || 'Failed to apply parameters');
      setApplySuccess(false);
    },
  });
  // Transform optimization_history to chart data
  const historyData = result.optimization_history.map(([trial, score]) => ({
    trial,
    score: parseFloat(score.toFixed(4)),
  }));

  // Calculate cumulative best score
  const cumulativeBestData = historyData.map((point, index) => {
    const bestSoFar = Math.max(...historyData.slice(0, index + 1).map(p => p.score));
    return {
      trial: point.trial,
      score: point.score,
      best: parseFloat(bestSoFar.toFixed(4)),
    };
  });

  const wfMetrics = result.walk_forward_metrics;

  // Transform parameter importances to chart data
  const importanceData = result.parameter_importances
    ? Object.entries(result.parameter_importances)
        .map(([name, importance]) => ({
          name,
          importance: parseFloat(importance.toFixed(4)),
        }))
        .sort((a, b) => b.importance - a.importance) // Sort descending
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <CheckCircle2 className="h-6 w-6 text-green-500" />
            Optimization Results
          </h2>
          <p className="text-muted-foreground">
            Strategy: {result.strategy_id} | Metric: {result.objective_metric.replace('_', ' ')}
          </p>
        </div>
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Summary Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Best Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {parseFloat(result.best_score).toFixed(4)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {result.objective_metric.replace('_', ' ')}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Trials Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{result.trials_completed}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {result.duration_seconds}s duration
            </p>
          </CardContent>
        </Card>

        {wfMetrics && (
          <>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Avg Test Sharpe
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {wfMetrics.avg_test_sharpe?.toFixed(3) ?? 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Train: {wfMetrics.avg_train_sharpe?.toFixed(3) ?? 'N/A'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Overfitting Ratio
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${
                  wfMetrics.overfitting_ratio !== null && wfMetrics.overfitting_ratio < 1.2 ? 'text-green-600' : 'text-orange-600'
                }`}>
                  {wfMetrics.overfitting_ratio?.toFixed(2) ?? 'N/A'}{wfMetrics.overfitting_ratio !== null ? 'x' : ''}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {wfMetrics.overfitting_ratio !== null ? (wfMetrics.overfitting_ratio < 1.2 ? 'Good' : 'High') : 'Not available'}
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Optimization History Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Optimization Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={cumulativeBestData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="trial"
                stroke="hsl(var(--muted-foreground))"
                label={{ value: 'Trial Number', position: 'insideBottom', offset: -5 }}
              />
              <YAxis
                stroke="hsl(var(--muted-foreground))"
                label={{ value: result.objective_metric.replace('_', ' '), angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="score"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth={1}
                dot={false}
                name="Trial Score"
              />
              <Line
                type="stepAfter"
                dataKey="best"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name="Best Score"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Parameter Importance Chart */}
      {result.parameter_importances && importanceData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Parameter Importance
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Shows which parameters had the most impact on the objective metric
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={importanceData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  type="number"
                  stroke="hsl(var(--muted-foreground))"
                  label={{ value: 'Importance Score', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="hsl(var(--muted-foreground))"
                  width={120}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                  formatter={(value: number) => [value.toFixed(4), 'Importance']}
                />
                <Bar dataKey="importance" fill="hsl(var(--primary))" />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 text-xs text-muted-foreground">
              <p>
                Higher values indicate parameters that had stronger influence on optimization results.
                Parameters with low importance may have minimal impact or be correlated with other parameters.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Walk-Forward Metrics */}
      {wfMetrics && (
        <Card>
          <CardHeader>
            <CardTitle>Walk-Forward Validation Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Train/Test Correlation</span>
                  <span className="font-medium">{wfMetrics.train_test_correlation?.toFixed(3) ?? 'N/A'}</span>
                </div>
                {wfMetrics.train_test_correlation !== null && wfMetrics.train_test_correlation < 0.5 && (
                  <div className="flex items-start gap-2 text-xs text-orange-600">
                    <AlertTriangle className="h-3 w-3 mt-0.5" />
                    Low correlation may indicate overfitting
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Consistency Score</span>
                  <span className="font-medium">{wfMetrics.consistency_score?.toFixed(3) ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Successful Windows</span>
                  <span>{wfMetrics.successful_windows} / {wfMetrics.total_windows}</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Train Sharpe</span>
                  <span className="font-medium">{wfMetrics.avg_train_sharpe?.toFixed(3) ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Test Sharpe</span>
                  <span>{wfMetrics.avg_test_sharpe?.toFixed(3) ?? 'N/A'}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Best Parameters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Optimized Parameters</CardTitle>
            {/* Apply Parameters Button */}
            <div className="flex items-center gap-2">
              {applySuccess && (
                <Badge variant="default" className="bg-green-600">
                  <Check className="h-3 w-3 mr-1" />
                  Applied!
                </Badge>
              )}
              {applyError && (
                <Badge variant="destructive">
                  {applyError}
                </Badge>
              )}
              <Button
                variant="default"
                size="sm"
                onClick={() => applyParamsMutation.mutate(false)}
                disabled={applyParamsMutation.isPending || applySuccess}
              >
                {applyParamsMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Applying...
                  </>
                ) : applySuccess ? (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Applied to Strategy
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Apply to Strategy
                  </>
                )}
              </Button>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            These parameters produced the best optimization results. Click "Apply to Strategy" to update the strategy definition.
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries(result.best_params).map(([key, value]) => (
              <div key={key} className="p-3 rounded-lg border">
                <div className="text-sm text-muted-foreground mb-1">{key}</div>
                <div className="text-lg font-semibold">
                  {typeof value === 'number' ? value.toFixed(4) : value}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

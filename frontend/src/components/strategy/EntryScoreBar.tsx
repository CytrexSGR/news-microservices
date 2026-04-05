import { CheckCircle2, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { ConditionEvaluation } from '@/types/strategy-evaluation';

interface EntryScoreBarProps {
  score: number;          // 0.0 - 1.0
  maxScore: number;       // Maximum possible score
  threshold: number;      // 0.0 - 1.0, threshold for entry
  entryPossible: boolean;
  aggregation: 'all' | 'any' | 'weighted_avg';
  conditions: ConditionEvaluation[];
  className?: string;
}

interface ScoreBreakdown {
  metConditions: ConditionEvaluation[];
  unmetConditions: ConditionEvaluation[];
  metSum: number;
  unmetSum: number;
  total: number;
  percentage: number;
}

function calculateBreakdown(conditions: ConditionEvaluation[]): ScoreBreakdown {
  const met = conditions.filter(c => c.met);
  const unmet = conditions.filter(c => !c.met);

  const metSum = met.reduce((sum, c) => sum + c.confidence, 0);
  const unmetSum = unmet.reduce((sum, c) => sum + c.confidence, 0);
  const total = metSum + unmetSum;

  return {
    metConditions: met,
    unmetConditions: unmet,
    metSum,
    unmetSum,
    total,
    percentage: total > 0 ? (metSum / total) * 100 : 0
  };
}

export function EntryScoreBar({
  score,
  maxScore,
  threshold,
  entryPossible,
  aggregation,
  conditions,
  className
}: EntryScoreBarProps) {
  const scorePercentage = score * 100;
  const thresholdPercentage = threshold * 100;
  const breakdown = aggregation === 'weighted_avg' ? calculateBreakdown(conditions) : null;

  // Determine colors based on entry possibility
  const statusColor = entryPossible ? 'bg-green-500' : 'bg-red-500';
  const statusTextColor = entryPossible ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
  const borderColor = entryPossible ? 'border-green-500/20' : 'border-red-500/20';
  const bgColor = entryPossible ? 'bg-green-500/10' : 'bg-red-500/10';

  return (
    <div className={cn('space-y-3', className)}>
      {/* Progress Bar Section */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            Entry Score: <span className={cn('font-semibold', statusTextColor)}>
              {scorePercentage.toFixed(0)}%
            </span>
          </span>
          <span className="text-xs text-muted-foreground">
            Threshold: {thresholdPercentage.toFixed(0)}%
          </span>
        </div>

        {/* Progress bar with threshold marker */}
        <div className="relative">
          <Progress
            value={scorePercentage}
            className="h-2"
            indicatorClassName={statusColor}
          />

          {/* Threshold marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-gray-700 dark:bg-gray-300"
            style={{ left: `${thresholdPercentage}%` }}
          >
            <div className="absolute -top-1 left-1/2 -translate-x-1/2 text-xs text-gray-700 dark:text-gray-300">
              ▼
            </div>
          </div>
        </div>
      </div>

      {/* Entry Status Badge */}
      <div className="flex items-center gap-2">
        <Badge
          variant={entryPossible ? 'default' : 'destructive'}
          className="font-semibold"
        >
          {entryPossible ? (
            <>
              <CheckCircle2 className="h-3 w-3 mr-1" />
              ENTRY POSSIBLE
            </>
          ) : (
            <>
              <XCircle className="h-3 w-3 mr-1" />
              NO ENTRY
            </>
          )}
        </Badge>
      </div>

      {/* Aggregation Mode Display */}
      <div className={cn('p-3 rounded-lg border text-xs', borderColor, bgColor)}>
        <div className="space-y-1">
          {aggregation === 'all' && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground font-medium">Mode: All Conditions (AND)</span>
              <span className={cn('font-semibold', statusTextColor)}>
                {conditions.filter(c => c.met).length}/{conditions.length} met
              </span>
            </div>
          )}

          {aggregation === 'any' && (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground font-medium">Mode: Any Condition (OR)</span>
              <span className={cn('font-semibold', statusTextColor)}>
                {conditions.filter(c => c.met).length} met (1 required)
              </span>
            </div>
          )}

          {aggregation === 'weighted_avg' && breakdown && (
            <div className="space-y-2">
              <div className="font-medium text-muted-foreground">
                Mode: Weighted Average
              </div>

              <div className="space-y-1 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-green-600 dark:text-green-400">
                    Met conditions:
                  </span>
                  <span className="text-green-600 dark:text-green-400 font-semibold">
                    {breakdown.metConditions.map(c => c.confidence.toFixed(1)).join(' + ')}
                    {' = '}
                    {breakdown.metSum.toFixed(2)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-red-600 dark:text-red-400">
                    Unmet conditions:
                  </span>
                  <span className="text-red-600 dark:text-red-400 font-semibold">
                    {breakdown.unmetConditions.length > 0
                      ? `${breakdown.unmetConditions.map(c => c.confidence.toFixed(1)).join(' + ')} = ${breakdown.unmetSum.toFixed(2)}`
                      : '0.00'
                    }
                  </span>
                </div>

                <div className="border-t border-gray-200 dark:border-gray-700 pt-1 mt-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">Final Score:</span>
                    <span className={cn('font-bold', statusTextColor)}>
                      {breakdown.metSum.toFixed(2)} / {breakdown.total.toFixed(2)} = {breakdown.percentage.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Conditions Quick View */}
      {conditions.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs font-semibold text-muted-foreground">
            Conditions Overview:
          </div>
          <div className="grid gap-1">
            {conditions.map((condition, idx) => (
              <div
                key={idx}
                className={cn(
                  'flex items-center justify-between p-2 rounded text-xs',
                  condition.met
                    ? 'bg-green-500/10 border border-green-500/20'
                    : 'bg-red-500/10 border border-red-500/20'
                )}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {condition.met ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-red-500 flex-shrink-0" />
                  )}
                  <span className="text-muted-foreground truncate" title={condition.description}>
                    {condition.description}
                  </span>
                </div>
                <span className={cn(
                  'font-mono font-semibold ml-2 flex-shrink-0',
                  condition.met
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                )}>
                  {(condition.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

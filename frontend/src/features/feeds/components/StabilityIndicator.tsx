/**
 * Stability Indicator Component
 *
 * Displays geopolitical stability score with visual indicator.
 * Score ranges from -1 (very unstable) to +1 (very stable).
 */

import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StabilityIndicatorProps {
  score: number; // -1 to +1
  escalationPotential?: number; // 0 to 1
  className?: string;
}

export function StabilityIndicator({
  score,
  escalationPotential,
  className,
}: StabilityIndicatorProps) {
  const getStabilityLevel = (score: number) => {
    if (score >= 0.5) return 'Very Stable';
    if (score >= 0.1) return 'Stable';
    if (score >= -0.1) return 'Neutral';
    if (score >= -0.5) return 'Unstable';
    return 'Very Unstable';
  };

  const getColorClass = (score: number) => {
    if (score >= 0.5) return 'text-green-600 bg-green-50 dark:bg-green-900/20';
    if (score >= 0.1) return 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20';
    if (score >= -0.1) return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
    if (score >= -0.5) return 'text-orange-600 bg-orange-50 dark:bg-orange-900/20';
    return 'text-red-600 bg-red-50 dark:bg-red-900/20';
  };

  const getIcon = (score: number) => {
    if (score > 0.1) return TrendingUp;
    if (score < -0.1) return TrendingDown;
    return Minus;
  };

  const Icon = getIcon(score);

  return (
    <div className={cn('inline-flex items-center gap-2', className)}>
      <div
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-medium',
          getColorClass(score)
        )}
      >
        <Icon className="h-4 w-4" />
        <span>{getStabilityLevel(score)}</span>
        <span className="text-xs opacity-70">({score > 0 ? '+' : ''}{score.toFixed(2)})</span>
      </div>

      {escalationPotential !== undefined && escalationPotential > 0.3 && (
        <div
          className={cn(
            'px-2 py-1 rounded-md text-xs font-medium',
            escalationPotential >= 0.7
              ? 'text-red-600 bg-red-50 dark:bg-red-900/20'
              : escalationPotential >= 0.5
              ? 'text-orange-600 bg-orange-50 dark:bg-orange-900/20'
              : 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20'
          )}
        >
          Escalation: {(escalationPotential * 100).toFixed(0)}%
        </div>
      )}
    </div>
  );
}

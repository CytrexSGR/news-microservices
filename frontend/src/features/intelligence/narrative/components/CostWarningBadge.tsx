/**
 * CostWarningBadge - Visual indicator for API costs
 *
 * Displays estimated or actual cost for narrative analysis operations.
 * Helps users understand the cost implications of running analyses.
 */
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { DollarSign, AlertTriangle, Info } from 'lucide-react';
import { formatCost } from '../types/narrative.types';
import { NARRATIVE_ANALYSIS_COST_USD } from '../api/useAnalyzeNarrative';

interface CostWarningBadgeProps {
  /**
   * Actual or estimated cost in USD
   * If not provided, uses the default analysis cost
   */
  cost?: number;
  /**
   * Whether this is an estimated or actual cost
   */
  isEstimate?: boolean;
  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Show warning icon for costs above threshold
   */
  warnThreshold?: number;
  /**
   * Additional CSS classes
   */
  className?: string;
}

export function CostWarningBadge({
  cost,
  isEstimate = true,
  size = 'md',
  warnThreshold = 0.01,
  className = '',
}: CostWarningBadgeProps) {
  const displayCost = cost ?? NARRATIVE_ANALYSIS_COST_USD;
  const isHighCost = displayCost >= warnThreshold;

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const iconSize = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant={isHighCost ? 'destructive' : 'secondary'}
            className={`inline-flex items-center gap-1 ${sizeClasses[size]} ${className}`}
          >
            {isHighCost ? (
              <AlertTriangle className={iconSize[size]} />
            ) : (
              <DollarSign className={iconSize[size]} />
            )}
            <span>{isEstimate ? '~' : ''}{formatCost(displayCost)}</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1">
            <p className="font-medium">
              {isEstimate ? 'Estimated' : 'Actual'} Cost: {formatCost(displayCost)}
            </p>
            <p className="text-xs text-muted-foreground">
              {isEstimate
                ? 'This is an estimate. Actual cost may vary based on text length.'
                : 'This was the actual cost of the operation.'}
            </p>
            {isHighCost && (
              <p className="text-xs text-destructive">
                This operation has a relatively high cost.
              </p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Compact cost indicator for inline use
 */
interface InlineCostProps {
  cost?: number;
  className?: string;
}

export function InlineCost({ cost, className = '' }: InlineCostProps) {
  const displayCost = cost ?? NARRATIVE_ANALYSIS_COST_USD;

  return (
    <span
      className={`inline-flex items-center gap-0.5 text-xs text-muted-foreground ${className}`}
    >
      <DollarSign className="h-3 w-3" />
      <span>{formatCost(displayCost)}</span>
    </span>
  );
}

/**
 * Cost summary card for dashboard
 */
interface CostSummaryProps {
  totalCost: number;
  analysisCount: number;
  period?: string;
  className?: string;
}

export function CostSummary({
  totalCost,
  analysisCount,
  period = 'this month',
  className = '',
}: CostSummaryProps) {
  const avgCost = analysisCount > 0 ? totalCost / analysisCount : 0;

  return (
    <div
      className={`p-4 rounded-lg border bg-secondary/20 space-y-2 ${className}`}
    >
      <div className="flex items-center gap-2 text-sm font-medium">
        <Info className="h-4 w-4 text-muted-foreground" />
        <span>Cost Summary ({period})</span>
      </div>
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold">{formatCost(totalCost)}</div>
          <div className="text-xs text-muted-foreground">Total</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{analysisCount}</div>
          <div className="text-xs text-muted-foreground">Analyses</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{formatCost(avgCost)}</div>
          <div className="text-xs text-muted-foreground">Avg/Analysis</div>
        </div>
      </div>
    </div>
  );
}

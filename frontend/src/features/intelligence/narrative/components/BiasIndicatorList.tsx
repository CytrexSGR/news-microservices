/**
 * BiasIndicatorList - Display bias indicators from analysis
 *
 * Shows individual bias indicators with type, score, and explanation.
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { AlertCircle, Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { BiasIndicator, BiasType } from '../types/narrative.types';

interface BiasIndicatorListProps {
  indicators: BiasIndicator[];
  showExplanations?: boolean;
  compact?: boolean;
  className?: string;
}

export function BiasIndicatorList({
  indicators,
  showExplanations = true,
  compact = false,
  className = '',
}: BiasIndicatorListProps) {
  if (indicators.length === 0) {
    return (
      <div className={`text-center py-6 text-muted-foreground ${className}`}>
        <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No bias indicators detected.</p>
      </div>
    );
  }

  const getBiasTypeColor = (type: BiasType): string => {
    switch (type) {
      case 'political':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'ideological':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'commercial':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'emotional':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'source':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  const getScoreIcon = (score: number) => {
    if (score > 0.3) return <TrendingUp className="h-4 w-4 text-red-500" />;
    if (score < -0.3) return <TrendingDown className="h-4 w-4 text-blue-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  const getScoreColor = (score: number): string => {
    const absScore = Math.abs(score);
    if (absScore > 0.6) return 'text-red-500';
    if (absScore > 0.3) return 'text-orange-500';
    return 'text-gray-500';
  };

  if (compact) {
    return (
      <div className={`space-y-2 ${className}`}>
        {indicators.map((indicator, index) => (
          <div
            key={index}
            className="flex items-center gap-2 p-2 rounded-lg bg-secondary/50"
          >
            <Badge className={`text-xs capitalize ${getBiasTypeColor(indicator.type)}`}>
              {indicator.type}
            </Badge>
            <span className="flex-1 text-sm truncate">{indicator.text}</span>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <span className={`font-mono text-sm ${getScoreColor(indicator.score)}`}>
                    {indicator.score > 0 ? '+' : ''}
                    {indicator.score.toFixed(2)}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{indicator.explanation}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {indicators.map((indicator, index) => (
        <BiasIndicatorCard
          key={index}
          indicator={indicator}
          showExplanation={showExplanations}
        />
      ))}
    </div>
  );
}

interface BiasIndicatorCardProps {
  indicator: BiasIndicator;
  showExplanation?: boolean;
  className?: string;
}

export function BiasIndicatorCard({
  indicator,
  showExplanation = true,
  className = '',
}: BiasIndicatorCardProps) {
  const getBiasTypeColor = (type: BiasType): string => {
    switch (type) {
      case 'political':
        return 'border-l-purple-500';
      case 'ideological':
        return 'border-l-blue-500';
      case 'commercial':
        return 'border-l-yellow-500';
      case 'emotional':
        return 'border-l-red-500';
      case 'source':
        return 'border-l-green-500';
      default:
        return 'border-l-gray-500';
    }
  };

  const getScoreColor = (score: number): string => {
    if (score > 0.3) return 'text-red-500';
    if (score < -0.3) return 'text-blue-500';
    return 'text-gray-500';
  };

  // Convert score to 0-100 for progress bar (0.5 = center)
  const progressValue = ((indicator.score + 1) / 2) * 100;

  return (
    <Card className={`border-l-4 ${getBiasTypeColor(indicator.type)} ${className}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="space-y-1">
            <Badge variant="outline" className="capitalize">
              {indicator.type}
            </Badge>
            <p className="text-sm font-medium mt-1">{indicator.text}</p>
          </div>
          <div className="text-right">
            <div className={`text-xl font-bold ${getScoreColor(indicator.score)}`}>
              {indicator.score > 0 ? '+' : ''}
              {indicator.score.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Score bar */}
        <div className="relative mt-3 mb-2">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Left</span>
            <span>Center</span>
            <span>Right</span>
          </div>
          <div className="h-2 bg-gradient-to-r from-blue-500 via-gray-300 to-red-500 rounded-full relative">
            <div
              className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-gray-700 rounded-full shadow-md"
              style={{ left: `calc(${progressValue}% - 6px)` }}
            />
          </div>
        </div>

        {showExplanation && indicator.explanation && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-start gap-2 text-sm text-muted-foreground">
              <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <p>{indicator.explanation}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Bias type summary showing counts by type
 */
interface BiasTypeSummaryProps {
  indicators: BiasIndicator[];
  className?: string;
}

export function BiasTypeSummary({ indicators, className = '' }: BiasTypeSummaryProps) {
  const typeCounts = indicators.reduce(
    (acc, indicator) => {
      acc[indicator.type] = (acc[indicator.type] || 0) + 1;
      return acc;
    },
    {} as Record<BiasType, number>
  );

  const typeOrder: BiasType[] = ['political', 'ideological', 'commercial', 'emotional', 'source'];

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {typeOrder.map((type) => {
        const count = typeCounts[type] || 0;
        if (count === 0) return null;

        return (
          <Badge key={type} variant="secondary" className="capitalize">
            {type}: {count}
          </Badge>
        );
      })}
    </div>
  );
}

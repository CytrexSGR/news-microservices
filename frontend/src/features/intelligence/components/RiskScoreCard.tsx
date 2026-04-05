/**
 * RiskScoreCard - Current risk level indicator with trend
 *
 * Displays the global risk index with visual gauge and trend line
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getRiskLevel, getRiskColor, getRiskBgColor } from '../types/intelligence.types';

interface RiskScoreCardProps {
  score: number;
  delta?: number;
  label?: string;
  isLoading?: boolean;
}

export function RiskScoreCard({ score, delta = 0, label = 'Global Risk Index', isLoading = false }: RiskScoreCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-5 w-5 rounded" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-12 w-24 mb-2" />
          <Skeleton className="h-3 w-full mb-2" />
          <Skeleton className="h-3 w-20" />
        </CardContent>
      </Card>
    );
  }

  const riskLevel = getRiskLevel(score);
  const riskColor = getRiskColor(score);
  const bgColor = getRiskBgColor(score);

  const getTrendIcon = () => {
    if (delta > 1) return <TrendingUp className="h-4 w-4 text-red-500" />;
    if (delta < -1) return <TrendingDown className="h-4 w-4 text-green-500" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  const getTrendText = () => {
    if (Math.abs(delta) < 0.1) return 'stable';
    return delta > 0 ? `+${(delta ?? 0).toFixed(1)} from yesterday` : `${(delta ?? 0).toFixed(1)} from yesterday`;
  };

  return (
    <Card className={bgColor}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{label}</CardTitle>
        <AlertTriangle className={`h-5 w-5 ${riskColor}`} />
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <span className={`text-4xl font-bold ${riskColor}`}>
            {(score ?? 0).toFixed(1)}
          </span>
          <span className="text-sm text-muted-foreground uppercase">
            {riskLevel}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mt-3 w-full bg-secondary rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              riskLevel === 'low' ? 'bg-green-500' :
              riskLevel === 'moderate' ? 'bg-yellow-500' :
              riskLevel === 'elevated' ? 'bg-orange-500' :
              riskLevel === 'high' ? 'bg-red-500' : 'bg-red-700'
            }`}
            style={{ width: `${Math.min(100, score)}%` }}
          />
        </div>

        {/* Trend indicator */}
        <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
          {getTrendIcon()}
          <span>{getTrendText()}</span>
        </div>
      </CardContent>
    </Card>
  );
}

interface CompactRiskBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

export function CompactRiskBadge({ score, size = 'md' }: CompactRiskBadgeProps) {
  const riskLevel = getRiskLevel(score);
  const riskColor = getRiskColor(score);
  const bgColor = getRiskBgColor(score);

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ${bgColor} ${riskColor} ${sizeClasses[size]}`}>
      <span>{(score ?? 0).toFixed(0)}</span>
      <span className="uppercase text-[0.65em] opacity-70">{riskLevel}</span>
    </span>
  );
}

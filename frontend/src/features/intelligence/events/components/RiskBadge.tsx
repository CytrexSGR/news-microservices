/**
 * RiskBadge Component
 *
 * Displays a risk level badge with appropriate styling
 */
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, AlertCircle, AlertOctagon, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { RiskLevel } from '../types/events.types';
import { getRiskLevelColor, getRiskLevelBgColor } from '../types/events.types';

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'text-xs px-1.5 py-0.5',
  md: 'text-sm px-2 py-1',
  lg: 'text-base px-3 py-1.5',
};

const iconSizes = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
};

function getRiskIcon(level: RiskLevel, size: 'sm' | 'md' | 'lg') {
  const iconClass = iconSizes[size];

  switch (level) {
    case 'critical':
      return <AlertOctagon className={cn(iconClass, 'text-red-500')} />;
    case 'high':
      return <AlertTriangle className={cn(iconClass, 'text-orange-500')} />;
    case 'medium':
      return <AlertCircle className={cn(iconClass, 'text-yellow-500')} />;
    case 'low':
    default:
      return <ShieldCheck className={cn(iconClass, 'text-green-500')} />;
  }
}

export function RiskBadge({
  level,
  score,
  showIcon = true,
  size = 'md',
  className,
}: RiskBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        'inline-flex items-center gap-1 font-medium',
        getRiskLevelBgColor(level),
        getRiskLevelColor(level),
        sizeClasses[size],
        className
      )}
    >
      {showIcon && getRiskIcon(level, size)}
      <span className="capitalize">{level}</span>
      {score !== undefined && (
        <span className="opacity-75">({score.toFixed(0)})</span>
      )}
    </Badge>
  );
}

interface CompactRiskBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function CompactRiskBadge({ score, size = 'md', className }: CompactRiskBadgeProps) {
  const level: RiskLevel =
    score >= 80 ? 'critical' :
    score >= 60 ? 'high' :
    score >= 40 ? 'medium' : 'low';

  return (
    <Badge
      variant="outline"
      className={cn(
        'inline-flex items-center font-mono font-bold',
        getRiskLevelBgColor(level),
        getRiskLevelColor(level),
        sizeClasses[size],
        className
      )}
    >
      {score.toFixed(0)}
    </Badge>
  );
}

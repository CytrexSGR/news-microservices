/**
 * AnalysisStatusBadge - Badge showing analysis status with color coding
 *
 * Displays the current status of an analysis job with appropriate
 * styling and icons.
 */
import { Badge } from '@/components/ui/badge';
import { Clock, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AnalysisStatus } from '../types/analysis.types';
import { getStatusConfig } from '../types/analysis.types';

interface AnalysisStatusBadgeProps {
  status: AnalysisStatus;
  progressPercent?: number;
  showProgress?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const iconMap = {
  Clock,
  Loader2,
  CheckCircle,
  XCircle,
};

export function AnalysisStatusBadge({
  status,
  progressPercent,
  showProgress = true,
  size = 'md',
  className,
}: AnalysisStatusBadgeProps) {
  const config = getStatusConfig(status);
  const IconComponent = iconMap[config.icon as keyof typeof iconMap];

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-0.5',
    lg: 'text-base px-3 py-1',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <Badge
      variant="outline"
      className={cn(
        'border-0 font-medium inline-flex items-center gap-1.5',
        config.bgColor,
        config.color,
        sizeClasses[size],
        className
      )}
    >
      <IconComponent
        className={cn(
          iconSizes[size],
          status === 'processing' && 'animate-spin'
        )}
      />
      <span>{config.label}</span>
      {showProgress && status === 'processing' && progressPercent !== undefined && (
        <span className="ml-1 opacity-75">({progressPercent}%)</span>
      )}
    </Badge>
  );
}

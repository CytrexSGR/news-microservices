/**
 * ResearchStatusBadge Component
 *
 * Displays the status of a research task with appropriate styling:
 * - pending: Yellow, clock icon
 * - processing: Blue, spinning loader
 * - completed: Green, check icon
 * - failed: Red, X icon
 * - cancelled: Gray, slash icon
 */

import {
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Ban,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TaskStatus } from '../types';

interface ResearchStatusBadgeProps {
  status: TaskStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

const STATUS_CONFIG: Record<
  TaskStatus,
  {
    icon: typeof Clock;
    color: string;
    bgColor: string;
    label: string;
    animate?: boolean;
  }
> = {
  pending: {
    icon: Clock,
    color: 'text-yellow-600 dark:text-yellow-400',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    label: 'Pending',
  },
  processing: {
    icon: Loader2,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    label: 'Processing',
    animate: true,
  },
  completed: {
    icon: CheckCircle2,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    label: 'Completed',
  },
  failed: {
    icon: XCircle,
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    label: 'Failed',
  },
  cancelled: {
    icon: Ban,
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-900/30',
    label: 'Cancelled',
  },
};

const SIZE_CONFIG = {
  sm: {
    container: 'px-2 py-0.5 text-xs',
    icon: 'h-3 w-3',
    gap: 'gap-1',
  },
  md: {
    container: 'px-2.5 py-1 text-sm',
    icon: 'h-3.5 w-3.5',
    gap: 'gap-1.5',
  },
  lg: {
    container: 'px-3 py-1.5 text-base',
    icon: 'h-4 w-4',
    gap: 'gap-2',
  },
};

export function ResearchStatusBadge({
  status,
  size = 'md',
  showLabel = true,
  className,
}: ResearchStatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const sizeConfig = SIZE_CONFIG[size];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        config.color,
        config.bgColor,
        sizeConfig.container,
        sizeConfig.gap,
        className
      )}
    >
      <Icon
        className={cn(sizeConfig.icon, config.animate && 'animate-spin')}
      />
      {showLabel && <span>{config.label}</span>}
    </span>
  );
}

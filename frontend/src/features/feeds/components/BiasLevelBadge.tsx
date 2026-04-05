/**
 * Bias Level Badge Component
 *
 * Displays the bias detection level with color-coded severity:
 * - minimal: Green
 * - low: Light green
 * - moderate: Yellow/Orange
 * - high: Orange/Red
 * - extreme: Red
 */

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface BiasLevelBadgeProps {
  level: 'minimal' | 'low' | 'moderate' | 'high' | 'extreme';
  className?: string;
}

export function BiasLevelBadge({ level, className }: BiasLevelBadgeProps) {
  const getColorClass = (level: string) => {
    switch (level) {
      case 'minimal':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'low':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'extreme':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  const getLabel = (level: string) => {
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  return (
    <Badge
      variant="outline"
      className={cn(getColorClass(level), 'font-medium', className)}
    >
      Bias: {getLabel(level)}
    </Badge>
  );
}

/**
 * Priority Score Badge Component
 *
 * Displays the triage priority score with color-coded severity:
 * - 0-30: Low priority (gray)
 * - 30-60: Medium priority (blue)
 * - 60-80: High priority (orange)
 * - 80-100: Critical priority (red)
 */

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface PriorityScoreBadgeProps {
  score: number;
  className?: string;
}

export function PriorityScoreBadge({ score, className }: PriorityScoreBadgeProps) {
  const getVariant = (score: number) => {
    if (score >= 80) return 'destructive'; // Critical
    if (score >= 60) return 'default'; // High (will style as orange)
    if (score >= 30) return 'secondary'; // Medium
    return 'outline'; // Low
  };

  const getColorClass = (score: number) => {
    if (score >= 80) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    if (score >= 60) return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    if (score >= 30) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
  };

  const getLabel = (score: number) => {
    if (score >= 80) return 'Critical';
    if (score >= 60) return 'High';
    if (score >= 30) return 'Medium';
    return 'Low';
  };

  return (
    <Badge
      variant={getVariant(score)}
      className={cn(getColorClass(score), 'font-semibold', className)}
    >
      {getLabel(score)} ({score})
    </Badge>
  );
}

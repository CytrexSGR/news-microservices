import { cn } from '@/lib/utils';

interface HealthScoreBadgeProps {
  score: number;
  className?: string;
}

export function HealthScoreBadge({ score, className }: HealthScoreBadgeProps) {
  const getColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        getColor(score),
        className
      )}
    >
      {score.toFixed(1)}
    </span>
  );
}

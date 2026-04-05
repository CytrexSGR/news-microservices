import { cn } from '@/lib/utils';

interface QualityScoreBadgeProps {
  score: number | null | undefined;
  className?: string;
  showLabel?: boolean;
}

export function QualityScoreBadge({ score, className, showLabel = false }: QualityScoreBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span
        className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
          'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
          className
        )}
      >
        Not assessed
      </span>
    );
  }

  const getColor = (score: number) => {
    if (score >= 85) return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    if (score >= 70) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (score >= 50) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
  };

  const getLabel = (score: number) => {
    if (score >= 85) return 'Premium';
    if (score >= 70) return 'Trusted';
    if (score >= 50) return 'Moderate';
    return 'Limited';
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        getColor(score),
        className
      )}
      title={`Quality Score: ${score}/100 (${getLabel(score)})`}
    >
      {showLabel ? `${getLabel(score)} (${score})` : score}
    </span>
  );
}

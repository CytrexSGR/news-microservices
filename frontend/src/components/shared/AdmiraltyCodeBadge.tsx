/**
 * AdmiraltyCodeBadge Component
 *
 * Displays Admiralty Code rating (A-F) as a colored badge.
 *
 * NATO Admiralty Code System:
 * - A: Completely Reliable (green)
 * - B: Usually Reliable (blue)
 * - C: Fairly Reliable (yellow)
 * - D: Not Usually Reliable (orange)
 * - E: Unreliable (red)
 * - F: Cannot Be Judged (gray)
 */
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface AdmiraltyCodeData {
  code: 'A' | 'B' | 'C' | 'D' | 'E' | 'F';
  label: string;
  color: string;
}

export interface AdmiraltyCodeBadgeProps {
  admiraltyCode: AdmiraltyCodeData | null;
  showLabel?: boolean;
  className?: string;
}

// Color mapping from backend color names to Tailwind classes
const colorMap: Record<string, string> = {
  green: 'bg-green-500 hover:bg-green-600 border-green-600',
  blue: 'bg-blue-500 hover:bg-blue-600 border-blue-600',
  yellow: 'bg-yellow-500 hover:bg-yellow-600 border-yellow-600 text-gray-900',
  orange: 'bg-orange-500 hover:bg-orange-600 border-orange-600',
  red: 'bg-red-500 hover:bg-red-600 border-red-600',
  gray: 'bg-gray-500 hover:bg-gray-600 border-gray-600',
};

export function AdmiraltyCodeBadge({
  admiraltyCode,
  showLabel = true,
  className,
}: AdmiraltyCodeBadgeProps) {
  if (!admiraltyCode) {
    return null;
  }

  const { code, label, color } = admiraltyCode;
  const colorClass = colorMap[color] || colorMap.gray;

  return (
    <Badge
      className={cn(
        'font-mono text-white border-transparent',
        colorClass,
        className
      )}
      title={label}
    >
      {showLabel ? `${code}: ${label}` : code}
    </Badge>
  );
}

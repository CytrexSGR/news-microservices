/**
 * SourceCredibilityBadge Component
 *
 * Displays the credibility tier and reputation score for a source.
 */

import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { CredibilityTier } from '@/types/source'
import { getTierColor, getTierLabel } from '@/types/source'
import { cn } from '@/lib/utils'

interface SourceCredibilityBadgeProps {
  tier?: CredibilityTier
  score?: number
  showScore?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function SourceCredibilityBadge({
  tier,
  score,
  showScore = true,
  size = 'md',
  className,
}: SourceCredibilityBadgeProps) {
  const color = getTierColor(tier)
  const label = getTierLabel(tier)

  const colorClasses: Record<string, string> = {
    green: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-400',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-400',
    red: 'bg-red-100 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-400',
    gray: 'bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800 dark:text-gray-400',
  }

  const sizeClasses: Record<string, string> = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  }

  const tierShortLabel: Record<string, string> = {
    tier_1: 'T1',
    tier_2: 'T2',
    tier_3: 'T3',
    unknown: '?',
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className={cn(
              'font-medium border',
              colorClasses[color],
              sizeClasses[size],
              className
            )}
          >
            <span className="font-semibold">{tier ? tierShortLabel[tier] : '?'}</span>
            {showScore && score !== undefined && (
              <span className="ml-1 opacity-80">{score}</span>
            )}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-sm">
            <p className="font-medium">{label}</p>
            {score !== undefined && (
              <p className="text-muted-foreground">Reputation Score: {score}/100</p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

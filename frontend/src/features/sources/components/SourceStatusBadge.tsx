/**
 * SourceStatusBadge Component
 *
 * Displays the status of a source (active, inactive, blocked).
 */

import { Badge } from '@/components/ui/badge'
import type { SourceStatus, ScrapeStatus } from '@/types/source'
import { cn } from '@/lib/utils'

interface SourceStatusBadgeProps {
  status: SourceStatus
  className?: string
}

export function SourceStatusBadge({ status, className }: SourceStatusBadgeProps) {
  const statusConfig: Record<SourceStatus, { label: string; className: string }> = {
    active: {
      label: 'Active',
      className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    },
    inactive: {
      label: 'Inactive',
      className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
    },
    blocked: {
      label: 'Blocked',
      className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    },
  }

  const config = statusConfig[status] || statusConfig.inactive

  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}

interface ScrapeStatusBadgeProps {
  status: ScrapeStatus
  className?: string
}

export function ScrapeStatusBadge({ status, className }: ScrapeStatusBadgeProps) {
  const statusConfig: Record<ScrapeStatus, { label: string; className: string }> = {
    working: {
      label: 'Working',
      className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    },
    degraded: {
      label: 'Degraded',
      className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    },
    blocked: {
      label: 'Blocked',
      className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    },
    unsupported: {
      label: 'Unsupported',
      className: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    },
    unknown: {
      label: 'Unknown',
      className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
    },
  }

  const config = statusConfig[status] || statusConfig.unknown

  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}

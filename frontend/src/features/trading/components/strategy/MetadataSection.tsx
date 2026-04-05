/**
 * MetadataSection Component
 *
 * Displays strategy metadata:
 * - Name, version, description
 * - Created/updated dates
 * - Public/private status
 */

import { Badge } from '@/components/ui/badge'
import type { Strategy } from '@/types/strategy'

interface MetadataSectionProps {
  strategy: Strategy
}

export function MetadataSection({ strategy }: MetadataSectionProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-lg font-semibold">{strategy.name}</h3>
        <p className="text-sm text-muted-foreground">Version {strategy.version}</p>
      </div>

      {strategy.definition.description && (
        <p className="text-sm text-muted-foreground">{strategy.definition.description}</p>
      )}

      <div className="flex gap-4 text-xs text-muted-foreground">
        <span>Created: {formatDate(strategy.created_at)}</span>
        <span>Updated: {formatDate(strategy.updated_at)}</span>
      </div>

      <div>
        <Badge variant={strategy.is_public ? 'default' : 'secondary'}>
          {strategy.is_public ? 'Public' : 'Private'}
        </Badge>
      </div>
    </div>
  )
}

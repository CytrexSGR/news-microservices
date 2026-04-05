/**
 * Entity Type Icon Component
 *
 * Displays icons for different entity types from entity extraction.
 */

import type { EntityTypeV2 } from '../types/analysisV2';
import { cn } from '@/lib/utils';
import {
  User,
  Building2,
  MapPin,
  Calendar,
  Zap,
  DollarSign,
  Package,
  Scale,
  Cpu,
} from 'lucide-react';

interface EntityTypeIconProps {
  type: EntityTypeV2;
  className?: string;
  showLabel?: boolean;
}

const ENTITY_TYPE_CONFIG: Record<
  EntityTypeV2,
  { icon: React.ComponentType<{ className?: string }>; color: string; label: string }
> = {
  PERSON: { icon: User, color: 'text-blue-500', label: 'Person' },
  ORGANIZATION: { icon: Building2, color: 'text-purple-500', label: 'Organization' },
  LOCATION: { icon: MapPin, color: 'text-green-500', label: 'Location' },
  DATE: { icon: Calendar, color: 'text-orange-500', label: 'Date' },
  EVENT: { icon: Zap, color: 'text-red-500', label: 'Event' },
  MONETARY_VALUE: { icon: DollarSign, color: 'text-emerald-500', label: 'Money' },
  PRODUCT: { icon: Package, color: 'text-yellow-500', label: 'Product' },
  LAW: { icon: Scale, color: 'text-indigo-500', label: 'Law' },
  TECHNOLOGY: { icon: Cpu, color: 'text-cyan-500', label: 'Technology' },
};

export function EntityTypeIcon({ type, className, showLabel = false }: EntityTypeIconProps) {
  const config = ENTITY_TYPE_CONFIG[type];
  const IconComponent = config.icon;

  return (
    <div className={cn('flex items-center gap-1', className)} title={config.label}>
      <IconComponent className={cn('h-4 w-4', config.color)} />
      {showLabel && <span className="text-xs text-muted-foreground">{config.label}</span>}
    </div>
  );
}

interface EntityCountBadgeProps {
  entities: Array<{ entity_type: EntityTypeV2 }>;
  maxTypes?: number;
  className?: string;
}

export function EntityCountBadge({ entities, maxTypes = 3, className }: EntityCountBadgeProps) {
  // Count entities by type
  const typeCounts = entities.reduce((acc, entity) => {
    acc[entity.entity_type] = (acc[entity.entity_type] || 0) + 1;
    return acc;
  }, {} as Record<EntityTypeV2, number>);

  // Sort by count and take top N
  const topTypes = Object.entries(typeCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, maxTypes);

  if (topTypes.length === 0) {
    return null;
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {topTypes.map(([type, count]) => (
        <div key={type} className="flex items-center gap-1 text-sm">
          <EntityTypeIcon type={type as EntityTypeV2} />
          <span className="text-muted-foreground font-medium">{count}</span>
        </div>
      ))}
    </div>
  );
}

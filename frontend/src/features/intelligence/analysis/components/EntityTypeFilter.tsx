/**
 * EntityTypeFilter - Filter entities by type
 *
 * Provides a toggle group for filtering entities by their type.
 * Shows counts for each entity type.
 */
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import {
  User,
  Building2,
  MapPin,
  Calendar,
  Hash,
  Package,
  DollarSign,
  CalendarDays,
  Percent,
  ListOrdered,
  Scale,
  Palette,
  Tag,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { EntityType } from '../types/analysis.types';
import { getEntityTypeConfig } from '../types/analysis.types';

interface EntityTypeFilterProps {
  entityTypes: EntityType[];
  entityCounts: Record<EntityType, number>;
  selectedTypes: EntityType[];
  onSelectionChange: (types: EntityType[]) => void;
  showCounts?: boolean;
  multiSelect?: boolean;
  className?: string;
}

const iconMap: Record<string, React.ElementType> = {
  User,
  Building2,
  MapPin,
  Calendar,
  Hash,
  Package,
  DollarSign,
  CalendarDays,
  Percent,
  ListOrdered,
  Scale,
  Palette,
  Tag,
};

export function EntityTypeFilter({
  entityTypes,
  entityCounts,
  selectedTypes,
  onSelectionChange,
  showCounts = true,
  multiSelect = true,
  className,
}: EntityTypeFilterProps) {
  const [hoveredType, setHoveredType] = useState<EntityType | null>(null);

  const handleTypeClick = (type: EntityType) => {
    if (multiSelect) {
      if (selectedTypes.includes(type)) {
        onSelectionChange(selectedTypes.filter((t) => t !== type));
      } else {
        onSelectionChange([...selectedTypes, type]);
      }
    } else {
      if (selectedTypes.includes(type)) {
        onSelectionChange([]);
      } else {
        onSelectionChange([type]);
      }
    }
  };

  const handleClearAll = () => {
    onSelectionChange([]);
  };

  const handleSelectAll = () => {
    onSelectionChange([...entityTypes]);
  };

  if (entityTypes.length === 0) {
    return null;
  }

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          Filter by Entity Type
        </span>
        <div className="flex gap-2">
          {selectedTypes.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearAll}
              className="h-6 px-2 text-xs"
            >
              <X className="h-3 w-3 mr-1" />
              Clear
            </Button>
          )}
          {selectedTypes.length < entityTypes.length && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSelectAll}
              className="h-6 px-2 text-xs"
            >
              Select All
            </Button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {entityTypes.map((type) => {
          const config = getEntityTypeConfig(type);
          const IconComponent = iconMap[config.icon] || Tag;
          const isSelected = selectedTypes.includes(type);
          const count = entityCounts[type] || 0;

          return (
            <Button
              key={type}
              variant={isSelected ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleTypeClick(type)}
              onMouseEnter={() => setHoveredType(type)}
              onMouseLeave={() => setHoveredType(null)}
              className={cn(
                'h-8 px-3 transition-all',
                isSelected && config.bgColor,
                isSelected && config.color,
                !isSelected && 'hover:bg-accent'
              )}
            >
              <IconComponent className="h-3.5 w-3.5 mr-1.5" />
              <span className="text-xs">{config.label}</span>
              {showCounts && (
                <Badge
                  variant="secondary"
                  className={cn(
                    'ml-1.5 h-5 px-1.5 text-xs',
                    isSelected && 'bg-white/20'
                  )}
                >
                  {count}
                </Badge>
              )}
            </Button>
          );
        })}
      </div>

      {selectedTypes.length > 0 && (
        <div className="text-xs text-muted-foreground">
          Showing {selectedTypes.length} of {entityTypes.length} types
          ({selectedTypes.reduce((sum, type) => sum + (entityCounts[type] || 0), 0)} entities)
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for inline use
 */
export function EntityTypeFilterCompact({
  entityTypes,
  selectedTypes,
  onSelectionChange,
  className,
}: Omit<EntityTypeFilterProps, 'entityCounts' | 'showCounts'> & {
  entityCounts?: Record<EntityType, number>;
}) {
  return (
    <div className={cn('flex flex-wrap gap-1', className)}>
      {entityTypes.map((type) => {
        const config = getEntityTypeConfig(type);
        const IconComponent = iconMap[config.icon] || Tag;
        const isSelected = selectedTypes.includes(type);

        return (
          <button
            key={type}
            onClick={() => {
              if (isSelected) {
                onSelectionChange(selectedTypes.filter((t) => t !== type));
              } else {
                onSelectionChange([...selectedTypes, type]);
              }
            }}
            className={cn(
              'inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium transition-all',
              isSelected
                ? cn(config.bgColor, config.color)
                : 'bg-secondary text-secondary-foreground hover:bg-accent'
            )}
          >
            <IconComponent className="h-3 w-3" />
            {config.label}
          </button>
        );
      })}
    </div>
  );
}

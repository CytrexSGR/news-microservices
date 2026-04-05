/**
 * EntityExtractionView - Display extracted entities grouped by type
 *
 * Shows entities in a structured view with filtering, sorting, and
 * confidence indicators.
 */
import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
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
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ArrowUpDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AnalysisEntity, EntityType } from '../types/analysis.types';
import { getEntityTypeConfig } from '../types/analysis.types';
import { EntityTypeFilter } from './EntityTypeFilter';

interface EntityExtractionViewProps {
  entities: AnalysisEntity[];
  isLoading?: boolean;
  extractedAt?: string;
  showFilters?: boolean;
  showConfidence?: boolean;
  maxInitialItems?: number;
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

type SortKey = 'name' | 'confidence' | 'type';
type SortOrder = 'asc' | 'desc';

export function EntityExtractionView({
  entities,
  isLoading = false,
  extractedAt,
  showFilters = true,
  showConfidence = true,
  maxInitialItems = 20,
  className,
}: EntityExtractionViewProps) {
  const [selectedTypes, setSelectedTypes] = useState<EntityType[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>('confidence');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [showAll, setShowAll] = useState(false);

  // Calculate entity statistics
  const entityTypes = useMemo(() => {
    const types = new Set(entities.map((e) => e.type));
    return Array.from(types) as EntityType[];
  }, [entities]);

  const entityCounts = useMemo(() => {
    return entities.reduce(
      (acc, entity) => {
        acc[entity.type] = (acc[entity.type] || 0) + 1;
        return acc;
      },
      {} as Record<EntityType, number>
    );
  }, [entities]);

  // Filter and sort entities
  const filteredEntities = useMemo(() => {
    let result = [...entities];

    // Apply type filter
    if (selectedTypes.length > 0) {
      result = result.filter((e) => selectedTypes.includes(e.type));
    }

    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortKey) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'confidence':
          comparison = a.confidence - b.confidence;
          break;
        case 'type':
          comparison = a.type.localeCompare(b.type);
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [entities, selectedTypes, sortKey, sortOrder]);

  // Apply display limit
  const displayedEntities = showAll
    ? filteredEntities
    : filteredEntities.slice(0, maxInitialItems);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.7) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-60" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-5 w-16" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (entities.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Extracted Entities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No entities extracted yet. Run analysis to extract entities.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Extracted Entities
              <Badge variant="secondary">{entities.length}</Badge>
            </CardTitle>
            {extractedAt && (
              <CardDescription>
                Extracted {new Date(extractedAt).toLocaleString()}
              </CardDescription>
            )}
          </div>

          {/* Sort controls */}
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleSort('name')}
              className={cn(
                'h-8 px-2',
                sortKey === 'name' && 'bg-accent'
              )}
            >
              Name
              {sortKey === 'name' && (
                sortOrder === 'asc' ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleSort('confidence')}
              className={cn(
                'h-8 px-2',
                sortKey === 'confidence' && 'bg-accent'
              )}
            >
              Confidence
              {sortKey === 'confidence' && (
                sortOrder === 'asc' ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Filters */}
        {showFilters && entityTypes.length > 1 && (
          <EntityTypeFilter
            entityTypes={entityTypes}
            entityCounts={entityCounts}
            selectedTypes={selectedTypes}
            onSelectionChange={setSelectedTypes}
          />
        )}

        {/* Entity list */}
        <div className="space-y-2">
          {displayedEntities.map((entity, idx) => {
            const config = getEntityTypeConfig(entity.type);
            const IconComponent = iconMap[config.icon] || Tag;

            return (
              <div
                key={`${entity.name}-${entity.type}-${idx}`}
                className={cn(
                  'flex items-center gap-3 p-3 rounded-lg border',
                  'hover:bg-accent/50 transition-colors'
                )}
              >
                {/* Entity type icon */}
                <div
                  className={cn(
                    'flex items-center justify-center w-8 h-8 rounded-full',
                    config.bgColor
                  )}
                >
                  <IconComponent className={cn('h-4 w-4', config.color)} />
                </div>

                {/* Entity details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{entity.name}</span>
                    {entity.wikidata_id && (
                      <a
                        href={`https://www.wikidata.org/wiki/${entity.wikidata_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-primary"
                      >
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline" className={cn('border-0 text-xs', config.bgColor, config.color)}>
                      {config.label}
                    </Badge>
                    {entity.start_offset !== undefined && entity.end_offset !== undefined && (
                      <span>Position: {entity.start_offset}-{entity.end_offset}</span>
                    )}
                  </div>
                </div>

                {/* Confidence */}
                {showConfidence && (
                  <div className="text-right">
                    <span className={cn('font-mono text-sm', getConfidenceColor(entity.confidence))}>
                      {formatConfidence(entity.confidence)}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Show more/less button */}
        {filteredEntities.length > maxInitialItems && (
          <div className="flex justify-center pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  Show All ({filteredEntities.length - maxInitialItems} more)
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

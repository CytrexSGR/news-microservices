/**
 * EntityClustersTable - Table of entity clusters by type
 *
 * Displays entities with their alias counts and Wikidata linking status.
 */
import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  User,
  Building2,
  MapPin,
  Calendar,
  Package,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Layers,
} from 'lucide-react';
import { useEntityClusters } from '../api/useEntityClusters';
import type { EntityType, EntityCluster } from '../types/entities.types';
import { ENTITY_TYPE_CONFIGS, getEntityTypeConfig } from '../types/entities.types';

interface EntityClustersTableProps {
  initialType?: EntityType;
  onEntityClick?: (entity: EntityCluster) => void;
  className?: string;
}

const EntityTypeIcon = ({ type }: { type: EntityType }) => {
  const config = getEntityTypeConfig(type);
  const iconProps = { className: `h-4 w-4 ${config.color}` };

  switch (type) {
    case 'PERSON':
      return <User {...iconProps} />;
    case 'ORGANIZATION':
      return <Building2 {...iconProps} />;
    case 'LOCATION':
      return <MapPin {...iconProps} />;
    case 'EVENT':
      return <Calendar {...iconProps} />;
    case 'PRODUCT':
      return <Package {...iconProps} />;
    default:
      return <HelpCircle {...iconProps} />;
  }
};

export function EntityClustersTable({
  initialType,
  onEntityClick,
  className,
}: EntityClustersTableProps) {
  const [selectedType, setSelectedType] = useState<EntityType | 'ALL'>(initialType || 'ALL');

  const { data, isLoading, isError, error } = useEntityClusters({
    type: selectedType === 'ALL' ? undefined : selectedType,
    limit: 50,
    refetchInterval: 60000,
  });

  const entities = data?.top_entities_by_aliases || [];

  if (isError) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Entity Clusters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-destructive/10 rounded-lg text-destructive">
            Failed to load entity clusters: {error?.message}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Layers className="h-5 w-5" />
              Entity Clusters
            </CardTitle>
            <CardDescription>Top entities by alias/variant count</CardDescription>
          </div>
          <Select
            value={selectedType}
            onValueChange={(value) => setSelectedType(value as EntityType | 'ALL')}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Types</SelectItem>
              {ENTITY_TYPE_CONFIGS.filter((c) => !['OTHER', 'MISC', 'NOT_APPLICABLE'].includes(c.type)).map(
                (config) => (
                  <SelectItem key={config.type} value={config.type}>
                    {config.label}
                  </SelectItem>
                )
              )}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-8 w-8 rounded" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        ) : entities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No entities found for the selected type
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Entity</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-center">Aliases</TableHead>
                <TableHead className="text-center">Wikidata</TableHead>
                <TableHead className="w-10"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entities.map((entity, idx) => (
                <TableRow
                  key={`${entity.canonical_name}-${idx}`}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onEntityClick?.(entity)}
                >
                  <TableCell className="font-medium">{entity.canonical_name}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <EntityTypeIcon type={entity.entity_type} />
                      <span className="text-sm text-muted-foreground">
                        {getEntityTypeConfig(entity.entity_type).label}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary">{entity.alias_count}</Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    {entity.wikidata_linked && entity.canonical_id ? (
                      <a
                        href={`https://www.wikidata.org/wiki/${entity.canonical_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-blue-500 hover:underline"
                      >
                        {entity.canonical_id}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * EntityClustersPage - Clusters by type page
 *
 * Displays all entity clusters with filtering by type.
 */
import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Layers, Filter, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { EntityClustersTable } from '../components/EntityClustersTable';
import { CanonStatsCard } from '../components/CanonStatsCard';
import type { EntityType, EntityCluster } from '../types/entities.types';
import { ENTITY_TYPE_CONFIGS } from '../types/entities.types';

interface EntityClustersPageProps {
  onEntitySelect?: (entity: EntityCluster) => void;
  showBackButton?: boolean;
}

export function EntityClustersPage({ onEntitySelect, showBackButton }: EntityClustersPageProps) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialType = searchParams.get('type') as EntityType | null;

  const [selectedType, setSelectedType] = useState<EntityType | undefined>(
    initialType || undefined
  );

  const handleTypeChange = (value: string) => {
    const type = value === 'ALL' ? undefined : (value as EntityType);
    setSelectedType(type);
    if (type) {
      setSearchParams({ type });
    } else {
      setSearchParams({});
    }
  };

  const handleEntityClick = (entity: EntityCluster) => {
    if (onEntitySelect) {
      onEntitySelect(entity);
    } else {
      // Navigate to entity details page
      navigate(
        `/intelligence/entities/${encodeURIComponent(entity.canonical_name)}?type=${entity.entity_type}`
      );
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {showBackButton && (
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Layers className="h-8 w-8" />
              Entity Clusters
            </h1>
            <p className="text-muted-foreground mt-1">
              Browse and explore canonical entities grouped by type
            </p>
          </div>
        </div>

        {/* Type Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select
            value={selectedType || 'ALL'}
            onValueChange={handleTypeChange}
          >
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Types</SelectItem>
              {ENTITY_TYPE_CONFIGS.filter(
                (c) => !['OTHER', 'MISC', 'NOT_APPLICABLE'].includes(c.type)
              ).map((config) => (
                <SelectItem key={config.type} value={config.type}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Entity Clusters Table */}
        <div className="lg:col-span-3">
          <EntityClustersTable
            initialType={selectedType}
            onEntityClick={handleEntityClick}
          />
        </div>

        {/* Sidebar - Stats */}
        <div className="lg:col-span-1">
          <CanonStatsCard />
        </div>
      </div>
    </div>
  );
}

/**
 * TopNarrativeEntitiesWidget - Display entities ranked by narrative frame involvement
 *
 * Shows entities with the most frame mentions, filterable by frame type.
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Users,
  TrendingUp,
  Flame,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import { useTopNarrativeEntities, useMostControversialEntities } from '../api/kg';
import type {
  TopNarrativeEntity,
  NarrativeType,
} from '../types/narrative.types';
import {
  getNarrativeColor,
  getNarrativeBgColor,
  getTensionColor,
} from '../types/narrative.types';

interface TopNarrativeEntitiesWidgetProps {
  title?: string;
  limit?: number;
  showFrameFilter?: boolean;
  showControversial?: boolean;
  onEntityClick?: (entity: TopNarrativeEntity) => void;
  className?: string;
}

export function TopNarrativeEntitiesWidget({
  title = 'Top Narrative Entities',
  limit = 10,
  showFrameFilter = true,
  showControversial = false,
  onEntityClick,
  className = '',
}: TopNarrativeEntitiesWidgetProps) {
  const [frameFilter, setFrameFilter] = useState<NarrativeType | 'all'>('all');
  const [sortBy, setSortBy] = useState<'frame_mentions' | 'avg_tension'>('frame_mentions');

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useTopNarrativeEntities(
    {
      frame_type: frameFilter === 'all' ? undefined : frameFilter,
      limit,
      sort_by: sortBy,
      min_mentions: 2,
    }
  );

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        {showFrameFilter && (
          <div className="flex gap-2 mt-2">
            <Select
              value={frameFilter}
              onValueChange={(value) => setFrameFilter(value as NarrativeType | 'all')}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="All frames" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Frames</SelectItem>
                <SelectItem value="conflict">Conflict</SelectItem>
                <SelectItem value="cooperation">Cooperation</SelectItem>
                <SelectItem value="crisis">Crisis</SelectItem>
                <SelectItem value="progress">Progress</SelectItem>
                <SelectItem value="decline">Decline</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={sortBy}
              onValueChange={(value) => setSortBy(value as 'frame_mentions' | 'avg_tension')}
            >
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="frame_mentions">Most Mentions</SelectItem>
                <SelectItem value="avg_tension">Highest Tension</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {/* Loading State */}
        {isLoading && <EntitiesListSkeleton count={5} />}

        {/* Error State */}
        {error && (
          <div className="text-center py-6 text-muted-foreground">
            <p>{error.message}</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        )}

        {/* Entities List */}
        {data && !isLoading && (
          <div className="space-y-2">
            {data.entities.length > 0 ? (
              data.entities.map((entity, index) => (
                <EntityRankCard
                  key={entity.entity_id}
                  rank={index + 1}
                  entity={entity}
                  onClick={() => onEntityClick?.(entity)}
                />
              ))
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                No entities found with the selected filters.
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Entity Rank Card
 */
interface EntityRankCardProps {
  rank: number;
  entity: TopNarrativeEntity;
  onClick?: () => void;
}

function EntityRankCard({ rank, entity, onClick }: EntityRankCardProps) {
  return (
    <div
      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors hover:bg-muted/80 ${getNarrativeBgColor(
        entity.dominant_frame
      )}`}
      onClick={onClick}
    >
      {/* Rank */}
      <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-background text-sm font-bold">
        {rank}
      </div>

      {/* Entity Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{entity.entity_name}</span>
          <Badge variant="outline" className="text-xs capitalize">
            {entity.entity_type}
          </Badge>
        </div>
        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
          <span>{entity.frame_mentions} frames</span>
          <span>|</span>
          <span>{entity.article_count} articles</span>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={getNarrativeColor(entity.dominant_frame)}>
          {entity.dominant_frame}
        </Badge>
        {entity.avg_tension > 0.5 && (
          <Badge className={`${getTensionColor(entity.avg_tension)} bg-opacity-20`}>
            <Flame className="h-3 w-3 mr-1" />
            {(entity.avg_tension * 100).toFixed(0)}%
          </Badge>
        )}
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </div>
    </div>
  );
}

/**
 * Loading Skeleton
 */
function EntitiesListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {[...Array(count)].map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}

/**
 * Compact version for sidebars/dashboards
 */
export function CompactTopEntities({
  limit = 5,
  onEntityClick,
  className = '',
}: {
  limit?: number;
  onEntityClick?: (entity: TopNarrativeEntity) => void;
  className?: string;
}) {
  const { data, isLoading } = useTopNarrativeEntities({ limit, min_mentions: 3 });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          Top Entities
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {data && data.entities.length > 0 ? (
          <div className="space-y-1">
            {data.entities.map((entity, index) => (
              <div
                key={entity.entity_id}
                className="flex items-center justify-between p-2 hover:bg-muted/50 rounded cursor-pointer"
                onClick={() => onEntityClick?.(entity)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-4">
                    {index + 1}.
                  </span>
                  <span className="text-sm truncate">{entity.entity_name}</span>
                </div>
                <Badge variant="secondary" className="text-xs">
                  {entity.frame_mentions}
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">
            No entity data available
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Most Controversial Entities Widget
 */
export function ControversialEntitiesWidget({
  limit = 5,
  onEntityClick,
  className = '',
}: {
  limit?: number;
  onEntityClick?: (entity: TopNarrativeEntity) => void;
  className?: string;
}) {
  const { data, isLoading, refetch } = useMostControversialEntities(limit);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Flame className="h-4 w-4 text-orange-500" />
            Most Controversial
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {data && data.entities.length > 0 ? (
          <div className="space-y-2">
            {data.entities.map((entity) => (
              <div
                key={entity.entity_id}
                className={`flex items-center justify-between p-2 rounded cursor-pointer ${getTensionColor(
                  entity.avg_tension
                ).replace('text-', 'bg-')}/10 hover:opacity-80`}
                onClick={() => onEntityClick?.(entity)}
              >
                <span className="text-sm font-medium truncate">
                  {entity.entity_name}
                </span>
                <Badge className={getTensionColor(entity.avg_tension)}>
                  {(entity.avg_tension * 100).toFixed(0)}%
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">
            No controversial entities found
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * EntityNarrativePanel - Entity-centric narrative analysis from Knowledge Graph
 *
 * Provides entity search, framing analysis, and co-occurrence network visualization.
 */
import { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import {
  AlertCircle,
  Search,
  Users,
  Network,
  TrendingUp,
  Loader2,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import {
  useEntityFramingAnalysis,
  useEntityCooccurrences,
} from '../api/kg';
import type {
  EntityFramingAnalysis,
  NarrativeCooccurrence,
  NarrativeType,
} from '../types/narrative.types';
import {
  getNarrativeColor,
  getNarrativeBgColor,
  getBiasColor,
  getBiasLabel,
} from '../types/narrative.types';

interface EntityNarrativePanelProps {
  initialEntity?: string;
  onEntitySelect?: (entityName: string) => void;
  showCooccurrences?: boolean;
  className?: string;
}

export function EntityNarrativePanel({
  initialEntity = '',
  onEntitySelect,
  showCooccurrences = true,
  className = '',
}: EntityNarrativePanelProps) {
  const [searchQuery, setSearchQuery] = useState(initialEntity);
  const [selectedEntity, setSelectedEntity] = useState(initialEntity);

  // Fetch entity framing analysis
  const {
    data: framingData,
    isLoading: isLoadingFraming,
    error: framingError,
    refetch: refetchFraming,
  } = useEntityFramingAnalysis(
    { entity_name: selectedEntity, include_related: true, related_limit: 10 },
    !!selectedEntity
  );

  // Fetch co-occurrences
  const {
    data: cooccurrenceData,
    isLoading: isLoadingCooccurrence,
  } = useEntityCooccurrences(
    selectedEntity,
    { minSharedFrames: 2, limit: 15 },
    !!selectedEntity && showCooccurrences
  );

  const handleSearch = useCallback(() => {
    if (!searchQuery.trim()) return;
    setSelectedEntity(searchQuery.trim());
    onEntitySelect?.(searchQuery.trim());
  }, [searchQuery, onEntitySelect]);

  const handleRelatedEntityClick = useCallback((entityName: string) => {
    setSearchQuery(entityName);
    setSelectedEntity(entityName);
    onEntitySelect?.(entityName);
  }, [onEntitySelect]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Entity Narrative Analysis
          </CardTitle>
          <CardDescription>
            Analyze how entities are framed in news narratives
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Enter entity name (e.g., Apple, Elon Musk)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={!searchQuery.trim()}>
              <Search className="h-4 w-4 mr-2" />
              Analyze
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {isLoadingFraming && <EntityFramingAnalysisSkeleton />}

      {/* Error State */}
      {framingError && (
        <Card>
          <CardContent className="py-6">
            <div className="flex flex-col items-center gap-4 text-center">
              <AlertCircle className="h-10 w-10 text-destructive" />
              <p className="text-muted-foreground">{framingError.message}</p>
              <Button variant="outline" onClick={() => refetchFraming()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {framingData && (
        <>
          {/* Entity Framing Analysis */}
          <EntityFramingCard
            analysis={framingData.analysis}
            relatedEntities={framingData.related_entities}
            onRelatedEntityClick={handleRelatedEntityClick}
          />

          {/* Co-occurrence Network */}
          {showCooccurrences && cooccurrenceData && (
            <CooccurrenceCard
              cooccurrences={cooccurrenceData.cooccurrences}
              entityName={selectedEntity}
              onEntityClick={handleRelatedEntityClick}
              isLoading={isLoadingCooccurrence}
            />
          )}
        </>
      )}
    </div>
  );
}

/**
 * Entity Framing Analysis Card
 */
interface EntityFramingCardProps {
  analysis: EntityFramingAnalysis;
  relatedEntities: Array<{ entity_name: string; shared_frames: number }>;
  onRelatedEntityClick: (entityName: string) => void;
}

function EntityFramingCard({
  analysis,
  relatedEntities,
  onRelatedEntityClick,
}: EntityFramingCardProps) {
  const frameEntries = Object.entries(analysis.frame_distribution) as [NarrativeType, number][];
  const totalFrames = frameEntries.reduce((sum, [, count]) => sum + count, 0);
  const dominantFrame = frameEntries.reduce(
    (max, [type, count]) => (count > max.count ? { type, count } : max),
    { type: 'neutral' as NarrativeType, count: 0 }
  );
  const biasDirection = getBiasLabel(analysis.bias_score);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{analysis.entity_name}</CardTitle>
          <Badge variant="outline" className={getNarrativeColor(dominantFrame.type)}>
            {dominantFrame.type}
          </Badge>
        </div>
        <CardDescription>
          {analysis.total_frames} frames analyzed since{' '}
          {new Date(analysis.first_seen).toLocaleDateString()}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatBox
            label="Total Frames"
            value={analysis.total_frames.toString()}
          />
          <StatBox
            label="Avg Confidence"
            value={`${(analysis.avg_confidence * 100).toFixed(1)}%`}
          />
          <StatBox
            label="Bias Score"
            value={analysis.bias_score.toFixed(2)}
            valueClass={getBiasColor(biasDirection)}
          />
          <StatBox
            label="Bias Direction"
            value={biasDirection}
            valueClass={getBiasColor(biasDirection)}
          />
        </div>

        {/* Frame Distribution */}
        <div className="space-y-3">
          <Label className="text-sm font-medium">Frame Distribution</Label>
          <div className="space-y-2">
            {frameEntries.map(([type, count]) => (
              <div key={type}>
                <div className="flex justify-between mb-1 text-sm">
                  <span className={`capitalize font-medium ${getNarrativeColor(type)}`}>
                    {type}
                  </span>
                  <span className="text-muted-foreground">
                    {count} ({totalFrames > 0 ? ((count / totalFrames) * 100).toFixed(1) : 0}%)
                  </span>
                </div>
                <Progress
                  value={totalFrames > 0 ? (count / totalFrames) * 100 : 0}
                  className="h-2"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Related Entities */}
        {relatedEntities.length > 0 && (
          <div className="space-y-2">
            <Label className="text-sm font-medium">Related Entities</Label>
            <div className="flex flex-wrap gap-2">
              {relatedEntities.slice(0, 8).map((entity) => (
                <Button
                  key={entity.entity_name}
                  variant="outline"
                  size="sm"
                  onClick={() => onRelatedEntityClick(entity.entity_name)}
                  className="text-xs"
                >
                  {entity.entity_name}
                  <Badge variant="secondary" className="ml-2">
                    {entity.shared_frames}
                  </Badge>
                </Button>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Co-occurrence Network Card
 */
interface CooccurrenceCardProps {
  cooccurrences: NarrativeCooccurrence[];
  entityName: string;
  onEntityClick: (entityName: string) => void;
  isLoading: boolean;
}

function CooccurrenceCard({
  cooccurrences,
  entityName,
  onEntityClick,
  isLoading,
}: CooccurrenceCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (cooccurrences.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Network className="h-5 w-5" />
          Co-framed Entities
        </CardTitle>
        <CardDescription>
          Entities frequently appearing in narratives with {entityName}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {cooccurrences.map((cooc, index) => {
            const otherEntity =
              cooc.entity1 === entityName ? cooc.entity2 : cooc.entity1;

            return (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted cursor-pointer transition-colors"
                onClick={() => onEntityClick(otherEntity)}
              >
                <div className="flex items-center gap-3">
                  <span className="font-medium">{entityName}</span>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{otherEntity}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    {cooc.shared_frame_count} shared
                  </Badge>
                  <div className="flex gap-1">
                    {cooc.frame_types.slice(0, 2).map((type) => (
                      <Badge
                        key={type}
                        variant="outline"
                        className={`text-xs ${getNarrativeColor(type)}`}
                      >
                        {type}
                      </Badge>
                    ))}
                    {cooc.frame_types.length > 2 && (
                      <Badge variant="outline" className="text-xs">
                        +{cooc.frame_types.length - 2}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Stat Box Component
 */
interface StatBoxProps {
  label: string;
  value: string;
  valueClass?: string;
}

function StatBox({ label, value, valueClass = '' }: StatBoxProps) {
  return (
    <div className="text-center p-3 bg-muted/50 rounded-lg">
      <div className={`text-xl font-bold ${valueClass}`}>{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

/**
 * Loading Skeleton
 */
function EntityFramingAnalysisSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-5 w-20" />
        </div>
        <Skeleton className="h-4 w-64" />
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Compact version for embedding
 */
export function CompactEntityNarrativePanel({
  onEntitySelect,
  className = '',
}: Pick<EntityNarrativePanelProps, 'onEntitySelect' | 'className'>) {
  return (
    <EntityNarrativePanel
      showCooccurrences={false}
      onEntitySelect={onEntitySelect}
      className={className}
    />
  );
}

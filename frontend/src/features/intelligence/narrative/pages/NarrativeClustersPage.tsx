/**
 * NarrativeClustersPage - View and manage narrative clusters
 *
 * Displays clusters of related narratives with filtering and search.
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Users, TrendingUp, Clock, Tag } from 'lucide-react';
import {
  NarrativeClustersGrid,
  ClusterStatsSummary,
} from '../components/NarrativeClustersGrid';
import { BiasGauge } from '../components/BiasChart';
import { useNarrativeClusters } from '../api/useNarrativeClusters';
import type { NarrativeCluster } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor } from '../types/narrative.types';

interface NarrativeClustersPageProps {
  className?: string;
}

export function NarrativeClustersPage({ className = '' }: NarrativeClustersPageProps) {
  const [selectedCluster, setSelectedCluster] = useState<NarrativeCluster | null>(null);
  const { data } = useNarrativeClusters({ per_page: 100 });

  const handleClusterSelect = (cluster: NarrativeCluster) => {
    setSelectedCluster(cluster);
  };

  const handleCloseDialog = () => {
    setSelectedCluster(null);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Narrative Clusters</h1>
        <p className="text-muted-foreground mt-1">
          Explore clusters of related narratives across analyzed content.
        </p>
      </div>

      {/* Stats Summary */}
      {data?.clusters && <ClusterStatsSummary clusters={data.clusters} />}

      {/* Clusters Grid */}
      <NarrativeClustersGrid
        onClusterSelect={handleClusterSelect}
        selectedClusterId={selectedCluster?.id}
        columns={3}
      />

      {/* Cluster Detail Dialog */}
      <Dialog open={!!selectedCluster} onOpenChange={handleCloseDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedCluster?.name}
              <Badge
                variant="outline"
                className={`capitalize ${
                  selectedCluster
                    ? getNarrativeColor(selectedCluster.dominant_frame)
                    : ''
                }`}
              >
                {selectedCluster?.dominant_frame}
              </Badge>
            </DialogTitle>
          </DialogHeader>

          {selectedCluster && <ClusterDetailContent cluster={selectedCluster} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * Cluster Detail Content for Dialog
 */
interface ClusterDetailContentProps {
  cluster: NarrativeCluster;
}

function ClusterDetailContent({ cluster }: ClusterDetailContentProps) {
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-4 rounded-lg bg-secondary/50">
          <Users className="h-5 w-5 mx-auto mb-1 text-muted-foreground" />
          <div className="text-2xl font-bold">{cluster.article_count}</div>
          <div className="text-xs text-muted-foreground">Articles</div>
        </div>
        <div className="text-center p-4 rounded-lg bg-secondary/50">
          <TrendingUp className="h-5 w-5 mx-auto mb-1 text-muted-foreground" />
          <div className="text-2xl font-bold">
            {cluster.avg_bias > 0 ? '+' : ''}
            {cluster.avg_bias.toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground">Avg Bias</div>
        </div>
        <div className="text-center p-4 rounded-lg bg-secondary/50">
          <Tag className="h-5 w-5 mx-auto mb-1 text-muted-foreground" />
          <div className="text-2xl font-bold">{cluster.entities.length}</div>
          <div className="text-xs text-muted-foreground">Entities</div>
        </div>
      </div>

      <Separator />

      {/* Bias Gauge */}
      <div>
        <h4 className="text-sm font-medium mb-3">Bias Score</h4>
        <BiasGauge score={cluster.avg_bias} confidence={0.85} size="lg" />
      </div>

      <Separator />

      {/* Entities */}
      {cluster.entities.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-3">Key Entities</h4>
          <div className="flex flex-wrap gap-2">
            {cluster.entities.map((entity) => (
              <Badge key={entity} variant="secondary">
                {entity}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <Separator />

      {/* Timestamps */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-1">
          <Clock className="h-4 w-4" />
          <span>Created: {new Date(cluster.created_at).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="h-4 w-4" />
          <span>Updated: {new Date(cluster.last_updated).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
}

export default NarrativeClustersPage;

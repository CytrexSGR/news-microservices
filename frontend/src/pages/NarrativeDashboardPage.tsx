import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  getNarrativeOverview,
  listFrames,
  listClusters,
  getBiasComparison,
  type NarrativeOverview,
  type NarrativeFrame,
  type NarrativeCluster,
  type BiasAnalysis,
} from '@/api/narrative';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatCard } from '@/components/shared/StatCard';
import { FrameTimeline } from '@/components/shared/FrameTimeline';
import { BiasComparisonChart } from '@/components/shared/BiasComparisonChart';
import { TextAnalyzer } from '@/features/narrative';
import {
  Activity,
  TrendingUp,
  AlertCircle,
  Users,
  RefreshCw,
  Filter,
  ChevronDown,
  ChevronUp,
  FileText,
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

/**
 * NarrativeDashboardPage - Narrative analysis and frame detection dashboard
 *
 * Location: /intelligence
 * Access: Protected (authenticated users only)
 *
 * Features:
 * - Overview statistics (frames, clusters, bias scores)
 * - Frame distribution visualization
 * - Recent frames list with filters
 * - Active narrative clusters
 * - Bias score trends
 *
 * @returns {JSX.Element} Narrative dashboard page
 */
export function NarrativeDashboardPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<number>(7);
  const [selectedFrameType, setSelectedFrameType] = useState<string | undefined>();
  const [expandedFrames, setExpandedFrames] = useState<Set<string>>(new Set());

  // Fetch overview data
  const {
    data: overview,
    isLoading: isLoadingOverview,
    error: overviewError,
    refetch: refetchOverview,
  } = useQuery<NarrativeOverview>({
    queryKey: ['narrative-overview', selectedPeriod],
    queryFn: () => getNarrativeOverview(selectedPeriod),
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch recent frames
  const {
    data: framesData,
    isLoading: isLoadingFrames,
    refetch: refetchFrames,
  } = useQuery({
    queryKey: ['narrative-frames', selectedFrameType],
    queryFn: () =>
      listFrames({
        page: 1,
        per_page: 20,
        frame_type: selectedFrameType,
        min_confidence: 0.5,
      }),
  });

  // Fetch active clusters
  const {
    data: clusters,
    isLoading: isLoadingClusters,
    refetch: refetchClusters,
  } = useQuery<NarrativeCluster[]>({
    queryKey: ['narrative-clusters'],
    queryFn: listClusters,
  });

  // Fetch bias comparison data
  const {
    data: biasData,
    isLoading: isLoadingBias,
    refetch: refetchBias,
  } = useQuery<BiasAnalysis[]>({
    queryKey: ['narrative-bias', selectedPeriod],
    queryFn: () => getBiasComparison({ days: selectedPeriod }),
  });

  // Frame types for filtering
  const frameTypes = ['victim', 'hero', 'threat', 'solution', 'conflict', 'economic'];

  // Toggle frame expansion
  const toggleFrameExpansion = (frameId: string) => {
    const newExpanded = new Set(expandedFrames);
    if (newExpanded.has(frameId)) {
      newExpanded.delete(frameId);
    } else {
      newExpanded.add(frameId);
    }
    setExpandedFrames(newExpanded);
  };

  // Refresh all data
  const handleRefresh = () => {
    refetchOverview();
    refetchFrames();
    refetchClusters();
    refetchBias();
  };

  // Get frame type color
  const getFrameTypeColor = (frameType: string): string => {
    const colors: Record<string, string> = {
      victim: 'text-red-500',
      hero: 'text-green-500',
      threat: 'text-orange-500',
      solution: 'text-blue-500',
      conflict: 'text-purple-500',
      economic: 'text-yellow-500',
    };
    return colors[frameType] || 'text-gray-500';
  };

  // Get bias label color
  const getBiasLabelColor = (biasScore: number): string => {
    if (biasScore < -0.5) return 'text-blue-500';
    if (biasScore < -0.2) return 'text-blue-400';
    if (biasScore < 0.2) return 'text-gray-500';
    if (biasScore < 0.5) return 'text-red-400';
    return 'text-red-500';
  };

  const getBiasLabel = (biasScore: number): string => {
    if (biasScore < -0.5) return 'Left';
    if (biasScore < -0.2) return 'Center-Left';
    if (biasScore < 0.2) return 'Center';
    if (biasScore < 0.5) return 'Center-Right';
    return 'Right';
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Narrative Analysis</h1>
          <p className="text-muted-foreground">
            Frame detection, bias analysis, and narrative clustering
          </p>
        </div>
        <div className="flex gap-2">
          {/* Period Selector */}
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg bg-background text-foreground"
          >
            <option value={1}>Last 24h</option>
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {overviewError && (
        <Card className="p-4 bg-destructive/10 border-destructive">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>Failed to load narrative data. Please try again.</p>
          </div>
        </Card>
      )}

      {/* Overview Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Frames"
          value={overview?.total_frames ?? 0}
          icon={Activity}
          trend={overview?.total_frames ? 'up' : undefined}
          loading={isLoadingOverview}
        />
        <StatCard
          title="Active Clusters"
          value={overview?.total_clusters ?? 0}
          icon={Users}
          loading={isLoadingOverview}
        />
        <StatCard
          title="Avg Bias Score"
          value={
            overview?.avg_bias_score !== undefined
              ? overview.avg_bias_score.toFixed(2)
              : '-'
          }
          icon={TrendingUp}
          loading={isLoadingOverview}
        />
        <StatCard
          title="Avg Sentiment"
          value={
            overview?.avg_sentiment !== undefined
              ? overview.avg_sentiment.toFixed(2)
              : '-'
          }
          icon={AlertCircle}
          loading={isLoadingOverview}
        />
      </div>

      {/* Tabs: Overview / Timeline / Bias / Recent Frames / Clusters / Text Analyzer */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analyzer">
            <FileText className="h-4 w-4 mr-1" />
            Text Analyzer
          </TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="bias">Bias Analysis</TabsTrigger>
          <TabsTrigger value="frames">Recent Frames</TabsTrigger>
          <TabsTrigger value="clusters">Active Clusters</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {/* Frame Distribution */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Frame Type Distribution</h3>
            {isLoadingOverview ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : overview && Object.keys(overview.frame_distribution).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(overview.frame_distribution).map(([frameType, count]) => (
                  <div key={frameType}>
                    <div className="flex justify-between mb-1">
                      <span className={`capitalize font-medium ${getFrameTypeColor(frameType)}`}>
                        {frameType}
                      </span>
                      <span className="text-sm text-muted-foreground">{count}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{
                          width: `${(count / overview.total_frames) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No frame data available
              </div>
            )}
          </Card>

          {/* Top Narratives */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Top Narratives</h3>
            {isLoadingOverview ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : overview && overview.top_narratives.length > 0 ? (
              <div className="space-y-3">
                {overview.top_narratives.map((narrative) => (
                  <div
                    key={narrative.cluster_id}
                    className="p-4 border rounded-lg hover:bg-accent transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium">{narrative.name}</h4>
                      <span className="text-sm text-muted-foreground">
                        {narrative.frame_count} frames
                      </span>
                    </div>
                    <div className="flex gap-4 text-sm">
                      <span className={`capitalize ${getFrameTypeColor(narrative.dominant_frame)}`}>
                        {narrative.dominant_frame}
                      </span>
                      {narrative.bias_score !== undefined && (
                        <span className={getBiasLabelColor(narrative.bias_score)}>
                          Bias: {getBiasLabel(narrative.bias_score)} ({narrative.bias_score.toFixed(2)})
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No narrative clusters found
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Text Analyzer Tab */}
        <TabsContent value="analyzer" className="space-y-4">
          <TextAnalyzer />
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-4">
          {isLoadingFrames ? (
            <Card className="p-6">
              <div className="text-center py-8 text-muted-foreground">Loading timeline...</div>
            </Card>
          ) : framesData && framesData.frames.length > 0 ? (
            <FrameTimeline
              frames={framesData.frames}
              height={500}
              selectedFrameType={selectedFrameType}
              onFrameClick={(frame) => {
                console.log('Frame clicked:', frame);
                // Could expand frame details or navigate to event
              }}
            />
          ) : (
            <Card className="p-6">
              <div className="text-center py-12 text-muted-foreground">
                No frames available for timeline visualization
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Bias Analysis Tab */}
        <TabsContent value="bias" className="space-y-4">
          {isLoadingBias ? (
            <Card className="p-6">
              <div className="text-center py-8 text-muted-foreground">Loading bias data...</div>
            </Card>
          ) : biasData && biasData.length > 0 ? (
            <>
              <BiasComparisonChart biasAnalyses={biasData} height={450} groupBy="source" />
              <BiasComparisonChart biasAnalyses={biasData} height={350} groupBy="perspective" />
            </>
          ) : (
            <Card className="p-6">
              <div className="text-center py-12 text-muted-foreground">
                No bias analysis data available
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Recent Frames Tab */}
        <TabsContent value="frames" className="space-y-4">
          {/* Frame Type Filter */}
          <Card className="p-4">
            <div className="flex items-center gap-2 flex-wrap">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Filter by type:</span>
              <Button
                variant={selectedFrameType === undefined ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedFrameType(undefined)}
              >
                All
              </Button>
              {frameTypes.map((type) => (
                <Button
                  key={type}
                  variant={selectedFrameType === type ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedFrameType(type)}
                >
                  <span className="capitalize">{type}</span>
                </Button>
              ))}
            </div>
          </Card>

          {/* Frames List */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Frames</h3>
            {isLoadingFrames ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : framesData && framesData.frames.length > 0 ? (
              <div className="space-y-3">
                {framesData.frames.map((frame) => {
                  const isExpanded = expandedFrames.has(frame.id);
                  return (
                    <div
                      key={frame.id}
                      className="p-4 border rounded-lg hover:bg-accent transition-colors"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`capitalize font-medium ${getFrameTypeColor(frame.frame_type)}`}>
                            {frame.frame_type}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            Confidence: {(frame.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleFrameExpansion(frame.id)}
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                      {frame.text_excerpt && (
                        <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                          {frame.text_excerpt}
                        </p>
                      )}
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-t space-y-2">
                          <div className="text-sm">
                            <span className="font-medium">Event ID:</span>{' '}
                            <span className="text-muted-foreground">{frame.event_id}</span>
                          </div>
                          {frame.entities && Object.keys(frame.entities).length > 0 && (
                            <div className="text-sm">
                              <span className="font-medium">Entities:</span>
                              <div className="mt-1 flex flex-wrap gap-2">
                                {Object.entries(frame.entities).map(([type, entities]) => (
                                  <span
                                    key={type}
                                    className="px-2 py-1 bg-secondary rounded text-xs"
                                  >
                                    {type}: {(entities as any[]).join(', ')}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          <div className="text-xs text-muted-foreground">
                            Created: {new Date(frame.created_at).toLocaleString()}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No frames found for the selected filter
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Active Clusters Tab */}
        <TabsContent value="clusters" className="space-y-4">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Active Narrative Clusters</h3>
            {isLoadingClusters ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : clusters && clusters.length > 0 ? (
              <div className="space-y-3">
                {clusters.filter(c => c.is_active).map((cluster) => (
                  <div
                    key={cluster.id}
                    className="p-4 border rounded-lg hover:bg-accent transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium">{cluster.name}</h4>
                      <span className="text-sm text-muted-foreground">
                        {cluster.frame_count} frames
                      </span>
                    </div>
                    <div className="flex gap-4 text-sm mb-2">
                      <span className={`capitalize ${getFrameTypeColor(cluster.dominant_frame)}`}>
                        {cluster.dominant_frame}
                      </span>
                      {cluster.bias_score !== undefined && (
                        <span className={getBiasLabelColor(cluster.bias_score)}>
                          {getBiasLabel(cluster.bias_score)} ({cluster.bias_score.toFixed(2)})
                        </span>
                      )}
                      {cluster.sentiment !== undefined && (
                        <span className="text-muted-foreground">
                          Sentiment: {cluster.sentiment.toFixed(2)}
                        </span>
                      )}
                    </div>
                    {cluster.keywords && cluster.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {cluster.keywords.map((keyword) => (
                          <span
                            key={keyword}
                            className="px-2 py-1 bg-secondary rounded text-xs"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No active clusters found
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

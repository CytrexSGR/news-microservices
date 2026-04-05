/**
 * MarketGraphPage
 *
 * Full-page view for market node visualization in the knowledge graph.
 * Combines market list, details, statistics, and graph visualization.
 *
 * @example
 * ```tsx
 * <MarketGraphPage />
 * ```
 *
 * @module features/knowledge-graph/pages/MarketGraphPage
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { TrendingUp, Network, LayoutGrid, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

import { MarketNodePanel } from '../components/market/MarketNodePanel';
import { MarketDetailsCard } from '../components/market/MarketDetailsCard';
import { MarketStatsWidget } from '../components/market/MarketStatsWidget';
import { GraphVisualization } from '../components/graph-viewer/GraphVisualization';
import { useGraphStore } from '../store/graphStore';
import { useEntityConnections } from '../hooks/useEntityConnections';

// ===========================
// Component Props
// ===========================

export interface MarketGraphPageProps {
  /** Initial selected symbol */
  initialSymbol?: string;
  /** Additional CSS classes */
  className?: string;
}

// ===========================
// Main Component
// ===========================

export function MarketGraphPage({ initialSymbol, className }: MarketGraphPageProps) {
  const navigate = useNavigate();

  // ===== State =====
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(
    initialSymbol ?? null
  );
  const [activeTab, setActiveTab] = useState<'list' | 'graph'>('list');

  // ===== Store =====
  const setSelectedEntity = useGraphStore((state) => state.setSelectedEntity);

  // ===== Graph Data =====
  const { data: graphData, isLoading: graphLoading } = useEntityConnections(
    selectedSymbol,
    {
      enabled: !!selectedSymbol && activeTab === 'graph',
      limit: 50,
    }
  );

  // ===== Handlers =====
  const handleMarketSelect = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
  }, []);

  const handleEntityClick = useCallback((entityName: string) => {
    setSelectedEntity(entityName);
  }, [setSelectedEntity]);

  const handleArticleClick = useCallback((articleId: string) => {
    navigate(`/articles/${articleId}`);
  }, [navigate]);

  const handleViewInGraph = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
    setActiveTab('graph');
  }, []);

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedEntity(nodeId);
  }, [setSelectedEntity]);

  // ===== Render =====
  return (
    <div className={cn('h-full flex flex-col', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">Market Graph</h1>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'list' | 'graph')}>
          <TabsList>
            <TabsTrigger value="list" className="gap-2">
              <LayoutGrid className="h-4 w-4" />
              List View
            </TabsTrigger>
            <TabsTrigger value="graph" className="gap-2">
              <Network className="h-4 w-4" />
              Graph View
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'list' ? (
          <ResizablePanelGroup direction="horizontal">
            {/* Left: Stats + Market List */}
            <ResizablePanel defaultSize={35} minSize={25} maxSize={50}>
              <div className="h-full overflow-y-auto p-4 space-y-4">
                <MarketStatsWidget
                  onMarketClick={handleMarketSelect}
                  compact
                />
                <MarketNodePanel
                  selectedSymbol={selectedSymbol}
                  onSelect={handleMarketSelect}
                  limit={100}
                />
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Right: Details */}
            <ResizablePanel defaultSize={65}>
              <div className="h-full overflow-y-auto p-4">
                <MarketDetailsCard
                  symbol={selectedSymbol}
                  onEntityClick={handleEntityClick}
                  onArticleClick={handleArticleClick}
                  onViewInGraph={handleViewInGraph}
                />
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        ) : (
          <ResizablePanelGroup direction="horizontal">
            {/* Left: Market Selection */}
            <ResizablePanel defaultSize={25} minSize={20} maxSize={35}>
              <div className="h-full overflow-y-auto p-4">
                <MarketNodePanel
                  selectedSymbol={selectedSymbol}
                  onSelect={handleMarketSelect}
                  limit={50}
                />
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Center: Graph */}
            <ResizablePanel defaultSize={50}>
              <div className="h-full p-2">
                {!selectedSymbol ? (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <Network className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>Select a market to view its graph</p>
                    </div>
                  </div>
                ) : graphLoading ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center text-muted-foreground">
                      <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-3" />
                      <p>Loading graph data...</p>
                    </div>
                  </div>
                ) : graphData ? (
                  <GraphVisualization
                    graphData={graphData}
                    onNodeClick={handleNodeClick}
                    className="h-full rounded-lg border"
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    No graph data available
                  </div>
                )}
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Right: Details */}
            <ResizablePanel defaultSize={25} minSize={20} maxSize={35}>
              <div className="h-full overflow-y-auto p-4">
                <MarketDetailsCard
                  symbol={selectedSymbol}
                  onEntityClick={handleEntityClick}
                  onArticleClick={handleArticleClick}
                />
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        )}
      </div>
    </div>
  );
}

export default MarketGraphPage;

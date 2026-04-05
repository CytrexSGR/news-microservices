/**
 * Optimization Dashboard
 *
 * Complete dashboard for ML parameter optimization.
 *
 * Features:
 * - Strategy selection and optimization start
 * - Real-time job monitoring
 * - Results visualization
 * - Optimization history
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, Settings, Activity } from 'lucide-react';

import { OptimizationStartDialog } from '../components/OptimizationStartDialog';
import { OptimizationJobMonitor } from '../components/OptimizationJobMonitor';
import { OptimizationHistoryView } from '../components/OptimizationHistoryView';
import type { OptimizationJob } from '../types/optimization';
import type { StrategyStats } from '../types/strategy';
import { predictionClient } from '@/lib/api-client';

// Strategy configurations - matching actual database strategies
const STRATEGIES = [
  { id: 'Freqtrade Adaptive Futures Strategy', name: 'Freqtrade Adaptive', description: 'Adaptive futures with regime-based logic' },
  // Legacy strategies (disabled until implemented in DB)
  // { id: 'OI_Trend', name: 'OI Trend', description: 'Open Interest trend with RSI confirmation' },
  // { id: 'MeanReversion', name: 'Mean Reversion', description: 'RSI + Bollinger Bands' },
  // { id: 'GoldenPocket', name: 'Golden Pocket', description: 'Fibonacci 0.618-0.65 zone' },
  // { id: 'VolatilityBreakout', name: 'Volatility Breakout', description: 'Bollinger Band Squeeze' },
];

export default function OptimizationDashboard() {
  const [optimizationDialogOpen, setOptimizationDialogOpen] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);

  // Fetch strategy stats for strategy selection
  const { data: strategiesStats } = useQuery<Record<string, StrategyStats>>({
    queryKey: ['all-strategies-stats'],
    queryFn: async () => {
      const promises = STRATEGIES.map(async (strategy) => {
        try {
          const response = await predictionClient.get<StrategyStats>(
            `/strategies/${strategy.id}/stats`,
            { days: '7' }
          );
          return [strategy.id, response.data];
        } catch (error) {
          // Strategy stats endpoint not yet implemented - gracefully skip
          return [strategy.id, null];
        }
      });
      const results = await Promise.all(promises);
      return Object.fromEntries(results.filter(([_, stats]) => stats !== null));
    },
    refetchInterval: 60000,
    retry: false, // Don't retry if endpoint doesn't exist
    staleTime: 300000, // Cache for 5 minutes
  });

  const handleOptimizeClick = (strategyId: string) => {
    setSelectedStrategyId(strategyId);
    setOptimizationDialogOpen(true);
  };

  const handleOptimizationSuccess = (job: OptimizationJob) => {
    console.log('Optimization job created:', job);
    // Job will appear in OptimizationJobMonitor automatically
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <TrendingUp className="h-8 w-8" />
            ML Parameter Optimization
          </h1>
          <p className="text-muted-foreground mt-1">
            Find optimal strategy parameters using Bayesian optimization with walk-forward validation
          </p>
        </div>
      </div>

      {/* Strategy Selection Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {STRATEGIES.map((strategy) => {
          const stats = strategiesStats?.[strategy.id];

          return (
            <Card key={strategy.id} className="hover:border-primary transition-colors cursor-pointer">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center justify-between">
                  {strategy.name}
                  <Settings className="h-4 w-4 text-muted-foreground" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  {strategy.description}
                </p>

                {stats && (
                  <div className="flex items-center gap-2 mb-4">
                    <Badge variant="outline" className="text-xs">
                      <Activity className="h-3 w-3 mr-1" />
                      {stats.total_analyses} signals (7d)
                    </Badge>
                  </div>
                )}

                <Button
                  onClick={() => handleOptimizeClick(strategy.id)}
                  className="w-full"
                  variant="outline"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Optimize Parameters
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Optimization Jobs - Tabs for Active vs History */}
      <Tabs defaultValue="active" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="active">Active Jobs</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-6">
          <OptimizationJobMonitor />
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <OptimizationHistoryView />
        </TabsContent>
      </Tabs>

      {/* Optimization Dialog */}
      {selectedStrategyId && (
        <OptimizationStartDialog
          strategyId={selectedStrategyId}
          strategyName={STRATEGIES.find(s => s.id === selectedStrategyId)?.name || selectedStrategyId}
          isOpen={optimizationDialogOpen}
          onClose={() => setOptimizationDialogOpen(false)}
          onSuccess={handleOptimizationSuccess}
        />
      )}
    </div>
  );
}

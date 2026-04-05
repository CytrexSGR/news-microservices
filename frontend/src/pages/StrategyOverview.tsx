/**
 * StrategyOverview Page
 *
 * Orchestrator component that coordinates strategy display tabs.
 * All tab content has been extracted to separate components for maintainability.
 *
 * Refactored: 2376 lines → ~300 lines (orchestrator only)
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Activity, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

// Feature imports
import {
  StrategyHeader,
  StrategyControls,
  OverviewTab,
  IndicatorsTab,
  LogicTab,
  RiskManagementTab,
  MTFATab,
  ExecutionTab,
  BacktestsTab,
  StrategyEditProvider,
  useStrategyEditContext,
} from '@/features/strategy';
import { PaperTradeTab } from '@/features/strategy/components/tabs/PaperTradeTab';
import type { Strategy, BacktestListResponse } from '@/features/strategy';
import { Button } from '@/components/ui/Button';
import { Pencil, Eye } from 'lucide-react';
import { BacktestDialog } from '@/features/trading/components/BacktestDialog';
import { predictionService } from '@/lib/api/prediction-service';
import { toBybitSymbol } from '@/constants/symbols';
import { useStrategyEvaluation } from '@/hooks/useStrategyEvaluation';
import type { Timeframe } from '@/types/indicators';
import type { StrategyLabBacktestRequest } from '@/types/backtest';

// LocalStorage keys for persisting user selection
const STORAGE_KEY_SYMBOL = 'strategy-overview-symbol';
const STORAGE_KEY_TIMEFRAME = 'strategy-overview-timeframe';

// ============================================================================
// Edit Mode Toggle Component
// ============================================================================

function EditModeToggle() {
  const { isEditMode, toggleEditMode, isPending } = useStrategyEditContext();

  return (
    <Button
      variant={isEditMode ? 'default' : 'outline'}
      size="sm"
      onClick={toggleEditMode}
      disabled={isPending}
      className="gap-2"
    >
      {isEditMode ? (
        <>
          <Eye className="h-4 w-4" />
          View Mode
        </>
      ) : (
        <>
          <Pencil className="h-4 w-4" />
          Edit Mode
        </>
      )}
    </Button>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export const StrategyOverview: React.FC = () => {
  const { strategyId } = useParams<{ strategyId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Strategy state
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [backtestDialogOpen, setBacktestDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Backtest progress state (SSE tracking)
  const [runningBacktestRequest, setRunningBacktestRequest] = useState<StrategyLabBacktestRequest | null>(null);
  const [backtestProgress, setBacktestProgress] = useState<{
    percentage: number;
    phase: string;
    current_bar: number;
    total_bars: number;
  } | null>(null);
  const [backtestJobId, setBacktestJobId] = useState<string | null>(null);

  // Symbol/Timeframe selection (persisted to localStorage)
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_TIMEFRAME);
    return (saved as Timeframe) || '1h';
  });
  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => {
    return localStorage.getItem(STORAGE_KEY_SYMBOL) || 'BTCUSDT';
  });

  // Symbol/Timeframe handlers with persistence
  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
    localStorage.setItem(STORAGE_KEY_SYMBOL, symbol);
  };

  const handleTimeframeChange = (timeframe: Timeframe) => {
    setSelectedTimeframe(timeframe);
    localStorage.setItem(STORAGE_KEY_TIMEFRAME, timeframe);
  };

  // Fetch strategy data
  useEffect(() => {
    const fetchStrategy = async () => {
      try {
        const response = await fetch(`/api/prediction/v1/strategies/${strategyId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch strategy: ${response.statusText}`);
        }

        const data = await response.json();
        setStrategy(data);
      } catch (err) {
        console.error('Error fetching strategy:', err);
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    if (strategyId) {
      fetchStrategy();
    }
  }, [strategyId]);

  // Restore backtest job from localStorage on mount
  useEffect(() => {
    if (!strategyId) return;
    const savedJobId = localStorage.getItem(`backtest_job_${strategyId}`);
    if (savedJobId) {
      setBacktestJobId(savedJobId);
    }
  }, [strategyId]);

  // Fetch backtests for this strategy
  const {
    data: backtestsData,
    isLoading: backtestsLoading,
    error: backtestsError,
    refetch: refetchBacktests,
  } = useQuery<BacktestListResponse>({
    queryKey: ['strategy-backtests', strategyId],
    queryFn: async () => {
      const response = await fetch(`/api/prediction/v1/strategies/${strategyId}/backtests`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch backtests');
      }
      return response.json();
    },
    enabled: !!strategyId,
  });

  // Delete backtest mutation
  const deleteBacktestMutation = useMutation({
    mutationFn: async (backtestId: number) => {
      const response = await fetch(
        `/api/prediction/v1/strategies/${strategyId}/backtests/${backtestId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      if (!response.ok) {
        throw new Error('Failed to delete backtest');
      }
    },
    onSuccess: () => {
      toast.success('Backtest deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['strategy-backtests', strategyId] });
    },
    onError: (err) => {
      toast.error(`Failed to delete backtest: ${err.message}`);
    },
  });

  // Fetch live indicators
  const {
    data: liveIndicators,
    isLoading: indicatorsLoading,
    error: indicatorsError,
  } = useQuery({
    queryKey: ['indicators', selectedSymbol, selectedTimeframe, 'comprehensive'],
    queryFn: () => predictionService.getIndicators(selectedSymbol, selectedTimeframe, true),
    refetchInterval: 60000,
    enabled: !!selectedSymbol,
  });

  // Fetch strategy evaluation
  const {
    data: strategyEvaluation,
    isLoading: evaluationLoading,
    error: evaluationError,
  } = useStrategyEvaluation(strategyId, toBybitSymbol(selectedSymbol), selectedTimeframe, {
    refetchInterval: 30000,
    enabled: !!strategyId && !!selectedSymbol,
  });

  // SSE backtest handler
  const handleStartBacktest = async (request: StrategyLabBacktestRequest) => {
    setRunningBacktestRequest(request);
    setBacktestProgress({ percentage: 0, phase: 'initializing', current_bar: 0, total_bars: 0 });
    setActiveTab('backtests');

    try {
      const response = await fetch('/api/prediction/v1/strategy-lab/backtest/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6));

              if ('job_id' in parsed && !('status' in parsed)) {
                setBacktestJobId(parsed.job_id);
                localStorage.setItem(`backtest_job_${strategyId}`, parsed.job_id);
              } else if ('percentage' in parsed && 'phase' in parsed) {
                setBacktestProgress({
                  percentage: parsed.percentage,
                  phase: parsed.phase,
                  current_bar: parsed.current_bar,
                  total_bars: parsed.total_bars,
                });
              } else if (parsed.status === 'success') {
                localStorage.removeItem(`backtest_job_${strategyId}`);
                setBacktestJobId(null);
                setRunningBacktestRequest(null);
                setBacktestProgress(null);
                refetchBacktests();
                navigate('/trading/backtest/results', {
                  state: { backtestResponse: parsed, strategy },
                });
                return;
              } else if ('error' in parsed || parsed.status === 'error') {
                localStorage.removeItem(`backtest_job_${strategyId}`);
                setBacktestJobId(null);
                throw new Error(parsed.error || parsed.error_message || 'Backtest failed');
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (err) {
      console.error('Backtest SSE error:', err);
      if (backtestJobId) {
        localStorage.removeItem(`backtest_job_${strategyId}`);
        setBacktestJobId(null);
      }
      toast.error(`Backtest failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setBacktestProgress(null);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <Activity className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !strategy) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>{error || 'Strategy not found'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const def = strategy.definition;

  return (
    <StrategyEditProvider strategy={strategy}>
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <StrategyHeader definition={def} backPath="/trading/debug" />
          <div className="flex items-center gap-3">
            <EditModeToggle />
            <StrategyControls
              strategyId={strategyId || ''}
              selectedSymbol={selectedSymbol}
              selectedTimeframe={selectedTimeframe}
              onSymbolChange={handleSymbolChange}
              onTimeframeChange={handleTimeframeChange}
            />
          </div>
        </div>

        {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="indicators">Indicators</TabsTrigger>
          <TabsTrigger value="logic">Logic</TabsTrigger>
          <TabsTrigger value="risk">Risk Mgmt</TabsTrigger>
          <TabsTrigger value="mtfa">MTFA</TabsTrigger>
          <TabsTrigger value="execution">Execution</TabsTrigger>
          <TabsTrigger value="paper-trade">Paper Trade</TabsTrigger>
          <TabsTrigger value="backtests">
            Backtests
            {runningBacktestRequest ? (
              <Badge variant="default" className="ml-1.5 h-5 px-1.5 text-xs animate-pulse">
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
                Running
              </Badge>
            ) : backtestsData && backtestsData.total > 0 ? (
              <Badge variant="secondary" className="ml-1.5 h-5 px-1.5 text-xs">
                {backtestsData.total}
              </Badge>
            ) : null}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <OverviewTab
            definition={def}
            selectedSymbol={selectedSymbol}
            selectedTimeframe={selectedTimeframe}
            liveIndicators={liveIndicators || null}
            strategyEvaluation={strategyEvaluation || null}
            evaluationLoading={evaluationLoading}
            evaluationError={evaluationError as Error | null}
          />
        </TabsContent>

        <TabsContent value="indicators" className="space-y-4">
          <IndicatorsTab
            definition={def}
            selectedSymbol={selectedSymbol}
            selectedTimeframe={selectedTimeframe}
            onSymbolChange={handleSymbolChange}
            onTimeframeChange={handleTimeframeChange}
            indicators={liveIndicators || null}
            isLoading={indicatorsLoading}
            error={indicatorsError as Error | null}
          />
        </TabsContent>

        <TabsContent value="logic" className="space-y-4">
          <LogicTab definition={def} />
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <RiskManagementTab definition={def} strategyEvaluation={strategyEvaluation} />
        </TabsContent>

        <TabsContent value="mtfa" className="space-y-4">
          <MTFATab definition={def} />
        </TabsContent>

        <TabsContent value="execution" className="space-y-4">
          <ExecutionTab definition={def} />
        </TabsContent>

        <TabsContent value="paper-trade" className="space-y-4">
          <PaperTradeTab strategy={strategy} />
        </TabsContent>

        <TabsContent value="backtests" className="space-y-4">
          <BacktestsTab
            strategyId={strategyId || ''}
            strategy={strategy}
            backtests={backtestsData?.backtests || []}
            total={backtestsData?.total || 0}
            isLoading={backtestsLoading}
            error={backtestsError as Error | null}
            onOpenBacktestDialog={() => setBacktestDialogOpen(true)}
            onDeleteBacktest={(id) => deleteBacktestMutation.mutate(id)}
            isDeleting={deleteBacktestMutation.isPending}
            runningBacktestRequest={runningBacktestRequest}
            backtestProgress={backtestProgress}
            isRunning={!!runningBacktestRequest}
          />
        </TabsContent>
      </Tabs>

        {/* Backtest Dialog */}
        <BacktestDialog
          strategy={strategy}
          isOpen={backtestDialogOpen}
          onClose={() => setBacktestDialogOpen(false)}
          onStartBacktest={handleStartBacktest}
          initialSymbol={selectedSymbol}
          initialTimeframe={selectedTimeframe}
        />
      </div>
    </StrategyEditProvider>
  );
};

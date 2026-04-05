/**
 * Strategies Tab - Strategy-Centric Trading Management
 *
 * List and manage trading strategies with portfolio configuration.
 * Each strategy can run in: Backtest → Paper → Live modes.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import {
  RefreshCw,
  Plus,
  Trash2,
  Loader2,
  Play,
  Square,
  TrendingUp,
  Wallet,
  PieChart,
  History,
  TestTube,
  Radio,
  ChevronRight,
  Settings2,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { tradingStrategyApi } from '../../api/mlLabApi';
import type { TradingStrategy, StrategyExecution, ExecutionMode, ExecutionStatus } from '../../types';
import { CreateStrategyModal } from './CreateStrategyModal';
import { StrategyExecutionPanel } from './StrategyExecutionPanel';

// Status badge colors
const STATUS_COLORS: Record<ExecutionStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  running: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  stopped: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};

// Mode icons
const MODE_ICONS: Record<ExecutionMode, React.ReactNode> = {
  backtest: <History className="h-4 w-4" />,
  paper: <TestTube className="h-4 w-4" />,
  live: <Radio className="h-4 w-4" />,
};

export function StrategiesTab() {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<TradingStrategy | null>(null);

  const fetchStrategies = useCallback(async () => {
    try {
      setLoading(true);
      const data = await tradingStrategyApi.list();
      setStrategies(data.strategies);
    } catch (error) {
      console.error('Failed to fetch strategies:', error);
      toast.error('Failed to load strategies');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStrategies();
  }, [fetchStrategies]);

  const handleDelete = async (strategyId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this strategy? All executions will be deleted.')) return;
    try {
      await tradingStrategyApi.delete(strategyId);
      toast.success('Strategy deleted');
      fetchStrategies();
      if (selectedStrategy?.id === strategyId) {
        setSelectedStrategy(null);
      }
    } catch (error) {
      toast.error('Failed to delete strategy');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  // If a strategy is selected, show the execution panel
  if (selectedStrategy) {
    return (
      <StrategyExecutionPanel
        strategy={selectedStrategy}
        onBack={() => setSelectedStrategy(null)}
        onRefresh={fetchStrategies}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <PieChart className="h-6 w-6 text-primary" />
            Trading Strategies
          </h2>
          <p className="text-muted-foreground">
            Create portfolio strategies and run them in Backtest → Paper → Live modes
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchStrategies}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Strategy
          </Button>
        </div>
      </div>

      {/* Strategies List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : strategies.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <PieChart className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No strategies found</p>
            <p className="text-muted-foreground mb-4">
              Create your first portfolio strategy to start trading
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Strategy
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {strategies.map((strategy) => (
            <Card
              key={strategy.id}
              className="cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => setSelectedStrategy(strategy)}
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  {/* Strategy Info */}
                  <div className="flex items-center gap-4 flex-1">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <TrendingUp className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg">{strategy.name}</h3>
                        <Badge variant={strategy.is_active ? 'default' : 'secondary'}>
                          {strategy.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                        {strategy.ml_gates_enabled && (
                          <Badge variant="outline" className="border-primary text-primary">
                            ML Gates
                          </Badge>
                        )}
                      </div>
                      {strategy.description && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {strategy.description}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Strategy Stats */}
                  <div className="flex items-center gap-6">
                    {/* Symbols */}
                    <div className="text-center">
                      <div className="flex gap-1 mb-1">
                        {strategy.symbols.slice(0, 3).map((symbol) => (
                          <Badge key={symbol} variant="outline" className="text-xs">
                            {symbol.replace('USDT', '')}
                          </Badge>
                        ))}
                        {strategy.symbols.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{strategy.symbols.length - 3}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">Symbols</span>
                    </div>

                    {/* Capital */}
                    <div className="text-center min-w-[80px]">
                      <div className="flex items-center justify-center gap-1">
                        <Wallet className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{formatCurrency(strategy.total_capital)}</span>
                      </div>
                      <span className="text-xs text-muted-foreground">Capital</span>
                    </div>

                    {/* Risk */}
                    <div className="text-center min-w-[60px]">
                      <div className="font-medium text-orange-600">
                        {formatPercent(strategy.stop_loss_pct)}
                      </div>
                      <span className="text-xs text-muted-foreground">Stop Loss</span>
                    </div>

                    {/* Position Size */}
                    <div className="text-center min-w-[60px]">
                      <div className="font-medium">
                        {formatPercent(strategy.position_size_pct)}
                      </div>
                      <span className="text-xs text-muted-foreground">Pos. Size</span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                        onClick={(e) => handleDelete(strategy.id, e)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <ChevronRight className="h-5 w-5 text-muted-foreground" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateStrategyModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            fetchStrategies();
          }}
        />
      )}
    </div>
  );
}

export default StrategiesTab;

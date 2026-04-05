/**
 * Data Management Page
 *
 * Unified Market Data Architecture - UI for managing market data inventory,
 * backfilling historical data, and monitoring data availability.
 */

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Database,
  RefreshCw,
  Download,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  BarChart3,
  Calendar,
  Activity,
  TrendingUp,
  Layers,
  Play,
  Pause,
  XCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  useDataInventory,
  useSymbolInventory,
  useSupportedSymbols,
  useDataGaps,
  useBackfillJobs,
  useStartBackfill,
  useFillGaps,
  useDataManagementHealth,
} from '@/hooks/useDataManagement';
import type {
  CandleInterval,
  BackfillSource,
  BackfillJob,
  SymbolInventory,
  DataGap,
} from '@/types/data-management';

// ============================================================================
// Constants
// ============================================================================

const INTERVALS: { value: CandleInterval; label: string }[] = [
  { value: '1min', label: '1 Minute' },
  { value: '5min', label: '5 Minutes' },
  { value: '15min', label: '15 Minutes' },
  { value: '30min', label: '30 Minutes' },
  { value: '1hour', label: '1 Hour' },
  { value: '4hour', label: '4 Hours' },
  { value: '1day', label: '1 Day' },
];

const SOURCES: { value: BackfillSource; label: string }[] = [
  { value: 'auto', label: 'Auto (Best Source)' },
  { value: 'bybit', label: 'Bybit' },
  { value: 'fmp', label: 'FMP' },
];

// ============================================================================
// Sub-Components
// ============================================================================

function HealthStatus() {
  const { data: health, isLoading, error } = useDataManagementHealth();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Checking status...</span>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="flex items-center gap-2 text-destructive">
        <XCircle className="h-4 w-4" />
        <span>Service unavailable</span>
      </div>
    );
  }

  const statusColors = {
    healthy: 'text-green-500',
    degraded: 'text-yellow-500',
    unhealthy: 'text-red-500',
  };

  const StatusIcon = health.status === 'healthy' ? CheckCircle2 : AlertTriangle;

  return (
    <div className="flex items-center gap-4">
      <div className={`flex items-center gap-2 ${statusColors[health.status]}`}>
        <StatusIcon className="h-4 w-4" />
        <span className="capitalize">{health.status}</span>
      </div>
      {health.sync_worker_running && (
        <Badge variant="outline" className="text-green-500 border-green-500">
          <Activity className="h-3 w-3 mr-1" />
          Sync Active
        </Badge>
      )}
      {health.last_sync && (
        <span className="text-xs text-muted-foreground">
          Last sync: {new Date(health.last_sync).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}

function InventoryOverview() {
  const { data: inventory, isLoading, error, refetch } = useDataInventory();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Failed to load inventory: {error.message}</AlertDescription>
      </Alert>
    );
  }

  if (!inventory) return null;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-500" />
                <div>
                  <p className="text-2xl font-bold">{inventory.total_symbols}</p>
                  <p className="text-xs text-muted-foreground">Symbols</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-2xl font-bold">{inventory.total_candles.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">Total Candles</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-purple-500" />
                <div>
                  <p className="text-sm font-medium">
                    {new Date(inventory.last_updated).toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">Last Updated</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-2 text-left text-sm font-medium">Symbol</th>
              <th className="px-4 py-2 text-left text-sm font-medium">Candles</th>
              <th className="px-4 py-2 text-left text-sm font-medium">Timeframes</th>
              <th className="px-4 py-2 text-left text-sm font-medium">Date Range</th>
              <th className="px-4 py-2 text-left text-sm font-medium">Sources</th>
              <th className="px-4 py-2 text-left text-sm font-medium">Gaps</th>
            </tr>
          </thead>
          <tbody>
            {inventory.symbols.map((symbol) => (
              <SymbolRow key={symbol.symbol} symbol={symbol} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SymbolRow({ symbol }: { symbol: SymbolInventory }) {
  const formatDate = (date: string | null) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString();
  };

  return (
    <tr className="border-t hover:bg-muted/30">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="font-medium">{symbol.display_name}</span>
          <Badge variant="outline" className="text-xs">
            {symbol.asset_type}
          </Badge>
        </div>
      </td>
      <td className="px-4 py-3 text-sm">{symbol.total_candles.toLocaleString()}</td>
      <td className="px-4 py-3">
        <div className="flex gap-1 flex-wrap">
          {symbol.timeframes.map((tf) => (
            <Badge key={tf.interval} variant="secondary" className="text-xs">
              {tf.interval}: {tf.count.toLocaleString()}
            </Badge>
          ))}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-muted-foreground">
        {formatDate(symbol.first_data)} - {formatDate(symbol.last_data)}
      </td>
      <td className="px-4 py-3">
        <div className="flex gap-1">
          {symbol.sources.map((source) => (
            <Badge
              key={source}
              variant={source === 'bybit' ? 'default' : 'secondary'}
              className="text-xs"
            >
              {source}
            </Badge>
          ))}
        </div>
      </td>
      <td className="px-4 py-3">
        {symbol.gaps_detected > 0 ? (
          <Badge variant="destructive" className="text-xs">
            {symbol.gaps_detected} gaps
          </Badge>
        ) : (
          <Badge variant="outline" className="text-xs text-green-500 border-green-500">
            Complete
          </Badge>
        )}
      </td>
    </tr>
  );
}

function GapDetector() {
  const { data: symbols } = useSupportedSymbols();
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedInterval, setSelectedInterval] = useState<CandleInterval>('1hour');

  const { data: gaps, isLoading, error, refetch } = useDataGaps(
    selectedSymbol,
    selectedInterval
  );

  const fillGapsMutation = useFillGaps();

  const handleFillGaps = async () => {
    if (!selectedSymbol || !gaps || gaps.gaps.length === 0) return;

    try {
      const result = await fillGapsMutation.mutateAsync({
        symbol: selectedSymbol,
        interval: selectedInterval,
        start_date: gaps.analyzed_from,
        end_date: gaps.analyzed_to,
      });
      toast.success(`Created ${result.jobs_created} backfill jobs`);
    } catch (e) {
      toast.error('Failed to start gap filling');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4 items-end">
        <div className="space-y-2">
          <label className="text-sm font-medium">Symbol</label>
          <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select symbol" />
            </SelectTrigger>
            <SelectContent>
              {symbols?.map((s) => (
                <SelectItem key={s.internal} value={s.internal}>
                  {s.name || s.display || s.internal}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Interval</label>
          <Select
            value={selectedInterval}
            onValueChange={(v) => setSelectedInterval(v as CandleInterval)}
          >
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INTERVALS.map((i) => (
                <SelectItem key={i.value} value={i.value}>
                  {i.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={!selectedSymbol || isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span className="ml-2">Analyze</span>
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {gaps && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="text-lg">
                  Gap Analysis: {selectedSymbol} ({selectedInterval})
                </CardTitle>
                <CardDescription>
                  {gaps.total_gaps} gaps found ({(gaps.total_missing_candles ?? gaps.total_missing_hours ?? 0).toLocaleString()} missing
                  {gaps.total_missing_hours ? ' hours' : ' candles'})
                </CardDescription>
              </div>
              {gaps.gaps.length > 0 && (
                <Button
                  onClick={handleFillGaps}
                  disabled={fillGapsMutation.isPending}
                >
                  {fillGapsMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Download className="h-4 w-4 mr-2" />
                  )}
                  Fill All Gaps
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {gaps.gaps.length === 0 ? (
              <div className="flex items-center justify-center py-8 text-green-500">
                <CheckCircle2 className="h-8 w-8 mr-2" />
                <span className="text-lg font-medium">No gaps detected - data is complete!</span>
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {gaps.gaps.map((gap, idx) => (
                  <GapRow key={idx} gap={gap} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function GapRow({ gap }: { gap: DataGap }) {
  return (
    <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
      <div className="flex items-center gap-4">
        <AlertTriangle className="h-4 w-4 text-yellow-500" />
        <div>
          <p className="text-sm font-medium">
            {new Date(gap.start).toLocaleString()} - {new Date(gap.end).toLocaleString()}
          </p>
          <p className="text-xs text-muted-foreground">
            {gap.duration_hours.toFixed(1)} hours
          </p>
        </div>
      </div>
      <Badge variant="outline">{(gap.missing_candles ?? gap.missing_candles_estimated ?? 0).toLocaleString()} candles</Badge>
    </div>
  );
}

function BackfillPanel() {
  const { data: symbols } = useSupportedSymbols();
  const { data: jobs, isLoading: jobsLoading } = useBackfillJobs();
  const startBackfillMutation = useStartBackfill();

  const [formData, setFormData] = useState({
    symbol: '',
    interval: '1hour' as CandleInterval,
    startDate: '',
    endDate: '',
    source: 'auto' as BackfillSource,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.symbol || !formData.startDate || !formData.endDate) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      const result = await startBackfillMutation.mutateAsync({
        symbol: formData.symbol,
        interval: formData.interval,
        start_date: formData.startDate,
        end_date: formData.endDate,
        source: formData.source,
      });
      toast.success(`Backfill job started: ${result.job_id}`);
    } catch (e) {
      toast.error('Failed to start backfill');
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Start New Backfill
          </CardTitle>
          <CardDescription>
            Fetch historical data for a symbol from FMP or Bybit
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Symbol *</label>
                <Select
                  value={formData.symbol}
                  onValueChange={(v) => setFormData((f) => ({ ...f, symbol: v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select symbol" />
                  </SelectTrigger>
                  <SelectContent>
                    {symbols?.map((s) => (
                      <SelectItem key={s.internal} value={s.internal}>
                        {s.name || s.display || s.internal}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Interval</label>
                <Select
                  value={formData.interval}
                  onValueChange={(v) =>
                    setFormData((f) => ({ ...f, interval: v as CandleInterval }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INTERVALS.map((i) => (
                      <SelectItem key={i.value} value={i.value}>
                        {i.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Start Date *</label>
                <Input
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => setFormData((f) => ({ ...f, startDate: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">End Date *</label>
                <Input
                  type="date"
                  value={formData.endDate}
                  onChange={(e) => setFormData((f) => ({ ...f, endDate: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Data Source</label>
                <Select
                  value={formData.source}
                  onValueChange={(v) =>
                    setFormData((f) => ({ ...f, source: v as BackfillSource }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SOURCES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button
              type="submit"
              disabled={startBackfillMutation.isPending}
              className="w-full"
            >
              {startBackfillMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Start Backfill
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Active Backfill Jobs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {jobsLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !jobs || jobs.length === 0 ? (
            <p className="text-center text-muted-foreground py-4">No active backfill jobs</p>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <BackfillJobRow key={job.job_id} job={job} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function BackfillJobRow({ job }: { job: BackfillJob }) {
  const statusConfig = {
    pending: { color: 'bg-gray-500', icon: Clock },
    running: { color: 'bg-blue-500', icon: Loader2 },
    completed: { color: 'bg-green-500', icon: CheckCircle2 },
    failed: { color: 'bg-red-500', icon: XCircle },
    cancelled: { color: 'bg-yellow-500', icon: Pause },
  };

  const config = statusConfig[job.status];
  const StatusIcon = config.icon;

  return (
    <div className="p-4 border rounded-lg space-y-2">
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${config.color}/20`}>
            <StatusIcon
              className={`h-4 w-4 ${
                job.status === 'running' ? 'animate-spin text-blue-500' : ''
              }`}
            />
          </div>
          <div>
            <p className="font-medium">
              {job.symbol} ({job.interval})
            </p>
            <p className="text-xs text-muted-foreground">
              {job.start_date} to {job.end_date}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">{job.source}</Badge>
          <Badge
            variant={job.status === 'completed' ? 'default' : 'secondary'}
            className="capitalize"
          >
            {job.status}
          </Badge>
        </div>
      </div>

      {job.status === 'running' && (
        <div className="space-y-1">
          <Progress value={job.progress_percent} className="h-2" />
          <p className="text-xs text-muted-foreground text-right">
            {job.candles_inserted.toLocaleString()} / {job.candles_fetched.toLocaleString()} candles
            ({job.progress_percent}%)
          </p>
        </div>
      )}

      {job.error && (
        <Alert variant="destructive" className="py-2">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-xs">{job.error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DataManagementPage() {
  const [activeTab, setActiveTab] = useState('inventory');

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Database className="h-8 w-8 text-primary" />
            Data Management
          </h1>
          <p className="text-muted-foreground mt-1">
            Unified Market Data Architecture - Manage historical market data for backtesting
          </p>
        </div>
        <HealthStatus />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="inventory" className="flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Inventory
          </TabsTrigger>
          <TabsTrigger value="gaps" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Gap Detection
          </TabsTrigger>
          <TabsTrigger value="backfill" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Backfill
          </TabsTrigger>
        </TabsList>

        <TabsContent value="inventory" className="mt-4">
          <InventoryOverview />
        </TabsContent>

        <TabsContent value="gaps" className="mt-4">
          <GapDetector />
        </TabsContent>

        <TabsContent value="backfill" className="mt-4">
          <BackfillPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default DataManagementPage;

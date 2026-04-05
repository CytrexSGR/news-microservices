/**
 * Optimization Start Dialog
 *
 * Form for starting ML parameter optimization jobs.
 *
 * Features:
 * - Preset parameter space selection (RSI Optimization, EMA Crossover, Regime Detection, etc.)
 * - Custom parameter configuration
 * - Optimization settings (trials, data range, objective)
 * - Live job submission with feedback
 */

import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Loader2, TrendingUp, Settings, Database, Clock, CheckCircle } from 'lucide-react';

import type {
  OptimizationRequest,
  OptimizationJob,
  ParameterSpaceItem,
  ValidateParametersRequest,
  ValidateParametersResponse,
} from '../types/optimization';
import { COMMON_PARAMETER_SPACES, PRESET_DESCRIPTIONS, AVAILABLE_SYMBOLS, AVAILABLE_TIMEFRAMES } from '../types/optimization';
import { predictionClient } from '@/lib/api-client';

interface OptimizationStartDialogProps {
  strategyId: string;
  strategyName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (job: OptimizationJob) => void;
}

export function OptimizationStartDialog({
  strategyId,
  strategyName,
  isOpen,
  onClose,
  onSuccess,
}: OptimizationStartDialogProps) {
  // Form state
  const [selectedPreset, setSelectedPreset] = useState<string>('RSI_Optimization');
  const [nTrials, setNTrials] = useState<number>(20);
  const [marketDataDays, setMarketDataDays] = useState<number>(180);
  const [objectiveMetric, setObjectiveMetric] = useState<'sharpe_ratio' | 'total_return' | 'win_rate' | 'consistency_score'>('sharpe_ratio');
  const [symbol, setSymbol] = useState<string>('BTCUSDT');
  const [timeframe, setTimeframe] = useState<string>('1h');

  // Polling state
  const [runningJobId, setRunningJobId] = useState<string | null>(null);

  // Validation state (Phase 6)
  const [validationResponse, setValidationResponse] = useState<ValidateParametersResponse | null>(null);

  // API mutation for validating parameters (Phase 6)
  const validateParametersMutation = useMutation({
    mutationFn: async (request: ValidateParametersRequest): Promise<ValidateParametersResponse> => {
      const response = await predictionClient.post<ValidateParametersResponse>(
        `/optimization/strategies/${strategyId}/validate-parameters`,
        request
      );
      return response.data;
    },
    onSuccess: (response) => {
      setValidationResponse(response);

      // If validation passes, proceed with job creation
      if (response.is_valid) {
        const parameterSpace: ParameterSpaceItem[] =
          COMMON_PARAMETER_SPACES[selectedPreset] || COMMON_PARAMETER_SPACES.RSI_Optimization;

        const request: OptimizationRequest = {
          parameter_space: parameterSpace,
          objective_metric: objectiveMetric,
          n_trials: nTrials,
          market_data_days: marketDataDays,
          symbol: symbol,
          timeframe: timeframe,
        };

        startOptimizationMutation.mutate(request);
      }
    },
  });

  // API mutation for starting optimization (creates job, returns immediately)
  const startOptimizationMutation = useMutation({
    mutationFn: async (request: OptimizationRequest): Promise<OptimizationJob> => {
      const response = await predictionClient.post<OptimizationJob>(
        `/optimization/strategies/${strategyId}/optimize`,
        request
      );
      return response.data;
    },
    onSuccess: (job) => {
      // Job created with status='pending', start polling
      setRunningJobId(job.id);
      // Clear validation response after successful job creation
      setValidationResponse(null);
    },
  });

  // Poll for job status while running
  const jobStatusQuery = useQuery({
    queryKey: ['optimization-status', runningJobId],
    queryFn: async (): Promise<OptimizationJob> => {
      if (!runningJobId) throw new Error('No job ID');
      const response = await predictionClient.get<OptimizationJob>(
        `/optimization/jobs/${runningJobId}`
      );
      return response.data;
    },
    enabled: runningJobId !== null,
    refetchInterval: (query) => {
      // React Query v5: callback receives query object, not data directly
      const data = query.state.data;

      // Poll every 2 seconds while job is running, pending, or loading data
      if (!data) return 2000;
      const status = data.status;
      if (status === 'pending' || status === 'loading_data' || status === 'running') {
        return 2000;
      }
      return false; // Stop polling when completed/failed/cancelled
    },
  });

  // Handle job completion
  useEffect(() => {
    const job = jobStatusQuery.data;
    if (job && (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled')) {
      // Job finished, notify parent and close dialog
      setRunningJobId(null);
      onSuccess(job);
      onClose();
    }
  }, [jobStatusQuery.data, onSuccess, onClose]);

  const handleSubmit = () => {
    // Phase 6: Validate parameters before job creation
    const parameterSpace: ParameterSpaceItem[] =
      COMMON_PARAMETER_SPACES[selectedPreset] || COMMON_PARAMETER_SPACES.RSI_Optimization;

    const validationRequest: ValidateParametersRequest = {
      parameter_space: parameterSpace,
    };

    // Trigger validation - onSuccess will create job if valid
    validateParametersMutation.mutate(validationRequest);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Start ML Parameter Optimization
          </DialogTitle>
          <DialogDescription>
            Find optimal parameters for <strong>{strategyName}</strong> using Bayesian optimization
            with walk-forward validation
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Parameter Space Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Parameter Space
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Parameter Preset
                </label>
                <Select value={selectedPreset} onValueChange={setSelectedPreset}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="RSI_Optimization">
                      RSI Optimization (period, entry threshold, take profit)
                    </SelectItem>
                    <SelectItem value="EMA_Crossover">
                      EMA Crossover (fast, medium, slow periods)
                    </SelectItem>
                    <SelectItem value="Bollinger_Bands">
                      Bollinger Bands (period, stddev)
                    </SelectItem>
                    <SelectItem value="Risk_Management">
                      Risk Management (take profit, trailing offset)
                    </SelectItem>
                    <SelectItem value="Regime_Detection">
                      Regime Detection (ADX trend, BBW volatility)
                    </SelectItem>
                  </SelectContent>
                </Select>
                {/* Preset Description */}
                {PRESET_DESCRIPTIONS[selectedPreset] && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {PRESET_DESCRIPTIONS[selectedPreset]}
                  </p>
                )}
              </div>

              {/* Parameter Space Preview */}
              <div>
                <div className="text-sm font-medium mb-2">Parameters to Optimize:</div>
                <div className="flex flex-wrap gap-2">
                  {(COMMON_PARAMETER_SPACES[selectedPreset] || []).map((param) => (
                    <Badge key={param.name} variant="secondary">
                      {param.name}
                      {param.param_type === 'int' || param.param_type === 'float'
                        ? ` [${param.low}-${param.high}]`
                        : ''}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Market Data Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Market Data
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Symbol Selection */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Trading Pair
                  </label>
                  <Select value={symbol} onValueChange={setSymbol}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_SYMBOLS.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Timeframe Selection */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Timeframe
                  </label>
                  <Select value={timeframe} onValueChange={setTimeframe}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_TIMEFRAMES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Select the trading pair and candlestick timeframe for backtesting. Different pairs have different volatility characteristics.
              </p>
            </CardContent>
          </Card>

          {/* Optimization Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Database className="h-4 w-4" />
                Optimization Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Number of Trials */}
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-sm font-medium">Number of Trials</label>
                  <span className="text-sm text-muted-foreground">{nTrials}</span>
                </div>
                <Slider
                  value={[nTrials]}
                  onValueChange={(values) => setNTrials(values[0])}
                  min={10}
                  max={500}
                  step={10}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  More trials = better optimization, but slower (recommended: 20-50 for testing, 100+ for production)
                </p>
              </div>

              {/* Market Data Days */}
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-sm font-medium">Historical Data (days)</label>
                  <span className="text-sm text-muted-foreground">{marketDataDays}</span>
                </div>
                <Slider
                  value={[marketDataDays]}
                  onValueChange={(values) => setMarketDataDays(values[0])}
                  min={210}
                  max={730}
                  step={30}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  More data = better validation, but slower (recommended: 180-365). Minimum 210 days required for walk-forward validation.
                </p>
              </div>

              {/* Objective Metric */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Objective Metric (What to Optimize)
                </label>
                <Select
                  value={objectiveMetric}
                  onValueChange={(value: any) => setObjectiveMetric(value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sharpe_ratio">
                      Sharpe Ratio (risk-adjusted returns)
                    </SelectItem>
                    <SelectItem value="total_return">
                      Total Return (absolute profit)
                    </SelectItem>
                    <SelectItem value="win_rate">
                      Win Rate (trade success %)
                    </SelectItem>
                    <SelectItem value="consistency_score">
                      Consistency Score (stable performance)
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Progress Display (while polling) */}
          {runningJobId && jobStatusQuery.data && (
            <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-blue-900 dark:text-blue-100">
                      {jobStatusQuery.data.status === 'pending' && 'Starting optimization...'}
                      {jobStatusQuery.data.status === 'loading_data' && 'Loading market data (3-5 seconds)...'}
                      {jobStatusQuery.data.status === 'running' && 'Optimization in progress'}
                      {jobStatusQuery.data.status === 'completed' && (
                        <>
                          <CheckCircle className="inline h-4 w-4 mr-1 text-green-600" />
                          Optimization completed!
                        </>
                      )}
                      {jobStatusQuery.data.status === 'failed' && 'Optimization failed'}
                    </div>
                    {jobStatusQuery.data.status === 'running' && (
                      <div className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                        Trial {jobStatusQuery.data.trials_completed} / {jobStatusQuery.data.trials_total}
                        {jobStatusQuery.data.best_score && (
                          <span className="ml-2">
                            • Best {objectiveMetric}: {parseFloat(jobStatusQuery.data.best_score).toFixed(4)}
                          </span>
                        )}
                      </div>
                    )}
                    {jobStatusQuery.data.error_message && (
                      <div className="text-sm text-destructive mt-1">
                        {jobStatusQuery.data.error_message}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Validation Error Display (Phase 6) */}
          {validationResponse && !validationResponse.is_valid && (
            <Card className="bg-destructive/10 border-destructive/30">
              <CardHeader>
                <CardTitle className="text-destructive flex items-center gap-2 text-base">
                  <AlertCircle className="h-5 w-5" />
                  Parameter Validation Failed ({validationResponse.invalid_count} {validationResponse.invalid_count === 1 ? 'error' : 'errors'})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {validationResponse.results
                    .filter(r => !r.is_valid)
                    .map((result) => (
                      <div key={result.name} className="bg-white dark:bg-gray-900 rounded-md p-3 border border-destructive/20">
                        <div className="font-medium text-sm">{result.name}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Path: <code className="bg-muted px-1 rounded">{result.path}</code>
                        </div>
                        <div className="text-sm text-destructive mt-2">
                          {result.error_message}
                        </div>
                      </div>
                    ))}
                  <div className="text-sm text-muted-foreground pt-2 border-t">
                    💡 These parameters cannot be optimized because their paths don't exist in the strategy.
                    Please contact support or select a different preset.
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Job Creation Error Display */}
          {startOptimizationMutation.isError && (
            <div className="flex items-start gap-2 p-4 bg-destructive/10 text-destructive rounded-lg">
              <AlertCircle className="h-5 w-5 mt-0.5" />
              <div>
                <div className="font-medium">Failed to Start Optimization</div>
                <div className="text-sm">
                  {startOptimizationMutation.error instanceof Error
                    ? startOptimizationMutation.error.message
                    : 'Unknown error occurred'}
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={validateParametersMutation.isPending || startOptimizationMutation.isPending || runningJobId !== null}
            >
              {runningJobId ? 'Close' : 'Cancel'}
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={validateParametersMutation.isPending || startOptimizationMutation.isPending || runningJobId !== null}
              className="min-w-32"
            >
              {validateParametersMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Validating...
                </>
              ) : startOptimizationMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Job...
                </>
              ) : runningJobId ? (
                <>
                  <Clock className="mr-2 h-4 w-4" />
                  Running...
                </>
              ) : (
                'Start Optimization'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

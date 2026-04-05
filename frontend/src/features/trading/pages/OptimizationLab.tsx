/**
 * Optimization Lab
 *
 * Lab-style view for ML parameter optimization.
 * Layout matches StrategyEditorPage: Fixed Header + Sidebar + Main Panel
 *
 * Sections:
 * - Configuration: Parameter space, market data, optimization settings
 * - Active Jobs: Monitor running optimization jobs
 * - Results: View completed optimization results
 * - History: Browse all past optimization jobs
 *
 * Part of Backtest Comprehensive Upgrade - Phase 4
 */

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { Slider } from '@/components/ui/slider'
import { Progress } from '@/components/ui/progress'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import {
  TrendingUp,
  Settings,
  Activity,
  Beaker,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  AlertCircle,
  Play,
  X,
  Database,
  RefreshCw,
  Eye,
  History,
  Zap,
  ChevronRight,
} from 'lucide-react'

import type {
  OptimizationJob,
  OptimizationRequest,
  OptimizationResult,
  ParameterSpaceItem,
  ValidateParametersRequest,
  ValidateParametersResponse,
} from '../types/optimization'
import {
  COMMON_PARAMETER_SPACES,
  PRESET_DESCRIPTIONS,
  AVAILABLE_SYMBOLS,
  AVAILABLE_TIMEFRAMES,
} from '../types/optimization'
import type { StrategyStats } from '../types/strategy'
import { OptimizationResultsView } from '../components/OptimizationResultsView'
import { predictionClient } from '@/lib/api-client'

// Sidebar sections
type LabSection = 'config' | 'active' | 'results' | 'history'

// Strategy configurations
const STRATEGIES = [
  {
    id: 'Freqtrade Adaptive Futures Strategy',
    name: 'Freqtrade Adaptive',
    description: 'Adaptive futures with regime-based logic',
  },
]

// Sidebar Component
function LabSidebar({
  activeSection,
  onSectionChange,
  runningJobsCount,
  completedJobsCount,
}: {
  activeSection: LabSection
  onSectionChange: (section: LabSection) => void
  runningJobsCount: number
  completedJobsCount: number
}) {
  const sections = [
    {
      id: 'config' as LabSection,
      label: 'Configuration',
      icon: Settings,
      description: 'Setup optimization',
    },
    {
      id: 'active' as LabSection,
      label: 'Active Jobs',
      icon: Zap,
      description: 'Monitor running',
      badge: runningJobsCount > 0 ? runningJobsCount : undefined,
    },
    {
      id: 'results' as LabSection,
      label: 'Results',
      icon: Eye,
      description: 'View details',
    },
    {
      id: 'history' as LabSection,
      label: 'History',
      icon: History,
      description: 'Past optimizations',
      badge: completedJobsCount > 0 ? completedJobsCount : undefined,
    },
  ]

  return (
    <aside className="w-[280px] border-r bg-muted/30 overflow-y-auto">
      <div className="p-4 space-y-2">
        {sections.map((section) => {
          const Icon = section.icon
          const isActive = activeSection === section.id

          return (
            <button
              key={section.id}
              onClick={() => onSectionChange(section.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">{section.label}</div>
                <div className={`text-xs ${isActive ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                  {section.description}
                </div>
              </div>
              {section.badge && (
                <Badge
                  variant={isActive ? 'secondary' : 'default'}
                  className="shrink-0"
                >
                  {section.badge}
                </Badge>
              )}
            </button>
          )
        })}
      </div>
    </aside>
  )
}

export default function OptimizationLab() {
  const queryClient = useQueryClient()

  // Navigation
  const [activeSection, setActiveSection] = useState<LabSection>('config')

  // Strategy selection
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>(STRATEGIES[0].id)
  const selectedStrategy = STRATEGIES.find((s) => s.id === selectedStrategyId)

  // Configuration state
  const [selectedPreset, setSelectedPreset] = useState<string>('RSI_Optimization')
  const [nTrials, setNTrials] = useState<number>(20)
  const [marketDataDays, setMarketDataDays] = useState<number>(210)
  const [objectiveMetric, setObjectiveMetric] = useState<
    'sharpe_ratio' | 'total_return' | 'win_rate' | 'consistency_score'
  >('sharpe_ratio')
  const [symbol, setSymbol] = useState<string>('BTCUSDT')
  const [timeframe, setTimeframe] = useState<string>('1h')

  // Job management
  const [runningJobId, setRunningJobId] = useState<string | null>(null)
  const [selectedResultJobId, setSelectedResultJobId] = useState<string | null>(null)

  // Validation state
  const [validationResponse, setValidationResponse] = useState<ValidateParametersResponse | null>(null)

  // Fetch strategy stats
  const { data: strategiesStats } = useQuery<Record<string, StrategyStats>>({
    queryKey: ['all-strategies-stats'],
    queryFn: async () => {
      const promises = STRATEGIES.map(async (strategy) => {
        try {
          const response = await predictionClient.get<StrategyStats>(
            `/strategies/${strategy.id}/stats`,
            { days: '7' }
          )
          return [strategy.id, response.data]
        } catch {
          return [strategy.id, null]
        }
      })
      const results = await Promise.all(promises)
      return Object.fromEntries(results.filter(([_, stats]) => stats !== null))
    },
    refetchInterval: 60000,
    retry: false,
    staleTime: 300000,
  })

  // Fetch optimization jobs
  const { data: jobs, isRefetching: isRefetchingJobs } = useQuery<OptimizationJob[]>({
    queryKey: ['optimization-jobs-lab'],
    queryFn: async () => {
      const response = await predictionClient.get<OptimizationJob[]>('/optimization/jobs', {
        limit: '50',
      })
      return response.data
    },
    refetchInterval: (query) => {
      const data = query.state.data
      const hasRunningJobs =
        Array.isArray(data) &&
        data.some((job) => job.status === 'running' || job.status === 'pending' || job.status === 'loading_data')
      return hasRunningJobs ? 2000 : 10000
    },
    retry: 2,
  })

  // Fetch job results when viewing details
  const { data: jobResults, isLoading: isLoadingResults } = useQuery<OptimizationResult | null>({
    queryKey: ['optimization-results', selectedResultJobId],
    queryFn: async () => {
      if (!selectedResultJobId) return null
      try {
        const response = await predictionClient.get<OptimizationResult>(
          `/optimization/jobs/${selectedResultJobId}/results`
        )
        return response.data
      } catch {
        return null
      }
    },
    enabled: !!selectedResultJobId,
  })

  // Poll for running job status
  const { data: runningJobStatus } = useQuery({
    queryKey: ['optimization-status', runningJobId],
    queryFn: async (): Promise<OptimizationJob> => {
      if (!runningJobId) throw new Error('No job ID')
      const response = await predictionClient.get<OptimizationJob>(
        `/optimization/jobs/${runningJobId}`
      )
      return response.data
    },
    enabled: runningJobId !== null,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 2000
      const status = data.status
      if (status === 'pending' || status === 'loading_data' || status === 'running') {
        return 2000
      }
      return false
    },
  })

  // Handle job completion
  useEffect(() => {
    const job = runningJobStatus
    if (job && (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled')) {
      setRunningJobId(null)
      queryClient.invalidateQueries({ queryKey: ['optimization-jobs-lab'] })
      if (job.status === 'completed') {
        setSelectedResultJobId(job.id)
        setActiveSection('results')
      }
    }
  }, [runningJobStatus, queryClient])

  // Validate parameters mutation
  const validateParametersMutation = useMutation({
    mutationFn: async (request: ValidateParametersRequest): Promise<ValidateParametersResponse> => {
      const response = await predictionClient.post<ValidateParametersResponse>(
        `/optimization/strategies/${selectedStrategyId}/validate-parameters`,
        request
      )
      return response.data
    },
    onSuccess: (response) => {
      setValidationResponse(response)
      if (response.is_valid) {
        const parameterSpace: ParameterSpaceItem[] =
          COMMON_PARAMETER_SPACES[selectedPreset] || COMMON_PARAMETER_SPACES.RSI_Optimization
        const request: OptimizationRequest = {
          parameter_space: parameterSpace,
          objective_metric: objectiveMetric,
          n_trials: nTrials,
          market_data_days: marketDataDays,
          symbol: symbol,
          timeframe: timeframe,
        }
        startOptimizationMutation.mutate(request)
      }
    },
  })

  // Start optimization mutation
  const startOptimizationMutation = useMutation({
    mutationFn: async (request: OptimizationRequest): Promise<OptimizationJob> => {
      const response = await predictionClient.post<OptimizationJob>(
        `/optimization/strategies/${selectedStrategyId}/optimize`,
        request
      )
      return response.data
    },
    onSuccess: (job) => {
      setRunningJobId(job.id)
      setValidationResponse(null)
      setActiveSection('active')
    },
  })

  // Cancel job mutation
  const cancelJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await predictionClient.delete(`/optimization/jobs/${jobId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['optimization-jobs-lab'] })
    },
  })

  const handleSubmit = () => {
    if (!selectedStrategyId) return

    const parameterSpace: ParameterSpaceItem[] =
      COMMON_PARAMETER_SPACES[selectedPreset] || COMMON_PARAMETER_SPACES.RSI_Optimization

    const validationRequest: ValidateParametersRequest = {
      parameter_space: parameterSpace,
    }

    validateParametersMutation.mutate(validationRequest)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-500" />
      case 'running':
      case 'loading_data':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-500" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  }

  const runningJobs = jobs?.filter((j) => j.status === 'running' || j.status === 'pending' || j.status === 'loading_data') || []
  const completedJobs = jobs?.filter((j) => j.status === 'completed') || []

  return (
    <div className="h-screen flex flex-col">
      {/* Fixed Header */}
      <header className="border-b bg-background px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4 flex-1">
          {/* Breadcrumbs */}
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/trading/backtest">Strategy Lab</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>ML Optimization Lab</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          {/* Running indicator */}
          {runningJobs.length > 0 && (
            <Badge variant="secondary" className="flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              {runningJobs.length} running
            </Badge>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            onClick={handleSubmit}
            disabled={
              validateParametersMutation.isPending ||
              startOptimizationMutation.isPending ||
              runningJobId !== null
            }
          >
            {validateParametersMutation.isPending || startOptimizationMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting...
              </>
            ) : runningJobId ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Start Optimization
              </>
            )}
          </Button>
        </div>
      </header>

      {/* Main Layout: Sidebar + Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <LabSidebar
          activeSection={activeSection}
          onSectionChange={setActiveSection}
          runningJobsCount={runningJobs.length}
          completedJobsCount={completedJobs.length}
        />

        {/* Main Panel */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            {/* Configuration Section */}
            {activeSection === 'config' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Optimization Configuration</h2>
                  <p className="text-muted-foreground mt-1">
                    Configure parameters for Bayesian optimization with walk-forward validation
                  </p>
                </div>

                {/* Strategy Selection */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      Strategy
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Select value={selectedStrategyId} onValueChange={setSelectedStrategyId}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {STRATEGIES.map((s) => (
                          <SelectItem key={s.id} value={s.id}>
                            {s.name} - {s.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </CardContent>
                </Card>

                {/* Parameter Space Selection */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Parameter Space
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Parameter Preset</label>
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
                      {PRESET_DESCRIPTIONS[selectedPreset] && (
                        <p className="text-sm text-muted-foreground mt-2">
                          {PRESET_DESCRIPTIONS[selectedPreset]}
                        </p>
                      )}
                    </div>

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
                    <CardTitle className="text-base flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      Market Data
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Trading Pair</label>
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
                      <div>
                        <label className="text-sm font-medium mb-2 block">Timeframe</label>
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
                  </CardContent>
                </Card>

                {/* Optimization Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      Optimization Settings
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
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
                        More trials = better optimization, but slower (20-50 for testing, 100+ for production)
                      </p>
                    </div>

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
                        Min 210 days required for walk-forward validation
                      </p>
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Objective Metric</label>
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
                          <SelectItem value="win_rate">Win Rate (trade success %)</SelectItem>
                          <SelectItem value="consistency_score">
                            Consistency Score (stable performance)
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>

                {/* Validation Error */}
                {validationResponse && !validationResponse.is_valid && (
                  <Card className="bg-destructive/10 border-destructive/30">
                    <CardHeader>
                      <CardTitle className="text-destructive flex items-center gap-2 text-base">
                        <AlertCircle className="h-5 w-5" />
                        Validation Failed
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {validationResponse.results
                          .filter((r) => !r.is_valid)
                          .map((result) => (
                            <div key={result.name} className="text-sm">
                              <span className="font-medium">{result.name}:</span>{' '}
                              {result.error_message}
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Active Jobs Section */}
            {activeSection === 'active' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Active Jobs</h2>
                  <p className="text-muted-foreground mt-1">
                    Monitor running optimization jobs in real-time
                  </p>
                </div>

                {runningJobs.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center">
                      <Zap className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-muted-foreground">No Active Jobs</h3>
                      <p className="text-sm text-muted-foreground/70 mt-2">
                        Start an optimization from the Configuration tab
                      </p>
                      <Button
                        variant="outline"
                        className="mt-4"
                        onClick={() => setActiveSection('config')}
                      >
                        Go to Configuration
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  runningJobs.map((job) => (
                    <Card key={job.id} className="border-blue-200 dark:border-blue-800">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                            <div>
                              <div className="font-medium">{job.strategy_id}</div>
                              <div className="text-sm text-muted-foreground">
                                Job ID: {job.id.slice(0, 8)}...
                              </div>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => cancelJobMutation.mutate(job.id)}
                          >
                            <X className="h-4 w-4 mr-1" />
                            Cancel
                          </Button>
                        </div>

                        <div className="space-y-3">
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Status</span>
                            <Badge variant="secondary">
                              {job.status === 'loading_data' ? 'Loading Data' : job.status}
                            </Badge>
                          </div>

                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-muted-foreground">Progress</span>
                              <span className="font-medium">
                                {job.trials_completed} / {job.trials_total} trials
                              </span>
                            </div>
                            <Progress value={job.progress_percentage} className="h-2" />
                          </div>

                          {job.best_score && (
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Best {job.objective_metric.replace('_', ' ')}</span>
                              <span className="font-medium text-green-600">
                                {parseFloat(job.best_score).toFixed(4)}
                              </span>
                            </div>
                          )}

                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Started</span>
                            <span>
                              {job.started_at
                                ? new Date(job.started_at).toLocaleTimeString()
                                : '-'}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            )}

            {/* Results Section */}
            {activeSection === 'results' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Optimization Results</h2>
                  <p className="text-muted-foreground mt-1">
                    View detailed results and apply optimized parameters
                  </p>
                </div>

                {isLoadingResults ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : selectedResultJobId && jobResults ? (
                  <OptimizationResultsView
                    result={jobResults}
                    jobId={selectedResultJobId}
                    onClose={() => setSelectedResultJobId(null)}
                  />
                ) : (
                  <Card>
                    <CardContent className="py-12 text-center">
                      <Eye className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-muted-foreground">No Results Selected</h3>
                      <p className="text-sm text-muted-foreground/70 mt-2">
                        Select a completed job from History to view its results
                      </p>
                      <Button
                        variant="outline"
                        className="mt-4"
                        onClick={() => setActiveSection('history')}
                      >
                        Browse History
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* History Section */}
            {activeSection === 'history' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold">Optimization History</h2>
                    <p className="text-muted-foreground mt-1">
                      Browse and compare past optimization runs
                    </p>
                  </div>
                  {isRefetchingJobs && (
                    <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
                  )}
                </div>

                {completedJobs.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center">
                      <History className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-muted-foreground">No History Yet</h3>
                      <p className="text-sm text-muted-foreground/70 mt-2">
                        Completed optimization jobs will appear here
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    {completedJobs.map((job) => (
                      <Card
                        key={job.id}
                        className={`cursor-pointer transition-all ${
                          selectedResultJobId === job.id
                            ? 'ring-2 ring-primary'
                            : 'hover:border-primary/50'
                        }`}
                        onClick={() => {
                          setSelectedResultJobId(job.id)
                          setActiveSection('results')
                        }}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                              {getStatusIcon(job.status)}
                              <div>
                                <div className="font-medium">{job.strategy_id}</div>
                                <div className="text-sm text-muted-foreground">
                                  {job.objective_metric.replace('_', ' ')} • {job.trials_completed} trials
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-medium text-green-600">
                                {job.best_score ? parseFloat(job.best_score).toFixed(4) : '-'}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {job.started_at
                                  ? new Date(job.started_at).toLocaleDateString()
                                  : '-'}
                              </div>
                            </div>
                          </div>

                          {job.best_params && Object.keys(job.best_params).length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-1">
                              {Object.entries(job.best_params)
                                .slice(0, 4)
                                .map(([key, value]) => (
                                  <Badge key={key} variant="outline" className="text-xs">
                                    {key}: {typeof value === 'number' ? value.toFixed(2) : value}
                                  </Badge>
                                ))}
                              {Object.keys(job.best_params).length > 4 && (
                                <Badge variant="outline" className="text-xs">
                                  +{Object.keys(job.best_params).length - 4} more
                                </Badge>
                              )}
                            </div>
                          )}

                          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                            <span>Duration: {job.duration_seconds > 0 ? formatDuration(job.duration_seconds) : '-'}</span>
                            <span className="flex items-center gap-1">
                              View Results <ChevronRight className="h-3 w-3" />
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

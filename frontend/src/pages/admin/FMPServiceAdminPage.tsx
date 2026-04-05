import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Activity, Database, TrendingUp, Settings, PlayCircle, PauseCircle, AlertCircle, CheckCircle2, Gauge, Layers, Search, Filter, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import * as fmpAdmin from '@/lib/api/fmpAdmin'
import * as fmpMarket from '@/lib/api/fmpMarket'
import { getSystemHealth, getApiCallStats } from '@/services/fmpApi'
import { useJobPerformance, useDataQuality, useDataGrowth } from '@/features/admin/fmp-service/hooks/useAdminStats'
import { JobPerformanceCard, DataQualityCard, DataGrowthChart } from '@/features/admin/fmp-service/components/monitoring'
import { HistoricalSyncForm } from '@/features/admin/fmp-service/components/operations'
import type { SystemHealth } from '@/types/fmp'

type FilterTier = 'all' | fmpMarket.TierLevel
type FilterAsset = 'all' | fmpMarket.AssetType

export function FMPServiceAdminPage() {
  const [activeTab, setActiveTab] = useState('operations')
  const queryClient = useQueryClient()

  // Tier Management State
  const [searchQuery, setSearchQuery] = useState('')
  const [filterTier, setFilterTier] = useState<FilterTier>('all')
  const [filterAsset, setFilterAsset] = useState<FilterAsset>('all')
  const [page, setPage] = useState(0)
  const [pageSize] = useState(50)

  // NEW: System health using new API client
  const { data: systemHealthResponse, isLoading: systemHealthLoading } = useQuery({
    queryKey: ['fmp-system-health'],
    queryFn: getSystemHealth,
    refetchInterval: 10000, // 10s
  })

  // NEW: API call stats using new API client
  const { data: apiCallStatsResponse, isLoading: apiStatsLoading } = useQuery({
    queryKey: ['fmp-api-call-stats'],
    queryFn: () => getApiCallStats('24h'),
    refetchInterval: 30000, // 30s
  })

  // Extract data from API responses (handle error case)
  const systemHealth: SystemHealth | undefined = systemHealthResponse?.data
  const apiCallStats = apiCallStatsResponse?.data

  // EXISTING: Admin queries (using existing axios client)
  const { data: schedulerStatus, isLoading: schedulerLoading } = useQuery({
    queryKey: ['fmp-scheduler-status'],
    queryFn: () => fmpAdmin.getSchedulerStatus().then(res => res.data),
    refetchInterval: 10000, // 10s
  })

  const { data: dbStats, isLoading: dbLoading } = useQuery({
    queryKey: ['fmp-database-stats'],
    queryFn: () => fmpAdmin.getDatabaseStats().then(res => res.data),
    refetchInterval: 30000, // 30s
  })

  const { data: apiUsage, isLoading: apiLoading } = useQuery({
    queryKey: ['fmp-api-usage'],
    queryFn: () => fmpAdmin.getAPIUsage(7).then(res => res.data),
    refetchInterval: 30000,
  })

  const { data: serviceHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['fmp-service-health'],
    queryFn: () => fmpAdmin.getServiceHealth().then(res => res.data),
    refetchInterval: 10000,
  })

  const { data: rateLimitStats, isLoading: rateLimitLoading } = useQuery({
    queryKey: ['fmp-rate-limit-stats'],
    queryFn: () => fmpAdmin.getRateLimitStats().then(res => res.data),
    refetchInterval: 2000, // 2s - faster for real-time monitoring
  })

  // New Admin Stats Hooks
  const { data: jobPerformance, isLoading: jobPerfLoading, error: jobPerfError } = useJobPerformance()
  const { data: dataQuality, isLoading: dataQualityLoading, error: dataQualityError } = useDataQuality()
  const { data: dataGrowth, isLoading: dataGrowthLoading, error: dataGrowthError } = useDataGrowth({ days: 30 })

  // Mutations
  const pauseSchedulerMut = useMutation({
    mutationFn: fmpAdmin.pauseScheduler,
    onSuccess: () => {
      toast.success('Scheduler paused')
      queryClient.invalidateQueries({ queryKey: ['fmp-scheduler-status'] })
    },
    onError: () => toast.error('Failed to pause scheduler'),
  })

  const resumeSchedulerMut = useMutation({
    mutationFn: fmpAdmin.resumeScheduler,
    onSuccess: () => {
      toast.success('Scheduler resumed')
      queryClient.invalidateQueries({ queryKey: ['fmp-scheduler-status'] })
    },
    onError: () => toast.error('Failed to resume scheduler'),
  })

  const pauseJobMut = useMutation({
    mutationFn: (jobId: string) => fmpAdmin.pauseJob(jobId),
    onSuccess: () => {
      toast.success('Job paused')
      queryClient.invalidateQueries({ queryKey: ['fmp-scheduler-status'] })
    },
  })

  const resumeJobMut = useMutation({
    mutationFn: (jobId: string) => fmpAdmin.resumeJob(jobId),
    onSuccess: () => {
      toast.success('Job resumed')
      queryClient.invalidateQueries({ queryKey: ['fmp-scheduler-status'] })
    },
  })

  const triggerMarketSyncMut = useMutation({
    mutationFn: fmpAdmin.triggerMarketSync,
    onSuccess: () => {
      toast.success('Market sync triggered successfully! Check logs for progress.')
      queryClient.invalidateQueries({ queryKey: ['fmp-scheduler-status'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to trigger market sync')
    },
  })

  // Tier Management Queries
  const { data: tierStats, isLoading: tierStatsLoading } = useQuery({
    queryKey: ['tier-statistics'],
    queryFn: fmpMarket.getTierStatistics,
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: symbolsData, isLoading: symbolsLoading } = useQuery({
    queryKey: ['tier-symbols', filterTier, filterAsset, searchQuery, page, pageSize],
    queryFn: () => fmpMarket.listSymbols({
      tier: filterTier === 'all' ? undefined : filterTier,
      asset_type: filterAsset === 'all' ? undefined : filterAsset,
      search: searchQuery || undefined,
      limit: pageSize,
      offset: page * pageSize,
    }),
    keepPreviousData: true,
  })

  const reloadConfigMut = useMutation({
    mutationFn: fmpMarket.reloadTierConfig,
    onSuccess: () => {
      toast.success('Configuration reloaded successfully!')
      queryClient.invalidateQueries({ queryKey: ['tier-statistics'] })
      queryClient.invalidateQueries({ queryKey: ['tier-symbols'] })
    },
    onError: () => toast.error('Failed to reload configuration'),
  })

  // Calculate total pages
  const totalPages = useMemo(() => {
    if (!symbolsData) return 0
    return Math.ceil(symbolsData.total / pageSize)
  }, [symbolsData, pageSize])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">FMP Service Administration</h1>
        <p className="text-muted-foreground">
          Monitor scheduler, database stats, API usage, and manage data synchronization
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="operations" className="gap-2">
            <Activity className="h-4 w-4" />
            Live Operations
          </TabsTrigger>
          <TabsTrigger value="management" className="gap-2">
            <Settings className="h-4 w-4" />
            Management
          </TabsTrigger>
          <TabsTrigger value="tiers" className="gap-2">
            <Layers className="h-4 w-4" />
            Tier Management
          </TabsTrigger>
        </TabsList>

        {/* Live Operations Tab */}
        <TabsContent value="operations" className="space-y-4">
          {/* NEW: System Health Card - Using new API */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {systemHealth?.status === 'healthy' ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : systemHealth?.status === 'degraded' ? (
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
                System Health
              </CardTitle>
              <CardDescription>
                Status: {systemHealth?.status || 'unknown'} • Updated: {systemHealth?.timestamp ? new Date(systemHealth.timestamp).toLocaleTimeString() : 'N/A'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {systemHealthLoading ? (
                <div className="h-32 bg-muted animate-pulse rounded"></div>
              ) : systemHealthResponse?.error ? (
                <div className="text-sm text-red-500">Error: {systemHealthResponse.error}</div>
              ) : systemHealth ? (
                <div className="space-y-4">
                  {/* Database Status */}
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Database</div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Status</span>
                        <div className="flex items-center gap-2">
                          {systemHealth.database.connected ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          )}
                          <span>{systemHealth.database.connected ? 'Connected' : 'Disconnected'}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Latency</span>
                        <span className="font-mono">{systemHealth.database.latency_ms?.toFixed(2) || 'N/A'} ms</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Pool Size</span>
                        <span className="font-mono">{systemHealth.database.pool_size || 'N/A'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Available</span>
                        <span className="font-mono">{systemHealth.database.pool_available || 'N/A'}</span>
                      </div>
                    </div>
                  </div>

                  {/* API Quota */}
                  <div className="space-y-2">
                    <div className="text-sm font-medium">API Quota</div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Daily Usage</span>
                        <span className="font-mono">
                          {systemHealth.api_quota.daily_used.toLocaleString()} / {systemHealth.api_quota.daily_limit.toLocaleString()}
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            systemHealth.api_quota.usage_percentage > 90 ? 'bg-red-500' :
                            systemHealth.api_quota.usage_percentage > 70 ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(100, systemHealth.api_quota.usage_percentage)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>{systemHealth.api_quota.usage_percentage.toFixed(1)}% used</span>
                        <span>Resets: {new Date(systemHealth.api_quota.resets_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Workers */}
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Background Workers</div>
                    <div className="space-y-1">
                      {systemHealth.workers.map((worker) => (
                        <div key={worker.name} className="flex items-center justify-between p-2 rounded border text-sm">
                          <span>{worker.name}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant={worker.status === 'running' ? 'default' : 'secondary'}>
                              {worker.status}
                            </Badge>
                            {worker.last_heartbeat && (
                              <span className="text-xs text-muted-foreground">
                                {new Date(worker.last_heartbeat).toLocaleTimeString()}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          {/* Rate Limit Warning Card - Full Width */}
          <Card className={
            rateLimitStats?.status === 'critical' ? 'border-red-500' :
            rateLimitStats?.status === 'warning' ? 'border-yellow-500' : ''
          }>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gauge className="h-5 w-5" />
                Rate Limit Monitor
                {rateLimitStats?.status === 'critical' && (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
                {rateLimitStats?.status === 'warning' && (
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                )}
              </CardTitle>
              <CardDescription>
                {rateLimitStats?.current_calls || 0} / {rateLimitStats?.limit || 300} calls in last minute
              </CardDescription>
            </CardHeader>
            <CardContent>
              {rateLimitLoading ? (
                <div className="h-20 bg-muted animate-pulse rounded"></div>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Current Usage</span>
                      <span className={`font-medium ${
                        rateLimitStats?.status === 'critical' ? 'text-red-500' :
                        rateLimitStats?.status === 'warning' ? 'text-yellow-500' :
                        'text-green-500'
                      }`}>
                        {rateLimitStats?.percentage || 0}%
                      </span>
                    </div>
                    <div className="h-3 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          rateLimitStats?.status === 'critical' ? 'bg-red-500' :
                          rateLimitStats?.status === 'warning' ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(100, rateLimitStats?.percentage || 0)}%` }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Current</div>
                      <div className="text-lg font-semibold">{rateLimitStats?.current_calls || 0}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Remaining</div>
                      <div className="text-lg font-semibold">{rateLimitStats?.remaining || 0}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Limit</div>
                      <div className="text-lg font-semibold">{rateLimitStats?.limit || 300}/min</div>
                    </div>
                  </div>
                  {rateLimitStats?.status === 'critical' && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-sm text-red-600 dark:text-red-400">
                      ⚠️ <strong>CRITICAL:</strong> Rate limit at {rateLimitStats.percentage}%. Reduce API calls immediately!
                    </div>
                  )}
                  {rateLimitStats?.status === 'warning' && (
                    <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded text-sm text-yellow-600 dark:text-yellow-400">
                      ⚠️ <strong>WARNING:</strong> Rate limit at {rateLimitStats.percentage}%. Monitor closely.
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            {/* Scheduler Status Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Scheduler Status
                </CardTitle>
                <CardDescription>
                  {schedulerStatus?.running ? 'Active' : 'Stopped'} • {schedulerStatus?.total_jobs || 0} jobs
                </CardDescription>
              </CardHeader>
              <CardContent>
                {schedulerLoading ? (
                  <div className="h-64 bg-muted animate-pulse rounded"></div>
                ) : (
                  <div className="space-y-2">
                    {schedulerStatus?.jobs.map((job: any) => (
                      <div key={job.id} className="flex items-center justify-between p-2 rounded border">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{job.name}</div>
                          <div className="text-xs text-muted-foreground">
                            Next: {job.next_run ? new Date(job.next_run).toLocaleString() : 'N/A'}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={job.status === 'running' ? 'default' : 'secondary'}>
                            {job.status}
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              if (job.status === 'running') {
                                pauseJobMut.mutate(job.id)
                              } else {
                                resumeJobMut.mutate(job.id)
                              }
                            }}
                            aria-label={job.status === 'running' ? `Pause ${job.name}` : `Resume ${job.name}`}
                          >
                            {job.status === 'running' ? (
                              <PauseCircle className="h-4 w-4" />
                            ) : (
                              <PlayCircle className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* API Usage Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  API Usage
                </CardTitle>
                <CardDescription>
                  {(apiUsage?.today_estimate || 0).toLocaleString()} / {(apiUsage?.limit || 0).toLocaleString()} calls today
                </CardDescription>
              </CardHeader>
              <CardContent>
                {apiLoading ? (
                  <div className="h-32 bg-muted animate-pulse rounded"></div>
                ) : (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Usage</span>
                        <span className="font-medium">
                          {((apiUsage?.today_estimate || 0) / (apiUsage?.limit || 300) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${((apiUsage?.today_estimate || 0) / (apiUsage?.limit || 300) * 100)}%` }}
                        />
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {(apiUsage?.remaining_estimate || 0).toLocaleString()} calls remaining today
                    </div>
                    {apiUsage?.note && (
                      <div className="text-xs text-muted-foreground italic">{apiUsage.note}</div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Database Stats Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Database Statistics
                </CardTitle>
                <CardDescription>
                  {dbStats?.total_rows.toLocaleString() || 0} total records
                </CardDescription>
              </CardHeader>
              <CardContent>
                {dbLoading ? (
                  <div className="h-64 bg-muted animate-pulse rounded"></div>
                ) : (
                  <div className="space-y-1 max-h-64 overflow-y-auto">
                    {dbStats?.tables.map((table: any) => (
                      <div key={table.table} className="flex justify-between text-sm p-1">
                        <span className="text-muted-foreground">{table.table}</span>
                        <span className="font-medium">{table.rows.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Service Health Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {serviceHealth?.status === 'healthy' ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  Service Health
                </CardTitle>
                <CardDescription>
                  Status: {serviceHealth?.status || 'unknown'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {healthLoading ? (
                  <div className="h-32 bg-muted animate-pulse rounded"></div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Database</span>
                      {serviceHealth?.database_connected ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">FMP API</span>
                      {serviceHealth?.fmp_api_reachable ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Scheduler</span>
                      {serviceHealth?.scheduler_running ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* New Monitoring Components - Full Width */}
          <JobPerformanceCard
            data={jobPerformance}
            isLoading={jobPerfLoading}
            error={jobPerfError}
          />

          <DataQualityCard
            data={dataQuality}
            isLoading={dataQualityLoading}
            error={dataQualityError}
          />

          <DataGrowthChart
            data={dataGrowth}
            isLoading={dataGrowthLoading}
            error={dataGrowthError}
            days={30}
          />
        </TabsContent>

        {/* Management Tab */}
        <TabsContent value="management" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Scheduler Controls</CardTitle>
              <CardDescription>Pause or resume the entire scheduler</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button
                  onClick={() => pauseSchedulerMut.mutate()}
                  disabled={!schedulerStatus?.running || schedulerStatus?.paused || pauseSchedulerMut.isPending}
                  variant="destructive"
                >
                  <PauseCircle className="h-4 w-4 mr-2" />
                  Pause All Jobs
                </Button>
                <Button
                  onClick={() => resumeSchedulerMut.mutate()}
                  disabled={!schedulerStatus?.running || !schedulerStatus?.paused || resumeSchedulerMut.isPending}
                >
                  <PlayCircle className="h-4 w-4 mr-2" />
                  Resume All Jobs
                </Button>
              </div>
              {schedulerStatus?.paused && (
                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded text-sm">
                  ⚠️ Scheduler is currently paused. Click "Resume All Jobs" to continue data synchronization.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Historical Data Sync Form */}
          <HistoricalSyncForm />

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Market Data Sync
              </CardTitle>
              <CardDescription>
                Event-driven market data synchronization to Knowledge Graph (Neo4j)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="text-sm font-medium">Background Job Status</div>
                <div className="text-sm text-muted-foreground">
                  Runs every 15 minutes, publishes market data events to RabbitMQ for automatic Neo4j sync.
                </div>
                {schedulerStatus?.jobs.find((j: any) => j.id === 'market_sync') ? (
                  <div className="flex items-center gap-2 p-2 rounded border">
                    <div className="flex-1">
                      <div className="font-medium text-sm">Market Sync Job</div>
                      <div className="text-xs text-muted-foreground">
                        Next: {schedulerStatus.jobs.find((j: any) => j.id === 'market_sync')?.next_run
                          ? new Date(schedulerStatus.jobs.find((j: any) => j.id === 'market_sync').next_run).toLocaleString()
                          : 'N/A'}
                      </div>
                    </div>
                    <Badge variant="default">running</Badge>
                  </div>
                ) : (
                  <div className="text-xs text-muted-foreground italic">
                    Job not found in scheduler (check backend logs)
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="text-sm font-medium">Manual Trigger</div>
                <div className="text-sm text-muted-foreground mb-2">
                  Manually trigger market data sync to Neo4j. Publishes 40 market events (10 per asset type: STOCK, FOREX, COMMODITY, CRYPTO).
                </div>
                <Button
                  onClick={() => triggerMarketSyncMut.mutate()}
                  disabled={triggerMarketSyncMut.isPending}
                  className="w-full"
                >
                  {triggerMarketSyncMut.isPending ? (
                    <>
                      <Activity className="h-4 w-4 mr-2 animate-spin" />
                      Triggering Market Sync...
                    </>
                  ) : (
                    <>
                      <Activity className="h-4 w-4 mr-2" />
                      Trigger Market Sync Now
                    </>
                  )}
                </Button>
              </div>

              <div className="space-y-2">
                <div className="text-sm font-medium">Event Flow</div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <div>1. FMP Service publishes market data events to RabbitMQ</div>
                  <div>2. RabbitMQ routes events via "finance" exchange</div>
                  <div>3. Knowledge-Graph Service consumes events</div>
                  <div>4. Market data synced to Neo4j MARKET nodes</div>
                </div>
              </div>

              {serviceHealth?.circuit_breaker && (
                <div className="space-y-2">
                  <div className="text-sm font-medium">Circuit Breaker</div>
                  <div className="flex items-center gap-2">
                    <Badge variant={
                      serviceHealth.circuit_breaker.state === 'closed' ? 'default' :
                      serviceHealth.circuit_breaker.state === 'open' ? 'destructive' : 'secondary'
                    }>
                      {serviceHealth.circuit_breaker.state}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {serviceHealth.circuit_breaker.failure_count || 0} failures
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tier Management Tab */}
        <TabsContent value="tiers" className="space-y-4">
          {/* Tier Statistics Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Tier 1</CardTitle>
                <CardDescription>1-min OHLCV</CardDescription>
              </CardHeader>
              <CardContent>
                {tierStatsLoading ? (
                  <div className="h-16 bg-muted animate-pulse rounded"></div>
                ) : (
                  <div className="space-y-2">
                    <div className="text-2xl font-bold">
                      {tierStats?.tier1_actual || 0} / {tierStats?.tier1_configured || 0}
                    </div>
                    <div className="flex items-center gap-2">
                      {tierStats?.tier1_synced ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      <span className="text-xs text-muted-foreground">
                        {tierStats?.tier1_synced ? 'Synced' : 'Partial'}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tier 2</CardTitle>
                <CardDescription>5-min OHLCV</CardDescription>
              </CardHeader>
              <CardContent>
                {tierStatsLoading ? (
                  <div className="h-16 bg-muted animate-pulse rounded"></div>
                ) : (
                  <div className="space-y-2">
                    <div className="text-2xl font-bold">
                      {tierStats?.tier2_actual || 0} / {tierStats?.tier2_configured || 0}
                    </div>
                    <div className="flex items-center gap-2">
                      {tierStats?.tier2_synced ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      <span className="text-xs text-muted-foreground">
                        {tierStats?.tier2_synced ? 'Synced' : 'Partial'}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tier 3</CardTitle>
                <CardDescription>1-min quotes</CardDescription>
              </CardHeader>
              <CardContent>
                {tierStatsLoading ? (
                  <div className="h-16 bg-muted animate-pulse rounded"></div>
                ) : (
                  <div className="space-y-2">
                    <div className="text-2xl font-bold">
                      {tierStats?.tier3_actual || 0} / {tierStats?.tier3_configured || 0}
                    </div>
                    <div className="flex items-center gap-2">
                      {tierStats?.tier3_synced ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      <span className="text-xs text-muted-foreground">
                        {tierStats?.tier3_synced ? 'Synced' : 'Partial'}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Symbol Management Card */}
          <Card>
            <CardHeader>
              <CardTitle>Symbol Management</CardTitle>
              <CardDescription>
                Browse and search configured symbols ({symbolsData?.total || 0} total)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search and Filters */}
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search symbols..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value)
                      setPage(0)
                    }}
                    className="w-full pl-10 pr-4 py-2 border rounded-md bg-background"
                  />
                </div>
                <select
                  value={filterTier}
                  onChange={(e) => {
                    setFilterTier(e.target.value as FilterTier)
                    setPage(0)
                  }}
                  className="px-4 py-2 border rounded-md bg-background"
                >
                  <option value="all">All Tiers</option>
                  <option value="tier1">Tier 1</option>
                  <option value="tier2">Tier 2</option>
                  <option value="tier3">Tier 3</option>
                </select>
                <select
                  value={filterAsset}
                  onChange={(e) => {
                    setFilterAsset(e.target.value as FilterAsset)
                    setPage(0)
                  }}
                  className="px-4 py-2 border rounded-md bg-background"
                >
                  <option value="all">All Assets</option>
                  <option value="crypto">Crypto</option>
                  <option value="forex">Forex</option>
                  <option value="indices">Indices</option>
                  <option value="commodities">Commodities</option>
                </select>
                <Button
                  onClick={() => reloadConfigMut.mutate()}
                  disabled={reloadConfigMut.isPending}
                  variant="outline"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${reloadConfigMut.isPending ? 'animate-spin' : ''}`} />
                  Reload Config
                </Button>
              </div>

              {/* Symbols Table */}
              {symbolsLoading ? (
                <div className="h-64 bg-muted animate-pulse rounded"></div>
              ) : symbolsData && symbolsData.symbols.length > 0 ? (
                <div className="border rounded-md">
                  <table className="w-full">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium">Symbol</th>
                        <th className="px-4 py-2 text-left text-xs font-medium">Tier</th>
                        <th className="px-4 py-2 text-left text-xs font-medium">Asset Type</th>
                        <th className="px-4 py-2 text-left text-xs font-medium">Interval</th>
                        <th className="px-4 py-2 text-left text-xs font-medium">Status</th>
                        <th className="px-4 py-2 text-left text-xs font-medium">Last Update</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {symbolsData.symbols.map((symbol) => (
                        <tr key={symbol.symbol} className="hover:bg-muted/50">
                          <td className="px-4 py-2 font-mono font-semibold">{symbol.symbol}</td>
                          <td className="px-4 py-2">
                            <Badge variant={
                              symbol.tier === 'tier1' ? 'default' :
                              symbol.tier === 'tier2' ? 'secondary' : 'outline'
                            }>
                              {symbol.tier.toUpperCase()}
                            </Badge>
                          </td>
                          <td className="px-4 py-2">
                            <span className="text-sm capitalize">{symbol.asset_type}</span>
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">{symbol.interval}</td>
                          <td className="px-4 py-2">
                            {symbol.in_database ? (
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                            ) : (
                              <AlertCircle className="h-4 w-4 text-yellow-500" />
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            {symbol.last_update ? new Date(symbol.last_update).toLocaleString() : 'Never'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No symbols found matching your filters
                </div>
              )}

              {/* Pagination */}
              {symbolsData && totalPages > 1 && (
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, symbolsData.total)} of {symbolsData.total}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setPage(p => Math.max(0, p - 1))}
                      disabled={page === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                      disabled={page >= totalPages - 1}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Important Note */}
          <Card className="border-yellow-500/50 bg-yellow-500/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
                <AlertCircle className="h-5 w-5" />
                Important Note
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>
                <strong>Validation Mode:</strong> API endpoints currently validate changes but do NOT modify the JSON configuration file.
              </p>
              <p>
                To add/remove/update symbols, manually edit: <code className="bg-muted px-1 py-0.5 rounded">services/fmp-service/app/config/symbol_tiers.json</code>
              </p>
              <p>
                After editing, click <strong>"Reload Config"</strong> to apply changes.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

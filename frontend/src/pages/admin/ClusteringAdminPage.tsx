import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Loader2, Play, CheckCircle2, XCircle, Clock, Info } from 'lucide-react'
import { clusteringAdminApi, type ClusteringTriggerRequest } from '@/api/clusteringAdmin'
import toast from 'react-hot-toast'

export function ClusteringAdminPage() {
  const queryClient = useQueryClient()

  // Form state
  const [hours, setHours] = useState(24)
  const [minSamples, setMinSamples] = useState(3)
  const [eps, setEps] = useState(0.55)

  // Active task tracking
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)

  // Fetch clustering status (config, params, intervals)
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['clustering', 'status'],
    queryFn: () => clusteringAdminApi.getClusteringStatus(),
    refetchInterval: 30000, // Refresh every 30s
  })

  // Poll active task status
  const { data: taskStatus, isLoading: taskLoading } = useQuery({
    queryKey: ['clustering', 'task', activeTaskId],
    queryFn: () => clusteringAdminApi.getTaskStatus(activeTaskId!),
    enabled: !!activeTaskId,
    refetchInterval: (query) => {
      // Poll every 2s while task is running
      const status = query.state.data?.status
      if (status === 'PENDING' || status === 'STARTED' || status === 'RETRY') {
        return 2000
      }
      // Stop polling when done
      return false
    },
  })

  // Trigger clustering mutation
  const triggerMutation = useMutation({
    mutationFn: (params: ClusteringTriggerRequest) => clusteringAdminApi.triggerClustering(params),
    onSuccess: (data) => {
      setActiveTaskId(data.task_id)
      toast.success(`Clustering started: ${data.task_id}`)
      queryClient.invalidateQueries({ queryKey: ['clustering', 'status'] })
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || error.message || 'Failed to trigger clustering'
      toast.error(message)
    },
  })

  // Handle form submission
  const handleTrigger = () => {
    triggerMutation.mutate({ hours, min_samples: minSamples, eps })
  }

  // Validation
  const isValid =
    hours >= 1 &&
    hours <= 168 &&
    minSamples >= 2 &&
    minSamples <= 50 &&
    eps >= 0.1 &&
    eps <= 1.0

  // Task status badge
  const renderTaskStatus = () => {
    if (!taskStatus) return null

    const statusConfig = {
      PENDING: { color: 'bg-blue-500', icon: Clock, label: 'Pending' },
      STARTED: { color: 'bg-yellow-500', icon: Loader2, label: 'Running' },
      SUCCESS: { color: 'bg-green-500', icon: CheckCircle2, label: 'Completed' },
      FAILURE: { color: 'bg-red-500', icon: XCircle, label: 'Failed' },
      RETRY: { color: 'bg-orange-500', icon: Clock, label: 'Retrying' },
    }

    const config = statusConfig[taskStatus.status] || statusConfig.PENDING
    const Icon = config.icon

    return (
      <Badge className={`${config.color} text-white`}>
        <Icon className="h-3 w-3 mr-1" />
        {config.label}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Clustering Administration</h1>
        <p className="text-muted-foreground">
          Manual clustering control with custom parameters
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Section 1: Current Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Current Configuration</CardTitle>
            <CardDescription>Active clustering parameters and schedule</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {statusLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : status ? (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">Algorithm</Label>
                    <p className="font-medium">{status.current_config.algorithm}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Metric</Label>
                    <p className="font-medium">{status.current_config.metric}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Hours</Label>
                    <p className="font-medium">{status.current_config.default_hours}h</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Min Samples</Label>
                    <p className="font-medium">{status.current_config.default_min_samples}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Epsilon</Label>
                    <p className="font-medium">{status.current_config.default_eps}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Schedule</Label>
                    <p className="font-medium text-xs">{status.scheduled_interval}</p>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-sm text-destructive">Failed to load configuration</p>
            )}
          </CardContent>
        </Card>

        {/* Section 2: Manual Trigger */}
        <Card>
          <CardHeader>
            <CardTitle>Manual Trigger</CardTitle>
            <CardDescription>Run clustering with custom parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="hours">Hours (1-168)</Label>
              <Input
                id="hours"
                type="number"
                min={1}
                max={168}
                value={hours}
                onChange={(e) => setHours(parseInt(e.target.value) || 1)}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Process events from last N hours
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="minSamples">Min Samples (2-50)</Label>
              <Input
                id="minSamples"
                type="number"
                min={2}
                max={50}
                value={minSamples}
                onChange={(e) => setMinSamples(parseInt(e.target.value) || 2)}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Minimum events required to form a cluster
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="eps">Epsilon (0.1-1.0)</Label>
              <Input
                id="eps"
                type="number"
                min={0.1}
                max={1.0}
                step={0.01}
                value={eps}
                onChange={(e) => setEps(parseFloat(e.target.value) || 0.1)}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                DBSCAN epsilon parameter for cosine distance. Lower = stricter clustering.
              </p>
            </div>

            <Button
              onClick={handleTrigger}
              disabled={!isValid || triggerMutation.isPending}
              className="w-full"
            >
              {triggerMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Trigger Clustering
                </>
              )}
            </Button>

            {!isValid && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Please enter valid parameters within the allowed ranges.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Section 3: Active Task Status */}
      {activeTaskId && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Active Task
              {renderTaskStatus()}
            </CardTitle>
            <CardDescription>Task ID: {activeTaskId}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {taskLoading && !taskStatus ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : taskStatus ? (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">Status</Label>
                    <p className="font-medium">{taskStatus.status}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Task ID</Label>
                    <p className="font-mono text-xs">{taskStatus.task_id}</p>
                  </div>
                </div>

                {taskStatus.status === 'SUCCESS' && taskStatus.result && (
                  <Alert className="bg-green-50 border-green-200">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-900">
                      <strong>Clustering completed successfully</strong>
                      {taskStatus.result.total_events_processed !== undefined && (
                        <div className="mt-2 space-y-1 text-xs">
                          <div>Events processed: {taskStatus.result.total_events_processed}</div>
                          <div>Clusters created: {taskStatus.result.clusters_created || 0}</div>
                          <div>Duration: {taskStatus.result.duration_seconds}s</div>
                        </div>
                      )}
                    </AlertDescription>
                  </Alert>
                )}

                {taskStatus.status === 'FAILURE' && taskStatus.result && (
                  <Alert className="bg-red-50 border-red-200">
                    <XCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-900">
                      <strong>Clustering failed</strong>
                      <p className="mt-1 text-xs">{String(taskStatus.result)}</p>
                    </AlertDescription>
                  </Alert>
                )}
              </>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* Section 4: Parameter Reference */}
      {status && (
        <Card>
          <CardHeader>
            <CardTitle>Parameter Reference</CardTitle>
            <CardDescription>Allowed ranges and descriptions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(status.available_parameters).map(([param, config]) => (
                <div key={param} className="border-l-4 border-primary pl-4">
                  <h4 className="font-medium capitalize">{param.replace('_', ' ')}</h4>
                  <p className="text-sm text-muted-foreground mt-1">{config.description}</p>
                  <div className="mt-2 flex gap-4 text-xs">
                    <span>Min: <strong>{config.min}</strong></span>
                    <span>Max: <strong>{config.max}</strong></span>
                    <span>Default: <strong>{config.default}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

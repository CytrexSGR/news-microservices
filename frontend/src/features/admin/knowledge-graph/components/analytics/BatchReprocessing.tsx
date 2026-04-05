import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  RefreshCw,
  Play,
  StopCircle,
  CheckCircle2,
  XCircle,
  Info,
  AlertTriangle,
} from 'lucide-react'
import { useReprocessingStatus } from '../../hooks/useReprocessingStatus'
import { startBatchReprocessing, stopBatchReprocessing } from '@/lib/api/canonicalizationAdmin'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

const phaseLabels = {
  analyzing: 'Analyzing Entities',
  fuzzy_matching: 'Fuzzy Matching',
  semantic_matching: 'Semantic Matching',
  wikidata_lookup: 'Wikidata Lookup',
  merging: 'Merging Duplicates',
  updating: 'Updating Database',
}

export function BatchReprocessing() {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [dryRun, setDryRun] = useState(false)
  const [forcePolling, setForcePolling] = useState(false)
  const queryClient = useQueryClient()

  // Fetch status (polls every 2s when running or force polling)
  const { data: status, isLoading } = useReprocessingStatus(true, forcePolling ? 1000 : undefined)

  // Start mutation
  const startMutation = useMutation({
    mutationFn: () => startBatchReprocessing(dryRun),
    onSuccess: () => {
      // Force polling for 30 seconds to catch fast jobs
      setForcePolling(true)
      setTimeout(() => setForcePolling(false), 30000)

      // Invalidate status query to trigger immediate refetch
      queryClient.invalidateQueries({ queryKey: ['canonicalization', 'reprocessing-status'] })
      queryClient.invalidateQueries({ queryKey: ['canonicalization', 'detailed-stats'] })
      setShowConfirmDialog(false)
    },
  })

  // Stop mutation
  const stopMutation = useMutation({
    mutationFn: stopBatchReprocessing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['canonicalization', 'reprocessing-status'] })
    },
  })

  const handleStart = () => {
    setShowConfirmDialog(true)
  }

  const handleConfirmStart = () => {
    startMutation.mutate()
  }

  const handleStop = () => {
    stopMutation.mutate()
  }

  const isRunning = status?.status === 'running'
  const isCompleted = status?.status === 'completed'
  const isFailed = status?.status === 'failed'
  const isIdle = !status || status.status === 'idle'

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Batch Reprocessing
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-sm">
                    Reprocess all existing entities through the canonicalization pipeline
                    to find duplicates, add missing Wikidata Q-IDs, and improve data quality.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Idle State - Start Button */}
          {isIdle && (
            <>
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  <p className="font-medium mb-2">What will be processed:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Find and merge duplicate entities (e.g., "USA" → "United States")</li>
                    <li>Add missing Wikidata Q-IDs (~26% entities need Q-IDs)</li>
                    <li>Apply fuzzy and semantic matching to historical data</li>
                    <li>Improve deduplication ratio and data quality</li>
                  </ul>
                </AlertDescription>
              </Alert>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={(e) => setDryRun(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300"
                  />
                  <span>Dry Run (preview only, no changes)</span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-3 w-3 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-sm">Shows what would be changed without saving</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </label>
              </div>

              <Button
                onClick={handleStart}
                disabled={startMutation.isPending || isLoading}
                className="w-full"
                size="lg"
              >
                <Play className="h-4 w-4 mr-2" />
                {dryRun ? 'Start Dry Run' : 'Start Batch Reprocessing'}
              </Button>
            </>
          )}

          {/* Running State - Progress */}
          {isRunning && status && (
            <>
              {/* Current Phase */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                    <span className="text-sm font-medium">
                      {status.current_phase && phaseLabels[status.current_phase]}
                    </span>
                  </div>
                  {status.dry_run && (
                    <Badge variant="outline" className="text-xs">
                      DRY RUN
                    </Badge>
                  )}
                </div>

                {/* Overall Progress */}
                <div className="space-y-1">
                  <Progress value={status.progress_percent} className="h-3 [&>div]:bg-blue-600" />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{status.progress_percent.toFixed(1)}% Complete</span>
                    <span>
                      {status.stats.processed_entities} / {status.stats.total_entities} entities
                    </span>
                  </div>
                </div>
              </div>

              {/* Live Statistics Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800">
                  <div className="text-xs text-green-700 dark:text-green-300 mb-1">
                    Duplicates Found
                  </div>
                  <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                    {status.stats.duplicates_found}
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
                  <div className="text-xs text-blue-700 dark:text-blue-300 mb-1">
                    Q-IDs Added
                  </div>
                  <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                    {status.stats.qids_added}
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-950 border border-purple-200 dark:border-purple-800">
                  <div className="text-xs text-purple-700 dark:text-purple-300 mb-1">
                    Entities Merged
                  </div>
                  <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                    {status.stats.entities_merged}
                  </p>
                </div>
              </div>

              {/* Errors */}
              {status.stats.errors > 0 && (
                <Alert className="bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-sm text-yellow-900 dark:text-yellow-100">
                    {status.stats.errors} errors encountered during processing
                  </AlertDescription>
                </Alert>
              )}

              {/* Stop Button */}
              <Button
                onClick={handleStop}
                disabled={stopMutation.isPending}
                variant="destructive"
                className="w-full"
              >
                <StopCircle className="h-4 w-4 mr-2" />
                Stop Reprocessing
              </Button>

              {/* Started At */}
              {status.started_at && (
                <p className="text-xs text-center text-muted-foreground">
                  Started: {new Date(status.started_at).toLocaleString()}
                </p>
              )}
            </>
          )}

          {/* Completed State - Results */}
          {isCompleted && status && (
            <>
              <Alert className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <AlertDescription>
                  <p className="font-medium text-green-900 dark:text-green-100">
                    {status.dry_run ? 'Dry Run Completed' : 'Reprocessing Completed Successfully'}
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                    {status.completed_at &&
                      `Completed at ${new Date(status.completed_at).toLocaleString()}`}
                  </p>
                </AlertDescription>
              </Alert>

              {/* Results Summary */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">Processing Results</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-muted/30">
                    <div className="text-xs text-muted-foreground mb-1">Total Processed</div>
                    <p className="text-xl font-bold">{status.stats.processed_entities}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-muted/30">
                    <div className="text-xs text-muted-foreground mb-1">Duplicates Found</div>
                    <p className="text-xl font-bold text-green-600">
                      {status.stats.duplicates_found}
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-muted/30">
                    <div className="text-xs text-muted-foreground mb-1">Entities Merged</div>
                    <p className="text-xl font-bold text-purple-600">
                      {status.stats.entities_merged}
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-muted/30">
                    <div className="text-xs text-muted-foreground mb-1">Q-IDs Added</div>
                    <p className="text-xl font-bold text-blue-600">{status.stats.qids_added}</p>
                  </div>
                </div>

                {status.stats.errors > 0 && (
                  <Alert className="bg-yellow-50 dark:bg-yellow-950 border-yellow-200">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <AlertDescription className="text-sm text-yellow-900">
                      {status.stats.errors} errors occurred during processing
                    </AlertDescription>
                  </Alert>
                )}
              </div>

              {/* Reset Button */}
              <Button
                onClick={handleStart}
                className="w-full"
                variant="outline"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Run Again
              </Button>
            </>
          )}

          {/* Failed State */}
          {isFailed && status && (
            <>
              <Alert className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
                <XCircle className="h-4 w-4 text-red-600" />
                <AlertDescription>
                  <p className="font-medium text-red-900 dark:text-red-100 mb-2">
                    Reprocessing Failed
                  </p>
                  {status.error_message && (
                    <p className="text-xs text-red-700 dark:text-red-300">
                      {status.error_message}
                    </p>
                  )}
                </AlertDescription>
              </Alert>

              <Button
                onClick={handleStart}
                className="w-full"
                variant="outline"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {dryRun ? 'Start Dry Run?' : 'Start Batch Reprocessing?'}
            </AlertDialogTitle>
          </AlertDialogHeader>

          <div className="space-y-3 text-sm text-muted-foreground">
            <p>
              {dryRun
                ? 'This will analyze all entities and show what would be changed without saving.'
                : 'This will reprocess all entities through the canonicalization pipeline.'}
            </p>

            <div className="bg-muted p-3 rounded text-sm space-y-2">
              <p className="font-medium">Expected Actions:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Find and merge duplicate entities</li>
                <li>Add missing Wikidata Q-IDs (~70 entities)</li>
                <li>Apply fuzzy matching to similar names</li>
                <li>Update entity relationships</li>
              </ul>
            </div>

            {!dryRun && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  A database backup is recommended before running. This operation may take
                  several minutes depending on the number of entities.
                </AlertDescription>
              </Alert>
            )}
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmStart} disabled={startMutation.isPending}>
              {startMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  {dryRun ? 'Start Dry Run' : 'Start Reprocessing'}
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

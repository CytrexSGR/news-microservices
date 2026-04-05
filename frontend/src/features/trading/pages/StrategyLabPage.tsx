/**
 * StrategyLabPage - Strategy Lab (Agent) dashboard.
 *
 * Displays champion info, status metrics, and tabbed views for:
 * Portfolio routing matrix, Experiments, Index Register, Sessions, and Log.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  useChampion,
  usePortfolios,
  useExperiments,
  useIndices,
} from '../hooks/useStrategyLab'
import RoutingMatrixGrid from '../components/strategy-lab/RoutingMatrixGrid'
import ExperimentsTable from '../components/strategy-lab/ExperimentsTable'
import IndexRegisterTable from '../components/strategy-lab/IndexRegisterTable'

function StrategyLabPage() {
  const { data: champion, isLoading: championLoading } = useChampion()
  const { data: portfolios, isLoading: portfoliosLoading } = usePortfolios()
  const { data: experiments, isLoading: experimentsLoading } = useExperiments()
  const { data: indices, isLoading: indicesLoading } = useIndices()

  const championPortfolio = champion?.portfolio ?? portfolios?.find((p) => p.is_champion)

  const runningExperiments = experiments?.filter((e) => e.status === 'running').length ?? 0
  const totalExperiments = experiments?.length ?? 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight">Strategy Lab</h1>
          {champion && (
            <Badge variant="default" className="text-xs">
              Champion: v{champion.version}
            </Badge>
          )}
        </div>
      </div>

      {/* Status Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {/* Champion Version */}
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Champion</p>
              {championLoading ? (
                <Skeleton className="h-5 w-16" />
              ) : (
                <p className="text-sm font-semibold">
                  {champion?.version ?? '--'}
                </p>
              )}
            </div>

            {/* Champion Score */}
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Score</p>
              {championLoading ? (
                <Skeleton className="h-5 w-16" />
              ) : (
                <p className="text-sm font-semibold">
                  {champion?.score != null ? champion.score.toFixed(2) : '--'}
                </p>
              )}
            </div>

            {/* Portfolios Count */}
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Portfolios</p>
              {portfoliosLoading ? (
                <Skeleton className="h-5 w-10" />
              ) : (
                <p className="text-sm font-semibold">
                  {portfolios?.length ?? 0}
                </p>
              )}
            </div>

            {/* Experiments */}
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Experiments</p>
              {experimentsLoading ? (
                <Skeleton className="h-5 w-16" />
              ) : (
                <p className="text-sm font-semibold">
                  {runningExperiments} running / {totalExperiments} total
                </p>
              )}
            </div>

            {/* Custom Indices */}
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Custom Indices</p>
              {indicesLoading ? (
                <Skeleton className="h-5 w-10" />
              ) : (
                <p className="text-sm font-semibold">
                  {indices?.length ?? 0}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="portfolio" className="space-y-4">
        <TabsList>
          <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
          <TabsTrigger value="experiments">Experiments</TabsTrigger>
          <TabsTrigger value="indices">Index Register</TabsTrigger>
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
          <TabsTrigger value="log">Log</TabsTrigger>
        </TabsList>

        {/* Portfolio Tab */}
        <TabsContent value="portfolio">
          <RoutingMatrixGrid
            portfolio={championPortfolio}
            isLoading={championLoading && portfoliosLoading}
          />
        </TabsContent>

        {/* Experiments Tab */}
        <TabsContent value="experiments">
          <ExperimentsTable
            experiments={experiments}
            isLoading={experimentsLoading}
          />
        </TabsContent>

        {/* Index Register Tab */}
        <TabsContent value="indices">
          <IndexRegisterTable
            indices={indices}
            isLoading={indicesLoading}
          />
        </TabsContent>

        {/* Sessions Tab - TODO */}
        <TabsContent value="sessions">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                TODO: Trading session history and replay viewer. Planned for Phase 6.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Log Tab - TODO */}
        <TabsContent value="log">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Activity Log</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                TODO: Strategy Lab event log with filtering. Planned for Phase 6.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default StrategyLabPage

/**
 * Strategy Lab Landing Page
 *
 * Main entry point for Strategy Lab - List and manage trading strategies
 */

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { strategyLabClient } from '@/lib/api/strategyLab'
import { predictionClient } from '@/lib/api-client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/Input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  BarChart3,
  Plus,
  Search,
  TrendingUp,
  TrendingDown,
  Activity,
  RefreshCw,
  PlayCircle,
  FileText,
  Edit,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { BacktestDialog } from '../components/BacktestDialog'
import type { Strategy } from '@/types/strategy'
import type { StrategyLabBacktestRequest, StrategyLabBacktestResponse } from '@/types/backtest'

export default function StrategyLabLandingPage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [backtestDialogOpen, setBacktestDialogOpen] = useState(false)
  const [backtestStrategy, setBacktestStrategy] = useState<Strategy | null>(null)
  const [isRunningBacktest, setIsRunningBacktest] = useState(false)

  // Fetch strategies
  const {
    data: strategiesData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['strategies', { name: searchQuery }],
    queryFn: () =>
      strategyLabClient.strategy.list({
        name: searchQuery || undefined,
        limit: 50,
      }),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const strategies = strategiesData?.strategies || []
  const totalStrategies = strategiesData?.total || 0

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const getRegimeCount = () => {
    const regimeCounts = { TREND: 0, CONSOLIDATION: 0, HIGH_VOLATILITY: 0 }
    strategies.forEach((strategy) => {
      const logic = strategy.definition?.logic || {}
      Object.keys(logic).forEach((regime) => {
        if (regime in regimeCounts) {
          regimeCounts[regime as keyof typeof regimeCounts]++
        }
      })
    })
    return regimeCounts
  }

  const regimeCounts = getRegimeCount()

  // Run backtest mutation
  const runBacktestMutation = useMutation({
    mutationFn: async (request: StrategyLabBacktestRequest): Promise<StrategyLabBacktestResponse> => {
      const response = await predictionClient.post<StrategyLabBacktestResponse>(
        '/strategy-lab/backtest',
        request
      )
      return response.data
    },
    onSuccess: (response) => {
      setIsRunningBacktest(false)
      toast.success('Backtest completed!')
      // Navigate to results page with the response data
      navigate('/trading/backtest/results', {
        state: {
          backtestResponse: response,
          strategy: backtestStrategy,
        },
      })
    },
    onError: (error) => {
      setIsRunningBacktest(false)
      toast.error(`Backtest failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    },
  })

  // Handler for starting a backtest from the dialog
  const handleStartBacktest = (request: StrategyLabBacktestRequest) => {
    setIsRunningBacktest(true)
    toast.loading('Starting backtest...', { id: 'backtest-start' })
    runBacktestMutation.mutate(request)
    toast.dismiss('backtest-start')
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Strategy Lab</h1>
          </div>
          <p className="text-muted-foreground">
            Design, backtest, and optimize regime-based trading strategies with multi-timeframe
            analysis
          </p>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create New Strategy
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Strategies</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStrategies}</div>
            <p className="text-xs text-muted-foreground">Active strategies</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trend Strategies</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{regimeCounts.TREND}</div>
            <p className="text-xs text-muted-foreground">Using TREND regime</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Range Strategies</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{regimeCounts.CONSOLIDATION}</div>
            <p className="text-xs text-muted-foreground">Using CONSOLIDATION regime</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Volatile Strategies</CardTitle>
            <TrendingDown className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{regimeCounts.HIGH_VOLATILITY}</div>
            <p className="text-xs text-muted-foreground">Using HIGH_VOLATILITY regime</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Strategies</CardTitle>
              <CardDescription>
                Browse and manage your regime-based trading strategies
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search Bar */}
          <div className="flex gap-2 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search strategies by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>

          {/* Strategies Table */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : strategies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No strategies found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery
                  ? 'Try adjusting your search query'
                  : 'Create your first regime-based trading strategy to get started'}
              </p>
              {!searchQuery && (
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Strategy
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Regimes</TableHead>
                  <TableHead>Indicators</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {strategies.map((strategy) => {
                  const regimeTypes = Object.keys(strategy.definition?.logic || {})
                  const indicatorCount = strategy.definition?.indicators?.length || 0

                  return (
                    <TableRow key={strategy.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <BarChart3 className="h-4 w-4 text-muted-foreground" />
                          {strategy.name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">v{strategy.version}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {regimeTypes.map((regime) => (
                            <Badge
                              key={regime}
                              variant="secondary"
                              className="text-xs"
                            >
                              {regime}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>{indicatorCount} indicators</TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDate(strategy.created_at)}
                      </TableCell>
                      <TableCell>
                        {strategy.is_public ? (
                          <Badge variant="default">Public</Badge>
                        ) : (
                          <Badge variant="secondary">Private</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Link to={`/trading/strategy/${strategy.id}`}>
                            <Button
                              variant="ghost"
                              size="sm"
                              title="View details"
                            >
                              <FileText className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Link to={`/trading/backtest/strategy/${strategy.id}/edit`}>
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Edit strategy"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Run backtest"
                            onClick={() => {
                              setBacktestStrategy(strategy)
                              setBacktestDialogOpen(true)
                            }}
                          >
                            <PlayCircle className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Backtest Dialog */}
      {backtestStrategy && (
        <BacktestDialog
          strategy={backtestStrategy}
          isOpen={backtestDialogOpen}
          onClose={() => {
            setBacktestDialogOpen(false)
            setBacktestStrategy(null)
          }}
          onStartBacktest={handleStartBacktest}
        />
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Pause, Play, RefreshCw, Bot, Save, ShieldAlert, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { AgentStatusBar } from '../components/agent/AgentStatusBar'
import { PositionsTable } from '../components/agent/PositionsTable'
import { TradeHistory } from '../components/agent/TradeHistory'
import { DecisionLog } from '../components/agent/DecisionLog'
import {
  useAgentState,
  useAgentPositions,
  useAgentRiskStatus,
  useAgentDecisionLog,
  useAgentConfig,
  useAgentTrades,
  useAgentPause,
  useAgentResume,
  useUpdateConfig,
  useUpdateCapital,
  useEmergencyStop,
  useEmergencyReset,
} from '../hooks/useAgentControl'
import type { ConfigUpdate } from '../hooks/useAgentControl'
import toast from 'react-hot-toast'

export default function AgentMonitorPage() {
  const [activeTab, setActiveTab] = useState('positions')

  const state = useAgentState()
  const positions = useAgentPositions()
  const risk = useAgentRiskStatus()
  const decisions = useAgentDecisionLog('24h')
  const config = useAgentConfig()
  const trades = useAgentTrades()

  const pauseMutation = useAgentPause()
  const resumeMutation = useAgentResume()
  const updateConfigMutation = useUpdateConfig()
  const updateCapitalMutation = useUpdateCapital()
  const emergencyStopMutation = useEmergencyStop()
  const emergencyResetMutation = useEmergencyReset()

  const isPaused = state.data?.paused ?? false
  const isConnected = !state.isError

  const handlePause = () => {
    pauseMutation.mutate(undefined, {
      onSuccess: () => toast.success('Engine paused'),
      onError: () => toast.error('Failed to pause engine'),
    })
  }

  const handleResume = () => {
    resumeMutation.mutate(undefined, {
      onSuccess: () => toast.success('Engine resumed'),
      onError: () => toast.error('Failed to resume engine'),
    })
  }

  const handleEmergencyStop = () => {
    if (!window.confirm('EMERGENCY STOP: Close ALL positions and lock trading?')) return
    emergencyStopMutation.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(`Emergency stop: ${data.positions_closed} positions closed`)
      },
      onError: () => toast.error('Emergency stop failed'),
    })
  }

  const handleEmergencyReset = () => {
    if (!window.confirm('Unlock trading? Engine will remain paused.')) return
    emergencyResetMutation.mutate(undefined, {
      onSuccess: () => toast.success('Emergency lock removed. Use Resume to start trading.'),
      onError: () => toast.error('Emergency reset failed'),
    })
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className="h-6 w-6" />
          <h1 className="text-2xl font-bold">Agent Monitor</h1>
          {isConnected ? (
            <Badge variant="default" className="gap-1">
              <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
              Connected
            </Badge>
          ) : (
            <Badge variant="destructive">Disconnected</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isPaused ? (
            <Button
              size="sm"
              onClick={handleResume}
              disabled={resumeMutation.isPending}
            >
              <Play className="h-4 w-4 mr-1" />
              Resume
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={handlePause}
              disabled={pauseMutation.isPending}
            >
              <Pause className="h-4 w-4 mr-1" />
              Pause
            </Button>
          )}
          {state.data?.engine_status === 'paused' ? (
            <Button
              size="sm"
              variant="outline"
              onClick={handleEmergencyReset}
              disabled={emergencyResetMutation.isPending}
              className="border-amber-500 text-amber-600 hover:bg-amber-50"
            >
              <ShieldCheck className="h-4 w-4 mr-1" />
              Unlock
            </Button>
          ) : (
            <Button
              size="sm"
              variant="destructive"
              onClick={handleEmergencyStop}
              disabled={emergencyStopMutation.isPending}
            >
              <ShieldAlert className="h-4 w-4 mr-1" />
              Emergency Stop
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              state.refetch()
              positions.refetch()
              risk.refetch()
            }}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Status Bar */}
      <AgentStatusBar
        state={state.data}
        risk={risk.data}
        isLoading={state.isLoading}
      />

      {/* Connection Error */}
      {state.isError && (
        <Card className="border-destructive">
          <CardContent className="py-4">
            <p className="text-sm text-destructive">
              Cannot reach Agent Control API. Is the prediction-service running on port 8116?
            </p>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="positions">
            Positions {positions.data?.length ? `(${positions.data.length})` : ''}
          </TabsTrigger>
          <TabsTrigger value="history">Trade History</TabsTrigger>
          <TabsTrigger value="decisions">Decisions</TabsTrigger>
          <TabsTrigger value="config">Config & Risk</TabsTrigger>
        </TabsList>

        <TabsContent value="positions">
          <PositionsTable positions={positions.data} isLoading={positions.isLoading} />
        </TabsContent>

        <TabsContent value="history">
          <TradeHistory data={trades.data} isLoading={trades.isLoading} />
        </TabsContent>

        <TabsContent value="decisions">
          <DecisionLog decisions={decisions.data} isLoading={decisions.isLoading} />
        </TabsContent>

        <TabsContent value="config">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Engine Config — Editable */}
            <Card>
              <CardHeader>
                <CardTitle>Engine Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                {config.isLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="h-6 bg-muted animate-pulse rounded" />
                    ))}
                  </div>
                ) : config.data ? (
                  <ConfigEditor
                    config={config.data}
                    onSave={(update) => {
                      updateConfigMutation.mutate(update, {
                        onSuccess: () => toast.success('Config updated'),
                        onError: () => toast.error('Failed to update config'),
                      })
                    }}
                    isSaving={updateConfigMutation.isPending}
                  />
                ) : (
                  <p className="text-sm text-muted-foreground">No config available</p>
                )}
              </CardContent>
            </Card>

            {/* Risk Status */}
            <Card>
              <CardHeader><CardTitle>Risk Status</CardTitle></CardHeader>
              <CardContent>
                {risk.isLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="h-6 bg-muted animate-pulse rounded" />
                    ))}
                  </div>
                ) : risk.data ? (
                  <div className="space-y-4">
                    <CapitalEditor
                      capital={risk.data.portfolio.capital}
                      onSave={(val) => {
                        updateCapitalMutation.mutate(val, {
                          onSuccess: () => toast.success('Capital updated'),
                          onError: () => toast.error('Failed to update capital'),
                        })
                      }}
                      isSaving={updateCapitalMutation.isPending}
                    />
                    <dl className="space-y-2 text-sm">
                      <ConfigRow label="Peak Capital" value={`$${risk.data.portfolio.peak_capital.toFixed(2)}`} />
                      <ConfigRow label="Drawdown" value={`-${risk.data.portfolio.drawdown_pct.toFixed(2)}%`} />
                      <ConfigRow label="Size Multiplier" value={`${risk.data.position_size_multiplier}x`} />
                      <ConfigRow label="Trading Blocked" value={risk.data.trading_blocked ? 'YES' : 'No'} />
                    </dl>

                    {risk.data.circuit_breakers.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2">Active Circuit Breakers</h4>
                        <div className="space-y-1">
                          {risk.data.circuit_breakers.map((cb, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs p-2 rounded bg-destructive/10">
                              <Badge variant="destructive" className="text-xs">{cb.type}</Badge>
                              <span className="text-muted-foreground">{cb.reason}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No risk data available</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ConfigRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  )
}

interface ConfigEditorProps {
  config: import('../hooks/useAgentControl').AgentConfig
  onSave: (update: ConfigUpdate) => void
  isSaving: boolean
}

function ConfigEditor({ config, onSave, isSaving }: ConfigEditorProps) {
  const [form, setForm] = useState({
    max_positions: config.max_positions,
    risk_per_trade_pct: config.risk_per_trade_pct,
    max_size_usd: config.max_size_usd ?? 50,
    max_leverage: config.max_leverage ?? 1,
    direction_bias: config.direction_bias,
    tick_interval_seconds: config.tick_interval_seconds,
  })

  // Sync form when config changes from polling
  useEffect(() => {
    setForm({
      max_positions: config.max_positions,
      risk_per_trade_pct: config.risk_per_trade_pct,
      max_size_usd: config.max_size_usd ?? 50,
      max_leverage: config.max_leverage ?? 1,
      direction_bias: config.direction_bias,
      tick_interval_seconds: config.tick_interval_seconds,
    })
  }, [config.max_positions, config.risk_per_trade_pct, config.max_size_usd,
      config.max_leverage, config.direction_bias, config.tick_interval_seconds])

  const hasChanges =
    form.max_positions !== config.max_positions ||
    form.risk_per_trade_pct !== config.risk_per_trade_pct ||
    form.max_size_usd !== (config.max_size_usd ?? 50) ||
    form.max_leverage !== (config.max_leverage ?? 1) ||
    form.direction_bias !== config.direction_bias ||
    form.tick_interval_seconds !== config.tick_interval_seconds

  const handleSave = () => {
    const update: ConfigUpdate = {}
    if (form.max_positions !== config.max_positions) update.max_positions = form.max_positions
    if (form.risk_per_trade_pct !== config.risk_per_trade_pct) update.risk_per_trade_pct = form.risk_per_trade_pct
    if (form.max_size_usd !== (config.max_size_usd ?? 50)) update.max_size_usd = form.max_size_usd
    if (form.max_leverage !== (config.max_leverage ?? 1)) update.max_leverage = form.max_leverage
    if (form.direction_bias !== config.direction_bias) update.direction_bias = form.direction_bias
    if (form.tick_interval_seconds !== config.tick_interval_seconds) update.tick_interval_seconds = form.tick_interval_seconds
    onSave(update)
  }

  const limits = config.hard_limits

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <ConfigField
          label="Max Positions"
          hint={limits ? `Hard limit: ${limits.max_positions}` : undefined}
        >
          <input
            type="number" min={1} max={limits?.max_positions ?? 10} step={1}
            value={form.max_positions}
            onChange={(e) => setForm(f => ({ ...f, max_positions: Number(e.target.value) }))}
            className="w-20 px-2 py-1 text-sm border rounded bg-background text-right"
          />
        </ConfigField>

        <ConfigField
          label="Risk per Trade"
          hint={limits ? `Hard limit: ${limits.max_risk_per_trade}%` : undefined}
        >
          <div className="flex items-center gap-1">
            <input
              type="number" min={0.1} max={limits?.max_risk_per_trade ?? 2} step={0.1}
              value={form.risk_per_trade_pct}
              onChange={(e) => setForm(f => ({ ...f, risk_per_trade_pct: Number(e.target.value) }))}
              className="w-20 px-2 py-1 text-sm border rounded bg-background text-right"
            />
            <span className="text-sm text-muted-foreground">%</span>
          </div>
        </ConfigField>

        <ConfigField
          label="Max Size per Trade"
          hint={limits ? `Hard limit: $${limits.max_size_usd}` : undefined}
        >
          <div className="flex items-center gap-1">
            <span className="text-sm text-muted-foreground">$</span>
            <input
              type="number" min={5} max={limits?.max_size_usd ?? 250} step={5}
              value={form.max_size_usd}
              onChange={(e) => setForm(f => ({ ...f, max_size_usd: Number(e.target.value) }))}
              className="w-20 px-2 py-1 text-sm border rounded bg-background text-right"
            />
          </div>
        </ConfigField>

        <ConfigField
          label="Max Leverage"
          hint={limits ? `Hard limit: ${limits.max_leverage}x` : undefined}
        >
          <div className="flex items-center gap-1">
            <input
              type="number" min={1} max={limits?.max_leverage ?? 20} step={1}
              value={form.max_leverage}
              onChange={(e) => setForm(f => ({ ...f, max_leverage: Number(e.target.value) }))}
              className="w-20 px-2 py-1 text-sm border rounded bg-background text-right"
            />
            <span className="text-sm text-muted-foreground">x</span>
          </div>
        </ConfigField>

        <ConfigField label="Direction Bias">
          <select
            value={form.direction_bias}
            onChange={(e) => setForm(f => ({ ...f, direction_bias: e.target.value }))}
            className="px-2 py-1 text-sm border rounded bg-background"
          >
            <option value="both">Both</option>
            <option value="long_only">Long Only</option>
            <option value="short_only">Short Only</option>
          </select>
        </ConfigField>

        <ConfigField label="Tick Interval">
          <div className="flex items-center gap-1">
            <input
              type="number" min={10} max={600} step={10}
              value={form.tick_interval_seconds}
              onChange={(e) => setForm(f => ({ ...f, tick_interval_seconds: Number(e.target.value) }))}
              className="w-20 px-2 py-1 text-sm border rounded bg-background text-right"
            />
            <span className="text-sm text-muted-foreground">s</span>
          </div>
        </ConfigField>
      </div>

      {/* Read-only info */}
      <div className="pt-2 border-t space-y-1 text-sm">
        <ConfigRow label="Status" value={config.paused ? 'Paused' : 'Active'} />
        <ConfigRow
          label="Watchlist"
          value={(config.watchlist ?? []).join(', ') || 'None'}
        />
      </div>

      <Button
        size="sm"
        onClick={handleSave}
        disabled={!hasChanges || isSaving}
        className="w-full"
      >
        <Save className="h-4 w-4 mr-1" />
        {isSaving ? 'Saving...' : 'Save Changes'}
      </Button>
    </div>
  )
}

function ConfigField({ label, hint, children }: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <span className="text-sm">{label}</span>
        {hint && <span className="text-xs text-muted-foreground ml-2">({hint})</span>}
      </div>
      {children}
    </div>
  )
}

function CapitalEditor({ capital, onSave, isSaving }: {
  capital: number
  onSave: (val: number) => void
  isSaving: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(capital)

  useEffect(() => {
    if (!editing) setValue(capital)
  }, [capital, editing])

  if (!editing) {
    return (
      <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/30">
        <div>
          <p className="text-xs text-muted-foreground">Capital</p>
          <p className="text-lg font-bold">${capital.toFixed(2)}</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
          Edit
        </Button>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-primary/50 bg-muted/30">
      <div>
        <p className="text-xs text-muted-foreground">Capital (no limits)</p>
        <div className="flex items-center gap-1">
          <span className="text-lg font-bold">$</span>
          <input
            type="number" min={1} step={100}
            value={value}
            onChange={(e) => setValue(Number(e.target.value))}
            className="w-32 px-2 py-1 text-lg font-bold border rounded bg-background"
            autoFocus
          />
        </div>
      </div>
      <div className="flex gap-1">
        <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={() => { onSave(value); setEditing(false) }}
          disabled={isSaving || value === capital}
        >
          {isSaving ? '...' : 'Set'}
        </Button>
      </div>
    </div>
  )
}

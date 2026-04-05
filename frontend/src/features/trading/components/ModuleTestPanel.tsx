/**
 * Module Test Panel
 *
 * Collapsible panel for selecting and configuring module isolation tests.
 * Tests individual strategy components (entry, exit, risk, regime) in isolation.
 *
 * Part of Backtest Comprehensive Upgrade - Phase 3
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/Button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  ChevronDown,
  ChevronRight,
  Beaker,
  Crosshair,
  LogOut,
  Shield,
  TrendingUp,
  Info,
  Layers,
} from 'lucide-react'
import type { ModuleTestMode } from '@/types/backtest'

// Module test mode definitions
const MODULE_TEST_MODES: {
  mode: ModuleTestMode
  label: string
  description: string
  icon: React.ElementType
  color: string
  hasParams: boolean
}[] = [
  {
    mode: 'full',
    label: 'Full Strategy',
    description: 'Complete strategy with all modules working together',
    icon: Layers,
    color: 'bg-blue-500',
    hasParams: false,
  },
  {
    mode: 'entry',
    label: 'Entry Logic',
    description: 'Test entry signals with random exits after N bars',
    icon: Crosshair,
    color: 'bg-green-500',
    hasParams: true,
  },
  {
    mode: 'exit',
    label: 'Exit Logic',
    description: 'Random entries, test exit timing quality',
    icon: LogOut,
    color: 'bg-amber-500',
    hasParams: true,
  },
  {
    mode: 'risk',
    label: 'Risk Management',
    description: 'Fixed entries every N bars, test SL/TP effectiveness',
    icon: Shield,
    color: 'bg-red-500',
    hasParams: true,
  },
  {
    mode: 'regime',
    label: 'Regime Detection',
    description: 'Compare detected regimes vs actual market trends',
    icon: TrendingUp,
    color: 'bg-purple-500',
    hasParams: false,
  },
]

export interface ModuleTestConfig {
  mode: ModuleTestMode
  hold_bars?: number // For entry test
  num_random_entries?: number // For exit test
  entry_interval?: number // For risk test
}

interface ModuleTestPanelProps {
  /** Currently selected test mode configuration */
  config: ModuleTestConfig
  /** Callback when config changes */
  onConfigChange: (config: ModuleTestConfig) => void
  /** Whether the panel is expanded */
  isExpanded: boolean
  /** Callback when expansion state changes */
  onExpandedChange: (expanded: boolean) => void
}

export function ModuleTestPanel({
  config,
  onConfigChange,
  isExpanded,
  onExpandedChange,
}: ModuleTestPanelProps) {
  // Local state for parameters
  const [holdBars, setHoldBars] = useState(config.hold_bars ?? 10)
  const [numRandomEntries, setNumRandomEntries] = useState(config.num_random_entries ?? 50)
  const [entryInterval, setEntryInterval] = useState(config.entry_interval ?? 24)

  // Sync parameters with config when mode changes
  useEffect(() => {
    const newConfig: ModuleTestConfig = { mode: config.mode }

    if (config.mode === 'entry') {
      newConfig.hold_bars = holdBars
    } else if (config.mode === 'exit') {
      newConfig.num_random_entries = numRandomEntries
    } else if (config.mode === 'risk') {
      newConfig.entry_interval = entryInterval
    }

    // Only update if something changed
    if (
      newConfig.hold_bars !== config.hold_bars ||
      newConfig.num_random_entries !== config.num_random_entries ||
      newConfig.entry_interval !== config.entry_interval
    ) {
      onConfigChange(newConfig)
    }
  }, [config.mode, holdBars, numRandomEntries, entryInterval])

  const handleModeChange = (mode: ModuleTestMode) => {
    const newConfig: ModuleTestConfig = { mode }

    if (mode === 'entry') {
      newConfig.hold_bars = holdBars
    } else if (mode === 'exit') {
      newConfig.num_random_entries = numRandomEntries
    } else if (mode === 'risk') {
      newConfig.entry_interval = entryInterval
    }

    onConfigChange(newConfig)
  }

  const selectedModeInfo = MODULE_TEST_MODES.find(m => m.mode === config.mode)
  const isModuleTest = config.mode !== 'full'

  return (
    <Card className={isModuleTest ? 'border-primary/50' : ''}>
      <Collapsible open={isExpanded} onOpenChange={onExpandedChange}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors">
            <CardTitle className="text-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Beaker className="h-4 w-4" />
                Module Test Mode
                {isModuleTest && (
                  <Badge variant="outline" className="ml-2">
                    {selectedModeInfo?.label}
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                {isModuleTest && (
                  <Badge className={`${selectedModeInfo?.color} text-white`}>
                    Active
                  </Badge>
                )}
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </CardTitle>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="space-y-4">
            {/* Info Banner */}
            <div className="p-3 rounded-lg border bg-muted/30">
              <div className="flex items-start gap-2">
                <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                <p className="text-sm text-muted-foreground">
                  Module tests isolate individual strategy components to identify specific
                  weaknesses. Select a mode below to test entries, exits, risk management,
                  or regime detection separately.
                </p>
              </div>
            </div>

            {/* Mode Selection Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {MODULE_TEST_MODES.map((modeInfo) => {
                const Icon = modeInfo.icon
                const isSelected = config.mode === modeInfo.mode

                return (
                  <TooltipProvider key={modeInfo.mode}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant={isSelected ? 'default' : 'outline'}
                          className={`
                            h-auto p-3 flex flex-col items-start gap-1.5 text-left
                            ${isSelected ? 'ring-2 ring-primary ring-offset-2' : ''}
                          `}
                          onClick={() => handleModeChange(modeInfo.mode)}
                        >
                          <div className="flex items-center gap-2 w-full">
                            <div className={`p-1.5 rounded ${modeInfo.color}`}>
                              <Icon className="h-3.5 w-3.5 text-white" />
                            </div>
                            <span className="font-medium text-sm">{modeInfo.label}</span>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {modeInfo.description}
                          </p>
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="max-w-xs">
                        <p>{modeInfo.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )
              })}
            </div>

            {/* Mode-Specific Parameters */}
            {config.mode === 'entry' && (
              <div className="p-4 rounded-lg border bg-green-50/50 dark:bg-green-950/20 space-y-3">
                <div className="flex items-center gap-2">
                  <Crosshair className="h-4 w-4 text-green-600" />
                  <span className="font-medium text-sm">Entry Test Parameters</span>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="holdBars" className="text-sm">
                    Hold Bars (exit after N bars)
                  </Label>
                  <Input
                    id="holdBars"
                    type="number"
                    value={holdBars}
                    onChange={(e) => setHoldBars(Number(e.target.value))}
                    min={1}
                    max={100}
                    className="w-32"
                  />
                  <p className="text-xs text-muted-foreground">
                    Number of bars to hold each position before random exit.
                    Lower values test entry timing, higher values test entry quality.
                  </p>
                </div>
              </div>
            )}

            {config.mode === 'exit' && (
              <div className="p-4 rounded-lg border bg-amber-50/50 dark:bg-amber-950/20 space-y-3">
                <div className="flex items-center gap-2">
                  <LogOut className="h-4 w-4 text-amber-600" />
                  <span className="font-medium text-sm">Exit Test Parameters</span>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="numRandomEntries" className="text-sm">
                    Number of Random Entries
                  </Label>
                  <Input
                    id="numRandomEntries"
                    type="number"
                    value={numRandomEntries}
                    onChange={(e) => setNumRandomEntries(Number(e.target.value))}
                    min={10}
                    max={200}
                    className="w-32"
                  />
                  <p className="text-xs text-muted-foreground">
                    Number of random entry points to test exit timing.
                    More entries = more statistically significant results.
                  </p>
                </div>
              </div>
            )}

            {config.mode === 'risk' && (
              <div className="p-4 rounded-lg border bg-red-50/50 dark:bg-red-950/20 space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-red-600" />
                  <span className="font-medium text-sm">Risk Test Parameters</span>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="entryInterval" className="text-sm">
                    Entry Interval (bars between entries)
                  </Label>
                  <Input
                    id="entryInterval"
                    type="number"
                    value={entryInterval}
                    onChange={(e) => setEntryInterval(Number(e.target.value))}
                    min={6}
                    max={100}
                    className="w-32"
                  />
                  <p className="text-xs text-muted-foreground">
                    Fixed interval for systematic entries.
                    Tests stop-loss and take-profit effectiveness across market conditions.
                  </p>
                </div>
              </div>
            )}

            {config.mode === 'regime' && (
              <div className="p-4 rounded-lg border bg-purple-50/50 dark:bg-purple-950/20 space-y-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-purple-600" />
                  <span className="font-medium text-sm">Regime Detection Test</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  No additional parameters needed. This test compares your strategy's
                  detected regimes against actual market trends using price action analysis.
                </p>
              </div>
            )}

            {/* Reset Button */}
            {isModuleTest && (
              <div className="flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleModeChange('full')}
                >
                  Reset to Full Strategy
                </Button>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}

/**
 * ML Lab Page
 *
 * Gatekeeper Model Laboratory for ML-powered trading signal validation.
 * Manages 6 gate areas: Regime, Direction, Entry, Exit, Risk, Volatility
 *
 * Features:
 * - Dashboard: Overview of models, training, and performance
 * - Models: Create and manage ML models
 * - Training: Configure and monitor training jobs
 * - Live: Real-time inference and predictions
 * - Shadow Trades: Paper trading based on predictions
 * - Config: Gate thresholds and settings
 */

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Brain,
  BarChart3,
  Activity,
  Settings2,
  Zap,
  BarChart2,
  Play,
  Gauge,
  History,
  PieChart,
} from 'lucide-react';

import { DashboardTab } from './components/dashboard';
import { ModelsTab } from './components/models';
import { TrainingTab } from './components/training';
import { ConfigTab } from './components/config';
import { LiveInferenceTab, ShadowTradesPanel, LivePaperTradingPanel, LiveIndicatorsPanel } from './components/live';
import { BacktestPanel } from './components/backtest';
import { StrategiesTab } from './components/strategies';

export function MLLabPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Brain className="h-8 w-8 text-primary" />
            ML Lab
          </h1>
          <p className="text-muted-foreground mt-1">
            Gatekeeper Model Laboratory - Train and manage ML models for trading signal validation
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-10">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="strategies" className="flex items-center gap-2">
            <PieChart className="h-4 w-4" />
            <span className="hidden sm:inline">Strategies</span>
          </TabsTrigger>
          <TabsTrigger value="indicators" className="flex items-center gap-2">
            <Gauge className="h-4 w-4" />
            <span className="hidden sm:inline">Indicators</span>
          </TabsTrigger>
          <TabsTrigger value="models" className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            <span className="hidden sm:inline">Models</span>
          </TabsTrigger>
          <TabsTrigger value="training" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            <span className="hidden sm:inline">Training</span>
          </TabsTrigger>
          <TabsTrigger value="live" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            <span className="hidden sm:inline">Live</span>
          </TabsTrigger>
          <TabsTrigger value="paper" className="flex items-center gap-2">
            <Play className="h-4 w-4" />
            <span className="hidden sm:inline">Paper</span>
          </TabsTrigger>
          <TabsTrigger value="backtest" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">Backtest</span>
          </TabsTrigger>
          <TabsTrigger value="shadow" className="flex items-center gap-2">
            <BarChart2 className="h-4 w-4" />
            <span className="hidden sm:inline">Shadow</span>
          </TabsTrigger>
          <TabsTrigger value="config" className="flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            <span className="hidden sm:inline">Config</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <DashboardTab />
        </TabsContent>

        <TabsContent value="strategies">
          <StrategiesTab />
        </TabsContent>

        <TabsContent value="indicators">
          <LiveIndicatorsPanel />
        </TabsContent>

        <TabsContent value="models">
          <ModelsTab />
        </TabsContent>

        <TabsContent value="training">
          <TrainingTab />
        </TabsContent>

        <TabsContent value="live">
          <LiveInferenceTab />
        </TabsContent>

        <TabsContent value="paper">
          <LivePaperTradingPanel />
        </TabsContent>

        <TabsContent value="backtest">
          <BacktestPanel />
        </TabsContent>

        <TabsContent value="shadow">
          <ShadowTradesPanel />
        </TabsContent>

        <TabsContent value="config">
          <ConfigTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default MLLabPage;

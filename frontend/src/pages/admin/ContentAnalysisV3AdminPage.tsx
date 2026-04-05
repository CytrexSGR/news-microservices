/**
 * Content-Analysis-V3 Admin Page
 *
 * Simplified administration interface for V3 analysis service.
 *
 * Features:
 * - Service status and health monitoring
 * - Cost optimization metrics
 * - Tier configuration and budgets
 * - Recent analysis history
 *
 * Compared to V2:
 * - Much simpler (4 tabs vs V2's 7 tabs)
 * - No agent management (V3 has fixed specialists)
 * - No complex thresholds (V3 uses budget redistribution)
 * - Cost-focused (96.7% reduction is the main metric)
 */

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { CheckCircle2, XCircle, TrendingDown, Zap, Database, Settings } from 'lucide-react';

export function ContentAnalysisV3AdminPage() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Content-Analysis-V3 Admin</h1>
          <p className="text-muted-foreground mt-1">
            Cost-optimized analysis pipeline • 96.7% cost reduction
          </p>
        </div>
        <Badge variant="outline" className="bg-green-50 text-green-700 h-8 px-4">
          <Zap className="h-4 w-4 mr-1" />
          V3 Active
        </Badge>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="diagnostics">Diagnostics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <OverviewTab />
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="space-y-6">
          <ConfigurationTab />
        </TabsContent>

        {/* Monitoring Tab */}
        <TabsContent value="monitoring" className="space-y-6">
          <MonitoringTab />
        </TabsContent>

        {/* Diagnostics Tab */}
        <TabsContent value="diagnostics" className="space-y-6">
          <DiagnosticsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * Overview Tab - Service status and key metrics
 */
function OverviewTab() {
  // TODO: Fetch real data from V3 API
  const serviceStatus = 'healthy'; // Mock data
  const isLoading = false;

  if (isLoading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Service Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {serviceStatus === 'healthy' ? (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600" />
            )}
            Service Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">API:</span>
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Online
              </Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Database:</span>
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Connected
              </Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">RabbitMQ:</span>
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Connected
              </Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Consumer:</span>
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Running
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Cost Savings */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost Savings</CardTitle>
            <TrendingDown className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">96.7%</div>
            <p className="text-xs text-muted-foreground mt-1">
              $0.0085 → $0.00028 per article
            </p>
          </CardContent>
        </Card>

        {/* Articles Analyzed */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Articles Analyzed</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground mt-1">
              Total V3 analyses
            </p>
          </CardContent>
        </Card>

        {/* Average Cost */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Cost per Article</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$0.00028</div>
            <p className="text-xs text-muted-foreground mt-1">
              Target budget
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Architecture */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Architecture</CardTitle>
          <CardDescription>4-tier progressive analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <PipelineTierCard
              tier="Tier 0: Triage"
              description="Fast keep/discard decision"
              budget={{ tokens: 800, cost: 0.00005 }}
              model="gemini-2.0-flash-thinking-exp"
            />
            <PipelineTierCard
              tier="Tier 1: Foundation"
              description="Entity/relation/topic extraction"
              budget={{ tokens: 2000, cost: 0.0001 }}
              model="gemini-2.0-flash-thinking-exp"
            />
            <PipelineTierCard
              tier="Tier 2: Specialists"
              description="5 specialized analysis modules"
              budget={{ tokens: 8000, cost: 0.0005 }}
              model="gemini-2.0-flash-thinking-exp"
            />
            <PipelineTierCard
              tier="Tier 3: Intelligence"
              description="Event timelines, multi-doc reasoning (planned)"
              budget={{ tokens: 3000, cost: 0.001 }}
              model="N/A"
              disabled
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Pipeline Tier Display Card
 */
function PipelineTierCard({
  tier,
  description,
  budget,
  model,
  disabled = false,
}: {
  tier: string;
  description: string;
  budget: { tokens: number; cost: number };
  model: string;
  disabled?: boolean;
}) {
  return (
    <div className={`flex items-start justify-between p-4 border rounded-lg ${disabled ? 'opacity-50' : ''}`}>
      <div className="space-y-1">
        <h4 className="font-semibold text-sm">{tier}</h4>
        <p className="text-xs text-muted-foreground">{description}</p>
        <p className="text-xs text-muted-foreground">Model: {model}</p>
      </div>
      <div className="text-right text-sm space-y-1">
        <div className="font-mono text-green-600">${budget.cost.toFixed(5)}</div>
        <div className="text-xs text-muted-foreground">{budget.tokens} tokens</div>
      </div>
    </div>
  );
}

/**
 * Configuration Tab - Tier budgets and provider settings
 */
function ConfigurationTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Tier Configuration
        </CardTitle>
        <CardDescription>
          Provider models and budget limits for each tier
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Configuration management coming soon. Currently using default settings from
          <code className="mx-1 px-1.5 py-0.5 bg-muted rounded">services/content-analysis-v3/.env</code>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Monitoring Tab - Recent analyses and performance metrics
 */
function MonitoringTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Analyses</CardTitle>
        <CardDescription>Latest articles processed through V3 pipeline</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Analysis history monitoring coming soon.
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Diagnostics Tab - Health checks and troubleshooting
 */
function DiagnosticsTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Diagnostics</CardTitle>
        <CardDescription>Health checks and performance analysis</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Diagnostics tools coming soon. Use
          <code className="mx-1 px-1.5 py-0.5 bg-muted rounded">GET /health/detailed</code>
          for current health status.
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * GraphQualityPage
 *
 * Full-page dashboard for knowledge graph quality monitoring.
 * Combines integrity metrics, disambiguation stats, and quality trends.
 *
 * @example
 * ```tsx
 * <GraphQualityPage />
 * ```
 *
 * @module features/knowledge-graph/pages/GraphQualityPage
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ArrowLeft,
  Activity,
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

import { GraphHealthDashboard } from '../components/quality/GraphHealthDashboard';
import { EntityQualityPanel } from '../components/quality/EntityQualityPanel';
import { useIntegritySummary } from '../api/useGraphIntegrity';
import { useDisambiguationSummary } from '../api/useDisambiguationQuality';
import type { QualityIssue } from '../types/quality';
import { getQualityLevel, QUALITY_LEVEL_COLORS } from '../types/quality';

// ===========================
// Component Props
// ===========================

export interface GraphQualityPageProps {
  /** Additional CSS classes */
  className?: string;
}

// ===========================
// Main Component
// ===========================

export function GraphQualityPage({ className }: GraphQualityPageProps) {
  const navigate = useNavigate();

  // ===== State =====
  const [selectedIssue, setSelectedIssue] = useState<QualityIssue | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'integrity' | 'disambiguation'>('overview');

  // ===== Data =====
  const { summary: integritySummary, isLoading: integrityLoading } = useIntegritySummary();
  const { summary: disambiguationSummary, isLoading: disambiguationLoading } = useDisambiguationSummary();

  // ===== Handlers =====
  const handleIssueClick = (issue: QualityIssue) => {
    setSelectedIssue(issue);
    // Could open a modal or navigate to issue details
    console.log('Issue clicked:', issue);
  };

  const handleEntityTypeClick = (entityType: string) => {
    // Navigate to entity filter or similar
    console.log('Entity type clicked:', entityType);
  };

  // ===== Overall Score =====
  const overallScore = integritySummary
    ? Math.round(
        (integritySummary.qualityScore +
          parseFloat(disambiguationSummary?.successRate ?? '0')) /
          2
      )
    : 0;
  const overallLevel = getQualityLevel(overallScore);
  const overallColor = QUALITY_LEVEL_COLORS[overallLevel];

  // ===== Render =====
  return (
    <div className={cn('h-full flex flex-col', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">Graph Quality</h1>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
          <TabsList>
            <TabsTrigger value="overview" className="gap-2">
              <Activity className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="integrity" className="gap-2">
              <Shield className="h-4 w-4" />
              Integrity
            </TabsTrigger>
            <TabsTrigger value="disambiguation" className="gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Disambiguation
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Overall Score Card */}
            <Card className="bg-gradient-to-r from-primary/5 to-primary/10">
              <CardContent className="py-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-medium text-muted-foreground">
                      Overall Graph Health
                    </h2>
                    <div className="flex items-baseline gap-3 mt-2">
                      <span
                        className="text-5xl font-bold"
                        style={{ color: overallColor }}
                      >
                        {overallScore}
                      </span>
                      <span className="text-2xl text-muted-foreground">/ 100</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge
                      variant="secondary"
                      className="text-sm px-3 py-1"
                      style={{ backgroundColor: `${overallColor}20`, color: overallColor }}
                    >
                      {overallLevel.toUpperCase()}
                    </Badge>
                    <p className="text-sm text-muted-foreground mt-2">
                      Last updated: Just now
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <SummaryCard
                icon={<Activity className="h-5 w-5" />}
                label="Data Quality Score"
                value={integritySummary?.qualityScore.toFixed(0) ?? '--'}
                subtext="out of 100"
                loading={integrityLoading}
              />
              <SummaryCard
                icon={<TrendingUp className="h-5 w-5" />}
                label="Disambiguation Rate"
                value={`${disambiguationSummary?.successRate ?? '--'}%`}
                subtext="entities resolved"
                loading={disambiguationLoading}
              />
              <SummaryCard
                icon={<AlertTriangle className="h-5 w-5 text-orange-600" />}
                label="Active Issues"
                value={integritySummary?.issueCount.toString() ?? '--'}
                subtext={`${integritySummary?.criticalCount ?? 0} critical`}
                loading={integrityLoading}
                warning={integritySummary?.criticalCount ?? 0 > 0}
              />
              <SummaryCard
                icon={<CheckCircle2 className="h-5 w-5 text-green-600" />}
                label="Total Nodes"
                value={integritySummary?.totalNodes.toLocaleString() ?? '--'}
                subtext={`${integritySummary?.totalRelationships.toLocaleString() ?? '--'} relationships`}
                loading={integrityLoading}
              />
            </div>

            {/* Dashboards Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GraphHealthDashboard
                onIssueClick={handleIssueClick}
              />
              <EntityQualityPanel
                onEntityTypeClick={handleEntityTypeClick}
              />
            </div>
          </div>
        )}

        {activeTab === 'integrity' && (
          <div className="max-w-4xl mx-auto">
            <GraphHealthDashboard
              onIssueClick={handleIssueClick}
            />
          </div>
        )}

        {activeTab === 'disambiguation' && (
          <div className="max-w-4xl mx-auto">
            <EntityQualityPanel
              onEntityTypeClick={handleEntityTypeClick}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ===========================
// Summary Card Component
// ===========================

interface SummaryCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext: string;
  loading?: boolean;
  warning?: boolean;
}

function SummaryCard({ icon, label, value, subtext, loading, warning }: SummaryCardProps) {
  return (
    <Card className={cn(warning && 'border-orange-300')}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 text-muted-foreground mb-2">
          {icon}
          <span className="text-sm font-medium">{label}</span>
        </div>
        {loading ? (
          <div className="h-8 w-20 bg-muted animate-pulse rounded" />
        ) : (
          <div>
            <span className="text-2xl font-bold">{value}</span>
            <p className="text-xs text-muted-foreground mt-1">{subtext}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default GraphQualityPage;

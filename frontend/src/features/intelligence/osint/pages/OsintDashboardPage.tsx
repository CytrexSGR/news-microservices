/**
 * OsintDashboardPage - OSINT Overview Dashboard
 *
 * Main dashboard showing OSINT monitoring overview with stats and quick actions
 */
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import {
  Shield,
  Network,
  Bell,
  Play,
  FileSearch,
  ChevronRight,
  AlertTriangle,
  Calendar,
  Activity,
} from 'lucide-react';
import { AlertStatsCard } from '../components/AlertStatsCard';
import { GraphQualityReport } from '../components/GraphQualityReport';
import { useOsintInstances, useAlertStats, useUnacknowledgedAlertsCount } from '../api';

export function OsintDashboardPage() {
  const { data: instancesData, isLoading: instancesLoading } = useOsintInstances({ per_page: 5 });
  const { data: alertStats } = useAlertStats();
  const { count: unackCount } = useUnacknowledgedAlertsCount();

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="h-8 w-8" />
            OSINT Monitoring
          </h1>
          <p className="text-muted-foreground mt-1">
            Open Source Intelligence monitoring and analysis
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/intelligence/osint/templates"
            className="inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
          >
            <FileSearch className="h-4 w-4" />
            Templates
          </Link>
          <Link
            to="/intelligence/osint/instances/create"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Play className="h-4 w-4" />
            New Instance
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Instances"
          value={instancesData?.instances.filter((i) => i.enabled).length ?? 0}
          total={instancesData?.total ?? 0}
          icon={<Calendar className="h-5 w-5" />}
          href="/intelligence/osint/instances"
        />
        <StatCard
          title="Pending Alerts"
          value={unackCount}
          highlight={unackCount > 0}
          icon={<Bell className="h-5 w-5" />}
          href="/intelligence/osint/alerts"
        />
        <StatCard
          title="Last 24h Alerts"
          value={alertStats?.last_24h ?? 0}
          icon={<AlertTriangle className="h-5 w-5" />}
          href="/intelligence/osint/alerts"
        />
        <StatCard
          title="Pattern Detection"
          value="Ready"
          icon={<Network className="h-5 w-5" />}
          href="/intelligence/osint/patterns"
        />
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Instances */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Recent Instances</CardTitle>
              <CardDescription>Latest OSINT monitoring instances</CardDescription>
            </div>
            <Link
              to="/intelligence/osint/instances"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              View all
              <ChevronRight className="h-4 w-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {instancesLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-muted" />
                    <div className="flex-1">
                      <div className="h-4 w-32 bg-muted rounded" />
                      <div className="h-3 w-24 bg-muted rounded mt-1" />
                    </div>
                  </div>
                ))}
              </div>
            ) : instancesData?.instances.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No instances yet</p>
                <Link
                  to="/intelligence/osint/templates"
                  className="text-primary hover:underline mt-2 inline-block"
                >
                  Browse templates to get started
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {instancesData?.instances.slice(0, 5).map((instance) => (
                  <Link
                    key={instance.id}
                    to={`/intelligence/osint/instances/${instance.id}`}
                    className="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                  >
                    <div
                      className={`rounded-full p-2 ${
                        instance.enabled ? 'bg-green-500/10 text-green-500' : 'bg-gray-500/10 text-gray-500'
                      }`}
                    >
                      {instance.enabled ? <Play className="h-4 w-4" /> : <Activity className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{instance.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {instance.template_name} - {instance.schedule || 'Manual'}
                      </div>
                    </div>
                    {instance.last_status && (
                      <Badge variant={instance.last_status === 'completed' ? 'default' : 'outline'}>
                        {instance.last_status}
                      </Badge>
                    )}
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Alert Stats */}
        <AlertStatsCard />
      </div>

      {/* Graph Quality */}
      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Network className="h-5 w-5" />
          Graph Quality
        </h2>
        <GraphQualityReport />
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <QuickLinkCard
          title="Pattern Detection"
          description="Analyze entities for intelligence patterns"
          icon={<Network className="h-6 w-6" />}
          href="/intelligence/osint/patterns"
        />
        <QuickLinkCard
          title="Graph Quality"
          description="View knowledge graph quality metrics"
          icon={<Activity className="h-6 w-6" />}
          href="/intelligence/osint/quality"
        />
        <QuickLinkCard
          title="Templates"
          description="Browse available OSINT templates"
          icon={<FileSearch className="h-6 w-6" />}
          href="/intelligence/osint/templates"
        />
        <QuickLinkCard
          title="Alerts"
          description="View and manage OSINT alerts"
          icon={<Bell className="h-6 w-6" />}
          href="/intelligence/osint/alerts"
          badge={unackCount > 0 ? unackCount : undefined}
        />
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number | string;
  total?: number;
  icon: React.ReactNode;
  href: string;
  highlight?: boolean;
}

function StatCard({ title, value, total, icon, href, highlight = false }: StatCardProps) {
  return (
    <Link to={href}>
      <Card className={`hover:shadow-md transition-shadow ${highlight ? 'border-yellow-500/50' : ''}`}>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div className="text-muted-foreground">{icon}</div>
            {highlight && <Badge variant="destructive">Action Required</Badge>}
          </div>
          <div className="mt-2">
            <div className={`text-2xl font-bold ${highlight ? 'text-yellow-500' : ''}`}>
              {value}
              {total !== undefined && (
                <span className="text-sm font-normal text-muted-foreground"> / {total}</span>
              )}
            </div>
            <div className="text-sm text-muted-foreground">{title}</div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

interface QuickLinkCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
}

function QuickLinkCard({ title, description, icon, href, badge }: QuickLinkCardProps) {
  return (
    <Link to={href}>
      <Card className="hover:shadow-md hover:border-primary/50 transition-all h-full">
        <CardContent className="pt-4">
          <div className="flex items-start justify-between">
            <div className="rounded-md bg-primary/10 p-2 text-primary">{icon}</div>
            {badge !== undefined && (
              <Badge variant="destructive">{badge}</Badge>
            )}
          </div>
          <div className="mt-3">
            <div className="font-medium">{title}</div>
            <div className="text-sm text-muted-foreground">{description}</div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export default OsintDashboardPage;

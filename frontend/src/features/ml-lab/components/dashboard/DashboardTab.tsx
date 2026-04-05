/**
 * ML Lab Dashboard Tab
 *
 * Overview of ML Lab statistics, gate status, top models, and recent alerts.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  Brain,
  CheckCircle2,
  Activity,
  TrendingUp,
  AlertTriangle,
  Loader2,
  Shield,
} from 'lucide-react';

import { dashboardApi } from '../../api/mlLabApi';
import { MLArea, type DashboardResponse } from '../../types';
import { AREA_ICONS, STATUS_COLORS } from '../../utils/constants';

export function DashboardTab() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const data = await dashboardApi.get();
      setDashboard(data);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Failed to load dashboard data</AlertDescription>
      </Alert>
    );
  }

  const { stats } = dashboard;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              <div>
                <p className="text-2xl font-bold">{stats.total_models}</p>
                <p className="text-sm text-muted-foreground">Total Models</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{stats.active_models}</p>
                <p className="text-sm text-muted-foreground">Active Models</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{stats.running_training_jobs}</p>
                <p className="text-sm text-muted-foreground">Training Jobs</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold">
                  {stats.overall_win_rate != null
                    ? `${(stats.overall_win_rate * 100).toFixed(1)}%`
                    : 'N/A'}
                </p>
                <p className="text-sm text-muted-foreground">Win Rate (24h)</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gate Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Gate Status
          </CardTitle>
          <CardDescription>Active models per gate area</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.values(MLArea).map((area) => {
              const count = stats.models_by_area[area] || 0;
              return (
                <div
                  key={area}
                  className="flex flex-col items-center p-4 bg-muted rounded-lg"
                >
                  {AREA_ICONS[area]}
                  <span className="mt-2 text-sm font-medium capitalize">{area}</span>
                  <span className="text-lg font-bold">{count}</span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Top Models */}
        <Card>
          <CardHeader>
            <CardTitle>Top Models</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard.top_models.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">No trained models yet</p>
              ) : (
                dashboard.top_models.slice(0, 5).map((model) => (
                  <div key={model.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {AREA_ICONS[model.area]}
                      <span className="font-medium">{model.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {model.metrics?.test_accuracy && (
                        <span className="text-sm text-muted-foreground">
                          {(model.metrics.test_accuracy * 100).toFixed(1)}%
                        </span>
                      )}
                      <Badge className={STATUS_COLORS[model.status]}>{model.status}</Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard.recent_alerts.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">No alerts</p>
              ) : (
                dashboard.recent_alerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} className="flex items-start gap-2">
                    <AlertTriangle
                      className={`h-4 w-4 mt-0.5 ${
                        alert.severity === 'critical'
                          ? 'text-red-500'
                          : alert.severity === 'warning'
                            ? 'text-yellow-500'
                            : 'text-blue-500'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(alert.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default DashboardTab;

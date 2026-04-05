import React, { useState, useEffect } from 'react';
import { Activity, Server, AlertTriangle, CheckCircle, XCircle, Clock } from 'lucide-react';

interface Container {
  name: string;
  status: string;
  health: string | null;
  cpu_percent: number;
  memory_percent: number;
  memory_usage: string;
  pids: number;
  timestamp: string;
}

interface Summary {
  total_containers: number;
  healthy: number;
  unhealthy: number;
  no_healthcheck: number;
  running: number;
  stopped: number;
  avg_cpu_percent: number;
  avg_memory_percent: number;
  total_pids: number;
  recent_critical_alerts: number;
  recent_warning_alerts: number;
  timestamp: string;
}

interface Alert {
  timestamp: string;
  severity: string;
  service: string;
  message: string;
}

const HealthDashboard: React.FC = () => {
  const [containers, setContainers] = useState<Container[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Use current hostname for API calls (works for both localhost and LAN access)
  const API_BASE_URL = `http://${window.location.hostname}:8107/api/v1/health`;

  const fetchData = async () => {
    try {
      setRefreshing(true);
      const [containersRes, summaryRes, alertsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/containers`),
        fetch(`${API_BASE_URL}/summary`),
        fetch(`${API_BASE_URL}/alerts?limit=20`)
      ]);

      if (containersRes.ok) setContainers(await containersRes.json());
      if (summaryRes.ok) setSummary(await summaryRes.json());
      if (alertsRes.ok) setAlerts(await alertsRes.json());

      setLastUpdated(new Date());
      setLoading(false);
      setRefreshing(false);
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = autoRefresh ? setInterval(fetchData, 5000) : null;
    return () => { if (interval) clearInterval(interval); };
  }, [autoRefresh]);

  const getHealthColor = (container: Container) => {
    const { status, health } = container;

    // Stopped/exited containers (not an error, just disabled)
    if (status !== 'running') {
      return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-950/50 border border-gray-300 dark:border-gray-700';
    }

    // Running containers with health checks
    if (health === 'healthy') return 'text-green-700 bg-green-100 dark:text-green-400 dark:bg-green-950/50 border border-green-300 dark:border-green-800';
    if (health === 'unhealthy') return 'text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-950/50 border border-red-300 dark:border-red-800';

    // Running containers without health check
    return 'text-muted-foreground bg-muted border border-border';
  };

  const getHealthIcon = (container: Container) => {
    const { status, health } = container;

    // Stopped/exited containers
    if (status !== 'running') {
      return <Server className="w-4 h-4 opacity-50" />;
    }

    // Running containers
    if (health === 'healthy') return <CheckCircle className="w-4 h-4" />;
    if (health === 'unhealthy') return <XCircle className="w-4 h-4" />;
    return <Server className="w-4 h-4" />;
  };

  const getHealthLabel = (container: Container) => {
    const { status, health } = container;

    // Stopped/exited containers
    if (status !== 'running') {
      return 'stopped';
    }

    // Running containers
    return health || 'N/A';
  };

  const getSeverityColor = (severity: string) => {
    if (severity === 'CRITICAL') return 'bg-red-100 text-red-800 border-red-200 dark:bg-red-950/50 dark:text-red-400 dark:border-red-800';
    if (severity === 'WARNING') return 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-950/50 dark:text-yellow-400 dark:border-yellow-800';
    return 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-800';
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen bg-background">
      <Activity className="w-8 h-8 animate-spin text-primary" />
    </div>;
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
              <Activity className={`w-8 h-8 text-primary ${refreshing ? 'animate-spin' : ''}`} />
              System Health Monitor
            </h1>
            <p className="text-muted-foreground mt-1">Real-time container health and resource metrics (5s refresh)</p>
            {lastUpdated && (
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Last updated: {lastUpdated.toLocaleTimeString()}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2 items-end">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg transition ${
                autoRefresh
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </button>
            <button
              onClick={fetchData}
              disabled={refreshing}
              className="px-4 py-2 rounded-lg bg-muted text-muted-foreground hover:bg-muted/80 disabled:opacity-50 transition"
            >
              Refresh Now
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-card border border-border p-4 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm">Total Containers</p>
                  <p className="text-2xl font-bold text-foreground">{summary.total_containers}</p>
                </div>
                <Server className="w-8 h-8 text-primary" />
              </div>
            </div>

            <div className="bg-card border border-border p-4 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm">Healthy</p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-500">{summary.healthy}</p>
                  {summary.stopped > 0 && (
                    <p className="text-xs text-muted-foreground mt-1">{summary.stopped} stopped</p>
                  )}
                </div>
                <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-500" />
              </div>
            </div>

            <div className="bg-card border border-border p-4 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm">Avg CPU</p>
                  <p className="text-2xl font-bold text-foreground">{summary.avg_cpu_percent.toFixed(1)}%</p>
                </div>
                <Activity className="w-8 h-8 text-purple-600 dark:text-purple-500" />
              </div>
            </div>

            <div className="bg-card border border-border p-4 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm">Avg Memory</p>
                  <p className="text-2xl font-bold text-foreground">{summary.avg_memory_percent.toFixed(1)}%</p>
                </div>
                <Activity className="w-8 h-8 text-orange-600 dark:text-orange-500" />
              </div>
            </div>
          </div>
        )}

        {/* Containers Grid */}
        <div className="bg-card border border-border rounded-lg shadow-sm mb-6 p-6">
          <h2 className="text-xl font-bold text-foreground mb-4">Container Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {containers.map((container) => (
              <div key={container.name} className="border border-border rounded-lg p-4 hover:border-primary/50 transition bg-card/50">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium text-sm truncate flex-1 text-foreground">{container.name}</span>
                  <span className={`ml-2 px-2 py-1 rounded text-xs flex items-center gap-1 font-semibold ${getHealthColor(container)}`}>
                    {getHealthIcon(container)}
                    {getHealthLabel(container)}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="block text-muted-foreground">CPU</span>
                    <span className="font-semibold text-foreground">{container.cpu_percent.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="block text-muted-foreground">Memory</span>
                    <span className="font-semibold text-foreground">{container.memory_percent.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="block text-muted-foreground">PIDs</span>
                    <span className="font-semibold text-foreground">{container.pids}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts Timeline */}
        <div className="bg-card border border-border rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-500" />
            Recent Alerts
          </h2>
          {alerts.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No recent alerts</p>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert, idx) => (
                <div key={idx} className={`p-3 rounded-lg border flex items-start gap-3 ${getSeverityColor(alert.severity)}`}>
                  <Clock className="w-4 h-4 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold">{alert.service}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-background/80 border border-border font-medium">{alert.severity}</span>
                    </div>
                    <p className="text-sm">{alert.message}</p>
                    <p className="text-xs mt-1 opacity-75">{alert.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthDashboard;

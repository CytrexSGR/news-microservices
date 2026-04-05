/**
 * AlertsPage - OSINT Alerts Page
 *
 * Page for viewing and managing OSINT alerts
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Bell, Filter } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { AlertsTable } from '../components/AlertsTable';
import { AlertStatsCard } from '../components/AlertStatsCard';
import type { AlertSeverity } from '../types/osint.types';
import { getSeverityColor, getSeverityBgColor } from '../types/osint.types';

const severities: AlertSeverity[] = ['critical', 'high', 'medium', 'low'];

export function AlertsPage() {
  const [selectedSeverity, setSelectedSeverity] = useState<AlertSeverity | undefined>();
  const [showAcknowledged, setShowAcknowledged] = useState<boolean | undefined>(false);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/intelligence/osint"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6" />
            OSINT Alerts
          </h1>
          <p className="text-muted-foreground">
            View and manage OSINT monitoring alerts
          </p>
        </div>
      </div>

      {/* Alert Stats */}
      <AlertStatsCard />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Severity:</span>
          <button
            onClick={() => setSelectedSeverity(undefined)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              !selectedSeverity
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted-foreground/10'
            }`}
          >
            All
          </button>
          {severities.map((severity) => (
            <button
              key={severity}
              onClick={() => setSelectedSeverity(severity)}
              className={`rounded-full px-3 py-1 text-sm transition-colors capitalize ${
                selectedSeverity === severity
                  ? `${getSeverityBgColor(severity)} ${getSeverityColor(severity)} border border-current`
                  : 'bg-muted hover:bg-muted-foreground/10'
              }`}
            >
              {severity}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Status:</span>
          <button
            onClick={() => setShowAcknowledged(undefined)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              showAcknowledged === undefined
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted-foreground/10'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setShowAcknowledged(false)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              showAcknowledged === false
                ? 'bg-yellow-500/20 text-yellow-600 border border-yellow-500/50'
                : 'bg-muted hover:bg-muted-foreground/10'
            }`}
          >
            Pending
          </button>
          <button
            onClick={() => setShowAcknowledged(true)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              showAcknowledged === true
                ? 'bg-green-500/20 text-green-600 border border-green-500/50'
                : 'bg-muted hover:bg-muted-foreground/10'
            }`}
          >
            Acknowledged
          </button>
        </div>
      </div>

      {/* Alerts Table */}
      <AlertsTable
        severity={selectedSeverity}
        acknowledged={showAcknowledged}
      />
    </div>
  );
}

export default AlertsPage;

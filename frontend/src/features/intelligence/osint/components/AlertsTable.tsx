/**
 * AlertsTable - OSINT Alerts Table with Acknowledgement
 *
 * Displays OSINT alerts in a sortable table with acknowledge actions
 */
import { DataTable, type Column } from '@/components/ui/DataTable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { useOsintAlerts } from '../api';
import type { OsintAlert, AlertSeverity } from '../types/osint.types';
import { getSeverityColor, getSeverityBgColor } from '../types/osint.types';
import { AlertAckButton } from './AlertAckButton';

interface AlertsTableProps {
  instanceId?: string;
  severity?: AlertSeverity;
  acknowledged?: boolean;
  onAlertSelect?: (alert: OsintAlert) => void;
}

export function AlertsTable({
  instanceId,
  severity,
  acknowledged,
  onAlertSelect,
}: AlertsTableProps) {
  const { data, isLoading, error } = useOsintAlerts({
    instance_id: instanceId,
    severity,
    acknowledged,
  });

  if (isLoading) {
    return <AlertsTableSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load alerts</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.alerts.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground py-8">
            <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No alerts found</p>
            <p className="text-sm mt-1">
              {acknowledged === false
                ? 'All alerts have been acknowledged'
                : 'No alerts match the current filters'}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const columns: Column<OsintAlert>[] = [
    {
      header: 'Severity',
      accessor: (row) => (
        <Badge
          className={`${getSeverityBgColor(row.severity)} ${getSeverityColor(row.severity)} border-0`}
        >
          <SeverityIcon severity={row.severity} />
          <span className="ml-1 capitalize">{row.severity}</span>
        </Badge>
      ),
      sortKey: 'severity',
      sortFn: (a, b) => {
        const order: Record<AlertSeverity, number> = {
          critical: 4,
          high: 3,
          medium: 2,
          low: 1,
        };
        return order[a.severity] - order[b.severity];
      },
    },
    {
      header: 'Title',
      accessor: (row) => (
        <div>
          <div
            className={`font-medium ${onAlertSelect ? 'cursor-pointer hover:text-primary' : ''}`}
            onClick={() => onAlertSelect?.(row)}
          >
            {row.title}
          </div>
          {row.instance_name && (
            <div className="text-xs text-muted-foreground">{row.instance_name}</div>
          )}
        </div>
      ),
      sortKey: 'title',
    },
    {
      header: 'Description',
      accessor: (row) => (
        <div className="max-w-md truncate text-sm text-muted-foreground">
          {row.description}
        </div>
      ),
    },
    {
      header: 'Created',
      accessor: (row) => (
        <div className="flex items-center gap-1 text-sm">
          <Clock className="h-3 w-3" />
          {new Date(row.created_at).toLocaleString()}
        </div>
      ),
      sortKey: 'created_at',
    },
    {
      header: 'Status',
      accessor: (row) =>
        row.acknowledged ? (
          <div className="flex items-center gap-1 text-green-500 text-sm">
            <CheckCircle2 className="h-4 w-4" />
            <span>Acknowledged</span>
          </div>
        ) : (
          <Badge variant="outline" className="text-yellow-500 border-yellow-500/50">
            Pending
          </Badge>
        ),
    },
    {
      header: 'Actions',
      accessor: (row) =>
        !row.acknowledged && (
          <AlertAckButton alertId={row.id} alertTitle={row.title} size="sm" />
        ),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Alerts ({data.total})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <DataTable
          data={data.alerts}
          columns={columns}
          keyExtractor={(row) => row.id}
        />
      </CardContent>
    </Card>
  );
}

interface SeverityIconProps {
  severity: AlertSeverity;
}

function SeverityIcon({ severity }: SeverityIconProps) {
  switch (severity) {
    case 'critical':
      return <AlertTriangle className="h-3 w-3" />;
    case 'high':
      return <AlertCircle className="h-3 w-3" />;
    case 'medium':
      return <AlertTriangle className="h-3 w-3" />;
    case 'low':
      return <Bell className="h-3 w-3" />;
    default:
      return <Bell className="h-3 w-3" />;
  }
}

function AlertsTableSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-5 w-20" />
              <div className="flex-1">
                <Skeleton className="h-4 w-48 mb-1" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-24" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default AlertsTable;

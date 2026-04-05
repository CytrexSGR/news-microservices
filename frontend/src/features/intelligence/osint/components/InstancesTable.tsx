/**
 * InstancesTable - OSINT Instances List Table
 *
 * Displays OSINT monitoring instances in a sortable table
 */
import { DataTable, type Column } from '@/components/ui/DataTable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Play,
  Pause,
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { useOsintInstances } from '../api';
import type { OsintInstance, ExecutionStatus } from '../types/osint.types';
import { getStatusColor, getStatusBgColor } from '../types/osint.types';
import { InstanceExecuteButton } from './InstanceExecuteButton';
import { InstanceDeleteButton } from './InstanceDeleteButton';

interface InstancesTableProps {
  templateName?: string;
  onInstanceSelect?: (instance: OsintInstance) => void;
  onEditInstance?: (instance: OsintInstance) => void;
}

export function InstancesTable({
  templateName,
  onInstanceSelect,
  onEditInstance,
}: InstancesTableProps) {
  const { data, isLoading, error } = useOsintInstances({ template_name: templateName });

  if (isLoading) {
    return <InstancesTableSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load instances</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.instances.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground py-8">
            <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No OSINT instances found</p>
            <p className="text-sm mt-1">Create an instance to start monitoring</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const columns: Column<OsintInstance>[] = [
    {
      header: 'Name',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <div
            className={`rounded-full p-1 ${row.enabled ? 'bg-green-500/10' : 'bg-gray-500/10'}`}
          >
            {row.enabled ? (
              <Play className="h-3 w-3 text-green-500" />
            ) : (
              <Pause className="h-3 w-3 text-gray-500" />
            )}
          </div>
          <div>
            <div
              className={`font-medium ${onInstanceSelect ? 'cursor-pointer hover:text-primary' : ''}`}
              onClick={() => onInstanceSelect?.(row)}
            >
              {row.name}
            </div>
            <div className="text-xs text-muted-foreground">{row.template_name}</div>
          </div>
        </div>
      ),
      sortKey: 'name',
    },
    {
      header: 'Status',
      accessor: (row) => {
        if (!row.last_status) {
          return <Badge variant="outline">Not run</Badge>;
        }
        return (
          <Badge className={`${getStatusBgColor(row.last_status)} ${getStatusColor(row.last_status)} border-0`}>
            {row.last_status}
          </Badge>
        );
      },
      sortKey: 'last_status',
    },
    {
      header: 'Schedule',
      accessor: (row) => (
        <div className="flex items-center gap-1 text-sm">
          <Clock className="h-3 w-3" />
          {row.schedule || 'Manual'}
        </div>
      ),
    },
    {
      header: 'Last Run',
      accessor: (row) =>
        row.last_run ? (
          <span className="text-sm">{new Date(row.last_run).toLocaleString()}</span>
        ) : (
          <span className="text-sm text-muted-foreground">Never</span>
        ),
      sortKey: 'last_run',
    },
    {
      header: 'Runs',
      accessor: 'run_count',
      sortKey: 'run_count',
    },
    {
      header: 'Actions',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <InstanceExecuteButton
            instanceId={row.id}
            instanceName={row.name}
            disabled={!row.enabled}
            size="sm"
          />
          {onEditInstance && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEditInstance(row);
              }}
              className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              Edit
            </button>
          )}
          <InstanceDeleteButton instanceId={row.id} instanceName={row.name} size="sm" />
        </div>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>OSINT Instances ({data.total})</CardTitle>
      </CardHeader>
      <CardContent>
        <DataTable
          data={data.instances}
          columns={columns}
          keyExtractor={(row) => row.id}
        />
      </CardContent>
    </Card>
  );
}

function InstancesTableSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-48" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="flex-1">
                <Skeleton className="h-4 w-32 mb-1" />
                <Skeleton className="h-3 w-24" />
              </div>
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-32" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default InstancesTable;

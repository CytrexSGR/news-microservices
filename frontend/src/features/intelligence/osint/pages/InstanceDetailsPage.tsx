/**
 * InstanceDetailsPage - Instance Detail Page
 *
 * Page for viewing and managing a specific OSINT instance
 */
import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  Calendar,
  Play,
  Pause,
  Clock,
  Settings,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { useOsintInstance, useExecuteOsint } from '../api';
import { InstanceEditForm } from '../components/InstanceEditForm';
import { InstanceExecuteButton } from '../components/InstanceExecuteButton';
import { InstanceDeleteButton } from '../components/InstanceDeleteButton';
import { ExecutionResultView } from '../components/ExecutionResultView';
import type { OsintInstance } from '../types/osint.types';

export function InstanceDetailsPage() {
  const { instanceId } = useParams<{ instanceId: string }>();
  const navigate = useNavigate();
  const { instance, isLoading, error, isNotFound } = useOsintInstance(instanceId);
  const [isEditing, setIsEditing] = useState(false);
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-muted rounded" />
          <div className="h-4 w-64 bg-muted rounded" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (error || isNotFound || !instance) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-semibold">Instance Not Found</h2>
          <p className="text-muted-foreground mt-2">
            The requested instance could not be found.
          </p>
          <Link
            to="/intelligence/osint/instances"
            className="text-primary hover:underline mt-4 inline-block"
          >
            Back to instances
          </Link>
        </div>
      </div>
    );
  }

  if (isEditing) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsEditing(false)}
            className="rounded-md p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold">Edit Instance</h1>
            <p className="text-muted-foreground">Update {instance.name} configuration</p>
          </div>
        </div>
        <InstanceEditForm
          instance={instance}
          onSuccess={() => setIsEditing(false)}
          onCancel={() => setIsEditing(false)}
        />
      </div>
    );
  }

  const handleExecutionStarted = (executionId: string) => {
    setActiveExecutionId(executionId);
  };

  const handleDeleted = () => {
    navigate('/intelligence/osint/instances');
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/intelligence/osint/instances"
            className="rounded-md p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              {instance.enabled ? (
                <Play className="h-6 w-6 text-green-500" />
              ) : (
                <Pause className="h-6 w-6 text-gray-500" />
              )}
              {instance.name}
            </h1>
            <p className="text-muted-foreground">{instance.template_name}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <InstanceExecuteButton
            instanceId={instance.id}
            instanceName={instance.name}
            disabled={!instance.enabled}
            onExecutionStarted={handleExecutionStarted}
          />
          <button
            onClick={() => setIsEditing(true)}
            className="inline-flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
          >
            <Settings className="h-4 w-4" />
            Edit
          </button>
          <InstanceDeleteButton
            instanceId={instance.id}
            instanceName={instance.name}
            onDeleted={handleDeleted}
          />
        </div>
      </div>

      {/* Instance Info */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Instance Details</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-4">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Status</dt>
                <dd>
                  <Badge variant={instance.enabled ? 'default' : 'secondary'}>
                    {instance.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Template</dt>
                <dd className="font-medium">{instance.template_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Schedule</dt>
                <dd className="font-medium">{instance.schedule || 'Manual'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Run Count</dt>
                <dd className="font-medium">{instance.run_count ?? 0}</dd>
              </div>
              {instance.last_status && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Last Status</dt>
                  <dd>
                    <Badge
                      variant={instance.last_status === 'completed' ? 'default' : 'outline'}
                    >
                      {instance.last_status}
                    </Badge>
                  </dd>
                </div>
              )}
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Schedule Info</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-4">
              <div className="flex justify-between">
                <dt className="text-muted-foreground flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  Created
                </dt>
                <dd>{new Date(instance.created_at).toLocaleString()}</dd>
              </div>
              {instance.updated_at && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Updated</dt>
                  <dd>{new Date(instance.updated_at).toLocaleString()}</dd>
                </div>
              )}
              {instance.last_run && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Last Run</dt>
                  <dd>{new Date(instance.last_run).toLocaleString()}</dd>
                </div>
              )}
              {instance.next_run && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Next Run</dt>
                  <dd>{new Date(instance.next_run).toLocaleString()}</dd>
                </div>
              )}
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Parameters */}
      {Object.keys(instance.parameters).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded-lg bg-muted p-4 text-sm overflow-x-auto">
              {JSON.stringify(instance.parameters, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Description */}
      {instance.description && (
        <Card>
          <CardHeader>
            <CardTitle>Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{instance.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Active Execution */}
      {activeExecutionId && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Execution Results</h2>
          <ExecutionResultView executionId={activeExecutionId} />
        </div>
      )}
    </div>
  );
}

export default InstanceDetailsPage;

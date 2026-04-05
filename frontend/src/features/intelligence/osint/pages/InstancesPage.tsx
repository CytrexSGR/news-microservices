/**
 * InstancesPage - OSINT Instances List Page
 *
 * Page for managing OSINT monitoring instances
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Calendar, Plus, Filter } from 'lucide-react';
import { InstancesTable } from '../components/InstancesTable';
import type { OsintInstance } from '../types/osint.types';

export function InstancesPage() {
  const navigate = useNavigate();
  const [templateFilter, setTemplateFilter] = useState<string | undefined>();
  const [editingInstance, setEditingInstance] = useState<OsintInstance | null>(null);

  const handleInstanceSelect = (instance: OsintInstance) => {
    navigate(`/intelligence/osint/instances/${instance.id}`);
  };

  const handleEditInstance = (instance: OsintInstance) => {
    navigate(`/intelligence/osint/instances/${instance.id}/edit`);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/intelligence/osint"
            className="rounded-md p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Calendar className="h-6 w-6" />
              OSINT Instances
            </h1>
            <p className="text-muted-foreground">
              Manage your OSINT monitoring instances
            </p>
          </div>
        </div>
        <Link
          to="/intelligence/osint/instances/create"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Instance
        </Link>
      </div>

      {/* Instances Table */}
      <InstancesTable
        templateName={templateFilter}
        onInstanceSelect={handleInstanceSelect}
        onEditInstance={handleEditInstance}
      />
    </div>
  );
}

export default InstancesPage;

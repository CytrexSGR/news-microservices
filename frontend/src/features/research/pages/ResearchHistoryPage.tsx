/**
 * ResearchHistoryPage
 *
 * Full research history with table view:
 * - Sortable columns
 * - Advanced filtering
 * - Pagination
 * - Batch actions
 */

import { History } from 'lucide-react';
import { ResearchHistoryTable } from '../components/ResearchHistoryTable';

export function ResearchHistoryPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <History className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-foreground">
            Research History
          </h1>
          <p className="text-sm text-muted-foreground">
            View and manage all your research tasks
          </p>
        </div>
      </div>

      {/* Table */}
      <ResearchHistoryTable />
    </div>
  );
}

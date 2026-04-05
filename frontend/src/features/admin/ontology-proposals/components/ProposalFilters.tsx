/**
 * ProposalFilters Component
 *
 * Filter controls for ontology proposals list.
 */

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { X } from 'lucide-react';
import type { ProposalStatus, Severity, ChangeType } from '@/lib/api/ontologyProposals';

interface ProposalFiltersProps {
  status?: ProposalStatus;
  severity?: Severity;
  changeType?: ChangeType;
  onStatusChange: (status?: ProposalStatus) => void;
  onSeverityChange: (severity?: Severity) => void;
  onChangeTypeChange: (changeType?: ChangeType) => void;
  onClearFilters: () => void;
}

export function ProposalFilters({
  status,
  severity,
  changeType,
  onStatusChange,
  onSeverityChange,
  onChangeTypeChange,
  onClearFilters,
}: ProposalFiltersProps) {
  const hasFilters = status || severity || changeType;

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Status Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Status:</label>
        <Select value={status || 'all'} onValueChange={(v) => onStatusChange(v === 'all' ? undefined : v as ProposalStatus)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="ACCEPTED">Accepted</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
            <SelectItem value="IMPLEMENTED">Implemented</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Severity Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Severity:</label>
        <Select value={severity || 'all'} onValueChange={(v) => onSeverityChange(v === 'all' ? undefined : v as Severity)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All severities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            <SelectItem value="CRITICAL">Critical</SelectItem>
            <SelectItem value="HIGH">High</SelectItem>
            <SelectItem value="MEDIUM">Medium</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Change Type Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Type:</label>
        <Select value={changeType || 'all'} onValueChange={(v) => onChangeTypeChange(v === 'all' ? undefined : v as ChangeType)}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="NEW_ENTITY_TYPE">New Entity Type</SelectItem>
            <SelectItem value="NEW_RELATIONSHIP_TYPE">New Relationship Type</SelectItem>
            <SelectItem value="MODIFY_ENTITY_TYPE">Modify Entity Type</SelectItem>
            <SelectItem value="MODIFY_RELATIONSHIP_TYPE">Modify Relationship Type</SelectItem>
            <SelectItem value="FLAG_INCONSISTENCY">Flag Inconsistency</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Clear Filters */}
      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={onClearFilters} className="gap-1">
          <X className="h-4 w-4" />
          Clear Filters
        </Button>
      )}
    </div>
  );
}

/**
 * ProposalsListPage
 *
 * Main page for listing and filtering ontology proposals.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { RefreshCw } from 'lucide-react';
import { ProposalsList } from '../components/ProposalsList';
import { ProposalFilters } from '../components/ProposalFilters';
import { StatisticsCards } from '../components/StatisticsCards';
import type { OntologyProposal, ProposalStatus, Severity, ChangeType } from '@/lib/api/ontologyProposals';

export function ProposalsListPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<ProposalStatus | undefined>();
  const [severity, setSeverity] = useState<Severity | undefined>();
  const [changeType, setChangeType] = useState<ChangeType | undefined>();
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSelectProposal = (proposal: OntologyProposal) => {
    navigate(`/admin/ontology/proposals/${proposal.id}`);
  };

  const handleClearFilters = () => {
    setStatus(undefined);
    setSeverity(undefined);
    setChangeType(undefined);
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Ontology Proposals</h1>
          <p className="text-muted-foreground">
            Review and manage OSS-generated ontology change proposals
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Statistics */}
      <StatisticsCards key={`stats-${refreshKey}`} />

      {/* Filters */}
      <div className="bg-card border rounded-lg p-4">
        <ProposalFilters
          status={status}
          severity={severity}
          changeType={changeType}
          onStatusChange={setStatus}
          onSeverityChange={setSeverity}
          onChangeTypeChange={setChangeType}
          onClearFilters={handleClearFilters}
        />
      </div>

      {/* Proposals List */}
      <ProposalsList
        key={`list-${refreshKey}`}
        status={status}
        severity={severity}
        changeType={changeType}
        onSelectProposal={handleSelectProposal}
      />
    </div>
  );
}

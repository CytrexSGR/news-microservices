/**
 * ProposalDetailPage
 *
 * Detailed view page for a single ontology proposal with accept/reject actions.
 */

import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getProposal } from '@/lib/api/ontologyProposals';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { ProposalDetail } from '../components/ProposalDetail';
import { ProposalActions } from '../components/ProposalActions';
import { ProposalImplementButton } from '../components/ProposalImplementButton';

export function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const proposalId = Number(id);

  const { data, isLoading, error } = useQuery({
    queryKey: ['ontology-proposal', proposalId],
    queryFn: () => getProposal(proposalId),
    enabled: !isNaN(proposalId),
  });

  const handleBack = () => {
    navigate('/admin/ontology/proposals');
  };

  const handleActionSuccess = () => {
    // Refresh data after action
    // Query will auto-refresh due to invalidation in ProposalActions
  };

  if (isNaN(proposalId)) {
    return (
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Invalid proposal ID</AlertDescription>
        </Alert>
        <Button onClick={handleBack} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to List
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Back Button */}
      <Button variant="ghost" onClick={handleBack} className="gap-2">
        <ArrowLeft className="h-4 w-4" />
        Back to Proposals
      </Button>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load proposal: {error instanceof Error ? error.message : 'Unknown error'}
          </AlertDescription>
        </Alert>
      )}

      {/* Content */}
      {data && (
        <>
          {/* Actions */}
          <div className="flex justify-end">
            {data.status === 'PENDING' && (
              <ProposalActions proposal={data} onSuccess={handleActionSuccess} />
            )}
            {data.status === 'ACCEPTED' && (
              <ProposalImplementButton proposal={data} onSuccess={handleActionSuccess} />
            )}
          </div>

          {/* Proposal Detail */}
          <ProposalDetail proposalId={proposalId} onBack={handleBack} />
        </>
      )}
    </div>
  );
}

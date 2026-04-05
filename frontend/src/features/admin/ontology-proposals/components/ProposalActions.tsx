/**
 * ProposalActions Component
 *
 * Accept/Reject actions for ontology proposals with dialogs.
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { acceptProposal, rejectProposal, type OntologyProposal } from '@/lib/api/ontologyProposals';
import { Button } from '@/components/ui/Button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { toast } from 'react-hot-toast';
import { CheckCircle, XCircle } from 'lucide-react';

interface ProposalActionsProps {
  proposal: OntologyProposal;
  onSuccess?: () => void;
}

export function ProposalActions({ proposal, onSuccess }: ProposalActionsProps) {
  const queryClient = useQueryClient();
  const [acceptDialogOpen, setAcceptDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [implementationNotes, setImplementationNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');

  // Accept Mutation
  const acceptMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) =>
      acceptProposal(id, 'andreas', notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ontology-proposals'] });
      queryClient.invalidateQueries({ queryKey: ['ontology-proposal', proposal.id] });
      queryClient.invalidateQueries({ queryKey: ['ontology-proposal-statistics'] });
      toast.success('Proposal accepted successfully!');
      setAcceptDialogOpen(false);
      setImplementationNotes('');
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Failed to accept proposal: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  // Reject Mutation
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      rejectProposal(id, 'andreas', reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ontology-proposals'] });
      queryClient.invalidateQueries({ queryKey: ['ontology-proposal', proposal.id] });
      queryClient.invalidateQueries({ queryKey: ['ontology-proposal-statistics'] });
      toast.success('Proposal rejected successfully!');
      setRejectDialogOpen(false);
      setRejectionReason('');
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Failed to reject proposal: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const handleAccept = () => {
    acceptMutation.mutate({ id: proposal.id, notes: implementationNotes });
  };

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }
    rejectMutation.mutate({ id: proposal.id, reason: rejectionReason });
  };

  // Only show actions for PENDING proposals
  if (proposal.status !== 'PENDING') {
    return null;
  }

  return (
    <div className="flex gap-3">
      {/* Accept Button */}
      <Button
        variant="default"
        className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
        onClick={() => setAcceptDialogOpen(true)}
      >
        <CheckCircle className="h-4 w-4" />
        Accept Proposal
      </Button>

      {/* Reject Button */}
      <Button
        variant="destructive"
        className="flex items-center gap-2"
        onClick={() => setRejectDialogOpen(true)}
      >
        <XCircle className="h-4 w-4" />
        Reject Proposal
      </Button>

      {/* Accept Dialog */}
      <Dialog open={acceptDialogOpen} onOpenChange={setAcceptDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Accept Proposal</DialogTitle>
            <DialogDescription>
              You are about to accept this ontology change proposal. This will mark it as approved for implementation.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="implementation-notes">Implementation Notes (Optional)</Label>
              <Textarea
                id="implementation-notes"
                placeholder="Add any notes about implementation..."
                value={implementationNotes}
                onChange={(e) => setImplementationNotes(e.target.value)}
                rows={4}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setAcceptDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-green-600 hover:bg-green-700"
              onClick={handleAccept}
              disabled={acceptMutation.isPending}
            >
              {acceptMutation.isPending ? 'Accepting...' : 'Accept Proposal'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reject Proposal</DialogTitle>
            <DialogDescription>
              You are about to reject this ontology change proposal. Please provide a reason.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="rejection-reason">Rejection Reason *</Label>
              <Textarea
                id="rejection-reason"
                placeholder="Explain why this proposal is being rejected..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                rows={4}
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setRejectDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={rejectMutation.isPending || !rejectionReason.trim()}
            >
              {rejectMutation.isPending ? 'Rejecting...' : 'Reject Proposal'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

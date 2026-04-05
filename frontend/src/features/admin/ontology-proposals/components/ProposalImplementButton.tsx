/**
 * ProposalImplementButton Component
 *
 * Implement button for ACCEPTED proposals - executes Cypher scripts against Neo4j.
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { implementProposal, type OntologyProposal } from '@/lib/api/ontologyProposals';
import { Button } from '@/components/ui/Button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { toast } from 'react-hot-toast';
import { Play, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ProposalImplementButtonProps {
  proposal: OntologyProposal;
  onSuccess?: () => void;
}

export function ProposalImplementButton({ proposal, onSuccess }: ProposalImplementButtonProps) {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [implementationResult, setImplementationResult] = useState<any>(null);

  // Implement Mutation
  const implementMutation = useMutation({
    mutationFn: (id: number) => implementProposal(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['ontology-proposals'] });
      queryClient.invalidateQueries({ queryKey: ['ontology-proposal', proposal.id] });
      queryClient.invalidateQueries({ queryKey: ['ontology-proposal-statistics'] });
      setImplementationResult(data.results);
      toast.success('Proposal implemented successfully!');
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Failed to implement proposal: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const handleImplement = () => {
    implementMutation.mutate(proposal.id);
  };

  return (
    <>
      <Button
        onClick={() => setDialogOpen(true)}
        className="gap-2"
        variant="default"
      >
        <Play className="h-4 w-4" />
        Implement Now
      </Button>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Implement Proposal</DialogTitle>
            <DialogDescription>
              Execute Cypher scripts to apply this proposal to the Knowledge Graph.
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-md">
              <p className="text-sm font-medium">{proposal.title}</p>
              <p className="text-xs text-muted-foreground mt-1">{proposal.change_type.replace(/_/g, ' ')}</p>
            </div>

            {implementationResult && (
              <Alert>
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-medium">Implementation Results:</p>
                    <pre className="text-xs bg-background p-2 rounded overflow-auto">
                      {JSON.stringify(implementationResult, null, 2)}
                    </pre>
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => {
                setDialogOpen(false);
                setImplementationResult(null);
              }}
              disabled={implementMutation.isPending}
            >
              {implementationResult ? 'Close' : 'Cancel'}
            </Button>
            {!implementationResult && (
              <Button
                onClick={handleImplement}
                disabled={implementMutation.isPending}
                className="gap-2"
              >
                {implementMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Execute Scripts
                  </>
                )}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

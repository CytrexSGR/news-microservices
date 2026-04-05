/**
 * ProposalsList Component
 *
 * Displays list of ontology change proposals with status, severity, and actions.
 */

import { useQuery } from '@tanstack/react-query';
import { getProposals, type OntologyProposal, type ProposalStatus, type Severity, type ChangeType } from '@/lib/api/ontologyProposals';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { AlertCircle, CheckCircle, Clock, XCircle, FileText } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ProposalsListProps {
  status?: ProposalStatus;
  severity?: Severity;
  changeType?: ChangeType;
  onSelectProposal: (proposal: OntologyProposal) => void;
}

const severityConfig = {
  CRITICAL: { color: 'bg-red-500', icon: AlertCircle, label: 'Critical' },
  HIGH: { color: 'bg-orange-500', icon: AlertCircle, label: 'High' },
  MEDIUM: { color: 'bg-yellow-500', icon: AlertCircle, label: 'Medium' },
  LOW: { color: 'bg-blue-500', icon: AlertCircle, label: 'Low' },
};

const statusConfig = {
  PENDING: { color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: Clock, label: 'Pending' },
  ACCEPTED: { color: 'bg-green-100 text-green-800 border-green-300', icon: CheckCircle, label: 'Accepted' },
  REJECTED: { color: 'bg-red-100 text-red-800 border-red-300', icon: XCircle, label: 'Rejected' },
  IMPLEMENTED: { color: 'bg-blue-100 text-blue-800 border-blue-300', icon: CheckCircle, label: 'Implemented' },
};

export function ProposalsList({ status, severity, changeType, onSelectProposal }: ProposalsListProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['ontology-proposals', { status, severity, change_type: changeType }],
    queryFn: () => getProposals({ status, severity, change_type: changeType }),
    refetchInterval: 30000, // Refresh every 30s
    staleTime: 0, // Always consider data stale, force fresh fetches
    gcTime: 0, // Don't cache data (previously cacheTime)
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6 border-destructive">
        <div className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <p>Failed to load proposals: {error instanceof Error ? error.message : 'Unknown error'}</p>
        </div>
      </Card>
    );
  }

  if (!data || data.proposals.length === 0) {
    return (
      <Card className="p-12">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <FileText className="h-12 w-12" />
          <p className="text-lg">No proposals found</p>
          <p className="text-sm">Try adjusting your filters or check back later</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {data.proposals.map((proposal) => {
        const SeverityIcon = severityConfig[proposal.severity].icon;
        const StatusIcon = statusConfig[proposal.status].icon;

        return (
          <Card
            key={proposal.id}
            className="p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onSelectProposal(proposal)}
          >
            <div className="flex items-start justify-between gap-4">
              {/* Left: Severity + Content */}
              <div className="flex gap-4 flex-1">
                {/* Severity Indicator */}
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 rounded-full ${severityConfig[proposal.severity].color} flex items-center justify-center`}>
                    <SeverityIcon className="h-5 w-5 text-white" />
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 space-y-2">
                  {/* Title */}
                  <div className="flex items-start gap-2">
                    <h3 className="font-semibold text-lg flex-1">{proposal.title}</h3>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {proposal.description}
                  </p>

                  {/* Metadata */}
                  <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <strong>ID:</strong> {proposal.proposal_id}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <strong>Occurrences:</strong> {proposal.occurrence_count}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <strong>Confidence:</strong> {(proposal.confidence * 100).toFixed(0)}%
                    </span>
                    <span>•</span>
                    <span title={new Date(proposal.created_at).toLocaleString()}>
                      {formatDistanceToNow(new Date(proposal.created_at), { addSuffix: true })}
                    </span>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5">
                    <Badge variant="secondary" className="text-xs">
                      {proposal.change_type.replace(/_/g, ' ')}
                    </Badge>
                    {proposal.tags && proposal.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {proposal.tags && proposal.tags.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{proposal.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: Status + Actions */}
              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                {/* Status Badge */}
                <Badge className={`${statusConfig[proposal.status].color} flex items-center gap-1`}>
                  <StatusIcon className="h-3 w-3" />
                  {statusConfig[proposal.status].label}
                </Badge>

                {/* Severity Badge */}
                <Badge variant="outline" className="text-xs">
                  {severityConfig[proposal.severity].label}
                </Badge>

                {/* Action Button */}
                <Button size="sm" variant="ghost" className="mt-2">
                  View Details →
                </Button>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

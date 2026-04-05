/**
 * ProposalDetail Component
 *
 * Detailed view of a single ontology proposal with evidence, impact analysis, and actions.
 */

import { useQuery } from '@tanstack/react-query';
import { getProposal, type OntologyProposal } from '@/lib/api/ontologyProposals';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertCircle,
  CheckCircle,

  Code,
  FileText,
  Info,
  Tag,
  TrendingUp,

} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ProposalDetailProps {
  proposalId: number;
  onBack: () => void;
}

const severityColors = {
  CRITICAL: 'bg-red-500 text-white',
  HIGH: 'bg-orange-500 text-white',
  MEDIUM: 'bg-yellow-500 text-white',
  LOW: 'bg-blue-500 text-white',
};

const statusColors = {
  PENDING: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  ACCEPTED: 'bg-green-100 text-green-800 border-green-300',
  REJECTED: 'bg-red-100 text-red-800 border-red-300',
  IMPLEMENTED: 'bg-blue-100 text-blue-800 border-blue-300',
};

export function ProposalDetail({ proposalId, _onBack }: ProposalDetailProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['ontology-proposal', proposalId],
    queryFn: () => getProposal(proposalId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load proposal: {error instanceof Error ? error.message : 'Unknown error'}
        </AlertDescription>
      </Alert>
    );
  }

  const proposal = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-3">
            <Badge className={severityColors[proposal.severity]}>
              {proposal.severity}
            </Badge>
            <Badge className={statusColors[proposal.status]}>
              {proposal.status}
            </Badge>
            <Badge variant="outline">{proposal.change_type.replace(/_/g, ' ')}</Badge>
          </div>
          <h1 className="text-3xl font-bold mt-2">{proposal.title}</h1>
          <p className="text-sm text-muted-foreground">
            ID: {proposal.proposal_id} • Created {formatDistanceToNow(new Date(proposal.created_at), { addSuffix: true })}
          </p>
        </div>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="evidence">Evidence ({proposal.evidence.length})</TabsTrigger>
          <TabsTrigger value="impact">Impact Analysis</TabsTrigger>
          <TabsTrigger value="query">Pattern Query</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Description
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap">{proposal.description}</p>
            </CardContent>
          </Card>

          {/* Metadata Grid */}
          <div className="grid gap-4 md:grid-cols-3">
            {/* Confidence */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <TrendingUp className="h-8 w-8 text-blue-500" />
                  <div>
                    <div className="text-2xl font-bold">{(proposal.confidence * 100).toFixed(0)}%</div>
                    <p className="text-xs text-muted-foreground">Confidence</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Occurrences */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Info className="h-8 w-8 text-orange-500" />
                  <div>
                    <div className="text-2xl font-bold">{proposal.occurrence_count}</div>
                    <p className="text-xs text-muted-foreground">Occurrences</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* OSS Version */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Code className="h-8 w-8 text-purple-500" />
                  <div>
                    <div className="text-2xl font-bold">{proposal.oss_version}</div>
                    <p className="text-xs text-muted-foreground">OSS Version</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tags */}
          {proposal.tags && proposal.tags.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tag className="h-5 w-5" />
                  Tags
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {proposal.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Review Info */}
          {proposal.reviewed_by && (
            <Card>
              <CardHeader>
                <CardTitle>Review Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div>
                  <span className="text-sm font-medium">Reviewed by:</span>{' '}
                  <span className="text-sm">{proposal.reviewed_by}</span>
                </div>
                {proposal.reviewed_at && (
                  <div>
                    <span className="text-sm font-medium">Reviewed at:</span>{' '}
                    <span className="text-sm">{new Date(proposal.reviewed_at).toLocaleString()}</span>
                  </div>
                )}
                {proposal.rejection_reason && (
                  <div>
                    <span className="text-sm font-medium">Rejection reason:</span>
                    <p className="text-sm text-muted-foreground mt-1">{proposal.rejection_reason}</p>
                  </div>
                )}
                {proposal.implementation_notes && (
                  <div>
                    <span className="text-sm font-medium">Implementation notes:</span>
                    <p className="text-sm text-muted-foreground mt-1">{proposal.implementation_notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Evidence Tab */}
        <TabsContent value="evidence" className="space-y-4">
          {proposal.evidence.map((evidence, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="text-sm">Evidence #{index + 1}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">ID:</span>
                    <code className="text-sm bg-muted px-2 py-1 rounded">{evidence.example_id}</code>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Type:</span>
                    <Badge variant="outline">{evidence.example_type}</Badge>
                  </div>
                  {evidence.context && (
                    <div>
                      <span className="text-sm font-medium">Context:</span>
                      <p className="text-sm text-muted-foreground mt-1">{evidence.context}</p>
                    </div>
                  )}
                  {evidence.frequency && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Frequency:</span>
                      <span className="text-sm">{evidence.frequency}</span>
                    </div>
                  )}
                </div>

                {/* Properties */}
                {evidence.properties && Object.keys(evidence.properties).length > 0 && (
                  <div>
                    <span className="text-sm font-medium block mb-2">Properties:</span>
                    <div className="bg-muted p-3 rounded-md">
                      <pre className="text-xs overflow-x-auto">
                        {JSON.stringify(evidence.properties, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Impact Analysis Tab */}
        <TabsContent value="impact" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Impact Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Stats Grid */}
              <div className="grid gap-4 md:grid-cols-2">
                {proposal.impact_analysis.affected_entities_count !== undefined && (
                  <div>
                    <span className="text-sm font-medium">Affected Entities:</span>
                    <p className="text-2xl font-bold">{proposal.impact_analysis.affected_entities_count}</p>
                  </div>
                )}
                {proposal.impact_analysis.affected_relationships_count !== undefined && (
                  <div>
                    <span className="text-sm font-medium">Affected Relationships:</span>
                    <p className="text-2xl font-bold">{proposal.impact_analysis.affected_relationships_count}</p>
                  </div>
                )}
                <div>
                  <span className="text-sm font-medium">Breaking Change:</span>
                  <p className="text-lg font-semibold">
                    {proposal.impact_analysis.breaking_change ? (
                      <Badge variant="destructive">Yes</Badge>
                    ) : (
                      <Badge variant="secondary">No</Badge>
                    )}
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium">Migration Complexity:</span>
                  <p className="text-lg font-semibold">
                    <Badge variant="outline">{proposal.impact_analysis.migration_complexity}</Badge>
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium">Estimated Effort:</span>
                  <p className="text-2xl font-bold">{proposal.impact_analysis.estimated_effort_hours}h</p>
                </div>
              </div>

              {/* Benefits */}
              <div>
                <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Benefits
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {proposal.impact_analysis.benefits.map((benefit, i) => (
                    <li key={i} className="text-sm">{benefit}</li>
                  ))}
                </ul>
              </div>

              {/* Risks */}
              <div>
                <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-orange-500" />
                  Risks
                </h3>
                <ul className="list-disc list-inside space-y-1">
                  {proposal.impact_analysis.risks.map((risk, i) => (
                    <li key={i} className="text-sm">{risk}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pattern Query Tab */}
        <TabsContent value="query">
          <Card>
            <CardHeader>
              <CardTitle>Pattern Detection Query</CardTitle>
            </CardHeader>
            <CardContent>
              {proposal.pattern_query ? (
                <div className="bg-muted p-4 rounded-md">
                  <pre className="text-sm overflow-x-auto whitespace-pre-wrap">{proposal.pattern_query}</pre>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No pattern query available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

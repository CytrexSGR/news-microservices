/**
 * StatisticsCards Component
 *
 * Overview statistics cards for ontology proposals.
 */

import { useQuery } from '@tanstack/react-query';
import { getProposalStatistics } from '@/lib/api/ontologyProposals';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { CheckCircle, Clock, FileText, TrendingUp, XCircle } from 'lucide-react';

export function StatisticsCards() {
  const { data, isLoading } = useQuery({
    queryKey: ['ontology-proposal-statistics'],
    queryFn: getProposalStatistics,
    refetchInterval: 30000, // Refresh every 30s (reduced from 60s)
    staleTime: 0, // Always consider data stale
    gcTime: 0, // Don't cache data
  });

  if (isLoading || !data) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-muted rounded"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted rounded mb-2"></div>
              <div className="h-3 w-24 bg-muted rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Proposals */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Proposals</CardTitle>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.total_proposals}</div>
          <p className="text-xs text-muted-foreground mt-1">
            All ontology proposals
          </p>
        </CardContent>
      </Card>

      {/* Pending */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
          <Clock className="h-4 w-4 text-yellow-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.pending_count}</div>
          <p className="text-xs text-muted-foreground mt-1">
            Awaiting human review
          </p>
        </CardContent>
      </Card>

      {/* Accepted */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Accepted</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.accepted_count}</div>
          <p className="text-xs text-muted-foreground mt-1">
            {data.implemented_count} implemented
          </p>
        </CardContent>
      </Card>

      {/* Average Confidence */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg. Confidence</CardTitle>
          <TrendingUp className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{(data.avg_confidence * 100).toFixed(0)}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            OSS detection accuracy
          </p>
        </CardContent>
      </Card>

      {/* By Severity */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm font-medium">By Severity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span className="text-xs font-medium">Critical</span>
              </div>
              <div className="text-lg font-bold">{data.by_severity.CRITICAL || 0}</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                <span className="text-xs font-medium">High</span>
              </div>
              <div className="text-lg font-bold">{data.by_severity.HIGH || 0}</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <span className="text-xs font-medium">Medium</span>
              </div>
              <div className="text-lg font-bold">{data.by_severity.MEDIUM || 0}</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-xs font-medium">Low</span>
              </div>
              <div className="text-lg font-bold">{data.by_severity.LOW || 0}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* By Status */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Status Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="flex flex-col items-center">
              <Clock className="h-6 w-6 text-yellow-500 mb-1" />
              <div className="text-lg font-bold">{data.pending_count}</div>
              <span className="text-xs text-muted-foreground">Pending</span>
            </div>
            <div className="flex flex-col items-center">
              <CheckCircle className="h-6 w-6 text-green-500 mb-1" />
              <div className="text-lg font-bold">{data.accepted_count}</div>
              <span className="text-xs text-muted-foreground">Accepted</span>
            </div>
            <div className="flex flex-col items-center">
              <XCircle className="h-6 w-6 text-red-500 mb-1" />
              <div className="text-lg font-bold">{data.rejected_count}</div>
              <span className="text-xs text-muted-foreground">Rejected</span>
            </div>
            <div className="flex flex-col items-center">
              <CheckCircle className="h-6 w-6 text-blue-500 mb-1" />
              <div className="text-lg font-bold">{data.implemented_count}</div>
              <span className="text-xs text-muted-foreground">Implemented</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

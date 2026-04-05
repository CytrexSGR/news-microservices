import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { FileSearch, CheckCircle2, XCircle, Clock, Info } from 'lucide-react'
import type { FeedResponse, AssessmentStatus } from '@/types/feedServiceAdmin'

interface AssessmentHistorySectionProps {
  feeds: FeedResponse[]
}

export function AssessmentHistorySection({ feeds }: AssessmentHistorySectionProps) {
  const getAssessmentStatusBadge = (status?: AssessmentStatus) => {
    switch (status) {
      case 'completed':
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </Badge>
        )
      case 'failed':
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        )
      case 'pending':
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        )
      default:
        return (
          <Badge variant="outline" className="gap-1">
            <Info className="h-3 w-3" />
            No Assessment
          </Badge>
        )
    }
  }

  const getTierBadgeVariant = (tier?: string) => {
    if (!tier) return 'outline'
    const lowerTier = tier.toLowerCase()
    if (lowerTier.includes('high') || lowerTier.includes('tier 1')) return 'default'
    if (lowerTier.includes('medium') || lowerTier.includes('tier 2')) return 'secondary'
    return 'outline'
  }

  const assessedFeeds = feeds.filter((feed) => feed.assessment)

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <FileSearch className="h-5 w-5" />
          Assessment History
        </h3>
        <Badge variant="outline">
          {assessedFeeds.length} of {feeds.length} feeds assessed
        </Badge>
      </div>

      {assessedFeeds.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <FileSearch className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No assessments found</p>
          <p className="text-sm mt-1">Trigger assessments from the Feed List table</p>
        </div>
      ) : (
        <div className="rounded-md border overflow-x-auto">
          <table className="w-full">
            <thead className="border-b">
              <tr className="text-sm">
                <th className="text-left p-3 font-medium">Feed Name</th>
                <th className="text-left p-3 font-medium">Status</th>
                <th className="text-left p-3 font-medium">Credibility Tier</th>
                <th className="text-left p-3 font-medium">Reputation Score</th>
                <th className="text-left p-3 font-medium">Political Bias</th>
                <th className="text-left p-3 font-medium">Assessment Date</th>
              </tr>
            </thead>
            <tbody>
              {assessedFeeds.map((feed) => {
                const assessment = feed.assessment!
                return (
                  <tr key={feed.id} className="border-b hover:bg-muted/50">
                    <td className="p-3">
                      <div>
                        <div className="font-medium">{feed.name}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-xs">
                          {feed.url}
                        </div>
                      </div>
                    </td>
                    <td className="p-3">
                      {getAssessmentStatusBadge(assessment.assessment_status)}
                    </td>
                    <td className="p-3">
                      {assessment.credibility_tier ? (
                        <Badge variant={getTierBadgeVariant(assessment.credibility_tier)}>
                          {assessment.credibility_tier}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">N/A</span>
                      )}
                    </td>
                    <td className="p-3">
                      {assessment.reputation_score !== undefined &&
                      assessment.reputation_score !== null ? (
                        <Badge variant="outline">{assessment.reputation_score}/100</Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">N/A</span>
                      )}
                    </td>
                    <td className="p-3">
                      {assessment.political_bias ? (
                        <Badge variant="secondary">{assessment.political_bias}</Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">N/A</span>
                      )}
                    </td>
                    <td className="p-3">
                      {assessment.assessment_date ? (
                        <div className="text-sm">
                          {new Date(assessment.assessment_date).toLocaleString()}
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-sm">N/A</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

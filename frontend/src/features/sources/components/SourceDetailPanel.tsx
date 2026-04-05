/**
 * SourceDetailPanel Component
 *
 * Displays comprehensive information about a single source,
 * including assessment data, scraping metrics, and associated feeds.
 */

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import {
  Globe,
  ExternalLink,
  RefreshCw,
  Edit,
  Rss,
  Shield,
  Activity,
  Clock,
  X,
  AlertCircle,
  CheckCircle,
  BarChart3,
  Building2,
  Calendar,
} from 'lucide-react'
import { SourceCredibilityBadge } from './SourceCredibilityBadge'
import { SourceStatusBadge, ScrapeStatusBadge } from './SourceStatusBadge'
import { useSource, useSourceFeeds, useSourceAssessmentHistory, useTriggerSourceAssessment } from '../hooks'
import type { Source, SourceFeed } from '@/types/source'
import { formatDistanceToNow, format } from 'date-fns'

interface SourceDetailPanelProps {
  sourceId: string
  onClose?: () => void
  onEdit?: (source: Source) => void
  onAddFeed?: (source: Source) => void
}

export function SourceDetailPanel({
  sourceId,
  onClose,
  onEdit,
  onAddFeed,
}: SourceDetailPanelProps) {
  const [activeTab, setActiveTab] = useState('overview')

  const { data: source, isLoading, error } = useSource(sourceId)
  const { data: feeds = [] } = useSourceFeeds(sourceId)
  const { data: assessmentHistory = [] } = useSourceAssessmentHistory(sourceId)
  const triggerAssessment = useTriggerSourceAssessment()

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-64">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
        </CardContent>
      </Card>
    )
  }

  if (error || !source) {
    return (
      <Card className="h-full">
        <CardContent className="flex flex-col items-center justify-center h-64 gap-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <p className="text-destructive">Failed to load source</p>
        </CardContent>
      </Card>
    )
  }

  const handleTriggerAssessment = () => {
    triggerAssessment.mutate(sourceId)
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0 pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {source.logo_url ? (
              <img
                src={source.logo_url}
                alt={source.canonical_name}
                className="w-12 h-12 rounded-lg object-contain"
              />
            ) : (
              <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center">
                <Globe className="w-6 h-6 text-muted-foreground" />
              </div>
            )}
            <div>
              <CardTitle className="text-xl">{source.canonical_name}</CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-sm text-muted-foreground">{source.domain}</span>
                {source.homepage_url && (
                  <a
                    href={source.homepage_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <SourceCredibilityBadge tier={source.credibility_tier} score={source.reputation_score} />
            {onClose && (
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 mt-4">
          <SourceStatusBadge status={source.status} />
          <ScrapeStatusBadge status={source.scrape_status} />
          {source.country && (
            <Badge variant="outline" className="font-mono text-xs">
              {source.country}
            </Badge>
          )}
          {source.category && (
            <Badge variant="secondary">{source.category}</Badge>
          )}
        </div>

        <div className="flex items-center gap-2 mt-4">
          {onEdit && (
            <Button variant="outline" size="sm" onClick={() => onEdit(source)}>
              <Edit className="h-4 w-4 mr-1" />
              Edit
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleTriggerAssessment}
            disabled={triggerAssessment.isPending}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${triggerAssessment.isPending ? 'animate-spin' : ''}`} />
            Reassess
          </Button>
          {onAddFeed && (
            <Button variant="outline" size="sm" onClick={() => onAddFeed(source)}>
              <Rss className="h-4 w-4 mr-1" />
              Add Feed
            </Button>
          )}
        </div>
      </CardHeader>

      <Separator />

      <CardContent className="flex-1 overflow-auto pt-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="assessment">Assessment</TabsTrigger>
            <TabsTrigger value="scraping">Scraping</TabsTrigger>
            <TabsTrigger value="feeds">Feeds ({feeds.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4 space-y-4">
            <OverviewTab source={source} />
          </TabsContent>

          <TabsContent value="assessment" className="mt-4 space-y-4">
            <AssessmentTab source={source} history={assessmentHistory} />
          </TabsContent>

          <TabsContent value="scraping" className="mt-4 space-y-4">
            <ScrapingTab source={source} />
          </TabsContent>

          <TabsContent value="feeds" className="mt-4 space-y-4">
            <FeedsTab feeds={feeds} onAddFeed={onAddFeed ? () => onAddFeed(source) : undefined} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

function OverviewTab({ source }: { source: Source }) {
  return (
    <>
      {source.description && (
        <div>
          <h4 className="text-sm font-medium mb-2">Description</h4>
          <p className="text-sm text-muted-foreground">{source.description}</p>
        </div>
      )}

      {source.organization_name && (
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">{source.organization_name}</span>
          {source.organization_type && (
            <Badge variant="outline" className="text-xs">
              {source.organization_type.replace('_', ' ')}
            </Badge>
          )}
        </div>
      )}

      {source.founded_year && (
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">Founded {source.founded_year}</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 pt-4">
        <StatCard
          icon={<Rss className="h-4 w-4" />}
          label="Feeds"
          value={source.active_feeds_count ?? source.feeds_count ?? 0}
        />
        <StatCard
          icon={<BarChart3 className="h-4 w-4" />}
          label="Success Rate"
          value={`${(source.scrape_success_rate * 100).toFixed(0)}%`}
        />
        <StatCard
          icon={<Clock className="h-4 w-4" />}
          label="Avg Response"
          value={source.scrape_avg_response_ms ? `${source.scrape_avg_response_ms}ms` : 'N/A'}
        />
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          label="Total Attempts"
          value={source.scrape_total_attempts?.toLocaleString() ?? '0'}
        />
      </div>

      {source.assessment_summary && (
        <div className="pt-4">
          <h4 className="text-sm font-medium mb-2">Assessment Summary</h4>
          <p className="text-sm text-muted-foreground">{source.assessment_summary}</p>
        </div>
      )}

      {source.notes && (
        <div className="pt-4">
          <h4 className="text-sm font-medium mb-2">Notes</h4>
          <p className="text-sm text-muted-foreground">{source.notes}</p>
        </div>
      )}
    </>
  )
}

function AssessmentTab({ source, history }: { source: Source; history: unknown[] }) {
  return (
    <>
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium">Assessment Status</h4>
          <p className="text-sm text-muted-foreground capitalize">
            {source.assessment_status ?? 'Not assessed'}
          </p>
        </div>
        {source.assessment_date && (
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(source.assessment_date), { addSuffix: true })}
          </span>
        )}
      </div>

      {source.political_bias && (
        <div>
          <h4 className="text-sm font-medium mb-2">Political Bias</h4>
          <Badge variant="outline" className="capitalize">
            {source.political_bias.replace('_', ' ')}
          </Badge>
        </div>
      )}

      {source.editorial_standards && Object.keys(source.editorial_standards).length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Editorial Standards</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(source.editorial_standards).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-medium capitalize">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {source.trust_ratings && Object.keys(source.trust_ratings).length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Trust Ratings</h4>
          <div className="space-y-2">
            {Object.entries(source.trust_ratings).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-medium">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Assessment History</h4>
          <div className="space-y-2 max-h-48 overflow-auto">
            {history.slice(0, 5).map((entry: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between text-sm p-2 bg-muted/50 rounded">
                <span>{entry.assessment_status}</span>
                <span className="text-muted-foreground">
                  {entry.assessment_date && format(new Date(entry.assessment_date), 'PP')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

function ScrapingTab({ source }: { source: Source }) {
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="text-sm font-medium mb-1">Scrape Method</h4>
          <Badge variant="outline">{source.scrape_method}</Badge>
        </div>
        <div>
          <h4 className="text-sm font-medium mb-1">Paywall</h4>
          <Badge variant={source.paywall_type === 'none' ? 'secondary' : 'destructive'}>
            {source.paywall_type}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center gap-2">
          {source.requires_stealth ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <X className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="text-sm">Stealth Mode</span>
        </div>
        <div className="flex items-center gap-2">
          {source.requires_proxy ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <X className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="text-sm">Proxy Required</span>
        </div>
        <div className="text-sm">
          <span className="text-muted-foreground">Rate Limit:</span>
          <span className="ml-1 font-medium">{source.rate_limit_per_minute}/min</span>
        </div>
      </div>

      <Separator />

      <div>
        <h4 className="text-sm font-medium mb-3">Scraping Metrics</h4>
        <div className="grid grid-cols-2 gap-4">
          <MetricRow label="Success Rate" value={`${(source.scrape_success_rate * 100).toFixed(1)}%`} />
          <MetricRow label="Avg Response" value={`${source.scrape_avg_response_ms}ms`} />
          <MetricRow label="Avg Word Count" value={source.scrape_avg_word_count.toLocaleString()} />
          <MetricRow label="Avg Quality" value={source.scrape_avg_quality.toFixed(2)} />
          <MetricRow label="Total Attempts" value={source.scrape_total_attempts.toLocaleString()} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-muted-foreground">Last Success:</span>
          <p className="font-medium">
            {source.scrape_last_success
              ? formatDistanceToNow(new Date(source.scrape_last_success), { addSuffix: true })
              : 'Never'}
          </p>
        </div>
        <div>
          <span className="text-muted-foreground">Last Failure:</span>
          <p className="font-medium">
            {source.scrape_last_failure
              ? formatDistanceToNow(new Date(source.scrape_last_failure), { addSuffix: true })
              : 'Never'}
          </p>
        </div>
      </div>

      {source.fallback_methods && source.fallback_methods.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Fallback Methods</h4>
          <div className="flex flex-wrap gap-2">
            {source.fallback_methods.map((method: string) => (
              <Badge key={method} variant="outline">
                {method}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

function FeedsTab({ feeds, onAddFeed }: { feeds: SourceFeed[]; onAddFeed?: () => void }) {
  if (feeds.length === 0) {
    return (
      <div className="text-center py-8">
        <Rss className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-muted-foreground mb-4">No feeds associated with this source</p>
        {onAddFeed && (
          <Button onClick={onAddFeed}>
            <Rss className="h-4 w-4 mr-2" />
            Add Feed
          </Button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {feeds.map((feed) => (
        <div
          key={feed.id}
          className="flex items-center justify-between p-3 rounded-lg border"
        >
          <div>
            <p className="font-medium text-sm">{feed.name}</p>
            <p className="text-xs text-muted-foreground truncate max-w-xs">{feed.url}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={feed.is_active ? 'default' : 'secondary'}>
              {feed.is_active ? 'Active' : 'Inactive'}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {feed.provider_type}
            </Badge>
          </div>
        </div>
      ))}
      {onAddFeed && (
        <Button variant="outline" className="w-full" onClick={onAddFeed}>
          <Rss className="h-4 w-4 mr-2" />
          Add Another Feed
        </Button>
      )}
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <div className="text-muted-foreground">{icon}</div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="font-semibold">{value}</p>
      </div>
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

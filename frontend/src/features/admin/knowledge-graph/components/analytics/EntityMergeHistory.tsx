import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { GitMerge, Calendar, ArrowRight, Info, XCircle } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useEntityMergeHistory } from '../../hooks/useEntityMergeHistory'

const mergeMethodColors = {
  exact: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  fuzzy: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  semantic: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  wikidata: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
}

const mergeMethodLabels = {
  exact: 'Exact Match',
  fuzzy: 'Fuzzy Match',
  semantic: 'Semantic Similarity',
  wikidata: 'Wikidata Link',
}

export function EntityMergeHistory() {
  const { data: events, isLoading, error } = useEntityMergeHistory(20, {
    refetchInterval: 60 * 1000 // Auto-refresh every minute
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitMerge className="h-5 w-5" />
            Entity Merge History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm">Loading merge history...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitMerge className="h-5 w-5" />
            Entity Merge History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-sm text-red-900 dark:text-red-100">
              Failed to load merge history. Please try again later.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  const displayEvents = events || []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitMerge className="h-5 w-5" />
          Entity Merge History
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  Shows recent entity deduplication events. When duplicate entities
                  are detected, they are merged into a canonical form.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {displayEvents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <GitMerge className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No merge events recorded yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {displayEvents.map((event) => (
              <div
                key={event.id}
                className="border rounded-lg p-4 hover:bg-muted/30 transition-colors"
              >
                {/* Timestamp */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                  <Calendar className="h-3 w-3" />
                  {new Date(event.timestamp).toLocaleString()}
                </div>

                {/* Merge Flow */}
                <div className="flex items-center gap-3">
                  {/* Source Entity */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{event.source_entity}</p>
                    <Badge variant="outline" className="text-xs">
                      {event.source_type}
                    </Badge>
                  </div>

                  {/* Arrow */}
                  <ArrowRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />

                  {/* Target Entity */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{event.target_entity}</p>
                    <Badge variant="outline" className="text-xs">
                      {event.target_type}
                    </Badge>
                  </div>
                </div>

                {/* Method and Confidence */}
                <div className="flex items-center justify-between mt-3 pt-3 border-t">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            mergeMethodColors[event.merge_method]
                          }`}
                        >
                          {mergeMethodLabels[event.merge_method]}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-sm">Merge method used for deduplication</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>

                  <div className="text-xs text-muted-foreground">
                    Confidence: {(event.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary */}
        {displayEvents.length > 0 && (
          <div className="mt-4 pt-4 border-t text-center text-xs text-muted-foreground">
            Showing {displayEvents.length} most recent merge events
          </div>
        )}
      </CardContent>
    </Card>
  )
}

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/Button'
import { Label } from '@/components/ui/Label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { BookOpen, Search, ExternalLink, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import type { EnrichmentCandidate, ToolExecutionResult } from '@/api/knowledgeGraphEnrichment'

interface EnrichmentToolPanelProps {
  candidate: EnrichmentCandidate | null
  onExecuteTool: (tool: string, language: string) => Promise<void>
  toolResult: ToolExecutionResult | null
  isExecuting: boolean
  onApplySuggestion: (suggestion: {
    relationship_type: string
    confidence: number
    evidence: string
    source: string
  }) => void
  isApplying: boolean
}

export function EnrichmentToolPanel({
  candidate,
  onExecuteTool,
  toolResult,
  isExecuting,
  onApplySuggestion,
  isApplying
}: EnrichmentToolPanelProps) {
  const [selectedTool, setSelectedTool] = useState<string>('wikipedia')
  const [selectedLanguage, setSelectedLanguage] = useState<string>('de')

  if (!candidate) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Enrichment Tools
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Select a candidate to execute enrichment tools
          </div>
        </CardContent>
      </Card>
    )
  }

  const handleExecute = async () => {
    await onExecuteTool(selectedTool, selectedLanguage)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Enrichment Tools
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Selected Candidate Info */}
        <div className="p-3 bg-muted/30 rounded-lg">
          <div className="text-xs text-muted-foreground mb-1">Selected Entity Pair</div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">{candidate.entity1_type}</Badge>
            <span className="font-medium">{candidate.entity1}</span>
            <span className="text-muted-foreground">→</span>
            <span className="font-medium">{candidate.entity2}</span>
            <Badge variant="outline" className="text-xs">{candidate.entity2_type}</Badge>
          </div>
        </div>

        {/* Tool Selection */}
        <div className="space-y-3 pt-2 border-t">
          <div className="space-y-2">
            <Label htmlFor="tool">Select Tool</Label>
            <Select value={selectedTool} onValueChange={setSelectedTool}>
              <SelectTrigger id="tool">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="wikipedia">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-4 w-4" />
                    Wikipedia (MediaWiki API)
                  </div>
                </SelectItem>
                <SelectItem value="research_perplexity" disabled>
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4" />
                    Research (Perplexity) - Coming Soon
                  </div>
                </SelectItem>
                <SelectItem value="google_deep_research" disabled>
                  <div className="flex items-center gap-2">
                    <ExternalLink className="h-4 w-4" />
                    Google Deep Research - Coming Soon
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {selectedTool === 'wikipedia' && (
            <div className="space-y-2">
              <Label htmlFor="language">Language</Label>
              <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                <SelectTrigger id="language">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="de">German (de)</SelectItem>
                  <SelectItem value="en">English (en)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          <Button
            onClick={handleExecute}
            disabled={isExecuting}
            className="w-full"
          >
            {isExecuting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Executing...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Execute Tool
              </>
            )}
          </Button>
        </div>

        {/* Tool Results */}
        {toolResult && (
          <div className="space-y-3 pt-4 border-t">
            <div className="flex items-center gap-2">
              {toolResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" />
              )}
              <span className="text-sm font-medium">
                {toolResult.success ? 'Tool Executed Successfully' : 'Tool Execution Failed'}
              </span>
            </div>

            {/* Error Message */}
            {!toolResult.success && toolResult.error && (
              <div className="p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded text-sm text-red-900 dark:text-red-200">
                {toolResult.error}
              </div>
            )}

            {/* Article Data */}
            {toolResult.success && toolResult.data && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Article Information</div>
                <div className="p-3 bg-muted/30 rounded space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Title:</span>{' '}
                    <span className="font-medium">{toolResult.data.article_title}</span>
                  </div>
                  {toolResult.data.article_url && (
                    <div>
                      <a
                        href={toolResult.data.article_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline flex items-center gap-1"
                      >
                        View Article
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  )}
                  {toolResult.data.extract && (
                    <div>
                      <span className="text-muted-foreground">Extract:</span>
                      <p className="text-xs mt-1">{toolResult.data.extract}</p>
                    </div>
                  )}
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    {toolResult.data.infobox_fields && (
                      <span>Infobox fields: {toolResult.data.infobox_fields}</span>
                    )}
                    {toolResult.data.categories && (
                      <span>Categories: {toolResult.data.categories.length}</span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Suggestions */}
            {toolResult.success && toolResult.suggestions && toolResult.suggestions.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Relationship Suggestions</div>
                <div className="space-y-2">
                  {toolResult.suggestions.map((suggestion, idx) => (
                    <div
                      key={idx}
                      className="p-3 border rounded-lg space-y-2 hover:border-primary/50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="default" className="font-mono">
                            {suggestion.relationship_type}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {(suggestion.confidence * 100).toFixed(0)}% confidence
                          </Badge>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onApplySuggestion(suggestion)}
                          disabled={isApplying}
                        >
                          {isApplying ? 'Applying...' : 'Apply'}
                        </Button>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        <span className="font-medium">Evidence:</span> {suggestion.evidence}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        <span className="font-medium">Source:</span> {suggestion.source}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Suggestions */}
            {toolResult.success && (!toolResult.suggestions || toolResult.suggestions.length === 0) && (
              <div className="text-center py-4 text-sm text-muted-foreground">
                No relationship suggestions found. Try a different tool or language.
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Search, ArrowRight, Hash, ChevronDown, ChevronRight } from 'lucide-react'
import type { EnrichmentCandidate } from '@/api/knowledgeGraphEnrichment'

interface EnrichmentCandidateListProps {
  candidates: EnrichmentCandidate[] | null
  isLoading: boolean
  onSelectCandidate: (candidate: EnrichmentCandidate) => void
  selectedCandidate: EnrichmentCandidate | null
  onAnalyze: (limit: number, minOccurrence: number) => void
}

export function EnrichmentCandidateList({
  candidates,
  isLoading,
  onSelectCandidate,
  selectedCandidate,
  onAnalyze
}: EnrichmentCandidateListProps) {
  const [limit, setLimit] = useState(50)
  const [minOccurrence, setMinOccurrence] = useState(5)
  const [expandedCandidates, setExpandedCandidates] = useState<Set<string>>(new Set())

  const toggleExpand = (candidateKey: string) => {
    const newSet = new Set(expandedCandidates)
    if (newSet.has(candidateKey)) {
      newSet.delete(candidateKey)
    } else {
      newSet.add(candidateKey)
    }
    setExpandedCandidates(newSet)
  }

  const getCandidateKey = (candidate: EnrichmentCandidate) =>
    `${candidate.entity1}-${candidate.entity2}`

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Enrichment Candidates
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Analysis Controls */}
        <div className="flex items-end gap-2 pb-4 border-b">
          <div className="flex-1">
            <Label htmlFor="limit" className="text-xs">Max Candidates</Label>
            <Input
              id="limit"
              type="number"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 50)}
              min={1}
              max={500}
              className="h-8"
            />
          </div>
          <div className="flex-1">
            <Label htmlFor="minOccurrence" className="text-xs">Min Occurrences</Label>
            <Input
              id="minOccurrence"
              type="number"
              value={minOccurrence}
              onChange={(e) => setMinOccurrence(parseInt(e.target.value) || 5)}
              min={1}
              max={100}
              className="h-8"
            />
          </div>
          <Button
            onClick={() => onAnalyze(limit, minOccurrence)}
            disabled={isLoading}
            size="sm"
          >
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </Button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-8 text-muted-foreground">
            Analyzing relationships...
          </div>
        )}

        {/* Candidate List */}
        {!isLoading && candidates && candidates.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm text-muted-foreground mb-2">
              Found {candidates.length} candidates
            </div>
            <div className="space-y-1 max-h-[600px] overflow-y-auto">
              {candidates.map((candidate) => {
                const candidateKey = getCandidateKey(candidate)
                const isExpanded = expandedCandidates.has(candidateKey)
                const isSelected = selectedCandidate && getCandidateKey(selectedCandidate) === candidateKey

                return (
                  <div
                    key={candidateKey}
                    className={`border rounded-lg p-3 transition-colors ${
                      isSelected ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
                    }`}
                  >
                    {/* Candidate Header */}
                    <div
                      className="flex items-start justify-between cursor-pointer"
                      onClick={() => onSelectCandidate(candidate)}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleExpand(candidateKey)
                          }}
                          className="flex-shrink-0"
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                          )}
                        </button>
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <Badge variant="outline" className="text-xs">
                            {candidate.entity1_type}
                          </Badge>
                          <span className="font-medium truncate">{candidate.entity1}</span>
                          <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                          <span className="font-medium truncate">{candidate.entity2}</span>
                          <Badge variant="outline" className="text-xs">
                            {candidate.entity2_type}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                        <Badge variant="secondary" className="text-xs">
                          <Hash className="h-3 w-3 mr-1" />
                          {candidate.occurrence_count}
                        </Badge>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t space-y-2">
                        {/* Suggested Tools */}
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Suggested Tools:</div>
                          <div className="flex flex-wrap gap-1">
                            {candidate.suggested_tools.map((tool) => (
                              <Badge key={tool} variant="outline" className="text-xs">
                                {tool}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        {/* Context Samples */}
                        {candidate.context_samples.length > 0 && (
                          <div>
                            <div className="text-xs text-muted-foreground mb-1">Context Samples:</div>
                            <div className="space-y-1">
                              {candidate.context_samples.slice(0, 3).map((context, idx) => (
                                <div key={idx} className="text-xs p-2 bg-muted/30 rounded">
                                  {context.substring(0, 150)}
                                  {context.length > 150 && '...'}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && candidates && candidates.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No enrichment candidates found. Try adjusting the filters.
          </div>
        )}

        {/* No Data State */}
        {!isLoading && !candidates && (
          <div className="text-center py-8 text-muted-foreground">
            Click "Analyze" to find enrichment candidates
          </div>
        )}
      </CardContent>
    </Card>
  )
}

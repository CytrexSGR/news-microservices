/**
 * PatternDetectionPanel - Pattern Detection Form and Results
 *
 * Allows users to trigger pattern detection and view results
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import { Search, AlertTriangle, TrendingUp, Clock, ChevronRight } from 'lucide-react';
import { useDetectPatterns } from '../api';
import type { DetectedPattern, PatternDetectionRequest } from '../types/osint.types';

interface PatternDetectionPanelProps {
  initialEntityIds?: string[];
  onPatternSelect?: (pattern: DetectedPattern) => void;
}

export function PatternDetectionPanel({
  initialEntityIds = [],
  onPatternSelect,
}: PatternDetectionPanelProps) {
  const [entityIds, setEntityIds] = useState<string>(initialEntityIds.join(', '));
  const [timeframeDays, setTimeframeDays] = useState<number>(30);
  const [minConfidence, setMinConfidence] = useState<number>(0.5);

  const detectPatterns = useDetectPatterns();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const request: PatternDetectionRequest = {
      entity_ids: entityIds ? entityIds.split(',').map((id) => id.trim()).filter(Boolean) : undefined,
      timeframe_days: timeframeDays,
      min_confidence: minConfidence,
    };
    detectPatterns.mutate(request);
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.6) return 'text-yellow-500';
    if (confidence >= 0.4) return 'text-orange-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Detection Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Pattern Detection
          </CardTitle>
          <CardDescription>
            Analyze entities and relationships to detect intelligence patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="entityIds">Entity IDs (comma-separated)</Label>
                <Input
                  id="entityIds"
                  value={entityIds}
                  onChange={(e) => setEntityIds(e.target.value)}
                  placeholder="entity-1, entity-2, ..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timeframe">Timeframe (days)</Label>
                <Input
                  id="timeframe"
                  type="number"
                  min={1}
                  max={365}
                  value={timeframeDays}
                  onChange={(e) => setTimeframeDays(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="confidence">
                Minimum Confidence: {(minConfidence * 100).toFixed(0)}%
              </Label>
              <input
                id="confidence"
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={minConfidence}
                onChange={(e) => setMinConfidence(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <button
              type="submit"
              disabled={detectPatterns.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {detectPatterns.isPending ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Detect Patterns
                </>
              )}
            </button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {detectPatterns.isError && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-500">
              <AlertTriangle className="h-5 w-5" />
              <span>Error: {detectPatterns.error?.message || 'Detection failed'}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {detectPatterns.isPending && (
        <Card>
          <CardContent className="pt-6 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {detectPatterns.data && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Detected Patterns ({detectPatterns.data.patterns.length})</span>
              <span className="text-sm font-normal text-muted-foreground">
                Analysis time: {detectPatterns.data.analysis_time_ms}ms
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {detectPatterns.data.patterns.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No patterns detected with the current criteria
              </p>
            ) : (
              <div className="space-y-4">
                {detectPatterns.data.patterns.map((pattern, index) => (
                  <PatternCard
                    key={index}
                    pattern={pattern}
                    onClick={() => onPatternSelect?.(pattern)}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface PatternCardProps {
  pattern: DetectedPattern;
  onClick?: () => void;
}

function PatternCard({ pattern, onClick }: PatternCardProps) {
  const confidencePercent = (pattern.confidence * 100).toFixed(0);

  return (
    <div
      className={`rounded-lg border p-4 hover:bg-muted/50 transition-colors ${
        onClick ? 'cursor-pointer' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="outline">{pattern.type}</Badge>
            <span
              className={`text-sm font-medium ${
                pattern.confidence >= 0.7 ? 'text-green-500' : 'text-yellow-500'
              }`}
            >
              {confidencePercent}% confidence
            </span>
            {pattern.risk_score !== undefined && pattern.risk_score > 50 && (
              <Badge variant="destructive" className="text-xs">
                Risk: {pattern.risk_score.toFixed(0)}
              </Badge>
            )}
          </div>
          <p className="text-sm text-foreground">{pattern.description}</p>
        </div>
        {onClick && <ChevronRight className="h-5 w-5 text-muted-foreground" />}
      </div>

      <div className="mt-3 flex flex-wrap gap-1">
        {pattern.entities.slice(0, 5).map((entity, i) => (
          <Badge key={i} variant="secondary" className="text-xs">
            {entity}
          </Badge>
        ))}
        {pattern.entities.length > 5 && (
          <Badge variant="secondary" className="text-xs">
            +{pattern.entities.length - 5} more
          </Badge>
        )}
      </div>

      {pattern.evidence.length > 0 && (
        <div className="mt-3 text-xs text-muted-foreground">
          <TrendingUp className="inline h-3 w-3 mr-1" />
          {pattern.evidence.length} evidence items
          <Clock className="inline h-3 w-3 ml-3 mr-1" />
          {new Date(pattern.detected_at).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}

export default PatternDetectionPanel;

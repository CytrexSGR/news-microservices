/**
 * TextAnalyzerPanel - Real-time text narrative analysis panel
 *
 * Provides a textarea for entering text and displays real-time narrative analysis
 * including detected frames, bias scoring, and propaganda signals.
 */
import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/Textarea';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import {
  AlertCircle,
  CheckCircle,
  Loader2,
  FileText,
  TrendingUp,
  AlertTriangle,
  Shield,
} from 'lucide-react';
import { useAnalyzeTextNarrative, REALTIME_ANALYSIS_COST_USD } from '../api/useAnalyzeTextNarrative';
import type { RealTimeNarrativeAnalysis, NarrativeType } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor, getBiasColor, formatCost } from '../types/narrative.types';

interface TextAnalyzerPanelProps {
  initialText?: string;
  onAnalysisComplete?: (result: RealTimeNarrativeAnalysis) => void;
  showCostWarning?: boolean;
  className?: string;
}

export function TextAnalyzerPanel({
  initialText = '',
  onAnalysisComplete,
  showCostWarning = true,
  className = '',
}: TextAnalyzerPanelProps) {
  const [text, setText] = useState(initialText);
  const [includeBias, setIncludeBias] = useState(true);
  const [includePropaganda, setIncludePropaganda] = useState(true);

  const { mutate, data, isPending, error, reset } = useAnalyzeTextNarrative();

  const handleAnalyze = useCallback(() => {
    if (!text.trim() || text.length < 50) return;

    mutate(
      {
        text: text.trim(),
        include_bias: includeBias,
        include_propaganda: includePropaganda,
      },
      {
        onSuccess: (result) => {
          onAnalysisComplete?.(result);
        },
      }
    );
  }, [text, includeBias, includePropaganda, mutate, onAnalysisComplete]);

  const handleClear = useCallback(() => {
    setText('');
    reset();
  }, [reset]);

  const textLength = text.length;
  const isValidLength = textLength >= 50 && textLength <= 50000;
  const charCountColor =
    textLength < 50 ? 'text-yellow-500' : textLength > 50000 ? 'text-red-500' : 'text-muted-foreground';

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Text Narrative Analyzer
        </CardTitle>
        <CardDescription>
          Analyze text for narrative frames, bias, and propaganda signals
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Text Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="analysis-text">Text to Analyze</Label>
            <span className={`text-xs ${charCountColor}`}>
              {textLength.toLocaleString()} / 50,000 characters
            </span>
          </div>
          <Textarea
            id="analysis-text"
            placeholder="Enter or paste text to analyze for narrative frames, bias, and propaganda signals..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            className="resize-y min-h-[150px]"
          />
          {textLength > 0 && textLength < 50 && (
            <p className="text-xs text-yellow-500">
              Minimum 50 characters required for meaningful analysis
            </p>
          )}
        </div>

        {/* Options */}
        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-2">
            <Switch
              id="include-bias"
              checked={includeBias}
              onCheckedChange={setIncludeBias}
            />
            <Label htmlFor="include-bias" className="text-sm">
              Include Bias Analysis
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              id="include-propaganda"
              checked={includePropaganda}
              onCheckedChange={setIncludePropaganda}
            />
            <Label htmlFor="include-propaganda" className="text-sm">
              Include Propaganda Detection
            </Label>
          </div>
        </div>

        {/* Cost Warning */}
        {showCostWarning && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 p-2 rounded">
            <AlertCircle className="h-4 w-4" />
            Estimated cost: {formatCost(REALTIME_ANALYSIS_COST_USD)} per analysis
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleAnalyze}
            disabled={isPending || !isValidLength}
            className="flex-1"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                Analyze Text
              </>
            )}
          </Button>
          <Button variant="outline" onClick={handleClear} disabled={isPending}>
            Clear
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span>{error.message}</span>
          </div>
        )}

        {/* Results Display */}
        {data && <AnalysisResults result={data} />}
      </CardContent>
    </Card>
  );
}

/**
 * Analysis Results Component
 */
interface AnalysisResultsProps {
  result: RealTimeNarrativeAnalysis;
}

function AnalysisResults({ result }: AnalysisResultsProps) {
  return (
    <div className="space-y-4 pt-4 border-t">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-green-500" />
          Analysis Results
        </h4>
        <span className="text-xs text-muted-foreground">
          Processed in {result.processing_time_ms}ms
        </span>
      </div>

      {/* Detected Frames */}
      {result.frames.length > 0 && (
        <div className="space-y-2">
          <Label className="text-sm font-medium">Detected Frames</Label>
          <div className="space-y-2">
            {result.frames.map((frame, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg ${getNarrativeBgColor(frame.type)}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <Badge variant="outline" className={getNarrativeColor(frame.type)}>
                    {frame.type}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {(frame.confidence * 100).toFixed(1)}% confidence
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{frame.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bias Analysis */}
      <div className="space-y-2">
        <Label className="text-sm font-medium flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          Bias Analysis
        </Label>
        <div className="bg-muted/50 p-3 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm">Direction</span>
            <Badge
              variant="outline"
              className={getBiasColor(result.bias_direction as any)}
            >
              {result.bias_direction}
            </Badge>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Bias Score</span>
              <span className="font-medium">
                {result.bias_score > 0 ? '+' : ''}
                {result.bias_score.toFixed(2)}
              </span>
            </div>
            <Progress
              value={((result.bias_score + 1) / 2) * 100}
              className="h-2"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Left (-1)</span>
              <span>Center (0)</span>
              <span>Right (+1)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sentiment */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Sentiment</Label>
        <div className="bg-muted/50 p-3 rounded-lg">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm">
              {result.sentiment > 0.2
                ? 'Positive'
                : result.sentiment < -0.2
                ? 'Negative'
                : 'Neutral'}
            </span>
            <span className="font-medium">
              {result.sentiment > 0 ? '+' : ''}
              {result.sentiment.toFixed(2)}
            </span>
          </div>
          <Progress
            value={((result.sentiment + 1) / 2) * 100}
            className="h-2"
          />
        </div>
      </div>

      {/* Propaganda Signals */}
      {result.propaganda_signals.length > 0 && (
        <div className="space-y-2">
          <Label className="text-sm font-medium flex items-center gap-2">
            <Shield className="h-4 w-4 text-orange-500" />
            Propaganda Signals Detected
          </Label>
          <div className="bg-orange-100 dark:bg-orange-900/30 p-3 rounded-lg">
            <ul className="space-y-1">
              {result.propaganda_signals.map((signal, index) => (
                <li key={index} className="flex items-center gap-2 text-sm">
                  <AlertTriangle className="h-3 w-3 text-orange-500 flex-shrink-0" />
                  {signal}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {result.propaganda_signals.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-green-600 bg-green-100 dark:bg-green-900/30 p-3 rounded-lg">
          <CheckCircle className="h-4 w-4" />
          No propaganda signals detected
        </div>
      )}
    </div>
  );
}

/**
 * Compact version of the analyzer for embedding
 */
export function CompactTextAnalyzer({
  onAnalysisComplete,
  className = '',
}: Pick<TextAnalyzerPanelProps, 'onAnalysisComplete' | 'className'>) {
  return (
    <TextAnalyzerPanel
      showCostWarning={false}
      onAnalysisComplete={onAnalysisComplete}
      className={className}
    />
  );
}

/**
 * Skeleton for loading state
 */
export function TextAnalyzerPanelSkeleton({ className = '' }: { className?: string }) {
  return (
    <Card className={className}>
      <CardHeader>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64" />
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <div className="flex gap-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-6 w-40" />
        </div>
        <Skeleton className="h-10 w-full" />
      </CardContent>
    </Card>
  );
}

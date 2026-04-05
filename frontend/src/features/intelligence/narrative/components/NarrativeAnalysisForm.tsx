/**
 * NarrativeAnalysisForm - Text input form for narrative analysis
 *
 * Provides a form to input text and configure analysis options.
 * Shows cost warning and handles submission.
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FileText, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import { CostWarningBadge } from './CostWarningBadge';
import { useAnalyzeNarrative, NARRATIVE_ANALYSIS_COST_USD } from '../api/useAnalyzeNarrative';
import type { NarrativeAnalysisRequest, NarrativeAnalysisResult } from '../types/narrative.types';

const MIN_TEXT_LENGTH = 100;
const MAX_TEXT_LENGTH = 50000;

interface NarrativeAnalysisFormProps {
  onAnalysisComplete?: (result: NarrativeAnalysisResult) => void;
  initialText?: string;
  className?: string;
}

export function NarrativeAnalysisForm({
  onAnalysisComplete,
  initialText = '',
  className = '',
}: NarrativeAnalysisFormProps) {
  const [text, setText] = useState(initialText);
  const [options, setOptions] = useState({
    include_bias: true,
    include_propaganda: false,
    language: 'en',
  });

  const { mutate, data, isPending, error, reset } = useAnalyzeNarrative();

  const handleSubmit = () => {
    if (!isValid) return;

    const request: NarrativeAnalysisRequest = {
      text,
      include_bias: options.include_bias,
      include_propaganda: options.include_propaganda,
      language: options.language,
    };

    mutate(request, {
      onSuccess: (result) => {
        onAnalysisComplete?.(result);
      },
    });
  };

  const handleClear = () => {
    setText('');
    reset();
  };

  const charCount = text.length;
  const isValid = charCount >= MIN_TEXT_LENGTH && charCount <= MAX_TEXT_LENGTH;
  const isTooShort = charCount > 0 && charCount < MIN_TEXT_LENGTH;
  const isTooLong = charCount > MAX_TEXT_LENGTH;

  // Estimate cost based on text length (simplified model)
  const estimatedCost = NARRATIVE_ANALYSIS_COST_USD * (1 + Math.floor(charCount / 10000) * 0.5);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            <CardTitle>Narrative Analysis</CardTitle>
          </div>
          <CostWarningBadge cost={estimatedCost} isEstimate />
        </div>
        <CardDescription>
          Analyze text for narrative frames, bias indicators, and propaganda techniques.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Text Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="analysis-text">Text to Analyze</Label>
            <span
              className={`text-xs ${
                isTooShort
                  ? 'text-destructive'
                  : isTooLong
                  ? 'text-destructive'
                  : 'text-muted-foreground'
              }`}
            >
              {charCount.toLocaleString()} / {MIN_TEXT_LENGTH.toLocaleString()} min
              {charCount > 10000 && ` (${(charCount / 1000).toFixed(1)}k)`}
            </span>
          </div>
          <Textarea
            id="analysis-text"
            placeholder="Paste your news article, press release, or any text content here for narrative analysis..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-[200px] resize-y font-mono text-sm"
            disabled={isPending}
          />
          {isTooShort && (
            <p className="text-sm text-destructive">
              Please enter at least {MIN_TEXT_LENGTH} characters.
              ({MIN_TEXT_LENGTH - charCount} more needed)
            </p>
          )}
          {isTooLong && (
            <p className="text-sm text-destructive">
              Text exceeds maximum length of {MAX_TEXT_LENGTH.toLocaleString()} characters.
              Please shorten by {(charCount - MAX_TEXT_LENGTH).toLocaleString()} characters.
            </p>
          )}
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-lg bg-secondary/30">
          {/* Bias Analysis Toggle */}
          <div className="flex items-center justify-between space-x-2">
            <Label htmlFor="include-bias" className="cursor-pointer">
              Bias Analysis
            </Label>
            <Switch
              id="include-bias"
              checked={options.include_bias}
              onCheckedChange={(checked) =>
                setOptions((prev) => ({ ...prev, include_bias: checked }))
              }
              disabled={isPending}
            />
          </div>

          {/* Propaganda Detection Toggle */}
          <div className="flex items-center justify-between space-x-2">
            <div>
              <Label htmlFor="include-propaganda" className="cursor-pointer">
                Propaganda Detection
              </Label>
              <p className="text-xs text-muted-foreground">+$0.001</p>
            </div>
            <Switch
              id="include-propaganda"
              checked={options.include_propaganda}
              onCheckedChange={(checked) =>
                setOptions((prev) => ({ ...prev, include_propaganda: checked }))
              }
              disabled={isPending}
            />
          </div>

          {/* Language Selection */}
          <div className="space-y-1">
            <Label htmlFor="language">Language</Label>
            <Select
              value={options.language}
              onValueChange={(value) =>
                setOptions((prev) => ({ ...prev, language: value }))
              }
              disabled={isPending}
            >
              <SelectTrigger id="language">
                <SelectValue placeholder="Select language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="de">German</SelectItem>
                <SelectItem value="fr">French</SelectItem>
                <SelectItem value="es">Spanish</SelectItem>
                <SelectItem value="auto">Auto-detect</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isPending}
            className="gap-2"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Analyze
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleClear}
            disabled={isPending || (!text && !data)}
          >
            Clear
          </Button>

          {/* Cost reminder */}
          <div className="flex-1 text-right text-sm text-muted-foreground">
            Estimated cost: ~${estimatedCost.toFixed(4)}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error.message || 'Failed to analyze text. Please try again.'}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Compact inline form for quick analysis
 */
interface QuickAnalysisFormProps {
  onAnalysisComplete?: (result: NarrativeAnalysisResult) => void;
  placeholder?: string;
  className?: string;
}

export function QuickAnalysisForm({
  onAnalysisComplete,
  placeholder = 'Enter text to analyze...',
  className = '',
}: QuickAnalysisFormProps) {
  const [text, setText] = useState('');
  const { mutate, isPending } = useAnalyzeNarrative();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.length < MIN_TEXT_LENGTH) return;

    mutate(
      { text, include_bias: true },
      { onSuccess: onAnalysisComplete }
    );
  };

  return (
    <form onSubmit={handleSubmit} className={`flex gap-2 ${className}`}>
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        className="min-h-[80px] flex-1"
        disabled={isPending}
      />
      <Button
        type="submit"
        disabled={text.length < MIN_TEXT_LENGTH || isPending}
        className="self-end"
      >
        {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Analyze'}
      </Button>
    </form>
  );
}

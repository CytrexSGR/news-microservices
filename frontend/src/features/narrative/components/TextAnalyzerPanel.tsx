import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/Label';
import { Progress } from '@/components/ui/progress';
import {
  AlertCircle,
  FileText,
  Loader2,
  Zap,
  User,
  Building2,
  MapPin,
  ArrowLeft,
  ArrowRight,
  Minus
} from 'lucide-react';
import { useTextAnalysis } from '../api/useTextAnalysis';
import type { FrameType, BiasLabel } from '../types';

/**
 * Panel for analyzing text for narrative frames and bias
 *
 * Features:
 * - Text input for content analysis
 * - Optional source identifier
 * - Displays detected narrative frames with confidence
 * - Shows bias analysis with spectrum visualization
 * - Sentiment indicator
 * - Cache status indicator
 */
export function TextAnalyzerPanel() {
  const [text, setText] = useState('');
  const [source, setSource] = useState('');
  const { mutate, data, isPending, error, reset } = useTextAnalysis();

  const handleAnalyze = () => {
    if (!text.trim() || text.length < 50) return;
    mutate({
      text: text.trim(),
      source: source.trim() || undefined,
    });
  };

  const handleClear = () => {
    setText('');
    setSource('');
    reset();
  };

  const getFrameIcon = (type: FrameType) => {
    const icons: Record<FrameType, string> = {
      victim: '😢',
      hero: '🦸',
      threat: '⚠️',
      solution: '💡',
      conflict: '⚔️',
      economic: '💰',
    };
    return icons[type] || '📄';
  };

  const getFrameColor = (type: FrameType) => {
    const colors: Record<FrameType, string> = {
      victim: 'bg-blue-500/10 text-blue-700 border-blue-200',
      hero: 'bg-green-500/10 text-green-700 border-green-200',
      threat: 'bg-red-500/10 text-red-700 border-red-200',
      solution: 'bg-emerald-500/10 text-emerald-700 border-emerald-200',
      conflict: 'bg-orange-500/10 text-orange-700 border-orange-200',
      economic: 'bg-yellow-500/10 text-yellow-700 border-yellow-200',
    };
    return colors[type] || 'bg-gray-500/10';
  };

  const getBiasPosition = (score: number) => {
    // Score ranges from -1 (left) to +1 (right), normalize to 0-100
    return ((score + 1) / 2) * 100;
  };

  const getBiasColor = (label: BiasLabel) => {
    const colors: Record<BiasLabel, string> = {
      left: 'text-blue-600',
      'center-left': 'text-blue-400',
      center: 'text-gray-600',
      'center-right': 'text-red-400',
      right: 'text-red-600',
    };
    return colors[label] || 'text-gray-600';
  };

  const getSentimentIcon = (sentiment: number) => {
    if (sentiment > 0.2) return '😊';
    if (sentiment < -0.2) return '😔';
    return '😐';
  };

  const result = data?.data;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Text Analyzer
        </CardTitle>
        <CardDescription>
          Analyze text for narrative frames, bias, and sentiment
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Input Section */}
        <div className="space-y-3">
          <div>
            <Label htmlFor="text">Text to Analyze</Label>
            <Textarea
              id="text"
              placeholder="Paste article content here (minimum 50 characters)..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="mt-1 min-h-[150px]"
            />
            <p className="text-xs text-muted-foreground mt-1">
              {text.length} / 50 characters minimum
              {text.length > 0 && text.length < 50 && (
                <span className="text-yellow-600 ml-2">
                  ({50 - text.length} more needed)
                </span>
              )}
            </p>
          </div>

          <div>
            <Label htmlFor="source">Source (optional)</Label>
            <Input
              id="source"
              placeholder="e.g., reuters, bbc, fox-news"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="mt-1"
            />
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleAnalyze}
              disabled={isPending || text.length < 50}
              className="flex-1"
            >
              {isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Analyze Text
                </>
              )}
            </Button>
            <Button variant="outline" onClick={handleClear}>
              Clear
            </Button>
          </div>
        </div>

        {/* Error Display */}
        {(error || data?.error) && (
          <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-lg">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error?.message || data?.error}</span>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div className="space-y-4 pt-4 border-t">
            {/* Cache & Performance */}
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Analyzed {result.text_length} characters</span>
              <div className="flex items-center gap-2">
                {result.from_cache && (
                  <Badge variant="outline" className="text-xs">
                    <Zap className="h-3 w-3 mr-1" />
                    Cached
                  </Badge>
                )}
                <span>{new Date(result.analyzed_at).toLocaleTimeString('de-DE')}</span>
              </div>
            </div>

            {/* Bias Analysis */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Bias Analysis</h4>
              <div className="p-4 bg-muted rounded-lg space-y-3">
                {/* Bias Spectrum */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <ArrowLeft className="h-3 w-3" /> Left
                    </span>
                    <span>Center</span>
                    <span className="flex items-center gap-1">
                      Right <ArrowRight className="h-3 w-3" />
                    </span>
                  </div>
                  <div className="relative h-3 bg-gradient-to-r from-blue-500 via-gray-300 to-red-500 rounded-full">
                    <div
                      className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-gray-800 rounded-full shadow"
                      style={{ left: `calc(${getBiasPosition(result.bias.bias_score)}% - 8px)` }}
                    />
                  </div>
                </div>

                {/* Bias Details */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-xs text-muted-foreground">Label</p>
                    <Badge variant="outline" className={getBiasColor(result.bias.bias_label)}>
                      {result.bias.bias_label}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Sentiment</p>
                    <p className="text-lg">
                      {getSentimentIcon(result.bias.sentiment)}
                      <span className="text-sm ml-1">
                        {result.bias.sentiment > 0 ? '+' : ''}{result.bias.sentiment.toFixed(2)}
                      </span>
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Perspective</p>
                    <Badge variant="secondary">{result.bias.perspective}</Badge>
                  </div>
                </div>

                {/* Language Indicators */}
                <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Political Markers</p>
                    <div className="flex gap-2">
                      <Badge variant="outline" className="text-blue-600">
                        L: {result.bias.language_indicators.left_markers}
                      </Badge>
                      <Badge variant="outline" className="text-red-600">
                        R: {result.bias.language_indicators.right_markers}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Emotional Tone</p>
                    <div className="flex gap-2">
                      <Badge variant="outline" className="text-green-600">
                        +{result.bias.language_indicators.emotional_positive}
                      </Badge>
                      <Badge variant="outline" className="text-red-600">
                        -{result.bias.language_indicators.emotional_negative}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Detected Frames */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">
                Detected Frames ({result.frames.length})
              </h4>
              {result.frames.length > 0 ? (
                <div className="space-y-2">
                  {result.frames.map((frame, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-lg border ${getFrameColor(frame.frame_type)}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{getFrameIcon(frame.frame_type)}</span>
                          <span className="font-medium capitalize">{frame.frame_type}</span>
                        </div>
                        <Badge variant="outline">
                          {(frame.confidence * 100).toFixed(0)}% confidence
                        </Badge>
                      </div>

                      {frame.text_excerpt && (
                        <p className="text-sm italic text-muted-foreground mb-2 line-clamp-2">
                          "{frame.text_excerpt}"
                        </p>
                      )}

                      {/* Frame Entities */}
                      <div className="flex flex-wrap gap-1">
                        {frame.entities.persons.map((p, j) => (
                          <Badge key={`p-${j}`} variant="secondary" className="text-xs">
                            <User className="h-3 w-3 mr-1" />
                            {p}
                          </Badge>
                        ))}
                        {frame.entities.organizations.map((o, j) => (
                          <Badge key={`o-${j}`} variant="secondary" className="text-xs">
                            <Building2 className="h-3 w-3 mr-1" />
                            {o}
                          </Badge>
                        ))}
                        {frame.entities.locations.map((l, j) => (
                          <Badge key={`l-${j}`} variant="secondary" className="text-xs">
                            <MapPin className="h-3 w-3 mr-1" />
                            {l}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground p-3 bg-muted rounded-lg">
                  No significant narrative frames detected in this text.
                </p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TextAnalyzerPanel;

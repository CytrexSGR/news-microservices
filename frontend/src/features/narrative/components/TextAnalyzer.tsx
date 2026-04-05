import { useState } from 'react';
import { useTextAnalyzer } from '../hooks/useTextAnalyzer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { Label } from '@/components/ui/Label';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Loader2,
  AlertCircle,
  Users,
  Building2,
  MapPin,
  TrendingUp,
  TrendingDown,
  Minus,
  FileText,
} from 'lucide-react';
import type { TextAnalysisResult, DetectedFrame, BiasResult } from '@/api/narrative';

const MIN_TEXT_LENGTH = 100;

interface TextAnalyzerProps {
  className?: string;
}

/**
 * TextAnalyzer Component
 *
 * Allows users to input text and analyze it for:
 * - Named entities (persons, organizations, locations)
 * - Sentiment and bias analysis
 * - Narrative frame detection
 */
export function TextAnalyzer({ className }: TextAnalyzerProps) {
  const [text, setText] = useState('');
  const [options, setOptions] = useState({
    analyze_entities: true,
    analyze_sentiment: true,
    analyze_frames: true,
  });

  const { mutate, data, isPending, error, reset } = useTextAnalyzer();

  const handleAnalyze = () => {
    if (text.length < MIN_TEXT_LENGTH) return;
    mutate({ text, options });
  };

  const handleClear = () => {
    setText('');
    reset();
  };

  const isValid = text.length >= MIN_TEXT_LENGTH;
  const charCount = text.length;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Text Analyzer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Input Section */}
        <div className="space-y-2">
          <Label htmlFor="analysis-text">
            Text to Analyze
            <span className="ml-2 text-muted-foreground text-xs">
              ({charCount}/{MIN_TEXT_LENGTH} min characters)
            </span>
          </Label>
          <Textarea
            id="analysis-text"
            placeholder="Paste news article or text content here for narrative analysis..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-[150px] resize-y"
            disabled={isPending}
          />
          {text.length > 0 && text.length < MIN_TEXT_LENGTH && (
            <p className="text-sm text-destructive">
              Please enter at least {MIN_TEXT_LENGTH} characters ({MIN_TEXT_LENGTH - text.length} more needed)
            </p>
          )}
        </div>

        {/* Options */}
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Checkbox
              id="opt-entities"
              checked={options.analyze_entities}
              onCheckedChange={(checked) =>
                setOptions((prev) => ({ ...prev, analyze_entities: !!checked }))
              }
              disabled={isPending}
            />
            <Label htmlFor="opt-entities" className="cursor-pointer">
              Entities
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="opt-sentiment"
              checked={options.analyze_sentiment}
              onCheckedChange={(checked) =>
                setOptions((prev) => ({ ...prev, analyze_sentiment: !!checked }))
              }
              disabled={isPending}
            />
            <Label htmlFor="opt-sentiment" className="cursor-pointer">
              Sentiment
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="opt-frames"
              checked={options.analyze_frames}
              onCheckedChange={(checked) =>
                setOptions((prev) => ({ ...prev, analyze_frames: !!checked }))
              }
              disabled={isPending}
            />
            <Label htmlFor="opt-frames" className="cursor-pointer">
              Narrative Frames
            </Label>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button onClick={handleAnalyze} disabled={!isValid || isPending}>
            {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {isPending ? 'Analyzing...' : 'Analyze'}
          </Button>
          <Button variant="outline" onClick={handleClear} disabled={isPending}>
            Clear
          </Button>
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

        {/* Results */}
        {data && <AnalysisResults data={data} />}
      </CardContent>
    </Card>
  );
}

interface AnalysisResultsProps {
  data: TextAnalysisResult;
}

function AnalysisResults({ data }: AnalysisResultsProps) {
  return (
    <div className="mt-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Analysis Results</h3>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>{data.text_length} characters</span>
          {data.from_cache && (
            <Badge variant="secondary">Cached</Badge>
          )}
        </div>
      </div>

      <Tabs defaultValue="entities" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="entities">Entities</TabsTrigger>
          <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
          <TabsTrigger value="frames">Narrative Frames</TabsTrigger>
        </TabsList>

        <TabsContent value="entities" className="mt-4">
          <EntitiesTab frames={data.frames} />
        </TabsContent>

        <TabsContent value="sentiment" className="mt-4">
          <SentimentTab bias={data.bias} />
        </TabsContent>

        <TabsContent value="frames" className="mt-4">
          <FramesTab frames={data.frames} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface EntitiesTabProps {
  frames: DetectedFrame[];
}

function EntitiesTab({ frames }: EntitiesTabProps) {
  // Aggregate entities from all frames
  const allEntities = {
    persons: new Set<string>(),
    organizations: new Set<string>(),
    locations: new Set<string>(),
  };

  frames.forEach((frame) => {
    frame.entities.persons?.forEach((p) => allEntities.persons.add(p));
    frame.entities.organizations?.forEach((o) => allEntities.organizations.add(o));
    frame.entities.locations?.forEach((l) => allEntities.locations.add(l));
  });

  const hasEntities =
    allEntities.persons.size > 0 ||
    allEntities.organizations.size > 0 ||
    allEntities.locations.size > 0;

  if (!hasEntities) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No entities detected in the text.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {allEntities.persons.size > 0 && (
        <EntitySection
          icon={<Users className="h-4 w-4" />}
          title="Persons"
          items={Array.from(allEntities.persons)}
          color="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
        />
      )}
      {allEntities.organizations.size > 0 && (
        <EntitySection
          icon={<Building2 className="h-4 w-4" />}
          title="Organizations"
          items={Array.from(allEntities.organizations)}
          color="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
        />
      )}
      {allEntities.locations.size > 0 && (
        <EntitySection
          icon={<MapPin className="h-4 w-4" />}
          title="Locations"
          items={Array.from(allEntities.locations)}
          color="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
        />
      )}
    </div>
  );
}

interface EntitySectionProps {
  icon: React.ReactNode;
  title: string;
  items: string[];
  color: string;
}

function EntitySection({ icon, title, items, color }: EntitySectionProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium">
        {icon}
        {title}
        <span className="text-muted-foreground">({items.length})</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className={`px-2 py-1 rounded-md text-sm ${color}`}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

interface SentimentTabProps {
  bias: BiasResult;
}

function SentimentTab({ bias }: SentimentTabProps) {
  const getSentimentIcon = (sentiment: number) => {
    if (sentiment > 0.2) return <TrendingUp className="h-5 w-5 text-green-500" />;
    if (sentiment < -0.2) return <TrendingDown className="h-5 w-5 text-red-500" />;
    return <Minus className="h-5 w-5 text-gray-500" />;
  };

  const getSentimentLabel = (sentiment: number) => {
    if (sentiment > 0.5) return 'Very Positive';
    if (sentiment > 0.2) return 'Positive';
    if (sentiment > -0.2) return 'Neutral';
    if (sentiment > -0.5) return 'Negative';
    return 'Very Negative';
  };

  const getBiasColor = (label: string) => {
    switch (label.toLowerCase()) {
      case 'left':
        return 'bg-blue-500';
      case 'center-left':
        return 'bg-blue-300';
      case 'center':
        return 'bg-gray-400';
      case 'center-right':
        return 'bg-red-300';
      case 'right':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const biasPosition = ((bias.bias_score + 1) / 2) * 100; // Convert -1..1 to 0..100

  return (
    <div className="space-y-6">
      {/* Sentiment */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium">Sentiment</h4>
        <div className="flex items-center gap-3">
          {getSentimentIcon(bias.sentiment)}
          <span className="text-lg font-semibold">
            {getSentimentLabel(bias.sentiment)}
          </span>
          <span className="text-muted-foreground">
            ({bias.sentiment.toFixed(2)})
          </span>
        </div>
      </div>

      {/* Bias Score */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium">Political Bias</h4>
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Left</span>
            <span>Center</span>
            <span>Right</span>
          </div>
          <div className="relative h-4 bg-gradient-to-r from-blue-500 via-gray-300 to-red-500 rounded-full">
            <div
              className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-gray-700 rounded-full shadow-md"
              style={{ left: `calc(${biasPosition}% - 8px)` }}
            />
          </div>
          <div className="text-center">
            <Badge className={`${getBiasColor(bias.bias_label)} text-white`}>
              {bias.bias_label}
            </Badge>
            <span className="ml-2 text-sm text-muted-foreground">
              ({bias.bias_score.toFixed(2)})
            </span>
          </div>
        </div>
      </div>

      {/* Language Indicators */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium">Language Indicators</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-secondary">
            <div className="text-xs text-muted-foreground">Left Markers</div>
            <div className="text-lg font-semibold">
              {bias.language_indicators.left_markers}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-secondary">
            <div className="text-xs text-muted-foreground">Right Markers</div>
            <div className="text-lg font-semibold">
              {bias.language_indicators.right_markers}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-secondary">
            <div className="text-xs text-muted-foreground">Positive Emotional</div>
            <div className="text-lg font-semibold">
              {bias.language_indicators.emotional_positive}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-secondary">
            <div className="text-xs text-muted-foreground">Negative Emotional</div>
            <div className="text-lg font-semibold">
              {bias.language_indicators.emotional_negative}
            </div>
          </div>
        </div>
      </div>

      {/* Perspective */}
      {bias.perspective && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Perspective</h4>
          <Badge variant="outline" className="capitalize">
            {bias.perspective === 'pro' ? 'Pro' : bias.perspective === 'con' ? 'Con' : 'Neutral'}
          </Badge>
        </div>
      )}
    </div>
  );
}

interface FramesTabProps {
  frames: DetectedFrame[];
}

function FramesTab({ frames }: FramesTabProps) {
  if (frames.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No narrative frames detected in the text.
      </div>
    );
  }

  const getFrameColor = (frameType: string): string => {
    const colors: Record<string, string> = {
      victim: 'border-l-red-500',
      hero: 'border-l-green-500',
      threat: 'border-l-orange-500',
      solution: 'border-l-blue-500',
      conflict: 'border-l-purple-500',
      economic: 'border-l-yellow-500',
    };
    return colors[frameType.toLowerCase()] || 'border-l-gray-500';
  };

  const getFrameBadgeColor = (frameType: string): string => {
    const colors: Record<string, string> = {
      victim: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      hero: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      threat: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      solution: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      conflict: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      economic: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    };
    return colors[frameType.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-4">
      {frames.map((frame, index) => (
        <div
          key={index}
          className={`p-4 border-l-4 rounded-r-lg bg-secondary/50 ${getFrameColor(frame.frame_type)}`}
        >
          <div className="flex items-start justify-between mb-2">
            <span className={`px-2 py-1 rounded-md text-sm font-medium capitalize ${getFrameBadgeColor(frame.frame_type)}`}>
              {frame.frame_type}
            </span>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Confidence</div>
              <div className="font-semibold">
                {(frame.confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>
          {frame.text_excerpt && (
            <p className="text-sm text-muted-foreground mt-2 italic">
              "{frame.text_excerpt}"
            </p>
          )}
          {frame.match_count > 1 && (
            <div className="mt-2 text-xs text-muted-foreground">
              {frame.match_count} pattern matches
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default TextAnalyzer;

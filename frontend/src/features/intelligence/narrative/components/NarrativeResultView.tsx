/**
 * NarrativeResultView - Display full analysis result
 *
 * Comprehensive view of narrative analysis results including
 * frames, bias, and propaganda indicators.
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import {
  Clock,
  DollarSign,
  BarChart3,
  Shield,
  FileText,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { DetectedFramesList } from './DetectedFrameCard';
import { BiasIndicatorList, BiasTypeSummary } from './BiasIndicatorList';
import { PropagandaWarnings, PropagandaSummaryBadge } from './PropagandaWarnings';
import { BiasRadarChart, BiasBarChart, BiasGauge } from './BiasChart';
import { CostWarningBadge, InlineCost } from './CostWarningBadge';
import type { NarrativeAnalysisResult, NarrativeType } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor, formatCost } from '../types/narrative.types';

interface NarrativeResultViewProps {
  result: NarrativeAnalysisResult;
  showMetadata?: boolean;
  defaultTab?: 'frames' | 'bias' | 'propaganda';
  className?: string;
}

export function NarrativeResultView({
  result,
  showMetadata = true,
  defaultTab = 'frames',
  className = '',
}: NarrativeResultViewProps) {
  const hasFrames = result.detected_frames.length > 0;
  const hasBias = !!result.bias_analysis;
  const hasPropaganda = (result.propaganda_indicators?.length ?? 0) > 0;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary Header */}
      <Card className={getNarrativeBgColor(result.overall_narrative)}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                <CardTitle>Analysis Results</CardTitle>
              </div>
              <CardDescription>
                {result.text_length.toLocaleString()} characters analyzed
              </CardDescription>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Badge
                variant="outline"
                className={`text-lg capitalize ${getNarrativeColor(result.overall_narrative)}`}
              >
                {result.overall_narrative}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {(result.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatItem
              icon={<FileText className="h-4 w-4" />}
              label="Frames Detected"
              value={result.detected_frames.length.toString()}
            />
            {result.bias_analysis && (
              <StatItem
                icon={<TrendingUp className="h-4 w-4" />}
                label="Bias Score"
                value={`${result.bias_analysis.bias_score > 0 ? '+' : ''}${result.bias_analysis.bias_score.toFixed(2)}`}
                valueClass={
                  result.bias_analysis.bias_score > 0.3
                    ? 'text-red-500'
                    : result.bias_analysis.bias_score < -0.3
                    ? 'text-blue-500'
                    : ''
                }
              />
            )}
            <StatItem
              icon={<Shield className="h-4 w-4" />}
              label="Propaganda"
              value={
                hasPropaganda
                  ? `${result.propaganda_indicators!.length} found`
                  : 'None'
              }
              valueClass={hasPropaganda ? 'text-orange-500' : 'text-green-500'}
            />
            {showMetadata && (
              <StatItem
                icon={<DollarSign className="h-4 w-4" />}
                label="Cost"
                value={formatCost(result.cost_usd)}
              />
            )}
          </div>

          {/* Metadata */}
          {showMetadata && (
            <div className="flex items-center gap-4 mt-4 pt-4 border-t text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {result.latency_ms}ms
              </span>
              <InlineCost cost={result.cost_usd} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed Tabs */}
      <Tabs defaultValue={defaultTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="frames" className="gap-2">
            <FileText className="h-4 w-4" />
            Frames ({result.detected_frames.length})
          </TabsTrigger>
          <TabsTrigger value="bias" className="gap-2" disabled={!hasBias}>
            <BarChart3 className="h-4 w-4" />
            Bias Analysis
          </TabsTrigger>
          <TabsTrigger value="propaganda" className="gap-2">
            <Shield className="h-4 w-4" />
            Propaganda
            {hasPropaganda && (
              <Badge variant="destructive" className="ml-1 text-xs">
                {result.propaganda_indicators!.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Frames Tab */}
        <TabsContent value="frames" className="mt-4 space-y-4">
          {hasFrames ? (
            <DetectedFramesList frames={result.detected_frames} showEvidence />
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No narrative frames were detected in this text.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Bias Tab */}
        <TabsContent value="bias" className="mt-4 space-y-4">
          {hasBias ? (
            <>
              {/* Overall Bias Gauge */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Overall Bias</CardTitle>
                </CardHeader>
                <CardContent>
                  <BiasGauge
                    score={result.bias_analysis!.bias_score}
                    confidence={result.bias_analysis!.confidence}
                    size="lg"
                  />
                </CardContent>
              </Card>

              {/* Charts Grid */}
              <div className="grid md:grid-cols-2 gap-4">
                <BiasRadarChart biasResult={result.bias_analysis!} height={250} />
                <BiasBarChart
                  biasResult={result.bias_analysis!}
                  height={250}
                  orientation="horizontal"
                />
              </div>

              {/* Indicators List */}
              {result.bias_analysis!.indicators.length > 0 && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">Bias Indicators</CardTitle>
                      <BiasTypeSummary indicators={result.bias_analysis!.indicators} />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <BiasIndicatorList
                      indicators={result.bias_analysis!.indicators}
                      showExplanations
                    />
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Bias analysis was not included in this request.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Propaganda Tab */}
        <TabsContent value="propaganda" className="mt-4">
          <PropagandaWarnings
            indicators={result.propaganda_indicators ?? []}
            showExamples
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * Compact result view for lists/cards
 */
interface CompactResultViewProps {
  result: NarrativeAnalysisResult;
  onClick?: () => void;
  className?: string;
}

export function CompactResultView({
  result,
  onClick,
  className = '',
}: CompactResultViewProps) {
  return (
    <Card
      className={`cursor-pointer hover:bg-secondary/50 transition-colors ${className}`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <Badge
            variant="outline"
            className={`capitalize ${getNarrativeColor(result.overall_narrative)}`}
          >
            {result.overall_narrative}
          </Badge>
          <div className="flex items-center gap-2">
            {result.propaganda_indicators && result.propaganda_indicators.length > 0 && (
              <PropagandaSummaryBadge indicators={result.propaganda_indicators} />
            )}
            <InlineCost cost={result.cost_usd} />
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>{result.detected_frames.length} frames</span>
          {result.bias_analysis && (
            <span>
              Bias: {result.bias_analysis.bias_score > 0 ? '+' : ''}
              {result.bias_analysis.bias_score.toFixed(2)}
            </span>
          )}
          <span>{(result.confidence * 100).toFixed(0)}% confidence</span>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Helper component for stat items
 */
interface StatItemProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueClass?: string;
}

function StatItem({ icon, label, value, valueClass = '' }: StatItemProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1 text-muted-foreground text-xs">
        {icon}
        {label}
      </div>
      <div className={`text-lg font-semibold ${valueClass}`}>{value}</div>
    </div>
  );
}

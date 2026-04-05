/**
 * PropagandaWarnings - Display detected propaganda techniques
 *
 * Shows propaganda indicators with technique names, confidence scores,
 * and examples found in the text.
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/Button';
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Shield,
  ShieldAlert,
  Info,
} from 'lucide-react';
import { useState } from 'react';
import type { PropagandaIndicator } from '../types/narrative.types';

interface PropagandaWarningsProps {
  indicators: PropagandaIndicator[];
  showExamples?: boolean;
  threshold?: number;
  className?: string;
}

export function PropagandaWarnings({
  indicators,
  showExamples = true,
  threshold = 0.5,
  className = '',
}: PropagandaWarningsProps) {
  const significantIndicators = indicators.filter((i) => i.confidence >= threshold);
  const hasHighConfidence = significantIndicators.some((i) => i.confidence >= 0.8);

  if (indicators.length === 0) {
    return (
      <Alert className={`border-green-500/50 bg-green-50 dark:bg-green-950/20 ${className}`}>
        <Shield className="h-4 w-4 text-green-500" />
        <AlertTitle className="text-green-700 dark:text-green-400">
          No Propaganda Detected
        </AlertTitle>
        <AlertDescription className="text-green-600 dark:text-green-500">
          No significant propaganda techniques were detected in this text.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Summary alert */}
      <Alert
        variant={hasHighConfidence ? 'destructive' : 'default'}
        className={!hasHighConfidence ? 'border-yellow-500/50 bg-yellow-50 dark:bg-yellow-950/20' : ''}
      >
        <ShieldAlert className={`h-4 w-4 ${hasHighConfidence ? '' : 'text-yellow-500'}`} />
        <AlertTitle className={hasHighConfidence ? '' : 'text-yellow-700 dark:text-yellow-400'}>
          {hasHighConfidence ? 'High-Confidence Propaganda Detected' : 'Potential Propaganda Detected'}
        </AlertTitle>
        <AlertDescription className={hasHighConfidence ? '' : 'text-yellow-600 dark:text-yellow-500'}>
          {significantIndicators.length} propaganda technique
          {significantIndicators.length !== 1 ? 's' : ''} detected above {threshold * 100}%
          confidence threshold.
        </AlertDescription>
      </Alert>

      {/* Individual indicators */}
      <div className="space-y-3">
        {indicators.map((indicator, index) => (
          <PropagandaIndicatorCard
            key={index}
            indicator={indicator}
            showExamples={showExamples}
          />
        ))}
      </div>

      {/* Educational note */}
      <div className="flex items-start gap-2 p-3 rounded-lg bg-secondary/50 text-sm">
        <Info className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
        <div className="text-muted-foreground">
          <p className="font-medium">What is propaganda?</p>
          <p className="mt-1">
            Propaganda techniques are rhetorical devices used to influence audiences
            through emotional appeal rather than rational argument. Detection helps
            identify potentially manipulative content.
          </p>
        </div>
      </div>
    </div>
  );
}

interface PropagandaIndicatorCardProps {
  indicator: PropagandaIndicator;
  showExamples?: boolean;
  className?: string;
}

export function PropagandaIndicatorCard({
  indicator,
  showExamples = true,
  className = '',
}: PropagandaIndicatorCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const confidencePercent = Math.round(indicator.confidence * 100);

  const getSeverityColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'border-l-red-500 bg-red-50 dark:bg-red-950/20';
    if (confidence >= 0.6) return 'border-l-orange-500 bg-orange-50 dark:bg-orange-950/20';
    return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-950/20';
  };

  const getSeverityBadge = (confidence: number) => {
    if (confidence >= 0.8)
      return (
        <Badge variant="destructive" className="text-xs">
          High
        </Badge>
      );
    if (confidence >= 0.6)
      return (
        <Badge className="text-xs bg-orange-500">
          Medium
        </Badge>
      );
    return (
      <Badge className="text-xs bg-yellow-500 text-yellow-900">
        Low
      </Badge>
    );
  };

  return (
    <Card className={`border-l-4 ${getSeverityColor(indicator.confidence)} ${className}`}>
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              <span className="font-semibold">{indicator.technique}</span>
              {getSeverityBadge(indicator.confidence)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold">{confidencePercent}%</div>
            <div className="text-xs text-muted-foreground">confidence</div>
          </div>
        </div>

        {/* Confidence bar */}
        <Progress
          value={confidencePercent}
          className={`h-2 mb-3 ${
            indicator.confidence >= 0.8
              ? '[&>div]:bg-red-500'
              : indicator.confidence >= 0.6
              ? '[&>div]:bg-orange-500'
              : '[&>div]:bg-yellow-500'
          }`}
        />

        {/* Description */}
        <p className="text-sm text-muted-foreground mb-3">{indicator.description}</p>

        {/* Examples - Collapsible */}
        {showExamples && indicator.examples.length > 0 && (
          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="w-full justify-between">
                <span>Examples ({indicator.examples.length})</span>
                {isOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-2">
              {indicator.examples.map((example, index) => (
                <div
                  key={index}
                  className="p-2 rounded bg-background/50 text-sm italic border-l-2 border-destructive/30"
                >
                  "{example}"
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Compact propaganda summary badge
 */
interface PropagandaSummaryBadgeProps {
  indicators: PropagandaIndicator[];
  threshold?: number;
  className?: string;
}

export function PropagandaSummaryBadge({
  indicators,
  threshold = 0.5,
  className = '',
}: PropagandaSummaryBadgeProps) {
  const significantCount = indicators.filter((i) => i.confidence >= threshold).length;
  const maxConfidence = indicators.length > 0
    ? Math.max(...indicators.map((i) => i.confidence))
    : 0;

  if (significantCount === 0) {
    return (
      <Badge variant="secondary" className={`text-green-600 ${className}`}>
        <Shield className="h-3 w-3 mr-1" />
        Clear
      </Badge>
    );
  }

  const variant = maxConfidence >= 0.8 ? 'destructive' : 'default';
  const bgClass =
    maxConfidence >= 0.8
      ? ''
      : maxConfidence >= 0.6
      ? 'bg-orange-500 hover:bg-orange-600'
      : 'bg-yellow-500 hover:bg-yellow-600 text-yellow-900';

  return (
    <Badge variant={variant} className={`${bgClass} ${className}`}>
      <ShieldAlert className="h-3 w-3 mr-1" />
      {significantCount} detected
    </Badge>
  );
}

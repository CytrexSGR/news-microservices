/**
 * DetectedFrameCard - Display a single detected narrative frame
 *
 * Shows frame type, confidence score, and evidence text.
 */
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/Button';
import { ChevronDown, ChevronUp, Quote, Target } from 'lucide-react';
import { useState } from 'react';
import type { DetectedFrame, NarrativeType } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor } from '../types/narrative.types';

interface DetectedFrameCardProps {
  frame: DetectedFrame;
  showEvidence?: boolean;
  compact?: boolean;
  className?: string;
}

export function DetectedFrameCard({
  frame,
  showEvidence = true,
  compact = false,
  className = '',
}: DetectedFrameCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  const confidencePercent = Math.round(frame.confidence * 100);
  const narrativeColor = getNarrativeColor(frame.frame.type);
  const narrativeBgColor = getNarrativeBgColor(frame.frame.type);

  if (compact) {
    return (
      <div
        className={`flex items-center gap-3 p-3 rounded-lg border ${narrativeBgColor} ${className}`}
      >
        <Badge variant="outline" className={`capitalize ${narrativeColor}`}>
          {frame.frame.type}
        </Badge>
        <span className="flex-1 text-sm font-medium">{frame.frame.name}</span>
        <div className="flex items-center gap-2">
          <Progress value={confidencePercent} className="w-16 h-2" />
          <span className="text-xs text-muted-foreground w-8">
            {confidencePercent}%
          </span>
        </div>
      </div>
    );
  }

  return (
    <Card className={`${narrativeBgColor} ${className}`}>
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={`capitalize ${narrativeColor}`}>
                {frame.frame.type}
              </Badge>
              <span className="font-semibold">{frame.frame.name}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              {frame.frame.description}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{confidencePercent}%</div>
            <div className="text-xs text-muted-foreground">confidence</div>
          </div>
        </div>

        {/* Confidence bar */}
        <Progress value={confidencePercent} className="h-2 mb-3" />

        {/* Keywords */}
        {frame.frame.keywords.length > 0 && (
          <div className="mb-3">
            <div className="text-xs font-medium mb-1 flex items-center gap-1">
              <Target className="h-3 w-3" />
              Keywords
            </div>
            <div className="flex flex-wrap gap-1">
              {frame.frame.keywords.slice(0, 6).map((keyword) => (
                <Badge key={keyword} variant="secondary" className="text-xs">
                  {keyword}
                </Badge>
              ))}
              {frame.frame.keywords.length > 6 && (
                <Badge variant="secondary" className="text-xs">
                  +{frame.frame.keywords.length - 6} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Evidence - Collapsible */}
        {showEvidence && frame.evidence.length > 0 && (
          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="w-full justify-between">
                <span className="flex items-center gap-1">
                  <Quote className="h-3 w-3" />
                  Evidence ({frame.evidence.length})
                </span>
                {isOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-2">
              {frame.evidence.map((text, index) => (
                <div
                  key={index}
                  className="p-2 rounded bg-background/50 text-sm italic border-l-2 border-primary/30"
                >
                  "{text}"
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Position indicator */}
        {frame.start_position !== undefined && frame.end_position !== undefined && (
          <div className="mt-2 text-xs text-muted-foreground">
            Position: {frame.start_position} - {frame.end_position}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * List of detected frames
 */
interface DetectedFramesListProps {
  frames: DetectedFrame[];
  showEvidence?: boolean;
  compact?: boolean;
  maxItems?: number;
  className?: string;
}

export function DetectedFramesList({
  frames,
  showEvidence = true,
  compact = false,
  maxItems,
  className = '',
}: DetectedFramesListProps) {
  const displayFrames = maxItems ? frames.slice(0, maxItems) : frames;
  const hasMore = maxItems && frames.length > maxItems;

  if (frames.length === 0) {
    return (
      <div className={`text-center py-8 text-muted-foreground ${className}`}>
        No narrative frames detected.
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {displayFrames.map((frame, index) => (
        <DetectedFrameCard
          key={frame.frame.id || index}
          frame={frame}
          showEvidence={showEvidence}
          compact={compact}
        />
      ))}
      {hasMore && (
        <div className="text-center text-sm text-muted-foreground">
          +{frames.length - maxItems!} more frames
        </div>
      )}
    </div>
  );
}

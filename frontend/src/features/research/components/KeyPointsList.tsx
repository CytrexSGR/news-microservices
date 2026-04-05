/**
 * KeyPointsList Component
 *
 * Displays a bulleted list of key points extracted from research:
 * - Numbered or bullet points
 * - Copy to clipboard functionality
 * - Expandable for long lists
 */

import { useState } from 'react';
import {
  ListChecks,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface KeyPointsListProps {
  points: string[];
  title?: string;
  numbered?: boolean;
  maxVisible?: number;
  className?: string;
}

export function KeyPointsList({
  points,
  title = 'Key Points',
  numbered = false,
  maxVisible = 5,
  className,
}: KeyPointsListProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const visiblePoints = expanded ? points : points.slice(0, maxVisible);
  const hasMore = points.length > maxVisible;

  const handleCopy = async () => {
    const text = points.map((p, i) => (numbered ? `${i + 1}. ${p}` : `- ${p}`)).join('\n');
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (points.length === 0) {
    return null;
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
          <ListChecks className="h-4 w-4 text-primary" />
          {title} ({points.length})
        </h4>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-8 gap-1 text-xs"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Points List */}
      <ul className={cn(numbered ? 'list-decimal' : 'list-disc', 'ml-5 space-y-2')}>
        {visiblePoints.map((point, index) => (
          <li key={index} className="text-sm text-foreground pl-1">
            {point}
          </li>
        ))}
      </ul>

      {/* Show More/Less */}
      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-3 w-3" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3" />
              Show {points.length - maxVisible} more
            </>
          )}
        </button>
      )}
    </div>
  );
}

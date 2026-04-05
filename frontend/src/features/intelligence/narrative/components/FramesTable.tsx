/**
 * FramesTable - Display available narrative frames in a table
 *
 * Shows all narrative frames that can be detected with their
 * descriptions, keywords, and example phrases.
 */
import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Search,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  BookOpen,
  AlertCircle,
} from 'lucide-react';
import { useNarrativeFrames } from '../api/useNarrativeFrames';
import type { NarrativeFrame, NarrativeType } from '../types/narrative.types';
import { getNarrativeColor, getNarrativeBgColor } from '../types/narrative.types';

interface FramesTableProps {
  onFrameSelect?: (frame: NarrativeFrame) => void;
  selectedFrameId?: string;
  compact?: boolean;
  className?: string;
}

export function FramesTable({
  onFrameSelect,
  selectedFrameId,
  compact = false,
  className = '',
}: FramesTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFrames, setExpandedFrames] = useState<Set<string>>(new Set());
  const [selectedType, setSelectedType] = useState<NarrativeType | 'all'>('all');

  const { data, isLoading, error, refetch } = useNarrativeFrames();

  const filteredFrames = useMemo(() => {
    if (!data?.frames) return [];

    return data.frames.filter((frame) => {
      // Type filter
      if (selectedType !== 'all' && frame.type !== selectedType) return false;

      // Search filter
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        return (
          frame.name.toLowerCase().includes(term) ||
          frame.description.toLowerCase().includes(term) ||
          frame.keywords.some((k) => k.toLowerCase().includes(term))
        );
      }

      return true;
    });
  }, [data?.frames, searchTerm, selectedType]);

  const toggleExpanded = (frameId: string) => {
    const newExpanded = new Set(expandedFrames);
    if (newExpanded.has(frameId)) {
      newExpanded.delete(frameId);
    } else {
      newExpanded.add(frameId);
    }
    setExpandedFrames(newExpanded);
  };

  const narrativeTypes: NarrativeType[] = [
    'conflict',
    'cooperation',
    'crisis',
    'progress',
    'decline',
    'neutral',
  ];

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-muted-foreground">Failed to load narrative frames.</p>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <CompactFramesTable
        frames={filteredFrames}
        isLoading={isLoading}
        onFrameSelect={onFrameSelect}
        selectedFrameId={selectedFrameId}
        className={className}
      />
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            <CardTitle>Narrative Frames</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>
          Reference of all narrative frames that can be detected in text analysis.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search frames..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={selectedType === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType('all')}
            >
              All
            </Button>
            {narrativeTypes.map((type) => (
              <Button
                key={type}
                variant={selectedType === type ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedType(type)}
                className="capitalize"
              >
                {type}
              </Button>
            ))}
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : filteredFrames.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            {searchTerm
              ? `No frames found matching "${searchTerm}"`
              : 'No frames available.'}
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[150px]">Type</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="hidden md:table-cell">Description</TableHead>
                  <TableHead className="w-[100px]">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredFrames.map((frame) => {
                  const isExpanded = expandedFrames.has(frame.id);
                  const isSelected = frame.id === selectedFrameId;

                  return (
                    <Collapsible key={frame.id} open={isExpanded} asChild>
                      <>
                        <TableRow
                          className={`cursor-pointer ${
                            isSelected ? 'bg-primary/10' : ''
                          }`}
                          onClick={() => onFrameSelect?.(frame)}
                        >
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={`capitalize ${getNarrativeColor(frame.type)}`}
                            >
                              {frame.type}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-medium">{frame.name}</TableCell>
                          <TableCell className="hidden md:table-cell text-muted-foreground max-w-xs truncate">
                            {frame.description}
                          </TableCell>
                          <TableCell>
                            <CollapsibleTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleExpanded(frame.id);
                                }}
                              >
                                {isExpanded ? (
                                  <ChevronUp className="h-4 w-4" />
                                ) : (
                                  <ChevronDown className="h-4 w-4" />
                                )}
                              </Button>
                            </CollapsibleTrigger>
                          </TableCell>
                        </TableRow>
                        <CollapsibleContent asChild>
                          <TableRow className={`${getNarrativeBgColor(frame.type)}`}>
                            <TableCell colSpan={4} className="p-4">
                              <FrameDetails frame={frame} />
                            </TableCell>
                          </TableRow>
                        </CollapsibleContent>
                      </>
                    </Collapsible>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Results count */}
        {data?.frames && (
          <div className="text-sm text-muted-foreground">
            Showing {filteredFrames.length} of {data.frames.length} frames
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Frame details panel shown when expanded
 */
interface FrameDetailsProps {
  frame: NarrativeFrame;
}

function FrameDetails({ frame }: FrameDetailsProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm md:hidden">{frame.description}</p>

      {/* Keywords */}
      {frame.keywords.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Keywords</h4>
          <div className="flex flex-wrap gap-1">
            {frame.keywords.map((keyword) => (
              <Badge key={keyword} variant="secondary" className="text-xs">
                {keyword}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Example Phrases */}
      {frame.example_phrases.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Example Phrases</h4>
          <ul className="space-y-1">
            {frame.example_phrases.map((phrase, index) => (
              <li
                key={index}
                className="text-sm text-muted-foreground italic border-l-2 border-primary/30 pl-3"
              >
                "{phrase}"
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for sidebar/selection lists
 */
interface CompactFramesTableProps {
  frames: NarrativeFrame[];
  isLoading: boolean;
  onFrameSelect?: (frame: NarrativeFrame) => void;
  selectedFrameId?: string;
  className?: string;
}

function CompactFramesTable({
  frames,
  isLoading,
  onFrameSelect,
  selectedFrameId,
  className = '',
}: CompactFramesTableProps) {
  if (isLoading) {
    return (
      <div className={`space-y-2 ${className}`}>
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className={`space-y-1 ${className}`}>
      {frames.map((frame) => (
        <button
          key={frame.id}
          onClick={() => onFrameSelect?.(frame)}
          className={`w-full flex items-center gap-2 p-2 rounded-lg text-left transition-colors ${
            selectedFrameId === frame.id
              ? 'bg-primary/10 ring-1 ring-primary'
              : 'hover:bg-secondary'
          }`}
        >
          <Badge
            variant="outline"
            className={`text-xs capitalize ${getNarrativeColor(frame.type)}`}
          >
            {frame.type}
          </Badge>
          <span className="text-sm font-medium">{frame.name}</span>
        </button>
      ))}
    </div>
  );
}

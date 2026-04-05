/**
 * AsyncJobResultView - Job results display
 *
 * Displays the results of a completed async batch canonicalization job.
 */
import { CheckCircle2, AlertCircle, ExternalLink, Clock, Download } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAsyncJobResult } from '../api/useAsyncJobResult';
import { getConfidenceColor, getEntityTypeConfig } from '../types/entities.types';
import type { CanonicalEntity } from '../types/entities.types';

interface AsyncJobResultViewProps {
  jobId: string;
  onClose?: () => void;
  className?: string;
}

const ConfidenceBadge = ({ confidence }: { confidence: number }) => {
  const color = getConfidenceColor(confidence);
  return (
    <span className={`font-medium ${color}`}>{(confidence * 100).toFixed(0)}%</span>
  );
};

export function AsyncJobResultView({ jobId, onClose, className }: AsyncJobResultViewProps) {
  const { data: result, isLoading, isError, error } = useAsyncJobResult(jobId);

  // Export results as CSV
  const exportToCSV = () => {
    if (!result) return;

    const headers = [
      'Canonical Name',
      'Wikidata ID',
      'Entity Type',
      'Confidence',
      'Source',
      'Aliases',
    ];
    const rows = result.results.map((r) => [
      r.canonical_name,
      r.canonical_id || '',
      r.entity_type,
      r.confidence.toFixed(3),
      r.source,
      r.aliases.join('; '),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `canonicalization-results-${jobId.slice(0, 8)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            Failed to Load Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{error?.message}</p>
          {onClose && (
            <Button variant="outline" onClick={onClose} className="mt-4">
              Close
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  if (!result) return null;

  // Calculate summary stats
  const withWikidata = result.results.filter((r) => r.canonical_id).length;
  const avgConfidence =
    result.results.reduce((sum, r) => sum + r.confidence, 0) / result.results.length;
  const sourceCounts = result.results.reduce(
    (acc, r) => {
      acc[r.source] = (acc[r.source] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Batch Results
            </CardTitle>
            <CardDescription className="font-mono text-xs mt-1">{jobId}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={exportToCSV}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            {onClose && (
              <Button variant="ghost" size="sm" onClick={onClose}>
                Close
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-3">
          <div className="p-3 bg-muted rounded-lg text-center">
            <div className="text-2xl font-bold">{result.total_processed}</div>
            <div className="text-xs text-muted-foreground">Total Processed</div>
          </div>
          <div className="p-3 bg-muted rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-500">{withWikidata}</div>
            <div className="text-xs text-muted-foreground">With Wikidata</div>
          </div>
          <div className="p-3 bg-muted rounded-lg text-center">
            <div className="text-2xl font-bold text-green-500">
              {(avgConfidence * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg Confidence</div>
          </div>
          <div className="p-3 bg-muted rounded-lg text-center">
            <div className="text-2xl font-bold">{result.total_time_ms.toFixed(0)}ms</div>
            <div className="text-xs text-muted-foreground">Total Time</div>
          </div>
        </div>

        {/* Source Breakdown */}
        <div className="flex items-center gap-2 flex-wrap">
          {Object.entries(sourceCounts).map(([source, count]) => (
            <Badge key={source} variant="secondary">
              {source}: {count}
            </Badge>
          ))}
        </div>

        {/* Results Table */}
        <ScrollArea className="h-[400px] border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Canonical Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Wikidata</TableHead>
                <TableHead className="text-center">Confidence</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Aliases</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.results.map((entity, idx) => (
                <ResultRow key={idx} entity={entity} />
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function ResultRow({ entity }: { entity: CanonicalEntity }) {
  const typeConfig = getEntityTypeConfig(entity.entity_type);

  return (
    <TableRow>
      <TableCell className="font-medium">{entity.canonical_name}</TableCell>
      <TableCell>
        <Badge variant="outline" className={typeConfig.color}>
          {entity.entity_type}
        </Badge>
      </TableCell>
      <TableCell>
        {entity.canonical_id ? (
          <a
            href={`https://www.wikidata.org/wiki/${entity.canonical_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-blue-500 hover:underline text-sm"
          >
            {entity.canonical_id}
            <ExternalLink className="h-3 w-3" />
          </a>
        ) : (
          <span className="text-muted-foreground">-</span>
        )}
      </TableCell>
      <TableCell className="text-center">
        <ConfidenceBadge confidence={entity.confidence} />
      </TableCell>
      <TableCell>
        <Badge variant="secondary" className="text-xs">
          {entity.source}
        </Badge>
      </TableCell>
      <TableCell>
        {entity.aliases.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {entity.aliases.slice(0, 3).map((alias, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {alias}
              </Badge>
            ))}
            {entity.aliases.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{entity.aliases.length - 3}
              </Badge>
            )}
          </div>
        ) : (
          <span className="text-muted-foreground">-</span>
        )}
      </TableCell>
    </TableRow>
  );
}

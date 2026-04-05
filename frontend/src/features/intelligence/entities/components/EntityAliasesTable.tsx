/**
 * EntityAliasesTable - Aliases table
 *
 * Displays all known aliases for a canonical entity.
 */
import { Tag, Copy, Check, ExternalLink } from 'lucide-react';
import { useState } from 'react';
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
import { useEntityAliases } from '../api/useEntityAliases';
import type { EntityType } from '../types/entities.types';
import { getEntityTypeConfig } from '../types/entities.types';

interface EntityAliasesTableProps {
  canonicalName: string;
  entityType: EntityType;
  canonicalId?: string | null;
  className?: string;
}

export function EntityAliasesTable({
  canonicalName,
  entityType,
  canonicalId,
  className,
}: EntityAliasesTableProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const { data: aliases, isLoading, isError, error } = useEntityAliases(
    canonicalName,
    entityType
  );

  const typeConfig = getEntityTypeConfig(entityType);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Tag className="h-5 w-5" />
            Entity Aliases
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-destructive/10 rounded-lg text-destructive text-sm">
            Failed to load aliases: {error?.message}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              {canonicalName}
            </CardTitle>
            <CardDescription className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className={typeConfig.color}>
                {entityType}
              </Badge>
              {canonicalId && (
                <a
                  href={`https://www.wikidata.org/wiki/${canonicalId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-500 hover:underline text-sm"
                >
                  {canonicalId}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </CardDescription>
          </div>
          <Badge variant="secondary">{aliases?.length || 0} aliases</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {!aliases || aliases.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No aliases found for this entity
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>Alias</TableHead>
                <TableHead className="w-20 text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {aliases.map((alias, idx) => (
                <TableRow key={idx}>
                  <TableCell className="text-muted-foreground">{idx + 1}</TableCell>
                  <TableCell className="font-medium">{alias}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => copyToClipboard(alias, idx)}
                    >
                      {copiedIndex === idx ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Compact aliases display for inline use
 */
interface AliasesInlineProps {
  aliases: string[];
  maxDisplay?: number;
  className?: string;
}

export function AliasesInline({ aliases, maxDisplay = 3, className }: AliasesInlineProps) {
  if (aliases.length === 0) {
    return <span className="text-muted-foreground">No aliases</span>;
  }

  const displayAliases = aliases.slice(0, maxDisplay);
  const remaining = aliases.length - maxDisplay;

  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {displayAliases.map((alias, idx) => (
        <Badge key={idx} variant="outline" className="text-xs">
          {alias}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="secondary" className="text-xs">
          +{remaining} more
        </Badge>
      )}
    </div>
  );
}

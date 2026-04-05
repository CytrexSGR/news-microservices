/**
 * ExperimentsTable - Displays strategy experiments in a table.
 *
 * Columns: experiment_id, hypothesis, status, variants count, created_at, completed_at.
 * Status badges use color coding: running=blue, completed=green, failed=red, cancelled=gray.
 */

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table'
import type { StrategyExperiment } from '../../hooks/useStrategyLab'

interface ExperimentsTableProps {
  experiments: StrategyExperiment[] | undefined
  isLoading: boolean
}

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  running: 'default',
  completed: 'outline',
  failed: 'destructive',
  cancelled: 'secondary',
}

const STATUS_CLASS: Record<string, string> = {
  running: 'bg-blue-500/15 text-blue-600 border-blue-500/30',
  completed: 'bg-green-500/15 text-green-600 border-green-500/30',
  failed: '',
  cancelled: '',
}

function formatDate(iso: string | undefined): string {
  if (!iso) return '--'
  try {
    return new Date(iso).toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

export default function ExperimentsTable({ experiments, isLoading }: ExperimentsTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Experiments</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!experiments || experiments.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Experiments</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No experiments found. Create an experiment to test strategy variations.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Experiments
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({experiments.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Experiment ID</TableHead>
              <TableHead>Hypothesis</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-center">Variants</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Completed</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {experiments.map((exp) => (
              <TableRow key={exp.experiment_id}>
                <TableCell className="font-mono text-xs">
                  {truncate(exp.experiment_id, 12)}
                </TableCell>
                <TableCell className="max-w-[300px]">
                  <span title={exp.hypothesis}>{truncate(exp.hypothesis, 60)}</span>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={STATUS_VARIANT[exp.status] ?? 'outline'}
                    className={STATUS_CLASS[exp.status] ?? ''}
                  >
                    {exp.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-center">
                  {exp.variants?.length ?? 0}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatDate(exp.created_at)}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatDate(exp.completed_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

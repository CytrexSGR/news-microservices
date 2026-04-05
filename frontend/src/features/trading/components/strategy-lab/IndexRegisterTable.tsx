/**
 * IndexRegisterTable - Displays custom indices in a table.
 *
 * Columns: name, type (badge), version, description (truncated), created_at.
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
import type { CustomIndex } from '../../hooks/useStrategyLab'

interface IndexRegisterTableProps {
  indices: CustomIndex[] | undefined
  isLoading: boolean
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
  if (!text) return '--'
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

export default function IndexRegisterTable({ indices, isLoading }: IndexRegisterTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Index Register</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!indices || indices.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Index Register</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No custom indices registered. Create an index to define custom asset groups.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Index Register
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({indices.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-center">Version</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {indices.map((idx) => (
              <TableRow key={idx.id}>
                <TableCell className="font-medium">{idx.name}</TableCell>
                <TableCell>
                  <Badge variant="secondary">{idx.type}</Badge>
                </TableCell>
                <TableCell className="text-center">v{idx.version}</TableCell>
                <TableCell className="max-w-[300px]">
                  <span title={idx.description}>{truncate(idx.description, 60)}</span>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatDate(idx.created_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

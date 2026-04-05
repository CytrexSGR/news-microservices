import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Search } from 'lucide-react'
import type { TopQuery } from '@/types/searchServiceAdmin'

interface TopQueriesTableProps {
  queries: TopQuery[]
}

export function TopQueriesTable({ queries }: TopQueriesTableProps) {
  // Sort by hits descending and limit to 20
  const sortedQueries = [...(queries || [])]
    .sort((a, b) => b.hits - a.hits)
    .slice(0, 20)

  const getRankBadge = (rank: number) => {
    switch (rank) {
      case 1:
        return (
          <Badge variant="default" className="bg-yellow-500 hover:bg-yellow-600">
            🥇 {rank}
          </Badge>
        )
      case 2:
        return (
          <Badge variant="default" className="bg-gray-400 hover:bg-gray-500">
            🥈 {rank}
          </Badge>
        )
      case 3:
        return (
          <Badge variant="default" className="bg-amber-600 hover:bg-amber-700">
            🥉 {rank}
          </Badge>
        )
      default:
        return <span className="text-sm text-muted-foreground">{rank}</span>
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Search className="h-5 w-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Top Queries</h3>
        </div>
        <Badge variant="outline">{sortedQueries.length} queries</Badge>
      </div>

      {/* Table */}
      <div className="rounded-md border overflow-x-auto">
        <table className="w-full">
          <thead className="border-b">
            <tr className="text-sm">
              <th className="text-left p-3 font-medium w-20">Rank</th>
              <th className="text-left p-3 font-medium">Query</th>
              <th className="text-right p-3 font-medium w-24">Hits</th>
            </tr>
          </thead>
          <tbody>
            {sortedQueries.length === 0 ? (
              <tr>
                <td colSpan={3} className="text-center py-8 text-muted-foreground">
                  No queries yet
                </td>
              </tr>
            ) : (
              sortedQueries.map((query, index) => (
                <tr key={index} className="border-b hover:bg-muted/50">
                  <td className="p-3">{getRankBadge(index + 1)}</td>
                  <td className="p-3">
                    <span className="font-medium">{query.query}</span>
                  </td>
                  <td className="p-3 text-right">
                    <span className="font-semibold">{query.hits}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

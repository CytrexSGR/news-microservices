import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Network, Circle, GitBranch, Tag } from 'lucide-react'
import type { GraphStats } from '@/types/knowledgeGraph'

interface GraphStatsCardProps {
  stats: GraphStats | null
  isLoading: boolean
}

export function GraphStatsCard({ stats, isLoading }: GraphStatsCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Graph Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading graph statistics...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Graph Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-destructive">
            Failed to load graph statistics
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate graph density (approximate: edges / (nodes * (nodes-1)/2))
  const density =
    stats.total_nodes > 1
      ? (stats.total_relationships / (stats.total_nodes * (stats.total_nodes - 1))) * 2
      : 0

  // Get top 3 entity types
  const topEntityTypes = Object.entries(stats.entity_types)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5" />
          Graph Statistics
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Total Nodes */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Circle className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Total Nodes</span>
          </div>
          <span className="text-2xl font-bold">{stats.total_nodes.toLocaleString()}</span>
        </div>

        {/* Total Relationships */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Total Relationships</span>
          </div>
          <span className="text-2xl font-bold">{stats.total_relationships.toLocaleString()}</span>
        </div>

        {/* Graph Density */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Graph Density</span>
          <span className="text-sm font-medium">{(density * 100).toFixed(2)}%</span>
        </div>

        {/* Top Entity Types */}
        <div className="pt-2 border-t">
          <div className="flex items-center gap-2 mb-2">
            <Tag className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Top Entity Types</span>
          </div>
          <div className="space-y-1">
            {topEntityTypes.map(([type, count]) => {
              const percentage = ((count / stats.total_nodes) * 100).toFixed(1)
              return (
                <div key={type} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{type}</span>
                  <span className="font-medium">
                    {count.toLocaleString()} ({percentage}%)
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
